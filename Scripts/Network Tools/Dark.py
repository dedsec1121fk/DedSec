#!/usr/bin/env python3
from __future__ import annotations
import os
import sys
import re
import json
import csv
import time
import socket
import subprocess
import argparse
import curses
from urllib.parse import urljoin, urlparse, quote_plus
from collections import deque
from datetime import datetime

# -------------------------
# Auto pip install (best-effort)
# -------------------------
REQ = ["requests", "bs4", "lxml", "validators", "tldextract", "python_dotenv", "pysocks"]
MISSING = []
for p in REQ:
    try:
        __import__(p if p != "python_dotenv" else "dotenv")
    except Exception:
        MISSING.append(p)


def pip_install(pkgs):
    if not pkgs:
        return True
    mapped = []
    for p in pkgs:
        if p == "requests":
            mapped.append("requests[socks]")
        elif p == "python_dotenv":
            mapped.append("python-dotenv")
        else:
            mapped.append(p)
    try:
        print("[*] pip installing:", mapped)
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + mapped)
        return True
    except Exception as e:
        print("[!] pip install failed:", e)
        print("[!] Please install manually:", " ".join(mapped))
        return False


def ensure_dependencies():
    """Try to install missing python packages and re-import them. Returns tuple (ok, missing_list)"""
    global MISSING
    if not MISSING:
        return True, []
    ok = pip_install(MISSING)
    if not ok:
        return False, MISSING
    # retry imports
    failed = []
    for p in list(MISSING):
        try:
            __import__(p if p != "python_dotenv" else "dotenv")
        except Exception:
            failed.append(p)
    MISSING = failed
    return (len(failed) == 0), failed

# Try to auto-install missing deps before importing modules we depend on
if MISSING:
    success, failed = ensure_dependencies()
    if not success:
        print("[!] Some python packages failed to install automatically:", failed)
        print("[!] Continuing but some features may be unavailable.")

# Try import again (some environments may still fail)
try:
    import requests
    from bs4 import BeautifulSoup
    import validators
    import tldextract
    from dotenv import load_dotenv
except Exception as e:
    print("[!] Some optional dependencies failed to import:", e)
    # script will still run but some features may break

# -------------------------
# Constants & paths
# -------------------------
DEFAULT_SOCKS = "socks5h://127.0.0.1:9050"
USER_AGENT = "TorBot-AllInOne-Mega/1.0 (+https://ded-sec.space)"
DEFAULT_TIMEOUT = 20
DEFAULT_DELAY = 0.6

ANDROID_RESULTS = "/sdcard/Download/DarkNet"
FALLBACK_RESULTS = os.path.expanduser("~/DarkNet")
PLUGINS_SUB = "plugins"


def ensure_results_and_plugins():
    preferred = ANDROID_RESULTS
    results_dir = None
    try:
        os.makedirs(preferred, exist_ok=True)
        results_dir = preferred
    except Exception:
        try:
            os.makedirs(FALLBACK_RESULTS, exist_ok=True)
            results_dir = FALLBACK_RESULTS
        except Exception:
            # final fallback: current dir
            results_dir = os.path.join(os.getcwd(), "DarkNet")
            os.makedirs(results_dir, exist_ok=True)
    plugins_dir = os.path.join(results_dir, PLUGINS_SUB)
    os.makedirs(plugins_dir, exist_ok=True)
    return results_dir, plugins_dir

RESULTS_DIR, PLUGINS_DIR = ensure_results_and_plugins()

# -------------------------
# Self-install plugins (writes plugin files into PLUGINS_DIR)
# -------------------------
def write_plugin_file(name, code):
    path = os.path.join(PLUGINS_DIR, name)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        return True
    except Exception as e:
        return False

