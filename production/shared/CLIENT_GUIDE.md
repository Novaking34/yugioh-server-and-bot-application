# 🌌 Yu-Gi-Oh! Player & Client Connection Guide

Welcome to the custom Yu-Gi-Oh! duel server! This folder contains everything you need to play with our custom card pool in **EDOPro (Project Ignis)** or compatible YGOPro clients.

---

## ⚡ Quick 1-Click Install

### Linux / macOS

Run the client installer from this directory:

```bash
./install_client.sh
```

### Windows

Open PowerShell or Command Prompt in this folder and run:

```powershell
python sync_client.py
```

The script will automatically detect your EDOPro installation directory and copy:

1. `expansions/custom_cards.cdb` -> `<EDOPro>/expansions/`
2. `expansions/scripts/*.lua` -> `<EDOPro>/expansions/scripts/`
3. `decks/*.ydk` -> `<EDOPro>/deck/`

---

## 🎮 How to Connect & Duel Online

1. Open **EDOPro**.
2. Click **Multiplayer** -> **Duel Online**.
3. Select **Direct Connect / IP Connection**:
   - **Host:** Enter the server IP address (or `localhost` if running locally).
   - **Port:** `7911`
4. Enter any room name or leave blank for random matchmaking.
5. Select your custom deck (pre-made decks are loaded from the `decks/` folder) and start dueling!

---

## 📂 Manual Installation (Alternative)

If you prefer to copy the files manually:

1. Copy `expansions/custom_cards.cdb` into your EDOPro `expansions/` folder.
2. Copy all files inside `expansions/scripts/` into your EDOPro `expansions/scripts/` folder.
3. (Optional) Copy `.ydk` deck files from `decks/` into your EDOPro `deck/` folder.
4. Restart EDOPro.

---

## 🌐 Web Catalog & Lore

You can also browse all custom cards, faction lore, and deck profiles in your browser at:
`http://<SERVER_IP>:8000`
