@echo off
REM =============================================================================
REM Yu-Gi-Oh! Platform - Windows Server Host Launcher & Service Controller
REM =============================================================================
REM Provides local orchestration for Windows host environments to start, manage,
REM and monitor the Yu-Gi-Oh! server stack (Simulator, Web Catalog API, Discord Bot).
REM
REM Usage:
REM   start_server.bat             (Displays interactive management menu)
REM   start_server.bat all         (Starts Simulator, Web Server, and Discord Bot)
REM   start_server.bat simulator   (Starts ocgcore Docker Compose container)
REM   start_server.bat web         (Starts FastAPI Web Catalog on localhost:8000)
REM   start_server.bat bot         (Starts The Great Kasutamaiza Discord Bot)
REM   start_server.bat sync        (Synchronizes custom card database and Lua scripts)
REM   start_server.bat tunnel      (Starts Cloudflare HTTPS tunnel)
REM   start_server.bat duckdns     (Updates DuckDNS dynamic DNS record)
REM   start_server.bat stop        (Stops Docker containers and running services)
REM =============================================================================

title Yu-Gi-Oh! Server Host Manager (Windows)
setlocal enabledelayedexpansion

REM Resolve directories
set "SERVER_DIR=%~dp0"
set "BASE_DIR="

REM Detect if running from repo root or standalone package
if exist "%SERVER_DIR%..\..\manage.py" (
    pushd "%SERVER_DIR%..\.."
    set "BASE_DIR=!CD!"
    popd
) else if exist "%SERVER_DIR%manage.py" (
    set "BASE_DIR=%SERVER_DIR%"
) else (
    set "BASE_DIR=%SERVER_DIR%"
)

REM Locate Python executable
set "PYTHON_BIN=%BASE_DIR%\venv\Scripts\python.exe"
if not exist "%PYTHON_BIN%" (
    where python >nul 2>nul
    if !ERRORLEVEL! EQU 0 (
        set "PYTHON_BIN=python"
    ) else (
        echo [-] Error: Python was not found in PATH or venv\Scripts\.
        echo     Please install Python 3.9+ from https://www.python.org/
        pause
        exit /b 1
    )
)

REM CLI Argument Routing
if not "%~1"=="" (
    if /i "%~1"=="all" goto do_all
    if /i "%~1"=="simulator" goto do_simulator
    if /i "%~1"=="web" goto do_web
    if /i "%~1"=="bot" goto do_bot
    if /i "%~1"=="sync" goto do_sync
    if /i "%~1"=="tunnel" goto do_tunnel
    if /i "%~1"=="duckdns" goto do_duckdns
    if /i "%~1"=="stop" goto do_stop
    echo [-] Unknown argument: %~1
    echo     Available options: all, simulator, web, bot, sync, tunnel, duckdns, stop
    exit /b 1
)

:menu
cls
echo =====================================================================
echo   🖥️  Yu-Gi-Oh! Server Host Management Console (Windows)
echo =====================================================================
echo.
echo   1. Start Full Server Stack (Simulator + Web API + Discord Bot)
echo   2. Start Live Duel Simulator Container (ocgcore on TCP 7911/7922)
echo   3. Start Web Catalog & REST API Server (FastAPI on Port 8000)
echo   4. Start Discord Story & Duel Bot (The Great Kasutamaiza)
echo   5. Synchronize Custom Cards (Compile CDB & Lua effect scripts)
echo   6. Start Cloudflare HTTPS Tunnel (Remote Card Sync & Web Access)
echo   7. Update DuckDNS Dynamic DNS Record
echo   8. Stop Simulator Containers
echo   0. Exit
echo.
echo =====================================================================
set /p "CHOICE=Select an option [0-8]: "

if "%CHOICE%"=="1" goto do_all
if "%CHOICE%"=="2" goto do_simulator
if "%CHOICE%"=="3" goto do_web
if "%CHOICE%"=="4" goto do_bot
if "%CHOICE%"=="5" goto do_sync
if "%CHOICE%"=="6" goto do_tunnel
if "%CHOICE%"=="7" goto do_duckdns
if "%CHOICE%"=="8" goto do_stop
if "%CHOICE%"=="0" exit /b 0

echo [-] Invalid choice, please try again.
pause
goto menu

:do_all
echo.
echo [*] Starting ocgcore Live Duel Simulator Container...
call :sub_simulator
echo [*] Launching FastAPI Web Catalog Server in separate window...
start "Yu-Gi-Oh! Web Catalog" cmd /c "%SERVER_DIR%start_server.bat web"
echo [*] Launching Discord Story & Duel Bot in separate window...
start "Yu-Gi-Oh! Discord Bot" cmd /c "%SERVER_DIR%start_server.bat bot"
echo.
echo [+] Full Yu-Gi-Oh! server stack is running!
echo     - Simulator: localhost:7911 (raw TCP)
echo     - Web API  : http://localhost:8000
echo.
pause
goto menu

:do_simulator
call :sub_simulator
pause
goto menu

:sub_simulator
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [-] Error: Docker is not installed or not in PATH.
    echo     Please install Docker Desktop for Windows: https://www.docker.com/products/docker-desktop/
    exit /b 1
)
cd /d "%BASE_DIR%"
docker compose up -d
echo [+] Simulator container is active.
exit /b 0

:do_web
cd /d "%BASE_DIR%"
echo [*] Launching FastAPI Web Catalog on http://localhost:8000...
"%PYTHON_BIN%" -m uvicorn production.main.web.api_server:app --host 0.0.0.0 --port 8000 --reload
exit /b 0

:do_bot
cd /d "%BASE_DIR%"
echo [*] Launching Discord Story & Duel Bot...
"%PYTHON_BIN%" "%BASE_DIR%\production\main\discord_bot\bot.py"
exit /b 0

:do_sync
cd /d "%BASE_DIR%"
echo [*] Synchronizing SQLite CDB and Lua effect scripts...
"%PYTHON_BIN%" "%BASE_DIR%\manage.py" sync
pause
goto menu

:do_tunnel
cd /d "%SERVER_DIR%scripts"
call setup_cloudflare_tunnel.bat
pause
goto menu

:do_duckdns
cd /d "%SERVER_DIR%scripts"
call update_duckdns.bat
pause
goto menu

:do_stop
cd /d "%BASE_DIR%"
echo [*] Stopping Docker containers...
docker compose down
echo [+] Docker containers stopped.
pause
goto menu
