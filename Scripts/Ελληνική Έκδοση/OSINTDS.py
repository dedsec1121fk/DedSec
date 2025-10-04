#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import re
import socket
import ssl
import json
import time
import random
import subprocess
import base64
import html
import tempfile
import webbrowser
import shutil
from urllib.parse import urlparse, urljoin, parse_qs, urlencode, urlunparse, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Εξαρτήσεις και Ρύθμιση ---

ΑΠΑΙΤΟΥΜΕΝΑ = ("requests", "bs4", "dnspython", "python-whois")

def elegxos_paketon_termux(onoma_paketou, entoli_pros_elegxo=None):
    """Ελέγχει αν μια εντολή, συνήθως από ένα πακέτο Termux, είναι διαθέσιμη στο PATH του συστήματος."""
    entoli_pros_elegxo = entoli_pros_elegxo or onoma_paketou
    # Χρήση του shutil.which για έναν πιο αξιόπιστο και cross-platform τρόπο εύρεσης ενός εκτελέσιμου.
    return shutil.which(entoli_pros_elegxo) is not None

def diasfalisi_exartiseon():
    """Ελέγχει για τα απαιτούμενα πακέτα Python και προσπαθεί να εγκαταστήσει όσα λείπουν."""
    leipoun = []
    for pkg in ΑΠΑΙΤΟΥΜΕΝΑ:
        try:
            # Χειρισμός της ειδικής περίπτωσης όπου το όνομα του πακέτου διαφέρει από το όνομα εισαγωγής.
            onoma_eisagogis = "whois" if pkg == "python-whois" else pkg
            __import__(onoma_eisagogis)
        except ImportError:
            leipoun.append(pkg)
    if leipoun:
        print(f"Εγκατάσταση απαιτούμενων πακέτων Python που λείπουν: {', '.join(leipoun)}")
        try:
            # Κατασκευή της εντολής pip χρησιμοποιώντας το sys.executable για να διασφαλιστεί η χρήση του σωστού pip.
            entoli_pip = [sys.executable, "-m", "pip", "install", *leipoun]
            subprocess.check_call(entoli_pip)
        except subprocess.CalledProcessError as e:
            print(f"[ΣΦΑΛΜΑ] Αποτυχία εγκατάστασης των εξαρτήσεων Python μέσω pip: {e}")
            print("Παρακαλώ εκτελέστε χειροκίνητα την εντολή 'pip install requests beautifulsoup4 dnspython python-whois'.")
            sys.exit(1)
        except Exception as e:
            print(f"[ΣΦΑΛΜΑ] Παρουσιάστηκε ένα μη αναμενόμενο σφάλμα κατά την εγκατάσταση των εξαρτήσεων: {e}")
            sys.exit(1)

diasfalisi_exartiseon()

try:
    import requests
    from bs4 import BeautifulSoup
    import dns.resolver
    import dns.query
    import dns.exception
    import csv
    import whois
except ImportError:
    print("[ΚΡΙΣΙΜΟ ΣΦΑΛΜΑ] Τα απαιτούμενα πακέτα Python λείπουν παρά την προσπάθεια εγκατάστασης. Τερματισμός.")
    sys.exit(1)

# Απενεργοποίηση προειδοποιήσεων του requests για μη ασφαλείς συνδέσεις SSL.
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

# --- Διαμόρφωση και Σταθερές ---

# Ορισμός προτιμώμενων διαδρομών για την αποθήκευση αρχείων εξόδου.
ΠΡΟΤΙΜΩΜΕΝΕΣ_ΔΙΑΔΡΟΜΕΣ = [
    os.path.expanduser("~/storage/downloads"),
    os.path.expanduser("/sdcard/Download"),
    os.path.expanduser("~/Downloads"),
    os.getcwd()
]
ΒΑΣΙΚΟΣ_ΦΑΚΕΛΟΣ_ΛΗΨΕΩΝ_TERMUX = os.path.join(os.path.expanduser('~'), 'storage', 'downloads')

def ληψη_φακελου_ληψεων():
    """Βρίσκει τον πρώτο υπάρχοντα προτιμώμενο κατάλογο για λήψεις."""
    for p in ΠΡΟΤΙΜΩΜΕΝΕΣ_ΔΙΑΔΡΟΜΕΣ:
        if os.path.isdir(p):
            return p
    return os.getcwd()

ΦΑΚΕΛΟΣ_ΛΗΨΕΩΝ = ληψη_φακελου_ληψεων()
ΒΑΣΙΚΟΣ_ΦΑΚΕΛΟΣ_OSINT = os.path.join(ΦΑΚΕΛΟΣ_ΛΗΨΕΩΝ, "OSINTDS_GR")
os.makedirs(ΒΑΣΙΚΟΣ_ΦΑΚΕΛΟΣ_OSINT, exist_ok=True)

ΚΕΦΑΛΙΔΕΣ = {"User-Agent": "OSINTDS-Scanner/1.1-GR"}
ΧΡΟΝΙΚΟ_ΟΡΙΟ_HTTP = 10
ΠΡΟΕΠΙΛΕΓΜΕΝΑ_THREADS = 25
ΚΑΘΥΣΤΕΡΗΣΗ_ΑΙΤΗΜΑΤΩΝ = 0.05
PAYLOAD_ΔΟΚΙΜΗΣ_XSS = "<script>alert('OSINTDS_XSS_GR')</script>"
ΜΟΤΙΒΑ_ΣΦΑΛΜΑΤΩΝ_SQL = [
    "you have an error in your sql syntax", "sql syntax error",
    "unclosed quotation mark after the character string", "mysql_fetch",
    "syntax error in query", "warning: mysql", "unterminated string constant",
]

ΚΕΦΑΛΙΔΕΣ_ΑΣΦΑΛΕΙΑΣ = [
    "Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options",
    "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy",
]

ΕΠΕΞΕΡΓΑΣΤΗΣ = os.environ.get('EDITOR', 'nano')
ΧΑΡΤΗΣ_ΠΟΡΩΝ = [
    ('link', 'href', 'css', lambda tag: tag.get('rel') and 'stylesheet' in tag.get('rel', [])),
    ('script', 'src', 'js', None),
    ('img', 'src', 'images', None),
    ('source', 'src', 'media', None),
    ('video', 'poster', 'images', None),
    ('link', 'href', 'icons', lambda tag: tag.get('rel') and any(r in ['icon', 'shortcut icon'] for r in tag.get('rel', []))),
]
REGEX_URL_INLINE_CSS = re.compile(r'url\(([\'"]?.*?[\'"]?)\)')

# --- Λίστες λέξεων (Απλό Base64) ---
ΛΙΣΤΑ_ΛΕΞΕΩΝ_DIR_B64 = "YWRtaW4KYmFja3VwCnJvYm90cy50eHQKc2l0ZW1hcC54bWwKLmVudi5iYWNrCnVwbG9hZHMKYWRtaW5pc3RyYXRvcgo="
ΛΙΣΤΑ_ΛΕΞΕΩΝ_SUBDOMAIN_B64 = "d3d3CmFwaQpibG9nCmRldgptYWlsCnN0YWdpbmcKdGVzdApzdG9yZQ=="

# --- Βοηθητικές Συναρτήσεις για Λίστες Λέξεων ---

