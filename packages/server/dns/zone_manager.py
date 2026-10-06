#!/usr/bin/env python3
# =============================================================================
# BLOCK 1: METADATA BLOCK
# =============================================================================
"""
Module: packages.server.dns.zone_manager
Architecture: Hybrid Systems Engineering (Server Infrastructure & Deployment)
Subsystem: DNS & Domain Routing Management
Description:
    Authoritative BIND RFC 1035 Zone File Generator, Validator, and Synchronizer.
    Manages DNS routing rules for Cloudflare Zero Trust Argo Tunnels, raw TCP
    game sockets (Port 7911/7922), and Dynamic DNS fallback endpoints.

Responsibilities:
    1. Render compliant RFC 1035 / BIND 9 zone files from active environment settings.
    2. Validate zone file syntax, origin headers, TTL directives, and record integrity.
    3. Synchronize zone files dynamically during packaging or deployment cycles.
    4. Provide CLI inspection and validation for platform diagnostics.

Exported API:
    - DNSZoneRecord: Strongly-typed record model
    - render_zone_content(): Dynamic string renderer
    - validate_zone_content(): RFC 1035 syntax & semantic rule validator
    - sync_zone_file_from_settings(): Settings-driven synchronization engine
    - load_zone_file(): Zone file loader and parser
"""

# =============================================================================
# BLOCK 2: OPENING BLOCK (Inclusions & Imports)
# =============================================================================

import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

# Ensure project root is available in sys.path
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_CURRENT_DIR))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from config.paths import (
    BASE_DIR,
    SERVER_PACKAGE_DIR,
)
from config.settings import settings


# Canonical Zone File Path
DEFAULT_ZONE_FILE_PATH: str = os.path.join(_CURRENT_DIR, "thelandofkustomazi.com.zone")


# =============================================================================
# BLOCK 3: BODY BLOCK (Core DNS Zone Operations)
# =============================================================================

# -----------------------------------------------------------------------------
# Sub-Block 3.1: Data Models
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class DNSZoneRecord:
    """Strongly-typed DNS record representation within an RFC 1035 zone."""
    name: str
    record_type: str
    target: str
    ttl: Optional[int] = None
    proxied: bool = False
    comment: str = ""

    def to_zone_line(self) -> str:
        """Render single DNS record line formatted for BIND zone file."""
        ttl_str = f" {self.ttl}" if self.ttl else ""
        return f"{self.name:<8} IN  {self.record_type:<7}{ttl_str} {self.target}"


# -----------------------------------------------------------------------------
# Sub-Block 3.2: Zone Content Renderer
# -----------------------------------------------------------------------------
def render_zone_content(
    origin: str = "thelandofkustomazi.com",
    ttl: int = 3600,
    tunnel_id: str = "c346aa27-b4c1-41ba-815c-f66b2b84243b",
    direct_ip: str = "147.224.147.30",
    duckdns_domain: str = "thelandofkustomazi.duckdns.org",
) -> str:
    """Renders a fully-formed RFC 1035 / BIND 9 zone file.
    
    Args:
        origin (str): Apex domain origin without trailing dot.
        ttl (int): Default Time-to-Live in seconds.
        tunnel_id (str): Cloudflare Zero Trust Tunnel UUID.
        direct_ip (str): Direct public IPv4 address for raw TCP game sockets.
        duckdns_domain (str): Dynamic DNS fallback hostname.
        
    Returns:
        str: Formatted BIND zone file content compatible with Cloudflare import.
    """
    clean_origin = origin.strip().rstrip(".")
    tunnel_target = f"{tunnel_id}.cfargotunnel.com."
    
    return f"""; =============================================================================
; BIND Zone File for {clean_origin}
; Compatible with Cloudflare DNS Zone File Import
; Subsystem: packages/server/dns (Yu-Gi-Oh! Server Infrastructure)
; Generated for Yu-Gi-Oh! Platform (Web Card Catalog & Game Simulator)
; =============================================================================
$ORIGIN {clean_origin}.
$TTL {ttl}

; =============================================================================
; 1. WEBSITE & CARD CATALOG (HTTP/HTTPS - Port 8000)
; =============================================================================
; Option A: Cloudflare Tunnel (Recommended)
; Tunnel ID: {tunnel_id}
; Provides instant DDoS protection, SSL certificates, and zero open web ports.
@       IN  CNAME   {tunnel_target}
www     IN  CNAME   {tunnel_target}

; Option B: Direct Oracle Cloud Public IP (Alternative if not using Tunnel)
; If using direct IP instead of Tunnel, comment out Option A above and uncomment below:
; @     IN  A       {direct_ip}
; www   IN  CNAME   {clean_origin}.

; =============================================================================
; 2. YU-GI-OH! SIMULATOR & EDOPro PROTOCOL (TCP 7911 & 7922)
; =============================================================================
; [IMPORTANT] Cloudflare Proxy Status MUST be DNS-ONLY (Grey Cloud) for this!
; Cloudflare's standard CDN proxy only supports HTTP/HTTPS web traffic.
; Raw TCP game socket connections (Port 7911) will fail if Proxied (Orange Cloud).
play    IN  A       {direct_ip}
sim     IN  A       {direct_ip}

; =============================================================================
; 3. DYNAMIC DNS FALLBACK (Optional)
; =============================================================================
; If your server IP ever changes dynamically, you can use DuckDNS as an alias:
; play  IN  CNAME   {duckdns_domain}.
"""


