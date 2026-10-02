#!/usr/bin/env python3
"""
=============================================================================
Yu-Gi-Oh! Platform - Centralized Platform Settings & Environment Engine
=============================================================================
Provides a strongly-typed, centralized configuration loader that reads from:
1. Root environment file (.env)
2. Operating system environment variables
3. Hardcoded production/development defaults

Subsystems Covered:
- Platform Runtime & Logging Settings
- Public Network, Web Catalog & REST API Endpoints
- Live Duel Simulator (ocgcore Container & Sockets)
- The Great Kasutamaiza Modular Discord Bot
- Cloudflare Zero Trust Named Tunnel
- DuckDNS Dynamic DNS Synchronizer
- Database & Card Expansion Storage Paths
- Future Card Ingestion Pipeline Settings
=============================================================================
"""

import os
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# Ensure project root is available in sys.path
from config.paths import (
    BASE_DIR, ENV_FILE_PATH, STORY_DB_PATH, CDB_OUTPUT_PATH,
    SCRIPTS_DIR, DECKS_DIR, SIMULATOR_CONFIG_DIR, CLIENT_CONFIG_PATH
)

# Load .env file automatically into os.environ if present
if os.path.exists(ENV_FILE_PATH):
    try:
        from dotenv import load_dotenv
        load_dotenv(ENV_FILE_PATH)
    except ImportError:
        pass


@dataclass(frozen=True)
class PlatformConfig:
    """Core platform operating environment and logging settings."""
    environment: str = os.getenv("ENVIRONMENT", "production").lower()
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    base_dir: str = BASE_DIR

    @property
    def is_production(self) -> bool:
        """Return True if running in production mode."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Return True if running in development mode."""
        return self.environment in ("development", "dev", "local")


@dataclass(frozen=True)
class NetworkConfig:
    """Public domain, routing, and HTTP web catalog settings."""
    public_domain: str = os.getenv("PUBLIC_DOMAIN", "thelandofkustomazi.com")
    public_fallback_domain: str = os.getenv("PUBLIC_FALLBACK_DOMAIN", "thelandofkustomazi.duckdns.org")
    public_api_url: str = os.getenv("PUBLIC_API_URL", "https://thelandofkustomazi.com")
    web_host: str = os.getenv("WEB_HOST", "0.0.0.0")
    web_port: int = int(os.getenv("WEB_PORT", "8000"))
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")


@dataclass(frozen=True)
class SimulatorConfig:
    """Live ocgcore duel simulator container and network socket settings."""
    host: str = os.getenv("SIMULATOR_HOST", "thelandofkustomazi.com")
    fallback_host: str = os.getenv("SIMULATOR_FALLBACK_HOST", "147.224.147.30")
    port: int = int(os.getenv("SIMULATOR_PORT", "7911"))
    room_port: int = int(os.getenv("SIMULATOR_ROOM_PORT", "7922"))
    docker_username: str = os.getenv("DOCKER_USERNAME", "professorseanex")
    docker_image: str = os.getenv("DOCKER_IMAGE", "professorseanex/ygoserver:latest")
    container_name: str = os.getenv("DOCKER_CONTAINER_NAME", "ygo-simulator-server")
    config_dir: str = SIMULATOR_CONFIG_DIR

    @property
    def direct_connect_address(self) -> str:
        """Formatted host:port string for EDOPro / YGOPro direct connect."""
        return f"{self.host}:{self.port}"


@dataclass(frozen=True)
class DiscordConfig:
    """The Great Kasutamaiza Discord bot identity and guild configurations."""
    bot_token: Optional[str] = os.getenv("DISCORD_BOT_TOKEN")
    guild_id: Optional[int] = int(os.getenv("DISCORD_GUILD_ID")) if os.getenv("DISCORD_GUILD_ID") else None
    client_id: Optional[int] = int(os.getenv("DISCORD_CLIENT_ID")) if os.getenv("DISCORD_CLIENT_ID") else None
    command_prefix: str = os.getenv("DISCORD_COMMAND_PREFIX", "!")

    @property
    def is_configured(self) -> bool:
        """Check if a non-empty Discord bot token is present."""
        return bool(self.bot_token and len(self.bot_token.strip()) > 10)


@dataclass(frozen=True)
class CloudflareConfig:
    """Cloudflare Zero Trust edge tunnel settings."""
    tunnel_token: Optional[str] = os.getenv("CLOUDFLARE_TUNNEL_TOKEN")
    tunnel_id: str = os.getenv("CLOUDFLARE_TUNNEL_ID", "c346aa27-b4c1-41ba-815c-f66b2b84243b")
    tunnel_name: str = os.getenv("CLOUDFLARE_TUNNEL_NAME", "ygo-server-tunnel")

    @property
    def is_configured(self) -> bool:
        """Check if a Cloudflare tunnel token is present."""
        return bool(self.tunnel_token and len(self.tunnel_token.strip()) > 10)


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


@dataclass(frozen=True)
class StorageConfig:
    """Database and expansion filesystem paths."""
    db_path: str = STORY_DB_PATH
    cdb_path: str = CDB_OUTPUT_PATH
    scripts_dir: str = SCRIPTS_DIR
    decks_dir: str = DECKS_DIR
    client_config_path: str = CLIENT_CONFIG_PATH


@dataclass(frozen=True)
class PipelineConfig:
    """Card ingestion, artwork caching, and future upgrade placeholders."""
    duelingbook_api_endpoint: str = os.getenv("DUELINGBOOK_API_ENDPOINT", "https://www.duelingbook.com")
    card_art_cache_dir: str = os.getenv("CARD_ART_CACHE_DIR", os.path.join(BASE_DIR, "production", "main", "assets", "cache"))
    auto_sync_interval_minutes: int = int(os.getenv("AUTO_SYNC_INTERVAL_MINUTES", "15"))
    api_secret_key: str = os.getenv("API_SECRET_KEY", "default-dev-secret-key")


class Settings:
    """Master aggregated settings object providing access to all platform configurations."""
    def __init__(self):
        self.platform = PlatformConfig()
        self.network = NetworkConfig()
        self.simulator = SimulatorConfig()
        self.discord = DiscordConfig()
        self.cloudflare = CloudflareConfig()
        self.duckdns = DuckDNSConfig()
        self.storage = StorageConfig()
        self.pipeline = PipelineConfig()

    def as_sanitized_dict(self) -> Dict[str, Any]:
        """Return a dictionary of all active configurations with secrets redacted."""
        return {
            "platform": {
                "environment": self.platform.environment,
                "log_level": self.platform.log_level,
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
                "decks_dir": self.storage.decks_dir,
            },
        }


# Global singleton instance for centralized import across the codebase
settings = Settings()


if __name__ == "__main__":
    import json
    print("=== 🌌 Yu-Gi-Oh! Platform Active Configuration ===")
    print(json.dumps(settings.as_sanitized_dict(), indent=2))
