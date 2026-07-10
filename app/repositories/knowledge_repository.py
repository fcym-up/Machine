"""知识图谱 Repository 层。

EntityRepository：CRUD + 实体模糊名称搜索。
RelationshipRepository：创建 + 按实体查询关系。
"""
from __future__ import annotations
from typing import Sequence

from sqlalchemy.orm import Session

from app.models.knowledge import Entity, Relationship


class EntityRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, entity: Entity) -> Entity:
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def get_by_id(self, entity_id: int) -> Entity | None:
        return self.db.query(Entity).filter(Entity.id == entity_id).first()

    def find_by_name(self, name: str, entity_type: str | None = None) -> Sequence[Entity]:
        query = self.db.query(Entity).filter(Entity.name.ilike(f"%{name}%"))
        if entity_type:
            query = query.filter(Entity.entity_type == entity_type)
        return query.order_by(Entity.confidence.desc()).all()

    def list(self, skip: int = 0, limit: int = 20, entity_type: str | None = None) -> Sequence[Entity]:
        query = self.db.query(Entity)
        if entity_type:
            query = query.filter(Entity.entity_type == entity_type)
        return query.order_by(Entity.created_at.desc()).offset(skip).limit(limit).all()

    def count(self, entity_type: str | None = None) -> int:
        query = self.db.query(Entity)
        if entity_type:
            query = query.filter(Entity.entity_type == entity_type)
        return query.count()

    def update(self, entity: Entity) -> Entity:
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity: Entity) -> None:
        self.db.delete(entity)
        self.db.commit()


class RelationshipRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, rel: Relationship) -> Relationship:
        self.db.add(rel)
        self.db.commit()
        self.db.refresh(rel)
        return rel

    def find_by_entity(self, entity_id: int) -> Sequence[Relationship]:
        return (
            self.db.query(Relationship)
            .filter(
                (Relationship.subject_id == entity_id)
                | (Relationship.object_id == entity_id)
            )
            .all()
        )

    def list(self, skip: int = 0, limit: int = 20) -> Sequence[Relationship]:
        return self.db.query(Relationship).offset(skip).limit(limit).all()

    def delete(self, rel: Relationship) -> None:
        self.db.delete(rel)
        self.db.commit()
