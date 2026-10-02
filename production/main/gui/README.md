# 🖥️ Host Administrative GUI Subsystem (`production/main/gui/`)

The `production/main/gui/` package houses the desktop administration tools, control panels, configuration wizards, and UI assets for the Yu-Gi-Oh! platform.

---

## 📁 Components

| Module | Purpose |
| :--- | :--- |
| [`app.py`](file:///home/professorseanex/yugioh-server/production/main/gui/app.py) | Full implementation of the native Tkinter Platform Manager control panel |
| [`setup_wizard.py`](file:///home/professorseanex/yugioh-server/production/main/gui/setup_wizard.py) | Interactive setup wizard (supporting both dark Tkinter GUI and headless terminal CLI) |
| [`assets/`](file:///home/professorseanex/yugioh-server/production/main/gui/assets/) | Icons and graphics (`icon.png`) |

---

## 🚀 Launching

```bash
# Launch Desktop Platform Manager GUI:
./manage.sh app
# Or directly:
python3 production/main/app.py

# Launch Setup Wizard:
python3 production/main/setup_wizard.py
# Or force headless CLI mode on a VPS:
python3 production/main/setup_wizard.py --cli
```
