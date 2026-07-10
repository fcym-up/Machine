"""Code Agent — 代码分析与文件操作。

分析代码结构、检查代码质量、生成代码文档。
"""

import os
from typing import Any

from app.agents.base import BaseAgent


class CodeAgent(BaseAgent):
    """代码分析与操作 Agent。"""

    SYSTEM_PROMPT = "你是一个专业的代码分析助手。分析代码结构、检查代码质量。用中文回复。"

    def __init__(self):
        super().__init__("CodeAgent", "代码分析与文件操作")

    def execute(self, task, **kwargs):
        self._log_start(task)
        file_path = kwargs.get("file_path", "")
        if file_path and os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as fh:
                content = fh.read()[:5000]
        else:
            content = task
        prompt = "分析代码:\n`\n" + content + "\n`\n给出分析报告。"
        result = self._llm_or_fallback(prompt=prompt, system=self.SYSTEM_PROMPT, fallback=self._fallback(file_path, content))
        self._log_done(task)
        return {"success": True, "result": result, "details": {"agent": self.name, "has_llm": self.has_llm}}

    def _fallback(self, fp, content):
        lines = content.split("\n")
        fns = [l.strip() for l in lines if l.strip().startswith("def ")]
        cls = [l.strip() for l in lines if l.strip().startswith("class ")]
        imps = [l.strip() for l in lines if l.strip().startswith(("import ", "from "))]
        r = [f"代码分析: {fp or 'code'}", f"行数:{len(lines)} 函数:{len(fns)} 类:{len(cls)} 导入:{len(imps)}"]
        if fns:
            r.append("函数:" + ",".join(fns[:5]))
        return "\n".join(r)
