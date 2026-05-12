from .base_tool import BaseTool, ToolResult
from simpleeval import simple_eval
import re

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Safely evaluate math expressions and percentages."
    schema = {
        "type": "object",
        "properties": {
            "expression": {"type": "string"}
        },
        "required": ["expression"]
    }

    def run(self, expression: str, **kwargs) -> ToolResult:
        try:
            # Handle percentage: "15% of 2500" -> "0.15 * 2500"
            expr = expression.lower()
            expr = re.sub(r'(\d+)% of (\d+)', r'(\1/100) * \2', expr)
            expr = expr.replace('%', '/100')
            
            result = simple_eval(expr)
            return ToolResult(success=True, output=f"Result: {result}")
        except Exception as e:
            return ToolResult(success=False, output=None, error=f"Invalid expression: {str(e)}")
