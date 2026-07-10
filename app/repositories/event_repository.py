"""EventRepository — Event 模型的数据访问层。

提供：create、create_batch、get_by_id、list、count、search、
stats_by_type、stats_by_source、stats_by_day、update、delete。
Search 支持按 event_type、source、keyword、时间范围过滤。
"""
from __future__ import annotations
from datetime import datetime
from typing import Sequence

from sqlalchemy import String, func, text
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import JSONB

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
        for event in events:
            self.db.refresh(event)
        return events

    def get_by_id(self, event_id: int) -> Event | None:
        return self.db.query(Event).filter(Event.id == event_id).first()

    def list(self, skip: int = 0, limit: int = 20) -> Sequence[Event]:
        return (
            self.db.query(Event)
            .order_by(Event.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count(self) -> int:
        return self.db.query(Event).count()

    def search(
        self,
        event_type: str | None = None,
        source: str | None = None,
        keyword: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Event], int]:
        query = self.db.query(Event)
        if event_type:
            query = query.filter(Event.event_type == event_type)
        if source:
            query = query.filter(Event.source == source)
        if start_time:
            query = query.filter(Event.created_at >= start_time)
        if end_time:
            query = query.filter(Event.created_at <= end_time)
        if keyword:
            query = query.filter(
                Event.payload.cast(JSONB).cast(String).ilike(f"%{keyword}%")
            )
        total = query.count()
        items = (
            query.order_by(Event.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    def stats_by_type(self) -> list[dict]:
        return (
            self.db.query(
                Event.event_type,
                func.count(Event.id).label("count"),
            )
            .group_by(Event.event_type)
            .order_by(func.count(Event.id).desc())
            .all()
        )

    def stats_by_source(self) -> list[dict]:
        return (
            self.db.query(
                Event.source,
                func.count(Event.id).label("count"),
            )
            .group_by(Event.source)
            .order_by(func.count(Event.id).desc())
            .all()
        )

    def stats_by_day(self, days: int = 7) -> list[dict]:
        return (
            self.db.query(
                func.date(Event.created_at).label("day"),
                func.count(Event.id).label("count"),
            )
            .filter(
                Event.created_at
                >= func.now() - text(f"interval '{days} days'")
            )
            .group_by(func.date(Event.created_at))
            .order_by(func.date(Event.created_at).desc())
            .all()
        )

    def update(self, event: Event) -> Event:
        self.db.commit()
        self.db.refresh(event)
        return event

    def delete(self, event: Event) -> None:
        self.db.delete(event)
        self.db.commit()