# -----------------------------------------------------------------------------
# Sub-Block 3.3: Zone Content Syntax & Semantic Validator
# -----------------------------------------------------------------------------
def validate_zone_content(content: str) -> Tuple[bool, List[str]]:
    """Validates zone file content for RFC 1035 compliance and platform requirements.
    
    Args:
        content (str): Raw zone file text content.
        
    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_error_messages)
    """
    errors: List[str] = []
    
    if not content or not content.strip():
        return False, ["Zone content is empty."]
    
    # Check mandatory directives
    origin_match = re.search(r"^\$ORIGIN\s+([a-zA-Z0-9.\-_]+)", content, re.MULTILINE)
    if not origin_match:
        errors.append("Missing mandatory $ORIGIN directive.")
    
    ttl_match = re.search(r"^\$TTL\s+(\d+)", content, re.MULTILINE)
    if not ttl_match:
        errors.append("Missing mandatory $TTL directive.")
    elif int(ttl_match.group(1)) <= 0:
        errors.append(f"Invalid $TTL directive: {ttl_match.group(1)} (must be > 0).")
    
    # Check Web Catalog routing (CNAME or A for @ and www)
    has_apex = bool(re.search(r"^@\s+IN\s+(CNAME|A)\s+", content, re.MULTILINE))
    has_www = bool(re.search(r"^www\s+IN\s+(CNAME|A)\s+", content, re.MULTILINE))
    if not has_apex:
        errors.append("Missing mandatory apex '@' routing record.")
    if not has_www:
        errors.append("Missing mandatory 'www' routing record.")
        
    # Check Game Simulator direct routing (play / sim)
    has_play = bool(re.search(r"^play\s+IN\s+(A|CNAME)\s+", content, re.MULTILINE))
    has_sim = bool(re.search(r"^sim\s+IN\s+(A|CNAME)\s+", content, re.MULTILINE))
    if not has_play:
        errors.append("Missing mandatory 'play' simulator routing record.")
    if not has_sim:
        errors.append("Missing mandatory 'sim' simulator routing record.")
        
    # Verify IPv4 formatting for active A records
    a_records = re.findall(r"^[a-zA-Z0-9@*._-]+\s+IN\s+A\s+([0-9.]+)", content, re.MULTILINE)
    ip_pattern = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
    for ip in a_records:
        if not ip_pattern.match(ip):
            errors.append(f"Invalid IPv4 address in A record: {ip}")
        else:
            octets = [int(o) for o in ip.split(".")]
            if any(o < 0 or o > 255 for o in octets):
                errors.append(f"IPv4 octet out of bounds (0-255) in A record: {ip}")
                
    # Verify Cloudflare tunnel target formatting
    cname_records = re.findall(r"^[a-zA-Z0-9@*._-]+\s+IN\s+CNAME\s+([a-zA-Z0-9.\-_]+)", content, re.MULTILINE)
    for cname in cname_records:
        if "cfargotunnel.com" in cname:
            if not re.match(r"^[a-f0-9\-]+\.cfargotunnel\.com\.?$", cname):
                errors.append(f"Malformed Cloudflare Argo Tunnel target: {cname}")

    return len(errors) == 0, errors


