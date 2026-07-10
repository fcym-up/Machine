# Pipecat Voice Pipeline — 设计文档

> 版本: v1.0 | 日期: 2026-07-10 | 状态: Draft

## 1. 目标

将 Machine 的语音交互从当前的"浏览器直连百度 API"方案升级为 Pipecat 流水线架构，
实现 STT → LLM(DeepSeek+Function Calling) → TTS 的完整闭环，
内嵌 Agent 集成能力和 Machine 记忆系统。

## 2. 架构

```
┌─ 浏览器 ───────────────────────────────────┐
│  AudioContext → WebSocket (PCM 16kHz)     │
│  ← TTS 音频流                             │
└─────────────────┬────────────────────────┘
                  │ WebSocket
┌─────────────────▼────────────────────────┐
│  Pipecat Pipeline                        │
│                                          │
│  输入 → [VAD] → [BaiduSTT] → [LLM] → [BaiduTTS] → 输出
│                             │
│                       AgentBridge
│                             │
│                     ┌───────▼──────┐
│                     │ Function Call│
│                     └───────┬──────┘
└─────────────────────────────┼──────────────
                              │
          ┌────────────────────┼──────────────┐
          ▼                    ▼              ▼
   MemoryService          Brain        KnowledgeService
   (记忆注入/存储)      (思考/情绪)    (实体/关系查询)
```

### 2.1 部署模式

Pipecat Pipeline 作为 Machine 后端的一部分内嵌运行，共享 FastAPI 进程。
Pipeline 在 uvicorn 启动时以 asyncio task 方式运行，不阻塞主 API。
新模块位于 app/services/voice_pipecat/ 目录下。

### 2.2 传输层

当前阶段：WebSocket（零额外基础设施，本地可用）
传输 16kHz 16bit PCM 音频帧，复用现有 WebSocket 端点思路。
后续可升级到 WebRTC（需 coturn 或 Daily 等 relay 服务）。

## 3. 组件清单

| 组件 | 角色 | 实现方式 |
|------|------|----------|
| VAD | 语音活动检测 | SileroVAD 内置在 Pipecat 中 |
| BaiduSTTService | 中文语音→文字 | 包裹现有百度 ASR 逻辑为 Pipecat Service |
| LLM 推理 | 对话生成 | OpenAILLMService + DeepSeek(base_url) |
| AgentBridge | FunctionCalling→Agent | tools 参数注入，桥接到现有的 Research/Code/Planner Agent |
| BaiduTTSService | 文字→中文语音 | 包裹现有百度 TTS 逻辑为 Pipecat Service |
| MemoryInjector | 记忆注入/存储 | Pipecat Frame Processor，流水线前置读取记忆，后置存储对话 |
| ContextBuilder | 上下文构建 | 拼接 system prompt: 情绪+活动+最近对话+用户画像 |

## 4. 数据流

### 4.1 一次对话回合

1. 用户说话 → 浏览器采集 PCM 帧 → WebSocket 发送
2. VAD 检测 → 检测到语音开始，缓存到缓冲区
3. 语音结束 → VAD 检测到静音 → 缓冲区送入 STT
4. STT 识别 → BaiduSTTService 返回文字
5. Memory 注入 → MemoryInjector 检索相关记忆，拼入 system prompt
6. Context 构建 → ContextBuilder 注入情绪+活动+最近对话
7. LLM 推理 → DeepSeek 生成回复，过程中可能调用 Function Call
8. Agent 回调 → 如果命中，AgentBridge 执行对应操作并返回结果
9. TTS 合成 → LLM 回复文字送入 BaiduTTSService → MP3 音频块
10. 音频输出 → WebSocket 发送音频帧到浏览器播放
11. Memory 存储 → 本轮对话存入 ConversationMessage 表 + 触发 Event

## 5. 记忆系统集成

### 5.1 前置注入（Pre-inject）

- 从 MemoryService 检索最近 10 轮对话
- 从 UserModelService 获取当前情绪状态和用户画像
- 从 Brain 获取当天活动摘要
- 拼接为 system prompt 前缀（复用现有 _build_instructions 逻辑）

### 5.2 后置存储（Post-store）

- 用户语音 + LLM 回复写入 ConversationMessage 表
- 触发 Event 记录（event_type: voice-interaction）
- 触发情绪信号采集（emotion_collector）

## 6. Agent 集成

LLM(DeepSeek) 注册 tools 参数，每个 tool 映射到一个 Machine Agent 或 Service：

| tool 名称 | 桥接目标 | 用途 |
|-----------|----------|------|
| search_memory | MemoryService | 查询长期记忆 |
| query_knowledge | KnowledgeService | 查知识图谱 |
| get_user_state | UserModelService | 查用户当前状态 |
| analyze_pattern | Brain | 触发综合分析 |

## 7. 文件结构

新建：

| 文件 | 职责 |
|------|------|
| app/services/voice_pipecat/__init__.py | 包标记 |
| app/services/voice_pipecat/pipeline.py | Pipecat Pipeline 构建 + 启动 |
| app/services/voice_pipecat/services/baidu_stt.py | Baidu ASR 的 Pipecat Service 封装 |
| app/services/voice_pipecat/services/baidu_tts.py | Baidu TTS 的 Pipecat Service 封装 |
| app/services/voice_pipecat/services/agent_bridge.py | Function Calling → Agent 桥接 |
| app/services/voice_pipecat/processors/memory_injector.py | 记忆注入/存储 |
| app/services/voice_pipecat/processors/context_builder.py | 构建 system prompt + 上下文 |

修改：

| 文件 | 改动 |
|------|------|
| app/api/v1/voice.py | 新增 /ws WebSocket 端点 |
| app/static/voice.js | 重写为 WebSocket 连接 Pipecat |
| app/static/index.html | 更新语音 UI 状态映射 |

## 8. 依赖

| 依赖 | 用途 |
|------|------|
| pipecat-ai | 核心流水线框架 |
| silero-vad | VAD（Pipecat 内置） |

## 9. 风险与缓解

| 风险 | 缓解方案 |
|------|----------|
| Pipecat 无内置中文 ASR/TTS Service | 注册自定义 Service 类包裹百度逻辑 |
| Baidu API 延迟波动 | Pipeline 中增加超时和重试逻辑 |
| asyncio 循环冲突 | Pipecat 在独立 task 中运行，不阻塞 FastAPI |
| Function Calling 增加 LLM 延迟 | Tool 调用设置 5s 超时，超时后降级 |
