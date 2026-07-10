"""知识图谱操作的 Pydantic Schema。

EntityCreate/Update/Response/List、RelationshipCreate/Response、
GraphNode、GraphEdge、GraphResponse（可视化用）。
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class EntityCreate(BaseModel):
    name: str
    entity_type: str
    attributes: dict[str, Any] | None = None
    source_event_id: int | None = None
    confidence: float = 1.0


class EntityUpdate(BaseModel):
    name: str | None = None
    entity_type: str | None = None
    attributes: dict[str, Any] | None = None
    confidence: float | None = None


class EntityResponse(BaseModel):
    id: int
    name: str
    entity_type: str
    attributes: dict[str, Any] | None = None
    source_event_id: int | None = None
    confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EntityList(BaseModel):
    items: list[EntityResponse]
    total: int


class RelationshipCreate(BaseModel):
    subject_id: int
    predicate: str
    object_id: int
    source_event_id: int | None = None
    confidence: float = 1.0


class RelationshipResponse(BaseModel):
    id: int
    subject_id: int
    predicate: str
    object_id: int
    source_event_id: int | None = None
    confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GraphNode(BaseModel):
    id: int
    name: str
    entity_type: str


class GraphEdge(BaseModel):
    subject_id: int
    predicate: str
    object_id: int


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
