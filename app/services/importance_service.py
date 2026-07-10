from __future__ import annotations
from typing import Any
from loguru import logger
from app.algorithms.importance_learner import ImportanceLearner
from app.algorithms.self_learner import SelfLearner


class ImportanceService:

    def __init__(self):
        self._importance = ImportanceLearner()
        self._learner = SelfLearner()
        self._event_scores = {}

    def score_event(self, event_id, event_type, payload, created_at):
        category = payload.get("category", "") if isinstance(payload, dict) else ""
        surprise = self._learner.get_surprise_factor(event_type, category)
        query_score = min(self._importance.query_counts.get(event_id, 0) * 0.05, 0.3)
        score = round(surprise * 0.5 + query_score + 0.2, 3)
        self._event_scores[event_id] = score
        self._importance.scores[event_id] = score
        return score

    def get_important_events(self, top_k=10):
        scored = sorted(self._event_scores.items(), key=lambda x: x[1], reverse=True)
        return [eid for eid, _ in scored[:top_k]]

    def get_score(self, event_id):
        return self._event_scores.get(event_id, 0.5)

    def mark_queried(self, event_id):
        self._importance.record_query(event_id)
        if event_id in self._event_scores:
            self._event_scores[event_id] = min(self._event_scores[event_id] + 0.05, 1.0)

    def get_surface_summary(self):
        if not self._event_scores:
            return {"message": "Not enough data yet", "items": []}
        surfaced = [(eid, score) for eid, score in self._event_scores.items() if score >= 0.6]
        surfaced.sort(key=lambda x: x[1], reverse=True)
        return {
            "threshold": 0.6,
            "total_events": len(self._event_scores),
            "surfaced_count": len(surfaced),
            "items": [{"event_id": eid, "importance": score} for eid, score in surfaced[:20]],
        }


importance_service = ImportanceService()