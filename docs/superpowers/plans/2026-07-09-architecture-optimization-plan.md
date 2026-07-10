# Architecture Optimization (Plan A) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** Fix 4 core architecture issues with minimal intrusion and zero functional change.

## Global Constraints

- Do NOT change existing API paths, request formats, or response formats
- Do NOT change existing database schema
- Do NOT change environment variable names
- Do NOT change Dashboard frontend
- Do NOT change collector business logic
- All changes must pass pytest before commit

---

### Task 1: Unified Configuration System

**Files:** Modify app/core/config.py, app/core/llm.py, requirements.txt

- [ ] Rewrite config.py with pydantic-settings BaseSettings, keep all property names
- [ ] Update llm.py to use from app.core.config import settings, remove own load_dotenv
- [ ] Add pydantic-settings to requirements.txt
- [ ] Run pytest tests/ -v

---

### Task 2: APScheduler Replacement

**Files:** Rewrite app/core/scheduler.py, update requirements.txt

- [ ] Rewrite scheduler.py with APScheduler BackgroundScheduler, keep start()/stop() interface
  - hourly tasks: IntervalTrigger(seconds=60)
  - entity enrich: IntervalTrigger(seconds=30)
  - emotion tasks: IntervalTrigger(minutes=5)
  - daily tasks: CronTrigger(hour=2, minute=0)
  - weekly tasks: CronTrigger(day_of_week=0, hour=3, minute=0)
- [ ] Add apscheduler to requirements.txt
- [ ] Run pytest tests/ -v

---

### Task 3: Remove Dead Code in app/collectors/

**Files:** Delete entire app/collectors/ directory

- [ ] Confirm zero imports via rg
- [ ] Remove-Item -Recurse -Force the directory
- [ ] Run pytest tests/ -v

---

### Task 4: Complete Database Migrations

- [ ] alembic stamp head
- [ ] alembic revision --autogenerate -m capture_full_schema_v0.6.0
- [ ] alembic current to verify
- [ ] Final pytest tests/ -v
