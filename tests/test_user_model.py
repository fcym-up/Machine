"""Test user model dimension calculation."""
import pytest, sys
sys.path.insert(0, ".")
from app.core.database import SessionLocal
from app.models.event import Event
from app.models.memory import Memory
from app.models.user_profile import TraitDimension
from app.services.user_model import UserModelService


class TestUserModel:
    def setup_method(self):
        self.db = SessionLocal()
        from app.models.knowledge import Entity, Relationship
        self.db.query(Relationship).delete()
        self.db.query(Entity).delete()
        self.db.query(Memory).delete()
        self.db.query(TraitDimension).delete()
        self.db.query(Event).delete()
        self.db.commit()

    def teardown_method(self):
        self.db.close()

    def test_update_dimensions_empty(self):
        um = UserModelService(self.db)
        result = um.update_dimensions()
        assert result == {"message": "No events to analyze"}

    def test_update_dimensions_with_coding_events(self):
        for i in range(10):
            e = Event(event_type="user-action", source="activity",
                      payload={"app": "Codex", "category": "coding"})
            self.db.add(e)
        self.db.commit()
        um = UserModelService(self.db)
        result = um.update_dimensions()
        assert "productivity" in result
        assert result["productivity"] > 0.5

    def test_trait_dimensions_persisted(self):
        for i in range(5):
            e = Event(event_type="user-action", source="activity",
                      payload={"app": "WeChat", "category": "social"})
            self.db.add(e)
        self.db.commit()
        um = UserModelService(self.db)
        um.update_dimensions()
        dims = self.db.query(TraitDimension).all()
        assert len(dims) == 5
        social = next(d for d in dims if d.dimension == "social_energy")
        assert social.current_value > 0
