# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: config.settings
Description:
    Authoritative Centralized Platform Settings & Environment Engine.
    Provides strongly-typed, frozen dataclass configurations loaded from:
    1. Operating system environment variables
    2. Local environment secrets (.env via python-dotenv)
    3. Production-tested domain defaults
    
    Subsystems Configured:
    - Platform & Environment Mode (PlatformConfig)
    - Public Network, Web Catalog & Routing (NetworkConfig)
    - Live Duel Simulator Container & Sockets (SimulatorConfig)
    - The Great Kasutamaiza Discord Bot (DiscordConfig)
    - Cloudflare Zero Trust Named Tunnel (CloudflareConfig)
    - DuckDNS Dynamic DNS Synchronizer (DuckDNSConfig)
    - Unified Data Subsystem Paths (StorageConfig)
    - SQLite Engine Pragmas & Concurrency (DatabaseConfig)
    - Diagnostic Assertions & Telemetry Tracing (DebugConfig)
    - Card Ingestion & Artwork Pipelines (PipelineConfig)
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import os
import sys

# Ensure project root is available in sys.path and prevent shadowing stdlib
_CURR_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_CURR_DIR)
if sys.path and sys.path[0] == _CURR_DIR:
    sys.path.pop(0)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from config.paths import (
    BASE_DIR, ENV_FILE_PATH, DATA_DIR, AUTHORITATIVE_DATA_DIR,
    STORY_DB_PATH, SCHEMA_PATH, TRACKERS_DIR, DEFAULT_TRACKER_CSV,
    DEFAULT_TRACKER_TSV, ARTWORK_DIR, RAW_CARD_ART_DIR, EXPANSIONS_DIR,
    CDB_OUTPUT_PATH, SCRIPTS_DIR, PICS_DIR, THUMBNAILS_DIR, DECKS_DIR,
    SIMULATOR_DATA_DIR, SIMULATOR_CONFIG_DIR, SIMULATOR_REPLAYS_DIR,
    CLIENT_CONFIG_PATH, LOGS_DIR, COMBINED_LOG_PATH, ERRORS_LOG_PATH,
    AUDIT_LOG_PATH, DEBUG_SNAPSHOTS_DIR
)

# Load .env file automatically into os.environ if present
if os.path.exists(ENV_FILE_PATH):
    try:
        from dotenv import load_dotenv
        load_dotenv(ENV_FILE_PATH)
    except ImportError:
        pass

# =============================================================================
# BLOCK 3: BODY BLOCK (Strongly-Typed Configuration Dataclasses)
# =============================================================================

# -----------------------------------------------------------------------------
# SUB-BLOCK 3.1: Platform & Environment Configuration
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class PlatformConfig:
    """Core platform operating environment and execution mode settings."""
    environment: str = os.getenv("ENVIRONMENT", "production").lower()
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    debug: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    base_dir: str = BASE_DIR

    @property
    def is_production(self) -> bool:
        """Return True if running in production mode."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Return True if running in development mode."""
        return self.environment in ("development", "dev", "local")


# -----------------------------------------------------------------------------
# SUB-BLOCK 3.2: Network & Public Routing Configuration
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class NetworkConfig:
    """Public domain, routing, and HTTP web catalog settings."""
    public_domain: str = os.getenv("PUBLIC_DOMAIN", "thelandofkustomazi.com")
    public_fallback_domain: str = os.getenv("PUBLIC_FALLBACK_DOMAIN", "thelandofkustomazi.duckdns.org")
    public_api_url: str = os.getenv("PUBLIC_API_URL", "https://thelandofkustomazi.com")
    web_host: str = os.getenv("WEB_HOST", "0.0.0.0")
    web_port: int = int(os.getenv("WEB_PORT", "8000"))
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")


