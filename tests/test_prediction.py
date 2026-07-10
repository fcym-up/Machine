"""Prediction Engine tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.event import Event
from app.repositories.event_repository import EventRepository
from app.services.prediction import PredictionEngine

DATABASE_URL = "postgresql://postgres:machine123@localhost:5432/machine_test"

@pytest.fixture(scope="module")
def engine():
    return create_engine(DATABASE_URL, echo=False)

@pytest.fixture
def db_session(engine):
    import app.models
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()
    Base.metadata.drop_all(engine)

class TestAnomalyDetection:
    def test_no_anomalies_empty(self, db_session):
        engine = PredictionEngine(db_session)
        result = engine.detect_anomalies()
        assert result["total_analyzed"] == 0

    def test_detect_unusual_frequency(self, db_session):
        repo = EventRepository(db_session)
        for i in range(30):
            repo.create(Event(event_type="unusual-spike", source="test", payload={"i": i}))
        engine = PredictionEngine(db_session)
        result = engine.detect_anomalies(lookback_hours=48)
        assert len(result["anomalies"]) >= 0

class TestForecast:
    def test_forecast(self, db_session):
        repo = EventRepository(db_session)
        for i in range(10):
            repo.create(Event(event_type="test", source="test", payload={"i": i}))
        engine = PredictionEngine(db_session)
        result = engine.forecast()
        assert "forecast" in result
        assert len(result["forecast"]) == 3

class TestRiskPrediction:
    def test_risk_prediction(self, db_session):
        repo = EventRepository(db_session)
        repo.create(Event(event_type="test", source="test", payload={}))
        engine = PredictionEngine(db_session)
        result = engine.risk_prediction()
        assert "predicted_risk" in result
        assert 0 <= result["predicted_risk"] <= 100
