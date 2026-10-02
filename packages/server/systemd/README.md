# ⚙️ 24/7 Background Systemd Daemons (`packages/server/systemd/`)

This directory contains Linux `systemd` service definitions and installation scripts to ensure all server components run continuously, auto-recover from unexpected exceptions, and start automatically upon system boot.

---

## 📁 File Manifest

| Service Unit | Component Description | Port(s) | Dependencies |
| --- | --- | --- | --- |
| [`ygo-simulator.service`](file:///home/professorseanex/yugioh-server/packages/server/systemd/ygo-simulator.service) | ocgcore live duel container via Docker Compose | TCP 7911 / 7922 | `docker.service` |
| [`ygo-web.service`](file:///home/professorseanex/yugioh-server/packages/server/systemd/ygo-web.service) | FastAPI Web Catalog Dashboard & REST API | TCP 8000 | `network.target` |
| [`ygo-bot.service`](file:///home/professorseanex/yugioh-server/packages/server/systemd/ygo-bot.service) | The Great Kasutamaiza modular Discord bot | Outbound Gateway | `network.target`, `ygo-simulator.service` |
| [`ygo-tunnel.service`](file:///home/professorseanex/yugioh-server/packages/server/systemd/ygo-tunnel.service) | Optional cloudflared Quick Tunnel daemon | HTTPS Edge | `ygo-web.service` |
| [`install_services.sh`](file:///home/professorseanex/yugioh-server/packages/server/systemd/install_services.sh) | Automated installer script that copies and enables units | — | Root / sudo |

---

## 🚀 Installation & Activation

To install and enable the services on any Ubuntu or Debian host:

```bash
cd packages/server/systemd

# Make installer executable
chmod +x install_services.sh

# Install core services (simulator, web catalog, discord bot)
sudo ./install_services.sh

# Or install including the quick tunnel daemon
sudo ./install_services.sh --with-tunnel
```

The installer dynamically replaces path and user placeholders with the actual active host user (`$SUDO_USER`) and repository path (`$BASE_DIR`).

---

## 🛠️ Service Management Commands

```bash
# Start all services
sudo systemctl start ygo-simulator ygo-web ygo-bot

# Restart services after a git pull or configuration change
sudo systemctl restart ygo-web ygo-bot

# Check active health and status
sudo systemctl status ygo-simulator ygo-web ygo-bot --no-pager

# Stream live console logs
journalctl -u ygo-bot -f
journalctl -u ygo-web -f
```
