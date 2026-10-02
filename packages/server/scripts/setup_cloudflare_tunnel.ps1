<#
.SYNOPSIS
    Yu-Gi-Oh! Platform - Windows Cloudflare Zero Trust Tunnel Setup & Manager (PowerShell)

.DESCRIPTION
    Connects the local FastAPI Web Card Catalog & REST API (Port 8000)
    to Cloudflare's global edge network via an encrypted tunnel on Windows.

    Operational Modes:
    1. Quick Tunnel (Free, zero-config, ephemeral https://*.trycloudflare.com):
       Useful for local testing, LAN duels, and quick remote sharing without an account.
    2. Named Tunnel (Custom domain via Cloudflare Zero Trust token):
       Production 24/7 tunnel mapped to your custom domain (e.g. thelandofkustomazi.com).

.PARAMETER Quick
    Force launch of a quick ephemeral tunnel regardless of .env configuration.

.PARAMETER Token
    Explicit Cloudflare Zero Trust Tunnel token string.

.EXAMPLE
    .\setup_cloudflare_tunnel.ps1
    .\setup_cloudflare_tunnel.ps1 -Quick
    .\setup_cloudflare_tunnel.ps1 -Token "eyJhIjoi..."
#>

[CmdletBinding()]
param (
    [switch]$Quick,
    [string]$Token
)

$ErrorActionPreference = "Stop"

function Write-Info ($msg) { Write-Host "[*] $msg" -ForegroundColor Cyan }
function Write-Success ($msg) { Write-Host "[+] $msg" -ForegroundColor Green }
function Write-Warn ($msg) { Write-Host "[!] $msg" -ForegroundColor Yellow }
function Write-Err ($msg) { Write-Host "[-] $msg" -ForegroundColor Red }

# Visual Header
Write-Host "=====================================================================" -ForegroundColor Blue
Write-Host "  🌐 Yu-Gi-Oh! Cloudflare Tunnel Secure Connector (Windows)          " -ForegroundColor Blue
Write-Host "=====================================================================" -ForegroundColor Blue

# 1. Resolve Script & Root Directories
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = $null

$SearchDir = $ScriptDir
for ($i = 0; $i -lt 5; $i++) {
    if ((Test-Path "$SearchDir\.env") -or (Test-Path "$SearchDir\manage.py")) {
        $BaseDir = $SearchDir
        break
    }
    $Parent = Split-Path -Parent $SearchDir
    if ($Parent -eq $SearchDir) { break }
    $SearchDir = $Parent
}

if (-not $BaseDir) {
    $BaseDir = (Resolve-Path "$ScriptDir\..\..\..").Path
}

$EnvFile = "$BaseDir\.env"
$ClientConfigFile = "$BaseDir\config\client\config.json"
if (-not (Test-Path $ClientConfigFile)) {
    $ClientConfigFile = "$BaseDir\production\shared\config.json"
}

# 2. Helper: Ensure cloudflared.exe binary exists
function Get-CloudflaredPath {
    $cmd = Get-Command "cloudflared.exe" -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $LocalDir = "$env:LOCALAPPDATA\cloudflared"
    $LocalBin = "$LocalDir\cloudflared.exe"
    if (Test-Path $LocalBin) {
        return $LocalBin
    }

    # Also check venv\Scripts
    $VenvBin = "$BaseDir\venv\Scripts\cloudflared.exe"
    if (Test-Path $VenvBin) {
        return $VenvBin
    }

    Write-Info "cloudflared.exe not found in PATH. Downloading Windows 64-bit binary..."
    if (-not (Test-Path $LocalDir)) {
        New-Item -ItemType Directory -Path $LocalDir -Force | Out-Null
    }

    $DownloadUrl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $DownloadUrl -OutFile $LocalBin -UseBasicParsing
        Write-Success "cloudflared.exe downloaded to $LocalBin."
        return $LocalBin
    }
    catch {
        Write-Err "Failed to download cloudflared.exe: $($_.Exception.Message)"
        Write-Err "Please download manually from: $DownloadUrl"
        exit 1
    }
}

$CloudflaredBin = Get-CloudflaredPath

# 3. Read .env configuration if token not explicitly passed
$EnvToken = ""
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -notmatch '^#' -and $line -match '^CLOUDFLARE_TUNNEL_TOKEN=(.*)$') {
            $EnvToken = $matches[1].Trim().Trim('"').Trim("'")
        }
    }
}

$Mode = "auto"
if ($Quick) {
    $Mode = "quick"
}
elseif ($Token) {
    $Mode = "token"
}
elseif ($EnvToken -and $EnvToken -ne "your_cloudflare_tunnel_token_here") {
    $Mode = "token"
    $Token = $EnvToken
}
else {
    $Mode = "quick"
}

