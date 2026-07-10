"""智能分析 API — 模式检测、风险评分、趋势分析。

GET /api/v1/intelligence/patterns — 事件频率与高峰时段
GET /api/v1/intelligence/risk     — 基于规则的风险评估
GET /api/v1/intelligence/trends   — 每日趋势分析
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.schemas.intelligence import PatternResponse, RiskResponse, TrendResponse
from app.services.intelligence import IntelligenceService
from app.services.importance_service import importance_service
from app.services.alert_service import get_alert_service

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/patterns", response_model=PatternResponse)
def get_patterns(days: int = Query(7, ge=1, le=30), db: Session = Depends(get_db)):
    service = IntelligenceService(db)
    return service.detect_patterns(days=days)


@router.get("/risk", response_model=RiskResponse)
def get_risk(db: Session = Depends(get_db)):
    service = IntelligenceService(db)
    return service.risk_score()


@router.get("/trends", response_model=TrendResponse)
def get_trends(days: int = Query(7, ge=1, le=30), db: Session = Depends(get_db)):
    service = IntelligenceService(db)
    return service.trend_analysis(days=days)


@router.get("/surface")
def get_surface(db: Session = Depends(get_db)):
    return importance_service.get_surface_summary()


@router.get("/alerts")
def get_alerts(hours: int = Query(24), db: Session = Depends(get_db)):
    svc = get_alert_service(db)
    return {"alerts": svc.generate_alerts(hours), "watchlist": svc.get_watchlist()}
