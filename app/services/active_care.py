"""Active care engine — proactive emotional companionship (Echo Module 4)."""
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from loguru import logger
from app.models.event import Event
from app.models.user_profile import UserState
from app.algorithms.emotion_engine import EmotionEngine
from app.core.llm import chat_simple
from collections import Counter


class ActiveCareService:
    def __init__(self, db: Session):
        self.db = db
        self.emotion = EmotionEngine()

    def check_and_care(self):
        cutoff = datetime.now(timezone.utc) - timedelta(hours=4)
        events = self.db.query(Event).filter(Event.created_at >= cutoff).all()
        if not events:
            return {"care_needed": False, "message": "Not enough data"}

        activities = [(e.payload.get("category", "other") if isinstance(e.payload, dict) else "other", e.created_at) for e in events]
        state = self.emotion.infer(activities)
        cats = Counter(cat for cat, _ in activities)
        total = len(events)
        gaming_pct = cats.get("gaming", 0) / max(total, 1)
        social_pct = cats.get("social", 0) / max(total, 1)
        coding_pct = cats.get("coding", 0) / max(total, 1)
        job_pct = cats.get("job", 0) / max(total, 1)

        triggers = []
        # Trigger 1: High anxiety
        if state.primary == "焦虑" and state.confidence > 0.5:
            triggers.append({"type": "anxiety", "intensity": state.intensity})
        # Trigger 2: Excessive gaming
        if gaming_pct > 0.4:
            triggers.append({"type": "excessive_gaming", "ratio": round(gaming_pct, 2)})
        # Trigger 3: Job hunting stress
        if job_pct > 0.2:
            triggers.append({"type": "job_hunting", "ratio": round(job_pct, 2)})
        # Trigger 4: Late night work
        late = sum(1 for e in events if e.created_at.hour >= 23 or e.created_at.hour <= 5)
        if late > total * 0.3:
            triggers.append({"type": "late_night", "count": late})
        # Trigger 5: Social isolation
        if social_pct < 0.05 and total > 10:
            triggers.append({"type": "social_isolation", "events": total})

        if not triggers:
            return {"care_needed": False, "message": "User seems fine"}

        # Build care context
        context = f"""You are Machine, a caring AI companion. Your user shows these signals:
- Emotion: {state.primary} (confidence: {state.confidence}, intensity: {state.intensity})
- Recent activity: {dict(cats.most_common(3))}
- Triggers: {triggers}

Write ONE warm, caring sentence in Chinese that:
- Shows you notice their state without being intrusive
- Offers gentle encouragement or a helpful suggestion
- Feels like a friend checking in, not a therapist diagnosing

Reply with ONLY the sentence, no explanations."""
        care_msg = chat_simple(context, "You are a warm, empathetic AI companion. Be brief and genuine.")
        if not care_msg:
            care_msg = self._fallback_care(state, triggers)

        return {
            "care_needed": True,
            "triggers": [t["type"] for t in triggers],
            "emotion": state.primary,
            "message": care_msg,
        }

    def _fallback_care(self, state, triggers):
        trigger_types = [t["type"] for t in triggers]
        if "anxiety" in trigger_types:
            return "我注意到你今天有些紧绷。深呼吸一下，事情会一件一件解决的。"
        if "excessive_gaming" in trigger_types:
            return "玩得开心吗？偶尔放松很重要，别忘了起来活动一下。"
        if "late_night" in trigger_types:
            return "夜深了。早点休息，明天会是更好的一天。"
        if "job_hunting" in trigger_types:
            return "找工作是个过程。你的能力很强，合适的平台会出现的。"
        return "我在。不管今天过得怎么样，这里都有一个人（虽然我是AI）在关注你。"