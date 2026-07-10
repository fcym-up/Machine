# Machine 前端界面重设计 v2.0

> 设计文档 v2.0 | 2026-07-09

## 1. 项目背景

基于上一版前端改造的实践反馈和两份设计文档（Machine UI Design Specification v2.0、Machine Design Bible v1.0），对 Machine 前端进行第二次迭代。

核心变化：从"展示数据"转向"表达理解"，从"系统监控面板"转向"AI 陪伴界面"。

## 2. 架构策略

采用渐进迭代方式（路径 B）：保留现有 Three.js 粒子系统和文件结构，通过替换内容、调整布局、增加状态来达到新设计文档的要求。语音管线（ASR/TTS）留到后续阶段。

### 2.1 整体架构

```
用户 -> Electron 窗口（将来）
         |
    app/static/index.html
         |
    fetch / WebSocket -> FastAPI /api/v1/*（Python）
         |
    PostgreSQL
```

### 2.2 技术选型（不变）

| 项 | 选择 |
|---|---|
| AI Core 渲染 | Three.js（现有粒子系统保留 + Core Light 新增）|
| 前端框架 | 原生 JS + Three.js |
| 布局 | CSS Grid + Flexbox（三栏）|
| 图标 | Lucide icons（线性单色，6 项）|
| 语音输入 | Web Speech API（唤醒词，不变）|
| 字体 | Inter + Segoe UI Variable + HarmonyOS Sans |
| 数据获取 | 定时 fetch 轮询（8-10s）|

## 3. 交互模型

### 3.1 状态机

```
[Idle] -- 检测到 "Machine" 关键词 --> [Listening]
                                          |
                                          v
                                      [Thinking]  -- 分析中
                                          |
                                          v
                                      [Speaking] -- 回答
                                          |
                              +-----------+-----------+
                              |                       |
                         用户继续说话              静默5秒
                              |                       |
                              v                       |
                          [Listening]             [Idle]
                              |
                          [Sleeping] (5min无活动)
```

### 3.2 5 状态对照

| 状态 | 前端常量 | 用途 |
|------|---------|------|
| Idle | `state = 'idle'` | 默认待机 |
| Listening | `state = 'listening'` | 检测到唤醒词后 |
| Thinking | `state = 'thinking'` | 发送到 API 等待回复（原 analyzing）|
| Speaking | `state = 'speaking'` | 显示 AI 回答（原 answering）|
| Sleeping | `state = 'sleeping'` | 长时间无活动后 |

### 3.3 语音交互

- 唤醒词：说 "Machine"
- 快捷键（未来支持）：长按 Space、Alt+Space
- 5 秒静默超时自动回到 Idle
- 5 分钟无活动自动进入 Sleeping（可选，暂不实现）

## 4. 布局结构

```
+----------------------------------------------------------+
| +---------+  +-------------------------+  +--------------+ |
| | Status   |  |     AI Core             |  | Machine      | |
| | Panel    |  |   (Three.js + Overlay)  |  | Thoughts     | |
| | 260px    |  |     ~65% width          |  | 280px        | |
| |          |  |                         |  |              | |
| | . Online |  |     Machine             |  | 我注意到      | |
| |          |  |    我一直都在。           |  | 今天开发了    | |
| | Observe  |  |   说 "Machine"          |  | 2h30m        | |
| |   Coding |  |                         |  |              | |
| |    High  |  |   [AI Core Three.js]    |  | 最近频繁查看  | |
| |  3.5h    |  |   Core Light + 粒子     |  | FastAPI      | |
| |          |  |   5 状态动画             |  | PostgreSQL   | |
| | Voice    |  |                         |  |              | |
| |   唤醒词  |  |  Listening/Thinking/   |  | 建议：        | |
| |          |  |  Speaking/Sleeping      |  | 休息         | |
| +---------+  +-------------------------+  +--------------+ |
|                                                           |
| +------------------------------------------------------+ |
| |  Voice | Observe | Memory | Knowledge | Tasks | Set   | |
| +------------------------------------------------------+ |
+----------------------------------------------------------+
```

### 4.1 Left - Observe Status Panel

宽度 260px，顶部对齐。

内容（从上到下）：
- 在线状态（绿色圆点 + 文字 "Online"）
- **Observe 区域**（从 think 端点获取）：
  - 当前行为（如 Coding、Reading）
  - 专注度（High / Medium / Low）
  - 今日已专注时长（推算）
  - 当前阶段（如"开发中"）
- **Voice Status 区域**：
  - "🎤 唤醒词模式"
  - "说 "Machine""

视觉约束：
- 字段名 opacity: 0.35，值 opacity: 0.8
- 无卡片、无边框、无大图标
- gap 14px，字号 12px
- 不展示 CPU、Memory、FPS、Latency、事件数

### 4.2 Center - AI Consciousness

