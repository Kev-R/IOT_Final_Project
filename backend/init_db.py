import sqlite3

conn = sqlite3.connect("lab.db")
c = conn.cursor()

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

# Sample users — replace these with your real RFID IDs after scanning
c.execute("INSERT OR REPLACE INTO users VALUES ('1079825143068', 'Alice', 'student', 1, 0, 0)")
c.execute("INSERT OR REPLACE INTO users VALUES ('946175681221', 'Bob', 'TA', 3, 0, 0)")

# Sample assets — replace later with real asset RFID IDs
c.execute("INSERT OR REPLACE INTO assets VALUES ('163941859838', 'Breadboard Kit', 'electronics', 1, 0, 'slot1', NULL)")
c.execute("INSERT OR REPLACE INTO assets VALUES ('737756135838', 'Oscilloscope Probe Set', 'electronics', 1, 1, 'slot2', NULL)")
c.execute("INSERT OR REPLACE INTO assets VALUES ('685595771343', 'Multimeter Kit', 'electronics', 1, 0, 'slot3',NULL)")
c.execute("INSERT OR REPLACE INTO assets VALUES ('107973067209', 'FPGA Development Board', 'advanced', 1, 1, 'slot4', NULL)")
c.execute("INSERT OR REPLACE INTO assets VALUES ('529265738162', 'Signal Generator', 'electronics', 1, 0, 'slot5', NULL)")

conn.commit()
conn.close()

print("Database initialized.")
