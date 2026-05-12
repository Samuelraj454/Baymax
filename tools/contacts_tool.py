from .base_tool import BaseTool, ToolResult
import sqlite3
import datetime
from app_config import DB_PATH
import json

class ContactsTool(BaseTool):
    name = "contacts"
    description = "Manage personal contacts (add, find, list, delete)."
    schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["add", "find", "list", "delete"]},
            "name": {"type": "string"},
            "phone": {"type": "string"},
            "email": {"type": "string"},
            "notes": {"type": "string"}
        },
        "required": ["action"]
    }

    def __init__(self):
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                notes TEXT,
                created TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def run(self, action: str, **kwargs) -> ToolResult:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            if action == "add":
                name = kwargs.get("name")
                now = datetime.datetime.now().isoformat()
                cursor.execute(
                    "INSERT INTO contacts (name, phone, email, notes, created) VALUES (?, ?, ?, ?, ?)",
                    (name, kwargs.get("phone"), kwargs.get("email"), kwargs.get("notes"), now)
                )
                conn.commit()
                return ToolResult(success=True, output=f"Added contact: {name}")

            elif action == "find":
                name = kwargs.get("name")
                cursor.execute("SELECT name, phone, email, notes FROM contacts WHERE name LIKE ?", (f"%{name}%",))
                rows = cursor.fetchall()
                results = [{"name": r[0], "phone": r[1], "email": r[2], "notes": r[3]} for r in rows]
                return ToolResult(success=True, output=json.dumps(results, indent=2))

            elif action == "list":
                cursor.execute("SELECT name, phone, email FROM contacts ORDER BY name")
                rows = cursor.fetchall()
                results = [{"name": r[0], "phone": r[1], "email": r[2]} for r in rows]
                return ToolResult(success=True, output=json.dumps(results, indent=2))

            return ToolResult(success=False, output=None, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))
        finally:
            conn.close()
