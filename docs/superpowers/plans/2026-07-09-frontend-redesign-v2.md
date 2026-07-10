# Machine 前端界面重设计 v2.0 — 实施计划

> **For agentic workers:** Use subagent-driven-development or executing-plans to implement.

**Goal:** 将 Machine 前端从数据展示型界面改造为 AI 陪伴型界面，替换左/中/右三栏内容，新增 AI Consciousness 5 状态系统，配色和背景升级。

**Architecture:** 渐进迭代。保留 Three.js、文件结构、API 层。内容替换为主，不改基础框架。

**Tech Stack:** HTML5, CSS3, Three.js (CDN), Web Speech API, Lucide Icons

---

## Task 1: Left Panel — Observe Status Panel

**Files:**
- Modify: `app/static/index.html` — 替换左栏内容
- Modify: `app/static/css/style.css` — 新增 Observe/Voice Status 样式

**Changes:**
1. 去掉 CPU、Memory、事件数相关内容
2. 新增 Observe 区域（当前行为、专注度、今日时长、当前阶段）
3. 新增 Voice Status 区域（语音模式状态）
4. 配色新增 Warning #FFC857、Error #FF5D73 CSS 变量

---

## Task 2: Center — AI Consciousness 5 状态

**Files:**
- Modify: `app/static/js/particle-core.js` — 5 状态 + Core Light
- Modify: `app/static/js/app.js` — 状态映射

**Changes:**
1. 粒子球中心新增 Core Light（SphereGeometry + MeshBasicMaterial）
2. 新增 setState('sleeping')，重命名 setState('analyzing') 为 setState('thinking')
3. 新增 Speaking 状态（波纹扩散动画）
4. 各状态粒子行为映射到新设计

---

## Task 3: Right Panel — Machine Thoughts

**Files:**
- Modify: `app/static/js/timeline.js` — 重写为 Machine Thoughts

**Changes:**
1. 去掉时间戳事件列表
2. 改为展示 think 端点返回的 thoughts 数组
3. 顶部显示 "Machine 的思考" 头部
4. Top 3 活动类别（activity_distribution）
5. 一句话建议

---

## Task 4: Background + Colors + Dock

**Files:**
- Modify: `app/static/css/style.css` — 背景渐变、Warning/Error 色值
- Modify: `app/static/css/animations.css` — 星点漂移动画
- Modify: `app/static/assets/icons.js` — 新增 Tasks 图标

**Changes:**
1. 背景从纯黑改为深蓝黑渐变
2. CSS 星点 overlay（极慢漂移）
3. Dock 从 5 项增至 6 项
