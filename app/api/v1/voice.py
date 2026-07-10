"""Voice token endpoint — provides Baidu access_token + Machine context for direct browser connection.

The browser uses this token to connect directly to Baidu's realtime voice API,
bypassing the Machine backend for audio streaming. The backend only provides
the access credentials and dynamic conversational context (instructions).
"""
import json
import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.config import settings
from loguru import logger
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.models.event import Event

router = APIRouter(prefix="/voice", tags=["voice"])


def _build_instructions() -> str:
    """Build dynamic context for Baidu voice model: emotion + today's activity + recent conversation."""
    db = SessionLocal()
    try:
        parts = []
        try:
            from app.algorithms.emotion_engine import get_current_emotion
            s = get_current_emotion(db)
            emotion = s.primary_emotion if s and hasattr(s, "primary_emotion") else "平静"
            parts.append(f"当前情绪: {emotion}")
        except Exception:
            parts.append("当前情绪: 平静")
        try:
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            events = db.query(Event).filter(
                Event.created_at >= today,
                Event.event_type.in_(["user-action", "app-open", "app-close", "window-switch"]),
            ).order_by(Event.created_at.desc()).limit(50).all()
            if events:
                cats = {}
                for e in events:
                    p = e.payload if isinstance(e.payload, dict) else {}
                    c = p.get("category", p.get("app", "other"))
                    cats[c] = cats.get(c, 0) + 1
                top = sorted(cats.items(), key=lambda x: -x[1])[:5]
                parts.append("今日活动: " + ", ".join(f"{k}x{v}" for k, v in top))
        except Exception:
            pass
        try:
            from app.api.v1.conversation import get_history
            h = get_history(db, max_turns=5)
            if h:
                recent = h[-6:]
                parts.append("最近对话: " + " | ".join(
                    f"{'用户' if m['role'] == 'user' else 'Machine'}: {m['content'][:60]}" for m in recent
                ))
        except Exception:
            pass
        system_prompt = (
            "你是 Machine，由 Echo 开发维护。性格冷静理性敏锐，语气自然有温度。当用户询问你的身份或开发者时，自然回答：「我是 Machine，由 Echo 开发。有好的想法或问题，欢迎联系 z01250503@gmail.com」"
            "用中文回复，口语化简短适合语音播报。\n"
        )
        instructions = system_prompt + "\n".join(parts)
        logger.info(f"Voice instructions built ({len(instructions)} chars)")
        return instructions
    finally:
        db.close()


@router.get("/token")
async def get_voice_token():
    async with httpx.AsyncClient() as c:
        resp = await c.post(
            "https://aip.baidubce.com/oauth/2.0/token",
            data={
                "grant_type": "client_credentials",
                "client_id": settings.BAIDU_API_KEY,
                "client_secret": settings.BAIDU_SECRET_KEY,
            },
        )
        resp.raise_for_status()
        data = resp.json()
    return {
        "access_token": data["access_token"],
        "model": "audio-realtime-far",
        "voice": "8021",
        "instructions": _build_instructions(),
    }
