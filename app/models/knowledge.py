"""Knowledge graph models - Entity and Relationship."""
from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.compat import JSONField

class Entity(Base):
    __tablename__ = "knowledge_entities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description = mapped_column(Text, nullable=True)
    attributes = mapped_column(JSONField, nullable=True)
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Relationship(Base):
    __tablename__ = "knowledge_relationships"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("knowledge_entities.id"), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, ForeignKey("knowledge_entities.id"), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    source = relationship("Entity", foreign_keys=[source_id], lazy="joined")
    target = relationship("Entity", foreign_keys=[target_id], lazy="joined")
