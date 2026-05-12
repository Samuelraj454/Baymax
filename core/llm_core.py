import os
import json
import re
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from .prompts import BAYMAX_SYSTEM_PROMPT
from loguru import logger

class LLMCore:
    def __init__(self, memory_context: List[Dict] = None, profile_context: str = ""):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.primary_model = "llama-3.3-70b-versatile"
        self.fallback_model = "llama-3.1-8b-instant"
        self.memory = memory_context or []
        self.profile_context = profile_context

    async def think(self, user_input: str, intent: str = None, entities: dict = None) -> dict:
        """Process input through the JSON waterfall."""
        from datetime import datetime
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%dT%H:%M:%S")
        day = now.strftime("%A")
        
        context_prompt = f"\n\nCURRENT CONTEXT:\n- Time: {timestamp}\n- Day: {day}\n- Location: Hyderabad, India\n"
        profile_prompt = f"\n\nUSER PROFILE:\n{self.profile_context}" if self.profile_context else ""
        system_prompt = BAYMAX_SYSTEM_PROMPT + context_prompt + profile_prompt
        
        # Build message history
        messages = [{"role": "system", "content": system_prompt}]
        for m in self.memory[-10:]: # Last 10 turns
            messages.append(m)
        messages.append({"role": "user", "content": user_input})

        # Strategy 1 & 2: Primary call with temperature control
        raw_response = await self._call_llm(messages, self.primary_model, temperature=0.1)
        logger.debug(f"Primary LLM ({self.primary_model}) Response: {raw_response}")
        
        # Strategy 3: Extraction Waterfall
        data = self._extract_json(raw_response)
        
        if data:
            return data

        # Strategy 4: Two-model fallback
        logger.warning(f"JSON Parse failed on {self.primary_model}. Retrying with {self.fallback_model}...")
        
        # If raw_response is empty, don't include it in history
        retry_messages = [{"role": "system", "content": system_prompt}]
        for m in self.memory[-5:]:
             retry_messages.append(m)
        retry_messages.append({"role": "user", "content": user_input})
        retry_messages.append({"role": "user", "content": "Respond ONLY with the JSON object. No explanation."})
        
        raw_retry = await self._call_llm(retry_messages, self.fallback_model, temperature=0.0)
        logger.debug(f"Fallback LLM ({self.fallback_model}) Response: {raw_retry}")
        data = self._extract_json(raw_retry)
        
        if data:
            return data
            
        # Strategy 5: Failure fallback
        return {"needs_tools": False, "response": "I'm having trouble formatting my thoughts as JSON right now. Let's try again."}

    def _extract_json(self, raw: str) -> Optional[dict]:
        """Resilient JSON extraction."""
        if not raw: return None
        
        text = raw.strip()
        
        # Try 1: Direct parse
        try:
            return json.loads(text)
        except:
            pass

        # Try 2: Handle Markdown blocks
        try:
            if "```" in text:
                # Find content between ```json and ``` or just ``` and ```
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
        except:
            pass

        # Try 3: Regex for outermost braces
        try:
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except:
            pass
            
        return None

    async def _call_llm(self, messages: List[Dict], model: str, temperature: float = 0.1) -> str:
        """Generic Groq API caller with retry for rate limits."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1024,
            "response_format": {"type": "json_object"}
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(3):
                try:
                    response = await client.post(url, headers=headers, json=payload)
                    if response.status_code == 200:
                        return response.json()["choices"][0]["message"]["content"]
                    
                    if response.status_code == 429:
                        wait = (attempt + 1) * 5
                        logger.warning(f"Rate limited (429). Retrying in {wait}s...")
                        await asyncio.sleep(wait)
                        continue
                        
                    logger.error(f"Groq API Error: {response.status_code} - {response.text}")
                    return ""
                except Exception as e:
                    logger.error(f"LLM Call failed: {e}")
                    if attempt == 2: return ""
                    await asyncio.sleep(1)
        return ""