Three.js 场景，5 种状态动画：

**Idle：**
- 现有粒子球缓慢旋转 + 呼吸（±3%）
- Core Light（新增）：中心半球形光晕，#67B8FF，opacity 0.15
- 三条轨道缓慢移动
- 文字："Machine" + "我一直都在。" + "说 "Machine""

**Listening：**
- 粒子向中心聚集 + 膨胀 20%
- 中心 Core Light 亮起至 opacity 0.6
- 轨道加速
- 文字："我在听。"

**Thinking：**
- 内部流线效果，粒子快速流动
- Core Light 脉冲（0.3-0.7）
- 外围轨道重新排列
- 文字："思考中..."

**Speaking：**
- 中心向外扩散波纹效果
- Core Light 稳定发光 0.5
- 轨道正常移动
- 文字：AI 回答（淡入）

**Sleeping：**
- 亮度下降 60%
- 粒子运动几乎停止
- Core Light 最暗 opacity 0.05
- 轨道停止
- 文字："休息中..."

### 4.3 Right - Machine Thoughts

不是 Timeline。展示 Machine 对用户的理解。

数据来自 `GET /api/v1/conversation/think` 返回的 `thoughts` 数组、`activity_distribution`、`main_activity`、`events_analyzed`。

渲染格式（纯文字区块，无时间戳）：
- 头部："Machine 的思考"（11px uppercase）
- AI 生成的 2-3 句理解文本
- Top 3 活动类别（从 distribution 提取）
- 一句话建议

轮询频率：10 秒

### 4.4 底部 Dock

6 项线性图标，居中分布：Voice / Observe / Memory / Knowledge / Tasks / Settings

- Lucide 图标 20×20，间距 40px
- 未激活 opacity: 0.35，hover glow
- 激活态底部 2px 圆点 #67B8FF
- 本版只实现 Voice 页面，其他为占位

### 4.5 Voice Status 指示

左栏底部展示语音状态：
- 待机："🎤 唤醒词模式 / 说 "Machine""
- 对话中："🎤 对话中..."
- 麦克风不可用："🎤 麦克风不可用"

## 5. 颜色系统

| 用途 | 色值 |
|------|------|
| 背景 | #05070A → linear-gradient(#05070A, #0A0E17) |
| 主体文字 | #EAF4FF |
| 强调色 | #67B8FF |
| 辅助色 | #3F89D7 |
| 成功色 | #4ADE80 |
| 警告色 | #FFC857 |
| 错误色 | #FF5D73 |

## 6. 动画

### 6.1 背景层

- 渐变：CSS linear-gradient(135deg, #05070A, #0A0E17, #05070A)
- 星点：CSS @keyframes 极慢漂移，周期 30s+

### 6.2 AI Core 层

| 状态 | 粒子 | Core Light | 轨道 |
|------|------|-----------|------|
| idle | 呼吸 ±3%，0.1x 速 | opacity 0.15 | 慢速 |
| listening | 向心 + 膨胀 20%，0.5x 速 | opacity 0.6 | 加速 |
| thinking | 流线 + 快速流动 1.0x 速 | 脉冲 0.3-0.7 | 重排 |
| speaking | 波纹扩散 0.3x 速 | opacity 0.5 | 正常 |
| sleeping | 几乎静止 0.02x 速 | opacity 0.05 | 停止 |

### 6.3 交互层

- 唤醒：粒子 0.3s ease-out 加速，Core Light 渐亮
- 状态切换：所有粒子参数使用 lerp 缓动（不是硬切换）
- 回答：整句 fade-in 0.8s
- Machine Thoughts 更新：内容 fade-in 过渡

## 7. 文件变更清单

| 文件 | 操作 |
|------|------|
| `index.html` | 左栏替换、右栏结构调整 |
| `css/style.css` | 新增字段样式、配色补充、Dock 6 项 |
| `css/animations.css` | 新增 Sleeping/星点动画 |
| `js/particle-core.js` | 5 状态 + Core Light + Speaking/Sleeping |
| `js/app.js` | 5 状态映射 + 左栏数据 |
| `js/timeline.js` | 改为 Machine Thoughts |
| `assets/icons.js` | 新增 Tasks 图标 |

## 8. API 依赖（不变）

| 端点 | 用途 |
|------|------|
| POST /api/v1/conversation/chat | AI 对话 |
| GET /api/v1/conversation/think | 获取 Machine Thoughts 数据 |
| GET /api/v1/events/search?limit=30 | （保留备用）|

## 9. 非本次范围

- 后端 ASR/TTS 语音管线
- Dock 其他 5 页面的展开视图
- Electron 桌面应用打包
- Sleeping 自动切换（5min idle）
- Dream Mode 夜间整理
- Context-aware 自适应行为模式（Coding/Reading/Gaming 等）
