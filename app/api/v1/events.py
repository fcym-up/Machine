"""Events API — CRUD + 批量 + 搜索 + 统计。

POST   /api/v1/events        — 创建单个事件
POST   /api/v1/events/batch   — 批量导入（1-100 条）
GET    /api/v1/events         — 列表（分页）
GET    /api/v1/events/search  — 按 type/source/keyword/time 搜索
GET    /api/v1/events/stats   — 统计聚合
GET    /api/v1/events/{id}    — 按 ID 查询
PUT    /api/v1/events/{id}    — 更新
DELETE /api/v1/events/{id}    — 删除

所有端点需要 X-API-Key 请求头。
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.schemas.event import (
    EventCreate,
    EventBatchCreate,
    EventUpdate,
    EventResponse,
    EventList,
    EventSearchParams,
    EventStats,
)
from app.services.event import EventService

router = APIRouter(prefix="/events", tags=["events"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=EventResponse, status_code=201)
def create_event(event_data: EventCreate, db: Session = Depends(get_db)):
    service = EventService(db)
    try:
        event = service.create_event(event_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return event


@router.post("/batch", response_model=EventList, status_code=201)
def create_batch(batch_data: EventBatchCreate, db: Session = Depends(get_db)):
    service = EventService(db)
    try:
        events = service.create_batch(batch_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return EventList(items=events, total=len(events))


@router.get("/search", response_model=EventList)
def search_events(
    event_type: str | None = Query(None),
    source: str | None = Query(None),
    keyword: str | None = Query(None),
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    service = EventService(db)
    items, total = service.search_events(
        event_type=event_type,
        source=source,
        keyword=keyword,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit,
    )
    return EventList(items=items, total=total)


@router.get("/stats", response_model=EventStats)
def get_stats(db: Session = Depends(get_db)):
    service = EventService(db)
    return service.get_stats()


@router.get("/", response_model=EventList)
def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    service = EventService(db)
    items, total = service.list_events(skip=skip, limit=limit)
    return EventList(items=items, total=total)




@router.get("/timeline")
def get_timeline(limit: int = 30, db: Session = Depends(get_db)):
    from app.models.event import Event
    """Timeline: activity summary + process-level event stream."""
    from collections import Counter
    events = db.query(Event).order_by(Event.created_at.desc()).limit(limit * 2).all()
    events = sorted(events, key=lambda e: e.created_at)
    if not events:
        return {"summary": [], "timeline": []}

    # Build summary: per-app stats
    app_stats = {}
    for e in events:
        app = e.payload.get("app", "") if isinstance(e.payload, dict) else ""
        cat = e.payload.get("category", "other") if isinstance(e.payload, dict) else "other"
        if not app or cat == "other":
            continue
        key = app
        if key not in app_stats:
            app_stats[key] = {"app": app, "category": cat, "count": 0, "first_seen": e.created_at, "last_seen": e.created_at}
        app_stats[key]["count"] += 1
        app_stats[key]["last_seen"] = e.created_at
    for k in app_stats:
        fs = app_stats[k]["first_seen"]
        ls = app_stats[k]["last_seen"]
        dur = (ls - fs).total_seconds()
        if dur > 3600: app_stats[k]["duration"] = f"{int(dur/3600)}h{int((dur%3600)/60)}m"
        elif dur > 60: app_stats[k]["duration"] = f"{int(dur/60)}分钟"
        else: app_stats[k]["duration"] = "刚刚"
    summary = sorted(app_stats.values(), key=lambda x: x["last_seen"], reverse=True)[:8]

    # Build timeline: action-based descriptions
    tl = []
    for e in events[-limit:]:
        a = e.payload.get("action", "") if isinstance(e.payload, dict) else ""
        app = e.payload.get("app", "") if isinstance(e.payload, dict) else ""
        cat = e.payload.get("category", "other") if isinstance(e.payload, dict) else "other"
        ts = e.created_at.strftime("%H:%M")
        if a == "opened":
            desc = f"打开了 {app}"
        elif a == "closed":
            desc = f"关闭了 {app}"
        elif a == "switch-to":
            desc = f"切换至 {app}"
        else:
            desc = f"{app}"
        tl.append({"time": ts, "action": a, "app": app, "category": cat, "description": desc, "created_at": str(e.created_at)})
    return {"summary": summary, "timeline": tl[-limit:]}

@router.get("/feed")
def get_event_feed(limit: int = 20, db: Session = Depends(get_db)):
    """Smart event feed - noise filtered and merged."""
    service = EventService(db)
    return {"items": service.get_feed(limit=limit)}

@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    service = EventService(db)
    event = service.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.put("/{event_id}", response_model=EventResponse)
def update_event(event_id: int, event_data: EventUpdate, db: Session = Depends(get_db)):
    service = EventService(db)
    try:
        event = service.update_event(event_id, event_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    service = EventService(db)
    deleted = service.delete_event(event_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event not found")
