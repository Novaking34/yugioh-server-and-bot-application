# 🗄️ Story Database & Schema Subsystem (`development/database/`)

This directory contains the SQLite relational database definitions, Full-Text Search (FTS5) virtual tables, and bootstrapping seed scripts for the Yu-Gi-Oh! custom card, story lore, and duelist progression engine.

---

## 📁 Database Files

| File | Purpose | Notes |
| :--- | :--- | :--- |
| [`schema.sql`](file:///home/professorseanex/yugioh-server/development/database/schema.sql) | Relational SQLite DDL schema definition | 8 relational tables + 1 FTS5 virtual table |
| [`seed_story_data.py`](file:///home/professorseanex/yugioh-server/development/database/seed_story_data.py) | Bootstrapping seed script | Populates initial saga, factions, duelists, & cards |

The live database file is maintained at:
**[`production/main/web/ygo_story.db`](file:///home/professorseanex/yugioh-server/production/main/web/ygo_story.db)**

---

## 🏛️ Relational Schema Design

```mermaid
erDiagram
    LORE_ARCS ||--o{ FACTIONS : contains
    LORE_ARCS ||--o{ CHARACTERS : spans
    FACTIONS ||--o{ CHARACTERS : aligns
    FACTIONS ||--o{ CUSTOM_CARDS : themes
    CHARACTERS ||--o{ DECKS : pilots
    DECKS ||--o{ DECK_CARDS : contains
    CUSTOM_CARDS ||--o{ DECK_CARDS : includes
    CUSTOM_CARDS ||--o{ PLAYER_DECKS : equips

    LORE_ARCS {
        int id PK
        text title
        text synopsis
        text era_or_season
    }
    FACTIONS {
        int id PK
        text name
        text lore_description
        text playstyle_overview
        int arc_id FK
    }
    CHARACTERS {
        int id PK
        text name
        text alias
        text bio
        int faction_id FK
        int arc_id FK
        text avatar_url
    }
    CUSTOM_CARDS {
        int id PK
        text name
        text card_type
        text card_subtype
        text attribute
        text monster_type
        int level_or_rank_or_link
        int scale
        int atk
        int def
        text link_arrows
        text effect_text
        text pendulum_effect
        text lore_snippet
        int faction_id FK
        int arc_id FK
    }
    DECKS {
        int id PK
        text name
        text description
        int character_id FK
    }
    DECK_CARDS {
        int deck_id FK
        int card_id FK
        int quantity
        text section
    }
```

---

## 🔍 Full-Text Search (FTS5)

To provide lightning-fast card searching across card names, archetypes, and effect text (for both the Web Catalog and Discord `/search` slash commands), the schema creates an SQLite FTS5 virtual table:

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS custom_cards_fts USING fts5(
    name,
    effect_text,
    card_type,
    card_subtype,
    attribute,
    monster_type,
    content='custom_cards',
    content_rowid='id'
);
```

Automated SQLite triggers keep the search index synchronized whenever cards are inserted, updated, or deleted.

---

## 🚀 Initializing & Seeding the Database

To create the tables and seed default data:

```bash
# Direct Python execution:
python3 development/database/seed_story_data.py

# Via Master CLI (sync also compiles CDB and Lua):
./manage.sh sync
```
