# Project Machine

> **受《疑犯追踪》"The Machine" 启发的个人 AI 系统**
>
> 版本 v0.5.0 | 2026-07-08 | 43 项测试全部通过（已优化）

---

## 项目概述

Project Machine 的目标不是复刻影视作品，而是构建一个能够长期积累信息、理解事件、辅助决策的智能平台。整个系统围绕 **Event（事件）** 构建——世界中的所有变化（浏览网页、创建文件、Git 提交、AI 推理、用户聊天）都被抽象为 Event，经由分析管道转化为知识、记忆和决策依据。

**核心设计文档：** [Machine 项目总体设计方案.pdf](C:/Users/赵鹏程/Desktop/machine/Machine%20项目总体设计方案.pdf)

---

## 总体架构（依据设计文档第3节）

```
  现实世界 → 数据采集层 → Event Engine → Memory System
                                    ↓
                              Knowledge System
                                    ↓
                            Intelligence Engine
                                    ↓
                             Prediction Engine
                                    ↓
                               User Interface (API)
```

**当前技术实现（依据设计文档第8节技术选型）：**

| 层次 | 设计文档选型 | 当前实现 | 状态 |
|------|-------------|---------|------|
| 后端语言 | Python | Python 3.13 | ✅ |
| Web 框架 | FastAPI | FastAPI 0.122 | ✅ |
| 核心数据库 | PostgreSQL | PostgreSQL 18 | ✅ |
| 缓存 | Redis | 未安装（docker-compose 预留） | ⬜ |
| 向量数据库 | Qdrant/pgvector | Float[] ARRAY (pgvector 未安装) | ⚠️ |
| 知识图谱 | Neo4j | PostgreSQL 关系表模拟 | ⚠️ |
| 消息队列 | Kafka/RabbitMQ | 未安装 | ⬜ |
| AI 框架 | LangChain/LlamaIndex | 未安装 | ⬜ |

> ⚠️ 标记项详见 [GAP_ANALYSIS.md](docs/GAP_ANALYSIS.md)

---

## 系统核心模块（依据设计文档第4节）

### 4.1 Data Collection Layer（数据采集层）
- **当前状态：** 手动 API 输入
- **未来：** 浏览器插件、Git hooks、系统监控

### 4.2 Event Engine（事件引擎）✅ Phase 2
- Event 标准化：所有输入统一为 `{id, event_type, source, payload, created_at}`
- 批量导入：`POST /api/v1/events/batch`
- 搜索过滤：`GET /api/v1/events/search?type=&source=&keyword=`
- 统计分析：`GET /api/v1/events/stats`
- 自动分类：EventClassifier（关键词→event_type 映射）
- 标准化管道：EventNormalizer（按 source 类型的 payload 规整）

### 4.3 Memory System（记忆系统）✅ Phase 3
- Short Memory / Long Memory / Semantic Memory / Episode Memory
- CRUD API：`POST/GET/PUT/DELETE /api/v1/memories`
- 语义搜索：`GET /api/v1/memories/search?query=...`
- Embedding 引擎：SimpleEmbedder（128 维 hash-based 向量）
- 记忆-事件链接：`source_event_id` 外键

### 4.4 Knowledge System（知识系统）✅ Phase 4
- Entity（实体）模型与 CRUD：`/api/v1/knowledge/entities`
- Relationship（关系）模型：`/api/v1/knowledge/relationships`
- 知识图谱查询：`GET /api/v1/knowledge/graph`
- 实体抽取：正则表达式模式匹配（person/org/tech）

### 4.5 Intelligence Engine（智能分析引擎）✅ Phase 5
- 模式识别：`GET /api/v1/intelligence/patterns`
- 风险评分：`GET /api/v1/intelligence/risk`
- 趋势分析：`GET /api/v1/intelligence/trends`

### 4.5.1 认证系统 ✅ 已优化
- API Key 认证：`X-API-Key` header 校验（详见 ADR-0002）
- 所有 `/api/v1/*` 端点受保护
- `GET /` 和 `/docs` 保持公开

### 4.6 Prediction Engine（预测系统）⬜
- 设计文档规划：异常行为检测、趋势预测、潜在风险评估
- 依赖：LLM 集成（Phase 6-7）

### 4.7 Agent System（智能代理系统）⬜
- 设计文档规划：Research Agent、Analysis Agent、Automation Agent
- 目标：多 Agent 协同工作
- 计划：Phase 6

---

## 开发路线图（依据设计文档第9节）

