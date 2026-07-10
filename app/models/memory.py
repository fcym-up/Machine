"""Memory model — long and short term memory storage.

Supports four memory types: short, long, semantic, episode.
Each memory stores an embedding vector (Float[]) for semantic search.
Linked to source event via source_event_id foreign key.

v1.0: Added memory hierarchy fields (layer, decay_rate, access_count, etc.)
"""
from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    memory_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(ARRAY(Float))
    source_event_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("events.id"))
    layer: Mapped[str] = mapped_column(String(10), default="working")
    decay_rate: Mapped[float] = mapped_column(Float, default=1.0)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed: Mapped[datetime | None] = mapped_column(DateTime)
    consolidated_from: Mapped[list | None] = mapped_column(JSONB)
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    tags: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc))

    source_event = relationship("Event", backref="memories", lazy="joined")