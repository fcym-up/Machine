"""Test memory consolidation pipeline."""
import pytest, sys
sys.path.insert(0, ".")
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.event import Event
from app.models.memory import Memory
from app.services.consolidation import ConsolidationService


class TestConsolidation:
    def setup_method(self):
        self.db = SessionLocal()
        # Clean up test data
        self.db.query(Memory).delete()
        from app.models.knowledge import Entity, Relationship
        self.db.query(Relationship).delete()
        self.db.query(Entity).delete()
        self.db.query(Event).delete()
        self.db.commit()

    def teardown_method(self):
        self.db.close()

    def test_consolidate_hourly_empty(self):
        cs = ConsolidationService(self.db)
        result = cs.consolidate_hourly()
        assert result["consolidated"] == 0

    def test_consolidate_hourly_with_events(self):
        for i in range(5):
            e = Event(event_type="user-action", source="activity",
                      payload={"app": f"Test{i}", "category": "coding"})
            self.db.add(e)
        self.db.commit()
        cs = ConsolidationService(self.db)
        result = cs.consolidate_hourly()
        assert result["events_processed"] == 5

    def test_memory_layer_creation(self):
        e = Event(event_type="user-action", source="activity",
                  payload={"app": "Test", "category": "coding"})
        self.db.add(e)
        self.db.commit()
        cs = ConsolidationService(self.db)
        cs.consolidate_hourly()
        mems = self.db.query(Memory).filter(Memory.layer == "working").all()
        assert len(mems) > 0