PLUGIN_FILES = {
"plugin_base.py": '''\
# plugin_base.py
# Utility helpers for plugins (optional)
def info():
    return {"name": "plugin_base", "version": "0.1"}

def run(data):
    # base plugin does nothing
    return data
''',

"extract_emails.py": '''\
# extract_emails.py
import re
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\\-]{1,64}@[a-zA-Z0-9.\\-]+\\.[a-zA-Z]{2,}", re.I)
def run(data):
    items = data if isinstance(data, list) else [data]
    for item in items:
        text = (item.get("text_snippet") or "") + "\\n" + (" ".join(item.get("links", [])) if item.get("links") else "")
        found = list(set(m.group(0) for m in EMAIL_RE.finditer(text)))
        if found:
            item.setdefault("plugin_emails", []).extend([e for e in found if e not in item.get("plugin_emails", [])])
    return data
''',

"extract_btc.py": '''\
# extract_btc.py
import re
BTC_RE = re.compile(r"\\b([13][a-km-zA-HJ-NP-Z1-9]{25,34})\\b")
def run(data):
    items = data if isinstance(data, list) else [data]
    for item in items:
        text = item.get("text_snippet","")
        found = list(set(m.group(0) for m in BTC_RE.finditer(text)))
        if found:
            item.setdefault("plugin_btc", []).extend([b for b in found if b not in item.get("plugin_btc", [])])
    return data
''',

"extract_metadata.py": '''\
# extract_metadata.py
def run(data):
    items = data if isinstance(data, list) else [data]
    for item in items:
        meta = item.get("meta") or {}
        item["plugin_meta_normalized"] = {k.lower(): v for k, v in meta.items()}
    return data
''',

"extract_links.py": '''\
# extract_links.py
def run(data):
    items = data if isinstance(data, list) else [data]
    for item in items:
        links = item.get("links") or []
        onions = [l for l in links if ".onion" in l]
        clearnet = [l for l in links if ".onion" not in l]
        item["plugin_links"] = {"onion": onions, "clearnet": clearnet, "count": len(links)}
    return data
''',

"clean_html.py": '''\
# clean_html.py
from bs4 import BeautifulSoup
def run(data):
    items = data if isinstance(data, list) else [data]
    for item in items:
        html = item.get("raw_html") or item.get("text_snippet") or ""
        if html:
            try:
                soup = BeautifulSoup(html, "lxml")
                for t in soup(["script","style","noscript"]):
                    t.decompose()
                item["plugin_clean_text"] = "\\n".join([l.strip() for l in soup.get_text().splitlines() if l.strip()])[:2000]
            except Exception:
                item["plugin_clean_text"] = ""
    return data
''',

"save_snapshot.py": '''\
# save_snapshot.py
import os, time, re
def run(data):
    out_dir = os.environ.get("TORBOT_RESULTS_DIR")
    if not out_dir:
        return data
    items = data if isinstance(data, list) else [data]
    saved = []
    for item in items:
        raw_html = item.get("raw_html")
        if not raw_html:
            continue
        safe = re.sub(r'[^\\w\\-_.]', '_', item.get("url",""))[:200]
        fname = os.path.join(out_dir, f"plugin_snapshot_{safe}_{int(time.time())}.html")
        try:
            with open(fname, "w", encoding="utf-8") as f:
                f.write(raw_html)
            saved.append(fname)
        except Exception:
            pass
    if saved:
        for item in items:
            item.setdefault("plugin_snapshots", []).extend(saved)
    return data
''',

"plugin_logger.py": '''\
# plugin_logger.py
import json, os
def run(data):
    out_dir = os.environ.get("TORBOT_RESULTS_DIR")
    if not out_dir:
        return data
    logf = os.path.join(out_dir, "plugin_logger_urls.json")
    items = data if isinstance(data, list) else [data]
    existing = []
    try:
        if os.path.exists(logf):
            with open(logf,"r",encoding="utf-8") as f:
                existing = json.load(f)
    except Exception:
        existing = []
    for item in items:
        existing.append({"url": item.get("url"), "ts": item.get("fetched_at")})
    try:
        with open(logf,"w",encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
    return data
''',

"plugin_export_csv.py": '''\
# plugin_export_csv.py
import os, csv
def run(data):
    out_dir = os.environ.get("TORBOT_RESULTS_DIR")
    if not out_dir:
        return data
    items = data if isinstance(data, list) else [data]
    path = os.path.join(out_dir, "plugin_export.csv")
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["url","title","emails","phones","btc"])
            for it in items:
                w.writerow([it.get("url",""), it.get("title",""), ";".join(it.get("emails",[])), ";".join(it.get("phones",[])), ";".join(it.get("btc",[]))])
    except Exception:
        pass
    return data
''',

"plugin_example_transform.py": '''\
# plugin_example_transform.py
def run(data):
    items = data if isinstance(data, list) else [data]
    for i, it in enumerate(items):
        title = it.get("title") or ""
        it["plugin_title_len"] = len(title)
    return data
'''
}


def install_plugins():
    installed = []
    for name, code in PLUGIN_FILES.items():
        ok = write_plugin_file(name, code)
        if ok:
            installed.append(name)
    os.environ["TORBOT_RESULTS_DIR"] = RESULTS_DIR
    return installed

# ensure some plugins exist at startup for better UX
try:
    if not os.listdir(PLUGINS_DIR):
        install_plugins()
except Exception:
    pass

# -------------------------
# Core functionality: requests, session
# -------------------------
session = None


