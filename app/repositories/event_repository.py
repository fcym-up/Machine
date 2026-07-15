"""Event repository — database access layer for Event."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.event import Event


class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, event: Event) -> Event:
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def create_batch(self, events: list[Event]) -> list[Event]:
        self.db.add_all(events)
        self.db.commit()
        for e in events:
            self.db.refresh(e)
        return events

    def get_by_id(self, event_id: int) -> Optional[Event]:
        return self.db.query(Event).filter(Event.id == event_id).first()

    def list(self, skip: int = 0, limit: int = 20) -> list[Event]:
        return self.db.query(Event).order_by(Event.created_at.desc()).offset(skip).limit(limit).all()

    def search(self, event_type: Optional[str] = None, source: Optional[str] = None, keyword: Optional[str] = None, skip: int = 0, limit: int = 20) -> list[Event]:
        q = self.db.query(Event)
        if event_type: q = q.filter(Event.event_type == event_type)
        if source: q = q.filter(Event.source == source)
        return q.order_by(Event.created_at.desc()).offset(skip).limit(limit).all()

    def stats_by_type(self, days: int = 1) -> list:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return (self.db.query(Event.event_type, func.count(Event.id))
                .filter(Event.created_at >= cutoff)
                .group_by(Event.event_type).all())

    def stats_by_source(self, days: int = 1) -> list:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return (self.db.query(Event.source, func.count(Event.id))
                .filter(Event.created_at >= cutoff)
                .group_by(Event.source).all())

    def stats_by_day(self, days: int = 7) -> list:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return (self.db.query(func.date(Event.created_at).label("day"), func.count(Event.id))
                .filter(Event.created_at >= cutoff)
                .group_by(func.date(Event.created_at))
                .order_by(func.date(Event.created_at).desc()).all())

    def count(self) -> int:
        return self.db.query(func.count(Event.id)).scalar() or 0

    def update(self, event: Event) -> Event:
        self.db.commit()
        self.db.refresh(event)
        return event

    def delete(self, event_id: int) -> bool:
        event = self.get_by_id(event_id)
        if not event: return False
        self.db.delete(event)
        self.db.commit()
        return True

    def get_feed(self, limit: int = 20) -> list[Event]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        return (self.db.query(Event)
                .filter(Event.created_at >= cutoff)
                .order_by(Event.created_at.desc())
                .limit(limit).all())
