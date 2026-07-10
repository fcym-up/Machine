"""Memory Agent — 长期记忆整理与检索。

负责整理、总结、归档记忆，执行语义搜索。
"""

from typing import Any

from app.agents.base import BaseAgent
from sqlalchemy.orm import Session

from app.services.embedding import embedder
from app.services.memory import MemoryService


class MemoryAgent(BaseAgent):
    """长期记忆管理与检索 Agent。"""

    SYSTEM_PROMPT = "你是一个专业的记忆管理助手。整理和总结用户的长期记忆。用中文回复。"

    def __init__(self, db: Session | None = None):
        super().__init__("MemoryAgent", "长期记忆整理与检索")
        self.db = db
        self.memory_service = MemoryService(db) if db else None

    def execute(self, task, **kwargs):
        self._log_start(task)
        if self.memory_service:
            similar = self.memory_service.search_similar(task, limit=5)
            ctx = "\n".join([f"- {m.content[:200]}" for m, _ in similar])
        else:
            ctx = "无数据库连接"
        prompt = "任务：" + task + "\n\n相关记忆：\n" + ctx + "\n\n请分析并给出建议。"
        result = self._llm_or_fallback(prompt=prompt, system=self.SYSTEM_PROMPT, fallback="记忆检索结果：\n" + ctx)
        self._log_done(task)
        return {"success": True, "result": result, "details": {"agent": self.name, "has_llm": self.has_llm}}
