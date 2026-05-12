from .base_tool import BaseTool, ToolResult
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

# Shared scheduler for the application
scheduler = BackgroundScheduler()
scheduler.start()

class ReminderTool(BaseTool):
    name = "reminder"
    description = "Set a scheduled reminder for the user."
    schema = {
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "time": {"type": "string", "description": "ISO 8601 datetime"}
        },
        "required": ["message", "time"]
    }

    def run(self, message: str, time: str, **kwargs) -> ToolResult:
        try:
            # Handle Z suffix for UTC
            iso_time = time.replace('Z', '+00:00')
            dt = datetime.fromisoformat(iso_time)
            
            now = datetime.now(timezone.utc) if dt.tzinfo else datetime.now()
            
            if dt < now:
                return ToolResult(success=False, output=None, error="This time has already passed.")
                
            # For now, we log it. In a real OS integration, this would trigger a notification.
            scheduler.add_job(
                lambda msg=message: logger.info(f"REMINDER TRIGGERED: {msg}"), 
                'date', 
                run_date=dt
            )
            
            return ToolResult(
                success=True, 
                output=f"I've scheduled that for {dt.strftime('%H:%M:%S')}. Message: '{message}'"
            )
        except ValueError:
            return ToolResult(success=False, output=None, error="Invalid ISO 8601 time format.")
