#!/usr/bin/env python3
# Store Scrapper.py (v10.4) — Termux Universal Store Scraper (No-root)
# - Auto-installs pip deps ONLY if missing + termux-setup-storage best-effort
# - Multi-strategy collection: Sitemap → Shopify/Woo/Nike APIs → HTML crawl → Domain crawler → optional headless/API sniff
# - INLINE_CATALOG fallback for single-page catalogs like /Pages/store.html (DedSec-style)
# - Deep per-product scrape (optional): JSON-LD + meta + images + variants/sizes + reviews (when available)
# - Resume mode + SQLite + CSV/XLSX export + product folders + image downloads
# - Proxy rotation + exponential backoff + UA rotation + per-URL strategy memory + analytics

import os, sys, re, json, time, hashlib, random, sqlite3, subprocess, shutil
from urllib.parse import urlparse, urljoin, urldefrag, unquote, parse_qsl, urlencode, urlunparse
from pathlib import Path
from collections import deque, defaultdict

# ============================================================
# Auto-install (ONLY if missing) — Termux friendly bootstrap
# ============================================================
PIP_REQUIRED = {
    "requests": "requests",
    "bs4": "beautifulsoup4",
    "openpyxl": "openpyxl",
}
PIP_OPTIONAL = {
    # Optional faster parser; if it fails, we continue.
    "lxml": "lxml",
}

def _run(cmd):
    return subprocess.check_call(cmd)

def _pip_install(pkg):
    _run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--no-input", pkg])

def _pip_upgrade_safe_tools():
    """Termux note: upgrading pip can break the python-pip package.
    We ONLY (best-effort) ensure setuptools/wheel are present.
    """
    try:
        _run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--upgrade",
              "setuptools", "wheel"])
    except Exception:
        pass

def ensure_termux_storage():
    """
    Best-effort to enable /storage access.
    Android will still prompt permission once.
    """
    home = str(Path.home())
    if os.path.isdir(os.path.join(home, "storage")):
        return
    if shutil.which("termux-setup-storage"):
        try:
            print("📁 Ενεργοποίηση πρόσβασης αποθήκευσης στο Termux (το Android μπορεί να ζητήσει άδεια μία φορά)...")
            subprocess.call(["termux-setup-storage"])
            time.sleep(1.0)
        except Exception:
            pass

def ensure_import(mod: str, pip_name: str, optional: bool = False):
    try:
        __import__(mod)
        return True
    except Exception:
        try:
            _pip_install(pip_name)
            __import__(mod)
            return True
        except Exception:
            if optional:
                print(f"⚠️ Optional dependency '{pip_name}' could not be installed. Continuing without it.")
                return False
            raise

def bootstrap_dependencies():
    """
    Installs ONLY missing deps.
    Upgrades pip tooling once (best-effort).
    """
    try:
        import pip  # noqa: F401
    except Exception:
        if shutil.which("pkg"):
            print("🔧 Installing Python via Termux pkg (to ensure pip exists)...")
            subprocess.call(["pkg", "install", "-y", "python"])
        import pip  # noqa: F401

    _pip_upgrade_safe_tools()

    for mod, pkg in PIP_REQUIRED.items():
        ensure_import(mod, pkg, optional=False)
    for mod, pkg in PIP_OPTIONAL.items():
        ensure_import(mod, pkg, optional=True)

bootstrap_dependencies()
ensure_termux_storage()

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook

try:
    import lxml  # noqa: F401
    HAVE_LXML = True
except Exception:
    HAVE_LXML = False

# ============================================================
# Config (low-end friendly defaults)
# ============================================================
UA_POOL = [
    "Mozilla/5.0 (Linux; Android 13; Termux) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Mobile Safari/537.36",
]
DEFAULT_UA = UA_POOL[0]

TIMEOUT = 25
BASE_DELAY = 0.6

MAX_LISTING_PAGES = 80
MAX_PRODUCT_URLS = 1200
MAX_IMAGES_PER_PRODUCT = 24
MAX_REVIEWS_PER_PRODUCT = 30

SHOPIFY_MAX_PAGES = 60
WOOCOMMERCE_MAX_PAGES = 60
NIKE_MAX_PAGES = 20

MAX_ATTEMPTS_PER_STRATEGY = 3
BACKOFF_BASE = 0.8
BACKOFF_MAX = 25.0

PRODUCT_HINTS = ("/product", "/products", "/p/", "/item", "/shop", "/prod")
PAGINATION_HINTS = ("page=", "/page/", "?p=", "?pg=", "start=", "offset=", "from=", "p=")

CRAWLER_MAX_PAGES_DEFAULT = 500
CRAWLER_MAX_DEPTH_DEFAULT = 4
CRAWLER_MAX_RUNTIME_SEC_DEFAULT = 15 * 60  # 15 minutes

# ============================================================
# Helpers
# ============================================================
def parser_name():
    return "lxml" if HAVE_LXML else "html.parser"

def sleep(sec=BASE_DELAY):
    time.sleep(max(0.0, float(sec)))

def md5(s: str, n=10):
    return hashlib.md5((s or "").encode("utf-8", "ignore")).hexdigest()[:n]

def slug(s: str, max_len=80):
    s = (s or "").strip().lower()
    s = re.sub(r"https?://", "", s)
    s = re.sub(r"[^\w]+", "_", s).strip("_")
    return (s[:max_len] or "site")

def normalize_url(u: str):
    u = (u or "").strip()
    u, _ = urldefrag(u)
    return u

def downloads_dir():
    home = str(Path.home())
    for p in [
        os.path.join(home, "storage", "downloads"),
        "/storage/emulated/0/Download",
        "/sdcard/Download",
    ]:
        if os.path.isdir(p):
            return p
    return os.path.join(home, "Download")

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def clean_text(s: str, max_len: int = 5000):
    s = (s or "").replace("\x00", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s[:max_len]

def is_probably_product(u: str):
    p = urlparse(u).path.lower()
    return any(h in p for h in PRODUCT_HINTS)

def is_probably_pagination(u: str):
    p = urlparse(u).path.lower()
    q = urlparse(u).query.lower()
    return any(h in p for h in PAGINATION_HINTS) or any(h in q for h in PAGINATION_HINTS)

def strip_tracking_params(u: str):
    try:
        pu = urlparse(u)
        qs = parse_qsl(pu.query, keep_blank_values=True)
        filtered = []
        for k, v in qs:
            lk = k.lower()
            if lk.startswith("utm_") or lk in ("fbclid", "gclid", "msclkid", "igshid"):
                continue
            filtered.append((k, v))
        new_q = urlencode(filtered, doseq=True)
        return urlunparse((pu.scheme, pu.netloc, pu.path, pu.params, new_q, pu.fragment))
    except Exception:
        return u

def best_currency_from_text(t: str):
    t = (t or "")
    if "€" in t or "EUR" in t or "eur" in t: return "EUR"
    if "$" in t or "USD" in t or "usd" in t: return "USD"
    if "£" in t or "GBP" in t or "gbp" in t: return "GBP"
    return None

# ============================================================
# Proxy rotation + backoff + UA rotation
# ============================================================
def parse_proxy_list(text: str):
    text = (text or "").strip()
    if not text:
        return []
    parts = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts.extend([x.strip() for x in line.split(",") if x.strip()])
    return parts

class Net:
    def __init__(self, proxies):
        self.session = requests.Session()
        self.proxies = proxies or []
        self.proxy_idx = 0
        self.proxy_stats = defaultdict(lambda: {"ok": 0, "fail": 0})
        self.ua_idx = 0

    def _pick_proxy(self):
        if not self.proxies:
            return None, None
        p = self.proxies[self.proxy_idx % len(self.proxies)]
        self.proxy_idx += 1
        return p, {"http": p, "https": p}

    def _pick_ua(self):
        self.ua_idx += 1
        return UA_POOL[self.ua_idx % len(UA_POOL)]

    def get_once(self, url, headers=None, params=None, stream=False):
        p_raw, p = self._pick_proxy()
        ua = self._pick_ua()
        hdr = dict(headers or {})
        hdr.setdefault("User-Agent", ua)
        try:
            r = self.session.get(
                url,
                headers=hdr,
                params=params,
                timeout=TIMEOUT,
                allow_redirects=True,
                proxies=p,
                stream=stream
            )
            if p_raw:
                self.proxy_stats[p_raw]["ok"] += 1
            return r, p_raw, None
        except Exception as e:
            if p_raw:
                self.proxy_stats[p_raw]["fail"] += 1
            return None, p_raw, e

    def get(self, url, headers=None, params=None, stream=False, max_attempts=3):
        backoff = BACKOFF_BASE
        last_err = None
        for _ in range(max_attempts):
            r, _, err = self.get_once(url, headers=headers, params=params, stream=stream)
            if r is not None:
                if r.status_code in (429, 403):
                    last_err = Exception(f"HTTP {r.status_code}")
                    sleep(backoff + random.random())
                    backoff = min(BACKOFF_MAX, backoff * 2.0)
                    continue
                return r, None, None
            last_err = err
            sleep(backoff + random.random() * 0.5)
            backoff = min(BACKOFF_MAX, backoff * 2.0)
        return None, None, last_err

# ============================================================
# Headless OPTIONAL (Playwright) — Termux-safe (no spam)
# ============================================================
_HEADLESS = {"checked": False, "available": False, "warned": False}

def headless_available():
    """
    Try ONCE to enable Playwright.
    If Termux can't install it, disable headless quietly.
    """
    global _HEADLESS
    if _HEADLESS["checked"]:
        return _HEADLESS["available"]
    _HEADLESS["checked"] = True

    if os.environ.get("STORE_SCRAPER_NO_HEADLESS", "").strip() == "1":
        _HEADLESS["available"] = False
        return False

    try:
        import playwright  # noqa: F401
    except Exception:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "playwright"])
        except Exception:
            _HEADLESS["available"] = False
            return False

    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        _HEADLESS["available"] = True
        return True
    except Exception:
        _HEADLESS["available"] = False
        return False

