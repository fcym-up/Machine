"""Text-to-speech services."""
from app.services.voice.tts.kokoro_tts import KokoroTTSService
from app.services.voice.tts.edge_tts import EdgeTTSService as EdgeTTSService

__all__ = ["KokoroTTSService", "EdgeTTSService"]
