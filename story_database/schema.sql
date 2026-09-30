-- Yu-Gi-Oh Story, Lore, and Custom Card Database Schema
-- Designed for Duelingbook Integration & Simulator Synchronization

PRAGMA foreign_keys = ON;

-- 1. Lore Arcs & Sagas
CREATE TABLE IF NOT EXISTS lore_arcs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL UNIQUE,
    synopsis TEXT,
    era_or_season TEXT DEFAULT 'Season 1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Factions / Archetypes / Groups
CREATE TABLE IF NOT EXISTS factions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    lore_description TEXT,
    playstyle_overview TEXT,
    arc_id INTEGER REFERENCES lore_arcs(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Story Characters / Duelists
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    alias TEXT,
    bio TEXT,
    faction_id INTEGER REFERENCES factions(id) ON DELETE SET NULL,
    arc_id INTEGER REFERENCES lore_arcs(id) ON DELETE SET NULL,
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Custom Cards (Compatible with Duelingbook & YGOPro/EDOPro simulators)
CREATE TABLE IF NOT EXISTS custom_cards (
    id INTEGER PRIMARY KEY,                  -- Card Passcode (8 digits e.g. 50000001)
    name TEXT NOT NULL UNIQUE,
    card_type TEXT NOT NULL,                 -- Monster, Spell, Trap
    card_subtype TEXT,                       -- Normal, Effect, Fusion, Synchro, Xyz, Link, Ritual, Continuous, Equip, Field, Quick-Play, Counter
    attribute TEXT,                          -- LIGHT, DARK, WATER, FIRE, EARTH, WIND, DIVINE
    monster_type TEXT,                       -- Dragon, Spellcaster, Warrior, Cyberse, etc.
    level_or_rank_or_link INTEGER,           -- Level/Rank/Link Rating (e.g. 4, 8, Link-2)
    scale INTEGER DEFAULT NULL,              -- Pendulum Scale
    atk INTEGER DEFAULT NULL,
    def INTEGER DEFAULT NULL,
    link_arrows TEXT DEFAULT NULL,           -- e.g. "BL,BR" or "TL,TR,B"
    effect_text TEXT NOT NULL,
    pendulum_effect TEXT DEFAULT NULL,
    
    -- Duelingbook Integration Fields
    duelingbook_id TEXT,                     -- Duelingbook custom card ID / hash
    duelingbook_url TEXT,                    -- Link to Duelingbook card view
    image_url TEXT,                          -- Hosted card artwork or Duelingbook art link
    creator_name TEXT,                       -- Designer / player who submitted the card
    
    -- Story / Roleplay Metadata
    lore_text TEXT,                          -- In-universe lore / flavor text / backstory
    faction_id INTEGER REFERENCES factions(id) ON DELETE SET NULL,
    signature_character_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
    story_significance TEXT,                 -- e.g. "Boss Monster", "Relic", "Ace Card", "Forbidden Art"
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Character Decks
CREATE TABLE IF NOT EXISTS decks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    character_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
    creator_name TEXT,
    description TEXT,
    duelingbook_deck_url TEXT,
    ydk_content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Deck Cards Junction
CREATE TABLE IF NOT EXISTS deck_cards (
    deck_id INTEGER REFERENCES decks(id) ON DELETE CASCADE,
    card_id INTEGER REFERENCES custom_cards(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1 CHECK (quantity BETWEEN 1 AND 3),
    section TEXT DEFAULT 'MAIN' CHECK (section IN ('MAIN', 'EXTRA', 'SIDE')),
    PRIMARY KEY (deck_id, card_id, section)
);

-- 7. Story Duel Logs
CREATE TABLE IF NOT EXISTS duel_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arc_id INTEGER REFERENCES lore_arcs(id) ON DELETE SET NULL,
    chapter_or_episode TEXT,
    duelist_1_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
    duelist_2_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
    winner_id INTEGER REFERENCES characters(id) ON DELETE SET NULL,
    duel_summary TEXT,
    replay_file_or_link TEXT,
    duel_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Full Text Search table for quick card and lore search
CREATE VIRTUAL TABLE IF NOT EXISTS cards_fts USING fts5(
    name,
    effect_text,
    lore_text,
    card_type,
    monster_type,
    content='custom_cards',
    content_rowid='id'
);
