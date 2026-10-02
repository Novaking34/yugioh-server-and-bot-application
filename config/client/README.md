# 🌐 Client Connection Manifest Subsystem (`config/client/`)

This directory contains the canonical connection manifest and configuration parameters used by client applications, desktop launchers, and players connecting to the live duel server.

---

## 📁 File Manifest

| File | Purpose |
| --- | --- |
| [`config.json`](file:///home/professorseanex/yugioh-server/config/client/config.json) | Canonical JSON manifest containing live duel endpoints and update URLs |
| [`README.md`](file:///home/professorseanex/yugioh-server/config/client/README.md) | Subsystem documentation (this file) |

---

## ⚙️ Configuration Schema Reference (`config.json`)

```json
{
  "server_name": "The Great Kasutamaiza Duel Server",
  "server_host": "thelandofkustomazi.com",
  "server_port": 7911,
  "room_port": 7922,
  "fallback_host": "thelandofkustomazi.duckdns.org",
  "web_catalog_url": "https://thelandofkustomazi.com",
  "expansions_update_url": "https://thelandofkustomazi.com/api/expansions/download"
}
```

### Field Definitions

- **`server_name`** *(string)*: Display name shown in player client server selection menus.
- **`server_host`** *(string)*: Primary hostname for raw TCP game client connections (e.g. EDOPro / YGOPro).
- **`server_port`** *(integer)*: Primary game server TCP port (`7911`).
- **`room_port`** *(integer)*: Web Room Manager dashboard & WebSocket spectator feed TCP port (`7922`).
- **`fallback_host`** *(string)*: DuckDNS dynamic DNS failover hostname (`thelandofkustomazi.duckdns.org`).
- **`web_catalog_url`** *(string)*: Public HTTPS endpoint for browsing custom card lore and archetypes.
- **`expansions_update_url`** *(string)*: REST API endpoint where client download utilities pull the latest `custom_cards.cdb` and Lua script bundle.

---

## 🔗 Zero-Drift Symlink Architecture

To ensure client packages and production shared assets never drift from this single source of truth, symlinks are maintained across the repository:

- `packages/client/config.json` ➔ `../../config/client/config.json`
- `production/shared/config.json` ➔ `../../config/client/config.json`

When building client release packages (`./manage.sh package`), this manifest is bundled directly into `dist/ygo-client-package.zip`.
