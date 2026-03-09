#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Store Scrapper για Termux
Python scraper σε ένα μόνο αρχείο για πολλά online καταστήματα χωρίς root.

Δυνατότητες:
- Δοκιμάζει πολλούς τρόπους για να βρει κατηγορίες και προϊόντα
- Δουλεύει με απλές HTML σελίδες αλλά και με πολλά JS-based καταστήματα διαβάζοντας:
  HTML, JSON-LD, ενσωματωμένο JSON, sitemaps, Shopify endpoints, WooCommerce APIs,
  γενικές κάρτες προϊόντων, breadcrumbs, OpenGraph/meta tags και εσωτερικά links
- Αποθηκεύει όσο τρέχει
- Ξεκινά πλήρες scraping προϊόντος τη στιγμή που το βρίσκει
- Δείχνει ζωντανή κατάσταση στο terminal
- Enter = προεπιλογή σε όλα τα prompts
- Αποθηκεύει τα αποτελέσματα στο:
  ~/storage/downloads/Store Scrapper/<Κατάστημα>/<Κατηγορία>/<Προϊόν>/

Σημειώσεις:
- Κανένα scraper δεν μπορεί να εγγυηθεί 100% επιτυχία σε κάθε κατάστημα. Μερικά sites
  χρησιμοποιούν ισχυρή anti-bot προστασία ή ιδιωτικά APIs. Αυτό το script χρησιμοποιεί
  πολλές εναλλακτικές μεθόδους ώστε να πιάνει όσο το δυνατόν περισσότερα JS-driven stores
  χωρίς να χρειάζεται root.
