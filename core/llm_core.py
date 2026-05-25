import os
import json
import re
import asyncio
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI, RateLimitError, APIError
from .prompts import BAYMAX_SYSTEM_PROMPT
from loguru import logger

class LLMCore:
    def __init__(self, memory_context: List[Dict] = None, profile_context: str = ""):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None
        self.primary_model = os.getenv("OPENAI_PRIMARY_MODEL", "gpt-4o")
        self.fallback_model = os.getenv("OPENAI_FALLBACK_MODEL", "gpt-4o-mini")
        self.memory = memory_context or []
        self.profile_context = profile_context

    async def think(self, user_input: str, intent: str = None, entities: dict = None) -> dict:
        """Process input through the JSON waterfall."""
        from datetime import datetime
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%dT%H:%M:%S")
        day = now.strftime("%A")
        
        context_prompt = f"\n\nCURRENT CONTEXT:\n- Time: {timestamp}\n- Day: {day}\n- Location: Hyderabad, India\n"
        
        system_with_profile = BAYMAX_SYSTEM_PROMPT + context_prompt
        if self.profile_context:
            system_with_profile += f"\n\n━━━ USER PROFILE ━━━\n{self.profile_context}\n━━━━━━━━━━━━━━━━━━━━"
            
        messages = [{"role": "system", "content": system_with_profile}]
        for m in self.memory[-10:]:
            messages.append(m)
        messages.append({"role": "user", "content": user_input})

        task_words = [
            "play", "open", "weather", "remind", "email",
            "whatsapp", "search", "note", "calendar", "translate",
            "calculate", "news", "time", "date", "volume", "call"
        ]
        is_task = any(w in user_input.lower() for w in task_words)
        temp = 0.1 if is_task else 0.75

        target_model = self.fallback_model if is_task else self.primary_model

        raw_response = await self._call_llm(messages, target_model, temperature=temp)
        logger.debug(f"Primary LLM ({target_model}) Response: {raw_response}")
        
        data = self._extract_json(raw_response)
        
        if data:
            return data
        
        if target_model != self.fallback_model:
            logger.warning(f"JSON parse failed on {target_model}. Retrying with {self.fallback_model}...")
            
            retry_messages = [{"role": "system", "content": system_with_profile}]
            for m in self.memory[-5:]:
                 retry_messages.append(m)
            retry_messages.append({"role": "user", "content": user_input})
            retry_messages.append({"role": "user", "content": "Respond ONLY with the JSON object. No explanation."})
            
            raw_retry = await self._call_llm(retry_messages, self.fallback_model, temperature=0.0)
            logger.debug(f"Fallback LLM ({self.fallback_model}) Response: {raw_retry}")
            data = self._extract_json(raw_retry)
            
            if data:
                return data
            
        return {"needs_tools": False, "response": "I'm having trouble formatting my thoughts as JSON right now. Let's try again."}

    def _extract_json(self, raw: str) -> Optional[dict]:
        """Resilient JSON extraction."""
        if not raw: return None
        
        text = raw.strip()
        
        try:
            return json.loads(text)
        except:
            pass
 
        try:
            if "```" in text:
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
        except:
            pass
 
        try:
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except:
            pass
            
        return None

    async def _call_llm(self, messages: List[Dict], model: str, temperature: float = 0.1) -> str:
        """OpenAI chat completions with retry for rate limits."""
        if not self.client:
            logger.error("OPENAI_API_KEY not set")
            return ""

        for attempt in range(3):
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=1024,
                    response_format={"type": "json_object"},
                )
                return response.choices[0].message.content or ""

            except RateLimitError:
                if model == self.primary_model:
                    logger.warning(f"Primary model ({model}) rate limited. Falling back immediately.")
                    return ""
                wait = (attempt + 1) * 2
                logger.warning(f"Rate limited (429). Retrying in {wait}s...")
                await asyncio.sleep(wait)

            except APIError as e:
                logger.error(f"OpenAI API Error: {e}")
                return ""

            except Exception as e:
                logger.error(f"LLM Call failed: {e}")
                if attempt == 2:
                    return ""
                await asyncio.sleep(1)

        return ""
