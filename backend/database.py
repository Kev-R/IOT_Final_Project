"""
database.py

SQLite helper functions for the Smart Lab Inventory Tracking System.

This module isolates all database access from the rest of the backend. The rules
layer calls these functions instead of writing SQL directly. This makes the
backend easier to maintain and keeps database reads/writes consistent.
"""

import sqlite3

# SQLite database file created by init_db.py
DB_NAME = "lab.db"

# Open and return a connection to the SQLite database.
def get_connection():
    return sqlite3.connect(DB_NAME)

# Return a user row by RFID user_id, or None if no matching user exists
def get_user(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

# Return an asset row by RFID asset_id, or None if no matching asset exists
def get_asset_by_id(asset_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM assets WHERE asset_id=?", (asset_id,))
    row = c.fetchone()
    conn.close()
    return row

# Return an asset row by human-readable name. Kept for older menu flows
def get_asset_by_name(asset_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM assets WHERE asset_name=?", (asset_name,))
    row = c.fetchone()
    conn.close()
    return row

# Return all assets currently checked out by the specified user
def get_assets_held_by_user(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM assets WHERE current_holder=?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

# Return the number of assets currently held by a user
def count_user_checked_out_items(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM assets WHERE current_holder=?", (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

# Mark an asset as checked out by a user
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

# Mark an asset as returned
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

# Log a transaction in the database, including both approved and denied actions
def log_transaction(user_id, asset_id, action, result, reason):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO transactions (user_id, asset_id, action, result, reason)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, asset_id, action, result, reason))
    conn.commit()
    conn.close()
