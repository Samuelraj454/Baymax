from .base_tool import BaseTool, ToolResult

class VoiceSettingsTool(BaseTool):
    name = "voice_settings"
    description = "Change BAYMAX voice, language, speed, pitch, and volume."
    schema = {
        "required": ["action"],
        "properties": {
            "action": {
                "type": "string",
                "description": "Action to perform: set_voice, set_language, set_rate, set_pitch, set_volume, get_settings"
            },
            "voice_id": {
                "type": "string",
                "description": "Voice ID to switch to"
            },
            "language_code": {
                "type": "string",
                "description": "Language code to switch to, e.g., en-IN, hi-IN"
            },
            "value": {
                "type": "number",
                "description": "Numeric value for rate, pitch, or volume"
            }
        }
    }

    def __init__(self, user_profile=None):
        self.user_profile = user_profile

    def run(self, action: str, **kwargs) -> ToolResult:
        if not self.user_profile:
            return ToolResult(success=False, error="UserProfile not initialized in VoiceSettingsTool")

        if action == "set_voice":
            voice_id = kwargs.get("voice_id")
            if voice_id:
                self.user_profile.set("preferred_voice_id", voice_id, "preferences")
                return ToolResult(success=True, output=self.user_profile.get_voice_settings())
            return ToolResult(success=False, error="voice_id required")

        elif action == "set_language":
            lang = kwargs.get("language_code")
            if lang:
                self.user_profile.set("user_language", lang, "identity")
                return ToolResult(success=True, output=self.user_profile.get_voice_settings())
            return ToolResult(success=False, error="language_code required")

        elif action == "set_rate":
            val = kwargs.get("value")
            if val is not None:
                self.user_profile.set("preferred_voice_rate", str(val), "preferences")
                return ToolResult(success=True, output=self.user_profile.get_voice_settings())
            return ToolResult(success=False, error="value required")

        elif action == "set_pitch":
            val = kwargs.get("value")
            if val is not None:
                self.user_profile.set("preferred_voice_pitch", str(val), "preferences")
                return ToolResult(success=True, output=self.user_profile.get_voice_settings())
            return ToolResult(success=False, error="value required")

        elif action == "set_volume":
            val = kwargs.get("value")
            if val is not None:
                self.user_profile.set("preferred_voice_volume", str(val), "preferences")
                return ToolResult(success=True, output=self.user_profile.get_voice_settings())
            return ToolResult(success=False, error="value required")

        elif action == "get_settings":
            return ToolResult(success=True, output=self.user_profile.get_voice_settings())

        return ToolResult(success=False, error=f"Unknown action {action}")
