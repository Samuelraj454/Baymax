import os
from dotenv import load_dotenv
load_dotenv()

# LLM
GROQ_API_KEY    = os.getenv("GROQ_API_KEY")
PRIMARY_MODEL   = "llama-3.3-70b-versatile"
FALLBACK_MODEL  = "gemma2-9b-it"
MAX_TOKENS      = 1024
MAX_RETRIES     = 3

# Paths
DB_PATH         = "memory/baymax.db"
CHROMA_PATH     = "memory/chroma"
LOG_PATH        = "logs/baymax.log"

# Identity
SYSTEM_NAME     = "BAYMAX"
SYSTEM_VERSION  = "11.0"

# Voice defaults
DEFAULT_VOICE        = "jarvis"
DEFAULT_LANGUAGE     = "en-IN"
DEFAULT_VOICE_RATE   = 1.05
DEFAULT_VOICE_PITCH  = 0.85
DEFAULT_VOICE_VOLUME = 1.0

# Personal defaults
DEFAULT_CITY         = "Hyderabad"
DEFAULT_COUNTRY      = "IN"
DEFAULT_TIMEZONE     = "Asia/Kolkata"

# Optional services
GMAIL_ADDRESS        = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD   = os.getenv("GMAIL_APP_PASSWORD", "")
TWILIO_SID           = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN         = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE         = os.getenv("TWILIO_PHONE_NUMBER", "")
NEWS_API_KEY         = os.getenv("NEWS_API_KEY", "")
ELEVENLABS_KEY       = os.getenv("ELEVENLABS_API_KEY", "")
