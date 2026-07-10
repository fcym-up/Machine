"""Weighted multi-signal emotion computation engine."""
from collections import defaultdict
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.models.emotion import EmotionSignal, EmotionState, SignalWeight

WINDOW_SECONDS = 3600  # 1-hour sliding window
EMOTION_LABELS = ["焦虑", "开心", "疲惫", "专注", "放松", "平静", "沮丧", "好奇"]


class EmotionComputer:

    def load_weights(self, db: Session) -> dict[str, float]:
        rows = db.query(SignalWeight).filter(SignalWeight.enabled.is_(True)).all()
        return {r.source: float(r.weight) for r in rows}

    def compute(self, db: Session) -> EmotionState | None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        cutoff = now - timedelta(seconds=WINDOW_SECONDS)
        signals = db.query(EmotionSignal).filter(
            EmotionSignal.created_at >= cutoff
        ).all()

        if not signals:
            return None

        weights = self.load_weights(db)
        scores: dict[str, float] = defaultdict(float)
        factors: list[str] = []

        for sig in signals:
            source_weight = weights.get(sig.source, 0.1)
            sig_ts = sig.created_at if sig.created_at.tzinfo is None else sig.created_at.replace(tzinfo=None)
            age = (now - sig_ts).total_seconds()
            decay = max(0.0, 1.0 - age / WINDOW_SECONDS)
            score = source_weight * float(sig.confidence) * decay
            scores[sig.emotion_label] += score
            if sig.payload and sig.payload.get("factor"):
                factors.append(sig.payload["factor"])

        if not scores:
            return None

        sorted_scores = sorted(scores.items(), key=lambda x: -x[1])
        primary = sorted_scores[0][0]
        secondary = sorted_scores[1][0] if len(sorted_scores) > 1 else None
        top_score = sorted_scores[0][1]
        confidence = min(0.95, top_score)
        intensity = min(0.95, max(0.1, top_score * 1.2))

        state = EmotionState(
            primary_emotion=primary,
            secondary_emotion=secondary,
            intensity=round(intensity, 2),
            confidence=round(confidence, 2),
            scores=dict(sorted_scores),
            factors=list(dict.fromkeys(factors))[-5:],
            signal_count=len(signals),
        )
        db.add(state)
        db.commit()
        db.refresh(state)
        return state

    def get_current(self, db: Session) -> EmotionState | None:
        return db.query(EmotionState).order_by(
            EmotionState.created_at.desc()
        ).first()
