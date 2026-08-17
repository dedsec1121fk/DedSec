#!/usr/bin/env python3
"""
Digital Footprint Finder.py
=================

Public-source OSINT casework toolkit for lawful, authorized investigations.

Design goals
------------
- One-file Python tool with self-maintaining optional enrichers.
- Easy Mode: enter one target and get a case + report automatically.
- Case-centric workflow backed by SQLite.
- Entity/relation graph instead of disconnected search results.
- Evidence capture with SHA-256 hashes and UTC timestamps.
- Native public-source pivots for domains, URLs, usernames, emails, IPs, names, phones, and local files.
- Keyless public APIs by default, plus optional user-configured API credentials for additional enrichment.
- Built-in profile-baseline detection, passive host discovery, bounded site crawling, JS endpoint discovery, and correlation.
- Cross-source confidence, contradictions, timelines, relationship paths, correlation clusters, and evidence integrity checks.
- Markdown, JSON, CSV, GraphML, STIX 2.1, raw-evidence, ZIP-package, and self-contained HTML exports.
- First-class Termux workspace and Downloads case folders.
- Works well in Termux, Linux, macOS, and Windows with Python 3.10+.

Important
---------
This program is intended for legitimate OSINT, cybersecurity education,
journalism, due diligence, and investigations using information you are
authorized to access. It does not bypass authentication, access private
accounts, retrieve stolen credentials, or defeat access controls.

Some public services used by this script can rate-limit or change behavior.
Results should be treated as leads and independently verified.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import contextlib
import datetime as dt
import difflib
import getpass
import base64
import hashlib
import html
import ipaddress
import importlib
import io
import json
import math
import heapq
import os
import re
import shutil
import shlex
import site
import socket
import ssl
import sqlite3
import subprocess
import sys
import textwrap
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import uuid
import webbrowser
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

APP_NAME = "Digital Footprint Finder"
DEFAULT_TIMEOUT = 10
MAX_HTTP_BYTES = 2_000_000
USER_AGENT = "DigitalFootprintFinder (public-source research; local-user)"

# ---------------------------------------------------------------------------
# MAINTENANCE NOTES
# ---------------------------------------------------------------------------
# Keep provider URLs and site templates in one place so upstream changes are easy to fix.
# Digital Footprint Finder implements its investigation capabilities natively. It must NOT clone,
# install, import, or execute third-party OSINT projects. Similar useful techniques are
# independently implemented below so one file remains the investigation engine.
# Mandatory functionality must continue to work with the Python standard library.
# Optional small Python packages are installed into ~/Digital Footprint Finder/dependencies, never globally.
# Every public source must fail soft: one unavailable API must not abort a case.
# Never treat a search/API/profile candidate as confirmed identity without corroboration.
# Confidence is confidence in an observation, not a declaration that two people are identical.
# Keep crawling polite: public pages only, respect robots.txt, cap pages, and avoid auth/session use.
# Do not add credential, breach-dump, secret-extraction, authentication-bypass, or exploit features.
# Keep result storage stable: Downloads/Digital Footprint Finder/<Case Name>/files.

APP_HOME = Path.home() / "Digital Footprint Finder"
DATA_DIR = APP_HOME / "data"
CACHE_DIR = APP_HOME / "cache"
DEPENDENCY_DIR = APP_HOME / "dependencies"
LOG_DIR = APP_HOME / "logs"
DEFAULT_DB_PATH = DATA_DIR / "digital_footprint_finder.db"
SETTINGS_PATH = APP_HOME / "settings.json"
SESSION_PATH = APP_HOME / "session.json"
API_KEYS_PATH = APP_HOME / "api_keys.json"

# API keys are optional. The tool remains fully usable with keyless public sources.
# Keys are never written to reports/evidence and are masked in the UI.
API_PROVIDERS = {
    "github": {
        "label": "GitHub",
        "env": ("DIGITAL_FOOTPRINT_FINDER_GITHUB_TOKEN", "GITHUB_TOKEN"),
        "purpose": "Higher REST API limits for public GitHub enrichment",
    },
    "virustotal": {
        "label": "VirusTotal",
        "env": ("DIGITAL_FOOTPRINT_FINDER_VIRUSTOTAL_API_KEY", "VIRUSTOTAL_API_KEY"),
        "purpose": "Public reputation/context for domains, IPs, URLs and SHA-256 hashes",
    },
    "urlscan": {
        "label": "urlscan.io",
        "env": ("DIGITAL_FOOTPRINT_FINDER_URLSCAN_API_KEY", "URLSCAN_API_KEY"),
        "purpose": "Search existing public website-scan history; never submits scans",
    },
    "shodan": {
        "label": "Shodan",
        "env": ("DIGITAL_FOOTPRINT_FINDER_SHODAN_API_KEY", "SHODAN_API_KEY"),
        "purpose": "Passive public host/service observations for public IP addresses",
    },
    "openalex": {
        "label": "OpenAlex",
        "env": ("DIGITAL_FOOTPRINT_FINDER_OPENALEX_API_KEY", "OPENALEX_API_KEY"),
        "purpose": "Optional authenticated scholarly-graph access",
    },
}

OPTIONAL_API_ENDPOINTS = {
    "virustotal_domain": "https://www.virustotal.com/api/v3/domains/{value}",
    "virustotal_ip": "https://www.virustotal.com/api/v3/ip_addresses/{value}",
    "virustotal_url": "https://www.virustotal.com/api/v3/urls/{value}",
    "virustotal_file": "https://www.virustotal.com/api/v3/files/{value}",
    "urlscan_search": "https://urlscan.io/api/v1/search/?{query}",
    "shodan_host": "https://api.shodan.io/shodan/host/{ip}?key={key}",
}

KEYLESS_PUBLIC_API_CATALOG = [
    {"name": "Google Public DNS", "purpose": "DNS-over-HTTPS fallback and record resolution"},
    {"name": "RDAP.org", "purpose": "Public domain and IP registration data"},
    {"name": "crt.sh", "purpose": "Certificate Transparency hostname observations"},
    {"name": "Internet Archive CDX", "purpose": "Historical public URLs and hostnames"},
    {"name": "GitHub REST API", "purpose": "Public profiles, repositories and low-confidence name candidates"},
    {"name": "GitLab API", "purpose": "Public profile candidates"},
    {"name": "ipwho.is", "purpose": "Approximate public IP network/location context"},
    {"name": "RIPEstat", "purpose": "ASN, prefix, reverse-DNS and routing context"},
    {"name": "HackerTarget", "purpose": "Passive host and reverse-IP observations within provider limits"},
    {"name": "AlienVault OTX", "purpose": "Passive DNS observations"},
    {"name": "Common Crawl", "purpose": "Historical public web-index observations"},
    {"name": "Wikidata", "purpose": "Public person and organization candidates"},
    {"name": "Crossref", "purpose": "Public scholarly publication/author context"},
    {"name": "ROR", "purpose": "Public research-organization identity context"},
    {"name": "OpenAlex", "purpose": "Public scholarly author/institution context"},
    {"name": "Stack Exchange", "purpose": "Low-confidence public community-profile candidates"},
]

DEFAULT_SETTINGS = {
    "default_mode": "auto",
    "network_timeout": DEFAULT_TIMEOUT,
    "guided_followup": True,
    "auto_open_report": False,
    "auto_install_dependencies": True,
    "search_scope": "current",
    "search_limit": 25,
    "colors": "auto",
    "resume_latest_case": True,
    "max_crawl_pages": 18,
    "username_workers": 8,
    "json_cache_ttl": 900,
    "save_raw_evidence": True,
}

# Pure-Python enrichers. If installation fails, the relevant feature degrades cleanly.
BOOTSTRAP_PACKAGES = {
    "bs4": "beautifulsoup4",
    "dns": "dnspython",
    "phonenumbers": "phonenumbers",
    "exifread": "exifread",
    "pypdf": "pypdf",
}

FREE_API_ENDPOINTS = {
    # DNS / registration / archive
    "google_dns": "https://dns.google/resolve",
    "rdap_domain": "https://rdap.org/domain/{value}",
    "rdap_ip": "https://rdap.org/ip/{value}",
    "crtsh": "https://crt.sh/?q={query}&output=json",
    "wayback_cdx": "https://web.archive.org/cdx/search/cdx",

    # Public developer identity sources
    "github_user": "https://api.github.com/users/{username}",
    "github_user_repos": "https://api.github.com/users/{username}/repos?per_page=30&sort=updated",
    "github_user_search": "https://api.github.com/search/users?q={query}&per_page=5",
    "gitlab_users": "https://gitlab.com/api/v4/users?{query}",

    # Network intelligence / passive host observations
    "ipwhois": "https://ipwho.is/{ip}",
    "ripe_network_info": "https://stat.ripe.net/data/network-info/data.json?resource={resource}",
    "ripe_reverse_dns": "https://stat.ripe.net/data/reverse-dns-ip/data.json?resource={resource}",
    "hackertarget_hostsearch": "https://api.hackertarget.com/hostsearch/?q={domain}",
    "hackertarget_reverseip": "https://api.hackertarget.com/reverseiplookup/?q={ip}",
    "otx_passive_dns": "https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns",

    # Large public web / knowledge / scholarly indexes
    "commoncrawl_collections": "https://index.commoncrawl.org/collinfo.json",
    "wikidata_api": "https://www.wikidata.org/w/api.php",
    "crossref_works": "https://api.crossref.org/works",

    # Routing / ASN / prefix intelligence
    "ripe_as_overview": "https://stat.ripe.net/data/as-overview/data.json?resource={resource}",
    "ripe_announced_prefixes": "https://stat.ripe.net/data/announced-prefixes/data.json?resource={resource}",
    "ripe_prefix_overview": "https://stat.ripe.net/data/prefix-overview/data.json?resource={resource}",

    # Organization / scholarly identity
    "ror_organizations": "https://api.ror.org/v2/organizations",
    "openalex_authors": "https://api.openalex.org/authors",
    "openalex_institutions": "https://api.openalex.org/institutions",

    # Public community identity context
    "stackexchange_users": "https://api.stackexchange.com/2.3/users",
}


USERNAME_SITES = {
    # Developer / technical
    "GitHub": "https://github.com/{username}",
    "GitLab": "https://gitlab.com/{username}",
    "Codeberg": "https://codeberg.org/{username}",
    "SourceHut": "https://sr.ht/~{username}/",
    "Docker Hub": "https://hub.docker.com/u/{username}",
    "PyPI": "https://pypi.org/user/{username}/",
    "npm": "https://www.npmjs.com/~{username}",
    "Replit": "https://replit.com/@{username}",
    "Kaggle": "https://www.kaggle.com/{username}",
    "DEV Community": "https://dev.to/{username}",
    "Hacker News": "https://news.ycombinator.com/user?id={username}",
    "LeetCode": "https://leetcode.com/u/{username}/",
    "HackerRank": "https://www.hackerrank.com/profile/{username}",
    "TryHackMe": "https://tryhackme.com/p/{username}",
    "Keybase": "https://keybase.io/{username}",

    # Social / publishing
    "Reddit": "https://www.reddit.com/user/{username}/",
    "Medium": "https://medium.com/@{username}",
    "Tumblr": "https://www.tumblr.com/{username}",
    "Pinterest": "https://www.pinterest.com/{username}/",
    "Twitch": "https://www.twitch.tv/{username}",
    "YouTube Handle": "https://www.youtube.com/@{username}",
    "TikTok": "https://www.tiktok.com/@{username}",
    "Instagram": "https://www.instagram.com/{username}/",
    "X": "https://x.com/{username}",
    "Threads": "https://www.threads.net/@{username}",
    "Mastodon.social": "https://mastodon.social/@{username}",
    "Quora": "https://www.quora.com/profile/{username}",
    "About.me": "https://about.me/{username}",
    "Linktree": "https://linktr.ee/{username}",
    "Substack": "https://substack.com/@{username}",

    # Creative / media
    "Behance": "https://www.behance.net/{username}",
    "Dribbble": "https://dribbble.com/{username}",
    "Vimeo": "https://vimeo.com/{username}",
    "SoundCloud": "https://soundcloud.com/{username}",
    "Flickr": "https://www.flickr.com/people/{username}/",
    "Last.fm": "https://www.last.fm/user/{username}",
    "Letterboxd": "https://letterboxd.com/{username}/",

    # Gaming / communities
    "Steam Community": "https://steamcommunity.com/id/{username}",
    "Chess.com": "https://www.chess.com/member/{username}",
    "Lichess": "https://lichess.org/@/{username}",
    "Speedrun.com": "https://www.speedrun.com/users/{username}",
    "Product Hunt": "https://www.producthunt.com/@{username}",

    # Creator pages
    "Ko-fi": "https://ko-fi.com/{username}",
    "Buy Me a Coffee": "https://www.buymeacoffee.com/{username}",
    "Patreon": "https://www.patreon.com/{username}",
    "WordPress.com": "https://{username}.wordpress.com/",
}


SEARCH_ENGINES = {
    "Google": "https://www.google.com/search?q={q}",
    "Bing": "https://www.bing.com/search?q={q}",
    "DuckDuckGo": "https://duckduckgo.com/?q={q}",
}

PROFILE_NEGATIVE_MARKERS = (
    "user not found", "profile not found", "page not found", "account not found",
    "this page doesn't exist", "this page does not exist", "sorry, nobody on reddit",
    "the specified profile could not be found", "404 not found", "doesn’t exist",
    "doesn't exist", "no such user", "unknown user",
)

DOCUMENT_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".csv", ".txt", ".rtf", ".odt", ".ods", ".xml", ".json",
}

SOCIAL_HOST_HINTS = (
    "github.com", "gitlab.com", "linkedin.com", "x.com", "twitter.com",
    "instagram.com", "facebook.com", "youtube.com", "youtu.be", "tiktok.com",
    "reddit.com", "medium.com", "dev.to", "twitch.tv", "mastodon",
    "bsky.app", "threads.net", "linktr.ee", "keybase.io",
)

SECURITY_HEADERS = (
    "strict-transport-security",
    "content-security-policy",
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
    "permissions-policy",
)

ENTITY_TYPES = {
    "person", "username", "email", "phone", "domain", "url", "ip",
    "organization", "location", "file", "hash", "social", "note", "other",
    "asn", "prefix", "publication", "identifier", "technology", "service",
    "fediverse", "claim"
}


# ---------------------------------------------------------------------------
# Workspace / bootstrap
# ---------------------------------------------------------------------------

def is_termux() -> bool:
    prefix = os.environ.get("PREFIX", "")
    return "com.termux" in prefix or Path("/data/data/com.termux").exists()


def ensure_workspace() -> None:
    """Create the persistent Digital Footprint Finder home workspace."""
    for directory in (APP_HOME, DATA_DIR, CACHE_DIR, DEPENDENCY_DIR, LOG_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    dep = str(DEPENDENCY_DIR)
    if dep not in sys.path:
        sys.path.insert(0, dep)


def load_settings() -> dict[str, Any]:
    """Load persistent settings, merging future defaults without breaking old files."""
    ensure_workspace()
    data: dict[str, Any] = {}
    if SETTINGS_PATH.is_file():
        with contextlib.suppress(Exception):
            raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data = raw
    merged = dict(DEFAULT_SETTINGS)
    merged.update({k: v for k, v in data.items() if k in DEFAULT_SETTINGS})
    return merged


def save_settings(settings: dict[str, Any]) -> None:
    ensure_workspace()
    clean = dict(DEFAULT_SETTINGS)
    clean.update({k: v for k, v in settings.items() if k in DEFAULT_SETTINGS})
    SETTINGS_PATH.write_text(json.dumps(clean, indent=2, ensure_ascii=False), encoding="utf-8")


def load_session() -> dict[str, Any]:
    if not SESSION_PATH.is_file():
        return {}
    with contextlib.suppress(Exception):
        value = json.loads(SESSION_PATH.read_text(encoding="utf-8"))
        if isinstance(value, dict):
            return value
    return {}


def save_session(**values: Any) -> None:
    ensure_workspace()
    session = load_session()
    session.update(values)
    session["updated_at"] = utcnow()
    SESSION_PATH.write_text(json.dumps(session, indent=2, ensure_ascii=False), encoding="utf-8")


def load_api_keys() -> dict[str, str]:
    """Load optional provider keys. Unknown fields are ignored and secrets are never exported."""
    ensure_workspace()
    if not API_KEYS_PATH.is_file():
        return {}
    with contextlib.suppress(Exception):
        raw = json.loads(API_KEYS_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            return {k: str(v).strip() for k, v in raw.items() if k in API_PROVIDERS and str(v).strip()}
    return {}


def save_api_keys(keys: dict[str, str]) -> None:
    ensure_workspace()
    clean = {k: str(v).strip() for k, v in keys.items() if k in API_PROVIDERS and str(v).strip()}
    tmp = API_KEYS_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(clean, indent=2, ensure_ascii=False), encoding="utf-8")
    with contextlib.suppress(Exception):
        os.chmod(tmp, 0o600)
    tmp.replace(API_KEYS_PATH)
    with contextlib.suppress(Exception):
        os.chmod(API_KEYS_PATH, 0o600)


def get_api_key(provider: str) -> str:
    provider = provider.lower().strip()
    meta = API_PROVIDERS.get(provider) or {}
    for env_name in meta.get("env", ()):
        value = os.environ.get(str(env_name), "").strip()
        if value:
            return value
    return load_api_keys().get(provider, "").strip()


def api_provider_status() -> dict[str, dict[str, Any]]:
    saved = load_api_keys()
    out: dict[str, dict[str, Any]] = {}
    for name, meta in API_PROVIDERS.items():
        env_source = next((e for e in meta.get("env", ()) if os.environ.get(str(e), "").strip()), None)
        out[name] = {
            "label": meta["label"],
            "configured": bool(env_source or saved.get(name)),
            "source": "environment" if env_source else ("secure local file" if saved.get(name) else "not configured"),
            "purpose": meta["purpose"],
        }
    return out


def api_status_report() -> dict[str, Any]:
    return {
        "keyless_public_sources": KEYLESS_PUBLIC_API_CATALOG,
        "optional_credentials": api_provider_status(),
        "privacy": "API credential values are never printed or exported into case reports.",
    }


def api_headers(provider: str) -> dict[str, str]:
    key = get_api_key(provider)
    if not key:
        return {}
    if provider == "github":
        return {"Authorization": f"Bearer {key}", "Accept": "application/vnd.github+json"}
    if provider == "virustotal":
        return {"x-apikey": key}
    if provider == "urlscan":
        return {"api-key": key}
    return {}


def redact_url_secrets(url: str) -> str:
    """Remove common credential query parameters before anything is displayed or persisted."""
    try:
        parts = urllib.parse.urlsplit(url)
        pairs = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
        hidden = {"key", "token", "api_key", "apikey", "access_token"}
        safe = [(k, "<redacted>" if k.lower() in hidden else v) for k, v in pairs]
        return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, urllib.parse.urlencode(safe), parts.fragment))
    except Exception:
        return url


def api_keys_menu() -> None:
    while True:
        status = api_provider_status()
        UI.title("Optional APIs")
        names = list(API_PROVIDERS)
        for i, name in enumerate(names, 1):
            row = status[name]
            state = "configured" if row["configured"] else "not configured"
            print(f"[{i}] {row['label']:<16} {state:<16} {row['purpose']}")
        print("[R] Remove a saved API key")
        print("[0] Back")
        raw = input("Choose provider: ").strip().lower()
        if raw in {"", "0"}:
            return
        if raw == "r":
            target = input("Provider name to remove: ").strip().lower()
            if target not in API_PROVIDERS:
                UI.err("Unknown provider.")
                continue
            keys = load_api_keys(); keys.pop(target, None); save_api_keys(keys); UI.ok("Saved key removed.")
            continue
        try:
            provider = names[int(raw)-1]
        except (ValueError, IndexError):
            UI.err("Invalid choice.")
            continue
        value = getpass.getpass(f"{API_PROVIDERS[provider]['label']} API key/token (input hidden): ").strip()
        if not value:
            UI.warn("Nothing changed.")
            continue
        keys = load_api_keys(); keys[provider] = value; save_api_keys(keys); UI.ok("API credential saved locally with restricted permissions.")


def apply_color_setting(settings: Optional[dict[str, Any]] = None) -> None:
    settings = settings or load_settings()
    mode = str(settings.get("colors", "auto")).lower()
    if "UI" in globals():
        if mode == "on":
            UI.COLOR = True
        elif mode == "off":
            UI.COLOR = False
        else:
            UI.COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def ensure_termux_storage() -> Optional[Path]:
    """Return Termux Downloads. Ask Android for storage permission once if needed."""
    downloads = Path.home() / "storage" / "downloads"
    if downloads.is_dir():
        return downloads
    if is_termux():
        setup = shutil.which("termux-setup-storage")
        if setup:
            with contextlib.suppress(Exception):
                subprocess.run([setup], timeout=20, check=False)
            # Android may need a moment after the permission dialog is accepted.
            for _ in range(6):
                if downloads.is_dir():
                    return downloads
                time.sleep(0.5)
    return None


def _module_available(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except Exception:
        return False


def bootstrap_dependencies(verbose: bool = True) -> dict[str, str]:
    """
    Install small optional enrichers locally when missing.

    Nothing is installed into the global Python/Termux environment. The script keeps
    functioning if installation is unavailable; this is intentionally best-effort.
    """
    ensure_workspace()
    status: dict[str, str] = {}
    settings = load_settings()
    if os.environ.get("DIGITAL_FOOTPRINT_FINDER_NO_INSTALL") == "1" or not settings.get("auto_install_dependencies", True):
        return {m: ("available" if _module_available(m) else "skipped") for m in BOOTSTRAP_PACKAGES}

    for module, package in BOOTSTRAP_PACKAGES.items():
        if _module_available(module):
            status[module] = "available"
            continue
        if verbose:
            print(f"[setup] Adding optional capability: {package}")
        cmd = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--no-input",
               "--target", str(DEPENDENCY_DIR), package]
        try:
            cp = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                timeout=180, check=False)
            importlib.invalidate_caches()
            status[module] = "installed" if cp.returncode == 0 and _module_available(module) else "unavailable"
        except Exception:
            status[module] = "unavailable"
    return status


def case_files_dir(case_name: str) -> Path:
    """Downloads/Digital Footprint Finder/<Case Name>/files, with a home fallback if permission is unavailable."""
    base_downloads = ensure_termux_storage()
    if base_downloads is None:
        # Non-Termux systems get a conventional Downloads folder when possible.
        candidate = Path.home() / "Downloads"
        if candidate.exists() or not is_termux():
            with contextlib.suppress(Exception):
                candidate.mkdir(parents=True, exist_ok=True)
            base_downloads = candidate if candidate.exists() else None
    base = (base_downloads / "Digital Footprint Finder") if base_downloads else (APP_HOME / "results")
    out = base / safe_filename(case_name) / "files"
    out.mkdir(parents=True, exist_ok=True)
    return out

# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def clean_domain(value: str) -> str:
    value = value.strip().lower()
    if "://" in value:
        value = urllib.parse.urlsplit(value).hostname or value
    value = value.split("/")[0].rstrip(".")
    try:
        value = value.encode("idna").decode("ascii")
    except UnicodeError:
        pass
    return value


def normalize_url(value: str) -> str:
    value = value.strip()
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", value):
        value = "https://" + value
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http:// and https:// URLs are supported.")
    if not parsed.hostname:
        raise ValueError("URL has no hostname.")
    return urllib.parse.urlunsplit(parsed)


def is_public_ip(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    return not (
        ip.is_private or ip.is_loopback or ip.is_link_local or
        ip.is_multicast or ip.is_reserved or ip.is_unspecified
    )


def safe_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return value[:100] or "item"


def pretty_json(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True)


def truncate(value: str, n: int = 180) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    return value if len(value) <= n else value[: n - 1] + "…"


def extract_title(body: bytes) -> Optional[str]:
    text = body[:500_000].decode("utf-8", errors="replace")
    m = re.search(r"<title\b[^>]*>(.*?)</title\s*>", text, re.I | re.S)
    if not m:
        return None
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()


def extract_links(base_url: str, body: bytes, limit: int = 100) -> list[str]:
    text = body[:1_000_000].decode("utf-8", errors="replace")
    raw = re.findall(r"""href\s*=\s*["']([^"'#]+)["']""", text, flags=re.I)
    out: list[str] = []
    seen: set[str] = set()
    for href in raw:
        with contextlib.suppress(Exception):
            u = urllib.parse.urljoin(base_url, html.unescape(href.strip()))
            p = urllib.parse.urlsplit(u)
            if p.scheme in {"http", "https"}:
                u = urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, p.query, ""))
                if u not in seen:
                    seen.add(u)
                    out.append(u)
                    if len(out) >= limit:
                        break
    return out




def human_size(n: int) -> str:
    value = float(max(0, n))
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"


def strip_tags(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", value or "")).strip()


def extract_document_metadata_bytes(body: bytes, suffix: str) -> dict[str, Any]:
    """Extract metadata from a bounded public document body without writing it to disk."""
    suffix = suffix.lower()
    metadata: dict[str, Any] = {}
    if suffix == ".pdf":
        with contextlib.suppress(Exception):
            from pypdf import PdfReader  # type: ignore
            reader = PdfReader(io.BytesIO(body))
            values = {}
            if reader.metadata:
                values = {str(k): str(v)[:2000] for k, v in reader.metadata.items() if v is not None}
            metadata["pdf"] = {"pages": len(reader.pages), "metadata": values}
    elif suffix in {".docx", ".xlsx", ".pptx"}:
        with contextlib.suppress(Exception):
            with zipfile.ZipFile(io.BytesIO(body), "r") as zf:
                raw = zf.read("docProps/core.xml")
            root_xml = ET.fromstring(raw)
            core = {}
            for elem in root_xml.iter():
                tag = elem.tag.split("}")[-1]
                if elem.text and elem.text.strip():
                    core[tag] = elem.text.strip()[:2000]
            metadata["office_core_properties"] = core
    return metadata


def extract_page_intelligence(base_url: str, body: bytes) -> dict[str, Any]:
    """Extract conservative, explicitly public page metadata and contact leads."""
    text = body[:1_500_000].decode("utf-8", errors="replace")
    soup = None
    with contextlib.suppress(Exception):
        from bs4 import BeautifulSoup  # type: ignore
        soup = BeautifulSoup(text, "html.parser")

    def meta_value(*names: str) -> Optional[str]:
        if soup is not None:
            for name in names:
                tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", attrs={"property": name})
                if tag and tag.get("content"):
                    return str(tag.get("content")).strip()
        for name in names:
            patterns = [
                rf"<meta[^>]+(?:name|property)=[\"']{re.escape(name)}[\"'][^>]+content=[\"']([^\"']*)",
                rf"<meta[^>]+content=[\"']([^\"']*)[\"'][^>]+(?:name|property)=[\"']{re.escape(name)}[\"']",
            ]
            for pattern in patterns:
                m = re.search(pattern, text, re.I)
                if m:
                    return html.unescape(m.group(1)).strip()
        return None

    canonical = None
    if soup is not None:
        with contextlib.suppress(Exception):
            tag = soup.find("link", rel=lambda v: v and "canonical" in (v if isinstance(v, list) else [v]))
            if tag and tag.get("href"):
                canonical = urllib.parse.urljoin(base_url, str(tag.get("href")).strip())
    m = re.search(r"<link[^>]+rel=[\"']canonical[\"'][^>]+href=[\"']([^\"']+)", text, re.I)
    if not m:
        m = re.search(r"<link[^>]+href=[\"']([^\"']+)[\"'][^>]+rel=[\"']canonical[\"']", text, re.I)
    if m and not canonical:
        with contextlib.suppress(Exception):
            canonical = urllib.parse.urljoin(base_url, html.unescape(m.group(1)).strip())

    emails = sorted(set(
        match.group(0).rstrip(".,;:")
        for match in re.finditer(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I)
    ))[:30]

    phones: set[str] = set()
    visible_source = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", text, flags=re.I | re.S)
    visible_text = strip_tags(visible_source)
    if soup is not None:
        with contextlib.suppress(Exception):
            for noisy in soup(["script", "style", "noscript"]):
                noisy.decompose()
            visible_text = soup.get_text(" ", strip=True)
    for match in re.finditer(r"(?<!\w)(?:\+?\d[\d .()/-]{6,}\d)(?!\w)", visible_text):
        raw = re.sub(r"\s+", " ", match.group(0)).strip()
        digits = re.sub(r"\D", "", raw)
        if 8 <= len(digits) <= 16:
            phones.add(raw)

    links = extract_links(base_url, body, limit=300)
    social_links: list[str] = []
    documents: list[str] = []
    javascript: list[str] = []
    # href extraction intentionally stays generic; script src attributes need their own pass.
    script_sources: list[str] = []
    if soup is not None:
        with contextlib.suppress(Exception):
            for tag in soup.find_all("script", src=True):
                src = str(tag.get("src") or "").strip()
                if src:
                    script_sources.append(urllib.parse.urljoin(base_url, src))
    if not script_sources:
        for src in re.findall(r"<script\b[^>]*\bsrc=[\"']([^\"']+)[\"']", text, flags=re.I):
            with contextlib.suppress(Exception):
                script_sources.append(urllib.parse.urljoin(base_url, html.unescape(src.strip())))
    javascript.extend(script_sources)
    for link in links:
        host = (urllib.parse.urlsplit(link).hostname or "").lower()
        path = urllib.parse.urlsplit(link).path.lower()
        if any(hint in host for hint in SOCIAL_HOST_HINTS):
            social_links.append(link)
        if Path(path).suffix.lower() in DOCUMENT_EXTENSIONS:
            documents.append(link)
        if path.endswith(".js"):
            javascript.append(link)

    structured_items: list[dict[str, Any]] = []
    same_as: set[str] = set()
    structured_names: set[str] = set()
    # Parse JSON-LD from the original HTML string because the BeautifulSoup object above
    # is deliberately stripped of <script> tags before visible-text phone extraction.
    jsonld_blocks = re.findall(
        r"<script\b[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
        text, flags=re.I | re.S,
    )[:40]
    for raw in jsonld_blocks:
        with contextlib.suppress(Exception):
            parsed = json.loads(html.unescape(raw).strip())
            stack = parsed if isinstance(parsed, list) else [parsed]
            flattened: list[Any] = []
            while stack:
                item = stack.pop(0)
                if isinstance(item, dict):
                    flattened.append(item)
                    graph = item.get("@graph")
                    if isinstance(graph, list):
                        stack.extend(graph)
                elif isinstance(item, list):
                    stack.extend(item)
            for item in flattened[:80]:
                if not isinstance(item, dict):
                    continue
                summary = {k: item.get(k) for k in ("@type", "name", "url", "sameAs") if item.get(k) is not None}
                if summary:
                    structured_items.append(summary)
                name = item.get("name")
                if isinstance(name, str) and name.strip():
                    structured_names.add(name.strip())
                values = item.get("sameAs")
                if isinstance(values, str):
                    values = [values]
                if isinstance(values, list):
                    for value in values:
                        if isinstance(value, str) and value.startswith(("http://", "https://")):
                            same_as.add(value)

    favicons: list[str] = []
    forms: list[dict[str, Any]] = []
    if soup is not None:
        with contextlib.suppress(Exception):
            for tag in soup.find_all("link", href=True):
                rel = tag.get("rel") or []
                rel_text = " ".join(rel if isinstance(rel, list) else [str(rel)]).lower()
                if "icon" in rel_text:
                    favicons.append(urllib.parse.urljoin(base_url, str(tag.get("href")).strip()))
            for form in soup.find_all("form")[:40]:
                action = urllib.parse.urljoin(base_url, str(form.get("action") or "").strip())
                method = str(form.get("method") or "GET").upper()
                inputs = []
                for inp in form.find_all(["input", "textarea", "select"])[:60]:
                    name = str(inp.get("name") or "").strip()
                    typ = str(inp.get("type") or inp.name or "").strip().lower()
                    if name or typ:
                        inputs.append({"name": name, "type": typ})
                forms.append({"action": action, "method": method, "inputs": inputs})

    tracker_ids: set[str] = set()
    tracker_patterns = {
        "Google Analytics": r"\bG-[A-Z0-9]{6,15}\b",
        "Universal Analytics": r"\bUA-\d{4,12}-\d+\b",
        "Google Tag Manager": r"\bGTM-[A-Z0-9]{5,12}\b",
        "Google AdSense": r"\bca-pub-\d{8,20}\b",
        "Meta Pixel": r"fbq\s*\(\s*[\"']init[\"']\s*,\s*[\"'](\d{5,25})",
    }
    for family, pattern in tracker_patterns.items():
        for match in re.finditer(pattern, text, re.I):
            value = match.group(1) if match.lastindex else match.group(0)
            tracker_ids.add(f"{family}:{value}")

    return {
        "description": meta_value("description", "og:description", "twitter:description"),
        "og_title": meta_value("og:title", "twitter:title"),
        "og_site_name": meta_value("og:site_name"),
        "generator": meta_value("generator"),
        "canonical": canonical,
        "public_emails": emails,
        "public_phones": sorted(phones)[:20],
        "social_links": sorted(set(social_links))[:50],
        "documents": sorted(set(documents))[:100],
        "javascript": sorted(set(javascript))[:80],
        "structured_data": structured_items[:80],
        "structured_names": sorted(structured_names)[:50],
        "same_as": sorted(same_as)[:80],
        "favicons": sorted(set(favicons))[:20],
        "forms": forms[:40],
        "tracker_ids": sorted(tracker_ids)[:80],
    }


def detect_target_type(target: str) -> str:
    """Best-effort target classifier for Easy Mode."""
    target = target.strip()
    if not target:
        return "unknown"
    lowered = target.lower()
    explicit = {
        "org:": "organization", "organization:": "organization",
        "person:": "person", "username:": "username", "domain:": "domain",
        "url:": "url", "email:": "email", "ip:": "ip", "phone:": "phone",
        "file:": "file", "fediverse:": "fediverse", "doi:": "doi", "asn:": "asn",
        "prefix:": "prefix", "hash:": "hash",
    }
    for prefix, typ in explicit.items():
        if lowered.startswith(prefix) and target[len(prefix):].strip():
            return typ
    if re.fullmatch(r"@?[A-Za-z0-9_.-]{1,64}@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", target) and target.startswith("@"): 
        return "fediverse"
    if lowered.startswith("acct:") and "@" in target:
        return "fediverse"
    expanded = Path(strip_explicit_target_prefix(target)).expanduser()
    if expanded.exists() and expanded.is_file():
        return "file"
    if target.startswith(("http://", "https://")):
        return "url"
    if re.fullmatch(r"(?i)AS\d{1,10}", target):
        return "asn"
    with contextlib.suppress(ValueError):
        network = ipaddress.ip_network(target, strict=False)
        if "/" in target:
            return "prefix"
        ipaddress.ip_address(target)
        return "ip"
    if re.fullmatch(r"(?i)(?:doi:\s*)?10\.\d{4,9}/[-._;()/:A-Z0-9]+", target):
        return "doi"
    if re.fullmatch(r"(?i)(?:sha256:)?[a-f0-9]{64}", target):
        return "hash"
    if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", target):
        return "email"
    compact_phone = re.sub(r"[\s()./-]", "", target)
    if re.fullmatch(r"\+?\d{8,16}", compact_phone):
        return "phone"
    cleaned = clean_domain(target)
    if "." in cleaned and re.fullmatch(r"[a-z0-9.-]+", cleaned):
        return "domain"
    if lowered.startswith(("org:", "organization:")):
        return "organization"
    if " " in target:
        return "person"
    return "username"


def strip_explicit_target_prefix(target: str) -> str:
    """Remove user-friendly prefixes such as org:, doi:, asn:, prefix:, hash:."""
    value = target.strip()
    lowered = value.lower()
    for prefix in ("organization:", "username:", "domain:", "url:", "email:", "phone:",
                   "person:", "fediverse:", "prefix:", "hash:", "asn:", "doi:", "file:", "ip:", "org:"):
        if lowered.startswith(prefix):
            return value[len(prefix):].strip()
    return value

def auto_case_name(target: str) -> str:
    """Use a stable human-readable case name so repeated runs continue the same case."""
    target = re.sub(r"\s+", " ", target.strip())
    if detect_target_type(target) == "file":
        return Path(target).expanduser().name or "Local File"
    return truncate(target, 72) or "Investigation"


def default_report_dir(case_name: str = "General") -> Path:
    """Compatibility helper; new code should use case_files_dir(case_name)."""
    return case_files_dir(case_name)


def open_local_file(path: Path) -> bool:
    """Best-effort open using the platform default application."""
    try:
        return bool(webbrowser.open(path.resolve().as_uri()))
    except Exception:
        return False


@dataclass
class HTTPResult:
    requested_url: str
    final_url: str
    status: int
    headers: dict[str, str]
    body: bytes
    elapsed: float


def http_get(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
    max_bytes: int = MAX_HTTP_BYTES,
    accept: str = "*/*",
    extra_headers: Optional[dict[str, str]] = None,
) -> HTTPResult:
    """Bounded GET with small retries for transient public-provider failures."""
    transient={408,425,429,500,502,503,504}
    last_error: Optional[Exception]=None
    for attempt in range(3):
        headers = {"User-Agent": USER_AGENT, "Accept": accept, "Accept-Language": "en-US,en;q=0.8"}
        if extra_headers:
            headers.update({str(k): str(v) for k, v in extra_headers.items() if v is not None})
        req = urllib.request.Request(url, headers=headers, method="GET")
        start=time.monotonic()
        try:
            with urllib.request.urlopen(req,timeout=timeout) as r:
                body=r.read(max_bytes+1)
                if len(body)>max_bytes: body=body[:max_bytes]
                result=HTTPResult(url,r.geturl(),int(getattr(r,"status",200)),{k.lower():v for k,v in r.headers.items()},body,time.monotonic()-start)
                if result.status in transient and attempt<2:
                    delay=min(3.0,0.35*(2**attempt))
                    with contextlib.suppress(Exception):
                        delay=min(3.0,max(delay,float(result.headers.get("retry-after","0"))))
                    time.sleep(delay); continue
                return result
        except urllib.error.HTTPError as e:
            body=e.read(min(max_bytes,200_000)); headers={k.lower():v for k,v in e.headers.items()}
            result=HTTPResult(url,e.geturl(),int(e.code),headers,body,time.monotonic()-start)
            if result.status in transient and attempt<2:
                delay=min(3.0,0.35*(2**attempt))
                with contextlib.suppress(Exception): delay=min(3.0,max(delay,float(headers.get("retry-after","0"))))
                time.sleep(delay); continue
            return result
        except (urllib.error.URLError,TimeoutError,socket.timeout,OSError) as exc:
            last_error=exc
            if attempt<2:
                time.sleep(0.35*(2**attempt)); continue
            raise
    if last_error: raise last_error
    raise RuntimeError(f"Request failed: {url}")


def _json_cache_file(url: str) -> Path:
    return CACHE_DIR / "json" / (hashlib.sha256(url.encode("utf-8")).hexdigest()+".json")


def http_json(url: str, timeout: int = DEFAULT_TIMEOUT, *, extra_headers: Optional[dict[str, str]] = None, cache_key: Optional[str] = None) -> Any:
    settings=load_settings(); ttl=int(settings.get("json_cache_ttl",900))
    cache=_json_cache_file(cache_key or url)
    if ttl>0 and os.environ.get("DIGITAL_FOOTPRINT_FINDER_NO_CACHE")!="1" and cache.is_file():
        with contextlib.suppress(Exception):
            payload=json.loads(cache.read_text(encoding="utf-8"))
            if time.time()-float(payload.get("saved_at",0))<=ttl:
                return payload["data"]
    result=http_get(url,timeout=timeout,max_bytes=3_000_000,accept="application/json,*/*;q=0.8",extra_headers=extra_headers)
    if not (200<=result.status<300): raise RuntimeError(f"HTTP {result.status} from {redact_url_secrets(url)}")
    data=json.loads(result.body.decode("utf-8",errors="replace"))
    if ttl>0 and os.environ.get("DIGITAL_FOOTPRINT_FINDER_NO_CACHE")!="1":
        with contextlib.suppress(Exception):
            cache.parent.mkdir(parents=True,exist_ok=True)
            cache.write_text(json.dumps({"saved_at":time.time(),"data":data},ensure_ascii=False),encoding="utf-8")
    return data

def http_json_lines(url: str, timeout: int = DEFAULT_TIMEOUT, max_bytes: int = 4_000_000) -> list[dict[str, Any]]:
    """Read newline-delimited JSON used by public indexes such as Common Crawl."""
    result = http_get(url, timeout=timeout, max_bytes=max_bytes, accept="application/json,text/plain,*/*;q=0.5")
    if not (200 <= result.status < 300):
        raise RuntimeError(f"HTTP {result.status} from {url}")
    rows: list[dict[str, Any]] = []
    for line in result.body.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        with contextlib.suppress(Exception):
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
    return rows


def run_dig(name: str, record_type: str) -> list[str]:
    """Resolve DNS with local dig when available, then fall back to Google Public DNS DoH JSON."""
    dig = shutil.which("dig")
    if dig:
        try:
            cp = subprocess.run(
                [dig, "+short", name, record_type],
                text=True,
                capture_output=True,
                timeout=12,
                check=False,
            )
            values = [line.strip() for line in cp.stdout.splitlines() if line.strip()]
            if values:
                return values
        except Exception:
            pass

    # Local Python DNS resolver is installed into the private workspace when possible.
    try:
        import dns.resolver  # type: ignore
        answers = dns.resolver.resolve(name, record_type, lifetime=8)
        values = [str(answer).strip() for answer in answers]
        if values:
            return values
    except Exception:
        pass

    # Final no-dependency fallback: Google Public DNS JSON/DoH.
    try:
        params = urllib.parse.urlencode({"name": name, "type": record_type})
        data = http_json(FREE_API_ENDPOINTS["google_dns"] + "?" + params, timeout=10)
        if int(data.get("Status", -1)) != 0:
            return []
        out: list[str] = []
        for answer in data.get("Answer", []) or []:
            value = str(answer.get("data", "")).strip()
            if value:
                out.append(value)
        return out
    except Exception:
        return []



def _response_text(body: bytes, limit: int = 180_000) -> str:
    return body[:limit].decode("utf-8", errors="replace")


def _normalized_page_sample(body: bytes, limit: int = 80_000) -> str:
    """Normalize enough HTML to compare a real profile response with a fake-profile baseline."""
    text = _response_text(body, limit).lower()
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"[0-9a-f]{20,}", "<token>", text)
    text = re.sub(r"\d{10,}", "<number>", text)
    text = re.sub(r"\s+", " ", strip_tags(text))
    return text[:limit]


def _same_site(url: str, base_host: str) -> bool:
    host = (urllib.parse.urlsplit(url).hostname or "").lower().rstrip(".")
    base = base_host.lower().rstrip(".")
    return host == base or host.endswith("." + base)


def _extract_js_endpoints(js_url: str, body: bytes, limit: int = 120) -> list[str]:
    """Extract public URL/path strings from JavaScript; deliberately does not hunt secrets."""
    text = _response_text(body, 500_000)
    patterns = [
        r"[\"']((?:https?://)[^\"'\\s<>]{4,250})[\"']",
        r"[\"']((?:/|\\.\\./|\\./)[A-Za-z0-9_./?=&%+~:#@-]{2,220})[\"']",
    ]
    out: list[str] = []
    seen: set[str] = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            value = html.unescape(match.group(1)).strip()
            if value.startswith(("javascript:", "data:")):
                continue
            with contextlib.suppress(Exception):
                value = urllib.parse.urljoin(js_url, value)
            if value not in seen:
                seen.add(value)
                out.append(value)
                if len(out) >= limit:
                    return out
    return out


def _parse_sitemap_urls(xml_text: str, limit: int = 500) -> list[str]:
    """Parse both sitemap indexes and URL sets without requiring an XML dependency."""
    out: list[str] = []
    try:
        root = ET.fromstring(xml_text)
        for elem in root.iter():
            if elem.tag.lower().endswith("loc") and elem.text:
                value = elem.text.strip()
                if value.startswith(("http://", "https://")):
                    out.append(value)
                    if len(out) >= limit:
                        break
    except Exception:
        out.extend(re.findall(r"<loc>\s*(https?://[^<\s]+)\s*</loc>", xml_text, flags=re.I)[:limit])
    return list(dict.fromkeys(out))[:limit]



def detect_technology_hints(headers: dict[str, str], body: bytes, page_intelligence: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Conservative fingerprinting from public headers/HTML; findings are hints, not guarantees."""
    text = _response_text(body, 700_000).lower()
    found: dict[str, list[str]] = {}
    def hit(name: str, reason: str) -> None:
        found.setdefault(name, [])
        if reason not in found[name]:
            found[name].append(reason)

    server = headers.get("server")
    powered = headers.get("x-powered-by")
    if server:
        hit(server.split("/")[0].strip(), "Server header")
    if powered:
        hit(powered.strip(), "X-Powered-By header")
    if headers.get("cf-ray") or headers.get("cf-cache-status"):
        hit("Cloudflare", "CF response headers")
    if headers.get("x-vercel-id"):
        hit("Vercel", "x-vercel-id header")
    if headers.get("x-nf-request-id"):
        hit("Netlify", "x-nf-request-id header")

    patterns = [
        ("WordPress", ("wp-content/", "wp-includes/")),
        ("Drupal", ("drupalsettings", "/sites/default/files/")),
        ("Joomla", ("/media/system/js/", "joomla!")),
        ("Next.js", ("__next_data__", "/_next/static/")),
        ("Nuxt", ("__nuxt__", "/_nuxt/")),
        ("React", ("data-reactroot", "react-dom")),
        ("Angular", ("ng-version=", "<app-root")),
        ("Vue", ("data-v-", "__vue__")),
        ("Shopify", ("cdn.shopify.com", "shopify.theme")),
        ("Wix", ("wixstatic.com", "wix-code")),
        ("Squarespace", ("static1.squarespace.com", "squarespace-context")),
        ("Bootstrap", ("bootstrap.min.css", "bootstrap.bundle")),
        ("jQuery", ("jquery.min.js", "jquery-")),
    ]
    for name, markers in patterns:
        if any(marker in text for marker in markers):
            hit(name, "HTML/asset marker")
    generator = (page_intelligence or {}).get("generator")
    if generator:
        hit(str(generator), "generator meta tag")
    return {"technologies": [{"name": k, "evidence": v} for k, v in sorted(found.items())],
            "server": server, "powered_by": powered}