def headless_warn_once():
    global _HEADLESS
    if not _HEADLESS["warned"]:
        _HEADLESS["warned"] = True
        print("\n⚠️ Headless disabled: Playwright isn't available in this Termux environment.")
        print("   \u03a3\u03c5\u03bd\u03b5\u03c7\u03af\u03b6\u03c9 \u03bc\u03b5 sitemap/API/crawler/deep HTML (\u03b4\u03bf\u03c5\u03bb\u03b5\u03cd\u03b5\u03b9 \u03c3\u03c4\u03b1 \u03c0\u03b5\u03c1\u03b9\u03c3\u03c3\u03cc\u03c4\u03b5\u03c1\u03b1 \u03ba\u03b1\u03c4\u03b1\u03c3\u03c4\u03ae\u03bc\u03b1\u03c4\u03b1).\n")

def headless_fetch_html(url: str, timeout_ms=55000):
    if not headless_available():
        headless_warn_once()
        return None, None
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=DEFAULT_UA)
        page = ctx.new_page()

        def route_handler(route):
            rt = route.request.resource_type
            if rt in ("image", "media", "font"):
                return route.abort()
            return route.continue_()
        page.route("**/*", route_handler)

        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(1800)
        html = page.content()
        final = page.url
        ctx.close()
        browser.close()
        return final, html

def headless_sniff_api(url: str, timeout_ms=65000):
    if not headless_available():
        headless_warn_once()
        return []
    from playwright.sync_api import sync_playwright

    found = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=DEFAULT_UA)

        def on_response(res):
            try:
                ctype = (res.headers.get("content-type") or "").lower()
                if "json" not in ctype:
                    return
                j = res.json()
                if isinstance(j, dict) and any(k in j for k in ("products", "items", "results", "data")):
                    found.append(res.url)
            except Exception:
                pass

        page.on("response", on_response)
        page.goto(url, wait_until="networkidle", timeout=timeout_ms)
        page.wait_for_timeout(2500)
        browser.close()

    out, seen = [], set()
    for u in found:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out

# ============================================================
# Robots.txt (basic) + Crawl-delay + Sitemaps
# ============================================================
def fetch_robots(net: Net, base: str):
    r, _, _ = net.get(base + "/robots.txt", headers={"User-Agent": DEFAULT_UA}, max_attempts=2)
    if r is None or r.status_code != 200:
        return ""
    return r.text or ""

def parse_robots(text: str):
    disallow, allow, sitemaps = [], [], []
    crawl_delay = None

    ua_block = False
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        low = line.lower()

        if low.startswith("user-agent:"):
            ua = line.split(":", 1)[1].strip()
            ua_block = (ua == "*" or ua == "* ")
            continue

        if low.startswith("sitemap:"):
            sm = line.split(":", 1)[1].strip()
            if sm.startswith("http"):
                sitemaps.append(sm)
            continue

        if not ua_block:
            continue

        if low.startswith("disallow:"):
            path = line.split(":", 1)[1].strip()
            if path:
                disallow.append(path)
            continue

        if low.startswith("allow:"):
            path = line.split(":", 1)[1].strip()
            if path:
                allow.append(path)
            continue

        if low.startswith("crawl-delay:"):
            val = line.split(":", 1)[1].strip()
            try:
                crawl_delay = float(val)
            except Exception:
                crawl_delay = None

    return disallow, allow, crawl_delay, sitemaps

def robots_allowed(url: str, base: str, disallow, allow):
    try:
        path = urlparse(url).path or "/"
    except Exception:
        return True

    for a in allow:
        if a == "/":
            return True
        if path.startswith(a):
            return True

    for d in disallow:
        if d == "/":
            return False
        if path.startswith(d):
            return False

    return True

