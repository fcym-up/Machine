# Architecture Optimization (Plan A) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 4 core architecture issues with minimal intrusion and zero functional change.

## Global Constraints

- Do NOT change existing API paths, request formats, or response formats
- Do NOT change existing database schema
- Do NOT change environment variable names
- All changes must pass pytest before commit
