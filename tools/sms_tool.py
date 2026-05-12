from .base_tool import BaseTool, ToolResult
from integrations.twilio_client import TwilioClient
import json

class SMSTool(BaseTool):
    name = "sms"
    description = "Send SMS messages via Twilio."
    schema = {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "Recipient phone number"},
            "message": {"type": "string"}
        },
        "required": ["to", "message"]
    }

    def run(self, to: str, message: str, **kwargs) -> ToolResult:
        client = TwilioClient()
        res = client.send_sms(to, message)
        if isinstance(res, dict):
            return ToolResult(success=True, output=json.dumps(res))
        return ToolResult(success=False, output=None, error=res)
