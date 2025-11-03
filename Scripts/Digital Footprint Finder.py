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
# CONFIGURATION
# ---------------------------
DATA_FOLDER = "Digital Footprint Finder Files"
PLATFORMS_FILE_NAME = "Digital Footprint Finder Platforms.json"
OLD_DB_NAME = "footprint_history.db"
# Using v2 to avoid cache-poisoning from old, less-accurate scans
NEW_DB_NAME = "search_history_v2.db"


# Termux-friendly results path; fallback if unavailable
RESULTS_SAVE_FOLDER = os.path.join(os.path.expanduser('~'), 'storage', 'downloads', 'Digital Footprint Finder')
FALLBACK_RESULTS_FOLDER = os.path.join(os.path.expanduser('~'), 'Digital_Footprint_Results')

# Default network settings
DEFAULT_TIMEOUT = 7  # Slightly increased timeout for proxies
DEFAULT_RETRIES = 2
DEFAULT_BACKOFF = 1.5
CACHE_DURATION_HOURS = 24

# Stealth defaults (ON by default)
STEALTH_DEFAULT = True
STEALTH_MAX_WORKERS = 6
NONSTEALTH_MAX_WORKERS = 30

# Platforms known to be ambiguous or non-functional
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
# Dependency auto-install (best-effort)
# ---------------------------
def install_dependencies():
    # ... (Code from previous version, no changes) ...
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

# Try to import rich for nicer console output
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TaskID
    console = Console()
    RICH_AVAILABLE = True
except Exception:
    console = None # type: ignore
    RICH_AVAILABLE = False
    # ... (Dummy classes from previous version, no changes) ...
    class Progress: pass
    class SpinnerColumn: pass
    class TextColumn: pass
    class BarColumn: pass
    class TimeElapsedColumn: pass
    class TaskID: pass

