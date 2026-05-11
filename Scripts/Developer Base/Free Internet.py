#!/usr/bin/env python3

import argparse
import base64
import hashlib
import hmac
import html
import json
import mimetypes
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.parse
import uuid
import socket
from pathlib import Path
from typing import Dict, List, Optional, Tuple

APP_TITLE = "Free Internet"
DEFAULT_PORT = 6060
SEARCH_ENGINES = {
    "google": ("Google", "https://www.google.com/search?q={q}"),
    "duckduckgo": ("DuckDuckGo", "https://duckduckgo.com/html/?q={q}"),
    "bing": ("Bing", "https://www.bing.com/search?q={q}"),
    "brave": ("Brave", "https://search.brave.com/search?q={q}"),
    "startpage": ("Startpage", "https://www.startpage.com/sp/search?query={q}"),
    "yahoo": ("Yahoo", "https://search.yahoo.com/search?p={q}"),
    "yandex": ("Yandex", "https://yandex.com/search/?text={q}"),
}
COUNTRIES = {
    "US": "United States",
    "DE": "Germany",
    "GB": "United Kingdom",
    "FR": "France",
    "NL": "Netherlands",
    "JP": "Japan",
    "IN": "India",
    "BR": "Brazil",
    "AU": "Australia",
}
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid", "mc_cid", "mc_eid", "igshid", "mkt_tok", "ref_src",
}
BLOCKED_HOST_PATTERNS = {
    "doubleclick.net", "googlesyndication.com", "googleadservices.com", "adservice.google.",
    "googletagmanager.com", "google-analytics.com", "analytics.google.com", "adnxs.com",
    "taboola.com", "outbrain.com", "criteo.com", "scorecardresearch.com", "hotjar.com",
    "segment.io", "facebook.net", "connect.facebook.net", "ads-twitter.com", "amazon-adsystem.com",
    "branch.io", "appsflyer.com", "quantserve.com", "zedo.com", "adsystem.com",
    "propellerads.com", "popads.net", "onesignal.com", "sentry.io",
}
ADLIKE_CLASS_RE = re.compile(r"(?i)(^|[\s\-_])(ad|ads|advert|advertisement|banner|sponsor|sponsored|popup|promoted)([\s\-_]|$)")
URL_ATTR_RE = re.compile(r'(?i)(\b(?:href|src|action|poster)\s*=\s*)(["\'])(.*?)(\2)')
FORM_TAG_RE = re.compile(r'(?i)<form\b(?![^>]*\benctype=)([^>]*)>')
TITLE_RE = re.compile(r'(?is)<title[^>]*>(.*?)</title>')
TEXT_CLEAN_RE = re.compile(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>|<!--.*?-->|<[^>]+>')
REQUEST_TIMEOUT = 18
PROXY_API = "https://api.proxyscrape.com/v3/free-proxy-list/get"
PROXY_CACHE_TTL = 240
BAD_PROXY_TTL = 1800
MIN_PROXY_POOL = 10
MAX_PROXY_TRIES = 14
TOR_SOCKS_PORT = 9050

# ---------------- bootstrap ----------------
def _run(cmd: List[str]) -> bool:
    try:
        res = subprocess.run(cmd, check=False)
        return res.returncode == 0
    except Exception:
        return False


def which(name: str) -> Optional[str]:
    for p in os.environ.get("PATH", "").split(os.pathsep):
        if not p:
            continue
        c = Path(p) / name
        if c.exists() and os.access(str(c), os.X_OK):
            return str(c)
    return None


def is_termux() -> bool:
    prefix = os.environ.get("PREFIX", "")
    return "com.termux" in prefix or "TERMUX_VERSION" in os.environ


def ensure_python_deps() -> None:
    missing = []
    try:
        import flask  # noqa: F401
    except Exception:
        missing.append("flask")
    try:
        import requests  # noqa: F401
    except Exception:
        missing.append("requests")
    if not missing:
        return
    if is_termux() and which("pkg"):
        _run(["pkg", "update", "-y"])
        _run(["pkg", "install", "-y", "python"])
    if not _run([sys.executable, "-m", "pip", "install", "--upgrade", *missing]):
        print("Failed to install Python dependencies.")
        print("Try in Termux:")
        print("  pkg install python")
        print("  pip install flask requests")
        sys.exit(1)
    os.execv(sys.executable, [sys.executable] + sys.argv)


def ensure_openssl() -> None:
    if which("openssl"):
        return
    if is_termux() and which("pkg"):
        _run(["pkg", "update", "-y"])
        if _run(["pkg", "install", "-y", "openssl"]):
            return
    print("OpenSSL CLI is required for the vault.")
    print("Try in Termux: pkg install openssl")
    sys.exit(1)


ensure_python_deps()
ensure_openssl()

import requests
from flask import Flask, Response, flash, redirect, render_template_string, request, session, url_for, send_file

# ---------------- storage ----------------
def default_data_dir() -> Path:
    home = Path.home()
    if is_termux():
        return home / "Free Internet"
    return home / ".free_internet"


DATA_DIR = default_data_dir()
DATA_DIR.mkdir(parents=True, exist_ok=True)
BROWSER_DIR = DATA_DIR / "browser"
VAULT_DIR = DATA_DIR / "vault"
DOWNLOADS_DIR = BROWSER_DIR / "saved"
TOOLS_DIR = DATA_DIR / "tools"
SCREENSHOT_DIR = TOOLS_DIR / "screenshots"
for p in (BROWSER_DIR, VAULT_DIR, DOWNLOADS_DIR, TOOLS_DIR, SCREENSHOT_DIR):
    p.mkdir(parents=True, exist_ok=True)

BOOKMARKS_FILE = BROWSER_DIR / "bookmarks.json"
HISTORY_FILE = BROWSER_DIR / "history.json"
PREFS_FILE = BROWSER_DIR / "prefs.json"
PROXY_CACHE_FILE = BROWSER_DIR / "proxy_cache.json"
PROXY_STATE_FILE = BROWSER_DIR / "proxy_state.json"
VAULT_DB = VAULT_DIR / "vault.db"

# ---------------- browser state ----------------
BROWSER_CLIENTS: Dict[str, requests.Session] = {}
VAULT_KEYS: Dict[str, str] = {}
TOR_PROCESS: Optional[subprocess.Popen] = None
TOR_STDOUT_PATH = BROWSER_DIR / "tor.log"
TOR_DATA_DIR = BROWSER_DIR / "tor_data"
TOR_DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_client_id() -> str:
    cid = session.get("client_id")
    if not cid:
        cid = uuid.uuid4().hex
        session["client_id"] = cid
    return cid


def browser_session() -> requests.Session:
    cid = get_client_id()
    if cid not in BROWSER_CLIENTS:
        s = requests.Session()
        s.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Mobile) AppleWebKit/537.36 Chrome/124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "DNT": "1",
            "Sec-GPC": "1",
            "Upgrade-Insecure-Requests": "1",
        })
        BROWSER_CLIENTS[cid] = s
    return BROWSER_CLIENTS[cid]


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def safe_file_stem(value: str, fallback: str = "file") -> str:
    value = re.sub(r'[^a-zA-Z0-9._-]+', '_', (value or "").strip()).strip('._')
    return (value or fallback)[:80]


def browser_prefs() -> dict:
    prefs = load_json(PREFS_FILE, {})
    merged = {
        "country": prefs.get("country", "US"),
        "engine": prefs.get("engine", "google"),
        "adblock": bool(prefs.get("adblock", True)),
        "lite": bool(prefs.get("lite", False)),
        "block_images": bool(prefs.get("block_images", False)),
        "vpn_enabled": bool(prefs.get("vpn_enabled", False)),
        "tor_enabled": bool(prefs.get("tor_enabled", False)),
        "mode": prefs.get("mode", "smart"),
    }
    if merged["mode"] not in {"strict", "smart", "direct"}:
        merged["mode"] = "smart"
    return merged

def save_browser_prefs(prefs: dict) -> None:
    save_json(PREFS_FILE, prefs)



ASSET_HISTORY_EXTENSIONS = {
    ".js", ".mjs", ".css", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot", ".map", ".json", ".webmanifest", ".xml",
    ".mp4", ".webm", ".mp3", ".wav", ".ogg", ".avi", ".mov", ".m4a", ".zip", ".gz", ".rar", ".7z", ".bin"
}
HISTORY_IGNORE_HOSTS = {
    "github.githubassets.com", "githubusercontent.com", "fonts.gstatic.com", "fonts.googleapis.com",
    "www.googletagmanager.com", "ssl.google-analytics.com", "google-analytics.com"
}

def should_track_history(url: str, content_type: str = "") -> bool:
    try:
        split = urllib.parse.urlsplit(url)
        if split.scheme not in {"http", "https"}:
            return False
        host = (split.netloc or "").lower()
        if not host:
            return False
        if host in HISTORY_IGNORE_HOSTS or any(host.endswith("." + h) for h in HISTORY_IGNORE_HOSTS):
            return False
        path = (split.path or "").lower()
        ext = Path(path).suffix.lower()
        if ext in ASSET_HISTORY_EXTENSIONS:
            return False
        ctype = (content_type or "").split(";", 1)[0].strip().lower()
        if ctype:
            if ctype.startswith("image/") or "javascript" in ctype or ctype in {"text/css", "application/json", "application/manifest+json", "image/svg+xml", "application/xml", "text/xml"}:
                return False
            if ctype in {"text/html", "application/xhtml+xml", "text/plain"} or ctype.startswith("application/pdf"):
                return True
        return ext in {"", ".html", ".htm", ".php", ".asp", ".aspx", ".jsp", ".md", ".pdf"}
    except Exception:
        return False

def clean_history_title(title: str, url: str) -> str:
    title = (title or "").strip()
    if title.startswith("[") and "] " in title:
        title = title.split("] ", 1)[1].strip()
    if not title or title == url:
        try:
            split = urllib.parse.urlsplit(url)
            host = split.netloc or url
            path = split.path.strip("/")
            return f"{host}/{path[:50]}" if path else host
        except Exception:
            return url
    return title[:120]

def history_items() -> List[dict]:
    raw = load_json(HISTORY_FILE, [])
    clean = []
    seen = set()
    changed = False
    for item in raw:
        if not isinstance(item, dict):
            changed = True
            continue
        url = strip_tracking((item.get("url") or "").strip())
        if not should_track_history(url):
            changed = True
            continue
        if url in seen:
            changed = True
            continue
        seen.add(url)
        clean.append({"url": url, "title": clean_history_title(item.get("title") or "", url), "ts": int(item.get("ts") or 0)})
    clean = clean[:40]
    if changed or clean != raw:
        save_json(HISTORY_FILE, clean)
    return clean

def add_history(url: str, title: str = "", content_type: str = "") -> None:
    url = strip_tracking((url or "").strip())
    if not should_track_history(url, content_type):
        return
    items = history_items()
    items = [x for x in items if x.get("url") != url]
    items.insert(0, {"url": url, "title": clean_history_title(title, url), "ts": int(time.time())})
    save_json(HISTORY_FILE, items[:40])

def add_bookmark(title: str, url: str) -> None:
    items = load_json(BOOKMARKS_FILE, [])
    items = [x for x in items if x.get("url") != url]
    items.insert(0, {"title": title or url, "url": url, "ts": int(time.time())})
    save_json(BOOKMARKS_FILE, items)


