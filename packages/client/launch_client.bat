@echo off
REM =============================================================================
REM Yu-Gi-Oh! Player Client Desktop GUI Launcher (Windows)
REM =============================================================================
REM Double-click to launch the Player Expansion Manager GUI.
REM =============================================================================

title Yu-Gi-Oh! Client Launcher
cd /d "%~dp0"
setlocal enabledelayedexpansion

set "APP_SCRIPT=%~dp0src\client_app.py"

if not exist "%APP_SCRIPT%" (
    echo [-] Error: Application script was not found at:
    echo     %APP_SCRIPT%
    pause
    exit /b 1
)

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    python "%APP_SCRIPT%" %*
) else (
    where py >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        py -3 "%APP_SCRIPT%" %*
    ) else (
        echo [-] Error: Python 3 was not found. Please install Python 3.
        echo https://www.python.org/downloads/
        pause
    )
)
