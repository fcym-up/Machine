# Project Machine

> **受《疑犯追踪》"The Machine" 启发的个人 AI 系统**
>
> v0.5.0 | Python 3.13 | FastAPI | PostgreSQL | SenseVoice | Kokoro TTS

---

## 项目概述

Project Machine 是一个长期运行的 AI 陪伴平台。它不是一个语音助手，而是构建一个能持续观察、理解、记忆用户行为的智能系统。

核心理念：1.所有行为都是有目的性的
         2.世界上所有变化都是 Event——浏览网页、切换窗口、离开键盘、语音交流，都被抽象为 Event，经过分析管道转化为知识、记忆和决策依据。

---

## 系统架构

```
现实世界 -> 数据采集层 -> Event Engine -> Memory System
                                    -> Knowledge System
                                    -> Intelligence Engine
                                    -> Prediction Engine
                                    -> Agent System
                                    -> Voice Interface
                               User (Dashboard + Voice)
```

## 核心模块

### Event Engine
统一事件模型 `{id, event_type, source, payload, created_at}`，支持自动分类和规范化。

### Memory System
四层记忆：Working -> Short -> Long -> Semantic。每小时/每天/每周自动固化合并，带衰减率和重要性评分。

### Knowledge System
Entity 实体 + Relationship 关系构建知识图谱，支持 LLM 辅助实体抽取。

### Intelligence Engine
模式识别、风险评分、趋势分析、Z-score/IQR 异常检测。

### Emotion Engine
从活动模式 + 时间节律 + 夜间比例 + 社交/工作比等多个维度推理用户情绪状态。

### Brain（中央大脑）
整合所有算法引擎，生成综合洞察。支持 LLM 深度思考模式。

### Agent System（代理系统）
5 个专用 Agent：Research、Code、Memory、Planner、Security，每个支持 LLM + 规则回退双模式。

### Voice System（语音系统）
- **STT**: SenseVoice（阿里，本地 GPU，3.5GB）
- **VAD**: Silero VAD（语音活动检测）
- **LLM**: DeepSeek API（异步流式，逐句输出）
- **TTS**: Kokoro TTS（本地 GPU，312MB）+ Edge TTS 降级
- **上下文**: 获取 Machine Brain 实时状态（情绪/记忆/实体/节律）
- **回写**: 语音 Event 写入系统，构建长期对话记忆

### Active Care（主动关心）
检测焦虑、游戏过度、深夜工作、社交隔离，主动问候。

### Collector（数据采集器）
Win32 API 采集窗口标题/进程名/停留时长、键盘空闲状态、音乐播放信息。

### Dashboard（监控界面）
Person-of-Interest 风格 Web UI，Three.js 粒子核心，实时状态面板。

---

## 开发路线图

| Phase | 名称 | 状态 |
|-------|------|:--:|
| Phase 0 | 环境建设 | Done |
| Phase 1 | Foundation（基础 API + 数据库） | Done |
| Phase 2 | Event Engine（事件引擎） | Done |
| Phase 3 | Memory System（记忆系统） | Done |
| Phase 4 | Knowledge System（知识系统） | Done |
| Phase 5 | Intelligence System（智能分析） | Done |
| Phase 6 | Voice System（语音系统重设计） | Done |
| Phase 7 | Agent System（代理系统联调） | TODO |

---

## 待完成事项

### 高优先级
- [ ] **Agent System 联调**：5 个 Agent 已编码但未经完整功能测试，缺少 LLM 上下文注入
- [ ] **WebSocket 稳定性**：Dashboard 语音面板的 WebSocket 连接存在 CLOSE_WAIT 泄漏问题
- [ ] **onnxruntime DLL 修复**：FunASR 依赖链缺少 onnxruntime DLL，需添加 PATH 环境变量
- [ ] **Kokoro TTS 模型下载**：首次使用需下载约 312MB 模型

