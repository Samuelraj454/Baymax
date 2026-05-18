from .base_tool import BaseTool, ToolResult
import datetime
from loguru import logger

class WhatsAppTool(BaseTool):
    name = "whatsapp"
    description = "Send WhatsApp messages instantly or scheduled."
    schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["send", "send_to_contact"]},
            "phone": {"type": "string", "description": "Phone number with country code"},
            "name": {"type": "string", "description": "Contact name"},
            "message": {"type": "string"},
            "hour": {"type": "integer"},
            "minute": {"type": "integer"}
        },
        "required": ["action", "message"]
    }

    def run(self, action: str, message: str, **kwargs) -> ToolResult:
        try:
            import pywhatkit
            phone = kwargs.get("phone")
            
            if action == "send_to_contact":
                # Contact lookup logic would go here
                return ToolResult(success=False, output=None, error="Contact lookup not implemented yet.")

            if not phone:
                return ToolResult(success=False, output=None, error="Phone number required for 'send' action.")

            hour = kwargs.get("hour")
            minute = kwargs.get("minute")

            if hour is not None and minute is not None:
                pywhatkit.sendwhatmsg(phone, message, hour, minute, wait_time=15)
                return ToolResult(success=True, output=f"Scheduled WhatsApp to {phone} at {hour}:{minute}")
            else:
                pywhatkit.sendwhatmsg_instantly(phone, message, wait_time=15, tab_close=True)
                return ToolResult(success=True, output=f"WhatsApp sent instantly to {phone}")

        except Exception as e:
            logger.error(f"WhatsApp Error: {e}")
            return ToolResult(success=False, output=None, error=str(e))
