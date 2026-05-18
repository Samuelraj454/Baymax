import sqlite3
import os
import json
from datetime import datetime
from loguru import logger

class UserProfile:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_db()
        self.profile = {}
        self.load_all()

    def _ensure_db_dir(self):
        dir_name = os.path.dirname(self.db_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_profile (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        category TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to init user_profile db: {e}")

    def load_all(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT key, value FROM user_profile')
                rows = cursor.fetchall()
                for key, value in rows:
                    self.profile[key] = value
        except Exception as e:
            logger.error(f"Failed to load user profile: {e}")

    def get(self, key: str, default=None) -> str:
        return self.profile.get(key, default)

    def set(self, key: str, value: str, category: str = "preferences"):
        value_str = str(value)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO user_profile (key, value, category, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (key, value_str, category, datetime.now().isoformat()))
                conn.commit()
            self.profile[key] = value_str
            logger.info(f"UserProfile update: {key} = {value_str}")
        except Exception as e:
            logger.error(f"Failed to save to user profile: {e}")

    def get_all(self, category: str = None) -> dict:
        if not category:
            return self.profile.copy()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT key, value FROM user_profile WHERE category = ?', (category,))
                return {k: v for k, v in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Failed to get category {category}: {e}")
            return {}

    def learn_from_conversation(self, text: str, entities: dict):
        text_lower = text.lower()
        # Simple heuristic extraction
        if "my name is" in text_lower:
            parts = text_lower.split("my name is")
            if len(parts) > 1:
                name = parts[1].strip().split()[0].capitalize()
                self.set("user_name", name, "identity")
        elif "call me" in text_lower:
            parts = text_lower.split("call me")
            if len(parts) > 1:
                name = parts[1].strip().split()[0].capitalize()
                self.set("user_name", name, "identity")
        elif "i'm from" in text_lower:
            parts = text_lower.split("i'm from")
            if len(parts) > 1:
                city = parts[1].strip().split()[0].capitalize()
                self.set("user_city", city, "identity")
        elif "i live in" in text_lower:
            parts = text_lower.split("i live in")
            if len(parts) > 1:
                city = parts[1].strip().split()[0].capitalize()
                self.set("user_city", city, "identity")

        if entities:
            # entities might contain resolved contacts
            if "phone" in entities and "name" in entities:
                self.set(f"{entities['name'].lower()}_phone", entities["phone"], "contacts")
            if "email" in entities and "name" in entities:
                self.set(f"{entities['name'].lower()}_email", entities["email"], "contacts")

    def build_context_string(self) -> str:
        from app_config import DEFAULT_CITY, DEFAULT_COUNTRY, DEFAULT_TIMEZONE

        name     = self.get("user_name",    "the user")
        city     = self.get("user_city",    DEFAULT_CITY)
        country  = self.get("user_country", DEFAULT_COUNTRY)
        lang     = self.get("user_language", "en-IN")
        timezone = self.get("user_timezone", DEFAULT_TIMEZONE)
        music    = self.get("preferred_music_genre",   "top hits")
        news_cat = self.get("preferred_news_category", "general")

        # Build contacts string dynamically
        contacts = []
        for k, v in self.profile.items():
            if k.endswith("_phone") or k.endswith("_email"):
                contacts.append(f"{k.replace('_phone', '').replace('_email', '')}={v}")
        contacts_str = ", ".join(contacts) if contacts else "none saved yet"

        return (
            f"User's name: {name}. "
            f"City: {city}. "
            f"Country: {country}. "
            f"Language: {lang}. "
            f"Timezone: {timezone}. "
            f"Preferred music: {music}. "
            f"News category: {news_cat}. "
            f"Known contacts: {contacts_str}. "
            f"IMPORTANT: Always use {city} as default city for weather. "
            f"Never ask for city again — it is {city}."
        )

    def get_voice_settings(self) -> dict:
        return {
            "voice_id":  self.get("preferred_voice_id", "jarvis"),
            "rate":      float(self.get("preferred_voice_rate", "1.05")),
            "pitch":     float(self.get("preferred_voice_pitch", "0.85")),
            "volume":    float(self.get("preferred_voice_volume", "1.0")),
            "language":  self.get("user_language", "en-IN")
        }

    def get_language_config(self) -> dict:
        lang = self.get("user_language", "en-IN")
        configs = {
            "en-IN": {
                "speech_lang":  "en-IN",
                "llm_lang":     "English",
                "greeting":     "Hey",
                "weather_city": self.get("user_city", "Hyderabad")
            },
            "hi-IN": {
                "speech_lang":  "hi-IN",
                "llm_lang":     "Hindi",
                "greeting":     "नमस्ते",
                "weather_city": self.get("user_city", "Hyderabad")
            },
            "te-IN": {
                "speech_lang":  "te-IN",
                "llm_lang":     "Telugu",
                "greeting":     "నమస్కారం",
                "weather_city": self.get("user_city", "Hyderabad")
            },
            "ta-IN": {
                "speech_lang":  "ta-IN",
                "llm_lang":     "Tamil",
                "greeting":     "வணக்கம்",
                "weather_city": self.get("user_city", "Hyderabad")
            },
            "kn-IN": {
                "speech_lang":  "kn-IN",
                "llm_lang":     "Kannada",
                "greeting":     "ನಮಸ್ಕಾರ",
                "weather_city": self.get("user_city", "Hyderabad")
            },
            "mr-IN": {
                "speech_lang":  "mr-IN",
                "llm_lang":     "Marathi",
                "greeting":     "नमस्कार",
                "weather_city": self.get("user_city", "Hyderabad")
            },
        }
        return configs.get(lang, configs["en-IN"])
