# Project Machine - Architecture Optimization (Plan A)

> Date: 2026-07-09
> Status: Reviewed, pending execution

## Objective

Resolve core architecture issues with minimal intrusion, keeping API fully compatible, zero functional changes, and all tests passing.

## Constraints

- No changes to existing API paths, request formats, or response formats
- No changes to existing database schema
- No changes to environment variable names
- No changes to Dashboard frontend
- No changes to collector business logic

---

## 1. Unified Configuration System

### Current State

- `app/core/config.py`: plain class with class-level attributes, self-managed load_dotenv()
- `app/core/llm.py`: another independent load_dotenv()
- `collector/config.py`: hardcoded constants, independent from app config

### Changes

| File | Change |
|------|--------|
| app/core/config.py | Rewrite as pydantic-settings BaseSettings, property names fully compatible |
| app/core/llm.py | Remove own load_dotenv(), use from app.core.config import settings |
| collector/config.py | No change (collector runs independently) |
| requirements.txt | Add pydantic-settings |

### Safety

- All env var names unchanged: DATABASE_URL, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, API_KEY
- settings.xxx usage unchanged
- pytest tests/ -v green after change

---

## 2. Scheduler: APScheduler Replacement

### Current State

- app/core/scheduler.py: time.sleep(5) + manual tick accumulation
- Task duration >5s causes clock drift
- All ticks reset on service restart
- DB session created every loop iteration (even when no tasks)

### Changes

Replace sleep+tick with APScheduler:

| Current Tick | Frequency | APScheduler Equivalent |
|---|---|---|
| consolidate_hourly / dimensions / state / behavior / reflection | Every ~60s | IntervalTrigger(seconds=60) |
| batch_enrich_entities | Every ~30s | IntervalTrigger(seconds=30) |
| emotion collect + compute | Every ~5min | IntervalTrigger(minutes=5) |
| consolidate_daily / daily_reflection | Every ~24h | CronTrigger(hour=2, minute=0) |
| consolidate_weekly | Every ~7d | CronTrigger(day_of_week=0, hour=3, minute=0) |

Scope:

| File | Change |
|------|--------|
| app/core/scheduler.py | Full rewrite; start()/stop() interface unchanged |
| app/main.py | No change |
| requirements.txt | Add apscheduler |

### Safety

- TaskScheduler.start()/stop() signature unchanged
- All task function references unchanged (no changes to consolidation, reflection, user_model, emotion, etc.)
- DB session created only when tasks actually execute
- pytest tests/ -v green after change

---

## 3. Remove Dead Code in app/collectors/

### Current State

- app/collectors/ has 6 .py files with zero imports
- Active collector lives in collector/; two sets coexist confusingly

### Changes

Delete these files (after confirming zero imports):

- app/collectors/activity_monitor.py
- app/collectors/file_watcher.py
- app/collectors/git_monitor.py
- app/collectors/process_monitor.py
- app/collectors/terminal_recorder.py
- app/collectors/window_monitor.py
- app/collectors/__init__.py
- app/collectors/__pycache__/ (entire directory)

### Safety

- Run rg for from app.collectors before deletion
- pytest tests/ -v green after deletion
- Git history preserves deleted files

---

## 4. Complete Database Migrations

### Current State

- alembic/versions/ has only 1 migration (create events table)
- Actual DB has 8 tables, not under migration control

### Changes

Two-step, no data loss:

1. alembic stamp head - mark current version as latest
2. alembic revision --autogenerate -m 'capture_full_schema_v0.6.0' - generate baseline capturing full schema

### Safety

- --autogenerate only diffs models vs DB, does not modify existing data
- alembic current after to verify sync

---

## Regression Verification Checklist

- pytest tests/ -v: all passing
- Collector starts and writes events normally
- Scheduler background tasks fire at correct intervals
- alembic current shows latest version
- /docs accessible, all endpoints return normally
- Dashboard loads correctly
