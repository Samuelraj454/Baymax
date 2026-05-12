from .base_tool import BaseTool, ToolResult
import httpx

class WebTool(BaseTool):
    name = "web_fetch"
    description = "Fetch data from a URL via GET or POST."
    schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "method": {"type": "string", "enum": ["GET", "POST"]},
            "payload": {"type": "object"}
        },
        "required": ["url"]
    }

    def run(self, url: str, method: str = "GET", payload: dict = None, **kwargs) -> ToolResult:
        try:
            with httpx.Client() as client:
                if method.upper() == "POST":
                    response = client.post(url, json=payload)
                else:
                    response = client.get(url)
                    
                response.raise_for_status()
                text = response.text
                if len(text) > 4000:
                    text = text[:4000] + "... [truncated]"
                return ToolResult(success=True, output=text)
        except httpx.HTTPStatusError as e:
            return ToolResult(success=False, output=None, error=f"HTTP Error {e.response.status_code}")
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))