def strip_tracking(url: str) -> str:
    try:
        p = urllib.parse.urlsplit(url)
        q = urllib.parse.parse_qsl(p.query, keep_blank_values=True)
        q = [(k, v) for k, v in q if k.lower() not in TRACKING_PARAMS]
        return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, urllib.parse.urlencode(q, doseq=True), p.fragment))
    except Exception:
        return url


def is_blocked_url(url: str) -> bool:
    try:
        host = urllib.parse.urlsplit(url).netloc.lower()
    except Exception:
        return False
    if not host:
        return False
    for pattern in BLOCKED_HOST_PATTERNS:
        if pattern.startswith("adservice.google."):
            if host.startswith("adservice.google.") or host.endswith(".adservice.google.com"):
                return True
        elif host == pattern or host.endswith("." + pattern):
            return True
    return False


def local_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def tor_binary() -> Optional[str]:
    return which("tor")


def tor_running() -> bool:
    global TOR_PROCESS
    if TOR_PROCESS and TOR_PROCESS.poll() is None and local_port_open("127.0.0.1", TOR_SOCKS_PORT):
        return True
    if local_port_open("127.0.0.1", TOR_SOCKS_PORT):
        return True
    if TOR_PROCESS and TOR_PROCESS.poll() is not None:
        TOR_PROCESS = None
    return False


def pysocks_available() -> bool:
    try:
        import socks  # noqa: F401
        return True
    except Exception:
        return False


def install_tor_support() -> Tuple[bool, str]:
    if is_termux() and which("pkg") and not tor_binary():
        _run(["pkg", "update", "-y"])
        if not _run(["pkg", "install", "-y", "tor"]):
            return False, "Could not install tor with pkg."
    if not tor_binary():
        return False, "Tor binary not found. In Termux run: pkg install tor"
    if not pysocks_available():
        if not _run([sys.executable, "-m", "pip", "install", "--upgrade", "pysocks"]):
            return False, "Could not install PySocks. Run: pip install pysocks"
    return True, "Tor support ready."


def start_tor() -> Tuple[bool, str]:
    global TOR_PROCESS
    ok, msg = install_tor_support()
    if not ok:
        return False, msg
    if tor_running():
        return True, "Tor is already running."
    try:
        logf = open(TOR_STDOUT_PATH, "ab")
        TOR_PROCESS = subprocess.Popen(
            [tor_binary(), "--SocksPort", f"127.0.0.1:{TOR_SOCKS_PORT}", "--DataDirectory", str(TOR_DATA_DIR)],
            stdout=logf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, close_fds=True
        )
        for _ in range(40):
            if tor_running():
                return True, "Tor started on 127.0.0.1:9050."
            if TOR_PROCESS and TOR_PROCESS.poll() is not None:
                break
            time.sleep(0.5)
        return False, "Tor did not finish bootstrapping yet. Check tor.log in the browser data folder."
    except Exception as e:
        return False, f"Could not start Tor: {e}"


def stop_tor() -> Tuple[bool, str]:
    global TOR_PROCESS
    if TOR_PROCESS and TOR_PROCESS.poll() is None:
        try:
            TOR_PROCESS.terminate()
            TOR_PROCESS.wait(timeout=5)
        except Exception:
            try:
                TOR_PROCESS.kill()
            except Exception:
                pass
        TOR_PROCESS = None
        return True, "Tor stopped."
    return False, "Tor was not started by this app."


def tor_proxy_dict() -> Dict[str, str]:
    if not pysocks_available():
        raise RuntimeError("PySocks is missing. Open Browser settings and use Install/Start Tor.")
    return {"http": f"socks5h://127.0.0.1:{TOR_SOCKS_PORT}", "https": f"socks5h://127.0.0.1:{TOR_SOCKS_PORT}"}


def rewrite_html(raw_html: str, base_url: str, prefs: dict, embedded: bool = False) -> str:
    def repl(match):
        prefix, quote, value, suffix = match.groups()
        if not value:
            return match.group(0)
        if value.startswith(("javascript:", "data:", "mailto:", "tel:", "#")):
            return match.group(0)
        abs_url = urllib.parse.urljoin(base_url, value)
        abs_url = strip_tracking(abs_url)
        proxied = url_for("browser_open") + "?url=" + urllib.parse.quote(abs_url, safe="")
        if embedded:
            proxied += "&embed=1"
        return f"{prefix}{quote}{proxied}{suffix}"

    out = URL_ATTR_RE.sub(repl, raw_html)
    out = FORM_TAG_RE.sub(r'<form\1 enctype="multipart/form-data">', out)

    if prefs.get("adblock"):
        out = re.sub(r"(?is)<script[^>]+(?:doubleclick|googlesyndication|googletagmanager|google-analytics|adsystem|taboola|outbrain|criteo)[^>]*>.*?</script>", "", out)
        out = re.sub(r"(?is)<iframe[^>]+(?:doubleclick|googlesyndication|googletagmanager|adsystem|taboola|outbrain)[^>]*>.*?</iframe>", "", out)
        out = re.sub(r"(?is)<[^>]+(?:id|class)=['\"][^'\"]*(?:ad-|ads-|advert|advertisement|sponsor|sponsored|popup|promoted)[^'\"]*['\"][^>]*>.*?</[^>]+>", "", out)

    if prefs.get("lite"):
        out = re.sub(r"(?is)<script[^>]*>.*?</script>", "", out)
        out = re.sub(r"(?is)<link[^>]+rel=['\"](?:preload|prefetch|modulepreload)['\"][^>]*>", "", out)
        out = re.sub(r"(?is)<video[^>]*>.*?</video>", '<div style="padding:12px;border:1px solid rgba(191,151,255,.34);border-radius:14px;margin:10px 0;">Video hidden in Lite mode.</div>', out)

    if prefs.get("block_images"):
        out = re.sub(r"(?is)<img\b[^>]*>", '<div style="display:inline-block;padding:8px 10px;border:1px solid rgba(191,151,255,.34);border-radius:12px;font-size:12px;opacity:.8;">Image blocked</div>', out)

    if embedded:
        return out

    mini = f"""
    <style>
    #freeinternet-mini{{position:sticky;top:0;z-index:2147483000;padding:8px 10px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;border-bottom:1px solid rgba(191,151,255,.24);font:12px system-ui,sans-serif;background:rgba(11,8,17,.92);backdrop-filter:blur(10px);color:#f4f1fb}}
    #freeinternet-mini a{{color:inherit;text-decoration:none;padding:7px 10px;border-radius:10px;border:1px solid rgba(191,151,255,.20);background:rgba(255,255,255,.04)}}
    #freeinternet-mini .url{{opacity:.72;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:min(48vw,420px)}}
    @media (prefers-color-scheme: light){{#freeinternet-mini{{background:rgba(246,242,251,.92);color:#21172f}} #freeinternet-mini a{{background:rgba(255,255,255,.72)}}}}
    </style>
    <div id="freeinternet-mini">
      <a href="{url_for('browser_home')}">Browser</a>
      <a href="{url_for('browser_save_bookmark')}?url={urllib.parse.quote(base_url, safe='')}&title=Saved">Bookmark</a>
      <span class="url">{html.escape(base_url)}</span>
    </div>
    """
    body_idx = out.lower().find("<body")
    if body_idx != -1:
        close_idx = out.find(">", body_idx)
        if close_idx != -1:
            return out[:close_idx+1] + mini + out[close_idx+1:]
    return mini + out

def page_title_from_html(raw_html: str, fallback: str) -> str:
    m = TITLE_RE.search(raw_html or "")
    if m:
        t = html.unescape(m.group(1)).strip()
        return t[:120] or fallback
    return fallback


def reader_html(raw_html: str, url: str) -> str:
    title = page_title_from_html(raw_html, url)
    text = TEXT_CLEAN_RE.sub(" ", raw_html)
    text = re.sub(r'\s+', ' ', text).strip()
    paras = [text[i:i+1200] for i in range(0, len(text), 1200)] or ["No readable text found."]
    blocks = "".join(f"<p style='line-height:1.7;margin:0 0 16px 0;'>{html.escape(p)}</p>" for p in paras[:30])
    return f"""
    <html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>{html.escape(title)}</title></head>
    <body style='margin:0;background:#06040b;color:#f4edff;font-family:system-ui,sans-serif;'>
    <div style='max-width:900px;margin:0 auto;padding:18px;'>
      <div style='position:sticky;top:0;background:#06040b;padding:10px 0 18px;border-bottom:1px solid #5c3e82;margin-bottom:18px;'>
        <a href='{url_for('browser_open')}?url={urllib.parse.quote(url, safe='')}' style='color:#d7a6ff;text-decoration:none;'>← Back</a>
        <h1 style='margin:12px 0 0;font-size:24px;'>{html.escape(title)}</h1>
        <div style='font-size:13px;opacity:.75;word-break:break-all;'>{html.escape(url)}</div>
      </div>
      {blocks}
    </div></body></html>
    """


def fetch_proxies_from_proxyscrape_v4(country: str) -> List[str]:
    params = {
        "request": "display_proxies",
        "proxy_format": "protocolipport",
        "format": "json",
        "protocol": "http",
        "timeout": 10000,
        "country": (country or "all").lower(),
        "anonymity": "elite",
    }
    out: List[str] = []
    try:
        r = requests.get("https://api.proxyscrape.com/v4/free-proxy-list/get", params=params, timeout=12)
        data = r.json()
        for item in data.get("proxies", [])[:80]:
            ip = item.get("ip")
            port = item.get("port")
            proto = item.get("protocol") or "http"
            if ip and port and proto in {"http", "https"}:
                out.append(f"{proto}://{ip}:{port}")
    except Exception:
        pass
    return out


def fetch_proxies_from_proxyscrape_legacy(country: str) -> List[str]:
    params = {
        "protocol": "http",
        "country": country.upper(),
        "anonymity": "elite",
        "timeout": 10000,
        "format": "json",
    }
    items: List[str] = []
    try:
        r = requests.get(PROXY_API, params=params, timeout=12)
        data = r.json()
        for item in data.get("proxies", [])[:60]:
            ip = item.get("ip")
            port = item.get("port")
            proto = item.get("protocol") or "http"
            if ip and port and proto in {"http", "https"}:
                items.append(f"{proto}://{ip}:{port}")
    except Exception:
        pass
    return items


def fetch_proxies_from_geonode(country: str) -> List[str]:
    params = {
        "limit": 80,
        "page": 1,
        "sort_by": "lastChecked",
        "sort_type": "desc",
        "filterLastChecked": 90,
        "country": country.upper(),
        "protocols": "http,https",
    }
    out: List[str] = []
    try:
        r = requests.get("https://proxylist.geonode.com/api/proxy-list", params=params, timeout=12)
        data = r.json()
        for item in data.get("data", [])[:80]:
            ip = item.get("ip")
            port = item.get("port")
            protos = item.get("protocols") or []
            proto = "https" if "https" in protos else "http"
            if ip and port:
                out.append(f"{proto}://{ip}:{port}")
    except Exception:
        pass
    return out


def load_proxy_state() -> dict:
    state = load_json(PROXY_STATE_FILE, {})
    return state if isinstance(state, dict) else {}


def save_proxy_state(state: dict) -> None:
    save_json(PROXY_STATE_FILE, state)


