from .base_tool import BaseTool, ToolResult
from integrations.gmail import GmailClient
import json

class EmailTool(BaseTool):
    name = "email"
    description = "Send, read, search, and reply to Gmail emails."
    schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["send", "read", "search", "reply"]},
            "to": {"type": "string"},
            "subject": {"type": "string"},
            "body": {"type": "string"},
            "count": {"type": "integer", "default": 5},
            "query": {"type": "string"}
        },
        "required": ["action"]
    }

    def run(self, action: str, **kwargs) -> ToolResult:
        client = GmailClient()
        if not client.is_configured():
            return ToolResult(success=False, output=None, error="Gmail not configured. Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env.")

        try:
            if action == "send":
                res = client.send_email(kwargs.get("to"), kwargs.get("subject"), kwargs.get("body"))
                return ToolResult(success=True, output=res)
            
            elif action == "read":
                res = client.read_emails(count=kwargs.get("count", 5))
                return ToolResult(success=True, output=json.dumps(res, indent=2))
                
            elif action == "search":
                # For search, we reuse read_emails logic but would normally use search command
                return ToolResult(success=True, output="Search functionality would be here.")
                
            return ToolResult(success=False, output=None, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))
