"""Emotion v2 API — history, weights, current state."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import SessionLocal
from app.models.emotion import EmotionState, EmotionSignal, SignalWeight
from app.algorithms.emotion_engine import compute_current, get_current_emotion

router = APIRouter(prefix="/emotion", tags=["emotion"])


def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()


class WeightUpdate(BaseModel):
    weight: float
    enabled: bool = True


@router.get("/current")
def current(db: Session = Depends(get_db)):
    state = get_current_emotion(db)
    if not state:
        return {
            "primary_emotion": "平静", "secondary_emotion": None,
            "confidence": 0.0, "intensity": 0.5, "scores": {},
            "factors": [], "signal_count": 0,
        }
    return {
        "id": state.id,
        "primary_emotion": state.primary_emotion,
        "secondary_emotion": state.secondary_emotion,
        "intensity": state.intensity,
        "confidence": state.confidence,
        "scores": state.scores,
        "factors": state.factors or [],
        "signal_count": state.signal_count,
        "created_at": str(state.created_at),
    }


@router.get("/history")
def history(limit: int = Query(24, ge=1, le=168), db: Session = Depends(get_db)):
    states = db.query(EmotionState).order_by(
        EmotionState.created_at.desc()
    ).limit(limit).all()
    return {
        "count": len(states),
        "items": [{
            "id": s.id,
            "primary_emotion": s.primary_emotion,
            "secondary_emotion": s.secondary_emotion,
            "intensity": s.intensity,
            "confidence": s.confidence,
            "created_at": str(s.created_at),
        } for s in states],
    }


@router.get("/weights")
def list_weights(db: Session = Depends(get_db)):
    rows = db.query(SignalWeight).all()
    return {
        "items": [{
            "source": r.source, "weight": float(r.weight),
            "enabled": r.enabled, "updated_at": str(r.updated_at),
        } for r in rows],
    }


@router.put("/weights/{source}")
def update_weight(source: str, data: WeightUpdate, db: Session = Depends(get_db)):
    row = db.query(SignalWeight).filter_by(source=source).first()
    if not row:
        row = SignalWeight(source=source, weight=data.weight, enabled=data.enabled)
        db.add(row)
    else:
        row.weight = data.weight
        row.enabled = data.enabled
    from datetime import datetime, timezone
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"source": source, "weight": float(row.weight), "enabled": row.enabled}


@router.post("/recompute")
def recompute(db: Session = Depends(get_db)):
    """Manually trigger recomputation."""
    from app.services.emotion_collector import collect_all
    collect_all(db)
    state = compute_current(db)
    if state:
        return {"primary_emotion": state.primary_emotion, "confidence": state.confidence}
    return {"message": "No signals to compute"}
