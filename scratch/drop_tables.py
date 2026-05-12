import sqlite3
import os

DB_PATH = r"c:\Users\samue\Baymax\memory\baymax.db"

print(f"Attempting to clear tables in {DB_PATH}...")
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS memories;")
    cursor.execute("DROP TABLE IF EXISTS tool_logs;")
    cursor.execute("DROP TABLE IF EXISTS sessions;")
    conn.commit()
    conn.close()
    print("SUCCESS: Tables dropped. They will be re-created with the correct schema on next server start.")
except Exception as e:
    print(f"FAILURE: Could not drop tables: {e}")
