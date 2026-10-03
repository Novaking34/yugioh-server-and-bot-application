# 🌌 The Land of Kustomazi — Discord Bot Platform

> **Modular, Enterprise-Grade Discord Bot for Custom Card Dueling, Competitive ELO Rankings, and Story Mode RPG Progression.**

---

## 🏛️ System Architecture

The bot follows a strict **Separation of Concerns** using a three-tier architecture:

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                       Discord Presentation Layer                         │
│   (Interactions, Slash Commands, Modals, Views, Buttons, Embeds)        │
│   cogs.general | cogs.cardpool | cogs.deckbuilding | cogs.duel_engine    │
│   cogs.ranking | cogs.story    | cogs.lore         | cogs.admin          │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼─────────────────────────────────────┐
│                         Service & Domain Layer                           │
│   (Business Logic, Calculations, Telemetry, Validations, State Mgmt)    │
│   • CardService   : Card lookup, FTS autocomplete, usage statistics      │
│   • DeckService   : Deck assembly, 34-card Set 1 validation, copy/export │
│   • RatingService : FIDE ELO engine, tier brackets, match logging        │
│   • StoryService  : Lore campaign chapters, stage dialogue, progression  │
│   • DuelManager   : Live session registry, recovery & safe termination   │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼─────────────────────────────────────┐
│                          Data & Telemetry Layer                          │
│   SQLite Database: `production/main/web/ygo_story.db`                    │
│   Tables: custom_cards, decks, player_decks, player_ratings,             │
│           duel_matches, card_usage_stats, story_chapters, story_stages,  │
│           player_story_progress, lore_arcs, factions, characters         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Directory Layout

```bash
production/main/discord_bot/
├── bot.py                  # Orchestrator with structured logging, lifecycle hooks & error handler
├── bot_config.py           # Configuration bridge to centralized config subsystem
├── utils.py                # Card frame palettes, status embeds, rating badges & dialog builders
├── services/               # Decoupled Domain & Database Services
│   ├── __init__.py
│   ├── card/               # Modular Card subsystem (foundation, domain discovery, autocomplete, analytics, mutators)
│   ├── card.py             # Root Card service entry point & translation bridge
│   ├── deck/               # Modular Deck subsystem (foundation, domain storage, slots, story, YDK, visual)
│   ├── deck.py             # Root Deck service entry point & translation bridge
│   ├── rating_service.py   # ELO calculation, rank brackets & leaderboard generation
│   ├── story_service.py    # Story chapters, stage encounters, dialogue & rewards
│   └── duel_service.py     # In-memory live session registry & recovery tools
├── cogs/                   # Discord Slash Command Modules
│   ├── general.py          # /ping, /info, /rules, /board, /server_status
│   ├── cardpool.py         # /card, /cardpool, /card_stats, /meta, /random_card, /recent_cards
│   ├── deckbuilding.py     # /deck_add, /deck_remove, /mydeck, /deck_clear, /load_character_deck
│   ├── duel_engine.py      # /duel (Interactive live matches with Ranked & Casual options)
│   ├── ranking.py          # /rank, /leaderboard, /rank_tiers
│   ├── story.py            # /story, /story_stages, /story_progress (RPG Campaign)
│   ├── lore.py             # /lore, /stats
│   ├── server_tools.py     # /coinflip, /dice, /duel_role, /clear_messages
│   └── admin.py            # /admin sync_cards, reload, status, reset_duel, reset_story
└── README.md               # This documentation
```

---

## 🃏 Set 1: The Land of Kustomazi Expansions & Cardpool

* **Total Cardpool Size**: 64 unique custom cards (`TLOK-001` through `TLOK-064`).
* **Archetype 1: The Creators of Kustomazi** (`TLOK-001` to `TLOK-014`):
  * Primordial creation deities, high-stat DIVINE Divine-Beasts, and void recursion led by **ProfessorSeanEX**.
  * Pre-built Deck: *Kasutamaiza - Creation Control* (34 Main Deck + 6 Extra Deck cards).