# -----------------------------------------------------------------------------
# SUB-BLOCK 3.3: Live Simulator Container & Engine Configuration
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class SimulatorConfig:
    """Live ocgcore duel simulator container and network socket settings."""
    host: str = os.getenv("SIMULATOR_HOST", "thelandofkustomazi.com")
    fallback_host: str = os.getenv("SIMULATOR_FALLBACK_HOST", "thelandofkustomazi.duckdns.org")
    port: int = int(os.getenv("SIMULATOR_PORT", "7911"))
    room_port: int = int(os.getenv("SIMULATOR_ROOM_PORT", "7922"))
    docker_username: str = os.getenv("DOCKER_USERNAME", "professorseanex")
    docker_image: str = os.getenv("DOCKER_IMAGE", "professorseanex/ygoserver:latest")
    container_name: str = os.getenv("DOCKER_CONTAINER_NAME", "ygo-simulator-server")
    config_dir: str = SIMULATOR_CONFIG_DIR
    replays_dir: str = SIMULATOR_REPLAYS_DIR

    @property
    def direct_connect_address(self) -> str:
        """Formatted host:port string for EDOPro / YGOPro direct connect."""
        return f"{self.host}:{self.port}"


# -----------------------------------------------------------------------------
# SUB-BLOCK 3.4: Discord Bot Identity & Operational Configuration
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class DiscordConfig:
    """The Great Kasutamaiza Discord bot identity and guild configurations."""
    bot_token: Optional[str] = os.getenv("DISCORD_BOT_TOKEN")
    guild_id: Optional[int] = int(os.getenv("DISCORD_GUILD_ID")) if os.getenv("DISCORD_GUILD_ID") else None
    client_id: Optional[int] = int(os.getenv("DISCORD_CLIENT_ID")) if os.getenv("DISCORD_CLIENT_ID") else None
    command_prefix: str = os.getenv("DISCORD_COMMAND_PREFIX", "!")

    @property
    def is_configured(self) -> bool:
        """Check if a valid, non-empty Discord bot token is configured."""
        return bool(self.bot_token and len(self.bot_token.strip()) > 10)


# -----------------------------------------------------------------------------
# SUB-BLOCK 3.5: Cloudflare Zero Trust Edge Tunnel Configuration
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class CloudflareConfig:
    """Cloudflare Zero Trust edge tunnel credentials and parameters."""
    tunnel_token: Optional[str] = os.getenv("CLOUDFLARE_TUNNEL_TOKEN")
    tunnel_id: str = os.getenv("CLOUDFLARE_TUNNEL_ID", "c346aa27-b4c1-41ba-815c-f66b2b84243b")
    tunnel_name: str = os.getenv("CLOUDFLARE_TUNNEL_NAME", "ygo-server-tunnel")

    @property
    def is_configured(self) -> bool:
        """Check if a Cloudflare tunnel token is present."""
        return bool(self.tunnel_token and len(self.tunnel_token.strip()) > 10)


# -----------------------------------------------------------------------------
# SUB-BLOCK 3.6: DuckDNS Dynamic DNS Auto-Updater Configuration
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class DuckDNSConfig:
    """DuckDNS dynamic DNS auto-updater credentials."""
    domain: str = os.getenv("DUCKDNS_DOMAIN", "thelandofkustomazi")
    token: Optional[str] = os.getenv("DUCKDNS_TOKEN")

    @property
    def full_domain(self) -> str:
        """Full domain name string: <subdomain>.duckdns.org."""
        return f"{self.domain}.duckdns.org"

    @property
    def is_configured(self) -> bool:
        """Check if a DuckDNS account token is present."""
        return bool(self.token and len(self.token.strip()) > 10)


# -----------------------------------------------------------------------------
# SUB-BLOCK 3.7: Unified Data Subsystem Storage Configuration
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class StorageConfig:
    """Canonical filesystem paths for data, databases, and expansion assets."""
    data_dir: str = DATA_DIR
    authoritative_dir: str = AUTHORITATIVE_DATA_DIR
    db_path: str = STORY_DB_PATH
    schema_path: str = SCHEMA_PATH
    trackers_dir: str = TRACKERS_DIR
    default_tracker_csv: str = DEFAULT_TRACKER_CSV
    default_tracker_tsv: str = DEFAULT_TRACKER_TSV
    artwork_dir: str = ARTWORK_DIR
    raw_card_art_dir: str = RAW_CARD_ART_DIR
    expansions_dir: str = EXPANSIONS_DIR
    cdb_path: str = CDB_OUTPUT_PATH
    scripts_dir: str = SCRIPTS_DIR
    pics_dir: str = PICS_DIR
    thumbnails_dir: str = THUMBNAILS_DIR
    decks_dir: str = DECKS_DIR
    simulator_data_dir: str = SIMULATOR_DATA_DIR
    simulator_config_dir: str = SIMULATOR_CONFIG_DIR
    replays_dir: str = SIMULATOR_REPLAYS_DIR
    client_config_path: str = CLIENT_CONFIG_PATH