| Phase | 名称 | 对应设计文档 | 状态 | 测试 |
|-------|------|-------------|------|------|
| Phase 0 | 环境建设 | Phase 0 | ✅ | — |
| Phase 1 | Foundation | Phase 1 | ✅ | 6/6 |
| Phase 2 | Event Engine | Phase 2 | ✅ | 6/6 |
| Phase 3 | Memory System | Phase 3 | ✅ | 8/8 |
| Phase 4 | Knowledge System | Phase 4 | ✅ | 6/6 |
| Phase 5 | Intelligence System | Phase 5 | ✅ | 3/3 |
| Phase 6 | Agent System | Phase 6 | ⬜ | — |
| Phase 7 | Automation | — | ⬜ | — |

**累计：43 项测试全部通过**

---

## 项目结构（依据设计文档第6节）

```
D:\workplace/
├── app/
│   ├── api/v1/           # REST API
│   │   ├── events.py     # POST/GET /events, /events/batch, /events/search, /events/stats
│   │   ├── memories.py   # POST/GET /memories, /memories/search
│   │   ├── knowledge.py  # CRUD /knowledge/entities, /relationships, /graph
│   │   └── intelligence.py  # GET /intelligence/patterns, /risk, /trends
│   ├── core/             # config.py, database.py, logger.py
│   ├── models/           # Event, Memory, Entity, Relationship
│   ├── schemas/          # Pydantic request/response schemas
│   ├── repositories/     # EventRepository, MemoryRepository, EntityRepository
│   ├── services/         # EventService, MemoryService, KnowledgeService, IntelligenceService
│   │   ├── embedding.py  # SimpleEmbedder (hash-based 128-dim vectors)
│   │   ├── event_engine.py # EventClassifier + EventNormalizer
│   │   └── entity_extractor.py # Regex-based entity extraction
│   ├── agents/           # [预留] Research/Code/Memory/Planner/Security Agent
│   ├── memory/           # [预留]
│   └── graph/            # [预留]
├── alembic/              # 数据库迁移
├── docker/               # Docker 配置
├── docs/                 # ROADMAP, ADR, Phase Reports, GAP_ANALYSIS
├── tests/                # 29 项测试
├── scripts/              # daily_shutdown.ps1
├── docker-compose.yml    # [就绪] PostgreSQL + Redis + Neo4j + Ollama
├── .env / .env.example
└── README.md
```

---

## 快速启动

```bash
# 前提：PostgreSQL 18 运行中 (C:\pgsql)
cd D:\workplace
uvicorn app.main:app --reload

# API 文档： http://127.0.0.1:8000/docs
# 健康检查： curl http://127.0.0.1:8000/
# 运行测试： pytest tests/ -v
```

---

## 关键文档索引

| 文档 | 内容 |
|------|------|
| [ROADMAP](docs/ROADMAP.md) | 8 阶段开发路线图 |
| [GAP_ANALYSIS](docs/GAP_ANALYSIS.md) | 当前实现与设计方案的差距 |
| [CHANGELOG](CHANGELOG.md) | 版本发布记录 |
| [ADR-0001](docs/adr/ADR-0001-payload-jsonb.md) | payload 用 JSONB 的决策 |
| [Phase 1 Report](docs/phases/PHASE-01-foundation.md) | Foundation 阶段报告 |
| [Phase 2 Report](docs/phases/PHASE-02-event-engine.md) | Event Engine 阶段报告 |
| [Phase 3 Report](docs/phases/PHASE-03-memory.md) | Memory System 阶段报告 |
| [Phase 4 Report](docs/phases/PHASE-04-knowledge.md) | Knowledge System 阶段报告 |
| [Phase 5 Report](docs/phases/PHASE-05-intelligence.md) | Intelligence System 阶段报告 |

---

---

## 已完成的优化（v0.5.0 优化轮次）

| 优化项 | 位置 | 状态 |
|--------|------|:--:|
| datetime.utcnow 废弃修复 | models/*.py | ✅ |
| API Key 认证 | app/core/security.py + main.py | ✅ |
| API 限流（100 req/min） | app/main.py middleware | ✅ |
| HTTP 请求日志 | app/main.py middleware | ✅ |
| API 集成测试（14 个） | tests/test_api.py | ✅ |
| Embedding NaN/维度修复 | app/services/embedding.py | ✅ |
| make_interval SQL 兼容 | app/repositories/event_repository.py | ✅ |

> 无法现在优化的项（缺外部工具）仍在 [GAP_ANALYSIS.md](docs/GAP_ANALYSIS.md) 中跟踪

---
## 下一阶段（Phase 6 — Agent System）

依据设计文档 4.7 节，Phase 6 将实现多 Agent 协同：

- Research Agent — 信息检索与研究报告生成
- Code Agent — 代码分析与操作
- Memory Agent — 长期记忆整理与检索
- Planner Agent — 任务分解与规划
- Security Agent — 安全风险分析

**入口条件：** JWT 认证 + LLM API key 可用