def create_session(socks_url=DEFAULT_SOCKS):
    global session
    try:
        import requests as _req
        session_local = _req.Session()
        session_local.headers.update({"User-Agent": USER_AGENT})
        # set proxies; requests[socks] required for socks via PySocks
        if socks_url:
            session_local.proxies.update({"http": socks_url, "https": socks_url})
        session = session_local
        return session
    except Exception as e:
        session = None
        return None

create_session()

def set_socks(socks):
    if session:
        try:
            session.proxies.update({"http": socks, "https": socks})
        except Exception:
            pass

# -------------------------
# Helpers & extractors
# -------------------------

def now_ts():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def log(msg, lvl="INFO"):
    print(f"[{now_ts()}] {lvl}: {msg}")


def shutil_which(cmd):
    for d in os.environ.get("PATH","").split(os.pathsep):
        full = os.path.join(d, cmd)
        if os.path.isfile(full) and os.access(full, os.X_OK):
            return full
    return None


def is_tor_running(host="127.0.0.1", port=9050, timeout=2):
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False


def try_start_tor_background():
    tor_bin = shutil_which("tor")
    if not tor_bin:
        # try to auto install tor via common package managers (best-effort, may require privileges)
        # termux: pkg install tor
        attempts = [
            ("pkg", ["pkg", "install", "tor", "-y"]),
            ("apt-get", ["apt-get", "install", "tor", "-y"]),
            ("brew", ["brew", "install", "tor"]),
            ("pacman", ["pacman", "-S", "tor", "--noconfirm"]),
        ]
        for name, cmd in attempts:
            if shutil_which(cmd[0]):
                try:
                    log(f"Attempting system install of tor via: {' '.join(cmd)}")
                    subprocess.check_call(cmd)
                except Exception:
                    pass
        tor_bin = shutil_which("tor")
        if not tor_bin:
            return False, "No 'tor' binary found after attempted installs. Please install manually (pkg/apt/brew)."
    try:
        p = subprocess.Popen([tor_bin], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(4)
        # quick check
        if is_tor_running():
            return True, f"Started tor pid={p.pid}"
        return True, f"Started tor pid={p.pid} (SOCKS port might not be up yet)"
    except Exception as e:
        return False, f"Failed to start tor: {e}"

# Regex extractors
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]{1,64}@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(?:\+?\d[\d\-\s]{6,}\d)")
BTC_RE = re.compile(r"\b([13][a-km-zA-HJ-NP-Z1-9]{25,34})\b")
XMR_RE = re.compile(r"\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b")
PGP_RE = re.compile(r"-----BEGIN PGP PUBLIC KEY BLOCK-----.*?-----END PGP PUBLIC KEY BLOCK-----", re.S)


def extract_emails(text):
    return list(set(m.group(0) for m in EMAIL_RE.finditer(text or "")))
def extract_phones(text):
    return list(set(m.group(0) for m in PHONE_RE.finditer(text or "")))
def extract_btc(text):
    return list(set(m.group(0) for m in BTC_RE.finditer(text or "")))
def extract_xmr(text):
    return list(set(m.group(0) for m in XMR_RE.finditer(text or "")))
def extract_pgp(text):
    return PGP_RE.findall(text or "")

# HTML helpers
def normalize_url(u):
    u = (u or "").strip()
    if not u:
        return ""
    if u.startswith("http://") or u.startswith("https://"):
        return u
    if ".onion" in u and "://" not in u:
        return "http://" + u
    if "://" not in u:
        return "http://" + u
    return u


def safe_get(url, allow_redirects=True, timeout=DEFAULT_TIMEOUT):
    # robust safe_get: if requests session missing, fall back to urllib
    if session:
        try:
            r = session.get(url, timeout=timeout, allow_redirects=allow_redirects)
            return r
        except Exception:
            return None
    # fallback
    try:
        from urllib.request import Request, urlopen
        req = Request(url, headers={"User-Agent": USER_AGENT})
        resp = urlopen(req, timeout=timeout)
        class R:
            pass
        r = R()
        r.status_code = getattr(resp, 'status', 200)
        r.text = resp.read().decode('utf-8', errors='ignore')
        return r
    except Exception:
        return None


def extract_title_meta(html):
    try:
        soup = BeautifulSoup(html, "lxml")
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        metas = {}
        for m in soup.find_all("meta"):
            k = m.get("name") or m.get("property") or m.get("http-equiv")
            if k:
                metas[k.lower()] = m.get("content","")
        return title, metas
    except Exception:
        return "", {}


def extract_links(base, html):
    try:
        soup = BeautifulSoup(html, "lxml")
        links = set()
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith("javascript:") or href.startswith("#"):
                continue
            absu = urljoin(base, href)
            absu = absu.split("#")[0]
            links.add(absu)
        return list(links)
    except Exception:
        return []


