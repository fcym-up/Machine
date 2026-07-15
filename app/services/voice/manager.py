"""Voice session manager - streaming sessions with VAD and wake word."""
import time
import numpy as np
from dataclasses import dataclass, field
from loguru import logger
from app.services.voice.vad.silero_vad import SileroVAD


@dataclass
class VoiceSession:
    """A single voice stream session."""
    buffer: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float32))
    vad_state: dict = field(default_factory=lambda: {"speech_detected": False, "silence_frames": 0})
    last_active: float = field(default_factory=time.time)
    sample_rate: int = 16000
    wake_detected: bool = False


class VoiceManager:
    """Manages sessions with VAD and wake word."""

    def __init__(self, vad_threshold=0.5):
        self._sessions = {}
        self._vad = None
        self._wake = None

    def _get_vad(self):
        if self._vad is None:
            self._vad = SileroVAD()
        return self._vad

    def _get_wake(self):
        if self._wake is None:
            from app.services.voice.wake.openwakeword import WakeWordDetector
            self._wake = WakeWordDetector()
        return self._wake

    def create_session(self, session_id, sample_rate=16000):
        self._sessions[session_id] = VoiceSession(sample_rate=sample_rate)
        return self._sessions[session_id]

    def get_session(self, session_id):
        return self._sessions.get(session_id)

    def feed_audio(self, session_id, audio_chunk):
        session = self._sessions.get(session_id)
        if session is None: return None
        if isinstance(audio_chunk, bytes):
            audio_chunk = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
        session.buffer = np.concatenate([session.buffer[-session.sample_rate * 30:], audio_chunk])
        session.last_active = time.time()
        try:
            vad = self._get_vad()
            if vad.stream_speech_end(audio_chunk, session.vad_state):
                utterance = session.buffer.copy()
                start, end = vad.detect_utterance(utterance)
                if end > start: utterance = utterance[start:end]
                session.buffer = np.array([], dtype=np.float32)
                session.vad_state = {"speech_detected": False, "silence_frames": 0}
                if len(utterance) >= 160: return utterance
        except Exception as e:
            logger.warning("VAD error: %s" % e)
        return None

    def feed_wake_audio(self, session_id, audio_chunk):
        session = self._sessions.get(session_id)
        if session is None: return None
        if isinstance(audio_chunk, bytes):
            audio_chunk = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
        session.buffer = np.concatenate([session.buffer[-session.sample_rate * 30:], audio_chunk])
        session.last_active = time.time()
        if not session.wake_detected:
            wd = self._get_wake()
            if wd.detect(audio_chunk):
                session.wake_detected = True
                session.buffer = np.array([], dtype=np.float32)
                session.vad_state = {"speech_detected": False, "silence_frames": 0}
                return {"type": "wake"}
        else:
            try:
                vad = self._get_vad()
                if vad.stream_speech_end(audio_chunk, session.vad_state):
                    utterance = session.buffer.copy()
                    start, end = vad.detect_utterance(utterance)
                    if end > start: utterance = utterance[start:end]
                    session.buffer = np.array([], dtype=np.float32)
                    session.wake_detected = False
                    session.vad_state = {"speech_detected": False, "silence_frames": 0}
                    if len(utterance) >= 160:
                        return {"type": "utterance", "audio": utterance}
            except Exception as e:
                logger.warning("VAD error in wake: %s" % e)
        return None

    def force_flush(self, session_id):
        session = self._sessions.get(session_id)
        if session is None or len(session.buffer) < 160: return None
        utterance = session.buffer.copy()
        try:
            vad = self._get_vad()
            start, end = vad.detect_utterance(utterance)
            if end > start: utterance = utterance[start:end]
        except: pass
        session.buffer = np.array([], dtype=np.float32)
        session.vad_state = {"speech_detected": False, "silence_frames": 0}
        return utterance if len(utterance) >= 160 else None

    def remove_session(self, session_id):
        self._sessions.pop(session_id, None)

    def cleanup_stale(self, max_idle=300):
        now = time.time()
        stale = [s for s, sess in self._sessions.items() if now - sess.last_active > max_idle]
        for s in stale: self.remove_session(s)
        return len(stale)
