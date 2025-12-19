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
# Αυτόματη εγκατάσταση pip (προσπάθεια)
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
        print("[*] Εγκατάσταση pip:", mapped)
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + mapped)
        return True
    except Exception as e:
        print("[!] Αποτυχία εγκατάστασης pip:", e)
        print("[!] Παρακαλώ εγκαταστήστε χειροκίνητα:", " ".join(mapped))
        return False


def ensure_dependencies():
    """Προσπαθεί να εγκαταστήσει τα λείποντα πακέτα python και να τα επαναφορτώσει. Επιστρέφει tuple (ok, missing_list)"""
    global MISSING
    if not MISSING:
        return True, []
    ok = pip_install(MISSING)
    if not ok:
        return False, MISSING
    # επανάληψη εισαγωγών
    failed = []
    for p in list(MISSING):
        try:
            __import__(p if p != "python_dotenv" else "dotenv")
        except Exception:
            failed.append(p)
    MISSING = failed
    return (len(failed) == 0), failed

# Προσπάθεια αυτόματης εγκατάστασης λείποντων εξαρτήσεων πριν από εισαγωγή μονάδων
if MISSING:
    success, failed = ensure_dependencies()
    if not success:
        print("[!] Κάποια πακέτα python απέτυχαν να εγκατασταθούν αυτόματα:", failed)
        print("[!] Συνέχεια αλλά κάποιες λειτουργίες μπορεί να μην είναι διαθέσιμες.")

# Προσπάθεια επανεισαγωγής (κάποια περιβάλλοντα μπορεί ακόμα να αποτύχουν)
try:
    import requests
    from bs4 import BeautifulSoup
    import validators
    import tldextract
    from dotenv import load_dotenv
except Exception as e:
    print("[!] Κάποιες προαιρετικές εξαρτήσεις απέτυχαν να φορτωθούν:", e)
    # το script θα συνεχίσει να τρέχει αλλά κάποιες λειτουργίες μπορεί να σπάσουν

# -------------------------
# Σταθερές & διαδρομές
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
            # τελική εφεδρική: τρέχοντος καταλόγου
            results_dir = os.path.join(os.getcwd(), "DarkNet")
            os.makedirs(results_dir, exist_ok=True)
    plugins_dir = os.path.join(results_dir, PLUGINS_SUB)
    os.makedirs(plugins_dir, exist_ok=True)
    return results_dir, plugins_dir

RESULTS_DIR, PLUGINS_DIR = ensure_results_and_plugins()

# -------------------------
# Αυτο-εγκατάσταση plugins (γράφει αρχεία plugin στον PLUGINS_DIR)
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
# Βοηθητικές λειτουργίες για plugins (προαιρετικό)
def info():
    return {"name": "plugin_base", "version": "0.1"}

def run(data):
    # βασικό plugin δεν κάνει τίποτα
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

# διασφάλιση ύπαρξης κάποιων plugins κατά την εκκίνηση για καλύτερη εμπειρία χρήστη
try:
    if not os.listdir(PLUGINS_DIR):
        install_plugins()
except Exception:
    pass

# -------------------------
# Βασική λειτουργικότητα: requests, session
# -------------------------
session = None


