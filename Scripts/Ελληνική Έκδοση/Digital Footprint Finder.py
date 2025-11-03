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

# Δικτύωση
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------------
# ΡΥΘΜΙΣΕΙΣ
# ---------------------------
DATA_FOLDER = "Digital Footprint Finder Files"
PLATFORMS_FILE_NAME = "Digital Footprint Finder Platforms.json"
OLD_DB_NAME = "footprint_history.db"
# Χρήση v2 για αποφυγή δηλητηρίασης της κρυφής μνήμης (cache-poisoning) από παλιές, λιγότερο ακριβείς σαρώσεις
NEW_DB_NAME = "search_history_v2.db"


# Διαδρομή αποθήκευσης αποτελεσμάτων φιλική προς το Termux. εφεδρική εάν δεν είναι διαθέσιμη
RESULTS_SAVE_FOLDER = os.path.join(os.path.expanduser('~'), 'storage', 'downloads', 'Digital Footprint Finder')
FALLBACK_RESULTS_FOLDER = os.path.join(os.path.expanduser('~'), 'Digital_Footprint_Results')

# Προεπιλεγμένες ρυθμίσεις δικτύου
DEFAULT_TIMEOUT = 7  # Ελαφρώς αυξημένο χρονικό όριο για proxies
DEFAULT_RETRIES = 2
DEFAULT_BACKOFF = 1.5
CACHE_DURATION_HOURS = 24

# Προεπιλογές Stealth (ΕΝΕΡΓΟ από προεπιλογή)
STEALTH_DEFAULT = True
STEALTH_MAX_WORKERS = 6
NONSTEALTH_MAX_WORKERS = 30

# Πλατφόρμες που είναι γνωστό ότι είναι διφορούμενες ή μη λειτουργικές
AMBIGUOUS_PLATFORMS_TO_SKIP = [
    "wechat", "spotify"
]

# --- ΓΙΑ ΠΡΟΧΩΡΗΜΕΝΟΥΣ: Λίστα εναλλαγής User-Agent ---
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/119.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
]

# ---------------------------
# Αυτόματη εγκατάσταση εξαρτήσεων (κατά το δυνατόν)
# ---------------------------
def install_dependencies():
    # ... (Κώδικας από προηγούμενη έκδοση, χωρίς αλλαγές) ...
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
        return False
install_dependencies()

# Προσπάθεια εισαγωγής του rich για καλύτερη εμφάνιση στην κονσόλα
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TaskID
    console = Console()
    RICH_AVAILABLE = True
except Exception:
    console = None # type: ignore
    RICH_AVAILABLE = False
    # ... (Εικονικές κλάσεις από προηγούμενη έκδοση, χωρίς αλλαγές) ...
    class Progress: pass # type: ignore
    class SpinnerColumn: pass # type: ignore
    class TextColumn: pass # type: ignore
    class BarColumn: pass # type: ignore
    class TimeElapsedColumn: pass # type: ignore
    class TaskID: pass # type: ignore