# ============================================================
# SQLite
# ============================================================
def db_connect(run_dir):
    conn = sqlite3.connect(os.path.join(run_dir, "store.db"))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def db_init(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS products (
      id TEXT PRIMARY KEY,
      engine TEXT,
      name TEXT,
      brand TEXT,
      url TEXT,
      sku TEXT,
      gtin TEXT,
      mpn TEXT,
      availability TEXT,
      price TEXT,
      currency TEXT,
      description TEXT,
      categories TEXT,
      attributes_json TEXT,
      rating REAL,
      review_count INTEGER,
      fetched_with TEXT,
      updated_at INTEGER
    );

    CREATE TABLE IF NOT EXISTS variants (
      id TEXT PRIMARY KEY,
      product_id TEXT,
      title TEXT,
      sku TEXT,
      price TEXT,
      available INTEGER,
      size TEXT
    );

    CREATE TABLE IF NOT EXISTS images (
      id TEXT PRIMARY KEY,
      product_id TEXT,
      url TEXT,
      local_path TEXT
    );

    CREATE TABLE IF NOT EXISTS reviews (
      id TEXT PRIMARY KEY,
      product_id TEXT,
      author TEXT,
      rating REAL,
      title TEXT,
      body TEXT,
      date TEXT
    );
    """)

    # --- Migration: older versions used UNIQUE(url), which breaks inline catalogs (multiple items share a page URL).
    try:
        row = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='products'").fetchone()
        if row and row[0] and "url TEXT UNIQUE" in row[0]:
            # Create new table without UNIQUE(url)
            conn.executescript("""
            ALTER TABLE products RENAME TO products_old;
            CREATE TABLE IF NOT EXISTS products (
              id TEXT PRIMARY KEY,
              engine TEXT,
              name TEXT,
              brand TEXT,
              url TEXT,
              sku TEXT,
              gtin TEXT,
              mpn TEXT,
              availability TEXT,
              price TEXT,
              currency TEXT,
              description TEXT,
              categories TEXT,
              attributes_json TEXT,
              rating REAL,
              review_count INTEGER,
              fetched_with TEXT,
              updated_at INTEGER
            );
            INSERT INTO products
              (id, engine, name, brand, url, sku, gtin, mpn, availability, price, currency,
               description, categories, attributes_json, rating, review_count, fetched_with, updated_at)
            SELECT
              id, engine, name, brand, url, sku, gtin, mpn, availability, price, currency,
              description, categories, attributes_json, rating, review_count, fetched_with, updated_at
            FROM products_old;
            DROP TABLE products_old;
            """)
    except Exception:
        # If migration fails for any reason, continue with current schema.
        pass

    conn.commit()

def upsert_product(conn, p):
    now = int(time.time())
    # Inline catalogs may share URLs; url is not required to be unique in v10.5.
    try:
        conn.execute("""
    INSERT INTO products(
      id, engine, name, brand, url, sku, gtin, mpn, availability, price, currency,
      description, categories, attributes_json, rating, review_count, fetched_with, updated_at
    )
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ON CONFLICT(id) DO UPDATE SET
      engine=excluded.engine,
      name=excluded.name,
      brand=excluded.brand,
      url=excluded.url,
      sku=excluded.sku,
      gtin=excluded.gtin,
      mpn=excluded.mpn,
      availability=excluded.availability,
      price=excluded.price,
      currency=excluded.currency,
      description=excluded.description,
      categories=excluded.categories,
      attributes_json=excluded.attributes_json,
      rating=excluded.rating,
      review_count=excluded.review_count,
      fetched_with=excluded.fetched_with,
      updated_at=excluded.updated_at
    """, (
        p["id"], p.get("engine"), p.get("name"), p.get("brand"), p.get("url"),
        p.get("sku"), p.get("gtin"), p.get("mpn"), p.get("availability"),
        str(p.get("price") or ""), str(p.get("currency") or ""),
        (p.get("description") or "")[:20000],
        json.dumps(p.get("categories") or [], ensure_ascii=False),
        json.dumps(p.get("attributes") or {}, ensure_ascii=False),
        p.get("review_rating"), p.get("review_count"),
        p.get("fetched_with"), now
        ))
    except sqlite3.IntegrityError:
        # If some old DB still enforces UNIQUE(url), make url unique and retry.
        p2 = dict(p)
        p2['url'] = (p.get('url') or '') + '#dup-' + md5(p.get('id') or p.get('url') or '', 8)
        conn.execute("""
        INSERT INTO products(
          id, engine, name, brand, url, sku, gtin, mpn, availability, price, currency,
          description, categories, attributes_json, rating, review_count, fetched_with, updated_at
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
          engine=excluded.engine,
          name=excluded.name,
          brand=excluded.brand,
          url=excluded.url,
          sku=excluded.sku,
          gtin=excluded.gtin,
          mpn=excluded.mpn,
          availability=excluded.availability,
          price=excluded.price,
          currency=excluded.currency,
          description=excluded.description,
          categories=excluded.categories,
          attributes_json=excluded.attributes_json,
          rating=excluded.rating,
          review_count=excluded.review_count,
          fetched_with=excluded.fetched_with,
          updated_at=excluded.updated_at
        """, (
            p2['id'], p2.get('engine'), p2.get('name'), p2.get('brand'), p2.get('url'),
            p2.get('sku'), p2.get('gtin'), p2.get('mpn'), p2.get('availability'),
            str(p2.get('price') or ''), str(p2.get('currency') or ''),
            (p2.get('description') or '')[:20000],
            json.dumps(p2.get('categories') or [], ensure_ascii=False),
            json.dumps(p2.get('attributes') or {}, ensure_ascii=False),
            p2.get('review_rating'), p2.get('review_count'),
            p2.get('fetched_with'), now
        ))
    conn.commit()

def replace_children(conn, pid, variants, images, reviews):
    conn.execute("DELETE FROM variants WHERE product_id=?", (pid,))
    conn.execute("DELETE FROM images WHERE product_id=?", (pid,))
    conn.execute("DELETE FROM reviews WHERE product_id=?", (pid,))

    for v in variants or []:
        vid = v.get("id") or (pid + "_v_" + md5(json.dumps(v, ensure_ascii=False), 10))
        conn.execute("""
        INSERT INTO variants(id, product_id, title, sku, price, available, size)
        VALUES(?,?,?,?,?,?,?)
        """, (
            vid, pid, v.get("title"), v.get("sku"),
            str(v.get("price") or ""),
            1 if v.get("available") else 0,
            v.get("size")
        ))

    for im in images or []:
        iid = pid + "_i_" + md5(im.get("url") or "", 10)
        conn.execute("""
        INSERT INTO images(id, product_id, url, local_path)
        VALUES(?,?,?,?)
        """, (iid, pid, im.get("url"), im.get("local_path")))

    for r in reviews or []:
        rid = pid + "_r_" + md5((r.get("author") or "") + (r.get("body") or ""), 10)
        conn.execute("""
        INSERT INTO reviews(id, product_id, author, rating, title, body, date)
        VALUES(?,?,?,?,?,?,?)
        """, (
            rid, pid, r.get("author"), r.get("rating"), r.get("title"),
            (r.get("body") or "")[:4000], r.get("date")
        ))
    conn.commit()

def export_csv_xlsx(run_dir, conn):
    rows = conn.execute("""
    SELECT name, brand, url, engine, sku, availability, price, currency, rating, review_count, updated_at
    FROM products ORDER BY updated_at DESC
    """).fetchall()
    headers = ["name","brand","url","engine","sku","availability","price","currency","rating","review_count","updated_at"]

    import csv
    csv_path = os.path.join(run_dir, "products.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for r in rows:
            w.writerow(list(r))

    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for r in rows:
        ws.append(list(r))
    wb.save(os.path.join(run_dir, "products.xlsx"))

# ============================================================
# State/Resume + analytics
# ============================================================
def state_file(run_dir):
    return os.path.join(run_dir, "resume_state.json")

def load_state(run_dir):
    if os.path.isfile(state_file(run_dir)):
        try:
            with open(state_file(run_dir), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "engine": None,
        "queue": [],
        "processed": [],
        "url_strategy": {},
        "scores": {},
        "analytics": {
            "strategy": {},
            "best_strategy": None,
            "api_used": None,
            "headless_used": 0,
            "api_sniff_used": 0,
            "crawler": {"pages": 0, "product_urls": 0, "category_pages": 0, "started_at": None, "finished_at": None},
            "started_at": int(time.time()),
        }
    }

def save_state(run_dir, st):
    with open(state_file(run_dir), "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)

def ana_touch(st, strat, ok=False, fail=False, dt=None, found=0):
    a = st["analytics"]["strategy"].setdefault(strat, {"ok":0,"fail":0,"time_sec":0.0,"found":0})
    if ok: a["ok"] += 1
    if fail: a["fail"] += 1
    if dt is not None: a["time_sec"] += float(dt)
    if found: a["found"] += int(found)

def scores_dict(st):
    if not isinstance(st.get("scores"), dict):
        st["scores"] = {}
    return st["scores"]

# ============================================================
# Extraction helpers (maximize data)
# ============================================================
def meta_content(soup, **attrs):
    tag = soup.find("meta", attrs=attrs)
    if tag and tag.get("content"):
        return tag.get("content").strip()
    return None

def extract_breadcrumbs_categories(soup):
    cats = []
    for nav in soup.find_all(["nav","ol","ul"], attrs={"class": re.compile(r"breadcrumb", re.I)}):
        for a in nav.find_all("a", href=True):
            t = clean_text(a.get_text(" ", strip=True), 120)
            if t and t not in cats:
                cats.append(t)

    for sc in soup.find_all("script", attrs={"type":"application/ld+json"}):
        raw = (sc.string or sc.get_text() or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue

        def walk(o):
            if isinstance(o, dict):
                if str(o.get("@type")).lower() == "breadcrumblist":
                    items = o.get("itemListElement") or []
                    if isinstance(items, list):
                        for it in items:
                            if isinstance(it, dict):
                                name = it.get("name") or (it.get("item") or {}).get("name")
                                name = clean_text(str(name), 120)
                                if name and name not in cats:
                                    cats.append(name)
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for it in o:
                    walk(it)

        walk(data)

    return cats[:30]

def parse_jsonld_product(soup):
    product = {}
    aggregate = None
    reviews = []

    scripts = soup.find_all("script", attrs={"type":"application/ld+json"})
    for sc in scripts:
        raw = (sc.string or sc.get_text() or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue

        def walk(o):
            nonlocal product, aggregate, reviews
            if isinstance(o, dict):
                t = str(o.get("@type") or "").lower()
                if t == "product" and not product:
                    product = o
                if isinstance(o.get("aggregateRating"), dict) and not aggregate:
                    aggregate = o.get("aggregateRating")
                rev = o.get("review")
                if rev:
                    if isinstance(rev, dict):
                        rev = [rev]
                    if isinstance(rev, list):
                        for rr in rev:
                            if isinstance(rr, dict):
                                reviews.append(rr)
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for it in o:
                    walk(it)
        walk(data)

    out_reviews = []
    for rr in reviews[:MAX_REVIEWS_PER_PRODUCT]:
        author = rr.get("author")
        if isinstance(author, dict):
            author = author.get("name")
        rating = None
        if isinstance(rr.get("reviewRating"), dict):
            rating = rr["reviewRating"].get("ratingValue")
        try:
            rating = float(rating) if rating is not None else None
        except Exception:
            rating = None
        out_reviews.append({
            "author": author,
            "rating": rating,
            "title": rr.get("name") or rr.get("headline"),
            "body": clean_text(rr.get("reviewBody") or "", 2500),
            "date": rr.get("datePublished"),
        })

    return product, aggregate, out_reviews

def extract_price_currency_from_dom(soup):
    price = None
    currency = None

    tag = soup.find(attrs={"itemprop":"price"})
    if tag:
        price = tag.get("content") or tag.get("value") or clean_text(tag.get_text(), 60)

    tagc = soup.find(attrs={"itemprop":"priceCurrency"})
    if tagc:
        currency = tagc.get("content") or tagc.get("value") or clean_text(tagc.get_text(), 10)

    if not price:
        price = meta_content(soup, property="product:price:amount") or meta_content(soup, name="product:price:amount")
    if not currency:
        currency = meta_content(soup, property="product:price:currency") or meta_content(soup, name="product:price:currency")

    if not currency:
        currency = best_currency_from_text(soup.get_text(" ", strip=True)[:900])

    if isinstance(price, str):
        m = re.search(r"(\d+[.,]?\d*)", price.replace(" ", ""))
        if m:
            price = m.group(1).replace(",", ".")
    return price, currency

def extract_images_rich(soup, base_url):
    urls = []
    seen = set()

    def add(u):
        if not u:
            return
        u = urljoin(base_url, u)
        if u not in seen:
            seen.add(u)
            urls.append(u)

    add(meta_content(soup, property="og:image"))
    add(meta_content(soup, name="twitter:image"))

    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-zoom-image")
        if src:
            add(src)

        srcset = img.get("srcset")
        if srcset:
            candidates = []
            for part in srcset.split(","):
                part = part.strip()
                if not part:
                    continue
                bits = part.split()
                u = bits[0]
                size = 0
                if len(bits) > 1:
                    m = re.search(r"(\d+)", bits[1])
                    if m:
                        size = int(m.group(1))
                candidates.append((size, u))
            if candidates:
                candidates.sort(key=lambda x: x[0], reverse=True)
                add(candidates[0][1])

        if len(urls) >= MAX_IMAGES_PER_PRODUCT:
            break

    return urls[:MAX_IMAGES_PER_PRODUCT]

def extract_attributes_best_effort(soup):
    attrs = {}

    for dl in soup.find_all("dl"):
        dts = dl.find_all("dt")
        dds = dl.find_all("dd")
        if dts and dds and len(dts) == len(dds):
            for dt, dd in zip(dts, dds):
                k = clean_text(dt.get_text(" ", strip=True), 80)
                v = clean_text(dd.get_text(" ", strip=True), 240)
                if k and v and k.lower() not in (kk.lower() for kk in attrs.keys()):
                    attrs[k] = v

    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            th = tr.find("th")
            td = tr.find("td")
            if th and td:
                k = clean_text(th.get_text(" ", strip=True), 80)
                v = clean_text(td.get_text(" ", strip=True), 240)
                if k and v and k.lower() not in (kk.lower() for kk in attrs.keys()):
                    attrs[k] = v

    return attrs

def extract_variants_sizes_best_effort(soup):
    variants = []

    for sel in soup.find_all("select"):
        name = (sel.get("name") or sel.get("id") or "").lower()
        if any(k in name for k in ("size", "variant", "option")):
            for opt in sel.find_all("option"):
                txt = clean_text(opt.get_text(" ", strip=True), 60)
                if not txt or "select" in txt.lower():
                    continue
                variants.append({"title": txt, "size": txt, "available": True})

    for btn in soup.find_all(["button","a","span"], attrs={"class": re.compile(r"size|variant|option", re.I)}):
        txt = clean_text(btn.get_text(" ", strip=True), 30)
        if txt and len(txt) <= 12 and re.search(r"\d|xs|s|m|l|xl|xxl", txt.lower()):
            variants.append({"title": txt, "size": txt, "available": True})

    out, seen = [], set()
    for v in variants:
        t = (v.get("title") or "").lower()
        if t and t not in seen:
            seen.add(t)
            out.append(v)
    return out[:200]

# ============================================================
# INLINE CATALOG fallback (single-page "store" lists)
# ============================================================
def extract_inline_catalog_from_html(html: str, page_url: str):
    """
    Fallback for pages that list multiple "products" inline (cards/sections)
    and do NOT have product URLs. Example: /Pages/store.html style pages.

    Returns list of product dicts.
    """
    soup = BeautifulSoup(html or "", parser_name())
    products = []
    host = urlparse(page_url).netloc.lower()

    def grab_price_currency(text):
        text = text or ""
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*(€|\$|£)\b", text)
        if not m:
            m = re.search(r"(\d+(?:[.,]\d+)?)\s*(€|\$|£)", text)
        if not m:
            return None, None
        price = m.group(1).replace(",", ".")
        sym = m.group(2)
        cur = {"€": "EUR", "$": "USD", "£": "GBP"}.get(sym, None)
        return price, cur

    stop_titles = {"store policies", "policies", "privacy policy", "terms", "terms of service"}

    headings = soup.find_all(["h3", "h2"])
    for h in headings:
        title = clean_text(h.get_text(" ", strip=True), 200)
        if not title:
            continue
        if title.strip().lower() in stop_titles:
            break
        # prioritize H3 (common for cards/services)
        if h.name != "h3":
            continue

        block_nodes = []
        for sib in h.next_siblings:
            if hasattr(sib, "name") and sib.name in ("h3", "h2"):
                break
            block_nodes.append(sib)

        block_text_parts = []
        features = []
        purchase_url = None
        images = []

        for node in block_nodes:
            # node can be bs4 Tag or NavigableString
            if hasattr(node, "get_text"):
                try:
                    block_text_parts.append(node.get_text(" ", strip=True))
                except Exception:
                    pass

            # Only bs4 Tag objects have find_all
            if not hasattr(node, "find_all"):
                continue

            try:
                for li in node.find_all("li"):
                    t = clean_text(li.get_text(" ", strip=True), 250)
                    if t and t not in features:
                        features.append(t)

                for a in node.find_all("a", href=True):
                    href = urljoin(page_url, a["href"])
                    txt = (a.get_text(" ", strip=True) or "").lower()
                    if ("buy.stripe.com" in href.lower()) or ("purchase" in txt) or ("checkout" in txt) or ("buy" in txt):
                        purchase_url = href
                        break

                for img in node.find_all("img"):
                    src = img.get("src") or img.get("data-src")
                    if src:
                        images.append(urljoin(page_url, src))
            except Exception:
                # If any node parsing fails, just skip it
                continue

        block_text = clean_text(" ".join(block_text_parts), 12000)

        # Description: first <p> after heading, else block text
        desc = ""
        ptag = h.find_next("p")
        if ptag:
            desc = clean_text(ptag.get_text(" ", strip=True), 3000)
        if not desc:
            desc = block_text[:3000]

        price, currency = grab_price_currency(block_text)
        if not currency:
            currency = best_currency_from_text(block_text)

        url_for_product = purchase_url or (page_url + "#inline-" + slug(title, 40))
        pid = md5((title + "|" + url_for_product), 16)

        p = {
            "id": pid,
            "engine": "inline_catalog",
            "fetched_with": "inline_html",
            "name": title,
            "brand": "DedSec Project" if "ded-sec.space" in host else None,
            "url": url_for_product,
            "sku": None, "gtin": None, "mpn": None,
            "availability": None,
            "price": price,
            "currency": currency,
            "description": (desc + ("\n\nWhat you get:\n- " + "\n- ".join(features) if features else "")).strip(),
            "categories": ["Store", "Services"] if "store" in page_url.lower() else [],
            "attributes": {
                "source_page": page_url,
                "purchase_url": purchase_url,
                "features": features[:80],
            },
            "review_rating": None,
            "review_count": None,
            "variants": [],
            "images": images[:MAX_IMAGES_PER_PRODUCT],
            "reviews": [],
            "raw_jsonld_product": {},
        }

        if len(p["name"]) >= 3 and (p["price"] or p["attributes"]["purchase_url"] or len(p["description"]) > 40):
            products.append(p)

    # Secondary heuristic: "View details" cards
    for a in soup.find_all("a", href=True):
        txt = clean_text(a.get_text(" ", strip=True), 300)
        if "view details" in txt.lower():
            href = urljoin(page_url, a["href"])
            pid = md5(("card|" + txt + "|" + href), 16)
            products.append({
                "id": pid,
                "engine": "inline_card",
                "fetched_with": "inline_html",
                "name": txt.split("View details")[0].strip()[:200] or txt[:200],
                "brand": "DedSec Project" if "ded-sec.space" in host else None,
                "url": href,
                "sku": None, "gtin": None, "mpn": None,
                "availability": None,
                "price": None,
                "currency": None,
                "description": txt,
                "categories": ["Store", "Best picks"],
                "attributes": {"source_page": page_url},
                "review_rating": None,
                "review_count": None,
                "variants": [],
                "images": [],
                "reviews": [],
                "raw_jsonld_product": {},
            })

    # Deduplicate by (name,url)
    out = []
    seen = set()
    for p in products:
        key = (p.get("name","").lower().strip(), p.get("url","").strip())
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out

# ============================================================
# Per-product folder
# ============================================================
def save_product_folder(run_dir, p):
    products_dir = os.path.join(run_dir, "products")
    ensure_dir(products_dir)

    pid_folder = slug(p.get("name") or "product", 55) + "_" + md5(p.get("url") or "", 10)
    pdir = os.path.join(products_dir, pid_folder)
    ensure_dir(pdir)

    with open(os.path.join(pdir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)

    with open(os.path.join(pdir, "description.txt"), "w", encoding="utf-8") as f:
        f.write((p.get("description") or "").strip() + "\n")

    if p.get("reviews"):
        with open(os.path.join(pdir, "reviews.json"), "w", encoding="utf-8") as f:
            json.dump(p["reviews"], f, ensure_ascii=False, indent=2)

    # Convenience files for inline catalogs
    if p.get("engine") in ("inline_catalog", "inline_card"):
        src = (p.get("attributes") or {}).get("source_page") or ""
        pur = (p.get("attributes") or {}).get("purchase_url") or ""
        with open(os.path.join(pdir, "source_page.txt"), "w", encoding="utf-8") as f:
            f.write(src + "\n")
        with open(os.path.join(pdir, "purchase_link.txt"), "w", encoding="utf-8") as f:
            f.write(pur + "\n")

# ============================================================
# Image downloader
# ============================================================
def download_images(net: Net, run_dir, product_id, image_urls):
    img_dir = os.path.join(run_dir, "images_cache", product_id)
    ensure_dir(img_dir)

    saved = []
    seen = set()

    for idx, u in enumerate(image_urls or []):
        if len(saved) >= MAX_IMAGES_PER_PRODUCT:
            break
        if not u or u in seen:
            continue
        seen.add(u)

        r, _, _ = net.get(u, headers={"User-Agent": DEFAULT_UA}, stream=True, max_attempts=3)
        if r is None or r.status_code != 200:
            continue

        ctype = (r.headers.get("Content-Type") or "").lower()
        ext = ".jpg"
        if "png" in ctype: ext = ".png"
        elif "webp" in ctype: ext = ".webp"
        elif "gif" in ctype: ext = ".gif"

        out = os.path.join(img_dir, f"{idx+1:02d}{ext}")
        try:
            with open(out, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
            saved.append({"url": u, "local_path": out})
        except Exception:
            pass

        sleep(BASE_DELAY)

    return saved

# ============================================================
# Discovery: sitemap + APIs + crawlers
# ============================================================
def parse_sitemap_xml(xml_text: str):
    urls = []
    for m in re.finditer(r"<loc>(.*?)</loc>", xml_text, flags=re.I | re.S):
        u = clean_text(m.group(1), 1200)
        if u.startswith("http"):
            urls.append(u)
    return urls

def try_sitemaps(net: Net, base_url: str):
    base = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
    robots_txt = fetch_robots(net, base)
    disallow, allow, crawl_delay, robot_sitemaps = parse_robots(robots_txt)

    candidates = [
        base + "/sitemap.xml",
        base + "/sitemap_index.xml",
        base + "/sitemap-index.xml",
        base + "/sitemap1.xml",
    ] + robot_sitemaps

    all_urls = []
    for sm in candidates:
        rr, _, _ = net.get(sm, headers={"User-Agent": DEFAULT_UA}, max_attempts=2)
        if rr is None or rr.status_code != 200 or len(rr.text) < 30:
            continue
        urls = parse_sitemap_xml(rr.text)
        if urls and any(u.endswith(".xml") for u in urls[:10]):
            for child in urls[:30]:
                cr, _, _ = net.get(child, headers={"User-Agent": DEFAULT_UA}, max_attempts=2)
                if cr is None or cr.status_code != 200:
                    continue
                all_urls.extend(parse_sitemap_xml(cr.text))
        else:
            all_urls.extend(urls)

        if len(all_urls) > MAX_PRODUCT_URLS * 4:
            break

    dom = urlparse(base_url).netloc.lower()
    out, seen = [], set()
    for u in all_urls:
        u = strip_tracking_params(normalize_url(u))
        if urlparse(u).netloc.lower() != dom:
            continue
        if is_probably_product(u) or re.search(r"/(products|product|p|item)/", urlparse(u).path.lower()):
            if u not in seen:
                seen.add(u)
                out.append(u)
        if len(out) >= MAX_PRODUCT_URLS:
            break

    return out, (float(crawl_delay) if crawl_delay else BASE_DELAY), {"disallow": disallow, "allow": allow, "crawl_delay": crawl_delay}

def shopify_probe(net: Net, base_url: str):
    base = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
    r, _, _ = net.get(base + "/products.json?limit=1", headers={"Accept":"application/json"}, max_attempts=2)
    if r is None or r.status_code != 200:
        return False
    try:
        j = r.json()
        return isinstance(j, dict) and "products" in j
    except Exception:
        return False

def shopify_collect(net: Net, base_url: str):
    base = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
    out = []
    for page in range(1, SHOPIFY_MAX_PAGES + 1):
        api = f"{base}/products.json?limit=250&page={page}"
        r, _, _ = net.get(api, headers={"Accept":"application/json"}, max_attempts=3)
        if r is None or r.status_code != 200:
            break
        try:
            data = r.json()
        except Exception:
            break
        items = data.get("products") or []
        if not items:
            break
        for p in items:
            handle = p.get("handle")
            if handle:
                out.append(f"{base}/products/{handle}")
        if len(out) >= MAX_PRODUCT_URLS:
            break
        sleep(BASE_DELAY)
    seen, res = set(), []
    for u in out:
        if u not in seen:
            seen.add(u); res.append(u)
    return res[:MAX_PRODUCT_URLS]

def woocommerce_probe(net: Net, base_url: str):
    base = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
    api = base + "/wp-json/wc/store/products?per_page=1"
    r, _, _ = net.get(api, headers={"Accept":"application/json"}, max_attempts=2)
    if r is None or r.status_code != 200:
        return False
    try:
        j = r.json()
        return isinstance(j, list)
    except Exception:
        return False

def woocommerce_collect(net: Net, base_url: str):
    base = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
    out = []
    for page in range(1, WOOCOMMERCE_MAX_PAGES + 1):
        api = base + f"/wp-json/wc/store/products?per_page=100&page={page}"
        r, _, _ = net.get(api, headers={"Accept":"application/json"}, max_attempts=3)
        if r is None or r.status_code != 200:
            break
        try:
            j = r.json()
        except Exception:
            break
        if not isinstance(j, list) or not j:
            break
        for item in j:
            u = item.get("permalink") or item.get("link")
            if u and u.startswith("http"):
                out.append(u)
        if len(out) >= MAX_PRODUCT_URLS:
            break
        sleep(BASE_DELAY)
    seen, res = set(), []
    for u in out:
        u = strip_tracking_params(normalize_url(u))
        if u not in seen:
            seen.add(u); res.append(u)
    return res[:MAX_PRODUCT_URLS]

def nike_collect(net: Net, category_url: str):
    if "nike.com" not in urlparse(category_url).netloc.lower():
        return []
    endpoint = category_url.replace("https://www.nike.com", "")
    api = "https://api.nike.com/cic/browse/v1"
    anchor = None
    out = []
    pages = 0

    while pages < NIKE_MAX_PAGES and len(out) < MAX_PRODUCT_URLS:
        params = {"queryid":"products","endpoint":endpoint,"country":"GR","language":"en"}
        if anchor:
            params["anchor"] = anchor
        r, _, _ = net.get(api, headers={"Accept":"application/json"}, params=params, max_attempts=3)
        if r is None or r.status_code != 200:
            break
        try:
            data = r.json()
        except Exception:
            break
        items = (((data.get("data") or {}).get("products") or {}).get("products")) or []
        if not items:
            break
        for it in items:
            prod = (it.get("product") or {})
            pdp = prod.get("pdpUrl")
            if pdp:
                out.append("https://www.nike.com" + pdp)
        anchor = ((data.get("data") or {}).get("products") or {}).get("next")
        pages += 1
        if not anchor:
            break
        sleep(BASE_DELAY)

    seen, res = set(), []
    for u in out:
        if u not in seen:
            seen.add(u); res.append(u)
    return res[:MAX_PRODUCT_URLS]

def generic_smart_crawl(net: Net, start_url: str, use_headless=False, per_request_delay=BASE_DELAY):
    start_url = strip_tracking_params(normalize_url(start_url))
    dom = urlparse(start_url).netloc.lower()

    q = deque([start_url])
    visited = set([start_url])
    product_urls = []
    pages = 0

    while q and pages < MAX_LISTING_PAGES and len(product_urls) < MAX_PRODUCT_URLS:
        cur = q.popleft()
        pages += 1

        if use_headless:
            final, html = headless_fetch_html(cur)
            if not html:
                return product_urls
        else:
            r, _, _ = net.get(cur, headers={"Accept":"text/html,*/*"}, max_attempts=3)
            if r is None or r.status_code != 200:
                continue
            final, html = r.url, r.text

        soup = BeautifulSoup(html, parser_name())

        ln = soup.find("link", rel=lambda v: v and "next" in str(v).lower())
        if ln and ln.get("href"):
            nxt = strip_tracking_params(normalize_url(urljoin(final, ln.get("href"))))
            if urlparse(nxt).netloc.lower() == dom and nxt not in visited:
                visited.add(nxt); q.append(nxt)

        for a in soup.find_all("a", href=True):
            u = strip_tracking_params(normalize_url(urljoin(final, a["href"])))
            if not u.startswith("http"):
                continue
            if urlparse(u).netloc.lower() != dom:
                continue

            if is_probably_product(u) and u not in product_urls:
                product_urls.append(u)
                if len(product_urls) >= MAX_PRODUCT_URLS:
                    break

            if u not in visited and is_probably_pagination(u):
                visited.add(u)
                q.append(u)

        sleep(per_request_delay)

    return product_urls

def sniff_api_then_extract_product_urls(net: Net, url: str):
    cands = headless_sniff_api(url)
    if not cands:
        return []
    dom = urlparse(url).netloc.lower()
    for api in cands[:8]:
        r, _, _ = net.get(api, headers={"Accept":"application/json"}, max_attempts=3)
        if r is None or r.status_code != 200:
            continue
        try:
            j = r.json()
        except Exception:
            continue

        urls = []
        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    lk = str(k).lower()
                    if lk in ("url","permalink","link","pdpurl","producturl") and isinstance(v, str) and v.startswith("http"):
                        urls.append(v)
                    walk(v)
            elif isinstance(o, list):
                for it in o:
                    walk(it)
        walk(j)

        seen, out = set(), []
        for u in urls:
            u = strip_tracking_params(normalize_url(u))
            if urlparse(u).netloc.lower() == dom and u not in seen:
                seen.add(u); out.append(u)
        if out:
            return out[:MAX_PRODUCT_URLS]
    return []

# ============================================================
# Domain Crawler Mode
# ============================================================
def domain_crawler_mode(net: Net, start_url: str, crawler_conf: dict, robots_rules: dict, crawl_delay_used: float):
    start_url = strip_tracking_params(normalize_url(start_url))
    dom = urlparse(start_url).netloc.lower()
    base = f"{urlparse(start_url).scheme}://{dom}"

    disallow = robots_rules.get("disallow") or []
    allow = robots_rules.get("allow") or []

    max_pages = int(crawler_conf.get("max_pages", CRAWLER_MAX_PAGES_DEFAULT))
    max_depth = int(crawler_conf.get("max_depth", CRAWLER_MAX_DEPTH_DEFAULT))
    max_runtime = int(crawler_conf.get("max_runtime_sec", CRAWLER_MAX_RUNTIME_SEC_DEFAULT))

    t_start = time.time()

    seeds = [
        start_url,
        base + "/",
        base + "/shop",
        base + "/store",
        base + "/category",
        base + "/categories",
        base + "/collections",
        base + "/collections/all",
        base + "/products",
        base + "/sale",
        base + "/men",
        base + "/women",
        base + "/new",
    ]

    q = deque()
    visited = set()
    product_urls = []
    prod_seen = set()
    category_pages = 0

    def enqueue(u, d):
        u = strip_tracking_params(normalize_url(u))
        if not u.startswith("http"):
            return
        if urlparse(u).netloc.lower() != dom:
            return
        if u in visited:
            return
        path = urlparse(u).path.lower()
        if re.search(r"\.(jpg|jpeg|png|webp|gif|pdf|zip|mp4|mp3|svg|woff2?)$", path):
            return
        if not robots_allowed(u, base, disallow, allow):
            return
        visited.add(u)
        q.append((u, d))

    def looks_like_category(u):
        p = urlparse(u).path.lower()
        return any(k in p for k in ("/category", "/categories", "/collection", "/collections", "/shop", "/sale", "/search", "/men", "/women", "/new"))

    for s in seeds:
        enqueue(s, 0)

    pages = 0
    while q and pages < max_pages and (time.time() - t_start) < max_runtime and len(product_urls) < MAX_PRODUCT_URLS:
        cur, depth = q.popleft()
        pages += 1

        r, _, _ = net.get(cur, headers={"Accept":"text/html,*/*"}, max_attempts=3)
        if r is None or r.status_code != 200 or not r.text:
            continue
        final = r.url
        soup = BeautifulSoup(r.text, parser_name())

        for a in soup.find_all("a", href=True):
            u = strip_tracking_params(normalize_url(urljoin(final, a["href"])))
            if urlparse(u).netloc.lower() != dom:
                continue
            if is_probably_product(u) and u not in prod_seen:
                prod_seen.add(u)
                product_urls.append(u)
                if len(product_urls) >= MAX_PRODUCT_URLS:
                    break

        jprod, _, _ = parse_jsonld_product(soup)
        if isinstance(jprod, dict) and str(jprod.get("@type", "")).lower() == "product":
            u = strip_tracking_params(normalize_url(final))
            if u not in prod_seen:
                prod_seen.add(u)
                product_urls.append(u)

        if depth < max_depth:
            for a in soup.find_all("a", href=True):
                u = strip_tracking_params(normalize_url(urljoin(final, a["href"])))
                if urlparse(u).netloc.lower() != dom:
                    continue
                if looks_like_category(u) or is_probably_pagination(u) or (depth <= 1 and not is_probably_product(u)):
                    enqueue(u, depth + 1)

        if looks_like_category(final):
            category_pages += 1

        sleep(crawl_delay_used)

    return {
        "pages": pages,
        "category_pages": category_pages,
        "product_urls": product_urls[:MAX_PRODUCT_URLS],
        "visited_count": len(visited),
        "runtime_sec": int(time.time() - t_start),
        "crawl_delay_used": crawl_delay_used,
    }

# ============================================================
# Deep scrape (max info)
# ============================================================
def deep_scrape(net: Net, product_url: str, headless=False, want_reviews=True):
    fetched_with = "requests"
    final_url = product_url
    html = None

    if headless:
        final_url, html = headless_fetch_html(product_url)
        if html:
            fetched_with = "headless"
        else:
            headless = False

    if not headless:
        r, _, _ = net.get(product_url, headers={"Accept":"text/html,*/*"}, max_attempts=3)
        if r is None or r.status_code != 200:
            return None
        final_url, html = r.url, r.text

    soup = BeautifulSoup(html, parser_name())

    jprod, agg, reviews = parse_jsonld_product(soup)
    cats = extract_breadcrumbs_categories(soup)
    attrs = extract_attributes_best_effort(soup)

    name = None
    brand = None
    sku = None
    gtin = None
    mpn = None
    availability = None
    price = None
    currency = None
    desc = ""

    if isinstance(jprod, dict) and jprod:
        name = jprod.get("name")
        b = jprod.get("brand")
        if isinstance(b, dict): brand = b.get("name")
        elif isinstance(b, str): brand = b

        sku = jprod.get("sku") or jprod.get("mpn")
        gtin = jprod.get("gtin13") or jprod.get("gtin14") or jprod.get("gtin12") or jprod.get("gtin8")
        mpn = jprod.get("mpn")

        offers = jprod.get("offers")
        if isinstance(offers, list) and offers:
            offers = offers[0]
        if isinstance(offers, dict):
            price = offers.get("price") or offers.get("lowPrice") or offers.get("highPrice")
            currency = offers.get("priceCurrency")
            availability = offers.get("availability")

        if jprod.get("description"):
            desc = BeautifulSoup(str(jprod.get("description")), parser_name()).get_text(" ", strip=True)

    if not name:
        name = meta_content(soup, property="og:title") or meta_content(soup, name="twitter:title")
    if not name:
        name = soup.title.get_text(" ", strip=True) if soup.title else "product"

    if not brand:
        brand = meta_content(soup, property="product:brand") or meta_content(soup, name="brand")

    if not price or not currency:
        p2, c2 = extract_price_currency_from_dom(soup)
        price = price or p2
        currency = currency or c2

    if not desc:
        desc = meta_content(soup, name="description") or meta_content(soup, property="og:description") or ""
    if not desc:
        desc = soup.get_text(" ", strip=True)[:2000]
    desc = clean_text(desc, 20000)

    rating = None
    review_count = None
    if isinstance(agg, dict):
        rv = agg.get("ratingValue")
        rc = agg.get("reviewCount") or agg.get("ratingCount")
        try: rating = float(rv) if rv is not None else None
        except Exception: rating = None
        try: review_count = int(rc) if rc is not None else None
        except Exception: review_count = None

    images = extract_images_rich(soup, final_url)
    variants = extract_variants_sizes_best_effort(soup)
    reviews_out = reviews if want_reviews else []

    if isinstance(availability, str):
        availability = availability.split("/")[-1]

    engine = "generic"
    host = urlparse(final_url).netloc.lower()
    if "nike.com" in host: engine = "nike"
    elif "/products/" in urlparse(final_url).path.lower(): engine = "shopify"
    elif "woocommerce" in (html or "").lower(): engine = "woocommerce"

    return {
        "engine": engine,
        "fetched_with": fetched_with,
        "name": clean_text(name, 250),
        "brand": clean_text(brand or "", 120) or None,
        "url": final_url,
        "sku": clean_text(sku or "", 80) or None,
        "gtin": clean_text(gtin or "", 40) or None,
        "mpn": clean_text(mpn or "", 80) or None,
        "availability": clean_text(availability or "", 40) or None,
        "price": price,
        "currency": currency,
        "description": desc,
        "categories": cats,
        "attributes": attrs,
        "review_rating": rating,
        "review_count": review_count,
        "variants": variants,
        "images": images,
        "reviews": reviews_out,
        "raw_jsonld_product": jprod if isinstance(jprod, dict) else {},
    }

# ============================================================
# Strategy escalation (collect + deep)
# ============================================================
STRATEGIES_COLLECT = [
    ("SITEMAP", 1),
    ("SHOPIFY_API", 1),
    ("WOOCOMMERCE_API", 1),
    ("NIKE_API", 1),
    ("HTML_CRAWL", 2),
    ("DOMAIN_CRAWLER", 3),
    ("HEADLESS_HTML_CRAWL", 5),
    ("HEADLESS_API_SNIFF", 6),
]
STRATEGIES_DEEP = [
    ("DEEP_HTML", 1),
    ("DEEP_HEADLESS", 5),
]

def strategy_order(st, phase, url):
    sc = scores_dict(st)
    base = STRATEGIES_COLLECT if phase == "collect" else STRATEGIES_DEEP
    ordered = sorted(base, key=lambda x: (x[1], -int(sc.get(x[0], 0))))
    mem = st.get("url_strategy", {}).get(url)
    if phase == "deep" and mem:
        ordered = [s for s in ordered if s[0] != mem]
        ordered.insert(0, (mem, dict(base).get(mem, 99)))
    return [s[0] for s in ordered]

def run_collect(net, st, url, headless_allowed, domain_crawler_enabled, crawler_conf, robots_rules, crawl_delay_used):
    sc = scores_dict(st)
    attempted = set()
    order = strategy_order(st, "collect", url)

    for strat in order:
        if strat in attempted:
            continue
        if strat == "DOMAIN_CRAWLER" and not domain_crawler_enabled:
            continue
        if strat.startswith("HEADLESS") and not headless_allowed:
            continue
        if strat.startswith("HEADLESS") and headless_allowed and not headless_available():
            headless_warn_once()
            continue

        attempted.add(strat)
        t0 = time.time()
        backoff = BACKOFF_BASE

        for _ in range(MAX_ATTEMPTS_PER_STRATEGY):
            try:
                urls = []
                used_engine = None

                if strat == "SITEMAP":
                    urls, _, _ = try_sitemaps(net, url)

                elif strat == "SHOPIFY_API":
                    if shopify_probe(net, url):
                        used_engine = "shopify"
                        urls = shopify_collect(net, url)

                elif strat == "WOOCOMMERCE_API":
                    if woocommerce_probe(net, url):
                        used_engine = "woocommerce"
                        urls = woocommerce_collect(net, url)

                elif strat == "NIKE_API":
                    used_engine = "nike"
                    urls = nike_collect(net, url)

                elif strat == "HTML_CRAWL":
                    urls = generic_smart_crawl(net, url, use_headless=False, per_request_delay=crawl_delay_used)

                elif strat == "DOMAIN_CRAWLER":
                    st["analytics"]["crawler"]["started_at"] = int(time.time())
                    crawl_res = domain_crawler_mode(net, url, crawler_conf, robots_rules, crawl_delay_used)
                    st["analytics"]["crawler"]["pages"] += crawl_res["pages"]
                    st["analytics"]["crawler"]["category_pages"] += crawl_res["category_pages"]
                    st["analytics"]["crawler"]["product_urls"] += len(crawl_res["product_urls"])
                    st["analytics"]["crawler"]["finished_at"] = int(time.time())
                    st["analytics"]["crawler"]["crawl_delay_used"] = crawl_res["crawl_delay_used"]
                    urls = crawl_res["product_urls"]

                elif strat == "HEADLESS_HTML_CRAWL":
                    st["analytics"]["headless_used"] += 1
                    urls = generic_smart_crawl(net, url, use_headless=True, per_request_delay=crawl_delay_used)

                elif strat == "HEADLESS_API_SNIFF":
                    st["analytics"]["api_sniff_used"] += 1
                    urls = sniff_api_then_extract_product_urls(net, url)

                dt = time.time() - t0

                if urls:
                    seen, out = set(), []
                    for u in urls:
                        u = strip_tracking_params(normalize_url(u))
                        if u not in seen:
                            seen.add(u); out.append(u)
                        if len(out) >= MAX_PRODUCT_URLS:
                            break

                    sc[strat] = int(sc.get(strat, 0)) + len(out)
                    st["analytics"]["best_strategy"] = strat
                    st["analytics"]["api_used"] = strat
                    ana_touch(st, strat, ok=True, dt=dt, found=len(out))

                    if not used_engine:
                        host = urlparse(url).netloc.lower()
                        if "nike.com" in host: used_engine = "nike"
                        elif strat == "SHOPIFY_API": used_engine = "shopify"
                        elif strat == "WOOCOMMERCE_API": used_engine = "woocommerce"
                        else: used_engine = "generic"

                    return used_engine, out, strat

                ana_touch(st, strat, fail=True, dt=dt, found=0)
                sc[strat] = int(sc.get(strat, 0)) - 2

            except Exception:
                dt = time.time() - t0
                ana_touch(st, strat, fail=True, dt=dt, found=0)
                sc[strat] = int(sc.get(strat, 0)) - 5

            sleep(backoff + random.random())
            backoff = min(BACKOFF_MAX, backoff * 2.0)

    return "generic", [], None

def run_deep(net, st, product_url, headless_allowed, want_reviews):
    sc = scores_dict(st)
    mem = st.setdefault("url_strategy", {})
    attempted = set()
    order = strategy_order(st, "deep", product_url)

    for strat in order:
        if strat in attempted:
            continue
        attempted.add(strat)

        if strat == "DEEP_HEADLESS":
            if not headless_allowed:
                continue
            if headless_allowed and not headless_available():
                headless_warn_once()
                continue

        t0 = time.time()
        backoff = BACKOFF_BASE

        for _ in range(MAX_ATTEMPTS_PER_STRATEGY):
            try:
                if strat == "DEEP_HTML":
                    p = deep_scrape(net, product_url, headless=False, want_reviews=want_reviews)
                elif strat == "DEEP_HEADLESS":
                    st["analytics"]["headless_used"] += 1
                    p = deep_scrape(net, product_url, headless=True, want_reviews=want_reviews)
                else:
                    p = None

                dt = time.time() - t0
                if p and p.get("name") and p.get("url"):
                    sc[strat] = int(sc.get(strat, 0)) + 5
                    ana_touch(st, strat, ok=True, dt=dt, found=1)
                    mem[product_url] = strat
                    return p, strat

                ana_touch(st, strat, fail=True, dt=dt, found=0)
                sc[strat] = int(sc.get(strat, 0)) - 2

            except Exception:
                dt = time.time() - t0
                ana_touch(st, strat, fail=True, dt=dt, found=0)
                sc[strat] = int(sc.get(strat, 0)) - 5

            sleep(backoff + random.random())
            backoff = min(BACKOFF_MAX, backoff * 2.0)

    return None, None

# ============================================================
# MAIN
# ============================================================
def main():
    print("=== Store Scrapper v10.5 (\u0391\u03c3\u03c6\u03b1\u03bb\u03ad\u03c2 \u03b3\u03b9\u03b1 Termux + Inline \u039a\u03b1\u03c4\u03ac\u03bb\u03bf\u03b3\u03bf\u03c2) ===\n")

    url = input("\u0395\u03c0\u03b9\u03ba\u03cc\u03bb\u03bb\u03b7\u03c3\u03b5 URL \u03ba\u03b1\u03c4\u03b1\u03c3\u03c4\u03ae\u03bc\u03b1\u03c4\u03bf\u03c2/\u03bb\u03af\u03c3\u03c4\u03b1\u03c2: ").strip()
    if not url.startswith("http"):
        url = "https://" + url
    url = strip_tracking_params(normalize_url(url))

    deep = input("\u0395\u03bd\u03b5\u03c1\u03b3\u03bf\u03c0\u03bf\u03af\u03b7\u03c3\u03b7 \u0391\u039d\u0391\u039b\u03a5\u03a4\u0399\u039a\u039f\u03a5 (DEEP) \u03b5\u03bb\u03ad\u03b3\u03c7\u03bf\u03c5 \u03b1\u03bd\u03ac \u03c0\u03c1\u03bf\u03ca\u03cc\u03bd (\u03c0\u03c1\u03bf\u03c4\u03b5\u03af\u03bd\u03b5\u03c4\u03b1\u03b9); (y/n): ").strip().lower().startswith("y")
    want_reviews = input("\u0395\u03be\u03b1\u03b3\u03c9\u03b3\u03ae \u03ba\u03c1\u03b9\u03c4\u03b9\u03ba\u03ce\u03bd \u03cc\u03c0\u03bf\u03c5 \u03c5\u03c0\u03ac\u03c1\u03c7\u03bf\u03c5\u03bd; (y/n): ").strip().lower().startswith("y")
    download_imgs = input("\u039b\u03ae\u03c8\u03b7 \u03b5\u03b9\u03ba\u03cc\u03bd\u03c9\u03bd \u03c0\u03c1\u03bf\u03ca\u03cc\u03bd\u03c4\u03c9\u03bd; (y/n): ").strip().lower().startswith("y")

    headless_allowed = input("\u0395\u03bd\u03b5\u03c1\u03b3\u03bf\u03c0\u03bf\u03af\u03b7\u03c3\u03b7 headless fallback \u03cc\u03c4\u03b1\u03bd \u03c7\u03c1\u03b5\u03b9\u03ac\u03b6\u03b5\u03c4\u03b1\u03b9; (y/n): ").strip().lower().startswith("y")
    if headless_allowed and not headless_available():
        headless_warn_once()
        headless_allowed = False

    resume = input("\u03a3\u03c5\u03bd\u03ad\u03c7\u03b5\u03b9\u03b1 \u03c0\u03c1\u03bf\u03b7\u03b3\u03bf\u03cd\u03bc\u03b5\u03bd\u03b7\u03c2 \u03b5\u03ba\u03c4\u03ad\u03bb\u03b5\u03c3\u03b7\u03c2 \u03b1\u03bd \u03b2\u03c1\u03b5\u03b8\u03b5\u03af; (y/n): ").strip().lower().startswith("y")
    domain_crawler_enabled = input("\u0395\u03bd\u03b5\u03c1\u03b3\u03bf\u03c0\u03bf\u03af\u03b7\u03c3\u03b7 \u039b\u0395\u0399\u03a4\u039f\u03a5\u03a1\u0393\u0399\u0391\u03a3 DOMAIN CRAWLER (\u03b5\u03cd\u03c1\u03b5\u03c3\u03b7 \u03c3\u03b5 \u03cc\u03bb\u03bf \u03c4\u03bf site); (y/n): ").strip().lower().startswith("y")

    proxy_text = input("\u03a0\u03c1\u03bf\u03b1\u03b9\u03c1\u03b5\u03c4\u03b9\u03ba\u03ac proxies (\u03ba\u03cc\u03bc\u03bc\u03b1/\u03bd\u03ad\u03b1 \u03b3\u03c1\u03b1\u03bc\u03bc\u03ae). \u0386\u03c6\u03b7\u03c3\u03b5 \u03ba\u03b5\u03bd\u03cc \u03b3\u03b9\u03b1 \u03ba\u03b1\u03bd\u03ad\u03bd\u03b1:\n> ").strip()
    proxies = parse_proxy_list(proxy_text)

    base_out = os.path.join(downloads_dir(), "Store Scrapper")
    ensure_dir(base_out)
    run_dir = os.path.join(base_out, f"{slug(url,70)}_{md5(url,8)}")
    ensure_dir(run_dir)
    ensure_dir(os.path.join(run_dir, "products"))
    ensure_dir(os.path.join(run_dir, "images_cache"))

    net = Net(proxies)
    conn = db_connect(run_dir)
    db_init(conn)

    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    robots_txt = fetch_robots(net, base)
    disallow, allow, crawl_delay, _sitemaps = parse_robots(robots_txt)
    crawl_delay_used = float(crawl_delay) if crawl_delay else BASE_DELAY
    robots_rules = {"disallow": disallow, "allow": allow, "crawl_delay": crawl_delay}

    crawler_conf = {
        "max_pages": CRAWLER_MAX_PAGES_DEFAULT,
        "max_depth": CRAWLER_MAX_DEPTH_DEFAULT,
        "max_runtime_sec": CRAWLER_MAX_RUNTIME_SEC_DEFAULT,
    }

    st = load_state(run_dir)

    if resume and st.get("queue"):
        queue = list(st["queue"])
        processed = set(st.get("processed", []))
        engine_hint = st.get("engine") or "generic"
        print(f"
Συνέχεια: σε αναμονή={len(queue)} ολοκληρωμένα={len(processed)} engine={engine_hint}
")
    else:
        print("\n🔍 Collecting product URLs (auto-retry + multi-strategy)…\n")
        engine_hint, urls, used = run_collect(
            net, st, url,
            headless_allowed=headless_allowed,
            domain_crawler_enabled=domain_crawler_enabled,
            crawler_conf=crawler_conf,
            robots_rules=robots_rules,
            crawl_delay_used=crawl_delay_used
        )

        if not urls:
            print("⚠️ No product URLs collected (this may be an inline catalog page).")
            print("🔎 Trying INLINE_CATALOG extraction from this page…")
            r, _, _ = net.get(url, headers={"Accept":"text/html,*/*"}, max_attempts=3)
            inline_products = []
            if r is not None and r.status_code == 200 and r.text:
                inline_products = extract_inline_catalog_from_html(r.text, r.url)

            if not inline_products:
                print("❌ Still no products found.")
                print("Tips: enable Domain Crawler, add proxies, or try a category/listing URL.")
                st["engine"] = engine_hint
                save_state(run_dir, st)
                return

            print(f"✅ INLINE_CATALOG found {len(inline_products)} products on this page.")
            for p in inline_products:
                upsert_product(conn, p)

                image_rows = []
                if download_imgs and p.get("images"):
                    image_rows = download_images(net, run_dir, p["id"], p.get("images"))
                replace_children(conn, p["id"], p.get("variants"), image_rows, p.get("reviews"))
                save_product_folder(run_dir, p)

            export_csv_xlsx(run_dir, conn)
            conn.close()
            st["analytics"]["finished_at"] = int(time.time())
            save_state(run_dir, st)

            print("\n✅ DONE (INLINE_CATALOG MODE)")
            print(f"Run folder: {run_dir}")
            print("Outputs: store.db, products.csv, products.xlsx, resume_state.json")
            return

        queue = urls
        processed = set()

        st["engine"] = engine_hint
        st["queue"] = queue
        st["processed"] = []
        st["analytics"]["api_used"] = used
        save_state(run_dir, st)

        print(f"✅ Collected {len(queue)} product URLs via: {used}")
        print(f"Engine hint: {engine_hint}\n")

    total = len(queue)
    for i, purl in enumerate(list(queue), start=1):
        if purl in processed:
            continue

        print(f"[{i}/{total}] {purl}")

        if deep:
            p, _used_deep = run_deep(net, st, purl, headless_allowed=headless_allowed, want_reviews=want_reviews)
            if not p:
                print("  ⚠️ Deep scrape failed → saving minimal record.")
                p = {
                    "engine": engine_hint,
                    "fetched_with": "none",
                    "name": unquote(urlparse(purl).path.strip("/").split("/")[-1] or "product"),
                    "brand": None,
                    "url": purl,
                    "sku": None, "gtin": None, "mpn": None, "availability": None,
                    "price": None, "currency": None,
                    "description": "",
                    "categories": [],
                    "attributes": {},
                    "review_rating": None,
                    "review_count": None,
                    "variants": [],
                    "images": [],
                    "reviews": [],
                    "raw_jsonld_product": {}
                }
        else:
            p = {
                "engine": engine_hint,
                "fetched_with": "none",
                "name": unquote(urlparse(purl).path.strip("/").split("/")[-1] or "product"),
                "brand": None,
                "url": purl,
                "sku": None, "gtin": None, "mpn": None, "availability": None,
                "price": None, "currency": None,
                "description": "",
                "categories": [],
                "attributes": {},
                "review_rating": None,
                "review_count": None,
                "variants": [],
                "images": [],
                "reviews": [],
                "raw_jsonld_product": {}
            }

        p["id"] = md5(p.get("url") or purl, 16)
        upsert_product(conn, p)

        image_rows = []
        if download_imgs and p.get("images"):
            image_rows = download_images(net, run_dir, p["id"], p.get("images"))

        replace_children(conn, p["id"], p.get("variants"), image_rows, p.get("reviews"))
        save_product_folder(run_dir, p)

        processed.add(purl)
        st["processed"] = list(processed)
        st["queue"] = [u for u in st.get("queue", []) if u not in processed]
        save_state(run_dir, st)

        sleep(BASE_DELAY)

    export_csv_xlsx(run_dir, conn)
    conn.close()

    st["analytics"]["finished_at"] = int(time.time())
    st["analytics"]["proxy_stats"] = net.proxy_stats
    save_state(run_dir, st)

    print("\n✅ DONE")
    print(f"Run folder: {run_dir}")
    print("Outputs: store.db, products.csv, products.xlsx, resume_state.json")

    print("\n📊 Strategy analytics (top):")
    best = st["analytics"].get("best_strategy")
    print(f"- Best: {best}")
    top = sorted(st["analytics"]["strategy"].items(),
                 key=lambda kv: (kv[1].get("ok",0), kv[1].get("found",0)),
                 reverse=True)[:8]
    for strat, info in top:
        print(f"- {strat}: ok={info['ok']} fail={info['fail']} found={info['found']} time={info['time_sec']:.1f}s")

    if domain_crawler_enabled:
        c = st["analytics"]["crawler"]
        print("\n🕷 Domain crawler stats:")
        print(f"- pages={c.get('pages')} category_pages={c.get('category_pages')} product_urls={c.get('product_urls')}")
        print(f"- crawl_delay_used={c.get('crawl_delay_used', BASE_DELAY)}s")

    if proxies:
        print("\n🛡 Proxy stats:")
        for pxy, s in st["analytics"]["proxy_stats"].items():
            print(f"- {pxy}: ok={s['ok']} fail={s['fail']}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped. Re-run and choose resume=y to continue.")
