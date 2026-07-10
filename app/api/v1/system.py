"""System API - reflections and scheduler control."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.reflection import ReflectionService
from app.core.scheduler import scheduler

router = APIRouter(prefix="/system", tags=["system"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.get("/reflections")
def list_reflections(ref_type: str = None, limit: int = 20, db: Session = Depends(get_db)):
    refs = ReflectionService(db).get_reflections(ref_type, limit)
    return {"count": len(refs), "items": [{"id": r.id, "type": r.reflection_type, "content": r.content[:300], "tone": r.emotional_tone, "created": str(r.created_at)} for r in refs]}

@router.post("/reflections/generate")
def generate_reflection(ref_type: str = "daily", db: Session = Depends(get_db)):
    rs = ReflectionService(db)
    r = rs.generate_daily_reflection() if ref_type == "daily" else rs.generate_hourly_reflection()
    if r: return {"id": r.id, "content": r.content[:300]}
    return {"message": "Not enough data to reflect"}

@router.post("/scheduler/start")
def start_scheduler():
    scheduler.start()
    return {"status": "scheduler started"}

@router.post("/scheduler/stop")
def stop_scheduler():
    scheduler.stop()
    return {"status": "scheduler stopped"}