# P0/P1 稳定性修复 — 设计文档

> Project Machine v0.5.1 | 2026-07-09

## 概览

修复 5 个已知问题，分三个独立改动区域。

| # | 级别 | 问题 | 改动区域 |
|---|------|------|---------|
| 1 | P0 | 采集器随 python 进程被杀 | 采集器 v5 |
| 2 | P0 | 采集器启动时抓到自己窗口 | 采集器 v5 |
| 3 | P1 | Edge/微信中文标题乱码 | 采集器 v5 |
| 4 | P1 | entities 抽取太慢（3s/条） | 实体抽取管线 |
| 5 | P1 | 多轮对话记忆不稳定 | 对话持久化 |

---

## 区域 A：采集器 v5

**文件：** `scripts/collector_v5.ps1`（新建，取代 v4）

### P0 #1 — 独立化管理
- 不再裸跑，通过 Windows 计划任务注册
- 脚本自身增加 `Register-ScheduledTask` 辅助函数，一键注册

### P0 #2 — 防自抓
- 启动时获取 `$PID`，在窗口检测循环中永久过滤该 PID 对应窗口
- 保留原有 `Start-Sleep 3` 启动缓冲

### P1 #3 — 中文乱码
- `GetWindowText`（ANSI）→ `GetWindowTextW`（Unicode）
- P/Invoke 声明改为 `CharSet=Unicode`

---

## 区域 B：实体抽取加速

**文件：** `app/services/llm_entity_extractor.py`

**方案：混合流水线**

```
事件到达 → 正则抽取（<1ms）→ 立即返回
                       → push 内存队列
                            ↓
               调度器每 30s 消费队列
                            ↓
               DeepSeek 批量抽取 → 合并写回
```

**改动：**
- `extract()` 新增 `async_enrich: bool = True` 参数
- 新增 `_enqueue_for_enrichment(event_id, text, regex_entities)` 入队方法
- 新增 `_batch_enrich()` 批量 LLM 抽取方法
- 调度器注册 `enrich_entities` 定时任务（30s 间隔）

---

## 区域 C：对话持久化

**文件：** `app/models/conversation.py`（新建）、`app/api/v1/conversation.py`（修改）

### 新建表 `conversation_messages`
| 列 | 类型 | 说明 |
|---|---|---|
| id | UUID PK | 主键 |
| session_id | VARCHAR(64) | 会话标识 |
| role | VARCHAR(16) | user/assistant/system |
| content | TEXT | 消息内容 |
| created_at | TIMESTAMPTZ | 时间戳 |

### 行为变更
- `add_to_history()` → DB 写入 + 内存缓存更新
- `get_history()` → 内存优先，miss 查 DB（最近 20 轮）
- 每会话最多 100 条，超出自动删旧
- 服务重启不丢历史

### 系统提示词精简
- system role 改为固定人格模板
- 动态上下文（情绪、活动摘要）移到 user 消息 prefix

---

## 测试

| 区域 | 测试文件 | 覆盖 |
|------|---------|------|
| A | `tests/test_collector.py`（可选） | P/Invoke 声明验证 |
| B | `tests/test_llm_extractor.py`（可选） | 正则路径同步返回 + 入队 |
| C | `tests/test_conversation_memory.py`（已有） | 更新以覆盖 DB 持久化 |

---

## 风险

- P0 #1 计划任务注册需要管理员权限，若不可用则提供手动注册说明
- entities 异步管线引入内存队列，服务重启丢失未处理队列（可接受，丢失率 < 30s）

*** End of File