def get_bad_proxy_map(country: str) -> dict:
    key = country.upper()
    state = load_proxy_state()
    bucket = state.get(key, {}) if isinstance(state.get(key, {}), dict) else {}
    now = int(time.time())
    cleaned = {proxy: int(expiry) for proxy, expiry in bucket.items() if int(expiry) > now}
    if cleaned != bucket:
        if cleaned:
            state[key] = cleaned
        elif key in state:
            del state[key]
        save_proxy_state(state)
    return cleaned


def mark_proxy_bad(country: str, proxy: str, ttl: int = BAD_PROXY_TTL) -> None:
    if not proxy:
        return
    state = load_proxy_state()
    key = country.upper()
    bucket = state.setdefault(key, {})
    bucket[proxy] = int(time.time()) + ttl
    save_proxy_state(state)


def mark_proxy_good(country: str, proxy: str) -> None:
    state = load_proxy_state()
    key = country.upper()
    bucket = state.get(key, {})
    if proxy in bucket:
        del bucket[proxy]
        if bucket:
            state[key] = bucket
        elif key in state:
            del state[key]
        save_proxy_state(state)


def fetch_proxy_pool(country: str, force_refresh: bool = False) -> List[str]:
    cache = load_json(PROXY_CACHE_FILE, {})
    key = country.upper()
    now = int(time.time())
    cached = cache.get(key)
    gathered: List[str] = []

    if (not force_refresh) and cached and now - int(cached.get("ts", 0)) < PROXY_CACHE_TTL:
        gathered = cached.get("items", [])
    else:
        seen = set()
        for loader in (fetch_proxies_from_proxyscrape_v4, fetch_proxies_from_geonode, fetch_proxies_from_proxyscrape_legacy):
            for proxy in loader(key):
                if proxy not in seen:
                    seen.add(proxy)
                    gathered.append(proxy)
        cache[key] = {"ts": now, "items": gathered}
        save_json(PROXY_CACHE_FILE, cache)

    bad = get_bad_proxy_map(key)
    usable = [proxy for proxy in gathered if proxy not in bad]

    if len(usable) < MIN_PROXY_POOL and not force_refresh:
        return fetch_proxy_pool(key, force_refresh=True)
    return usable


def direct_fetch(sess: requests.Session, method: str, url: str, *, data=None, files=None, stream=False):
    return sess.request(method, url, data=data, files=files, timeout=REQUEST_TIMEOUT, allow_redirects=True, stream=stream)


def proxied_fetch(sess: requests.Session, method: str, url: str, country: str, *, data=None, files=None, stream=False):
    key = country.upper()
    errors = []
    tried = set()
    bad_statuses = {403, 407, 429, 500, 502, 503, 504}

    for force_refresh in (False, True):
        proxies = fetch_proxy_pool(key, force_refresh=force_refresh)
        if not proxies:
            continue
        for proxy in proxies:
            if proxy in tried:
                continue
            tried.add(proxy)
            try:
                resp = sess.request(
                    method, url, data=data, files=files, timeout=REQUEST_TIMEOUT,
                    allow_redirects=True, stream=stream, proxies={"http": proxy, "https": proxy}
                )
                if resp.status_code in bad_statuses:
                    mark_proxy_bad(key, proxy)
                    errors.append(f"{proxy} -> HTTP {resp.status_code}")
                    continue
                mark_proxy_good(key, proxy)
                session["last_proxy"] = proxy
                return resp
            except Exception as e:
                mark_proxy_bad(key, proxy)
                errors.append(f"{proxy} -> {e}")
                if len(tried) >= MAX_PROXY_TRIES and not force_refresh:
                    break
        if len(tried) >= MAX_PROXY_TRIES and not force_refresh:
            continue

    session.pop("last_proxy", None)
    raise RuntimeError(errors[-1] if errors else "No working proxy. The app refreshed the pool automatically but did not find a live one yet.")


def tor_fetch(sess: requests.Session, method: str, url: str, *, data=None, files=None, stream=False):
    if not tor_running():
        ok, msg = start_tor()
        if not ok and not tor_running():
            raise RuntimeError(msg)
    return sess.request(method, url, data=data, files=files, timeout=max(REQUEST_TIMEOUT, 30), allow_redirects=True, stream=stream, proxies=tor_proxy_dict())


def browser_fetch(method: str, url: str, *, data=None, files=None, stream=False):
    prefs = browser_prefs()
    sess = browser_session()
    country = prefs.get("country", "US")
    vpn_enabled = bool(prefs.get("vpn_enabled", False))
    tor_enabled = bool(prefs.get("tor_enabled", False))
    mode = prefs.get("mode", "smart")

    if not vpn_enabled or mode == "direct":
        session.pop("last_proxy", None)
        return direct_fetch(sess, method, url, data=data, files=files, stream=stream), "direct"

    if tor_enabled:
        try:
            session.pop("last_proxy", None)
            return tor_fetch(sess, method, url, data=data, files=files, stream=stream), "tor"
        except Exception as e:
            if mode == "strict":
                raise RuntimeError(str(e))

    if mode == "strict":
        return proxied_fetch(sess, method, url, country, data=data, files=files, stream=stream), "proxy"

    proxy_error = None
    try:
        return proxied_fetch(sess, method, url, country, data=data, files=files, stream=stream), "proxy"
    except Exception as e:
        proxy_error = str(e)

    session.pop("last_proxy", None)
    resp = direct_fetch(sess, method, url, data=data, files=files, stream=stream)
    if proxy_error:
        resp.headers["X-Free-Internet-Fallback"] = "proxy-refresh-failed"
    return resp, "direct"

# ---------------- vault ----------------
def db_connect() -> sqlite3.Connection:
    prefs = browser_prefs()
    sess = browser_session()
    mode = prefs.get("mode", "smart")
    if mode == "direct":
        return direct_fetch(sess, method, url, data=data, files=files, stream=stream), "direct"
    if mode == "strict":
        return proxied_fetch(sess, method, url, prefs.get("country", "US"), data=data, files=files, stream=stream), "proxy"
    try:
        return proxied_fetch(sess, method, url, prefs.get("country", "US"), data=data, files=files, stream=stream), "proxy"
    except Exception:
        return direct_fetch(sess, method, url, data=data, files=files, stream=stream), "direct"

# ---------------- vault ----------------
def db_connect() -> sqlite3.Connection:
    con = sqlite3.connect(str(VAULT_DB))
    con.row_factory = sqlite3.Row
    return con


