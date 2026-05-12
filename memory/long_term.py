import sqlite3
import json
import uuid
import datetime
from app_config import DB_PATH
import os

class LongTermMemory:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tool_logs (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                tool_name TEXT,
                args TEXT,
                result TEXT,
                success INTEGER,
                timestamp TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_name TEXT NOT NULL,
                args TEXT,
                success INTEGER,
                user_corrected INTEGER DEFAULT 0,
                timestamp TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def ensure_session(self, session_id: str):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
        if not cursor.fetchone():
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            cursor.execute("INSERT INTO sessions (id, created_at) VALUES (?, ?)", (session_id, now))
            self.conn.commit()

    def save_turn(self, session_id: str, role: str, content: str):
        cursor = self.conn.cursor()
        memory_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute(
            "INSERT INTO memories (id, session_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
            (memory_id, session_id, role, content, now)
        )
        self.conn.commit()

    def log_tool(self, session_id: str, tool_name: str, args: str, result: str, success: int):
        cursor = self.conn.cursor()
        log_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute(
            "INSERT INTO tool_logs (id, session_id, tool_name, args, result, success, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (log_id, session_id, tool_name, args, result, success, now)
        )
        self.conn.commit()

    def recall(self, session_id: str, limit: int = 20) -> list:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT role, content FROM memories WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
            (session_id, limit)
        )
        rows = cursor.fetchall()
        # Return in chronological order
        return [{"role": row[0], "content": row[1]} for row in reversed(rows)]

    def get_tool_logs(self, session_id: str) -> list:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT tool_name, args, result, success, timestamp FROM tool_logs WHERE session_id = ? ORDER BY timestamp DESC",
            (session_id,)
        )
        columns = ["tool_name", "args", "result", "success", "timestamp"]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def close(self):
        self.conn.close()
