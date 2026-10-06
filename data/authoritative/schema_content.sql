-- =============================================================================
-- THE LAND OF KUSTOMAZI - AUTHORITATIVE CONTENT DATABASE SCHEMA
-- Target Database: data/authoritative/content.db
-- Architecture: Static, Authored Game Rules, Cards, Lore, Decks & Story Encounters
-- =============================================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ----------------------------------------------------------------------------
-- 1. Canonical Sagas & Lore Arcs
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lore_arcs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL UNIQUE,              -- e.g. "The Land of Kustomazi Genesis"
    synopsis TEXT NOT NULL,                 -- Narrative overview of the story arc
    era_or_season TEXT DEFAULT 'Genesis Era',-- Timeline classification
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. Factions, Orders & Archetypes
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS factions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,              -- e.g. "The Genesis Void", "Spellspire"
    lore_description TEXT NOT NULL,         -- Worldbuilding narrative & philosophy
    playstyle_overview TEXT,                -- Mechanical overview of faction's playstyle
    arc_id INTEGER REFERENCES lore_arcs(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 3. Worldbuilding Elements (Relics, Locations, Phenomena)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS worldbuilding_elements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,                 -- 'RELIC', 'LOCATION', 'PHENOMENON', 'FACTION'
    name TEXT NOT NULL UNIQUE,              -- e.g. "The Genesis Seed", "Planet Kustomazi"
    lore_description TEXT NOT NULL,         -- Narrative breakdown and historical origin
    significance TEXT,                      -- Cosmic / story significance
    arc_id INTEGER REFERENCES lore_arcs(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 4. Key Story Characters & Duelists
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,              -- e.g. "The Great Kasutamaiza", "LeSpookie Singles"
    alias TEXT,                             -- Formal moniker / nickname
    bio TEXT NOT NULL,                      -- Narrative backstory
    faction_id INTEGER REFERENCES factions(id) ON DELETE SET NULL,
    arc_id INTEGER REFERENCES lore_arcs(id) ON DELETE SET NULL,
    avatar_url TEXT,                        -- Avatar artwork asset path or URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 5. Authoritative Custom Cards Registry
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS custom_cards (
    id INTEGER PRIMARY KEY,                 -- Konami 8-digit passcode (50,000,000 - 59,999,999)
    name TEXT NOT NULL UNIQUE,              -- Official card name
    card_type TEXT NOT NULL,                -- 'Monster', 'Spell', 'Trap'
    card_subtype TEXT,                      -- 'Normal', 'Effect', 'Fusion', 'Xyz', 'Quick-Play', etc.
    attribute TEXT,                         -- 'LIGHT', 'DARK', 'DIVINE', 'FIRE', etc.
    monster_type TEXT,                      -- 'Warrior', 'Spellcaster', 'Dragon', etc.
    level_or_rank_or_link INTEGER,          -- Level (1-12), Rank (1-13), or Link Rating (1-8)
    scale INTEGER,                          -- Pendulum Scale (0-13)
    atk INTEGER,                            -- Attack points (or NULL for ? / non-monster)
    def INTEGER,                            -- Defense points (or NULL for Link / non-monster)
    link_arrows TEXT,                       -- Comma-separated Link arrows (e.g. "BL,BR,T")
    effect_text TEXT,                       -- Primary text / Monster effect
    pendulum_effect TEXT,                   -- Pendulum scale effect text
    duelingbook_id INTEGER,                 -- Source Duelingbook card serial
    duelingbook_url TEXT,                   -- Original Duelingbook card link
    image_url TEXT,                         -- Remote source image URL
    creator_name TEXT DEFAULT 'Community',  -- Designer / Author attribution
    lore_text TEXT,                         -- Non-effect flavor text or universe lore
    faction_id INTEGER REFERENCES factions(id) ON DELETE SET NULL,
    signature_character_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
    story_significance TEXT,                -- 'Ace Monster', 'Boss', 'Searcher', etc.
    set_number TEXT,                        -- e.g. 'TLOK-001'
    set_code TEXT DEFAULT 'TLOK',           -- e.g. 'TLOK'
    rarity TEXT DEFAULT 'Common',           -- 'Common', 'Rare', 'Super Rare', 'Ultra Rare', 'Secret Rare'
    archetype TEXT,                         -- Archetype string
    banlist_status TEXT DEFAULT 'Unlimited',-- 'Unlimited', 'Semi-Limited', 'Limited', 'Forbidden'
    playtesting_status TEXT DEFAULT 'Approved',
    local_image_path TEXT,                  -- Relative path to cached high-res image
    script_file TEXT,                       -- Relative path to ocgcore effect script
    script_status TEXT DEFAULT 'Generated', -- 'Generated', 'Custom', 'Verified'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_custom_cards_type ON custom_cards(card_type, card_subtype);
CREATE INDEX IF NOT EXISTS idx_custom_cards_set ON custom_cards(set_number);
CREATE INDEX IF NOT EXISTS idx_custom_cards_faction ON custom_cards(faction_id);
CREATE INDEX IF NOT EXISTS idx_custom_cards_rarity ON custom_cards(rarity);

-- ----------------------------------------------------------------------------
-- 6. Card Full-Text Search (FTS5) Engine
-- ----------------------------------------------------------------------------
CREATE VIRTUAL TABLE IF NOT EXISTS cards_fts USING fts5(
    name,
    effect_text,
    lore_text,
    card_type,
    monster_type,
    content='custom_cards',
    content_rowid='id'
);

-- ----------------------------------------------------------------------------
-- 7. Pre-Made Story & Character Decks
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS decks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,              -- Deck name
    character_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
    creator_name TEXT DEFAULT 'Authoritative',
    description TEXT,
    duelingbook_deck_url TEXT,
    ydk_content TEXT,                       -- Raw contents of canonical .ydk file
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS deck_cards (
    deck_id INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    card_id INTEGER NOT NULL REFERENCES custom_cards(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1 CHECK (quantity BETWEEN 1 AND 3),
    section TEXT DEFAULT 'MAIN' CHECK (section IN ('MAIN', 'EXTRA', 'SIDE')),
    PRIMARY KEY (deck_id, card_id, section)
);
CREATE INDEX IF NOT EXISTS idx_deck_cards_card ON deck_cards(card_id);

-- ----------------------------------------------------------------------------
-- 8. Story Mode Chapters & Progressive Stages
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS story_chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_number INTEGER NOT NULL UNIQUE,
    title TEXT NOT NULL,
    arc_id INTEGER REFERENCES lore_arcs(id) ON DELETE SET NULL,
    synopsis TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS story_stages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id INTEGER REFERENCES story_chapters(id) ON DELETE CASCADE,
    stage_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    intro_dialogue TEXT NOT NULL,
    outro_dialogue TEXT NOT NULL,
    opponent_name TEXT NOT NULL,
    opponent_title TEXT,
    opponent_character_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
    opponent_deck_id INTEGER REFERENCES decks(id) ON DELETE SET NULL,
    encounter_type TEXT DEFAULT 'AI',       -- 'AI' (dynamic RNG deck play) or 'SCRIPTED' (pre-determined events)
    boss_hp INTEGER DEFAULT 8000,           -- Starting LP for NPC boss
    script_data TEXT DEFAULT NULL,          -- JSON encoded scripted timeline & dialogue cues
    reward_title TEXT,
    reward_card_id INTEGER REFERENCES custom_cards(id) ON DELETE SET NULL,
    UNIQUE(chapter_id, stage_number)
);

-- ----------------------------------------------------------------------------
-- 9. Story Duel Narrative Logs & Chronicles
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS duel_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arc_id INTEGER REFERENCES lore_arcs(id) ON DELETE SET NULL,
    chapter_or_episode TEXT,                 -- e.g. "Chapter 1: The Sky Weeps Glass"
    duelist_1_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
    duelist_2_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
    winner_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
    duel_summary TEXT NOT NULL,              -- Narrative log of the duel
    replay_file_or_link TEXT,                -- Simulator replay path or web link
    duel_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
