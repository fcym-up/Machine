"""Agent API — 多 Agent 任务执行。

GET  /api/v1/agents           — 列出所有可用 Agent
POST /api/v1/agents/research  — ResearchAgent 执行研究任务
POST /api/v1/agents/code      — CodeAgent 执行代码分析
POST /api/v1/agents/memory    — MemoryAgent 执行记忆任务
POST /api/v1/agents/plan      — PlannerAgent 执行任务规划
POST /api/v1/agents/security  — SecurityAgent 执行安全分析
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.research_agent import ResearchAgent
from app.agents.code_agent import CodeAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.security_agent import SecurityAgent
from app.core.database import SessionLocal
from app.schemas.agent import AgentTaskRequest, AgentTaskResponse, AgentListResponse

router = APIRouter(prefix="/agents", tags=["agents"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=AgentListResponse)
def list_agents():
    """列出所有可用 Agent。"""
    return AgentListResponse(agents=[
        {"name": "ResearchAgent", "description": "信息检索与研究报告生成"},
        {"name": "CodeAgent", "description": "代码分析与文件操作"},
        {"name": "MemoryAgent", "description": "长期记忆整理与检索"},
        {"name": "PlannerAgent", "description": "任务分解与规划"},
        {"name": "SecurityAgent", "description": "安全风险分析"},
    ])


@router.post("/research", response_model=AgentTaskResponse)
def run_research_agent(req: AgentTaskRequest):
    agent = ResearchAgent()
    result = agent.execute(req.task, context=req.context or "")
    return AgentTaskResponse(**result)


@router.post("/code", response_model=AgentTaskResponse)
def run_code_agent(req: AgentTaskRequest):
    agent = CodeAgent()
    result = agent.execute(req.task, file_path=req.file_path)
    return AgentTaskResponse(**result)


@router.post("/memory", response_model=AgentTaskResponse)
def run_memory_agent(req: AgentTaskRequest, db: Session = Depends(get_db)):
    agent = MemoryAgent(db=db)
    result = agent.execute(req.task)
    return AgentTaskResponse(**result)


@router.post("/plan", response_model=AgentTaskResponse)
def run_planner_agent(req: AgentTaskRequest):
    agent = PlannerAgent()
    result = agent.execute(req.task, context=req.context or "")
    return AgentTaskResponse(**result)


@router.post("/security", response_model=AgentTaskResponse)
def run_security_agent(req: AgentTaskRequest, db: Session = Depends(get_db)):
    agent = SecurityAgent(db=db)
    result = agent.execute(req.task)
    return AgentTaskResponse(**result)
