import json
import re
import datetime
from typing import Optional, Dict, List, Tuple
from loguru import logger

class AccuracyEngine:
    def __init__(self, tool_registry=None):
        self.tool_registry = tool_registry

    def validate_json(self, raw_text: str) -> Optional[dict]:
        """Multi-layer JSON extraction with 4 fallback strategies."""
        if not raw_text:
            return None
            
        raw_text = raw_text.strip()
        
        # Strategy 1: Direct parse
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            pass

        # Strategy 2: Regex extract outermost { } block
        match = re.search(r'(\{.*\})', raw_text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                logger.info("AccuracyEngine: Strategy 2 (regex) succeeded")
                return data
            except json.JSONDecodeError:
                pass

        # Strategy 3: Find first { and last } manually
        start = raw_text.find('{')
        end = raw_text.rfind('}')
        if start != -1 and end != -1:
            try:
                data = json.loads(raw_text[start:end+1])
                logger.info("AccuracyEngine: Strategy 3 (manual slice) succeeded")
                return data
            except json.JSONDecodeError:
                pass

        # Strategy 4: Placeholder for LLM retry (handled in LLMCore)
        logger.warning("AccuracyEngine: All internal JSON extraction strategies failed")
        return None

    def validate_plan_args(self, steps: List[dict], tool_registry=None) -> Tuple[bool, List[str]]:
        """Check all required args are present and non-empty."""
        registry = tool_registry or self.tool_registry
        if not registry:
            return True, []
            
        issues = []
        for i, step in enumerate(steps):
            tool_name = step.get("tool")
            args = step.get("args", {})
            
            tool = registry.get(tool_name)
            if not tool:
                issues.append(f"Unknown tool: {tool_name}")
                continue
                
            # Check schema
            schema = getattr(tool, 'schema', {})
            required = schema.get("required", [])
            for field in required:
                if field not in args or args[field] in [None, "", "UNKNOWN", "null"]:
                    issues.append(f"missing: {field} field in {tool_name} step")
                    
        return len(issues) == 0, issues

    def extract_entities(self, text: str) -> dict:
        """Extract names, phones, emails, times, etc. with dedicated parsers."""
        entities = {
            "names": [],
            "phones": [],
            "emails": [],
            "times": [],
            "dates": [],
            "amounts": []
        }
        
        # Names: Capitalized words after "to", "for", "with"
        name_matches = re.findall(r'(?:to|for|with|message|email)\s+([A-Z][a-z]+)', text)
        entities["names"] = list(set(name_matches))
        
        # Phones: 10-digit or +91 format
        phone_matches = re.findall(r'(\+?\d[\d\s-]{8,12}\d)', text)
        entities["phones"] = [p.replace(" ", "").replace("-", "") for p in phone_matches]
        
        # Emails: standard pattern
        email_matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        entities["emails"] = email_matches
        
        # Times & Dates: Relative expressions
        time_expressions = ["tonight", "tomorrow", "today", "at", "by", "pm", "am", "morning", "night", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "next"]
        lower_text = text.lower()
        found_times = []
        for expr in time_expressions:
            if expr in lower_text:
                # Extract a bit of context around the expression
                match = re.search(fr'([^.!?]*{expr}[^.!?]*)', lower_text)
                if match:
                    found_times.append(match.group(1).strip())
        entities["times"] = list(set(found_times))
        
        # Amounts: numbers with currency
        amount_matches = re.findall(r'(\d+(?:\.\d+)?\s*(?:rs|rupees|dollars|\$|%))', lower_text)
        entities["amounts"] = amount_matches
        
        return entities

    def convert_relative_time(self, expression: str) -> str:
        """Convert relative expressions to ISO 8601."""
        now = datetime.datetime.now()
        text = expression.lower()
        
        target = now
        
        if "tonight" in text:
            target = target.replace(hour=20, minute=0, second=0, microsecond=0)
        elif "tomorrow" in text:
            target += datetime.timedelta(days=1)
            if "morning" in text:
                target = target.replace(hour=9, minute=0, second=0, microsecond=0)
            elif "night" in text or "evening" in text:
                target = target.replace(hour=20, minute=0, second=0, microsecond=0)
            else:
                target = target.replace(hour=9, minute=0, second=0, microsecond=0)
        elif "in" in text and "hour" in text:
            match = re.search(r'in (\d+) hour', text)
            hours = int(match.group(1)) if match else 1
            target += datetime.timedelta(hours=hours)
        elif "at" in text:
            match = re.search(r'at (\d+)(?::(\d+))?\s*(am|pm)?', text)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2)) if match.group(2) else 0
                meridiem = match.group(3)
                
                if meridiem == "pm" and hour < 12:
                    hour += 12
                elif meridiem == "am" and hour == 12:
                    hour = 0
                elif not meridiem:
                    # Heuristic: 1-6 -> PM, 7-12 -> AM
                    if 1 <= hour <= 6:
                        hour += 12
                target = target.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Check if target is in the past, if so, move to next day for ambiguous "at X"
        if target < now and "at" in text and not any(kw in text for kw in ["today", "tomorrow", "yesterday"]):
             target += datetime.timedelta(days=1)

        return target.isoformat()

    def identify_missing_fields(self, step: dict, tool_registry: dict) -> List[str]:
        """Return list of required field names that are missing."""
        tool_name = step.get("tool")
        args = step.get("args", {})
        tool = tool_registry.get(tool_name)
        if not tool:
            return []
            
        schema = getattr(tool, 'schema', {})
        required = schema.get("required", [])
        missing = []
        for field in required:
            if field not in args or args[field] in [None, "", "UNKNOWN", "null"]:
                missing.append(field)
        return missing

    def check_for_placeholders(self, args: Dict) -> bool:
        """Return True if any placeholder values like 'your_email' are found."""
        # Removed '?' and 'null' as they cause false positives in URLs and valid JSON
        placeholders = ["your_", "UNKNOWN", "example", "test@", "X", "place_holder"]
        for val in args.values():
            if isinstance(val, str):
                # Don't flag URLs as placeholders even if they contain typical characters
                if val.startswith("http"):
                    continue
                if any(p in val.lower() for p in placeholders) or val.strip() == "":
                    return True
        return False
