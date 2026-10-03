# Yu-Gi-Oh! Deck Subsystem Architecture

## 1. Architectural Philosophy: Top-Down & Bottom-Up Modularization

The Deck Subsystem is engineered following principles of modular systems programming (analogous to C/C++ header contracts `.h` and compilation units `.c`). Rather than a monolithic single-file design, logic is organized into hierarchical layers:

- **Top-Down (Orchestration & Facade)**: Provides the public API, orchestrating database transactions, Discord cog interactions, and duel engine integrations.
- **Bottom-Up (Foundation & Primitives)**: Zero-dependency math, type contracts, Master Rule constants, and card classification rules that form the base upon which all higher operations build.
- **Middle Tier (Domain Engines & Handlers)**: Decoupled domain engines each responsible for a distinct functional section (Cardpool, Storage/CRUD, Named Slots, Story Progression, and .YDK serialization).

---

## 2. Directory Hierarchy

```bash
production/main/discord_bot/services/deck/
├── __init__.py               # Top-level root module exposing public API & re-exports
├── core.py                   # Core DeckService orchestrator unit
├── README.md                 # Subsystem Architecture Documentation
│
├── foundation/               # Bottom-Up Foundation (Zero-dependency primitives)
│   ├── __init__.py           # Re-exports foundation types and primitives
│   ├── constants.py          # "Header" (.h): Master Rule limits, hand boundaries, zones, banlists
│   ├── types.py              # "Header" (.h): TypedDict structs (CardDict, DeckPartition, etc.)
│   ├── classifier.py         # Dynamic card type classification & PSCT zone detectors
│   └── math.py               # Hypergeometric probabilities & Fisher-Yates PRNG fair shuffle
│
├── domain/                   # Domain Logic & Subsystem Engines
│   ├── __init__.py           # Re-exports domain engine procedures
│   ├── cardpool.py           # Section 3.1: Live cardpool queries, mechanics & zone telemetry
│   ├── storage.py            # Section 3.2: Player active deck CRUD & capacity enforcement
│   ├── slots.py              # Section 3.3: Multi-deck named slots (20-slot ceiling per user)
│   ├── story.py              # Section 3.4: Pre-constructed story decks & AI ELO matchmaking
│   └── ydk.py                # Section 3.5: EDOPro / Project Ignis .YDK serialization & ingestion
│
└── visual/                   # Visual & Tactical Presentation Layer
    ├── __init__.py           # Re-exports visual and analytical components
    ├── analytics.py          # Section 4: Tactical deck profiling & MR5 legality validation
    └── canvas.py             # Visual Pillow canvas renderer (10-column DuelingBook layout)
```

---

## 3. Layer Breakdown & Section Mapping

### 3.1 Bottom-Up Foundation (`core/`)

| File | Purpose | Key Symbols |
| :--- | :--- | :--- |
| `constants.py` | Official Yu-Gi-Oh! Master Rule constants and zone definitions. | `STANDARD_MIN_MAIN_DECK (40)`, `STANDARD_MAX_MAIN_DECK (60)`, `STANDARD_MAX_EXTRA_DECK (15)`, `MAX_USER_DECK_SLOTS (20)`, `BANLIST_LIMITS` |
| `types.py` | C-style struct equivalents using Python `TypedDict`. | `CardDict`, `DeckPartition`, `ParsedYDK`, `SavedDeckSlot`, `StoryDeckRecord`, `DeckAnalysisResult`, `LegalityResult` |
| `classifier.py` | Card type resolution, summoning rules, and PSCT pattern detectors. | `is_extra_deck_card`, `is_ritual_monster`, `get_tribute_cost`, `is_field_spell`, `has_field_awareness`, `has_graveyard_interaction` |
| `math.py` | Probability calculations, deckout verification, and fair shuffling. | `calculate_opening_hand_prob`, `calculate_combo_prob`, `fair_shuffle`, `simulate_fair_draw`, `validate_hand_size` |

### 3.2 Domain Subsystem Engines (`domain/`)

| Section | Module | Primary Responsibilities |
| :--- | :--- | :--- |
| **3.1** | `cardpool.py` | Dynamically queries `custom_cards` for live telemetry, booster rarity breakdowns, mechanics counts, and field engine awareness. |
| **3.2** | `storage.py` | Manages player personal decks in `player_decks`, clamps deck capacity ($\le 60$ Main, $\le 15$ Extra), updates card usage telemetry, and partitions decks with MR5 status. |
| **3.3** | `slots.py` | Manages named deck profiles in `player_saved_decks`, enforces the 20-slot limit per player, and handles saving, loading, listing, and renaming slots. |
| **3.4** | `story.py` | Loads pre-constructed story decks (`decks` and `deck_cards`), computes AI ELO matchmaking dynamically, and copies story decks to player active slots. |
| **3.5** | `ydk.py` | Handles bidirectional EDOPro / Project Ignis `.ydk` serialization, UTF-8 BOM handling, passcode validation, and atomic deck ingestion. |

### 3.3 Visual & Analytical Presentation (`visual/`)

| Component | Module | Responsibilities |
| :--- | :--- | :--- |
| **Analytics (4)** | `analytics.py` | Tactical curve analysis (Levels 1-4, 5-6, 7+), extra summoning mechanics distribution, attributes, species, and Master Rule legality verification. |
| **Visual Canvas** | `canvas.py` | Pillow-based 10-column visual canvas renderer matching DuelingBook / EDOPro standards with tournament header banners. |

### 3.4 Core Orchestration (`core.py`)

- `core.py` defines the [`DeckService`](file:///home/professorseanex/yugioh-server/production/main/discord_bot/services/deck/core.py) class. It acts as the primary translation unit, holding the database path, lifecycle methods (`ensure_tables`), and orchestrating domain engine operations.
- `services/deck.py` and `services/deck/__init__.py` provide full re-exports (`from services.deck import DeckService, ...`).

---

## 4. Usage Examples

### Using the High-Level Facade

```python
from services.deck import DeckService

service = DeckService()

# 3.1 Cardpool telemetry
stats = await service.get_cardpool_stats()

# 3.2 Player deck partition & legality
partition = await service.get_player_deck_partitioned(user_id="123456789")

# 3.3 Save named slot
await service.save_named_deck(user_id="123456789", deck_name="Genesis Control")

# 3.5 Ingest standard .YDK
success, msg, cards_added = await service.import_from_ydk(user_id="123456789", ydk_text=ydk_content)
```

### Using Core Primitives Directly

```python
from services.deck.core.math import calculate_opening_hand_prob
from services.deck.core.constants import STANDARD_MIN_MAIN_DECK

# Calculate 5-card opening hand probability of drawing 1 of 3 Field Spells in a 40-card deck
prob = calculate_opening_hand_prob(deck_size=40, target_count=3, hand_size=5, min_hits=1)
print(f"Opening hand probability: {prob}%")
```
