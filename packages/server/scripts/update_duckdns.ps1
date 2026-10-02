<#
.SYNOPSIS
    Yu-Gi-Oh! Platform - Windows DuckDNS Dynamic DNS Auto-Updater (PowerShell)

.DESCRIPTION
    Synchronizes the current public WAN IP of the Windows host machine with DuckDNS
    (e.g., thelandofkustomazi.duckdns.org).

    Primary Purpose:
    Provides a reliable dynamic fallback hostname for live game client direct
    connections (Port 7911) in case the host IP ever changes.

.PARAMETER Domain
    The DuckDNS subdomain (defaults to DUCKDNS_DOMAIN from .env or 'thelandofkustomazi').

.PARAMETER Token
    The DuckDNS authentication token (defaults to DUCKDNS_TOKEN from .env).

.EXAMPLE
    .\update_duckdns.ps1
    .\update_duckdns.ps1 -Domain "thelandofkustomazi" -Token "your_token"

.NOTES
    To schedule as a recurring task every 5 minutes in Windows Task Scheduler:
    schtasks /create /tn "DuckDNS_AutoUpdate" /tr "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\path\to\packages\server\scripts\update_duckdns.ps1" /sc minute /mo 5 /f
#>

[CmdletBinding()]
param (
    [string]$Domain,
    [string]$Token
)

$ErrorActionPreference = "Stop"

# Visual status helper functions
function Write-Info ($msg) { Write-Host "[*] $msg" -ForegroundColor Cyan }
function Write-Success ($msg) { Write-Host "[+] $msg" -ForegroundColor Green }
function Write-Warn ($msg) { Write-Host "[!] $msg" -ForegroundColor Yellow }
function Write-Err ($msg) { Write-Host "[-] $msg" -ForegroundColor Red }

# 1. Resolve Script & Root Directories
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = $null

# Walk up to find project root (containing .env or manage.py)
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

# 2. Extract configuration from .env if not explicitly passed as arguments
if ((-not $Domain -or -not $Token) -and (Test-Path $EnvFile)) {
    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -notmatch '^#' -and $line -match '^([^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $val = $matches[2].Trim().Trim('"').Trim("'")
            if ($key -eq "DUCKDNS_DOMAIN" -and -not $Domain) { $Domain = $val }
            if ($key -eq "DUCKDNS_TOKEN" -and -not $Token) { $Token = $val }
        }
    }
}

if (-not $Domain) {
    $Domain = "thelandofkustomazi"
}

if (-not $Token -or $Token -eq "your_duckdns_token_here") {
    Write-Warn "Notice: DUCKDNS_TOKEN not yet specified in .env or arguments."
    Write-Warn "To enable automatic IP syncing, set DUCKDNS_TOKEN in your .env file."
    exit 0
}

# 3. Discover Public IPv4 Address
Write-Info "Detecting public WAN IPv4 address..."
$CurrentIP = $null
$IPProviders = @(
    "https://api.ipify.org",
    "https://ifconfig.me/ip",
    "https://icanhazip.com"
)

foreach ($provider in $IPProviders) {
    try {
        $resp = Invoke-RestMethod -Uri $provider -TimeoutSec 5 -UseBasicParsing
        $candidate = ($resp.ToString().Trim())
        if ($candidate -match '^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$') {
            $CurrentIP = $candidate
            break
        }
    }
    catch {
        # Continue to next provider
    }
}

if (-not $CurrentIP) {
    Write-Err "Failed to determine public IPv4 address from discovery endpoints."
    exit 1
}

# 4. Synchronize with DuckDNS API
Write-Info "Updating DuckDNS record: $Domain.duckdns.org -> $CurrentIP..."
$DuckDnsUrl = "https://www.duckdns.org/update?domains=$Domain&token=$Token&ip=$CurrentIP"

try {
    $Result = (Invoke-RestMethod -Uri $DuckDnsUrl -TimeoutSec 10 -UseBasicParsing).ToString().Trim()
    if ($Result -eq "OK") {
        Write-Success "DuckDNS successfully updated: $Domain.duckdns.org -> $CurrentIP"
        exit 0
    }
    else {
        Write-Err "DuckDNS update failed. Response: $Result"
        exit 1
    }
}
catch {
    Write-Err "HTTP request to DuckDNS failed: $($_.Exception.Message)"
    exit 1
}
