from database import get_connection

def create_alert(user_id, asset_id, alert_type, message):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO alerts (user_id, asset_id, alert_type, message)
        VALUES (?, ?, ?, ?)
    """, (user_id, asset_id, alert_type, message))
    conn.commit()
    conn.close()