# ---------------------------
# Βοηθητικά: Διαχειριστής DB, φάκελος αποτελεσμάτων
# ---------------------------
@contextmanager
def database_manager(db_path: str):
    # ... (Κώδικας από προηγούμενη έκδοση, χωρίς αλλαγές) ...
    conn = None
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY,
                username TEXT,
                timestamp TEXT
            )
        """)
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
    # ... (Κώδικας από προηγούμενη έκδοση, χωρίς αλλαγές) ...
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
# Προεπιλεγμένο ελάχιστο σύνολο πλατφορμών (εφεδρικό)
# ---------------------------
DEFAULT_PLATFORMS = {
    # ... (Κώδικας από προηγούμενη έκδοση, χωρίς αλλαγές) ...
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
# Δημιουργία session αιτημάτων (με επαναπροσπάθειες)
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
    
    # --- ΓΙΑ ΠΡΟΧΩΡΗΜΕΝΟΥΣ: Ορισμός βασικών headers, αλλά το User-Agent θα εναλλάσσεται ανά αίτημα ---
    if stealth:
        session.headers.update({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        })
    else:
        session.headers.update({'User-Agent': f'DigitalFootprintFinder/1.1 (Advanced)'})
    
    setattr(session, 'request_timeout', timeout)
    return session

# ---------------------------
# Κύρια ενοποιημένη κλάση
# ---------------------------
class DigitalFootprintFinder:
    def __init__(self, stealth: bool = STEALTH_DEFAULT, keep_tui: bool = True, proxy_file: Optional[str] = None):
        self.stealth = stealth
        self.keep_tui = keep_tui
        self.data_folder = DATA_FOLDER
        self.db_path = os.path.join(DATA_FOLDER, NEW_DB_NAME)
        
        # --- ΕΝΑΡΞΗ ΔΙΟΡΘΩΣΗΣ ---
        # Αυτή η νέα μέθοδος βρίσκει τη σωστή διαδρομή αρχείου platforms.json
        # *πριν* συμβεί οποιαδήποτε άλλη αρχικοποίηση.
        self.platforms_file = self._find_or_create_platforms_json()
        # --- ΤΕΛΟΣ ΔΙΟΡΘΩΣΗΣ ---
        
        self.max_workers = STEALTH_MAX_WORKERS if stealth else NONSTEALTH_MAX_WORKERS
        self._initialize_file_structure() # Αυτό τώρα χειρίζεται μόνο τη ΒΔ
        self.platforms = self._load_platforms()
        self.history = self._load_history()
        
        # --- ΓΙΑ ΠΡΟΧΩΡΗΜΕΝΟΥΣ: Φόρτωση Proxies ---
        self.proxies_list = self._load_proxies(proxy_file)
        if proxy_file and self.proxies_list and RICH_AVAILABLE:
            console.print(f"[green]Φορτώθηκαν {len(self.proxies_list)} proxies από το {proxy_file}[/green]")
        elif proxy_file and not self.proxies_list:
            if RICH_AVAILABLE:
                console.print(f"[red]Το αρχείο proxy {proxy_file} ήταν κενό ή δεν ήταν δυνατή η ανάγνωσή του.[/red]")
        
        # --- ΔΙΟΡΘΩΣΗ: Δημιουργία μιας ενιαίας, ταξινομημένης λίστας όλων των πλατφορμών ---
        self.all_platform_keys = sorted(list(self.platforms.keys()))
        # --- ΤΕΛΟΣ ΔΙΟΡΘΩΣΗΣ ---
        
        self.session = make_requests_session(timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES, backoff=DEFAULT_BACKOFF, stealth=self.stealth)
        
        # --- ΝΕΟ: Για αποτελέσματα αναζήτησης Google ---
        self.google_results_links: List[Tuple[str, str]] = []


    # --- ΕΝΑΡΞΗ ΔΙΟΡΘΩΣΗΣ: ΝΕΑ ΒΟΗΘΗΤΙΚΗ ΜΕΘΟΔΟΣ ---
    def _find_or_create_platforms_json(self) -> str:
        """
        Βρίσκει το JSON πλατφορμών, δίνοντας προτεραιότητα στον τοπικό κατάλογο.
        Αν δεν βρεθεί πουθενά, δημιουργεί ένα προεπιλεγμένο στον DATA_FOLDER.
        """
        local_path = PLATFORMS_FILE_NAME
        data_folder_path = os.path.join(self.data_folder, PLATFORMS_FILE_NAME)

        # 1. Έλεγχος αν βρίσκεται στον τοπικό κατάλογο (μαζί με το .py)
        if os.path.exists(local_path):
            if RICH_AVAILABLE:
                console.print(f"[green]Χρήση αρχείου πλατφορμών από τον τοπικό κατάλογο: {local_path}[/green]")
            return local_path
        
        # 2. Έλεγχος αν βρίσκεται ήδη στον φάκελο δεδομένων
        if os.path.exists(data_folder_path):
            if RICH_AVAILABLE:
                console.print(f"[green]Χρήση αρχείου πλατφορμών από τον φάκελο δεδομένων: {data_folder_path}[/green]")
            return data_folder_path

        # 3. Δεν βρίσκεται πουθενά. Δημιουργία του προεπιλεγμένου στον φάκελο δεδομένων.
        os.makedirs(self.data_folder, exist_ok=True)
        try:
            with open(data_folder_path, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_PLATFORMS, f, indent=2)
            if RICH_AVAILABLE:
                console.print(f"[yellow]Το JSON πλατφορμών δεν βρέθηκε — δημιουργήθηκε προεπιλεγμένο στο {data_folder_path}[/yellow]")
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red]Προειδοποίηση: δεν ήταν δυνατή η δημιουργία προεπιλεγμένου JSON πλατφορμών: {e}[/red]")
        
        return data_folder_path
    # --- ΤΕΛΟΣ ΔΙΟΡΘΩΣΗΣ ---

    def _initialize_file_structure(self):
        # ... (Κώδικας από προηγούμενη έκδοση, χωρίς αλλαγές) ...
        os.makedirs(self.data_folder, exist_ok=True)
        try:
            db_target = os.path.join(self.data_folder, NEW_DB_NAME)
            if os.path.exists(OLD_DB_NAME) and not os.path.exists(db_target):
                os.rename(OLD_DB_NAME, db_target)
                if RICH_AVAILABLE:
                    console.print(f"[green]Μετακινήθηκε η παλιά DB '{OLD_DB_NAME}' -> '{db_target}'[/green]")
        except Exception:
            pass
        
        # --- ΕΝΑΡΞΗ ΔΙΟΡΘΩΣΗΣ ---
        # Η λογική δημιουργίας του platforms.json ΑΦΑΙΡΕΘΗΚΕ από εδώ.
        # Τη χειρίζεται πλέον η _find_or_create_platforms_json() στον constructor.
        # --- ΤΕΛΟΣ ΔΙΟΡΘΩΣΗΣ ---

    def _load_platforms(self) -> Dict[str, Any]:
        # ... (Κώδικας από προηγούμενη έκδοση, χωρίς αλλαγές) ...
        try:
            # το self.platforms_file είναι τώρα εγγυημένα η *σωστή* διαδρομή
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
            if RICH_AVAILABLE:
                console.print(f"[red]Σφάλμα: Δεν φορτώθηκαν πλατφόρμες. Χρήση εσωτερικής προεπιλογής.[/red]")
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
                # Ανάγνωση γραμμών, αφαίρεση κενών διαστημάτων και φιλτράρισμα κενών γραμμών
                proxies = [line.strip() for line in f if line.strip()]
                return proxies
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red]Σφάλμα κατά τη φόρτωση του αρχείου proxy {proxy_file}: {e}[/red]")
            return []

    def _load_history(self):
        # ... (Κώδικας από προηγούμενη έκδοση, χωρίς αλλαγές) ...
        try:
            with database_manager(self.db_path) as (_, cursor):
                cursor.execute("SELECT id, username, timestamp FROM history ORDER BY id DESC")
                return cursor.fetchall()
        except Exception:
            return []

    def _save_to_history(self, username: str):
        # ... (Κώδικας από προηγούμενη έκδοση, χωρίς αλλαγές) ...
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with database_manager(self.db_path) as (conn, cursor):
                cursor.execute("INSERT INTO history (username, timestamp) VALUES (?, ?)", (username, timestamp))
                conn.commit()
            self.history = self._load_history()
        except Exception:
            pass

    def _get_from_cache(self, username: str, platform_key: str) -> Optional[Tuple[str, str]]:
        # ... (Κώδικας από προηγούμενη έκδοση, χωρίς αλλαγές) ...
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
                    if datetime.now() - ts < timedelta(hours=CACHE_DURATION_HOURS):
                        # Χρήση του self.platforms.get για αποφυγή σφάλματος κλειδιού αν η πλατφόρμα αφαιρέθηκε από το JSON
                        platform = self.platforms.get(platform_key)
                        if platform:
                            return (platform['name'], url) if found else None
        except Exception:
            return None
        return None

    def _save_to_cache(self, username: str, platform_key: str, url: str, found: bool):
        # ... (Κώδικας από προηγούμενη έκδοση, χωρίς αλλαγές) ...
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
        # ... (Κώδικας από προηγούμενη έκδοση, χωρίς αλλαγές) ...
        validation_pattern = re.compile(r"^(?=.{1,90}$)[a-zA-Z0-9_.-]+$", re.UNICODE)
        return bool(validation_pattern.match(username))

    def fetch_url(self, url: str) -> Optional[requests.Response]:
        try:
            timeout = getattr(self.session, 'request_timeout', DEFAULT_TIMEOUT)
            
            # --- ΓΙΑ ΠΡΟΧΩΡΗΜΕΝΟΥΣ: Ορισμός headers και proxies ανά αίτημα ---
            headers = self.session.headers.copy()
            if self.stealth:
                headers['User-Agent'] = random.choice(USER_AGENTS)

            proxies = None
            if self.proxies_list:
                proxy_url = random.choice(self.proxies_list)
                # Εξασφάλιση ότι το proxy_url έχει σχήμα (π.χ., http:// ή socks5://)
                if not proxy_url.startswith(('http://', 'https://', 'socks5://')):
                    proxy_url = f"http://{proxy_url}"
                proxies = {
                    "http": proxy_url,
                    "https": proxy_url
                }

            return self.session.get(url, timeout=timeout, headers=headers, proxies=proxies)
        
        except requests.exceptions.ProxyError:
            if RICH_AVAILABLE:
                console.log(f"[red]ProxyError: Αποτυχία σύνδεσης στον proxy για {url}[/red]")
            return None
        except requests.exceptions.ReadTimeout:
            # Αυτό είναι συνηθισμένο, ας μην γεμίσουμε την κονσόλα
            return None
        except Exception:
            # Παρακολούθηση άλλων πιθανών σφαλμάτων (π.χ., σφάλματα σύνδεσης)
            return None

    def _content_looks_real(self, content: str, platform_info: Dict[str, Any], username: str) -> bool:
        # ... (Κώδικας από προηγούμενη έκδοση, χωρίς αλλαγές) ...
        c = content.lower()
        if username.lower() in c:
            return True
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
            
            # --- Διατήρηση της κρίσιμης διόρθωσης λογικής ---
            if error_type == 'status_code':
                # Έλεγχος κατάστασης: Πρέπει να είναι 200 ΚΑΙ να έχει "πραγματικό" περιεχόμενο
                if resp.status_code == 200 and self._content_looks_real(content_lower, platform, username):
                    found = True
            
            elif error_type == 'string':
                # --- ΛΟΓΙΚΗ ΑΚΡΙΒΕΙΑΣ ---
                # Αυτός είναι ο νέος, πιο ακριβής έλεγχος.
                # 1. Πρέπει να είναι 200
                # 2. ΔΕΝ ΠΡΕΠΕΙ να περιέχει κείμενο "not found"
                # 3. ΠΡΕΠΕΙ ΕΠΙΣΗΣ να περιέχει δείκτες "πραγματικού περιεχομένου"
                not_found_markers = [t.lower() for t in platform.get('not_found_text', [])]
                if resp.status_code == 200 and not any(t in content_lower for t in not_found_markers):
                    
                    # --- Βελτίωση Ακρίβειας ---
                    # Τώρα, έλεγχος και για θετικούς δείκτες για να είμαστε σίγουροι ότι είναι πραγματικό προφίλ.
                    if self._content_looks_real(content_lower, platform, username):
                        found = True
                    # Αν περάσει τον έλεγχο "not found" αλλά δεν έχει πραγματικό περιεχόμενο,
                    # είναι πιθανότατα μια γενική σελίδα (π.χ., σελίδα αναζήτησης, τείχος σύνδεσης).
                    # Σε αυτή την περίπτωση, το 'found' παραμένει False.

        if found:
            result = (platform.get('name', platform_key), url)
        
        self._save_to_cache(username, platform_key, url if found else "", found)
        return result

    def _run_scan_phase(self, phase_name: str, keys_to_scan: List[str], username: str, progress: Optional[Progress]) -> List[Tuple[str, str]]:
        # ... (Κώδικας από προηγούμενη έκδοση, χωρίς αλλαγές) ...
        found_results = []
        if not keys_to_scan:
            return []
        
        task_id = None
        if progress:
            task_id = progress.add_task(f"[cyan]{phase_name}", total=len(keys_to_scan))
        else:
            print(f"  {phase_name}: Έλεγχος {len(keys_to_scan)} πλατφορμών...")

        # --- ΤΡΟΠΟΠΟΙΗΣΗ: Προστέθηκε για μπάρα προόδου βασισμένη σε κείμενο ---
        completed_count = 0
        total_count = len(keys_to_scan)
        # --- ΤΕΛΟΣ ΤΡΟΠΟΠΟΙΗΣΗΣ ---

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
                
                # --- ΤΡΟΠΟΠΟΙΗΣΗ: Λογική και για rich και για text progress ---
                completed_count += 1
                if progress and task_id:
                    progress.update(task_id, advance=1)
                elif not progress and total_count > 0:
                    # Απλή μπάρα προόδου κειμένου
                    percent = (completed_count * 100) // total_count
                    bar_len = 20
                    filled_len = int(bar_len * completed_count // total_count)
                    bar = '█' * filled_len + '-' * (bar_len - filled_len)
                    print(f"  Πρόοδος: [{bar}] {percent}% ({completed_count}/{total_count})", end='\r')
                # --- ΤΕΛΟΣ ΤΡΟΠΟΠΟΙΗΣΗΣ ---

        if not progress:
             print() # Εκτύπωση νέας γραμμής για να τελειώσει η μπάρα προόδου
        
        return found_results

    # --- ΝΕΟ: Φάση Αναζήτησης Google ---
    def _run_google_search_phase(self, username: str, progress: Optional[Progress]) -> List[Tuple[str, str]]:
        """
        Δημιουργεί συνδέσμους αναζήτησης Google (dorks) ως εννοιολογική αναζήτηση.
        Αυτό ΔΕΝ "ξύνει" (scrape) το Google, αλλά παρέχει συνδέσμους για χειροκίνητη έρευνα.
        """
        task_id = None
        if progress:
            task_id = progress.add_task("[yellow]Δημιουργία Προτάσεων Google...", total=1)
        else:
            print("\n  Δημιουργία Προτάσεων Αναζήτησης Google...")

        if RICH_AVAILABLE:
            console.print("  [bold yellow]ΠΛΗΡΟΦΟΡΙΑ:[/bold yellow] Αυτή είναι μια εννοιολογική αναζήτηση για προχωρημένο OSINT.")
            console.print("  Για να το αυτοματοποιήσετε, θα χρειαζόταν να ενσωματώσετε μια υπηρεσία όπως το [bold]Google Custom Search JSON API[/bold].")
            console.print("  Οι παρακάτω σύνδεσμοι είναι προτάσεις για [bold]χειροκίνητη αναζήτηση[/bold]:")
        else:
            print("  ΠΛΗΡΟΦΟΡΙΑ: Αυτή είναι μια εννοιολογική αναζήτηση για προχωρημένο OSINT.")
            print("  Για να το αυτοματοποιήσετε, θα χρειαζόταν να ενσωματώσετε μια υπηρεσία όπως το Google Custom Search JSON API.")
            print("  Οι παρακάτω σύνδεσμοι είναι προτάσεις για χειροκίνητη αναζήτηση:")

        # Συνήθεις "dorks" για πλατφόρμες που είναι δύσκολο να σαρωθούν ή για εύρεση περισσότερων πληροφοριών
        dorks = [
            f'"https://www.linkedin.com/in/{username}"',
            f'"https://github.com/{username}"',
            f'"https://twitter.com/{username}"',
            f'"{username}" site:stackoverflow.com/users',
            f'"{username}" site:reddit.com/user',
            f'"{username}" site:medium.com',
            f'"{username}" site:dev.to'
        ]
        
        results_for_file = []
        for dork in dorks:
            google_url = f"https://www.google.com/search?q={quote(dork)}"
            # Αυτό το όνομα θα χρησιμοποιηθεί για την αναγνώρισή του στην αναφορά
            name = f"Google Search: {dork}" 
            if RICH_AVAILABLE:
                console.print(f"  - [cyan]{dork}[/cyan]")
            else:
                print(f"  - {dork}")
            results_for_file.append((name, google_url))
        
        if progress and task_id:
            progress.update(task_id, advance=1)
        
        return results_for_file
    # --- ΤΕΛΟΣ ΝΕΟΥ ---


    def run_account_discovery(self, username_list: List[str]):
        # ... (Κώδικας από προηγούμενη έκδοση, χωρίς αλλαγές) ...
        if not self.platforms:
            if RICH_AVAILABLE: console.print("[red]Δεν φορτώθηκαν δεδομένα πλατφορμών. Ακύρωση.[/red]")
            else: print("Δεν φορτώθηκαν δεδομένα πλατφορμών. Ακύρωση.")
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
                # --- ΔΙΟΡΘΩΣΗ: Εκτέλεση μίας, ενοποιημένης σάρωσης ---
                platform_results = self._run_scan_phase(
                    f"Σάρωση {len(self.all_platform_keys)} Πλατφορμών", # <-- Ενημερωμένο κείμενο
                    self.all_platform_keys, 
                    username, 
                    progress_manager
                )
                all_found_results.extend(platform_results)
                # --- ΤΕΛΟΣ ΔΙΟΡΘΩΣΗΣ ---
                
                # --- ΝΕΟ: Φάση Αναζήτησης Google ---
                self.google_results_links = self._run_google_search_phase(username, progress_manager)
                all_found_results.extend(self.google_results_links)
                # --- ΤΕΛΟΣ ΝΕΟΥ ---
            
            finally:
                if progress_manager:
                    progress_manager.stop()
                    console.print(f"[bold]Η σάρωση για τον {username} ολοκληρώθηκε.[/bold]")

            # --- ΤΡΟΠΟΠΟΙΗΣΗ: Αποθήκευση Αποτελεσμάτων ---
            txt_path = os.path.join(RESULTS_SAVE_FOLDER, f"{username}.txt")
            json_path = os.path.join(RESULTS_SAVE_FOLDER, f"{username}.json")
            try:
                # Διαχωρισμός αποτελεσμάτων πλατφορμών από προτάσεις Google
                platform_results = sorted([res for res in all_found_results if not res[0].startswith("Google Search:")])
                google_suggestions = [res for res in all_found_results if res[0].startswith("Google Search:")]

                with open(txt_path, 'w', encoding='utf-8') as tf:
                    if not platform_results:
                        tf.write(f"Δεν βρέθηκε άμεσο ψηφιακό αποτύπωμα για τον {username}\n")
                    else:
                        tf.write(f"Αποτελέσματα για {username} ({len(platform_results)} αντιστοιχίες)\n{'='*40}\n")
                        for name, url in platform_results:
                            tf.write(f"{name}: {url}\n")
                    
                    if google_suggestions:
                        tf.write(f"\n\nΠροτεινόμενες Αναζητήσεις Google\n{'='*40}\n")
                        tf.write("Αυτά δεν είναι επιβεβαιωμένα ευρήματα, αλλά σύνδεσμοι για αναζητήσεις Google που μπορείτε να εκτελέσετε χειροκίνητα.\n\n")
                        for name, url in google_suggestions:
                            # Καθαρισμός του ονόματος για την αναφορά
                            clean_name = name.replace("Google Search: ", "")
                            tf.write(f"Αναζήτηση: {clean_name}\n  -> Σύνδεσμος: {url}\n")
                
                # Το αρχείο JSON θα περιέχει μόνο επιβεβαιωμένα αποτελέσματα πλατφορμών
                with open(json_path, 'w', encoding='utf-8') as jf:
                    json.dump([{"platform": name, "url": url} for name, url in platform_results], jf, indent=2)

                if RICH_AVAILABLE: console.print(f"[bold green]Αποθηκεύτηκαν {len(platform_results)} αποτελέσματα για {username} στο {RESULTS_SAVE_FOLDER}[/bold green]")
                else: print(f"Αποθηκεύτηκαν {len(platform_results)} αποτελέσματα για {username} στο {RESULTS_SAVE_FOLDER}")
            
            except Exception as e:
                if RICH_AVAILABLE: console.print(f"[red]Σφάλμα κατά την αποθήκευση αποτελεσμάτων για {username}: {e}[/red]")
            # --- ΤΕΛΟΣ ΤΡΟΠΟΠΟΙΗΣΗΣ ---

    def run(self):
        # ... (Κώδικας από προηγούμενη έκδοση, χωρίς αλλαγές) ...
        if self.keep_tui:
            try:
                curses.wrapper(self._tui)
                return
            except Exception as e:
                if RICH_AVAILABLE: console.print(f"[red]Το Curses TUI απέτυχε να φορτώσει ({e}). Επιστροφή σε λειτουργία κονσόλας.[/red]")
                else: print(f"Το Curses TUI απέτυχε ({e}). Επιστροφή σε λειτουργία κονσόλας.")
        self._console()

    def _console(self):
        # ... (Κώδικας από προηγούμενη έκδοση, χωρίς αλλαγές) ...
        print("--- Digital Footprint Finder — Λειτουργία Κονσόλας ---")
        if self.proxies_list:
            if RICH_AVAILABLE: console.print(f"--- [bold green]Λειτουργία Proxy: ΕΝΕΡΓΗ ({len(self.proxies_list)} proxies φορτώθηκαν)[/bold green] ---", end='\n\n')
            else: print(f"--- Λειτουργία Proxy: ΕΝΕΡΓΗ ({len(self.proxies_list)} proxies φορτώθηκαν) ---\n")
        print("Εισαγάγετε ονόματα χρήστη, ένα ανά γραμμή. Μια κενή γραμμή ξεκινά τη σάρωση.")
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
        # ... (Κώδικας από προηγούμενη έκδοση, χωρίς αλλαγές) ...
        curses.curs_set(0)
        try:
            curses.start_color()
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
            curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
        except Exception: pass

        menu = ["Νέα Αναζήτηση", "Προβολή Ιστορικού", "Βοήθεια", "Έξοδος"]
        current = 0
        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()
            title = "Εύρεση Ψηφιακού Αποτυπώματος - DedSec"
            subtitle = "(Stealth: ΕΝΕΡΓΟ)" if self.stealth else "(Stealth: ΑΝΕΝΕΡΓΟ)"
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
        # ... (Κώδικας από προηγούμενη έκδοση, χωρίς αλλαγές) ...
        print("\n" * 5)
        self._console()
        input("\nΠατήστε ENTER για να επιστρέψετε στο μενού...")


    def _display_history_console(self):
        # ... (Κώδικας από προηγούμενη έκδοση, χωρίς αλλαγές) ...
        print("\n--- ΙΣΤΟΡΙΚΟ ΑΝΑΖΗΤΗΣΕΩΝ (τελευταίες 50) ---")
        if not self.history:
            print("Δεν υπάρχει ακόμη ιστορικό.")
        else:
            print(f"{'ID':<4} | {'Όνομα Χρήστη':<25} | {'Χρον. Σήμανση':<20}")
            print("-" * 53)
            for row in self.history[:50]:
                print(f"{row[0]:<4} | {row[1]:<25} | {row[2]:<20}")
        input("\nΠατήστε ENTER για να επιστρέψετε στο μενού...")

    def _display_help_console(self):
        # --- ΔΙΟΡΘΩΣΗ: Ενημερωμένο κείμενο βοήθειας για να αντικατοπτρίζει τη νέα λογική αρχείου πλατφορμών ---
        help_text = f"""
