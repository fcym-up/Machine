"""Memory model - long and short term memory storage."""
from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.compat import JSONField

class Memory(Base):
    __tablename__ = "memories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    memory_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary = mapped_column(Text, nullable=True)
    embedding = mapped_column(JSONField, nullable=True)
    source_event_id = mapped_column(Integer, ForeignKey("events.id"), nullable=True)
    layer: Mapped[str] = mapped_column(String(10), default="working")
    decay_rate: Mapped[float] = mapped_column(Float, default=1.0)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed = mapped_column(DateTime, nullable=True)
    consolidated_from = mapped_column(JSONField, nullable=True)
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    tags = mapped_column(JSONField, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    source_event = relationship("Event", backref="memories", lazy="joined")
