from .base_tool import BaseTool, ToolResult
from .reminder_tool import ReminderTool
from .file_tool import FileTool
from .web_tool import WebTool
from .system_tool import SystemTool
from .email_tool import EmailTool
from .whatsapp_tool import WhatsAppTool
from .sms_tool import SMSTool
from .contacts_tool import ContactsTool
from .calendar_tool import CalendarTool
from .notes_tool import NotesTool
from .news_tool import NewsTool
from .calculator_tool import CalculatorTool
from .translate_tool import TranslateTool
from .clipboard_tool import ClipboardTool
from .voice_settings_tool import VoiceSettingsTool

TOOL_REGISTRY = {
    "reminder":   ReminderTool(),
    "file_ops":   FileTool(),
    "web_fetch":  WebTool(),
    "system":     SystemTool(),
    "email":      EmailTool(),
    "whatsapp":   WhatsAppTool(),
    "sms":        SMSTool(),
    "contacts":   ContactsTool(),
    "calendar":   CalendarTool(),
    "notes":      NotesTool(),
    "news":       NewsTool(),
    "calculator": CalculatorTool(),
    "translate":  TranslateTool(),
    "clipboard":  ClipboardTool(),
    "voice_settings": VoiceSettingsTool(),
}

__all__ = [
    "BaseTool", "ToolResult", "ReminderTool", "FileTool", "WebTool", "SystemTool",
    "EmailTool", "WhatsAppTool", "SMSTool", "ContactsTool", "CalendarTool",
    "NotesTool", "NewsTool", "CalculatorTool", "TranslateTool", "ClipboardTool",
    "VoiceSettingsTool", "TOOL_REGISTRY"
]
