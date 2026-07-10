"""Behavior mapping engine — discover user patterns from event streams (Echo Section 3)."""
from datetime import datetime, timezone, timedelta
from collections import Counter
from sqlalchemy.orm import Session
from loguru import logger
from app.models.event import Event
from app.models.user_profile import BehaviorPattern


class BehaviorMappingService:
    def __init__(self, db: Session):
        self.db = db

    def scan_hourly(self):
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        events = self.db.query(Event).filter(Event.created_at >= cutoff).order_by(Event.created_at).all()
        if len(events) < 10:
            return {"discovered": 0}
        self._detect_daily_rhythms(events)
        self._detect_emotion_triggers(events)
        self._detect_anomalies(events)
        return {"discovered": self.db.query(BehaviorPattern).filter(BehaviorPattern.active == True).count()}

    def _detect_daily_rhythms(self, events):
        hourly = Counter(e.created_at.hour for e in events)
        total = len(events)
        for hour, cnt in hourly.items():
            if cnt > total * 0.15:
                existing = self.db.query(BehaviorPattern).filter(
                    BehaviorPattern.pattern_type == "daily",
                    BehaviorPattern.trigger_events.contains({"hour": hour})).first()
                if existing:
                    existing.frequency += 1
                    existing.last_seen = datetime.now(timezone.utc)
                    existing.confidence = min(existing.confidence + 0.05, 0.95)
                else:
                    self.db.add(BehaviorPattern(
                        pattern_type="daily",
                        trigger_events={"hour": hour, "count": cnt},
                        frequency=1,
                        confidence=0.3))
        self.db.commit()

    def _detect_emotion_triggers(self, events):
        from app.algorithms.emotion_engine import EmotionEngine
        em = EmotionEngine()
        activities = [(e.payload.get("category", "other") if isinstance(e.payload, dict) else "other", e.created_at) for e in events]
        state = em.infer(activities)
        if state.primary != "平静" and state.confidence > 0.5:
            cats = Counter(e.payload.get("category", "other") for e in events if isinstance(e.payload, dict))
            top_cat = cats.most_common(1)[0][0] if cats else "other"
            existing = self.db.query(BehaviorPattern).filter(
                BehaviorPattern.pattern_type == "trigger",
                BehaviorPattern.trigger_events.contains({"emotion": state.primary})).first()
            if existing:
                existing.frequency += 1
                existing.confidence = min(existing.confidence + 0.03, 0.9)
            else:
                self.db.add(BehaviorPattern(
                    pattern_type="trigger",
                    trigger_events={"emotion": state.primary},
                    result_actions={"category": top_cat, "count": cats[top_cat]},
                    frequency=1, confidence=0.25))
            self.db.commit()

    def _detect_anomalies(self, events):
        from app.algorithms.anomaly_detector import AnomalyDetector
        ad = AnomalyDetector()
        hourly = Counter(e.created_at.hour for e in events)
        ad.fit(dict(hourly))
        for hour, cnt in hourly.items():
            is_a, z, reason = ad.detect(cnt)
            if is_a:
                existing = self.db.query(BehaviorPattern).filter(
                    BehaviorPattern.pattern_type == "anomaly",
                    BehaviorPattern.trigger_events.contains({"hour": hour})).first()
                if not existing:
                    self.db.add(BehaviorPattern(
                        pattern_type="anomaly",
                        trigger_events={"hour": hour, "z_score": z},
                        result_actions={"count": cnt, "reason": reason},
                        frequency=1, confidence=0.4))
        self.db.commit()