"""IntelligenceService - pattern detection and risk analysis."""
from collections import Counter
from datetime import datetime, timezone, timedelta

from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.event import Event


class IntelligenceService:

    def __init__(self, db: Session):
        self.db = db

    def detect_patterns(self, days: int = 7) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        events = self.db.query(Event).filter(Event.created_at >= cutoff).all()
        type_counter = Counter(e.event_type for e in events)
        source_counter = Counter(e.source for e in events)
        patterns = []
        total = len(events)
        for event_type, count in type_counter.most_common(5):
            freq = count / max(total, 1)
            patterns.append({"type": "frequent_event_type", "detail": event_type, "count": count, "frequency": round(freq, 3)})
        hourly = Counter(e.created_at.hour for e in events)
        peak_hour = hourly.most_common(1)[0] if hourly else (0, 0)
        patterns.append({"type": "peak_hour", "detail": f"Most active at hour {peak_hour[0]}:00", "count": peak_hour[1]})
        return {"total_events": total, "period_days": days, "patterns": patterns,
                "top_types": [{"type": t, "count": c} for t, c in type_counter.most_common(5)],
                "top_sources": [{"source": s, "count": c} for s, c in source_counter.most_common(5)]}

    def risk_score(self) -> dict:
        total = self.db.query(func.count(Event.id)).scalar() or 0
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        recent = self.db.query(Event).filter(Event.created_at >= cutoff).count()
        factors = []
        risk = 0.0
        if recent > 20:
            risk += 30.0
            factors.append({"factor": "high_event_frequency", "detail": f"{recent} events in last hour", "contribution": 30.0})
        error_count = self.db.query(Event).filter(Event.event_type == "system-event").count()
        if error_count > 5:
            risk += 20.0
            factors.append({"factor": "error_rate", "detail": f"{error_count} error events detected", "contribution": 20.0})
        risk = min(risk, 100.0)
        return {"overall_risk": round(risk, 1), "factors": factors, "total_events": total, "events_last_hour": recent}

    def trend_analysis(self, days: int = 7) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        daily_counts = (self.db.query(func.date(Event.created_at).label("day"), func.count(Event.id).label("count"))
                        .filter(Event.created_at >= cutoff).group_by(func.date(Event.created_at)).order_by(func.date(Event.created_at)).all())
        counts = [r[1] for r in daily_counts]
        daily_data = [{"day": str(r[0]), "count": r[1]} for r in daily_counts]
        trend = "stable"
        if len(counts) >= 3:
            mid = len(counts) // 2
            fh = sum(counts[:mid])
            sh = sum(counts[mid:])
            trend = "increasing" if sh > fh * 1.3 else ("decreasing" if sh < fh * 0.7 else "stable")
        return {"period_days": days, "trend": trend, "daily_data": daily_data, "total": sum(counts), "avg_per_day": round(sum(counts) / max(len(counts), 1), 1)}