def create_session(socks_url=DEFAULT_SOCKS):
    global session
    try:
        import requests as _req
        session_local = _req.Session()
        session_local.headers.update({"User-Agent": USER_AGENT})
        # ορισμός proxies; απαιτείται requests[socks] για socks μέσω PySocks
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
# Βοηθητικές & εξαγωγείς
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
        # προσπάθεια αυτόματης εγκατάστασης tor μέσω κοινών διαχειριστών πακέτων (προσπάθεια, μπορεί να απαιτεί δικαιώματα)
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
                    log(f"Προσπάθεια συστηματικής εγκατάστασης tor μέσω: {' '.join(cmd)}")
                    subprocess.check_call(cmd)
                except Exception:
                    pass
        tor_bin = shutil_which("tor")
        if not tor_bin:
            return False, "Δεν βρέθηκε δυαδικό 'tor' μετά από προσπάθειες εγκατάστασης. Παρακαλώ εγκαταστήστε χειροκίνητα (pkg/apt/brew)."
    try:
        p = subprocess.Popen([tor_bin], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(4)
        # γρήγορος έλεγχος
        if is_tor_running():
            return True, f"Εκκίνηση Tor pid={p.pid}"
        return True, f"Εκκίνηση Tor pid={p.pid} (το SOCKS port μπορεί να μην είναι ακόμα ενεργό)"
    except Exception as e:
        return False, f"Αποτυχία εκκίνησης Tor: {e}"

# Regex εξαγωγείς
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

# Βοηθητικές HTML
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
    # εύρωστο safe_get: αν λείπει το session requests, πτώση σε urllib
    if session:
        try:
            r = session.get(url, timeout=timeout, allow_redirects=allow_redirects)
            return r
        except Exception:
            return None
    # πτώση
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

# Σκράπινγκ μίας σελίδας
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
        log(f"Αποθήκευση στιγμιότυπου: {fname}")
    except Exception as e:
        log(f"Σφάλμα αποθήκευσης στιγμιότυπου: {e}", "ΣΦΑΛΜΑ")

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
            log(f"Crawling βάθος={depth} url={url}")
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

# Απλή αναζήτηση Ahmia
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

# Εξαγωγές
def save_json(name, data):
    path = os.path.join(RESULTS_DIR, name)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        log(f"Αποθήκευση JSON -> {path}")
        return path
    except Exception as e:
        log(f"Σφάλμα αποθήκευσης JSON: {e}", "ΣΦΑΛΜΑ")
        return None


def save_csv(name, data):
    path = os.path.join(RESULTS_DIR, name)
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["url","status","title","emails","phones","btc","xmr","pgp_count","links_count","fetched_at"])
            for d in data:
                w.writerow([d.get("url",""), d.get("status",""), (d.get("title") or "").replace("\n"," "), ";".join(d.get("emails",[])), ";".join(d.get("phones",[])), ";".join(d.get("btc",[])), ";".join(d.get("xmr",[])), len(d.get("pgp",[])), len(d.get("links",[])), d.get("fetched_at","")])
        log(f"Αποθήκευση CSV -> {path}")
        return path
    except Exception as e:
        log(f"Σφάλμα αποθήκευσης CSV: {e}", "ΣΦΑΛΜΑ")
        return None


def save_txt(name, data):
    path = os.path.join(RESULTS_DIR, name)
    try:
        with open(path, "w", encoding="utf-8") as f:
            for d in data:
                f.write(f"URL: {d.get('url','')}\n")
                f.write(f"Κατάσταση: {d.get('status','')}\n")
                f.write(f"Τίτλος: {d.get('title','')}\n")
                f.write(f"Emails: {','.join(d.get('emails',[]))}\n")
                f.write("-"*40 + "\n")
        log(f"Αποθήκευση TXT -> {path}")
        return path
    except Exception as e:
        log(f"Σφάλμα αποθήκευσης TXT: {e}", "ΣΦΑΛΜΑ")
        return None

# Φορτωτής & εκτελεστής plugins
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
                log(f"Φόρτωση plugin: {fname}")
            else:
                log(f"Το plugin {fname} δεν έχει run(data) συνάρτηση; παραλείφθηκε", "ΠΡΟΣΟΧΗ")
        except Exception as e:
            log(f"Αποτυχία φόρτωσης plugin {fname}: {e}", "ΣΦΑΛΜΑ")
    return plugins


def run_plugins(plugins, data):
    for p in plugins:
        try:
            out = p["run"](data)
            if out is not None:
                data = out
        except Exception as e:
            log(f"Σφάλμα plugin {p['name']}: {e}", "ΣΦΑΛΜΑ")
    return data

# -------------------------
# Συναρτήσεις Curses UI
# -------------------------
# (αμετάβλητες από το πρωτότυπο αλλά βελτιωμένες προστασίες)

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
        f"Κατάλογος αποτελεσμάτων: {RESULTS_DIR}",
        f"Tor socks: {DEFAULT_SOCKS}",
        f"Tor ενεργό: {is_tor_running()}",
        f"Plugins: {len(os.listdir(PLUGINS_DIR)) if os.path.isdir(PLUGINS_DIR) else 0} εγκατεστημένα"
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
        stdscr.addstr(h-2, 0, "Χρησιμοποιήστε ↑↓ για πλοήγηση, Enter για επιλογή, q για έξοδο")
    else:
        stdscr.addstr(h-2, 0, f"Εισάγετε αριθμό (1-{len(menu_items)}) για επιλογή, q για έξοδο")
    stdscr.refresh()


