## 实时语音交互系统 — 设计文档

版本 1.0 | 2026-07-10

### 目标

为 Project Machine Dashboard 接入实时语音对话能力。用户通过麦克风说话，经过百度 ASR 识别 → Machine 管线处理（情绪+记忆+DeepSeek LLM）→ 百度 TTS 合成 → 前端播放，实现自然的语音交互。

### 架构

```
浏览器 (mic → PCM 16kHz mono → WebSocket)
    ↕
Machine Backend (WebSocket endpoint /api/v1/voice/ws)
    ├── BaiduASRClient → wss://vop.baidu.com/realtime_asr
    ├── VoicePipeline  → app/api/v1/conversation/chat 逻辑复用
    └── BaiduTTSClient → https://tsn.baidu.com/text2audio
```

后端采用 WebSocket 代理模式：前端与后端保持一对 WebSocket，后端内部再向百度建立独立的 WebSocket（ASR）和 HTTP（TTS）连接。API Key 仅存储在后端，不暴露到前端。

### 消息协议

前端 → 后端：
| type | payload | 说明 |
|------|---------|------|
| audio | base64 编码的 PCM 字节 | 每 ~160ms 一帧 |
| interrupt | {} | 用户打断当前播放 |
| stop | {} | 结束语音会话 |

后端 → 前端：
| type | payload | 说明 |
|------|---------|------|
| status | {state: "listening"\|"thinking"\|"speaking"} | 当前状态 |
| text_partial | {text: "..."} | ASR 实时识别片段 |
| text_final | {text: "..."} | 最终识别文本 |
| reply_text | {text: "...", emotion: "..."} | Machine 文字回复 |
| audio_chunk | {data: base64, is_last: bool} | TTS 音频块 |
| error | {message: "..."} | 错误信息 |

### 文件清单

| 文件 | 作用 |
|------|------|
| app/services/voice/__init__.py | 语音服务包 |
| app/services/voice/asr_client.py | 百度实时 ASR WebSocket 客户端 |
| app/services/voice/tts_client.py | 百度 TTS HTTP 客户端 |
| app/services/voice/pipeline.py | 语音对话管线 |
| app/api/v1/voice.py | WebSocket 端点 |
| app/static/voice.js | 前端语音交互模块 |
| app/static/index.html | 修改：嵌入语音模块 |
| .env | 新增 BAIDU_API_KEY / BAIDU_SECRET_KEY |

### 各组件职责

#### BaiduASRClient
- 管理到百度 `wss://vop.baidu.com/realtime_asr` 的 WebSocket 连接
- 使用 access_token 鉴权（每 30 天刷新一次，已封装 get_access_token）
- 参数：PCM 16kHz 16bit 单声道
- 实时接收 on_recognition_result 回调，区分 partial（中间结果，unstable=true）和 final（最终结果，unstable=false）
- VAD 由百度服务端自动完成，检测静音后自动结束识别并返回 final 结果
- 异常时自动重连并上报错误

#### BaiduTTSClient
- 调用百度 `https://tsn.baidu.com/text2audio` HTTP API
- 输入：文本 + 语速(spd)/音调(pit)/音量(vol)/发音人(per)
- 输出：MP3 音频字节，流式返回（分块传回前端）
- 默认使用度逍遥（per=4）或度丫丫（per=5），语速略快(spd=6)以降低延迟感

#### VoicePipeline
- 接收 ASR final 文本
- 调用 conversation/chat 中的核心逻辑（情绪获取、活动摘要、LLM 对话），输出回复文本 + 情绪标签
- 文本 → TTSClient 合成 → 音频分块通过 WebSocket 发送
- 将语音对话写入 ConversationMessage 和 Event 表

#### VoiceWebSocket 端点
- 路径：`/api/v1/voice/ws`
- 每个连接创建一个 VoicePipeline 实例
- 消息分发：audio → ASR Client、interrupt → 停止 TTS 播放、stop → 清理
- 状态机：listening → thinking → speaking → listening（循环）

### 前端交互

- Dashboard 右侧对话面板底部新增麦克风按钮
- 点击激活 → 浏览器请求麦克风权限 → AudioContext 创建 ScriptProcessorNode 或 AudioWorklet
- 收音时按钮脉动动画，显示 "正在听..." 
- ASR 部分结果实时显示为灰色文字
- Machine 回复文字正常展示，同时播放 TTS 音频
- 用户说话自动打断当前播放（前端 AudioContext 音量检测 + interrupt 信号）

### 凭证管理

| 环境变量 | 值 |
|----------|-----|
| BAIDU_API_KEY | 百度 AI Cloud API Key |
| BAIDU_SECRET_KEY | 百度 AI Cloud Secret Key |

access_token 由 `BaiduASRClient.get_access_token()` 在每个 token 过期时自动刷新。

### 测试策略

- 单元测试：BaiduASRClient mock、BaiduTTSClient mock、VoicePipeline 逻辑
- 集成测试：WebSocket 端点生命周期、中断流程
- 手动测试：真实麦克风收音 → 识别 → 回复 → 播放完整流程

### 风险与缓解

| 风险 | 缓解 |
|------|------|
| 百度 API 延迟 1-2s | TTS 语速调快、分块播放、前端 loading 状态 |
| WebSocket 断连 | 后端自动重连、前端显示重连提示 |
| 噪声误触 VAD | 前端音量阈值预过滤 |
| token 过期 | 每次 API 调用前检查、自动刷新 |