def clean_text(html):
    try:
        soup = BeautifulSoup(html, "lxml")
        for t in soup(["script","style","noscript"]):
            t.decompose()
        text = soup.get_text(separator="\n")
        return "\n".join([ln.strip() for ln in text.splitlines() if ln.strip()])
    except Exception:
        return ""

# Scrape single page
def scrape_page(url, save_snapshot=False):
    norm = normalize_url(url)
    r = safe_get(norm)
    if not r:
        return {"url": norm, "online": False, "status": None, "fetched_at": now_ts()}
    html = r.text
    title, metas = extract_title_meta(html)
    emails = extract_emails(html)
    phones = extract_phones(html)
    btc = extract_btc(html)
    xmr = extract_xmr(html)
    pgp = extract_pgp(html)
    links = extract_links(norm, html)
    text = clean_text(html)
    res = {
        "url": norm,
        "status": r.status_code,
        "title": title,
        "meta": metas,
        "emails": emails,
        "phones": phones,
        "btc": btc,
        "xmr": xmr,
        "pgp": pgp,
        "links": links,
        "raw_html": html,
        "text_snippet": text[:4000],
        "fetched_at": now_ts()
    }
    if save_snapshot:
        save_snapshot_html(norm, html)
    return res


def save_snapshot_html(url, html):
    safe = re.sub(r"[^\w\-_.]", "_", url)[:200]
    fname = os.path.join(RESULTS_DIR, f"snapshot_{safe}_{int(time.time())}.html")
    try:
        with open(fname, "w", encoding="utf-8") as f:
            f.write(html)
        log(f"Saved snapshot: {fname}")
    except Exception as e:
        log(f"Snapshot save error: {e}", "ERROR")

# Crawler
def crawl(start_url, max_pages=200, max_depth=2, same_domain=True, save_snapshots=False, verbose=True):
    start_url = normalize_url(start_url)
    q = deque()
    q.append((start_url, 0))
    visited = set([start_url])
    out = []
    pages = 0
    base_domain = urlparse(start_url).netloc
    while q and pages < max_pages:
        url, depth = q.popleft()
        if verbose:
            log(f"Crawling depth={depth} url={url}")
        item = scrape_page(url, save_snapshot=save_snapshots)
        out.append(item)
        pages += 1
        time.sleep(DEFAULT_DELAY)
        if depth < max_depth:
            for l in item.get("links", []):
                if l in visited:
                    continue
                parsed = urlparse(l)
                if parsed.scheme not in ("http", "https"):
                    continue
                if same_domain and parsed.netloc != base_domain:
                    continue
                visited.add(l)
                q.append((l, depth + 1))
    return out

# Simple Ahmia search
def search_ahmia(query):
    q = quote_plus(query)
    url = f"https://ahmia.fi/search/?q={q}"
    r = safe_get(url)
    res = []
    if not r:
        return res
    try:
        soup = BeautifulSoup(r.text, "lxml")
        for item in soup.select("div.result, li.result"):
            a = item.find("a", href=True)
            if a:
                title = a.get_text(strip=True)
                href = a["href"]
                desc = item.get_text(" ", strip=True)
                res.append({"title": title, "url": href, "desc": desc})
    except Exception:
        pass
    return res


def search_combined(query, limit=50):
    out = []
    seen = set()
    for r in search_ahmia(query):
        u = r.get("url")
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(r)
        if len(out) >= limit:
            break
    return out

# Exports
def save_json(name, data):
    path = os.path.join(RESULTS_DIR, name)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        log(f"Saved JSON -> {path}")
        return path
    except Exception as e:
        log(f"Save JSON error: {e}", "ERROR")
        return None


def save_csv(name, data):
    path = os.path.join(RESULTS_DIR, name)
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["url","status","title","emails","phones","btc","xmr","pgp_count","links_count","fetched_at"])
            for d in data:
                w.writerow([d.get("url",""), d.get("status",""), (d.get("title") or "").replace("\n"," "), ";".join(d.get("emails",[])), ";".join(d.get("phones",[])), ";".join(d.get("btc",[])), ";".join(d.get("xmr",[])), len(d.get("pgp",[])), len(d.get("links",[])), d.get("fetched_at","")])
        log(f"Saved CSV -> {path}")
        return path
    except Exception as e:
        log(f"Save CSV error: {e}", "ERROR")
        return None