def get_user_input(stdscr, prompt, default=""):
    curses.echo()
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    stdscr.addstr(0, 0, prompt)
    if default:
        stdscr.addstr(1, 0, f"Προεπιλογή: {default}")
        stdscr.addstr(2, 0, "Είσοδος: ")
    else:
        stdscr.addstr(1, 0, "Είσοδος: ")
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
    stdscr.addstr(h-1, 0, "Πατήστε οποιοδήποτε πλήκτρο για συνέχεια...")
    stdscr.refresh()
    stdscr.getch()


def curses_menu(stdscr):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
    
    menu_style = "list"  # "list" ή "number"
    
    menu_items = [
        "Εγκατάσταση παραδειγματικών plugins",
        "Έλεγχος/εκκίνηση Tor",
        "Crawl σε URL",
        "Αναζήτηση Ahmia",
        "Φόρτωση & εκτέλεση plugins σε τελευταία αποτελέσματα",
        "Εξαγωγή τελευταίων αποτελεσμάτων (json/csv/txt)",
        "Επιλογή Στυλ Μενού",
        "Έξοδος"
    ]
    current_selection = 0
    status_msg = ""
    while True:
        draw_menu(stdscr, current_selection, menu_items, "TorBot All-in-One", status_msg, menu_style)
        status_msg = ""
        key = stdscr.getch()

        selected_action_index = -1  # Σημαία για καμία ενέργεια

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
                    # '1' αντιστοιχεί σε δείκτη 0
                    selected_action_index = int(chr(key)) - 1
                except ValueError:
                    pass  # Μη έγκυρος αριθμός

        # --- Χειρισμός επιλεγμένης ενέργειας ---
        if selected_action_index == -1:
            continue  # Δεν επιλέχθηκε ενέργεια, συνέχεια βρόχου

        # --- Επεξεργασία ενέργειας ---
        if selected_action_index == 0:  # Εγκατάσταση plugins
            installed = install_plugins()
            status_msg = f"Εγκαταστάθηκαν {len(installed)} plugins: {', '.join(installed)}"
        elif selected_action_index == 1:  # Έλεγχος/εκκίνηση Tor
            if is_tor_running():
                status_msg = "[*] Το Tor φαίνεται να τρέχει (SOCKS ανοιχτό)."
            else:
                ok, msg = try_start_tor_background()
                status_msg = f"[*] try_start_tor_background -> {ok}, {msg}"
                time.sleep(1)
                if is_tor_running():
                    create_session(DEFAULT_SOCKS)
                    status_msg += " Το Tor τρέχει και το session ρυθμίστηκε."
                else:
                    status_msg += " Το Tor ακόμα δεν τρέχει."
        elif selected_action_index == 2:  # Crawl
            url = get_user_input(stdscr, "Εισάγετε URL εκκίνησης (.onion ή http):")
            if not url:
                status_msg = "Δεν δόθηκε URL, παράλειψη crawl."
                continue
            max_pages = get_user_input(stdscr, "Μέγιστος αριθμός σελίδων:", "200")
            depth = get_user_input(stdscr, "Μέγιστο βάθος:", "2")
            same_domain = get_user_input(stdscr, "Μόνο ίδιο domain? (y/N):", "n").lower().startswith('y')
            save_snap = get_user_input(stdscr, "Αποθήκευση στιγμιότυπων? (y/N):", "n").lower().startswith('y')
            socks_proxy = get_user_input(stdscr, f"SOCKS proxy:", DEFAULT_SOCKS)
            try:
                max_pages = int(max_pages)
                depth = int(depth)
            except:
                max_pages = 200
                depth = 2
            if not is_tor_running() and (".onion" in url):
                status_msg = "[*] Δεν εντοπίστηκε Tor SOCKS; προσπάθεια αυτόματης εκκίνησης Tor."
                ok, msg = try_start_tor_background()
                status_msg += f" Αποτέλεσμα: {ok}, {msg}"
            set_socks(socks_proxy or DEFAULT_SOCKS)
            create_session(socks_proxy or DEFAULT_SOCKS)
            show_message(stdscr, "Εκκίνηση crawl... Αυτό μπορεί να πάρει λίγο χρόνο.")
            out = crawl(url, max_pages=max_pages, max_depth=depth,
                       same_domain=same_domain, save_snapshots=save_snap, verbose=False)
            # Εκτέλεση plugins
            plugins = load_plugins()
            if plugins:
                out = run_plugins(plugins, out)
            # Αποθήκευση εξαγωγών
            fn_json = save_json(f"crawl_{int(time.time())}.json", out)
            save_csv(f"crawl_{int(time.time())}.csv", out)
            save_txt(f"crawl_{int(time.time())}.txt", out)
            status_msg = f"Ολοκλήρωση crawl. Βρέθηκαν {len(out)} σελίδες. JSON: {fn_json}"
        elif selected_action_index == 3:  # Αναζήτηση
            query = get_user_input(stdscr, "Εισάγετε αναζήτηση:")
            if not query:
                status_msg = "Δεν δόθηκε αναζήτηση, παράλειψη αναζήτησης."
                continue
            limit = get_user_input(stdscr, "Όριο αποτελεσμάτων:", "50")
            socks_proxy = get_user_input(stdscr, f"SOCKS proxy:", DEFAULT_SOCKS)
            try:
                limit = int(limit)
            except:
                limit = 50
            set_socks(socks_proxy or DEFAULT_SOCKS)
            create_session(socks_proxy or DEFAULT_SOCKS)
            show_message(stdscr, "Αναζήτηση... Παρακαλώ περιμένετε.")
            res = search_combined(query, limit=limit)
            if not res:
                status_msg = "Κανένα αποτέλεσμα ή απέτυχε η αναζήτηση Ahmia."
            else:
                save_json(f"search_{int(time.time())}.json", res)
                status_msg = f"Βρέθηκαν {len(res)} αποτελέσματα. Αποθηκεύτηκε σε JSON."
        elif selected_action_index == 4:  # Φόρτωση plugins
            files = [f for f in os.listdir(RESULTS_DIR) if f.startswith("crawl_") and f.endswith(".json")]
            if not files:
                status_msg = "Δεν βρέθηκαν αρχεία αποτελεσμάτων. Εκτελέστε πρώτα crawl."
                continue
            files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(RESULTS_DIR, x)), reverse=True)
            default_file = os.path.join(RESULTS_DIR, files[0])
            file_path = get_user_input(stdscr, "Διαδρομή προς αρχείο JSON αποτελεσμάτων:", default_file)
            if not os.path.isfile(file_path):
                status_msg = f"Αρχείο δεν βρέθηκε: {file_path}"
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                status_msg = f"Αποτυχία φόρτωσης JSON: {e}"
                continue
            plugins = load_plugins()
            if not plugins:
                status_msg = "Δεν φορτώθηκαν plugins."
                continue
            show_message(stdscr, "Εκτέλεση plugins... Παρακαλώ περιμένετε.")
            out = run_plugins(plugins, data)
            save_json(f"plugins_out_{int(time.time())}.json", out)
            status_msg = f"Ολοκλήρωση εκτέλεσης plugins. Επεξεργάστηκε {len(out) if isinstance(out, list) else 1} αντικείμενο(α)."
        elif selected_action_index == 5:  # Εξαγωγή
            files = [f for f in os.listdir(RESULTS_DIR) if f.startswith("crawl_") and f.endswith(".json")]
            if not files:
                status_msg = "Δεν βρέθηκαν αρχεία αποτελεσμάτων. Εκτελέστε πρώτα crawl."
                continue
            files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(RESULTS_DIR, x)), reverse=True)
            default_file = os.path.join(RESULTS_DIR, files[0])
            file_path = get_user_input(stdscr, "Διαδρομή προς αρχείο JSON αποτελεσμάτων:", default_file)
            if not os.path.isfile(file_path):
                status_msg = f"Αρχείο δεν βρέθηκε: {file_path}"
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                status_msg = f"Αποτυχία φόρτωσης JSON: {e}"
                continue
            save_csv(f"export_{int(time.time())}.csv", data)
            save_txt(f"export_{int(time.time())}.txt", data)
            status_msg = f"Ολοκλήρωση εξαγωγής. Επεξεργάστηκε {len(data)} αντικείμενο(α)."
        elif selected_action_index == 6:  # Επιλογή Στυλ Μενού
            prompt = "Επιλογή Στυλ Μενού:\n1. Στυλ Λίστας (Βέλη)\n2. Στυλ Αριθμών (1, 2, 3...)\n\nΕπιλογή: "
            stdscr.clear()
            stdscr.addstr(0, 0, prompt)
            stdscr.refresh()
            curses.echo()  # Ενεργοποίηση echo για αυτό
            try:
                choice = stdscr.getstr(4, 13, 1).decode('utf-8').strip()
            except Exception:
                choice = ""
            curses.noecho()  # Απενεργοποίηση πάλι

            if choice == "1":
                menu_style = "list"
                status_msg = "Στυλ μενού ορίστηκε σε Λίστα."
            elif choice == "2":
                menu_style = "number"
                status_msg = "Στυλ μενού ορίστηκε σε Αριθμούς."
                current_selection = 0  # Επαναφορά επιλογής
            else:
                status_msg = "Μη έγκυρη επιλογή. Καμία αλλαγή."
        elif selected_action_index == 7:  # Έξοδος
            break

