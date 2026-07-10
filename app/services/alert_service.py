from __future__ import annotations
from datetime import datetime, timezone, timedelta
from collections import Counter
from sqlalchemy.orm import Session
from loguru import logger
from app.models.event import Event
from app.algorithms.anomaly_detector import AnomalyDetector
from app.algorithms.temporal_learner import TemporalLearner
from app.services.importance_service import importance_service


class AlertService:

    def __init__(self, db: Session):
        self.db = db
        self.anomaly = AnomalyDetector()
        self.temporal = TemporalLearner()

    def generate_alerts(self, lookback_hours: int = 24) -> list[dict]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        events = self.db.query(Event).filter(Event.created_at >= cutoff).order_by(Event.created_at).all()
        if not events:
            return []
        alerts = []
        hourly = Counter(e.created_at.hour for e in events)
        self.anomaly.fit(dict(hourly))
        baseline = sum(hourly.values()) / max(len(hourly), 1)
        for h, cnt in hourly.items():
            is_anomaly, z, reason = self.anomaly.detect(cnt)
            if is_anomaly and cnt > baseline * 2:
                alerts.append({
                    "type": "anomaly",
                    "severity": "high" if z > 3 else "medium",
                    "message": f"Unusual activity at {h}:00 ({cnt} events, baseline {baseline:.0f})",
                    "z_score": round(z, 2),
                })
        self.temporal.fit([(e.created_at, e.event_type) for e in events])
        if self.temporal.hourly_profile:
            peak_hour = max(self.temporal.hourly_profile, key=self.temporal.hourly_profile.get)
            if peak_hour >= 23 or peak_hour <= 5:
                alerts.append({
                    "type": "rhythm_deviation",
                    "severity": "low",
                    "message": f"Peak activity at unusual hour ({peak_hour}:00). Consider adjusting your schedule.",
                })
        return alerts

    def get_watchlist(self, top_k: int = 5) -> list[dict]:
        important_ids = importance_service.get_important_events(top_k)
        if not important_ids:
            return []
        events = self.db.query(Event).filter(Event.id.in_(important_ids)).all()
        event_map = {e.id: e for e in events}
        result = []
        for eid in important_ids:
            if eid in event_map:
                e = event_map[eid]
                result.append({
                    "event_id": e.id,
                    "event_type": e.event_type,
                    "source": e.source,
                    "importance": importance_service.get_score(e.id),
                    "created_at": str(e.created_at),
                    "payload_preview": str(e.payload)[:100] if e.payload else "",
                })
        return result

alert_service = None


def get_alert_service(db: Session) -> AlertService:
    global alert_service
    if alert_service is None or alert_service.db is not db:
        alert_service = AlertService(db)
    return alert_service