def save_txt(name, data):
    path = os.path.join(RESULTS_DIR, name)
    try:
        with open(path, "w", encoding="utf-8") as f:
            for d in data:
                f.write(f"URL: {d.get('url','')}\n")
                f.write(f"Status: {d.get('status','')}\n")
                f.write(f"Title: {d.get('title','')}\n")
                f.write(f"Emails: {','.join(d.get('emails',[]))}\n")
                f.write("-"*40 + "\n")
        log(f"Saved TXT -> {path}")
        return path
    except Exception as e:
        log(f"Save TXT error: {e}", "ERROR")
        return None

# Plugin loader & runner
def load_plugins():
    plugins = []
    if not os.path.isdir(PLUGINS_DIR):
        return plugins
    for fname in sorted(os.listdir(PLUGINS_DIR)):
        if not fname.endswith(".py"):
            continue
        full = os.path.join(PLUGINS_DIR, fname)
        try:
            ns = {}
            with open(full, "r", encoding="utf-8") as f:
                code = f.read()
            exec(compile(code, full, "exec"), ns)
            if "run" in ns and callable(ns["run"]):
                plugins.append({"name": fname, "run": ns["run"]})
                log(f"Loaded plugin: {fname}")
            else:
                log(f"Plugin {fname} has no run(data) function; skipped", "WARN")
        except Exception as e:
            log(f"Failed loading plugin {fname}: {e}", "ERROR")
    return plugins


def run_plugins(plugins, data):
    for p in plugins:
        try:
            out = p["run"](data)
            if out is not None:
                data = out
        except Exception as e:
            log(f"Plugin {p['name']} error: {e}", "ERROR")
    return data

# -------------------------
# Curses UI functions
# -------------------------
# (unchanged from original but improved safeguards)

