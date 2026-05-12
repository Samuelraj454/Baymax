import datetime
import sqlite3
import json
from typing import Optional, List, Dict, Any
from app_config import DB_PATH
from tools import TOOL_REGISTRY

class ProactiveEngine:
    def __init__(self, long_mem=None):
        self.db_path = DB_PATH
        self.long_mem = long_mem

    def check_morning_briefing(self, session_id: str) -> Optional[str]:
        """Generate a briefing if this is the first interaction of the day."""
        # Check last interaction
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT timestamp FROM memories WHERE session_id = ? ORDER BY timestamp DESC LIMIT 1",
            (session_id,)
        )
        row = cursor.fetchone()
        
        now = datetime.datetime.now()
        if row:
            last_ts = datetime.datetime.fromisoformat(row[0].replace('Z', '+00:00'))
            # If last interaction was more than 6 hours ago and it's currently morning (5am-12pm)
            if (now.astimezone() - last_ts).total_seconds() < 21600:
                conn.close()
                return None
        
        if not (5 <= now.hour <= 12):
            conn.close()
            return None

        # Build briefing
        briefing = ["Good morning! Here's your briefing for today."]
        
        # 1. Weather (from tools)
        weather_tool = TOOL_REGISTRY.get("weather")
        if weather_tool:
            try:
                # Use a default city or look up from preferences
                cursor.execute("SELECT value FROM user_preferences WHERE key = 'city'")
                pref_city = cursor.fetchone()
                city = pref_city[0] if pref_city else "Hyderabad"
                res = weather_tool.run(city=city)
                if res.success:
                    briefing.append(f"The weather in {city} is {res.output}.")
            except:
                pass
                
        # 2. Calendar
        cal_tool = TOOL_REGISTRY.get("calendar")
        if cal_tool:
            try:
                res = cal_tool.run(action="list", date=now.date().isoformat())
                if res.success and isinstance(res.output, list) and len(res.output) > 0:
                    count = len(res.output)
                    briefing.append(f"You have {count} events on your calendar today.")
                else:
                    briefing.append("Your calendar is clear for today.")
            except:
                pass
                
        # 3. News
        news_tool = TOOL_REGISTRY.get("news")
        if news_tool:
            try:
                res = news_tool.run(query="top headlines")
                if res.success and isinstance(res.output, list) and len(res.output) > 0:
                    top_story = res.output[0].get("title")
                    briefing.append(f"Top story today: {top_story}.")
            except:
                pass
        
        conn.close()
        return " ".join(briefing)

    def suggest_followup(self, last_tool: str, last_args: Dict, result: Any) -> Optional[str]:
        """Suggest a logical next step after a tool completes."""
        if last_tool == "email":
            return "Want me to add a follow-up reminder for this?"
        elif last_tool == "reminder":
            return "Should I also block that time on your calendar?"
        elif last_tool == "notes":
            return "Want me to set a reminder to review this note later?"
        elif last_tool == "calendar":
            return "Want me to message the other people involved?"
        return None

    def detect_pattern(self, session_history: List[Dict]) -> Optional[str]:
        """Identify repeated behavior and offer to automate it."""
        # Simple pattern: same tool used multiple times in short succession
        if len(session_history) < 3:
            return None
            
        # Example: if user checked news multiple times, offer to make it a morning briefing
        news_calls = [h for h in session_history if "news" in h.get("content", "").lower()]
        if len(news_calls) >= 2:
            return "I noticed you check the news often. Want me to include it in your morning briefing?"
            
        return None

    def check_pending_reminders(self) -> List[str]:
        """Check for reminders due in the next 60 seconds."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.datetime.now().isoformat()
        soon = (datetime.datetime.now() + datetime.timedelta(minutes=1)).isoformat()
        
        # This assumes a 'reminders' table exists from a reminder tool
        try:
            cursor.execute(
                "SELECT id, message FROM reminders WHERE time >= ? AND time <= ? AND notified = 0",
                (now, soon)
            )
            rows = cursor.fetchall()
            
            alerts = []
            for row in rows:
                alerts.append(f"Reminder: {row[1]}")
                cursor.execute("UPDATE reminders SET notified = 1 WHERE id = ?", (row[0],))
            
            conn.commit()
            return alerts
        except:
            return []
        finally:
            conn.close()