# ---------------------------
# Helpers: DB manager, results folder
# ---------------------------
@contextmanager
def database_manager(db_path: str):
    # ... (Code from previous version, no changes) ...
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
    # ... (Code from previous version, no changes) ...
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
    # ... (Code from previous version, no changes) ...
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
    
    # --- ADVANCED: Set base headers, but User-Agent will be rotated per-request ---
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
# Main unified class
# ---------------------------
class DigitalFootprintFinder:
    def __init__(self, stealth: bool = STEALTH_DEFAULT, keep_tui: bool = True, proxy_file: Optional[str] = None):
        self.stealth = stealth
        self.keep_tui = keep_tui
        self.data_folder = DATA_FOLDER
        self.db_path = os.path.join(DATA_FOLDER, NEW_DB_NAME)
        
        # --- START FIX ---
        # This new method finds the correct platforms.json file path
        # *before* any other initialization happens.
        self.platforms_file = self._find_or_create_platforms_json()
        # --- END FIX ---
        
        self.max_workers = STEALTH_MAX_WORKERS if stealth else NONSTEALTH_MAX_WORKERS
        self._initialize_file_structure() # This now only handles the DB
        self.platforms = self._load_platforms()
        self.history = self._load_history()
        
        # --- ADVANCED: Load Proxies ---
        self.proxies_list = self._load_proxies(proxy_file)
        if proxy_file and self.proxies_list and RICH_AVAILABLE:
            console.print(f"[green]Loaded {len(self.proxies_list)} proxies from {proxy_file}[/green]")
        elif proxy_file and not self.proxies_list:
            if RICH_AVAILABLE:
                console.print(f"[red]Proxy file {proxy_file} was empty or could not be read.[/red]")
        
        # --- FIX: Create one single, sorted list of all platforms ---
        self.all_platform_keys = sorted(list(self.platforms.keys()))
        # --- END FIX ---
        
        self.session = make_requests_session(timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES, backoff=DEFAULT_BACKOFF, stealth=self.stealth)

    # --- START FIX: NEW HELPER METHOD ---
    def _find_or_create_platforms_json(self) -> str:
        """
        Finds the platform JSON, prioritizing the local directory.
        If not found anywhere, creates a default one in DATA_FOLDER.
        """
        local_path = PLATFORMS_FILE_NAME
        data_folder_path = os.path.join(self.data_folder, PLATFORMS_FILE_NAME)

        # 1. Check if it's in the local directory (alongside .py)
        if os.path.exists(local_path):
            if RICH_AVAILABLE:
                console.print(f"[green]Using platforms file from local directory: {local_path}[/green]")
            return local_path
        
        # 2. Check if it's already in the data folder
        if os.path.exists(data_folder_path):
            if RICH_AVAILABLE:
                console.print(f"[green]Using platforms file from data folder: {data_folder_path}[/green]")
            return data_folder_path

        # 3. It's nowhere. Create the default one in the data folder.
        os.makedirs(self.data_folder, exist_ok=True)
        try:
            with open(data_folder_path, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_PLATFORMS, f, indent=2)
            if RICH_AVAILABLE:
                console.print(f"[yellow]Platforms JSON not found — created default at {data_folder_path}[/yellow]")
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red]Warning: could not create default Platforms JSON: {e}[/red]")
        
        return data_folder_path
    # --- END FIX ---

    def _initialize_file_structure(self):
        # ... (Code from previous version, no changes) ...
        os.makedirs(self.data_folder, exist_ok=True)
        try:
            db_target = os.path.join(self.data_folder, NEW_DB_NAME)
            if os.path.exists(OLD_DB_NAME) and not os.path.exists(db_target):
                os.rename(OLD_DB_NAME, db_target)
                if RICH_AVAILABLE:
                    console.print(f"[green]Moved old DB '{OLD_DB_NAME}' -> '{db_target}'[/green]")
        except Exception:
            pass
        
        # --- START FIX ---
        # The logic for creating platforms.json was REMOVED from here.
        # It is now handled by _find_or_create_platforms_json() in the constructor.
        # --- END FIX ---

    def _load_platforms(self) -> Dict[str, Any]:
        # ... (Code from previous version, no changes) ...
        try:
            # self.platforms_file is now guaranteed to be the *correct* path
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
            console.print(f"[yellow]Warning: Skipped loading ambiguous platforms: {', '.join(skipped_platforms)}[/yellow]")
        
        if not all_platforms:
            if RICH_AVAILABLE:
                console.print(f"[red]Error: No platforms loaded. Using internal default.[/red]")
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
                # Read lines, strip whitespace, and filter out empty lines
                proxies = [line.strip() for line in f if line.strip()]
                return proxies
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red]Error loading proxy file {proxy_file}: {e}[/red]")
            return []

    def _load_history(self):
        # ... (Code from previous version, no changes) ...
        try:
            with database_manager(self.db_path) as (_, cursor):
                cursor.execute("SELECT id, username, timestamp FROM history ORDER BY id DESC")
                return cursor.fetchall()
        except Exception:
            return []

    def _save_to_history(self, username: str):
        # ... (Code from previous version, no changes) ...
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with database_manager(self.db_path) as (conn, cursor):
                cursor.execute("INSERT INTO history (username, timestamp) VALUES (?, ?)", (username, timestamp))
                conn.commit()
            self.history = self._load_history()
        except Exception:
            pass

    def _get_from_cache(self, username: str, platform_key: str) -> Optional[Tuple[str, str]]:
        # ... (Code from previous version, no changes) ...
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
                        # Use self.platforms.get to avoid key error if platform was removed from JSON
                        platform = self.platforms.get(platform_key)
                        if platform:
                            return (platform['name'], url) if found else None
        except Exception:
            return None
        return None

    def _save_to_cache(self, username: str, platform_key: str, url: str, found: bool):
        # ... (Code from previous version, no changes) ...
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
        # ... (Code from previous version, no changes) ...
        validation_pattern = re.compile(r"^(?=.{1,90}$)[a-zA-Z0-9_.-]+$", re.UNICODE)
        return bool(validation_pattern.match(username))

    def fetch_url(self, url: str) -> Optional[requests.Response]:
        try:
            timeout = getattr(self.session, 'request_timeout', DEFAULT_TIMEOUT)
            
            # --- ADVANCED: Set request-specific headers and proxies ---
            headers = self.session.headers.copy()
            if self.stealth:
                headers['User-Agent'] = random.choice(USER_AGENTS)

            proxies = None
            if self.proxies_list:
                proxy_url = random.choice(self.proxies_list)
                # Ensure proxy_url has a scheme (e.g., http:// or socks5://)
                if not proxy_url.startswith(('http://', 'https://', 'socks5://')):
                    proxy_url = f"http://{proxy_url}"
                proxies = {
                    "http": proxy_url,
                    "https": proxy_url
                }

            return self.session.get(url, timeout=timeout, headers=headers, proxies=proxies)
        
        except requests.exceptions.ProxyError:
            if RICH_AVAILABLE:
                console.log(f"[red]ProxyError: Failed to connect to proxy for {url}[/red]")
            return None
        except requests.exceptions.ReadTimeout:
            # This is common, don't flood console
            return None
        except Exception:
            # Catch other potential errors (e.g., connection errors)
            return None

    def _content_looks_real(self, content: str, platform_info: Dict[str, Any], username: str) -> bool:
        # ... (Code from previous version, no changes) ...
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
            
            # --- Retaining the crucial logic fix ---
            if error_type == 'status_code':
                # Status check: Must be 200 AND have "real" content
                if resp.status_code == 200 and self._content_looks_real(content_lower, platform, username):
                    found = True
            
            elif error_type == 'string':
                # --- ACCURACY LOGIC ---
                # This is the new, more accurate check.
                # 1. Must be 200
                # 2. Must NOT contain "not found" text
                # 3. Must ALSO contain "real content" markers
                not_found_markers = [t.lower() for t in platform.get('not_found_text', [])]
                if resp.status_code == 200 and not any(t in content_lower for t in not_found_markers):
                    
                    # --- Accuracy Improvement ---
                    # Now, also check for positive markers to be sure it's a real profile.
                    if self._content_looks_real(content_lower, platform, username):
                        found = True
                    # If it passes the "not found" check but has no real content,
                    # it's likely a generic page (e.g., search page, login wall).
                    # In this case, 'found' remains False.

        if found:
            result = (platform.get('name', platform_key), url)
        
        self._save_to_cache(username, platform_key, url if found else "", found)
        return result

    def _run_scan_phase(self, phase_name: str, keys_to_scan: List[str], username: str, progress: Optional[Progress]) -> List[Tuple[str, str]]:
        # ... (Code from previous version, no changes) ...
        found_results = []
        if not keys_to_scan:
            return []
        
        task_id = None
        if progress:
            task_id = progress.add_task(f"[cyan]{phase_name}", total=len(keys_to_scan))
        else:
            print(f"  {phase_name}: Checking {len(keys_to_scan)} platforms...")

        with ThreadPoolExecutor(max_workers=min(len(keys_to_scan), self.max_workers)) as executor:
            future_to_key = {executor.submit(self._check_platform, key, username): key for key in keys_to_scan}
            
            for future in as_completed(future_to_key):
                try:
                    res = future.result()
                    if res:
                        found_results.append(res)
                        if progress and task_id:
                            progress.console.print(f"  [green]✓ Found:[/green] {res[0]}")
                except Exception:
                    pass
                
                if progress and task_id:
                    progress.update(task_id, advance=1)
        
        return found_results

    def run_account_discovery(self, username_list: List[str]):
        # ... (Code from previous version, no changes) ...
        if not self.platforms:
            if RICH_AVAILABLE: console.print("[red]No platform data loaded. Aborting.[/red]")
            else: print("No platform data loaded. Aborting.")
            return

        valid_usernames = [u for u in username_list if self._validate_username_structure(u)]
        invalid_usernames = [u for u in username_list if u not in valid_usernames]

        if invalid_usernames:
            if RICH_AVAILABLE: console.print(f"[yellow]Skipped {len(invalid_usernames)} invalid usernames: {', '.join(invalid_usernames)}[/yellow]")
            else: print("Skipped invalid usernames:", invalid_usernames)
        if not valid_usernames:
            return

        for username in valid_usernames:
            if RICH_AVAILABLE: console.print(f"\n[bold cyan]Scanning for [magenta]{username}[/magenta]...[/] (stealth={self.stealth})")
            else: print(f"\nScanning {username} (stealth={self.stealth})...")
            
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
                # --- FIX: Run a single, unified scan ---
                all_found_results = self._run_scan_phase(
                    f"Scanning {len(self.all_platform_keys)} Platforms", # <-- Updated text
                    self.all_platform_keys, 
                    username, 
                    progress_manager
                )
                # --- END FIX ---
            
            finally:
                if progress_manager:
                    progress_manager.stop()
                    console.print(f"[bold]Scan for {username} complete.[/bold]")

            # --- Save Results ---
            txt_path = os.path.join(RESULTS_SAVE_FOLDER, f"{username}.txt")
            json_path = os.path.join(RESULTS_SAVE_FOLDER, f"{username}.json")
            try:
                all_found_results.sort()
                with open(txt_path, 'w', encoding='utf-8') as tf:
                    if not all_found_results:
                        tf.write(f"No digital footprint found for {username}\n")
                    else:
                        tf.write(f"Results for {username} ({len(all_found_results)} matches)\n{'='*40}\n")
                        for name, url in all_found_results:
                            tf.write(f"{name}: {url}\n")
                
                with open(json_path, 'w', encoding='utf-8') as jf:
                    json.dump([{"platform": name, "url": url} for name, url in all_found_results], jf, indent=2)

                if RICH_AVAILABLE: console.print(f"[bold green]Saved {len(all_found_results)} results for {username} to {RESULTS_SAVE_FOLDER}[/bold green]")
                else: print(f"Saved {len(all_found_results)} results for {username} to {RESULTS_SAVE_FOLDER}")
            except Exception as e:
                if RICH_AVAILABLE: console.print(f"[red]Error saving results for {username}: {e}[/red]")

    def run(self):
        # ... (Code from previous version, no changes) ...
        if self.keep_tui:
            try:
                curses.wrapper(self._tui)
                return
            except Exception as e:
                if RICH_AVAILABLE: console.print(f"[red]Curses TUI failed to load ({e}). Falling back to console mode.[/red]")
                else: print(f"Curses TUI failed ({e}). Falling back to console mode.")
        self._console()

    def _console(self):
        # ... (Code from previous version, no changes) ...
        print("--- Digital Footprint Finder — Console Mode ---")
        if self.proxies_list:
            print(f"--- [bold green]Proxy Mode: ACTIVE ({len(self.proxies_list)} proxies loaded)[/bold green] ---", end='\n\n')
        print("Enter usernames one per line. A blank line starts the scan.")
        usernames = []
        i = 1
        try:
            while True:
                u = input(f"Username {i}: ").strip()
                if not u:
                    break
                usernames.append(u)
                i += 1
        except (KeyboardInterrupt, EOFError):
            print()
        if usernames:
            self.run_account_discovery(usernames)
        else:
            print("No usernames entered. Exiting.")

    def _tui(self, stdscr):
        # ... (Code from previous version, no changes) ...
        curses.curs_set(0)
        try:
            curses.start_color()
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
            curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
        except Exception: pass

        menu = ["New Search", "View History", "Help", "Exit"]
        current = 0
        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()
            title = "Digital Footprint Finder - DedSec"
            subtitle = "(Stealth: ACTIVE)" if self.stealth else "(Stealth: INACTIVE)"
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
                    try: std.attron(curses.color_pair(1)); stdscr.addstr(y, x, item); stdscr.attroff(curses.color_pair(1))
                    except Exception: stdscr.addstr(y, x, item, curses.A_REVERSE)
                else:
                    stdscr.addstr(y, x, item)
            stdscr.refresh()
            k = stdscr.getch()
            if k in (curses.KEY_UP, ord('k')): current = (current - 1) % len(menu)
            elif k in (curses.KEY_DOWN, ord('j')): current = (current + 1) % len(menu)
            elif k in (10, 13):
                choice = menu[current]
                if choice == "New Search":
                    curses.endwin()
                    self._tui_input_screen()
                    stdscr = curses.initscr(); curses.curs_set(0)
                elif choice == "View History":
                    curses.endwin()
                    self._display_history_console()
                    stdscr = curses.initscr(); curses.curs_set(0)
                elif choice == "Help":
                    curses.endwin()
                    self._display_help_console()
                    stdscr = curses.initscr(); curses.curs_set(0)
                else:
                    break
            elif k in (ord('q'), 27):
                break

    def _tui_input_screen(self):
        # ... (Code from previous version, no changes) ...
        print("\n" * 5)
        self._console()
        input("\nPress ENTER to return to the menu...")


    def _display_history_console(self):
        # ... (Code from previous version, no changes) ...
        print("\n--- SEARCH HISTORY (last 50) ---")
        if not self.history:
            print("No history yet.")
        else:
            print(f"{'ID':<4} | {'Username':<25} | {'Timestamp':<20}")
            print("-" * 53)
            for row in self.history[:50]:
                print(f"{row[0]:<4} | {row[1]:<25} | {row[2]:<20}")
        input("\nPress ENTER to return to the menu...")

    def _display_help_console(self):
        # --- FIX: Updated help text to reflect new platform file logic ---
        help_text = f"""
Digital Footprint Finder - Help

- Attempts to discover public accounts for a username across multiple platforms.
- Uses a Platforms JSON database.
- Results are saved to: {RESULTS_SAVE_FOLDER}

Platform File:
- The script will FIRST look for '{PLATFORMS_FILE_NAME}' in the SAME directory.
- If not found, it will look in '{self.data_folder}'.
- If not found anywhere, a small default file is created in '{self.data_folder}'.
- **To use your large JSON, just keep it in the same folder as the .py script.**

Usage:
1. Select "New Search".
2. Enter usernames one per line (press ENTER on a blank line to start).
3. The program scans all platforms in a single, unified scan.
4. Results are saved as .txt and .json files.

Advanced Features:
- Stealth Mode (default ACTIVE):
  - Uses fewer concurrent requests.
  - Rotates `User-Agent` headers for every request to look like a real browser.
- Proxy Support:
  - To use proxies, run the script from your terminal with an argument
    pointing to your proxy file:
    `python "Digital Footprint Finder.py" /path/to/my_proxies.txt`
  - The proxy file should be a plain text file with one proxy per line
    (e.g., `1.2.3.4:8080` or `http://user:pass@1.2.3.4:8080`).

Files:
- DB & History: '{os.path.join(self.data_folder, NEW_DB_NAME)}'
- Platforms JSON: '{self.platforms_file}' (This is the path it's *currently* using)
- The database now includes a 24-hour cache to speed up repeated searches.

Press ENTER to return to the menu...
"""
        # --- END FIX ---
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
    
    # --- ADVANCED: Check for proxy file argument ---
    proxy_file_path = None
    if len(sys.argv) > 1:
        arg_path = sys.argv[1]
        if os.path.exists(arg_path):
            proxy_file_path = arg_path
            print(f"Loading with proxy file: {proxy_file_path}")
        else:
            print(f"Warning: Proxy file not found at '{arg_path}'. Starting without proxies.")
            time.sleep(2)

    dff = DigitalFootprintFinder(
        stealth=STEALTH_DEFAULT, 
        keep_tui=True, 
        proxy_file=proxy_file_path
    )
    dff.run()
