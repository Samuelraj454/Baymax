from .base_tool import BaseTool, ToolResult
import os

class FileTool(BaseTool):
    name = "file_ops"
    description = "Read, write, append, or list files."
    schema = {
        "type": "object",
        "properties": {
            "operation": {"type": "string", "enum": ["read", "write", "append", "list"]},
            "path": {"type": "string"},
            "content": {"type": "string"}
        },
        "required": ["operation", "path"]
    }

    def run(self, operation: str, path: str, content: str = "", **kwargs) -> ToolResult:
        try:
            if operation == "write":
                os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                return ToolResult(success=True, output=f"Successfully wrote to {path}")
            
            elif operation == "append":
                os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
                with open(path, "a", encoding="utf-8") as f:
                    f.write(content)
                return ToolResult(success=True, output=f"Successfully appended to {path}")
                
            elif operation == "read":
                if not os.path.exists(path):
                    return ToolResult(success=False, output=None, error=f"File {path} not found.")
                with open(path, "r", encoding="utf-8") as f:
                    data = f.read()
                return ToolResult(success=True, output=data)
                
            elif operation == "list":
                if not os.path.isdir(path):
                    return ToolResult(success=False, output=None, error=f"Directory {path} not found.")
                items = os.listdir(path)
                return ToolResult(success=True, output="\n".join(items))
                
            return ToolResult(success=False, output=None, error=f"Unknown operation: {operation}")
            
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))
