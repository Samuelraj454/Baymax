from .base_tool import BaseTool, ToolResult
import sqlite3
import datetime
from app_config import DB_PATH
import json

class NotesTool(BaseTool):
    name = "notes"
    description = "Manage personal notes (create, read, search, list)."
    schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["create", "read", "search", "list", "append"]},
            "title": {"type": "string"},
            "content": {"type": "string"},
            "query": {"type": "string"},
            "tags": {"type": "string"}
        },
        "required": ["action"]
    }

    def __init__(self):
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT,
                created TEXT NOT NULL,
                updated TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def run(self, action: str, **kwargs) -> ToolResult:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            now = datetime.datetime.now().isoformat()
            if action == "create":
                title = kwargs.get("title")
                cursor.execute(
                    "INSERT INTO notes (title, content, tags, created, updated) VALUES (?, ?, ?, ?, ?)",
                    (title, kwargs.get("content"), kwargs.get("tags"), now, now)
                )
                conn.commit()
                return ToolResult(success=True, output=f"Note '{title}' saved.")

            elif action == "search":
                query = kwargs.get("query")
                cursor.execute("SELECT title, content FROM notes WHERE title LIKE ? OR content LIKE ?", (f"%{query}%", f"%{query}%"))
                rows = cursor.fetchall()
                results = [{"title": r[0], "content": r[1][:100] + "..."} for r in rows]
                return ToolResult(success=True, output=json.dumps(results, indent=2))

            elif action == "list":
                cursor.execute("SELECT title, tags FROM notes ORDER BY updated DESC")
                rows = cursor.fetchall()
                results = [{"title": r[0], "tags": r[1]} for r in rows]
                return ToolResult(success=True, output=json.dumps(results, indent=2))

            return ToolResult(success=False, output=None, error=f"Action {action} not implemented.")
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))
        finally:
            conn.close()