def αποσυμπιεση_λιστας_λεξεων(b64, διαδρομη_προορισμου, ονομα):
    """Αποκωδικοποιεί μια συμβολοσειρά Base64 και γράφει το περιεχόμενό της σε ένα αρχείο."""
    try:
        raw = base64.b64decode(b64)
        txt = raw.decode('utf-8', errors='ignore')
        if not txt.strip():
             print(f'[ΠΡΟΕΙΔΟΠΟΙΗΣΗ] Η λίστα λέξεων για {ονομα} είναι κενή.')
             return None
        with open(διαδρομη_προορισμου, 'w', encoding='utf-8') as f:
            f.write(txt)
        print(f'[ΠΛΗΡΟΦΟΡΙΑ] Δημιουργήθηκε προεπιλεγμένη λίστα λέξεων: {διαδρομη_προορισμου} ({len(txt.splitlines())} εγγραφές)')
        return διαδρομη_προορισμου
    except Exception as e:
        print(f'[ΣΦΑΛΜΑ] Σφάλμα αποσυμπίεσης λίστας λέξεων για {ονομα}: {e}')
        # Δημιουργία ενός κενού αρχείου για να αποφευχθούν επαναλαμβανόμενες προσπάθειες αποσυμπίεσης.
        open(διαδρομη_προορισμου, 'w').close()
        return None

ΦΑΚΕΛΟΣ_ΛΙΣΤΩΝ_ΛΕΞΕΩΝ = os.path.join(ΒΑΣΙΚΟΣ_ΦΑΚΕΛΟΣ_OSINT, 'wordlists')
os.makedirs(ΦΑΚΕΛΟΣ_ΛΙΣΤΩΝ_ΛΕΞΕΩΝ, exist_ok=True)
ΔΙΑΔΡΟΜΗ_ΛΙΣΤΑΣ_DIR = os.path.join(ΦΑΚΕΛΟΣ_ΛΙΣΤΩΝ_ΛΕΞΕΩΝ, 'dirs_gr.txt')
ΔΙΑΔΡΟΜΗ_ΛΙΣΤΑΣ_SUB = os.path.join(ΦΑΚΕΛΟΣ_ΛΙΣΤΩΝ_ΛΕΞΕΩΝ, 'subdomains_gr.txt')

# Αποσυμπίεση λιστών λέξεων αν δεν υπάρχουν ή είναι κενές.
if not os.path.isfile(ΔΙΑΔΡΟΜΗ_ΛΙΣΤΑΣ_DIR) or os.path.getsize(ΔΙΑΔΡΟΜΗ_ΛΙΣΤΑΣ_DIR) == 0:
    αποσυμπιεση_λιστας_λεξεων(ΛΙΣΤΑ_ΛΕΞΕΩΝ_DIR_B64, ΔΙΑΔΡΟΜΗ_ΛΙΣΤΑΣ_DIR, 'dirs_gr.txt')
if not os.path.isfile(ΔΙΑΔΡΟΜΗ_ΛΙΣΤΑΣ_SUB) or os.path.getsize(ΔΙΑΔΡΟΜΗ_ΛΙΣΤΑΣ_SUB) == 0:
    αποσυμπιεση_λιστας_λεξεων(ΛΙΣΤΑ_ΛΕΞΕΩΝ_SUBDOMAIN_B64, ΔΙΑΔΡΟΜΗ_ΛΙΣΤΑΣ_SUB, 'subdomains_gr.txt')

def διαβασμα_λιστας_λεξεων(διαδρομη):
    """Διαβάζει ένα αρχείο λίστας λέξεων και επιστρέφει μια λίστα με καθαρισμένες γραμμές."""
    try:
        with open(διαδρομη, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f'[ΣΦΑΛΜΑ] Η λίστα λέξεων δεν βρέθηκε στη διαδρομή {διαδρομη}.')
        return []
    except Exception as e:
        print(f'[ΣΦΑΛΜΑ] Αποτυχία ανάγνωσης της λίστας λέξεων στη διαδρομή {διαδρομη}: {e}')
        return []

ΛΕΞΕΙΣ_DIR = διαβασμα_λιστας_λεξεων(ΔΙΑΔΡΟΜΗ_ΛΙΣΤΑΣ_DIR)
ΛΕΞΕΙΣ_SUB = διαβασμα_λιστας_λεξεων(ΔΙΑΔΡΟΜΗ_ΛΙΣΤΑΣ_SUB)

# --- Βασικές Βοηθητικές Συναρτήσεις ---

def κανονικοποιηση_στοχου(ακατεργαστη_εισοδος):
    """Καθαρίζει και τυποποιεί ένα URL στόχου, επιστρέφοντας το βασικό URL και το domain."""
    ακατεργαστη_εισοδος = ακατεργαστη_εισοδος.strip()
    if not ακατεργαστη_εισοδος:
        return None, None
    if not re.match(r'^(http://|https://)', ακατεργαστη_εισοδος, re.IGNORECASE):
        ακατεργαστη_εισοδος = 'http://' + ακατεργαστη_εισοδος
    try:
        parsed = urlparse(ακατεργαστη_εισοδος)
        domain = parsed.hostname
        if not domain:
            return None, None
        base = f"{parsed.scheme}://{parsed.netloc}"
        return base.rstrip('/'), domain
    except ValueError:
        return None, None

def δημιουργια_φακελων(domain):
    """Δημιουργεί έναν κατάλογο για το domain του στόχου για την αποθήκευση των αποτελεσμάτων της σάρωσης."""
    ασφαλες_domain = re.sub(r'[^\w\-.]', '_', domain)
    φακελος_στοχου = os.path.join(ΒΑΣΙΚΟΣ_ΦΑΚΕΛΟΣ_OSINT, ασφαλες_domain)
    os.makedirs(φακελος_στοχου, exist_ok=True)
    return φακελος_στοχου

def αποθηκευση_κειμενου(φακελος, ονομα_αρχειου, κειμενο):
    """Αποθηκεύει περιεχόμενο κειμένου σε ένα αρχείο."""
    διαδρομη = os.path.join(φακελος, ονομα_αρχειου)
    try:
        with open(διαδρομη, 'w', encoding='utf-8') as f:
            f.write(κειμενο)
        print(f"[ΠΛΗΡΟΦΟΡΙΑ] Αποθηκεύτηκε: {διαδρομη}")
    except IOError as e:
        print(f'[ΣΦΑΛΜΑ] Σφάλμα αποθήκευσης αρχείου για {διαδρομη}: {e}')

def αποθηκευση_csv(φακελος, ονομα_αρχειου, σειρες, κεφαλιδες=None):
    """Αποθηκεύει μια λίστα από σειρές σε ένα αρχείο CSV."""
    διαδρομη = os.path.join(φακελος, ονομα_αρχειου)
    try:
        with open(διαδρομη, 'w', newline='', encoding='utf-8') as cf:
            writer = csv.writer(cf)
            if κεφαλιδες:
                writer.writerow(κεφαλιδες)
            writer.writerows([[str(item) for item in row] for row in σειρες])
        print('[ΠΛΗΡΟΦΟΡΙΑ] Αποθηκεύτηκε CSV:', διαδρομη)
    except IOError as e:
        print(f'[ΣΦΑＬΜΑ] Σφάλμα αποθήκευσης CSV για {διαδρομη}: {e}')

def αποθηκευση_checkpoint(φακελος, αναφορα):
    """Αποθηκεύει την τρέχουσα κατάσταση της αναφοράς σε ένα αρχείο JSON για συνέχιση."""
    αποθηκευση_κειμενου(φακελος, 'report.json', json.dumps(αναφορα, indent=2, default=str))

# --- ΣΥΝΑΡΤΗΣΕΙΣ ΣΑΡΩΣΗΣ ---