* **Archetype 2: The LeSpookiest Night** (`TLOK-015` to `TLOK-064`):
  * In a quiet town on Halloween night, costumed youths trick-or-treat under bright streetlights. Ordinary mortals enter as Normal Monsters and awaken into supernatural entities via Gemini summons, Trick-or-Treat Counters, and Synchro/Link evolutions led by **Magnolia, Ghost of LeSpookie Street**.
  * Pre-built Deck: *LeSpookie Singles* (36 Main Deck + 14 Extra Deck cards, 50 total).
* **Validation & UI**: The `DeckService` and `/mydeck` command recognize both archetypes, accommodating custom early-access deck construction and displaying informative status badges without rejecting decks.

---

## 🎮 Command Reference

### 1. Card & Cardpool (`cogs.cardpool`)

| Command | Parameters | Description |
| :--- | :--- | :--- |
| `/card` | `<name>` (Autocomplete) | Inspect card with Duelingbook art, stats, and lore. |
| `/cardpool` | None | Full catalog of Set 1 cards categorized by type. |
| `/card_types` | `[category]` | Guide to Monster, Spell, and Trap types, speeds, 26 races, 7 attributes, and Levels/Ranks. |
| `/card_stats` | `<name>` | View live telemetry: inclusion count, draws, plays, and win rate. |
| `/meta` | None | Top 5 cards by deck popularity and win rate in the server. |
| `/random_card` | None | Showcase a random card from the live pool. |
| `/recent_cards` | `[limit]` | View recently registered custom cards. |

### 2. Deckbuilding (`cogs.deckbuilding`)

| Command | Parameters | Description |
| :--- | :--- | :--- |
| `/deck_add` | `<card_name>`, `[quantity=1-3]` | Add 1–3 copies of a custom card to your active deck. |
| `/deck_remove` | `<card_name>` | Remove a card from your personal deck. |
| `/mydeck` | None | Display your deck list with Set 1 alpha validation. |
| `/deck_clear` | None | Empty your active deck. |
| `/load_character_deck` | `<character>` | Copy a pre-built story deck (e.g. *Kasutamaiza - Creation Control*). |

### 3. Manual PvP Duels (`cogs.duel_engine`)

| Command | Parameters | Description |
| :--- | :--- | :--- |
| `/duel` | `@opponent` | Challenge another duelist to a live manual duel. Opponent chooses **⚔️ Ranked** (ELO stakes) or **🎮 Casual** (Practice). |
| `/duel_manual` | `@opponent` | Explicit alias for the manual PvP duel system. |

**Manual In-Duel Action Controls (Natural Yu-Gi-Oh! RNG & Real Field Physics)**:

* **🎴 View Hand**: Displays secret hand privately via ephemeral embed.
* **🃏 Draw Card**: Draws 1 card from player's real deck into hand with true RNG and logs telemetry.
* **⚡ Summon**: Select a monster from hand with Level & Tribute checks (0 for Lv 1-4, 1 for Lv 5-6, 2 for Lv 7+) and place into an open MMZ.
* **⚔️ Attack**: Declares an attack executing official Yu-Gi-Oh! battle damage calculation (Attack vs Attack, Attack vs Defense, Direct Attack).
* **🗺️ Duel Field**: Displays live ASCII playmat with all 5 MMZs, 5 STZs, Field Spells, hands, decks, GY, and banished zones.
* **🌀 Mill 1 Card**: Sends the top card of your deck directly to Graveyard with true RNG.
* **🪙 Coin Toss**: Flips a coin (Heads/Tails) for effect resolution.
* **🎲 Roll d6**: Random six-sided die roll for effect resolution.
* **❤️ -1000 LP**: Fast combat damage button.
* **❤️ Custom LP**: Modal input allowing arbitrary damage or healing with reason string.
* **⏳ End Turn**: Passes priority and triggers automatic turn draw for opponent.
* **🏳️ Surrender**: Concedes match to opponent and triggers ELO/telemetry settlement.

### 4. Competitive ELO & Rankings (`cogs.ranking`)

| Command | Parameters | Description |
| :--- | :--- | :--- |
| `/rank` | `[user]` | View official Duelist License card, division, ELO, win rate, and streak. |
| `/leaderboard` | `[season]` | Server leaderboard displaying top duelists ordered by ELO. |
| `/rank_tiers` | None | View division brackets and badges. |

#### Division Brackets

