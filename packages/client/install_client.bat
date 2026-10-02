@echo off
REM =============================================================================
REM Yu-Gi-Oh! Custom Expansions - Windows Player Client Installer
REM =============================================================================
REM Double-click to install custom cards, scripts, and decks into EDOPro / YGOPro.
REM =============================================================================

title Yu-Gi-Oh! Expansion Synchronizer
setlocal enabledelayedexpansion

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    python "%~dp0sync_client.py" %*
) else (
    where py >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        py -3 "%~dp0sync_client.py" %*
    ) else (
        echo [-] Error: Python was not found on your system.
        echo Please install Python 3 from https://www.python.org/downloads/
        echo Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    )
)

pause