def ληψη_πληροφοριων_whois(domain):
    """Ανακτά και μορφοποιεί πληροφορίες WHOIS για ένα domain."""
    try:
        w = whois.whois(domain)
        # ΔΙΟΡΘΩΣΗ BUG: Χειρισμός περίπτωσης όπου η αναζήτηση whois επιστρέφει None
        if not w:
            return {'error': 'Δεν επιστράφηκαν δεδομένα WHOIS.'}
        
        # ΒΕΛΤΙΩΣΗ: Ομορφοποίηση λιστών και αντικειμένων datetime για καλύτερη αναγνωσιμότητα.
        δεδομενα_whois = {}
        for κλειδι, τιμη in w.items():
            if not τιμη:
                continue
            if isinstance(τιμη, list):
                δεδομενα_whois[κλειδι] = ', '.join(map(str, τιμη))
            elif hasattr(τιμη, 'strftime'):
                δεδομενα_whois[κλειδι] = τιμη.strftime('%Y-%m-%d %H:%M:%S')
            else:
                δεδομενα_whois[κλειδι] = str(τιμη)
        return δεδομενα_whois
    except Exception as e:
        return {'error': str(e)}

def αντιστροφη_αναζητηση_dns(διευθυνση_ip):
    """Πραγματοποιεί μια αντίστροφη αναζήτηση DNS σε μια διεύθυνση IP."""
    if not διευθυνση_ip:
        return None
    try:
        return socket.gethostbyaddr(διευθυνση_ip)[0]
    except (socket.herror, socket.gaierror):
        return None

def επιλυση_ολων_των_dns(domain):
    """Επιλύει κοινούς τύπους εγγραφών DNS για ένα domain."""
    αποτελεσματα = {}
    τυποι_εγγραφων = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME']
    for τυπος_εγγραφης in τυποι_εγγραφων:
        try:
            απαντησεις = dns.resolver.resolve(domain, τυπος_εγγραφης)
            αποτελεσματα[τυπος_εγγραφης] = sorted([str(r).strip() for r in απαντησεις])
        except dns.resolver.NoAnswer:
            αποτελεσματα[τυπος_εγγραφης] = []
        # ΒΕΛΤΙΩΣΗ: Προσθήκη ειδικού χειρισμού εξαιρέσεων για κοινά σφάλματα DNS.
        except dns.resolver.NXDOMAIN:
            αποτελεσματα[τυπος_εγγραφης] = ['Το Domain Δεν Βρέθηκε']
        except dns.exception.Timeout:
             αποτελεσματα[τυπος_εγγραφης] = ['Χρονικό Όριο']
        except Exception:
             αποτελεσματα[τυπος_εγγραφης] = ['Σφάλμα']
    return αποτελεσματα

def εξαγωγη_πληροφοριων_περιεχομενου(περιεχομενο_html):
    """Εξάγει emails, ετικέτες generator, και σχόλια από HTML."""
    soup = BeautifulSoup(περιεχομενο_html, 'html.parser')
    πληροφοριες = {'emails': [], 'generator': None, 'comments': []}
    
    # Χρήση ενός ισχυρού regex για την εύρεση διευθύνσεων email.
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', περιεχομενο_html)
    πληροφοριες['emails'] = sorted(list(set(emails)))

    meta_gen = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'generator'})
    if meta_gen and 'content' in meta_gen.attrs:
        πληροφοριες['generator'] = meta_gen['content'].strip()
    
    # ΔΙΟΡΘΩΣΗ BUG: Διόρθωση του regex για την εύρεση σχολίων HTML.
    σχολια = re.findall(r'', περιεχομενο_html, re.DOTALL)
    πληροφοριες['comments'] = [c.strip() for c in σχολια if c.strip() and len(c.strip()) < 300]
    
    return πληροφοριες

def ελεγχος_wayback_machine(domain):
    """Ελέγχει το Wayback Machine για στιγμιότυπα του domain."""
    try:
        url = f"http://web.archive.org/cdx/search/cdx?url={domain}&limit=1&output=json"
        r = requests.get(url, headers=ΚΕΦΑΛΙΔΕΣ, timeout=ΧΡΟΝΙΚΟ_ΟΡΙΟ_HTTP, verify=False)
        if r.status_code == 200 and r.text.strip():
            δεδομενα = r.json()
            if len(δεδομενα) > 1:
                return {'snapshots_found': True, 'first_snapshot': δεδομενα[1][1]}
        return {'snapshots_found': False}
    except (requests.RequestException, json.JSONDecodeError):
        return {'snapshots_found': 'Σφάλμα'}

def ελεγχος_κεφαλιδων_ασφαλειας(κεφαλιδες):
    """Ελέγχει για την παρουσία σημαντικών κεφαλίδων ασφαλείας."""
    return {h: κεφαλιδες.get(h, 'ΛΕΙΠΕΙ') for h in ΚΕΦΑΛΙΔΕΣ_ΑΣΦΑΛΕΙΑΣ}

# --- ΣΥΝΑΡΤΗΣΕΙΣ ΔΙΚΤΥΟΥ ---

def ανακτηση(url, επιτρεπονται_ανακατευθυνσεις=True, χρονικο_οριο=ΧΡΟΝΙΚΟ_ΟΡΙΟ_HTTP, εκτενες=False):
    """Wrapper για το requests.get με συνεπή χειρισμό σφαλμάτων και user-agent."""
    try:
        time.sleep(ΚΑΘΥΣΤΕΡΗΣΗ_ΑΙΤΗΜΑΤΩΝ + random.random() * 0.05)
        r = requests.get(url, headers=ΚΕΦΑΛΙΔΕΣ, timeout=χρονικο_οριο, allow_redirects=επιτρεπονται_ανακατευθυνσεις, verify=False)
        return r
    except requests.exceptions.Timeout:
        if εκτενες: print(f'[ΠΡΟΕΙΔΟΠΟΙΗΣΗ] Χρονικό όριο κατά την πρόσβαση στο {url}')
    except requests.exceptions.RequestException as e:
        if εκτενες: print(f'[ΠΡΟΕΙΔΟΠΟΙΗΣΗ] Σφάλμα αιτήματος για το {url}: {e}')
    return None