# 4. Launch Tunnel
if ($Mode -eq "token") {
    Write-Info "Starting Cloudflare Named Tunnel using configured token..."
    Write-Host "    Public Target : Custom Domain via Zero Trust Edge" -ForegroundColor Gray
    Write-Host "    Local Target  : http://localhost:8000 (FastAPI Web Catalog)" -ForegroundColor Gray
    Write-Host ""
    Write-Warn "Tunnel running in foreground. Press Ctrl+C to terminate."
    Write-Host ""
    & "$CloudflaredBin" tunnel --no-autoupdate run --token "$Token"
}
else {
    Write-Info "Starting Cloudflare Quick Tunnel (Free, zero-config)..."
    Write-Host "    Local Target : http://localhost:8000" -ForegroundColor Gray
    Write-Host ""

    $LogFile = [System.IO.Path]::GetTempFileName()

    $ProcessInfo = New-Object System.Diagnostics.ProcessStartInfo
    $ProcessInfo.FileName = $CloudflaredBin
    $ProcessInfo.Arguments = "tunnel --url http://localhost:8000"
    $ProcessInfo.RedirectStandardError = $true
    $ProcessInfo.RedirectStandardOutput = $true
    $ProcessInfo.UseShellExecute = $false
    $ProcessInfo.CreateNoWindow = $true

    $Process = New-Object System.Diagnostics.Process
    $Process.StartInfo = $ProcessInfo

    # Background capture
    $ErrorEvent = Register-ObjectEvent -InputObject $Process -EventName "ErrorDataReceived" -Action {
        if ($EventArgs.Data) { Add-Content -Path $using:LogFile -Value $EventArgs.Data }
    }
    $OutputEvent = Register-ObjectEvent -InputObject $Process -EventName "OutputDataReceived" -Action {
        if ($EventArgs.Data) { Add-Content -Path $using:LogFile -Value $EventArgs.Data }
    }

    $Process.Start() | Out-Null
    $Process.BeginErrorReadLine()
    $Process.BeginOutputReadLine()

    Write-Info "Waiting for tunnel connection and public HTTPS URL..."
    $TunnelUrl = $null

    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        if (Test-Path $LogFile) {
            $Content = Get-Content $LogFile -Raw -ErrorAction SilentlyContinue
            if ($Content -match '(https://[-a-zA-Z0-9\.]*\.trycloudflare\.com)') {
                $TunnelUrl = $matches[1]
                break
            }
        }
    }

    if (-not $TunnelUrl) {
        Write-Err "Timeout: Failed to acquire tunnel URL within 30 seconds."
        if (Test-Path $LogFile) {
            Write-Host (Get-Content $LogFile -Raw) -ForegroundColor Gray
        }
        $Process.Kill()
        exit 1
    }

    Write-Host ""
    Write-Host "=====================================================================" -ForegroundColor Green
    Write-Host "  🎉 CLOUDFLARE HTTPS TUNNEL IS LIVE!                                " -ForegroundColor Green
    Write-Host "=====================================================================" -ForegroundColor Green
    Write-Host "  Public HTTPS URL: " -NoNewline
    Write-Host "$TunnelUrl" -ForegroundColor Yellow -BackgroundColor Black
    Write-Host "  Local Service   : http://localhost:8000"
    Write-Host ""

    # Update config.json with live URL
    if (Test-Path $ClientConfigFile) {
        try {
            Write-Info "Updating $ClientConfigFile with live tunnel URL..."
            $Json = Get-Content $ClientConfigFile -Raw | ConvertFrom-Json
            $Json.web_catalog_url = $TunnelUrl
            $Json.expansions_update_url = "$TunnelUrl/api/expansions/download"
            $Json | ConvertTo-Json -Depth 5 | Set-Content $ClientConfigFile -Encoding UTF8
            Write-Success "Client config manifest updated with public HTTPS URL."
        }
        catch {
            Write-Warn "Could not update client manifest: $($_.Exception.Message)"
        }
    }

    Write-Host ""
    Write-Warn "Tunnel is active. Press Ctrl+C in this console to terminate."

    try {
        while (-not $Process.HasExited) {
            Start-Sleep -Seconds 1
        }
    }
    finally {
        if (-not $Process.HasExited) {
            Write-Info "Stopping Cloudflare Tunnel..."
            $Process.Kill()
        }
        Unregister-Event -SourceIdentifier $ErrorEvent.Name -ErrorAction SilentlyContinue
        Unregister-Event -SourceIdentifier $OutputEvent.Name -ErrorAction SilentlyContinue
        Remove-Item $LogFile -ErrorAction SilentlyContinue
    }
}
