import time
import random
from loguru import logger
from voice.voice_engine import SpeechToText, TextToSpeech
from core.speech_engine import SpeechEngine

BAYMAX_READY_PHRASES = [
    "Listening.", "Yeah?", "Go ahead.", "I'm here.", "Mm?", "Yep?"
]

class VoiceLoop:
    def __init__(self, agent, stt: SpeechToText, tts: TextToSpeech):
        self.agent = agent
        self.stt = stt
        self.tts = tts
        self.speech_engine = SpeechEngine()

    async def _handle_voice_turn(self, session_id: str):
        """Standard flow: record -> confidence check -> agent -> speak."""
        # 1. Signal ready
        phrase = random.choice(BAYMAX_READY_PHRASES)
        self.tts.speak(phrase)
        self.tts.beep_ready()
        
        # 2. Listen
        print("\n[BAYMAX LISTENING...]")
        text, confidence = self.stt.listen_with_confidence()
        
        if not text:
            self.tts.speak("Didn't catch that. Say it again?")
            return

        print(f"Heard: {text} [confidence: {confidence:.0%}]")

        # 3. Confidence Check
        if confidence < 0.65:
            question = self.speech_engine.confirm_heard(text)
            self.tts.speak_question(question)
            confirmed = self.stt.listen_for_confirmation()
            if not confirmed:
                self.tts.speak("No problem — say it again.")
                return

        # 4. Agent Run
        # Note: BAYMAXAgent needs to implement run_voice_turn
        response = await self.agent.run_voice_turn(
            raw_input=text,
            confidence=confidence,
            session_id=session_id
        )

        # 5. Output
        self.tts.speak_and_wait(response)
        time.sleep(0.3)

    def run_push_to_talk(self, session_id: str):
        """Wait for keypress then handle turn."""
        try:
            import keyboard
            print("Press and hold SPACE to speak to BAYMAX (Ctrl+C to quit)...")
            while True:
                if keyboard.is_pressed('space'):
                    import asyncio
                    asyncio.run(self._handle_voice_turn(session_id))
                    time.sleep(0.5)
                time.sleep(0.1)
        except (ImportError, Exception):
            print("Note: 'keyboard' module not found. Falling back to Enter key.")
            print("Press ENTER to speak to BAYMAX (Ctrl+C to quit)...")
            while True:
                input() # Wait for Enter
                import asyncio
                asyncio.run(self._handle_voice_turn(session_id))

    def run_always_on(self, session_id: str):
        """Wake word detection (Stub for v5.0)."""
        print("BAYMAX Always-on mode active. Say 'Hey Baymax'...")
        # In a real implementation, use a library like Porcupine for wake word
        # For now, we'll simulate it or wait for input
        while True:
            # Placeholder for wake word logic
            time.sleep(1)