def draw_menu(stdscr, selected_idx, menu_items, title, status_msg="", menu_style="list"):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    try:
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(0, max(0, (w - len(title)) // 2), title)
        stdscr.attroff(curses.color_pair(1))
    except Exception:
        pass
    if status_msg:
        stdscr.addstr(1, 0, status_msg[:w-1])
    info_lines = [
        f"Results dir: {RESULTS_DIR}",
        f"Tor socks: {DEFAULT_SOCKS}",
        f"Tor running: {is_tor_running()}",
        f"Plugins: {len(os.listdir(PLUGINS_DIR)) if os.path.isdir(PLUGINS_DIR) else 0} installed"
    ]
    for i, line in enumerate(info_lines):
        stdscr.addstr(3 + i, 0, line[:w-1])
    start_y = 8
    for idx, item in enumerate(menu_items):
        x = 2
        y = start_y + idx
        if menu_style == "list":
            if idx == selected_idx:
                try:
                    stdscr.attron(curses.color_pair(2))
                    stdscr.addstr(y, x, f"> {item}")
                    stdscr.attroff(curses.color_pair(2))
                except Exception:
                    stdscr.addstr(y, x, f"> {item}")
            else:
                stdscr.addstr(y, x, f"  {item}")
        elif menu_style == "number":
            stdscr.addstr(y, x, f"{idx + 1}. {item}")

    if menu_style == "list":
        stdscr.addstr(h-2, 0, "Use ↑↓ to navigate, Enter to select, q to quit")
    else:
        stdscr.addstr(h-2, 0, f"Enter a number (1-{len(menu_items)}) to select, q to quit")
    stdscr.refresh()


def get_user_input(stdscr, prompt, default=""):
    curses.echo()
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    stdscr.addstr(0, 0, prompt)
    if default:
        stdscr.addstr(1, 0, f"Default: {default}")
        stdscr.addstr(2, 0, "Your input: ")
    else:
        stdscr.addstr(1, 0, "Your input: ")
    stdscr.refresh()
    try:
        if default:
            user_input = stdscr.getstr(2, 12, 200).decode('utf-8').strip()
        else:
            user_input = stdscr.getstr(1, 12, 200).decode('utf-8').strip()
    except Exception:
        user_input = ""
    curses.noecho()
    return user_input if user_input else default


def show_message(stdscr, message):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    lines = message.split('\n')
    for i, line in enumerate(lines):
        if i < h - 2:
            stdscr.addstr(i, 0, line[:w-1])
    stdscr.addstr(h-1, 0, "Press any key to continue...")
    stdscr.refresh()
    stdscr.getch()


def curses_menu(stdscr):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
    
    menu_style = "list"  # "list" or "number"
    
    menu_items = [
        "Install example plugins",
        "Check/start Tor",
        "Crawl a URL",
        "Search Ahmia",
        "Load & run plugins on last results",
        "Export last results (json/csv/txt)",
        "Choose Menu Style",
        "Exit"
    ]
    current_selection = 0
    status_msg = ""
    while True:
        draw_menu(stdscr, current_selection, menu_items, "TorBot All-in-One", status_msg, menu_style)
        status_msg = ""
        key = stdscr.getch()

        selected_action_index = -1  # Flag for no action

        if key == ord('q'):
            break

        if menu_style == "list":
            if key == curses.KEY_UP:
                current_selection = (current_selection - 1) % len(menu_items)
            elif key == curses.KEY_DOWN:
                current_selection = (current_selection + 1) % len(menu_items)
            elif key == ord('\n') or key == ord(' '):
                selected_action_index = current_selection

        elif menu_style == "number":
            if ord('1') <= key <= ord(str(len(menu_items))):
                try:
                    # '1' maps to index 0
                    selected_action_index = int(chr(key)) - 1
                except ValueError:
                    pass  # Not a valid number

        # --- Handle the selected action ---
        if selected_action_index == -1:
            continue  # No action selected, loop again

        # --- Action processing ---
        if selected_action_index == 0:  # Install plugins
            installed = install_plugins()
            status_msg = f"Installed {len(installed)} plugins: {', '.join(installed)}"
        elif selected_action_index == 1:  # Check/start Tor
            if is_tor_running():
                status_msg = "[*] Tor appears to be running (SOCKS open)."
            else:
                ok, msg = try_start_tor_background()
                status_msg = f"[*] try_start_tor_background -> {ok}, {msg}"
                time.sleep(1)
                if is_tor_running():
                    create_session(DEFAULT_SOCKS)
                    status_msg += " Tor is running and session configured."
                else:
                    status_msg += " Tor still not running."
        elif selected_action_index == 2:  # Crawl
            url = get_user_input(stdscr, "Enter start URL (.onion or http):")
            if not url:
                status_msg = "No URL provided, skipping crawl."
                continue
            max_pages = get_user_input(stdscr, "Max pages:", "200")
            depth = get_user_input(stdscr, "Max depth:", "2")
            same_domain = get_user_input(stdscr, "Same domain only? (y/N):", "n").lower().startswith('y')
            save_snap = get_user_input(stdscr, "Save snapshots? (y/N):", "n").lower().startswith('y')
            socks_proxy = get_user_input(stdscr, f"SOCKS proxy:", DEFAULT_SOCKS)
            try:
                max_pages = int(max_pages)
                depth = int(depth)
            except:
                max_pages = 200
                depth = 2
            if not is_tor_running() and (".onion" in url):
                status_msg = "[*] Tor SOCKS not detected; trying to start tor automatically."
                ok, msg = try_start_tor_background()
                status_msg += f" Result: {ok}, {msg}"
            set_socks(socks_proxy or DEFAULT_SOCKS)
            create_session(socks_proxy or DEFAULT_SOCKS)
            show_message(stdscr, "Starting crawl... This may take a while.")
            out = crawl(url, max_pages=max_pages, max_depth=depth,
                       same_domain=same_domain, save_snapshots=save_snap, verbose=False)
            # Run plugins
            plugins = load_plugins()
            if plugins:
                out = run_plugins(plugins, out)
            # Save exports
            fn_json = save_json(f"crawl_{int(time.time())}.json", out)
            save_csv(f"crawl_{int(time.time())}.csv", out)
            save_txt(f"crawl_{int(time.time())}.txt", out)
            status_msg = f"Crawl completed. Found {len(out)} pages. JSON: {fn_json}"
        elif selected_action_index == 3:  # Search
            query = get_user_input(stdscr, "Enter search query:")
            if not query:
                status_msg = "No query provided, skipping search."
                continue
            limit = get_user_input(stdscr, "Result limit:", "50")
            socks_proxy = get_user_input(stdscr, f"SOCKS proxy:", DEFAULT_SOCKS)
            try:
                limit = int(limit)
            except:
                limit = 50
            set_socks(socks_proxy or DEFAULT_SOCKS)
            create_session(socks_proxy or DEFAULT_SOCKS)
            show_message(stdscr, "Searching... Please wait.")
            res = search_combined(query, limit=limit)
            if not res:
                status_msg = "No results or failed to query Ahmia."
            else:
                save_json(f"search_{int(time.time())}.json", res)
                status_msg = f"Found {len(res)} results. Saved to JSON."
        elif selected_action_index == 4:  # Load plugins
            files = [f for f in os.listdir(RESULTS_DIR) if f.startswith("crawl_") and f.endswith(".json")]
            if not files:
                status_msg = "No result files found. Run a crawl first."
                continue
            files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(RESULTS_DIR, x)), reverse=True)
            default_file = os.path.join(RESULTS_DIR, files[0])
            file_path = get_user_input(stdscr, "Path to JSON results file:", default_file)
            if not os.path.isfile(file_path):
                status_msg = f"File not found: {file_path}"
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                status_msg = f"Failed to load JSON: {e}"
                continue
            plugins = load_plugins()
            if not plugins:
                status_msg = "No plugins loaded."
                continue
            show_message(stdscr, "Running plugins... Please wait.")
            out = run_plugins(plugins, data)
            save_json(f"plugins_out_{int(time.time())}.json", out)
            status_msg = f"Plugins run complete. Processed {len(out) if isinstance(out, list) else 1} items."
        elif selected_action_index == 5:  # Export
            files = [f for f in os.listdir(RESULTS_DIR) if f.startswith("crawl_") and f.endswith(".json")]
            if not files:
                status_msg = "No result files found. Run a crawl first."
                continue
            files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(RESULTS_DIR, x)), reverse=True)
            default_file = os.path.join(RESULTS_DIR, files[0])
            file_path = get_user_input(stdscr, "Path to JSON results file:", default_file)
            if not os.path.isfile(file_path):
                status_msg = f"File not found: {file_path}"
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                status_msg = f"Failed to load JSON: {e}"
                continue
            save_csv(f"export_{int(time.time())}.csv", data)
            save_txt(f"export_{int(time.time())}.txt", data)
            status_msg = f"Export completed. Processed {len(data)} items."
        elif selected_action_index == 6:  # Choose Menu Style
            prompt = "Choose Menu Style:\n1. List Style (Arrows)\n2. Number Style (1, 2, 3...)\n\nYour choice: "
            stdscr.clear()
            stdscr.addstr(0, 0, prompt)
            stdscr.refresh()
            curses.echo()  # Turn echo on for this
            try:
                choice = stdscr.getstr(4, 13, 1).decode('utf-8').strip()
            except Exception:
                choice = ""
            curses.noecho()  # Turn it back off

            if choice == "1":
                menu_style = "list"
                status_msg = "Menu style set to List."
            elif choice == "2":
                menu_style = "number"
                status_msg = "Menu style set to Number."
                current_selection = 0  # Reset selection
            else:
                status_msg = "Invalid choice. No change."
        elif selected_action_index == 7:  # Exit
            break

