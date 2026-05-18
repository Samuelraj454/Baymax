import os
import re
import time
import tempfile
import numpy as np
import sounddevice as sd
import soundfile as sf
import pyttsx3
import httpx
from faster_whisper import WhisperModel
from loguru import logger
from typing import Tuple, Optional

class SpeechToText:
    def __init__(self, model_size="base"):
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def listen_with_confidence(self, samplerate: int = 16000) -> Tuple[str, float]:
        """Transcribe with confidence score based on dual-beam comparison."""
        audio = self.record_vad(samplerate)
        if audio is None or len(audio) == 0:
            return "", 0.0
            
        fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            sf.write(temp_path, audio, samplerate)
            
            # Transcription 1: Beam size 5
            segments1, _ = self.model.transcribe(temp_path, beam_size=5)
            text1 = " ".join([s.text for s in segments1]).strip()
            
            # Transcription 2: Beam size 3 (different perspective)
            segments2, _ = self.model.transcribe(temp_path, beam_size=3)
            text2 = " ".join([s.text for s in segments2]).strip()
            
            if not text1:
                return "", 0.0
                
            # Confidence calculation: If match, high confidence. 
            # If mismatch, calculate similarity or use 0.5 as fallback.
            if text1.lower() == text2.lower():
                confidence = 0.95
            else:
                # Basic similarity check
                confidence = 0.6 if text1 and text2 else 0.4
                
            return text1, confidence
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def transcribe_file(self, file_path: str) -> Tuple[str, float]:
        """Transcribe an existing audio file."""
        try:
            segments, _ = self.model.transcribe(file_path, beam_size=5)
            text = " ".join([s.text for s in segments]).strip()
            return text, 0.9 # Constant high confidence for clear file uploads
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return "", 0.0

    def listen_for_confirmation(self) -> bool:
        """Listen for 'yes', 'no', or variants."""
        text, _ = self.listen_with_confidence()
        text = text.lower()
        
        yes_words = ["yes", "yeah", "correct", "right", "yep", "sure", "go ahead", "do it"]
        no_words = ["no", "nope", "wrong", "not", "incorrect", "stop", "don't"]
        
        if any(w in text for w in yes_words):
            return True
        if any(w in text for w in no_words):
            return False
            
        return True # Default to True if unclear, to avoid blocking flow unnecessarily

    def listen_for_short_answer(self) -> str:
        """Listen for a short burst (e.g., missing name or email)."""
        text, _ = self.listen_with_confidence()
        return text

    def record_vad(self, samplerate: int = 16000, silence_threshold: float = 0.01, max_silence: float = 1.2, max_duration: float = 10.0) -> Optional[np.ndarray]:
        """Record audio using Voice Activity Detection."""
        chunk_duration = 0.1
        chunk_samples = int(samplerate * chunk_duration)
        audio_data = []
        silence_time = 0.0
        total_time = 0.0
        has_started = False

        with sd.InputStream(samplerate=samplerate, channels=1, dtype='float32') as stream:
            while total_time < max_duration:
                chunk, _ = stream.read(chunk_samples)
                audio_data.append(chunk)
                total_time += chunk_duration
                
                rms = np.sqrt(np.mean(chunk**2))
                if rms > silence_threshold:
                    has_started = True
                    silence_time = 0.0
                elif has_started:
                    silence_time += chunk_duration
                    
                if has_started and silence_time >= max_silence:
                    break
                    
        return np.concatenate(audio_data) if has_started else None

class TextToSpeech:
    def __init__(self, use_elevenlabs: bool = False, elevenlabs_key: str = None):
        self.use_elevenlabs = use_elevenlabs
        self.elevenlabs_key = elevenlabs_key
        self.engine = pyttsx3.init()
        self._init_engine()

    def _init_engine(self):
        self.engine.setProperty('rate', 170)
        voices = self.engine.getProperty('voices')
        # Prefer a clear male voice for BAYMAX identity
        for v in voices:
            if "david" in v.name.lower() or "zira" not in v.name.lower():
                self.engine.setProperty('voice', v.id)
                break

    def speak_and_wait(self, text: str):
        """Speak and pause briefly for natural flow."""
        self.speak(text)
        time.sleep(0.5)

    def speak_question(self, text: str):
        """Speak with a tone that suggests a question is being asked."""
        # pyttsx3 doesn't support complex prosody, but we can pause longer after
        self.speak(text)
        time.sleep(1.0)

    def beep_ready(self):
        """Play a short 'mm-hmm' sound or beep to signal listening."""
        # For now, use TTS to say a short signal
        self.speak("Mm-hmm?")

    def speak(self, text: str):
        # Strip markdown and symbols before speaking
        clean_text = re.sub(r'[*_#`─█✓✗⏳⚠]', '', text)
        clean_text = clean_text.replace('\n', '. ')
        
        if self.use_elevenlabs and self.elevenlabs_key:
            try:
                logger.info("Using ElevenLabs TTS...")
                voice_id = "pNInz6obpgDQGcFmaJgB" # Example voice ID (Adam or similar)
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream?output_format=pcm_44100"
                headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": self.elevenlabs_key
                }
                data = {
                    "text": clean_text,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.5
                    }
                }
                
                # Stream the PCM data
                with httpx.stream("POST", url, json=data, headers=headers, timeout=10.0) as response:
                    response.raise_for_status()
                    # Play stream directly with sounddevice
                    samplerate = 44100
                    stream = sd.OutputStream(samplerate=samplerate, channels=1, dtype='int16')
                    stream.start()
                    
                    # Read chunks
                    for chunk in response.iter_bytes(chunk_size=4096):
                        if chunk:
                            # Convert bytes to int16 numpy array
                            audio_data = np.frombuffer(chunk, dtype=np.int16)
                            stream.write(audio_data)
                            
                    stream.stop()
                    stream.close()
                return # Successfully spoke using ElevenLabs
            except Exception as e:
                logger.error(f"ElevenLabs TTS failed: {e}. Falling back to local TTS.")
                
        # Fallback to local TTS
        self.engine.say(clean_text)
        self.engine.runAndWait()
