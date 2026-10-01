@echo off
REM =============================================================================
REM Yu-Gi-Oh! Platform Manager - Windows CLI & Launcher
REM =============================================================================
REM Usage:
REM   manage.bat status
REM   manage.bat sync
REM   manage.bat app
REM =============================================================================

title Yu-Gi-Oh! Platform Manager
setlocal enabledelayedexpansion

set "BASE_DIR=%~dp0"
set "VENV_PYTHON=%BASE_DIR%venv\Scripts\python.exe"

if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" "%BASE_DIR%manage.py" %*
) else (
    python "%BASE_DIR%manage.py" %*
)
