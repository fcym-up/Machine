"""Microsoft Edge TTS service — free, fast, no API key needed."""
import edge_tts
from loguru import logger

VOICE = "zh-CN-XiaoxiaoNeural"


class EdgeTTSService:
    """Text-to-speech using Microsoft Edge's free TTS engine."""
    
    def __init__(self, voice: str = VOICE):
        self.voice = voice
    
    async def run_tts(self, text: str) -> bytes:
        if not text:
            return b""
        try:
            chunks = []
            communicate = edge_tts.Communicate(text, self.voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    chunks.append(chunk["data"])
            result = b"".join(chunks)
            logger.info(f"EdgeTTS: {len(result)}b for '{text[:30]}...'")
            return result
        except Exception as e:
            logger.error(f"EdgeTTS failed: {e}")
            return b""
    
    def set_voice(self, voice: str):
        """Change TTS voice."""
        self.voice = voice
        logger.info(f"TTS voice changed to: {voice}")