def ανιχνευση_θυρας(host, θυρα, χρονικο_οριο=1.5):
    """Ανιχνεύει μια μεμονωμένη θύρα TCP σε έναν host."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(χρονικο_οριο)
            s.connect((host, θυρα))
            return θυρα, True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return θυρα, False

def ανιχνευση_θυρων_συνδεση(host, θυρες, threads=100, χρονικο_οριο=1.5):
    """Ανιχνεύει μια λίστα από θύρες ταυτόχρονα."""
    ανοιχτες_θυρες = []
    with ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_port = {executor.submit(ανιχνευση_θυρας, host, p, χρονικο_οριο): p for p in θυρες}
        for future in as_completed(future_to_port):
            θυρα, ειναι_ανοιχτη = future.result()
            if ειναι_ανοιχτη:
                ανοιχτες_θυρες.append(θυρα)
    return sorted(ανοιχτες_θυρες)

def πληροφοριες_ssl(domain):
    """Ανακτά λεπτομέρειες πιστοποιητικού SSL για ένα domain."""
    πληροφοριες = {}
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=ΧΡΟΝΙΚΟ_ΟΡΙΟ_HTTP) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                πληροφοριες['subject'] = dict(x[0] for x in cert.get('subject', []))
                πληροφοριες['issuer'] = dict(x[0] for x in cert.get('issuer', []))
                πληροφοριες['version'] = cert.get('version')
                πληροφοριες['serialNumber'] = cert.get('serialNumber')
                πληροφοριες['notBefore'] = cert.get('notBefore')
                πληροφοριες['notAfter'] = cert.get('notAfter')
    except (socket.gaierror, socket.timeout, ssl.SSLError, ConnectionRefusedError, OSError) as e:
        πληροφοριες['error'] = str(e)
    return πληροφοριες

def επιλυση_host(ονομα):
    """Επιλύει ένα όνομα κεντρικού υπολογιστή στην κύρια διεύθυνση IP του."""
    try:
        return socket.gethostbyname(ονομα)
    except socket.gaierror:
        return None

def bruteforce_υποτομεων(domain, λιστα_λεξεων, threads=50):
    """Εκτελεί μια αναζήτηση bruteforce για υποτομείς."""
    βρεθηκαν = []
    def ελεγχος(sub):
        fqdn = f"{sub}.{domain}"
        ip = επιλυση_host(fqdn)
        if ip:
            return (fqdn, ip)
        return None

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(ελεγχος, w): w for w in λιστα_λεξεων}
        for future in as_completed(futures):
            αποτελεσμα = future.result()
            if αποτελεσμα:
                βρεθηκαν.append(αποτελεσμα)
    return βρεθηκαν

def αποπειρα_μεταφορας_ζωνης(domain):
    """Προσπαθεί να εκτελέσει μια Μεταφορά Ζώνης DNS (AXFR) έναντι των nameservers ενός domain."""
    αποτελεσματα = []
    try:
        απαντησεις = dns.resolver.resolve(domain, 'NS')
        for rdata in απαντησεις:
            ns = str(rdata.target).rstrip('.')
            try:
                ζωνη = dns.zone.from_xfr(dns.query.xfr(ns, domain, timeout=5))
                if ζωνη:
                    εγγραφες = [f"{name} {ζωνη[name].to_text()}" for name in ζωνη.nodes.keys()]
                    αποτελεσματα.append({'nameserver': ns, 'records': εγγραφες})
            except (dns.exception.FormError, dns.exception.Timeout, ConnectionRefusedError):
                continue # Σιωπηρή αποτυχία για αυτόν τον NS
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
        pass # Δεν βρέθηκαν εγγραφές NS ή άλλο σφάλμα
    return αποτελεσματα

def bruteforce_καταλογων(βασικο_url, λεξεις, threads=50, εκτενες=False):
    """Εκτελεί μια αναζήτηση bruteforce για καταλόγους και αρχεία."""
    επιτυχιες = []
    def ανιχνευση(λεξη):
        url = urljoin(βασικο_url + '/', λεξη)
        r = ανακτηση(url, εκτενες=εκτενες, επιτρεπονται_ανακατευθυνσεις=False)
        if r and r.status_code in (200, 301, 302, 403, 500):
            return (λεξη, r.status_code, r.headers.get('Location', r.url))
        return None

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(ανιχνευση, w) for w in λεξεις}
        for future in as_completed(futures):
            αποτελεσμα = future.result()
            if αποτελεσμα:
                επιτυχιες.append(αποτελεσμα)
    return επιτυχιες

# --- ΕΥΡΕΣΤΙΚΕΣ ΜΕΘΟΔΟΙ ΓΙΑ ΕΥΠΑΘΕΙΕΣ ---

def βασικος_ελεγχος_sqli_στο_url(url, εκτενες=False):
    """Προσθέτει ένα μονό εισαγωγικό σε ένα URL για να ελέγξει για βασικές ευπάθειες SQL injection."""
    if '?' not in url:
        return None
    try:
        # Δοκιμή με ένα μονό εισαγωγικό
        r = ανακτηση(url + "'", εκτενες=εκτενες)
        if r:
            κειμενο_απαντησης = r.text.lower()
            for μοτιβο in ΜΟΤΙΒΑ_ΣΦΑΛΜΑΤΩΝ_SQL:
                if μοτιβο in κειμενο_απαντησης:
                    return {'url': url, 'pattern': μοτιβο, 'trigger': "'"}
    except Exception:
        pass
    return None

def ελεγχος_αντανακλασης_xss(url, εκτενες=False):
    """Ελέγχει για reflected XSS εισάγοντας ένα payload σε παραμέτρους URL."""
    try:
        parsed = urlparse(url)
        παραμετροι_query = parse_qs(parsed.query, keep_blank_values=True)
    except ValueError:
        return []
        
    if not παραμετροι_query:
        return []
    
    ευρηματα = []
    for παραμετρος, τιμες in παραμετροι_query.items():
        αρχικη_τιμη = τιμες[0] if τιμες else ''
        # Δημιουργία αντιγράφου για τροποποίηση
        προσωρινες_παραμετροι = παραμετροι_query.copy()
        προσωρινες_παραμετροι[παραμετρος] = αρχικη_τιμη + PAYLOAD_ΔΟΚΙΜΗΣ_XSS
        
        νεο_query = urlencode(προσωρινες_παραμετροι, doseq=True)
        νεο_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, νεο_query, parsed.fragment))
        
        r = ανακτηση(νεο_url, εκτενες=εκτενες)
        # Έλεγχος αν το payload αντανακλάται στο σώμα της απάντησης.
        if r and PAYLOAD_ΔΟΚΙΜΗΣ_XSS in r.text:
            ευρηματα.append({'url': νεο_url, 'param': παραμετρος})
            
    return ευρηματα

# --- ΣΥΝΑΡΤΗΣΕΙΣ ΕΥΡΕΤΗ/ΕΠΕΞΕΡΓΑΣΤΗ HTML ---

def εε_εμφανιση_μηνυματος(μηνυμα, χρωμα='default'):
    """Εκτυπώνει ένα χρωματιστό μήνυμα στην κονσόλα."""
    χρωματα = {'red': '\033[91m', 'green': '\033[92m', 'yellow': '\033[93m', 'blue': '\033[94m', 'default': '\033[0m'}
    τελος_χρωματος = χρωματα['default']
    αρχη_χρωματος = χρωματα.get(χρωμα, τελος_χρωματος)
    print(f"{αρχη_χρωματος}{μηνυμα}{τελος_χρωματος}")

def εε_ληψη_φακελου_ιστοσελιδας(url):
    """Δημιουργεί ένα ασφαλές τοπικό όνομα καταλόγου από ένα URL."""
    parsed_url = urlparse(url)
    hostname = parsed_url.netloc.replace('www.', '')
    καθαρο_ονομα = re.sub(r'[^\w\-.]', '_', hostname) or "periexomeno_istoselidas"
    return os.path.join(ΒΑΣΙΚΟΣ_ΦΑΚΕΛΟΣ_OSINT, 'html_inspector', καθαρο_ονομα.lower())

def εε_κατεβασμα_πορου(url_πορου, τοπικος_φακελος, βασικο_url):
    """Κατεβάζει έναν μεμονωμένο πόρο (CSS, JS, εικόνα) από ένα URL."""
    if not url_πορου or url_πορου.startswith('data:'):
        return None, None
    
    try:
        απολυτο_url_πορου = urljoin(βασικο_url, url_πορου)
        parsed_asset_url = urlparse(απολυτο_url_πορου)
        
        τμημα_διαδρομης = unquote(parsed_asset_url.path)
        ονομα_αρχειου = os.path.basename(τμημα_διαδρομης) or f"asset_{abs(hash(απολυτο_url_πορου))}"
        ονομα_αρχειου = re.sub(r'[\\/:*?"<>|]', '_', ονομα_αρχειου) # Εξυγίανση ονόματος αρχείου
        
        τοπικη_διαδρομη = os.path.join(τοπικος_φακελος, ονομα_αρχειου)
        
        # Αποφυγή εκ νέου λήψης αν το αρχείο υπάρχει και έχει λογικό μέγεθος
        if os.path.exists(τοπικη_διαδρομη) and os.path.getsize(τοπικη_διαδρομη) > 0:
            return os.path.relpath(τοπικη_διαδρομη, start=os.path.dirname(τοπικος_φακελος)), απολυτο_url_πορου

        response = requests.get(απολυτο_url_πορου, stream=True, timeout=10, verify=False)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(τοπικη_διαδρομη), exist_ok=True)
        with open(τοπικη_διαδρομη, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return os.path.relpath(τοπικη_διαδρομη, start=os.path.dirname(τοπικος_φακελος)), απολυτο_url_πορου
    except requests.exceptions.RequestException:
        return None, None
    except IOError as e:
        εε_εμφανιση_μηνυματος(f"Αποτυχία αποθήκευσης πόρου {url_πορου}: {e}", 'red')
        return None, None

def εε_επεξεργασια_html_και_κατεβασμα_πορων(περιεχομενο_html, βασικο_url, φακελος_ιστοσελιδας):
    """Αναλύει το HTML, κατεβάζει όλους τους συνδεδεμένους πόρους, και ενημερώνει τους συνδέσμους ώστε να είναι τοπικοί."""
    soup = BeautifulSoup(περιεχομενο_html, 'html.parser')
    url_που_κατεβηκαν = {}
    εε_εμφανιση_μηνυματος("\nΈναρξη διαδικασίας λήψης πόρων...", 'blue')

    for ονομα_ετικετας, ονομα_χαρακτηριστικου, υποφακελος, συναρτηση_φιλτρου in ΧΑΡΤΗΣ_ΠΟΡΩΝ:
        for tag in soup.find_all(ονομα_ετικετας):
            if συναρτηση_φιλτρου and not συναρτηση_φιλτρου(tag):
                continue
            
            url_πορου = tag.get(ονομα_χαρακτηριστικου)
            if url_πορου and url_πορου not in url_που_κατεβηκαν:
                διαδρομη_υποφακελου_πορου = os.path.join(φακελος_ιστοσελιδας, υποφακελος)
                σχετικη_διαδρομη_πορου, abs_url = εε_κατεβασμα_πορου(url_πορου, διαδρομη_υποφακελου_πορου, βασικο_url)
                if σχετικη_διαδρομη_πορου:
                    νεα_διαδρομη = os.path.join(υποφακελος, os.path.basename(σχετικη_διαδρομη_πορου)).replace('\\', '/')
                    tag[ονομα_χαρακτηριστικου] = νεα_διαδρομη
                    url_που_κατεβηκαν[abs_url] = νεα_διαδρομη

    εε_εμφανιση_μηνυματος(f"Η λήψη πόρων και η τροποποίηση του HTML ολοκληρώθηκε. ({len(url_που_κατεβηκαν)} πόροι επεξεργάστηκαν)", 'green')
    return str(soup)

def εε_επεξεργασια_html_σε_editor(περιεχομενο_html):
    """Ανοίγει το περιεχόμενο HTML στον προεπιλεγμένο επεξεργαστή του συστήματος για χειροκίνητες αλλαγές."""
    if not περιεχομενο_html:
        εε_εμφανιση_μηνυματος("Δεν υπάρχει περιεχόμενο για επεξεργασία.", 'yellow')
        return None
        
    try:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8', suffix='.html') as temp_file:
            διαδρομη_προσωρινου_αρχειου = temp_file.name
            temp_file.write(περιεχομενο_html)
        
        εε_εμφανιση_μηνυματος(f"\nΆνοιγμα HTML στον {ΕΠΕΞΕΡΓΑΣΤΗΣ}. Αποθηκεύστε και κλείστε για να εφαρμοστούν οι αλλαγές.", 'yellow')
        subprocess.run([ΕΠΕΞΕΡΓΑΣΤΗΣ, διαδρομη_προσωρινου_αρχειου], check=True)
        
        with open(διαδρομη_προσωρινου_αρχειου, 'r', encoding='utf-8') as f:
            τροποποιημενο_html = f.read()
        εε_εμφανιση_μηνυματος("Το περιεχόμενο HTML ενημερώθηκε από τον επεξεργαστή.", 'green')
        return τροποποιημενο_html
    except FileNotFoundError:
        εε_εμφανιση_μηνυματος(f"Σφάλμα: Ο επεξεργαστής '{ΕΠΕΞΕΡΓΑΣΤΗΣ}' δεν βρέθηκε.", 'red')
    except subprocess.CalledProcessError:
        εε_εμφανιση_μηνυματος(f"Ο επεξεργαστής '{ΕΠΕΞΕΡΓΑΣΤΗΣ}' τερμάτισε με σφάλμα. Οι αλλαγές ενδέχεται να μην αποθηκεύτηκαν.", 'red')
    except Exception as e:
        εε_εμφανιση_μηνυματος(f"Παρουσιάστηκε σφάλμα κατά την επεξεργασία: {e}", 'red')
    finally:
        if 'διαδρομη_προσωρινου_αρχειου' in locals() and os.path.exists(διαδρομη_προσωρινου_αρχειου):
            os.remove(διαδρομη_προσωρινου_αρχειου)
    return None

def εε_αποθηκευση_html_σε_αρχειο(περιεχομενο_html, φακελος_στοχου, ονομα_αρχειου="index.html"):
    """Αποθηκεύει το τελικό περιεχόμενο HTML σε ένα αρχείο."""
    if not περιεχομενο_html:
        εε_εμφανιση_μηνυματος("Δεν υπάρχει περιεχόμενο για αποθήκευση.", 'yellow')
        return None
    os.makedirs(φακελος_στοχου, exist_ok=True)
    διαδρομη_αρχειου = os.path.join(φακελος_στοχου, ονομα_αρχειου)
    try:
        with open(διαδρομη_αρχειου, 'w', encoding='utf-8') as f:
            f.write(περιεχομενο_html)
        εε_εμφανιση_μηνυματος(f"Το HTML αποθηκεύτηκε επιτυχώς στο '{διαδρομη_αρχειου}'", 'green')
        return διαδρομη_αρχειου
    except IOError as e:
        εε_εμφανιση_μηνυματος(f"Σφάλμα αποθήκευσης αρχείου: {e}", 'red')
    return None

def εε_προεπισκοπηση_html_σε_browser(διαδρομη_αρχειου):
    """Ανοίγει το τοπικό αρχείο HTML σε έναν περιηγητή ιστού για προεπισκόπηση."""
    if not διαδρομη_αρχειου or not os.path.exists(διαδρομη_αρχειου):
        εε_εμφανιση_μηνυματος("Δεν βρέθηκε αρχείο HTML για προεπισκόπηση.", 'yellow')
        return
    
    # ΒΕΛΤΙΩΣΗ: Χρήση της βιβλιοθήκης `webbrowser` για υποστήριξη cross-platform ως εναλλακτική.
    if elegxos_paketon_termux("termux-open-url"):
        εε_εμφανιση_μηνυματος("Άνοιγμα προεπισκόπησης στον περιηγητή του Termux...", 'cyan')
        subprocess.run(['termux-open-url', f'file://{διαδρομη_αρχειου}'])
    else:
        εε_εμφανιση_μηνυματος("Άνοιγμα προεπισκόπησης στον προεπιλεγμένο περιηγητή του συστήματος...", 'cyan')
        webbrowser.open(f'file://{os.path.abspath(διαδρομη_αρχειου)}')

def εε_ανακτηση_html(url, εκτενες=False):
    """Ανακτά το ακατέργαστο περιεχόμενο HTML ενός URL."""
    response = ανακτηση(url, εκτενες=εκτενες)
    if response:
        return response.text
    if εκτενες:
        εε_εμφανιση_μηνυματος(f"Αποτυχία ανάκτησης HTML για {url}", 'red')
    return None

def εκκινηση_επεξεργαστη_html(αρχικο_url, φακελος, εκτενες=False):
    """Εκτελεί το διαδραστικό εργαλείο Επιθεωρητή και Λήψης HTML."""
    τρεχον_url = αρχικο_url
    φακελος_ιστοσελιδας = εε_ληψη_φακελου_ιστοσελιδας(τρεχον_url)
    εε_εμφανιση_μηνυματος(f"\n--- Έναρξη Διαδραστικού Επιθεωρητή HTML για {τρεχον_url} ---", 'blue')
    εε_εμφανιση_μηνυματος(f"Η τοπική διαδρομή αποθήκευσης θα είναι: {φακελος_ιστοσελιδας}", 'yellow')

    περιεχομενο_html = εε_ανακτηση_html(τρεχον_url, εκτενες)
    if not περιεχομενο_html:
        εε_εμφανιση_μηνυματος("Αποτυχία ανάκτησης του αρχικού HTML. Δεν είναι δυνατή η συνέχιση.", 'red')
        return

    while True:
        εε_εμφανιση_μηνυματος("\n--- Επιλογές Επιθεωρητή HTML ---", 'blue')
        print("1. Λήψη Πόρων & Αποθήκευση HTML (Δημιουργία/Ενημέρωση Τοπικού Αντιγράφου)")
        print("2. Επεξεργασία Τρέχοντος HTML (Άνοιγμα σε Επεξεργαστή)")
        print("3. Προεπισκόπηση Τρέχοντος HTML σε Περιηγητή")
        print("4. Εισαγωγή ΝΕΟΥ URL (Ανάκτηση νέου περιεχομένου)")
        print("5. Έξοδος από τον Επιθεωρητή HTML")

        επιλογη = input("Εισάγετε την επιλογή σας (1-5): ").strip()

        if επιλογη == '1':
            τροποποιημενο_html = εε_επεξεργασια_html_και_κατεβασμα_πορων(περιεχομενο_html, τρεχον_url, φακελος_ιστοσελιδας)
            if τροποποιημενο_html:
                περιεχομενο_html = τροποποιημενο_html
                εε_αποθηκευση_html_σε_αρχειο(περιεχομενο_html, φακελος_ιστοσελιδας)
        elif επιλογη == '2':
            τροποποιημενο_html = εε_επεξεργασια_html_σε_editor(περιεχομενο_html)
            if τροποποιημενο_html is not None:
                περιεχομενο_html = τροποποιημενο_html
                εε_αποθηκευση_html_σε_αρχειο(περιεχομενο_html, φακελος_ιστοσελιδας) # Αποθήκευση μετά την επεξεργασία
        elif επιλογη == '3':
            αποθηκευμενη_διαδρομη = εε_αποθηκευση_html_σε_αρχειο(περιεχομενο_html, φακελος_ιστοσελιδας)
            if αποθηκευμενη_διαδρομη:
                εε_προεπισκοπηση_html_σε_browser(αποθηκευμενη_διαδρομη)
        elif επιλογη == '4':
            νεο_url_εισοδος = input("Εισάγετε το νέο URL της ιστοσελίδας: ").strip()
            if νεο_url_εισοδος:
                κανονικοποιημενο_url, _ = κανονικοποιηση_στοχου(νεο_url_εισοδος)
                if κανονικοποιημενο_url:
                    τρεχον_url = κανονικοποιημενο_url
                    φακελος_ιστοσελιδας = εε_ληψη_φακελου_ιστοσελιδας(τρεχον_url)
                    νεο_html = εε_ανακτηση_html(τρεχον_url, εκτενες)
                    if νεο_html:
                        περιεχομενο_html = νεο_html
                    else:
                        εε_εμφανιση_μηνυματος("Αποτυχία ανάκτησης νέου URL. Παραμονή στο προηγούμενο περιεχόμενο.", 'red')
                else:
                    εε_εμφανιση_μηνυματος("Παρέχεται μη έγκυρο URL.", 'yellow')
        elif επιλογη == '5':
            εε_εμφανιση_μηνυματος("Έξοδος από τον επιθεωρητή HTML.", 'blue')
            break
        else:
            εε_εμφανιση_μηνυματος("Μη έγκυρη επιλογή. Παρακαλώ εισάγετε έναν αριθμό μεταξύ 1 και 5.", 'red')

# --- ΣΥΝΑΡΤΗΣΕΙΣ ΑΝΑΦΟΡΑΣ ---

def αποθηκευση_αναφορας_html(φακελος, αναφορα):
    """Δημιουργεί και αποθηκεύει μια ολοκληρωμένη αναφορά HTML με τα ευρήματα της σάρωσης."""
    προτυπο_html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Αναφορά OSINTDS για {html.escape(αναφορα.get('domain', 'N/A'))}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, Cantarell, "Helvetica Neue", sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; }}
            h1, h2, h3 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            h1 {{ font-size: 2.5em; }}
            pre {{ background-color: #ecf0f1; padding: 1em; border: 1px solid #bdc3c7; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word; font-family: "Courier New", Courier, monospace; }}
            ul, ol {{ padding-left: 20px; }}
            li {{ margin-bottom: 5px; }}
            .card {{ background-color: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        <h1>Αναφορά OSINTDS για {html.escape(αναφορα.get('domain', 'N/A'))}</h1>
        <div class="card">
            <h2>Σύνοψη</h2>
            <ul>
                <li><b>URL Στόχου:</b> {html.escape(αναφορα.get('target', 'N/A'))}</li>
                <li><b>Τελικό URL:</b> {html.escape(αναφορα.get('final_url', 'N/A'))}</li>
                <li><b>Κύρια IP:</b> {html.escape(αναφορα.get('primary_ip', 'N/A'))}</li>
                <li><b>Αντίστροφο DNS:</b> {html.escape(αναφορα.get('reverse_dns', 'N/A'))}</li>
                <li><b>Κατάσταση HTTP:</b> {html.escape(str(αναφορα.get('http_status', 'N/A')))}</li>
                <li><b>Ανοιχτές Θύρες:</b> {len(αναφορα.get('open_ports', []))}</li>
                <li><b>Υποτομείς που Βρέθηκαν:</b> {len(αναφορα.get('subdomains', []))}</li>
            </ul>
        </div>
    """
    
    ενοτητες = {
        'Πληροφορίες WHOIS': αναφορα.get('whois'),
        'Εγγραφές DNS': αναφορα.get('dns_records'),
        'Πιστοποιητικό SSL': αναφορα.get('ssl'),
        'Κεφαλίδες Ασφαλείας HTTP': αναφορα.get('security_headers'),
        'Ανοιχτές Θύρες': αναφορα.get('open_ports'),
        'Υποτομείς': αναφορα.get('subdomains'),
        'Επιτυχίες Καταλόγων/Αρχείων': αναφορα.get('dir_hits'),
        'Wayback Machine': αναφορα.get('wayback'),
        'Ανάλυση Περιεχομένου Αρχικής Σελίδας': αναφορα.get('content_info'),
        'Ανακαλυφθέντα URLs (Sitemap/Robots)': αναφορα.get('discovered_urls'),
        'Πιθανές Ενδείξεις SQL Injection': αναφορα.get('sqli_evidence'),
        'Πιθανές Αντανακλάσεις XSS': αναφορα.get('xss_reflections'),
        'Μεταφορά Ζώνης DNS (AXFR)': αναφορα.get('axfr'),
    }

    for τιτλος, δεδομενα in ενοτητες.items():
        if δεδομενα:
            προτυπο_html += f'<div class="card"><h3>{τιτλος}</h3>'
            if isinstance(δεδομενα, list) and δεδομενα:
                προτυπο_html += '<ol>'
                for στοιχειο in δεδομενα:
                    προτυπο_html += f'<li>{html.escape(str(στοιχειο))}</li>'
                προτυπο_html += '</ol>'
            elif isinstance(δεδομενα, dict):
                 προτυπο_html += f'<pre>{html.escape(json.dumps(δεδομενα, indent=2, default=str))}</pre>'
            else:
                 προτυπο_html += f'<pre>{html.escape(str(δεδομενα))}</pre>'
            προτυπο_html += '</div>'

    προτυπο_html += '</body></html>'
    αποθηκευση_κειμενου(φακελος, 'report_gr.html', προτυπο_html)

