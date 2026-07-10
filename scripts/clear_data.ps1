# Project Machine — Clear all test data (auto-stops collector first)

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent

Write-Host "Stopping collector..." -ForegroundColor Yellow
Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*collector*"
} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep 2

Write-Host "Clearing data..." -ForegroundColor Yellow
& "$ROOT\.venv\Scripts\python.exe" -c @"
from app.core.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
for t in ['conversation_messages','system_reflections','behavior_patterns','trait_dimensions','user_state','relationships','entities','memories','events']:
    try: db.execute(text(f'TRUNCATE TABLE {t} CASCADE'))
    except: pass
db.commit()
db.close()
print('All tables truncated.')
"@

Write-Host "Restarting collector..." -ForegroundColor Yellow
Start-Process -FilePath "$ROOT\.venv\Scripts\python.exe" `
    -ArgumentList "$ROOT\collector\main.py" `
    -WorkingDirectory $ROOT -WindowStyle Hidden

Write-Host "Done. All data cleared, collector restarted." -ForegroundColor Green