### 中优先级
- [ ] **UserModel trait_name 字段**：PostgreSQL 表缺少 trait_name 列，导致定时任务报错
- [ ] **API 认证升级**：当前使用静态 API Key，计划升级为 JWT 认证
- [ ] **Prediction Engine**：异常检测已实现，但趋势预测和时间序列分析待完善
- [ ] **前端离线包**：Dashboard 依赖 Three.js CDN + Google Fonts，无网络时无法渲染

### 低优先级
- [ ] **Redis 集成**：docker-compose 已预留但未实现
- [ ] **Neo4j 知识图谱**：当前用 PostgreSQL 关系表模拟
- [ ] **移动端适配**：Dashboard 仅适配桌面端
- [ ] **多语言支持**：目前仅支持中文

---

## 部署指南

### 环境要求

- **Python** 3.11+
- **PostgreSQL** 18（运行中）
- **Windows** 10/11（Collector 依赖 Win32 API）
- **GPU**（推荐，用于 SenseVoice STT + Kokoro TTS）

### 1. 克隆项目

```bash
git clone https://github.com/fcym-up/Machine.git
cd Machine
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
copy .env.example .env
```

编辑 `.env`，填写必要配置：

```
POSTGRES_USER=machine_user
POSTGRES_PASSWORD=machine_pass
POSTGRES_DB=machine
MACHINE_API_KEY=your-secret-api-key
LLM_API_KEY=sk-your-deepseek-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

### 5. 启动 PostgreSQL

确保 PostgreSQL 服务在运行。默认连接 `localhost:5432`。

### 6. 下载语音模型

首次启动会自动下载模型，也可手动预热：

```python
# SenseVoice STT (约 1.8GB, 下载到 D:\modelscope_cache)
from funasr import AutoModel
AutoModel(model="iic/SenseVoiceSmall")

# Kokoro TTS (约 312MB)
from kokoro import KPipeline
KPipeline(lang_code="z")
```

GPU 内存占用估算：
- SenseVoice ~3.5GB VRAM
- Silero VAD ~100MB VRAM
- Kokoro TTS ~1GB VRAM
- 合计约 4.6GB，推荐 6GB+ 显存

### 7. 启动服务

一键启动：

```bash
start_services.bat
```

或手动分别启动：

```bash
# 终端 1：Web 服务
uvicorn app.main:app --host 127.0.0.1 --port 8080

# 终端 2：Collector（屏幕监控）
python collector/main.py
```

### 8. 访问

- **Dashboard**: http://127.0.0.1:8080/dashboard/
- **API 文档**: http://127.0.0.1:8080/docs
- **Web 根**: http://127.0.0.1:8080/

### 9. 停止服务

```bash
stop_services.bat
```

---

## 项目结构

```
Machine/
├── app/                    # FastAPI 后端
│   ├── api/v1/             # REST API 路由
│   ├── core/               # config/database/LLM/security/scheduler
│   ├── models/             # Event/Memory/Entity/Relationship/Emotion
│   ├── repositories/       # 数据访问层
│   ├── schemas/            # Pydantic 请求/响应模型
│   ├── services/           # 业务逻辑层
│   │   └── voice/          # 语音系统（STT/VAD/TTS/pipeline）
│   ├── algorithms/         # ML 算法（情绪/异常/学习/节律）
│   ├── agents/             # 5 个智能代理
│   └── static/             # Dashboard 前端
├── collector/              # 本机数据采集器
│   ├── core/               # Engine/Queue/Sender
│   └── modules/            # Window/Idle/Music 模块
├── tests/                  # 单元测试
├── docs/                   # 设计文档/ADR/Phase 报告
├── data/                   # 运行时数据（Brain 状态）
├── alembic/                # 数据库迁移
├── start_services.bat      # 一键启动
├── stop_services.bat       # 一键停止
└── requirements.txt
```

---

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Python 3.13, FastAPI, SQLAlchemy, Pydantic |
| 数据库 | PostgreSQL 18 |
| AI | DeepSeek API (LLM), FunASR SenseVoice (STT), Silero VAD, Kokoro TTS |
| ML | NumPy, Scipy, 自定义算法 |
| 调度 | APScheduler |
| 前端 | Three.js, 原生 JS |
| 采集 | Win32 API (ctypes) |


