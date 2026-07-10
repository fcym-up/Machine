"""EventClassifier 与 EventNormalizer 集成测试。

测试批量导入、搜索过滤、统计、
自动分类和 payload 标准化。
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.repositories.event_repository import EventRepository
from app.services.event import EventService
from app.schemas.event import EventCreate, EventBatchCreate, EventBatchItem

DATABASE_URL = "postgresql://postgres:machine123@localhost:5432/machine_test"


@pytest.fixture(scope="module")
def engine():
    return create_engine(DATABASE_URL, echo=False)


@pytest.fixture
def db_session(engine):
    import app.models  # noqa: F401
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()
    Base.metadata.drop_all(engine)


class TestBatchImport:
    def test_batch_import(self, db_session):
        service = EventService(db_session)
        batch = EventBatchCreate(
            events=[
                EventBatchItem(source="browser", payload={"url": "https://a.com"}),
                EventBatchItem(source="browser", payload={"url": "https://b.com"}),
                EventBatchItem(source="terminal", payload={"command": "ls -la"}),
            ]
        )
        events = service.create_batch(batch)
        assert len(events) == 3


class TestSearchFilter:
    def test_search_by_type(self, db_session):
        service = EventService(db_session)
        service.create_event(EventCreate(
            event_type="web-activity", source="browser",
            payload={"url": "https://test.com"}
        ))
        service.create_event(EventCreate(
            event_type="git-commit", source="git",
            payload={"message": "fix bug"}
        ))
        items, total = service.search_events(event_type="web-activity")
        assert total == 1
        assert items[0].event_type == "web-activity"

    def test_search_by_source(self, db_session):
        service = EventService(db_session)
        service.create_event(EventCreate(
            event_type="user-action", source="terminal",
            payload={"command": "python test.py"}
        ))
        items, total = service.search_events(source="terminal")
        assert total >= 1


class TestStats:
    def test_stats(self, db_session):
        service = EventService(db_session)
        service.create_event(EventCreate(
            event_type="web-activity", source="browser",
            payload={"url": "https://example.com"}
        ))
        stats = service.get_stats()
        assert stats["total_events"] >= 1
        assert "by_type" in stats
        assert "by_source" in stats
        assert "by_day" in stats


class TestClassifier:
    def test_classify_browser(self, db_session):
        service = EventService(db_session)
        batch = EventBatchCreate(
            events=[
                EventBatchItem(source="browser", payload={"url": "https://test.com", "page": "home"}),
            ]
        )
        events = service.create_batch(batch)
        assert events[0].event_type == "web-activity"


class TestNormalizer:
    def test_normalize_terminal(self, db_session):
        service = EventService(db_session)
        event = service.create_event(EventCreate(
            event_type="user-action", source="terminal",
            payload={"command": "  ls -la  "}
        ))
        assert event.payload["_command"] == "ls -la"
        assert event.payload["_source_normalized"] == "terminal"
