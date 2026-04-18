import sqlite3

DB_NAME = "lab.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def get_user(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def get_asset_by_id(asset_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM assets WHERE asset_id=?", (asset_id,))
    row = c.fetchone()
    conn.close()
    return row

def get_asset_by_name(asset_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM assets WHERE asset_name=?", (asset_name,))
    row = c.fetchone()
    conn.close()
    return row

def get_assets_held_by_user(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM assets WHERE current_holder=?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def count_user_checked_out_items(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM assets WHERE current_holder=?", (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

def mark_asset_checked_out(user_id, asset_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE assets
        SET available=0, current_holder=?
        WHERE asset_id=?
    """, (user_id, asset_id))
    conn.commit()
    conn.close()

def mark_asset_returned(asset_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE assets
        SET available=1, current_holder=NULL
        WHERE asset_id=?
    """, (asset_id,))
    conn.commit()
    conn.close()

def log_transaction(user_id, asset_id, action, result, reason):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO transactions (user_id, asset_id, action, result, reason)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, asset_id, action, result, reason))
    conn.commit()
    conn.close()
