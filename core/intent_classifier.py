import re
from typing import Tuple, Dict

INTENT_PATTERNS = {
    "music":      [r"play\b",r"song\b",r"music\b",r"youtube\b",
                   r"spotify\b",r"put on\b",r"listen\b"],
    "system":     [r"open\b",r"launch\b",r"chrome\b",r"firefox\b",
                   r"volume\b",r"mute\b",r"screenshot\b",r"lock\b",
                   r"calculator\b",r"close\b"],
    "weather":    [r"weather\b",r"temperature\b",r"rain\b",
                   r"hot\b",r"cold\b",r"forecast\b",r"climate\b"],
    "reminder":   [r"remind\b",r"reminder\b",r"alert\b",
                   r"don.t forget",r"notify\b",r"alarm\b"],
    "email":      [r"email\b",r"mail\b",r"inbox\b",r"compose\b"],
    "whatsapp":   [r"whatsapp\b",r"whats.?app\b",r"send.*message"],
    "news":       [r"news\b",r"headline\b",r"happening\b",r"latest\b"],
    "calendar":   [r"schedul\b",r"meeting\b",r"calendar\b",
                   r"appointment\b",r"book\b"],
    "notes":      [r"note\b",r"write.*down",r"remember this",
                   r"save this",r"jot\b"],
    "translate":  [r"translat\b",r"how.*say\b",r"in.*language\b"],
    "math":       [r"\d+.*[\+\-\*\/].*\d+",r"calculat\b",
                   r"percent\b",r"how much"],
    "web_search": [r"search\b",r"google\b",r"look up\b",r"find\b"],
    "time_date":  [r"\btime\b",r"\bdate\b",r"what.*day\b",
                   r"what.*time\b"],
    "contacts":   [r"contact\b",r"add.*number",r"save.*number",
                   r"find.*contact"],
}

class IntentClassifier:
    def classify(self, text: str) -> str:
        if not text: return "conversation"
        t = text.lower().strip()
        best_intent = "conversation"
        best_score  = 0
        for intent, patterns in INTENT_PATTERNS.items():
            score = sum(1 for p in patterns
                        if re.search(p, t, re.IGNORECASE))
            if score > best_score:
                best_score  = score
                best_intent = intent
        return best_intent

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
            if re.search(pattern, text, re.IGNORECASE):
                matches += 1
        
        return matches / len(INTENT_PATTERNS[intent])