def init_vault_db() -> None:
    con = db_connect()
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v BLOB NOT NULL)")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            username_enc TEXT,
            password_enc TEXT,
            notes_enc TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """
    )
    con.commit()
    con.close()


def meta_get(key: str) -> Optional[bytes]:
    con = db_connect()
    row = con.execute("SELECT v FROM meta WHERE k=?", (key,)).fetchone()
    con.close()
    return row[0] if row else None


def meta_set(key: str, value: bytes) -> None:
    con = db_connect()
    con.execute("INSERT INTO meta(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (key, value))
    con.commit()
    con.close()


def vault_configured() -> bool:
    return bool(meta_get("pw_salt") and meta_get("pw_hash"))


def pbkdf2_hash(password: str, salt: bytes, iterations: int = 260_000) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


def set_vault_password(password: str) -> None:
    salt = os.urandom(16)
    meta_set("pw_salt", salt)
    meta_set("pw_hash", pbkdf2_hash(password, salt))


def verify_vault_password(password: str) -> bool:
    salt = meta_get("pw_salt")
    digest = meta_get("pw_hash")
    if not salt or not digest:
        return False
    return hmac.compare_digest(digest, pbkdf2_hash(password, salt))


def vault_encrypt(master: str, text: str) -> Optional[str]:
    text = (text or "").strip()
    if not text:
        return None
    env = os.environ.copy()
    env["FS_PASS"] = master
    res = subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-salt", "-a", "-A", "-pass", "env:FS_PASS"],
        input=text.encode("utf-8"), capture_output=True, env=env, check=False
    )
    if res.returncode != 0:
        raise RuntimeError(res.stderr.decode("utf-8", "ignore") or "Encryption failed")
    return res.stdout.decode("utf-8").strip()


def vault_decrypt(master: str, token: Optional[str]) -> str:
    if not token:
        return ""
    env = os.environ.copy()
    env["FS_PASS"] = master
    res = subprocess.run(
        ["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-a", "-A", "-pass", "env:FS_PASS"],
        input=token.encode("utf-8"), capture_output=True, env=env, check=False
    )
    if res.returncode != 0:
        raise RuntimeError(res.stderr.decode("utf-8", "ignore") or "Decryption failed")
    return res.stdout.decode("utf-8", "ignore")


def vault_master() -> Optional[str]:
    cid = get_client_id()
    return VAULT_KEYS.get(cid)


def vault_unlocked() -> bool:
    return bool(vault_master())

# ---------------- UI ----------------
BASE_HTML = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{{ app_title }} · {{ title }}</title>
<style>
:root{
  color-scheme: dark;
  --bg:#09070e;
  --bg2:#110d19;
  --surface:rgba(255,255,255,.04);
  --surface-2:rgba(255,255,255,.06);
  --line:rgba(191,151,255,.16);
  --line-strong:rgba(191,151,255,.34);
  --text:#f7f3ff;
  --muted:rgba(247,243,255,.70);
  --accent:#b884ff;
  --accent-soft:rgba(184,132,255,.16);
  --danger:#ff7f9f;
  --shadow:0 18px 48px rgba(0,0,0,.34);
  --radius:22px;
  --radius-sm:14px;
  --header-bg:rgba(9,7,14,.86);
  --dock-bg:rgba(11,8,17,.94);
}
@media (prefers-color-scheme: light){
  :root{
    color-scheme: light;
    --bg:#f6f2fb;
    --bg2:#efe8f9;
    --surface:rgba(255,255,255,.74);
    --surface-2:rgba(255,255,255,.92);
    --line:rgba(125,81,173,.14);
    --line-strong:rgba(125,81,173,.28);
    --text:#21172f;
    --muted:rgba(33,23,47,.68);
    --accent:#8e58da;
    --accent-soft:rgba(142,88,218,.12);
    --danger:#d94874;
    --shadow:0 12px 32px rgba(56,33,84,.10);
    --header-bg:rgba(246,242,251,.86);
    --dock-bg:rgba(246,242,251,.96);
  }
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0;
  min-height:100vh;
  color:var(--text);
  font:15px/1.45 system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;
  background:
    radial-gradient(860px 520px at 12% -10%, rgba(158,95,255,.14), transparent 56%),
    radial-gradient(860px 560px at 100% 0%, rgba(84,71,255,.08), transparent 52%),
    linear-gradient(180deg, var(--bg), var(--bg2));
}
a{text-decoration:none;color:inherit}
button,input,select,textarea{font:inherit}
header{position:sticky;top:0;z-index:40;backdrop-filter:blur(14px);background:var(--header-bg);border-bottom:1px solid var(--line)}
.shell{max-width:1040px;margin:0 auto;padding:12px 16px}
.topbar{display:flex;align-items:center;justify-content:space-between;gap:12px}
.title{font-weight:900;letter-spacing:.12em;text-transform:uppercase;font-size:17px;white-space:nowrap}
.nav{display:flex;gap:8px;align-items:center;overflow:auto;scrollbar-width:none}
.nav::-webkit-scrollbar{display:none}
.nav a,.btn,.miniBtn{border:1px solid var(--line);background:var(--surface);color:var(--text);box-shadow:inset 0 1px 0 rgba(255,255,255,.03)}
.nav a,.btn{min-height:40px;padding:10px 14px;border-radius:14px;display:inline-flex;align-items:center;justify-content:center;white-space:nowrap;transition:border-color .16s ease,background .16s ease,transform .16s ease}
.nav a:hover,.btn:hover,.miniBtn:hover{border-color:var(--line-strong);background:var(--surface-2);transform:translateY(-1px)}
.nav a.is-on,.mobileNav a.is-on{background:var(--accent-soft);border-color:rgba(184,132,255,.42)}
.main{max-width:1040px;margin:0 auto;padding:16px 16px 28px}
.hero,.card,.site,.kpi{border:1px solid var(--line);background:linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02));border-radius:var(--radius);box-shadow:var(--shadow)}
.hero{padding:22px}
.card{padding:18px}
.site,.kpi{padding:14px;border-radius:18px}
.flash{margin-bottom:14px;padding:12px 14px;border-radius:14px;border:1px solid var(--line-strong);background:var(--accent-soft)}
h1,h2,h3{line-height:1.06;margin:0} h1{font-size:clamp(28px,4vw,40px)} h2{font-size:22px} h3{font-size:18px}
.muted{color:var(--muted)} .small{font-size:12px} .mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.stack{display:grid;gap:14px} .row{display:flex;gap:10px;align-items:center;flex-wrap:wrap} .row.spread{justify-content:space-between}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.grid2{display:grid;gap:14px;grid-template-columns:repeat(2,minmax(0,1fr))}
.grid3{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(180px,1fr))}
.cards{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}
.sep{height:1px;background:var(--line);margin:14px 0}
.pillRow{display:flex;gap:8px;flex-wrap:wrap}
.badge{padding:6px 10px;border-radius:999px;border:1px solid var(--line);background:rgba(255,255,255,.035);font-size:12px;white-space:nowrap}
.quicklinks{display:flex;gap:10px;flex-wrap:wrap}
.quicklinks a,.miniBtn{padding:10px 12px;border-radius:12px;display:inline-flex;align-items:center;justify-content:center}
.btn.primary{background:var(--accent-soft);border-color:rgba(184,132,255,.42)} .btn.danger{background:rgba(255,127,159,.10);border-color:rgba(255,127,159,.34)}
.sectionTitle{display:flex;gap:12px;align-items:flex-start;justify-content:space-between;flex-wrap:wrap}
.sectionTitle > div{min-width:0}
label{display:block;font-weight:760;font-size:13px;margin:10px 0 8px}
input,select,textarea{width:100%;min-width:0;padding:13px 14px;border-radius:14px;border:1px solid var(--line);background:var(--surface);color:var(--text);outline:none}
input:focus,select:focus,textarea:focus{border-color:var(--line-strong);background:var(--surface-2)}
textarea{min-height:120px;resize:vertical}
.kpiNum{font-size:34px;font-weight:900;line-height:1.05;margin-top:6px}
.listClean{display:grid;gap:10px}
.tinyActions{display:flex;gap:8px;flex-wrap:wrap}
.tinyActions a,.tinyActions button{padding:8px 10px;border-radius:12px;border:1px solid var(--line);background:var(--surface);color:var(--text)}
.toggleRow label{display:flex;gap:12px;align-items:flex-start;padding:14px;border-radius:18px;border:1px solid var(--line);background:linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02));margin:0}
.toggleRow input{width:18px;height:18px;accent-color:var(--accent);margin-top:2px}
.mobileDock{display:none}
@media (max-width:760px){
  .shell{padding:10px 14px}
  .title{font-size:16px;letter-spacing:.10em}
  .nav{display:none}
  .main{padding:14px 14px calc(88px + env(safe-area-inset-bottom))}
  .hero,.card{padding:16px}
  .grid2{grid-template-columns:1fr}
  .grid3{grid-template-columns:1fr 1fr}
  .quicklinks a,.miniBtn,.btn{flex:1 1 calc(50% - 10px);min-height:40px}
  .row > input[style], .row > input, form.row input{min-width:0 !important;flex:1 1 100%}
  .row > .btn, form.row > .btn, form.row > a.btn{flex:1 1 calc(50% - 10px)}
  .mobileDock{display:block;position:fixed;left:12px;right:12px;bottom:max(10px, env(safe-area-inset-bottom));z-index:50;padding:8px;border-radius:18px;border:1px solid var(--line-strong);background:var(--dock-bg);box-shadow:0 18px 44px rgba(0,0,0,.20);backdrop-filter:blur(12px)}
  .mobileNav{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}
  .mobileNav a{min-height:38px;padding:8px 6px;border-radius:12px;border:1px solid var(--line);background:var(--surface);text-align:center;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
}
</style>
</head>
<body>
<header>
  <div class="shell topbar">
    <div class="title">{{ app_title }}</div>
    <nav class="nav">
      <a class="{% if request.path == '/' %}is-on{% endif %}" href="{{ url_for('home') }}">Hub</a>
      <a class="{% if request.path.startswith('/browser') and not request.path.startswith('/browser/settings') %}is-on{% endif %}" href="{{ url_for('browser_home') }}">Browser</a>
      <a class="{% if request.path.startswith('/vault') %}is-on{% endif %}" href="{{ url_for('vault_home') }}">Vault</a>
      <a class="{% if request.path.startswith('/tools') %}is-on{% endif %}" href="{{ url_for('tools_home') }}">Tools</a>
      <a class="{% if request.path.startswith('/browser/settings') %}is-on{% endif %}" href="{{ url_for('browser_settings') }}">Settings</a>
      <a class="{% if request.path == '/about' %}is-on{% endif %}" href="{{ url_for('about') }}">About</a>
    </nav>
  </div>
</header>
<main class="main">
{% with messages = get_flashed_messages() %}{% if messages %}{% for m in messages %}<div class="flash">{{ m }}</div>{% endfor %}{% endif %}{% endwith %}
{{ body|safe }}
</main>
<div class="mobileDock">
  <nav class="mobileNav">
    <a class="{% if request.path == '/' %}is-on{% endif %}" href="{{ url_for('home') }}">Hub</a>
    <a class="{% if request.path.startswith('/browser') and not request.path.startswith('/browser/settings') %}is-on{% endif %}" href="{{ url_for('browser_home') }}">Browser</a>
    <a class="{% if request.path.startswith('/vault') %}is-on{% endif %}" href="{{ url_for('vault_home') }}">Vault</a>
    <a class="{% if request.path.startswith('/browser/settings') %}is-on{% endif %}" href="{{ url_for('browser_settings') }}">Settings</a>
  </nav>
</div>
</body>
</html>
"""

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
init_vault_db()

# ---------------- shared helpers ----------------
def render_page(title: str, body: str):
    return render_template_string(BASE_HTML, title=title, app_title=APP_TITLE, body=body)