# -----------------------------------------------------------------------------
# SUB-BLOCK 3.8: SQLite Database Engine & Concurrency Configuration
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class DatabaseConfig:
    """SQLite runtime connection pragmas, pooling, and concurrency settings."""
    busy_timeout_ms: int = int(os.getenv("DB_BUSY_TIMEOUT_MS", "5000"))
    wal_mode: bool = os.getenv("DB_WAL_MODE", "true").lower() in ("true", "1", "yes")
    foreign_keys: bool = True
    pool_size: int = int(os.getenv("DB_POOL_SIZE", "5"))
    echo_queries: bool = os.getenv("DB_ECHO", "false").lower() in ("true", "1", "yes")


# -----------------------------------------------------------------------------
# SUB-BLOCK 3.9: Diagnostic Assertion & Debugger Configuration
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class DebugConfig:
    """Diagnostic thresholds, slow query traps, and post-mortem settings."""
    slow_query_ms: float = float(os.getenv("DEBUG_SLOW_QUERY_MS", "50.0"))
    capture_locals: bool = os.getenv("DEBUG_CAPTURE_LOCALS", "true").lower() in ("true", "1", "yes")
    auto_audit_on_error: bool = os.getenv("DEBUG_AUTO_AUDIT", "true").lower() in ("true", "1", "yes")
    trace_retention_limit: int = int(os.getenv("DEBUG_TRACE_LIMIT", "1000"))
    snapshot_retention_days: int = int(os.getenv("DEBUG_SNAPSHOT_RETENTION_DAYS", "7"))
    snapshots_dir: str = DEBUG_SNAPSHOTS_DIR


# -----------------------------------------------------------------------------
# SUB-BLOCK 3.10: Ingestion Pipeline & Synchronization Settings
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class PipelineConfig:
    """Card ingestion, artwork caching, and API security settings."""
    duelingbook_api_endpoint: str = os.getenv("DUELINGBOOK_API_ENDPOINT", "https://www.duelingbook.com")
    card_art_cache_dir: str = os.getenv("CARD_ART_CACHE_DIR", os.path.join(BASE_DIR, "production", "main", "assets", "cache"))
    auto_sync_interval_minutes: int = int(os.getenv("AUTO_SYNC_INTERVAL_MINUTES", "15"))
    api_secret_key: str = os.getenv("API_SECRET_KEY", "default-dev-secret-key")


# -----------------------------------------------------------------------------
# SUB-BLOCK 3.11: Multi-Sink Logging & Observability Settings
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class LoggingConfig:
    """Platform multi-sink logging, formatting, rotation, and audit ledger settings."""
    level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    format: str = os.getenv("LOG_FORMAT", "text").lower()
    combined_log_path: str = COMBINED_LOG_PATH
    errors_log_path: str = ERRORS_LOG_PATH
    audit_log_path: str = AUDIT_LOG_PATH
    max_bytes_service: int = int(os.getenv("LOG_MAX_BYTES_SERVICE", str(10 * 1024 * 1024)))
    max_bytes_combined: int = int(os.getenv("LOG_MAX_BYTES_COMBINED", str(15 * 1024 * 1024)))
    backup_count: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    enable_trace_correlation: bool = os.getenv("LOG_TRACE_CORRELATION", "true").lower() in ("true", "1", "yes")

    @property
    def is_json_format(self) -> bool:
        """Return True if JSON telemetry mode is requested."""
        return self.format == "json"