"""

from __future__ import annotations

import os
import re
import sys
import json
import time
import math
import html
import queue
import random
import shutil
import signal
import socket
import hashlib
import pathlib
import zipfile
import threading
import subprocess
import traceback
import importlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse, parse_qsl, urlencode
from xml.etree import ElementTree as ET

# --------------------------- bootstrap dependencies ---------------------------

REQUIRED_PACKAGES = [
    ("requests", "requests"),
    ("bs4", "beautifulsoup4"),
]
OPTIONAL_PACKAGES = [
    ("cloudscraper", "cloudscraper"),
]


def ensure_package(import_name: str, pip_name: str, required: bool = True) -> bool:
    try:
        importlib.import_module(import_name)
        return True
    except Exception:
        pass

    try:
        with open(os.devnull, "wb") as devnull:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--upgrade", pip_name],
                stdout=devnull,
                stderr=devnull,
            )
        importlib.import_module(import_name)
        return True
    except Exception as exc:
        if required:
            print(f"[!] Αποτυχία εγκατάστασης του απαραίτητου πακέτου {pip_name}: {exc}", file=sys.stderr)
            sys.exit(1)
        return False


for _import_name, _pip_name in REQUIRED_PACKAGES:
    ensure_package(_import_name, _pip_name, required=True)

for _import_name, _pip_name in OPTIONAL_PACKAGES:
    ensure_package(_import_name, _pip_name, required=False)

import requests  # noqa: E402
from requests.adapters import HTTPAdapter  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

try:
    import cloudscraper  # type: ignore  # noqa: E402
except Exception:
    cloudscraper = None


# ------------------------------- misc helpers --------------------------------

VERSION = "1.4"
DEFAULT_TIMEOUT = 20
DEFAULT_DELAY_MIN = 0.05
DEFAULT_DELAY_MAX = 0.20
DEFAULT_MAX_CATEGORIES = 5
DEFAULT_MAX_PRODUCTS_PER_CATEGORY = 25
DEFAULT_MAX_PAGES_PER_CATEGORY = 10
DEFAULT_MAX_IMAGES_PER_PRODUCT = 5
DEFAULT_MAX_TOTAL_URLS = 500
DEFAULT_MAX_SITEMAP_URLS = 1500
DEFAULT_PRODUCT_WORKERS = 8
DEFAULT_IMAGE_WORKERS = 4
DEFAULT_CATEGORY_VERIFY_WORKERS = 6
DEFAULT_STATE_SAVE_INTERVAL = 2.0
DEFAULT_CONNECT_TIMEOUT = 6
DEFAULT_READ_TIMEOUT = 18
DEFAULT_TIMEOUT_STEP = 8

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 13; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

PRICE_RE = re.compile(
    r"(?:(?:€|\$|£|¥|₹)\s?\d[\d.,]*)|(?:\d[\d.,]*\s?(?:€|\$|£|¥|₹))|(?:\b\d[\d.,]*\b\s?(?:EUR|USD|GBP|JPY|INR))",
    re.I,
)
SCRIPT_JSON_ASSIGN_RE = re.compile(
    r"(?:window\.|var\s+|let\s+|const\s+)?(?:__INITIAL_STATE__|__PRELOADED_STATE__|__NUXT__|ShopifyAnalytics|meta|product|PRODUCT_DATA|productData)\s*=\s*(\{.*?\}|\[.*?\])\s*;",
    re.S,
)
RAW_URL_RE = re.compile(r'''(?:"|')((?:https?:)?//[^"'\s<>]+|/[A-Za-z0-9][^"'\s<>]+)(?:"|')''', re.I)
LIKELY_CATEGORY_WORDS = [
    "category", "categories", "collection", "collections", "department", "catalog", "catalogue",
    "product-category", "shop-all", "all-products", "all-shoes", "all-clothing", "new-arrivals",
    "new-releases", "mens", "mens-", "womens", "womens-", "kids", "boys", "girls",
    "sale", "shoes", "sneakers", "clothing", "apparel", "accessories", "sport", "sports",
    "running", "training", "football", "basketball", "tennis", "golf", "lifestyle", "jordan", "snkrs",
]
LIKELY_PRODUCT_WORDS = [
    "product", "products", "item", "sku", "buy", "p/", "/dp/", "prd", "details", "/t/",
]
BAD_LINK_WORDS = [
    "login", "register", "signup", "sign-in", "cart", "checkout", "wishlist",
    "account", "privacy", "terms", "returns", "help", "faq", "blog", "news",
    "contact", "about", "career", "jobs", "mailto:", "tel:", "javascript:",
    "membership", "member", "join-us", "join_us", "retail", "find-a-store", "find-store",
    "store-locator", "stores", "language", "country", "region", "guide", "lookbook",
]
BAD_CATEGORY_NAME_WORDS = [
    "find a store", "retail", "membership", "member", "join us", "join nike", "help", "support",
    "customer service", "shipping", "returns", "privacy", "terms", "account", "sign in", "login",
    "register", "wishlist", "bag", "cart", "checkout", "stories", "story", "guide", "lookbook",
    "news", "blog", "about", "careers", "jobs", "language", "english", "greece", "new zealand",
    "βρες ένα κατάστημα", "βοήθεια", "επιστροφ", "όροι", "πολιτική", "σύνδεση", "συνδεση", "λογαριασ",
    "καλάθι", "καλαθι", "ταμείο", "ταμειο", "οδηγός", "οδηγοι", "ιστορίες", "ιστοριες", "μέλος", "μελος",
    "έλα μαζί μας", "ελα μαζι μας", "αγγλικά", "αγγλικα",
]
BAD_CATEGORY_URL_WORDS = [
    "/retail", "/membership", "/member", "/help", "/support", "/privacy", "/terms", "/account", "/login",
    "/register", "/wishlist", "/bag", "/cart", "/checkout", "/blog", "/news", "/stories", "/story",
    "/guide", "/lookbook", "/jobs", "/careers", "/country", "/language", "/region",
]
COMMON_SECTION_WORDS = [
    "men", "women", "kids", "boys", "girls", "unisex", "sale", "new", "featured", "shoes",
    "sneakers", "boots", "sandals", "clothing", "apparel", "tops", "pants", "leggings", "shorts",
    "hoodies", "jackets", "accessories", "bags", "socks", "sport", "sports", "running", "training",
    "football", "soccer", "basketball", "tennis", "golf", "yoga", "lifestyle", "jordan", "snkrs", "acg",
    "ανδρ", "γυναικ", "παιδ", "εφηβ", "βρεφ", "προσφορ", "νεα", "δημοφι", "παπουτ", "ρουχ",
    "αξεσ", "τρεξ", "ποδοσφ", "μπασκε", "προπονη", "γυμναστη", "τενις", "γκολφ", "γιογκα", "τζορνταν",
]
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


class GracefulStop:
    def __init__(self) -> None:
        self.stop = False
        signal.signal(signal.SIGINT, self._handler)
        try:
            signal.signal(signal.SIGTERM, self._handler)
        except Exception:
            pass

    def _handler(self, signum, frame) -> None:
        self.stop = True
        print("\n[!] Ζητήθηκε διακοπή. Ολοκλήρωση του τρέχοντος βήματος με ασφάλεια...")


STOPPER = GracefulStop()


def truncate(text: Any, length: int = 60) -> str:
    text = "" if text is None else str(text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= length:
        return text
    return text[: max(0, length - 3)] + "..."


def now_ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def human_delay(min_s: float, max_s: float) -> None:
    if max_s <= 0:
        return
    time.sleep(random.uniform(max(0.0, min_s), max(min_s, max_s)))


def clean_text(text: Any) -> str:
    if text is None:
        return ""
    if isinstance(text, (dict, list)):
        try:
            text = json.dumps(text, ensure_ascii=False)
        except Exception:
            text = str(text)
    text = html.unescape(str(text))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def sanitize_name(name: str, max_len: int = 120) -> str:
    name = clean_text(name)
    if not name:
        name = "Χωρίς Όνομα"
    name = name.replace("/", "-").replace("\\", "-")
    name = re.sub(r"[:*?\"<>|]", "", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name[:max_len] or "Χωρίς Όνομα"


def slugify(name: str, max_len: int = 120) -> str:
    name = sanitize_name(name, max_len=max_len)
    return name


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def json_dump(obj: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def json_dump_sync(obj: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass


def write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text or "")


def write_text_sync(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text or "")
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass


def append_text_sync(path: str, text: str) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(text or "")
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass


def unique_keep_order(items: List[Any]) -> List[Any]:
    seen = set()
    out = []
    for item in items:
        key = item
        if isinstance(item, dict):
            key = json.dumps(item, sort_keys=True, ensure_ascii=False)
        elif not isinstance(item, (str, int, float, tuple)):
            key = repr(item)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def canonicalize_url(url: str) -> str:
    try:
        parts = urlparse(url.strip())
        scheme = parts.scheme or "https"
        netloc = parts.netloc.lower()
        path = re.sub(r"/+", "/", parts.path or "/")
        query_items = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                       if k.lower() not in {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "gclid"}]
        query = urlencode(query_items)
        return urlunparse((scheme, netloc, path.rstrip("/") or "/", "", query, ""))
    except Exception:
        return url


def same_domain(base_url: str, other_url: str) -> bool:
    try:
        a = urlparse(base_url).netloc.lower().split(":")[0]
        b = urlparse(other_url).netloc.lower().split(":")[0]
        return a == b or a.endswith("." + b) or b.endswith("." + a)
    except Exception:
        return False

def path_parts(url: str) -> List[str]:
    try:
        return [p for p in urlparse(url).path.split("/") if p]
    except Exception:
        return []


def strip_locale_parts(parts: List[str]) -> List[str]:
    if not parts:
        return []
    first = parts[0].lower()
    if re.fullmatch(r"[a-z]{2}(?:-[a-z]{2})?", first):
        return parts[1:]
    return parts


def looks_like_locale_root(url: str) -> bool:
    parts = path_parts(url)
    if not parts:
        return False
    stripped = strip_locale_parts(parts)
    return not stripped


def human_name_from_url(url: str) -> str:
    parts = strip_locale_parts(path_parts(url))
    if not parts:
        return "Κατηγορία"
    value = parts[-1]
    value = re.sub(r"[-_]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return sanitize_name(value or "Category")


def looks_like_bad_category_name(name: str) -> bool:
    lower = clean_text(name).lower()
    if not lower:
        return False
    return any(word in lower for word in BAD_CATEGORY_NAME_WORDS)


def looks_like_bad_category_url(url: str) -> bool:
    lower = canonicalize_url(url).lower()
    if looks_like_locale_root(lower):
        return True
    return any(word in lower for word in BAD_CATEGORY_URL_WORDS)


def looks_like_section_name(name: str) -> bool:
    lower = clean_text(name).lower()
    if not lower or looks_like_bad_category_name(lower):
        return False
    if any(word in lower for word in COMMON_SECTION_WORDS):
        return True
    words = [w for w in re.split(r"\s+", lower) if w]
    return 1 <= len(words) <= 5 and 2 <= len(lower) <= 40



def ext_from_url(url: str, default: str = ".bin") -> str:
    try:
        path = urlparse(url).path
        ext = os.path.splitext(path)[1].lower()
        if ext in IMAGE_EXTS:
            return ext
    except Exception:
        pass
    return default


def pick_first(*values: Any) -> str:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return ""


def parse_price_and_currency(text: str) -> Tuple[str, str]:
    text = clean_text(text)
    if not text:
        return "", ""
    currency = ""
    if "€" in text or "EUR" in text.upper():
        currency = "EUR"
    elif "$" in text or "USD" in text.upper():
        currency = "USD"
    elif "£" in text or "GBP" in text.upper():
        currency = "GBP"
    elif "¥" in text or "JPY" in text.upper():
        currency = "JPY"
    elif "₹" in text or "INR" in text.upper():
        currency = "INR"
    number_match = re.search(r"\d[\d.,]*", text)
    return (number_match.group(0) if number_match else "", currency)


def is_likely_category_url(url: str) -> bool:
    url = canonicalize_url(url)
    lower = url.lower()
    if any(word in lower for word in BAD_LINK_WORDS):
        return False
    if looks_like_bad_category_url(lower):
        return False
    parts = strip_locale_parts(path_parts(lower))
    if not parts:
        return False
    path = "/" + "/".join(parts)
    if re.search(r"/(?:w|c|b)(?:/|$)", path):
        return True
    if any(word in path for word in LIKELY_CATEGORY_WORDS):
        return True
    last = parts[-1]
    if any(word in last for word in LIKELY_CATEGORY_WORDS):
        return True
    if any(word in last for word in COMMON_SECTION_WORDS):
        return True
    return False


def is_likely_product_url(url: str) -> bool:
    url = canonicalize_url(url)
    lower = url.lower()
    if any(word in lower for word in BAD_LINK_WORDS):
        return False
    if looks_like_bad_category_url(lower) or looks_like_locale_root(lower):
        return False
    if any(word in lower for word in LIKELY_PRODUCT_WORDS):
        return True
    path = urlparse(lower).path.strip("/")
    parts = [p for p in path.split("/") if p]
    parts = strip_locale_parts(parts)
    if len(parts) < 2:
        return False
    if any(seg in {"product", "products", "item", "items", "p", "dp", "prd", "sku", "t"} for seg in parts[:-1]):
        return True
    last = parts[-1]
    prev = parts[-2] if len(parts) >= 2 else ""
    if len(parts) >= 3 and re.search(r"[a-z]", last):
        if re.search(r"[0-9]", last) or re.search(r"[0-9]", prev):
            return True
        if re.search(r"-[a-z0-9]{4,}$", last, re.I):
            return True
    if len(parts) >= 4 and re.search(r"[a-z]", last):
        return True
    return False


def looks_like_image(url: str) -> bool:
    lower = url.lower().split("?")[0]
    return any(lower.endswith(ext) for ext in IMAGE_EXTS)


def score_image_url(url: str) -> int:
    lower = canonicalize_url(url).lower()
    score = 0
    if not lower:
        return -100
    if any(word in lower for word in ["logo", "icon", "sprite", "favicon", "avatar", "flag", "badge", "placeholder"]):
        score -= 20
    if any(word in lower for word in ["product", "products", "catalog", "pdp", "item", "image", "images", "original", "zoom"]):
        score += 8
    if re.search(r"(?:^|[_-])\d{3,4}(?:x|w_|h_)?\d{0,4}", lower):
        score += 2
    if looks_like_image(lower):
        score += 1
    return score


def rank_image_urls(urls: List[str]) -> List[str]:
    urls = unique_keep_order([canonicalize_url(u) for u in urls if u])
    return [u for _, u in sorted(((score_image_url(u), u) for u in urls), key=lambda x: (-x[0], x[1]))]


def maybe_json(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return None


def recursive_find_productish(obj: Any, limit: int = 25) -> List[Dict[str, Any]]:
    found: List[Dict[str, Any]] = []

    def walk(node: Any) -> None:
        nonlocal found
        if len(found) >= limit:
            return
        if isinstance(node, dict):
            keys = {str(k).lower() for k in node.keys()}
            good = 0
            for name in ["name", "title"]:
                if name in keys:
                    good += 1
            for price in ["price", "saleprice", "pricevalue", "amount", "price_amount"]:
                if price in keys:
                    good += 1
            for img in ["image", "images", "thumbnail", "featuredimage"]:
                if img in keys:
                    good += 1
            if good >= 2:
                found.append(node)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(obj)
    return found


def safe_json_from_script(script_text: str) -> List[Any]:
    results: List[Any] = []
    script_text = script_text.strip()
    if not script_text:
        return results
    obj = maybe_json(script_text)
    if obj is not None:
        results.append(obj)
    for match in SCRIPT_JSON_ASSIGN_RE.finditer(script_text):
        obj = maybe_json(match.group(1))
        if obj is not None:
            results.append(obj)
    return results


def get_home_downloads_dir() -> str:
    termux_downloads = os.path.expanduser("~/storage/downloads")
    fallback_downloads = os.path.expanduser("~/downloads")
    if os.path.isdir(termux_downloads):
        return termux_downloads
    setup_cmd = shutil.which("termux-setup-storage")
    if setup_cmd:
        try:
            with open(os.devnull, "wb") as devnull:
                subprocess.run([setup_cmd], check=False, stdout=devnull, stderr=devnull)
            time.sleep(2.0)
        except Exception:
            pass
        if os.path.isdir(termux_downloads):
            return termux_downloads
    ensure_dir(fallback_downloads)
    return fallback_downloads


def input_default(prompt: str, default: str) -> str:
    value = input(f"{prompt} [{default}]: ").strip()
    return value if value else default


def input_int(prompt: str, default: int, minimum: int = 0) -> int:
    while True:
        value = input(f"{prompt} [{default}]: ").strip()
        if not value:
            return default
        try:
            number = int(value)
            if number < minimum:
                raise ValueError
            return number
        except Exception:
            print(f"[!] Δώσε έναν αριθμό >= {minimum} ή απλώς πάτα Enter για την προεπιλογή.")


def input_yes_no(prompt: str, default: bool = True) -> bool:
    default_txt = "Ν/ο" if default else "ν/Ο"
    value = input(f"{prompt} [{default_txt}]: ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes", "1", "true", "ν", "ναι"}


def greek_phase_label(phase: str) -> str:
    mapping = {
        "idle": "αναμονή",
        "fetch": "λήψη",
        "discover-categories": "εντοπισμός-κατηγοριών",
        "scrape-category": "σάρωση-κατηγορίας",
        "scrape-product": "σάρωση-προϊόντος",
        "shopify-api": "shopify-api",
        "woocommerce-api": "woocommerce-api",
        "generic-listing": "γενική-λίστα",
        "save-image": "αποθήκευση-εικόνας",
        "prepare": "προετοιμασία",
        "start": "έναρξη",
        "done": "ολοκληρώθηκε",
    }
    return mapping.get(phase, phase)


def greek_input_mode(mode: str) -> str:
    mapping = {
        "site": "ολόκληρο site",
        "category": "κατηγορία",
        "product": "προϊόν",
    }
    return mapping.get(mode, mode)


def greek_stat_key(key: str) -> str:
    mapping = {
        "saved_products": "αποθηκευμένα_προϊόντα",
        "skipped_duplicates": "διπλότυπα_που_παραλείφθηκαν",
        "errors": "σφάλματα",
        "fetched_pages": "σελίδες_που_λήφθηκαν",
        "discovered_categories": "κατηγορίες_που_βρέθηκαν",
        "discovered_products": "προϊόντα_που_βρέθηκαν",
        "downloaded_images": "εικόνες_που_κατέβηκαν",
    }
    return mapping.get(key, key)


def greek_platforms(platforms: Set[str]) -> str:
    return ", ".join(sorted(platforms)) or "γενικό"


# -------------------------------- live status --------------------------------

class LiveStatus:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.phase = "αναμονή"
        self.store = ""
        self.category = ""
        self.page = 0
        self.saved = 0
        self.products_found = 0
        self.categories_found = 0
        self.current_url = ""
        self.last_item = ""
        self.http_code = ""
        self.errors = 0
        self.started_at = time.time()

    def set(self, **kwargs: Any) -> None:
        with self.lock:
            for k, v in kwargs.items():
                if hasattr(self, k):
                    setattr(self, k, v)

    def inc(self, key: str, amount: int = 1) -> None:
        with self.lock:
            if hasattr(self, key):
                setattr(self, key, getattr(self, key) + amount)

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.5)

    def _loop(self) -> None:
        while self.running:
            with self.lock:
                elapsed = int(time.time() - self.started_at)
                msg = (
                    f"[LIVE] φάση={greek_phase_label(self.phase)} | κατάστημα={truncate(self.store, 22)} | "
                    f"κατ={truncate(self.category, 18)} | σελίδα={self.page} | "
                    f"αποθ={self.saved} | προϊ={self.products_found} | κατηγ={self.categories_found} | "
                    f"http={self.http_code or '-'} | σφάλμ={self.errors} | "
                    f"τελευταίο={truncate(self.last_item, 28)} | url={truncate(self.current_url, 58)} | "
                    f"χρόνος={elapsed}s"
                )
            print(msg)
            time.sleep(1.5)


# --------------------------------- data types --------------------------------

@dataclass
class CategoryRecord:
    name: str
    url: str
    source: str = "generic"
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProductRecord:
    name: str
    url: str
    category: str = "Uncategorized"
    description: str = ""
    price: str = ""
    price_text: str = ""
    currency: str = ""
    images: List[str] = field(default_factory=list)
    brand: str = ""
    sku: str = ""
    source: str = "generic"
    extra: Dict[str, Any] = field(default_factory=dict)


# -------------------------------- main scraper --------------------------------

class StoreScrapper:
    def __init__(self, base_url: str, config: Dict[str, Any]) -> None:
        self.base_url = canonicalize_url(base_url)
        self.parsed_base = urlparse(self.base_url)
        self.scheme = self.parsed_base.scheme or "https"
        self.netloc = self.parsed_base.netloc
        self.root_url = f"{self.scheme}://{self.netloc}"
        self.config = config
        self.status = LiveStatus()
        self.status.start()
        self.store_name = self.netloc
        self.output_root = ""
        self.platform: Set[str] = set()
        self.discovered_categories: List[CategoryRecord] = []
        self.visited_urls: Set[str] = set()
        self.saved_product_keys: Set[str] = set()
        self.discovery_notes: List[str] = []
        self.stats = {
            "saved_products": 0,
            "skipped_duplicates": 0,
            "errors": 0,
            "fetched_pages": 0,
            "discovered_categories": 0,
            "discovered_products": 0,
            "downloaded_images": 0,
        }
        self.state_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        self.discovery_lock = threading.Lock()
        self._thread_local = threading.local()
        self.last_state_save = 0.0
        self.discovered_product_urls: List[str] = []
        self.sitemap_product_urls: List[str] = []
        self.recorded_discovery_keys: Set[str] = set()
        self.requests_session = self._make_session()
        self.input_mode = self.detect_input_mode(self.base_url)
        self._active_category_dir = ""
        self._active_category_name = ""
        self._active_category_products: List[ProductRecord] = []
        self._active_category_seen_keys: Set[str] = set()
        self._active_category_detail_futures = []
        self._active_category_detail_executor = None
        self._active_category_task_index = 0

    # ----------------------------- session/network ----------------------------

    def _make_session(self):
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Connection": "keep-alive",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
        }
        pool_size = max(
            16,
            int(self.config.get("product_workers", DEFAULT_PRODUCT_WORKERS)) * 2,
            int(self.config.get("image_workers", DEFAULT_IMAGE_WORKERS)) * 2,
        )
        if cloudscraper is not None:
            try:
                sess = cloudscraper.create_scraper(
                    browser={"browser": "chrome", "platform": "android", "mobile": True}
                )
                sess.headers.update(headers)
                adapter = HTTPAdapter(pool_connections=pool_size, pool_maxsize=pool_size)
                sess.mount("http://", adapter)
                sess.mount("https://", adapter)
                return sess
            except Exception:
                pass
        sess = requests.Session()
        sess.headers.update(headers)
        adapter = HTTPAdapter(pool_connections=pool_size, pool_maxsize=pool_size)
        sess.mount("http://", adapter)
        sess.mount("https://", adapter)
        return sess

    def _get_session(self):
        sess = getattr(self._thread_local, "session", None)
        if sess is None:
            sess = self._make_session()
            self._thread_local.session = sess
        return sess

    def bump_stat(self, key: str, amount: int = 1) -> None:
        with self.stats_lock:
            self.stats[key] = int(self.stats.get(key, 0)) + amount

    def detect_input_mode(self, url: str) -> str:
        url = canonicalize_url(url)
        if is_likely_product_url(url):
            return "product"
        if is_likely_category_url(url):
            return "category"
        parts = [p for p in strip_locale_parts(path_parts(url)) if p]
        if len(parts) <= 1:
            return "site"
        return "category"

    def request_timeout(self, attempt: int = 1, kind: str = "html") -> Tuple[int, int]:
        connect_base = int(self.config.get("connect_timeout", DEFAULT_CONNECT_TIMEOUT))
        read_base = int(self.config.get("read_timeout", self.config.get("timeout", DEFAULT_READ_TIMEOUT)))
        step = int(self.config.get("timeout_step", DEFAULT_TIMEOUT_STEP))
        connect_timeout = max(3, min(20, connect_base + max(0, attempt - 1)))
        if kind == "json":
            read_timeout = read_base + 4 + (max(0, attempt - 1) * step)
        elif kind == "image":
            read_timeout = read_base + 10 + (max(0, attempt - 1) * step)
        else:
            read_timeout = read_base + (max(0, attempt - 1) * step)
        return int(connect_timeout), int(max(connect_timeout + 4, read_timeout))

    def fetch(self, url: str, referer: str = "", accept_json: bool = False, delay: bool = True) -> Optional[requests.Response]:
        url = canonicalize_url(url)
        if STOPPER.stop:
            return None
        self.status.set(phase="fetch", current_url=url)
        if delay:
            human_delay(self.config["delay_min"], self.config["delay_max"])
        headers = {}
        if referer:
            headers["Referer"] = referer
        if accept_json:
            headers["Accept"] = "application/json,text/plain,*/*"
        for attempt in range(1, self.config["retries"] + 1):
            try:
                resp = self._get_session().get(
                    url,
                    timeout=self.request_timeout(attempt, "json" if accept_json else "html"),
                    allow_redirects=True,
                    headers=headers,
                )
                self.bump_stat("fetched_pages", 1)
                self.status.set(http_code=str(resp.status_code))
                if resp.status_code >= 400:
                    if attempt == self.config["retries"]:
                        return resp
                    human_delay(0.6, 1.2)
                    continue
                return resp
            except Exception:
                if attempt == self.config["retries"]:
                    self.bump_stat("errors", 1)
                    self.status.inc("errors", 1)
                    return None
                human_delay(0.5, 1.0)
        return None

    def fetch_text(self, url: str, referer: str = "", accept_json: bool = False) -> str:
        resp = self.fetch(url, referer=referer, accept_json=accept_json)
        if resp is None:
            return ""
        try:
            return resp.text
        except Exception:
            return resp.content.decode("utf-8", errors="ignore")

    def fetch_json(self, url: str, referer: str = "") -> Any:
        resp = self.fetch(url, referer=referer, accept_json=True)
        if resp is None:
            return None
        try:
            return resp.json()
        except Exception:
            try:
                return json.loads(resp.text)
            except Exception:
                return None

    # -------------------------------- parsing --------------------------------

    def detect_platforms(self, html_text: str) -> None:
        lower = html_text.lower()
        if "shopify" in lower or "/cdn/shop/" in lower or "shopifyanalytics" in lower:
            self.platform.add("shopify")
        if "woocommerce" in lower or "/wp-content/" in lower or "/wp-json/" in lower:
            self.platform.add("woocommerce")
        if "__next_data__" in lower or 'id="__next_data__"' in lower:
            self.platform.add("nextjs")
        if "__nuxt" in lower:
            self.platform.add("nuxt")
        if "squarespace" in lower:
            self.platform.add("squarespace")
        if "wix" in lower or "wixstatic" in lower:
            self.platform.add("wix")
        if "magento" in lower or "mage/" in lower:
            self.platform.add("magento")

    def soup(self, html_text: str) -> BeautifulSoup:
        return BeautifulSoup(html_text, "html.parser")

    def get_meta(self, soup: BeautifulSoup, *names: str) -> str:
        for name in names:
            tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
            if tag and tag.get("content"):
                return clean_text(tag.get("content"))
        return ""

    def page_title(self, soup: BeautifulSoup) -> str:
        if soup.title and soup.title.text:
            return clean_text(soup.title.text)
        for selector in ["h1", "meta[property='og:title']"]:
            found = soup.select_one(selector)
            if found:
                if found.name == "meta":
                    return clean_text(found.get("content"))
                return clean_text(found.get_text(" ", strip=True))
        return ""

    def extract_site_name(self, soup: BeautifulSoup) -> str:
        site_name = self.get_meta(soup, "og:site_name", "application-name")
        if site_name:
            return sanitize_name(site_name)
        title = self.page_title(soup)
        if title:
            parts = re.split(r"\s*[|\-–:]\s*", title)
            if parts:
                return sanitize_name(parts[-1] if len(parts[-1]) <= 40 else parts[0])
        return sanitize_name(self.netloc.split(":")[0].replace("www.", ""))

    def extract_links(self, html_text: str, base_url: str) -> List[Tuple[str, str]]:
        soup = self.soup(html_text)
        links: List[Tuple[str, str]] = []
        for a in soup.find_all("a", href=True):
            href = a.get("href") or ""
            text = clean_text(a.get_text(" ", strip=True))
            url = canonicalize_url(urljoin(base_url, href))
            if not url.startswith(("http://", "https://")):
                continue
            if not same_domain(self.root_url, url):
                continue
            if any(bad in url.lower() for bad in BAD_LINK_WORDS):
                continue
            links.append((url, text))
        return unique_keep_order(links)

    def extract_embedded_candidate_urls(self, html_text: str, base_url: str) -> List[str]:
        urls: List[str] = []
        if not html_text:
            return urls
        for raw in RAW_URL_RE.findall(html_text):
            raw = clean_text(raw)
            if not raw:
                continue
            if raw.startswith("//"):
                raw = f"{self.scheme}:{raw}"
            url = canonicalize_url(urljoin(base_url, raw))
            if not url.startswith(("http://", "https://")):
                continue
            if not same_domain(self.root_url, url):
                continue
            lower = url.lower()
            if any(bad in lower for bad in BAD_LINK_WORDS):
                continue
            urls.append(url)
            if len(urls) >= int(self.config.get("max_total_urls", DEFAULT_MAX_TOTAL_URLS)):
                break
        return unique_keep_order(urls)

    def seed_products_for_category(self, category: CategoryRecord) -> List[ProductRecord]:
        seeds: List[ProductRecord] = []
        category_parts = [p.lower() for p in strip_locale_parts(path_parts(category.url))]
        category_tokens = [t for t in re.findall(r"[a-z0-9]+", category.name.lower()) if len(t) >= 3]
        candidate_urls = unique_keep_order(self.sitemap_product_urls + self.discovered_product_urls)
        max_seed = int(self.config.get("max_total_urls", DEFAULT_MAX_TOTAL_URLS))
        for url in candidate_urls:
            if not is_likely_product_url(url):
                continue
            path = urlparse(url).path.lower()
            score = 0
            for part in category_parts[-3:]:
                if not part:
                    continue
                if f"/{part}/" in path or path.endswith("/" + part):
                    score += 2
                elif part in path:
                    score += 1
            for token in category_tokens[:4]:
                if token in path:
                    score += 1
            if category.source == "fallback-home" and not category_parts:
                score += 2
            if score >= 2:
                seeds.append(ProductRecord(
                    name=sanitize_name(pathlib.Path(urlparse(url).path).name or "Προϊόν"),
                    url=canonicalize_url(url),
                    category=category.name,
                    source="seed-url",
                ))
            if len(seeds) >= max_seed:
                break
        return unique_keep_order(seeds)

    def parse_sitemap_xml(self, xml_text: str) -> List[str]:
        urls: List[str] = []
        xml_text = xml_text.strip()
        if not xml_text:
            return urls
        try:
            root = ET.fromstring(xml_text)
        except Exception:
            return urls
        for elem in root.iter():
            tag = elem.tag.lower()
            if tag.endswith("loc") and elem.text:
                urls.append(canonicalize_url(elem.text.strip()))
        return unique_keep_order(urls)

    def get_sitemap_urls(self) -> List[str]:
        sitemap_urls = []
        robots = self.fetch_text(urljoin(self.root_url, "/robots.txt"), referer=self.root_url)
        if robots:
            for line in robots.splitlines():
                if line.lower().startswith("sitemap:"):
                    sitemap_urls.append(canonicalize_url(line.split(":", 1)[1].strip()))
        sitemap_urls += [
            urljoin(self.root_url, "/sitemap.xml"),
            urljoin(self.root_url, "/sitemap_index.xml"),
            urljoin(self.root_url, "/sitemap_products_1.xml"),
        ]
        return unique_keep_order([u for u in sitemap_urls if u])

    def crawl_sitemaps(self, limit: int) -> Tuple[List[str], List[str]]:
        seen: Set[str] = set()
        queue_urls: List[str] = list(self.get_sitemap_urls())
        category_urls: List[str] = []
        product_urls: List[str] = []
        processed = 0
        while queue_urls and processed < 40 and len(seen) < limit and not STOPPER.stop:
            current = queue_urls.pop(0)
            if current in seen:
                continue
            seen.add(current)
            processed += 1
            xml_text = self.fetch_text(current, referer=self.root_url)
            if not xml_text:
                continue
            locs = self.parse_sitemap_xml(xml_text)
            if not locs:
                continue
            for loc in locs:
                if len(seen) >= limit:
                    break
                lower = loc.lower()
                if lower.endswith(".xml"):
                    queue_urls.append(loc)
                elif is_likely_category_url(loc):
                    category_urls.append(loc)
                elif is_likely_product_url(loc):
                    product_urls.append(loc)
                else:
                    # keep maybe-product URLs too
                    path = urlparse(loc).path.lower()
                    if path.count("/") >= 2:
                        product_urls.append(loc)
        return unique_keep_order(category_urls), unique_keep_order(product_urls)

    def category_candidate_name(self, text: str, url: str) -> str:
        return sanitize_name(text or human_name_from_url(url) or "Category")

    def extract_section_links_from_homepage(self, html_text: str, base_url: str) -> List[CategoryRecord]:
        soup = self.soup(html_text)
        found: List[CategoryRecord] = []
        selectors = [
            "header a[href]",
            "nav a[href]",
            "[role='navigation'] a[href]",
            ".menu a[href]",
            ".navigation a[href]",
            "[data-testid*='nav'] a[href]",
        ]
        seen: Set[str] = set()
        for selector in selectors:
            for a in soup.select(selector):
                href = a.get("href")
                if not href:
                    continue
                url = canonicalize_url(urljoin(base_url, href))
                if url in seen or not same_domain(self.root_url, url):
                    continue
                seen.add(url)
                text = clean_text(a.get_text(" ", strip=True))
                if looks_like_bad_category_url(url) or looks_like_bad_category_name(text):
                    continue
                if is_likely_category_url(url) or looks_like_section_name(text):
                    found.append(CategoryRecord(name=self.category_candidate_name(text, url), url=url, source="section-link"))
        return found

    def score_category_candidate(self, cat: CategoryRecord) -> int:
        url = canonicalize_url(cat.url)
        name = clean_text(cat.name).lower()
        lower = url.lower()
        parts = strip_locale_parts(path_parts(lower))
        score = 0
        if cat.source == "section-link":
            score += 24
        elif cat.source == "homepage-link":
            score += 18
        elif cat.source == "nav-link":
            score += 16
        elif cat.source == "shopify-api":
            score += 20
        elif cat.source == "woocommerce-api":
            score += 20
        elif cat.source == "sitemap":
            score += 8
        if looks_like_bad_category_url(url) or looks_like_bad_category_name(name):
            score -= 100
        if is_likely_category_url(url):
            score += 12
        if looks_like_section_name(name):
            score += 12
        if any(word in name for word in COMMON_SECTION_WORDS):
            score += 10
        if any(x in lower for x in ["/all", "all-products", "shop-all"]):
            score += 6
        if re.search(r"/(?:w|c|b)(?:/|$)", "/" + "/".join(parts)):
            score += 6
        if len(parts) <= 3:
            score += 3
        if name in {"new", "news", "blog", "stories", "story"}:
            score -= 20
        return score

    def score_category_page(self, category: CategoryRecord) -> int:
        html_text = self.fetch_text(category.url, referer=self.base_url)
        if not html_text:
            return -8
        soup = self.soup(html_text)
        score = 0
        title = " ".join([
            self.page_title(soup),
            self.get_meta(soup, "og:title", "description", "og:description"),
        ]).lower()
        if looks_like_bad_category_name(title) or looks_like_bad_category_url(category.url):
            score -= 20
        product_links = []
        for url, _ in self.extract_links(html_text, category.url):
            if is_likely_product_url(url):
                product_links.append(url)
        product_links = unique_keep_order(product_links)
        if len(product_links) >= 12:
            score += 18
        elif len(product_links) >= 6:
            score += 12
        elif len(product_links) >= 2:
            score += 7
        elif len(product_links) >= 1:
            score += 3
        text = clean_text(soup.get_text(" ", strip=True))[:40000]
        price_hits = len(PRICE_RE.findall(text))
        if price_hits >= 8:
            score += 12
        elif price_hits >= 3:
            score += 7
        elif price_hits >= 1:
            score += 3
        has_ld_product = False
        has_ld_itemlist = False
        for script in soup.find_all("script", attrs={"type": re.compile(r"application/ld\+json", re.I)}):
            payload = script.get_text("\n", strip=False)
            if not payload:
                continue
            if '"@type":"Product"' in payload or '"@type": "Product"' in payload:
                has_ld_product = True
            if '"@type":"ItemList"' in payload or '"@type": "ItemList"' in payload:
                has_ld_itemlist = True
        if has_ld_product:
            score += 8
        if has_ld_itemlist:
            score += 6
        body_lower = text.lower()
        if any(word in body_lower for word in ["add to bag", "add to cart", "shop now", "buy now", "choose size", "select size"]):
            score += 4
        return score

    def discover_categories(self) -> List[CategoryRecord]:
        self.status.set(phase="discover-categories", category="", page=0)
        homepage = self.fetch_text(self.base_url, referer=self.root_url)
        categories: List[CategoryRecord] = []
        discovered_products_from_sitemap: List[str] = []

        if homepage:
            soup = self.soup(homepage)
            self.detect_platforms(homepage)
            self.store_name = self.extract_site_name(soup)
            self.status.set(store=self.store_name)

            categories.extend(self.extract_section_links_from_homepage(homepage, self.base_url))

            for url, text in self.extract_links(homepage, self.base_url):
                if looks_like_bad_category_url(url) or looks_like_bad_category_name(text):
                    continue
                if is_likely_category_url(url) or looks_like_section_name(text):
                    categories.append(CategoryRecord(name=self.category_candidate_name(text, url), url=url, source="homepage-link"))
                elif is_likely_product_url(url):
                    self.discovered_product_urls.append(url)

            for url in self.extract_embedded_candidate_urls(homepage, self.base_url):
                if looks_like_bad_category_url(url):
                    continue
                if is_likely_category_url(url):
                    categories.append(CategoryRecord(name=self.category_candidate_name("", url), url=url, source="embedded-url"))
                elif is_likely_product_url(url):
                    self.discovered_product_urls.append(url)

        if "shopify" in self.platform:
            shopify_collections = self.fetch_json(urljoin(self.root_url, "/collections.json?limit=250&page=1"), referer=self.base_url)
            if isinstance(shopify_collections, dict):
                for item in shopify_collections.get("collections", []) or []:
                    handle = item.get("handle") or item.get("title") or "collection"
                    url = urljoin(self.root_url, f"/collections/{handle}")
                    categories.append(CategoryRecord(
                        name=sanitize_name(item.get("title") or handle),
                        url=canonicalize_url(url),
                        source="shopify-api",
                        meta=item,
                    ))

        wc_categories = self.fetch_json(urljoin(self.root_url, "/wp-json/wc/store/v1/products/categories"), referer=self.base_url)
        if isinstance(wc_categories, list):
            self.platform.add("woocommerce")
            for item in wc_categories:
                slug = item.get("slug") or item.get("name") or "category"
                url = urljoin(self.root_url, f"/product-category/{slug}")
                categories.append(CategoryRecord(
                    name=sanitize_name(item.get("name") or slug),
                    url=canonicalize_url(url),
                    source="woocommerce-api",
                    meta=item,
                ))

        sitemap_categories, discovered_products_from_sitemap = self.crawl_sitemaps(self.config["max_sitemap_urls"])
        self.sitemap_product_urls = unique_keep_order(discovered_products_from_sitemap)
        self.discovered_product_urls = unique_keep_order(self.discovered_product_urls + self.sitemap_product_urls)
        for url in sitemap_categories:
            if looks_like_bad_category_url(url):
                continue
            name = human_name_from_url(url)
            categories.append(CategoryRecord(name=sanitize_name(name), url=url, source="sitemap"))

        categories = self.rank_categories(categories)
        if not categories:
            categories = [CategoryRecord(name="Όλα τα Προϊόντα", url=self.base_url, source="fallback-home")]

        verify_cap = min(max(20, self.config.get("default_category_count", 5) * 4), len(categories), 36)
        rescored = []
        page_scores: Dict[str, int] = {}
        verify_targets = [cat for idx, cat in enumerate(categories[:verify_cap]) if cat.source != "fallback-home"]
        verify_workers = max(1, min(int(self.config.get("category_verify_workers", DEFAULT_CATEGORY_VERIFY_WORKERS)), len(verify_targets) or 1))
        if verify_targets:
            with ThreadPoolExecutor(max_workers=verify_workers) as executor:
                futures = {executor.submit(self.score_category_page, cat): cat.url for cat in verify_targets}
                for future in as_completed(futures):
                    url = futures[future]
                    try:
                        page_scores[url] = int(future.result())
                    except Exception:
                        page_scores[url] = -8
        for idx, cat in enumerate(categories):
            base_score = self.score_category_candidate(cat)
            page_score = page_scores.get(cat.url, 0)
            rescored.append((base_score + page_score, cat))
        rescored.sort(key=lambda x: (-x[0], x[1].name.lower(), x[1].url))
        categories = [cat for score, cat in rescored if score > -20]

        self.stats["discovered_categories"] = len(categories)
        self.status.set(categories_found=len(categories))
        self.discovery_notes.append(f"Πλατφόρμες που εντοπίστηκαν: {greek_platforms(self.platform)}")
        self.discovery_notes.append(f"Βρέθηκαν URLs προϊόντων από sitemap: {len(discovered_products_from_sitemap)}")
        self.discovery_notes.append(f"Βρέθηκαν αρχικά URLs προϊόντων: {len(self.discovered_product_urls)}")
        self.discovery_notes.append(f"Βρέθηκαν κατηγορίες: {len(categories)}")
        return categories

    def rank_categories(self, categories: List[CategoryRecord]) -> List[CategoryRecord]:
        scored = []
        seen_urls: Set[str] = set()
        seen_keys: Set[Tuple[str, str]] = set()
        for cat in categories:
            url = canonicalize_url(cat.url)
            name = sanitize_name(cat.name or human_name_from_url(url) or "Category")
            if not url or url in seen_urls:
                continue
            key = (name.lower(), url)
            if key in seen_keys:
                continue
            seen_urls.add(url)
            seen_keys.add(key)
            if looks_like_bad_category_url(url) or looks_like_bad_category_name(name):
                continue
            scored.append((self.score_category_candidate(CategoryRecord(name=name, url=url, source=cat.source, meta=cat.meta)), CategoryRecord(name=name, url=url, source=cat.source, meta=cat.meta)))
        scored.sort(key=lambda x: (-x[0], x[1].name.lower(), x[1].url))
        return [item for _, item in scored]

    def parse_category_selection_spec(self, spec: str, total: int) -> List[int]:
        spec = clean_text(spec)
        if not spec:
            default_count = int(self.config.get("default_category_count", 0) or 0)
            if default_count <= 0 or default_count >= total:
                return list(range(total))
            return list(range(default_count))
        lower = spec.lower().replace(" ", "")
        if lower in {"0", "all", "a", "*"}:
            return list(range(total))
        picked: Set[int] = set()
        for part in lower.split(","):
            if not part:
                continue
            if "-" in part:
                left, right = part.split("-", 1)
                if left.isdigit() and right.isdigit():
                    start = int(left)
                    end = int(right)
                    if start > end:
                        start, end = end, start
                    for value in range(start, end + 1):
                        if 1 <= value <= total:
                            picked.add(value - 1)
            elif part.isdigit():
                value = int(part)
                if 1 <= value <= total:
                    picked.add(value - 1)
        return sorted(picked)

    def choose_categories_interactively(self, categories: List[CategoryRecord]) -> List[CategoryRecord]:
        print(f"[+] Βρέθηκαν κατηγορίες / ενότητες: {len(categories)}")
        for idx, cat in enumerate(categories, start=1):
            print(f"  {idx}. {cat.name} -> {cat.url} [{cat.source}]")
        default_count = int(self.config.get("default_category_count", 0) or 0)
        default_text = "0" if default_count == 0 else f"πρώτες {min(default_count, len(categories))}"
        while True:
            raw = input(f"Διάλεξε αριθμούς κατηγοριών (παραδείγματα: 1,4,7 ή 2-5, 0=όλες) [{default_text}]: ").strip()
            indexes = self.parse_category_selection_spec(raw, len(categories))
            if indexes:
                return [categories[i] for i in indexes]
            print("[!] Μη έγκυρη επιλογή. Χρησιμοποίησε αριθμούς όπως 1,4,7 ή εύρη όπως 2-5. Χρησιμοποίησε 0 για όλες.")

    def build_output_root(self) -> None:
        downloads = get_home_downloads_dir()
        store_folder = sanitize_name(self.store_name or self.netloc)
        self.output_root = ensure_dir(os.path.join(downloads, "Store Scrapper", store_folder))
        ensure_dir(self.output_root)
        self.status.set(store=store_folder)
        print(f"[+] Αποθήκευση στο: {self.output_root}")

    # ---------------------------- product extraction ---------------------------

    def scrape_category(self, category: CategoryRecord) -> int:
        with self.stats_lock:
            saved_before = int(self.stats.get("saved_products", 0))
        self.status.set(phase="scrape-category", category=category.name, page=0)
        category_dir = ensure_dir(os.path.join(self.output_root, slugify(category.name)))
        category_state_path = os.path.join(category_dir, "_category_state.json")
        self.begin_category_stream(category, category_dir)
        try:
            # Strategy 1: platform-specific APIs
            if "shopify" in self.platform:
                self.shopify_products_from_category(category, category_dir)
            if "woocommerce" in self.platform:
                self.woocommerce_products_from_category(category, category_dir)

            # Strategy 2: crawl listing pages + seeds
            self.generic_products_from_category(category, category_dir)

            category_products = list(self._active_category_products)
            json_dump(
                {
                    "category": asdict(category),
                    "discovered_products": [asdict(p) for p in category_products],
                    "timestamp": now_ts(),
                },
                category_state_path,
            )
            self.status.set(products_found=int(self.stats.get("discovered_products", 0)))
            self.finish_category_stream()
        finally:
            self.reset_category_stream()

        with self.stats_lock:
            return int(self.stats.get("saved_products", 0)) - saved_before

    def begin_category_stream(self, category: CategoryRecord, category_dir: str) -> None:
        self._active_category_dir = category_dir
        self._active_category_name = category.name
        self._active_category_products = []
        self._active_category_seen_keys = set()
        self._active_category_detail_futures = []
        self._active_category_task_index = 0
        workers = max(1, int(self.config.get("product_workers", DEFAULT_PRODUCT_WORKERS)))
        self._active_category_detail_executor = ThreadPoolExecutor(max_workers=workers)

    def category_stream_limit_reached(self) -> bool:
        wanted = int(self.config.get("max_products_per_category", 0) or 0)
        return wanted > 0 and len(self._active_category_products) >= wanted

    def capture_found_product(self, product: ProductRecord) -> bool:
        category_dir = self._active_category_dir
        if not category_dir or STOPPER.stop:
            return False
        key = canonicalize_url(product.url) if product.url else clean_text(product.name).lower()
        if not key:
            return False
        with self.state_lock:
            if key in self.saved_product_keys:
                self.bump_stat("skipped_duplicates", 1)
                return False
        task_index = 0
        with self.discovery_lock:
            if key in self._active_category_seen_keys:
                return False
            if self.category_stream_limit_reached():
                return False
            self._active_category_seen_keys.add(key)
            self._active_category_products.append(product)
            self._active_category_task_index += 1
            task_index = self._active_category_task_index
        self.record_discovered_product(product, category_dir)
        executor = self._active_category_detail_executor
        if executor is not None:
            self._active_category_detail_futures.append(
                executor.submit(self._process_product_worker, product, task_index, category_dir)
            )
        return True

    def finish_category_stream(self) -> None:
        executor = self._active_category_detail_executor
        futures = list(self._active_category_detail_futures)
        if executor is None:
            return
        try:
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception:
                    self.bump_stat("errors", 1)
                    self.status.inc("errors", 1)
        finally:
            executor.shutdown(wait=True, cancel_futures=False)
            self._active_category_detail_executor = None
            self._active_category_detail_futures = []

    def reset_category_stream(self) -> None:
        executor = self._active_category_detail_executor
        if executor is not None:
            executor.shutdown(wait=False, cancel_futures=False)
        self._active_category_dir = ""
        self._active_category_name = ""
        self._active_category_products = []
        self._active_category_seen_keys = set()
        self._active_category_detail_futures = []
        self._active_category_detail_executor = None
        self._active_category_task_index = 0

    def _process_product_worker(self, product: ProductRecord, idx: int, category_dir: str) -> None:
        if STOPPER.stop:
            return
        self.status.set(phase="scrape-product", page=idx, last_item=product.name, current_url=product.url)
        try:
            detailed = self.scrape_product_detail(product)
            to_save = detailed if self.is_valid_product_record(detailed) else product
            self.save_product(to_save)
        except Exception:
            self.bump_stat("errors", 1)
            self.status.inc("errors", 1)
            err_path = os.path.join(category_dir, f"_error_{idx}.txt")
            write_text(err_path, traceback.format_exc())
            try:
                self.save_product(product)
            except Exception:
                pass


    def shopify_products_from_category(self, category: CategoryRecord, category_dir: str) -> List[ProductRecord]:
        products: List[ProductRecord] = []
        base = category.url.rstrip("/")
        pages = self.config["max_pages_per_category"]
        for page in range(1, pages + 1):
            if STOPPER.stop or self.category_stream_limit_reached():
                break
            api_url = f"{base}/products.json?limit=250&page={page}"
            self.status.set(phase="shopify-api", category=category.name, page=page, current_url=api_url)
            data = self.fetch_json(api_url, referer=category.url)
            if not isinstance(data, dict):
                break
            items = data.get("products") or []
            if not items:
                break
            for item in items:
                title = pick_first(item.get("title"), item.get("handle"), "Προϊόν Χωρίς Όνομα")
                handle = item.get("handle") or "product"
                product_url = urljoin(self.root_url, f"/products/{handle}")
                images = []
                for img in item.get("images") or []:
                    src = img.get("src") if isinstance(img, dict) else img
                    if src:
                        images.append(src)
                description = clean_text(item.get("body_html"))
                price_text = ""
                price = ""
                currency = ""
                variants = item.get("variants") or []
                if variants:
                    first_variant = variants[0] if isinstance(variants[0], dict) else {}
                    price = clean_text(first_variant.get("price"))
                    price_text = price
                    currency = clean_text(first_variant.get("currency"))
                product = ProductRecord(
                    name=title,
                    url=canonicalize_url(product_url),
                    category=category.name,
                    description=description,
                    price=price,
                    price_text=price_text,
                    currency=currency,
                    images=unique_keep_order(images),
                    brand=pick_first(item.get("vendor")),
                    sku=pick_first((variants[0] or {}).get("sku") if variants and isinstance(variants[0], dict) else ""),
                    source="shopify-api",
                    extra={"raw": item},
                )
                products.append(product)
                self.capture_found_product(product)
                if self.category_stream_limit_reached():
                    break
        return products

    def woocommerce_products_from_category(self, category: CategoryRecord, category_dir: str) -> List[ProductRecord]:
        products: List[ProductRecord] = []
        category_id = category.meta.get("id") if isinstance(category.meta, dict) else None
        pages = self.config["max_pages_per_category"]
        per_page = 100
        for page in range(1, pages + 1):
            if STOPPER.stop or self.category_stream_limit_reached():
                break
            if category_id:
                api_url = urljoin(self.root_url, f"/wp-json/wc/store/v1/products?category={category_id}&page={page}&per_page={per_page}")
            else:
                api_url = urljoin(self.root_url, f"/wp-json/wc/store/v1/products?page={page}&per_page={per_page}")
            self.status.set(phase="woocommerce-api", category=category.name, page=page, current_url=api_url)
            data = self.fetch_json(api_url, referer=category.url)
            if not isinstance(data, list) or not data:
                break
            for item in data:
                images = [img.get("src") for img in item.get("images", []) if isinstance(img, dict) and img.get("src")]
                permalink = pick_first(item.get("permalink"), item.get("slug"))
                if permalink and not permalink.startswith("http"):
                    permalink = urljoin(self.root_url, "/product/" + permalink.strip("/"))
                price_text = pick_first(item.get("prices", {}).get("price"), item.get("price_html"), item.get("price"))
                price, currency = parse_price_and_currency(price_text)
                product = ProductRecord(
                    name=pick_first(item.get("name"), item.get("slug"), "Προϊόν Χωρίς Όνομα"),
                    url=canonicalize_url(permalink or category.url),
                    category=category.name,
                    description=clean_text(item.get("short_description") or item.get("description")),
                    price=price,
                    price_text=clean_text(price_text),
                    currency=currency or clean_text(item.get("prices", {}).get("currency_code")),
                    images=unique_keep_order([u for u in images if u]),
                    brand=pick_first(item.get("brands"), item.get("brand")),
                    sku=pick_first(item.get("sku")),
                    source="woocommerce-api",
                    extra={"raw": item},
                )
                products.append(product)
                self.capture_found_product(product)
                if self.category_stream_limit_reached():
                    break
        return products

    def generic_products_from_category(self, category: CategoryRecord, category_dir: str) -> List[ProductRecord]:
        found: List[ProductRecord] = []
        seeded_products = self.seed_products_for_category(category)
        for product in seeded_products:
            found.append(product)
            self.capture_found_product(product)
            if self.category_stream_limit_reached():
                return found
        pages_done = 0
        queue_pages = [category.url]
        seen_pages: Set[str] = set()
        while queue_pages and pages_done < self.config["max_pages_per_category"] and not STOPPER.stop and not self.category_stream_limit_reached():
            page_url = canonicalize_url(queue_pages.pop(0))
            if page_url in seen_pages:
                continue
            seen_pages.add(page_url)
            pages_done += 1
            self.status.set(phase="generic-listing", category=category.name, page=pages_done, current_url=page_url)
            html_text = self.fetch_text(page_url, referer=category.url)
            if not html_text:
                continue
            self.detect_platforms(html_text)
            extracted_products = self.extract_products_from_listing_html(html_text, page_url, category.name)
            for product in extracted_products:
                found.append(product)
                self.capture_found_product(product)
                if self.category_stream_limit_reached():
                    return found
            queue_pages.extend(self.extract_pagination_links(html_text, page_url))
            # Also scan page for product links that cards may have missed
            for url, text in self.extract_links(html_text, page_url):
                if is_likely_product_url(url):
                    product = ProductRecord(
                        name=sanitize_name(text or pathlib.Path(urlparse(url).path).name or "Product"),
                        url=url,
                        category=category.name,
                        source="listing-link",
                    )
                    found.append(product)
                    self.capture_found_product(product)
                    if self.category_stream_limit_reached():
                        return found
            for raw_url in self.extract_embedded_candidate_urls(html_text, page_url):
                if raw_url in seen_pages:
                    continue
                if is_likely_product_url(raw_url):
                    product = ProductRecord(
                        name=sanitize_name(pathlib.Path(urlparse(raw_url).path).name or "Προϊόν"),
                        url=raw_url,
                        category=category.name,
                        source="embedded-url",
                    )
                    found.append(product)
                    self.capture_found_product(product)
                    if self.category_stream_limit_reached():
                        return found
                elif is_likely_category_url(raw_url) and len(queue_pages) < self.config["max_pages_per_category"] * 4:
                    queue_pages.append(raw_url)
        return found

    def extract_pagination_links(self, html_text: str, base_url: str) -> List[str]:
        soup = self.soup(html_text)
        links: List[str] = []
        for selector in [
            "a[rel='next']",
            "link[rel='next']",
            "a.next",
            "a.pagination-next",
            "a[aria-label*='Next']",
        ]:
            for tag in soup.select(selector):
                href = tag.get("href")
                if href:
                    links.append(canonicalize_url(urljoin(base_url, href)))
        for a in soup.find_all("a", href=True):
            text = clean_text(a.get_text(" ", strip=True)).lower()
            if text in {"next", "next page", ">", ">>", "›", "»"}:
                links.append(canonicalize_url(urljoin(base_url, a.get("href"))))
        return unique_keep_order([u for u in links if same_domain(self.root_url, u)])

    def extract_products_from_listing_html(self, html_text: str, base_url: str, category_name: str) -> List[ProductRecord]:
        soup = self.soup(html_text)
        found: List[ProductRecord] = []

        # Strategy A: JSON-LD ItemList/Product
        for script in soup.find_all("script", attrs={"type": re.compile(r"application/ld\+json", re.I)}):
            objs = safe_json_from_script(script.get_text("\n", strip=False))
            for obj in objs:
                for product in self.products_from_ld_json(obj, base_url, category_name):
                    found.append(product)

        # Strategy B: embedded JSON
        for script in soup.find_all("script"):
            text = script.get_text("\n", strip=False)
            if not text or len(text) < 20:
                continue
            for obj in safe_json_from_script(text):
                for product in self.products_from_embedded_json(obj, base_url, category_name):
                    found.append(product)

        # Strategy C: HTML cards
        card_selectors = [
            "article",
            "li",
            ".product",
            ".product-card",
            ".product-item",
            ".grid-product",
            ".card",
            "[data-product-id]",
            "[data-testid*='product']",
        ]
        candidates = []
        for selector in card_selectors:
            candidates.extend(soup.select(selector))
        candidates = unique_keep_order(candidates)[:500]

        for card in candidates:
            href = ""
            a = card.find("a", href=True)
            if a:
                href = canonicalize_url(urljoin(base_url, a.get("href")))
            if not href or not same_domain(self.root_url, href):
                continue
            if any(bad in href.lower() for bad in BAD_LINK_WORDS):
                continue
            name = ""
            for selector in [
                "[itemprop='name']",
                ".product-title",
                ".card__heading",
                "h1", "h2", "h3", "h4",
                "a[title]",
            ]:
                node = card.select_one(selector)
                if node:
                    name = clean_text(node.get("title") or node.get_text(" ", strip=True))
                    if name:
                        break
            if not name and a:
                name = clean_text(a.get("title") or a.get_text(" ", strip=True))
            text = clean_text(card.get_text(" ", strip=True))
            price_match = PRICE_RE.search(text)
            price_text = price_match.group(0) if price_match else ""
            price, currency = parse_price_and_currency(price_text)
            img = card.find("img")
            image_url = ""
            if img:
                image_url = pick_first(img.get("src"), img.get("data-src"), img.get("data-lazy"), img.get("data-original"))
                if image_url:
                    image_url = canonicalize_url(urljoin(base_url, image_url))
            found.append(ProductRecord(
                name=sanitize_name(name or pathlib.Path(urlparse(href).path).name or "Product"),
                url=href,
                category=category_name,
                description="",
                price=price,
                price_text=price_text,
                currency=currency,
                images=[image_url] if image_url else [],
                source="html-card",
            ))

        return unique_keep_order(found)

    def products_from_ld_json(self, obj: Any, base_url: str, category_name: str) -> List[ProductRecord]:
        out: List[ProductRecord] = []
        nodes = obj if isinstance(obj, list) else [obj]
        for node in nodes:
            if not isinstance(node, dict):
                continue
            type_name = clean_text(node.get("@type") or node.get("type")).lower()
            if type_name == "itemlist":
                elements = node.get("itemListElement") or []
                for item in elements:
                    if isinstance(item, dict):
                        inner = item.get("item") if isinstance(item.get("item"), dict) else item
                        out.extend(self.products_from_ld_json(inner, base_url, category_name))
            elif type_name == "product":
                url = pick_first(node.get("url"), base_url)
                name = pick_first(node.get("name"), node.get("title"), pathlib.Path(urlparse(url).path).name)
                images = node.get("image") or []
                if isinstance(images, str):
                    images = [images]
                offers = node.get("offers") or {}
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}
                price_text = pick_first(offers.get("price"), offers.get("priceSpecification", {}).get("price"))
                price, currency = parse_price_and_currency(price_text)
                currency = currency or pick_first(offers.get("priceCurrency"))
                out.append(ProductRecord(
                    name=sanitize_name(name or "Προϊόν"),
                    url=canonicalize_url(urljoin(base_url, url)),
                    category=category_name,
                    description=clean_text(node.get("description")),
                    price=price,
                    price_text=clean_text(price_text),
                    currency=currency,
                    images=[canonicalize_url(urljoin(base_url, u)) for u in images if u],
                    brand=pick_first((node.get("brand") or {}).get("name") if isinstance(node.get("brand"), dict) else node.get("brand")),
                    sku=pick_first(node.get("sku"), node.get("mpn")),
                    source="json-ld",
                    extra={"raw": node},
                ))
        return out

    def products_from_embedded_json(self, obj: Any, base_url: str, category_name: str) -> List[ProductRecord]:
        out: List[ProductRecord] = []
        for item in recursive_find_productish(obj, limit=40):
            name = pick_first(item.get("name"), item.get("title"), item.get("product_name"), item.get("handle"))
            url = pick_first(item.get("url"), item.get("permalink"), item.get("href"), item.get("handle"))
            if url and not url.startswith("http"):
                if not str(url).startswith("/") and "handle" in item:
                    url = "/products/" + str(url).strip("/")
                url = urljoin(base_url, str(url))
            elif not url:
                continue
            price_text = pick_first(
                item.get("price"),
                item.get("formatted_price"),
                item.get("sale_price"),
                item.get("amount"),
            )
            price, currency = parse_price_and_currency(price_text)
            images = item.get("images") or item.get("image") or item.get("thumbnail") or []
            if isinstance(images, str):
                images = [images]
            if isinstance(images, dict):
                images = [images.get("src") or images.get("url")]
            clean_images = []
            for img in images:
                if isinstance(img, dict):
                    img = img.get("src") or img.get("url")
                if img:
                    clean_images.append(canonicalize_url(urljoin(base_url, str(img))))
            out.append(ProductRecord(
                name=sanitize_name(name or pathlib.Path(urlparse(url).path).name or "Product"),
                url=canonicalize_url(url),
                category=category_name,
                description=clean_text(item.get("description") or item.get("short_description")),
                price=price,
                price_text=clean_text(price_text),
                currency=currency or pick_first(item.get("currency"), item.get("currency_code")),
                images=unique_keep_order([u for u in clean_images if u]),
                brand=pick_first(item.get("brand"), (item.get("vendor") or {}).get("name") if isinstance(item.get("vendor"), dict) else item.get("vendor")),
                sku=pick_first(item.get("sku"), item.get("id"), item.get("product_id")),
                source="embedded-json",
                extra={"raw": item},
            ))
        return unique_keep_order(out)

    def scrape_product_detail(self, product: ProductRecord) -> ProductRecord:
        key = canonicalize_url(product.url or product.name)
        with self.state_lock:
            if key in self.saved_product_keys:
                self.bump_stat("skipped_duplicates", 1)
                return product
        html_text = self.fetch_text(product.url, referer=self.root_url)
        if not html_text:
            return product
        self.detect_platforms(html_text)
        soup = self.soup(html_text)
        body_text = clean_text(soup.get_text(" ", strip=True))

        page_name = pick_first(
            self.get_meta(soup, "og:title", "twitter:title"),
            self.page_title(soup),
            clean_text((soup.find("h1") or {}).get_text(" ", strip=True) if soup.find("h1") else ""),
        )
        name = pick_first(page_name, product.name)
        description = pick_first(
            self.get_meta(soup, "og:description", "description", "twitter:description"),
            clean_text((soup.select_one("[itemprop='description']") or {}).get_text(" ", strip=True) if soup.select_one("[itemprop='description']") else ""),
            clean_text((soup.select_one(".product-description, .product__description, .description") or {}).get_text(" ", strip=True) if soup.select_one(".product-description, .product__description, .description") else ""),
            product.description,
        )

        price_text = pick_first(
            self.get_meta(soup, "product:price:amount"),
            clean_text((soup.select_one("[itemprop='price']") or {}).get_text(" ", strip=True) if soup.select_one("[itemprop='price']") else ""),
            product.price_text,
        )
        if not price_text:
            m = PRICE_RE.search(body_text)
            price_text = m.group(0) if m else ""
        price, currency = parse_price_and_currency(price_text)
        currency = pick_first(self.get_meta(soup, "product:price:currency"), product.currency, currency)

        images = []
        images.extend(product.images)
        images.extend(self.extract_images_from_product_page(soup, product.url))

        brand = pick_first(
            self.get_meta(soup, "product:brand"),
            clean_text((soup.select_one("[itemprop='brand']") or {}).get_text(" ", strip=True) if soup.select_one("[itemprop='brand']") else ""),
            product.brand,
        )
        sku = pick_first(
            self.get_meta(soup, "product:retailer_item_id"),
            clean_text((soup.select_one("[itemprop='sku']") or {}).get_text(" ", strip=True) if soup.select_one("[itemprop='sku']") else ""),
            product.sku,
        )
        category = pick_first(self.extract_category_from_breadcrumbs(soup), product.category, "Uncategorized")

        detail_signals = {
            "jsonld_product": False,
            "jsonld_itemlist": False,
            "has_add_to_cart": any(word in body_text.lower() for word in ["add to bag", "add to cart", "buy now", "choose size", "select size"]),
        }

        extra = dict(product.extra)
        extra["og"] = {
            "title": self.get_meta(soup, "og:title"),
            "description": self.get_meta(soup, "og:description"),
            "image": self.get_meta(soup, "og:image"),
        }

        for script in soup.find_all("script", attrs={"type": re.compile(r"application/ld\+json", re.I)}):
            payload = script.get_text("\n", strip=False)
            if payload:
                if '"@type":"Product"' in payload or '"@type": "Product"' in payload:
                    detail_signals["jsonld_product"] = True
                if '"@type":"ItemList"' in payload or '"@type": "ItemList"' in payload:
                    detail_signals["jsonld_itemlist"] = True
            for obj in safe_json_from_script(payload):
                for p in self.products_from_ld_json(obj, product.url, category):
                    if canonicalize_url(p.url) == canonicalize_url(product.url) or (p.name and p.name.lower() == (name or "").lower()):
                        name = pick_first(p.name, name)
                        description = pick_first(p.description, description)
                        price_text = pick_first(p.price_text, price_text)
                        price = pick_first(p.price, price)
                        currency = pick_first(p.currency, currency)
                        brand = pick_first(p.brand, brand)
                        sku = pick_first(p.sku, sku)
                        images.extend(p.images)

        for script in soup.find_all("script"):
            payload = script.get_text("\n", strip=False)
            if not payload or len(payload) < 20:
                continue
            for obj in safe_json_from_script(payload):
                for p in self.products_from_embedded_json(obj, product.url, category):
                    if canonicalize_url(p.url) == canonicalize_url(product.url) or (p.name and p.name.lower() == (name or "").lower()):
                        name = pick_first(p.name, name)
                        description = pick_first(p.description, description)
                        price_text = pick_first(p.price_text, price_text)
                        price = pick_first(p.price, price)
                        currency = pick_first(p.currency, currency)
                        brand = pick_first(p.brand, brand)
                        sku = pick_first(p.sku, sku)
                        images.extend(p.images)

        images = rank_image_urls(images)
        extra["detail_signals"] = detail_signals

        return ProductRecord(
            name=sanitize_name(name or product.name or "Product"),
            url=canonicalize_url(product.url),
            category=sanitize_name(category or "Uncategorized"),
            description=description,
            price=price,
            price_text=price_text,
            currency=currency,
            images=images,
            brand=brand,
            sku=sku,
            source=product.source,
            extra=extra,
        )

    def is_valid_product_record(self, product: ProductRecord) -> bool:
        name = clean_text(product.name).lower()
        url = canonicalize_url(product.url).lower()
        description = clean_text(product.description).lower()
        signals = product.extra.get("detail_signals", {}) if isinstance(product.extra, dict) else {}
        score = 0
        if is_likely_product_url(url):
            score += 8
        if product.price or product.price_text:
            score += 6
        if product.sku:
            score += 4
        if product.images:
            score += 2
        if signals.get("jsonld_product"):
            score += 8
        if signals.get("has_add_to_cart"):
            score += 3
        if looks_like_bad_category_name(name) or looks_like_bad_category_url(url):
            score -= 20
        if any(word in name for word in ["find a store", "join us", "membership", "guide", "lookbook", "βρες ένα κατάστημα", "έλα μαζί μας", "οδηγός"]):
            score -= 20
        if description and any(word in description for word in ["join the", "find your nearest", "store locator", "member benefits"]):
            score -= 10
        if not product.price and not product.price_text and not signals.get("jsonld_product") and not is_likely_product_url(url):
            score -= 6
        return score >= 6

    def extract_images_from_product_page(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        urls: List[str] = []
        meta_image = self.get_meta(soup, "og:image", "twitter:image")
        if meta_image:
            urls.append(canonicalize_url(urljoin(base_url, meta_image)))
        for img in soup.find_all("img"):
            for attr in ["src", "data-src", "data-lazy", "data-original", "data-zoom-image", "data-large_image"]:
                value = img.get(attr)
                if value:
                    urls.append(canonicalize_url(urljoin(base_url, value)))
            srcset = img.get("srcset") or img.get("data-srcset")
            if srcset:
                for part in srcset.split(","):
                    raw = part.strip().split(" ")[0]
                    if raw:
                        urls.append(canonicalize_url(urljoin(base_url, raw)))
        cleaned = []
        for u in urls:
            lower = u.lower()
            if any(word in lower for word in ["logo", "icon", "favicon", "sprite", "placeholder"]):
                continue
            if not same_domain(self.root_url, u):
                cleaned.append(u)
            elif any(x in lower for x in ["product", "products", "item", "catalog", "image", "images", "pdp"]):
                cleaned.append(u)
            elif looks_like_image(u):
                cleaned.append(u)
        return rank_image_urls(cleaned)

    def extract_category_from_breadcrumbs(self, soup: BeautifulSoup) -> str:
        for selector in [
            ".breadcrumb a",
            "nav[aria-label*='breadcrumb'] a",
            "[typeof='BreadcrumbList'] a",
        ]:
            names = [clean_text(a.get_text(" ", strip=True)) for a in soup.select(selector) if clean_text(a.get_text(" ", strip=True))]
            if len(names) >= 2:
                return sanitize_name(names[-2])
        return ""

    # --------------------------------- saving ---------------------------------

    def product_dir(self, product: ProductRecord) -> str:
        category_folder = ensure_dir(os.path.join(self.output_root, slugify(product.category or "Χωρίς Κατηγορία")))
        product_folder = ensure_dir(os.path.join(category_folder, slugify(product.name or "Προϊόν")))
        return product_folder

    def download_image(self, url: str, folder: str, index: int) -> Optional[str]:
        if not url:
            return None
        try:
            headers = {"Referer": self.root_url}
            last_error = None
            for attempt in range(1, max(2, int(self.config.get("retries", 2))) + 1):
                try:
                    resp = self._get_session().get(
                        canonicalize_url(url),
                        timeout=self.request_timeout(attempt, "image"),
                        allow_redirects=True,
                        headers=headers,
                    )
                    if resp is None or resp.status_code >= 400:
                        last_error = None
                        if attempt >= max(2, int(self.config.get("retries", 2))):
                            return None
                        continue
                    break
                except Exception as exc:
                    last_error = exc
                    if attempt >= max(2, int(self.config.get("retries", 2))):
                        raise
            if resp is None or resp.status_code >= 400:
                return None
            ext = ext_from_url(url, default=".jpg")
            path = os.path.join(folder, f"image_{index:03d}{ext}")
            with open(path, "wb") as f:
                f.write(resp.content)
            self.bump_stat("downloaded_images", 1)
            return path
        except Exception:
            self.bump_stat("errors", 1)
            self.status.inc("errors", 1)
            return None

    def record_discovered_product(self, product: ProductRecord, category_dir: str) -> None:
        key = canonicalize_url(product.url or product.name)
        if not key:
            return
        with self.discovery_lock:
            if key in self.recorded_discovery_keys:
                return
            self.recorded_discovery_keys.add(key)

            product_folder = self.product_dir(product)
            discovered_at = now_ts()
            discovery_metadata = asdict(product)
            discovery_metadata["discovered_at"] = discovered_at
            discovery_metadata["store"] = self.store_name
            discovery_metadata["output_folder"] = product_folder
            json_dump_sync(discovery_metadata, os.path.join(product_folder, "_discovered.json"))
            write_text_sync(
                os.path.join(product_folder, "FOUND.txt"),
                f"Εντοπίστηκε: {discovered_at}\nΌνομα: {product.name}\nURL: {product.url}\nΚατηγορία: {product.category}\nΠηγή: {product.source}\nΤιμή: {product.price_text or product.price}\n",
            )
            append_text_sync(
                os.path.join(category_dir, "_discovered_products.jsonl"),
                json.dumps(
                    {
                        "discovered_at": discovered_at,
                        "name": product.name,
                        "url": product.url,
                        "category": product.category,
                        "price": product.price,
                        "price_text": product.price_text,
                        "currency": product.currency,
                        "source": product.source,
                    },
                    ensure_ascii=False,
                ) + "\n",
            )
            append_text_sync(
                os.path.join(category_dir, "_discovered_products.txt"),
                f"[{discovered_at}] {product.name} | {product.url} | {product.price_text or product.price}\n",
            )

        self.bump_stat("discovered_products", 1)
        self.status.inc("products_found", 1)
        self.status.set(last_item=product.name)
        self.save_global_state(force=True)

    def save_product(self, product: ProductRecord) -> None:
        key = canonicalize_url(product.url or product.name)
        with self.state_lock:
            if key in self.saved_product_keys:
                self.bump_stat("skipped_duplicates", 1)
                return
            self.saved_product_keys.add(key)

        try:
            folder = self.product_dir(product)
            images_dir = ensure_dir(os.path.join(folder, "images"))

            metadata = asdict(product)
            metadata["saved_at"] = now_ts()
            metadata["store"] = self.store_name
            metadata["output_folder"] = folder
            json_dump_sync(metadata, os.path.join(folder, "metadata.json"))

            summary = []
            summary.append(f"Όνομα: {product.name}")
            summary.append(f"URL: {product.url}")
            summary.append(f"Κατηγορία: {product.category}")
            summary.append(f"Τιμή: {product.price_text or product.price}")
            summary.append(f"Νόμισμα: {product.currency}")
            summary.append(f"Μάρκα: {product.brand}")
            summary.append(f"SKU: {product.sku}")
            summary.append("")
            summary.append("Περιγραφή:")
            summary.append(product.description or "")
            write_text_sync(os.path.join(folder, "summary.txt"), "\n".join(summary).strip() + "\n")
            write_text_sync(os.path.join(folder, "description.txt"), (product.description or "") + "\n")

            max_images = self.config["max_images_per_product"]
            image_urls = unique_keep_order(product.images)
            if max_images > 0:
                image_urls = image_urls[:max_images]
            downloaded = []
            image_workers = max(1, min(int(self.config.get("image_workers", DEFAULT_IMAGE_WORKERS)), len(image_urls) or 1))
            if image_workers == 1:
                for i, img_url in enumerate(image_urls, start=1):
                    self.status.set(phase="save-image", last_item=product.name, current_url=img_url)
                    saved_path = self.download_image(img_url, images_dir, i)
                    if saved_path:
                        downloaded.append(saved_path)
            else:
                with ThreadPoolExecutor(max_workers=image_workers) as executor:
                    futures = {
                        executor.submit(self.download_image, img_url, images_dir, i): i
                        for i, img_url in enumerate(image_urls, start=1)
                    }
                    image_results: Dict[int, str] = {}
                    for future in as_completed(futures):
                        idx = futures[future]
                        try:
                            saved_path = future.result()
                        except Exception:
                            saved_path = None
                        if saved_path:
                            image_results[idx] = saved_path
                    downloaded = [image_results[i] for i in sorted(image_results)]

            json_dump_sync(
                {
                    "downloaded_images": downloaded,
                    "source_image_urls": image_urls,
                    "saved_at": now_ts(),
                },
                os.path.join(folder, "images.json"),
            )

            self.bump_stat("saved_products", 1)
            self.status.inc("saved", 1)
            self.status.set(last_item=product.name)
            self.save_global_state(force=True)
            print(f"[+] Αποθηκεύτηκε το προϊόν: {product.name}")
        except Exception:
            with self.state_lock:
                self.saved_product_keys.discard(key)
            self.bump_stat("errors", 1)
            self.status.inc("errors", 1)
            raise

    def save_global_state(self, force: bool = False) -> None:
        if not self.output_root:
            return
        interval = float(self.config.get("state_save_interval", DEFAULT_STATE_SAVE_INTERVAL))
        if not force and interval > 0 and (time.time() - self.last_state_save) < interval:
            return
        with self.state_lock:
            if not force and interval > 0 and (time.time() - self.last_state_save) < interval:
                return
            snapshot = {
                "store_name": self.store_name,
                "base_url": self.base_url,
                "platform": sorted(self.platform),
                "stats": dict(self.stats),
                "notes": list(self.discovery_notes),
                "timestamp": now_ts(),
            }
            json_dump_sync(snapshot, os.path.join(self.output_root, "_run_state.json"))
            self.last_state_save = time.time()

    # --------------------------------- run ------------------------------------

    def prepare_store_identity(self) -> None:
        self.status.set(phase="prepare", current_url=self.base_url)
        first_page = self.fetch_text(self.base_url, referer=self.root_url, accept_json=False)
        if first_page:
            self.detect_platforms(first_page)
            soup = self.soup(first_page)
            detected = self.extract_site_name(soup)
            if detected:
                self.store_name = detected
                self.status.set(store=self.store_name)
        if (not self.store_name or self.store_name == self.netloc) and self.base_url != self.root_url:
            home_page = self.fetch_text(self.root_url, referer=self.base_url, accept_json=False)
            if home_page:
                self.detect_platforms(home_page)
                soup = self.soup(home_page)
                detected = self.extract_site_name(soup)
                if detected:
                    self.store_name = detected
                    self.status.set(store=self.store_name)

    def auto_select_categories(self, categories: List[CategoryRecord]) -> List[CategoryRecord]:
        if self.input_mode == "category":
            return [CategoryRecord(name=self.category_candidate_name("", self.base_url), url=self.base_url, source="input-url")]
        if not categories:
            return [CategoryRecord(name="Όλα τα Προϊόντα", url=self.base_url, source="fallback-home")]
        default_count = int(self.config.get("default_category_count", 0) or 0)
        if default_count <= 0 or default_count >= len(categories):
            return list(categories)
        return list(categories[:default_count])

    def run(self) -> None:
        try:
            self.status.set(phase="start", current_url=self.base_url)
            self.prepare_store_identity()
            self.build_output_root()
            self.save_global_state(force=True)

            print(f"[+] Εντοπίστηκε κατάστημα: {self.store_name}")
            print(f"[+] Πλατφόρμες: {greek_platforms(self.platform)}")
            print(f"[+] Τρόπος εισόδου: {greek_input_mode(self.input_mode)}")

            if self.input_mode == "product":
                product = ProductRecord(
                    name=sanitize_name(pathlib.Path(urlparse(self.base_url).path).name or "Προϊόν"),
                    url=self.base_url,
                    category="Άμεσο Προϊόν",
                    source="input-url",
                )
                self.record_discovered_product(product, ensure_dir(os.path.join(self.output_root, slugify(product.category))))
                self._process_product_worker(product, 1, ensure_dir(os.path.join(self.output_root, slugify(product.category))))
            else:
                if self.input_mode == "site":
                    self.discovered_categories = self.discover_categories()
                    print(f"[+] Βρέθηκαν κατηγορίες: {len(self.discovered_categories)}")
                else:
                    self.discovered_categories = [CategoryRecord(name=self.category_candidate_name("", self.base_url), url=self.base_url, source="input-url")]
                    self.status.set(categories_found=1)
                    print(f"[+] Άμεσος στόχος κατηγορίας: {self.base_url}")

                selected_categories = self.auto_select_categories(self.discovered_categories)
                if not selected_categories:
                    selected_categories = [CategoryRecord(name="Όλα τα Προϊόντα", url=self.base_url, source="fallback-home")]

                for idx, category in enumerate(selected_categories, start=1):
                    if STOPPER.stop:
                        break
                    print(f"\n[+] Σάρωση κατηγορίας {idx}/{len(selected_categories)}: {category.name}")
                    saved_count = self.scrape_category(category)
                    print(f"[+] Ολοκληρώθηκε η κατηγορία: {category.name} | αποθηκεύτηκαν {saved_count} προϊόντα")

            self.save_global_state(force=True)
            self.write_final_report()
        finally:
            self.status.set(phase="done")
            self.status.stop()

    def write_final_report(self) -> None:
        report = []
        report.append(f"Κατάστημα: {self.store_name}")
        report.append(f"Αρχικό URL: {self.base_url}")
        report.append(f"Πλατφόρμες: {greek_platforms(self.platform)}")
        report.append("")
        report.append("Στατιστικά:")
        for key, value in self.stats.items():
            report.append(f"- {greek_stat_key(key)}: {value}")
        report.append("")
        report.append("Σημειώσεις:")
        for note in self.discovery_notes:
            report.append(f"- {note}")
        write_text(os.path.join(self.output_root, "FINAL_REPORT.txt"), "\n".join(report) + "\n")


# ---------------------------------- cli/ui -----------------------------------

def show_banner() -> None:
    print("=" * 78)
    print(f"Store Scrapper για Termux | v{VERSION}")
    print("Scraper καταστημάτων σε ένα αρχείο με live αποθήκευση, live κατάσταση και πολλές εναλλακτικές μεθόδους")
    print("Enter = προεπιλογή σε κάθε prompt")
    print("=" * 78)


def show_help() -> None:
    print(
        """
