from .base_tool import BaseTool, ToolResult
import sqlite3
import datetime
from app_config import DB_PATH
from integrations.google_calendar import GoogleCalendarClient
import json

class CalendarTool(BaseTool):
    name = "calendar"
    description = "Manage calendar events (create, list, today)."
    schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["create", "list", "today", "delete"]},
            "title": {"type": "string"},
            "start": {"type": "string", "description": "ISO datetime"},
            "end": {"type": "string", "description": "ISO datetime"},
            "description": {"type": "string"},
            "location": {"type": "string"}
        },
        "required": ["action"]
    }

    def __init__(self):
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                location TEXT,
                created TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def run(self, action: str, **kwargs) -> ToolResult:
        gclient = GoogleCalendarClient()
        
        # Local fallback logic
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            if action == "create":
                title = kwargs.get("title")
                start = kwargs.get("start")
                now = datetime.datetime.now().isoformat()
                cursor.execute(
                    "INSERT INTO events (title, description, start_time, end_time, location, created) VALUES (?, ?, ?, ?, ?, ?)",
                    (title, kwargs.get("description"), start, kwargs.get("end"), kwargs.get("location"), now)
                )
                conn.commit()
                msg = f"Event '{title}' saved to local calendar."
                if gclient.is_configured():
                    msg += " " + gclient.create_event(title, start)
                return ToolResult(success=True, output=msg)

            elif action == "today":
                today = datetime.date.today().isoformat()
                cursor.execute("SELECT title, start_time, location FROM events WHERE start_time LIKE ?", (f"{today}%",))
                rows = cursor.fetchall()
                results = [{"title": r[0], "start": r[1], "location": r[2]} for r in rows]
                return ToolResult(success=True, output=json.dumps(results, indent=2))

            return ToolResult(success=False, output=None, error=f"Action {action} not fully implemented.")
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))
        finally:
            conn.close()
