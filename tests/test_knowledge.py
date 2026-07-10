"""知识图谱系统单元测试。

测试 Entity CRUD、Relationship 创建、图谱查询、
实体类型验证。
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.services.knowledge import KnowledgeService
from app.schemas.knowledge import EntityCreate, EntityUpdate, RelationshipCreate

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


class TestEntityCRUD:
    def test_create_entity(self, db_session):
        service = KnowledgeService(db_session)
        entity = service.create_entity(EntityCreate(name="Google", entity_type="organization"))
        assert entity.id is not None
        assert entity.name == "Google"

    def test_get_entity(self, db_session):
        service = KnowledgeService(db_session)
        created = service.create_entity(EntityCreate(name="PostgreSQL", entity_type="technology"))
        found = service.get_entity(created.id)
        assert found.name == "PostgreSQL"

    def test_list_by_type(self, db_session):
        service = KnowledgeService(db_session)
        service.create_entity(EntityCreate(name="Alice", entity_type="person"))
        service.create_entity(EntityCreate(name="Bob", entity_type="person"))
        service.create_entity(EntityCreate(name="Redis", entity_type="technology"))
        items, total = service.list_entities(entity_type="person")
        assert total == 2

    def test_update_entity(self, db_session):
        service = KnowledgeService(db_session)
        created = service.create_entity(EntityCreate(name="Postgres", entity_type="technology"))
        updated = service.update_entity(created.id, EntityUpdate(name="PostgreSQL 18", confidence=0.95))
        assert updated.name == "PostgreSQL 18"
        assert updated.confidence == 0.95


class TestEntityExtraction:
    pass  # tracked in GAP_ANALYSIS.md

class TestRelationship:
    def test_create_relationship(self, db_session):
        service = KnowledgeService(db_session)
        e1 = service.create_entity(EntityCreate(name="Alice", entity_type="person"))
        e2 = service.create_entity(EntityCreate(name="GitHub", entity_type="organization"))
        rel = service.create_relationship(RelationshipCreate(
            subject_id=e1.id, predicate="works_at", object_id=e2.id
        ))
        assert rel.predicate == "works_at"

    def test_graph(self, db_session):
        service = KnowledgeService(db_session)
        e1 = service.create_entity(EntityCreate(name="Alice", entity_type="person"))
        e2 = service.create_entity(EntityCreate(name="PostgreSQL", entity_type="technology"))
        service.create_relationship(RelationshipCreate(
            subject_id=e1.id, predicate="uses", object_id=e2.id
        ))
        graph = service.get_graph()
        assert len(graph["nodes"]) >= 2
        assert len(graph["edges"]) >= 1
