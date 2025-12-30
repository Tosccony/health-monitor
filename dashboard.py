import os
import psycopg2
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(database_url)

@app.get("/", response_class=HTMLResponse)
def home():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT ON (url) url, is_healthy, response_time, checked_at 
        FROM health_checks 
        ORDER BY url, checked_at DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    html = """
    <html>
    <head>
        <title>Health Monitor Dashboard</title>
                <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #4CAF50; color: white; }
            tr:nth-child(even) { background-color: #f2f2f2; }
            .healthy { color: green; }
            .unhealthy { color: red; }
        </style>
    </head>
    <body>
        <h1>Health Monitor Dashboard</h1>
        <table>
            <tr>
            <th>Status</th>
            <th>URL</th>
            <th>Response Time (s)</th>
            <th>Checked At</th>
            </tr>
    """

    for row in rows:
        url, is_healthy, response_time, checked_at = row
        status = "✓" if is_healthy else "✗"
        status_class = "healthy" if is_healthy else "unhealthy"
        time_str = f"{response_time:.2f}s" if response_time else "N/A"

        html += f"""
            <tr>
                <td class="{status_class}">{status}</td>
                <td>{url}</td>
                <td>{time_str}</td>
                <td>{checked_at}</td>
            </tr>
        """
    html += """
        </table>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)