# -------------------------
# Command line interface (preserved for backward compatibility)
# -------------------------

def cmd_install_plugins(args):
    installed = install_plugins()
    print(f"Installed plugins: {installed}")


def cmd_check_start_tor(args):
    if is_tor_running():
        print("[*] Tor appears to be running (SOCKS open).")
        return
    ok, msg = try_start_tor_background()
    print("[*] try_start_tor_background ->", ok, msg)
    time.sleep(1)
    if is_tor_running():
        create_session(DEFAULT_SOCKS)
        print("[*] Tor is running and session configured to use it.")
    else:
        print("[!] Tor still not running. You can install and run 'tor' (pkg install tor) or run Orbot/Termux-Tor.")


def cmd_crawl(args):
    url = args.url or input("Start URL (.onion or http): ").strip()
    try:
        max_pages = int(args.max_pages)
    except Exception:
        max_pages = 200
    try:
        depth = int(args.depth)
    except Exception:
        depth = 2
    same_domain = not args.no_same_domain
    save_snap = args.snapshot
    set_socks(args.socks or DEFAULT_SOCKS)
    if not is_tor_running() and (".onion" in url or (args.force_tor)):
        print("[*] Tor SOCKS not detected; trying to start tor automatically.")
        cmd_check_start_tor(args)
    create_session(args.socks or DEFAULT_SOCKS)
    out = crawl(url, max_pages=max_pages, max_depth=depth, same_domain=same_domain, save_snapshots=save_snap, verbose=not args.quiet)
    # run plugins
    plugins = load_plugins()
    if plugins:
        out = run_plugins(plugins, out)
    # save exports
    fn_json = save_json(f"crawl_{int(time.time())}.json", out)
    save_csv(f"crawl_{int(time.time())}.csv", out)
    save_txt(f"crawl_{int(time.time())}.txt", out)
    print("[*] Crawl completed. JSON:", fn_json)


def cmd_search(args):
    q = args.query or input("Search query: ").strip()
    set_socks(args.socks or DEFAULT_SOCKS)
    create_session(args.socks or DEFAULT_SOCKS)
    res = search_combined(q, limit=args.limit)
    if not res:
        print("[!] No results or failed to query Ahmia.")
        return
    print(f"Found {len(res)} results:")
    for i, r in enumerate(res, 1):
        print(f"{i}) {r.get('title')} — {r.get('url')}")
    save_json(f"search_{int(time.time())}.json", res)


