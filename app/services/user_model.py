"""User model service — trait dimensions, state snapshots, behavior patterns."""
from datetime import datetime, timezone, timedelta
from collections import Counter
from sqlalchemy.orm import Session
from loguru import logger
from app.models.event import Event
from app.models.user_profile import TraitDimension, UserState, BehaviorPattern
from app.algorithms.emotion_engine import EmotionEngine

DIMENSIONS = ["productivity", "social_energy", "emotional_stability", "curiosity", "focus_depth"]


class UserModelService:
    def __init__(self, db: Session):
        self.db = db
        self.emotion = EmotionEngine()

    def update_dimensions(self, lookback_hours: int = 24):
        cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        events = self.db.query(Event).filter(Event.created_at >= cutoff).all()
        if not events:
            return {"message": "No events to analyze"}
        cats = Counter()
        hours = []
        for e in events:
            cat = e.payload.get("category", "other") if isinstance(e.payload, dict) else "other"
            cats[cat] += 1
            hours.append(e.created_at.hour)
        total = len(events)
        coding_pct = cats.get("coding", 0) / max(total, 1)
        social_pct = cats.get("social", 0) / max(total, 1)
        novel_cats = sum(1 for c in cats if cats[c] == 1)
        curiosity = novel_cats / max(len(cats), 1)
        # Focus depth: coding events with long streaks
        coding_events = [e for e in events if e.payload.get("category", "") == "coding"]
        focus_depth = min(len(coding_events) / max(total, 1) * 2, 1.0) if coding_events else 0.3
        # Emotional stability
        activities = [(e.payload.get("category", "other") if isinstance(e.payload, dict) else "other", e.created_at) for e in events]
        state = self.emotion.infer(activities)
        stability = 0.7 if state.confidence > 0.5 else 0.4
        values = {
            "productivity": round(coding_pct, 3),
            "social_energy": round(social_pct, 3),
            "emotional_stability": round(stability, 3),
            "curiosity": round(curiosity, 3),
            "focus_depth": round(focus_depth, 3),
        }
        for dim, val in values.items():
            existing = self.db.query(TraitDimension).filter(TraitDimension.dimension == dim).first()
            if existing:
                old_val = existing.current_value
                if val > old_val * 1.05:
                    existing.trend_direction = "up"
                elif val < old_val * 0.95:
                    existing.trend_direction = "down"
                else:
                    existing.trend_direction = "stable"
                existing.current_value = val
                existing.evidence_events = list(cats.most_common(5))
            else:
                self.db.add(TraitDimension(
                    dimension=dim, current_value=val,
                    trend_direction="stable",
                    evidence_events=list(cats.most_common(5))))
        self.db.commit()
        logger.info(f"Dimensions updated: {values}")
        return values

    def update_state(self):
        cutoff = datetime.now(timezone.utc) - timedelta(hours=4)
        events = self.db.query(Event).filter(Event.created_at >= cutoff).all()
        activities = [(e.payload.get("category", "other") if isinstance(e.payload, dict) else "other", e.created_at) for e in events]
        emo_state = self.emotion.infer(activities)
        cats = Counter()
        for e in events:
            cat = e.payload.get("category", "other") if isinstance(e.payload, dict) else "other"
            cats[cat] += 1
        total = max(len(events), 1)
        coding_ratio = cats.get("coding", 0) / total
        social_ratio = cats.get("social", 0) / total
        energy = min(coding_ratio * 0.6 + social_ratio * 0.3 + emo_state.intensity * 0.3, 1.0)
        focus = min(coding_ratio * 0.8 + (1 - social_ratio) * 0.3, 1.0)
        last_ts = events[-1].created_at if events else None
        summary = f"State: {emo_state.primary} emotion, {len(events)} activities in 4h, top: {cats.most_common(1)[0][0] if cats else 'none'}"
        existing = self.db.query(UserState).order_by(UserState.id.desc()).first()
        if existing:
            existing.emotional_state = emo_state.primary
            existing.energy_level = round(energy, 3)
            existing.focus_level = round(focus, 3)
            existing.active_topics = dict(cats.most_common(5))
            existing.social_engagement = round(social_ratio, 3)
            existing.last_activity_at = last_ts
            existing.summary_text = summary
        else:
            self.db.add(UserState(
                emotional_state=emo_state.primary,
                energy_level=round(energy, 3),
                focus_level=round(focus, 3),
                active_topics=dict(cats.most_common(5)),
                social_engagement=round(social_ratio, 3),
                last_activity_at=last_ts,
                summary_text=summary))
        self.db.commit()
        return {
            "emotional_state": emo_state.primary,
            "energy": round(energy, 3),
            "focus": round(focus, 3),
            "active_topics": dict(cats.most_common(5)),
            "events_count": len(events),
        }

    def get_model(self):
        dims = self.db.query(TraitDimension).all()
        state = self.db.query(UserState).order_by(UserState.id.desc()).first()
        patterns = self.db.query(BehaviorPattern).filter(BehaviorPattern.active == True).order_by(BehaviorPattern.frequency.desc()).limit(10).all()
        return {
            "dimensions": [{"dimension": d.dimension, "value": d.current_value, "trend": d.trend_direction} for d in dims],
            "state": {
                "emotional": state.emotional_state if state else "unknown",
                "energy": state.energy_level if state else 0.5,
                "focus": state.focus_level if state else 0.5,
                "topics": state.active_topics if state else {},
                "summary": state.summary_text if state else "",
            },
            "patterns": [{"type": p.pattern_type, "frequency": p.frequency, "confidence": p.confidence} for p in patterns],
        }