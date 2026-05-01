"""
app.py

Flask dashboard for the Smart Lab Inventory Tracking System.

The dashboard does not communicate over MQTT. Instead, it reads directly from
the SQLite database that the backend updates. This allows operators to view the
current inventory, recent transactions, and recent alerts in a browser.
"""

from flask import Flask, render_template
import sqlite3
import os

app = Flask(__name__)

# Resolve the database path relative to this dashboard folder.
# Expected project structure:
# smartlab/
#   backend/lab.db
#   dashboard/app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "backend", "lab.db")

# Open SQLite connection and return rows that behave like dictionaries
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    """Render the main dashboard page."""
    conn = get_connection()
    c = conn.cursor()

    # Inventory view
    c.execute("""
        SELECT
            a.asset_id,
            a.asset_name,
            a.category,
            a.available,
            a.restricted,
            a.shelf_slot,
            a.current_holder,
            u.name AS holder_name
        FROM assets a
        LEFT JOIN users u ON a.current_holder = u.user_id
        ORDER BY a.asset_name
    """)
    assets = c.fetchall()

    # Recent transactions view
    c.execute("""
        SELECT
            t.transaction_id,
            t.user_id,
            u.name AS user_name,
            t.asset_id,
            a.asset_name,
            t.action,
            t.result,
            t.reason,
            t.timestamp
        FROM transactions t
        LEFT JOIN users u ON t.user_id = u.user_id
        LEFT JOIN assets a ON t.asset_id = a.asset_id
        ORDER BY t.transaction_id DESC
        LIMIT 7
    """)
    transactions = c.fetchall()

    # Recent alerts view
    c.execute("""
        SELECT
            al.alert_id,
            al.user_id,
            u.name AS user_name,
            al.asset_id,
            a.asset_name,
            al.alert_type,
            al.message,
            al.timestamp
        FROM alerts al
        LEFT JOIN users u ON al.user_id = u.user_id
        LEFT JOIN assets a ON al.asset_id = a.asset_id
        ORDER BY al.alert_id DESC
        LIMIT 20
    """)
    alerts = c.fetchall()

    conn.close()

    return render_template(
        "index.html",
        assets=assets,
        transactions=transactions,
        alerts=alerts
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
