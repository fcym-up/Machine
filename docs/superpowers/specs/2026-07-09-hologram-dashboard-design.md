# Machine 全息投影 Dashboard 设计文档

## 一、设计概述

### 设计读
**Reading this as**: 个人 AI 系统监控面板（全息投影风格），面向技术用户日常使用，JARVIS / 疑犯追踪 Machine 风格，暗色科技视觉语言。

### 三档设置
| 档位 | 值 | 说明 |
|------|-----|------|
| DESIGN_VARIANCE | 8 | 不对称布局，全息元素穿插，有科技感的不规则感 |
| MOTION_INTENSITY | 8 | 扫描线动画、数据流、脉冲发光、淡入过渡 |
| VISUAL_DENSITY | 6 | 信息密度中等偏密，数据面板风格 |

## 二、技术架构

### 独立前端系统
- **形式**: 单页 HTML 文件（\index.html\）
- **无构建工具**: 纯原生 HTML + CSS + JS
- **无框架依赖**: 直接使用 Web API
- **后端通信**: 通过 REST API 调用（\/api/v1/*\）
- **语音接口**: 浏览器 Web Speech API
- **服务方式**: FastAPI 静态文件挂载在 /dashboard 路径

### 与后端解耦
- 前端完全独立，仅通过 API Key 认证的 REST 调用与后端交互
- 每个 API 调用都有独立 try/catch 保护
- 聊天接口故障不影响其他面板数据显示

## 三、视觉设计

### 色彩系统
- 深空底色: #080a1a
- 半透明面板: rgba(10, 15, 30, 0.6)
- 电光蓝主色: #00d4ff
- 亮青辅助色: #4af0ff
- 琥珀色警告: #ffb347
- 红色危险: #ff4757

### 动效系统
1. **面板呼吸发光** - 边框发光强度 2s 周期缓动
2. **扫描线动画** - 全屏半透明扫描线从顶部到底部循环
3. **数据流粒子** - 面板边缘的流动光点
4. **脉冲波纹** - 情绪状态变化时产生扩散波纹
5. **数字滚动** - 数值变化时数字滚动更新
6. **打字机效果** - Machine 回复时逐字出现
7. **语音波纹** - 麦克风激活时频谱波纹动画

### 布局结构
- 顶栏: Machine Logo + 状态指示器 + 刷新按钮
- 中栏左: 情绪状态面板 + 今日概览面板
- 中栏中: 活动分布面板
- 中栏右: Machine 会话面板（核心交互区域）
- 下栏左: 时间线
- 下栏右: Echo 思考面板
- 底栏: 系统状态信息

## 四、功能模块

### 4.1 情绪状态面板
- 显示主情绪 + 副情绪
- 情绪图标动态展示
- 置信度环形进度条
- 强度指示条
- 影响因素列表
- 实时刷新（每 20s）
- 情绪变化时触发脉冲动画

### 4.2 活动分布面板
- 横向柱状图，渐变填充
- 活动类别名称 + 次数 + 百分比
- 柱子动画（从底部升起）
- 数据来源: /api/v1/profile/full?days=1

### 4.3 Machine 会话面板（核心）
- 消息历史展示区域
- 打字机效果回复
- **语音输入**: Web Speech API 录音
- **语音输出**: TTS 朗读回复
- 调用 /api/v1/conversation/chat

### 4.4 今日概览
- 今日事件总数
- 简要摘要
- 数据来源: /api/v1/profile/digest

### 4.5 时间线
- 最近事件列表
- 数据来源: /api/v1/events/timeline?limit=50

### 4.6 Echo 思考
- Machine 自动反思
- 数据来源: /api/v1/conversation/think?hours=24

### 4.7 系统状态
- 顶栏状态指示器
- 最后刷新时间
- 底栏系统版本和状态

## 五、API 接口清单

| 端点 | 用途 | 刷新间隔 |
|------|------|---------|
| GET /api/v1/emotion/current | 获取当前情绪 | 20s |
| GET /api/v1/profile/full?days=1 | 活动分布 | 60s |
| POST /api/v1/conversation/chat | 发送消息 | 按需 |
| GET /api/v1/profile/digest | 今日概览 | 60s |
| GET /api/v1/events/timeline?limit=50 | 时间线 | 60s |
| GET /api/v1/conversation/think?hours=24 | 思考分析 | 120s |

## 六、语音功能细节

### 语音输入（SpeechRecognition）
- 浏览器原生 API
- 中文语音识别（lang: zh-CN）
- 连续识别模式（continuous: false）
- 识别中间结果（interimResults: true）
- 静音自动结束（5s）

### 语音输出（SpeechSynthesis）
- 浏览器原生 API
- 中文语音
- 可调节语速（rate: 1.0）
- 可开关（默认开启）

## 七、实现文件

单个文件：\D:\workplace\app\static\index.html
替换现有文件，通过 FastAPI 静态文件挂载在 http://127.0.0.1:8000/dashboard/ 访问。
