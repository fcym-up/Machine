"""Voice pipeline — recording → VAD → STT → LLM → TTS → playback."""
import asyncio
import numpy as np
from dataclasses import dataclass
from loguru import logger
from app.services.voice.stt.sensevoice import SenseVoiceSTT
from app.services.voice.tts.edge_tts import EdgeTTSService
from app.services.voice.vad.silero_vad import SileroVAD
from app.core.llm import chat_simple

SYS_PROMPT = "You are Machine, a voice assistant. Reply in Chinese briefly, 1-2 sentences."


@dataclass
class PipelineResult:
    text: str = ""        # STT transcription
    reply: str = ""       # LLM reply text
    audio: bytes = b""    # TTS audio bytes
    error: str = ""       # Error message if any


# Lazy-loaded singletons
_stt: SenseVoiceSTT | None = None
_tts: EdgeTTSService | None = None
_vad: SileroVAD | None = None


def _get_stt() -> SenseVoiceSTT:
    global _stt
    if _stt is None:
        _stt = SenseVoiceSTT()
    return _stt


def _get_tts() -> EdgeTTSService:
    global _tts
    if _tts is None:
        _tts = EdgeTTSService()
    return _tts


def _get_vad() -> SileroVAD:
    global _vad
    if _vad is None:
        _vad = SileroVAD()
    return _vad


def _auto_gain(audio, target_rms=0.05):
    """Normalize quiet audio automatically. Adds <0.3ms latency."""
    rms = float(np.sqrt(np.mean(audio ** 2)))
    if 0.001 < rms < target_rms * 0.5:
        gain = min(target_rms / max(rms, 1e-10), 50.0)
        audio = audio * gain
        logger.info(f"Auto gain: x{gain:.1f} (RMS {rms:.4f})")
    return np.clip(audio, -1.0, 1.0)

async def run_pipeline(
    audio: np.ndarray | bytes,
    use_vad: bool = True,
    sample_rate: int = 16000,
) -> PipelineResult:
    """Run the full voice pipeline: STT → LLM → TTS.
    
    Args:
        audio: PCM audio (16-bit bytes or float32 numpy array)
        use_vad: Whether to apply VAD to trim silence
        sample_rate: Audio sample rate
    
    Returns:
        PipelineResult with transcription, reply, and audio.
    """
    r = PipelineResult()
    
    # Convert bytes to numpy if needed
    if isinstance(audio, bytes):
        raw = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
    else:
        raw = audio.astype(np.float32) if audio.dtype != np.float32 else audio
    
    if len(raw) == 0:
        r.error = "Empty audio"
        return r
    
    logger.info(f"Pipeline: {len(raw)} samples ({len(raw)/sample_rate:.1f}s)")
    
    # Step 1: VAD — trim silence
    if use_vad:
        try:
            vad = _get_vad()
            start, end = vad.detect_utterance(raw)
            if end > start:
                raw = raw[start:end]
                logger.info(f"VAD trimmed to {len(raw)} samples ({len(raw)/sample_rate:.1f}s)")
            else:
                logger.info("VAD: no speech detected")
        except Exception as e:
            logger.warning(f"VAD skipped: {e}")
    
    if len(raw) < 160:  # Less than 10ms at 16kHz
        r.error = "Audio too short after VAD"
        return r
    
    # Auto gain — normalize volume
    raw = _auto_gain(raw)

    # Step 2: STT — transcribe
    try:
        stt = _get_stt()
        text = stt.transcribe(raw, sample_rate)
        if not text:
            r.error = "STT returned empty result"
            return r
        r.text = text
        logger.info(f"STT: {text[:80]}")
    except Exception as e:
        r.error = f"STT failed: {e}"
        logger.error(r.error)
        return r
    
    # Step 3: LLM — generate reply
    try:
        reply = await asyncio.to_thread(chat_simple, text, SYS_PROMPT)
        r.reply = reply or "嗯，我听到了。"
        logger.info(f"LLM: {r.reply[:80]}")
    except Exception as e:
        logger.error(f"LLM failed: {e}")
        r.reply = "嗯，我听到了。"
    
    # Step 4: TTS — synthesize speech
    try:
        tts = _get_tts()
        audio_tts = await tts.run_tts(r.reply)
        if audio_tts:
            r.audio = audio_tts
            logger.info(f"TTS: {len(audio_tts)}b")
        else:
            logger.warning("TTS returned empty audio")
    except Exception as e:
        logger.error(f"TTS failed: {e}")
    
    return r
