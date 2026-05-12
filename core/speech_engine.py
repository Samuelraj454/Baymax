from typing import Dict, Any

class SpeechEngine:
    def __init__(self):
        self.task_started = {
            "email":     "Alright, sending that email to {to} now.",
            "whatsapp":  "Messaging {phone} on WhatsApp.",
            "sms":       "Sending that text to {to}.",
            "reminder":  "Got it. I'll remind you at {time}.",
            "calendar":  "Booking that in — {title} at {time}.",
            "notes":     "Noted. Saving that for you.",
            "weather":   "Checking the weather in {city}.",
            "news":      "Pulling up today's headlines.",
            "music":     "Playing {query} for you.",
            "system":    "On it.",
            "translate": "Translating to {to_language}.",
            "calculator":"Quick math.",
            "contacts":  "Adding {name} to your contacts.",
            "web_search":"Searching for {query}.",
            "file_ops":  "Working on that file.",
        }

        self.task_done = {
            "email":     "Email sent to {to}.",
            "whatsapp":  "Message sent to {phone}.",
            "sms":       "Text sent to {to}.",
            "reminder":  "Reminder set. I'll get you at {time}.",
            "calendar":  "{title} is on your calendar at {time}.",
            "notes":     "Saved as '{title}'.",
            "weather":   "{result}",
            "news":      "Here's what's happening: {result}",
            "music":     "Opening {query} on Spotify.",
            "translate": "{text} in {to_language} is: {result}",
            "calculator":"{expression} equals {result}.",
            "contacts":  "{name} added to your contacts.",
            "file_ops":  "Done.",
        }

        self.task_failed = {
            "email":     "I couldn't send that email. {error}",
            "whatsapp":  "WhatsApp message didn't go through. {error}",
            "sms":       "Text message failed. {error}",
            "reminder":  "I couldn't set that reminder. {error}",
            "calendar":  "I couldn't add that to your calendar. {error}",
            "notes":     "I couldn't save the note. {error}",
            "weather":   "I couldn't get the weather update right now — {error}",
            "default":   "I'm sorry, that didn't work. {error} Should I try again?",
        }

        self.missing_info = {
            "to":       "Who should I send this to?",
            "message":  "What do you want to say?",
            "subject":  "What's the subject?",
            "time":     "What time?",
            "title":    "What should I call this?",
            "name":     "What's the name?",
            "phone":    "What's the phone number?",
            "city":     "Which city?",
            "query":    "What should I search for?",
            "text":     "What do you want to translate?",
            "language": "What language?",
            "expression":"What do you want me to calculate?",
        }

    def announce_start(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Return speech string for starting a task."""
        template = self.task_started.get(tool_name, self.task_started.get("system"))
        try:
            return template.format(**args)
        except KeyError:
            return template

    def announce_result(self, tool_name: str, args: Dict[str, Any], result: Any) -> str:
        """Return speech string for a successful task."""
        template = self.task_done.get(tool_name, "Task complete.")
        formatted_result = self.format_result_for_speech(tool_name, result)
        
        # Merge args and result for formatting
        data = {**args, "result": formatted_result}
        try:
            return template.format(**data)
        except KeyError:
            return template

    def announce_failure(self, tool_name: str, error: str) -> str:
        """Return speech string for a failed task."""
        template = self.task_failed.get(tool_name, self.task_failed.get("default"))
        try:
            return template.format(error=error)
        except KeyError:
            return template

    def ask_for_missing(self, field_name: str) -> str:
        """Return a natural question for a missing field."""
        return self.missing_info.get(field_name, f"I need a bit more info — what is the {field_name}?")

    def confirm_heard(self, transcript: str) -> str:
        """Confirm what was heard when confidence is low."""
        return f"I heard: {transcript}. Is that right?"

    def format_result_for_speech(self, tool_name: str, raw_result: Any) -> str:
        """Simplify tool output for voice reading."""
        if not raw_result:
            return ""
            
        if tool_name == "news":
            if isinstance(raw_result, list):
                titles = [r.get("title") for r in raw_result[:3] if r.get("title")]
                return "Here are the top stories: " + "... and ... ".join(titles)
        
        if tool_name == "weather":
            return str(raw_result) # Usually already short
            
        if tool_name == "calendar":
            if isinstance(raw_result, list):
                count = len(raw_result)
                titles = [r.get("title") for r in raw_result[:3]]
                res = f"You have {count} events. "
                if titles:
                    res += "... then ...".join(titles)
                return res

        if isinstance(raw_result, (dict, list)):
            return "Task completed successfully."
            
        # Truncate long text
        res_str = str(raw_result)
        if len(res_str) > 200:
            return res_str[:197] + "... Want the full details?"
            
        return res_str
