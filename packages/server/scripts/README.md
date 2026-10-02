# 🛠️ Server Management Scripts (`packages/server/scripts/`)

This directory contains standalone automation scripts for managing networking, dynamic DNS, and secure edge tunneling for the Yu-Gi-Oh! platform.

---

## 📁 Script Manifest

| Script | Purpose | Typical Execution |
| --- | --- | --- |
| [`setup_cloudflare_tunnel.sh`](file:///home/professorseanex/yugioh-server/packages/server/scripts/setup_cloudflare_tunnel.sh) | Connects local FastAPI catalog (Port 8000) to Cloudflare edge | Manual / Automated |
| [`update_duckdns.sh`](file:///home/professorseanex/yugioh-server/packages/server/scripts/update_duckdns.sh) | Synchronizes host public WAN IP with DuckDNS dynamic DNS | Cron Job (every 5 min) |

---

## 🌐 1. Cloudflare Tunnel Manager (`setup_cloudflare_tunnel.sh`)

Supports both zero-configuration ephemeral tunnels and production 24/7 Named Tunnels:

```bash
# 1. Automatic mode (uses CLOUDFLARE_TUNNEL_TOKEN from .env if present):
./setup_cloudflare_tunnel.sh

# 2. Ephemeral Quick Tunnel (generates free https://*.trycloudflare.com URL):
./setup_cloudflare_tunnel.sh --quick

# 3. Explicit Named Tunnel with token:
./setup_cloudflare_tunnel.sh --token <YOUR_CLOUDFLARE_TOKEN>
```

When a quick tunnel starts, it automatically updates `config/client/config.json` with the temporary HTTPS URL so connected duelists and developers can immediately access the catalog over SSL.

---

## 🦆 2. DuckDNS Dynamic DNS Synchronizer (`update_duckdns.sh`)

Queries `ifconfig.me` for the host's current public IPv4 address and issues an authenticated HTTPS update request to the DuckDNS API.

### Cron Setup on Cloud VPS

To ensure the fallback hostname `thelandofkustomazi.duckdns.org` remains locked to the cloud VPS:

```bash
crontab -e
# Add the following line:
*/5 * * * * /home/ubuntu/yugioh-server/packages/server/scripts/update_duckdns.sh >/dev/null 2>&1
```
