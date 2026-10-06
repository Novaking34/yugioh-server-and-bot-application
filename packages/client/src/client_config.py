#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: packages.client.src.client_config
Architecture: Hybrid Systems Engineering (Client Distribution Subsystem)
Description:
    Authoritative Client Configuration & Connection Manifest Subsystem.
    Provides strongly-typed dataclass settings, connection string formatters,
    manifest resolution, and server settings synchronization for the player client
    application and CLI synchronizer.

Resolution Hierarchy:
    1. Local JSON manifest in package root (packages/client/config.json)
    2. Local JSON manifest in source directory (packages/client/src/config.json)
    3. Active platform repository settings (config.settings if running inside repo)
    4. Safe embedded client production defaults
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import os
import sys
import json
from dataclasses import dataclass
from typing import Dict, Any, Optional

# Canonical directory detection
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
_PACKAGE_DIR = os.path.dirname(_SRC_DIR)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_PACKAGE_DIR))

# Default safe embedded client fallback values
DEFAULT_SERVER_NAME = "The Great Kasutamaiza Duel Server"
DEFAULT_SERVER_HOST = "thelandofkustomazi.com"
DEFAULT_SERVER_PORT = 7911
DEFAULT_ROOM_PORT = 7922
DEFAULT_DOMAIN = "thelandofkustomazi.com"
DEFAULT_FALLBACK_HOST = "thelandofkustomazi.duckdns.org"
DEFAULT_WEB_CATALOG_URL = "https://thelandofkustomazi.com"
DEFAULT_EXPANSIONS_UPDATE_URL = "https://thelandofkustomazi.com/api/expansions/download"
DEFAULT_WEB_PORT = 8000


