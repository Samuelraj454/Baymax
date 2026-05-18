import os
import logging
import uuid
import time
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from collections import deque
from datetime import datetime
from core.agent_loop import BAYMAXAgent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BAYMAX")

agent = BAYMAXAgent()
start_time = time.time()

VOICE_CATALOG = {
    "jarvis":   { "name": "Google UK English Male",  "rate": 1.0, "pitch": 0.7,  "lang": "en-GB", "label": "Jarvis (Deep Male)" },
    "siri_m":   { "name": "Google US English",        "rate": 1.1, "pitch": 0.9,  "lang": "en-US", "label": "Siri Male (US)" },
    "siri_f":   { "name": "Google US English",        "rate": 1.1, "pitch": 1.3,  "lang": "en-US", "label": "Siri Female (US)" },
    "indian_m": { "name": "Google हिन्दी",            "rate": 1.0, "pitch": 0.85, "lang": "hi-IN", "label": "Indian Male (Hindi)" },
    "alexa":    { "name": "Microsoft David",           "rate": 1.05,"pitch": 0.8,  "lang": "en-US", "label": "Alexa Style" },
    "natural":  { "name": "Google UK English Female", "rate": 1.05,"pitch": 1.0,  "lang": "en-GB", "label": "Natural Female" },
    "telugu":   { "name": "Google తెలుగు",             "rate": 1.0, "pitch": 0.9,  "lang": "te-IN", "label": "Telugu Voice" },
    "tamil":    { "name": "Google தமிழ்",              "rate": 1.0, "pitch": 0.9,  "lang": "ta-IN", "label": "Tamil Voice" },
    "hindi":    { "name": "Google हिन्दी",             "rate": 1.0, "pitch": 0.9,  "lang": "hi-IN", "label": "Hindi Voice" },
    "kannada":  { "name": "Google ಕನ್ನಡ",              "rate": 1.0, "pitch": 0.9,  "lang": "kn-IN", "label": "Kannada Voice" },
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    required_vars = ["GROQ_API_KEY"]
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        logger.error(f"[BAYMAX ERROR] Missing env vars: {missing}")
    else:
        logger.info("[BAYMAX] All environment variables OK.")
        logger.info("[BAYMAX] Backend online at http://localhost:8000")
    yield
    logger.info("[BAYMAX] Shutting down.")

app = FastAPI(title="BAYMAX API", version="10.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    source: str = "text"

# In-memory log store for UI display
ui_logs: Dict[str, deque] = {}

def add_ui_log(session_id: str, message: str, level: str = "INFO"):
    if session_id not in ui_logs:
        ui_logs[session_id] = deque(maxlen=50)
    ui_logs[session_id].append({
        "timestamp": datetime.utcnow().isoformat(),
        "level":     level,
        "message":   message
    })

@app.get("/logs/{session_id}")
async def get_logs(session_id: str):
    logs = list(ui_logs.get(session_id, []))
    return {
        "session_id": session_id,
        "logs":       logs,
        "count":      len(logs)
    }

@app.get("/briefing/{session_id}")
async def get_briefing(session_id: str):
    try:
        briefing = agent.proactive.check_morning_briefing(session_id)
        return {
            "session_id": session_id,
            "briefing":   briefing or "",
            "has_briefing": bool(briefing)
        }
    except Exception as e:
        return {
            "session_id":   session_id,
            "briefing":     "",
            "has_briefing": False,
            "error":        str(e)
        }

class QueryResponse(BaseModel):
    session_id: str
    response: str
    intent: str = ""
    tool_used: str = ""
    success: bool = True
    speak_text: str = ""
    display_text: str = ""
    latency_ms: int = 0
    language_change: bool = False
    new_language: str = ""
    voice_change: bool = False
    new_voice_id: str = ""
    user_name: str = ""

class ProfileItem(BaseModel):
    key: str
    value: str

@app.post("/query", response_model=QueryResponse)
async def query_baymax(body: QueryRequest):
    if not body.message or not body.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    sid = body.session_id or str(uuid.uuid4())
    start_query = time.time()
    add_ui_log(sid, f"Received: {body.message[:50]}", "INFO")
    try:
        result = await agent.run(
            f"[VOICE MODE] {body.message}" if body.source == "voice" else body.message,
            session_id=sid,
            source=body.source
        )
        add_ui_log(sid, f"Response: {str(result.get('response',''))[:50]}", "INFO")
        
        latency = int((time.time() - start_query) * 1000)

        return QueryResponse(
            session_id=sid,
            response=result.get("response", ""),
            success=result.get("success", True),
            speak_text=result.get("speak_text", ""),
            display_text=result.get("response", ""),
            latency_ms=latency,
            intent=result.get("intent", ""),
            tool_used=result.get("tool_used", ""),
            language_change=result.get("language_change", False),
            new_language=result.get("new_language", ""),
            voice_change=result.get("voice_change", False),
            new_voice_id=result.get("new_voice_id", ""),
            user_name=result.get("user_name", "User")
        )
    except Exception as e:
        add_ui_log(sid, f"ERROR: {str(e)}", "ERROR")
        logger.error(f"[BAYMAX] Query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"BAYMAX processing error: {str(e)}")

@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "system": "BAYMAX",
        "version": "10.0",
        "uptime_seconds": int(time.time() - start_time)
    }

@app.get("/telemetry")
async def get_telemetry():
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
    except ImportError:
        cpu = 15.0
        mem = 40.0
    
    return {
        "cpu": cpu,
        "memory": mem,
        "status": "OPTIMAL" if cpu < 80 else "WARNING",
        "active_tools": len(agent.short_mem.get()),
        "network": "SECURE"
    }

@app.get("/profile")
async def get_profile():
    return agent.user_profile.get_all()

@app.post("/profile")
async def update_profile(item: ProfileItem):
    agent.user_profile.set(item.key, item.value, "user_update")
    return {"status": "saved", "key": item.key, "value": item.value}

@app.get("/profile/voice")
async def get_voice():
    return agent.user_profile.get_voice_settings()

@app.post("/profile/voice")
async def save_voice(settings: Dict[str, Any]):
    for k, v in settings.items():
        if k == "voice_id":
            agent.user_profile.set("preferred_voice_id", v, "preferences")
        elif k == "language":
            agent.user_profile.set("user_language", v, "identity")
        elif k == "rate":
            agent.user_profile.set("preferred_voice_rate", str(v), "preferences")
        elif k == "pitch":
            agent.user_profile.set("preferred_voice_pitch", str(v), "preferences")
        elif k == "volume":
            agent.user_profile.set("preferred_voice_volume", str(v), "preferences")
    return agent.user_profile.get_voice_settings()

@app.get("/voices")
async def get_voices():
    return {"voices": VOICE_CATALOG}

@app.get("/languages")
async def get_languages():
    return {
        "languages": [
            {"code":"en-IN","name":"English (India)","flag":"🇮🇳"},
            {"code":"hi-IN","name":"Hindi","flag":"🇮🇳"},
            {"code":"te-IN","name":"Telugu","flag":"🇮🇳"},
            {"code":"ta-IN","name":"Tamil","flag":"🇮🇳"},
            {"code":"kn-IN","name":"Kannada","flag":"🇮🇳"},
            {"code":"en-US","name":"English (US)","flag":"🇺🇸"},
            {"code":"en-GB","name":"English (UK)","flag":"🇬🇧"},
            {"code":"mr-IN","name":"Marathi","flag":"🇮🇳"}
        ]
    }

@app.get("/history/{session_id}")
async def get_history(session_id: str):
    history = agent.long_mem.recall(session_id, limit=50)
    return {"session_id": session_id, "history": history}

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    agent.short_mem.clear()
    return {"status": "cleared", "session_id": session_id}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("api.server:app", host="0.0.0.0", port=port)

