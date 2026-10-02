@echo off
REM =============================================================================
REM Yu-Gi-Oh! Custom Expansions - Windows Player Client 1-Click Installer
REM =============================================================================
REM Double-click to install custom cards, scripts, and decks into EDOPro / YGOPro.
REM =============================================================================

title Yu-Gi-Oh! Expansion Synchronizer
setlocal enabledelayedexpansion

set "SYNC_SCRIPT=%~dp0src\sync_client.py"

if not exist "%SYNC_SCRIPT%" (
    echo [-] Error: Installer script was not found at:
    echo     %SYNC_SCRIPT%
    pause
    exit /b 1
)

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    python "%SYNC_SCRIPT%" %*
) else (
    where py >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        py -3 "%SYNC_SCRIPT%" %*
    ) else (
        echo [-] Error: Python was not found on your system.
        echo Please install Python 3 from https://www.python.org/downloads/
        echo Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    )
)

pause