# -------------------------
# Διεπαφή γραμμής εντολών (διατηρημένη για συμβατότητα)
# -------------------------

def cmd_install_plugins(args):
    installed = install_plugins()
    print(f"Εγκατεστημένα plugins: {installed}")


def cmd_check_start_tor(args):
    if is_tor_running():
        print("[*] Το Tor φαίνεται να τρέχει (SOCKS ανοιχτό).")
        return
    ok, msg = try_start_tor_background()
    print("[*] try_start_tor_background ->", ok, msg)
    time.sleep(1)
    if is_tor_running():
        create_session(DEFAULT_SOCKS)
        print("[*] Το Tor τρέχει και το session ρυθμίστηκε να το χρησιμοποιεί.")
    else:
        print("[!] Το Tor ακόμα δεν τρέχει. Μπορείτε να εγκαταστήσετε και να τρέξετε 'tor' (pkg install tor) ή να τρέξετε Orbot/Termux-Tor.")


def cmd_crawl(args):
    url = args.url or input("URL εκκίνησης (.onion ή http): ").strip()
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
        print("[*] Δεν εντοπίστηκε Tor SOCKS; προσπάθεια αυτόματης εκκίνησης Tor.")
        cmd_check_start_tor(args)
    create_session(args.socks or DEFAULT_SOCKS)
    out = crawl(url, max_pages=max_pages, max_depth=depth, same_domain=same_domain, save_snapshots=save_snap, verbose=not args.quiet)
    # εκτέλεση plugins
    plugins = load_plugins()
    if plugins:
        out = run_plugins(plugins, out)
    # αποθήκευση εξαγωγών
    fn_json = save_json(f"crawl_{int(time.time())}.json", out)
    save_csv(f"crawl_{int(time.time())}.csv", out)
    save_txt(f"crawl_{int(time.time())}.txt", out)
    print("[*] Ολοκλήρωση crawl. JSON:", fn_json)


