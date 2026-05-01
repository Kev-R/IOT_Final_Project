"""
alerts.py

Alert logging helper for the Smart Lab Inventory Tracking System.

Alerts represent security-relevant or policy-relevant events, such as unknown
users, restricted item attempts, max item violations, and wrong user returns.
They are displayed in the dashboard separately from normal transactions.
Essentially, they are a way to log and display important events that require attention.
"""

from database import get_connection

# Create a new alert in the database with the specified details
def create_alert(user_id, asset_id, alert_type, message):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO alerts (user_id, asset_id, alert_type, message)
        VALUES (?, ?, ?, ?)
    """, (user_id, asset_id, alert_type, message))
    conn.commit()
    conn.close()