def cmd_run_plugins_on_file(args):
    path = args.file or input("Path to JSON results file (default last crawl JSON in results dir): ").strip()
    if not path:
        files = [f for f in os.listdir(RESULTS_DIR) if f.startswith("crawl_") and f.endswith(".json")]
        files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(RESULTS_DIR, x)), reverse=True)
        if not files:
            print("[!] No result files found.")
            return
        path = os.path.join(RESULTS_DIR, files[0])
    if not os.path.isfile(path):
        print("[!] File not found:", path)
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print("[!] Failed to load JSON:", e)
        return
    plugins = load_plugins()
    if not plugins:
        print("[!] No plugins loaded.")
        return
    out = run_plugins(plugins, data)
    save_json(f"plugins_out_{int(time.time())}.json", out)
    print("[*] Plugins run complete. Saved output.")


def cmd_export(args):
    path = args.file or input("Path to JSON results file (default last crawl JSON): ").strip()
    if not path:
        files = [f for f in os.listdir(RESULTS_DIR) if f.startswith("crawl_") and f.endswith(".json")]
        files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(RESULTS_DIR, x)), reverse=True)
        if not files:
            print("[!] No result files found.")
            return
        path = os.path.join(RESULTS_DIR, files[0])
    if not os.path.isfile(path):
        print("[!] File not found:", path)
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print("[!] Failed to load JSON:", e)
        return
    save_csv(f"export_{int(time.time())}.csv", data)
    save_txt(f"export_{int(time.time())}.txt", data)
    print("[*] Export done.")


def main_cli():
    p = argparse.ArgumentParser(prog="dark.py", description="TorBot All-in-One (Termux)")
    sub = p.add_subparsers(dest="cmd")
    sub_install = sub.add_parser("install-plugins", help="Write example plugins into the plugins dir")
    sub_install.set_defaults(func=cmd_install_plugins)
    sub_tor = sub.add_parser("tor", help="Check/start Tor")
    sub_tor.set_defaults(func=cmd_check_start_tor)
    sub_crawl = sub.add_parser("crawl", help="Crawl a starting URL")
    sub_crawl.add_argument("url", nargs="?", help="Start URL")
    sub_crawl.add_argument("--max-pages", dest="max_pages", default=200, help="Maximum pages")
    sub_crawl.add_argument("--depth", dest="depth", default=2, help="Max depth")
    sub_crawl.add_argument("--no-same-domain", dest="no_same_domain", action="store_true", help="Don't restrict to same domain")
    sub_crawl.add_argument("--snapshot", dest="snapshot", action="store_true", help="Save snapshots")
    sub_crawl.add_argument("--socks", dest="socks", help="SOCKS proxy (e.g. socks5h://127.0.0.1:9050)")
    sub_crawl.add_argument("--quiet", dest="quiet", action="store_true")
    sub_crawl.add_argument("--force-tor", dest="force_tor", action="store_true", help="Force Tor attempt if .onion")
    sub_crawl.set_defaults(func=cmd_crawl)
    sub_search = sub.add_parser("search", help="Search Ahmia")
    sub_search.add_argument("query", nargs="?", help="Search query")
    sub_search.add_argument("--limit", type=int, default=50)
    sub_search.add_argument("--socks", dest="socks", help="SOCKS proxy")
    sub_search.set_defaults(func=cmd_search)
    sub_plugins = sub.add_parser("run-plugins", help="Run plugins on a JSON results file")
    sub_plugins.add_argument("--file", "-f", help="Path to JSON file")
    sub_plugins.set_defaults(func=cmd_run_plugins_on_file)
    sub_export = sub.add_parser("export", help="Export JSON results to CSV/TXT")
    sub_export.add_argument("--file", "-f", help="Path to JSON file")
    sub_export.set_defaults(func=cmd_export)
    # extra: autoinstall deps / check
    sub_deps = sub.add_parser("ensure-deps", help="Attempt to auto-install python deps and optional tor")
    sub_deps.add_argument("--install-tor", action="store_true", help="Also attempt to install tor via package manager (may require privileges)")
    sub_deps.set_defaults(func=lambda args: print(ensure_dependencies(), try_start_tor_background() if args.install_tor else None))

    args = p.parse_args()
    if not args.cmd:
        # Use curses interface; if curses fails, fallback to simple CLI
        try:
            curses.wrapper(curses_menu)
            return
        except Exception:
            print("[!] curses not available or failed; falling back to CLI mode.")
    # call subcommand
    try:
        args.func(args)
    except Exception as e:
        print("[!] Error executing command:", e)

if __name__ == "__main__":
    # ensure env for plugins
    os.environ["TORBOT_RESULTS_DIR"] = RESULTS_DIR
    main_cli()