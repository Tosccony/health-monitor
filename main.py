import os
import requests
import psycopg2
from datetime import datetime
import time

URLS = ["https://google.com", "https://github.com",
       "https://facebook.com", "https://Thisshouldfail.com"]

CHECK_INTERVAL = 60

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    retries = 5
    for attempt in range(retries):
        try:
            return psycopg2.connect(database_url)
        except psycopg2.OperationalError:
            if attempt < retries - 1:
                print("Database connection failed, retrying in 2 seconds...")
                time.sleep(2)
            else:
                raise

def create_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_checks (
        id SERIAL PRIMARY KEY,
        url TEXT NOT NULL,
        is_healthy BOOLEAN NOT NULL,
        response_time FLOAT,
        checked_at TIMESTAMP NOT NULL
        )
    """)
    conn.commit()
    cursor.close()

def save_result(conn, url, is_healthy, response_time):
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO health_checks (url, is_healthy, response_time, checked_at)
    VALUES (%s, %s, %s, %s)
    """, (url, is_healthy, response_time, datetime.now()))
    conn.commit()
    cursor.close()

def cleanup_old_checks(conn, hours=24):
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM health_checks 
        WHERE checked_at < NOW() - INTERVAL '%s hours'
    """, (hours,))
    deleted = cursor.rowcount
    conn.commit()
    cursor.close()
    if deleted > 0:
        print(f"  Cleaned up {deleted} old records")


def run_checks(conn):
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running health checks...")
    cleanup_old_checks(conn)
    for url in URLS:
        is_healthy, response_time = check_website_health(url)
        save_result(conn, url, is_healthy, response_time)

        if is_healthy:
            print(f"  ✓ {url} ({response_time:.2f}s)")
        else:
            print(f"  ✗ {url} (unreachable)")

def check_website_health(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return True, response.elapsed.total_seconds()
        else:
            return False, None
    except requests.RequestException:
        return False, None


if __name__ == "__main__":
    conn = get_db_connection()
    create_table(conn)

    print(f"Health Monitor started. Checking every {CHECK_INTERVAL} seconds.")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            run_checks(conn)
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        conn.close()