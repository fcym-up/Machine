"""智能分析结果的 Pydantic Schema。

PatternResponse：事件频率模式与高峰时段
RiskResponse：基于规则的风险评分及因素
TrendResponse：每日趋势分析（increasing/stable/decreasing）
"""
from pydantic import BaseModel
from typing import Any


class PatternItem(BaseModel):
    type: str
    detail: str
    count: int
    frequency: float | None = None


class PatternResponse(BaseModel):
    total_events: int
    period_days: int
    patterns: list[dict[str, Any]]
    top_types: list[dict[str, Any]]
    top_sources: list[dict[str, Any]]


class RiskFactor(BaseModel):
    factor: str
    detail: str
    contribution: float


class RiskResponse(BaseModel):
    overall_risk: float
    factors: list[dict[str, Any]]
    total_events: int
    events_last_hour: int


class DayData(BaseModel):
    day: str
    count: int


class TrendResponse(BaseModel):
    period_days: int
    trend: str
    daily_data: list[dict[str, Any]]
    total: int
    avg_per_day: float
