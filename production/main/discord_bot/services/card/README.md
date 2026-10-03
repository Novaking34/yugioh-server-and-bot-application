# Modular Custom Card Service Architecture (`services.card`)

## Overview

The `services.card` package is designed following a **Top-Down / Bottom-Up C-Style Compilation Unit Architecture** mirroring the modular standard established in `services.deck`.

```bash
services/card/
├── README.md                  # Architectural documentation & API guide
├── __init__.py                # Package root & unified public manifest
├── core.py                    # Top-Down Orchestrator Engine (CardService)
│
├── foundation/                # Bottom-Up Primitives & Invariants ("Headers")
│   ├── __init__.py            # Foundation re-exports
│   ├── constants.py           # Query limits, frame constants, bitmasks & projections
│   ├── types.py               # C-Style Struct contracts (TypedDicts)
│   └── formatters.py          # Autocomplete choice formatting & label sanitization
│
└── domain/                    # Operational Subsystems ("Translation Units")
    ├── __init__.py            # Domain re-exports
    ├── discovery.py           # Sub-Block 3.1: Card Discovery & Direct Lookups
    ├── autocomplete.py        # Sub-Block 3.2: Real-time Autocomplete Engine
    ├── analytics.py           # Sub-Block 3.3: Telemetry & Meta Analytics Engine
    └── mutators.py            # Sub-Block 3.4: Live Duel Event Tracking Mutators
```

---

## Subsystems

### 1. Foundation (`foundation/`)

- **`constants.py`**: Declares query limits (`DEFAULT_AUTOCOMPLETE_LIMIT = 20`, `DEFAULT_RECENT_LIMIT = 10`, `DEFAULT_META_LIMIT = 5`), primary frames (`CARD_TYPE_MONSTER`, `CARD_TYPE_SPELL`, `CARD_TYPE_TRAP`), monster attributes, canonical projections (`CARD_RECORD_PROJECTION`), and sentinels (`STAT_UNKNOWN = -2`).
- **`types.py`**: Defines strict TypedDict structs:
  - `CardRecordDict`
  - `CardSummaryDict`
  - `CardUsageStatsDict`
  - `MetaOverviewDict`
  - `ArchetypeMetaDict`
  - `CardpoolTelemetrySummaryDict`
- **`formatters.py`**: Implements single-line Discord autocomplete choice string generators strictly enforcing Discord's 100-character ceiling with rich frame mechanics tags.

### 2. Domain Subsystems (`domain/`)

- **`discovery.py`**:
  - `get_card_by_id(db_path, card_id)`: $O(1)$ indexed passcode lookup.
  - `get_card_by_set_number(db_path, set_number)`: Exact set number lookup.
  - `get_card_by_query(db_path, query)`: Multi-strategy fuzzy search with composite and bracketed label sanitization.
  - `get_cards_by_filter(db_path, ...)`: Multi-criteria mechanical filtering.
  - `get_all_cards_partitioned(db_path)`: Exports cardpool partitioned into Main Deck vs Extra Deck.
- **`autocomplete.py`**:
  - `search_cards(db_path, current, limit, ...)`: Real-time ranked suggestions with empty-query Set ordering and contextual scoping.
- **`analytics.py`**:
  - `get_card_usage_stats(db_path, card_id)`: Telemetry stats with calculated `win_rate` and `play_to_draw_ratio`.
  - `get_meta_overview(db_path, limit, ...)`: 5-axis meta overview (`most_popular`, `most_played`, `most_victorious`, `highest_win_rate`, `most_drawn`).
  - `get_card_win_rates(db_path, limit, min_matches)`: Sample-size filtered win rate rankings.
  - `get_archetype_meta_stats(db_path, archetype)`: Aggregated archetype statistics.
  - `get_cardpool_telemetry_summary(db_path)`: Server-wide macro activity.
  - `get_underused_cards(db_path, limit)`: Dormant card discovery.
- **`mutators.py`**:
  - `track_card_draw(db_path, card_id, count)` / `track_cards_drawn(db_path, card_ids)`: Atomic single and batch draw tracking.
  - `track_card_play(db_path, card_id, count)` / `track_cards_played(db_path, card_ids)`: Atomic single and batch play tracking.
  - `track_card_match_result(db_path, card_id, is_win)` / `track_cards_match_result(db_path, card_ids, is_win)`: Standalone and deck-wide match outcome tracking.
  - `track_deck_inclusion(db_path, card_id, delta)` / `batch_track_deck_inclusions(db_path, card_deltas)`: Atomic deck inclusion counters.
  - `reset_card_telemetry(db_path, card_id)`: Administrative reset helper.

### 3. Core Engine Facade (`core.py`)

- Defines `CardService(db_path: Optional[str] = None)` which delegates all calls directly to the pure functional domain compilation units while preserving instance state.

### 4. Backwards-Compatibility Bridge (`services/card_service.py`)

- Re-exports `CardService` and all public constants/types at `production/main/discord_bot/services/card_service.py` to ensure 100% zero breaking changes for existing cogs, slash commands, and test runners.
