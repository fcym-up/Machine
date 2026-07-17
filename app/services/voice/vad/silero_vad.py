"""Silero VAD 鈥?voice activity detection on GPU."""
import torch
import numpy as np
from loguru import logger
import silero_vad


class SileroVAD:
    """Voice Activity Detection using Silero VAD model.
    
    Detects speech presence in audio chunks.
    Runs on GPU by default.
    """
    
    def __init__(self, threshold: float = 0.5, sample_rate: int = 16000):
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.model = None
        self._load_model()
    
    def _load_model(self):
        try:
            self.model = silero_vad.load_silero_vad()
            self.model.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
            device = "GPU" if torch.cuda.is_available() else "CPU"
            logger.info(f"Silero VAD loaded on {device}")
        except Exception as e:
            logger.error(f"Failed to load Silero VAD: {e}")
            raise
    
    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """Detect if an audio chunk contains speech."""
        if self.model is None or len(audio_chunk) == 0:
            return False
        prob = self.model(audio_chunk, self.sample_rate)
        return prob > self.threshold
    
    def detect_utterance(self, audio: np.ndarray) -> tuple[int, int]:
        """Find speech start/end indices in an audio array.
        
        Returns (start_sample, end_sample).
        """
        if self.model is None or len(audio) == 0:
            return (0, 0)
        speeches = self.model.get_speech_timestamps(audio, self.sample_rate)
        if not speeches:
            return (0, 0)
        start = speeches[0]["start"]
        end = speeches[-1]["end"]
        return (start, end)
    
    @torch.no_grad()
    def stream_speech_end(self, audio_chunk: np.ndarray, state: dict) -> bool:
        """Process streaming audio chunk, return True if speech segment ended.
        
        state: dict with 'speech_detected' and 'silence_frames' counters.
        """
        is_sp = self.is_speech(audio_chunk)
        if is_sp:
            state["speech_detected"] = True
            state["silence_frames"] = 0
        elif state["speech_detected"]:
            state["silence_frames"] += 1
        
        # Consider speech ended after ~2s of silence (4 frames x 500ms chunks)
        SPEECH_END_FRAMES = 4
        if state["speech_detected"] and state["silence_frames"] >= SPEECH_END_FRAMES:
            state["speech_detected"] = False
            state["silence_frames"] = 0
            return True
        return False
