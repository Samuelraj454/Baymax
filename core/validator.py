import re
import datetime
from typing import Tuple, Dict, Any

class Validator:
    def validate_email_args(self, args: Dict) -> Tuple[bool, str]:
        """Check for valid email components."""
        email = args.get("to")
        if not email or "@" not in email or "." not in email:
            return False, "Invalid email address."
        if not args.get("subject"):
            return False, "Subject is required."
        if not args.get("body") or len(args.get("body")) < 2:
            return False, "Email body is too short or empty."
        return True, ""

    def validate_phone_number(self, phone: Any) -> Tuple[bool, str]:
        """Check for valid phone format (10+ digits)."""
        if not phone:
            return False, "Phone number is missing."
        
        # Strip common formatting
        clean_phone = str(phone).replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if clean_phone.startswith("+"):
            if len(clean_phone) >= 11 and clean_phone[1:].isdigit():
                return True, clean_phone
        elif len(clean_phone) >= 10 and clean_phone.isdigit():
            return True, clean_phone
            
        return False, "Invalid phone number format."

    def validate_datetime(self, dt_string: str) -> Tuple[bool, str]:
        """Ensure date is ISO 8601 and in the future."""
        try:
            dt = datetime.datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            now = datetime.datetime.now(dt.tzinfo)
            if dt < now:
                return False, "The specified time is in the past."
            return True, ""
        except ValueError:
            return False, "Invalid date/time format. Must be ISO 8601."

    def validate_tool_specific(self, tool_name: str, args: Dict) -> Tuple[bool, str]:
        """Route to specific validator based on tool name."""
        if tool_name == "email":
            return self.validate_email_args(args)
        elif tool_name in ["whatsapp", "sms"]:
            phone = args.get("phone") or args.get("to")
            return self.validate_phone_number(phone)
        elif tool_name in ["reminder", "calendar"]:
            time_val = args.get("time") or args.get("start")
            if time_val:
                return self.validate_datetime(time_val)
        
        return True, "" # Default pass for other tools
