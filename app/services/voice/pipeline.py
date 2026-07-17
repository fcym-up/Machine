"""Voice pipeline — STT → Machine Context → LLM Stream → TTS Stream.

Async flowing pipeline with full Machine integration:
- STT runs in thread pool (no event-loop blocking)
- LLM streams sentence by sentence
- TTS runs in parallel for each sentence
- Voice events written back to the Machine system
- Kokoro TTS primary, Edge TTS fallback
"""
import asyncio
import time

import numpy as np
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from loguru import logger

from app.core.database import SessionLocal
from app.core.llm import chat_simple, chat_stream


@dataclass
class PipelineResult:
    """Full pipeline output."""
    text: str = ""
    reply: str = ""
    error: str = ""
    context: dict = field(default_factory=dict)


_stt = None
_tts_kokoro = None
_tts_edge = None
_vad_singleton = None


def _get_stt():
    global _stt
    if _stt is None:
        from app.services.voice.stt.sensevoice import SenseVoiceSTT
        _stt = SenseVoiceSTT()
    return _stt


def _get_vad():
    global _vad_singleton
    if _vad_singleton is None:
        from app.services.voice.vad.silero_vad import SileroVAD
        _vad_singleton = SileroVAD()
    return _vad_singleton


async def _kokoro_tts(text: str) -> bytes:
    global _tts_kokoro
    if _tts_kokoro is None:
        try:
            from app.services.voice.tts.kokoro_tts import KokoroTTSService
            _tts_kokoro = KokoroTTSService()
            logger.info("Kokoro TTS loaded")
        except Exception as e:
            logger.warning(f"Kokoro unavailable: {e}")
            _tts_kokoro = False
    if _tts_kokoro is False:
        return await _tts_fallback(text)
    try:
        result = await _tts_kokoro.run_tts(text)
        if result:
            return result
    except Exception as e:
        logger.warning(f"Kokoro TTS error: {e}")
    return await _tts_fallback(text)


async def _tts_fallback(text: str) -> bytes:
    global _tts_edge
    if _tts_edge is None:
        try:
            from app.services.voice.tts.edge_tts import EdgeTTSService
            _tts_edge = EdgeTTSService()
            logger.info("Edge TTS loaded as fallback")
        except Exception as e:
            logger.error(f"Edge TTS failed: {e}")
            _tts_edge = False
    if _tts_edge is False:
        return b""
    try:
        return await _tts_edge.run_tts(text)
    except Exception as e:
        logger.error(f"Edge TTS error: {e}")
        return b""


def _auto_gain(audio: np.ndarray, target_rms: float = 0.05) -> np.ndarray:
    rms = float(np.sqrt(np.mean(audio ** 2)))
    if 0.001 < rms < target_rms * 0.5:
        gain = min(target_rms / max(rms, 1e-10), 50.0)
        audio = audio * gain
    return np.clip(audio, -1.0, 1.0)


def _write_voice_event(db: Session, event_type: str, transcript: str,
                       reply: str = "", duration_ms: float = 0):
    try:
        from app.models.event import Event
        payload = {"transcript": transcript}
        if reply:
            payload["reply_text"] = reply
        if duration_ms:
            payload["duration_ms"] = duration_ms
        event = Event(
            event_type=event_type,
            source="voice",
            payload=payload,
        )
        db.add(event)
        db.commit()
        logger.info(f"Voice event: {event_type} ({len(transcript)} chars)")
    except Exception as e:
        logger.warning(f"Voice event write failed: {e}")
        db.rollback()


async def run_pipeline(
    audio: np.ndarray | bytes,
    use_vad: bool = False,
    sample_rate: int = 16000,
    on_audio_chunk=None,
) -> PipelineResult:
    """Run the full voice pipeline with Machine context.

    Args:
        audio: PCM audio (bytes or float32 numpy array).
        use_vad: apply VAD to trim silence (False for STREAM mode).
        sample_rate: always 16000.
        on_audio_chunk: async callback(bytes) for streaming TTS audio.
    """
    r = PipelineResult()
    t0 = time.time()

    if isinstance(audio, bytes):
        raw = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
    else:
        raw = audio.astype(np.float32)

    if len(raw) < 160:
        r.error = "Audio too short"
        return r

    if use_vad:
        try:
            vad = _get_vad()
            start, end = vad.detect_utterance(raw)
            if end > start:
                raw = raw[start:end]
            else:
                r.error = "No speech detected"
                return r
        except Exception as e:
            logger.warning(f"VAD skipped: {e}")

    raw = _auto_gain(raw)

    # STT in thread pool
    try:
        stt = _get_stt()
        text = await asyncio.to_thread(stt.transcribe, raw, sample_rate)
        if not text:
            r.error = "STT returned empty result"
            return r
        r.text = text
        logger.info(f"STT: {text[:80]}")
    except Exception as e:
        r.error = f"STT failed: {e}"
        return r

    duration_ms = int((time.time() - t0) * 1000)

    # Load Machine context
    db = SessionLocal()
    try:
        from app.services.voice.voice_context import build_voice_context
        ctx = build_voice_context(db, r.text)
        _write_voice_event(db, "voice_input", r.text, duration_ms=duration_ms)
    except Exception as e:
        logger.warning(f"Context load failed: {e}")
        ctx = {
            "system_prompt": "你是 Machine，一个 AI 伴侣。请用中文回复，简洁温暖（2-4句话）。",
            "emotion": "未知",
            "emotion_intensity": 0.5,
            "rhythm": "",
            "main_activity": "",
            "recent_memories": [],
            "entities": [],
        }
    finally:
        db.close()

    r.context = ctx
    system_prompt = ctx["system_prompt"]

    # LLM stream + TTS parallel
    all_replies = []
    try:
        async for sentence in chat_stream(r.text, system_prompt):
            sentence = sentence.strip()
            if not sentence:
                continue
            all_replies.append(sentence)
            audio_out = await _kokoro_tts(sentence)
            if audio_out and on_audio_chunk:
                await on_audio_chunk(audio_out)
    except Exception as e:
        logger.error(f"LLM stream error: {e}")
        if not all_replies:
            fallback = await asyncio.to_thread(
                chat_simple, r.text, "你是 Machine。请用中文回复，简洁温暖（1-2句话）。"
            )
            if fallback:
                all_replies.append(fallback)

    r.reply = "".join(all_replies)
    if not r.reply:
        r.reply = "嗯，我听到了。"

    # Write voice reply event
    db2 = SessionLocal()
    try:
        _write_voice_event(db2, "voice_reply", r.text, reply=r.reply,
                           duration_ms=int((time.time() - t0) * 1000))
    except Exception as e:
        logger.warning(f"Voice reply event failed: {e}")
    finally:
        db2.close()

    logger.info(f"Pipeline: '{r.text[:30]}' -> '{r.reply[:30]}' ({int((time.time()-t0)*1000)}ms)")
    return r
