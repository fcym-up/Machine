"""Security Agent — 安全风险分析。

分析系统事件、检测异常模式、评估安全风险。
"""

from typing import Any

from app.agents.base import BaseAgent
from sqlalchemy.orm import Session

from app.services.intelligence import IntelligenceService


class SecurityAgent(BaseAgent):
    """安全风险分析 Agent。"""

    SYSTEM_PROMPT = "你是一个专业的安全分析助手。分析系统事件和风险。用中文回复。"

    def __init__(self, db: Session | None = None):
        super().__init__("SecurityAgent", "安全风险分析")
        self.db = db
        self.intel = IntelligenceService(db) if db else None

    def execute(self, task, **kwargs):
        self._log_start(task)
        info = ""
        if self.intel:
            risk = self.intel.risk_score()
            info = f"风险评分：{risk.get("overall_risk",0)}/100\n事件数：{risk["total_events"]}"
        prompt = "安全任务：" + task + "\n\n系统状态：\n" + info + "\n\n请分析并给建议。"
        result = self._llm_or_fallback(prompt=prompt, system=self.SYSTEM_PROMPT, fallback="安全分析：\n" + info + "\n[需LLM API Key]")
        self._log_done(task)
        return {"success": True, "result": result, "details": {"agent": self.name, "has_llm": self.has_llm}}
