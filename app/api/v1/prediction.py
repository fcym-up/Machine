"""Prediction API."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.schemas.prediction import AnomalyResponse, ForecastResponse, RiskPredictionResponse
from app.services.prediction import PredictionEngine

router = APIRouter(prefix="/prediction", tags=["prediction"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/anomalies", response_model=AnomalyResponse)
def detect_anomalies(hours: int = Query(24, ge=1, le=168), db: Session = Depends(get_db)):
    engine = PredictionEngine(db)
    return engine.detect_anomalies(lookback_hours=hours)

@router.get("/forecast", response_model=ForecastResponse)
def forecast(days_back: int = Query(7), days_forward: int = Query(3), db: Session = Depends(get_db)):
    engine = PredictionEngine(db)
    return engine.forecast(days_back=days_back, days_forward=days_forward)

@router.get("/risk", response_model=RiskPredictionResponse)
def risk_prediction(db: Session = Depends(get_db)):
    engine = PredictionEngine(db)
    return engine.risk_prediction()