Εύρεση Ψηφιακού Αποτυπώματος - Βοήθεια

- Προσπαθεί να ανακαλύψει δημόσιους λογαριασμούς για ένα όνομα χρήστη σε πολλές πλατφόρμες.
- Χρησιμοποιεί μια βάση δεδομένων JSON Πλατφορμών.
- Τα αποτελέσματα αποθηκεύονται στο: {RESULTS_SAVE_FOLDER}

Αρχείο Πλατφορμών:
- Το script θα αναζητήσει ΠΡΩΤΑ το '{PLATFORMS_FILE_NAME}' στον ΙΔΙΟ κατάλογο.
- Αν δεν βρεθεί, θα αναζητήσει στο '{self.data_folder}'.
- Αν δεν βρεθεί πουθενά, ένα μικρό προεπιλεγμένο αρχείο δημιουργείται στο '{self.data_folder}'.
- **Για να χρησιμοποιήσετε το μεγάλο σας JSON, απλώς κρατήστε το στον ίδιο φάκελο με το αρχείο .py.**

Χρήση:
1. Επιλέξτε "Νέα Αναζήτηση".
2. Εισαγάγετε ονόματα χρήστη, ένα ανά γραμμή (πατήστε ENTER σε κενή γραμμή για να ξεκινήσετε).
3. Το πρόγραμμα σαρώνει όλες τις πλατφόρμες σε μία, ενοποιημένη σάρωση.
4. **ΝΕΟ:** Μια εννοιολογική φάση αναζήτησης Google παρέχει συνδέσμους για χειροκίνητη έρευνα.
5. Τα αποτελέσματα αποθηκεύονται ως .txt (με συνδέσμους Google) και .json (μόνο πλατφόρμες).