def tls_certificate_info(domain: str, timeout: int = 8) -> dict[str, Any]:
    """Read the certificate presented by the public HTTPS service using a normal TLS handshake."""
    context = ssl.create_default_context()
    with socket.create_connection((domain, 443), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as tls:
            cert = tls.getpeercert()
    def name_pairs(value: Any) -> dict[str, str]:
        out: dict[str, str] = {}
        for group in value or []:
            for key, val in group:
                out[str(key)] = str(val)
        return out
    sans = [str(v) for k, v in cert.get("subjectAltName", []) if str(k).lower() == "dns"]
    return {
        "subject": name_pairs(cert.get("subject")),
        "issuer": name_pairs(cert.get("issuer")),
        "serial_number": cert.get("serialNumber"),
        "not_before": cert.get("notBefore"),
        "not_after": cert.get("notAfter"),
        "subject_alt_names": sorted(set(sans))[:300],
        "version": cert.get("version"),
    }


def _source_parts(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(" | ") if part.strip()]


# ---------------------------------------------------------------------------
# Database / case graph
# ---------------------------------------------------------------------------

SOURCE_FAMILY_PATTERNS = {
    "dns": ("dns", "google dns", "reverse dns", "ptr", "mx", "spf", "dmarc", "mta-sts", "tls-rpt"),
    "registration": ("rdap", "ror"),
    "routing": ("ripe", "asn", "prefix"),
    "certificates": ("certificate", "crt", "tls subject"),
    "archives": ("wayback", "common crawl", "commoncrawl"),
    "developer_profiles": ("github", "gitlab", "codeberg", "sourcehut"),
    "knowledge_graphs": ("wikidata", "ror"),
    "scholarly": ("crossref", "openalex", "doi"),
    "passive_dns": ("otx", "hackertarget", "passive dns"),
    "public_web": ("html", "website", "profile page", "json-ld", "webfinger", "mastodon"),
    "search_leads": ("generated search", "search lead", "dork"),
    "local": ("local", "sha-256", "user"),
    "heuristics": ("heuristic", "technology hint", "possible", "candidate", "alias"),
}


def source_family(source: str) -> str:
    text = (source or "").lower()
    for family, needles in SOURCE_FAMILY_PATTERNS.items():
        if any(n in text for n in needles):
            return family
    return "other" if text else "unknown"


def entity_source_families(source_text: str) -> set[str]:
    return {source_family(x) for x in _source_parts(source_text) if x.strip()}


def conservative_confidence(old: float, incoming: float, old_sources: str, new_source: str) -> float:
    """Raise confidence only when a genuinely different source family corroborates it."""
    base = max(float(old), float(incoming))
    old_families = entity_source_families(old_sources)
    new_family = source_family(new_source)
    if new_source and old_families and new_family not in old_families and new_family not in {"unknown", "heuristics", "search_leads"}:
        base = max(base, min(0.97, float(old) + 0.07))
    return min(0.97, base)


class CaseDB:
    def __init__(self, path: Path):
        self.path = Path(path)
        if str(self.path) != ":memory:":
            self.path.expanduser().parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def close(self) -> None:
        self.conn.close()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY,
                case_id INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
                type TEXT NOT NULL,
                value TEXT NOT NULL,
                label TEXT NOT NULL DEFAULT '',
                confidence REAL NOT NULL DEFAULT 0.5,
                source TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                UNIQUE(case_id, type, value)
            );

            CREATE TABLE IF NOT EXISTS relations (
                id INTEGER PRIMARY KEY,
                case_id INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
                src_entity_id INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
                dst_entity_id INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
                relation TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 0.5,
                source TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                UNIQUE(case_id, src_entity_id, dst_entity_id, relation)
            );

            CREATE TABLE IF NOT EXISTS evidence (
                id INTEGER PRIMARY KEY,
                case_id INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
                entity_id INTEGER REFERENCES entities(id) ON DELETE SET NULL,
                kind TEXT NOT NULL,
                source_url TEXT NOT NULL DEFAULT '',
                captured_at TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                content_type TEXT NOT NULL DEFAULT '',
                metadata_json TEXT NOT NULL DEFAULT '{}',
                body BLOB
            );

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY,
                case_id INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
                entity_id INTEGER REFERENCES entities(id) ON DELETE SET NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_entities_case ON entities(case_id);
            CREATE INDEX IF NOT EXISTS idx_relations_case ON relations(case_id);
            CREATE INDEX IF NOT EXISTS idx_evidence_case ON evidence(case_id);

            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY,
                case_id INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
                entity_id INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
                status TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS hypotheses (
                id INTEGER PRIMARY KEY,
                case_id INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
                text TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                confidence REAL NOT NULL DEFAULT 0.5,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                case_id INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
                entity_id INTEGER REFERENCES entities(id) ON DELETE SET NULL,
                parent_event_id INTEGER REFERENCES events(id) ON DELETE SET NULL,
                event_type TEXT NOT NULL,
                depth INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'observed',
                source TEXT NOT NULL DEFAULT '',
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY,
                case_id INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
                mode TEXT NOT NULL,
                target TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                stats_json TEXT NOT NULL DEFAULT '{}'
            );

            CREATE INDEX IF NOT EXISTS idx_assessments_case ON assessments(case_id);
            CREATE INDEX IF NOT EXISTS idx_hypotheses_case ON hypotheses(case_id);
            CREATE INDEX IF NOT EXISTS idx_events_case ON events(case_id);
            CREATE INDEX IF NOT EXISTS idx_runs_case ON runs(case_id);
            """
        )
        self.conn.commit()

    def get_or_create_case(self, name: str, description: str = "") -> int:
        row = self.conn.execute("SELECT id FROM cases WHERE name=?", (name,)).fetchone()
        if row:
            return int(row["id"])
        cur = self.conn.execute(
            "INSERT INTO cases(name,description,created_at) VALUES(?,?,?)",
            (name, description, utcnow()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_cases(self) -> list[sqlite3.Row]:
        return list(self.conn.execute("SELECT * FROM cases ORDER BY id DESC"))

    def latest_case(self) -> Optional[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM cases ORDER BY id DESC LIMIT 1").fetchone()

    def get_case(self, case_id: int) -> Optional[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone()

    def case_by_name(self, name: str) -> Optional[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM cases WHERE name=?", (name,)).fetchone()

    def add_entity(
        self,
        case_id: int,
        typ: str,
        value: str,
        *,
        label: str = "",
        confidence: float = 0.5,
        source: str = "",
    ) -> int:
        """Add/merge an entity and reward independent-source corroboration conservatively."""
        typ = typ.lower().strip()
        if typ not in ENTITY_TYPES:
            typ = "other"
        value = value.strip()
        confidence = max(0.0, min(1.0, confidence))
        existing = self.conn.execute(
            "SELECT id,label,confidence,source FROM entities WHERE case_id=? AND type=? AND value=?",
            (case_id, typ, value),
        ).fetchone()
        if existing:
            old_sources = _source_parts(existing["source"])
            new_source = source.strip()
            sources = list(old_sources)
            independent = bool(new_source and new_source not in sources)
            if independent:
                sources.append(new_source)
            # Corroboration only receives a confidence bonus when it comes from a
            # genuinely different source family. Five DNS-derived observations do
            # not count as five independent confirmations.
            merged_conf = conservative_confidence(
                float(existing["confidence"]), confidence, existing["source"], new_source
            )
            merged_label = label or existing["label"]
            self.conn.execute(
                "UPDATE entities SET label=?,confidence=?,source=? WHERE id=?",
                (merged_label, merged_conf, " | ".join(sources), int(existing["id"])),
            )
            self.conn.commit()
            return int(existing["id"])

        cur = self.conn.execute(
            "INSERT INTO entities(case_id,type,value,label,confidence,source,created_at) VALUES(?,?,?,?,?,?,?)",
            (case_id, typ, value, label, confidence, source.strip(), utcnow()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def add_relation(
        self,
        case_id: int,
        src: int,
        dst: int,
        relation: str,
        *,
        confidence: float = 0.5,
        source: str = "",
    ) -> None:
        if src == dst:
            return
        existing = self.conn.execute(
            "SELECT id,confidence,source FROM relations WHERE case_id=? AND src_entity_id=? AND dst_entity_id=? AND relation=?",
            (case_id, src, dst, relation.strip()),
        ).fetchone()
        if existing:
            sources = _source_parts(existing["source"])
            if source.strip() and source.strip() not in sources:
                sources.append(source.strip())
            merged_conf = conservative_confidence(float(existing["confidence"]), confidence, existing["source"], source)
            self.conn.execute(
                "UPDATE relations SET confidence=?,source=? WHERE id=?",
                (merged_conf, " | ".join(sources), int(existing["id"])),
            )
        else:
            self.conn.execute(
                "INSERT INTO relations(case_id,src_entity_id,dst_entity_id,relation,confidence,source,created_at) VALUES(?,?,?,?,?,?,?)",
                (case_id, src, dst, relation.strip(), confidence, source, utcnow()),
            )
        self.conn.commit()

    def add_evidence(
        self,
        case_id: int,
        entity_id: Optional[int],
        kind: str,
        *,
        source_url: str = "",
        content_type: str = "",
        metadata: Optional[dict[str, Any]] = None,
        body: bytes = b"",
    ) -> int:
        digest = sha256_bytes(body if body else pretty_json(metadata or {}).encode())
        duplicate = self.conn.execute(
            """SELECT id FROM evidence WHERE case_id=? AND entity_id IS ? AND kind=?
               AND source_url=? AND sha256=? LIMIT 1""",
            (case_id, entity_id, kind, source_url, digest),
        ).fetchone()
        if duplicate:
            return int(duplicate["id"])
        cur = self.conn.execute(
            """
            INSERT INTO evidence(
              case_id,entity_id,kind,source_url,captured_at,sha256,content_type,metadata_json,body
            ) VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (
                case_id, entity_id, kind, source_url, utcnow(), digest,
                content_type, json.dumps(metadata or {}, ensure_ascii=False), body,
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def add_note(self, case_id: int, text: str, entity_id: Optional[int] = None) -> None:
        self.conn.execute(
            "INSERT INTO notes(case_id,entity_id,text,created_at) VALUES(?,?,?,?)",
            (case_id, entity_id, text.strip(), utcnow()),
        )
        self.conn.commit()

    def add_assessment(self, case_id: int, entity_id: int, status: str, note: str = "") -> int:
        status = status.lower().strip()
        if status not in {"confirmed", "rejected", "uncertain"}:
            raise ValueError("Assessment must be confirmed, rejected, or uncertain.")
        cur = self.conn.execute(
            "INSERT INTO assessments(case_id,entity_id,status,note,created_at) VALUES(?,?,?,?,?)",
            (case_id, entity_id, status, note.strip(), utcnow()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def add_hypothesis(self, case_id: int, text: str, confidence: float = 0.5, status: str = "open") -> int:
        cur = self.conn.execute(
            "INSERT INTO hypotheses(case_id,text,status,confidence,created_at) VALUES(?,?,?,?,?)",
            (case_id, text.strip(), status, max(0.0, min(1.0, confidence)), utcnow()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def add_event(self, case_id: int, event_type: str, *, entity_id: Optional[int] = None,
                  parent_event_id: Optional[int] = None, depth: int = 0, status: str = "observed",
                  source: str = "", metadata: Optional[dict[str, Any]] = None) -> int:
        cur = self.conn.execute(
            """INSERT INTO events(case_id,entity_id,parent_event_id,event_type,depth,status,source,metadata_json,created_at)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (case_id, entity_id, parent_event_id, event_type, depth, status, source,
             json.dumps(metadata or {}, ensure_ascii=False), utcnow()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def begin_run(self, case_id: int, mode: str, target: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO runs(case_id,mode,target,started_at) VALUES(?,?,?,?)",
            (case_id, mode, target, utcnow()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def finish_run(self, run_id: int, stats: dict[str, Any]) -> None:
        self.conn.execute(
            "UPDATE runs SET finished_at=?,stats_json=? WHERE id=?",
            (utcnow(), json.dumps(stats, ensure_ascii=False), run_id),
        )
        self.conn.commit()

    def search(self, query: str, *, case_id: Optional[int] = None, limit: int = 25) -> list[dict[str, Any]]:
        """Smart local search with optional filters: kind:, type:, source:, confidence:, id:, case:."""
        raw=query.strip()
        if not raw: return []
        try: tokens=shlex.split(raw)
        except ValueError: tokens=raw.split()
        filters: dict[str,str]={}; terms=[]
        for token in tokens:
            if ":" in token:
                k,v=token.split(":",1); k=k.lower().strip()
                if k in {"kind","type","source","confidence","id","case","status"} and v.strip():
                    filters[k]=v.strip(); continue
            terms.append(token)
        text=" ".join(terms).strip(); like=f"%{text}%" if text else "%"
        kind_filter=filters.get("kind","").lower()
        if not kind_filter and any(k in filters for k in ("type","confidence","id")):
            kind_filter="entity"
        elif not kind_filter and "status" in filters:
            kind_filter="hypothesis"
        effective_case=case_id
        if filters.get("case"):
            row=self.conn.execute("SELECT id FROM cases WHERE name LIKE ? ORDER BY id DESC LIMIT 1",(f"%{filters['case']}%",)).fetchone()
            effective_case=int(row["id"]) if row else -1
        out: list[dict[str,Any]]=[]
        if kind_filter in {"","entity"}:
            clauses=["(e.value LIKE ? OR e.label LIKE ? OR e.source LIKE ?)"]; params:[Any]=[like,like,like]
            if effective_case is not None: clauses.append("e.case_id=?"); params.append(effective_case)
            if filters.get("type"): clauses.append("e.type=?"); params.append(filters["type"].lower())
            if filters.get("source"): clauses.append("e.source LIKE ?"); params.append(f"%{filters['source']}%")
            if filters.get("id") and filters["id"].isdigit(): clauses.append("e.id=?"); params.append(int(filters["id"]))
            conf=filters.get("confidence")
            if conf:
                m=re.fullmatch(r"(>=|<=|>|<|=)?\s*(0(?:\.\d+)?|1(?:\.0+)?)",conf)
                if m:
                    op=m.group(1) or ">="; clauses.append(f"e.confidence {op} ?"); params.append(float(m.group(2)))
            sql=f"""SELECT e.id,e.case_id,e.type,e.value,e.label,e.confidence,e.source,c.name AS case_name
                     FROM entities e JOIN cases c ON c.id=e.case_id WHERE {' AND '.join(clauses)}
                     ORDER BY e.confidence DESC,e.id DESC LIMIT ?"""
            for r in self.conn.execute(sql,(*params,limit)):
                d=dict(r); exact=(text.lower()==str(r["value"]).lower()) if text else False
                d.update({"kind":"entity","score":4.0+(2.0 if exact else 0.0)+float(r["confidence"])}); out.append(d)
        if kind_filter in {"","note"}:
            clauses=["n.text LIKE ?"]; params=[like]
            if effective_case is not None: clauses.append("n.case_id=?"); params.append(effective_case)
            for r in self.conn.execute(f"SELECT n.id,n.case_id,n.entity_id,n.text,n.created_at,c.name AS case_name FROM notes n JOIN cases c ON c.id=n.case_id WHERE {' AND '.join(clauses)} ORDER BY n.id DESC LIMIT ?",(*params,limit)):
                d=dict(r); d.update({"kind":"note","score":2.0}); out.append(d)
        if kind_filter in {"","evidence"}:
            clauses=["(ev.kind LIKE ? OR ev.source_url LIKE ? OR ev.metadata_json LIKE ?)"]; params=[like,like,like]
            if effective_case is not None: clauses.append("ev.case_id=?"); params.append(effective_case)
            if filters.get("source"): clauses.append("ev.source_url LIKE ?"); params.append(f"%{filters['source']}%")
            for r in self.conn.execute(f"SELECT ev.id,ev.case_id,ev.entity_id,ev.kind AS evidence_kind,ev.source_url,ev.captured_at,c.name AS case_name FROM evidence ev JOIN cases c ON c.id=ev.case_id WHERE {' AND '.join(clauses)} ORDER BY ev.id DESC LIMIT ?",(*params,limit)):
                d=dict(r); d.update({"kind":"evidence","score":1.7}); out.append(d)
        if kind_filter in {"","hypothesis"}:
            clauses=["h.text LIKE ?"]; params=[like]
            if effective_case is not None: clauses.append("h.case_id=?"); params.append(effective_case)
            if filters.get("status"): clauses.append("h.status=?"); params.append(filters["status"])
            for r in self.conn.execute(f"SELECT h.*,c.name AS case_name FROM hypotheses h JOIN cases c ON c.id=h.case_id WHERE {' AND '.join(clauses)} ORDER BY h.id DESC LIMIT ?",(*params,limit)):
                d=dict(r); d.update({"kind":"hypothesis","score":1.9}); out.append(d)
        return sorted(out,key=lambda x:(-float(x.get("score",0)),-int(x.get("id",0))))[:limit]

    def case_data(self, case_id: int) -> dict[str, Any]:
        case = self.conn.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone()
        if not case:
            raise ValueError("Case not found.")
        entities = [dict(r) for r in self.conn.execute(
            "SELECT * FROM entities WHERE case_id=? ORDER BY id", (case_id,)
        )]
        relations = [dict(r) for r in self.conn.execute(
            "SELECT * FROM relations WHERE case_id=? ORDER BY id", (case_id,)
        )]
        evidence = [dict(r) for r in self.conn.execute(
            """
            SELECT id,case_id,entity_id,kind,source_url,captured_at,sha256,
                   content_type,metadata_json,length(body) AS body_size
            FROM evidence WHERE case_id=? ORDER BY id
            """,
            (case_id,),
        )]
        notes = [dict(r) for r in self.conn.execute(
            "SELECT * FROM notes WHERE case_id=? ORDER BY id", (case_id,)
        )]
        assessments = [dict(r) for r in self.conn.execute(
            "SELECT * FROM assessments WHERE case_id=? ORDER BY id", (case_id,)
        )]
        hypotheses = [dict(r) for r in self.conn.execute(
            "SELECT * FROM hypotheses WHERE case_id=? ORDER BY id", (case_id,)
        )]
        events = [dict(r) for r in self.conn.execute(
            "SELECT * FROM events WHERE case_id=? ORDER BY id", (case_id,)
        )]
        for e in evidence:
            with contextlib.suppress(Exception):
                e["metadata"] = json.loads(e.pop("metadata_json"))
        return {
            "case": dict(case),
            "entities": entities,
            "relations": relations,
            "evidence": evidence,
            "notes": notes,
            "assessments": assessments,
            "hypotheses": hypotheses,
            "events": events,
        }


# ---------------------------------------------------------------------------
# Investigation engine
# ---------------------------------------------------------------------------

def _display_ror_name(record: dict[str, Any]) -> str:
    names = record.get("names") or []
    for preferred_type in ("ror_display", "label"):
        for item in names:
            if isinstance(item, dict) and preferred_type in (item.get("types") or []):
                return str(item.get("value") or "").strip()
    for item in names:
        if isinstance(item, dict) and item.get("value"):
            return str(item["value"]).strip()
    return str(record.get("name") or "").strip()


def _openalex_url(endpoint: str, **params: Any) -> str:
    key = get_api_key("openalex")
    if key:
        params["api_key"] = key
    return endpoint + "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})


class DigitalFootprintFinder:
    def __init__(self, db: CaseDB, case_id: int, timeout: int = DEFAULT_TIMEOUT):
        self.db = db
        self.case_id = case_id
        self.timeout = timeout

    def _stackexchange_candidates(self, value: str, root: int, limit: int = 6) -> list[dict[str, Any]]:
        """Keyless Stack Exchange public-profile candidates. Name/alias matches remain low-confidence leads."""
        out: list[dict[str, Any]] = []
        try:
            params = urllib.parse.urlencode({"site": "stackoverflow", "inname": value, "pagesize": min(max(limit, 1), 20), "order": "desc", "sort": "reputation"})
            url = FREE_API_ENDPOINTS["stackexchange_users"] + "?" + params
            data = http_json(url, max(self.timeout, 12))
            for row in ((data or {}).get("items") or [])[:limit]:
                if not isinstance(row, dict):
                    continue
                item = {k: row.get(k) for k in ("user_id", "display_name", "link", "website_url", "location", "reputation", "creation_date", "last_access_date")}
                out.append(item)
                profile = str(row.get("link") or "").strip()
                if profile:
                    uid = self._entity("url", profile, label="Stack Overflow candidate", confidence=0.34, source="Stack Exchange public API")
                    self.db.add_relation(self.case_id, root, uid, "possible_public_candidate", confidence=0.34, source="name/alias-only Stack Exchange search; verify identity")
                if row.get("website_url"):
                    with contextlib.suppress(Exception):
                        wid = self._entity("url", normalize_url(str(row["website_url"])), label="Candidate public website", confidence=0.30, source="Stack Exchange public API")
                        self.db.add_relation(self.case_id, root, wid, "candidate_public_website", confidence=0.30, source="Stack Exchange candidate; verify identity")
            self.db.add_evidence(self.case_id, root, "stackexchange_public_candidates", source_url=url, content_type="application/json", metadata={"query": value, "candidates": out})
        except Exception:
            return out
        return out

    def _virustotal_enrichment(self, typ: str, value: str, root: int) -> Optional[dict[str, Any]]:
        if not get_api_key("virustotal"):
            return None
        endpoint_key = {"domain": "virustotal_domain", "ip": "virustotal_ip", "hash": "virustotal_file", "url": "virustotal_url"}.get(typ)
        if not endpoint_key:
            return None
        encoded = value
        if typ == "url":
            encoded = base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii").rstrip("=")
        url = OPTIONAL_API_ENDPOINTS[endpoint_key].format(value=urllib.parse.quote(encoded, safe=""))
        try:
            data = http_json(url, max(self.timeout, 15), extra_headers=api_headers("virustotal"), cache_key=f"virustotal:{typ}:{value}")
            obj = data.get("data") if isinstance(data, dict) else None
            attrs = (obj or {}).get("attributes") if isinstance(obj, dict) else {}
            attrs = attrs if isinstance(attrs, dict) else {}
            slim = {k: attrs.get(k) for k in ("reputation", "last_analysis_stats", "categories", "tags", "registrar", "creation_date", "last_analysis_date", "last_modification_date", "as_owner", "asn", "network", "meaningful_name", "type_description") if attrs.get(k) is not None}
            if obj and isinstance(obj, dict):
                slim["id"] = obj.get("id"); slim["type"] = obj.get("type")
            self.db.add_evidence(self.case_id, root, "virustotal_public_context", source_url=redact_url_secrets(url), content_type="application/json", metadata=slim)
            if slim.get("as_owner"):
                oid = self._entity("organization", str(slim["as_owner"]), confidence=0.58, source="VirusTotal public context")
                self.db.add_relation(self.case_id, root, oid, "network_organization", confidence=0.58, source="VirusTotal")
            if slim.get("asn"):
                aid = self._entity("asn", "AS" + str(slim["asn"]).removeprefix("AS"), confidence=0.66, source="VirusTotal public context")
                self.db.add_relation(self.case_id, root, aid, "associated_asn", confidence=0.66, source="VirusTotal")
            return slim
        except Exception as exc:
            return {"error": str(exc)}

    def _urlscan_enrichment(self, typ: str, value: str, root: int) -> Optional[dict[str, Any]]:
        if not get_api_key("urlscan"):
            return None
        query = None
        if typ == "domain": query = f"domain:{value}"
        elif typ == "ip": query = f"ip:{value}"
        elif typ == "url":
            with contextlib.suppress(Exception):
                host = urllib.parse.urlsplit(normalize_url(value)).hostname
                if host: query = f"domain:{host}"
        if not query:
            return None
        url = OPTIONAL_API_ENDPOINTS["urlscan_search"].format(query=urllib.parse.urlencode({"q": query, "size": 25}))
        try:
            data = http_json(url, max(self.timeout, 15), extra_headers=api_headers("urlscan"), cache_key=f"urlscan:{query}")
            slim: list[dict[str, Any]] = []
            for row in ((data or {}).get("results") or [])[:25]:
                if not isinstance(row, dict): continue
                page = row.get("page") or {}; task = row.get("task") or {}; stats = row.get("stats") or {}
                item = {"url": page.get("url"), "domain": page.get("domain"), "ip": page.get("ip"), "asn": page.get("asn"), "asnname": page.get("asnname"), "country": page.get("country"), "scan_url": task.get("reportURL") or task.get("url"), "time": task.get("time"), "stats": stats}
                slim.append(item)
                if item.get("domain"):
                    did = self._entity("domain", clean_domain(str(item["domain"])), confidence=0.48, source="urlscan.io public scan history")
                    self.db.add_relation(self.case_id, root, did, "public_scan_observation", confidence=0.48, source="urlscan.io; historical observation")
            self.db.add_evidence(self.case_id, root, "urlscan_public_history", source_url=url, content_type="application/json", metadata={"query": query, "results": slim})
            return {"query": query, "results": slim}
        except Exception as exc:
            return {"error": str(exc)}

    def _shodan_enrichment(self, ip: str, root: int) -> Optional[dict[str, Any]]:
        key = get_api_key("shodan")
        if not key or not is_public_ip(ip):
            return None
        url = OPTIONAL_API_ENDPOINTS["shodan_host"].format(ip=urllib.parse.quote(ip), key=urllib.parse.quote(key))
        try:
            data = http_json(url, max(self.timeout, 15), cache_key=f"shodan:{ip}")
            if not isinstance(data, dict): return None
            slim = {k: data.get(k) for k in ("ip_str", "org", "isp", "asn", "hostnames", "domains", "ports", "tags", "vulns", "country_name", "city", "last_update") if data.get(k) is not None}
            services=[]
            for row in (data.get("data") or [])[:80]:
                if not isinstance(row, dict): continue
                services.append({"port": row.get("port"), "transport": row.get("transport"), "product": row.get("product"), "server": (row.get("http") or {}).get("server") if isinstance(row.get("http"), dict) else None, "timestamp": row.get("timestamp")})
            slim["services"] = services
            self.db.add_evidence(self.case_id, root, "shodan_public_host_observation", source_url=redact_url_secrets(url), content_type="application/json", metadata=slim)
            if slim.get("org"):
                oid=self._entity("organization", str(slim["org"]), confidence=0.58, source="Shodan public host observation")
                self.db.add_relation(self.case_id, root, oid, "network_organization", confidence=0.58, source="Shodan")
            for host in (slim.get("hostnames") or [])[:30]:
                if host:
                    did=self._entity("domain", clean_domain(str(host)), confidence=0.52, source="Shodan public host observation")
                    self.db.add_relation(self.case_id, root, did, "public_host_observation", confidence=0.52, source="Shodan")
            return slim
        except Exception as exc:
            return {"error": str(exc)}

    def optional_api_enrichment(self, typ: str, value: str, root: int) -> dict[str, Any]:
        """Run only configured optional providers and return public enrichment without exposing credentials."""
        out: dict[str, Any] = {}
        vt = self._virustotal_enrichment(typ, value, root)
        if vt is not None: out["virustotal"] = vt
        us = self._urlscan_enrichment(typ, value, root)
        if us is not None: out["urlscan"] = us
        if typ == "ip":
            sh = self._shodan_enrichment(value, root)
            if sh is not None: out["shodan"] = sh
        return out

    def _entity(self, typ: str, value: str, **kwargs: Any) -> int:
        return self.db.add_entity(self.case_id, typ, value, **kwargs)

    def _attach_search_leads(self, root_id: int, links: list[dict[str, str]]) -> None:
        for row in links:
            url = row.get("url", "")
            if not url:
                continue
            uid = self._entity(
                "url", url,
                label=f"{row.get('engine', 'Search')} lead",
                confidence=0.25,
                source="generated public-search query",
            )
            self.db.add_relation(
                self.case_id, root_id, uid, "manual_search_lead",
                confidence=0.25, source="generated query; not an identity match",
            )

    def _add_profile_observation(self, root: int, site: str, url: str, confidence: float, method: str) -> None:
        # Store the canonical profile as a URL entity so an independent API/crawl that
        # finds the exact same URL automatically corroborates it through add_entity().
        uid = self._entity(
            "url", url, label=f"{site} profile",
            confidence=confidence, source=f"native profile probe ({method})",
        )
        self.db.add_relation(
            self.case_id, root, uid, "possible_profile",
            confidence=confidence, source=f"native profile probe: {method}; verify identity",
        )

    def _enrich_public_profile(self, root: int, site: str, url: str, confidence: float) -> dict[str, Any]:
        """Extract bounded public metadata/links from a profile page; no login or cookies."""
        try:
            r = http_get(url, self.timeout, max_bytes=650_000, accept="text/html,*/*;q=0.8")
            if not (200 <= r.status < 400):
                return {}
            intel = extract_page_intelligence(r.final_url, r.body)
            summary = {
                "site": site, "url": url, "final_url": r.final_url, "status": r.status,
                "title": extract_title(r.body), "description": intel.get("description"),
                "canonical": intel.get("canonical"),
                "public_emails": intel.get("public_emails", []),
                "social_links": intel.get("social_links", []),
                "same_as": intel.get("same_as", []),
                "structured_names": intel.get("structured_names", []),
                "documents": intel.get("documents", []),
                "sha256": sha256_bytes(r.body),
            }
            for email in summary["public_emails"][:20]:
                eid = self._entity("email", str(email), confidence=min(0.68, confidence),
                                   source=f"public {site} profile page")
                self.db.add_relation(self.case_id, root, eid, "profile_public_email",
                                     confidence=min(0.68, confidence), source=f"{site} public profile")
            for link in list(dict.fromkeys(summary["social_links"] + summary["same_as"]))[:50]:
                lid = self._entity("url", str(link), label="Profile-linked public URL",
                                   confidence=min(0.62, confidence), source=f"public {site} profile page")
                self.db.add_relation(self.case_id, root, lid, "profile_linked_url",
                                     confidence=min(0.62, confidence), source=f"{site} public profile")
            canonical = summary.get("canonical")
            if canonical:
                cid = self._entity("url", str(canonical), label=f"{site} canonical profile",
                                   confidence=min(0.78, confidence + 0.05), source=f"{site} canonical link")
                self.db.add_relation(self.case_id, root, cid, "profile_canonical",
                                     confidence=min(0.78, confidence + 0.05), source=f"{site} canonical link")
            self.db.add_evidence(self.case_id, root, "public_profile_page", source_url=r.final_url,
                                 content_type=r.headers.get("content-type", "text/html"),
                                 metadata=summary, body=r.body)
            return summary
        except Exception:
            return {}

    def _probe_username_site(self, item: tuple[str, str], username: str) -> dict[str, Any]:
        """
        Native username discovery inspired by the general technique used by mature
        username OSINT tools: probe the candidate URL, then compare it with a clearly
        nonexistent username when the site returns an ambiguous success response.
        """
        site_name, template = item
        encoded = urllib.parse.quote(username, safe="._-")
        url = template.format(username=encoded)
        try:
            target = http_get(url, self.timeout, max_bytes=300_000)
        except Exception as exc:
            return {"site": site_name, "url": url, "result": "error", "error": str(exc)}

        title = extract_title(target.body)
        target_text = _normalized_page_sample(target.body)
        negative = any(marker in target_text for marker in PROFILE_NEGATIVE_MARKERS)
        if target.status in {404, 410} or negative:
            return {"site": site_name, "url": url, "http_status": target.status,
                    "result": "not_found", "confidence": 0.05, "title": title,
                    "method": "negative marker/status"}
        if target.status in {401, 403, 429} or target.status >= 500:
            return {"site": site_name, "url": url, "http_status": target.status,
                    "result": "unknown", "confidence": 0.1, "title": title,
                    "method": "blocked/rate-limited"}
        if not (200 <= target.status < 400):
            return {"site": site_name, "url": url, "http_status": target.status,
                    "result": "not_found", "confidence": 0.05, "title": title,
                    "method": "HTTP status"}

        # Only ambiguous successful pages need a fake-user baseline. This sharply
        # reduces false positives from websites that return HTTP 200 for every path.
        fake = "td_probe_" + hashlib.sha1((site_name + username).encode()).hexdigest()[:16]
        fake_url = template.format(username=fake)
        try:
            baseline = http_get(fake_url, self.timeout, max_bytes=300_000)
        except Exception:
            baseline = None

        if baseline is None:
            mentioned = username.lower() in target_text
            conf = 0.52 if mentioned else 0.38
            return {"site": site_name, "url": url, "http_status": target.status,
                    "result": "possible", "confidence": conf, "title": title,
                    "method": "candidate success; baseline unavailable"}

        baseline_text = _normalized_page_sample(baseline.body)
        baseline_negative = any(marker in baseline_text for marker in PROFILE_NEGATIVE_MARKERS)
        if baseline.status in {404, 410} or baseline_negative:
            return {"site": site_name, "url": url, "http_status": target.status,
                    "result": "probable", "confidence": 0.82, "title": title,
                    "method": "candidate success + fake-user negative baseline"}

        sample_a = target_text[:60_000]
        sample_b = baseline_text[:60_000]
        similarity = difflib.SequenceMatcher(None, sample_a, sample_b).ratio() if sample_a and sample_b else 1.0
        mentioned = username.lower() in sample_a and fake.lower() not in sample_a
        target_host_path = urllib.parse.urlsplit(target.final_url)
        fake_host_path = urllib.parse.urlsplit(baseline.final_url)
        same_destination = (
            target_host_path.netloc.lower() == fake_host_path.netloc.lower()
            and target_host_path.path.rstrip("/").lower() == fake_host_path.path.rstrip("/").lower()
        )

        if same_destination and similarity > 0.92:
            result, conf, method = "unknown", 0.15, "candidate and fake user collapse to same page"
        elif mentioned and similarity < 0.93:
            result, conf, method = "probable", 0.68, "username appears and differs from fake-user page"
        elif similarity < 0.72:
            result, conf, method = "possible", 0.52, "candidate materially differs from fake-user page"
        else:
            result, conf, method = "unknown", 0.18, "site returns ambiguous successful pages"

        return {"site": site_name, "url": url, "http_status": target.status,
                "baseline_status": baseline.status, "result": result,
                "confidence": conf, "similarity": round(similarity, 3),
                "title": title, "method": method}

    def _github_repositories(self, username: str, root: int) -> list[dict[str, Any]]:
        """Collect a bounded set of public GitHub repositories as corroborating public context."""
        url = FREE_API_ENDPOINTS["github_user_repos"].format(username=urllib.parse.quote(username))
        try:
            data = http_json(url, self.timeout, extra_headers=api_headers("github"))
            repos = data[:30] if isinstance(data, list) else []
            slim: list[dict[str, Any]] = []
            for repo in repos:
                if not isinstance(repo, dict):
                    continue
                item = {k: repo.get(k) for k in ("name", "html_url", "description", "language", "fork", "archived", "updated_at")}
                slim.append(item)
                if repo.get("html_url"):
                    rid = self._entity("url", str(repo["html_url"]), label="Public GitHub repository",
                                       confidence=0.78, source="GitHub public API")
                    self.db.add_relation(self.case_id, root, rid, "public_repository",
                                         confidence=0.78, source="GitHub public API")
            self.db.add_evidence(self.case_id, root, "github_public_repositories", source_url=url,
                                 content_type="application/json", metadata={"repositories": slim})
            return slim
        except Exception:
            return []

    def _hackertarget_hosts(self, domain: str, root: int) -> list[dict[str, str]]:
        """Use HackerTarget's free passive host-search endpoint; no scanning is performed."""
        url = FREE_API_ENDPOINTS["hackertarget_hostsearch"].format(domain=urllib.parse.quote(domain))
        try:
            r = http_get(url, self.timeout, max_bytes=600_000, accept="text/plain,*/*;q=0.8")
            text = _response_text(r.body, 600_000).strip()
            if r.status != 200 or text.lower().startswith(("error", "api count exceeded", "invalid")):
                return []
            rows: list[dict[str, str]] = []
            for line in text.splitlines()[:500]:
                if "," not in line:
                    continue
                host, ip = (x.strip().lower().rstrip(".") for x in line.split(",", 1))
                if host == domain or host.endswith("." + domain):
                    rows.append({"host": host, "ip": ip})
                    hid = self._entity("domain", host, confidence=0.66, source="HackerTarget passive host search")
                    self.db.add_relation(self.case_id, root, hid, "passive_subdomain",
                                         confidence=0.66, source="HackerTarget")
                    with contextlib.suppress(ValueError):
                        ipaddress.ip_address(ip)
                        iid = self._entity("ip", ip, confidence=0.6, source="HackerTarget passive host search")
                        self.db.add_relation(self.case_id, hid, iid, "observed_resolve_to",
                                             confidence=0.6, source="HackerTarget")
            self.db.add_evidence(self.case_id, root, "hackertarget_hostsearch", source_url=url,
                                 content_type="text/plain", metadata={"rows": rows})
            return rows
        except Exception:
            return []

    def _otx_passive_dns(self, domain: str, root: int) -> list[dict[str, Any]]:
        """Read public passive-DNS observations from OTX when the endpoint permits anonymous access."""
        url = FREE_API_ENDPOINTS["otx_passive_dns"].format(domain=urllib.parse.quote(domain))
        try:
            data = http_json(url, self.timeout)
            records = data.get("passive_dns", []) if isinstance(data, dict) else []
            slim: list[dict[str, Any]] = []
            for row in records[:500]:
                if not isinstance(row, dict):
                    continue
                host = str(row.get("hostname") or "").lower().rstrip(".")
                address = str(row.get("address") or "").strip()
                rec = {k: row.get(k) for k in ("hostname", "address", "record_type", "first", "last")}
                slim.append(rec)
                if host and (host == domain or host.endswith("." + domain)):
                    hid = self._entity("domain", host, confidence=0.64, source="OTX passive DNS")
                    self.db.add_relation(self.case_id, root, hid, "passive_subdomain",
                                         confidence=0.64, source="OTX passive DNS")
                    with contextlib.suppress(ValueError):
                        ipaddress.ip_address(address)
                        iid = self._entity("ip", address, confidence=0.58, source="OTX passive DNS")
                        self.db.add_relation(self.case_id, hid, iid, "historical_resolve_to",
                                             confidence=0.58, source="OTX passive DNS")
            self.db.add_evidence(self.case_id, root, "otx_passive_dns", source_url=url,
                                 content_type="application/json", metadata={"records": slim})
            return slim
        except Exception:
            return []

    def _wayback_hosts(self, domain: str, root: int) -> list[str]:
        """Derive historical hostnames from archived URLs, a passive subdomain source."""
        params = urllib.parse.urlencode({
            "url": f"*.{domain}/*", "output": "json", "fl": "original",
            "filter": "statuscode:200", "collapse": "urlkey", "limit": "300",
        })
        url = FREE_API_ENDPOINTS["wayback_cdx"] + "?" + params
        try:
            data = http_json(url, max(self.timeout, 15))
            hosts: set[str] = set()
            if isinstance(data, list):
                for row in data[1:] if data and isinstance(data[0], list) else data:
                    raw = row[0] if isinstance(row, list) and row else ""
                    host = (urllib.parse.urlsplit(str(raw)).hostname or "").lower().rstrip(".")
                    if host == domain or host.endswith("." + domain):
                        hosts.add(host)
            for host in sorted(hosts):
                hid = self._entity("domain", host, confidence=0.58, source="Wayback archived host")
                self.db.add_relation(self.case_id, root, hid, "historical_subdomain",
                                     confidence=0.58, source="Wayback Machine")
            self.db.add_evidence(self.case_id, root, "wayback_hostnames", source_url=url,
                                 metadata={"hostnames": sorted(hosts)})
            return sorted(hosts)
        except Exception:
            return []

    def passive_domain_intelligence(self, domain: str, root: int) -> dict[str, Any]:
        """Native passive host discovery from independent public sources."""
        return {
            "hackertarget": self._hackertarget_hosts(domain, root),
            "otx_passive_dns": self._otx_passive_dns(domain, root),
            "wayback_hostnames": self._wayback_hosts(domain, root),
        }

    def _ripe_ip_intelligence(self, ip: str, root: int) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, evidence_kind in (("ripe_network_info", "ripe_network_info"),
                                   ("ripe_reverse_dns", "ripe_reverse_dns")):
            url = FREE_API_ENDPOINTS[key].format(resource=urllib.parse.quote(ip))
            try:
                data = http_json(url, self.timeout)
                payload = data.get("data", {}) if isinstance(data, dict) else {}
                result[evidence_kind] = payload
                self.db.add_evidence(self.case_id, root, evidence_kind, source_url=url,
                                     content_type="application/json", metadata={"response": payload})
                if evidence_kind == "ripe_network_info":
                    prefix = payload.get("prefix")
                    if prefix:
                        pid = self._entity("other", "prefix:" + str(prefix), label="Network prefix",
                                           confidence=0.8, source="RIPEstat")
                        self.db.add_relation(self.case_id, root, pid, "network_prefix",
                                             confidence=0.8, source="RIPEstat")
                    for asn in payload.get("asns", []) or []:
                        aid = self._entity("asn", "AS" + str(asn), label="Autonomous System",
                                           confidence=0.8, source="RIPEstat")
                        self.db.add_relation(self.case_id, root, aid, "announced_by",
                                             confidence=0.8, source="RIPEstat")
            except Exception:
                continue
        return result

    def crawl_site(self, start_url: str, parent_id: int, max_pages: Optional[int] = None,
                   max_depth: int = 2) -> dict[str, Any]:
        """
        Polite native OSINT crawler: same-site public pages only, robots-aware, bounded,
        no cookies/authentication, and no secret extraction. It discovers URLs, public
        contact strings, documents, social profiles, JavaScript files and public endpoints.
        """
        start_url = normalize_url(start_url)
        parsed = urllib.parse.urlsplit(start_url)
        base_host = (parsed.hostname or "").lower()
        if not base_host:
            return {"pages": [], "errors": ["No hostname"]}
        if max_pages is None:
            with contextlib.suppress(Exception):
                max_pages = int(os.environ.get("DIGITAL_FOOTPRINT_FINDER_CRAWL_PAGES", str(load_settings().get("max_crawl_pages", 18))))
        max_pages = max(1, min(int(max_pages or load_settings().get("max_crawl_pages", 18)), 80))
        max_depth = max(0, min(max_depth, 3))

        origin = f"{parsed.scheme}://{parsed.netloc}"
        robots_url = origin + "/robots.txt"
        robots = urllib.robotparser.RobotFileParser()
        robots.set_url(robots_url)
        robots_loaded = False
        try:
            rr = http_get(robots_url, self.timeout, max_bytes=250_000)
            if rr.status == 200:
                robots.parse(_response_text(rr.body, 250_000).splitlines())
                robots_loaded = True
        except Exception:
            pass

        queue: list[tuple[str, int]] = [(start_url, 0)]
        seen: set[str] = set()
        pages: list[dict[str, Any]] = []
        all_urls: set[str] = set()
        emails: set[str] = set()
        phones: set[str] = set()
        documents: set[str] = set()
        social: set[str] = set()
        js_files: set[str] = set()
        endpoints: set[str] = set()
        errors: list[str] = []

        while queue and len(pages) < max_pages:
            current, depth = queue.pop(0)
            current = urllib.parse.urldefrag(current)[0]
            if current in seen or not _same_site(current, base_host):
                continue
            seen.add(current)
            if robots_loaded and not robots.can_fetch(USER_AGENT, current):
                continue
            try:
                r = http_get(current, self.timeout, max_bytes=1_200_000, accept="text/html,*/*;q=0.8")
            except Exception as exc:
                errors.append(f"{current}: {exc}")
                continue
            ctype = r.headers.get("content-type", "").lower()
            if "html" not in ctype and not r.body.lstrip().lower().startswith((b"<!doctype html", b"<html")):
                continue
            intel = extract_page_intelligence(r.final_url, r.body)
            links = extract_links(r.final_url, r.body, limit=250)
            pages.append({
                "url": current, "final_url": r.final_url, "status": r.status,
                "title": extract_title(r.body), "sha256": sha256_bytes(r.body),
                "depth": depth, "links": len(links),
            })
            for e in intel.get("public_emails", []):
                emails.add(str(e))
            for p in intel.get("public_phones", []):
                phones.add(str(p))
            documents.update(str(x) for x in intel.get("documents", []))
            social.update(str(x) for x in intel.get("social_links", []))
            js_files.update(str(x) for x in intel.get("javascript", []))

            for link in links:
                link = urllib.parse.urldefrag(link)[0]
                all_urls.add(link)
                lpath = urllib.parse.urlsplit(link).path.lower()
                if Path(lpath).suffix.lower() in DOCUMENT_EXTENSIONS:
                    documents.add(link)
                if lpath.endswith(".js"):
                    js_files.add(link)
                host = (urllib.parse.urlsplit(link).hostname or "").lower()
                if any(h in host for h in SOCIAL_HOST_HINTS):
                    social.add(link)
                if depth < max_depth and _same_site(link, base_host):
                    if Path(lpath).suffix.lower() not in DOCUMENT_EXTENSIONS and not lpath.endswith(".js"):
                        queue.append((link, depth + 1))

            # Very small delay keeps a bounded crawler polite on small sites.
            time.sleep(0.08)

        # JavaScript endpoint discovery, bounded separately.
        for js_url in list(sorted(js_files))[:10]:
            if not _same_site(js_url, base_host):
                continue
            try:
                jr = http_get(js_url, self.timeout, max_bytes=700_000, accept="application/javascript,text/javascript,*/*;q=0.5")
                for endpoint in _extract_js_endpoints(jr.final_url, jr.body, limit=80):
                    if _same_site(endpoint, base_host):
                        endpoints.add(endpoint)
            except Exception:
                continue

        # Sitemap adds public URLs without aggressively crawling them.
        sitemap_urls: set[str] = set()
        try:
            sr = http_get(origin + "/sitemap.xml", self.timeout, max_bytes=1_000_000)
            if sr.status == 200:
                sitemap_urls.update(_parse_sitemap_urls(_response_text(sr.body, 1_000_000), 500))
        except Exception:
            pass

        for value in sorted(all_urls)[:500]:
            uid = self._entity("url", value, confidence=0.46, source="native site crawler")
            self.db.add_relation(self.case_id, parent_id, uid, "crawl_url",
                                 confidence=0.46, source="native site crawler")
        for value in sorted(documents)[:200]:
            uid = self._entity("url", value, label="Public document", confidence=0.58, source="native site crawler")
            self.db.add_relation(self.case_id, parent_id, uid, "public_document",
                                 confidence=0.58, source="native site crawler")
        for value in sorted(social)[:100]:
            sid = self._entity("social", value, label="Linked social/profile", confidence=0.55, source="native site crawler")
            self.db.add_relation(self.case_id, parent_id, sid, "linked_social",
                                 confidence=0.55, source="native site crawler")
        for value in sorted(emails)[:100]:
            eid = self._entity("email", value, confidence=0.62, source="native site crawler")
            self.db.add_relation(self.case_id, parent_id, eid, "public_email_reference",
                                 confidence=0.62, source="native site crawler")
        for value in sorted(phones)[:80]:
            pid = self._entity("phone", value, confidence=0.48, source="native site crawler")
            self.db.add_relation(self.case_id, parent_id, pid, "public_phone_reference",
                                 confidence=0.48, source="native site crawler")
        for value in sorted(js_files)[:100]:
            jid = self._entity("url", value, label="JavaScript", confidence=0.5, source="native site crawler")
            self.db.add_relation(self.case_id, parent_id, jid, "javascript_file",
                                 confidence=0.5, source="native site crawler")
        for value in sorted(endpoints)[:200]:
            eid = self._entity("url", value, label="Public JS endpoint", confidence=0.48, source="native JS endpoint extraction")
            self.db.add_relation(self.case_id, parent_id, eid, "public_endpoint",
                                 confidence=0.48, source="native JS endpoint extraction")
        for value in sorted(sitemap_urls)[:500]:
            uid = self._entity("url", value, label="Sitemap URL", confidence=0.56, source="sitemap.xml")
            self.db.add_relation(self.case_id, parent_id, uid, "sitemap_url",
                                 confidence=0.56, source="sitemap.xml")

        summary = {
            "pages": pages, "urls": sorted(all_urls)[:500], "emails": sorted(emails),
            "phones": sorted(phones), "documents": sorted(documents), "social_links": sorted(social),
            "javascript": sorted(js_files), "endpoints": sorted(endpoints),
            "sitemap_urls": sorted(sitemap_urls)[:500], "robots_respected": robots_loaded,
            "errors": errors[:30],
        }
        self.db.add_evidence(self.case_id, parent_id, "native_site_crawl", source_url=start_url,
                             metadata=summary)
        return summary

    def domain_mail_posture(self, domain: str, root: int) -> dict[str, Any]:
        """Inspect public email-delivery/security records and MTA-STS policy."""
        domain = clean_domain(domain)
        mx = run_dig(domain, "MX")
        txt = run_dig(domain, "TXT")
        spf = [x for x in txt if "v=spf1" in x.lower()]
        dmarc = [x for x in run_dig("_dmarc." + domain, "TXT") if "v=dmarc1" in x.lower()]
        tls_rpt = [x for x in run_dig("_smtp._tls." + domain, "TXT") if "v=tlsrptv1" in x.lower()]
        mta_sts_txt = [x for x in run_dig("_mta-sts." + domain, "TXT") if "v=stsv1" in x.lower()]
        bimi = run_dig("default._bimi." + domain, "TXT")
        providers: set[str] = set()
        joined = " ".join(mx).lower()
        provider_hints = {
            "Google Workspace": ("google.com", "googlemail.com"),
            "Microsoft 365": ("protection.outlook.com",),
            "Proton Mail": ("protonmail.ch", "protonmail.com"),
            "Fastmail": ("messagingengine.com",),
            "Zoho Mail": ("zoho.",),
            "Amazon SES": ("amazonses.com",),
        }
        for provider, hints in provider_hints.items():
            if any(h in joined for h in hints):
                providers.add(provider)
                sid = self._entity("service", provider, label="Mail provider", confidence=0.72, source="MX fingerprint")
                self.db.add_relation(self.case_id, root, sid, "mail_provider_hint", confidence=0.72, source="MX records")

        policy = None
        policy_url = f"https://mta-sts.{domain}/.well-known/mta-sts.txt"
        if mta_sts_txt:
            with contextlib.suppress(Exception):
                r = http_get(policy_url, self.timeout, max_bytes=100_000, accept="text/plain,*/*;q=0.5")
                if r.status == 200:
                    policy = _response_text(r.body, 100_000)
                    self.db.add_evidence(self.case_id, root, "mta_sts_policy", source_url=policy_url,
                                         content_type=r.headers.get("content-type", "text/plain"),
                                         metadata={"status": r.status}, body=r.body)
        posture = {
            "mx": mx, "spf": spf, "dmarc": dmarc, "tls_rpt": tls_rpt,
            "mta_sts_txt": mta_sts_txt, "mta_sts_policy": policy, "bimi": bimi,
            "provider_hints": sorted(providers),
            "signals": {
                "spf": bool(spf), "dmarc": bool(dmarc), "tls_reporting": bool(tls_rpt),
                "mta_sts": bool(mta_sts_txt and policy), "bimi_default_selector": bool(bimi),
            },
        }
        self.db.add_evidence(self.case_id, root, "domain_mail_posture", metadata=posture)
        return posture

    def _common_crawl_domain(self, domain: str, root: int, limit: int = 120) -> dict[str, Any]:
        """Query the latest Common Crawl URL index without downloading crawl bodies."""
        result: dict[str, Any] = {"collection": None, "urls": [], "hosts": [], "errors": []}
        try:
            collections = http_json(FREE_API_ENDPOINTS["commoncrawl_collections"], max(self.timeout, 15))
            if not isinstance(collections, list) or not collections:
                return result
            latest = collections[0]
            api = str(latest.get("cdx-api") or "").strip()
            result["collection"] = latest.get("id")
            if not api:
                return result
            params = urllib.parse.urlencode({
                "url": f"*.{domain}/*",
                "output": "json",
                "collapse": "urlkey",
                "limit": str(max(20, min(limit, 300))),
            })
            query_url = api + ("&" if "?" in api else "?") + params
            rows = http_json_lines(query_url, max(self.timeout, 20), max_bytes=5_000_000)
            urls: set[str] = set()
            hosts: set[str] = set()
            kept_rows: list[dict[str, Any]] = []
            for row in rows[:limit]:
                url = str(row.get("url") or "").strip()
                if not url:
                    continue
                host = clean_domain(url)
                if host == domain or host.endswith("." + domain):
                    urls.add(url)
                    hosts.add(host)
                    kept_rows.append({k: row.get(k) for k in ("url", "timestamp", "status", "mime", "digest") if row.get(k) is not None})
            result["urls"] = sorted(urls)[:limit]
            result["hosts"] = sorted(hosts)[:limit]
            for host in result["hosts"]:
                hid = self._entity("domain", host, confidence=0.58, source="Common Crawl index")
                self.db.add_relation(self.case_id, root, hid, "commoncrawl_host", confidence=0.58, source="Common Crawl")
            for url in result["urls"][:100]:
                uid = self._entity("url", url, confidence=0.52, source="Common Crawl index")
                self.db.add_relation(self.case_id, root, uid, "commoncrawl_url", confidence=0.52, source="Common Crawl")
            self.db.add_evidence(self.case_id, root, "commoncrawl_index", source_url=query_url,
                                 content_type="application/x-ndjson", metadata={"collection": result["collection"], "rows": kept_rows})
        except Exception as exc:
            result["errors"].append(str(exc))
        return result

    def _wikidata_candidates(self, query: str, root: int, entity_kind: str = "person") -> list[dict[str, Any]]:
        """Low-confidence candidate search. Candidate records stay separate from the user's target."""
        params = urllib.parse.urlencode({
            "action": "wbsearchentities", "search": query, "language": "en", "format": "json", "limit": "5"
        })
        url = FREE_API_ENDPOINTS["wikidata_api"] + "?" + params
        out: list[dict[str, Any]] = []
        try:
            data = http_json(url, self.timeout)
            for row in (data.get("search", []) if isinstance(data, dict) else [])[:5]:
                qid = str(row.get("id") or "").strip()
                if not qid:
                    continue
                label = str(row.get("label") or "").strip()
                description = str(row.get("description") or "").strip()
                candidate = {
                    "id": qid, "label": label, "description": description,
                    "url": f"https://www.wikidata.org/wiki/{qid}",
                }
                out.append(candidate)
                cid = self._entity("identifier", f"Wikidata:{qid}", label=label or "Wikidata candidate",
                                   confidence=0.28, source="Wikidata search")
                self.db.add_relation(self.case_id, root, cid, f"possible_{entity_kind}_record",
                                     confidence=0.28, source="Wikidata search; verify candidate")
                # Fetch selected public identifiers/websites attached to the candidate itself.
                detail_params = urllib.parse.urlencode({
                    "action": "wbgetentities", "ids": qid, "props": "claims|sitelinks|labels|descriptions",
                    "languages": "en", "format": "json"
                })
                with contextlib.suppress(Exception):
                    detail_url = FREE_API_ENDPOINTS["wikidata_api"] + "?" + detail_params
                    detail = http_json(detail_url, self.timeout)
                    entity = (detail.get("entities", {}) or {}).get(qid, {}) if isinstance(detail, dict) else {}
                    claims = entity.get("claims", {}) or {}
                    property_map = {
                        "P856": ("url", "official_website"),
                        "P496": ("identifier", "orcid"),
                        "P2037": ("username", "github_username"),
                        "P2002": ("username", "x_username"),
                        "P2397": ("identifier", "youtube_channel_id"),
                    }
                    candidate_details: dict[str, list[str]] = {}
                    for prop, (typ, relation) in property_map.items():
                        values: list[str] = []
                        for claim in (claims.get(prop, []) or [])[:10]:
                            value = (((claim.get("mainsnak") or {}).get("datavalue") or {}).get("value"))
                            if isinstance(value, str) and value.strip():
                                values.append(value.strip())
                                eid = self._entity(typ, value.strip(), confidence=0.82, source=f"Wikidata {qid} {prop}")
                                self.db.add_relation(self.case_id, cid, eid, relation, confidence=0.82, source="Wikidata statement")
                        if values:
                            candidate_details[prop] = values
                    enwiki = ((entity.get("sitelinks") or {}).get("enwiki") or {}).get("title")
                    if enwiki:
                        wiki_url = "https://en.wikipedia.org/wiki/" + urllib.parse.quote(str(enwiki).replace(" ", "_"), safe="_()")
                        wid = self._entity("url", wiki_url, label="English Wikipedia", confidence=0.9, source=f"Wikidata {qid} sitelink")
                        self.db.add_relation(self.case_id, cid, wid, "encyclopedia_page", confidence=0.9, source="Wikidata sitelink")
                        candidate["wikipedia"] = wiki_url
                    if candidate_details:
                        candidate["identifiers"] = candidate_details
            self.db.add_evidence(self.case_id, root, "wikidata_candidates", source_url=url,
                                 content_type="application/json", metadata={"query": query, "candidates": out})
        except Exception:
            return out
        return out

    def _crossref_author_candidates(self, name: str, root: int, rows: int = 6) -> list[dict[str, Any]]:
        """Search public scholarly metadata and keep matches explicitly candidate-level."""
        params = urllib.parse.urlencode({"query.author": name, "rows": str(max(1, min(rows, 10)))})
        url = FREE_API_ENDPOINTS["crossref_works"] + "?" + params
        out: list[dict[str, Any]] = []
        try:
            data = http_json(url, max(self.timeout, 15))
            items = (((data or {}).get("message") or {}).get("items") or []) if isinstance(data, dict) else []
            query_norm = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
            for item in items[:rows]:
                doi = str(item.get("DOI") or "").strip()
                title_raw = item.get("title") or []
                title = str(title_raw[0] if isinstance(title_raw, list) and title_raw else title_raw or "").strip()
                matched_authors: list[str] = []
                for author in item.get("author", []) or []:
                    full = " ".join(str(author.get(k) or "").strip() for k in ("given", "family")).strip()
                    norm = re.sub(r"[^a-z0-9]+", " ", full.lower()).strip()
                    if norm and (norm == query_norm or query_norm in norm or norm in query_norm):
                        matched_authors.append(full)
                record = {
                    "doi": doi, "title": title, "type": item.get("type"), "publisher": item.get("publisher"),
                    "url": item.get("URL"), "matched_authors": matched_authors,
                }
                out.append(record)
                key = f"DOI:{doi}" if doi else (title or str(item.get("URL") or "publication"))
                pid = self._entity("publication", key, label=title[:160], confidence=0.45 if matched_authors else 0.25,
                                   source="Crossref author search")
                self.db.add_relation(self.case_id, root, pid, "possible_author_of",
                                     confidence=0.42 if matched_authors else 0.22,
                                     source="Crossref name match; verify authorship")
                if item.get("URL"):
                    uid = self._entity("url", str(item.get("URL")), confidence=0.8, source="Crossref")
                    self.db.add_relation(self.case_id, pid, uid, "publication_url", confidence=0.8, source="Crossref")
            self.db.add_evidence(self.case_id, root, "crossref_author_candidates", source_url=url,
                                 content_type="application/json", metadata={"query": name, "works": out})
        except Exception:
            return out
        return out

    def doi(self, value: str) -> dict[str, Any]:
        doi = strip_explicit_target_prefix(value)
        doi = re.sub(r"(?i)^https?://(?:dx\.)?doi\.org/", "", doi).strip()
        if not re.fullmatch(r"(?i)10\.\d{4,9}/[-._;()/:A-Z0-9]+", doi):
            raise ValueError("Enter a valid DOI, e.g. 10.1000/example")
        root = self._entity("publication", "DOI:" + doi, label="DOI", confidence=1.0, source="user")
        url = FREE_API_ENDPOINTS["crossref_works"] + "/" + urllib.parse.quote(doi, safe="")
        result: dict[str, Any] = {"doi": doi, "metadata": None, "errors": []}
        try:
            data = http_json(url, max(self.timeout, 15))
            msg = (data.get("message") or {}) if isinstance(data, dict) else {}
            title_raw = msg.get("title") or []
            title = str(title_raw[0] if isinstance(title_raw, list) and title_raw else title_raw or "").strip()
            result["metadata"] = {
                "title": title, "type": msg.get("type"), "publisher": msg.get("publisher"),
                "URL": msg.get("URL"), "author": msg.get("author", []), "published": msg.get("published"),
                "created": msg.get("created"), "references_count": msg.get("reference-count"),
            }
            if title:
                self.db.add_entity(self.case_id, "publication", "DOI:" + doi, label=title[:180], confidence=1.0, source="Crossref DOI metadata")
            if msg.get("URL"):
                uid = self._entity("url", str(msg.get("URL")), confidence=0.92, source="Crossref DOI metadata")
                self.db.add_relation(self.case_id, root, uid, "publication_url", confidence=0.92, source="Crossref")
            for author in (msg.get("author") or [])[:50]:
                full = " ".join(str(author.get(k) or "").strip() for k in ("given", "family")).strip()
                if full:
                    aid = self._entity("person", full, confidence=0.88, source="Crossref DOI metadata")
                    self.db.add_relation(self.case_id, root, aid, "authored_by", confidence=0.88, source="Crossref")
                orcid = str(author.get("ORCID") or "").strip()
                if orcid:
                    oid = self._entity("identifier", orcid, label="ORCID", confidence=0.9, source="Crossref DOI metadata")
                    self.db.add_relation(self.case_id, root, oid, "author_orcid", confidence=0.9, source="Crossref")
            self.db.add_evidence(self.case_id, root, "crossref_doi_metadata", source_url=url,
                                 content_type="application/json", metadata={"response": result["metadata"]})
        except Exception as exc:
            result["errors"].append(str(exc))
        result["dorks"] = self.dorks(doi, "doi", attach_to=root)
        return result

    def asn(self, value: str) -> dict[str, Any]:
        raw = strip_explicit_target_prefix(value).upper().strip()
        if raw.isdigit():
            raw = "AS" + raw
        if not re.fullmatch(r"AS\d{1,10}", raw):
            raise ValueError("Enter an ASN such as AS13335")
        root = self._entity("asn", raw, confidence=1.0, source="user")
        result: dict[str, Any] = {"asn": raw, "overview": None, "prefixes": [], "errors": []}
        try:
            url = FREE_API_ENDPOINTS["ripe_as_overview"].format(resource=urllib.parse.quote(raw))
            data = http_json(url, self.timeout)
            overview = data.get("data", {}) if isinstance(data, dict) else {}
            result["overview"] = overview
            holder = str(overview.get("holder") or "").strip()
            if holder:
                oid = self._entity("organization", holder, confidence=0.82, source="RIPEstat AS overview")
                self.db.add_relation(self.case_id, root, oid, "asn_holder", confidence=0.82, source="RIPEstat")
            self.db.add_evidence(self.case_id, root, "ripe_as_overview", source_url=url,
                                 content_type="application/json", metadata={"response": overview})
        except Exception as exc:
            result["errors"].append(f"AS overview: {exc}")
        try:
            url = FREE_API_ENDPOINTS["ripe_announced_prefixes"].format(resource=urllib.parse.quote(raw))
            data = http_json(url, max(self.timeout, 15))
            payload = data.get("data", {}) if isinstance(data, dict) else {}
            prefixes = []
            for row in (payload.get("prefixes") or [])[:1000]:
                prefix = str(row.get("prefix") if isinstance(row, dict) else row).strip()
                if prefix:
                    prefixes.append(prefix)
                    pid = self._entity("prefix", prefix, confidence=0.85, source="RIPEstat announced prefixes")
                    self.db.add_relation(self.case_id, root, pid, "announces_prefix", confidence=0.85, source="RIPEstat")
            result["prefixes"] = prefixes
            self.db.add_evidence(self.case_id, root, "ripe_announced_prefixes", source_url=url,
                                 content_type="application/json", metadata={"prefixes": prefixes})
        except Exception as exc:
            result["errors"].append(f"Announced prefixes: {exc}")
        result["dorks"] = self.dorks(raw, "asn", attach_to=root)
        return result

    def prefix(self, value: str) -> dict[str, Any]:
        raw = strip_explicit_target_prefix(value).strip()
        try:
            network = ipaddress.ip_network(raw, strict=False)
        except ValueError as exc:
            raise ValueError("Enter a CIDR prefix such as 1.1.1.0/24") from exc
        prefix = str(network)
        root = self._entity("prefix", prefix, confidence=1.0, source="user")
        result: dict[str, Any] = {"prefix": prefix, "overview": None, "errors": []}
        try:
            url = FREE_API_ENDPOINTS["ripe_prefix_overview"].format(resource=urllib.parse.quote(prefix))
            data = http_json(url, self.timeout)
            overview = data.get("data", {}) if isinstance(data, dict) else {}
            result["overview"] = overview
            for asn_value in overview.get("asns", []) or []:
                asn_text = str(asn_value)
                if not asn_text.upper().startswith("AS"):
                    asn_text = "AS" + asn_text
                aid = self._entity("asn", asn_text, confidence=0.85, source="RIPEstat prefix overview")
                self.db.add_relation(self.case_id, root, aid, "announced_by", confidence=0.85, source="RIPEstat")
            self.db.add_evidence(self.case_id, root, "ripe_prefix_overview", source_url=url,
                                 content_type="application/json", metadata={"response": overview})
        except Exception as exc:
            result["errors"].append(str(exc))
        result["dorks"] = self.dorks(prefix, "prefix", attach_to=root)
        return result

    def hash_value(self, value: str) -> dict[str, Any]:
        raw = strip_explicit_target_prefix(value).strip().lower()
        raw = re.sub(r"^sha256:", "", raw)
        if not re.fullmatch(r"[a-f0-9]{64}", raw):
            raise ValueError("Only SHA-256 hashes are recognized in Easy Mode.")
        root = self._entity("hash", "sha256:" + raw, confidence=1.0, source="user")
        dorks = self.dorks(raw, "hash", attach_to=root)
        self.db.add_evidence(self.case_id, root, "hash_public_search_pack", metadata={"algorithm": "SHA-256", "value": raw})
        optional_apis = self.optional_api_enrichment("hash", raw, root)
        return {"algorithm": "SHA-256", "hash": raw, "dorks": dorks, "optional_apis": optional_apis,
                "note": "Digital Footprint Finder does not query credential dumps or private breach databases."}

    def organization(self, value: str) -> dict[str, Any]:
        name = strip_explicit_target_prefix(value)
        name = re.sub(r"\s+", " ", name).strip()
        if len(name) < 2:
            raise ValueError("Enter an organization name.")
        root = self._entity("organization", name, confidence=1.0, source="user")
        wikidata = self._wikidata_candidates(name, root, entity_kind="organization")
        ror = self._ror_candidates(name, root)
        openalex = self._openalex_institution_candidates(name, root)
        stackexchange = self._stackexchange_candidates(name, root)
        queries = [
            f'"{name}" official website', f'"{name}" site:github.com', f'"{name}" filetype:pdf',
            f'"{name}" (press OR newsroom OR about OR contact)',
        ]
        links = self.search_links(queries, add_entities=False)
        self._attach_search_leads(root, links)
        dorks = self.dorks(name, "organization", attach_to=root)
        return {"organization": name, "wikidata_candidates": wikidata, "ror_candidates": ror,
                "openalex_candidates": openalex, "stackexchange_candidates": stackexchange, "search_links": links, "dorks": dorks,
                "note": "Candidate records remain separate until independently verified."}

    def _ror_candidates(self, name: str, root: int, limit: int = 8) -> list[dict[str, Any]]:
        """Resolve organization-name candidates through the open ROR v2 registry."""
        out: list[dict[str, Any]] = []
        try:
            url = FREE_API_ENDPOINTS["ror_organizations"] + "?" + urllib.parse.urlencode({"affiliation": name})
            data = http_json(url, max(self.timeout, 15))
            items = (data or {}).get("items") or [] if isinstance(data, dict) else []
            for row in items[:limit]:
                if not isinstance(row, dict):
                    continue
                record = row.get("organization") if isinstance(row.get("organization"), dict) else row
                chosen = bool(row.get("chosen"))
                score = row.get("score")
                ror_id = str(record.get("id") or "").strip()
                display = _display_ror_name(record)
                domains = [str(x).lower() for x in (record.get("domains") or []) if x]
                links_raw = record.get("links") or []
                links: list[str] = []
                for item in links_raw:
                    if isinstance(item, dict) and item.get("value"):
                        links.append(str(item["value"]))
                    elif isinstance(item, str):
                        links.append(item)
                locations: list[str] = []
                for loc in record.get("locations") or []:
                    if not isinstance(loc, dict):
                        continue
                    details = loc.get("geonames_details") or {}
                    label = ", ".join(str(details.get(k) or "").strip() for k in ("name", "country_name") if details.get(k))
                    if label:
                        locations.append(label)
                candidate = {
                    "ror": ror_id, "name": display, "chosen": chosen, "score": score,
                    "domains": domains[:20], "links": links[:20], "locations": locations[:10],
                    "status": record.get("status"), "types": record.get("types") or [],
                }
                out.append(candidate)
                conf = 0.82 if chosen else 0.52
                oid = self._entity("organization", display or ror_id, label=display, confidence=conf, source="ROR affiliation matcher")
                self.db.add_relation(self.case_id, root, oid, "possible_public_candidate", confidence=conf,
                                     source="ROR affiliation matcher; verify organization identity")
                if ror_id:
                    iid = self._entity("identifier", ror_id, label="ROR", confidence=0.96, source="ROR")
                    self.db.add_relation(self.case_id, oid, iid, "ror_identifier", confidence=0.96, source="ROR")
                for domain in domains[:10]:
                    did = self._entity("domain", clean_domain(domain), confidence=0.88, source="ROR")
                    self.db.add_relation(self.case_id, oid, did, "official_domain_candidate", confidence=0.84, source="ROR")
                for link in links[:10]:
                    with contextlib.suppress(Exception):
                        uid = self._entity("url", normalize_url(link), confidence=0.88, source="ROR")
                        self.db.add_relation(self.case_id, oid, uid, "official_url_candidate", confidence=0.84, source="ROR")
                for location in locations[:5]:
                    lid = self._entity("location", location, confidence=0.78, source="ROR")
                    self.db.add_relation(self.case_id, oid, lid, "organization_location", confidence=0.76, source="ROR")
            self.db.add_evidence(self.case_id, root, "ror_candidates", source_url=url,
                                 content_type="application/json", metadata={"query": name, "candidates": out})
        except Exception:
            return out
        return out

    def _openalex_author_candidates(self, name: str, root: int, limit: int = 6) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        try:
            url = _openalex_url(FREE_API_ENDPOINTS["openalex_authors"], search=name, per_page=limit,
                                select="id,display_name,orcid,works_count,cited_by_count,last_known_institutions")
            data = http_json(url, max(self.timeout, 15))
            for row in ((data or {}).get("results") or [])[:limit]:
                if not isinstance(row, dict):
                    continue
                display = str(row.get("display_name") or "").strip()
                norm_q = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
                norm_d = re.sub(r"[^a-z0-9]+", " ", display.lower()).strip()
                similarity = difflib.SequenceMatcher(None, norm_q, norm_d).ratio() if norm_q and norm_d else 0.0
                institutions = []
                for inst in row.get("last_known_institutions") or []:
                    if isinstance(inst, dict):
                        institutions.append({"id": inst.get("id"), "name": inst.get("display_name"), "ror": inst.get("ror")})
                candidate = {"id": row.get("id"), "name": display, "orcid": row.get("orcid"),
                             "works_count": row.get("works_count"), "cited_by_count": row.get("cited_by_count"),
                             "institutions": institutions, "name_similarity": round(similarity, 3)}
                out.append(candidate)
                conf = min(0.72, 0.30 + similarity * 0.40)
                aid = self._entity("person", display or str(row.get("id") or "OpenAlex author"),
                                   confidence=conf, source="OpenAlex author search")
                self.db.add_relation(self.case_id, root, aid, "possible_public_candidate", confidence=conf,
                                     source="OpenAlex name search; verify identity")
                if row.get("id"):
                    iid = self._entity("identifier", str(row["id"]), label="OpenAlex Author", confidence=0.9, source="OpenAlex")
                    self.db.add_relation(self.case_id, aid, iid, "openalex_identifier", confidence=0.9, source="OpenAlex")
                if row.get("orcid"):
                    oid = self._entity("identifier", str(row["orcid"]), label="ORCID", confidence=0.9, source="OpenAlex")
                    self.db.add_relation(self.case_id, aid, oid, "orcid_identifier", confidence=0.9, source="OpenAlex")
                for inst in institutions[:6]:
                    if inst.get("name"):
                        inst_id = self._entity("organization", str(inst["name"]), confidence=0.72, source="OpenAlex")
                        self.db.add_relation(self.case_id, aid, inst_id, "known_institution_candidate", confidence=0.68,
                                             source="OpenAlex; verify current affiliation")
            self.db.add_evidence(self.case_id, root, "openalex_author_candidates", source_url=url,
                                 content_type="application/json", metadata={"query": name, "candidates": out})
        except Exception:
            return out
        return out

    def _openalex_institution_candidates(self, name: str, root: int, limit: int = 6) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        try:
            url = _openalex_url(FREE_API_ENDPOINTS["openalex_institutions"], search=name, per_page=limit,
                                select="id,display_name,ror,country_code,homepage_url,type,works_count,cited_by_count")
            data = http_json(url, max(self.timeout, 15))
            for row in ((data or {}).get("results") or [])[:limit]:
                if not isinstance(row, dict):
                    continue
                display = str(row.get("display_name") or "").strip()
                similarity = difflib.SequenceMatcher(None, name.lower(), display.lower()).ratio() if display else 0.0
                candidate = {k: row.get(k) for k in ("id","display_name","ror","country_code","homepage_url","type","works_count","cited_by_count")}
                candidate["name_similarity"] = round(similarity, 3)
                out.append(candidate)
                conf = min(0.76, 0.34 + similarity * 0.40)
                oid = self._entity("organization", display or str(row.get("id") or "OpenAlex institution"),
                                   confidence=conf, source="OpenAlex institution search")
                self.db.add_relation(self.case_id, root, oid, "possible_public_candidate", confidence=conf,
                                     source="OpenAlex institution search; verify identity")
                if row.get("ror"):
                    rid = self._entity("identifier", str(row["ror"]), label="ROR", confidence=0.92, source="OpenAlex")
                    self.db.add_relation(self.case_id, oid, rid, "ror_identifier", confidence=0.92, source="OpenAlex")
                if row.get("homepage_url"):
                    with contextlib.suppress(Exception):
                        uid = self._entity("url", normalize_url(str(row["homepage_url"])), confidence=0.82, source="OpenAlex")
                        self.db.add_relation(self.case_id, oid, uid, "homepage_candidate", confidence=0.78, source="OpenAlex")
            self.db.add_evidence(self.case_id, root, "openalex_institution_candidates", source_url=url,
                                 content_type="application/json", metadata={"query": name, "candidates": out})
        except Exception:
            return out
        return out

    def fediverse(self, value: str) -> dict[str, Any]:
        """Resolve an explicit Fediverse handle through WebFinger and its public actor document."""
        raw = strip_explicit_target_prefix(value).strip()
        raw = re.sub(r"^acct:", "", raw, flags=re.I).lstrip("@")
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", raw):
            raise ValueError("Use an explicit Fediverse handle such as @alice@example.social")
        username, host = raw.rsplit("@", 1)
        canonical = f"@{username}@{host.lower()}"
        root = self._entity("fediverse", canonical, label="Fediverse handle", confidence=1.0, source="user")
        result: dict[str, Any] = {"handle": canonical, "webfinger": None, "actor": None, "errors": []}
        resource = "acct:" + raw
        wf_url = f"https://{host}/.well-known/webfinger?" + urllib.parse.urlencode({"resource": resource})
        try:
            wf = http_json(wf_url, self.timeout)
            result["webfinger"] = wf
            self.db.add_evidence(self.case_id, root, "webfinger", source_url=wf_url,
                                 content_type="application/jrd+json", metadata={"response": wf})
            actor_url = ""
            for link in (wf.get("links") or []) if isinstance(wf, dict) else []:
                if not isinstance(link, dict):
                    continue
                href = str(link.get("href") or "")
                rel = str(link.get("rel") or "")
                typ = str(link.get("type") or "")
                if href:
                    with contextlib.suppress(Exception):
                        uid = self._entity("url", normalize_url(href), confidence=0.9, source="WebFinger")
                        self.db.add_relation(self.case_id, root, uid, "webfinger_link", confidence=0.88, source="WebFinger")
                if rel == "self" and ("activity+json" in typ or "ld+json" in typ):
                    actor_url = href
            if actor_url:
                actor_res = http_get(actor_url, self.timeout, max_bytes=1_000_000,
                                     accept="application/activity+json, application/ld+json, application/json")
                if 200 <= actor_res.status < 300:
                    actor = json.loads(actor_res.body.decode("utf-8", errors="replace"))
                    if isinstance(actor, dict):
                        safe_actor = {k: actor.get(k) for k in ("id","type","preferredUsername","name","url","summary","alsoKnownAs","manuallyApprovesFollowers")}
                        if safe_actor.get("summary"):
                            safe_actor["summary"] = truncate(strip_tags(str(safe_actor["summary"])), 1000)
                        result["actor"] = safe_actor
                        self.db.add_evidence(self.case_id, root, "activitypub_actor", source_url=actor_url,
                                             content_type=actor_res.headers.get("content-type", "application/json"),
                                             metadata={"actor": safe_actor}, body=actor_res.body)
                        if actor.get("url"):
                            urls = actor.get("url") if isinstance(actor.get("url"), list) else [actor.get("url")]
                            for u in urls[:8]:
                                if isinstance(u, dict): u = u.get("href")
                                if u:
                                    with contextlib.suppress(Exception):
                                        uid = self._entity("url", normalize_url(str(u)), confidence=0.94, source="ActivityPub actor")
                                        self.db.add_relation(self.case_id, root, uid, "public_profile", confidence=0.92, source="ActivityPub actor")
                        for aka in (actor.get("alsoKnownAs") or [])[:20]:
                            if isinstance(aka, str) and aka.startswith(("http://","https://")):
                                with contextlib.suppress(Exception):
                                    uid = self._entity("url", normalize_url(aka), confidence=0.8, source="ActivityPub alsoKnownAs")
                                    self.db.add_relation(self.case_id, root, uid, "also_known_as", confidence=0.76, source="ActivityPub actor; verify")
            # NodeInfo describes the public federated server itself and is useful
            # context without inspecting private account data.
            with contextlib.suppress(Exception):
                ni_well = f"https://{host}/.well-known/nodeinfo"
                ni_index = http_json(ni_well, self.timeout)
                links = ni_index.get("links") or [] if isinstance(ni_index, dict) else []
                ni_href = next((str(x.get("href")) for x in links if isinstance(x,dict) and x.get("href")), "")
                if ni_href:
                    ni = http_json(ni_href, self.timeout)
                    software = (ni.get("software") or {}) if isinstance(ni,dict) else {}
                    usage = (ni.get("usage") or {}) if isinstance(ni,dict) else {}
                    result["nodeinfo"] = {
                        "software": software, "protocols": ni.get("protocols") if isinstance(ni,dict) else None,
                        "openRegistrations": ni.get("openRegistrations") if isinstance(ni,dict) else None,
                        "usage": usage,
                    }
                    self.db.add_evidence(self.case_id, root, "nodeinfo", source_url=ni_href,
                                         content_type="application/json", metadata={"response": result["nodeinfo"]})
                    if software.get("name"):
                        sid=self._entity("service", f"{software.get('name')} {software.get('version') or ''}".strip(),
                                         label="Fediverse server software", confidence=0.9, source="NodeInfo")
                        self.db.add_relation(self.case_id, root, sid, "hosted_on_federated_software", confidence=0.86, source="NodeInfo")
        except Exception as exc:
            result["errors"].append(str(exc))
        result["dorks"] = self.dorks(canonical, "fediverse", attach_to=root)
        return result

    def dorks(self, target: str, typ: Optional[str] = None, attach_to: Optional[int] = None) -> dict[str, Any]:
        """Build safe public-information search dorks and save them as case leads."""
        target = target.strip()
        typ = typ or detect_target_type(target)
        q: list[tuple[str, str]] = []
        if typ == "person":
            q = [
                ("Exact name", f'"{target}"'),
                ("Documents", f'"{target}" (filetype:pdf OR filetype:docx OR filetype:xlsx)'),
                ("GitHub", f'"{target}" site:github.com'),
                ("GitLab", f'"{target}" site:gitlab.com'),
                ("LinkedIn", f'"{target}" site:linkedin.com/in'),
                ("Professional", f'"{target}" (company OR university OR researcher OR developer)'),
                ("Contact context", f'"{target}" (email OR contact OR profile)'),
                ("News", f'"{target}" (interview OR press OR news)'),
                ("Usernames/handles", f'"{target}" (username OR handle OR alias)'),
                ("Code mentions", f'"{target}" (site:github.com OR site:gitlab.com OR site:codeberg.org)'),
                ("Public datasets", f'"{target}" (filetype:csv OR filetype:xlsx OR filetype:json)'),
            ]
        elif typ == "username":
            u = target.lstrip("@")
            q = [
                ("Exact username", f'"{u}"'),
                ("GitHub", f'"{u}" site:github.com'),
                ("GitLab", f'"{u}" site:gitlab.com'),
                ("Reddit", f'"{u}" site:reddit.com'),
                ("DEV", f'"{u}" site:dev.to'),
                ("Medium", f'"{u}" site:medium.com'),
                ("Documents", f'"{u}" (filetype:pdf OR filetype:docx)'),
                ("Public contact context", f'"{u}" (email OR contact OR bio)'),
                ("Code platforms", f'"{u}" (site:github.com OR site:gitlab.com OR site:codeberg.org)'),
                ("Creator profiles", f'"{u}" (site:linktr.ee OR site:patreon.com OR site:ko-fi.com)'),
                ("Media profiles", f'"{u}" (site:youtube.com OR site:twitch.tv OR site:soundcloud.com)'),
            ]
        elif typ == "email":
            local, _, domain = target.partition("@")
            q = [
                ("Exact email", f'"{target}"'),
                ("Documents", f'"{target}" (filetype:pdf OR filetype:docx OR filetype:xlsx)'),
                ("GitHub", f'"{target}" site:github.com'),
                ("GitLab", f'"{target}" site:gitlab.com'),
                ("Local part + domain", f'"{local}" "{domain}"'),
                ("Public profiles", f'"{target}" (profile OR bio OR contact)'),
            ]
        elif typ == "domain":
            d = clean_domain(target)
            q = [
                ("Indexed pages", f'site:{d}'),
                ("Non-www hosts", f'site:{d} -www'),
                ("Documents", f'site:{d} (filetype:pdf OR filetype:docx OR filetype:xlsx)'),
                ("Public contacts", f'site:{d} (contact OR about OR team)'),
                ("Public email references", f'"@{d}"'),
                ("GitHub references", f'"{d}" site:github.com'),
                ("GitLab references", f'"{d}" site:gitlab.com'),
                ("External references", f'"{d}" -site:{d}'),
                ("Archived/index traces", f'"{d}" (cache OR archive OR snapshot)'),
                ("Subdomain mentions", f'".{d}" -site:{d}'),
                ("Public repositories", f'"{d}" (site:github.com OR site:gitlab.com OR site:codeberg.org)'),
                ("Public configs/docs", f'"{d}" (filetype:json OR filetype:xml OR filetype:yaml OR filetype:yml)'),
            ]
        elif typ == "url":
            u = normalize_url(target)
            host = urllib.parse.urlsplit(u).hostname or ""
            q = [
                ("Exact URL", f'"{u}"'),
                ("Host index", f'site:{host}'),
                ("External references", f'"{u}" -site:{host}'),
                ("Documents", f'site:{host} (filetype:pdf OR filetype:docx OR filetype:xlsx)'),
            ]
        elif typ == "phone":
            compact = re.sub(r"\D", "", target)
            q = [
                ("Exact phone", f'"{target}"'),
                ("Digits", f'"{compact}"'),
                ("Documents", f'"{target}" (filetype:pdf OR filetype:docx OR filetype:xlsx)'),
                ("Public contact pages", f'"{target}" (contact OR phone OR tel)'),
            ]
        elif typ == "ip":
            q = [
                ("Exact IP", f'"{target}"'),
                ("Public references", f'"{target}" (server OR host OR network)'),
                ("Shodan public pages", f'"{target}" site:shodan.io'),
                ("GitHub references", f'"{target}" site:github.com'),
            ]
        elif typ == "organization":
            q = [
                ("Exact organization", f'"{target}"'),
                ("Official site", f'"{target}" (official OR homepage OR website)'),
                ("Public documents", f'"{target}" (filetype:pdf OR filetype:docx OR filetype:xlsx)'),
                ("Developer presence", f'"{target}" (site:github.com OR site:gitlab.com)'),
                ("Press", f'"{target}" (press OR newsroom OR interview)'),
            ]
        elif typ == "doi":
            q = [("Exact DOI", f'"{target}"'), ("Citations", f'"{target}" (citation OR references OR bibliography)')]
        elif typ == "asn":
            q = [("Exact ASN", f'"{target}"'), ("Routing context", f'"{target}" (BGP OR prefix OR routing)')]
        elif typ == "prefix":
            q = [("Exact prefix", f'"{target}"'), ("Routing context", f'"{target}" (BGP OR ASN OR route)')]
        elif typ == "hash":
            q = [("Exact SHA-256", f'"{target}"'), ("Public analysis references", f'"{target}" (sha256 OR hash OR analysis)')]
        else:
            q = [("Exact value", f'"{target}"')]

        rows: list[dict[str, str]] = []
        for category, query in q:
            for engine, template in SEARCH_ENGINES.items():
                rows.append({"category": category, "engine": engine, "query": query,
                             "url": template.format(q=urllib.parse.quote_plus(query))})
        if attach_to is not None:
            self._attach_search_leads(attach_to, rows)
        self.db.add_evidence(self.case_id, attach_to, "dork_pack",
                             metadata={"target": target, "type": typ, "queries": q, "links": rows})
        return {"target": target, "type": typ, "queries": [{"category": a, "query": b} for a,b in q], "links": rows}

    def _github_user_api(self, username: str, root: int) -> Optional[dict[str, Any]]:
        url = FREE_API_ENDPOINTS["github_user"].format(username=urllib.parse.quote(username))
        try:
            data = http_json(url, self.timeout, extra_headers=api_headers("github"))
            if not isinstance(data, dict) or not data.get("login"):
                return None
            self.db.add_evidence(self.case_id, root, "github_public_api", source_url=url,
                                 content_type="application/json", metadata={"response": data})
            profile = data.get("html_url")
            if profile:
                pid = self._entity("url", str(profile), label="GitHub profile", confidence=0.9, source="GitHub public API")
                self.db.add_relation(self.case_id, root, pid, "github_profile", confidence=0.9, source="GitHub public API")
            for typ, key, rel, confidence in [
                ("person", "name", "public_name", 0.7),
                ("email", "email", "public_email", 0.75),
                ("organization", "company", "public_company", 0.55),
                ("location", "location", "public_location", 0.45),
                ("url", "blog", "public_blog", 0.6),
            ]:
                value = data.get(key)
                if value:
                    value = str(value).strip()
                    if typ == "url" and value and not value.startswith(("http://", "https://")):
                        value = "https://" + value
                    ent = self._entity(typ, value, confidence=confidence, source="GitHub public API")
                    self.db.add_relation(self.case_id, root, ent, rel, confidence=confidence, source="GitHub public API")
            if data.get("twitter_username"):
                social = self._entity("social", "X:@" + str(data["twitter_username"]), label="X", confidence=0.65, source="GitHub public API")
                self.db.add_relation(self.case_id, root, social, "public_social", confidence=0.65, source="GitHub public API")
            return data
        except Exception:
            return None

    def _gitlab_user_api(self, username: str, root: int) -> list[dict[str, Any]]:
        params = urllib.parse.urlencode({"username": username, "per_page": 5})
        url = FREE_API_ENDPOINTS["gitlab_users"].format(query=params)
        try:
            data = http_json(url, self.timeout)
            rows = data if isinstance(data, list) else []
            self.db.add_evidence(self.case_id, root, "gitlab_public_api", source_url=url,
                                 content_type="application/json", metadata={"response": rows})
            for row in rows[:5]:
                profile = row.get("web_url")
                if profile:
                    pid = self._entity("url", str(profile), label="GitLab profile", confidence=0.85, source="GitLab public API")
                    self.db.add_relation(self.case_id, root, pid, "gitlab_profile", confidence=0.85, source="GitLab public API")
                name = row.get("name")
                if name:
                    nid = self._entity("person", str(name), confidence=0.6, source="GitLab public API")
                    self.db.add_relation(self.case_id, root, nid, "public_name", confidence=0.6, source="GitLab public API")
                public_email = row.get("public_email")
                if public_email:
                    eid = self._entity("email", str(public_email), confidence=0.7, source="GitLab public API")
                    self.db.add_relation(self.case_id, root, eid, "public_email", confidence=0.7, source="GitLab public API")
            return rows
        except Exception:
            return []

    def _github_name_candidates(self, name: str, root: int) -> list[dict[str, Any]]:
        """Low-confidence public candidates. Never auto-promote to confirmed identity."""
        url = FREE_API_ENDPOINTS["github_user_search"].format(query=urllib.parse.quote(name))
        try:
            data = http_json(url, self.timeout, extra_headers=api_headers("github"))
            items = data.get("items", []) if isinstance(data, dict) else []
            items = items[:5]
            self.db.add_evidence(self.case_id, root, "github_name_candidates", source_url=url,
                                 content_type="application/json", metadata={"items": items})
            for row in items:
                if row.get("html_url"):
                    uid = self._entity("url", str(row["html_url"]), label="GitHub candidate", confidence=0.15, source="GitHub search API")
                    self.db.add_relation(self.case_id, root, uid, "possible_public_candidate", confidence=0.15, source="name-only GitHub search; verify")
            return items
        except Exception:
            return []

    def domain(self, domain: str, deep: bool = True) -> dict[str, Any]:
        domain = clean_domain(domain)
        if not domain or "." not in domain:
            raise ValueError("Enter a valid domain, e.g. example.com")

        root_id = self._entity("domain", domain, confidence=1.0, source="user")
        result: dict[str, Any] = {
            "domain": domain,
            "resolved_ips": [],
            "dns": {},
            "rdap": None,
            "certificates": [],
            "wayback": [],
            "web": None,
            "tls": None,
            "network_intelligence": {},
            "errors": [],
        }

        # Basic address resolution.
        try:
            infos = socket.getaddrinfo(domain, None, type=socket.SOCK_STREAM)
            ips = sorted({item[4][0] for item in infos})
            result["resolved_ips"] = ips
            for ip in ips:
                ip_id = self._entity("ip", ip, confidence=0.95, source="DNS resolution")
                self.db.add_relation(
                    self.case_id, root_id, ip_id, "resolves_to",
                    confidence=0.95, source="DNS resolution"
                )
        except Exception as e:
            result["errors"].append(f"DNS resolution: {e}")

        # Rich DNS if dig exists.
        for typ in ("A", "AAAA", "MX", "NS", "TXT", "CNAME", "CAA", "SOA"):
            vals = run_dig(domain, typ)
            if vals:
                result["dns"][typ] = vals
                for val in vals[:50]:
                    if typ in {"A", "AAAA"}:
                        target_type = "ip"
                        target_value = val
                    elif typ in {"MX", "NS", "CNAME"}:
                        target_type = "domain"
                        target_value = val.split()[-1].rstrip(".")
                    else:
                        target_type = "other"
                        target_value = f"{typ}:{val}"
                    tid = self._entity(
                        target_type, target_value,
                        confidence=0.85, source=f"DNS {typ}"
                    )
                    self.db.add_relation(
                        self.case_id, root_id, tid, f"dns_{typ.lower()}",
                        confidence=0.85, source=f"DNS {typ}"
                    )

        # Public email-delivery/security posture is useful for organization/domain attribution.
        with contextlib.suppress(Exception):
            result["mail_posture"] = self.domain_mail_posture(domain, root_id)

        # RDAP registration data via the RDAP bootstrap service.
        try:
            rdap_url = FREE_API_ENDPOINTS["rdap_domain"].format(value=urllib.parse.quote(domain))
            rdap = http_json(rdap_url, self.timeout)
            result["rdap"] = rdap
            self.db.add_evidence(
                self.case_id, root_id, "rdap",
                source_url=rdap_url,
                content_type="application/json",
                metadata={"response": rdap},
            )
            for ns in rdap.get("nameservers", []) if isinstance(rdap, dict) else []:
                name = str(ns.get("ldhName") or "").lower().rstrip(".")
                if name:
                    nid = self._entity("domain", name, confidence=0.9, source="RDAP")
                    self.db.add_relation(
                        self.case_id, root_id, nid, "nameserver",
                        confidence=0.9, source="RDAP"
                    )
        except Exception as e:
            result["errors"].append(f"RDAP: {e}")

        if deep:
            # Certificate Transparency. Leads only; cert records are not proof of current ownership.
            try:
                crt_url = (
                    FREE_API_ENDPOINTS["crtsh"].format(query=urllib.parse.quote("%." + domain))
                )
                data = http_json(crt_url, max(self.timeout, 15))
                names: set[str] = set()
                if isinstance(data, list):
                    for cert in data[:2000]:
                        for key in ("name_value", "common_name"):
                            raw = str(cert.get(key) or "")
                            for name in raw.splitlines():
                                name = name.strip().lower().lstrip("*.").rstrip(".")
                                if name == domain or name.endswith("." + domain):
                                    names.add(name)
                result["certificates"] = sorted(names)[:500]
                for name in result["certificates"]:
                    sid = self._entity(
                        "domain", name, confidence=0.65,
                        source="Certificate Transparency"
                    )
                    self.db.add_relation(
                        self.case_id, root_id, sid, "certificate_name",
                        confidence=0.65, source="Certificate Transparency"
                    )
            except Exception as e:
                result["errors"].append(f"Certificate Transparency: {e}")

            # Wayback Machine CDX.
            try:
                cdx_params = urllib.parse.urlencode({
                    "url": f"{domain}/*",
                    "output": "json",
                    "fl": "timestamp,original,statuscode,mimetype,digest",
                    "filter": "statuscode:200",
                    "collapse": "urlkey",
                    "limit": "100",
                })
                cdx_url = FREE_API_ENDPOINTS["wayback_cdx"] + "?" + cdx_params
                cdx = http_json(cdx_url, max(self.timeout, 15))
                captures: list[dict[str, str]] = []
                if isinstance(cdx, list) and len(cdx) > 1:
                    headers = cdx[0]
                    for row in cdx[1:]:
                        if isinstance(row, list):
                            item = dict(zip(headers, row))
                            captures.append(item)
                result["wayback"] = captures
                self.db.add_evidence(
                    self.case_id, root_id, "wayback_index",
                    source_url=cdx_url, metadata={"captures": captures}
                )
                for item in captures[:100]:
                    u = item.get("original", "")
                    if u:
                        uid = self._entity(
                            "url", u, confidence=0.7, source="Wayback Machine"
                        )
                        self.db.add_relation(
                            self.case_id, root_id, uid, "archived_url",
                            confidence=0.7, source="Wayback Machine"
                        )
            except Exception as e:
                result["errors"].append(f"Wayback: {e}")

        # Website observation.
        try:
            result["web"] = self.url(f"https://{domain}", parent_id=root_id, shallow=True)
        except Exception as e:
            result["errors"].append(f"Website: {e}")

        if deep:
            try:
                tls = tls_certificate_info(domain, timeout=min(self.timeout, 8))
                result["tls"] = tls
                self.db.add_evidence(self.case_id, root_id, "tls_certificate",
                                     source_url=f"https://{domain}/", metadata=tls)
                for san in tls.get("subject_alt_names", [])[:300]:
                    san = san.lower().lstrip("*.").rstrip(".")
                    if san == domain or san.endswith("." + domain):
                        sid = self._entity("domain", san, confidence=0.76, source="current TLS certificate SAN")
                        self.db.add_relation(self.case_id, root_id, sid, "tls_subject_alt_name",
                                             confidence=0.76, source="current TLS certificate")
            except Exception as e:
                result["errors"].append(f"TLS certificate: {e}")
            for resolved_ip in result.get("resolved_ips", [])[:3]:
                ip_id = self._entity("ip", resolved_ip, confidence=0.95, source="DNS resolution")
                result["network_intelligence"][resolved_ip] = self._ripe_ip_intelligence(resolved_ip, ip_id)
            result["passive_sources"] = self.passive_domain_intelligence(domain, root_id)
            result["common_crawl"] = self._common_crawl_domain(domain, root_id)
            with contextlib.suppress(Exception):
                result["crawl"] = self.crawl_site(f"https://{domain}", root_id, max_depth=2)

        result["optional_apis"] = self.optional_api_enrichment("domain", domain, root_id)
        result["dorks"] = self.dorks(domain, "domain", attach_to=root_id)
        return result

    def ip(self, value: str) -> dict[str, Any]:
        ip = str(ipaddress.ip_address(value.strip()))
        eid = self._entity("ip", ip, confidence=1.0, source="user")
        result: dict[str, Any] = {"ip": ip, "rdap": None, "reverse_dns": [], "errors": []}

        try:
            host, aliases, _ = socket.gethostbyaddr(ip)
            names = sorted(set([host, *aliases]))
            result["reverse_dns"] = names
            for name in names:
                did = self._entity("domain", name.rstrip("."), confidence=0.65, source="PTR")
                self.db.add_relation(self.case_id, eid, did, "reverse_dns", confidence=0.65, source="PTR")
        except Exception as e:
            result["errors"].append(f"Reverse DNS: {e}")

        if is_public_ip(ip):
            try:
                url = FREE_API_ENDPOINTS["rdap_ip"].format(value=urllib.parse.quote(ip))
                data = http_json(url, self.timeout)
                result["rdap"] = data
                self.db.add_evidence(
                    self.case_id, eid, "rdap_ip",
                    source_url=url, content_type="application/json",
                    metadata={"response": data}
                )
            except Exception as e:
                result["errors"].append(f"RDAP: {e}")
            try:
                geo_url = FREE_API_ENDPOINTS["ipwhois"].format(ip=urllib.parse.quote(ip))
                geo = http_json(geo_url, self.timeout)
                if isinstance(geo, dict) and geo.get("success", True):
                    result["ip_intelligence"] = geo
                    self.db.add_evidence(self.case_id, eid, "ipwhois_public_api", source_url=geo_url,
                                         content_type="application/json", metadata={"response": geo})
                    conn = geo.get("connection") or {}
                    org = conn.get("org") or conn.get("isp") or geo.get("isp")
                    if org:
                        oid = self._entity("organization", str(org), confidence=0.55, source="ipwho.is public API")
                        self.db.add_relation(self.case_id, eid, oid, "network_organization", confidence=0.55, source="ipwho.is")
                    place = ", ".join(str(x) for x in [geo.get("city"), geo.get("region"), geo.get("country")] if x)
                    if place:
                        lid = self._entity("location", place, confidence=0.35, source="IP geolocation estimate")
                        self.db.add_relation(self.case_id, eid, lid, "approximate_ip_location", confidence=0.35, source="ipwho.is")
            except Exception as e:
                result["errors"].append(f"IP intelligence: {e}")
            result["ripe"] = self._ripe_ip_intelligence(ip, eid)
            try:
                reverse_url = FREE_API_ENDPOINTS["hackertarget_reverseip"].format(ip=urllib.parse.quote(ip))
                rr = http_get(reverse_url, self.timeout, max_bytes=400_000, accept="text/plain,*/*;q=0.8")
                reverse_hosts = []
                if rr.status == 200:
                    for line in _response_text(rr.body, 400_000).splitlines()[:200]:
                        host = line.strip().lower().rstrip(".")
                        if host and "." in host and not host.lower().startswith(("error", "api count")):
                            reverse_hosts.append(host)
                            hid = self._entity("domain", host, confidence=0.38, source="HackerTarget reverse-IP observation")
                            self.db.add_relation(self.case_id, eid, hid, "shared_ip_observation",
                                                 confidence=0.38, source="HackerTarget; shared hosting possible")
                    self.db.add_evidence(self.case_id, eid, "hackertarget_reverse_ip", source_url=reverse_url,
                                         content_type="text/plain", metadata={"hosts": reverse_hosts})
                result["reverse_ip_hosts"] = reverse_hosts
            except Exception as e:
                result["errors"].append(f"Reverse-IP passive lookup: {e}")
            result["optional_apis"] = self.optional_api_enrichment("ip", ip, eid)
            result["dorks"] = self.dorks(ip, "ip", attach_to=eid)
        else:
            result["errors"].append("Private/reserved address: external RDAP lookup skipped.")
        return result

    def url(
        self,
        value: str,
        *,
        parent_id: Optional[int] = None,
        shallow: bool = False,
    ) -> dict[str, Any]:
        url = normalize_url(value)
        uid = self._entity("url", url, confidence=1.0 if parent_id is None else 0.9, source="user")
        if parent_id:
            self.db.add_relation(self.case_id, parent_id, uid, "website", confidence=0.9, source="HTTP")

        parsed = urllib.parse.urlsplit(url)
        domain = parsed.hostname or ""
        did = self._entity("domain", domain, confidence=0.98, source="URL")
        self.db.add_relation(self.case_id, uid, did, "hosted_on_domain", confidence=0.98, source="URL parse")

        result: dict[str, Any] = {
            "requested_url": url,
            "final_url": None,
            "status": None,
            "title": None,
            "headers": {},
            "security_headers": {},
            "page_intelligence": {},
            "technology_hints": {},
            "document_metadata": {},
            "favicon_hashes": [],
            "content_sha256": None,
            "links": [],
            "robots": None,
            "security_txt": None,
            "sitemap": None,
            "errors": [],
        }

        try:
            r = http_get(url, self.timeout)
            result["final_url"] = r.final_url
            result["status"] = r.status
            result["headers"] = r.headers
            result["title"] = extract_title(r.body)
            result["content_sha256"] = sha256_bytes(r.body)
            result["security_headers"] = {
                h: r.headers.get(h) for h in SECURITY_HEADERS
            }
            result["links"] = extract_links(r.final_url, r.body, limit=80)
            result["page_intelligence"] = extract_page_intelligence(r.final_url, r.body)
            result["technology_hints"] = detect_technology_hints(
                r.headers, r.body, result["page_intelligence"]
            )
            suffix = Path(urllib.parse.urlsplit(r.final_url).path).suffix.lower()
            if suffix in {".pdf", ".docx", ".xlsx", ".pptx"}:
                result["document_metadata"] = extract_document_metadata_bytes(r.body, suffix)

            # Turn explicitly public contacts and canonical URLs into graph leads.
            for email_addr in result["page_intelligence"].get("public_emails", [])[:30]:
                eid = self._entity("email", email_addr, confidence=0.7, source=f"public page {r.final_url}")
                self.db.add_relation(self.case_id, uid, eid, "publicly_mentions_email", confidence=0.7, source="HTML")
            for phone in result["page_intelligence"].get("public_phones", [])[:20]:
                pid = self._entity("phone", phone, confidence=0.6, source=f"public page {r.final_url}")
                self.db.add_relation(self.case_id, uid, pid, "publicly_mentions_phone", confidence=0.6, source="HTML")
            canonical = result["page_intelligence"].get("canonical")
            if canonical and canonical != r.final_url:
                cid = self._entity("url", canonical, confidence=0.8, source="canonical link")
                self.db.add_relation(self.case_id, uid, cid, "canonical_url", confidence=0.8, source="HTML")
            for linked in result["page_intelligence"].get("same_as", [])[:80]:
                lid = self._entity("url", str(linked), label="Structured sameAs", confidence=0.72, source="JSON-LD sameAs")
                self.db.add_relation(self.case_id, uid, lid, "structured_same_as", confidence=0.72, source="JSON-LD")
            for tracker in result["page_intelligence"].get("tracker_ids", [])[:80]:
                tid = self._entity("identifier", str(tracker), label="Public web identifier", confidence=0.76, source="HTML/JavaScript fingerprint")
                self.db.add_relation(self.case_id, uid, tid, "uses_public_identifier", confidence=0.76, source="public page source")
            for tech in (result.get("technology_hints") or {}).get("technologies", [])[:40]:
                name = str(tech.get("name") or "").strip() if isinstance(tech, dict) else str(tech).strip()
                if name:
                    tid = self._entity("technology", name, confidence=0.58, source="public web fingerprint")
                    self.db.add_relation(self.case_id, did, tid, "technology_hint", confidence=0.58, source="headers/HTML")
            for favicon in result["page_intelligence"].get("favicons", [])[:20]:
                fid = self._entity("url", str(favicon), label="Favicon", confidence=0.65, source="HTML icon link")
                self.db.add_relation(self.case_id, uid, fid, "favicon", confidence=0.65, source="HTML")
            for favicon in result["page_intelligence"].get("favicons", [])[:3]:
                with contextlib.suppress(Exception):
                    fr = http_get(str(favicon), self.timeout, max_bytes=600_000, accept="image/*,*/*;q=0.5")
                    if 200 <= fr.status < 300 and fr.body:
                        digest = sha256_bytes(fr.body)
                        result["favicon_hashes"].append({"url": fr.final_url, "sha256": digest, "bytes": len(fr.body)})
                        hid = self._entity("hash", "sha256:" + digest, label="Favicon SHA-256", confidence=0.9, source="favicon bytes")
                        self.db.add_relation(self.case_id, uid, hid, "favicon_sha256", confidence=0.9, source="HTTP favicon capture")
                        self.db.add_evidence(self.case_id, hid, "favicon_capture", source_url=fr.final_url,
                                             content_type=fr.headers.get("content-type", "image/*"),
                                             metadata={"sha256": digest, "bytes": len(fr.body)}, body=fr.body)

            evid = {
                "requested_url": r.requested_url,
                "final_url": r.final_url,
                "status": r.status,
                "elapsed_seconds": round(r.elapsed, 3),
                "headers": r.headers,
                "title": result["title"],
                "page_intelligence": result["page_intelligence"],
                "technology_hints": result["technology_hints"],
                "document_metadata": result["document_metadata"],
                "favicon_hashes": result["favicon_hashes"],
            }
            self.db.add_evidence(
                self.case_id, uid, "http_capture",
                source_url=r.final_url,
                content_type=r.headers.get("content-type", ""),
                metadata=evid,
                body=r.body,
            )

            if r.final_url != url:
                fid = self._entity("url", r.final_url, confidence=0.95, source="HTTP redirect")
                self.db.add_relation(
                    self.case_id, uid, fid, "redirects_to",
                    confidence=0.95, source="HTTP"
                )

            if not shallow:
                for link in result["links"][:80]:
                    lid = self._entity("url", link, confidence=0.55, source=f"linked from {url}")
                    self.db.add_relation(
                        self.case_id, uid, lid, "links_to",
                        confidence=0.55, source="HTML"
                    )
        except Exception as e:
            result["errors"].append(f"HTTP: {e}")

        # robots.txt is useful public context, not an access-control bypass.
        if not shallow and domain:
            try:
                robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
                rr = http_get(robots_url, self.timeout, max_bytes=300_000)
                if rr.status == 200:
                    text = rr.body.decode("utf-8", errors="replace")
                    result["robots"] = text[:100_000]
                    self.db.add_evidence(
                        self.case_id, did, "robots_txt",
                        source_url=robots_url,
                        content_type=rr.headers.get("content-type", "text/plain"),
                        metadata={"status": rr.status},
                        body=rr.body,
                    )
            except Exception as e:
                result["errors"].append(f"robots.txt: {e}")

            for label, public_path in (("security_txt", "/.well-known/security.txt"), ("sitemap", "/sitemap.xml")):
                try:
                    public_url = f"{parsed.scheme}://{parsed.netloc}{public_path}"
                    pr = http_get(public_url, self.timeout, max_bytes=500_000)
                    if pr.status == 200:
                        text = pr.body.decode("utf-8", errors="replace")[:200_000]
                        result[label] = text
                        self.db.add_evidence(
                            self.case_id, did, label,
                            source_url=public_url,
                            content_type=pr.headers.get("content-type", "text/plain"),
                            metadata={"status": pr.status}, body=pr.body,
                        )
                except Exception as e:
                    result["errors"].append(f"{public_path}: {e}")

        if not shallow:
            with contextlib.suppress(Exception):
                result["crawl"] = self.crawl_site(url, uid, max_depth=2)

        result["optional_apis"] = self.optional_api_enrichment("url", url, uid)
        result["dorks"] = self.dorks(url, "url", attach_to=uid)
        return result

    def alias_variants(self, value: str, limit: int = 24) -> list[str]:
        """Generate conservative username/alias variants as leads only; do not probe them automatically."""
        raw = value.strip().lstrip("@").lower()
        pieces = [x for x in re.split(r"[._\-\s]+", raw) if x]
        variants: list[str] = []
        def add(v: str) -> None:
            v = re.sub(r"[^a-z0-9_.-]", "", v)[:64]
            if v and v != raw and v not in variants:
                variants.append(v)
        if len(pieces) >= 2:
            add("".join(pieces)); add("_".join(pieces)); add(".".join(pieces)); add("-".join(pieces))
            add(pieces[0][0] + pieces[-1]); add(pieces[0] + pieces[-1][0])
            add(pieces[-1] + pieces[0]); add(pieces[-1] + "." + pieces[0])
        if raw:
            add(raw.replace("_", ".")); add(raw.replace(".", "_")); add(raw.replace("-", "_"))
        return variants[:max(1, min(limit, 50))]

    def username(self, username: str, workers: int = 8) -> dict[str, Any]:
        username = username.strip().lstrip("@")
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", username):
            raise ValueError("Username contains unsupported characters.")

        root = self._entity("username", username, confidence=1.0, source="user")
        workers = max(1, min(workers, 12))
        items = list(USERNAME_SITES.items())
        # Optional cap for slow/mobile links; default searches the complete built-in catalog.
        with contextlib.suppress(Exception):
            limit = int(os.environ.get("DIGITAL_FOOTPRINT_FINDER_USERNAME_LIMIT", str(len(items))))
            items = items[:max(1, min(limit, len(items)))]

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            rows = list(ex.map(lambda item: self._probe_username_site(item, username), items))

        for row in rows:
            if row.get("result") in {"probable", "possible"}:
                self._add_profile_observation(
                    root, str(row.get("site")), str(row.get("url")),
                    float(row.get("confidence", 0.45)), str(row.get("method", "native probe")),
                )

        github = self._github_user_api(username, root)
        github_repos = self._github_repositories(username, root) if github else []
        gitlab = self._gitlab_user_api(username, root)
        aliases = self.alias_variants(username)
        stackexchange_candidates = self._stackexchange_candidates(username, root)
        for alias in aliases:
            aid = self._entity("username", alias, label="Unverified alias variant", confidence=0.12, source="generated alias variant")
            self.db.add_relation(self.case_id, root, aid, "possible_alias_variant", confidence=0.12, source="generated; not probed")
        dorks = self.dorks(username, "username", attach_to=root)

        probable = [r for r in rows if r.get("result") == "probable"]
        possible = [r for r in rows if r.get("result") == "possible"]
        unknown = [r for r in rows if r.get("result") == "unknown"]
        profile_intelligence: list[dict[str, Any]] = []
        # Enrich the strongest profile observations only; this keeps the default run fast.
        for row in (probable + possible)[:12]:
            info = self._enrich_public_profile(
                root, str(row.get("site")), str(row.get("url")), float(row.get("confidence", 0.45))
            )
            if info:
                profile_intelligence.append(info)
        self.db.add_evidence(
            self.case_id, root, "native_username_sweep",
            metadata={
                "username": username, "checked": len(rows), "results": rows,
                "probable": len(probable), "possible": len(possible), "unknown": len(unknown),
                "github": github, "github_repositories": github_repos, "gitlab": gitlab,
                "profile_intelligence": profile_intelligence, "alias_variants": aliases,
                "stackexchange_candidates": stackexchange_candidates,
            },
        )
        return {
            "username": username,
            "results": rows,
            "probable_profiles": probable,
            "possible_profiles": possible,
            "github_api": github,
            "github_repositories": github_repos,
            "gitlab_api": gitlab,
            "profile_intelligence": profile_intelligence,
            "alias_variants": aliases,
            "stackexchange_candidates": stackexchange_candidates,
            "dorks": dorks,
            "warning": (
                "A profile URL is an observation lead, not proof that multiple accounts belong "
                "to the same person. Digital Footprint Finder uses fake-user baselines to reduce wildcard "
                "HTTP false positives, but manual verification is still required."
            ),
        }

    def email(self, value: str) -> dict[str, Any]:
        email_addr = value.strip()
        m = re.fullmatch(r"([^@\s]+)@([^@\s]+\.[^@\s]+)", email_addr)
        if not m:
            raise ValueError("Invalid email address format.")
        local, domain = m.group(1), clean_domain(m.group(2))
        eid = self._entity("email", email_addr, confidence=1.0, source="user")
        did = self._entity("domain", domain, confidence=0.98, source="email domain")
        self.db.add_relation(self.case_id, eid, did, "email_domain", confidence=0.98, source="syntax")

        mail_posture = self.domain_mail_posture(domain, did)
        mx = mail_posture.get("mx", [])
        spf = mail_posture.get("spf", [])
        dmarc = mail_posture.get("dmarc", [])

        search_queries = [
            f'"{email_addr}"',
            f'"{email_addr}" filetype:pdf',
            f'"{email_addr}" site:github.com',
        ]
        links = self.search_links(search_queries, add_entities=False)
        self._attach_search_leads(eid, links)
        dorks = self.dorks(email_addr, "email", attach_to=eid)
        optional_apis = self.optional_api_enrichment("domain", domain, did)
        result = {
            "email": email_addr,
            "local_part": local,
            "domain": domain,
            "mx": mx,
            "spf": spf,
            "dmarc": dmarc,
            "mail_posture": mail_posture,
            "search_links": links,
            "dorks": dorks,
            "optional_apis": optional_apis,
        }
        self.db.add_evidence(self.case_id, eid, "email_public_context", metadata=result)
        return result

    def person(self, name: str) -> dict[str, Any]:
        name = re.sub(r"\s+", " ", name).strip()
        if len(name) < 3:
            raise ValueError("Enter a fuller name.")
        eid = self._entity("person", name, confidence=1.0, source="user")
        queries = [
            f'"{name}"',
            f'"{name}" LinkedIn',
            f'"{name}" GitHub',
            f'"{name}" site:gov',
            f'"{name}" filetype:pdf',
        ]
        links = self.search_links(queries, add_entities=False)
        self._attach_search_leads(eid, links)
        dorks = self.dorks(name, "person", attach_to=eid)
        github_candidates = self._github_name_candidates(name, eid)
        wikidata_candidates = self._wikidata_candidates(name, eid, entity_kind="person")
        crossref_candidates = self._crossref_author_candidates(name, eid)
        openalex_candidates = self._openalex_author_candidates(name, eid)
        stackexchange_candidates = self._stackexchange_candidates(name, eid)
        self.db.add_evidence(self.case_id, eid, "person_public_search_pack", metadata={
            "queries": queries, "links": links, "github_candidates": github_candidates,
            "wikidata_candidates": wikidata_candidates, "crossref_candidates": crossref_candidates,
            "openalex_candidates": openalex_candidates, "stackexchange_candidates": stackexchange_candidates
        })
        return {
            "person": name,
            "search_links": links,
            "dorks": dorks,
            "github_candidates": github_candidates,
            "wikidata_candidates": wikidata_candidates,
            "crossref_candidates": crossref_candidates,
            "openalex_candidates": openalex_candidates,
            "stackexchange_candidates": stackexchange_candidates,
            "note": "Name-only matches are ambiguous. Candidate records stay separate until multiple independent attributes corroborate them.",
        }

    def phone(self, value: str) -> dict[str, Any]:
        value = re.sub(r"\s+", " ", value).strip()
        compact = re.sub(r"[\s()./-]", "", value)
        if not re.fullmatch(r"\+?\d{8,16}", compact):
            raise ValueError("Enter a plausible international or national phone number.")
        eid = self._entity("phone", value, confidence=1.0, source="user")
        phone_info: dict[str, Any] = {}
        with contextlib.suppress(Exception):
            import phonenumbers  # type: ignore
            from phonenumbers import carrier, geocoder, timezone as phone_timezone  # type: ignore
            parsed = phonenumbers.parse(value, None if value.startswith("+") else "GR")
            phone_info = {
                "e164": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
                "international": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
                "possible": phonenumbers.is_possible_number(parsed),
                "valid": phonenumbers.is_valid_number(parsed),
                "region": geocoder.description_for_number(parsed, "en"),
                "carrier": carrier.name_for_number(parsed, "en"),
                "timezones": list(phone_timezone.time_zones_for_number(parsed)),
            }
        # Keep this to public web-search leads; do not query private-data brokers.
        queries = [f'"{value}"', f'"{compact}"']
        links = self.search_links(queries, add_entities=False)
        self._attach_search_leads(eid, links)
        dorks = self.dorks(value, "phone", attach_to=eid)
        self.db.add_evidence(self.case_id, eid, "phone_public_search_pack", metadata={"queries": queries, "links": links, "phone_info": phone_info})
        return {
            "phone": value,
            "normalized": compact,
            "phone_info": phone_info,
            "search_links": links,
            "dorks": dorks,
            "note": "Public-search leads only. A phone-number match does not establish identity or current ownership.",
        }

    def local_file(self, filename: str) -> dict[str, Any]:
        path = Path(filename).expanduser().resolve()
        if not path.is_file():
            raise ValueError(f"File not found: {path}")
        stat = path.stat()
        digest = sha256_file(path)
        fid = self._entity("file", str(path), label=path.name, confidence=1.0, source="local")
        hid = self._entity("hash", "sha256:" + digest, confidence=1.0, source="local")
        self.db.add_relation(self.case_id, fid, hid, "has_hash", confidence=1.0, source="SHA-256")

        metadata = {
            "path": str(path),
            "name": path.name,
            "suffix": path.suffix.lower(),
            "size": stat.st_size,
            "modified_utc": dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc).isoformat(),
            "sha256": digest,
        }

        # EXIF reader is bootstrapped locally; if unavailable, hashing still works.
        with contextlib.suppress(Exception):
            import exifread  # type: ignore
            with path.open("rb") as fh:
                tags = exifread.process_file(fh, details=False)
            if tags:
                metadata["exif"] = {str(k): str(v)[:1000] for k, v in tags.items()}

        # PDF document metadata (optional local dependency).
        if path.suffix.lower() == ".pdf":
            with contextlib.suppress(Exception):
                from pypdf import PdfReader  # type: ignore
                reader = PdfReader(str(path))
                pdf_meta = {}
                if reader.metadata:
                    pdf_meta = {str(k): str(v)[:2000] for k, v in reader.metadata.items() if v is not None}
                metadata["pdf"] = {"pages": len(reader.pages), "metadata": pdf_meta}

        # Office Open XML core properties are plain XML inside the ZIP; no extra package needed.
        if path.suffix.lower() in {".docx", ".xlsx", ".pptx"}:
            with contextlib.suppress(Exception):
                with zipfile.ZipFile(path, "r") as zf:
                    raw = zf.read("docProps/core.xml")
                root_xml = ET.fromstring(raw)
                core = {}
                for elem in root_xml.iter():
                    tag = elem.tag.split("}")[-1]
                    if elem.text and elem.text.strip():
                        core[tag] = elem.text.strip()[:2000]
                metadata["office_core_properties"] = core

        self.db.add_evidence(
            self.case_id, fid, "local_file_metadata",
            metadata=metadata
        )
        return metadata

    def search_links(
        self,
        queries: Iterable[str],
        *,
        add_entities: bool = True,
    ) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        for query in queries:
            query = query.strip()
            if not query:
                continue
            for engine, template in SEARCH_ENGINES.items():
                url = template.format(q=urllib.parse.quote_plus(query))
                out.append({"engine": engine, "query": query, "url": url})
                if add_entities:
                    qid = self._entity("note", f"search:{query}", label="Search query", confidence=1.0, source="user")
                    uid = self._entity("url", url, label=engine, confidence=1.0, source="generated search link")
                    self.db.add_relation(
                        self.case_id, qid, uid, "search_with",
                        confidence=1.0, source="generated"
                    )
        return out

    def deep(self, target: str) -> dict[str, Any]:
        """Easy Mode: classify one target and run the safest useful investigation automatically."""
        target = target.strip()
        if not target:
            raise ValueError("Empty target.")
        typ = detect_target_type(target)
        clean_target = strip_explicit_target_prefix(target)
        if typ == "file":
            result = self.local_file(clean_target)
        elif typ == "url":
            result = self.url(clean_target)
        elif typ == "ip":
            result = self.ip(clean_target)
        elif typ == "email":
            result = self.email(clean_target)
        elif typ == "fediverse":
            result = self.fediverse(clean_target)
        elif typ == "phone":
            result = self.phone(clean_target)
        elif typ == "domain":
            result = self.domain(clean_domain(clean_target), deep=True)
        elif typ == "person":
            result = self.person(clean_target)
        elif typ == "organization":
            result = self.organization(clean_target)
        elif typ == "doi":
            result = self.doi(clean_target)
        elif typ == "asn":
            result = self.asn(clean_target)
        elif typ == "prefix":
            result = self.prefix(clean_target)
        elif typ == "hash":
            result = self.hash_value(clean_target)
        elif typ == "username":
            result = self.username(clean_target)
        else:
            raise ValueError("Could not identify target type.")
        return {"type": typ, "target": target, "result": result}


# ---------------------------------------------------------------------------
# Adaptive investigation / reasoning layer
# ---------------------------------------------------------------------------

MODE_POLICIES = {
    "passive": {"max_pivots": 0, "max_depth": 0, "min_confidence": 0.80, "max_urls": 0},
    "normal": {"max_pivots": 6, "max_depth": 1, "min_confidence": 0.70, "max_urls": 2},
    "deep": {"max_pivots": 16, "max_depth": 2, "min_confidence": 0.62, "max_urls": 5},
}


def choose_investigation_mode(target: str, requested: str = "auto") -> str:
    requested = (requested or "auto").lower()
    if requested in MODE_POLICIES:
        return requested
    typ = detect_target_type(target)
    # Ambiguous human-identity targets remain conservative unless the operator
    # explicitly selects a deeper mode. Structured technical targets benefit
    # from a bounded normal pivot pass.
    if typ in {"person", "phone", "organization", "file"}:
        return "passive"
    return "normal"


def _entity_family_count(entity: dict[str, Any]) -> int:
    return len(entity_source_families(str(entity.get("source") or "")))


def _entity_degree(data: dict[str, Any]) -> dict[int, int]:
    degree = {int(e["id"]): 0 for e in data.get("entities", [])}
    for r in data.get("relations", []):
        a, b = int(r["src_entity_id"]), int(r["dst_entity_id"])
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1
    return degree


def case_graph_intelligence(db: CaseDB, case_id: int) -> dict[str, Any]:
    data = db.case_data(case_id)
    entities = {int(e["id"]): e for e in data["entities"]}
    adjacency: dict[int, set[int]] = {eid: set() for eid in entities}
    for r in data["relations"]:
        a, b = int(r["src_entity_id"]), int(r["dst_entity_id"])
        adjacency.setdefault(a, set()).add(b)
        adjacency.setdefault(b, set()).add(a)
    degree = {eid: len(v) for eid, v in adjacency.items()}
    central = sorted(
        ({"id": eid, "type": entities[eid]["type"], "value": entities[eid]["value"],
          "degree": degree[eid], "confidence": entities[eid]["confidence"]} for eid in entities),
        key=lambda x: (-x["degree"], -float(x["confidence"])),
    )[:20]
    seen: set[int] = set()
    components: list[list[int]] = []
    for start in entities:
        if start in seen:
            continue
        stack=[start]; comp=[]; seen.add(start)
        while stack:
            cur=stack.pop(); comp.append(cur)
            for nxt in adjacency.get(cur, set()):
                if nxt not in seen:
                    seen.add(nxt); stack.append(nxt)
        components.append(comp)
    components.sort(key=len, reverse=True)
    shared = []
    for eid, neighbors in adjacency.items():
        e=entities[eid]
        if len(neighbors) >= 2 and e["type"] in {"ip","domain","email","identifier","hash","asn","organization","technology"}:
            shared.append({"id":eid,"type":e["type"],"value":e["value"],"connections":len(neighbors),
                           "warning":"Shared infrastructure or identifiers are correlation leads, not proof of common ownership."})
    shared.sort(key=lambda x:-x["connections"])
    return {"central_entities":central,"components":[{"size":len(c),"entity_ids":c[:100]} for c in components[:20]],
            "shared_indicators":shared[:30]}


def case_contradictions(db: CaseDB, case_id: int) -> list[dict[str, Any]]:
    data=db.case_data(case_id)
    entities={int(e["id"]):e for e in data["entities"]}
    by_subject: dict[int, dict[str, list[dict[str, Any]]]] = {}
    for r in data["relations"]:
        rel=str(r["relation"])
        if rel not in {"public_name"}:
            continue
        by_subject.setdefault(int(r["src_entity_id"]),{}).setdefault(rel,[]).append(r)
    out=[]
    for sid, groups in by_subject.items():
        for rel, rows in groups.items():
            vals=[]
            for row in rows:
                dst=entities.get(int(row["dst_entity_id"]))
                if dst and dst["value"] not in vals: vals.append(dst["value"])
            if len(vals)>1:
                out.append({"entity_id":sid,"entity":entities.get(sid,{}).get("value"),"relation":rel,
                            "values":vals,"severity":"review","note":"Multiple public observations disagree; this may be a rename, stale data, or a different identity."})
    return out


def investigation_quality(db: CaseDB, case_id: int) -> dict[str, Any]:
    d=db.case_data(case_id)
    families=set()
    corroborated=0
    for e in d["entities"]:
        f=entity_source_families(str(e.get("source") or "")); families |= f
        if len(f)>=2: corroborated += 1
    assessment_count=len(d.get("assessments",[]))
    contradictions=len(case_contradictions(db,case_id))
    evidence=len(d["evidence"])
    # Quality describes the investigation, never the target.
    score=0
    score += min(25, len(families)*4)
    score += min(25, corroborated*3)
    score += min(20, int(math.log2(evidence+1)*4)) if evidence else 0
    score += min(20, assessment_count*4)
    score += 10 if evidence and all(e.get("sha256") for e in d["evidence"]) else 0
    score -= min(15, contradictions*5)
    score=max(0,min(100,score))
    label="early" if score<35 else "developing" if score<60 else "solid" if score<80 else "well-supported"
    return {"score":score,"label":label,"source_families":sorted(families),"corroborated_entities":corroborated,
            "evidence_records":evidence,"human_assessments":assessment_count,"unresolved_contradictions":contradictions,
            "note":"This measures investigation completeness/support, not suspicion, criminality, or risk."}


def explain_entity(db: CaseDB, case_id: int, entity_id: int) -> dict[str, Any]:
    d=db.case_data(case_id); entities={int(e["id"]):e for e in d["entities"]}
    e=entities.get(int(entity_id))
    if not e: raise ValueError(f"Entity #{entity_id} not found in this case.")
    incoming=[]; outgoing=[]
    for r in d["relations"]:
        if int(r["src_entity_id"])==entity_id:
            dst=entities.get(int(r["dst_entity_id"]),{})
            outgoing.append({"relation":r["relation"],"to_id":r["dst_entity_id"],"to":dst.get("value"),"confidence":r["confidence"],"source":r["source"]})
        if int(r["dst_entity_id"])==entity_id:
            src=entities.get(int(r["src_entity_id"]),{})
            incoming.append({"relation":r["relation"],"from_id":r["src_entity_id"],"from":src.get("value"),"confidence":r["confidence"],"source":r["source"]})
    evidence=[x for x in d["evidence"] if x.get("entity_id")==entity_id]
    assessments=[x for x in d.get("assessments",[]) if x.get("entity_id")==entity_id]
    families=sorted(entity_source_families(str(e.get("source") or "")))
    why=[]
    if len(families)>=3: why.append("Supported by several independent source families.")
    elif len(families)==1: why.append("Currently depends on only one source family; independent corroboration would materially strengthen it.")
    if len(incoming)+len(outgoing)>=5: why.append("This entity is highly connected and may be an important graph bridge or pivot.")
    if assessments: why.append(f"Latest investigator assessment: {assessments[-1]['status']}.")
    next_steps=[]
    if len(families)<2: next_steps.append("Seek a different source family before treating this as strongly corroborated.")
    if not assessments: next_steps.append("Review this entity manually and record confirmed/rejected/uncertain if important.")
    return {"entity":e,"source_families":families,"evidence_records":len(evidence),"incoming":incoming[:30],"outgoing":outgoing[:30],
            "assessments":assessments,"why_it_matters":why,"recommended_checks":next_steps}


def relationship_path(db: CaseDB, case_id: int, start_id: int, end_id: int) -> list[dict[str, Any]]:
    d=db.case_data(case_id); ents={int(e["id"]):e for e in d["entities"]}
    if start_id not in ents or end_id not in ents: raise ValueError("Both entity IDs must exist in the selected case.")
    adj: dict[int,list[tuple[int,dict[str,Any]]]]={i:[] for i in ents}
    for r in d["relations"]:
        a,b=int(r["src_entity_id"]),int(r["dst_entity_id"])
        adj.setdefault(a,[]).append((b,r)); adj.setdefault(b,[]).append((a,r))
    queue=[start_id]; prev={start_id:(None,None)}
    for cur in queue:
        if cur==end_id: break
        for nxt,rel in adj.get(cur,[]):
            if nxt not in prev:
                prev[nxt]=(cur,rel); queue.append(nxt)
    if end_id not in prev: return []
    ids=[]; cur=end_id
    while cur is not None:
        ids.append(cur); cur=prev[cur][0]
    ids.reverse(); out=[]
    for i,eid in enumerate(ids):
        row={"entity_id":eid,"type":ents[eid]["type"],"value":ents[eid]["value"]}
        if i<len(ids)-1:
            rel=prev[ids[i+1]][1]; row["relation_to_next"]=rel["relation"]; row["relation_source"]=rel["source"]
        out.append(row)
    return out


def ranked_questions(db: CaseDB, case_id: int, limit: int = 8) -> list[dict[str, Any]]:
    d=db.case_data(case_id); degree=_entity_degree(d); out=[]
    assessments={int(x["entity_id"]):x for x in d.get("assessments",[])}
    for e in d["entities"]:
        eid=int(e["id"]); fams=entity_source_families(str(e.get("source") or ""))
        if e["type"] in {"note","other"}: continue
        if len(fams)<2 and float(e["confidence"])>=0.55:
            priority=55 + min(20,degree.get(eid,0)*3) + (10 if eid not in assessments else 0)
            out.append({"priority":priority,"entity_id":eid,
                        "question":f"Can {e['type']} {e['value']} be corroborated by a different source family?",
                        "why":f"It currently has {len(fams)} independent source family/families and degree {degree.get(eid,0)}."})
        if degree.get(eid,0)>=5 and eid not in assessments:
            out.append({"priority":70+min(15,degree[eid]),"entity_id":eid,
                        "question":f"Has central entity #{eid} ({e['value']}) been manually reviewed?",
                        "why":"Highly connected entities can influence many downstream conclusions."})
    for c in case_contradictions(db,case_id):
        out.append({"priority":100,"entity_id":c["entity_id"],"question":f"Which conflicting {c['relation']} observation is best supported?","why":str(c["values"])})
    # deduplicate by entity + question stem
    seen=set(); unique=[]
    for q in sorted(out,key=lambda x:-x["priority"]):
        key=(q.get("entity_id"),q["question"])
        if key not in seen: seen.add(key); unique.append(q)
    return unique[:limit]


def focus_summary(db: CaseDB, case_id: int) -> dict[str, Any]:
    d=db.case_data(case_id); quality=investigation_quality(db,case_id); graph=case_graph_intelligence(db,case_id)
    strongest=[]
    for e in sorted(d["entities"],key=lambda x:(-_entity_family_count(x),-float(x["confidence"])))[:10]:
        if e["type"] in {"note","other"}: continue
        strongest.append({"id":e["id"],"type":e["type"],"value":e["value"],"confidence":e["confidence"],
                          "source_families":sorted(entity_source_families(str(e.get("source") or "")))})
    return {"case":d["case"]["name"],"quality":quality,"entities":len(d["entities"]),"relations":len(d["relations"]),
            "evidence":len(d["evidence"]),"contradictions":case_contradictions(db,case_id),"strongest":strongest,
            "central_entities":graph["central_entities"][:5],"questions":ranked_questions(db,case_id,5)}


def compare_entities(db: CaseDB, case_id: int, left_id: int, right_id: int) -> dict[str, Any]:
    d=db.case_data(case_id); ents={int(e["id"]):e for e in d["entities"]}
    if left_id not in ents or right_id not in ents: raise ValueError("Both entity IDs must exist in the selected case.")
    neigh: dict[int,dict[int,list[str]]]={left_id:{},right_id:{}}
    direct=[]
    for r in d["relations"]:
        a,b=int(r["src_entity_id"]),int(r["dst_entity_id"])
        if {a,b}=={left_id,right_id}: direct.append({"relation":r["relation"],"confidence":r["confidence"],"source":r["source"]})
        for subject,other in ((a,b),(b,a)):
            if subject in neigh: neigh[subject].setdefault(other,[]).append(str(r["relation"]))
    shared_ids=set(neigh[left_id]) & set(neigh[right_id]); weights={"email":3.0,"identifier":3.0,"hash":3.0,"domain":2.2,"url":2.0,"organization":2.0,"fediverse":2.0,"username":1.8,"ip":0.9,"asn":0.5,"technology":0.4,"service":0.4}
    shared=[]; total=0.0
    for eid in shared_ids:
        e=ents.get(eid,{}); w=weights.get(str(e.get("type")),0.6); total+=w
        shared.append({"id":eid,"type":e.get("type"),"value":e.get("value"),"weight":w,
                       "left_relations":neigh[left_id][eid],"right_relations":neigh[right_id][eid]})
    if direct: total += 2.0
    score=min(1.0,total/6.0); classification="likely-related" if score>=0.75 else "possible" if score>=0.35 else "insufficient"
    return {"left":ents[left_id],"right":ents[right_id],"classification":classification,"score":round(score,3),
            "direct_relationships":direct,"shared_indicators":sorted(shared,key=lambda x:-x["weight"]),
            "caution":"Correlation does not establish that two accounts, people, domains, or organizations are the same entity or share ownership."}


def correlation_clusters(db: CaseDB, case_id: int, limit: int = 25) -> list[dict[str, Any]]:
    d=db.case_data(case_id); ents={int(e["id"]):e for e in d["entities"]}
    candidates=[int(e["id"]) for e in d["entities"] if e["type"] in {"domain","url","organization"}][:120]
    adj={eid:set() for eid in candidates}
    for r in d["relations"]:
        a,b=int(r["src_entity_id"]),int(r["dst_entity_id"])
        if a in adj: adj[a].add(b)
        if b in adj: adj[b].add(a)
    weights={"email":3.0,"identifier":3.0,"hash":3.0,"fediverse":2.5,"domain":2.0,"url":1.8,"organization":2.0,"ip":0.8,"asn":0.4,"technology":0.3,"service":0.3}
    out=[]
    for i,a in enumerate(candidates):
        for b in candidates[i+1:]:
            shared=adj[a]&adj[b]
            indicators=[]; total=0.0
            for x in shared:
                e=ents.get(x,{}); w=weights.get(str(e.get("type")),0.0)
                if w>0:
                    total+=w; indicators.append({"id":x,"type":e.get("type"),"value":e.get("value"),"weight":w})
            if total>=1.0:
                out.append({"left_id":a,"left":ents[a]["value"],"right_id":b,"right":ents[b]["value"],
                            "score":round(min(1.0,total/5.0),3),"shared":sorted(indicators,key=lambda x:-x["weight"])})
    return sorted(out,key=lambda x:-x["score"])[:limit]


def cross_case_correlations(db: CaseDB, case_id: int, limit: int = 100) -> list[dict[str, Any]]:
    supported={"domain","ip","email","username","url","hash","identifier","asn","prefix","organization","fediverse"}
    rows=db.conn.execute("SELECT id,name FROM cases WHERE id<>? ORDER BY id DESC",(case_id,)).fetchall(); out=[]
    current=db.conn.execute("SELECT id,type,value,confidence FROM entities WHERE case_id=?",(case_id,)).fetchall()
    for e in current:
        if e["type"] not in supported: continue
        matches=db.conn.execute("""SELECT e.id,e.case_id,e.confidence,c.name FROM entities e JOIN cases c ON c.id=e.case_id
                                  WHERE e.case_id<>? AND e.type=? AND e.value=? ORDER BY e.confidence DESC LIMIT 20""",
                                (case_id,e["type"],e["value"])).fetchall()
        for m in matches:
            out.append({"type":e["type"],"value":e["value"],"current_entity_id":e["id"],"other_case_id":m["case_id"],
                        "other_case":m["name"],"other_entity_id":m["id"],"confidence":min(float(e["confidence"]),float(m["confidence"])),
                        "caution":"Same public indicator across cases is a correlation lead, not automatic proof of a shared actor."})
            if len(out)>=limit: return out
    return out


def evidence_integrity_audit(db: CaseDB, case_id: int) -> dict[str, Any]:
    rows=db.conn.execute("SELECT id,sha256,metadata_json,body FROM evidence WHERE case_id=? ORDER BY id",(case_id,)).fetchall()
    checks=[]; chain=hashlib.sha256()
    for r in rows:
        if r["body"] is not None and len(r["body"])>0: actual=sha256_bytes(bytes(r["body"]))
        else:
            try: actual=sha256_bytes(pretty_json(json.loads(r["metadata_json"] or "{}")).encode())
            except Exception: actual="unverifiable"
        ok=actual==r["sha256"]; checks.append({"evidence_id":r["id"],"stored":r["sha256"],"actual":actual,"valid":ok})
        chain.update(f"{r['id']}:{r['sha256']}\n".encode())
    quick=db.conn.execute("PRAGMA quick_check").fetchone()[0]
    return {"sqlite_quick_check":quick,"evidence_total":len(checks),"valid":sum(1 for x in checks if x["valid"]),
            "invalid":sum(1 for x in checks if not x["valid"]),"evidence_chain_sha256":chain.hexdigest(),"checks":checks}


def export_stix21(db: CaseDB, case_id: int, path: Path) -> Path:
    d=db.case_data(case_id); objects=[]
    for e in d["entities"]:
        typ=str(e["type"]); value=str(e["value"]); stix_type=""; props={}
        if typ=="domain": stix_type="domain-name"; props={"value":value}
        elif typ=="ip":
            try: stix_type="ipv6-addr" if ipaddress.ip_address(value).version==6 else "ipv4-addr"; props={"value":value}
            except ValueError: continue
        elif typ=="url": stix_type="url"; props={"value":value}
        elif typ=="email": stix_type="email-addr"; props={"value":value}
        elif typ=="hash" and re.fullmatch(r"(?i)(?:sha256:)?[a-f0-9]{64}",value):
            h=value.split(":",1)[-1].lower(); stix_type="file"; props={"hashes":{"SHA-256":h}}
        else: continue
        sid=f"{stix_type}--{uuid.uuid5(uuid.NAMESPACE_URL, stix_type+':'+value)}"
        obj={"type":stix_type,"spec_version":"2.1","id":sid,**props}; objects.append(obj)
    bundle={"type":"bundle","id":f"bundle--{uuid.uuid4()}","objects":objects}
    path.write_text(json.dumps(bundle,indent=2,ensure_ascii=False),encoding="utf-8"); return path

class InvestigationBrain:
    """Bounded event-driven planner for public-source technical pivots."""
    TYPE_WEIGHT={"domain":1.0,"email":0.95,"ip":0.92,"asn":0.82,"prefix":0.82,"fediverse":0.72,"url":0.62,"username":0.58}

    def __init__(self, db: CaseDB, case_id: int, timeout: int = DEFAULT_TIMEOUT):
        self.db=db; self.case_id=case_id; self.det=DigitalFootprintFinder(db,case_id,timeout=timeout)

    def _eligible(self, e: dict[str,Any], seed_type: str, seed_host: str, policy: dict[str,Any], url_count: int) -> bool:
        typ=str(e["type"]); conf=float(e["confidence"]); source=str(e.get("source") or "")
        if typ not in self.TYPE_WEIGHT or conf < float(policy["min_confidence"]): return False
        fams=entity_source_families(source)
        if fams and fams.issubset({"heuristics","search_leads","unknown"}): return False
        if typ=="username" and seed_type!="username": return False
        if typ=="fediverse" and seed_type not in {"fediverse","username"}: return False
        if typ=="url":
            if url_count>=int(policy["max_urls"]): return False
            if seed_host:
                with contextlib.suppress(Exception):
                    h=urllib.parse.urlsplit(normalize_url(str(e["value"]))).hostname or ""
                    if not (h==seed_host or h.endswith("."+seed_host)): return False
        return True

    def _score(self, e: dict[str,Any], degree: dict[int,int]) -> float:
        typ=str(e["type"]); fams=_entity_family_count(e); conf=float(e["confidence"])
        # Information gain is higher for useful, under-corroborated entities.
        uncertainty_bonus=max(0.0,1.0-min(1.0,fams/3.0))*0.45
        graph_bonus=min(0.35, degree.get(int(e["id"]),0)*0.035)
        return self.TYPE_WEIGHT.get(typ,0.0)*0.8 + conf*0.55 + uncertainty_bonus + graph_bonus

    def _dispatch(self, e: dict[str,Any], mode: str) -> Any:
        typ=str(e["type"]); v=str(e["value"])
        if typ=="domain": return self.det.domain(v,deep=(mode=="deep"))
        if typ=="ip": return self.det.ip(v)
        if typ=="email": return self.det.email(v)
        if typ=="asn": return self.det.asn(v)
        if typ=="prefix": return self.det.prefix(v)
        if typ=="fediverse": return self.det.fediverse(v)
        if typ=="username": return self.det.username(v,workers=min(6,int(load_settings().get("username_workers",8))))
        if typ=="url": return self.det.url(v,shallow=(mode!="deep"))
        return None

    def run(self, target: str, requested_mode: str = "auto") -> dict[str,Any]:
        mode=choose_investigation_mode(target,requested_mode); policy=MODE_POLICIES[mode]
        run_id=self.db.begin_run(self.case_id,mode,target)
        initial_before=len(self.db.case_data(self.case_id)["entities"])
        payload=self.det.deep(target)
        seed_type=payload["type"]
        clean=strip_explicit_target_prefix(target)
        seed_host=""
        if seed_type=="domain": seed_host=clean_domain(clean)
        elif seed_type=="url":
            with contextlib.suppress(Exception): seed_host=urllib.parse.urlsplit(normalize_url(clean)).hostname or ""
        root_event=self.db.add_event(self.case_id,"initial_target",depth=0,status="completed",source="user",metadata={"target":target,"type":seed_type,"mode":mode})
        processed={(seed_type, clean.lower())}; pivot_count=0; url_count=0; gains=[]; stop_reason="policy budget reached"
        while pivot_count<int(policy["max_pivots"]):
            d=self.db.case_data(self.case_id); degree=_entity_degree(d); heap=[]
            for e in d["entities"]:
                key=(str(e["type"]),str(e["value"]).lower())
                if key in processed: continue
                if not self._eligible(e,seed_type,seed_host,policy,url_count): continue
                heapq.heappush(heap,(-self._score(e,degree),int(e["id"]),e))
            if not heap:
                stop_reason="no eligible high-value pivots"; break
            negscore,eid,e=heapq.heappop(heap); processed.add((str(e["type"]),str(e["value"]).lower()))
            before=len(d["entities"])
            event_id=self.db.add_event(self.case_id,"automatic_pivot",entity_id=eid,parent_event_id=root_event,depth=1,
                                       status="running",source="Investigation Brain",metadata={"score":round(-negscore,3),"mode":mode})
            try:
                self._dispatch(e,mode)
                after=len(self.db.case_data(self.case_id)["entities"]); gain=max(0,after-before); gains.append(gain)
                self.db.conn.execute("UPDATE events SET status=?,metadata_json=? WHERE id=?",
                                     ("completed",json.dumps({"score":round(-negscore,3),"new_entities":gain},ensure_ascii=False),event_id)); self.db.conn.commit()
            except Exception as exc:
                gains.append(0)
                self.db.conn.execute("UPDATE events SET status=?,metadata_json=? WHERE id=?",
                                     ("failed",json.dumps({"error":str(exc)},ensure_ascii=False),event_id)); self.db.conn.commit()
            pivot_count += 1
            if str(e["type"])=="url": url_count += 1
            if len(gains)>=3 and sum(gains[-3:])/3.0 < 1.0:
                stop_reason="diminishing information gain"; break
        final_count=len(self.db.case_data(self.case_id)["entities"])
        stats={"mode":mode,"pivots":pivot_count,"new_entities":max(0,final_count-initial_before),"stopping_reason":stop_reason,
               "average_recent_gain":round(sum(gains[-3:])/max(1,len(gains[-3:])),2) if gains else 0.0}
        self.db.finish_run(run_id,stats)
        payload["investigation_brain"]=stats
        return payload

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

def export_json(db: CaseDB, case_id: int, path: Path) -> Path:
    data = db.case_data(case_id)
    path.write_text(pretty_json(data), encoding="utf-8")
    return path


def export_markdown(db: CaseDB, case_id: int, path: Path) -> Path:
    d = db.case_data(case_id)
    c = d["case"]
    entities_by_id = {e["id"]: e for e in d["entities"]}

    lines = [
        f"# Digital Footprint Finder Case Report — {c['name']}",
        "",
        f"- **Created:** {c['created_at']}",
        f"- **Generated:** {utcnow()}",
        f"- **Entities:** {len(d['entities'])}",
        f"- **Relations:** {len(d['relations'])}",
        f"- **Evidence records:** {len(d['evidence'])}",
        "",
    ]
    if c["description"]:
        lines += ["## Description", "", c["description"], ""]

    lines += ["## Entities", ""]
    for e in d["entities"]:
        label = f" — {e['label']}" if e["label"] else ""
        lines.append(
            f"- `#{e['id']}` **{e['type']}**: {e['value']}{label} "
            f"(confidence {e['confidence']:.2f}; source: {e['source'] or 'unspecified'})"
        )

    lines += ["", "## Relationships", ""]
    for r in d["relations"]:
        src = entities_by_id.get(r["src_entity_id"], {})
        dst = entities_by_id.get(r["dst_entity_id"], {})
        lines.append(
            f"- `#{r['src_entity_id']}` {src.get('value','?')} "
            f"— **{r['relation']}** → "
            f"`#{r['dst_entity_id']}` {dst.get('value','?')} "
            f"(confidence {r['confidence']:.2f})"
        )

    lines += ["", "## Evidence", ""]
    for e in d["evidence"]:
        lines.append(
            f"- Evidence `#{e['id']}` — **{e['kind']}**, captured {e['captured_at']}, "
            f"SHA-256 `{e['sha256']}`, bytes {e.get('body_size') or 0}"
        )
        if e["source_url"]:
            lines.append(f"  - Source: {e['source_url']}")

    if d["notes"]:
        lines += ["", "## Notes", ""]
        for n in d["notes"]:
            lines.append(f"- {n['created_at']}: {n['text']}")

    lines += [
        "",
        "## Verification note",
        "",
        "OSINT findings are leads, not automatic proof of identity, ownership, intent, or wrongdoing. "
        "Corroborate important claims with independent sources and preserve provenance.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def export_graphml(db: CaseDB, case_id: int, path: Path) -> Path:
    d = db.case_data(case_id)
    def x(v: Any) -> str:
        return html.escape(str(v), quote=True)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '<key id="type" for="node" attr.name="type" attr.type="string"/>',
        '<key id="value" for="node" attr.name="value" attr.type="string"/>',
        '<key id="confidence" for="all" attr.name="confidence" attr.type="double"/>',
        '<key id="relation" for="edge" attr.name="relation" attr.type="string"/>',
        '<graph id="G" edgedefault="directed">',
    ]
    for e in d["entities"]:
        lines += [
            f'<node id="n{e["id"]}">',
            f'<data key="type">{x(e["type"])}</data>',
            f'<data key="value">{x(e["value"])}</data>',
            f'<data key="confidence">{e["confidence"]}</data>',
            '</node>',
        ]
    for r in d["relations"]:
        lines += [
            f'<edge id="e{r["id"]}" source="n{r["src_entity_id"]}" target="n{r["dst_entity_id"]}">',
            f'<data key="relation">{x(r["relation"])}</data>',
            f'<data key="confidence">{r["confidence"]}</data>',
            '</edge>',
        ]
    lines += ["</graph>", "</graphml>"]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path



def _parse_wayback_timestamp(value: str) -> Optional[str]:
    value = str(value or "").strip()
    if re.fullmatch(r"\d{14}", value):
        with contextlib.suppress(Exception):
            return dt.datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc).isoformat()
    return None


def case_timeline(db: CaseDB, case_id: int, limit: int = 250) -> list[dict[str, Any]]:
    """Build a compact timeline from captured evidence and public metadata dates."""
    data = db.case_data(case_id)
    events: list[dict[str, Any]] = []
    for e in data["evidence"]:
        events.append({"time": e.get("captured_at"), "kind": "captured", "label": e.get("kind"), "source": e.get("source_url", "")})
        meta = e.get("metadata") or {}
        # RDAP events
        response = meta.get("response") if isinstance(meta, dict) else None
        if isinstance(response, dict):
            for row in response.get("events", []) or []:
                if isinstance(row, dict) and row.get("eventDate"):
                    events.append({"time": row.get("eventDate"), "kind": "rdap", "label": row.get("eventAction") or "RDAP event", "source": e.get("source_url", "")})
        # Wayback captures
        captures = meta.get("captures") if isinstance(meta, dict) else None
        if isinstance(captures, list):
            for row in captures[:100]:
                if isinstance(row, dict):
                    ts = _parse_wayback_timestamp(str(row.get("timestamp") or ""))
                    if ts:
                        events.append({"time": ts, "kind": "archive", "label": truncate(str(row.get("original") or "Wayback capture"), 120), "source": e.get("source_url", "")})
        # Common Crawl rows
        rows = meta.get("rows") if isinstance(meta, dict) else None
        if isinstance(rows, list):
            for row in rows[:100]:
                if isinstance(row, dict):
                    ts = _parse_wayback_timestamp(str(row.get("timestamp") or ""))
                    if ts:
                        events.append({"time": ts, "kind": "web_index", "label": truncate(str(row.get("url") or "Common Crawl record"), 120), "source": e.get("source_url", "")})
        # Common metadata date fields
        def walk(obj: Any, prefix: str = "") -> None:
            if isinstance(obj, dict):
                for k, v in list(obj.items())[:120]:
                    key = str(k).lower()
                    path = f"{prefix}.{k}" if prefix else str(k)
                    if key in {"created_at", "updated_at", "modified_utc", "not_before", "not_after", "registration_date", "last_profile_edit", "date-time"} and isinstance(v, str):
                        events.append({"time": v, "kind": "metadata", "label": path, "source": e.get("source_url", "")})
                    elif isinstance(v, (dict, list)) and len(events) < 1000:
                        walk(v, path)
            elif isinstance(obj, list):
                for i, v in enumerate(obj[:60]):
                    if isinstance(v, (dict, list)):
                        walk(v, f"{prefix}[{i}]")
        if isinstance(meta, dict):
            walk(meta)
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for event in events:
        raw = str(event.get("time") or "").strip()
        if not raw:
            continue
        # Keep parseable ISO-ish values only.
        parsed = None
        with contextlib.suppress(Exception):
            parsed = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed is None:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        iso = parsed.astimezone(dt.timezone.utc).isoformat()
        key = (iso, str(event.get("kind")), str(event.get("label")))
        if key in seen:
            continue
        seen.add(key)
        normalized.append({**event, "time": iso})
    normalized.sort(key=lambda x: x["time"])
    return normalized[-max(1, min(limit, 1000)):]


def case_source_coverage(db: CaseDB, case_id: int) -> dict[str, Any]:
    data = db.case_data(case_id)
    counts: dict[str, int] = {}
    for e in data["entities"]:
        for source in _source_parts(e.get("source", "")):
            counts[source] = counts.get(source, 0) + 1
    evidence_kinds: dict[str, int] = {}
    for ev in data["evidence"]:
        kind = str(ev.get("kind") or "unknown")
        evidence_kinds[kind] = evidence_kinds.get(kind, 0) + 1
    return {
        "independent_sources": len(counts),
        "sources": dict(sorted(counts.items(), key=lambda x: (-x[1], x[0]))),
        "evidence_kinds": dict(sorted(evidence_kinds.items(), key=lambda x: (-x[1], x[0]))),
    }


def smart_case_analysis(db: CaseDB, case_id: int) -> dict[str, Any]:
    """Summarize corroboration and prioritize useful next pivots without claiming identity."""
    data = db.case_data(case_id)
    corroborated: list[dict[str, Any]] = []
    strongest: list[dict[str, Any]] = []
    type_counts: dict[str, int] = {}
    for e in data["entities"]:
        type_counts[e["type"]] = type_counts.get(e["type"], 0) + 1
        sources = _source_parts(e.get("source", ""))
        item = {
            "id": e["id"], "type": e["type"], "value": e["value"],
            "confidence": float(e["confidence"]), "sources": sources,
        }
        if len(sources) >= 2:
            corroborated.append(item)
        if float(e["confidence"]) >= 0.75:
            strongest.append(item)
    corroborated.sort(key=lambda x: (-len(x["sources"]), -x["confidence"], x["type"], x["value"]))
    strongest.sort(key=lambda x: (-x["confidence"], -len(x["sources"]), x["type"], x["value"]))

    next_pivots: list[str] = []
    if type_counts.get("domain"):
        next_pivots.append("Review corroborated hostnames, archived URLs, public documents and linked profiles.")
    if type_counts.get("username") or type_counts.get("social"):
        next_pivots.append("Compare profile bios, linked domains and public repository metadata before joining identities.")
    if type_counts.get("email"):
        next_pivots.append("Compare email-domain context and independent public references; do not infer current ownership from one hit.")
    if type_counts.get("ip"):
        next_pivots.append("Separate current DNS from historical/passive observations and account for shared hosting/CDNs.")
    if type_counts.get("file"):
        next_pivots.append("Verify metadata timestamps and hashes against the original file; metadata can be edited.")
    if type_counts.get("identifier") or type_counts.get("technology"):
        next_pivots.append("Compare repeated public web identifiers, favicon hashes and technology fingerprints across independently observed sites.")
    if type_counts.get("asn") or type_counts.get("prefix"):
        next_pivots.append("Compare routing observations with current DNS/RDAP data; ASN and prefix ownership can change over time.")
    if type_counts.get("publication"):
        next_pivots.append("Use DOI/ORCID and exact author metadata to disambiguate scholarly name matches.")

    coverage = case_source_coverage(db, case_id)
    timeline = case_timeline(db, case_id, limit=80)
    return {
        "entity_types": dict(sorted(type_counts.items(), key=lambda x: (-x[1], x[0]))),
        "corroborated": corroborated[:30],
        "strongest": strongest[:30],
        "next_pivots": next_pivots,
        "source_coverage": coverage,
        "timeline_events": len(timeline),
        "caution": "Corroboration strengthens an observation, not a claim that two records identify the same person.",
    }

def export_html(db: CaseDB, case_id: int, path: Path) -> Path:
    d = db.case_data(case_id)
    c = d["case"]
    analysis = smart_case_analysis(db, case_id)
    focus = focus_summary(db, case_id)
    quality = focus["quality"]
    questions = focus["questions"]
    graph_info = case_graph_intelligence(db, case_id)
    contradictions = focus["contradictions"]
    timeline = case_timeline(db, case_id, limit=120)
    timeline_html = "".join(
        f"<tr><td>{html.escape(str(x.get('time','')))}</td><td>{html.escape(str(x.get('kind','')))}</td>"
        f"<td>{html.escape(truncate(str(x.get('label','')), 150))}</td></tr>"
        for x in timeline
    ) or "<tr><td colspan='3'>No dated public observations yet.</td></tr>"
    corroborated_html = "".join(
        f"<li><strong>{html.escape(str(x['type']))}</strong>: {html.escape(truncate(str(x['value']), 120))} "
        f"— {len(x['sources'])} sources, confidence {x['confidence']:.2f}</li>"
        for x in analysis["corroborated"][:12]
    ) or "<li>No multi-source corroboration yet.</li>"
    pivots_html = "".join(f"<li>{html.escape(x)}</li>" for x in analysis["next_pivots"]) or "<li>Verify the strongest leads manually.</li>"
    questions_html = "".join(
        f"<li><strong>P{int(x.get('priority',0))}</strong> {html.escape(str(x.get('question','')))}<br>"
        f"<span class='small'>{html.escape(str(x.get('why','')))}</span></li>" for x in questions
    ) or "<li>No high-priority unanswered questions were generated.</li>"
    contradictions_html = "".join(
        f"<li>Entity #{x.get('entity_id')}: {html.escape(str(x.get('note','')))}</li>" for x in contradictions
    ) or "<li>No explicit contradictions detected by the current conservative rules.</li>"
    central_html = "".join(
        f"<li>#{x['id']} <strong>{html.escape(str(x['type']))}</strong>: {html.escape(truncate(str(x['value']),100))} — degree {x['degree']}</li>"
        for x in graph_info.get("central_entities",[])[:10]
    ) or "<li>No graph hubs yet.</li>"
    entities = {e["id"]: e for e in d["entities"]}

    def entity_value_html(e: dict[str, Any]) -> str:
        value = str(e["value"])
        if e.get("type") == "url" and value.startswith(("http://", "https://")):
            return f'<a href="{html.escape(value, quote=True)}">{html.escape(truncate(value, 90))}</a>'
        return html.escape(value)

    entity_rows = "\n".join(
        "<tr>"
        f"<td>{e['id']}</td><td>{html.escape(e['type'])}</td>"
        f"<td>{entity_value_html(e)}</td>"
        f"<td>{e['confidence']:.2f}</td>"
        f"<td>{html.escape(e['source'] or '')}</td>"
        "</tr>"
        for e in d["entities"]
    )
    relation_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(entities.get(r['src_entity_id'], {}).get('value', '?'))}</td>"
        f"<td>{html.escape(r['relation'])}</td>"
        f"<td>{html.escape(entities.get(r['dst_entity_id'], {}).get('value', '?'))}</td>"
        f"<td>{r['confidence']:.2f}</td>"
        "</tr>"
        for r in d["relations"]
    )
    evidence_rows = "\n".join(
        "<tr>"
        f"<td>{e['id']}</td><td>{html.escape(e['kind'])}</td>"
        f"<td>{html.escape(e['captured_at'])}</td>"
        f"<td><code>{html.escape(e['sha256'])}</code></td>"
        f"<td>{('<a href=\"' + html.escape(e['source_url'], quote=True) + '\">source</a>') if e['source_url'] else ''}</td>"
        "</tr>"
        for e in d["evidence"]
    )

    # Lightweight SVG-ish graph layout without JS dependencies.
    nodes = d["entities"][:80]
    node_ids = {e["id"] for e in nodes}
    rels = [
        r for r in d["relations"]
        if r["src_entity_id"] in node_ids and r["dst_entity_id"] in node_ids
    ]
    width, height = 1200, max(600, ((len(nodes) + 5) // 6) * 150)
    positions: dict[int, tuple[int, int]] = {}
    for i, e in enumerate(nodes):
        col, row = i % 6, i // 6
        positions[e["id"]] = (110 + col * 195, 85 + row * 145)

    svg_edges = []
    for r in rels:
        x1, y1 = positions[r["src_entity_id"]]
        x2, y2 = positions[r["dst_entity_id"]]
        svg_edges.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            'stroke="currentColor" stroke-opacity=".22" stroke-width="1.5"/>'
        )

    svg_nodes = []
    for e in nodes:
        x0, y0 = positions[e["id"]]
        label = truncate(e["value"], 24)
        svg_nodes.append(
            f'<g><rect x="{x0-80}" y="{y0-28}" width="160" height="56" rx="10" '
            'fill="none" stroke="currentColor" stroke-opacity=".55"/>'
            f'<text x="{x0}" y="{y0-4}" text-anchor="middle" font-size="11">'
            f'{html.escape(e["type"])}</text>'
            f'<text x="{x0}" y="{y0+14}" text-anchor="middle" font-size="10">'
            f'{html.escape(label)}</text></g>'
        )

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Digital Footprint Finder — {html.escape(c['name'])}</title>
<style>
:root {{ color-scheme: dark light; }}
body {{ font-family: system-ui, sans-serif; margin: 0; padding: 24px; max-width: 1400px; margin-inline:auto; }}
header {{ border-bottom: 1px solid #7775; margin-bottom: 24px; }}
.card {{ border:1px solid #7775; border-radius:14px; padding:16px; margin:16px 0; overflow:auto; }}
table {{ border-collapse:collapse; width:100%; font-size:14px; }}
th,td {{ border-bottom:1px solid #7774; padding:8px; text-align:left; vertical-align:top; }}
code {{ word-break:break-all; }}
.small {{ opacity:.75; }}
svg {{ width:100%; min-width:900px; height:auto; }}
</style>
</head>
<body>
<header>
<h1>Digital Footprint Finder Case Report</h1>
<h2>{html.escape(c['name'])}</h2>
<p>{html.escape(c['description'])}</p>
<p class="small">Generated {utcnow()} · {len(d['entities'])} entities ·
{len(d['relations'])} relations · {len(d['evidence'])} evidence records</p>
</header>

<section class="card">
<h2>Smart Analysis</h2>
<p class="small">Digital Footprint Finder merges duplicate entities and raises confidence only when independent public observations agree.</p>
<h3>Corroborated observations</h3><ul>{corroborated_html}</ul>
<h3>Recommended next pivots</h3><ul>{pivots_html}</ul>
<p class="small">{html.escape(analysis['caution'])}</p>
</section>

<section class="card">
<h2>Investigator Focus</h2>
<p><strong>Investigation quality:</strong> {quality['score']}/100 — {html.escape(str(quality['label']))}</p>
<p class="small">{html.escape(str(quality['note']))}</p>
<h3>Ranked unanswered questions</h3><ol>{questions_html}</ol>
<h3>Potential contradictions</h3><ul>{contradictions_html}</ul>
<h3>Central graph entities</h3><ul>{central_html}</ul>
</section>

<section class="card">
<h2>Investigation Timeline</h2>
<p class="small">Dates are extracted from captured public metadata and archive indexes. They may describe different events and should be interpreted in context.</p>
<table><thead><tr><th>UTC time</th><th>Kind</th><th>Observation</th></tr></thead><tbody>{timeline_html}</tbody></table>
</section>

<section class="card">
<h2>Relationship Map</h2>
<p class="small">Showing up to 80 entities. Lines indicate recorded relations.</p>
<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
{''.join(svg_edges)}
{''.join(svg_nodes)}
</svg>
</section>

<section class="card"><h2>Entities</h2>
<table><thead><tr><th>ID</th><th>Type</th><th>Value</th><th>Confidence</th><th>Source</th></tr></thead>
<tbody>{entity_rows}</tbody></table></section>

<section class="card"><h2>Relationships</h2>
<table><thead><tr><th>From</th><th>Relation</th><th>To</th><th>Confidence</th></tr></thead>
<tbody>{relation_rows}</tbody></table></section>

<section class="card"><h2>Evidence Chain</h2>
<table><thead><tr><th>ID</th><th>Kind</th><th>Captured</th><th>SHA-256</th><th>Source</th></tr></thead>
<tbody>{evidence_rows}</tbody></table></section>

<section class="card"><h2>Verification Note</h2>
<p>OSINT findings are leads, not automatic proof of identity, ownership, intent, or wrongdoing.
Corroborate important claims independently and preserve provenance.</p>
</section>
</body></html>"""
    path.write_text(page, encoding="utf-8")
    return path


def case_summary(db: CaseDB, case_id: int) -> dict[str, Any]:
    data = db.case_data(case_id)
    type_counts: dict[str, int] = {}
    for e in data["entities"]:
        type_counts[e["type"]] = type_counts.get(e["type"], 0) + 1
    top_types = sorted(type_counts.items(), key=lambda x: (-x[1], x[0]))
    coverage = case_source_coverage(db, case_id)
    timeline = case_timeline(db, case_id, limit=1000)
    return {
        "case": data["case"]["name"],
        "entities": len(data["entities"]),
        "relations": len(data["relations"]),
        "evidence": len(data["evidence"]),
        "notes": len(data["notes"]),
        "independent_sources": coverage.get("independent_sources", 0),
        "timeline_events": len(timeline),
        "entity_types": dict(top_types),
    }


def export_csv(db: CaseDB, case_id: int, out_dir: Path, stem: str) -> list[Path]:
    data = db.case_data(case_id)
    paths: list[Path] = []
    coverage = case_source_coverage(db, case_id)
    source_rows = [{"source": source, "entity_observations": count} for source, count in coverage.get("sources", {}).items()]
    specs = [
        ("entities", data["entities"]),
        ("relations", data["relations"]),
        ("evidence", data["evidence"]),
        ("notes", data["notes"]),
        ("assessments", data.get("assessments", [])),
        ("hypotheses", data.get("hypotheses", [])),
        ("events", data.get("events", [])),
        ("timeline", case_timeline(db, case_id, limit=1000)),
        ("sources", source_rows),
    ]
    for suffix, rows in specs:
        path = out_dir / f"{stem}.{suffix}.csv"
        if rows:
            keys: list[str] = []
            for row in rows:
                for key in row.keys():
                    if key != "metadata" and key not in keys:
                        keys.append(key)
            with path.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
                w.writeheader()
                w.writerows(rows)
        else:
            path.write_text("", encoding="utf-8")
        paths.append(path)
    return paths



def export_raw_evidence(db: CaseDB, case_id: int, out_dir: Path) -> list[Path]:
    """Materialize captured response bodies and sidecar metadata for auditability."""
    if not load_settings().get("save_raw_evidence", True):
        return []
    raw_dir = out_dir / "evidence" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    rows = db.conn.execute(
        """
        SELECT id,kind,source_url,captured_at,sha256,content_type,metadata_json,body
        FROM evidence WHERE case_id=? AND body IS NOT NULL AND length(body)>0 ORDER BY id
        """,
        (case_id,),
    ).fetchall()
    for row in rows:
        ctype = (row["content_type"] or "").lower()
        if "html" in ctype:
            ext = ".html"
        elif "json" in ctype:
            ext = ".json"
        elif "xml" in ctype:
            ext = ".xml"
        elif "text" in ctype or "javascript" in ctype:
            ext = ".txt"
        else:
            ext = ".bin"
        stem = f"{int(row['id']):04d}_{safe_filename(str(row['kind']))}"
        body_path = raw_dir / (stem + ext)
        body_path.write_bytes(bytes(row["body"]))
        sidecar = raw_dir / (stem + ".metadata.json")
        try:
            metadata = json.loads(row["metadata_json"] or "{}")
        except Exception:
            metadata = {"raw_metadata": row["metadata_json"]}
        sidecar.write_text(pretty_json({
            "evidence_id": row["id"], "kind": row["kind"], "source_url": row["source_url"],
            "captured_at": row["captured_at"], "sha256": row["sha256"],
            "content_type": row["content_type"], "metadata": metadata,
        }), encoding="utf-8")
        paths.extend([body_path, sidecar])
    return paths


def build_case_package(db: CaseDB, case_id: int, out_dir: Path, files: list[Path]) -> Path:
    case = db.conn.execute("SELECT name FROM cases WHERE id=?", (case_id,)).fetchone()
    stem = safe_filename(case["name"])
    manifest_lines = ["Digital Footprint Finder evidence package", f"Generated: {utcnow()}", ""]
    for f in files:
        if f.exists() and f.is_file():
            try:
                display = f.relative_to(out_dir).as_posix()
            except ValueError:
                display = f.name
            manifest_lines.append(f"{sha256_file(f)}  {display}")
    manifest = out_dir / f"{stem}.manifest.sha256.txt"
    manifest.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    package = out_dir / f"{stem}.case.zip"
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for f in [*files, manifest]:
            if f.exists():
                try:
                    arcname = f.relative_to(out_dir).as_posix()
                except ValueError:
                    arcname = f.name
                z.write(f, arcname=arcname)
    return package


def export_all(db: CaseDB, case_id: int, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    case = db.conn.execute("SELECT name FROM cases WHERE id=?", (case_id,)).fetchone()
    stem = safe_filename(case["name"])
    files = [
        export_json(db, case_id, out_dir / f"{stem}.json"),
        export_markdown(db, case_id, out_dir / f"{stem}.md"),
        export_graphml(db, case_id, out_dir / f"{stem}.graphml"),
        export_html(db, case_id, out_dir / f"{stem}.html"),
    ]
    analytical = {
        "focus-summary": focus_summary(db, case_id),
        "graph-intelligence": case_graph_intelligence(db, case_id),
        "questions": ranked_questions(db, case_id, 50),
        "contradictions": case_contradictions(db, case_id),
        "quality": investigation_quality(db, case_id),
        "correlation-clusters": correlation_clusters(db, case_id),
        "cross-case": cross_case_correlations(db, case_id),
        "integrity": evidence_integrity_audit(db, case_id),
    }
    for suffix, payload in analytical.items():
        ap = out_dir / f"{stem}.{suffix}.json"
        ap.write_text(pretty_json(payload), encoding="utf-8")
        files.append(ap)
    files.append(export_stix21(db, case_id, out_dir / f"{stem}.stix.json"))
    files.extend(export_csv(db, case_id, out_dir, stem))
    files.extend(export_raw_evidence(db, case_id, out_dir))
    files.append(build_case_package(db, case_id, out_dir, files))
    return files


# ---------------------------------------------------------------------------
# Terminal UI
# ---------------------------------------------------------------------------

BANNER = r"""
 _______                  ____       _            _   _
|__   __|                |  _ \     | |          | | (_)
   | |_ __ _   _  ___    | | | | ___| |_ ___  ___| |_ ___   _____
   | | '__| | | |/ _ \   | | | |/ _ \ __/ _ \/ __| __| \ \ / / _ \
   | | |  | |_| |  __/   | |_| |  __/ ||  __/ (__| |_| |\ V /  __/
   |_|_|   \__,_|\___|   |____/ \___|\__\___|\___|\__|_| \_/ \___|
"""

class UI:
    COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
    C = {
        "reset": "\033[0m", "bold": "\033[1m", "dim": "\033[2m",
        "green": "\033[92m", "yellow": "\033[93m", "cyan": "\033[96m",
        "red": "\033[91m", "blue": "\033[94m",
    }

    @classmethod
    def style(cls, text: str, *styles: str) -> str:
        if not cls.COLOR:
            return text
        return "".join(cls.C[x] for x in styles) + text + cls.C["reset"]

    @classmethod
    def title(cls, text: str) -> None:
        print("\n" + cls.style(text, "bold", "cyan"))

    @classmethod
    def ok(cls, text: str) -> None:
        print(cls.style("[+] ", "green") + text)

    @classmethod
    def info(cls, text: str) -> None:
        print(cls.style("[*] ", "cyan") + text)

    @classmethod
    def warn(cls, text: str) -> None:
        print(cls.style("[!] ", "yellow") + text)

    @classmethod
    def err(cls, text: str) -> None:
        print(cls.style("[-] ", "red") + text)


def print_result(data: Any) -> None:
    print(pretty_json(data))


def print_case_summary(db: CaseDB, case_id: int) -> None:
    s = case_summary(db, case_id)
    UI.title(f"Case: {s['case']}")
    print(f"  Entities      {s['entities']}")
    print(f"  Relationships {s['relations']}")
    print(f"  Evidence      {s['evidence']}")
    print(f"  Notes         {s['notes']}")
    print(f"  Sources       {s.get('independent_sources', 0)}")
    print(f"  Timeline      {s.get('timeline_events', 0)} events")
    if s["entity_types"]:
        top = ", ".join(f"{k}: {v}" for k, v in list(s["entity_types"].items())[:8])
        print(f"  Found          {top}")


def print_easy_result(payload: dict[str, Any]) -> None:
    typ = payload.get("type", "target")
    target = payload.get("target", "")
    result = payload.get("result", {})
    UI.ok(f"Detected {typ}: {target}")

    if typ == "domain":
        ips = result.get("resolved_ips", [])
        certs = result.get("certificates", [])
        wb = result.get("wayback", [])
        web = result.get("web") or {}
        print(f"  IP addresses:       {', '.join(ips[:6]) if ips else 'none found'}")
        print(f"  Certificate names:  {len(certs)}")
        print(f"  Archived URLs:      {len(wb)}")
        if web.get("status"):
            print(f"  Website:            HTTP {web.get('status')} — {web.get('title') or 'no title'}")
        passive = result.get("passive_sources") or {}
        passive_count = len(passive.get("wayback_hostnames", [])) + len(passive.get("hackertarget", [])) + len(passive.get("otx_passive_dns", []))
        print(f"  Passive observations:{passive_count:>3}")
        cc = result.get("common_crawl") or {}
        if cc:
            print(f"  Common Crawl URLs:   {len(cc.get('urls', []))}")
            print(f"  Common Crawl hosts:  {len(cc.get('hosts', []))}")
        crawl = result.get("crawl") or {}
        mail = result.get("mail_posture") or {}
        if mail:
            sig = mail.get("signals", {})
            enabled = [k for k,v in sig.items() if v]
            print(f"  Mail protections:   {', '.join(enabled) if enabled else 'none detected'}")
        if crawl:
            print(f"  Crawled pages:      {len(crawl.get('pages', []))}")
            print(f"  Public documents:   {len(crawl.get('documents', []))}")
            print(f"  JS endpoints:       {len(crawl.get('endpoints', []))}")
    elif typ == "url":
        print(f"  HTTP status:        {result.get('status')}")
        print(f"  Final URL:          {result.get('final_url')}")
        print(f"  Page title:         {result.get('title') or 'none'}")
        pi = result.get("page_intelligence", {})
        print(f"  Public emails:      {len(pi.get('public_emails', []))}")
        print(f"  Public phones:      {len(pi.get('public_phones', []))}")
        print(f"  Links discovered:   {len(result.get('links', []))}")
        technologies = (result.get("technology_hints") or {}).get("technologies", [])
        if technologies:
            print(f"  Technology hints:   {', '.join(str(x.get('name')) for x in technologies[:8])}")
        pi = result.get("page_intelligence", {})
        if pi.get("tracker_ids"):
            print(f"  Public identifiers: {len(pi.get('tracker_ids', []))}")
        if result.get("favicon_hashes"):
            print(f"  Favicon hashes:     {len(result.get('favicon_hashes', []))}")
        if result.get("document_metadata"):
            print(f"  Document metadata:  found")
        crawl = result.get("crawl") or {}
        if crawl:
            print(f"  Crawled pages:      {len(crawl.get('pages', []))}")
            print(f"  Public documents:   {len(crawl.get('documents', []))}")
            print(f"  JS endpoints:       {len(crawl.get('endpoints', []))}")
    elif typ == "username":
        rows = result.get("results", [])
        probable = [r for r in rows if r.get("result") == "probable"]
        possible = [r for r in rows if r.get("result") == "possible"]
        unknown = [r for r in rows if r.get("result") == "unknown"]
        print(f"  Sites checked:      {len(rows)}")
        print(f"  Probable profiles:  {len(probable)}")
        print(f"  Possible profiles:  {len(possible)}")
        for row in (probable + possible)[:12]:
            print(f"    • {row.get('site')}: {row.get('url')} [{row.get('confidence', 0):.2f}]")
        if unknown:
            print(f"  Uncertain checks:   {len(unknown)}")
        print(f"  GitHub API:         {'public profile found' if result.get('github_api') else 'no exact public profile'}")
        print(f"  GitLab API:         {len(result.get('gitlab_api', []))} exact public result(s)")
        print(f"  Alias suggestions:  {len(result.get('alias_variants', []))}")
        print(f"  Dork leads:         {len((result.get('dorks') or {}).get('links', []))}")
        UI.warn("Profile URL matches are leads, not proof that accounts belong to one person.")
    elif typ == "email":
        print(f"  Domain:             {result.get('domain')}")
        print(f"  MX records:         {len(result.get('mx', []))}")
        print(f"  SPF records:        {len(result.get('spf', []))}")
        print(f"  DMARC records:      {len(result.get('dmarc', []))}")
        posture = result.get("mail_posture") or {}
        providers = posture.get("provider_hints", [])
        if providers:
            print(f"  Mail provider hint: {', '.join(providers)}")
        print(f"  Search leads:       {len(result.get('search_links', []))}")
    elif typ == "ip":
        print(f"  Reverse DNS:        {', '.join(result.get('reverse_dns', [])) or 'none found'}")
        print(f"  RDAP data:          {'found' if result.get('rdap') else 'not found'}")
        geo = result.get("ip_intelligence") or {}
        if geo:
            print(f"  Approx. location:   {', '.join(str(x) for x in [geo.get('city'), geo.get('region'), geo.get('country')] if x) or 'unknown'}")
    elif typ in {"person", "phone", "organization"}:
        links = result.get("search_links", [])
        print(f"  Public-search leads:{len(links):>4}")
        for row in links[:6]:
            print(f"    • {row.get('engine')}: {row.get('url')}")
        if typ == "person":
            print(f"  Wikidata candidates:{len(result.get('wikidata_candidates', [])):>3}")
            print(f"  Scholarly candidates:{len(result.get('crossref_candidates', [])):>2}")
        elif typ == "organization":
            print(f"  Wikidata candidates:{len(result.get('wikidata_candidates', [])):>3}")
        UI.warn("Candidate/search matches must be corroborated before you link them to a real person or organization.")
    elif typ == "doi":
        meta = result.get("metadata") or {}
        print(f"  DOI:                {result.get('doi')}")
        print(f"  Title:              {meta.get('title') or 'not found'}")
        print(f"  Publisher:          {meta.get('publisher') or 'unknown'}")
        print(f"  Authors:            {len(meta.get('author', []))}")
    elif typ == "asn":
        print(f"  ASN:                {result.get('asn')}")
        print(f"  Holder:             {(result.get('overview') or {}).get('holder') or 'unknown'}")
        print(f"  Announced prefixes: {len(result.get('prefixes', []))}")
    elif typ == "prefix":
        print(f"  Prefix:             {result.get('prefix')}")
        overview = result.get('overview') or {}
        print(f"  Announcing ASNs:    {', '.join('AS'+str(x) if not str(x).upper().startswith('AS') else str(x) for x in overview.get('asns', [])[:8]) or 'none found'}")
    elif typ == "hash":
        print(f"  Algorithm:          {result.get('algorithm')}")
        print(f"  Hash:               {result.get('hash')}")
    elif typ == "file":
        print(f"  File:               {result.get('name')}")
        print(f"  Size:               {human_size(int(result.get('size', 0)))}")
        print(f"  SHA-256:            {result.get('sha256')}")
        if result.get("exif"):
            print(f"  EXIF fields:        {len(result['exif'])}")

    errors = result.get("errors", []) if isinstance(result, dict) else []
    if errors:
        UI.warn(f"{len(errors)} source(s) could not be queried. The rest of the case was still saved.")


def run_easy_investigation(db: CaseDB, target: str, case_name: Optional[str] = None,
                           timeout: Optional[int] = None, mode: Optional[str] = None) -> tuple[int, dict[str, Any], list[Path]]:
    settings = load_settings()
    if settings.get("auto_install_dependencies", True):
        bootstrap_dependencies(verbose=False)
    name = case_name or auto_case_name(target)
    case_id = db.get_or_create_case(name, f"Guided investigation of {target}")
    effective_timeout = int(timeout if timeout is not None else settings.get("network_timeout", DEFAULT_TIMEOUT))
    requested_mode = mode or str(settings.get("default_mode", "auto"))
    effective_mode = choose_investigation_mode(target, requested_mode)
    UI.info(f"Investigating {target} · mode: {effective_mode}")
    brain = InvestigationBrain(db, case_id, timeout=max(2, min(effective_timeout, 60)))
    payload = brain.run(target, requested_mode=requested_mode)
    analysis = smart_case_analysis(db, case_id)
    db.add_evidence(case_id, None, "smart_case_analysis", metadata=analysis)
    payload["smart_analysis"] = analysis
    payload["focus_summary"] = focus_summary(db, case_id)
    print_easy_result(payload)
    if analysis.get("corroborated"):
        UI.ok(f"Cross-source corroboration: {len(analysis['corroborated'])} observation(s)")
    paths = export_all(db, case_id, case_files_dir(name))
    save_session(latest_case_id=case_id, latest_case_name=name, latest_target=target)
    html_paths = [p for p in paths if p.suffix.lower() == ".html"]
    zip_paths = [p for p in paths if p.name.endswith(".case.zip")]
    if html_paths:
        UI.ok(f"Readable report: {html_paths[0]}")
        if settings.get("auto_open_report"):
            open_local_file(html_paths[0])
    if zip_paths:
        UI.ok(f"Evidence package: {zip_paths[0]}")
    return case_id, payload, paths

def print_focus(db: CaseDB, case_id: int) -> None:
    f=focus_summary(db,case_id); q=f["quality"]
    UI.title("What matters now")
    print(f"  Investigation quality  {q['score']}/100 · {q['label']}")
    print(f"  Evidence graph         {f['entities']} entities · {f['relations']} relationships · {f['evidence']} evidence")
    print(f"  Contradictions         {len(f['contradictions'])}")
    if f["strongest"]:
        print("\n  Strongest supported findings:")
        for e in f["strongest"][:5]:
            print(f"    #{e['id']} {e['type']}: {truncate(str(e['value']),72)} · {len(e['source_families'])} source families · {float(e['confidence']):.2f}")
    if f["questions"]:
        best=f["questions"][0]
        print(f"\n  Best next question:\n    {best['question']}\n    Why: {best['why']}")


def render_search_results(rows: list[dict[str,Any]]) -> None:
    if not rows:
        UI.warn("No saved findings matched.")
        return
    UI.title("Search results")
    for i,r in enumerate(rows,1):
        kind=r.get("kind")
        if kind=="entity":
            print(f"[{i}] [entity] #{r['id']} {r['type']}: {truncate(str(r['value']),90)}")
            print(f"    case: {r.get('case_name')} · confidence {float(r.get('confidence',0)):.2f} · {truncate(str(r.get('source') or ''),100)}")
        elif kind=="evidence":
            print(f"[{i}] [evidence] #{r['id']} {r.get('evidence_kind')} · {truncate(str(r.get('source_url') or ''),100)}")
        elif kind=="note":
            print(f"[{i}] [note] #{r['id']} {truncate(str(r.get('text') or ''),110)}")
        else:
            print(f"[{i}] [{kind}] #{r.get('id')} {truncate(str(r.get('text') or r.get('value') or ''),110)}")


def settings_set_value(settings: dict[str,Any], key: str, raw: str) -> Any:
    if key not in DEFAULT_SETTINGS: raise ValueError(f"Unknown setting: {key}")
    current=DEFAULT_SETTINGS[key]
    if isinstance(current,bool):
        v=raw.lower()
        if v not in {"on","off","true","false","yes","no","1","0"}: raise ValueError("Use on/off.")
        return v in {"on","true","yes","1"}
    if isinstance(current,int):
        v=int(raw)
        ranges={"network_timeout":(2,60),"search_limit":(5,200),"max_crawl_pages":(1,80),"username_workers":(1,16),"json_cache_ttl":(0,86400)}
        if key in ranges and not (ranges[key][0]<=v<=ranges[key][1]): raise ValueError(f"{key} must be {ranges[key][0]}–{ranges[key][1]}.")
        return v
    if key=="default_mode" and raw not in {"auto","passive","normal","deep"}: raise ValueError("Use auto/passive/normal/deep.")
    if key=="search_scope" and raw not in {"current","all"}: raise ValueError("Use current/all.")
    if key=="colors" and raw not in {"auto","on","off"}: raise ValueError("Use auto/on/off.")
    return raw


def settings_menu() -> None:
    settings=load_settings()
    labels=[
        ("default_mode","Default investigation mode"),("network_timeout","Network timeout"),
        ("guided_followup","Guided follow-up menu"),("auto_open_report","Automatically open HTML report"),
        ("auto_install_dependencies","Auto-install optional Python enrichers"),("search_scope","Default search scope"),
        ("search_limit","Search result limit"),("colors","Terminal colors"),("resume_latest_case","Resume latest case"),
        ("max_crawl_pages","Default crawl-page ceiling"),("username_workers","Username-check workers"),
        ("json_cache_ttl","Public JSON cache TTL (seconds)"),("save_raw_evidence","Save raw HTTP evidence"),
    ]
    while True:
        UI.title("Settings")
        for i,(key,label) in enumerate(labels,1): print(f"[{i}] {label:38} {settings.get(key)}")
        print("[A] Optional API credentials")
        print("[0] Back")
        raw=input("Choose setting: ").strip()
        if raw in {"","0"}: break
        if raw.lower()=="a": api_keys_menu(); continue
        try:
            idx=int(raw)-1; key,label=labels[idx]
            value=input(f"{label} [{settings.get(key)}]: ").strip()
            if not value: continue
            settings[key]=settings_set_value(settings,key,value)
            save_settings(settings); apply_color_setting(settings); UI.ok("Saved.")
        except (ValueError,IndexError) as exc: UI.err(str(exc))


def current_case_id(db: CaseDB) -> Optional[int]:
    settings=load_settings(); session=load_session()
    if settings.get("resume_latest_case",True) and session.get("latest_case_id"):
        row=db.get_case(int(session["latest_case_id"]))
        if row: return int(row["id"])
    row=db.latest_case(); return int(row["id"]) if row else None


def local_search_prompt(db: CaseDB, case_id: Optional[int]=None, initial: str="") -> None:
    settings=load_settings(); q=initial.strip() or input("Search saved findings: ").strip()
    if not q: return
    scope_case=case_id if settings.get("search_scope","current")=="current" else None
    rows=db.search(q,case_id=scope_case,limit=int(settings.get("search_limit",25)))
    render_search_results(rows)
    if rows:
        choice=input("Open entity result number [Enter = done]: ").strip()
        if choice.isdigit():
            i=int(choice)-1
            if 0<=i<len(rows) and rows[i].get("kind")=="entity":
                print_result(explain_entity(db,int(rows[i]["case_id"]),int(rows[i]["id"])))


def ask_case(db: CaseDB, case_id: int, question: str) -> Any:
    q=question.lower().strip()
    ids=[int(x) for x in re.findall(r"#?(\d+)",q)]
    if "what next" in q or "check next" in q or "next step" in q or "question" in q:
        return ranked_questions(db,case_id,10)
    if "strong" in q or "matter" in q or "summary" in q:
        return focus_summary(db,case_id)
    if "contradiction" in q or "conflict" in q:
        return case_contradictions(db,case_id)
    if "quality" in q:
        return investigation_quality(db,case_id)
    if "connect" in q and len(ids)>=2:
        return relationship_path(db,case_id,ids[0],ids[1])
    if "compare" in q and len(ids)>=2:
        return compare_entities(db,case_id,ids[0],ids[1])
    if "cluster" in q or "related sites" in q:
        return correlation_clusters(db,case_id)
    if "explain" in q and ids:
        return explain_entity(db,case_id,ids[0])
    return {"answer":"I can answer: what next, strongest findings, contradictions, quality, explain <entity id>, or what connects <id> and <id>.",
            "focus":focus_summary(db,case_id)}


def home_menu(db: CaseDB) -> str:
    UI.title("Home")
    print("[1] Investigate a clue\n[2] Search saved findings\n[3] Continue current/recent case\n[4] Ask about current case\n[5] Cases\n[6] Settings\n[7] Help\n[0] Quit")
    return input("Choose: ").strip()


def guided_followup(db: CaseDB, case_id: int, paths: list[Path]) -> None:
    if not load_settings().get("guided_followup",True): return
    while True:
        print_focus(db,case_id)
        print("\n[Enter] Done  [1] Continue deeper  [2] Search case  [3] Explain entity  [4] Review entity")
        print("[5] Add another clue  [6] Open report  [7] Refresh exports  [8] Settings  [9] Ask case")
        c=input("Action: ").strip()
        if not c: return
        try:
            if c=="1":
                session=load_session(); target=str(session.get("latest_target") or "").strip() or input("Target to continue: ").strip()
                if target:
                    UI.info("Continuing with bounded Deep Mode …")
                    payload=InvestigationBrain(db,case_id,int(load_settings().get("network_timeout",DEFAULT_TIMEOUT))).run(target,"deep")
                    print_easy_result(payload); paths[:]=export_all(db,case_id,case_files_dir(db.get_case(case_id)["name"]))
            elif c=="2": local_search_prompt(db,case_id)
            elif c=="3":
                raw=input("Entity ID: ").strip().lstrip("#"); print_result(explain_entity(db,case_id,int(raw)))
            elif c=="4":
                eid=int(input("Entity ID: ").strip().lstrip("#")); status=input("confirmed / rejected / uncertain: ").strip().lower(); note=input("Note (optional): ")
                db.add_assessment(case_id,eid,status,note); UI.ok("Assessment saved.")
            elif c=="5":
                target=input("Additional clue: ").strip()
                if target:
                    payload=InvestigationBrain(db,case_id,int(load_settings().get("network_timeout",DEFAULT_TIMEOUT))).run(target,"auto")
                    print_easy_result(payload); save_session(latest_case_id=case_id,latest_case_name=db.get_case(case_id)["name"],latest_target=target)
                    paths[:]=export_all(db,case_id,case_files_dir(db.get_case(case_id)["name"]))
            elif c=="6":
                report=next((p for p in paths if p.suffix.lower()==".html"),None)
                if report and open_local_file(report): UI.ok("Opened report.")
                else: UI.warn("Could not open automatically; the report path is shown in the case folder.")
            elif c=="7": paths[:]=export_all(db,case_id,case_files_dir(db.get_case(case_id)["name"])); UI.ok("Exports refreshed.")
            elif c=="8": settings_menu()
            elif c=="9": print_result(ask_case(db,case_id,input("Ask: ")))
            else: UI.warn("Unknown action.")
        except Exception as exc: UI.err(str(exc))


def choose_existing_case(db: CaseDB) -> Optional[int]:
    cases = db.list_cases()[:12]
    if not cases:
        UI.warn("No saved cases yet.")
        return None
    UI.title("Recent cases")
    for i, row in enumerate(cases, 1):
        print(f"[{i}] {row['name']}  ({row['created_at']})")
    raw = input("Choose case number [Enter = cancel]: ").strip()
    if not raw:
        return None
    try:
        idx = int(raw) - 1
        return int(cases[idx]["id"])
    except (ValueError, IndexError):
        UI.err("Invalid case number.")
        return None


def advanced_menu(db: CaseDB, case_id: int) -> None:
    det = DigitalFootprintFinder(db, case_id)
    while True:
        print("""
Advanced tools
 [1] Domain        [2] URL          [3] Username
 [4] Email         [5] IP           [6] Person
 [7] Phone         [8] Local file   [9] Search links
 [10] Dork pack    [11] Add note     [12] Raw JSON
 [13] Export       [14] ASN          [15] CIDR prefix
 [16] DOI          [17] Organization [18] Timeline
 [0] Back
""")
        choice = input("advanced> ").strip()
        try:
            if choice == "1": print_result(det.domain(input("Domain: "), deep=True))
            elif choice == "2": print_result(det.url(input("URL: ")))
            elif choice == "3": print_result(det.username(input("Username: ")))
            elif choice == "4": print_result(det.email(input("Email: ")))
            elif choice == "5": print_result(det.ip(input("IP: ")))
            elif choice == "6": print_result(det.person(input("Full name: ")))
            elif choice == "7": print_result(det.phone(input("Phone: ")))
            elif choice == "8": print_result(det.local_file(input("File path: ")))
            elif choice == "9": print_result(det.search_links([input("Search query: ")]))
            elif choice == "10":
                target = input("Target for dorks: ")
                root = det._entity(detect_target_type(target), target, confidence=1.0, source="user")
                print_result(det.dorks(target, attach_to=root))
            elif choice == "11":
                db.add_note(case_id, input("Case note: "))
                UI.ok("Note saved.")
            elif choice == "12": print_result(db.case_data(case_id))
            elif choice == "13":
                row = db.conn.execute("SELECT name FROM cases WHERE id=?", (case_id,)).fetchone()
                paths = export_all(db, case_id, case_files_dir(row["name"]))
                for p in paths: print(" -", p)
            elif choice == "14": print_result(det.asn(input("ASN: ")))
            elif choice == "15": print_result(det.prefix(input("CIDR prefix: ")))
            elif choice == "16": print_result(det.doi(input("DOI: ")))
            elif choice == "17": print_result(det.organization(input("Organization: ")))
            elif choice == "18": print_result(case_timeline(db, case_id))
            elif choice == "0": return
            else: UI.err("Unknown option.")
        except KeyboardInterrupt:
            print("\nCancelled.")
        except Exception as e:
            UI.err(str(e))


def doctor() -> dict[str, Any]:
    ensure_workspace()
    checks: dict[str, Any] = {
        "python": "available",
        "sqlite": "available",
        "home_workspace": str(APP_HOME),
        "home_writable": os.access(APP_HOME, os.W_OK),
        "downloads": str(ensure_termux_storage() or (Path.home() / "Downloads")),
        "dig": shutil.which("dig") or "not installed (DoH fallback enabled)",
        "database_write": False,
        "api_sources": api_status_report(),
    }
    for module in BOOTSTRAP_PACKAGES:
        checks[module] = "available" if _module_available(module) else "missing (auto-install on startup)"
    try:
        tmp = DATA_DIR / ".digital_footprint_finder_doctor.db"
        testdb = CaseDB(tmp)
        cid = testdb.get_or_create_case("doctor")
        testdb.add_note(cid, "ok")
        testdb.close()
        for extra in (tmp, Path(str(tmp) + "-wal"), Path(str(tmp) + "-shm")):
            with contextlib.suppress(Exception):
                extra.unlink()
        checks["database_write"] = True
    except Exception as e:
        checks["database_error"] = str(e)
    return checks


def print_help_screen() -> None:
    print(r"""
Digital Footprint Finder — Help

EASIEST WAY
  python "Digital Footprint Finder.py"
  Paste one clue. Press Enter for the Home menu.

EXAMPLES
  example.com                 domain
  https://example.com/path    URL
  alice                       username
  alice@example.com           email
  @alice@example.social       explicit Fediverse handle
  8.8.8.8                     IP
  +30 210 123 4567            phone
  Jane Example                person/name
  org:Example Foundation      organization
  AS13335                     autonomous system
  1.1.1.0/24                 network prefix
  10.1000/example             DOI
  <64 hex chars>              SHA-256 hash
  /path/to/photo.jpg          local file

PLAIN-LANGUAGE INTERACTIVE COMMANDS
  search for example.com
  find alice
  ask what should I check next?
  what next?
  show strongest findings
  show contradictions
  show quality
  explain 17
  what connects 17 and 42
  settings
  api
  cases
  open
  doctor
  advanced

INVESTIGATION MODES
  auto      conservative for ambiguous identity targets; normal for structured technical targets
  passive   initial public-source investigation only
  normal    bounded high-value recursive pivots
  deep      larger but still bounded passive/public-source pivot budget

CLI EXAMPLES
  python "Digital Footprint Finder.py" --mode normal example.com
  python "Digital Footprint Finder.py" fediverse @alice@example.social
  python "Digital Footprint Finder.py" --case "Acme" search example.com
  python "Digital Footprint Finder.py" --case "Acme" ask "what should I check next?"
  python "Digital Footprint Finder.py" --case "Acme" explain 17
  python "Digital Footprint Finder.py" --case "Acme" path 17 42
  python "Digital Footprint Finder.py" --case "Acme" compare 17 42
  python "Digital Footprint Finder.py" --case "Acme" clusters
  python "Digital Footprint Finder.py" --case "Acme" crosscase
  python "Digital Footprint Finder.py" --case "Acme" audit
  python "Digital Footprint Finder.py" --case "Acme" quality
  python "Digital Footprint Finder.py" --case "Acme" questions
  python "Digital Footprint Finder.py" --case "Acme" contradictions
  python "Digital Footprint Finder.py" settings
  python "Digital Footprint Finder.py" settings default_mode deep
  python "Digital Footprint Finder.py" api list
  python "Digital Footprint Finder.py" api set github
  python "Digital Footprint Finder.py" api remove github
  python "Digital Footprint Finder.py" websearch "example.com contact"

STORAGE
  App data:  ~/Digital Footprint Finder/
  Settings:  ~/Digital Footprint Finder/settings.json
  API keys:  ~/Digital Footprint Finder/api_keys.json (restricted permissions; values never printed)
  Results:   ~/storage/downloads/Digital Footprint Finder/<Case Name>/files/

IMPORTANT
  Results are leads, not automatic proof of identity, ownership, intent, wrongdoing, or current control.
  Candidate people/organizations stay separate until independently corroborated.
  Digital Footprint Finder uses public sources and bounded crawling; it does not bypass authentication.
  Its OSINT logic is native to this file; it does not clone or execute external OSINT projects.
""")


def interactive(db_path: Path) -> None:
    settings=load_settings(); apply_color_setting(settings)
    print(BANNER)
    print(UI.style(APP_NAME, "bold"))
    print("Paste one clue, or press Enter for Home. Digital Footprint Finder chooses a safe investigation mode automatically.")
    print("Commands: search  settings  ask  cases  open  help  doctor  advanced  quit\n")
    db=CaseDB(db_path)
    try:
        while True:
            try: raw=input(UI.style("Investigate / command\n> ","bold")).strip()
            except EOFError: print(); break
            except KeyboardInterrupt: print("\nType quit to exit."); continue
            if not raw:
                choice=home_menu(db)
                if choice=="0": break
                if choice=="1": raw=input("Clue: ").strip()
                elif choice=="2": local_search_prompt(db,current_case_id(db)); continue
                elif choice=="3":
                    cid=current_case_id(db)
                    if cid: print_focus(db,cid); guided_followup(db,cid,export_all(db,cid,case_files_dir(db.get_case(cid)["name"])))
                    else: UI.warn("No saved case yet.")
                    continue
                elif choice=="4":
                    cid=current_case_id(db)
                    if cid: print_result(ask_case(db,cid,input("Ask: ")))
                    else: UI.warn("No saved case yet.")
                    continue
                elif choice=="5": raw="cases"
                elif choice=="6": settings_menu(); continue
                elif choice=="7": print_help_screen(); continue
                else: continue
            lower=raw.lower().strip(); command=lower[1:] if lower.startswith(":") else lower
            if command in {"quit","q","exit"}: break
            if command in {"help","h","?"}: print_help_screen(); continue
            if command in {"settings","setting"}: settings_menu(); continue
            if command in {"api","apis","api keys","api key"}: api_keys_menu(); continue
            if command=="cases":
                rows=db.list_cases()[:25]; UI.title("Recent cases")
                if not rows: UI.warn("No saved cases yet.")
                for row in rows: print(f"#{row['id']}  {row['name']}  {row['created_at']}")
                continue
            if command=="doctor": print_result(doctor()); continue
            if command=="open":
                cid=choose_existing_case(db)
                if cid:
                    row=db.get_case(cid); save_session(latest_case_id=cid,latest_case_name=row["name"]); print_focus(db,cid)
                    guided_followup(db,cid,export_all(db,cid,case_files_dir(row["name"])))
                continue
            if command=="advanced":
                cid=current_case_id(db) or db.get_or_create_case("Manual Investigation "+dt.datetime.now().strftime("%Y-%m-%d %H%M")); advanced_menu(db,cid); continue
            if command.startswith("search for "): local_search_prompt(db,current_case_id(db),raw[11:]); continue
            if command.startswith("search "): local_search_prompt(db,current_case_id(db),raw[7:]); continue
            if command.startswith("find "): local_search_prompt(db,current_case_id(db),raw[5:]); continue
            if command.startswith("ask "):
                cid=current_case_id(db)
                if cid: print_result(ask_case(db,cid,raw[4:]))
                else: UI.warn("No saved case yet.")
                continue
            if command in {"what next?","what next","what should i check next?","show strongest findings","show contradictions","show quality"} or command.startswith("explain ") or command.startswith("what connects "):
                cid=current_case_id(db)
                if cid: print_result(ask_case(db,cid,raw))
                else: UI.warn("No saved case yet.")
                continue
            if command.startswith("new "):
                target=raw[4:].strip(); case_name=auto_case_name(target)+" "+dt.datetime.now().strftime("%Y-%m-%d %H%M%S")
            else:
                target=raw; case_name=None
            if not target: continue
            try:
                cid,payload,paths=run_easy_investigation(db,target,case_name=case_name)
                print_focus(db,cid); guided_followup(db,cid,paths)
            except KeyboardInterrupt: print("\nCancelled.")
            except Exception as exc: UI.err(str(exc)); UI.info("Type help to see examples.")
    finally: db.close()

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog="Digital Footprint Finder.py",formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Digital Footprint Finder — guided, case-centric public-source OSINT toolkit.")
    p.add_argument("--db",default=str(DEFAULT_DB_PATH))
    p.add_argument("--case",default=None)
    p.add_argument("--description",default="")
    p.add_argument("--timeout",type=int,default=None)
    p.add_argument("--mode",choices=["auto","passive","normal","deep"],default=None)
    sub=p.add_subparsers(dest="command")
    q=sub.add_parser("quick"); q.add_argument("target")
    d=sub.add_parser("deep"); d.add_argument("target")
    domain=sub.add_parser("domain"); domain.add_argument("domain"); domain.add_argument("--shallow",action="store_true")
    url=sub.add_parser("url"); url.add_argument("url")
    un=sub.add_parser("username"); un.add_argument("username"); un.add_argument("--workers",type=int,default=None)
    email=sub.add_parser("email"); email.add_argument("email")
    ip=sub.add_parser("ip"); ip.add_argument("ip")
    person=sub.add_parser("person"); person.add_argument("name")
    phone=sub.add_parser("phone"); phone.add_argument("phone")
    org=sub.add_parser("organization"); org.add_argument("name")
    fed=sub.add_parser("fediverse"); fed.add_argument("handle")
    asn=sub.add_parser("asn"); asn.add_argument("asn")
    pref=sub.add_parser("prefix"); pref.add_argument("prefix")
    doi=sub.add_parser("doi"); doi.add_argument("doi")
    hp=sub.add_parser("hash"); hp.add_argument("hash")
    fp=sub.add_parser("file"); fp.add_argument("path")
    search=sub.add_parser("search",help="Search saved case data"); search.add_argument("query",nargs="+")
    web=sub.add_parser("websearch",help="Generate public search-engine leads"); web.add_argument("query",nargs="+")
    dorks=sub.add_parser("dorks"); dorks.add_argument("target")
    note=sub.add_parser("note"); note.add_argument("text")
    ask=sub.add_parser("ask"); ask.add_argument("question",nargs="+")
    explain=sub.add_parser("explain"); explain.add_argument("entity_id",type=int)
    path=sub.add_parser("path"); path.add_argument("start_id",type=int); path.add_argument("end_id",type=int)
    compare=sub.add_parser("compare"); compare.add_argument("left_id",type=int); compare.add_argument("right_id",type=int)
    assess=sub.add_parser("assess"); assess.add_argument("entity_id",type=int); assess.add_argument("status",choices=["confirmed","rejected","uncertain"]); assess.add_argument("note",nargs="*",default=[])
    hyp=sub.add_parser("hypothesis"); hyp.add_argument("text",nargs="+")
    settings=sub.add_parser("settings"); settings.add_argument("key",nargs="?"); settings.add_argument("value",nargs="?")
    api=sub.add_parser("api",help="Manage optional API credentials without putting secrets in shell history")
    api.add_argument("action",choices=["list","set","remove"],nargs="?",default="list")
    api.add_argument("provider",nargs="?")
    for cmd in ("summary","timeline","sources","graph","questions","quality","contradictions","clusters","crosscase","audit","cases","doctor","help"):
        sub.add_parser(cmd)
    export=sub.add_parser("export"); export.add_argument("--out",default=None)
    return p


def _rewrite_easy_argv(argv: list[str]) -> list[str]:
    commands={"quick","deep","domain","url","username","email","ip","person","phone","organization","fediverse","asn","prefix","doi","hash","file","search","websearch","dorks","note","ask","explain","path","compare","assess","hypothesis","settings","api","summary","timeline","sources","graph","questions","quality","contradictions","clusters","crosscase","audit","export","cases","doctor","help"}
    if not argv: return argv
    value_options={"--db","--case","--description","--timeout","--mode"}; i=0
    while i<len(argv):
        token=argv[i]
        if token in value_options: i+=2; continue
        if token.startswith("--"): i+=1; continue
        if token in commands: return argv
        return argv[:i]+["quick",token]+argv[i+1:]
    return argv


def _resolve_case_for_command(db: CaseDB, requested: Optional[str], description: str, create: bool=True) -> tuple[Optional[int],Optional[str]]:
    if requested:
        return db.get_or_create_case(requested,description),requested
    cid=current_case_id(db)
    if cid:
        row=db.get_case(cid); return cid,str(row["name"])
    if create:
        return db.get_or_create_case("Default Case",description),"Default Case"
    return None,None


def main(argv: Optional[list[str]]=None) -> int:
    ensure_workspace(); settings=load_settings(); apply_color_setting(settings)
    raw=_rewrite_easy_argv(list(sys.argv[1:] if argv is None else argv)); parser=build_parser(); args=parser.parse_args(raw)
    db_path=Path(args.db).expanduser()
    if args.command=="help": print_help_screen(); return 0
    if args.command=="settings":
        st=load_settings()
        if not args.key: print(pretty_json(st)); return 0
        if args.value is None: print(f"{args.key} = {st.get(args.key,'<unknown>')}"); return 0
        try:
            st[args.key]=settings_set_value(st,args.key,args.value); save_settings(st); apply_color_setting(st); print(f"{args.key} = {st[args.key]}"); return 0
        except Exception as exc: print(f"Error: {exc}",file=sys.stderr); return 1
    if args.command=="api":
        if args.action=="list":
            print(pretty_json(api_status_report())); return 0
        provider=(args.provider or "").lower().strip()
        if provider not in API_PROVIDERS:
            print("Provider must be one of: " + ", ".join(API_PROVIDERS), file=sys.stderr); return 1
        if args.action=="remove":
            keys=load_api_keys(); keys.pop(provider,None); save_api_keys(keys); print("Saved API credential removed."); return 0
        value=getpass.getpass(f"{API_PROVIDERS[provider]['label']} API key/token (input hidden): ").strip()
        if not value:
            print("No credential entered.",file=sys.stderr); return 1
        keys=load_api_keys(); keys[provider]=value; save_api_keys(keys); print("API credential saved securely."); return 0
    if not args.command: interactive(db_path); return 0
    if args.command=="doctor": print_result(doctor()); return 0
    db=CaseDB(db_path)
    try:
        if args.command=="cases":
            for r in db.list_cases(): print(f"{r['id']:>3}  {r['name']}  ({r['created_at']})")
            return 0
        timeout=max(2,min(int(args.timeout if args.timeout is not None else settings.get("network_timeout",DEFAULT_TIMEOUT)),60))
        mode=args.mode or str(settings.get("default_mode","auto"))
        if args.command in {"quick","deep"}:
            run_easy_investigation(db,args.target,case_name=args.case,timeout=timeout,mode=("deep" if args.command=="deep" else mode)); return 0
        analysis_commands={"search","ask","explain","path","compare","summary","timeline","sources","graph","questions","quality","contradictions","clusters","crosscase","audit","export","assess","hypothesis"}
        cid,cname=_resolve_case_for_command(db,args.case,args.description,create=args.command not in analysis_commands)
        if cid is None:
            print("No saved case. Investigate something first or provide --case.",file=sys.stderr); return 1
        case_id=int(cid); case_name=str(cname); det=DigitalFootprintFinder(db,case_id,timeout=timeout)
        investigation_commands={"domain","url","username","email","ip","person","phone","organization","fediverse","asn","prefix","doi","hash","file","websearch","dorks"}
        if args.command in investigation_commands and settings.get("auto_install_dependencies",True): bootstrap_dependencies(verbose=False)
        if args.command=="domain": result=det.domain(args.domain,deep=not args.shallow)
        elif args.command=="url": result=det.url(args.url)
        elif args.command=="username": result=det.username(args.username,workers=args.workers or int(settings.get("username_workers",8)))
        elif args.command=="email": result=det.email(args.email)
        elif args.command=="ip": result=det.ip(args.ip)
        elif args.command=="person": result=det.person(args.name)
        elif args.command=="phone": result=det.phone(args.phone)
        elif args.command=="organization": result=det.organization(args.name)
        elif args.command=="fediverse": result=det.fediverse(args.handle)
        elif args.command=="asn": result=det.asn(args.asn)
        elif args.command=="prefix": result=det.prefix(args.prefix)
        elif args.command=="doi": result=det.doi(args.doi)
        elif args.command=="hash": result=det.hash_value(args.hash)
        elif args.command=="file": result=det.local_file(args.path)
        elif args.command=="websearch": result=det.search_links(args.query)
        elif args.command=="dorks":
            root=det._entity(detect_target_type(args.target),strip_explicit_target_prefix(args.target),confidence=1.0,source="user"); result=det.dorks(args.target,attach_to=root)
        elif args.command=="search": result=db.search(" ".join(args.query),case_id=case_id,limit=int(settings.get("search_limit",25)))
        elif args.command=="ask": result=ask_case(db,case_id," ".join(args.question))
        elif args.command=="explain": result=explain_entity(db,case_id,args.entity_id)
        elif args.command=="path": result=relationship_path(db,case_id,args.start_id,args.end_id)
        elif args.command=="compare": result=compare_entities(db,case_id,args.left_id,args.right_id)
        elif args.command=="assess": db.add_assessment(case_id,args.entity_id,args.status," ".join(args.note)); result={"saved":True}
        elif args.command=="hypothesis": hid=db.add_hypothesis(case_id," ".join(args.text)); result={"hypothesis_id":hid}
        elif args.command=="note": db.add_note(case_id,args.text); result={"saved":True}
        elif args.command=="summary": result=case_summary(db,case_id)
        elif args.command=="timeline": result=case_timeline(db,case_id)
        elif args.command=="sources": result=case_source_coverage(db,case_id)
        elif args.command=="graph": result=case_graph_intelligence(db,case_id)
        elif args.command=="questions": result=ranked_questions(db,case_id,25)
        elif args.command=="quality": result=investigation_quality(db,case_id)
        elif args.command=="contradictions": result=case_contradictions(db,case_id)
        elif args.command=="clusters": result=correlation_clusters(db,case_id)
        elif args.command=="crosscase": result=cross_case_correlations(db,case_id)
        elif args.command=="audit": result=evidence_integrity_audit(db,case_id)
        elif args.command=="export":
            for path in export_all(db,case_id,Path(args.out) if args.out else case_files_dir(case_name)): print(path)
            return 0
        else: parser.error("Unknown command"); return 2
        print_result(result)
        if args.command in investigation_commands:
            save_session(latest_case_id=case_id,latest_case_name=case_name)
        return 0
    except KeyboardInterrupt: print("\nCancelled.",file=sys.stderr); return 130
    except Exception as exc: print(f"Error: {exc}",file=sys.stderr); return 1
    finally: db.close()


if __name__=="__main__":
    raise SystemExit(main())
