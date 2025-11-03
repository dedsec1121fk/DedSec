#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import json
import curses
import time
import sqlite3
import re
import random
from datetime import datetime, timedelta
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Optional, Tuple, List
from contextlib import contextmanager

# Networking
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------------
# CONFIGURATION (ΡΥΘΜΙΣΕΙΣ)
# ---------------------------
DATA_FOLDER = "Digital Footprint Finder Files"
PLATFORMS_FILE_NAME = "Digital Footprint Finder Platforms.json"
OLD_DB_NAME = "footprint_history.db"
NEW_DB_NAME = "search_history.db"

# Termux-friendly results path; fallback if unavailable
# Διαδρομή αποθήκευσης αποτελεσμάτων
RESULTS_SAVE_FOLDER = os.path.join(os.path.expanduser('~'), 'storage', 'downloads', 'Digital Footprint Finder')
FALLBACK_RESULTS_FOLDER = os.path.join(os.path.expanduser('~'), 'Digital_Footprint_Results')

# Default network settings (Προεπιλεγμένες ρυθμίσεις δικτύου)
DEFAULT_TIMEOUT = 7  # Slightly increased timeout for proxies (Ελαφρώς αυξημένο timeout για proxies)
DEFAULT_RETRIES = 2
DEFAULT_BACKOFF = 1.5
CACHE_DURATION_HOURS = 24

# Stealth defaults (Απόκρυψη defaults - ΕΝΕΡΓΗ από προεπιλογή)
STEALTH_DEFAULT = True
STEALTH_MAX_WORKERS = 6
NONSTEALTH_MAX_WORKERS = 30

# Major platforms (Σημαντικές πλατφόρμες - προτεραιότητα)
MAJOR_PLATFORMS_KEYS = [
    "facebook", "twitter", "instagram", "tiktok", "linkedin",
    "pinterest", "snapchat", "telegram", "vk", "wechat",
    "threads", "bereal", "reddit", "quora", "medium",
    "github", "gitlab", "bitbucket", "stackoverflow", "youtube", "twitch"
]

# Platforms known to be ambiguous or non-functional (Πλατφόρμες γνωστές ως διφορούμενες/μη λειτουργικές)
AMBIGUOUS_PLATFORMS_TO_SKIP = [
    "wechat", "spotify"
]

# --- ADVANCED: User-Agent Rotation List ---
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/119.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
]

# ---------------------------
# Dependency auto-install (best-effort) (Αυτόματη εγκατάσταση εξαρτήσεων)
# ---------------------------
def install_dependencies():
    required = {"requests": "requests", "rich": "rich"}
    if os.name == 'nt':
        required["curses"] = "windows-curses"
    missing = []
    for mod, pkg in required.items():
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
    if not missing:
        return True
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        return True
    except Exception:
        # If rich is not available, simple print is fine
        print("Προειδοποίηση: Δεν ήταν δυνατή η αυτόματη εγκατάσταση των εξαρτήσεων:", missing, file=sys.stderr)
        return False
install_dependencies()

# Try to import rich for nicer console output (Εισαγωγή rich για καλύτερη έξοδο κονσόλας)
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TaskID
    console = Console()
    RICH_AVAILABLE = True
except Exception:
    console = None # type: ignore
    RICH_AVAILABLE = False
    # Dummy classes (Ψεύτικες κλάσεις για fallback)
    class Progress:
        def __init__(self, *args, **kwargs): pass
        def add_task(self, *args, **kwargs): return None
        def update(self, *args, **kwargs): pass
        def start(self): pass
        def stop(self): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
    class SpinnerColumn: pass
    class TextColumn: pass
    class BarColumn: pass
    class TimeElapsedColumn: pass
    class TaskID: pass


# ---------------------------
# Helpers: DB manager, results folder (Βοηθητικές: Διαχειριστής ΒΔ, φάκελος αποτελεσμάτων)
# ---------------------------
@contextmanager
def database_manager(db_path: str):
    conn = None
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # History table (Πίνακας ιστορικού)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY,
                username TEXT,
                timestamp TEXT
            )
        """)
        # Cache table (Πίνακας cache)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                id INTEGER PRIMARY KEY,
                username TEXT,
                platform_key TEXT,
                url TEXT,
                found INTEGER,
                timestamp TEXT,
                UNIQUE(username, platform_key)
            )
        """)
        conn.commit()
        yield conn, cursor
    finally:
        if conn:
            conn.close()

