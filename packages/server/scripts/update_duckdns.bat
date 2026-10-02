@echo off
REM =============================================================================
REM Yu-Gi-Oh! Platform - Windows DuckDNS Auto-Updater Wrapper (Batch)
REM =============================================================================
REM Launches update_duckdns.ps1 via PowerShell with execution policy bypass.
REM Can be executed directly or scheduled via Windows Task Scheduler.
REM
REM Usage:
REM   update_duckdns.bat
REM   update_duckdns.bat -Domain "mycustomdomain" -Token "abc123token"
REM =============================================================================

setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%update_duckdns.ps1"

if not exist "%PS_SCRIPT%" (
    echo [-] Error: PowerShell script not found at %PS_SCRIPT%
    exit /b 1
)

REM Execute PowerShell script with bypassed execution policy
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%" %*
exit /b %ERRORLEVEL%
