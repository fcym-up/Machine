"""Prediction Engine — anomaly detection and risk prediction.

Phase 7: Rule-based anomaly detection, trend forecasting, risk prediction.
"""

from collections import Counter
from datetime import datetime, timezone, timedelta

from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.event import Event


class PredictionEngine:
    """Rule-based prediction and anomaly detection."""

    def __init__(self, db: Session):
        self.db = db

    def detect_anomalies(self, lookback_hours: int = 24) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
        recent = self.db.query(Event).filter(Event.created_at >= cutoff).all()
        total = len(recent)
        if total == 0:
            return {"anomalies": [], "total_analyzed": 0}
        anomalies = []
        type_counts = Counter(e.event_type for e in recent)
        avg_per_type = total / max(len(type_counts), 1)
        for etype, count in type_counts.items():
            if count > avg_per_type * 3:
                anomalies.append({"type": "unusual_frequency", "detail": etype, "count": count, "expected_avg": round(avg_per_type, 1)})
        hourly = Counter(e.created_at.hour for e in recent)
        for hour, count in hourly.items():
            avg_per_hour = total / 24
            if count > avg_per_hour * 2.5 and (hour >= 0 and hour <= 5):
                anomalies.append({"type": "off_hours_activity", "detail": f"Hour {hour}:00", "count": count})
        logger.info(f"Detected {len(anomalies)} anomalies from {total} events")
        return {"anomalies": anomalies, "total_analyzed": total}

    def forecast(self, days_back: int = 7, days_forward: int = 3) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
        daily = self.db.query(func.date(Event.created_at).label("day"), func.count(Event.id).label("count")).filter(Event.created_at >= cutoff).group_by(func.date(Event.created_at)).order_by(func.date(Event.created_at)).all()
        counts = [row[1] for row in daily]
        if not counts:
            return {"forecast": [], "trend": "insufficient_data"}
        avg = sum(counts) / len(counts)
        trend = "stable"
        if len(counts) >= 2:
            if counts[-1] > counts[0] * 1.2:
                trend = "increasing"
            elif counts[-1] < counts[0] * 0.8:
                trend = "decreasing"
        forecast = [round(avg * (1 + 0.1 * i * (1 if trend == "increasing" else -1 if trend == "decreasing" else 0)), 1) for i in range(1, days_forward + 1)]
        logger.info(f"Forecast: {forecast}, trend: {trend}")
        return {"forecast": forecast, "trend": trend, "period_days": days_back, "avg_daily": round(avg, 1)}

    def risk_prediction(self) -> dict:
        total = self.db.query(func.count(Event.id)).scalar() or 0
        recent_24h = self.db.query(Event).filter(Event.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)).count()
        recent_1h = self.db.query(Event).filter(Event.created_at >= datetime.now(timezone.utc) - timedelta(hours=1)).count()
        risk = 0.0
        factors = []
        if total > 0:
            hourly_rate = recent_1h
            if hourly_rate > 30:
                risk += 40
                factors.append({"factor": "high_throughput", "detail": f"{hourly_rate} events/hour"})
            daily_rate = recent_24h
            if total > 100 and daily_rate > total * 0.5:
                risk += 25
                factors.append({"factor": "traffic_spike", "detail": "More than 50 percent daily traffic"})
        return {"predicted_risk": min(round(risk, 1), 100.0), "factors": factors, "total_events": total, "recent_24h": recent_24h}
