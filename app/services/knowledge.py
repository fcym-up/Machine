"""KnowledgeService — 知识图谱业务逻辑。

管理 Entity 和 Relationship 的 CRUD、
从 payload 中提取实体、图谱查询（节点+边）。
"""
from loguru import logger
from sqlalchemy.orm import Session

from app.models.knowledge import Entity, Relationship
from app.repositories.knowledge_repository import EntityRepository, RelationshipRepository
from app.schemas.knowledge import EntityCreate, EntityUpdate, RelationshipCreate
from app.services.llm_entity_extractor import llm_extractor


class KnowledgeService:
    VALID_ENTITY_TYPES = {"person", "organization", "technology", "location", "event", "concept"}

    def __init__(self, db: Session):
        self.entity_repo = EntityRepository(db)
        self.relation_repo = RelationshipRepository(db)
        self.db = db
        self.extractor = llm_extractor

    def create_entity(self, data: EntityCreate) -> Entity:
        if data.entity_type not in self.VALID_ENTITY_TYPES:
            raise ValueError(f"Invalid entity_type: {data.entity_type}")
        entity = Entity(
            name=data.name,
            entity_type=data.entity_type,
            attributes=data.attributes,
            source_event_id=data.source_event_id,
            confidence=data.confidence,
        )
        created = self.entity_repo.create(entity)
        logger.info(f"Entity created: id={created.id}, name={created.name}")
        return created

    def get_entity(self, entity_id: int) -> Entity | None:
        return self.entity_repo.get_by_id(entity_id)

    def search_entities(self, name: str, entity_type: str | None = None):
        return self.entity_repo.find_by_name(name, entity_type)

    def list_entities(self, skip: int = 0, limit: int = 20, entity_type: str | None = None):
        items = self.entity_repo.list(skip=skip, limit=limit, entity_type=entity_type)
        total = self.entity_repo.count(entity_type=entity_type)
        return items, total

    def update_entity(self, entity_id: int, data: EntityUpdate) -> Entity | None:
        entity = self.entity_repo.get_by_id(entity_id)
        if entity is None:
            return None
        if data.name is not None:
            entity.name = data.name
        if data.entity_type is not None:
            if data.entity_type not in self.VALID_ENTITY_TYPES:
                raise ValueError(f"Invalid entity_type: {data.entity_type}")
            entity.entity_type = data.entity_type
        if data.attributes is not None:
            entity.attributes = data.attributes
        if data.confidence is not None:
            entity.confidence = data.confidence
        return self.entity_repo.update(entity)

    def delete_entity(self, entity_id: int) -> bool:
        entity = self.entity_repo.get_by_id(entity_id)
        if entity is None:
            return False
        self.entity_repo.delete(entity)
        logger.info(f"Entity deleted: id={entity_id}")
        return True

    def extract_and_save(self, payload: dict, event_id: int | None = None) -> list[Entity]:
        extracted = self.extractor.extract(payload)
        entities = []
        for e in extracted:
            entity = Entity(
                name=e["name"],
                entity_type=e["entity_type"],
                attributes={"extracted_from": str(payload)[:100]},
                source_event_id=event_id,
                confidence=e["confidence"],
            )
            created = self.entity_repo.create(entity)
            entities.append(created)
        logger.info(f"Extracted {len(entities)} entities from event {event_id}")
        return entities

    def create_relationship(self, data: RelationshipCreate) -> Relationship:
        rel = Relationship(
            subject_id=data.subject_id,
            predicate=data.predicate,
            object_id=data.object_id,
            source_event_id=data.source_event_id,
            confidence=data.confidence,
        )
        created = self.relation_repo.create(rel)
        logger.info(f"Relationship created: {data.subject_id} -[{data.predicate}]-> {data.object_id}")
        return created

    def get_graph(self, entity_id: int | None = None) -> dict:
        nodes = set()
        edges = []
        if entity_id:
            relations = self.relation_repo.find_by_entity(entity_id)
        else:
            relations = self.relation_repo.list(limit=100)
        for rel in relations:
            nodes.add((rel.subject.id, rel.subject.name, rel.subject.entity_type))
            nodes.add((rel.obj.id, rel.obj.name, rel.obj.entity_type))
            edges.append({
                "subject_id": rel.subject_id,
                "predicate": rel.predicate,
                "object_id": rel.object_id,
            })
        return {
            "nodes": [{"id": n[0], "name": n[1], "entity_type": n[2]} for n in nodes],
            "edges": edges,
        }
