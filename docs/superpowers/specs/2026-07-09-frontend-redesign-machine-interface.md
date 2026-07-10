# Machine 前端界面重设计

> 设计文档 v1.0 | 2026-07-09

## 1. 项目背景

Machine 是一个长期运行在 Windows 桌面的个人 AI 系统。它以"陪伴"和"观察"为核心，持续监控用户活动（打开的软件、浏览器标签页、文件操作、编辑器等），建立长期记忆。用户通过语音与 Machine 交流。

当前前端是一个传统 Dashboard 风格的单页应用。本次重设计的目标是将界面从一个"数据分析后台"重塑为一个有生命感的 AI 存在。

## 2. 架构与技术选型

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

### 2.2 技术选型

| 项 | 选择 | 理由 |
|---|---|---|
| 粒子核心 | Three.js | 3D 粒子球体、轨道、呼吸、状态切换效果最佳 |
| 前端框架 | 原生 JS + Three.js | 单页应用，无复杂状态流 |
| 布局 | CSS Grid + Flexbox | 三栏布局 + 底部 Dock，原生 CSS 足够 |
| 图标 | Lucide icons（线性单色） | 符合单色线性图标设计语言 |
| 语音 | Web Speech API（SpeechRecognition） | 唤醒词检测 + 连续语音识别 |
| 字体 | Inter + system-ui fallback | 免费，符合科幻极简气质 |
| 数据获取 | 定时 fetch 轮询（5-10s） | 状态/Timeline 数据，后期可切换 SSE |

## 3. 交互模型：语音唤醒 + 实时对话

### 3.1 状态机

```
[空闲] -- 检测到 "Machine" 关键词 --> [唤醒]
                                          |
                                          v
                                      [聆听]
                                          |
                              +-----------+-----------+
                              |                       |
                         用户说完（静默5秒）       仍在说话
                              |                       |
                              v                       |
                          [分析]                      |
                              |                       |
                              v                       |
                          [回答] --> 回到 [聆听]       |
                              |                       |
                              v                       |
                          [空闲] <------ 超时 5s -----+
```

### 3.2 实现方案

- 页面加载后启动 SpeechRecognition 实例（continuous: true, interimResults: true）
- 每次 onresult 事件检查识别文本中是否包含"Machine"
- 关键词命中 -> 进入对话模式，发送事件到粒子核心
- 对话模式中超过 5 秒静默 -> 超时退出
- 识别引擎约 60 秒自动断开，监听 onend 事件立即重启

## 4. 布局结构

### 4.1 Left - Status Panel

宽度约 220px，顶部对齐。

展示内容：
- 在线状态（绿色圆点 + 文字）
- 今日事件数（纯数字）
- 当前工作状态
- CPU / Memory 数值 + 细进度线

视觉约束：
- font-weight: 200-300，层级用透明度区分
- 无卡片、无圆角块、无装饰元素

### 4.2 Center - Particle Core（唯一视觉中心）

Three.js 全屏场景，四种状态：

**空闲状态：** ~1500-2000 粒子球体，缓慢自转（60s/圈），颜色 #67B8FF -> #3F89D7，三条轨道，呼吸脉动，背景星点。文字：Machine + 我一直都在。

**聆听状态：** 粒子加速（1圈/秒），球体膨胀 30%，亮度增加，声波动效。

**分析状态：** 粒子同心圆波纹扩散，文字 Analyzing...，逐条渐入感知上下文。

**回答状态：** 粒子恢复，色调微暖，显示 AI 回答。

### 4.3 Right - Event Timeline

宽度约 280px。头部 Timeline，事件行格式：时间 | 描述 | 类别标签。分隔线 opacity: 0.06。最新事件在顶部，滑入动画。

### 4.4 底部 Dock

5 个 Lunice 图标：Voice / Observation / Memory / Knowledge / Settings。20x20，间距 40px。未激活 opacity: 0.35，hover glow。

### 4.5 Machine 理解

右侧 Timeline 下方。字段：当前行为、目标、专注度、节奏、建议。纯文字排布。

## 5. 颜色系统

| 用途 | 色值 |
|------|------|
| 背景 | #05070A |
| 主体文字 | #EAF4FF |
| 强调色 | #67B8FF |
| 辅助色 | #3F89D7 |
| 状态绿 | #4ADE80 |

## 6. 动画

- 星点：CSS @keyframes 随机闪烁
- 粒子：Three.js requestAnimationFrame
- 唤醒：0.3s ease-out
- 分析结果：opacity + translate，300ms 间隔
- 回答：整句 fade-in 0.8s
- 状态切换：cross-fade 0.5s

## 7. 文件结构

```
app/static/
  index.html
  css/style.css, animations.css
  js/app.js, particle-core.js, voice.js, timeline.js
  assets/icons.js
```

## 8. API 依赖

- POST /api/v1/conversation/chat
- GET /api/v1/conversation/emotion
- GET /api/v1/conversation/think
- GET /api/v1/events/search?limit=30

## 9. 本次范围

- 三栏布局 + Dock
- Three.js 粒子核心（四状态）
- 语音唤醒 + 5 秒超时退出
- Event Timeline 实时轮询
- Machine 理解面板
- AI 对话完整链路
