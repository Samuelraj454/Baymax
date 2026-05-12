import sys
import os
sys.path.append(os.getcwd())

from tools import EmailTool, WhatsAppTool, NotesTool, NewsTool, ToolResult

def test_tool(tool_instance, **kwargs):
    print(f"Testing {tool_instance.name}...")
    # Most tools use 'action' as a required kwarg in their run() for v4
    # We pass it through kwargs if needed
    result = tool_instance.run(**kwargs)
    
    print(f"Result Type: {type(result)}")
    print(f"Success: {result.success}")
    print(f"Output: {result.output}")
    print(f"Error: {result.error}")
    
    assert isinstance(result, ToolResult), f"{tool_instance.name} did not return a ToolResult object!"
    print("-" * 30)

# 1. News Tool (RSS Fallback)
test_tool(NewsTool(), action="top")

# 2. Notes Tool
test_tool(NotesTool(), action="create", title="Verification Note", content="System v4.0 functional.")

# 3. Email Tool (Expected to fail if no .env keys, but must return ToolResult)
test_tool(EmailTool(), action="read")

# 4. WhatsApp Tool (Test validation failure to avoid opening browser)
test_tool(WhatsAppTool(), action="send", message="Hello", phone="")

print("\nSUCCESS: All tools verified to return proper ToolResult objects.")
