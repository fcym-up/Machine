"""EventService with auto-enrichment pipeline.

Each event creation auto-triggers:
1. Entity + relationship extraction (LLM NER)
2. Memory creation (episodic, for significant categories)
3. Importance scoring
"""
from datetime import datetime
from typing import Any
from loguru import logger
from sqlalchemy.orm import Session
from app.models.event import Event
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventCreate, EventBatchCreate, EventUpdate
from app.services.event_engine import EventClassifier, EventNormalizer
from app.services.importance_service import importance_service


class EventService:
    VALID_EVENT_TYPES = {
        "user-action", "system-event", "file-change", "web-activity",
        "git-commit", "chat-message", "ai-reasoning", "api-call",
        "app-open", "app-close",
    }
    VALID_SOURCES = {
        "browser", "terminal", "ide", "chat", "git", "api",
        "system", "user", "ai", "filesystem", "activity", "process",
    }

    def __init__(self, db: Session):
        self.repo = EventRepository(db)
        self.db = db
        self.classifier = EventClassifier()
        self.normalizer = EventNormalizer()

    def create_event(self, data: EventCreate) -> Event:
        if data.event_type not in self.VALID_EVENT_TYPES:
            raise ValueError(f"Invalid event_type: {data.event_type}")
        if data.source not in self.VALID_SOURCES:
            raise ValueError(f"Invalid source: {data.source}")
        normalized_payload = self.normalizer.normalize(data.source, data.payload)
        if "process" in (normalized_payload or {}) and "category" not in (normalized_payload or {}):
            from app.services.process_classifier import classify_process
            normalized_payload["category"] = classify_process(normalized_payload.get("process", ""))
