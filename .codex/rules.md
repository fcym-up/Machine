## Project Rules

### Changelog Requirement
Every bug fix or new feature MUST be documented in `fixbug&update-log/YYYY-MM-DD.md`.

### Running the System
```powershell
# Start PostgreSQL (if not running)
C:\pgsql\pgsql\bin\pg_ctl.exe -D C:\pgsql\data start

# Start FastAPI
cd D:\workplace
$env:HF_HUB_OFFLINE="1"
$env:CUDA_VISIBLE_DEVICES=""
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000

# Start collector (v4)
Start-Process powershell -ArgumentList "-NoProfile -Exec Bypass -WindowStyle Hidden -File D:\workplace\scripts\collector_v4.ps1"
```

### Project Context
- Tech: Python 3.13 + FastAPI + PostgreSQL 18 + DeepSeek LLM
- Dashboard: http://127.0.0.1:8000/dashboard
- API Docs: http://127.0.0.1:8000/docs
- Collector: `scripts/collector_v4.ps1` (PowerShell + .NET, 2s poll, 30s dedup)
- API Key: machine-dev-key-change-me
- HF_HUB_OFFLINE=1 (no network for ML model downloads)

### Key Files
- `scripts/collector_v4.ps1` — Current collector (PowerShell)
- `app/collectors/window_monitor.py` — Old Python collector (not used, kept for reference)
- `app/api/v1/events.py` — Events API
- `app/services/event.py` — Event service + dedup logic
- `app/services/process_classifier.py` — Process → category mapping