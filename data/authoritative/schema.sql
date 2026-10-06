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
-- 2b. Worldbuilding Lore & Cosmological Elements
-- ----------------------------------------------------------------------------
-- Detailed worldbuilding records: realms, landmarks, cosmological forces, and orders.
CREATE TABLE IF NOT EXISTS worldbuilding_elements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,                  -- 'Cosmology', 'Landmark', 'Artifact', 'Order', 'Realm'
    name TEXT NOT NULL UNIQUE,               -- e.g. "The Quiet Void", "Planet Kustomazi"
    lore_description TEXT NOT NULL,          -- In-depth canon description of this element
    significance TEXT,                       -- Role in the cosmic history of Kustomazi
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
    
    -- Card Set, Packaging & Release Tracker Fields
    set_number TEXT,                         -- Card code in expansion set (e.g. "TLOK-001")
    set_code TEXT,                           -- Expansion set abbreviation (e.g. "TLOK")
    rarity TEXT DEFAULT 'Common',            -- Ultra Rare, Secret Rare, Super Rare, Common
    archetype TEXT,                          -- Core Archetype (e.g. "Kasutamaiza")
    banlist_status TEXT DEFAULT 'Unlimited', -- Unlimited, Semi-Limited, Limited, Forbidden
    playtesting_status TEXT DEFAULT 'In Testing', -- In Testing, Approved, Needs Revision
    local_image_path TEXT,                   -- Local image file path (e.g. "production/shared/expansions/pics/50000101.jpg")
    script_file TEXT,                        -- Lua effect script path (e.g. "c50000101.lua")
    script_status TEXT DEFAULT 'Draft',      -- Implemented, Draft, Stub, Vanilla

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

-- ----------------------------------------------------------------------------
-- 10. Competitive ELO & Player Rankings
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS player_ratings (
    user_id TEXT PRIMARY KEY,               -- Discord Snowflake ID
    username TEXT,                          -- Cached Discord display name
    elo INTEGER DEFAULT 1200,               -- Current ELO score (default 1200)
    wins INTEGER DEFAULT 0,                 -- Total competitive wins
    losses INTEGER DEFAULT 0,               -- Total competitive losses
    draws INTEGER DEFAULT 0,                -- Total competitive draws
    win_streak INTEGER DEFAULT 0,           -- Current consecutive wins
    highest_streak INTEGER DEFAULT 0,       -- Peak consecutive wins
    highest_elo INTEGER DEFAULT 1200,       -- Peak ELO reached
    tier TEXT DEFAULT 'Bronze Duelist',      -- Tier title
    season_id TEXT DEFAULT 'Season 1',      -- Ranking season
    last_match_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_player_ratings_elo ON player_ratings(elo DESC);

-- ----------------------------------------------------------------------------
-- 11. Match History & Duel Tracking
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS duel_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_type TEXT DEFAULT 'CASUAL',       -- 'RANKED', 'CASUAL', 'STORY'
    p1_user_id TEXT NOT NULL,
    p2_user_id TEXT,                        -- NULL or 'NPC' if story duel
    winner_user_id TEXT,                    -- Winner user ID, 'DRAW', or 'CANCELLED'
    p1_elo_before INTEGER,
    p1_elo_after INTEGER,
    p2_elo_before INTEGER,
    p2_elo_after INTEGER,
    turns INTEGER DEFAULT 1,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    p1_deck_name TEXT DEFAULT NULL,
    p2_deck_name TEXT DEFAULT NULL
);

-- ----------------------------------------------------------------------------
-- 12. Card & Deck Usage Telemetry
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS card_usage_stats (
    card_id INTEGER PRIMARY KEY REFERENCES custom_cards(id) ON DELETE CASCADE,
    times_decked INTEGER DEFAULT 0,         -- Included in player decks
    times_drawn INTEGER DEFAULT 0,          -- Drawn in duels
    times_played INTEGER DEFAULT 0,         -- Played/summoned in duels
    wins INTEGER DEFAULT 0,                 -- Matches won when in active deck
    losses INTEGER DEFAULT 0,               -- Matches lost when in active deck
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 13. Story Mode Chapters & Progressive Stages
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


CREATE TABLE IF NOT EXISTS player_story_progress (
    user_id TEXT PRIMARY KEY,               -- Discord Snowflake ID
    current_chapter_id INTEGER DEFAULT 1,
    current_stage_number INTEGER DEFAULT 1,
    highest_stage_completed INTEGER DEFAULT 0,
    unlocked_titles TEXT DEFAULT '',        -- Comma-separated titles
    total_story_wins INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 14. Player Saved Decks & Macro Telemetry
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS player_saved_decks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    deck_name TEXT NOT NULL,
    ydk_content TEXT NOT NULL,
    times_used INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    last_used_at TIMESTAMP DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, deck_name)
);
CREATE INDEX IF NOT EXISTS idx_player_saved_decks_user ON player_saved_decks(user_id);


