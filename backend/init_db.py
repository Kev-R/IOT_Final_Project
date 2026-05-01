"""
init_db.py

Database initialization script for the Smart Lab Inventory Tracking System.

Run this script once when creating a fresh database, or rerun it when you want to
reset the demo database to known sample data. 
"""

import sqlite3

# Open or create the SQLite database file in the current backend directory
conn = sqlite3.connect("lab.db")
c = conn.cursor()

# Users table:
# user_id is the RFID UID for a user badge
# role determines access permissions, such as student or TA
# max_items limits how many assets a user can hold at once
# blocked and overdue_count are policy flags used by the rules engine
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    role TEXT,
    max_items INTEGER,
    blocked INTEGER,
    overdue_count INTEGER
)
""")

# Assets table:
# asset_id is the RFID UID attached to a physical item
# available = 1 means the item is in the lab; available = 0 means checked out
# restricted = 1 means only authorized roles, such as TA, may check it out
# current_holder stores the user_id of the person currently holding the item
c.execute("""
CREATE TABLE IF NOT EXISTS assets (
    asset_id TEXT PRIMARY KEY,
    asset_name TEXT,
    category TEXT,
    available INTEGER,
    restricted INTEGER,
    shelf_slot TEXT,
    current_holder TEXT
)
""")

# Transactions table:
# Stores every approved and denied user action for auditing and dashboard display
c.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    asset_id TEXT,
    action TEXT,
    result TEXT,
    reason TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Alerts table:
# Stores policy/security events such as unknown users, restricted denials,
# maximum item limit violations, and wrong user return attempts
c.execute("""
CREATE TABLE IF NOT EXISTS alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    asset_id TEXT,
    alert_type TEXT,
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Sample users
c.execute("INSERT OR REPLACE INTO users VALUES ('1079825143068', 'Alice', 'student', 1, 0, 0)")
c.execute("INSERT OR REPLACE INTO users VALUES ('946175681221', 'Bob', 'TA', 3, 0, 0)")
c.execute("INSERT OR REPLACE INTO users VALUES ('360419244072', 'Charlie', 'student', 1, 0, 0)")
c.execute("INSERT OR REPLACE INTO users VALUES ('700209248293', 'Diana', 'TA', 3, 0, 0)")

# Sample assets
c.execute("INSERT OR REPLACE INTO assets VALUES ('163941859838', 'Breadboard Kit', 'electronics', 1, 0, 'slot1', NULL)")
c.execute("INSERT OR REPLACE INTO assets VALUES ('737756135838', 'Oscilloscope Probe Set', 'electronics', 1, 1, 'slot2', NULL)")
c.execute("INSERT OR REPLACE INTO assets VALUES ('685595771343', 'Multimeter Kit', 'electronics', 1, 0, 'slot3', NULL)")
c.execute("INSERT OR REPLACE INTO assets VALUES ('107973067209', 'FPGA Development Board', 'advanced', 1, 1, 'slot4', NULL)")
c.execute("INSERT OR REPLACE INTO assets VALUES ('529265738162', 'Signal Generator', 'electronics', 1, 0, 'slot5', NULL)")
c.execute("INSERT OR REPLACE INTO assets VALUES ('629040327669', 'RC522 Kit', 'electronics', 1, 0, 'slot6', NULL)")
c.execute("INSERT OR REPLACE INTO assets VALUES ('355822578572', 'Soldering Iron', 'tools', 1, 1, 'slot7', NULL)")

conn.commit()
conn.close()

print("Database initialized.")
