"""知识图谱模型 — Entity 与 Relationship。

Entity：命名实体（person/organization/technology/location）
Relationship：实体间的类型化关系（subject -[predicate]-> object）
两者均通过 source_event_id 追溯来源。
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    attributes: Mapped[dict | None] = mapped_column(JSONB)
    source_event_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("events.id"))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    source_event = relationship("Event", backref="entities", lazy="joined")


class Relationship(Base):
    __tablename__ = "relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subject_id: Mapped[int] = mapped_column(Integer, ForeignKey("entities.id"), nullable=False)
    predicate: Mapped[str] = mapped_column(String(100), nullable=False)
    object_id: Mapped[int] = mapped_column(Integer, ForeignKey("entities.id"), nullable=False)
    source_event_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("events.id"))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    subject = relationship("Entity", foreign_keys=[subject_id], lazy="joined")
    obj = relationship("Entity", foreign_keys=[object_id], lazy="joined")
