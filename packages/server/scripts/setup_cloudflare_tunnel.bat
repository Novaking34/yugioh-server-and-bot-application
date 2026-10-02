@echo off
REM =============================================================================
REM Yu-Gi-Oh! Platform - Windows Cloudflare Tunnel Setup Wrapper (Batch)
REM =============================================================================
REM Launches setup_cloudflare_tunnel.ps1 via PowerShell with execution policy bypass.
REM
REM Usage:
REM   setup_cloudflare_tunnel.bat            REM Auto-detect token or fallback to quick
REM   setup_cloudflare_tunnel.bat --quick    REM Start instant ephemeral tunnel
REM   setup_cloudflare_tunnel.bat --token <TOKEN> REM Start named production tunnel
REM =============================================================================

setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%setup_cloudflare_tunnel.ps1"

if not exist "%PS_SCRIPT%" (
    echo [-] Error: PowerShell script not found at %PS_SCRIPT%
    pause
    exit /b 1
)

REM Translate --quick to -Quick and --token to -Token
set "PS_ARGS="
:arg_loop
if "%~1"=="" goto run_script
if /i "%~1"=="--quick" (
    set "PS_ARGS=!PS_ARGS! -Quick"
    shift
    goto arg_loop
)
if /i "%~1"=="-quick" (
    set "PS_ARGS=!PS_ARGS! -Quick"
    shift
    goto arg_loop
)
if /i "%~1"=="--token" (
    set "PS_ARGS=!PS_ARGS! -Token "%~2""
    shift
    shift
    goto arg_loop
)
if /i "%~1"=="-token" (
    set "PS_ARGS=!PS_ARGS! -Token "%~2""
    shift
    shift
    goto arg_loop
)
set "PS_ARGS=!PS_ARGS! %1"
shift
goto arg_loop

:run_script
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%" !PS_ARGS!
exit /b %ERRORLEVEL%
