"""EventRepository 单元测试。

在独立的 PostgreSQL 测试数据库（machine_test）上
测试 CRUD 操作、搜索和统计方法。
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.event import Event
from app.repositories.event_repository import EventRepository

DATABASE_URL = "postgresql://postgres:machine123@localhost:5432/machine_test"


@pytest.fixture(scope="function")
def engine():
    return create_engine(DATABASE_URL, echo=False)


@pytest.fixture(scope="function")
def tables(engine):
    import app.models  # noqa: F401
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(engine, tables):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


class TestEventRepository:
    def test_create_event(self, db_session):
        repo = EventRepository(db_session)
        event = Event(
            event_type="user-action",
            source="browser",
            payload={"url": "https://example.com", "action": "visit"},
        )
        created = repo.create(event)
        assert created.id is not None
        assert created.event_type == "user-action"
        assert created.payload["url"] == "https://example.com"

    def test_get_by_id(self, db_session):
        repo = EventRepository(db_session)
        event = Event(event_type="test", source="test", payload={"key": "value"})
        created = repo.create(event)
        found = repo.get_by_id(created.id)
        assert found is not None
        assert found.payload["key"] == "value"

    def test_get_by_id_not_found(self, db_session):
        repo = EventRepository(db_session)
        assert repo.get_by_id(99999) is None

    def test_list_events(self, db_session):
        repo = EventRepository(db_session)
        for i in range(5):
            event = Event(event_type="test", source="test", payload={"index": i})
            repo.create(event)
        items = repo.list(skip=0, limit=3)
        assert len(items) == 3
        assert repo.count() == 5

    def test_update_event(self, db_session):
        repo = EventRepository(db_session)
        event = Event(event_type="old", source="old", payload={"old": True})
        created = repo.create(event)
        created.payload = {"new": True}
        updated = repo.update(created)
        assert updated.payload["new"] is True

    def test_delete_event(self, db_session):
        repo = EventRepository(db_session)
        event = Event(event_type="delete-me", source="test", payload={})
        created = repo.create(event)
        repo.delete(created)
        assert repo.get_by_id(created.id) is None
