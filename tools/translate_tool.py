from .base_tool import BaseTool, ToolResult
from deep_translator import GoogleTranslator
from loguru import logger

class TranslateTool(BaseTool):
    name = "translate"
    description = "Translate text between any languages (free)."
    schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "to_language": {"type": "string"},
            "from_language": {"type": "string", "default": "auto"}
        },
        "required": ["text", "to_language"]
    }

    def run(self, text: str, to_language: str, from_language: str = "auto", **kwargs) -> ToolResult:
        try:
            # Common language mapping
            lang_map = {
                "hindi": "hi", "telugu": "te", "tamil": "ta", "french": "fr", 
                "spanish": "es", "german": "de", "japanese": "ja", 
                "chinese": "zh-CN", "arabic": "ar", "russian": "ru"
            }
            
            target = lang_map.get(to_language.lower(), to_language)
            source = lang_map.get(from_language.lower(), from_language)

            translated = GoogleTranslator(source=source, target=target).translate(text)
            return ToolResult(success=True, output=translated)
        except Exception as e:
            logger.error(f"Translation Error: {e}")
            return ToolResult(success=False, output=None, error=str(e))
