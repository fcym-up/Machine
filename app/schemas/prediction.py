"""Prediction schemas."""

from typing import Any
from pydantic import BaseModel


class AnomalyResponse(BaseModel):
    anomalies: list[dict[str, Any]]
    total_analyzed: int


class ForecastResponse(BaseModel):
    forecast: list[float]
    trend: str
    period_days: int
    avg_daily: float


class RiskPredictionResponse(BaseModel):
    predicted_risk: float
    factors: list[dict[str, Any]]
    total_events: int
    recent_24h: int
