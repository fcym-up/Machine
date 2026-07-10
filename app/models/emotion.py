"""Emotion v2 models — multi-signal weighted emotion tracking."""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, ARRAY, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EmotionSignal(Base):
    __tablename__ = "emotion_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    emotion_label: Mapped[str] = mapped_column(String(16), nullable=False)
    weight: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), default=0.5)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    event_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("events.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )


class EmotionState(Base):
    __tablename__ = "emotion_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    primary_emotion: Mapped[str] = mapped_column(String(16), nullable=False)
    secondary_emotion: Mapped[str | None] = mapped_column(String(16), nullable=True)
    intensity: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    scores: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    factors: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True)
    signal_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )


class SignalWeight(Base):
    __tablename__ = "emotion_signal_weights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    weight: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
