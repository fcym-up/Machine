"""Kokoro TTS - local GPU-based Chinese text-to-speech."""
import os, io, asyncio, numpy as np
from loguru import logger
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


class KokoroTTSService:
    """Local TTS using Kokoro-82M model on GPU (hexgrad/Kokoro-82M, ~312MB)."""
    
    def __init__(self, voice="zf_xiaoxiao", device="cuda:0"):
        self.voice_name = voice
        self.device = device
        self._pipeline = None
        self._sample_rate = 24000
    
    def _load(self):
        if self._pipeline is not None:
            return
        from kokoro import KPipeline
        self._pipeline = KPipeline(lang_code="z", repo_id="hexgrad/Kokoro-82M", device=self.device)
        self._pipeline.load_voice(self.voice_name)
        logger.info(f"Kokoro TTS ready (voice={self.voice_name})")
    
    async def run_tts(self, text: str) -> bytes:
        if not text:
            return b""
        self._load()
        try:
            import soundfile as sf
            def generate():
                chunks = [a for _, _, a in self._pipeline(text, voice=self.voice_name, speed=1.0)]
                if not chunks:
                    return b""
                buf = io.BytesIO()
                sf.write(buf, np.concatenate(chunks), self._sample_rate, format="wav")
                return buf.getvalue()
            audio = await asyncio.to_thread(generate)
            logger.info(f"Kokoro: {len(audio)}b for '{text[:30]}'")
            return audio
        except Exception as e:
            logger.error(f"Kokoro error: {e}")
            return b""
    
    @property
    def sample_rate(self):
        return self._sample_rate
    
    def set_voice(self, voice):
        self.voice_name = voice
        if self._pipeline:
            try:
                self._pipeline.load_voice(voice)
                logger.info(f"Voice changed: {voice}")
            except: pass
