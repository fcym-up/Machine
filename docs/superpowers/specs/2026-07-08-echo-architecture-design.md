# Project Machine v1.0 Design — Echo Architecture

> Date: 2026-07-08
> Status: Approved
> Based on: Echo Design Document v1.0

## Overview

Project Machine evolves from an event-centric data collector into a full Echo system — an empathetic AI companion with long-term memory, dynamic user modeling, behavioral pattern discovery, and self-reflection.

## Architecture

### Data Flow

Collector → Event Engine → events table
  ├── Entity extraction → entities + relationships
  ├── Importance scoring
  └── Hourly consolidation → Memory hierarchy (working→short→long→semantic)

Memory hierarchy feeds into:
  ├── User model update → trait_dimensions + user_state
  ├── Brain.think() → dashboard + conversation
  └── Daily reflection → system_reflections

### New Tables

1. **behavior_patterns** — Discovered user behavior patterns (daily rhythms, emotional triggers, anomalies)
2. **trait_dimensions** — Five personality dimensions: productivity, social_energy, emotional_stability, curiosity, focus_depth
3. **user_state** — Current snapshot: emotional state, energy, focus, active topics
4. **system_reflections** — Machine\'s self-reflection diary (Module 5)

### Modified Tables

5. **memories** — Added fields: layer (working/short/long/semantic), decay_rate, access_count, last_accessed, consolidated_from

### Memory Consolidation Pipeline

- Hourly: events → working memory (LLM summary, decay=1.0)
- Daily: working memories → short memory (pattern analysis, decay=0.5)
- Weekly: short memories → long/semantic memory (knowledge extraction, decay=0.1/0.0)

### User Model

Five trait dimensions updated from event stream:
- productivity: coding ratio + sustained focus duration
- social_energy: social event frequency + distribution
- emotional_stability: EmotionEngine output variance
- curiosity: novel event discovery rate
- focus_depth: single-session coding duration + interruption frequency

### Behavioral Mapping (Echo Section 3)

Dual mapping system:
- Static: LLM-initialized common human behavior knowledge
- Dynamic: patterns learned from user behavior (≥3 repetitions)
- Three trigger types: daily, trigger (emotion→action), anomaly (2σ deviation)

### Scheduled Tasks

| Task | Frequency | Action |
|------|-----------|--------|
| consolidate_hourly | Hourly | events→working memory, dimension updates |
| consolidate_daily | Daily | working→short→long, pattern discovery |
| consolidate_weekly | Weekly | long→semantic, reflection generation |
| update_user_state | 15min | Refresh user_state snapshot |
| behavior_scan | Hourly | Detect new behavior patterns |

### File Structure

- models: app/models/user_profile.py (new tables), app/models/memory.py (modified)
- schemas: app/schemas/user_profile.py
- services: consolidation.py, user_model.py, behavior_mapping.py, reflection.py
- api: profile.py (extended), memories.py (extended), system.py (new)
- core: scheduler.py (new)
- alembic: migration for new tables + memory fields
- tests: per-service test files