def cmd_search(args):
    q = args.query or input("Αναζήτηση: ").strip()
    set_socks(args.socks or DEFAULT_SOCKS)
    create_session(args.socks or DEFAULT_SOCKS)
    res = search_combined(q, limit=args.limit)
    if not res:
        print("[!] Κανένα αποτέλεσμα ή απέτυχε η αναζήτηση Ahmia.")
        return
    print(f"Βρέθηκαν {len(res)} αποτελέσματα:")
    for i, r in enumerate(res, 1):
        print(f"{i}) {r.get('title')} — {r.get('url')}")
    save_json(f"search_{int(time.time())}.json", res)


def cmd_run_plugins_on_file(args):
    path = args.file or input("Διαδρομή προς αρχείο JSON αποτελεσμάτων (προεπιλογή τελευταίο crawl JSON στον κατάλογο αποτελεσμάτων): ").strip()
    if not path:
        files = [f for f in os.listdir(RESULTS_DIR) if f.startswith("crawl_") and f.endswith(".json")]
        files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(RESULTS_DIR, x)), reverse=True)
        if not files:
            print("[!] Δεν βρέθηκαν αρχεία αποτελεσμάτων.")
            return
        path = os.path.join(RESULTS_DIR, files[0])
    if not os.path.isfile(path):
        print("[!] Αρχείο δεν βρέθηκε:", path)
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print("[!] Αποτυχία φόρτωσης JSON:", e)
        return
    plugins = load_plugins()
    if not plugins:
        print("[!] Δεν φορτώθηκαν plugins.")
        return
    out = run_plugins(plugins, data)
    save_json(f"plugins_out_{int(time.time())}.json", out)
    print("[*] Ολοκλήρωση εκτέλεσης plugins. Αποθηκεύτηκε έξοδος.")


