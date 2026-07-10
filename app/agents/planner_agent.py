"""Planner Agent — 任务分解与规划。

将复杂任务分解为可执行的子任务。
"""

from typing import Any

from app.agents.base import BaseAgent


class PlannerAgent(BaseAgent):
    """任务规划与分解 Agent。"""

    SYSTEM_PROMPT = "你是一个专业的任务规划助手。将任务分解为清晰步骤。用中文回复。"

    def __init__(self):
        super().__init__("PlannerAgent", "任务分解与规划")

    def execute(self, task, **kwargs):
        self._log_start(task)
        ctx = kwargs.get("context", "")
        prompt = "请为以下任务制定执行计划：\n" + task
        if ctx:
            prompt += "\n背景：" + ctx
        fallback = f"任务规划：{task}\n\n1.分析需求\n2.设计方案\n3.逐步实现\n4.测试验证\n\n[需LLM API Key获取详细规划]"
        result = self._llm_or_fallback(prompt=prompt, system=self.SYSTEM_PROMPT, fallback=fallback)
        self._log_done(task)
        return {"success": True, "result": result, "details": {"agent": self.name, "has_llm": self.has_llm}}
