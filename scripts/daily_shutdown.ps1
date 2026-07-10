# Machine Auto-Save & Shutdown Script
# Runs daily at 6:00 AM
$logfile = "D:\workplace\logs\shutdown.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $logfile -Value "$timestamp - Shutdown routine started"

# 1. Stop PostgreSQL gracefully
try {
    & "C:\pgsql\pgsql\bin\pg_ctl.exe" -D "C:\pgsql\data" stop -m fast 2>&1 | Out-Null
    Add-Content -Path $logfile -Value "$timestamp - PostgreSQL stopped"
} catch {
    Add-Content -Path $logfile -Value "$timestamp - PostgreSQL stop failed: $_"
}

# 2. Git save
Set-Location D:\workplace
try {
    git add -A 2>&1 | Out-Null
    git commit -m "auto: daily save $(Get-Date -Format 'yyyy-MM-dd HH:mm')" 2>&1 | Out-Null
    Add-Content -Path $logfile -Value "$timestamp - Git auto-commit done"
} catch {
    Add-Content -Path $logfile -Value "$timestamp - Git save skipped: $_"
}

# 3. Shutdown
Add-Content -Path $logfile -Value "$timestamp - Shutting down..."
shutdown /s /t 60 /c "Machine daily shutdown at 6:00 AM"