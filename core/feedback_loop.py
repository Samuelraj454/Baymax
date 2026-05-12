import sqlite3
import datetime
import json
from typing import Optional, Any, Dict
from app_config import DB_PATH

class FeedbackLoop:
    def __init__(self):
        self.db_path = DB_PATH

    def record_outcome(self, tool_name: str, args: Dict, success: bool, user_corrected: bool = False):
        """Log the result of a tool execution for learning."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO feedback_log (tool_name, args, success, user_corrected, timestamp) VALUES (?, ?, ?, ?, ?)",
            (tool_name, json.dumps(args), int(success), int(user_corrected), now)
        )
        conn.commit()
        conn.close()

    def get_tool_success_rate(self, tool_name: str) -> float:
        """Calculate success rate for a tool from last 50 calls."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT success FROM feedback_log WHERE tool_name = ? ORDER BY timestamp DESC LIMIT 50",
            (tool_name,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return 1.0 # Default to high confidence for new tools
            
        success_count = sum(row[0] for row in rows)
        return success_count / len(rows)

    def suggest_retry(self, tool_name: str) -> bool:
        """Decide if a retry is worth suggesting based on success history."""
        rate = self.get_tool_success_rate(tool_name)
        return rate > 0.5

    def log_user_preference(self, key: str, value: str):
        """Store or update user preferences (e.g., favorite music, common contacts)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()
        
        cursor.execute(
            "INSERT OR REPLACE INTO user_preferences (key, value, updated) VALUES (?, ?, ?)",
            (key, value, now)
        )
        conn.commit()
        conn.close()

    def get_preference(self, key: str) -> Optional[str]:
        """Retrieve a stored user preference."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM user_preferences WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else None
