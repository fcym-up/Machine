"""MemoryRepository — Memory 模型的数据访问层。

支持 CRUD 操作、按 memory_type 列表、
查找特定事件关联的记忆。
"""
from __future__ import annotations
from typing import Sequence

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.memory import Memory


class MemoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, memory: Memory) -> Memory:
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)
        return memory

    def get_by_id(self, memory_id: int) -> Memory | None:
        return self.db.query(Memory).filter(Memory.id == memory_id).first()

    def list(self, skip: int = 0, limit: int = 20, memory_type: str | None = None) -> Sequence[Memory]:
        query = self.db.query(Memory)
        if memory_type:
            query = query.filter(Memory.memory_type == memory_type)
        return query.order_by(Memory.created_at.desc()).offset(skip).limit(limit).all()

    def count(self, memory_type: str | None = None) -> int:
        query = self.db.query(func.count(Memory.id))
        if memory_type:
            query = query.filter(Memory.memory_type == memory_type)
        return query.scalar()

    def find_by_event(self, event_id: int) -> Sequence[Memory]:
        return self.db.query(Memory).filter(Memory.source_event_id == event_id).all()

    def update(self, memory: Memory) -> Memory:
        self.db.commit()
        self.db.refresh(memory)
        return memory

    def delete(self, memory: Memory) -> None:
        self.db.delete(memory)
        self.db.commit()
