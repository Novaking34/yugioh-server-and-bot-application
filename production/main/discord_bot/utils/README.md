# Modular Discord Bot Formatting & UI Architecture (`utils`)

## Overview

The `utils` package is engineered following a **Top-Down / Bottom-Up C-Style Compilation Unit Architecture** mirroring the modular standard established in `services.deck` and `services.card`.

```bash
utils/
├── README.md                      # Architectural documentation & API guide
├── __init__.py                    # Package root & unified public manifest
│
├── foundation/                    # Bottom-Up Primitives, Invariants & Types ("Headers")
│   ├── __init__.py                # Foundation re-exports
│   ├── colors.py                  # FRAME_COLORS palette & get_card_color()
│   ├── formatters.py              # format_passcode(), format_stat_value(), format_link_arrows(), format_spell_trap_property()
│   ├── types_guide_data.py        # Reference dictionaries (SPELL_CARD_TYPES, TRAP_CARD_TYPES, 26 races, etc.)
│   └── duel_math.py               # get_tribute_requirement(), calculate_battle_damage(), calculate_piercing_damage()
│
└── domain/                        # Presentation Units & Visual Renderers ("Translation Units")
    ├── __init__.py                # Domain re-exports
    ├── card_embeds.py             # build_card_embed(), build_card_stats_embed(), build_card_types_guide_embed()
    ├── autocomplete.py            # card_name_autocomplete(), create_card_autocomplete(), choice builders
    ├── duel_board.py              # DuelBoard class, render_duel_field_ascii(), build_board_guide_embed()
    ├── ranking_embeds.py          # build_rank_embed(), build_leaderboard_embed()
    └── story_embeds.py            # build_story_stage_embed()
```

---

## Subsystems

### 1. Foundation (`foundation/`)

- **`colors.py`**: Declares standard card frame hex colors (`FRAME_COLORS`, including Pendulum `#00A88F`) and the dynamic `get_card_color(card_type, card_subtype, attribute)` selector (handling DIVINE/Divine-Beast gold, summon mechanics, Spells, and Traps).
- **`formatters.py`**: Pure foundation string manipulation, stat sentinel translation (`-2 -> ?`), Link Arrow compass geometry decoding (`BL,BR,T -> ↙ ⬆ ↘`), 8-digit passcode zero-padding, and Spell Speed determination.
- **`types_guide_data.py`**: Educational metadata dictionaries providing speeds, icons, and descriptions:
  - `SPELL_CARD_TYPES`: 6 types (Normal, Continuous, Equip, Quick-Play, Field, Ritual).
  - `TRAP_CARD_TYPES`: 3 types (Normal, Continuous, Counter Trap).
  - `MONSTER_CARD_FRAMES`: 9 summoning categories.
  - `ALL_26_MONSTER_RACES`: All 26 official monster tribes.
  - `CARD_ATTRIBUTES`: 7 canonical elemental attributes with kanji and bitmasks.
  - `LEVELS_AND_RANKS_DATA`: Levels vs Ranks rules, Link Ratings, and Pendulum Scales.
- **`duel_math.py`**:
  - `get_tribute_requirement(level)`: 0 for Lv 1-4, 1 for Lv 5-6, 2 for Lv 7+.
  - `calculate_battle_damage(...)`: Full damage calculations (ATK vs ATK, ATK vs DEF, Direct attacks).

### 2. Domain Subsystems (`domain/`)

- **`card_embeds.py`**:
  - `build_card_embed(card)`: Complete card inspection embed with Duelingbook art, stats, and lore.
  - `build_card_stats_embed(stats)`: Inclusion count, duel appearances, and win rate.
  - `build_card_types_guide_embed(category)`: Educational interactive guide embeds.
- **`autocomplete.py`**:
  - `card_name_autocomplete(interaction, current)`: Universal real-time card autocomplete with 3-second timeout protection and 25-choice API guard.
  - `create_card_autocomplete(...)`: Scoped autocomplete factory generator (filtering by Monster, Spell, Trap, Extra Deck, or Archetype).
  - `build_card_autocomplete_choices(...)`: Pure choice transformation enforcing 100-character name limits.
- **`duel_board.py`**:
  - `DuelBoard`: 5 MMZs, 5 STZs, Field Spell, GY, and Banished zone tracking.
  - `render_duel_field_ascii(...)`: Live ASCII symmetrical playmat.
  - `build_board_guide_embed()`: Field zone explanations for `/board`.
- **`ranking_embeds.py`**:
  - `build_rank_embed(player, user)`: Official Duelist License card embed.
  - `build_leaderboard_embed(entries, season_id)`: Top duelists ranked by ELO.
- **`story_embeds.py`**:
  - `build_story_stage_embed(stage, progress)`: RPG campaign stage dialogue, boss profile, and rewards.

### 3. Root Entry Point & Translation Bridge (`utils.py`)

- `production/main/discord_bot/utils.py` serves as the root entry point and translation bridge re-exporting all symbols with the 4-block architecture, providing 100% backward compatibility.