def cmd_export(args):
    path = args.file or input("Διαδρομή προς αρχείο JSON αποτελεσμάτων (προεπιλογή τελευταίο crawl JSON): ").strip()
    if not path:
        files = [f for f in os.listdir(RESULTS_DIR) if f.startswith("crawl_") and f.endswith(".json")]
        files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(RESULTS_DIR, x)), reverse=True)
        if not files:
            print("[!] Δεν βρέθηκαν αρχεία αποτελεσμάτων.")
            return
        path = os.path.join(RESULTS_DIR, files[0])
    if not os.path.isfile(path):
        print("[!] Αρχείο δεν βρέθηκε:", path)
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print("[!] Αποτυχία φόρτωσης JSON:", e)
        return
    save_csv(f"export_{int(time.time())}.csv", data)
    save_txt(f"export_{int(time.time())}.txt", data)
    print("[*] Ολοκλήρωση εξαγωγής.")


def main_cli():
    p = argparse.ArgumentParser(prog="dark.py", description="TorBot All-in-One (Termux)")
    sub = p.add_subparsers(dest="cmd")
    sub_install = sub.add_parser("install-plugins", help="Εγγραφή παραδειγματικών plugins στον κατάλογο plugins")
    sub_install.set_defaults(func=cmd_install_plugins)
    sub_tor = sub.add_parser("tor", help="Έλεγχος/εκκίνηση Tor")
    sub_tor.set_defaults(func=cmd_check_start_tor)
    sub_crawl = sub.add_parser("crawl", help="Crawl σε URL εκκίνησης")
    sub_crawl.add_argument("url", nargs="?", help="URL εκκίνησης")
    sub_crawl.add_argument("--max-pages", dest="max_pages", default=200, help="Μέγιστος αριθμός σελίδων")
    sub_crawl.add_argument("--depth", dest="depth", default=2, help="Μέγιστο βάθος")
    sub_crawl.add_argument("--no-same-domain", dest="no_same_domain", action="store_true", help="Να μην περιοριστεί στο ίδιο domain")
    sub_crawl.add_argument("--snapshot", dest="snapshot", action="store_true", help="Αποθήκευση στιγμιότυπων")
    sub_crawl.add_argument("--socks", dest="socks", help="SOCKS proxy (π.χ. socks5h://127.0.0.1:9050)")
    sub_crawl.add_argument("--quiet", dest="quiet", action="store_true")
    sub_crawl.add_argument("--force-tor", dest="force_tor", action="store_true", help="Εξαναγκασμός Tor αν .onion")
    sub_crawl.set_defaults(func=cmd_crawl)
    sub_search = sub.add_parser("search", help="Αναζήτηση Ahmia")
    sub_search.add_argument("query", nargs="?", help="Αναζήτηση")
    sub_search.add_argument("--limit", type=int, default=50)
    sub_search.add_argument("--socks", dest="socks", help="SOCKS proxy")
    sub_search.set_defaults(func=cmd_search)
    sub_plugins = sub.add_parser("run-plugins", help="Εκτέλεση plugins σε αρχείο JSON αποτελεσμάτων")
    sub_plugins.add_argument("--file", "-f", help="Διαδρομή προς αρχείο JSON")
    sub_plugins.set_defaults(func=cmd_run_plugins_on_file)
    sub_export = sub.add_parser("export", help="Εξαγωγή JSON αποτελεσμάτων σε CSV/TXT")
    sub_export.add_argument("--file", "-f", help="Διαδρομή προς αρχείο JSON")
    sub_export.set_defaults(func=cmd_export)
    # επιπλέον: αυτόματη εγκατάσταση εξαρτήσεων / έλεγχος
    sub_deps = sub.add_parser("ensure-deps", help="Προσπάθεια αυτόματης εγκατάστασης python εξαρτήσεων και προαιρετικό tor")
    sub_deps.add_argument("--install-tor", action="store_true", help="Επίσης προσπάθεια εγκατάστασης tor μέσω διαχειριστή πακέτων (μπορεί να απαιτεί δικαιώματα)")
    sub_deps.set_defaults(func=lambda args: print(ensure_dependencies(), try_start_tor_background() if args.install_tor else None))

    args = p.parse_args()
    if not args.cmd:
        # Χρήση διεπαφής curses; αν αποτύχει, πτώση σε απλή CLI
        try:
            curses.wrapper(curses_menu)
            return
        except Exception:
            print("[!] Το curses δεν είναι διαθέσιμο ή απέτυχε; πτώση σε λειτουργία CLI.")
    # κλήση υποεντολής
    try:
        args.func(args)
    except Exception as e:
        print("[!] Σφάλμα εκτέλεσης εντολής:", e)

if __name__ == "__main__":
    # διασφάλιση περιβάλλοντος για plugins
    os.environ["TORBOT_RESULTS_DIR"] = RESULTS_DIR
    main_cli()