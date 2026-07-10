"""Event CRUD 的 Pydantic Schema。

EventCreate：单事件创建请求体
EventBatchCreate：批量导入请求体（1-100 条）
EventUpdate：部分更新请求体
EventResponse：API 响应（含 id/type/source/payload/timestamp）
EventList：分页响应包装
EventSearchParams：搜索过滤查询参数
EventStats：统计聚合响应
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    event_type: str
    source: str
    payload: dict[str, Any]


class EventBatchItem(BaseModel):
    event_type: str | None = None
    source: str
    payload: dict[str, Any]


class EventBatchCreate(BaseModel):
    events: list[EventBatchItem] = Field(..., min_length=1, max_length=100)


class EventUpdate(BaseModel):
    event_type: str | None = None
    source: str | None = None
    payload: dict[str, Any] | None = None


class EventResponse(BaseModel):
    id: int
    event_type: str
    source: str
    payload: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventList(BaseModel):
    items: list[EventResponse]
    total: int


class EventSearchParams(BaseModel):
    event_type: str | None = None
    source: str | None = None
    keyword: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


class EventStats(BaseModel):
    total_events: int
    by_type: list[dict[str, Any]]
    by_source: list[dict[str, Any]]
    by_day: list[dict[str, Any]]
