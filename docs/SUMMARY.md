# Project Machine — 文档体系汇总

> 生成日期: 2026-07-10
> 说明: 对 docs/ 下所有文档进行归纳、分类和时效性评估

---

## 一、文档健康度速览

| 分类 | 总量 | 有效 | 部分过时 | 已废弃 |
|------|------|------|----------|--------|
| adr/(架构决策) | 2 | 2 | 0 | 0 |
| phases/(完成报告) | 5 | 5 | 0 | 0 |
| ROADMAP, GAP_ANALYSIS | 2 | 0 | 2 | 0 |
| design/(UI概念稿) | 3 | 3 | 0 | 0 |
| superpowers/specs/(设计文档) | 11 | 0 | 9 | 2 |
| superpowers/plans/(实施计划) | 7 | 0 | 0 | 7 |
| **合计** | **30** | **10** | **11** | **9** |

---

## 二、文档分类评价

### 2.1 保留（10个，仍有效）

- **adr/ADR-0001-payload-jsonb.md** — Event payload使用PostgreSQL JSONB，该决策仍在使用
- **adr/ADR-0002-api-key-auth.md** — API Key认证方案，未改变
- **phases/PHASE-01~05.md** — Phase 1~5完成报告，作开发历史留存
- **design/mockup-*.png** — 前端UI概念参考图

### 2.2 部分过时（11个，可参考但不能全信）

| 文档 | 过时内容 | 实际现状 |
|------|----------|---------|
| ROADMAP.md | Phase 1-5标记为"进行中/待开始" | Phase 1-5已全部完成；Phase 6 Agent已实现；Phase 7部分落地 |
| GAP_ANALYSIS.md | 提到"无LLM API Key"、"无语义Embedding" | DeepSeek已接入、sentence-transformers已实现 |
| specs/echo-architecture.md | 规划中的consolidation等 | 大部分已实现(consolidation.py等) |
| specs/architecture-optimization.md | 规划配置重构、APScheduler | 全部已执行 |
| specs/emotion-v2-design.md | 规划5信号情绪引擎 | 已实现 |
| specs/p0-p1-stability-fixes.md | 规划采集器v5、对话持久化 | 全部已修复 |
| specs/frontend-redesign-v1/v2 | 规划Three.js粒子系统 | 已落地 |
| specs/hologram-dashboard.md | 全息风Dashboard | 功能已实现但风格不同 |
| specs/2026-07-09-summary.md | 当日工作清单 | 全部已落地 |

### 2.3 废弃（9个，被取代或空文件）

| 文档 | 废弃原因 |
|------|---------|
| specs/voice-realtime-design.md | sherpa-onnx本地方案未落地，改用百度API |
| specs/voice-interaction-design.md | 百度方案部分落地但设计细节未完全按设计实现 |
| plans/* (7个) | 全部是已完成实施计划，可归档 |
| plans/frontend-redesign-machine-interface.md | 仅50字节空文件 |

---

## 三、建议操作

**保留（10个）:** adr/, phases/, design/ 下的文件

**更新（2个）:** ROADMAP.md（更新Phase状态）、GAP_ANALYSIS.md（重写差距分析）

**归档或删除（18个）:**
- superpowers/specs/ 中9个过时设计文档
- superpowers/plans/ 中7个完成计划
- 2个废弃语音设计文档
