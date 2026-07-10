# Project Machine — One-click launcher
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent

# 1. PostgreSQL
$pgStatus = & "C:\pgsql\pgsql\bin\pg_ctl.exe" -D "C:\pgsql\data" status 2>&1
if ($LASTEXITCODE -ne 0) {
    & "C:\pgsql\pgsql\bin\pg_ctl.exe" -D "C:\pgsql\data" start 2>&1 | Out-Null
}

# 2. FastAPI
$env:HF_HUB_OFFLINE = "1"
Start-Process -FilePath "$ROOT\.venv\Scripts\python.exe" `
    -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" `
    -WorkingDirectory $ROOT -WindowStyle Hidden

for ($i = 0; $i -lt 30; $i++) {
    try { $null = Invoke-RestMethod -Uri "http://127.0.0.1:8000/" -TimeoutSec 2; break }
    catch { Start-Sleep 1 }
}

# 3. Open Dashboard
Start-Process "http://127.0.0.1:8000/dashboard"

# 4. Start Collector (Python v7)
Start-Process -FilePath "$ROOT\.venv\Scripts\python.exe" `
    -ArgumentList "$ROOT\collector\main.py" `
    -WorkingDirectory $ROOT -WindowStyle Hidden

Write-Host "All services started: PostgreSQL + FastAPI + Collector" -ForegroundColor Green
