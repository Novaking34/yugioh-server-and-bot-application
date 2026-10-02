# 🛠️ Server Management Scripts (`packages/server/scripts/`)

This directory contains standalone automation scripts for managing networking, dynamic DNS, and secure edge tunneling for the Yu-Gi-Oh! platform on both Linux and Windows host systems.

---

## 📁 Script Manifest

| Script | Platform | Purpose | Execution |
| --- | --- | --- | --- |
| [`setup_cloudflare_tunnel.sh`](file:///home/professorseanex/yugioh-server/packages/server/scripts/setup_cloudflare_tunnel.sh) | Linux / macOS | Connects local FastAPI catalog (:8000) to Cloudflare edge | Manual / Automated |
| [`setup_cloudflare_tunnel.bat`](file:///home/professorseanex/yugioh-server/packages/server/scripts/setup_cloudflare_tunnel.bat) | Windows Batch | Windows wrapper launching PowerShell tunnel manager | Double-click / CLI |
| [`setup_cloudflare_tunnel.ps1`](file:///home/professorseanex/yugioh-server/packages/server/scripts/setup_cloudflare_tunnel.ps1) | Windows PS | Downloads `cloudflared.exe` if missing & manages tunnel | PowerShell |
| [`update_duckdns.sh`](file:///home/professorseanex/yugioh-server/packages/server/scripts/update_duckdns.sh) | Linux / macOS | Synchronizes host public WAN IP with DuckDNS dynamic DNS | Cron Job (every 5 min) |
| [`update_duckdns.bat`](file:///home/professorseanex/yugioh-server/packages/server/scripts/update_duckdns.bat) | Windows Batch | Windows wrapper launching PowerShell DuckDNS updater | Task Scheduler / CLI |
| [`update_duckdns.ps1`](file:///home/professorseanex/yugioh-server/packages/server/scripts/update_duckdns.ps1) | Windows PS | Discovers WAN IP & updates DuckDNS API | PowerShell |

---

## 🌐 1. Cloudflare Tunnel Manager

Supports both zero-configuration ephemeral tunnels and production 24/7 Named Tunnels:

### Linux / macOS

```bash
# 1. Automatic mode (uses CLOUDFLARE_TUNNEL_TOKEN from .env if present):
./setup_cloudflare_tunnel.sh

# 2. Ephemeral Quick Tunnel (generates free https://*.trycloudflare.com URL):
./setup_cloudflare_tunnel.sh --quick

# 3. Explicit Named Tunnel with token:
./setup_cloudflare_tunnel.sh --token <YOUR_CLOUDFLARE_TOKEN>
```

### Windows

```cmd
# 1. Automatic mode:
setup_cloudflare_tunnel.bat

# 2. Ephemeral Quick Tunnel:
setup_cloudflare_tunnel.bat --quick

# 3. Explicit Named Tunnel with token:
setup_cloudflare_tunnel.bat --token <YOUR_CLOUDFLARE_TOKEN>
```

When a quick tunnel starts, it automatically updates `config/client/config.json` with the temporary HTTPS URL so connected duelists and developers can immediately access the catalog over SSL.

---

## 🦆 2. DuckDNS Dynamic DNS Synchronizer

Queries discovery endpoints for the host's current public IPv4 address and issues an authenticated HTTPS update request to the DuckDNS API.

### A. Linux / Cloud VPS (Cron)

```bash
crontab -e
# Add the following line:
*/5 * * * * /home/ubuntu/yugioh-server/packages/server/scripts/update_duckdns.sh >/dev/null 2>&1
```

### B. Windows (Task Scheduler)

```cmd
schtasks /create /tn "DuckDNS_AutoUpdate" /tr "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\path\to\packages\server\scripts\update_duckdns.ps1" /sc minute /mo 5 /f
```