Προηγμένες Δυνατότητες:
- Λειτουργία Stealth (προεπιλογή: ΕΝΕΡΓΗ):
  - Χρησιμοποιεί λιγότερα ταυτόχρονα αιτήματα.
  - Εναλλάσσει τα `User-Agent` headers για κάθε αίτημα ώστε να μοιάζει με πραγματικό πρόγραμμα περιήγησης.
- Υποστήριξη Proxy:
  - Για να χρησιμοποιήσετε proxies, εκτελέστε το script από το τερματικό σας με ένα όρισμα
    που να δείχνει στο αρχείο proxy σας:
    `python "Digital Footprint Finder.py" /διαδρομή/προς/το/my_proxies.txt`
  - Το αρχείο proxy πρέπει να είναι ένα απλό αρχείο κειμένου με έναν proxy ανά γραμμή
    (π.χ., `1.2.3.4:8080` ή `http://user:pass@1.2.3.4:8080`).

Αρχεία:
- ΒΔ & Ιστορικό: '{os.path.join(self.data_folder, NEW_DB_NAME)}'
- JSON Πλατφορμών: '{self.platforms_file}' (Αυτή είναι η διαδρομή που χρησιμοποιεί *αυτή τη στιγμή*)
- Η βάση δεδομένων περιλαμβάνει πλέον μια 24-ωρη κρυφή μνήμη (cache) για να επιταχύνει τις επαναλαμβανόμενες αναζητήσεις.

Πατήστε ENTER για να επιστρέψετε στο μενού...
"""
        # --- ΤΕΛΟΣ ΔΙΟΡΘΩΣΗΣ ---
        print(help_text)
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            pass

# ---------------------------
# Σημείο εισόδου
# ---------------------------
if __name__ == "__main__":
    os.makedirs(DATA_FOLDER, exist_ok=True)
    
    # --- ΓΙΑ ΠΡΟΧΩΡΗΜΕΝΟΥΣ: Έλεγχος για όρισμα αρχείου proxy ---
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
