# Phase 1 — Foundation

> 版本：v0.1.0 | 日期：2026-07-08 | 状态：✅ 已完成

## Phase Intent

搭建 Project Machine 的完整后端基础框架。交付一个可运行、可测试、可扩展的项目骨架，
包括配置系统、数据库连接、Event 数据模型、CRUD API 和自动化测试。

## Deliverables

- [x] 文档体系（ROADMAP, ADR, CHANGELOG, Phase Report）
- [x] 项目目录结构 + __init__.py
- [x] 配置系统（app/core/config.py + .env）
- [x] 日志系统（app/core/logger.py）
- [x] 数据库层（app/core/database.py）
- [x] Event 数据模型（app/models/event.py）
- [x] Pydantic Schema（app/schemas/event.py）
- [x] Repository 层（app/repositories/event_repository.py）
- [x] Service 层（app/services/event.py）
- [x] API 路由（app/api/v1/events.py）
- [x] FastAPI 入口（app/main.py）
- [x] Alembic 迁移（2f01db1168f5）
- [x] 单元测试（tests/test_event_repository.py — 6/6 passed）
- [x] 基础设施文件（docker-compose, .gitignore, README, requirements.txt）
- [x] 定时关机任务（MachineDailyShutdown, 每日 6:00 AM）

## Decisions Made

- Event payload 使用 PostgreSQL JSONB，详见 ADR-0001
- 同步 SQLAlchemy 引擎，保持简单
- loguru 替代标准 logging
- PostgreSQL 18 使用 zip 二进制包直接安装（免 admin）
- Service 层校验 event_type 和 source 白名单

## Files Created

- app/core/config.py
- app/core/logger.py
- app/core/database.py
- app/models/event.py + __init__.py
- app/schemas/event.py + __init__.py
- app/repositories/event_repository.py + __init__.py
- app/services/event.py
- app/api/v1/events.py
- app/main.py
- docker-compose.yml
- .env + .env.example
- .gitignore
- requirements.txt
- README.md
- CHANGELOG.md
- alembic.ini + alembic/env.py
- alembic/versions/2f01db1168f5_create_events_table_with_payload_jsonb.py
- tests/test_event_repository.py
- scripts/daily_shutdown.ps1

## Test Status

- 6 passing, 0 failing
- Tested on PostgreSQL machine_test database

## Issues & Blockers

- Windows Scheduled Task 创建需要管理员权限（脚本已就绪，手动运行 Register-ScheduledTask 即可）
- PostgreSQL 使用 zip 包本地运行（非 Docker），未来迁移到 Docker Compose

## Next Phase Preview

**Phase 2 — Event Engine** 将实现：
- Event 分类与标准化
- Event Pipeline 流处理
- Event 查询过滤与搜索
- Event 生命周期管理

入口条件：Phase 1 所有交付物验收通过 ✅
