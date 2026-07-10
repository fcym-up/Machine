"""Memory CRUD 的 Pydantic Schema。

MemoryCreate、MemoryUpdate、MemoryResponse、MemoryList、
MemorySearchResult（语义相似度搜索结果）。
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class MemoryCreate(BaseModel):
    memory_type: str = "episode"
    content: str
    summary: str | None = None
    source_event_id: int | None = None
    importance: float = 0.5
    tags: dict[str, Any] | None = None


class MemoryUpdate(BaseModel):
    content: str | None = None
    summary: str | None = None
    importance: float | None = None
    tags: dict[str, Any] | None = None


class MemoryResponse(BaseModel):
    id: int
    memory_type: str
    content: str
    summary: str | None = None
    source_event_id: int | None = None
    importance: float
    tags: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemoryList(BaseModel):
    items: list[MemoryResponse]
    total: int


class MemorySearchResult(BaseModel):
    id: int
    content: str
    summary: str | None = None
    memory_type: str
    similarity: float
