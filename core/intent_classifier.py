import re
from typing import Tuple, Dict

INTENT_PATTERNS = {
    "music": [
      r"play\b", r"song\b", r"music\b", r"youtube\b",
      r"spotify\b", r"gaana\b", r"jiosaavn\b",
      r"put on\b", r"play.*on"
    ],
    "system": [
      r"open\b", r"launch\b", r"start\b", r"close\b",
      r"chrome\b", r"firefox\b", r"app\b",
      r"volume\b", r"mute\b", r"screenshot\b",
      r"lock\b", r"calculator\b"
    ],
    "weather": [
      r"weather\b", r"temperature\b", r"rain\b",
      r"sunny\b", r"forecast\b", r"hot\b", r"cold\b",
      r"climate\b", r"humid\b"
    ],
    "reminder": [
      r"remind\b", r"reminder\b", r"alert\b",
      r"don.t.*forget", r"notify\b", r"alarm\b"
    ],
    "email": [
        r"email\b", r"send.*email", r"email.*to", r"mail.*to", r"write.*email",
        r"compose.*email", r"check.*inbox", r"read.*mail"
    ],
    "whatsapp": [
        r"whatsapp", r"send.*message.*to", r"message.*on whatsapp",
        r"text.*on whatsapp", r"wa.*to"
    ],
    "sms": [
        r"send.*sms", r"text message.*to", r"sms.*to"
    ],
    "calendar": [
        r"schedule", r"book.*meeting", r"add.*calendar", r"what.*today",
        r"my schedule", r"upcoming.*events", r"meeting.*at"
    ],
    "notes": [
        r"note this", r"note down", r"save this", r"remember this",
        r"write.*down", r"jot.*down", r"make.*note"
    ],
    "translate": [
        r"translate", r"how do you say", r"in.*language", r"meaning in"
    ],
    "calculator": [
        r"calculate", r"what is.*\d", r"how much is", r"percent",
        r"equals", r"\d+.*\+.*\d+", r"\d+.*\-.*\d+", r"sum of"
    ],
    "contacts": [
        r"add.*contact", r"save.*number", r"find.*contact",
        r"what.*number", r"contact.*for"
    ],
    "web_search": [
        r"search", r"look up", r"find.*on google", r"google for", r"who is", r"what is"
    ],
    "conversation": [
        r"hey", r"hi", r"how are you", r"who are you", r"what can you"
    ]
}

class IntentClassifier:
    def classify(self, text: str) -> str:
        if not text:
            return "conversation"

        text_lower = text.lower().strip()

        # Score-based classification — most specific first
        scores = {}

        for intent, patterns in INTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                try:
                    if re.search(pattern, text_lower):
                        score += 1
                except re.error:
                    continue
            if score > 0:
                scores[intent] = score

        if not scores:
            return "conversation"

        # Return intent with highest score
        return max(scores, key=scores.get)

    def needs_clarification(self, text: str, intent: str) -> Tuple[bool, str]:
        """Check if intent requires missing information."""
        text = text.lower()
        
        if intent == "email":
            if "@" not in text and "to" not in text:
                return True, "Who should I send this email to?"
        
        elif intent == "whatsapp" or intent == "sms":
            if not any(char.isdigit() for char in text) and "to" not in text and "message" not in text:
                return True, "Who do you want to message?"
                
        elif intent == "reminder":
            if not any(kw in text for kw in ["at", "by", "in", "tomorrow", "tonight"]):
                return True, "When do you want me to remind you?"
                
        elif intent == "calendar":
            if not any(kw in text for kw in ["at", "on", "tomorrow", "schedule"]):
                return True, "What time should I schedule this for?"
                
        return False, ""

    def get_confidence(self, text: str, intent: str) -> float:
        """Return ratio of matched to total patterns for that intent."""
        if intent not in INTENT_PATTERNS or not INTENT_PATTERNS[intent]:
            return 0.0
            
        text = text.lower()
        matches = 0
        for pattern in INTENT_PATTERNS[intent]:
            if re.search(pattern, text):
                matches += 1
        
        return matches / len(INTENT_PATTERNS[intent])
