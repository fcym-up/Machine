@echo off
title Machine Services Launcher
cd /d "%~dp0"
echo ========================================
echo   Machine Services Launcher
echo ========================================
echo.

REM --- PostgreSQL ---
echo [1/3] Checking PostgreSQL...
C:\pgsql\pgsql\bin\pg_ctl status -D "C:\pgsql\data" >nul 2>nul
if %errorlevel% equ 0 (
    echo   PostgreSQL is already running.
) else (
    echo   Starting PostgreSQL...
    start "Machine PostgreSQL" /MIN cmd /c "C:\pgsql\pgsql\bin\pg_ctl start -D \"C:\pgsql\data\" -l \"C:\pgsql\pgsql\logs\startup.log\""
    timeout /t 4 /nobreak >nul
    echo   PostgreSQL started.
)

REM --- Web Server ---
echo [2/3] Starting Web Server...
start "Machine Server" /MIN cmd /c ""%~dp0.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8080"

REM --- Collector ---
echo [3/3] Starting Collector...
start "Machine Collector" /MIN cmd /c ""%~dp0.venv\Scripts\python.exe" collector/main.py"

echo.
echo ========================================
echo   All services started!
echo   Web: http://127.0.0.1:8080/
echo   Stop: stop_services.bat
echo ========================================
