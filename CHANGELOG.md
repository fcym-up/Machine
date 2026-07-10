# CHANGELOG

## [v0.5.0] — 2026-07-08

### Added
- Authentication: API Key auth for all /api/v1/* endpoints (ADR-0002)
- Rate limiting: 100 requests per 60s per IP+path
- HTTP request logging middleware (method/path/status/duration)
- API integration tests (14 tests with TestClient)
- Fixed datetime.utcnow deprecation across all models
- Fixed embedding dimension and NaN issues
- Intelligence System: pattern detection, risk scoring, trend analysis
- GET /api/v1/intelligence/patterns — event frequency and peak hour detection
- GET /api/v1/intelligence/risk — rule-based risk scoring (high freq, errors)
- GET /api/v1/intelligence/trends — daily trend analysis (increasing/stable/decreasing)
- Integration tests (3/3 passed)

## [v0.4.0] — 2026-07-08

### Added
- Knowledge System: Entity + Relationship models
- Entity CRUD API (POST/GET/PUT/DELETE /api/v1/knowledge/entities)
- Relationship API (POST /api/v1/knowledge/relationships)
- Graph query (GET /api/v1/knowledge/graph)
- Entity extraction from payloads (regex-based)
- Integration tests (7/7 passed)

## [v0.3.0] — 2026-07-08

### Added
- Memory System: Short/Long/Semantic/Episodic memory types
- Embedding engine: hash-based 128-dim vectors (SimpleEmbedder)
- Memory CRUD API (POST/GET/PUT/DELETE /api/v1/memories)
- Vector similarity search (GET /api/v1/memories/search)
- Memory-to-Event linking (source_event_id)
- Integration tests (8/8 passed)

## [v0.2.0] — 2026-07-08

### Added
- Event batch import API (POST /api/v1/events/batch)
- Event search & filter API (GET /api/v1/events/search)
- Event statistics & aggregation API (GET /api/v1/events/stats)
- EventClassifier: keyword-based auto event_type classification
- EventNormalizer: per-source payload normalization pipeline
- Integration tests for batch, search, stats, classifier, normalizer

## [v0.1.0] — 2026-07-08

### Added
- 项目骨架与目录结构
- 配置系统（dotenv + Settings）
- 日志系统（loguru）
- PostgreSQL 数据库连接（SQLAlchemy + JSONB）
- Event 数据模型（event_type, source, payload, created_at）
- Event CRUD API（/api/v1/events）
- Repository + Service 分层架构
- Alembic 数据库迁移
- 单元测试（pytest）
- Docker Compose 配置
- 项目文档体系（ROADMAP, ADR, CHANGELOG, Phase Report）
