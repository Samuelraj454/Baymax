import os
import json
import asyncio
from datetime import datetime
from loguru import logger
from typing import Dict, List, Any, Optional

from .intent_classifier import IntentClassifier
from .accuracy_engine import AccuracyEngine
from .speech_engine import SpeechEngine
from .llm_core import LLMCore
from .validator import Validator
from .feedback_loop import FeedbackLoop
from .proactive import ProactiveEngine
from .user_profile import UserProfile
from app_config import DB_PATH

from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from tools import TOOL_REGISTRY

class BAYMAXAgent:
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.accuracy_engine = AccuracyEngine(tool_registry=TOOL_REGISTRY)
        self.speech_engine = SpeechEngine()
        self.validator = Validator()
        self.feedback_loop = FeedbackLoop()
        self.proactive = ProactiveEngine()
        
        self.short_mem = ShortTermMemory()
        self.long_mem = LongTermMemory()
        
        self.user_profile = UserProfile(DB_PATH)
        
        # Inject user_profile into VoiceSettingsTool if it exists
        voice_tool = TOOL_REGISTRY.get("voice_settings")
        if voice_tool:
            voice_tool.user_profile = self.user_profile

    def _clean_for_speech(self, text: str) -> str:
        import re
        if not text: return ""
        text = re.sub(r'\{[^}]*\}', '', text, flags=re.DOTALL)
        text = re.sub(r'[*_#`~]', '', text)
        text = re.sub(r'[✓✗⏳⚠═─█◆▸→]', '', text)
        text = re.sub(r'\s+', ' ', text)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return ' '.join(sentences[:3]).strip()

    async def run(self, raw_input: str, session_id: str = "default", source: str = "text") -> dict:
        """Full 7-step pipeline for processing user requests, returns a dict."""
        try:
            self.long_mem.ensure_session(session_id)
            is_voice = (source == "voice")
            
            # Load user profile
            profile_context = self.user_profile.build_context_string()
            lang_config = self.user_profile.get_language_config()
            user_name = self.user_profile.get("user_name", "User")
            
            # (Removed redundant short_mem USER PROFILE injection to prevent context bloat)

            # Tag input with mode
            tagged_input = raw_input if "[VOICE MODE]" in raw_input else f"[TEXT MODE] {raw_input}"
            
            # Learn from this conversation
            entities = self.accuracy_engine.extract_entities(raw_input)
            self.user_profile.learn_from_conversation(raw_input, entities)

            # Resolve relative times
            resolved_times = []
            for t_expr in entities.get("times", []):
                resolved = self.accuracy_engine.convert_relative_time(t_expr)
                resolved_times.append(resolved)
            entities["resolved_times"] = resolved_times
            
            logger.info(f"BAYMAX: User={user_name}, Input={tagged_input}, Entities={entities}")
            
            # LLM Thinking
            context = self.short_mem.get()
            llm = LLMCore(memory_context=context, profile_context=profile_context)
            plan_data = await llm.think(tagged_input, intent="conversation", entities=entities)
            
            open_url = None
            tool_used = ""
            final_response = plan_data.get("response", "")
            
            # Autonomous Self-Correction Loop
            max_iterations = 2
            iteration = 0
            
            while plan_data.get("needs_tools") and iteration < max_iterations:
                steps = plan_data.get("steps", [])
                results = []
                all_success = True
                
                for step in steps:
                    tool_name = step.get("tool")
                    args = step.get("args", {})
                    tool_used = tool_name
                    
                    # Intercept browser/web-facing tools for client-side execution
                    if tool_name == "system":
                        action = args.get("action")
                        if action == "open_url" and args.get("url"):
                            open_url = args.get("url")
                        elif action == "web_search" and args.get("query"):
                            import urllib.parse
                            open_url = f"https://www.google.com/search?q={urllib.parse.quote(args.get('query'))}"
                        elif action == "play_music" and args.get("query"):
                            plat = args.get("platform", "youtube")
                            query = args.get("query")
                            if plat == "spotify":
                                import urllib.parse
                                open_url = f"https://open.spotify.com/search/{urllib.parse.quote(query)}"
                            else:
                                system_tool = TOOL_REGISTRY.get("system")
                                if system_tool:
                                    video_url = system_tool._get_youtube_video_url(query)
                                    if video_url:
                                        open_url = video_url
                                    else:
                                        import urllib.parse
                                        open_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
                        elif action == "open_app" and args.get("app"):
                            app_name = args.get("app").lower()
                            app_urls = {
                                "youtube": "https://www.youtube.com",
                                "spotify": "https://open.spotify.com",
                                "gmail": "https://mail.google.com",
                                "calendar": "https://calendar.google.com",
                                "chrome": "https://www.google.com",
                                "edge": "https://www.google.com",
                                "browser": "https://www.google.com",
                                "whatsapp": "https://web.whatsapp.com",
                                "calculator": "https://www.google.com/search?q=calculator",
                                "calc": "https://www.google.com/search?q=calculator",
                                "notepad": "https://docs.new",
                                "paint": "https://jspaint.app"
                            }
                            if app_name in app_urls:
                                open_url = app_urls[app_name]
                        elif action == "calculator":
                            open_url = "https://www.google.com/search?q=calculator"

                    args = await self._resolve_contacts(tool_name, args)
                    res = await self._execute_tool(tool_name, args)
                    
                    if res["success"]:
                        results.append(str(res["output"]) if not isinstance(res["output"], str) else res["output"])
                    else:
                        results.append(f"Tool '{tool_name}' Failed: {res['error']}")
                        all_success = False
                        
                    self.user_profile.set("most_used_tool", tool_name, "usage")

                if all_success:
                    tool_output = " ".join(results).strip()
                    if "message" in plan_data:
                        if tool_output:
                            # Filter out standard system statuses and action confirmations
                            ignore_prefixes = ["opened", "playing", "volume", "executed", "screen locked", "saved screenshot", "done", "success", "true"]
                            is_action_output = any(tool_output.lower().startswith(p) for p in ignore_prefixes)
                            
                            if not is_action_output and tool_output.lower() not in plan_data["message"].lower():
                                final_response = f"{plan_data['message']} {tool_output}"
                            else:
                                final_response = plan_data["message"]
                        else:
                            final_response = plan_data["message"]
                    else:
                        final_response = tool_output or "Done."
                    break
                else:
                    iteration += 1
                    error_feedback = " ".join(results)
                    logger.warning(f"Self-correction loop {iteration} triggered. Error: {error_feedback}")
                    
                    correction_input = f"SYSTEM WARNING: The tool execution failed. Details: {error_feedback}. Please re-evaluate and provide a new JSON plan to fix this, or explain the failure to the user."
                    
                    # Call LLM again with the error context
                    context = self.short_mem.get()
                    llm = LLMCore(memory_context=context, profile_context=profile_context)
                    plan_data = await llm.think(correction_input, intent="correction", entities=entities)
                    final_response = plan_data.get("response", "")
                    
            if iteration >= max_iterations and not all_success:
                final_response = plan_data.get("response", "I encountered a persistent error while trying to complete that task.")

            # Build response dict
            speak_text = self._clean_for_speech(final_response)
            
            result = {
              "response":        final_response,
              "speak_text":      speak_text,
              "language_change": plan_data.get("language_change", False),
              "new_language":    plan_data.get("new_language", ""),
              "voice_change":    plan_data.get("voice_change", False),
              "new_voice_id":    plan_data.get("new_voice_id", ""),
              "user_name":       user_name,
              "intent":          "conversation",
              "tool_used":       tool_used,
              "open_url":        open_url,
              "success":         True
            }

            self._save_memory(session_id, raw_input, final_response)
            
            # Update usage stats
            self.user_profile.set("last_active", datetime.utcnow().isoformat(), "usage")
            return result

        except Exception as e:
            logger.error(f"Agent Pipeline Error: {e}", exc_info=True)
            return {
                "response": "I encountered a problem while processing that. Should I try again?",
                "speak_text": "I encountered a problem while processing that.",
                "language_change": False,
                "new_language": "",
                "voice_change": False,
                "new_voice_id": "",
                "user_name": self.user_profile.get("user_name", "User"),
                "intent": "error",
                "tool_used": "",
                "open_url": None,
                "success": False
            }

    async def run_voice_turn(self, raw_input: str, confidence: float, session_id: str) -> str:
        """Specialized voice interaction (not deeply changed as /query handles voice explicitly now)."""
        logger.info(f"BAYMAX Voice Turn: '{raw_input}' (confidence: {confidence:.2f})")
        res = await self.run(raw_input, session_id=session_id, source="voice")
        return res["speak_text"]

    async def _resolve_contacts(self, tool_name: str, args: Dict) -> Dict:
        """Resolve names to phone numbers or emails using Contacts tool or UserProfile."""
        if tool_name == "email" and "to" in args:
            to_val = args["to"]
            if to_val and "@" not in to_val:
                # Try UserProfile first
                prof_email = self.user_profile.get(f"{to_val.lower()}_email")
                if prof_email:
                    args["to"] = prof_email
                else:
                    resolved = self._find_contact(to_val, "email")
                    if resolved: args["to"] = resolved
                    
        elif tool_name in ["whatsapp", "sms"]:
            phone_val = args.get("phone") or args.get("to")
            if phone_val and not any(c.isdigit() for c in str(phone_val)):
                prof_phone = self.user_profile.get(f"{str(phone_val).lower()}_phone")
                if prof_phone:
                    if "phone" in args: args["phone"] = prof_phone
                    if "to" in args: args["to"] = prof_phone
                else:
                    resolved = self._find_contact(str(phone_val), "phone")
                    if resolved:
                        if "phone" in args: args["phone"] = resolved
                        if "to" in args: args["to"] = resolved
        return args

    def _find_contact(self, name: str, field: str) -> Optional[str]:
        contacts_tool = TOOL_REGISTRY.get("contacts")
        if contacts_tool:
            try:
                res = contacts_tool.run(action="find", name=name)
                if res.success and isinstance(res.output, list) and len(res.output) > 0:
                    return res.output[0].get(field)
            except: pass
        return None

    async def _execute_tool(self, tool_name: str, args: Dict) -> Dict:
        tool = TOOL_REGISTRY.get(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool {tool_name} not found."}
            
        try:
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, lambda: tool.run(**args))
            
            success = res.success if hasattr(res, 'success') else True
            output = res.output if hasattr(res, 'output') else str(res)
            
            if success:
                return {"success": True, "output": output}
            
            err_msg = res.error if hasattr(res, 'error') else "Unknown tool error"
            logger.warning(f"Tool {tool_name} failed: {err_msg}")
            return {"success": False, "error": err_msg}
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {"success": False, "error": str(e)}

    def _save_memory(self, session_id: str, user_text: str, assistant_text: str):
        self.short_mem.add("user", user_text)
        self.short_mem.add("assistant", assistant_text)
        self.long_mem.save_turn(session_id, "user", user_text)
        self.long_mem.save_turn(session_id, "assistant", assistant_text)