def absolute_or_search(text: str, engine: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', text):
        return strip_tracking(text)
    if "." in text and " " not in text:
        return strip_tracking("https://" + text)
    template = SEARCH_ENGINES.get(engine, SEARCH_ENGINES["google"])[1]
    return template.format(q=urllib.parse.quote(text))


def require_vault():
    if not vault_unlocked():
        return redirect(url_for("vault_login"))
    return None

# ---------------- routes: home/about ----------------

@app.route("/")
def home():
    prefs = browser_prefs()
    bookmarks_count = len(load_json(BOOKMARKS_FILE, []))
    history_count = len(history_items())
    saved_files = sorted(DOWNLOADS_DIR.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)[:4]
    con = db_connect()
    vault_count = con.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
    con.close()
    body = render_template_string(
        """
        <section class="hero stack">
          <div class="sectionTitle">
            <div>
              <div class="muted small">Home</div>
              <h1>Open what you need.</h1>
              <div class="muted">One local hub for browsing and your vault, without heavy packages.</div>
            </div>
          </div>
          <form class="row" action="{{ url_for('browser_open') }}" method="get" id="searchbox">
            <input name="url" placeholder="https://example.com or search words" style="flex:1;min-width:240px" required>
            <button class="btn primary" type="submit">Open</button>
            <a class="btn" href="{{ url_for('vault_home') }}">Vault</a>
            <a class="btn" href="{{ url_for('tools_home') }}">Tools</a>
          </form>
          <div class="quicklinks">
            <a class="miniBtn" href="{{ url_for('browser_open') }}?url=https%3A%2F%2Fgithub.com">GitHub</a>
            <a class="miniBtn" href="{{ url_for('browser_open') }}?url=https%3A%2F%2Fwww.youtube.com">YouTube</a>
            <a class="miniBtn" href="{{ url_for('browser_open') }}?url=https%3A%2F%2Fwww.wikipedia.org">Wikipedia</a>
            <a class="miniBtn" href="{{ url_for('browser_open') }}?url=https%3A%2F%2Freddit.com">Reddit</a>
          </div>
        </section>

        <div class="grid3" style="margin-top:14px;">
          <div class="kpi"><div class="muted small">Bookmarks</div><div class="kpiNum">{{ bookmarks_count }}</div></div>
          <div class="kpi"><div class="muted small">History</div><div class="kpiNum">{{ history_count }}</div></div>
          <div class="kpi"><div class="muted small">Vault entries</div><div class="kpiNum">{{ vault_count }}</div></div>
        </div>

        <div class="grid2" style="margin-top:14px;">
          <section class="card stack">
            <div class="sectionTitle"><h2>Browser</h2><a class="btn" href="{{ url_for('browser_settings') }}">Settings</a></div>
            <div class="pillRow">
              <span class="badge">{{ 'VPN enabled' if prefs.vpn_enabled else 'Direct by default' }}</span>
              <span class="badge">{{ countries[prefs.country] }}</span>
              <span class="badge">{{ engines[prefs.engine][0] }}</span>
              {% if prefs.adblock %}<span class="badge">Ad blocker</span>{% endif %}
            </div>
            <div class="row">
              <a class="btn primary" href="{{ url_for('browser_home') }}">Open browser</a>
              <a class="btn" href="{{ url_for('browser_compare') }}">Compare</a>
              <a class="btn" href="{{ url_for('browser_downloads') }}">Saved pages</a>
            </div>
          </section>

          <section class="card stack">
            <div class="sectionTitle"><h2>Recent saved pages</h2><a class="btn" href="{{ url_for('vault_home') }}">Open vault</a></div>
            {% if saved_files %}
              <div class="listClean">
                {% for f in saved_files %}
                  <div class="site row spread"><div><b>{{ f.name }}</b><div class="muted small">{{ (f.stat().st_size / 1024)|round(1) }} KB</div></div></div>
                {% endfor %}
              </div>
            {% else %}
              <div class="muted">No saved pages yet.</div>
            {% endif %}
          </section>
        </div>
        """,
        prefs=prefs, countries=COUNTRIES, engines=SEARCH_ENGINES,
        bookmarks_count=bookmarks_count, history_count=history_count,
        vault_count=vault_count, saved_files=saved_files,
    )
    return render_page("Home", body)

@app.route("/about")
def about():
    body = """
    <section class='card stack'>
      <h1 style='font-size:32px'>About</h1>
      <div class='muted'>Free Internet is a local browser and vault for Termux. Data lives in <code>~/Free Internet</code>.</div>
      <div class='grid3'>
        <div class='site'><b>Browser</b><div class='muted'>Search, proxy routing, Tor option, bookmarks, history, saved pages, and website screenshots.</div></div>
        <div class='site'><b>Vault</b><div class='muted'>Encrypted entries powered by the OpenSSL CLI.</div></div>
        <div class='site'><b>Packages</b><div class='muted'>Python: flask + requests. Screenshots use your browser and save PNG files locally.</div></div>
      </div>
    </section>
    """
    return render_page("About", body)



@app.route("/tools")
@app.route("/tools/")
def tools_home():
    target = (request.args.get("url") or "").strip()
    width = request.args.get("width", "mobile")
    width_map = {"mobile": 430, "tablet": 768, "desktop": 1280}
    if width not in width_map:
        width = "mobile"
    frame_width = width_map[width]
    captures = sorted(SCREENSHOT_DIR.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)[:12]
    body = render_template_string(
        """
        <section class="hero stack">
          <div class="sectionTitle">
            <div>
              <div class="muted small">Tools</div>
              <h1>Capture a full-page screenshot.</h1>
              <div class="muted">Open a link in a clean embedded browser view, then save the whole page as a PNG.</div>
            </div>
            <a class="btn" href="{{ url_for('browser_home') }}">Browser</a>
          </div>

          <form class="row" method="get" action="{{ url_for('tools_home') }}">
            <input name="url" value="{{ target }}" placeholder="https://example.com" style="flex:1;min-width:240px" required>
            <select name="width" style="max-width:170px">
              <option value="mobile" {% if width == 'mobile' %}selected{% endif %}>Mobile</option>
              <option value="tablet" {% if width == 'tablet' %}selected{% endif %}>Tablet</option>
              <option value="desktop" {% if width == 'desktop' %}selected{% endif %}>Desktop</option>
            </select>
            <button class="btn primary" type="submit">Preview</button>
          </form>

          {% if target %}
            <div class="card stack">
              <div class="row spread">
                <div>
                  <div class="muted small">Preview</div>
                  <div class="small mono" style="word-break:break-all">{{ target }}</div>
                </div>
                <div class="row">
                  <a class="btn" target="_blank" rel="noreferrer" href="{{ url_for('browser_open') }}?url={{ target|urlencode }}">Open live</a>
                  <button class="btn primary" type="button" onclick="captureFullPage()">Capture PNG</button>
                </div>
              </div>

              <div id="shotStatus" class="muted small">Load the preview, then tap Capture PNG.</div>

              <div style="overflow:auto;border:1px solid var(--line);border-radius:18px;background:rgba(0,0,0,.16);padding:10px;">
                <div style="width:{{ frame_width }}px;max-width:none;margin:0 auto;border:1px solid var(--line);border-radius:16px;overflow:hidden;background:#fff;">
                  <iframe id="shotFrame"
                          src="{{ url_for('browser_open') }}?url={{ target|urlencode }}&embed=1"
                          style="display:block;width:{{ frame_width }}px;height:720px;border:0;background:#fff"></iframe>
                </div>
              </div>

              <form id="captureForm" method="post" action="{{ url_for('tools_save_screenshot') }}">
                <input type="hidden" name="source_url" value="{{ target }}">
                <input type="hidden" name="width_mode" value="{{ width }}">
                <input type="hidden" name="image_data" id="image_data">
                <input type="hidden" name="page_title" id="page_title">
              </form>
            </div>
          {% endif %}
        </section>

        <section class="card stack" style="margin-top:14px;">
          <div class="sectionTitle">
            <div>
              <div class="muted small">Saved</div>
              <h2>Recent captures</h2>
            </div>
          </div>
          {% if captures %}
            <div class="cards">
              {% for cap in captures %}
                <div class="site stack">
                  <div style="aspect-ratio:16/10;border-radius:14px;overflow:hidden;border:1px solid var(--line);background:rgba(255,255,255,.03)">
                    <img src="{{ url_for('tools_get_screenshot', filename=cap.name) }}" alt="" style="width:100%;height:100%;object-fit:cover;display:block">
                  </div>
                  <div style="font-weight:800;word-break:break-word">{{ cap.name }}</div>
                  <div class="muted small">{{ (cap.stat().st_size / 1024)|round(1) }} KB</div>
                  <div class="tinyActions">
                    <a href="{{ url_for('tools_get_screenshot', filename=cap.name) }}" target="_blank">Open</a>
                    <a href="{{ url_for('tools_get_screenshot', filename=cap.name) }}?download=1">Download</a>
                    <form method="post" action="{{ url_for('tools_delete_screenshot', filename=cap.name) }}" style="display:inline">
                      <button type="submit">Delete</button>
                    </form>
                  </div>
                </div>
              {% endfor %}
            </div>
          {% else %}
            <div class="muted">No screenshots yet.</div>
          {% endif %}
        </section>

        <script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
        <script>
        const frame = document.getElementById('shotFrame');
        const statusEl = document.getElementById('shotStatus');
        if(frame && statusEl){
          frame.addEventListener('load', () => {
            statusEl.textContent = 'Preview ready. Capture will save a full-page PNG.';
          });
        }
        async function captureFullPage(){
          const iframe = document.getElementById('shotFrame');
          const status = document.getElementById('shotStatus');
          if(!iframe){
            return;
          }
          try{
            status.textContent = 'Capturing...';
            const doc = iframe.contentDocument || iframe.contentWindow.document;
            const root = doc.documentElement;
            const pageTitle = (doc.title || '').trim() || 'capture';
            const width = Math.max(root.scrollWidth, doc.body ? doc.body.scrollWidth : 0, iframe.clientWidth, 430);
            const height = Math.max(root.scrollHeight, doc.body ? doc.body.scrollHeight : 0, iframe.clientHeight, 720);
            const canvas = await html2canvas(root, {
              useCORS: true,
              allowTaint: true,
              backgroundColor: null,
              scale: 1,
              width: width,
              height: height,
              windowWidth: width,
              windowHeight: height,
              scrollX: 0,
              scrollY: 0
            });
            document.getElementById('page_title').value = pageTitle;
            document.getElementById('image_data').value = canvas.toDataURL('image/png');
            document.getElementById('captureForm').submit();
          }catch(err){
            status.textContent = 'Could not capture this page in the browser.';
            alert(err);
          }
        }
        </script>
        """,
        target=target,
        width=width,
        frame_width=frame_width,
        captures=captures,
    )
    return render_page("Tools", body)


@app.route("/tools/screenshot/save", methods=["POST"])
def tools_save_screenshot():
    image_data = request.form.get("image_data", "").strip()
    source_url = strip_tracking(request.form.get("source_url", "").strip())
    width_mode = (request.form.get("width_mode") or "mobile").strip()
    page_title = (request.form.get("page_title") or "").strip()
    if not image_data.startswith("data:image/png;base64,"):
        flash("No screenshot image was received.")
        return redirect(url_for("tools_home", url=source_url, width=width_mode))
    try:
        raw = base64.b64decode(image_data.split(",", 1)[1])
    except Exception:
        flash("Screenshot data was invalid.")
        return redirect(url_for("tools_home", url=source_url, width=width_mode))
    host = urllib.parse.urlsplit(source_url).netloc or "capture"
    stem = safe_file_stem(f"{host}_{page_title}_{int(time.time())}", "capture")
    out = SCREENSHOT_DIR / f"{stem}.png"
    out.write_bytes(raw)
    flash(f"Screenshot saved as {out.name}.")
    return redirect(url_for("tools_home"))


@app.route("/tools/screenshot/<path:filename>")
def tools_get_screenshot(filename: str):
    path = (SCREENSHOT_DIR / filename).resolve()
    if path.parent != SCREENSHOT_DIR.resolve() or not path.exists():
        return Response("Not found", status=404)
    as_download = request.args.get("download") == "1"
    return send_file(path, mimetype="image/png", as_attachment=as_download, download_name=path.name)


@app.route("/tools/screenshot/delete/<path:filename>", methods=["POST"])
def tools_delete_screenshot(filename: str):
    path = (SCREENSHOT_DIR / filename).resolve()
    if path.parent == SCREENSHOT_DIR.resolve() and path.exists():
        try:
            path.unlink()
            flash("Screenshot deleted.")
        except Exception:
            flash("Could not delete screenshot.")
    return redirect(url_for("tools_home"))

# ---------------- routes: browser
# ---------------- routes: browser ----------------
# ---------------- routes: browser ----------------

@app.route("/browser")
@app.route("/browser/")
def browser_home():
    prefs = browser_prefs()
    all_bookmarks = load_json(BOOKMARKS_FILE, [])
    all_history = history_items()
    bookmarks = all_bookmarks[:4]
    history = all_history[:4]
    saved_files = sorted(DOWNLOADS_DIR.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)[:4]
    proxy_count = len(load_json(PROXY_CACHE_FILE, {}).get("proxies", [])) if prefs.get("vpn_enabled") else 0
    body = render_template_string(
        """
        <section class="hero stack">
          <div class="sectionTitle">
            <div>
              <div class="muted small">Browser</div>
              <h1>Browse cleanly.</h1>
              <div class="muted">Open a site, search, or capture a full-page screenshot with the current browser settings.</div>
            </div>
            <div class="row">
              <a class="btn" href="{{ url_for('tools_home') }}">Website screenshot</a>
              <a class="btn" href="{{ url_for('browser_settings') }}">Settings</a>
            </div>
          </div>

          <form class="row" action="{{ url_for('browser_open') }}" method="get" id="searchbox">
            <input name="url" placeholder="https://example.com or search words" style="flex:1;min-width:240px" required>
            <button class="btn primary" type="submit">Open</button>
            <a class="btn" href="{{ url_for('browser_compare') }}">Compare</a>
          </form>

          <div class="quicklinks">
            <a class="miniBtn" href="{{ url_for('browser_open') }}?url=https%3A%2F%2Fgithub.com">GitHub</a>
            <a class="miniBtn" href="{{ url_for('browser_open') }}?url=https%3A%2F%2Fwww.wikipedia.org">Wikipedia</a>
            <a class="miniBtn" href="{{ url_for('browser_open') }}?url=https%3A%2F%2Freddit.com">Reddit</a>
            <a class="miniBtn" href="{{ url_for('browser_open') }}?url=https%3A%2F%2Fnews.ycombinator.com">HN</a>
          </div>

          <div class="pillRow">
            <span class="badge">{{ 'VPN on' if prefs.vpn_enabled else 'VPN off' }}</span>
            <span class="badge">{{ 'Tor on' if prefs.tor_enabled and tor_on else 'Tor off' }}</span>
            <span class="badge">{{ prefs.mode|title }}</span>
            <span class="badge">{{ engines[prefs.engine][0] }}</span>
            {% if prefs.vpn_enabled %}<span class="badge">{{ proxy_count }} proxies ready</span>{% endif %}
          </div>
        </section>

        <div class="grid3" style="margin-top:14px;">
          <div class="kpi"><div class="muted small">Bookmarks</div><div class="kpiNum">{{ all_bookmarks|length }}</div></div>
          <div class="kpi"><div class="muted small">History</div><div class="kpiNum">{{ all_history|length }}</div></div>
          <div class="kpi"><div class="muted small">Saved</div><div class="kpiNum">{{ saved_files|length }}</div></div>
        </div>

        <div class="grid2" style="margin-top:14px;">
          <section class="card stack">
            <div class="sectionTitle"><h2>Recent bookmarks</h2><a class="btn" href="{{ url_for('browser_downloads') }}">Saved pages</a></div>
            {% if bookmarks %}
              <div class="listClean">
              {% for b in bookmarks %}
                <div class="site stack">
                  <a href="{{ url_for('browser_open') }}?url={{ b.url|urlencode }}"><b>{{ b.title }}</b></a>
                  <div class="muted small mono">{{ b.url }}</div>
                  <div class="tinyActions">
                    <a href="{{ url_for('browser_open') }}?url={{ b.url|urlencode }}">Open</a>
                    <a href="{{ url_for('browser_delete_bookmark') }}?url={{ b.url|urlencode }}">Remove</a>
                  </div>
                </div>
              {% endfor %}
              </div>
            {% else %}
              <div class="muted">No bookmarks yet.</div>
            {% endif %}
          </section>

          <section class="card stack">
            <div class="sectionTitle"><h2>Recent history</h2><a class="btn danger" href="{{ url_for('browser_clear') }}">Clear</a></div>
            {% if history %}
              <div class="listClean">
              {% for h in history %}
                <div class="site stack">
                  <a href="{{ url_for('browser_open') }}?url={{ h.url|urlencode }}"><b>{{ h.title }}</b></a>
                  <div class="muted small mono">{{ h.url }}</div>
                </div>
              {% endfor %}
              </div>
            {% else %}<div class="muted">No page history yet.</div>{% endif %}
          </section>
        </div>

        <div class="card stack" style="margin-top:14px;">
          <div class="sectionTitle"><h2>Tools</h2></div>
          <div class="row">
            <a class="btn" href="{{ url_for('browser_proxy_refresh') }}">Refresh proxies</a>
            <a class="btn" href="{{ url_for('browser_update_tools') }}">Update tools</a>
            <a class="btn" href="{{ url_for('browser_downloads') }}">Files</a>
          </div>
        </div>
        """,
        prefs=prefs, countries=COUNTRIES, engines=SEARCH_ENGINES, tor_on=tor_running(),
        bookmarks=bookmarks, history=history, all_bookmarks=all_bookmarks, all_history=all_history,
        saved_files=saved_files, proxy_count=proxy_count,
    )
    return render_page("Browser", body)

@app.route("/browser/settings", methods=["GET", "POST"])
def browser_settings():
    prefs = browser_prefs()
    if request.method == "POST":
        prefs["engine"] = request.form.get("engine", "google") if request.form.get("engine") in SEARCH_ENGINES else "google"
        prefs["country"] = request.form.get("country", "US") if request.form.get("country") in COUNTRIES else "US"
        prefs["mode"] = request.form.get("mode", "smart") if request.form.get("mode") in {"strict", "smart", "direct"} else "smart"
        prefs["adblock"] = bool(request.form.get("adblock"))
        prefs["lite"] = bool(request.form.get("lite"))
        prefs["block_images"] = bool(request.form.get("block_images"))
        prefs["vpn_enabled"] = bool(request.form.get("vpn_enabled"))
        prefs["tor_enabled"] = bool(request.form.get("tor_enabled"))
        save_browser_prefs(prefs)
        if prefs["tor_enabled"]:
            ok, msg = start_tor()
            flash(msg)
        else:
            stop_tor()
        flash("Browser settings saved.")
        return redirect(url_for("browser_settings"))
    proxy_pool_size = len(fetch_proxy_pool(prefs.get("country", "US"))) if prefs.get("vpn_enabled") else 0
    body = render_template_string(
        """
        <section class="hero stack">
          <div>
            <div class="muted small">Settings</div>
            <h1>Keep it simple.</h1>
            <div class="muted">VPN starts off by default. Enable only what you want, then save.</div>
          </div>

          <form method="post" class="stack">
            <div class="grid3">
              <div><label>Search engine</label><select name="engine">{% for k,v in engines.items() %}<option value="{{ k }}" {% if prefs.engine == k %}selected{% endif %}>{{ v[0] }}</option>{% endfor %}</select></div>
              <div><label>Proxy country</label><select name="country">{% for k,v in countries.items() %}<option value="{{ k }}" {% if prefs.country == k %}selected{% endif %}>{{ v }}</option>{% endfor %}</select></div>
              <div><label>VPN mode</label><select name="mode"><option value="smart" {% if prefs.mode=='smart' %}selected{% endif %}>Smart</option><option value="strict" {% if prefs.mode=='strict' %}selected{% endif %}>Strict proxy</option><option value="direct" {% if prefs.mode=='direct' %}selected{% endif %}>Direct only</option></select></div>
            </div>

            <div class="grid2 toggleRow">
              <label><input type="checkbox" name="vpn_enabled" {% if prefs.vpn_enabled %}checked{% endif %}><span><b>Enable VPN routing</b><br><span class="muted small">Use proxies when routing is enabled.</span></span></label>
              <label><input type="checkbox" name="tor_enabled" {% if prefs.tor_enabled %}checked{% endif %}><span><b>Enable Tor routing</b><br><span class="muted small">Tor installs and starts automatically when enabled.</span></span></label>
              <label><input type="checkbox" name="adblock" {% if prefs.adblock %}checked{% endif %}><span><b>Enable ad blocker</b><br><span class="muted small">Block common ad and tracker requests.</span></span></label>
              <label><input type="checkbox" name="lite" {% if prefs.lite %}checked{% endif %}><span><b>Enable lite mode</b><br><span class="muted small">Remove heavier page parts when possible.</span></span></label>
              <label><input type="checkbox" name="block_images" {% if prefs.block_images %}checked{% endif %}><span><b>Block images</b><br><span class="muted small">Useful when speed or data matters more.</span></span></label>
            </div>

            <div class="card stack">
              <div class="pillRow">
                <span class="badge">{{ 'VPN enabled' if prefs.vpn_enabled else 'VPN off' }}</span>
                <span class="badge">{{ 'Tor running' if tor_on else 'Tor off' }}</span>
                <span class="badge">{{ proxy_pool_size }} cached proxies</span>
              </div>
              <div class="row">
                <a class="btn" href="{{ url_for('browser_proxy_refresh') }}">Refresh proxies</a>
                <a class="btn" href="{{ url_for('browser_update_tools') }}">Update browser tools</a>
                <a class="btn danger" href="{{ url_for('browser_clear') }}">Clear browser data</a>
                {% if tor_on %}<a class="btn danger" href="{{ url_for('browser_tor_stop') }}">Stop Tor</a>{% endif %}
              </div>
            </div>

            <div class="row">
              <button class="btn primary" type="submit">Save settings</button>
              <a class="btn" href="{{ url_for('browser_home') }}">Back</a>
            </div>
          </form>
        </section>
        """,
        prefs=prefs, countries=COUNTRIES, engines=SEARCH_ENGINES, tor_on=tor_running(), proxy_pool_size=proxy_pool_size
    )
    return render_page("Browser settings", body)

@app.route("/browser/toggle/<key>")
def browser_toggle(key: str):
    prefs = browser_prefs()
    if key in {"adblock", "lite", "block_images", "vpn_enabled", "tor_enabled"}:
        prefs[key] = not bool(prefs.get(key))
        save_browser_prefs(prefs)
        flash(f"{key.replace('_', ' ').title()} {'enabled' if prefs[key] else 'disabled'}.")
    return redirect(request.referrer or url_for("browser_home"))

@app.route("/browser/mode/<mode>")
def browser_set_mode(mode: str):
    prefs = browser_prefs()
    if mode in {"strict", "smart", "direct"}:
        prefs["mode"] = mode
        save_browser_prefs(prefs)
        flash(f"Browser mode set to {mode}.")
    return redirect(request.referrer or url_for("browser_home"))

@app.route("/browser/proxy/refresh")
def browser_proxy_refresh():
    prefs = browser_prefs()
    cache = load_json(PROXY_CACHE_FILE, {})
    cache.pop(prefs.get("country", "US").upper(), None)
    save_json(PROXY_CACHE_FILE, cache)
    count = len(fetch_proxy_pool(prefs.get("country", "US")))
    flash(f"Proxy pool refreshed. {count} proxies cached for {prefs.get('country', 'US')}.")
    return redirect(request.referrer or url_for("browser_settings"))

@app.route("/browser/update_tools")
def browser_update_tools():
    msgs = []
    if is_termux() and which("pkg"):
        _run(["pkg", "update", "-y"])
        _run(["pkg", "install", "-y", "openssl", "tor"])
        msgs.append("Termux packages checked")
    if _run([sys.executable, "-m", "pip", "install", "--upgrade", "requests", "pysocks"]):
        msgs.append("Python packages updated")
    prefs = browser_prefs()
    count = len(fetch_proxy_pool(prefs.get("country", "US"), force_refresh=True))
    msgs.append(f"{count} proxies ready")
    if prefs.get("tor_enabled"):
        ok, msg = start_tor()
        msgs.append(msg)
    flash(" · ".join(msgs) or "Browser tools checked.")
    return redirect(request.referrer or url_for("browser_settings"))



@app.route("/browser/tor/start")
def browser_tor_start():
    prefs = browser_prefs()
    ok, msg = start_tor()
    if ok and (prefs.get("tor_autostart") or request.args.get("set_mode") == "1"):
        prefs["mode"] = "tor"
        save_browser_prefs(prefs)
    flash(msg)
    return redirect(request.referrer or url_for("browser_settings"))


@app.route("/browser/tor/stop")
def browser_tor_stop():
    ok, msg = stop_tor()
    flash(msg)
    return redirect(request.referrer or url_for("browser_settings"))


@app.route("/browser/clear")
def browser_clear():
    load_json(HISTORY_FILE, [])
    save_json(HISTORY_FILE, [])
    cid = get_client_id()
    if cid in BROWSER_CLIENTS:
        del BROWSER_CLIENTS[cid]
    flash("Browser cookies and history cleared.")
    return redirect(url_for("browser_home"))

@app.route("/browser/bookmark")
def browser_save_bookmark():
    url = strip_tracking(request.args.get("url", "").strip())
    title = (request.args.get("title") or url).strip()
    if url:
        add_bookmark(title, url)
        flash("Bookmark saved.")
    return redirect(request.referrer or url_for("browser_home"))

@app.route("/browser/bookmark/delete")
def browser_delete_bookmark():
    url = strip_tracking(request.args.get("url", "").strip())
    if url:
        items = [x for x in load_json(BOOKMARKS_FILE, []) if x.get("url") != url]
        save_json(BOOKMARKS_FILE, items)
        flash("Bookmark removed.")
    return redirect(request.referrer or url_for("browser_home"))

@app.route("/browser/history/delete")
def browser_delete_history():
    url = strip_tracking(request.args.get("url", "").strip())
    if url:
        items = [x for x in load_json(HISTORY_FILE, []) if x.get("url") != url]
        save_json(HISTORY_FILE, items)
        flash("History item removed.")
    return redirect(request.referrer or url_for("browser_home"))

@app.route("/browser/downloads")
def browser_downloads():
    files = sorted(DOWNLOADS_DIR.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
    body = render_template_string(
        """
        <section class="card stack">
          <div class="row" style="justify-content:space-between;"><h2 style="margin:0;">Saved pages & files</h2><a class="btn" href="{{ url_for('browser_home') }}">Back</a></div>
          {% if files %}
            <div class="listClean">
              {% for f in files %}
                <div class="site stack">
                  <b style="word-break:break-word">{{ f.name }}</b>
                  <div class="muted small">{{ (f.stat().st_size/1024)|round(1) }} KB</div>
                  <div class="tinyActions">
                    <a href="{{ url_for('browser_get_saved_file', filename=f.name) }}" target="_blank">Open</a>
                    <a href="{{ url_for('browser_get_saved_file', filename=f.name) }}?download=1">Download</a>
                  </div>
                </div>
              {% endfor %}
            </div>
            <div class="muted small">Files are stored in {{ downloads_dir }}</div>
          {% else %}
            <div class="muted">No saved pages or files yet.</div>
          {% endif %}
        </section>
        """, files=files, downloads_dir=str(DOWNLOADS_DIR)
    )
    return render_page("Saved pages", body)

@app.route("/browser/saved/<path:filename>")
def browser_get_saved_file(filename: str):
    path = (DOWNLOADS_DIR / filename).resolve()
    if path.parent != DOWNLOADS_DIR.resolve() or not path.exists():
        return Response("Not found", status=404)
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    as_download = request.args.get("download") == "1"
    return send_file(path, mimetype=mime, as_attachment=as_download, download_name=path.name)

@app.route("/browser/save_page")
def browser_save_page():
    raw_url = request.args.get("url", "")
    if not raw_url:
        flash("No page URL to save.")
        return redirect(url_for("browser_home"))
    target = strip_tracking(raw_url)
    try:
        resp, _route_mode = browser_fetch("GET", target, stream=True)
        ctype = resp.headers.get("Content-Type", "")
        stem = re.sub(r'[^a-zA-Z0-9._-]+', '_', (urllib.parse.urlsplit(target).netloc or 'page') + '_' + str(int(time.time())))[:80]
        ext = '.html' if 'text/html' in ctype else (mimetypes.guess_extension(ctype.split(';')[0].strip()) or '.bin')
        out = DOWNLOADS_DIR / f"{stem}{ext}"
        out.write_bytes(resp.content)
        flash(f"Saved to {out.name}.")
    except Exception as e:
        flash(f"Could not save page: {e}")
    return redirect(request.referrer or (url_for('browser_open') + '?url=' + urllib.parse.quote(target, safe='')))

@app.route("/browser/compare", methods=["GET", "POST"])
def browser_compare():
    if request.method == "POST":
        q = (request.form.get("q") or "").strip()
        if not q:
            flash("Enter a search query.")
            return redirect(url_for("browser_compare"))
        return redirect(url_for("browser_compare", q=q))
    q = (request.args.get("q") or "").strip()
    results = []
    if q:
        for key, value in SEARCH_ENGINES.items():
            target = value[1].format(q=urllib.parse.quote(q))
            results.append({"key": key, "name": value[0], "url": target})
    body = render_template_string(
        """
        <section class="hero stack">
          <h1 style="margin:0;">Compare search engines</h1>
          <div class="muted">Build the same query for every engine, then open the one you want inside the browser.</div>
          <form method="post" class="row"><input name="q" value="{{ q }}" placeholder="Search query" required><button class="btn primary" type="submit">Build links</button><a class="btn" href="{{ url_for('browser_home') }}">Back</a></form>
          {% if results %}
            <div class="cards">
              {% for r in results %}
                <div class="site stack"><b>{{ r.name }}</b><div class="muted small mono">{{ r.url }}</div><div class="row"><a class="btn primary" href="{{ url_for('browser_open') }}?url={{ r.url|urlencode }}">Open</a><a class="btn" href="{{ url_for('browser_save_bookmark') }}?url={{ r.url|urlencode }}&title={{ (r.name ~ ': ' ~ q)|urlencode }}">Bookmark</a></div></div>
              {% endfor %}
            </div>
          {% endif %}
        </section>
        """, q=q, results=results
    )
    return render_page("Compare search engines", body)

@app.route("/browser/open", methods=["GET", "POST"])
def browser_open():
    raw_url = request.args.get("url") or request.form.get("url") or ""
    prefs = browser_prefs()
    target = absolute_or_search(raw_url, prefs.get("engine", "google"))
    if not target:
        flash("Enter a URL or search.")
        return redirect(url_for("browser_home"))
    target = strip_tracking(target)

    if prefs.get("vpn_enabled") and prefs.get("tor_enabled") and not tor_running():
        start_tor()

    if prefs.get("adblock") and is_blocked_url(target):
        return Response("Blocked by ad blocker.", status=451, content_type="text/plain; charset=utf-8")

    method = request.method.upper()
    if method == "POST":
        data = request.form.to_dict(flat=False)
        data.pop("url", None)
        files = {}
        for name, storage in request.files.items():
            if storage and storage.filename:
                files[name] = (storage.filename, storage.stream.read(), storage.mimetype or mimetypes.guess_type(storage.filename)[0] or "application/octet-stream")
    else:
        data = request.args.to_dict(flat=False)
        data.pop("url", None)
        files = None
        if data:
            method = "GET"
            split = list(urllib.parse.urlsplit(target))
            existing_q = urllib.parse.parse_qsl(split[3], keep_blank_values=True)
            for k, values in data.items():
                for v in values:
                    existing_q.append((k, v))
            split[3] = urllib.parse.urlencode(existing_q, doseq=True)
            target = urllib.parse.urlunsplit(split)
            data = None

    try:
        resp, route_mode = browser_fetch(method, target, data=data if method == "POST" else None, files=files, stream=True)
    except Exception as e:
        body = f"<section class='card stack'><h2 style='margin:0;'>Browser error</h2><div class='muted'>{html.escape(str(e))}</div><div class='row'><a class='btn' href='{url_for('browser_home')}'>Back</a><a class='btn' href='{url_for('browser_settings')}'>Settings</a><a class='btn' href='{url_for('browser_tor_start')}'>Start Tor</a></div></section>"
        return render_page("Browser error", body), 502

    content_type = resp.headers.get("Content-Type", "")
    final_url = strip_tracking(resp.url or target)

    if prefs.get("adblock") and is_blocked_url(final_url):
        return Response("Blocked by ad blocker.", status=451, content_type="text/plain; charset=utf-8")

    if "text/html" in content_type:
        raw_html = resp.text
        title = page_title_from_html(raw_html, final_url)
        embedded = request.args.get("embed") == "1"
        fetch_dest = (request.headers.get("Sec-Fetch-Dest") or "").lower()
        should_log_nav = (not embedded) and (fetch_dest in {"", "document", "iframe"})
        if should_log_nav:
            add_history(final_url, title, content_type)
        if request.args.get("reader") == "1" and not embedded:
            return reader_html(raw_html, final_url)
        if request.args.get("source") == "1" and not embedded:
            source = html.escape(raw_html)
            page = f"<section class='card stack'><div class='row'><a class='btn' href='{url_for('browser_open')}?url={urllib.parse.quote(final_url, safe='')}'>Back</a></div><textarea class='mono' style='min-height:70vh'>{source}</textarea></section>"
            return render_page("View source", page)
        rewritten = rewrite_html(raw_html, final_url, prefs, embedded=embedded)
        return rewritten


    data_bytes = resp.content
    headers = {"Content-Type": content_type} if content_type else {}
    return Response(data_bytes, status=resp.status_code, headers=headers)

# ---------------- routes: vault ----------------
@app.route("/vault")
@app.route("/vault/")
def vault_home():
    if not vault_configured():
        return redirect(url_for("vault_setup"))
    if not vault_unlocked():
        return redirect(url_for("vault_login"))
    q = (request.args.get("q") or "").strip().lower()
    con = db_connect()
    rows = con.execute("SELECT * FROM entries ORDER BY updated_at DESC").fetchall()
    con.close()
    if q:
        rows = [r for r in rows if q in (r['title'] or '').lower() or q in (r['url'] or '').lower()]
    body = render_template_string(
        """
        <section class="hero stack">
          <div class="row" style="justify-content:space-between;align-items:flex-start;">
            <div><h1 style="margin:0 0 8px 0;">Vault</h1><div class="muted">Local encrypted vault.</div></div>
            <div class="row"><a class="btn primary" href="{{ url_for('vault_add') }}">Add entry</a><a class="btn" href="{{ url_for('vault_settings') }}">Settings</a><a class="btn danger" href="{{ url_for('vault_logout') }}">Lock</a></div>
          </div>
          <form class="row" method="get" action="{{ url_for('vault_home') }}">
            <input name="q" value="{{ q }}" placeholder="Search title or URL..." style="flex:1;min-width:240px;">
            <button class="btn primary" type="submit">Search</button>
            <a class="btn" href="{{ url_for('vault_home') }}">Clear</a>
          </form>
          <div class="grid3">
            <div class="kpi"><div class="muted small">Entries shown</div><div class="num">{{ rows|length }}</div></div>
            <div class="kpi"><div class="muted small">State</div><div class="num" style="font-size:18px;margin-top:12px;">Unlocked</div></div>
            <div class="kpi"><div class="muted small">Encryption</div><div class="num" style="font-size:18px;margin-top:12px;">OpenSSL</div></div>
          </div>
        </section>
        <div class="sep"></div>
        {% if rows %}<div class="cards">{% for r in rows %}<div class="site stack"><div style="font-weight:900;">{{ r['title'] }}</div><div class="muted small mono">{{ r['url'] }}</div><div class="tinyActions"><a href="{{ url_for('vault_view', entry_id=r['id']) }}">Open</a><a href="{{ url_for('vault_edit', entry_id=r['id']) }}">Edit</a><a target="_blank" rel="noreferrer" href="{{ r['url'] }}">Visit</a></div></div>{% endfor %}</div>{% else %}<section class="card"><div class="muted">No entries yet.</div></section>{% endif %}
        """, rows=rows, q=q
    )
    return render_page("Vault", body)

@app.route("/vault/setup", methods=["GET", "POST"])
def vault_setup():
    if vault_configured():
        return redirect(url_for("vault_login"))
    if request.method == "POST":
        p1 = request.form.get("p1", "")
        p2 = request.form.get("p2", "")
        if len(p1) < 8:
            flash("Master password must be at least 8 characters.")
        elif p1 != p2:
            flash("Passwords do not match.")
        else:
            set_vault_password(p1)
            flash("Vault created. Unlock it now.")
            return redirect(url_for("vault_login"))
    body = """
    <section class='hero stack'>
      <div class='pillRow'><span class='badge'>Vault setup</span><span class='badge'>OpenSSL encryption</span></div>
      <h1 style='margin:0;'>Create vault</h1>
      <div class='muted'>Set one master password for the vault.</div>
      <form method='post' class='grid2'>
        <div class='card stack'><div><label>Master password</label><input type='password' name='p1' required></div><div><label>Confirm password</label><input type='password' name='p2' required></div><div class='row'><button class='btn primary' type='submit'>Create vault</button></div></div>
        <div class='card stack'><h3 style='margin:0;'>Tips</h3><div class='muted'>Use something long and unique.</div></div>
      </form>
    </section>
    """
    return render_page("Vault setup", body)

@app.route("/vault/login", methods=["GET", "POST"])
def vault_login():
    if not vault_configured():
        return redirect(url_for("vault_setup"))
    if request.method == "POST":
        master = request.form.get("master", "")
        if verify_vault_password(master):
            VAULT_KEYS[get_client_id()] = master
            flash("Vault unlocked.")
            return redirect(url_for("vault_home"))
        flash("Wrong master password.")
    body = """
    <section class='hero stack'>
      <div class='pillRow'><span class='badge'>Vault locked</span></div>
      <h1 style='margin:0;'>Unlock vault</h1>
      <form method='post' class='grid2'>
        <div class='card stack'><div><label>Master password</label><input type='password' name='master' required></div><div class='row'><button class='btn primary' type='submit'>Unlock</button></div></div>
        <div class='card stack'><h3 style='margin:0;'>What happens here</h3><div class='muted'>Unlock stays only in this local session until you lock it.</div></div>
      </form>
    </section>
    """
    return render_page("Vault login", body)

@app.route("/vault/logout")
def vault_logout():
    VAULT_KEYS.pop(get_client_id(), None)
    flash("Vault locked.")
    return redirect(url_for("vault_login"))

@app.route("/vault/add", methods=["GET", "POST"])
def vault_add():
    gate = require_vault()
    if gate:
        return gate
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        url = (request.form.get("url") or "").strip()
        username = request.form.get("username") or ""
        password = request.form.get("password") or ""
        notes = request.form.get("notes") or ""
        if not title or not url:
            flash("Title and URL are required.")
        else:
            master = vault_master()
            con = db_connect()
            con.execute(
                "INSERT INTO entries(title,url,username_enc,password_enc,notes_enc,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                (title, url, vault_encrypt(master, username), vault_encrypt(master, password), vault_encrypt(master, notes), int(time.time()), int(time.time()))
            )
            con.commit()
            con.close()
            flash("Entry saved.")
            return redirect(url_for("vault_home"))
    body = """
    <section class='hero stack'>
      <h1 style='margin:0;'>Add entry</h1>
      <div class='muted'>Store a login, password, and notes.</div>
      <form method='post' class='grid2'>
        <div class='card stack'>
          <div><label>Title</label><input name='title' required></div>
          <div><label>URL</label><input name='url' placeholder='https://example.com' required></div>
          <div><label>Username</label><input name='username'></div>
          <div><label>Password</label><input type='password' name='password' id='newPass'></div>
          <div class='row'><button class='btn' type='button' onclick="document.getElementById('newPass').value=Math.random().toString(36).slice(2)+Math.random().toString(36).slice(2)">Generate password</button></div>
        </div>
        <div class='card stack'>
          <div><label>Notes</label><textarea name='notes'></textarea></div>
          <div class='row'><button class='btn primary' type='submit'>Save entry</button><a class='btn' href='{{ url_for("vault_home") }}'>Back</a></div>
        </div>
      </form>
    </section>
    """
    return render_page("Add entry", body)

@app.route("/vault/view/<int:entry_id>")
def vault_view(entry_id: int):
    gate = require_vault()
    if gate:
        return gate
    con = db_connect()
    row = con.execute("SELECT * FROM entries WHERE id=?", (entry_id,)).fetchone()
    con.close()
    if not row:
        flash("Entry not found.")
        return redirect(url_for("vault_home"))
    master = vault_master()
    try:
        username = vault_decrypt(master, row["username_enc"])
        password = vault_decrypt(master, row["password_enc"])
        notes = vault_decrypt(master, row["notes_enc"])
    except Exception:
        flash("Could not decrypt entry. Unlock the vault again.")
        return redirect(url_for("vault_logout"))
    body = render_template_string(
        """
        <section class="hero stack">
          <div class="row" style="justify-content:space-between;align-items:flex-start;"><div><h1 style="margin:0 0 8px 0;">{{ r['title'] }}</h1><div class="muted small mono">{{ r['url'] }}</div></div><div class="row"><a class="btn primary" target="_blank" rel="noreferrer" href="{{ r['url'] }}">Open site</a><a class="btn" href="{{ url_for('vault_edit', entry_id=r['id']) }}">Edit</a></div></div>
          <div class="grid2">
            <div class="card stack">
              <div><label>Username</label><input id="u" value="{{ username }}" readonly></div>
              <div><label>Password</label><div class="row"><input id="p" type="password" value="{{ password }}" readonly style="flex:1;"><button class="btn" type="button" onclick="const p=document.getElementById('p');p.type=p.type==='password'?'text':'password'">Show/Hide</button></div></div>
              <div class="row"><button class="btn" type="button" onclick="navigator.clipboard.writeText(document.getElementById('u').value)">Copy username</button><button class="btn" type="button" onclick="navigator.clipboard.writeText(document.getElementById('p').value)">Copy password</button></div>
            </div>
            <div class="card stack">
              <div><label>Notes</label><textarea id="n" readonly>{{ notes }}</textarea></div>
              <div class="row"><button class="btn" type="button" onclick="navigator.clipboard.writeText(document.getElementById('n').value)">Copy notes</button></div>
              <form method="post" action="{{ url_for('vault_delete', entry_id=r['id']) }}" onsubmit="return confirm('Delete this entry?');"><button class="btn danger" type="submit">Delete</button></form>
            </div>
          </div>
        </section>
        """, r=row, username=username, password=password, notes=notes
    )
    return render_page("View entry", body)

@app.route("/vault/edit/<int:entry_id>", methods=["GET", "POST"])
def vault_edit(entry_id: int):
    gate = require_vault()
    if gate:
        return gate
    con = db_connect()
    row = con.execute("SELECT * FROM entries WHERE id=?", (entry_id,)).fetchone()
    con.close()
    if not row:
        flash("Entry not found.")
        return redirect(url_for("vault_home"))
    master = vault_master()
    try:
        username = vault_decrypt(master, row["username_enc"])
        password = vault_decrypt(master, row["password_enc"])
        notes = vault_decrypt(master, row["notes_enc"])
    except Exception:
        flash("Could not decrypt entry. Unlock the vault again.")
        return redirect(url_for("vault_logout"))
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        url = (request.form.get("url") or "").strip()
        username = request.form.get("username") or ""
        password = request.form.get("password") or ""
        notes = request.form.get("notes") or ""
        if not title or not url:
            flash("Title and URL are required.")
        else:
            con = db_connect()
            con.execute(
                "UPDATE entries SET title=?, url=?, username_enc=?, password_enc=?, notes_enc=?, updated_at=? WHERE id=?",
                (title, url, vault_encrypt(master, username), vault_encrypt(master, password), vault_encrypt(master, notes), int(time.time()), entry_id)
            )
            con.commit()
            con.close()
            flash("Entry updated.")
            return redirect(url_for("vault_view", entry_id=entry_id))
    body = render_template_string(
        """
        <section class="hero stack">
          <h1 style="margin:0;">Edit entry</h1>
          <form method="post" class="grid2">
            <div class="card stack">
              <div><label>Title</label><input name="title" value="{{ r['title'] }}" required></div>
              <div><label>URL</label><input name="url" value="{{ r['url'] }}" required></div>
              <div><label>Username</label><input name="username" value="{{ username }}"></div>
              <div><label>Password</label><input type="password" name="password" value="{{ password }}" id="editPass"></div>
              <div class='row'><button class='btn' type='button' onclick="document.getElementById('editPass').value=Math.random().toString(36).slice(2)+Math.random().toString(36).slice(2)">Generate password</button></div>
            </div>
            <div class="card stack">
              <div><label>Notes</label><textarea name="notes">{{ notes }}</textarea></div>
              <div class="row"><button class="btn primary" type="submit">Save</button><a class="btn" href="{{ url_for('vault_view', entry_id=r['id']) }}">Cancel</a></div>
            </div>
          </form>
        </section>
        """, r=row, username=username, password=password, notes=notes
    )
    return render_page("Edit entry", body)

@app.route("/vault/delete/<int:entry_id>", methods=["POST"])
def vault_delete(entry_id: int):
    gate = require_vault()
    if gate:
        return gate
    con = db_connect()
    con.execute("DELETE FROM entries WHERE id=?", (entry_id,))
    con.commit()
    con.close()
    flash("Entry deleted.")
    return redirect(url_for("vault_home"))

@app.route("/vault/settings", methods=["GET", "POST"])
def vault_settings():
    gate = require_vault()
    if gate:
        return gate
    if request.method == "POST":
        oldp = request.form.get("oldp", "")
        newp1 = request.form.get("newp1", "")
        newp2 = request.form.get("newp2", "")
        if not verify_vault_password(oldp):
            flash("Old password is wrong.")
        elif len(newp1) < 8:
            flash("New password must be at least 8 characters.")
        elif newp1 != newp2:
            flash("New passwords do not match.")
        else:
            con = db_connect()
            rows = con.execute("SELECT * FROM entries").fetchall()
            for row in rows:
                try:
                    username = vault_decrypt(oldp, row["username_enc"])
                    password = vault_decrypt(oldp, row["password_enc"])
                    notes = vault_decrypt(oldp, row["notes_enc"])
                except Exception:
                    con.close()
                    flash("Could not re-encrypt the vault.")
                    return redirect(url_for("vault_settings"))
                con.execute(
                    "UPDATE entries SET username_enc=?, password_enc=?, notes_enc=?, updated_at=? WHERE id=?",
                    (vault_encrypt(newp1, username), vault_encrypt(newp1, password), vault_encrypt(newp1, notes), int(time.time()), row["id"])
                )
            con.commit()
            con.close()
            set_vault_password(newp1)
            VAULT_KEYS[get_client_id()] = newp1
            flash("Vault password changed.")
            return redirect(url_for("vault_settings"))
    body = """
    <section class='hero stack'>
      <h1 style='margin:0;'>Vault settings</h1>
      <div class='muted'>Change the master password and re-encrypt all entries using the new one.</div>
      <form method='post' class='grid2'>
        <div class='card stack'>
          <div><label>Old password</label><input type='password' name='oldp' required></div>
          <div><label>New password</label><input type='password' name='newp1' required></div>
          <div><label>Confirm new password</label><input type='password' name='newp2' required></div>
          <div class='row'><button class='btn primary' type='submit'>Change password</button><a class='btn' href='{{ url_for("vault_home") }}'>Back</a></div>
        </div>
        <div class='card stack'><h3 style='margin:0;'>Reminder</h3><div class='muted'>Changing the password re-encrypts every stored field, so it may take a moment if you have many entries.</div></div>
      </form>
    </section>
    """
    return render_page("Vault settings", body)

# ---------------- auto open ----------------
def open_in_browser(url: str) -> None:
    try:
        if which("termux-open-url"):
            subprocess.Popen(["termux-open-url", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        if which("xdg-open"):
            subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
    except Exception:
        pass
    print(f"Open this in your browser: {url}")


def delayed_open(url: str, delay: float = 0.8) -> None:
    def _worker():
        time.sleep(delay)
        open_in_browser(url)
    threading.Thread(target=_worker, daemon=True).start()


def main() -> None:
    parser = argparse.ArgumentParser(description="Free Internet")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}"
    if not args.no_open:
        delayed_open(url)
    print(url)
    app.run(host=args.host, port=args.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
