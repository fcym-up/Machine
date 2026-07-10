"""知识图谱 API — Entity、Relationship、Graph 查询。

POST   /api/v1/knowledge/entities          — 创建实体
GET    /api/v1/knowledge/entities          — 列出实体
GET    /api/v1/knowledge/entities/search   — 模糊名称搜索
GET    /api/v1/knowledge/entities/{id}     — 按 ID 查询
PUT    /api/v1/knowledge/entities/{id}     — 更新
DELETE /api/v1/knowledge/entities/{id}     — 删除
POST   /api/v1/knowledge/relationships     — 创建关系
GET    /api/v1/knowledge/graph             — 查询完整图谱
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.schemas.knowledge import (
    EntityCreate,
    EntityUpdate,
    EntityResponse,
    EntityList,
    RelationshipCreate,
    RelationshipResponse,
    GraphResponse,
)
from app.services.knowledge import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/entities", response_model=EntityResponse, status_code=201)
def create_entity(data: EntityCreate, db: Session = Depends(get_db)):
    service = KnowledgeService(db)
    try:
        return service.create_entity(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/entities", response_model=EntityList)
def list_entities(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    entity_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    service = KnowledgeService(db)
    items, total = service.list_entities(skip=skip, limit=limit, entity_type=entity_type)
    return EntityList(items=items, total=total)


@router.get("/entities/search", response_model=EntityList)
def search_entities(name: str = Query(...), entity_type: str | None = Query(None), db: Session = Depends(get_db)):
    service = KnowledgeService(db)
    items = service.search_entities(name, entity_type)
    return EntityList(items=items, total=len(items))


@router.get("/entities/{entity_id}", response_model=EntityResponse)
def get_entity(entity_id: int, db: Session = Depends(get_db)):
    service = KnowledgeService(db)
    entity = service.get_entity(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.put("/entities/{entity_id}", response_model=EntityResponse)
def update_entity(entity_id: int, data: EntityUpdate, db: Session = Depends(get_db)):
    service = KnowledgeService(db)
    try:
        entity = service.update_entity(entity_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.delete("/entities/{entity_id}", status_code=204)
def delete_entity(entity_id: int, db: Session = Depends(get_db)):
    service = KnowledgeService(db)
    if not service.delete_entity(entity_id):
        raise HTTPException(status_code=404, detail="Entity not found")


@router.post("/relationships", response_model=RelationshipResponse, status_code=201)
def create_relationship(data: RelationshipCreate, db: Session = Depends(get_db)):
    service = KnowledgeService(db)
    return service.create_relationship(data)


@router.get("/graph", response_model=GraphResponse)
def get_graph(entity_id: int | None = Query(None), db: Session = Depends(get_db)):
    service = KnowledgeService(db)
    return service.get_graph(entity_id)
