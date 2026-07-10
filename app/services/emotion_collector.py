"""Signal collectors — gather emotion signals from all sources."""
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from loguru import logger

from app.models.emotion import EmotionSignal, SignalWeight
from app.models.event import Event

WINDOW_EMOTION_MAP = {
    "coding": "专注", "browsing": "平静", "social": "平静",
    "gaming": "放松", "music": "放松", "document": "专注",
    "terminal": "专注", "job": "焦虑", "video": "放松",
    "other": "平静",
}

TIME_EMOTION_MAP = {
    (0, 5): "疲惫", (5, 7): "专注", (7, 9): "开心",
    (9, 18): "专注", (18, 21): "放松", (21, 24): "平静",
}


def _get_weight(db: Session, source: str) -> float:
    row = db.query(SignalWeight).filter_by(source=source).first()
    return float(row.weight) if row else 0.1


def collect_window_signals(db: Session) -> int:
    """Collect signals from recent window-switch events."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    events = db.query(Event).filter(
        Event.event_type == "user-action",
        Event.source == "activity",
        Event.created_at >= cutoff,
    ).all()

    count = 0
    weight = _get_weight(db, "window")
    for e in events:
        payload = e.payload if isinstance(e.payload, dict) else {}
        category = payload.get("category", "other")
        emotion = WINDOW_EMOTION_MAP.get(category, "平静")
        duration = payload.get("duration", 0)
        confidence = min(0.8, max(0.1, duration / 300))

        db.add(EmotionSignal(
            source="window", emotion_label=emotion,
            weight=weight, confidence=confidence,
            payload={"category": category, "app": payload.get("app", ""),
                     "process": payload.get("process", ""),
                     "factor": f"在 {payload.get('app','某应用')} 工作了 {duration} 秒"},
            event_id=e.id,
        ))
        count += 1
    if count > 0:
        db.commit()
    return count


def collect_idle_signals(db: Session) -> int:
    """Collect idle signals — only emit when idle state changes."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    idle_events = db.query(Event).filter(
        Event.event_type == "system-event",
        Event.source == "system",
        Event.created_at >= cutoff,
    ).all()

    count = 0
    weight = _get_weight(db, "idle")
    for e in idle_events:
        payload = e.payload if isinstance(e.payload, dict) else {}
        if payload.get("state") == "away":
            db.add(EmotionSignal(
                source="idle", emotion_label="疲惫",
                weight=weight, confidence=0.6,
                payload={"factor": "长时间离开键盘"},
                event_id=e.id,
            ))
            count += 1
    if count > 0:
        db.commit()
    return count


def collect_time_signal(db: Session) -> int:
    """Collect time-based signal (called once per compute cycle)."""
    hour = datetime.now(timezone.utc).hour + 8  # UTC+8
    if hour >= 24:
        hour -= 24

    emotion = "平静"
    for (start, end), em in TIME_EMOTION_MAP.items():
        if start <= hour < end:
            emotion = em
            break

    weight = _get_weight(db, "time")
    db.add(EmotionSignal(
        source="time", emotion_label=emotion,
        weight=weight, confidence=0.5,
        payload={"factor": f"当前时段: {hour}:00"},
    ))
    db.commit()
    return 1


def inject_conversation_signal(
    db: Session, emotion_label: str, confidence: float = 0.7,
    payload: dict | None = None,
) -> EmotionSignal | None:
    """Inject a conversation-derived emotion signal (called from chat API)."""
    if emotion_label not in ("焦虑", "开心", "疲惫", "专注", "放松", "平静", "沮丧", "好奇"):
        return None
    weight = _get_weight(db, "conversation")
    sig = EmotionSignal(
        source="conversation", emotion_label=emotion_label,
        weight=weight, confidence=confidence,
        payload=payload or {},
    )
    db.add(sig)
    db.commit()
    db.refresh(sig)
    return sig


def collect_all(db: Session) -> dict:
    """Run all collectors, return counts."""
    result = {}
    try:
        result["window"] = collect_window_signals(db)
    except Exception as e:
        logger.warning(f"Window signal collect error: {e}")
        result["window"] = 0
    try:
        result["idle"] = collect_idle_signals(db)
    except Exception as e:
        logger.warning(f"Idle signal collect error: {e}")
        result["idle"] = 0
    try:
        result["time"] = collect_time_signal(db)
    except Exception as e:
        logger.warning(f"Time signal collect error: {e}")
        result["time"] = 0
    return result
