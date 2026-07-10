"""Research Agent — 信息检索与研究报告生成。

接收研究主题，利用 LLM 或规则引擎分析相关信息，
生成结构化的研究报告。
"""

from typing import Any

from app.agents.base import BaseAgent


class ResearchAgent(BaseAgent):
    """信息检索与研究分析 Agent。"""

    SYSTEM_PROMPT = "你是一个专业的研究分析助手。请对主题进行深入分析并生成结构化研究报告。用中文回复。"

    def __init__(self):
        super().__init__("ResearchAgent", "信息检索与研究报告生成")

    def execute(self, task, **kwargs):
        self._log_start(task)
        context = kwargs.get("context", "")
        prompt = f"研究主题：{task}"
        if context:
            prompt += f"\n背景信息：{context}"
        prompt += "\n请按照标准研究报告格式进行分析。"
        result = self._llm_or_fallback(prompt=prompt, system=self.SYSTEM_PROMPT, fallback=self._fallback(task, context))
        self._log_done(task)
        return {"success": True, "result": result, "details": {"agent": self.name, "has_llm": self.has_llm}}

    def _fallback(self, task, context):
        lines = [f"研究报告：{task}", "", "1. 主题概述", f"   对「{task}」进行基础分析。", "", "2. 关键发现"]
        if context:
            lines.append(f"   背景：{context[:200]}")
        lines.extend(["", "3. 详细分析", "   [需要 LLM API Key 以启用深度分析]", "", "4. 结论与建议", "   请在 .env 中配置 LLM_API_KEY。"])
        return "\n".join(lines)
