from flask import Flask, render_template
import sqlite3
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "backend", "lab.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    conn = get_connection()
    c = conn.cursor()

    # Inventory with current holder name
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

    # Transactions with user name and asset name
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
        LIMIT 20
    """)
    transactions = c.fetchall()

    # Alerts with user name and asset name
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
