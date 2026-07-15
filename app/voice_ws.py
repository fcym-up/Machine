"""Voice WebSocket — persistent connection."""
import traceback
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from app.services.voice.pipeline import run_pipeline

router = APIRouter()

@router.websocket("/api/v1/voice/ws")
async def voice_ws(ws: WebSocket):
    await ws.accept()
    buf = bytearray()
    try:
        while True:
            msg = await ws.receive()
            if "bytes" in msg:
                buf.extend(msg["bytes"])
            elif "text" in msg:
                if msg["text"] == "END":
                    audio = bytes(buf)
                    buf = bytearray()
                    if audio:
                        result = await run_pipeline(audio)
                        if result.error:
                            await ws.send_json({"type":"error","message":result.error})
                        else:
                            await ws.send_json({"type":"reply","transcript":result.text,"text":result.reply})
                            if result.audio:
                                await ws.send_bytes(result.audio)
                elif msg["text"] == "PING":
                    await ws.send_json({"type":"pong"})
    except WebSocketDisconnect:
        logger.info("Voice WS disconnected")
    except Exception as e:
        logger.error(f"Voice WS error: {e}")
        traceback.print_exc()
    try:
        await ws.close()
    except Exception:
        pass
