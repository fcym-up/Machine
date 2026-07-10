"""Test multi-turn conversation memory."""
import pytest
from app.api.v1.conversation import conv_memory, add_to_history, get_history


class TestConversationMemory:
    def setup_method(self):
        conv_memory.clear()

    def test_add_and_retrieve_history(self):
        add_to_history(role="user", content="wangwu")
        add_to_history(role="assistant", content="hello wangwu")
        h = get_history(db=None)
        assert len(h) == 2
        assert h[0]["content"] == "wangwu"
        assert h[1]["content"] == "hello wangwu"

    def test_max_turns_truncation(self):
        for i in range(15):
            add_to_history(role="user", content=f"msg{i}")
        h = get_history(db=None, max_turns=5)
        assert len(h) == 10  # 5 turns * 2 = 10 messages
        assert h[0]["content"] == "msg5"

    def test_empty_history(self):
        h = get_history(db=None)
        assert h == []

    def test_memory_capacity(self):
        for i in range(50):
            add_to_history(role="user", content=f"msg{i}")
        assert len(conv_memory["default"]) == 20  # MAX_CACHE_TURNS * 2 = 20
