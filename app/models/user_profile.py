"""User profile models — behavior patterns, traits, state, reflections."""
from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class BehaviorPattern(Base):
    __tablename__ = "behavior_patterns"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pattern_type: Mapped[str] = mapped_column(String(20), nullable=False)  # daily, trigger, anomaly
    trigger_events: Mapped[dict | None] = mapped_column(JSONB)
    result_actions: Mapped[dict | None] = mapped_column(JSONB)
    frequency: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class TraitDimension(Base):
    __tablename__ = "trait_dimensions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dimension: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    current_value: Mapped[float] = mapped_column(Float, default=0.5)
    trend_direction: Mapped[str] = mapped_column(String(10), default="stable")
    evidence_events: Mapped[list | None] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc))


class UserState(Base):
    __tablename__ = "user_state"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    emotional_state: Mapped[str] = mapped_column(String(30), default="平静")
    energy_level: Mapped[float] = mapped_column(Float, default=0.5)
    focus_level: Mapped[float] = mapped_column(Float, default=0.5)
    active_topics: Mapped[dict | None] = mapped_column(JSONB)
    social_engagement: Mapped[float] = mapped_column(Float, default=0.5)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime)
    summary_text: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc))


class SystemReflection(Base):
    __tablename__ = "system_reflections"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reflection_type: Mapped[str] = mapped_column(String(20), nullable=False)  # daily, hourly, event_triggered
    content: Mapped[str] = mapped_column(Text, nullable=False)
    emotional_tone: Mapped[str | None] = mapped_column(String(30))
    key_insights: Mapped[dict | None] = mapped_column(JSONB)
    related_event_ids: Mapped[list | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))