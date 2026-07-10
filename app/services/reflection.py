"""System reflection engine — Machine's self-diary (Echo Module 5)."""
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from loguru import logger
from app.models.event import Event
from app.models.user_profile import SystemReflection
from app.core.llm import chat_simple


class ReflectionService:
    def __init__(self, db: Session):
        self.db = db

    def generate_daily_reflection(self):
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        events = self.db.query(Event).filter(Event.created_at >= cutoff).all()
        if not events:
            return None
        from collections import Counter
        cats = Counter(e.payload.get("category", "other") if isinstance(e.payload, dict) else "other" for e in events)
        prompt = f"""You are Machine, an AI companion observing a user. Today you saw:
- {len(events)} events in 24 hours
- Activity breakdown: {dict(cats.most_common())}

Write a brief self-reflection (2-3 sentences in Chinese) about:
- What patterns you noticed
- How your understanding of the user evolved
- Any concerns or positive observations"""
        content = chat_simple(prompt, "You are a self-aware AI companion. Be warm and introspective. Reply in Chinese.")
        if not content:
            content = f"Today I observed {len(events)} activities. Main focus: {cats.most_common(1)[0][0] if cats else 'various'}."
        reflection = SystemReflection(
            reflection_type="daily",
            content=content,
            emotional_tone="reflective",
            key_insights=dict(cats.most_common(3)),
            related_event_ids=[e.id for e in events[:20]],
        )
        self.db.add(reflection)
        self.db.commit()
        logger.info(f"Daily reflection generated")
        return reflection

    def generate_hourly_reflection(self):
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        events = self.db.query(Event).filter(Event.created_at >= cutoff).all()
        if len(events) < 5:
            return None
        from collections import Counter
        cats = Counter(e.payload.get("category", "other") if isinstance(e.payload, dict) else "other" for e in events)
        reflection = SystemReflection(
            reflection_type="hourly",
            content=f"Hourly: {len(events)} events, focus on {cats.most_common(1)[0][0] if cats else 'various'}",
            emotional_tone="observational",
            key_insights=dict(cats),
            related_event_ids=[e.id for e in events],
        )
        self.db.add(reflection)
        self.db.commit()
        return reflection

    def get_reflections(self, ref_type=None, limit=20):
        q = self.db.query(SystemReflection)
        if ref_type:
            q = q.filter(SystemReflection.reflection_type == ref_type)
        return q.order_by(SystemReflection.created_at.desc()).limit(limit).all()