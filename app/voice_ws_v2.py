"""Voice WebSocket v2 — streaming VAD with Machine-integrated pipeline."""
import traceback, time, json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from app.services.voice.manager import VoiceManager
from app.services.voice.pipeline import run_pipeline

router = APIRouter()
_manager = VoiceManager()


@router.websocket('/api/v1/voice/v2/ws')
async def voice_ws_v2(ws: WebSocket):
    await ws.accept()
    session_id = f"ws_{id(ws)}_{int(time.time()*1000)}"
    buf = bytearray()
    mode = "manual"
    started = False

    try:
        await ws.send_json({
            "type": "connected", "session": session_id, "mode": mode,
            "message": "Voice v2 ready. Send PCM16 16kHz mono audio."
        })

        while True:
            msg = await ws.receive()

            if "bytes" in msg:
                data = msg["bytes"]
                if mode == "stream":
                    if not started:
                        _manager.create_session(session_id)
                        started = True
                    utterance = _manager.feed_audio(session_id, data)
                    if utterance is not None:
                        await _process_utterance(ws, utterance)

                elif mode == "manual":
                    buf.extend(data)

            elif "text" in msg:
                text = msg["text"]
                if text == "END":
                    if not buf:
                        await ws.send_json({"type": "error", "message": "No audio data"})
                        continue
                    audio = bytes(buf)
                    buf = bytearray()
                    if mode == "stream":
                        utterance = _manager.force_flush(session_id)
                        if utterance is not None:
                            await _process_utterance(ws, utterance)
                    else:
                        await _process_utterance(ws, audio)

                elif text == "STREAM":
                    mode = "stream"
                    await ws.send_json({
                        "type": "mode_change", "mode": "stream",
                        "message": "Streaming mode: speak naturally, VAD auto-detects end."
                    })

                elif text == "MANUAL":
                    mode = "manual"
                    _manager.remove_session(session_id)
                    started = False
                    buf = bytearray()
                    await ws.send_json({
                        "type": "mode_change", "mode": "manual",
                        "message": "Manual mode: send audio, use END to process."
                    })

                elif text == "PING":
                    await ws.send_json({"type": "pong"})

                elif text == "STATUS":
                    await ws.send_json({
                        "type": "status", "session": session_id, "mode": mode,
                        "buffer_size": len(buf),
                    })

    except WebSocketDisconnect:
        logger.info(f"Voice WS disconnect: {session_id}")
    except Exception as e:
        logger.error(f"Voice WS error: {e}")
        traceback.print_exc()
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        _manager.remove_session(session_id)
        try:
            await ws.close()
        except Exception:
            pass


async def _process_utterance(ws: WebSocket, audio):
    """Run pipeline on utterance and stream results back."""

    async def send_audio(chunk: bytes):
        try:
            await ws.send_bytes(chunk)
        except Exception:
            pass

    result = await run_pipeline(audio, use_vad=False, on_audio_chunk=send_audio)

    if result.error:
        await ws.send_json({"type": "error", "message": result.error})
        return

    await ws.send_json({
        "type": "reply",
        "transcript": result.text,
        "text": result.reply,
        "emotion": result.context.get("emotion", ""),
    })
