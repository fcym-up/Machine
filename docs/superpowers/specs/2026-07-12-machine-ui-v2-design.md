# Machine UI v2 — 三层沉浸式界面设计

## 设计目标
将当前仪表盘升级为更接近《疑犯追踪》The Machine 形象的沉浸式界面：核心态（观察者）→ 监控态（分析师）→ 操作态（交互者）三层结构，平滑过渡。

## Design Read
Reading this as: dark-tech AI-system cockpit for a single power user, with a cinematic POI / The Machine language, leaning toward Three.js 3D neural core + floating data overlay + glass-morphism panels.

## Three Dials
- DESIGN_VARIANCE: 8 — artsy but structured, neural networks + floating elements
- MOTION_INTENSITY: 7 — breathing core, scanning rings, flowing data tickers
- VISUAL_DENSITY: 4 — airy core view, denser monitor view

## 架构概览

```
                  ┌─────────────────────────────┐
                  │       Layer 1: CORE VIEW     │
                  │   (默认态, 全屏沉浸)          │
                  │   ┌─────────────────────┐    │
                  │   │  3D Neural Core     │    │
                  │   │  + floating info     │    │
                  │   │  + thought ticker    │    │
                  │   └────────┬────────────┘    │
                  └───────────┬─────────────────┘
                              │ click / key
                              ▼
┌─────────────────────────────────────────────────┐
│         Layer 2: MONITOR VIEW                   │
│  ┌──────────┬──────────────────┬──────────────┐ │
│  │ Status   │  View Container  │ Thought      │ │
│  │ Panel    │ (Obs/Mem/Kno     │ Stream       │ │
│  │ 190px    │  Tasks/Settings) │ 280px        │ │
│  └──────────┴──────────────────┴──────────────┘ │
└─────────────────────────────────────────────────┘
                              │ click / command
                              ▼
                  ┌─────────────────────────────┐
                  │  Layer 3: ACTION VIEW        │
                  │  (Fullscreen Terminal /      │
                  │   Graph / Dialog)            │
                  └─────────────────────────────┘
```

## 第一层：核心态

### 3D 神经网络核心
- 粒子数: 4000-5000 (当前 2000)
- 三层粒子壳: inner shell (密集, r=2.0-2.5), mid shell (r=2.5-3.5), outer shell (稀疏, r=3.5-4.5)
- 内核发光: 叠加 3 层光晕 (coreLight, coreAura, coreBloom)
- 状态动画:
  - idle: 缓慢呼吸, 旋转速度 0.08
  - listening: 扩大到 1.3x, 粒子波动, 旋转加速
  - thinking: 涡旋形态, 粒子沿螺旋线运动, 快速旋转
  - speaking: 径向脉冲波, 从核心向外扩散
  - alert: 琥珀色脉冲闪烁, 部分粒子变琥珀色
- 神经网络连线: 500 条, 每帧动态重算最近邻
- 3 层扫描环: 不同半径/速度/方向旋转

### 2D CSS Fallback
- WebGL 不可用时: 纯 CSS 同心圆 + 粒子点阵动画
- 保持相同状态颜色体系
- 线性渐变放射状背景模拟 3D 效果

### 浮动信息层
- 左上: Machine 标识 (纤细 mono, opacity 0.4)
- 左下: 事件 ticker (最近 5 条事件水平滚动)
- 右下: 用户状态标签 (情绪/精力 小标签)
- 思维文本: 从 /conversation/think 获取, 打字机效果淡入

### 交互
- 点击核心 → 进入监控态
- ESC → 回到核心态
- 双击核心 → 触发 "analyzing" 状态 3 秒

## 第二层：监控态

### 布局调整
- 左面板 190px: 精简为纯状态 + 警报
- 中央 flex: 保留现有视图切换逻辑, 卡片设计升级
- 右面板 280px: 重做为思维流 (thought stream), 垂直滚动
- 核心缩小到左上角 40x40 作为常驻标识, 点击返回

### 右面板重做
- 标题: "Machine 的思考" 保持
- 内容: 垂直排列的 thought blocks, 有时戳
- 底部: 简短的输入框, 可以直接对 Machine 说话
- 活动标签和 suggestion 保持

## 第三层：操作态

### 全屏对话
- 终端风格对话界面
- 打字机输出
- 语音波形提示

### 全屏图谱
- D3 图谱展开到全屏
- 搜索/过滤/聚焦功能

## 实现顺序

1. CSS 核心态 + 监控态样式 (style.css)
2. HTML 结构调整 (index.html)
3. particle-core.js 升级 + CSS fallback
4. app.js 核心态逻辑 + 思维流 + 层切换
5. 验证与调整
