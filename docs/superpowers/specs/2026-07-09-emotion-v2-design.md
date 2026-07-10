# Emotion Perception v2 — Multi-Signal Weighted Model

> 版本: v2.0 | 日期: 2026-07-09 | 状态: Design Approved

---

## 1. 目标

将情绪感知从「被动调用、单信号源」升级为「主动计算、多信号源加权」的持久化模型。

**核心变化：**
- 从 on-demand 变为 定时(5min) + 高权重信号即时触发
- 从单一窗口活动类别变为 5 个信号源加权融合
- 对话中的情绪表达不再只读取情绪，而是**作为最高权重信号源输入**
- 情绪状态持久化到数据库，支持历史趋势追溯

---

## 2. 信号源与权重

| 信号源 | 权重 | 检测方式 | 更新策略 |
|--------|------|----------|----------|
| 对话诉说 | 0.35 | LLM 情感共分类（聊天时附带输出） | 实时（每条消息） |
| 音乐类型 | 0.25 | process_classifier + MusicModule | 事件驱动 |
| 窗口活动 | 0.20 | process_classifier + WindowModule | 定时 5min |
| 空闲模式 | 0.10 | IdleModule（away/back 状态） | 定时 5min |
| 时间上下文 | 0.10 | 小时区间映射 | 定时 5min |

> 所有权重存储在 `emotion_signal_weights` 表中，可通过 API 动态调整。

### 2.1 LLM 情感共分类

聊天时在已有的 LLM 请求中附带情绪分类指令，不增加额外延迟：

```
System prompt 追加：
"同时分析用户情绪，仅返回标签之一：[焦虑, 开心, 疲惫, 专注, 放松, 平静, 沮丧, 好奇]"
```

LLM 返回格式：
```json
{"reply": "...", "emotion": "焦虑", "emotion_confidence": 0.85}
```

回退：LLM 不可用时，用关键词匹配 `["焦虑","开心","累了","疲惫","烦","兴奋","难过","无聊","压力"]`

### 2.2 音乐信号映射

```
rock/metal → 焦虑/压力
ambient/classical → 放松
electronic/upbeat → 专注
pop/indie → 平静
lofi/jazz → 专注/放松
```

基于 MusicModule 的窗口标题解析 `艺术家 - 歌曲名` + process_classifier 识别音乐播放器。

---

## 3. 数据库设计

### 3.1 emotion_signals（原始信号）

```sql
CREATE TABLE emotion_signals (
    id SERIAL PRIMARY KEY,
    source VARCHAR(32),          -- conversation / music / window / idle / time
    emotion_label VARCHAR(16),   -- 焦虑 / 开心 / 专注 / ...
    weight NUMERIC(3,2),         -- 该信号的权重
    confidence NUMERIC(3,2),     -- 信号自身的置信度 0-1
    payload JSONB,               -- 来源详情
    event_id INTEGER REFERENCES events(id),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### 3.2 emotion_states（计算后的情绪快照）

```sql
CREATE TABLE emotion_states (
    id SERIAL PRIMARY KEY,
    primary_emotion VARCHAR(16),
    secondary_emotion VARCHAR(16),
    intensity NUMERIC(3,2),
    confidence NUMERIC(3,2),
    scores JSONB,                -- {"焦虑": 0.45, "专注": 0.30, ...}
    factors TEXT[],              -- 触发因素列表
    signal_count INTEGER,        -- 参与计算的信号数
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### 3.3 emotion_signal_weights（可配置权重）

```sql
CREATE TABLE emotion_signal_weights (
    id SERIAL PRIMARY KEY,
    source VARCHAR(32) UNIQUE,   -- conversation / music / window / idle / time
    weight NUMERIC(3,2),
    enabled BOOLEAN DEFAULT true,
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 4. 架构

```
                  ┌──────────────────────────┐
                  │     SignalCollector       │
                  │  (各信号源采集器)           │
                  └─────┬──────────┬─────────┘
           ┌────────────┘          └──────────────┐
           ▼                                      ▼
   ┌──────────────┐                      ┌───────────────┐
   │ 实时触发:      │                      │ 定时触发:       │
   │ 对话消息       │                      │ Scheduler      │
   │ (每条消息后)   │                      │ (每5分钟)       │
   └──────┬───────┘                      └───────┬───────┘
          │                                      │
          └──────────────┬───────────────────────┘
                         ▼
               ┌──────────────────┐
               │  EmotionComputer │
               │  加权计算+时间衰减  │
               └────────┬─────────┘
                        ▼
               ┌──────────────────┐
               │  emotion_states  │  ← 持久化
               └────────┬─────────┘
                        ▼
          ┌─────────────┴──────────────┐
          ▼                            ▼
   Dashboard 情绪卡片           对话 API (/emotion, /chat)
```

---

## 5. 计算逻辑

### 5.1 滑动窗口

- 默认窗口：最近 1 小时
- 每个信号按 `weight × confidence × time_decay` 累计到对应情绪标签的分数

### 5.2 时间衰减

```
decay = max(0, 1.0 - (now - signal.created_at) / window_seconds)
```

信号越旧，权重越低。超过窗口的信号不参与计算。

### 5.3 最终输出

取最高分的情绪作为 `primary_emotion`，次高的作为 `secondary_emotion`。同时保存完整的 `scores` 分布。

---

## 6. 文件变更

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/models/event.py` | 修改 | 添加 emotion_signal / emotion_state 模型 |
| `app/algorithms/emotion_engine.py` | 重写 | 改为加权多信号模型 |
| `app/services/emotion_collector.py` | 新增 | 信号采集器 |
| `app/services/emotion_computer.py` | 新增 | 加权计算引擎 |
| `app/api/v1/conversation.py` | 修改 | LLM 共分类 + 信号注入 |
| `app/api/v1/emotion.py` | 新增 | 情绪 API（历史趋势、权重配置） |
| `app/static/index.html` | 修改 | Dashboard 情绪卡片改为读 emotion_states |
| `app/core/scheduler.py` | 修改 | 添加 5 分钟定时任务 |
| `alembic/versions/` | 新增 | 两张新表的迁移 |

---

## 7. 自审

- 无 TBD/TODO 占位
- 架构图与功能描述一致
- 信号源权重总和 = 1.0
- LLM 共分类方案不引入额外延迟
- 关键词回退保证 LLM 不可用时系统不降级
- 权重可通过数据库动态调整，无需重启
