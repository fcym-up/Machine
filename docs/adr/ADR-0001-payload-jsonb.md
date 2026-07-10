# ADR-0001: Event payload 使用 PostgreSQL JSONB

## 状态

已采纳

## 背景

Machine 的核心数据模型是 Event。Event 需要承载任意结构的数据（网页浏览记录、
Git commit 信息、聊天消息等），不同 event_type 的数据结构差异很大。

## 决策

Event 的载荷数据使用 PostgreSQL 的 JSONB 类型存储，字段名为 payload。

## 方案对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| JSONB | 支持索引、查询、结构化存储 | PostgreSQL 专属 |
| Text (JSON 字符串) | 通用性强 | 无法数据库内查询，需应用层解析 |
| 多表继承 | 严格 schema | 表数量膨胀，变更困难 |

## 影响

- 必须在 PostgreSQL 上运行，SQLite 仅用于临时测试
- 迁移脚本需使用 sa.dialects.postgresql.JSONB
- Pydantic Schema 中 payload 定义为 dict[str, Any]
