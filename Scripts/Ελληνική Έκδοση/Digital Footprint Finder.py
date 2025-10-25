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
# CONFIGURATION
# ---------------------------
DATA_FOLDER = "Digital Footprint Finder Files"
PLATFORMS_FILE_NAME = "Digital Footprint Finder Platforms.json"
OLD_DB_NAME = "footprint_history.db"
NEW_DB_NAME = "search_history.db"

# Termux-friendly results path; fallback if unavailable
RESULTS_SAVE_FOLDER = os.path.join(os.path.expanduser('~'), 'storage', 'downloads', 'Digital Footprint Finder')
FALLBACK_RESULTS_FOLDER = os.path.join(os.path.expanduser('~'), 'Digital_Footprint_Results')

# Default network settings
DEFAULT_TIMEOUT = 6
DEFAULT_RETRIES = 2
DEFAULT_BACKOFF = 1.5
CACHE_DURATION_HOURS = 24

# Stealth defaults (ON by default)
STEALTH_DEFAULT = True
STEALTH_MAX_WORKERS = 6
NONSTEALTH_MAX_WORKERS = 30

# Major platforms (prioritized)
MAJOR_PLATFORMS_KEYS = [
    "facebook", "twitter", "instagram", "tiktok", "linkedin",
    "pinterest", "snapchat", "telegram", "vk", "wechat",
    "threads", "bereal", "reddit", "quora", "medium",
    "github", "gitlab", "bitbucket", "stackoverflow", "youtube", "twitch"
]

# ---------------------------
# Dependency auto-install (best-effort)
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
        return False

# Attempt install (non-fatal)
install_dependencies()

# Try to import rich for nicer console output
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    console = Console()
    RICH_AVAILABLE = True
except Exception:
    console = None
    RICH_AVAILABLE = False

# ---------------------------
# Helpers: DB manager, results folder
# ---------------------------
@contextmanager
def database_manager(db_path: str):
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
# Default minimal platform set (fallback)
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
# Request session factory (with retries)
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
    if stealth:
        session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'})
    else:
        session.headers.update({'User-Agent': f'DigitalFootprintFinder/1.0 (Contact: your-email@example.com)'})
    # This attribute is custom, not a standard requests attribute
    setattr(session, 'request_timeout', timeout)
    return session