Πώς δουλεύει:
- Διαβάζει την αρχική σελίδα του καταστήματος
- Εντοπίζει συνηθισμένες πλατφόρμες καταστημάτων (Shopify, WooCommerce, Next.js, Nuxt κτλ.)
- Δοκιμάζει sitemaps, μενού, links κατηγοριών, ενσωματωμένο JSON, JSON-LD, κρυφά URLs,
  platform APIs, σελίδες λίστας, κάρτες προϊόντων, pagination και σελίδες λεπτομερειών προϊόντων
- Χρησιμοποιεί threaded workers για επαλήθευση κατηγοριών, σελίδες λεπτομερειών προϊόντων και λήψη εικόνων
- Αποθηκεύει κάθε προϊόν αμέσως μόλις το εντοπίσει
- Γράφει προσωρινή εγγραφή εντοπισμού για κάθε προϊόν τη στιγμή που βρίσκεται
- Κατεβάζει τις εικόνες προϊόντων μέσα στον φάκελο κάθε προϊόντος

Δομή φακέλων:
~/storage/downloads/Store Scrapper/<Κατάστημα>/<Κατηγορία>/<Προϊόν>/
  metadata.json
  summary.txt
  description.txt
  images/
  images.json

Συμβουλές:
- Τώρα χρειάζεται μόνο να επικολλήσεις ένα link· το script επιλέγει μόνο του timeouts, workers και mode
- Αν δώσεις URL κατηγορίας, θα σαρώσει απευθείας αυτή την κατηγορία χωρίς να χάνει χρόνο σε ολόκληρο το site
- Αν δώσεις URL προϊόντος, θα αποθηκεύσει απευθείας αυτό το προϊόν
- Μερικά καταστήματα μπλοκάρουν bots· το script παρ' όλα αυτά δοκιμάζει πολλές εναλλακτικές μεθόδους
- Τα καλύτερα αποτελέσματα συνήθως έρχονται όταν ξεκινάς από την αρχική σελίδα του store ή από σελίδα κατηγορίας
        """.strip()
    )


def auto_build_config(url: str) -> Dict[str, Any]:
    cpu = max(2, int(os.cpu_count() or 4))
    mode = "product" if is_likely_product_url(url) else ("category" if is_likely_category_url(url) or len([p for p in strip_locale_parts(path_parts(url)) if p]) > 1 else "site")
    product_workers = min(24, max(6, cpu * 2))
    image_workers = min(10, max(2, cpu))
    category_verify_workers = min(12, max(4, cpu))
    default_category_count = 1 if mode == "category" else DEFAULT_MAX_CATEGORIES
    max_pages_per_category = 30 if mode == "category" else 12
    return {
        "timeout": DEFAULT_TIMEOUT,
        "connect_timeout": DEFAULT_CONNECT_TIMEOUT,
        "read_timeout": DEFAULT_READ_TIMEOUT,
        "timeout_step": DEFAULT_TIMEOUT_STEP,
        "retries": 3,
        "delay_min": 0.0,
        "delay_max": 0.03,
        "default_category_count": default_category_count,
        "max_products_per_category": 0,
        "max_pages_per_category": max_pages_per_category,
        "max_images_per_product": 8,
        "product_workers": product_workers,
        "image_workers": image_workers,
        "category_verify_workers": category_verify_workers,
        "max_total_urls": 3000,
        "max_sitemap_urls": 5000,
        "state_save_interval": 0.0,
    }


def main() -> None:
    while True:
        url = input("Σύνδεσμος: " ).strip()
        if url:
            break
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    config = auto_build_config(url)

    scraper = StoreScrapper(url, config)
    scraper.run()
    print(f"\n[+] Φάκελος εξόδου: {scraper.output_root}")


if __name__ == "__main__":
    main()
