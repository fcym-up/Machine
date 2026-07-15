@echo off
title Machine Services Stopper
cd /d "%~dp0"
echo ========================================
echo   Stopping Machine Services
echo ========================================
echo.

REM --- Web Server ---
echo [1/3] Stopping Web Server...
taskkill /FI "WINDOWTITLE eq Machine Server*" /F 2>nul
taskkill /IM uvicorn.exe /F 2>nul
echo   Done.

REM --- Collector ---
echo [2/3] Stopping Collector...
taskkill /FI "WINDOWTITLE eq Machine Collector*" /F 2>nul
echo   Done.

REM --- PostgreSQL ---
echo [3/3] Stopping PostgreSQL...
C:\pgsql\pgsql\bin\pg_ctl stop -D "C:\pgsql\data" -m fast 2>nul
if %errorlevel% equ 0 (
    echo   PostgreSQL stopped.
) else (
    taskkill /F /IM postgres.exe 2>nul
    echo   PostgreSQL stopped (forced).
)

timeout /t 2 /nobreak >nul
echo.
echo ========================================
echo   All services stopped.
echo ========================================
