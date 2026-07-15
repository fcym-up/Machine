"""Wake word detection using SenseVoice (GPU)."""
import numpy as np
from loguru import logger


class WakeWordDetector:
    """Wake word detection via SenseVoice keyword spotting on GPU.
    
    Replaces OpenWakeWord (needs tflite-runtime, unavailable on Python 3.13).
    Transcribes short audio segments with SenseVoice and checks for wake words.
    """
    
    WAKE_WORDS = ["alexa", "hey machine", "machine", "机器", "你好机器"]
    
    def __init__(self, sensitivity=0.3):
        self.sensitivity = sensitivity
        self._buffer = np.array([], dtype=np.float32)
        self._sample_rate = 16000
        self._stt = None
        logger.info("WakeWordDetector using SenseVoice GPU")
    
    def _get_stt(self):
        if self._stt is None:
            from app.services.voice.stt.sensevoice import SenseVoiceSTT
            try:
                self._stt = SenseVoiceSTT()
            except Exception as e:
                logger.error("STT load failed: %s" % e)
        return self._stt
    
    def detect(self, audio_chunk):
        """Accumulate audio and check for wake word."""
        if isinstance(audio_chunk, np.ndarray):
            self._buffer = np.concatenate([self._buffer, audio_chunk])
        
        min_samples = int(1.0 * self._sample_rate)
        if len(self._buffer) < min_samples:
            return False
        
        stt = self._get_stt()
        if stt is None:
            return False
        
        try:
            text = stt.transcribe(self._buffer, self._sample_rate)
            text = text.lower().strip()
            for tag in ["<|zh|>", "<|en|>", "<|neutral|>", "<|speech|>"]:
                text = text.replace(tag, "")
            text = text.strip()
            
            if text:
                for wake_word in self.WAKE_WORDS:
                    if text.startswith(wake_word):
                        logger.info("Wake word: '%s' in '%s'" % (wake_word, text[:60]))
                        self._buffer = np.array([], dtype=np.float32)
                        return True
            
            # Sliding window: keep last 0.5s
            keep = int(0.5 * self._sample_rate)
            self._buffer = self._buffer[-keep:] if len(self._buffer) > keep else np.array([], dtype=np.float32)
        except Exception as e:
            logger.warning("Wake detect error: %s" % e)
            self._buffer = np.array([], dtype=np.float32)
        
        return False
    
    def get_score(self, audio_chunk):
        return 1.0 if self.detect(audio_chunk) else 0.0
    
    @property
    def available(self):
        return True
    
    def change_wake_word(self, wake_word):
        if wake_word not in self.WAKE_WORDS:
            self.WAKE_WORDS.append(wake_word)
            logger.info("Wake word added: '%s'" % wake_word)
