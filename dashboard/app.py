from flask import Flask, render_template
import sqlite3
import os

app = Flask(__name__)

# Path to the backend database
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

    c.execute("""
        SELECT asset_id, asset_name, category, available, restricted, shelf_slot, current_holder
        FROM assets
        ORDER BY asset_name
    """)
    assets = c.fetchall()

    c.execute("""
        SELECT transaction_id, user_id, asset_id, action, result, reason, timestamp
        FROM transactions
        ORDER BY transaction_id DESC
        LIMIT 20
    """)
    transactions = c.fetchall()

    c.execute("""
        SELECT alert_id, user_id, asset_id, alert_type, message, timestamp
        FROM alerts
        ORDER BY alert_id DESC
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
