# 🌐 DNS & Domain Configuration Subsystem (`config/dns/`)

This directory contains the canonical DNS zone configuration files for the **thelandofkustomazi.com** root domain and all platform subdomains.

---

## 📁 File Manifest

| File | Format | Purpose |
| --- | --- | --- |
| [`thelandofkustomazi.com.zone`](file:///home/professorseanex/yugioh-server/config/dns/thelandofkustomazi.com.zone) | RFC 1035 / BIND 9 | Master DNS zone file compatible with Cloudflare DNS Import, BIND9, and NSD |
| [`README.md`](file:///home/professorseanex/yugioh-server/config/dns/README.md) | Markdown | Subsystem documentation (this file) |

---

## 🗺️ Domain Routing & Proxy Architecture

The Yu-Gi-Oh! platform utilizes a hybrid architecture requiring **two distinct routing behaviors** in Cloudflare:

```text
                                  ┌───────────────────────────────┐
                                  │   thelandofkustomazi.com      │
                                  └──────────────┬────────────────┘
                                                 │
                   ┌─────────────────────────────┴─────────────────────────────┐
                   ▼                                                           ▼
       [HTTP/HTTPS Web Traffic]                                    [Raw TCP Game Sockets]
       Port 8000 (Catalog & API)                                   Port 7911 / 7922 (Simulator)
                   │                                                           │
                   ▼                                                           ▼
┌──────────────────────────────────────┐                   ┌──────────────────────────────────────┐
│ Cloudflare Zero Trust Named Tunnel   │                   │ Direct Public IP (DNS-Only / Grey)  │
│ CNAME -> cfargotunnel.com            │                   │ A Record -> 147.224.147.30           │
│ ✅ Orange Cloud (Proxied)            │                   │ ⚠️ GREY CLOUD (Unproxied / Raw TCP)  │
│ • SSL Termination & DDoS Protection  │                   │ • Raw game client binary protocol    │
│ • Zero open web ports on host VM     │                   │ • Bypasses Cloudflare HTTP proxy     │
└──────────────────────────────────────┘                   └──────────────────────────────────────┘
```

---

## 📋 DNS Records Breakdown

### 1. Web Catalog & REST API (HTTP / HTTPS)

- **`@` (Apex)**: `CNAME c346aa27-b4c1-41ba-815c-f66b2b84243b.cfargotunnel.com.` (**Proxied / Orange Cloud**)
- **`www`**: `CNAME c346aa27-b4c1-41ba-815c-f66b2b84243b.cfargotunnel.com.` (**Proxied / Orange Cloud**)

### 2. Live Duel Simulator (Raw TCP Game Socket)

- **`play`**: `A 147.224.147.30` (**DNS-Only / Grey Cloud**)
- **`sim`**: `A 147.224.147.30` (**DNS-Only / Grey Cloud**)

> [!CAUTION]
> The `play` and `sim` records **MUST remain DNS-Only (Grey Cloud)** in Cloudflare. Cloudflare's standard CDN proxy does not support arbitrary non-HTTP raw TCP sockets, and proxying Port 7911 will cause game client connections to fail with `Connection Refused` or `Handshake Timeout`.

### 3. Dynamic DNS Fallback

- Dynamic IP synchronization is managed via DuckDNS at `thelandofkustomazi.duckdns.org`.
- In the event of an IP change on the VPS, the cron job [`packages/server/scripts/update_duckdns.sh`](file:///home/professorseanex/yugioh-server/packages/server/scripts/update_duckdns.sh) automatically points DuckDNS to the new public IP.

---

## 📥 How to Import into Cloudflare

1. Log in to the [Cloudflare Dashboard](https://dash.cloudflare.com/).
2. Select your domain (`thelandofkustomazi.com`).
3. Navigate to **DNS -> Records**.
4. Click **Advanced -> Import and Export -> Import**.
5. Upload [`thelandofkustomazi.com.zone`](file:///home/professorseanex/yugioh-server/config/dns/thelandofkustomazi.com.zone).
6. Verify that `@` and `www` are **Orange Cloud (Proxied)**, and `play` and `sim` are **Grey Cloud (DNS-Only)**.