# ---------------------------
# Main unified class
# ---------------------------
class DigitalFootprintFinder:
    def __init__(self, stealth: bool = STEALTH_DEFAULT, keep_tui: bool = True):
        self.stealth = stealth
        self.keep_tui = keep_tui
        self.data_folder = DATA_FOLDER
        self.db_path = os.path.join(DATA_FOLDER, NEW_DB_NAME)
        self.platforms_file = os.path.join(DATA_FOLDER, PLATFORMS_FILE_NAME)
        self.max_workers = STEALTH_MAX_WORKERS if stealth else NONSTEALTH_MAX_WORKERS
        self._initialize_file_structure()
        self.platforms = self._load_platforms()
        self.history = self._load_history()
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
                    console.print(f"[green]Μετακινήθηκε η παλιά ΒΔ '{OLD_DB_NAME}' -> '{db_target}'[/green]")
        except Exception:
            pass
        if not os.path.exists(self.platforms_file):
            try:
                with open(self.platforms_file, 'w', encoding='utf-8') as f:
                    json.dump(DEFAULT_PLATFORMS, f, indent=2)
                if RICH_AVAILABLE:
                    console.print(f"[yellow]Δεν βρέθηκε JSON Πλατφορμών — δημιουργήθηκε προεπιλογή στο {self.platforms_file}[/yellow]")
            except Exception as e:
                if RICH_AVAILABLE:
                    console.print(f"[red]Προειδοποίηση: δεν ήταν δυνατή η δημιουργία του JSON Πλατφορμών: {e}[/red]")

    def _load_platforms(self) -> Dict[str, Any]:
        try:
            with open(self.platforms_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            all_platforms = {}
            for category in data.values():
                for key, info in category.items():
                    info.setdefault('not_found_text', [])
                    info.setdefault('profile_markers', [])
                    all_platforms[key] = info
            return all_platforms
        except Exception:
            fallback = {}
            for category in DEFAULT_PLATFORMS.values():
                fallback.update(category)
            return fallback

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
        validation_pattern = re.compile(r"^(?=.{2,64}$)(?![._-])(?!.*[._-]{2})(?!.*[._-]$)[\w\.-]+$", re.UNICODE)
        return bool(validation_pattern.match(username))

    def fetch_url(self, url: str) -> Optional[requests.Response]:
        try:
            timeout = getattr(self.session, 'request_timeout', DEFAULT_TIMEOUT)
            return self.session.get(url, timeout=timeout)
        except Exception:
            return None

    def _content_looks_real(self, content: str, platform_info: Dict[str, Any], username: str) -> bool:
        c = content.lower()
        if username.lower() in c:
            return True
        markers = [m.lower() for m in platform_info.get('profile_markers', [])] + ["followers", "joined", "posts", "following"]
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
            if platform.get('error_type') == 'status_code':
                if resp.status_code == 200 and self._content_looks_real(resp.text, platform, username):
                    found = True
            elif platform.get('error_type') == 'string':
                c = resp.text.lower()
                not_found = [t.lower() for t in platform.get('not_found_text', [])]
                if resp.status_code == 200 and not any(t in c for t in not_found) and self._content_looks_real(c, platform, username):
                    found = True
        
        if found:
            result = (platform.get('name', platform_key), url)
        
        self._save_to_cache(username, platform_key, url if found else "", found)
        return result

    def run_account_discovery(self, username_list: List[str]):
        if not self.platforms:
            if RICH_AVAILABLE:
                console.print("[red]Δεν φορτώθηκαν δεδομένα πλατφόρμας. Ακύρωση.[/red]")
            else:
                print("Δεν φορτώθηκαν δεδομένα πλατφόρμας. Ακύρωση.")
            return

        valid_usernames = [u for u in username_list if self._validate_username_structure(u)]
        invalid_usernames = [u for u in username_list if u not in valid_usernames]

        if invalid_usernames:
            if RICH_AVAILABLE:
                console.print(f"[yellow]Παραλείφθηκαν {len(invalid_usernames)} μη έγκυρα ονόματα χρήστη: {', '.join(invalid_usernames)}[/yellow]")
            else:
                print("Παραλείφθηκαν μη έγκυρα ονόματα χρήστη:", invalid_usernames)

        if not valid_usernames:
            return

        for username in valid_usernames:
            if RICH_AVAILABLE:
                console.print(f"[cyan]Σάρωση για {username}... (stealth={self.stealth})[/cyan]")
            else:
                print(f"Σάρωση {username} (stealth={self.stealth})...")
            
            self._save_to_history(username)
            found_results = []

            # --- Phase 1: Scan Major Platforms ---
            if RICH_AVAILABLE:
                console.print(f"  [bold]Φάση 1:[/bold] Έλεγχος {len(self.major_platform_keys)} κύριων πλατφορμών...")
            
            with ThreadPoolExecutor(max_workers=min(len(self.major_platform_keys), self.max_workers)) as executor:
                future_to_key = {executor.submit(self._check_platform, key, username): key for key in self.major_platform_keys}
                for future in as_completed(future_to_key):
                    try:
                        res = future.result()
                        if res:
                            found_results.append(res)
                    except Exception:
                        pass
            
            # --- Decision Point: Continue to full scan or stop ---
            if not found_results:
                if RICH_AVAILABLE:
                    console.print(f"[yellow]Δεν βρέθηκαν λογαριασμοί για τον/την {username} στις κύριες πλατφόρμες. Παράλειψη πλήρους σάρωσης.[/yellow]")
                else:
                    print(f"Δεν βρέθηκαν αποτελέσματα για τον/την {username} στις κύριες πλατφόρμες. Παράλειψη πλήρους σάρωσης.")
                continue  # Move to the next username
            
            if RICH_AVAILABLE:
                console.print(f"  [green]Βρέθηκε στις κύριες: {', '.join([r[0] for r in found_results])}[/green]")
                console.print(f"  [bold]Φάση 2:[/bold] Έλεγχος {len(self.minor_platform_keys)} άλλων πλατφορμών...")

            # --- Phase 2: Scan Minor Platforms ---
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_key = {executor.submit(self._check_platform, key, username): key for key in self.minor_platform_keys}
                for future in as_completed(future_to_key):
                    try:
                        res = future.result()
                        if res:
                            found_results.append(res)
                    except Exception:
                        pass

            # --- Save Results ---
            txt_path = os.path.join(RESULTS_SAVE_FOLDER, f"{username}.txt")
            json_path = os.path.join(RESULTS_SAVE_FOLDER, f"{username}.json")
            try:
                found_results.sort()
                with open(txt_path, 'w', encoding='utf-8') as tf:
                    if not found_results:
                        tf.write(f"Δεν βρέθηκε ψηφιακό αποτύπωμα για τον/την {username}\n")
                    else:
                        tf.write(f"Αποτελέσματα για τον/την {username} ({len(found_results)} αντιστοιχίες)\n{'='*40}\n")
                        for name, url in found_results:
                            tf.write(f"{name}: {url}\n")
                
                with open(json_path, 'w', encoding='utf-8') as jf:
                    json.dump([{"platform": name, "url": url} for name, url in found_results], jf, indent=2)

                if RICH_AVAILABLE:
                    console.print(f"[bold green]Αποθηκεύτηκαν {len(found_results)} αποτελέσματα για τον/την {username} στο {RESULTS_SAVE_FOLDER}[/bold green]")
                else:
                    print(f"Αποθηκεύτηκαν {len(found_results)} αποτελέσματα για τον/την {username} στο {RESULTS_SAVE_FOLDER}")
            except Exception as e:
                if RICH_AVAILABLE:
                    console.print(f"[red]Σφάλμα κατά την αποθήκευση των αποτελεσμάτων για τον/την {username}: {e}[/red]")

    def run(self):
        if self.keep_tui:
            try:
                curses.wrapper(self._tui)
                return
            except Exception:
                pass
        self._console()

    def _console(self):
        print("Εύρεση Ψηφιακού Αποτυπώματος — Λειτουργία κονσόλας")
        print("Εισαγάγετε ονόματα χρήστη ένα ανά γραμμή. Κενή γραμμή για εκτέλεση.")
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
        except Exception:
            pass

        menu = ["Νέα Αναζήτηση", "Προβολή Ιστορικού", "Βοήθεια", "Έξοδος"]
        current = 0
        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()
            title = "Εύρεση Ψηφιακού Αποτυπώματος - DedSec"
            subtitle = "(Stealth: ΕΝΕΡΓΟ)" if self.stealth else "(Stealth: ΑΝΕΝΕΡΓΟ)"
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
                    try:
                        stdscr.attron(curses.color_pair(1))
                        stdscr.addstr(y, x, item)
                        stdscr.attroff(curses.color_pair(1))
                    except Exception:
                        stdscr.addstr(y, x, item, curses.A_REVERSE)
                else:
                    stdscr.addstr(y, x, item)
            stdscr.refresh()
            k = stdscr.getch()
            if k in (curses.KEY_UP, ord('k')):
                current = (current - 1) % len(menu)
            elif k in (curses.KEY_DOWN, ord('j')):
                current = (current + 1) % len(menu)
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
        print("\n--- ΝΕΑ ΑΝΑΖΗΤΗΣΗ ---")
        print("Εισαγάγετε ονόματα χρήστη ένα-ένα. Πατήστε ENTER σε μια κενή γραμμή για να ξεκινήσει η αναζήτηση.")
        names = []
        try:
            while True:
                u = input(f"Όνομα χρήστη {len(names) + 1}: ").strip()
                if not u:
                    break
                names.append(u)
        except (KeyboardInterrupt, EOFError):
            print()
        if names:
            self.run_account_discovery(names)
            input("\nΠατήστε ENTER για επιστροφή στο μενού...")
        else:
            print("Δεν δόθηκαν ονόματα χρήστη. Επιστροφή στο μενού.")
            time.sleep(1)

    def _display_history_console(self):
        print("\n--- ΙΣΤΟΡΙΚΟ ΑΝΑΖΗΤΗΣΕΩΝ (τελευταίες 50) ---")
        if not self.history:
            print("Δεν υπάρχει ακόμη ιστορικό.")
        else:
            for row in self.history[:50]:
                print(f"{row[0]:4d} | {row[1]:20s} | {row[2]}")
        input("\nΠατήστε ENTER για επιστροφή στο μενού...")

    def _display_help_console(self):
        help_text = f"""
Εύρεση Ψηφιακού Αποτυπώματος - Βοήθεια

- Προσπαθεί να ανακαλύψει δημόσιους λογαριασμούς για ένα όνομα χρήστη σε πολλές πλατφόρμες.
- Χρησιμοποιεί μια βάση δεδομένων JSON Πλατφορμών: '{PLATFORMS_FILE_NAME}' στον φάκελο '{self.data_folder}'.
- Τα αποτελέσματα αποθηκεύονται στο: {RESULTS_SAVE_FOLDER}

Χρήση:
1. Επιλέξτε "Νέα Αναζήτηση".
2. Εισαγάγετε ονόματα χρήστη ένα ανά γραμμή (πατήστε ENTER σε κενή γραμμή για να ξεκινήσετε).
3. Το πρόγραμμα σαρώνει πρώτα τις κύριες πλατφόρμες. Αν βρεθεί αντιστοιχία, προχωρά
   στη σάρωση όλων των άλλων πλατφορμών. Διαφορετικά, παραλείπει για εξοικονόμηση χρόνου.
4. Τα αποτελέσματα αποθηκεύονται ως αρχεία .txt και .json.

Λειτουργία Stealth (προεπιλογή ΕΝΕΡΓΗ):
- Χρησιμοποιεί λιγότερα ταυτόχρονα αιτήματα και ένα γενικό User-Agent για να είναι λιγότερο αισθητό.

Αρχεία:
- ΒΔ & ιστορικό: '{os.path.join(self.data_folder, NEW_DB_NAME)}'
- JSON Πλατφορμών: '{self.platforms_file}'
- Η βάση δεδομένων περιλαμβάνει πλέον μια κρυφή μνήμη 24 ωρών για την επιτάχυνση επαναλαμβανόμενων αναζητήσεων.

Σημειώσεις:
- Αυτό το εργαλείο ελέγχει μόνο δημοσίως προσβάσιμα URLs.
- Σεβαστείτε την ιδιωτικότητα και τα νομικά όρια. Σφάλματα δικτύου ή αλλαγές στις πλατφόρμες ενδέχεται να επηρεάσουν τα αποτελέσματα.

Πατήστε ENTER για επιστροφή στο μενού...
"""
        print(help_text)
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            pass

# ---------------------------
# Entrypoint
# ---------------------------
if __name__ == "__main__":
    os.makedirs(DATA_FOLDER, exist_ok=True)
    dff = DigitalFootprintFinder(stealth=STEALTH_DEFAULT, keep_tui=True)
    dff.run()
