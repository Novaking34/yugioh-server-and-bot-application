-- =============================================================================
-- THE LAND OF KUSTOMAZI - DYNAMIC TELEMETRY & PLAYER RUNTIME SCHEMA
-- Target Database: data/telemetry/telemetry.db
-- Architecture: High-Churn Player State, Competitive Ladder, Matches & Analytics
-- =============================================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ----------------------------------------------------------------------------
-- 1. Competitive ELO & Player Rankings
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS player_ratings (
    user_id TEXT PRIMARY KEY,               -- Discord Snowflake ID
    username TEXT NOT NULL,
    elo INTEGER DEFAULT 1200,               -- Standard starting Elo
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
-- 2. Match History & Duel Tracking
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
CREATE INDEX IF NOT EXISTS idx_duel_matches_users ON duel_matches(p1_user_id, p2_user_id);
CREATE INDEX IF NOT EXISTS idx_duel_matches_created ON duel_matches(created_at DESC);

-- ----------------------------------------------------------------------------
-- 3. Card & Deck Usage Micro-Telemetry
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS card_usage_stats (
    card_id INTEGER PRIMARY KEY,            -- Konami 8-digit passcode
    times_decked INTEGER DEFAULT 0,         -- Included in player decks
    times_drawn INTEGER DEFAULT 0,          -- Drawn in duels
    times_played INTEGER DEFAULT 0,         -- Played/summoned in duels
    wins INTEGER DEFAULT 0,                 -- Matches won when in active deck
    losses INTEGER DEFAULT 0,               -- Matches lost when in active deck
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 5. Player Staging Deck Slot (Active Workspace)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS player_decks (
    user_id TEXT NOT NULL,                   -- Discord Snowflake User ID
    card_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1 CHECK (quantity BETWEEN 1 AND 3),
    PRIMARY KEY (user_id, card_id)
);

-- ----------------------------------------------------------------------------
-- 6. Player Saved Decks & Macro Telemetry (Named Profiles)
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

-- ----------------------------------------------------------------------------
-- 7. Player Story Campaign Progress
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS player_story_progress (
    user_id TEXT PRIMARY KEY,               -- Discord Snowflake ID
    current_chapter_id INTEGER DEFAULT 1,
    current_stage_number INTEGER DEFAULT 1,
    highest_stage_completed INTEGER DEFAULT 0,
    unlocked_titles TEXT DEFAULT '',        -- Comma-separated titles
    total_story_wins INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