# -----------------------------------------------------------------------------
# SUB-BLOCK 3.12: Master Aggregate Settings Engine
# -----------------------------------------------------------------------------
class Settings:
    """Master aggregated settings object providing centralized access across the codebase."""
    def __init__(self):
        self.platform = PlatformConfig()
        self.network = NetworkConfig()
        self.simulator = SimulatorConfig()
        self.discord = DiscordConfig()
        self.cloudflare = CloudflareConfig()
        self.duckdns = DuckDNSConfig()
        self.storage = StorageConfig()
        self.database = DatabaseConfig()
        self.debug = DebugConfig()
        self.pipeline = PipelineConfig()
        self.logging = LoggingConfig()

    @property
    def environment(self) -> str:
        """Operating environment name ('production' or 'development')."""
        return self.platform.environment

    @property
    def debug_mode(self) -> bool:
        """Whether debug mode is active."""
        return self.platform.debug

    @property
    def is_production(self) -> bool:
        """Whether running in live production mode."""
        return self.platform.is_production

    @property
    def is_development(self) -> bool:
        """Whether running in local development mode."""
        return self.platform.is_development

    def as_sanitized_dict(self) -> Dict[str, Any]:
        """Return a dictionary of all active configurations with sensitive secrets redacted."""
        return {
            "platform": {
                "environment": self.platform.environment,
                "log_level": self.platform.log_level,
                "debug": self.platform.debug,
                "base_dir": self.platform.base_dir,
            },
            "network": {
                "public_domain": self.network.public_domain,
                "public_fallback_domain": self.network.public_fallback_domain,
                "public_api_url": self.network.public_api_url,
                "web_port": self.network.web_port,
            },
            "simulator": {
                "host": self.simulator.host,
                "port": self.simulator.port,
                "room_port": self.simulator.room_port,
                "docker_image": self.simulator.docker_image,
                "direct_connect": self.simulator.direct_connect_address,
            },
            "discord": {
                "guild_id": self.discord.guild_id,
                "client_id": self.discord.client_id,
                "prefix": self.discord.command_prefix,
                "is_configured": self.discord.is_configured,
            },
            "cloudflare": {
                "tunnel_id": self.cloudflare.tunnel_id,
                "tunnel_name": self.cloudflare.tunnel_name,
                "is_configured": self.cloudflare.is_configured,
            },
            "duckdns": {
                "domain": self.duckdns.full_domain,
                "is_configured": self.duckdns.is_configured,
            },
            "storage": {
                "db_path": self.storage.db_path,
                "cdb_path": self.storage.cdb_path,
                "scripts_dir": self.storage.scripts_dir,
                "pics_dir": self.storage.pics_dir,
                "decks_dir": self.storage.decks_dir,
                "trackers_dir": self.storage.trackers_dir,
            },
            "database": {
                "busy_timeout_ms": self.database.busy_timeout_ms,
                "wal_mode": self.database.wal_mode,
                "pool_size": self.database.pool_size,
            },
            "debug": {
                "slow_query_ms": self.debug.slow_query_ms,
                "capture_locals": self.debug.capture_locals,
                "auto_audit_on_error": self.debug.auto_audit_on_error,
                "snapshot_retention_days": self.debug.snapshot_retention_days,
                "snapshots_dir": self.debug.snapshots_dir,
            },
            "logging": {
                "level": self.logging.level,
                "format": self.logging.format,
                "combined_log_path": self.logging.combined_log_path,
                "errors_log_path": self.logging.errors_log_path,
                "audit_log_path": self.logging.audit_log_path,
                "backup_count": self.logging.backup_count,
                "trace_correlation": self.logging.enable_trace_correlation,
            },
        }


# Global singleton instance for centralized import across the codebase
settings = Settings()

# =============================================================================
# BLOCK 4: CLOSING BLOCK (Exports & Namespace Control)
# =============================================================================

__all__ = [
    "PlatformConfig",
    "NetworkConfig",
    "SimulatorConfig",
    "DiscordConfig",
    "CloudflareConfig",
    "DuckDNSConfig",
    "StorageConfig",
    "DatabaseConfig",
    "DebugConfig",
    "PipelineConfig",
    "LoggingConfig",
    "Settings",
    "settings",
]

if __name__ == "__main__":
    import json
    print("=== 🌌 Yu-Gi-Oh! Platform Active Configuration ===")
    print(json.dumps(settings.as_sanitized_dict(), indent=2))