def ensure_results_folder():
    try:
        os.makedirs(RESULTS_SAVE_FOLDER, exist_ok=True)
        return RESULTS_SAVE_FOLDER
    except Exception:
        try:
            os.makedirs(FALLBACK_RESULTS_FOLDER, exist_ok=True)
            return FALLBACK_RESULTS_FOLDER
        except Exception:
            return os.getcwd()
RESULTS_SAVE_FOLDER = ensure_results_folder()

# ---------------------------
# Default minimal platform set (fallback) (Προεπιλεγμένο ελάχιστο σύνολο πλατφορμών)
# ---------------------------
DEFAULT_PLATFORMS = {
    "social_media": {
        "facebook": {
            "name": "Facebook",
            "method": "username_url",
            "url_check": "https://www.facebook.com/{identifier}",
            "error_type": "string",
            "not_found_text": ["page not found", "content isn't available"],
            "profile_markers": ["friends", "followers"]
        },
        "twitter": {
            "name": "Twitter/X",
            "method": "username_url",
            "url_check": "https://twitter.com/{identifier}",
            "error_type": "status_code"
        },
        "instagram": {
            "name": "Instagram",
            "method": "username_url",
            "url_check": "https://www.instagram.com/{identifier}",
            "error_type": "string",
            "not_found_text": ["sorry, this page isn't available"]
        },
        "github": {
            "name": "GitHub",
            "method": "username_url",
            "url_check": "https://github.com/{identifier}",
            "error_type": "status_code"
        }
    }
}

# ---------------------------
# Request session factory (with retries) (Εργοστάσιο περιόδου λειτουργίας αιτημάτων)
# ---------------------------
def make_requests_session(timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES, backoff=DEFAULT_BACKOFF, stealth=True):
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    
    # --- ADVANCED: Set base headers, but User-Agent will be rotated per-request ---
    if stealth:
        session.headers.update({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        })
    else:
        # Unchanged User-Agent (Μη αλλαγμένο User-Agent)
        session.headers.update({'User-Agent': f'DigitalFootprintFinder/1.1 (Advanced)'})
    
    setattr(session, 'request_timeout', timeout)
    return session