| Tier | Minimum ELO | Badge |
| :--- | :---: | :---: |
| **King of Games** | 2100+ | 👑 |
| **Diamond Duelist** | 1900 | 💠 |
| **Platinum Duelist** | 1700 | 💎 |
| **Gold Duelist** | 1500 | 🥇 |
| **Silver Duelist** | 1300 | 🥈 |
| **Bronze Duelist** | 1100 | 🥉 |
| **Novice Duelist** | < 1100 (Placement: 1200) | 🔰 |

### 5. Story Mode RPG & Lore Encounters (`cogs.story`)

| Command | Parameters | Description |
| :--- | :--- | :--- |
| `/story` | None | Interactive story hub with narrative dialog and "Begin Story Duel" button. |
| `/story_duel` | None | Direct shortcut to launch the story duel encounter for your active objective. |
| `/story_stages` | None | View campaign chapter roadmap with objective status. |
| `/story_progress` | None | View story victories, cleared stages, and earned lore titles. |

**Dual-Mode Story Duel Architecture (Zero Hardcoding)**:
Story scenarios are loaded dynamically from structured JSON files (`production/main/discord_bot/data/story/*.json`) and stored in SQLite. Writers and game designers can author or modify encounters without changing Python bot code.

* **📜 SCRIPTED Encounters** (e.g. Stage 1-1, 1-3): The opponent follows a database-loaded narrative script with tailored dialogue quotes, specific boss moves, and HP threshold responses (such as boss dialogue triggered at 4000 LP).
* **🤖 DYNAMIC AI Encounters** (e.g. Stage 1-2): The bot does not use a fixed script. It shuffles an authentic character deck with true RNG, draws cards, evaluates its hand, summons monsters, casts spells, and computes combat damage based on the monsters actually summoned!
* **Natural Duel RNG**: In both modes, the human duelist plays an actual duel with 8000 LP, draws cards from their shuffled deck with RNG, inspects their secret hand, summons monsters onto the field, attacks using their monster's actual ATK stat, adjusts LP for card effects, rolls dice, flips coins, and mills cards to the GY.

#### Chapter 1: The Genesis of Kustomazi

1. **Stage 1**: *Whispers of the Primordial Void* vs **Echo of the Void** [Scripted] (Reward: *Void Walker* title & `TLOK-002`).
2. **Stage 2**: *Rites of the Celestial Temple* vs **Acolytes of Kustomazi** [Dynamic AI] (Reward: *Temple Guardian* title & `TLOK-011`).
3. **Stage 3**: *Trial of the Supreme Architect* vs **ProfessorSeanEX** [Scripted] (Reward: *Architect's Champion* title & `TLOK-001`).

### 6. Administration & Recovery (`cogs.admin`)

| Command | Parameters | Description |
| :--- | :--- | :--- |
| `/admin sync_story` | None | Scan `data/story/*.json` scenario files and refresh all story chapters/stages in DB live with zero downtime. |
| `/admin sync_cards` | None | Compile `custom_cards.cdb` and regenerate Lua scripts live. |
| `/admin reload` | `<cog_name>` | Hot-reload bot extension without downtime (e.g. `cogs.story`). |
| `/admin status` | None | View live latency, active duels, and loaded cogs. |
| `/admin reset_duel` | `@user` | Safely clear a stuck in-memory duel session for a user. |
| `/admin clear_all_duels` | None | Emergency purge for all active duel sessions. |
| `/admin reset_story` | `@user`, `[stage]` | Adjust or reset a player's story progress. |
| `/admin db_stats` | None | Database record counts and storage diagnostics. |

---

## 🛠️ Observability & Resilience

* **Structured Logging**: All bot events, cog loads, command executions, and errors stream through `config.logging` (`logs/bot.log`).
* **Incident Tracking**: Any unhandled slash command exception generates a unique 8-character Incident ID (e.g. `[Incident #a1b2c3d4]`) logged with full traceback, while presenting a graceful explanation to the user.
* **Zero Downtime Reloading**: Cogs can be hot-reloaded using `/admin reload <cog>` without interrupting other active features.
* **Crash-Resistant State**: All competitive rankings, player decks, telemetry, and story progression persist in SQLite, ensuring zero state loss on server restarts.
