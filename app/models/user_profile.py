"""User profile models - behavior patterns, traits, states."""
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.core.compat import JSONField

class BehaviorPattern(Base):
    __tablename__ = "behavior_patterns"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pattern_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    frequency: Mapped[float] = mapped_column(Float, default=0.0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    trigger_events = mapped_column(JSONField, nullable=True)
    result_actions = mapped_column(JSONField, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class TraitDimension(Base):
    __tablename__ = "trait_dimensions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    trait_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    dimension: Mapped[str] = mapped_column(String(50), default="")
    current_value: Mapped[float] = mapped_column(Float, default=0.5)
    score: Mapped[float] = mapped_column(Float, default=0.5)
    confidence: Mapped[float] = mapped_column(Float, default=0.3)
    trend_direction: Mapped[str] = mapped_column(String(10), default="stable")
    evidence_events = mapped_column(JSONField, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class UserState(Base):
    __tablename__ = "user_states"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True, default="default")
    emotional_state: Mapped[str] = mapped_column(String(20), default="unknown")
    energy: Mapped[float] = mapped_column(Float, default=0.5)
    energy_level: Mapped[float] = mapped_column(Float, default=0.5)
    focus: Mapped[float] = mapped_column(Float, default=0.5)
    focus_level: Mapped[float] = mapped_column(Float, default=0.5)
    social: Mapped[float] = mapped_column(Float, default=0.5)
    social_engagement: Mapped[float] = mapped_column(Float, default=0.5)
    active_topics = mapped_column(JSONField, nullable=True)
    last_activity_at = mapped_column(DateTime, nullable=True)
    summary_text = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class SystemReflection(Base):
    __tablename__ = "system_reflections"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ref_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    key_insights = mapped_column(JSONField, nullable=True)
    related_event_ids = mapped_column(JSONField, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
