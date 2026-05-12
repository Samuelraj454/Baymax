import sqlite3
conn = sqlite3.connect('memory/baymax.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(f"Tables found: {c.fetchall()}")
conn.close()