# -----------------------------------------------------------------------------
# Sub-Block 3.4: Settings Synchronization & File Management
# -----------------------------------------------------------------------------
def sync_zone_file_from_settings(zone_file_path: Optional[str] = None) -> bool:
    """Synchronizes the authoritative zone file using current active settings.
    
    Args:
        zone_file_path (Optional[str]): Target zone file path. Defaults to DEFAULT_ZONE_FILE_PATH.
        
    Returns:
        bool: True if file was updated or verified successfully, False on error.
    """
    target_path = zone_file_path or DEFAULT_ZONE_FILE_PATH
    
    # Resolve parameters from centralized settings singleton
    origin = settings.network.public_domain
    tunnel_id = settings.cloudflare.tunnel_id
    direct_ip = settings.simulator.fallback_host
    duckdns_domain = settings.duckdns.full_domain
    
    # Default fallback for unconfigured environments
    if not direct_ip or direct_ip == "thelandofkustomazi.com":
        direct_ip = "147.224.147.30"
    if not tunnel_id:
        tunnel_id = "c346aa27-b4c1-41ba-815c-f66b2b84243b"
        
    content = render_zone_content(
        origin=origin,
        ttl=3600,
        tunnel_id=tunnel_id,
        direct_ip=direct_ip,
        duckdns_domain=duckdns_domain,
    )
    
    is_valid, errors = validate_zone_content(content)
    if not is_valid:
        print(f"[!] Warning: Generated zone content failed validation: {'; '.join(errors)}", file=sys.stderr)
        return False
        
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return True


def load_zone_file(zone_file_path: Optional[str] = None) -> str:
    """Reads and returns the content of the authoritative zone file.
    
    Args:
        zone_file_path (Optional[str]): Zone file path. Defaults to DEFAULT_ZONE_FILE_PATH.
        
    Returns:
        str: Raw zone file content.
    """
    target_path = zone_file_path or DEFAULT_ZONE_FILE_PATH
    if not os.path.exists(target_path):
        raise FileNotFoundError(f"DNS zone file not found at {target_path}")
    with open(target_path, "r", encoding="utf-8") as f:
        return f.read()


# =============================================================================
# BLOCK 4: CLOSING BLOCK (Public Package Manifest & CLI Entry Point)
# =============================================================================

__all__ = [
    "DNSZoneRecord",
    "DEFAULT_ZONE_FILE_PATH",
    "render_zone_content",
    "validate_zone_content",
    "sync_zone_file_from_settings",
    "load_zone_file",
]

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--sync":
        success = sync_zone_file_from_settings()
        print(f"Zone sync: {'SUCCESS' if success else 'FAILED'}")
    else:
        try:
            zone_text = load_zone_file()
            valid, errs = validate_zone_content(zone_text)
            if valid:
                print(f"[+] DNS Zone file is VALID: {DEFAULT_ZONE_FILE_PATH}")
                print(f"    Origin: {settings.network.public_domain}")
                print(f"    Tunnel: {settings.cloudflare.tunnel_id}")
                print(f"    Direct: {settings.simulator.fallback_host}")
            else:
                print(f"[-] DNS Zone file has validation ERRORS:")
                for e in errs:
                    print(f"    • {e}")
                sys.exit(1)
        except Exception as ex:
            print(f"[-] Error: {ex}", file=sys.stderr)
            sys.exit(1)
