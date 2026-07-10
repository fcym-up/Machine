# Project Machine — 开发路线图

> 受《疑犯追踪》Machine 启发的个人 AI 系统
> 更新日期：2026-07-10
> 注意：本文件已更新以反映实际开发状态。详细设计文档见 SUMMARY.md

## 当前项目状态

| 模块 | 状态 | 说明 |
|------|------|------|
| 后端框架 | 已完成 | FastAPI + SQLAlchemy + PostgreSQL |
| 桌面采集器 | 已完成 | 窗口/空闲/音乐监控，模块化架构 |
| Event 系统 | 已完成 | CRUD/分类/标准化/搜索/统计 |
| 记忆系统 | 已完成 | 四种记忆类型，向量语义搜索 |
| 知识图谱 | 已完成 | 实体/关系 CRUD，LLM辅助抽取 |
| 情报分析 | 已完成 | 模式检测/风险评分/趋势分析 |
| 多 Agent 系统 | 已完成 | Research/Code/Memory/Planner/Security |
| 情绪感知 v2 | 已完成 | 5信号加权融合，持久化历史 |
| 用户画像 | 已完成 | 五维特质/行为模式/状态快照 |
| 记忆固化 | 已完成 | 工作→短→长→语义层级固化 |
| 主动关怀 | 已完成 | 情绪触发/行为模式/LLM生成关怀 |
| 自我反思 | 已完成 | 定时生成反思报告 |
| 语音交互 | 已实现 | 百度 API + WebSocket 实时音频 |
| 前端 Dashboard | 已实现 | Three.js 粒子核心 + 三栏布局 |

## 开发阶段回顾

| Phase | 名称 | 目标 | 状态 |
|-------|------|------|------|
| Phase 0 | 环境建设 | Windows/Linux 开发环境搭建 | 已完成 |
| Phase 1 | Foundation | 项目骨架 + 配置 + DB + Event CRUD | 已完成 |
| Phase 2 | Event Engine | Event 分类/标准化/批处理/搜索/统计 | 已完成 |
| Phase 3 | Memory System | Embedding/向量搜索/记忆 CRUD | 已完成 |
| Phase 4 | Knowledge System | 实体/关系 CRUD + 图谱查询 | 已完成 |
| Phase 5 | Intelligence | 模式检测/风险评分/趋势分析 | 已完成 |
| Phase 6 | Agent System | 多 Agent 系统 | 已完成 |
| Phase 7 | 用户建模/情绪 | 画像/情绪/固化/反思/主动关怀 | 已完成 |
| Phase 8 | 语音交互 | WebSocket 实时语音对话 | 已完成 |
| Phase 9 | 前端重设计 | Three.js 粒子 + 三栏/状态/语音 | 已完成 |

## 后续方向

- **Docker 化**：迁移 PostgreSQL/Redis/Neo4j 到 Docker Compose
- **pgvector**：从 ARRAY(Float) 迁移到原生向量索引
- **性能优化**：修复全表扫描、全局状态非线程安全等问题
- **生产部署**：完善 CI/CD、错误监控、备份策略
- **移动端**：Flutter/React Native 客户端

