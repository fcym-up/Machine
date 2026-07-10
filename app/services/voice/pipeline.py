"""Voice pipeline - builds context for Baidu voice model."""
from datetime import datetime, timezone
from loguru import logger
from app.core.database import SessionLocal
from app.models.event import Event


def _build_instructions() -> str:
    """Build dynamic context for Baidu voice model."""
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
                Event.event_type.in_(["user-action", "app-open", "app-close", "window-switch"])
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
        system = (
            "你是 Machine，长期陪伴用户的个人AI系统。"
            "性格冷静理性敏锐，语气自然有温度。"
            "用中文回复，口语化简短适合语音播报。\n"
        )
        instructions = system + "\n".join(parts)
        logger.info(f"Voice instructions built ({len(instructions)} chars)")
        return instructions
    finally:
        db.close()