# ---------------------------
# Main unified class (Κύρια ενιαία κλάση)
# ---------------------------
class DigitalFootprintFinder:
    def __init__(self, stealth: bool = STEALTH_DEFAULT, keep_tui: bool = True, proxy_file: Optional[str] = None):
        self.stealth = stealth
        self.keep_tui = keep_tui
        self.data_folder = DATA_FOLDER
        self.db_path = os.path.join(DATA_FOLDER, NEW_DB_NAME)
        self.platforms_file = os.path.join(DATA_FOLDER, PLATFORMS_FILE_NAME)
        self.max_workers = STEALTH_MAX_WORKERS if stealth else NONSTEALTH_MAX_WORKERS
        self._initialize_file_structure()
        self.platforms = self._load_platforms()
        self.history = self._load_history()
        
        # --- ADVANCED: Load Proxies (Φόρτωση Proxies) ---
        self.proxies_list = self._load_proxies(proxy_file)
        if proxy_file and self.proxies_list and RICH_AVAILABLE:
            console.print(f"[green]Φορτώθηκαν {len(self.proxies_list)} proxies από το {proxy_file}[/green]")
        elif proxy_file and not self.proxies_list:
            if RICH_AVAILABLE:
                console.print(f"[red]Το αρχείο proxy {proxy_file} ήταν κενό ή δεν μπορούσε να διαβαστεί.[/red]")
        
        self.major_platform_keys = [k for k in MAJOR_PLATFORMS_KEYS if k in self.platforms]
        self.minor_platform_keys = [k for k in self.platforms.keys() if k not in self.major_platform_keys]
        self.session = make_requests_session(timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES, backoff=DEFAULT_BACKOFF, stealth=self.stealth)

    def _initialize_file_structure(self):
        os.makedirs(self.data_folder, exist_ok=True)
        try:
            db_target = os.path.join(self.data_folder, NEW_DB_NAME)
            if os.path.exists(OLD_DB_NAME) and not os.path.exists(db_target):
                os.rename(OLD_DB_NAME, db_target)
                if RICH_AVAILABLE:
                    console.print(f"[green]Μετακινήθηκε το παλιό DB '{OLD_DB_NAME}' -> '{db_target}'[/green]")
        except Exception:
            pass
        if not os.path.exists(self.platforms_file):
            try:
                with open(self.platforms_file, 'w', encoding='utf-8') as f:
                    json.dump(DEFAULT_PLATFORMS, f, indent=2)
                if RICH_AVAILABLE:
                    console.print(f"[yellow]Το Platforms JSON δεν βρέθηκε — δημιουργήθηκε προεπιλεγμένο στο {self.platforms_file}[/yellow]")
            except Exception as e:
                if RICH_AVAILABLE:
                    console.print(f"[red]Προειδοποίηση: Δεν ήταν δυνατή η δημιουργία του Platforms JSON: {e}[/red]")

    def _load_platforms(self) -> Dict[str, Any]:
        try:
            with open(self.platforms_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = DEFAULT_PLATFORMS
        
        all_platforms = {}
        skipped_platforms = []
        for category in data.values():
            for key, info in category.items():
                if key in AMBIGUOUS_PLATFORMS_TO_SKIP:
                    skipped_platforms.append(key)
                    continue
                info.setdefault('not_found_text', [])
                info.setdefault('profile_markers', [])
                all_platforms[key] = info
        
        if RICH_AVAILABLE and skipped_platforms:
            console.print(f"[yellow]Προειδοποίηση: Παραλείφθηκε η φόρτωση διφορούμενων πλατφορμών: {', '.join(skipped_platforms)}[/yellow]")
        
        if not all_platforms:
            fallback = {}
            for category in DEFAULT_PLATFORMS.values():
                fallback.update(category)
            return fallback

        return all_platforms

    def _load_proxies(self, proxy_file: Optional[str]) -> List[str]:
        if not proxy_file:
            return []
        try:
            with open(proxy_file, 'r') as f:
                # Read lines, strip whitespace, and filter out empty lines (Διαβάζει γραμμές, αφαιρεί κενά)
                proxies = [line.strip() for line in f if line.strip()]
                return proxies
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red]Σφάλμα φόρτωσης αρχείου proxy {proxy_file}: {e}[/red]")
            return []

    def _load_history(self):
        try:
            with database_manager(self.db_path) as (_, cursor):
                cursor.execute("SELECT id, username, timestamp FROM history ORDER BY id DESC")
                return cursor.fetchall()
        except Exception:
            return []

    def _save_to_history(self, username: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with database_manager(self.db_path) as (conn, cursor):
                cursor.execute("INSERT INTO history (username, timestamp) VALUES (?, ?)", (username, timestamp))
                conn.commit()
            self.history = self._load_history()
        except Exception:
            pass

    def _get_from_cache(self, username: str, platform_key: str) -> Optional[Tuple[str, str]]:
        try:
            with database_manager(self.db_path) as (_, cursor):
                cursor.execute(
                    "SELECT url, found, timestamp FROM cache WHERE username=? AND platform_key=?",
                    (username, platform_key)
                )
                result = cursor.fetchone()
                if result:
                    url, found, ts_str = result
                    ts = datetime.fromisoformat(ts_str)
                    # Check if cache is still valid (Ελέγχος εγκυρότητας cache)
                    if datetime.now() - ts < timedelta(hours=CACHE_DURATION_HOURS):
                        return (self.platforms[platform_key]['name'], url) if found else None
        except Exception:
            return None
        return None

    def _save_to_cache(self, username: str, platform_key: str, url: str, found: bool):
        timestamp = datetime.now().isoformat()
        try:
            with database_manager(self.db_path) as (conn, cursor):
                cursor.execute(
                    """INSERT INTO cache (username, platform_key, url, found, timestamp)
                       VALUES (?, ?, ?, ?, ?)
                       ON CONFLICT(username, platform_key) DO UPDATE SET
                       url=excluded.url, found=excluded.found, timestamp=excluded.timestamp""",
                    (username, platform_key, url, 1 if found else 0, timestamp)
                )
                conn.commit()
        except Exception:
            pass

    def _validate_username_structure(self, username: str) -> bool:
        validation_pattern = re.compile(r"^(?=.{1,90}$)[a-zA-Z0-9_.-]+$", re.UNICODE)
        return bool(validation_pattern.match(username))

    def fetch_url(self, url: str) -> Optional[requests.Response]:
        try:
            timeout = getattr(self.session, 'request_timeout', DEFAULT_TIMEOUT)
            
            # --- ADVANCED: Set request-specific headers and proxies (Ρύθμιση κεφαλίδων και proxies) ---
            headers = self.session.headers.copy()
            if self.stealth:
                headers['User-Agent'] = random.choice(USER_AGENTS)

            proxies = None
            if self.proxies_list:
                proxy_url = random.choice(self.proxies_list)
                # Ensure proxy_url has a scheme (Βεβαιωθείτε ότι το proxy_url έχει σχήμα)
                if not proxy_url.startswith(('http://', 'https://', 'socks5://')):
                    proxy_url = f"http://{proxy_url}"
                proxies = {
                    "http": proxy_url,
                    "https": proxy_url
                }

            return self.session.get(url, timeout=timeout, headers=headers, proxies=proxies)
        
        except requests.exceptions.ProxyError:
            if RICH_AVAILABLE:
                console.log(f"[red]Σφάλμα Proxy: Αποτυχία σύνδεσης στο proxy για {url}[/red]")
            return None
        except requests.exceptions.ReadTimeout:
            # This is common, don't flood console (Συνηθισμένο σφάλμα, μην γεμίζετε την κονσόλα)
            return None
        except Exception:
            # Catch other potential errors (Σύλληψη άλλων πιθανών σφαλμάτων)
            return None

    def _content_looks_real(self, content: str, platform_info: Dict[str, Any], username: str) -> bool:
        c = content.lower()
        if username.lower() in c:
            return True
        # Profile markers (Δείκτες προφίλ)
        markers = [m.lower() for m in platform_info.get('profile_markers', [])] + ["followers", "joined", "posts", "following", "repositories"]
        return any(m in c for m in markers)

    def _check_platform(self, platform_key: str, username: str) -> Optional[Tuple[str, str]]:
        cached_result = self._get_from_cache(username, platform_key)
        if cached_result:
            return cached_result

        platform = self.platforms.get(platform_key)
        if not platform:
            return None

        try:
            # Encode username for URL (Κωδικοποίηση ονόματος χρήστη για URL)
            url = platform['url_check'].format(identifier=quote(username))
        except Exception:
            self._save_to_cache(username, platform_key, "", False)
            return None

        resp = self.fetch_url(url)
        found = False
        result = None

        if resp:
            content_lower = resp.text.lower()
            error_type = platform.get('error_type')
            
            # --- Logic fix (Διόρθωση λογικής) ---
            if error_type == 'status_code':
                # Status check: Must be 200 AND have "real" content
                if resp.status_code == 200 and self._content_looks_real(content_lower, platform, username):
                    found = True
            
            elif error_type == 'string':
                # String check: Must be 200 AND NOT contain "not found" text
                not_found_markers = [t.lower() for t in platform.get('not_found_text', [])]
                if resp.status_code == 200 and not any(t in content_lower for t in not_found_markers):
                    found = True

        if found:
            result = (platform.get('name', platform_key), url)
        
        self._save_to_cache(username, platform_key, url if found else "", found)
        return result

    def _run_scan_phase(self, phase_name: str, keys_to_scan: List[str], username: str, progress: Optional[Progress]) -> List[Tuple[str, str]]:
        found_results = []
        if not keys_to_scan:
            return []
        
        task_id = None
        if progress:
            task_id = progress.add_task(f"[cyan]{phase_name}", total=len(keys_to_scan))
        else:
            print(f"  {phase_name}: Έλεγχος {len(keys_to_scan)} πλατφορμών...")

        with ThreadPoolExecutor(max_workers=min(len(keys_to_scan), self.max_workers)) as executor:
            future_to_key = {executor.submit(self._check_platform, key, username): key for key in keys_to_scan}
            
            for future in as_completed(future_to_key):
                try:
                    res = future.result()
                    if res:
                        found_results.append(res)
                        if progress and task_id:
                            progress.console.print(f"  [green]✓ Βρέθηκε:[/green] {res[0]}")
                except Exception:
                    pass
                
                if progress and task_id:
                    progress.update(task_id, advance=1)
        
        return found_results

    def run_account_discovery(self, username_list: List[str]):
        if not self.platforms:
            if RICH_AVAILABLE: console.print("[red]Δεν φορτώθηκαν δεδομένα πλατφόρμας. Ακύρωση.[/red]")
            else: print("Δεν φορτώθηκαν δεδομένα πλατφόρμας. Ακύρωση.")
            return

        valid_usernames = [u for u in username_list if self._validate_username_structure(u)]
        invalid_usernames = [u for u in username_list if u not in valid_usernames]

        if invalid_usernames:
            if RICH_AVAILABLE: console.print(f"[yellow]Παραλείφθηκαν {len(invalid_usernames)} μη έγκυρα ονόματα χρήστη: {', '.join(invalid_usernames)}[/yellow]")
            else: print("Παραλείφθηκαν μη έγκυρα ονόματα χρήστη:", invalid_usernames)
        if not valid_usernames:
            return

        for username in valid_usernames:
            if RICH_AVAILABLE: console.print(f"\n[bold cyan]Σάρωση για [magenta]{username}[/magenta]...[/] (stealth={self.stealth})")
            else: print(f"\nΣάρωση {username} (stealth={self.stealth})...")
            
            self._save_to_history(username)
            all_found_results = []
            
            progress_manager = None
            if RICH_AVAILABLE:
                progress_manager = Progress(
                    SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                    BarColumn(), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeElapsedColumn(), console=console, transient=False
                )
                progress_manager.start()
            
            try:
                # --- Phase 1: Scan Major Platforms (Φάση 1: Σάρωση Σημαντικών Πλατφορμών) ---
                phase_1_results = self._run_scan_phase("Φάση 1: Σημαντικές Πλατφόρμες", self.major_platform_keys, username, progress_manager)
                all_found_results.extend(phase_1_results)
                
                if not phase_1_results:
                    if RICH_AVAILABLE: console.print(f"[yellow]Δεν βρέθηκαν λογαριασμοί για {username} σε σημαντικές πλατφόρμες. Παράλειψη πλήρους σάρωσης.[/yellow]")
                    else: print(f"Δεν βρέθηκαν λογαριασμοί για {username} σε σημαντικές πλατφόρμες. Παράλειψη πλήρους σάρωσης.")
                    continue
                
                # --- Phase 2: Scan Minor Platforms (Φάση 2: Σάρωση Μικρότερων Πλατφορμών) ---
                phase_2_results = self._run_scan_phase("Φάση 2: Μικρότερες Πλατφόρμες", self.minor_platform_keys, username, progress_manager)
                all_found_results.extend(phase_2_results)
            
            finally:
                if progress_manager:
                    progress_manager.stop()
                    console.print(f"[bold]Η σάρωση για {username} ολοκληρώθηκε.[/bold]")

            # --- Save Results (Αποθήκευση Αποτελεσμάτων) ---
            txt_path = os.path.join(RESULTS_SAVE_FOLDER, f"{username}.txt")
            json_path = os.path.join(RESULTS_SAVE_FOLDER, f"{username}.json")
            try:
                all_found_results.sort()
                with open(txt_path, 'w', encoding='utf-8') as tf:
                    if not all_found_results:
                        tf.write(f"Δεν βρέθηκε ψηφιακό αποτύπωμα για {username}\n")
                    else:
                        tf.write(f"Αποτελέσματα για {username} ({len(all_found_results)} αντιστοιχίες)\n{'='*40}\n")
                        for name, url in all_found_results:
                            tf.write(f"{name}: {url}\n")
                
                with open(json_path, 'w', encoding='utf-8') as jf:
                    json.dump([{"platform": name, "url": url} for name, url in all_found_results], jf, indent=2)

                if RICH_AVAILABLE: console.print(f"[bold green]Αποθηκεύτηκαν {len(all_found_results)} αποτελέσματα για {username} στο {RESULTS_SAVE_FOLDER}[/bold green]")
                else: print(f"Αποθηκεύτηκαν {len(all_found_results)} αποτελέσματα για {username} στο {RESULTS_SAVE_FOLDER}")
            except Exception as e:
                if RICH_AVAILABLE: console.print(f"[red]Σφάλμα κατά την αποθήκευση των αποτελεσμάτων για {username}: {e}[/red]")

    def run(self):
        if self.keep_tui:
            try:
                curses.wrapper(self._tui)
                return
            except Exception as e:
                if RICH_AVAILABLE: console.print(f"[red]Το Curses TUI απέτυχε να φορτώσει ({e}). Επιστροφή σε λειτουργία κονσόλας.[/red]")
                else: print(f"Το Curses TUI απέτυχε ({e}). Επιστροφή σε λειτουργία κονσόλας.")
        self._console()

    def _console(self):
        # Console Mode (Λειτουργία Κονσόλας)
        print("--- Digital Footprint Finder — Λειτουργία Κονσόλας ---")
        if self.proxies_list:
            print(f"--- [bold green]Λειτουργία Proxy: ΕΝΕΡΓΗ ({len(self.proxies_list)} proxies φορτωμένα)[/bold green] ---", end='\n\n')
        print("Εισάγετε ονόματα χρήστη, ένα ανά γραμμή. Μια κενή γραμμή ξεκινά τη σάρωση.")
        usernames = []
        i = 1
        try:
            while True:
                u = input(f"Όνομα χρήστη {i}: ").strip()
                if not u:
                    break
                usernames.append(u)
                i += 1
        except (KeyboardInterrupt, EOFError):
            print()
        if usernames:
            self.run_account_discovery(usernames)
        else:
            print("Δεν εισήχθησαν ονόματα χρήστη. Έξοδος.")

    def _tui(self, stdscr):
        curses.curs_set(0)
        try:
            curses.start_color()
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
            curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
        except Exception: pass

        # Menu options (Επιλογές μενού)
        menu = ["Νέα Αναζήτηση", "Προβολή Ιστορικού", "Βοήθεια", "Έξοδος"]
        current = 0
        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()
            title = "Digital Footprint Finder - DedSec"
            subtitle = "(Απόκρυψη: ΕΝΕΡΓΗ)" if self.stealth else "(Απόκρυψη: ΑΝΕΝΕΡΓΗ)"
            if self.proxies_list:
                subtitle += f" (Proxies: {len(self.proxies_list)})"
            
            try:
                stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
                stdscr.addstr(1, max(0, w//2 - len(title)//2), title)
                stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
            except:
                stdscr.addstr(1, max(0, w//2 - len(title)//2), title, curses.A_BOLD)
                
            stdscr.addstr(2, max(0, w//2 - len(subtitle)//2), subtitle)

            for i, item in enumerate(menu):
                x = w//2 - len(item)//2
                y = h//2 - len(menu)//2 + i
                if i == current:
                    try: stdscr.attron(curses.color_pair(1)); stdscr.addstr(y, x, item); stdscr.attroff(curses.color_pair(1))
                    except Exception: stdscr.addstr(y, x, item, curses.A_REVERSE)
                else:
                    stdscr.addstr(y, x, item)
            stdscr.refresh()
            k = stdscr.getch()
            if k in (curses.KEY_UP, ord('k')): current = (current - 1) % len(menu)
            elif k in (curses.KEY_DOWN, ord('j')): current = (current + 1) % len(menu)
            elif k in (10, 13):
                choice = menu[current]
                if choice == "Νέα Αναζήτηση":
                    curses.endwin()
                    self._tui_input_screen()
                    stdscr = curses.initscr(); curses.curs_set(0)
                elif choice == "Προβολή Ιστορικού":
                    curses.endwin()
                    self._display_history_console()
                    stdscr = curses.initscr(); curses.curs_set(0)
                elif choice == "Βοήθεια":
                    curses.endwin()
                    self._display_help_console()
                    stdscr = curses.initscr(); curses.curs_set(0)
                else:
                    break
            elif k in (ord('q'), 27):
                break

    def _tui_input_screen(self):
        print("\n" * 5)
        self._console()
        # Input prompt (Προτροπή εισόδου)
        input("\nΠατήστε ENTER για επιστροφή στο μενού...")


    def _display_history_console(self):
        # Display History (Προβολή Ιστορικού)
        print("\n--- ΙΣΤΟΡΙΚΟ ΑΝΑΖΗΤΗΣΕΩΝ (τελευταία 50) ---")
        if not self.history:
            print("Δεν υπάρχει ιστορικό ακόμα.")
        else:
            print(f"{'ID':<4} | {'Όνομα Χρήστη':<25} | {'Χρονική Σήμανση':<20}")
            print("-" * 53)
            for row in self.history[:50]:
                print(f"{row[0]:<4} | {row[1]:<25} | {row[2]:<20}")
        input("\nΠατήστε ENTER για επιστροφή στο μενού...")

    def _display_help_console(self):
        # --- ADVANCED: Updated help text (Ενημερωμένο κείμενο βοήθειας) ---
        help_text = f"""
Digital Footprint Finder - Βοήθεια

- Προσπαθεί να ανακαλύψει δημόσιους λογαριασμούς για ένα όνομα χρήστη σε πολλές πλατφόρμες.
- Χρησιμοποιεί μια βάση δεδομένων Platforms JSON: '{PLATFORMS_FILE_NAME}' στον φάκελο '{self.data_folder}'.
- Τα αποτελέσματα αποθηκεύονται στο: {RESULTS_SAVE_FOLDER}

Χρήση:
1. Επιλέξτε "Νέα Αναζήτηση".
2. Εισάγετε ονόματα χρήστη ένα ανά γραμμή (πατήστε ENTER σε μια κενή γραμμή για να ξεκινήσει η σάρωση).
3. Το πρόγραμμα σαρώνει πρώτα τις κύριες πλατφόρμες. Εάν βρεθεί αντιστοιχία, προχωρά
   σε σάρωση όλων των άλλων πλατφορμών. Διαφορετικά, παραλείπει για εξοικονόμηση χρόνου.
4. Τα αποτελέσματα αποθηκεύονται ως αρχεία .txt και .json.

Προηγμένες Λειτουργίες:
- Λειτουργία Απόκρυψης (Stealth Mode) (προεπιλογή ΕΝΕΡΓΗ):
  - Χρησιμοποιεί λιγότερα ταυτόχρονα αιτήματα.
  - Περιστρέφει τις κεφαλίδες `User-Agent` για κάθε αίτημα ώστε να μοιάζει με πραγματικό πρόγραμμα περιήγησης.
- Υποστήριξη Proxy:
  - Για να χρησιμοποιήσετε proxies, εκτελέστε το σενάριο από το τερματικό σας με ένα όρισμα
    που να δείχνει στο αρχείο proxy σας:
    `python "Digital Footprint Finder.py" /path/to/my_proxies.txt`
  - Το αρχείο proxy πρέπει να είναι ένα απλό αρχείο κειμένου με έναν proxy ανά γραμμή
    (π.χ., `1.2.3.4:8080` ή `http://user:pass@1.2.3.4:8080`).

Αρχεία:
- ΒΔ & Ιστορικό: '{os.path.join(self.data_folder, NEW_DB_NAME)}'
- Platforms JSON: '{self.platforms_file}'
- Η βάση δεδομένων περιλαμβάνει πλέον μια κρυφή μνήμη 24 ωρών για να επιταχύνει τις επαναλαμβανόμενες αναζητήσεις.

Πατήστε ENTER για επιστροφή στο μενού...
"""
        print(help_text)
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            pass

# ---------------------------
# Entrypoint (Σημείο Εκκίνησης)
# ---------------------------
if __name__ == "__main__":
    os.makedirs(DATA_FOLDER, exist_ok=True)
    
    # --- ADVANCED: Check for proxy file argument (Έλεγχος για όρισμα αρχείου proxy) ---
    proxy_file_path = None
    if len(sys.argv) > 1:
        arg_path = sys.argv[1]
        if os.path.exists(arg_path):
            proxy_file_path = arg_path
            print(f"Φόρτωση με αρχείο proxy: {proxy_file_path}")
        else:
            print(f"Προειδοποίηση: Το αρχείο proxy δεν βρέθηκε στο '{arg_path}'. Εκκίνηση χωρίς proxies.")
            time.sleep(2)

    dff = DigitalFootprintFinder(
        stealth=STEALTH_DEFAULT, 
        keep_tui=True, 
        proxy_file=proxy_file_path
    )
    dff.run()
