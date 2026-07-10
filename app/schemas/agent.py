"""Agent 操作的 Pydantic Schema。"""

from typing import Any

from pydantic import BaseModel, Field


class AgentTaskRequest(BaseModel):
    """Agent 任务请求。"""

    task: str = Field(..., description="任务描述")
    context: str | None = Field(None, description="附加上下文信息")
    file_path: str | None = Field(None, description="文件路径（CodeAgent 专用）")


class AgentTaskResponse(BaseModel):
    """Agent 任务响应。"""

    success: bool
    agent: str = ""
    result: str
    details: dict[str, Any] = {}


class AgentListResponse(BaseModel):
    """可用 Agent 列表。"""

    agents: list[dict[str, str]]
