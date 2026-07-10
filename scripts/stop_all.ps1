# Project Machine — Graceful shutdown

# 1. Stop collector (standalone + legacy)
Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*collector*"
} | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name "powershell" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*collector*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

# 2. Stop FastAPI
Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*uvicorn*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

# 3. Stop PostgreSQL
& "C:\pgsql\pgsql\bin\pg_ctl.exe" -D "C:\pgsql\data" stop 2>&1 | Out-Null
