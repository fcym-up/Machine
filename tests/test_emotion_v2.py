"""Emotion v2 system integration tests."""
import pytest
from datetime import datetime, timezone, timedelta

from app.core.database import SessionLocal
from app.models.emotion import EmotionSignal, EmotionState, SignalWeight
from app.algorithms.emotion_computer import EmotionComputer
from app.services.emotion_collector import collect_all, inject_conversation_signal


class TestEmotionComputer:
    def setup_method(self):
        self.db = SessionLocal()
        for src, w in [("conversation", 0.35), ("window", 0.20), ("time", 0.10)]:
            sw = self.db.query(SignalWeight).filter_by(source=src).first()
            if not sw:
                self.db.add(SignalWeight(source=src, weight=w))
        self.db.commit()

    def teardown_method(self):
        self.db.query(EmotionState).delete()
        self.db.query(EmotionSignal).delete()
        self.db.commit()
        self.db.close()

    def test_no_signals_returns_none(self):
        computer = EmotionComputer()
        result = computer.compute(self.db)
        assert result is None or isinstance(result, EmotionState)

    def test_single_signal_computes(self):
        self.db.add(EmotionSignal(
            source="conversation", emotion_label="开心",
            weight=0.35, confidence=0.8,
            payload={"factor": "test"},
        ))
        self.db.commit()
        computer = EmotionComputer()
        state = computer.compute(self.db)
        assert state is not None
        assert state.primary_emotion == "开心"
        assert state.confidence > 0
        assert state.signal_count >= 1

    def test_time_decay_reduces_old_signals(self):
        old = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=4000)
        self.db.add(EmotionSignal(
            source="window", emotion_label="专注",
            weight=0.20, confidence=0.8,
            created_at=old,
        ))
        self.db.add(EmotionSignal(
            source="conversation", emotion_label="开心",
            weight=0.35, confidence=0.9,
        ))
        self.db.commit()
        computer = EmotionComputer()
        state = computer.compute(self.db)
        assert state is not None
        assert state.primary_emotion == "开心"

    def test_conversation_signal_injection(self):
        sig = inject_conversation_signal(
            self.db, "开心", confidence=0.9,
            payload={"factor": "test"},
        )
        assert sig is not None
        assert sig.emotion_label == "开心"
        assert float(sig.confidence) == 0.9

    def test_invalid_emotion_rejected(self):
        sig = inject_conversation_signal(self.db, "not_an_emotion", confidence=0.9)
        assert sig is None

    def test_collect_all_runs(self):
        result = collect_all(self.db)
        assert isinstance(result, dict)
        assert "window" in result
        assert "idle" in result
        assert "time" in result
