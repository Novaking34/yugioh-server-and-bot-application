@echo off
REM Launch the Player Expansion Manager Desktop Application on Windows
title Yu-Gi-Oh! Client Launcher
cd /d "%~dp0"

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    python client_app.py %*
) else (
    where py >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        py -3 client_app.py %*
    ) else (
        echo Python 3 was not found. Please install Python 3.
        pause
    )
)
