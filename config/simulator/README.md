# 🎮 Duel Simulator Engine Configuration Subsystem (`config/simulator/`)

This directory contains the operational parameters, chat filters, administrative privileges, and automated broadcasts used by the live `ocgcore` rule-enforcing duel simulator container (`professorseanex/ygoserver:latest`).

---

## 📁 File Manifest

| File | Purpose | Docker Container Mount |
| --- | --- | --- |
| [`config.json`](file:///home/professorseanex/yugioh-server/config/simulator/config.json) | Master duel engine configuration (ports, hand sizes, LP, timers, banlists) | `/ygoserver/config/config.json` |
| [`admin_user.json`](file:///home/professorseanex/yugioh-server/config/simulator/admin_user.json) | Administrative usernames and permissions for in-game `/op` management | `/ygoserver/config/admin_user.json` |
| [`badwords.json`](file:///home/professorseanex/yugioh-server/config/simulator/badwords.json) | In-game profanity and harassment filter wordlist | `/ygoserver/config/badwords.json` |
| [`dialogues.json`](file:///home/professorseanex/yugioh-server/config/simulator/dialogues.json) | Automated system announcements, room chat notifications, and match outcomes | `/ygoserver/config/dialogues.json` |
| [`tips.json`](file:///home/professorseanex/yugioh-server/config/simulator/tips.json) | Gameplay tips and ruling hints displayed in duel waiting rooms | `/ygoserver/config/tips.json` |
| [`README.md`](file:///home/professorseanex/yugioh-server/config/simulator/README.md) | Subsystem documentation (this file) | — |

---

## ⚙️ Configuration Files Detail

### 1. `config.json` — Duel Engine Parameters

Defines the core operational parameters for the duel server:

- `serverport`: The TCP socket port where game clients connect (default: `7911`).
- `room_port`: The HTTP / WebSocket room manager dashboard port (default: `7922`).
- `start_lp`: Starting Life Points (default: `8000`).
- `start_hand`: Opening hand card count (default: `5`).
- `draw_count`: Standard draw phase count (default: `1`).
- `time_limit`: Match turn timer in seconds (default: `180`).
- `default_rule`: Default duel Master Rule (Rule 5: Revision Master Rule 2020).

### 2. `admin_user.json` — Moderator Privileges

Contains administrative accounts authorized to execute server management commands inside match rooms (e.g., `/kick`, `/ban`, `/reload`, `/msg`).

### 3. `badwords.json` — Chat Filtering

Defines blocked strings and patterns. Any player sending messages matching these patterns in public lobbies or duel rooms will have their text redacted or muted.

### 4. `dialogues.json` — System Broadcasts

Localizable text templates rendered when events trigger in the engine:

- Player joining or leaving a room.
- Match start and end conditions (surrender, deck out, time out, LP 0).
- Server maintenance warnings and periodic broadcasts.

### 5. `tips.json` — Loading Screen Hints

An array of string tips cycled randomly to players while waiting for opponents or during deck validation.

---

## 🐳 Container Mount Integration

The simulator container in [`docker-compose.yml`](file:///home/professorseanex/yugioh-server/docker-compose.yml) mounts this directory directly:

```yaml
volumes:
  - ./production/main/simulator/config:/ygoserver/config:rw
```

Because `production/main/simulator/config` is a symlink pointing to `../../../config/simulator`, any changes made to files in this directory are reflected immediately inside the running container upon server restart:

```bash
./manage.sh restart
```
