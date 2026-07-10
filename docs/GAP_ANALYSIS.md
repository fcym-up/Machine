> [过时声明] 本文档于 2026-07-08 创建，之后大量功能已补充实现
> （LLM 接入、Embedding 升级、情绪感知 v2、Agent 系统等）。
> 当前实际差距和待优化项请参考项目根目录的分析。
# Gap Analysis — 当前实现 vs 设计方案

> 对照原始《Machine 项目总体设计方案》v1.0 和其他设计文档，记录当前实现的差距、原因和解决计划。

## 数据库与基础设施

| 设计方案要求 | 当前实现 | 差距 | 计划 |
|-------------|---------|------|------|
| PostgreSQL + Docker | PostgreSQL 18 (zip 直装) | 无 Docker 环境，docker-compose.yml 已就绪 | 等 Docker 可用后迁移 |
| Redis 缓存 | 无 | 未安装 Redis | docker-compose 已预留 Redis 服务 |
| Neo4j 知识图谱 | PostgreSQL 关系表模拟 | 无 Neo4j 实例 | docker-compose 已预留，Phase 4 代码兼容 Neo4j API 语义 |
| pgvector 向量检索 | Float[] ARRAY 列 | pgvector 扩展未安装 | PostgreSQL zip 不含 pgvector，需重新编译或等 Docker |
| Kafka/RabbitMQ 消息队列 | 无 | 设计文档 Phase 2+ 规划 | 当前事件量小不需要，Phase 6+ 评估 |

## AI / 智能模块

| 设计方案要求 | 当前实现 | 差距 | 计划 |
|-------------|---------|------|------|
| LLM 推理分析 | 无 | 无 OpenAI API key | 预留 langchain 集成点，Phase 6 Agent 需要时接入 |
| 语义 Embedding | hash-based SimpleEmbedder (128-dim) | 非 ML embedding，语义匹配效果有限 | 安装 sentence-transformers (all-MiniLM-L6-v2) 替换 |
| NER 实体抽取 | regex 模式匹配 | 无法从 dict payload 抽取实体 | 安装 spaCy 或使用 LLM API |
| LangChain / LlamaIndex | 无 | 未安装 | Phase 6 Agent 需要时安装 |

## 代码质量

| 问题 | 位置 | 严重度 | 计划 |
|------|------|--------|------|
| datetime.utcnow() 已废弃 | models/*.py | 低 | ✅ 已修复（使用 lambda: datetime.now(timezone.utc)） |
| 同步 SQLAlchemy | 全局 | 中 | Phase 6+ 评估并发需求后决定 |
| API Key 认证 | API 全部端点 | ✅ 已修复（API Key + X-API-Key header，见 ADR-0002） |
| API 限流 | API 全部端点 | ✅ 已修复（内存限流，100 req/60s per IP+path） |
| HTTP 请求日志 | main.py | ✅ 已修复（middleware 日志 method/path/status/duration） |

## 测试

| 项目 | 现状 | 差距 |
|------|------|------|
| 单元测试 | 29 tests, all passing | 缺少 API 集成测试（httpx） |
| 测试覆盖率 | 未度量 | 需添加 pytest-cov |
| CI/CD | 无 | 需配置 GitHub Actions |

## 文档

| 项目 | 现状 |
|------|------|
| README | ✅ Phase 1-5 完整说明 |
| ROADMAP | ✅ 8 Phase 路线图 |
| ADR | ✅ ADR-0001 (payload JSONB) |
| CHANGELOG | ✅ v0.1.0 ~ v0.5.0 |
| Phase Reports | ✅ PHASE-01 ~ PHASE-05 |
| GAP_ANALYSIS | ✅ 本文档 |