# =============================================================================
# BLOCK 3: BODY BLOCK (Strongly-Typed Models & Manifest Resolution)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Strongly-Typed Client Configuration Model
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class ClientConfig:
    """Strongly-typed connection settings for player clients and installers."""
    server_name: str = DEFAULT_SERVER_NAME
    server_host: str = DEFAULT_SERVER_HOST
    server_port: int = DEFAULT_SERVER_PORT
    room_port: int = DEFAULT_ROOM_PORT
    domain: str = DEFAULT_DOMAIN
    fallback_host: str = DEFAULT_FALLBACK_HOST
    fallback_simulator_host: str = DEFAULT_FALLBACK_HOST
    web_catalog_url: str = DEFAULT_WEB_CATALOG_URL
    server_url: str = DEFAULT_WEB_CATALOG_URL
    web_port: int = DEFAULT_WEB_PORT
    expansions_update_url: str = DEFAULT_EXPANSIONS_UPDATE_URL

    @property
    def direct_connect_address(self) -> str:
        """Formatted host:port string for EDOPro / YGOPro direct connect."""
        return f"{self.server_host}:{self.server_port}"

    @property
    def fallback_connect_address(self) -> str:
        """Formatted fallback host:port string for dynamic DNS connection."""
        return f"{self.fallback_host}:{self.server_port}"

    @property
    def is_ssl_enabled(self) -> bool:
        """Returns True if the web catalog or update URL uses HTTPS."""
        return self.web_catalog_url.startswith("https://")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to JSON-serializable dictionary."""
        return {
            "server_name": self.server_name,
            "server_host": self.server_host,
            "server_port": self.server_port,
            "room_port": self.room_port,
            "domain": self.domain,
            "fallback_host": self.fallback_host,
            "fallback_simulator_host": self.fallback_simulator_host,
            "web_catalog_url": self.web_catalog_url,
            "server_url": self.server_url,
            "web_port": self.web_port,
            "expansions_update_url": self.expansions_update_url,
        }


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Manifest Resolution Engine
# -----------------------------------------------------------------------------
def resolve_config_manifest() -> Dict[str, Any]:
    """Resolve and load the client configuration dictionary from candidate locations.

    Search Order:
    1. Package root directory (_PACKAGE_DIR/config.json)
    2. Local source directory (_SRC_DIR/config.json)
    3. Active platform settings (config.settings if in repository)
    4. Safe embedded defaults
    """
    candidates = [
        os.path.join(_PACKAGE_DIR, "config.json"),
        os.path.join(_SRC_DIR, "config.json"),
    ]

    for candidate in candidates:
        if os.path.isfile(candidate):
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data
            except Exception as e:
                sys.stderr.write(f"[WARN] Error reading config from {candidate}: {e}\n")

    # Attempt to load from platform settings if executed within server repo
    try:
        if _PROJECT_ROOT not in sys.path:
            sys.path.insert(0, _PROJECT_ROOT)
        from config.settings import settings
        return {
            "server_name": DEFAULT_SERVER_NAME,
            "server_host": settings.simulator.host,
            "server_port": settings.simulator.port,
            "room_port": settings.simulator.room_port,
            "domain": settings.network.public_domain,
            "fallback_host": settings.simulator.fallback_host,
            "fallback_simulator_host": settings.simulator.fallback_host,
            "web_catalog_url": settings.network.public_api_url,
            "server_url": settings.network.public_api_url,
            "web_port": settings.network.web_port,
            "expansions_update_url": f"{settings.network.public_api_url}/api/expansions/download",
        }
    except Exception:
        pass

    # Safe fallback defaults
    return {
        "server_name": DEFAULT_SERVER_NAME,
        "server_host": DEFAULT_SERVER_HOST,
        "server_port": DEFAULT_SERVER_PORT,
        "room_port": DEFAULT_ROOM_PORT,
        "domain": DEFAULT_DOMAIN,
        "fallback_host": DEFAULT_FALLBACK_HOST,
        "fallback_simulator_host": DEFAULT_FALLBACK_HOST,
        "web_catalog_url": DEFAULT_WEB_CATALOG_URL,
        "server_url": DEFAULT_WEB_CATALOG_URL,
        "web_port": DEFAULT_WEB_PORT,
        "expansions_update_url": DEFAULT_EXPANSIONS_UPDATE_URL,
    }


def load_client_config() -> ClientConfig:
    """Instantiate and return a strongly-typed ClientConfig from resolved manifest."""
    raw = resolve_config_manifest()
    return ClientConfig(
        server_name=raw.get("server_name", DEFAULT_SERVER_NAME),
        server_host=raw.get("server_host", DEFAULT_SERVER_HOST),
        server_port=int(raw.get("server_port", DEFAULT_SERVER_PORT)),
        room_port=int(raw.get("room_port", DEFAULT_ROOM_PORT)),
        domain=raw.get("domain", DEFAULT_DOMAIN),
        fallback_host=raw.get("fallback_host", DEFAULT_FALLBACK_HOST),
        fallback_simulator_host=raw.get("fallback_simulator_host", DEFAULT_FALLBACK_HOST),
        web_catalog_url=raw.get("web_catalog_url", DEFAULT_WEB_CATALOG_URL),
        server_url=raw.get("server_url", DEFAULT_WEB_CATALOG_URL),
        web_port=int(raw.get("web_port", DEFAULT_WEB_PORT)),
        expansions_update_url=raw.get("expansions_update_url", DEFAULT_EXPANSIONS_UPDATE_URL),
    )


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Server Settings Synchronization Helper
# -----------------------------------------------------------------------------
def sync_manifest_from_settings(target_path: Optional[str] = None) -> str:
    """Synchronizes packages/client/config.json directly from active platform settings.
    
    Guarantees zero configuration drift between server configuration (.env)
    and the standalone player client distribution manifest.
    """
    dest = target_path or os.path.join(_PACKAGE_DIR, "config.json")
    try:
        if _PROJECT_ROOT not in sys.path:
            sys.path.insert(0, _PROJECT_ROOT)
        from config.settings import settings
        data = {
            "server_name": DEFAULT_SERVER_NAME,
            "server_host": settings.simulator.host,
            "server_port": settings.simulator.port,
            "room_port": settings.simulator.room_port,
            "domain": settings.network.public_domain,
            "fallback_host": settings.simulator.fallback_host,
            "fallback_simulator_host": settings.simulator.fallback_host,
            "web_catalog_url": settings.network.public_api_url,
            "server_url": settings.network.public_api_url,
            "web_port": settings.network.web_port,
            "expansions_update_url": f"{settings.network.public_api_url}/api/expansions/download",
        }
    except Exception:
        cfg = load_client_config()
        data = cfg.to_dict()

    with open(dest, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return dest


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Manifest & CLI Inspector)
# =============================================================================

CLIENT_CONFIG: Dict[str, Any] = resolve_config_manifest()
CLIENT_SETTINGS: ClientConfig = load_client_config()

__all__ = [
    "ClientConfig",
    "CLIENT_CONFIG",
    "CLIENT_SETTINGS",
    "load_client_config",
    "resolve_config_manifest",
    "sync_manifest_from_settings",
]


if __name__ == "__main__":
    print("=== 🎮 Yu-Gi-Oh! Player Client Configuration Manifest ===")
    print(f"Server Name     : {CLIENT_SETTINGS.server_name}")
    print(f"Direct Connect  : {CLIENT_SETTINGS.direct_connect_address}")
    print(f"Fallback Connect: {CLIENT_SETTINGS.fallback_connect_address}")
    print(f"Web Catalog     : {CLIENT_SETTINGS.web_catalog_url}")
    print(f"Updates URL     : {CLIENT_SETTINGS.expansions_update_url}")
