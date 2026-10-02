@echo off
REM =============================================================================
REM Yu-Gi-Oh! Custom Server, Story Platform & Simulator - Windows Master CLI
REM =============================================================================
REM Windows batch controller and launcher wrapper for manage.py.
REM
REM Resolves:
REM 1. Virtual environment Python executable (%~dp0venv\Scripts\python.exe)
REM 2. Fallback to system Python executable if venv is not initialized
REM 3. Passes all commands and arguments transparently to manage.py
REM
REM Common Commands:
REM   manage.bat status       - Display live platform, DB, and container status
REM   manage.bat sync         - Synchronize custom card database & Lua scripts
REM   manage.bat package      - Build client zip & server tarball release packages
REM   manage.bat app          - Launch the Desktop GUI Platform Manager
REM   manage.bat web          - Launch the FastAPI Web Catalog on localhost:8000
REM   manage.bat bot          - Launch the Discord Story & Duel Bot
REM   manage.bat test         - Run the Pytest test suite
REM =============================================================================

title Yu-Gi-Oh! Platform Manager
setlocal enabledelayedexpansion

REM Resolve project root directory from batch file location
set "BASE_DIR=%~dp0"
set "VENV_PYTHON=%BASE_DIR%venv\Scripts\python.exe"

REM Check for virtual environment Python executable
if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" "%BASE_DIR%manage.py" %*
) else (
    REM Fallback to system Python
    where python >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        python "%BASE_DIR%manage.py" %*
    ) else (
        echo [-] Error: Python was not found in PATH or in the venv\ directory.
        echo     Please install Python 3.9+ from https://www.python.org/
        pause
        exit /b 1
    )
)