# --- ΒΟΗΘΟΣ ΑΛΛΗΛΕΠΙΔΡΑΣΗΣ ΧΡΗΣΤΗ ---

def ληψη_επιλογης_χρηστη(ερωτηση, προεπιλεγμενη_τιμη):
    """Ζητά από τον χρήστη να αποδεχτεί μια προεπιλεγμένη τιμή ή να δώσει μια νέα."""
    απαντηση = input(f'{ερωτηση} [Προεπιλογή: {προεπιλεγμενη_τιμη}] (Enter για προεπιλογή, ή πληκτρολογήστε νέα τιμή): ').strip()
    return απαντηση or προεπιλεγμενη_τιμη

# --- ΚΥΡΙΑ ΛΟΓΙΚΗ ---

def εκτελεση_ελεγχων_διαδραστικα():
    """Κύρια συνάρτηση για την εκτέλεση του σαρωτή σε διαδραστική λειτουργία."""
    print('--- Διαδραστικός Σαρωτής OSINTDS ---')
    εισοδος_στοχου = input('Εισάγετε domain ή URL στόχου (π.χ., example.com): ').strip()
    if not εισοδος_στοχου:
        print('Δεν δόθηκε στόχος. Τερματισμός.')
        return

    βαση, domain = κανονικοποιηση_στοχου(εισοδος_στοχου)
    if not domain:
        print('Μη έγκυρη μορφή στόχου. Τερματισμός.')
        return
    
    # Είσοδοι διαμόρφωσης με προεπιλογές
    try:
        threads = int(ληψη_επιλογης_χρηστη('Αριθμός threads;', ΠΡΟΕΠΙΛΕΓΜΕΝΑ_THREADS))
    except ValueError:
        threads = ΠΡΟΕΠΙΛΕΓΜΕΝΑ_THREADS

    πληρης_σαρωση_θυρων = input('Πλήρης σάρωση θυρών (1-65535); Πολύ αργή. (y/N): ').strip().lower().startswith('y')
    διαδρομη_λιστας_dir = ληψη_επιλογης_χρηστη('Διαδρομή λίστας λέξεων για καταλόγους;', ΔΙΑΔΡΟΜΗ_ΛΙΣΤΑΣ_DIR)
    διαδρομη_λιστας_sub = ληψη_επιλογης_χρηστη('Διαδρομή λίστας λέξεων για υποτομείς;', ΔΙΑΔΡΟΜΗ_ΛΙΣΤΑΣ_SUB)
    εκτενες = input('Ενεργοποίηση εκτενούς λειτουργίας για debugging; (y/N): ').strip().lower().startswith('y')
    
    μορφες_εξοδου_raw = ληψη_επιλογης_χρηστη('Μορφές εξόδου (json,html,csv);', 'json,html,csv')
    μορφες_εξοδου = {f.strip() for f in μορφες_εξοδου_raw.split(',') if f.strip()}

    λεξεις_dir = διαβασμα_λιστας_λεξεων(διαδρομη_λιστας_dir)
    λεξεις_sub = διαβασμα_λιστας_λεξεων(διαδρομη_λιστας_sub)

    print('\nΑΠΟΠΟΙΗΣΗ ΕΥΘΥΝΗΣ: Σαρώνετε μόνο στόχους που σας ανήκουν ή έχετε ρητή άδεια να ελέγξετε.')
    print('Έναρξη σάρωσης OSINT. Αυτό μπορεί να πάρει λίγο χρόνο...')

    αναφορα, φακελος = εκτελεση_ελεγχων(
        στοχος=εισοδος_στοχου,
        threads=threads,
        πληρης_σαρωση_θυρων=πληρης_σαρωση_θυρων,
        μορφες_εξοδου=μορφες_εξοδου,
        λεξεις_dir=λεξεις_dir,
        λεξεις_sub=λεξεις_sub,
        εκτενες=εκτενες
    )

    if not αναφορα:
        print("\nΗ σάρωση δεν μπόρεσε να ολοκληρωθεί.")
        return
        
    print("\n" + "="*50)
    print("--- Επιθεωρητής/Επεξεργαστής HTML μετά τη Σάρωση ---")
    if input("Εκτέλεση Διαδραστικού Εργαλείου Λήψης/Επεξεργασίας HTML στο URL του στόχου; (y/N): ").strip().lower().startswith('y'):
        τελικο_url = αναφορα.get('final_url') or εισοδος_στοχου
        if 'unreachable' not in str(αναφορα.get('http_status', '')):
            εκκινηση_επεξεργαστη_html(τελικο_url, φακελος, εκτενες)
        else:
            print("[ΠΡΟΕΙΔΟΠΟΙΗΣΗ] Ο στόχος δεν ήταν προσβάσιμος, παράλειψη του Επιθεωρητή HTML.")
    print("="*50)

