"""Memories API — CRUD + 语义搜索。

POST   /api/v1/memories          — 创建记忆（自动生成 embedding）
GET    /api/v1/memories          — 列表（分页，可按类型筛选）
GET    /api/v1/memories/search   — 语义相似度搜索
GET    /api/v1/memories/{id}     — 按 ID 查询
PUT    /api/v1/memories/{id}     — 更新（重新生成 embedding）
DELETE /api/v1/memories/{id}     — 删除
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.schemas.memory import (
    MemoryCreate,
    MemoryUpdate,
    MemoryResponse,
    MemoryList,
    MemorySearchResult,
)
from app.services.memory import MemoryService
from app.services.consolidation import ConsolidationService

router = APIRouter(prefix="/memories", tags=["memories"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=MemoryResponse, status_code=201)
def create_memory(data: MemoryCreate, db: Session = Depends(get_db)):
    service = MemoryService(db)
    try:
        memory = service.create_memory(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return memory


@router.get("/", response_model=MemoryList)
def list_memories(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    memory_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    service = MemoryService(db)
    items, total = service.list_memories(skip=skip, limit=limit, memory_type=memory_type)
    return MemoryList(items=items, total=total)


@router.get("/search", response_model=list[MemorySearchResult])
def search_memories(query: str = Query(...), limit: int = Query(5), db: Session = Depends(get_db)):
    service = MemoryService(db)
    results = service.search_similar(query, limit=limit)
    return [
        MemorySearchResult(
            id=mem.id,
            content=mem.content,
            summary=mem.summary,
            memory_type=mem.memory_type,
            similarity=round(sim, 4),
        )
        for mem, sim in results
    ]


@router.get("/{memory_id}", response_model=MemoryResponse)
def get_memory(memory_id: int, db: Session = Depends(get_db)):
    service = MemoryService(db)
    memory = service.get_memory(memory_id)
    if memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@router.put("/{memory_id}", response_model=MemoryResponse)
def update_memory(memory_id: int, data: MemoryUpdate, db: Session = Depends(get_db)):
    service = MemoryService(db)
    memory = service.update_memory(memory_id, data)
    if memory is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@router.delete("/{memory_id}", status_code=204)
def delete_memory(memory_id: int, db: Session = Depends(get_db)):
    service = MemoryService(db)
    deleted = service.delete_memory(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")

@router.post("/consolidate")
def trigger_consolidation(level: str = "hourly", db = Depends(get_db)):
    cs = ConsolidationService(db)
    if level == "hourly": return cs.consolidate_hourly()
    elif level == "daily": return cs.consolidate_daily()
    elif level == "weekly": return cs.consolidate_weekly()
    return {"error": "Use hourly/daily/weekly"}

@router.get("/layer/{layer}")
def list_by_layer(layer: str, limit: int = 20, db = Depends(get_db)):
    from app.models.memory import Memory
    mems = db.query(Memory).filter(Memory.layer == layer).order_by(Memory.created_at.desc()).limit(limit).all()
    return {"layer": layer, "count": len(mems), "items": [{"id": m.id, "content": m.content[:200], "decay": m.decay_rate} for m in mems]}
