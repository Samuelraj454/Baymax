import sys
import os
import asyncio
import threading
import time
from loguru import logger
from core.agent_loop import BAYMAXAgent

ASCII_BANNER = r"""
#######################################################
#   ____   _______ __   ____  __  _______  _  __    #
#  |  _ \ /   _   \ \ / /|  \/  |/   _   \| |/ /    #
#  | |_) |  /_\  | \ V / | \  / |  /_\  | ' /       #
#  |  _ <|  ___  |  | |  | |\/| |  ___  |  <        #
#  | |_) | |   | |  | |  | |  | | |   | | . \       #
#  |____/|_|   |_|  |_|  |_|  |_|_|   |_|_|\_\      #
#                                                   #
#              System Core v6.0                     #
#######################################################
"""

def print_banner():
    print("\033[96m" + ASCII_BANNER + "\033[0m")

def reminder_worker(agent):
    """Background thread to check for reminders every minute."""
    while True:
        try:
            alerts = agent.proactive.check_pending_reminders()
            for alert in alerts:
                print(f"\n[ALERT] {alert}")
                # In a voice-capable system, we'd trigger TTS here
        except Exception as e:
            logger.error(f"Reminder worker error: {e}")
        time.sleep(60)

async def run_text_mode():
    agent = BAYMAXAgent()
    session_id = "cli_session"
    print_banner()
    
    # Start reminder worker
    t = threading.Thread(target=reminder_worker, args=(agent,), daemon=True)
    t.start()
    
    # Morning Briefing
    briefing = agent.proactive.check_morning_briefing(session_id)
    if briefing:
        print(f"BAYMAX: {briefing}\n")
    else:
        print("Hey — BAYMAX is up. What are we working on?\n")
    
    try:
        while True:
            user_input = input("\nYou: ")
            if user_input.lower().strip() in ['exit', 'quit', 'bye']:
                print("BAYMAX: See you later.")
                break
                
            if not user_input.strip():
                continue
                
            response = await agent.run(user_input, session_id=session_id)
            print(f"\nBAYMAX: {response}")
    except KeyboardInterrupt:
        print("\nBAYMAX: Shutting down.")

def run_voice_mode(always_on: bool = False):
    print_banner()
    try:
        from voice.voice_engine import SpeechToText, TextToSpeech
        from voice.voice_loop import VoiceLoop
    except ImportError as e:
        logger.error(f"Voice dependencies missing: {e}")
        print("Error: Voice dependencies are not installed.")
        print("Please run: pip install faster-whisper sounddevice soundfile pyttsx3 numpy")
        sys.exit(1)

    agent = BAYMAXAgent()
    session_id = "voice_session"
    
    # Start reminder worker
    t = threading.Thread(target=reminder_worker, args=(agent,), daemon=True)
    t.start()
    
    print("Initializing voice engine (Whisper loading)...")
    stt = SpeechToText(model_size="base")
    use_elevenlabs = os.getenv("ELEVENLABS_API_KEY") is not None
    tts = TextToSpeech(use_elevenlabs=use_elevenlabs, elevenlabs_key=os.getenv("ELEVENLABS_API_KEY"))
    
    loop = VoiceLoop(agent, stt, tts)
    
    # Morning Briefing via TTS
    briefing = agent.proactive.check_morning_briefing(session_id)
    if briefing:
        tts.speak(briefing)
    
    if always_on:
        loop.run_always_on(session_id)
    else:
        loop.run_push_to_talk(session_id)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "--voice":
            run_voice_mode(always_on=False)
        elif arg == "--always":
            run_voice_mode(always_on=True)
        elif arg in ["-h", "--help"]:
            print("Usage: python main.py [options]")
            print("Options:")
            print("  (no args)  Run in standard text mode")
            print("  --voice    Run in push-to-talk voice mode")
            print("  --always   Run in always-on wake word mode ('Hey Baymax')")
        else:
            print(f"Unknown argument: {arg}")
            print("Run python main.py --help for usage.")
    else:
        asyncio.run(run_text_mode())
