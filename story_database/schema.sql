-- ============================================================================
-- Yu-Gi-Oh! Custom Card, Story Lore & Duel Simulator Database Schema
-- ============================================================================
-- This SQLite schema serves as the central source of truth for:
-- 1. Sagas, Lore Arcs, Factions, and Duelist dossiers
-- 2. Custom Card design attributes (synced with Duelingbook and ocgcore CDB)
-- 3. Character and Player decklists (exported to .ydk for simulators)
-- 4. In-universe Duel logs and narrative chronicles
-- 5. Full-Text Search (FTS5) for instant lookup via API and Discord Bot
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. Lore Arcs & Sagas
-- ----------------------------------------------------------------------------
-- Represents major overarching narrative sagas or seasons in the story.
CREATE TABLE IF NOT EXISTS lore_arcs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL UNIQUE,              -- e.g. "The Astral Fracture Saga"
    synopsis TEXT,                           -- High-level overview of the narrative conflict
    era_or_season TEXT DEFAULT 'Season 1',   -- Narrative era or season identifier
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. Factions / Archetypes / Guilds
-- ----------------------------------------------------------------------------
-- Groups of cards and duelists linked by shared lore and mechanics.
CREATE TABLE IF NOT EXISTS factions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,               -- e.g. "Starforged Order", "Void Sovereigns"
    lore_description TEXT,                  -- Origin and philosophy of the faction
    playstyle_overview TEXT,                -- Mechanical archetype dynamics (e.g. Rank 8 Xyz)
    arc_id INTEGER REFERENCES lore_arcs(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 3. Story Characters / Duelists
-- ----------------------------------------------------------------------------
-- In-universe duelists possessing signature decks and roleplay profiles.
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,               -- Duelist Name (e.g. "Valen Vance")
    alias TEXT,                              -- Title/moniker (e.g. "The Solar Vanguard")
    bio TEXT,                                -- Duelist history, personality, goals
    faction_id INTEGER REFERENCES factions(id) ON DELETE SET NULL,
    arc_id INTEGER REFERENCES lore_arcs(id) ON DELETE SET NULL,
    avatar_url TEXT,                         -- Hosted profile avatar / character artwork
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 4. Custom Cards (Compatible with Duelingbook & YGOPro simulators)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS custom_cards (
    id INTEGER PRIMARY KEY,                  -- 8-digit unique passcode (e.g. 50000001)
    name TEXT NOT NULL UNIQUE,               -- Official card display name
    card_type TEXT NOT NULL,                 -- Monster, Spell, Trap
    card_subtype TEXT,                       -- Normal, Effect, Fusion, Synchro, Xyz, Link, etc.
    attribute TEXT,                          -- LIGHT, DARK, WATER, FIRE, EARTH, WIND, DIVINE
    monster_type TEXT,                       -- Warrior, Dragon, Spellcaster, Cyberse, etc.
    level_or_rank_or_link INTEGER,           -- Level, Rank, or Link Rating
    scale INTEGER DEFAULT NULL,              -- Pendulum Scale (0-13)
    atk INTEGER DEFAULT NULL,                -- Attack stat (-2 for ?)
    def INTEGER DEFAULT NULL,                -- Defense stat (or Link arrows for Link monsters)
    link_arrows TEXT DEFAULT NULL,           -- Comma-separated Link arrows (e.g. "BL,BR,T")
    effect_text TEXT NOT NULL,               -- Rules text of the card
    pendulum_effect TEXT DEFAULT NULL,       -- Pendulum scale effect text if applicable
    
    -- Duelingbook Integration Metadata
    duelingbook_id TEXT,                     -- Duelingbook card serial or internal ID
    duelingbook_url TEXT,                    -- Direct link to card on duelingbook.com
    image_url TEXT,                          -- Hosted card artwork URL
    creator_name TEXT,                       -- Community designer username
    
    -- Story & Roleplay Lore
    lore_text TEXT,                          -- In-universe flavor lore / flavor backstory
    faction_id INTEGER REFERENCES factions(id) ON DELETE SET NULL,
    signature_character_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
    story_significance TEXT,                 -- Role (e.g. "Ace Card", "Boss Monster", "Starter")
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_custom_cards_type ON custom_cards(card_type);
CREATE INDEX IF NOT EXISTS idx_custom_cards_faction ON custom_cards(faction_id);
CREATE INDEX IF NOT EXISTS idx_custom_cards_name ON custom_cards(name);

-- ----------------------------------------------------------------------------
-- 5. Character Decks (Pre-constructed Story Decks)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS decks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                      -- Deck Title (e.g. "Sol Radiance")
    character_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
    creator_name TEXT,                       -- Designer / player
    description TEXT,                        -- Strategy and playstyle breakdown
    duelingbook_deck_url TEXT,               -- Link to full deck on Duelingbook
    ydk_content TEXT,                        -- Cached .ydk representation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 6. Character Deck Cards Junction Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS deck_cards (
    deck_id INTEGER REFERENCES decks(id) ON DELETE CASCADE,
    card_id INTEGER REFERENCES custom_cards(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1 CHECK (quantity BETWEEN 1 AND 3),
    section TEXT DEFAULT 'MAIN' CHECK (section IN ('MAIN', 'EXTRA', 'SIDE')),
    PRIMARY KEY (deck_id, card_id, section)
);

-- ----------------------------------------------------------------------------
-- 7. Player Personal Decks (Interactive Discord Deckbuilding)
-- ----------------------------------------------------------------------------
-- Tracks dynamic player decks assembled via Discord commands (`/deck_add`, `/mydeck`).
CREATE TABLE IF NOT EXISTS player_decks (
    user_id TEXT NOT NULL,                   -- Discord Snowflake User ID
    card_id INTEGER NOT NULL REFERENCES custom_cards(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1 CHECK (quantity BETWEEN 1 AND 3),
    PRIMARY KEY (user_id, card_id)
);

-- ----------------------------------------------------------------------------
-- 8. Story Duel Logs & Episode Chronicles
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS duel_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arc_id INTEGER REFERENCES lore_arcs(id) ON DELETE SET NULL,
    chapter_or_episode TEXT,                 -- e.g. "Chapter 1: The Sky Weeps Glass"
    duelist_1_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
    duelist_2_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
    winner_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
    duel_summary TEXT,                       -- Narrative recap of key turns & climax
    replay_file_or_link TEXT,                -- Path to saved simulator replay (.yrp)
    duel_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 9. Full-Text Search (FTS5) Virtual Table
-- ----------------------------------------------------------------------------
-- Powers lightning-fast autocomplete and fuzzy search across card names,
-- effect keywords, and lore descriptions.
CREATE VIRTUAL TABLE IF NOT EXISTS cards_fts USING fts5(
    name,
    effect_text,
    lore_text,
    card_type,
    monster_type,
    content='custom_cards',
    content_rowid='id'
);
