"""智能分析单元测试。

测试模式检测、风险评分和趋势分析。
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.event import Event
from app.repositories.event_repository import EventRepository
from app.services.intelligence import IntelligenceService

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


class TestPatternDetection:
    def test_patterns(self, db_session):
        repo = EventRepository(db_session)
        for i in range(10):
            repo.create(Event(event_type="web-activity", source="browser", payload={"url": f"page{i}"}))
        for i in range(5):
            repo.create(Event(event_type="git-commit", source="git", payload={"msg": f"fix{i}"}))
        service = IntelligenceService(db_session)
        result = service.detect_patterns(days=30)
        assert result["total_events"] >= 15
        assert len(result["patterns"]) >= 1


class TestRiskScoring:
    def test_risk_score(self, db_session):
        repo = EventRepository(db_session)
        for i in range(30):
            repo.create(Event(event_type="system-event", source="system", payload={"error": f"E{i}"}))
        service = IntelligenceService(db_session)
        result = service.risk_score()
        assert result["overall_risk"] >= 0
        assert result["total_events"] >= 30


class TestTrendAnalysis:
    def test_trend(self, db_session):
        repo = EventRepository(db_session)
        repo.create(Event(event_type="test", source="test", payload={}))
        service = IntelligenceService(db_session)
        result = service.trend_analysis(days=30)
        assert result["total"] >= 1
        assert result["trend"] in ("stable", "increasing", "decreasing")
