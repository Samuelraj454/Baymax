from .base_tool import BaseTool, ToolResult


class ClipboardTool(BaseTool):
    name = "clipboard"
    description = "Copy to or paste from the system clipboard."
    schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["copy", "paste", "clear"]},
            "text": {"type": "string"}
        },
        "required": ["action"]
    }

    def run(self, action: str, text: str = None, **kwargs) -> ToolResult:
        try:
            import pyperclip
            if action == "copy":
                pyperclip.copy(text)
                return ToolResult(success=True, output=f"Copied to clipboard: {text[:50]}...")
            elif action == "paste":
                content = pyperclip.paste()
                return ToolResult(success=True, output=content)
            elif action == "clear":
                pyperclip.copy("")
                return ToolResult(success=True, output="Clipboard cleared.")
            
            return ToolResult(success=False, output=None, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))
