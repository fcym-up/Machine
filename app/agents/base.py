"""Agent 基类。

定义所有 Agent 的统一接口：
- name: Agent 名称
- description: Agent 功能描述
- execute(): 执行 Agent 任务的核心方法
- fallback(): LLM 不可用时的规则回退
"""

from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from app.core.llm import get_llm_client


class BaseAgent(ABC):
    """Agent 基类。所有 Agent 必须继承此类。"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.llm = get_llm_client()

    @property
    def has_llm(self) -> bool:
        """是否已配置 LLM。"""
        return self.llm is not None

    @abstractmethod
    def execute(self, task: str, **kwargs) -> dict[str, Any]:
        """执行 Agent 任务。

        Args:
            task: 任务描述
            **kwargs: 附加参数

        Returns:
            {"success": bool, "result": str, "details": dict}
        """
        pass

    def _log_start(self, task: str) -> None:
        logger.info(f"[{self.name}] 开始执行: {task[:100]}")

    def _log_done(self, task: str) -> None:
        logger.info(f"[{self.name}] 执行完成: {task[:100]}")

    def _llm_or_fallback(
        self, prompt: str, system: str, fallback: Any
    ) -> str | None:
        """尝试 LLM 调用，失败则用回退方案。

        Args:
            prompt: 用户提示词
            system: 系统提示词
            fallback: 回退值

        Returns:
            LLM 回复或回退值
        """
        if self.has_llm:
            from app.core.llm import chat_simple
            result = chat_simple(prompt, system)
            if result:
                return result
            logger.warning(f"[{self.name}] LLM 调用失败，使用回退方案")
        return fallback
