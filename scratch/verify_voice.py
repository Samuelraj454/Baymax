from voice.voice_engine import SpeechToText, TextToSpeech
import os
import sys

# Mock sounddevice if needed? No, let's just see if it imports and inits classes.
print("Testing Voice Engine initialization...")
try:
    # Use base as specified in v3.0, but tiny is faster for validation if we wanted.
    # However, user wants 'base'.
    stt = SpeechToText(model_size="base")
    print("STT (faster-whisper) loaded successfully.")
    
    tts = TextToSpeech()
    print("TTS (pyttsx3) loaded successfully.")
    
    print("\nSUCCESS: Voice flow components are ready.")
except Exception as e:
    print(f"\nFAILURE: Voice flow error: {e}")
    sys.exit(1)