# DEDUP REMOVED
        event = Event(event_type=data.event_type, source=data.source, payload=normalized_payload)
        created = self.repo.create(event)
        logger.info(f"Event created: id={created.id}, type={created.event_type}")
        importance_service.score_event(created.id, created.event_type, created.payload, created.created_at)
        self._auto_enrich(created)
        return created

    def create_batch(self, data: EventBatchCreate) -> list[Event]:
        events = []
        for item in data.events:
            event_type = item.event_type or self.classifier.classify(item.source, item.payload)
            if event_type not in self.VALID_EVENT_TYPES:
                raise ValueError(f"Invalid event_type: {event_type}")
            if item.source not in self.VALID_SOURCES:
                raise ValueError(f"Invalid source: {item.source}")
            normalized_payload = self.normalizer.normalize(item.source, item.payload)
            if "process" in (normalized_payload or {}) and "category" not in (normalized_payload or {}):
                from app.services.process_classifier import classify_process
                normalized_payload["category"] = classify_process(normalized_payload.get("process", ""))
            events.append(Event(event_type=event_type, source=item.source, payload=normalized_payload))
        created = self.repo.create_batch(events)
        logger.info(f"Batch created: {len(created)} events")
        for e in created:
            importance_service.score_event(e.id, e.event_type, e.payload, e.created_at)
            self._auto_enrich(e)
        return created

    def _auto_enrich(self, event):
        try:
            from app.services.knowledge import KnowledgeService
            ks = KnowledgeService(self.db)
            entities = ks.extract_and_save(event.payload, event.id)
            if entities and len(entities) >= 2:
                from app.models.knowledge import Relationship
                for i in range(len(entities)):
                    for j in range(i + 1, len(entities)):
                        rel = Relationship(
                            subject_id=entities[i].id, predicate="co_occurrence",
                            object_id=entities[j].id, source_event_id=event.id, confidence=0.5)
                        self.db.add(rel)
                self.db.commit()
        except Exception as e:
            logger.debug(f"Auto enrich skipped: {e}")
        try:
            from app.services.memory import MemoryService
            from app.schemas.memory import MemoryCreate
            category = event.payload.get("category", "") if isinstance(event.payload, dict) else ""
            if category in ("coding", "social", "gaming", "job", "video", "news"):
                ms = MemoryService(self.db)
                data = MemoryCreate(
                    memory_type="episode",
                    content=f"{event.event_type} in {category}: {str(event.payload)[:200]}",
                    source_event_id=event.id, importance=0.6)
                ms.create_memory(data)
        except Exception as e:
            logger.debug(f"Auto memory skipped: {e}")

    def get_event(self, event_id: int) -> Event | None:
        return self.repo.get_by_id(event_id)

    def list_events(self, skip=0, limit=20):
        items = self.repo.list(skip=skip, limit=limit)
        return items, self.repo.count()

    def search_events(self, event_type=None, source=None, keyword=None, start_time=None, end_time=None, skip=0, limit=20):
        items, total = self.repo.search(
            event_type=event_type, source=source, keyword=keyword,
            start_time=start_time, end_time=end_time, skip=skip, limit=limit)
        return items, total

    def get_stats(self) -> dict[str, Any]:
        type_stats = self.repo.stats_by_type()
        source_stats = self.repo.stats_by_source()
        day_stats = self.repo.stats_by_day()
        return {
            "total_events": self.repo.count(),
            "by_type": [{"type": r[0], "count": r[1]} for r in type_stats],
            "by_source": [{"source": r[0], "count": r[1]} for r in source_stats],
            "by_day": [{"day": str(r[0]), "count": r[1]} for r in day_stats],
        }

    def get_feed(self, limit: int = 20) -> list[dict]:
        """Smart event feed - filters noise, merges consecutive same-app events."""
        from datetime import timedelta
        raw = sorted(self.repo.list(skip=0, limit=limit * 3), key=lambda e: e.created_at)
        if not raw:
            return []
        # Filter out system and noise events
        filtered = []
        for e in raw:
            cat = e.payload.get("category", "other") if isinstance(e.payload, dict) else "other"
            app = e.payload.get("app", "") if isinstance(e.payload, dict) else ""
            if cat == "system":
                continue
            if cat == "other":
                continue
            if cat == "browsing" and any(kw in app for kw in ["下载记录","快速访问","File Explorer"]):
                continue
            if not app or len(app) < 3:
                continue
            filtered.append(e)
        # Merge consecutive same-app events
        merged = []
        for e in filtered:
            app = e.payload.get("app", "") if isinstance(e.payload, dict) else ""
            cat = e.payload.get("category", "other") if isinstance(e.payload, dict) else "other"
            if merged and merged[-1]["app"] == app and merged[-1]["category"] == cat:
                prev = merged[-1]
                prev["duration_seconds"] = abs((e.created_at - prev["_first_ts"]).total_seconds()) if prev.get("_first_ts") else 0
                prev["_last_event"] = str(e.created_at)
                prev["count"] = prev.get("count", 1) + 1
            else:
                merged.append({
                    "app": app,
                    "category": cat,
                    "event_type": e.event_type,
                    "source": e.source,
                    "count": 1,
                    "created_at": str(e.created_at),
                    "duration_seconds": 0,
                    "_first_ts": e.created_at,
                })
        # Format output
        result = []
        for m in merged:
            dur = m.get("duration_seconds", 0)
            if dur > 3600:
                dur_str = f"{int(dur/3600)}小时"
            elif dur > 60:
                dur_str = f"{int(dur/60)}分钟"
            elif dur > 0:
                dur_str = f"{int(dur)}秒"
            else:
                dur_str = "刚刚"
            result.append({
                "app": m["app"][:80],
                "category": m["category"],
                "count": m["count"],
                "duration": dur_str,
                "duration_seconds": dur,
                "created_at": m["created_at"],
            })
        return result[:limit]

    def update_event(self, event_id: int, data: EventUpdate) -> Event | None:
        event = self.repo.get_by_id(event_id)
        if event is None: return None
        if data.event_type is not None:
            if data.event_type not in self.VALID_EVENT_TYPES:
                raise ValueError(f"Invalid event_type: {data.event_type}")
            event.event_type = data.event_type
        if data.source is not None:
            if data.source not in self.VALID_SOURCES:
                raise ValueError(f"Invalid source: {data.source}")
            event.source = data.source
        if data.payload is not None: event.payload = data.payload
        updated = self.repo.update(event)
        logger.info(f"Event updated: id={event_id}")
        return updated

    def delete_event(self, event_id: int) -> bool:
        event = self.repo.get_by_id(event_id)
        if event is None: return False
        self.repo.delete(event)
        logger.info(f"Event deleted: id={event_id}")
        return True