def εκτελεση_ελεγχων(στοχος, threads=ΠΡΟΕΠΙΛΕΓΜΕΝΑ_THREADS, πληρης_σαρωση_θυρων=False, μορφες_εξοδου=('json','html','csv'), 
               λεξεις_dir=None, λεξεις_sub=None, εκτενες=False):
    
    βαση, domain = κανονικοποιηση_στοχου(στοχος)
    φακελος = δημιουργια_φακελων(domain)
    διαδρομη_αναφορας = os.path.join(φακελος, 'report.json')
    αναφορα = {'target': στοχος, 'domain': domain, 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')}

    # Λογική Συνέχισης Σάρωσης
    if os.path.exists(διαδρομη_αναφορας):
        if input(f"Βρέθηκε υπάρχουσα αναφορά για το {domain}. Συνέχιση σάρωσης; (Y/n): ").strip().lower() != 'n':
            try:
                with open(διαδρομη_αναφορας, 'r', encoding='utf-8') as f:
                    αναφορα.update(json.load(f))
                print('[ΠΛΗΡΟΦΟΡΙΑ] Συνέχιση σάρωσης από υπάρχουσα αναφορά.')
            except (json.JSONDecodeError, IOError) as e:
                print(f'[ΠΡΟΕΙΔΟΠΟΙΗΣΗ] Δεν ήταν δυνατή η φόρτωση της υπάρχουσας αναφοράς ({e}). Έναρξη από την αρχή.')

    def εκτελεση_σταδιου(αριθμος_σταδιου, ονομα, κλειδι, συναρτηση, *args, **kwargs):
        """Βοηθητική συνάρτηση για την εκτέλεση και αναφορά κάθε σταδίου σάρωσης."""
        print(f"[ΣΤΑΔΙΟ {αριθμος_σταδιου}/13] {ονομα}...")
        if αναφορα.get(κλειδι) is None:
            αναφορα[κλειδι] = συναρτηση(*args, **kwargs)
            αποθηκευση_checkpoint(φακελος, αναφορα)
        else:
            print(f"[ΠΛΗΡΟΦΟΡΙΑ] Βρέθηκε αποθηκευμένο αποτέλεσμα για '{ονομα}'. Παράλειψη.")

    # --- ΣΤΑΔΙΟ 1: Αρχική Ανάκτηση HTTP ---
    print(f"[ΣΤΑΔΙΟ 1/13] Έλεγχος βασικού URL: {βαση}")
    if αναφορα.get('http_status') is None or 'unreachable' in str(αναφορα.get('http_status')):
        r = ανακτηση(βαση, εκτενες=εκτενες)
        if not r:
            αναφορα['http_status'] = 'unreachable'
            αποθηκευση_checkpoint(φακελος, αναφορα)
            print('[ΣΦΑΛΜΑ] Ο στόχος δεν είναι προσβάσιμος.')
            return None, None
        
        αναφορα['http_status'] = f"{r.status_code} {r.reason}"
        αναφορα['final_url'] = r.url
        αναφορα['headers'] = dict(r.headers)
        αποθηκευση_checkpoint(φακελος, αναφορα)
    else:
        # Ανάκτηση ξανά για να έχουμε περιεχόμενο για άλλα στάδια
        r = ανακτηση(αναφορα.get('final_url', βαση), εκτενες=εκτενες)
        if not r:
            print('[ΣΦΑΛΜΑ] Ο στόχος από την αναφορά δεν είναι πλέον προσβάσιμος.')
            return None, None

    # --- ΥΠΟΛΟΙΠΑ ΣΤΑΔΙΑ ---
    εκτελεση_σταδιου(2, "Έλεγχος κεφαλίδων ασφαλείας HTTP", 'security_headers', ελεγχος_κεφαλιδων_ασφαλειας, r.headers)
    εκτελεση_σταδιου(3, "Έλεγχος πληροφοριών WHOIS", 'whois', ληψη_πληροφοριων_whois, domain)
    εκτελεση_σταδιου(4, "Επίλυση DNS και Αντίστροφου DNS", 'dns_records', επιλυση_ολων_των_dns, domain)
    if 'dns_records' in αναφορα and αναφορα['dns_records'].get('A'):
        αναφορα['primary_ip'] = αναφορα['dns_records']['A'][0]
        εκτελεση_σταδιου(4, "Εκτέλεση Αντίστροφου DNS", 'reverse_dns', αντιστροφη_αναζητηση_dns, αναφορα['primary_ip'])
    
    εκτελεση_σταδιου(5, "Έλεγχος Wayback Machine", 'wayback', ελεγχος_wayback_machine, domain)
    εκτελεση_σταδιου(6, "Έλεγχος πιστοποιητικού SSL", 'ssl', πληροφοριες_ssl, domain)
    εκτελεση_σταδιου(7, "Ανάλυση περιεχομένου αρχικής σελίδας", 'content_info', εξαγωγη_πληροφοριων_περιεχομενου, r.text)

    # Στάδιο 8: Sitemap/Robots και συλλογή URL
    εκτελεση_σταδιου(8, "Αναζήτηση sitemap/robots.txt", 'discovered_urls', lambda: sorted(list(set(
        re.findall(r'<loc>([^<]+)</loc>', sm.text, re.I)
        for sm_url in (
            [line.split(':', 1)[1].strip() for line in (ανακτηση(urljoin(βαση, '/robots.txt')) or type('',(object,),{'text':''})()).text.splitlines() if line.lower().startswith('sitemap:')]
            or [urljoin(βαση, '/sitemap.xml')]
        )
        if (sm := ανακτηση(sm_url)) and sm.status_code == 200
    ))))
    
    εκτελεση_σταδιου(9, "Εκτέλεση απαρίθμησης υποτομέων", 'subdomains', bruteforce_υποτομεων, domain, λεξεις_sub, threads=threads)
    εκτελεση_σταδιου(10, "Απόπειρα μεταφοράς ζώνης DNS", 'axfr', αποπειρα_μεταφορας_ζωνης, domain)
    
    # Στάδιο 11: Θύρες
    λιστα_θυρων = list(range(1, 65536)) if πληρης_σαρωση_θυρων else [21, 22, 25, 53, 80, 110, 143, 443, 465, 587, 993, 995, 3306, 5432, 8000, 8080, 8443]
    εκτελεση_σταδιου(11, "Εκτέλεση ανίχνευσης θυρών", 'open_ports', ανιχνευση_θυρων_συνδεση, αναφορα.get('primary_ip', domain), λιστα_θυρων, threads=max(100, threads))
    
    εκτελεση_σταδιου(12, "Εκτέλεση brute-force καταλόγων", 'dir_hits', bruteforce_καταλογων, βαση, λεξεις_dir, threads=threads, εκτενες=εκτενες)

    # Στάδιο 13: Ευρετικές Μέθοδοι για Ευπάθειες
    print("[ΣΤΑΔΙΟ 13/13] Εκτέλεση ευρετικών μεθόδων για ευπάθειες...")
    if αναφορα.get('sqli_evidence') is None or αναφορα.get('xss_reflections') is None:
        ολοι_οι_συνδεσμοι = set(αναφορα.get('discovered_urls', []))
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            πληρες_url = urljoin(βαση, a['href'])
            if urlparse(πληρες_url).hostname == domain:
                ολοι_οι_συνδεσμοι.add(πληρες_url)
        
        συνδεσμοι_προς_σαρωση = list(ολοι_οι_συνδεσμοι)[:400]
        print(f'[ΠΛΗΡΟΦΟΡΙΑ] Εκτέλεση ευρετικών SQLi/XSS σε {len(συνδεσμοι_προς_σαρωση)} URLs...')
        
        sqli, xss = [], []
        with ThreadPoolExecutor(max_workers=threads) as executor:
            sql_futures = {executor.submit(βασικος_ελεγχος_sqli_στο_url, u, εκτενες): u for u in συνδεσμοι_προς_σαρωση if '?' in u}
            xss_futures = {executor.submit(ελεγχος_αντανακλασης_xss, u, εκτενες): u for u in συνδεσμοι_προς_σαρωση if '?' in u}
            
            for f in as_completed(sql_futures):
                if res := f.result(): sqli.append(res)
            for f in as_completed(xss_futures):
                if res := f.result(): xss.extend(res)
        
        αναφορα['sqli_evidence'] = sqli
        αναφορα['xss_reflections'] = xss
        αποθηκευση_checkpoint(φακελος, αναφορα)

    # --- ΤΕΛΙΚΗ Αποθήκευση Εξόδων και Σύνοψη ---
    print('\n[ΤΕΛΙΚΟ] Δημιουργία τελικών αρχείων αναφοράς...')
    if 'json' in μορφες_εξοδου:
        αποθηκευση_checkpoint(φακελος, αναφορα) 
    if 'csv' in μορφες_εξοδου:
        if αναφορα.get('subdomains'):
            αποθηκευση_csv(φακελος, 'subdomains.csv', αναφορα['subdomains'], κεφαλιδες=['Υποτομέας', 'IP'])
        if αναφορα.get('dir_hits'):
            αποθηκευση_csv(φακελος, 'dirs.csv', αναφορα['dir_hits'], κεφαλιδες=['Διαδρομή', 'Κατάσταση', 'Τελικό URL'])
    if 'html' in μορφες_εξοδου:
        αποθηκευση_αναφορας_html(φακελος, αναφορα)

    print('\n--- Σύνοψη Ολοκλήρωσης Σάρωσης ---')
    print(f"Στόχος: {αναφορα['target']}")
    print(f"Κύρια IP: {αναφορα.get('primary_ip', 'N/A')}")
    print(f"Κατάσταση HTTP: {αναφορα['http_status']}")
    print(f"Ανοιχτές θύρες ({len(αναφορα.get('open_ports',[]))} βρέθηκαν): {αναφορα.get('open_ports', 'N/A')}")
    print(f"Υποτομείς που βρέθηκαν: {len(αναφορα.get('subdomains',[]))}")
    print(f"Επιτυχίες καταλόγων: {len(αναφορα.get('dir_hits',[]))}")
    print(f"Πιθανές ενδείξεις SQLi: {len(αναφορα.get('sqli_evidence',[]))}")
    print(f"Πιθανές ενδείξεις XSS: {len(αναφορα.get('xss_reflections',[]))}")
    print(f'\nΤα αρχεία εξόδου αποθηκεύτηκαν στο: {φακελος}')
    
    return αναφορα, φακελος

if __name__ == '__main__':
    εκτελεση_ελεγχων_διαδραστικα()