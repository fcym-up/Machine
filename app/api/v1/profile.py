"""用户画像 API - Machine 对你的理解。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.user_profile import UserProfile
from app.services.user_model import UserModelService

router = APIRouter(prefix="/profile", tags=["profile"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.get("/habits")
def get_habits(days: int = Query(7), db: Session = Depends(get_db)):
    return UserProfile(db).get_habits(days)

@router.get("/insights")
def get_insights(days: int = Query(7), db: Session = Depends(get_db)):
    return UserProfile(db).get_insights(days)

@router.get("/digest")
def daily_digest(db: Session = Depends(get_db)):
    return UserProfile(db).daily_digest()

@router.get("/full")
def full_analysis(days: int = Query(7), db: Session = Depends(get_db)):
    return UserProfile(db).full_dimension_analysis(days)

# === 算法驱动的智能分析 ===
from app.algorithms.association_miner import AssociationMiner
from app.algorithms.temporal_learner import TemporalLearner
from app.algorithms.importance_learner import ImportanceLearner

learner_instances = {"temporal": TemporalLearner(), "association": AssociationMiner(), "importance": ImportanceLearner()}

@router.get("/learn/rhythm")
def learn_rhythm(days: int = Query(7), db: Session = Depends(get_db)):
    """时间节律学习"""
    from datetime import datetime, timezone, timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    events = db.query(Event).filter(Event.created_at >= cutoff).all()
    tl = TemporalLearner()
    tl.fit([(e.created_at, e.event_type) for e in events])
    return {"peak_hour": tl.get_peak_hour(), "most_active_day": tl.get_most_active_day(), "summary": tl.get_rhythm_summary(), "hourly": tl.hourly_profile}

@router.get("/learn/patterns")
def learn_patterns(days: int = Query(7), db: Session = Depends(get_db)):
    """行为关联模式挖掘"""
    from datetime import datetime, timezone, timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    events = db.query(Event).filter(Event.created_at >= cutoff).order_by(Event.created_at).all()
    transactions = []
    window = []
    for e in events:
        window.append(e.event_type)
        if len(window) >= 5:
            transactions.append(list(set(window)))
            window = window[1:]
    miner = AssociationMiner()
    miner.fit(transactions)
    return {"rules": miner.rules, "next_if_coding": miner.predict_next("file-change")}

@router.get("/model")
def get_user_model(db = Depends(get_db)):
    return UserModelService(db).get_model()

@router.get("/state")
def get_user_state(db = Depends(get_db)):
    return UserModelService(db).update_state()
