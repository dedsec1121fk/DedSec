#!/usr/bin/env python3

import os, sys, json, time, re, socket, subprocess, random, threading, hashlib
import asyncio, aiofiles, aiodns, concurrent.futures
import curses, ssl, urllib3
from dataclasses import dataclass, asdict, field
from urllib.parse import urlparse, urljoin, parse_qs, urlencode, urlunparse, parse_qsl
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from pathlib import Path
import xml.etree.ElementTree as ET

# ---------------- Αυτόματη εγκατάσταση εξαρτήσεων ----------------
REQUIRED = ["httpx", "rich", "dnspython", "beautifulsoup4", "jinja2", "requests",
            "pyopenssl", "cryptography", "colorama", "tqdm", "termcolor", "yaml",
            "python-whois", "shodan", "censys", "waybackpy"]

def ensure_deps():
    missing = []
    for p in REQUIRED:
        try:
            if p == "dnspython": __import__("dns")
            elif p == "beautifulsoup4": __import__("bs4")
            elif p == "python-whois": __import__("whois")
            elif p == "waybackpy": __import__("waybackpy")
            else: __import__(p)
        except ImportError:
            missing.append(p)
    if missing:
        print(f"[*] Εγκατάσταση ελλειπόντων εξαρτήσεων: {', '.join(missing)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-U"] + missing)

ensure_deps()

import httpx
import dns.resolver
import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.syntax import Syntax
from colorama import init, Fore, Back, Style

console = Console()
init(autoreset=True)

# ---------------- Βελτιωμένη Διαμόρφωση & Payloads ----------------

# Εκτεταμένα τεχνολογικά αποτυπώματα με εκδόσεις
TECH_SIGS = {
    "WordPress": {
        "body": ["wp-content", "wp-includes", "wp-json", "/wp-admin/"],
        "headers": ["x-powered-by: wordpress", "x-wp-total"],
        "version_regex": r"wordpress (\d+\.\d+(?:\.\d+)?)|wp-(\d+\.\d+(?:\.\d+)?)"
    },
    "Django": {
        "body": ["csrfmiddlewaretoken", "Django", "csrf_token"],
        "headers": ["x-frame-options: DENY", "server: WSGIServer"],
        "version_regex": r"django/(\d+\.\d+(?:\.\d+)?)"
    },
    "Laravel": {
        "body": ["laravel_session", "mix/"],
        "headers": ["x-powered-by: laravel"],
        "version_regex": r"laravel (\d+\.\d+(?:\.\d+)?)"
    },
    "React": {
        "body": ["react-dom", "data-reactroot", "__reactInternalInstance"],
        "headers": [],
        "version_regex": r"react@(\d+\.\d+(?:\.\d+)?)"
    },
    "Vue.js": {
        "body": ["data-v-", "vue.min.js", "__vue__"],
        "headers": [],
        "version_regex": r"vue@(\d+\.\d+(?:\.\d+)?)"
    },
    "Apache": {
        "body": [],
        "headers": ["server: apache", "apache"],
        "version_regex": r"apache/(\d+\.\d+(?:\.\d+)?)"
    },
    "Nginx": {
        "body": [],
        "headers": ["server: nginx"],
        "version_regex": r"nginx/(\d+\.\d+(?:\.\d+)?)"
    },
    "Node.js": {
        "body": [],
        "headers": ["x-powered-by: express"],
        "version_regex": r"node/(\d+\.\d+(?:\.\d+)?)"
    },
    "Joomla": {
        "body": ["joomla", "media/jui/", "templates/system/"],
        "headers": ["x-content-encoded-by: joomla"],
        "version_regex": r"joomla! (\d+\.\d+(?:\.\d+)?)"
    },
    "Drupal": {
        "body": ["drupal", "sites/all/", "/core/"],
        "headers": ["x-generator: drupal"],
        "version_regex": r"drupal (\d+\.\d+(?:\.\d+)?)"
    }
}

# Εκτεταμένη ανίχνευση Subdomain Takeover
TAKEOVER_SIGS = {
    "GitHub Pages": ["There is no GitHub Pages site here", "404 File not found"],
    "Heroku": ["Heroku | No such app", "herokucdn.com/error-pages/no-such-app.html"],
    "AWS S3": ["NoSuchBucket", "The specified bucket does not exist"],
    "Azure": ["Azure App Service", "The resource you are looking for has been removed"],
    "Zendesk": ["Help Center Closed", "This help center no longer exists"],
    "Shopify": ["Sorry, this shop is currently unavailable"],
    "Google Cloud": ["The requested URL was not found on this server"],
    "DigitalOcean": ["Domain uses DO name servers with no records in DO."],
    "Fastly": ["Fastly error: unknown domain"],
    "Cloudflare": ["cloudflare.com", "Error 1001"]
}

# Εκτεταμένη λίστα θυρών με ανίχνευση υπηρεσιών
COMMON_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    111: "RPC",
    135: "MSRPC",
    139: "NetBIOS",
    143: "IMAP",
    443: "HTTPS",
    445: "SMB",
    993: "IMAPS",
    995: "POP3S",
    1433: "MSSQL",
    1521: "Oracle",
    2049: "NFS",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    5900: "VNC",
    5985: "WinRM",
    6379: "Redis",
    8000: "HTTP Alt",
    8080: "HTTP Proxy",
    8443: "HTTPS Alt",
    9000: "Hadoop",
    9200: "Elasticsearch",
    27017: "MongoDB",
    28017: "MongoDB HTTP"
}

ΕΥΑΙΣΘΗΤΑ_ΑΡΧΕΙΑ = [
    # Αρχεία διαμόρφωσης
    "/.env", "/.env.local", "/.env.production", "/.env.development",
    "/config.json", "/config.php", "/configuration.php", "/config.yml",
    "/config.yaml", "/settings.py", "/web.config", "/application.ini",
    
    # Έλεγχος εκδόσεων
    "/.git/config", "/.git/HEAD", "/.git/logs/HEAD", "/.git/index",
    "/.svn/entries", "/.hg/store/00manifest.i",
    
    # Αρχεία αντιγράφων ασφαλείας
    "/backup.sql", "/database.sql", "/dump.sql", "/backup.zip",
    "/backup.tar.gz", "/backup.rar", "/site.bak", "/www.rar",
    
    # Αρχεία καταγραφής
    "/logs/access.log", "/error.log", "/debug.log", "/trace.log",
    
    # Διασυνδέσεις διαχείρισης
    "/admin/", "/administrator/", "/wp-admin/", "/manager/",
    "/login/", "/cpanel/", "/webmail/", "/phpmyadmin/",
    
    # Σημεία πρόσβασης API
    "/api/", "/graphql", "/rest/", "/v1/", "/v2/", "/swagger/",
    "/docs/", "/openapi.json", "/api-docs/",
    
    # Διάφορα
    "/phpinfo.php", "/test.php", "/info.php", "/server-status",
    "/.DS_Store", "/thumbs.db", "/crossdomain.xml", "/clientaccesspolicy.xml",
    "/sitemap.xml", "/robots.txt", "/humans.txt"
]

# Βελτιωμένα μοτίβα μυστικών με καλύτερη επικύρωση
SECRET_REGEX = {
    "Κλειδί Google API": r"AIza[0-9A-Za-z\-_]{35}",
    "Google OAuth": r"ya29\.[0-9A-Za-z\-_]+",
    "Κλειδί Πρόσβασης AWS": r"AKIA[0-9A-Z]{16}",
    "Μυστικό Κλειδί AWS": r"(?i)aws_secret_access_key[=:]\s*['\"]?([A-Za-z0-9\/+=]{40})['\"]?",
    "Κλειδί API Stripe": r"(?i)stripe_(?:api|secret|private)_key[=:]\s*['\"]?(sk_(?:live|test)_[0-9a-zA-Z]{24})['\"]?",
    "Token Slack": r"xox[baprs]-([0-9a-zA-Z]{10,48})",
    "Token GitHub": r"ghp_[a-zA-Z0-9]{36}",
    "GitHub OAuth": r"github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}",
    "JWT": r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}",
    "Ιδιωτικό Κλειδί SSH": r"-----BEGIN (?:RSA|DSA|EC|OPENSSH) PRIVATE KEY-----",
    "Ιδιωτικό Κλειδί PGP": r"-----BEGIN PGP PRIVATE KEY BLOCK-----",
    "Token Πρόσβασης Facebook": r"EAACEdEose0cBA[0-9A-Za-z]+",
    "Κλειδί API Twitter": r"(?i)twitter_api_(?:key|secret)[=:]\s*['\"]?([a-zA-Z0-9]{25,50})['\"]?",
    "Μυστικό Πελάτη LinkedIn": r"(?i)linkedin_client_secret[=:]\s*['\"]?([a-zA-Z0-9]{16})['\"]?",
    "Κλειδί API Mailgun": r"key-[0-9a-f]{32}",
    "Κλειδί API Twilio": r"SK[0-9a-fA-F]{32}",
    "Token Πρόσβασης Square": r"sq0atp-[0-9A-Za-z\-_]{22}",
    "Μυστικό Βάσης Δεδομένων Firebase": r"(?i)firebase_database_secret[=:]\s*['\"]?([a-zA-Z0-9]{40})['\"]?"
}

# Επικεφαλίδες για έλεγχο ασφαλιστικών παραμετροποιήσεων
SECURITY_HEADERS = [
    "Content-Security-Policy",
    "X-Frame-Options",
    "X-Content-Type-Options",
    "X-XSS-Protection",
    "Strict-Transport-Security",
    "Referrer-Policy",
    "Permissions-Policy",
    "Cache-Control"
]

# Κοινά μοτίβα ευπαθειών
VULN_PATTERNS = {
    "SQL Injection": [
        r"(?i)sql syntax.*mysql",
        r"(?i)warning.*mysql",
        r"(?i)unclosed quotation mark",
        r"(?i)you have an error in your sql syntax"
    ],
    "XSS": [
        r"<script>.*</script>",
        r"alert\(.*\)",
        r"onerror=.*",
        r"javascript:"
    ],
    "Path Traversal": [
        r"\.\./\.\./",
        r"etc/passwd",
        r"windows/win\.ini"
    ],
    "Command Injection": [
        r"(?i)(?:cmd|sh|bash|powershell)\.exe",
        r"(?i)(?:ping|nslookup|whoami)\s",
        r"\$\{IFS\}",
        r";\s*(?:ls|cat|id)"
    ]
}

# ---------------- Μοντέλα ----------------
@dataclass
class Εύρημα:
    κατηγορία: str
    σοβαρότητα: str  # Κρίσιμη, Υψηλή, Μέτρια, Χαμηλή, Πληροφορία
    url: str
    λεπτομέρειες: str = ""
    χρονική_σήμανση: str = ""
    βεβαιότητα: str = "Μέτρια"  # Χαμηλή, Μέτρια, Υψηλή
    απόδειξη_εκμετάλλευσης: str = ""
    αποκατάσταση: str = ""
    
    def __post_init__(self):
        self.χρονική_σήμανση = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@dataclass
class Τεχνολογία:
    όνομα: str
    έκδοση: str = ""
    βεβαιότητα: int = 0
    τοποθεσίες: List[str] = field(default_factory=list)

# ---------------- Εκτεταμένος Σαρωτής ----------------
class ΣύνθετοςΣαρωτής:
    def __init__(self, στόχος: str, κατάλογος_εξόδου: str, διαμόρφωση: dict):
        self.στόχος = στόχος if στόχος.startswith("http") else "https://" + στόχος
        parsed = urlparse(self.στόχος)
        self.τομέας = parsed.netloc
        self.βασική_url = f"{parsed.scheme}://{parsed.netloc}"
        self.κατάλογος_εξόδου = κατάλογος_εξόδου
        self.διαμόρφωση = διαμόρφωση
        
        self.ευρήματα = []
        self.τεχνολογίες = []
        self.js_σημεία_πρόσβασης = set()
        self.ανοιχτές_θύρες = []
        self.υποτομείς = set()
        self.διερευνημένα_url = set()
        self.ευαίσθητα_αρχεία = []
        self.ευρεθέντα_μυστικά = []
        
        # Βελτιστοποίηση απόδοσης
        self.όρια = httpx.Limits(
            max_connections=διαμόρφωση.get('concurrency', 50),
            max_keepalive_connections=20
        )
        self.επικεφαλίδες = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # Δημιουργία δομής εξόδου
        os.makedirs(self.κατάλογος_εξόδου, exist_ok=True)
        os.makedirs(os.path.join(self.κατάλογος_εξόδου, "screenshots"), exist_ok=True)
        os.makedirs(os.path.join(self.κατάλογος_εξόδου, "data"), exist_ok=True)
        
        # Αρχικοποίηση μετρητών
        self.στατιστικά = {
            "αποστολές_αιτήσεων": 0,
            "απαντήσεις_που_λήφθηκαν": 0,
            "λάθη": 0,
            "χρόνος_εκκίνησης": datetime.now()
        }

    def καταγραφή(self, εύρημα: Εύρημα):
        """Καταγραφή ευρημάτων με μορφοποίηση rich"""
        self.ευρήματα.append(asdict(εύρημα))
        
        # Χρωματικός κωδικοποίηση για κονσόλα
        χάρτης_χρωμάτων = {
            "Κρίσιμη": "red",
            "Υψηλή": "orange1",
            "Μέτρια": "yellow",
            "Χαμηλή": "green",
            "Πληροφορία": "blue"
        }
        
        console.print(f"[{χάρτης_χρωμάτων.get(εύρημα.σοβαρότητα, 'white')}][{εύρημα.σοβαρότητα}][/{χάρτης_χρωμάτων.get(εύρημα.σοβαρότητα, 'white')}] "
                     f"{εύρημα.κατηγορία}: {εύρημα.url}")
        if εύρημα.λεπτομέρειες:
            console.print(f"   Λεπτομέρειες: {εύρημα.λεπτομέρειες}")
        
        # Καταγραφή σε αρχείο
        αρχείο_καταγραφής = os.path.join(self.κατάλογος_εξόδου, "ευρήματα.jsonl")
        with open(αρχείο_καταγραφής, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(εύρημα), ensure_ascii=False) + "\n")
        
        # Επίσης καταγραφή σε CSV για ευκολότερη ανάλυση
        αρχείο_csv = os.path.join(self.κατάλογος_εξόδου, "ευρήματα.csv")
        if not os.path.exists(αρχείο_csv):
            with open(αρχείο_csv, "w", encoding="utf-8") as f:
                f.write("χρονική_σήμανση,σοβαρότητα,κατηγορία,url,λεπτομέρειες,βεβαιότητα\n")
        
        with open(αρχείο_csv, "a", encoding="utf-8") as f:
            f.write(f"{εύρημα.χρονική_σήμανση},{εύρημα.σοβαρότητα},{εύρημα.κατηγορία},{εύρημα.url},{εύρημα.λεπτομέρειες},{εύρημα.βεβαιότητα}\n")

    # --- Βελτιωμένες Ενότητες ---

    async def έλεγχος_ασφαλιστικών_επικεφαλίδων(self, client, url, headers):
        """Έλεγχος για ελλειπόμενες ασφαλιστικές επικεφαλίδες"""
        ελλείπουσες = []
        for επικεφαλίδα in SECURITY_HEADERS:
            if επικεφαλίδα not in headers:
                ελλείπουσες.append(επικεφαλίδα)
        
        if ελλείπουσες:
            self.καταγραφή(Εύρημα(
                "Ελλείπουσες_Ασφαλιστικές_Επικεφαλίδες", "Μέτρια", url,
                f"Ελλείπουσες επικεφαλίδες: {', '.join(ελλείπουσες)}",
                αποκατάσταση="Εφαρμόστε τις ελλείπουσες ασφαλιστικές επικεφαλίδες"
            ))

    async def ανίχνευση_στοίβας_τεχνολογιών(self, client, url, κείμενο, headers):
        """Βελτιωμένη ανίχνευση τεχνολογιών με αναγνώριση εκδόσεων"""
        ανιχνευμένες = []
        h_str = json.dumps(dict(headers)).lower()
        
        for τεχνολογία, υπογραφές in TECH_SIGS.items():
            τεχνολογία_βρέθηκε = False
            έκδοση = ""
            
            # Έλεγχος επικεφαλίδων
            for h in υπογραφές.get('headers', []):
                if h.lower() in h_str:
                    τεχνολογία_βρέθηκε = True
            
            # Έλεγχος σώματος
            for b in υπογραφές.get('body', []):
                if b in κείμενο:
                    τεχνολογία_βρέθηκε = True
            
            # Εξαγωγή έκδοσης εάν είναι δυνατή
            if τεχνολογία_βρέθηκε and 'version_regex' in υπογραφές:
                ταίριασμα = re.findall(υπογραφές['version_regex'], κείμενο, re.IGNORECASE)
                if ταίριασμα:
                    έκδοση = ταίριασμα[0][0] if isinstance(ταιριασμα[0], tuple) else ταίριασμα[0]
            
            if τεχνολογία_βρέθηκε:
                ανιχνευμένες.append((τεχνολογία, έκδοση))
        
        # Αποθήκευση τεχνολογιών
        for τεχνολογία, έκδοση in ανιχνευμένες:
            self.τεχνολογίες.append({
                "όνομα": τεχνολογία,
                "έκδοση": έκδοση,
                "βεβαιότητα": "Υψηλή" if έκδοση else "Μέτρια"
            })
        
        if ανιχνευμένες:
            τεχνολογία_συμβολοσειρά = ", ".join([f"{t} {v}" if v else t for t, v in ανιχνευμένες])
            self.καταγραφή(Εύρημα("Στοίβα_Τεχνολογιών", "Πληροφορία", url, f"Ανιχνεύθηκε: {τεχνολογία_συμβολοσειρά}"))

    async def βελτιωμένη_σάρωση_θυρών(self):
        """Βελτιωμένη σάρωση θυρών με ανίχνευση υπηρεσιών και λήψη banner"""
        ανοιχτές_θύρες = []
        
        async def έλεγχος_θύρας(θύρα):
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.τομέας, θύρα),
                    timeout=2.0
                )
                
                # Προσπάθεια λήψης banner
                writer.write(b"\r\n\r\n")
                await writer.drain()
                try:
                    banner = await asyncio.wait_for(reader.read(1024), timeout=1.0)
                    banner = banner.decode('utf-8', errors='ignore').strip()
                except:
                    banner = ""
                
                υπηρεσία = COMMON_PORTS.get(θύρα, "Άγνωστη")
                ανοιχτές_θύρες.append({
                    "θύρα": θύρα,
                    "υπηρεσία": υπηρεσία,
                    "banner": banner[:100] if banner else ""
                })
                
                writer.close()
                await writer.wait_closed()
                
                # Καταγραφή ευρήματος
                if banner:
                    self.καταγραφή(Εύρημα(
                        "Ανοιχτή_Θύρα", "Χαμηλή", f"{self.τομέας}:{θύρα}",
                        f"Υπηρεσία: {υπηρεσία}, Banner: {banner[:50]}..."
                    ))
                else:
                    self.καταγραφή(Εύρημα(
                        "Ανοιχτή_Θύρα", "Πληροφορία", f"{self.τομέας}:{θύρα}",
                        f"Υπηρεσία: {υπηρεσία}"
                    ))
                    
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                pass
            except Exception as e:
                pass
        
        # Σάρωση κοινών θυρών
        θύρες = list(COMMON_PORTS.keys())
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Σάρωση θυρών...", total=len(θύρες))
            
            # Επεξεργασία σε ομάδες για ταχύτητα
            μέγεθος_ομάδας = 100
            for i in range(0, len(θύρες), μέγεθος_ομάδας):
                ομάδα = θύρες[i:i + μέγεθος_ομάδας]
                await asyncio.gather(*[έλεγχος_θύρας(p) for p in ομάδα])
                progress.update(task, advance=len(ομάδα))
        
        self.ανοιχτές_θύρες = ανοιχτές_θύρες
        return ανοιχτές_θύρες

    async def έλεγχος_ανάληψης_υποτομέα(self):
        """Βελτιωμένη ανίχνευση ανάληψης υποτομέα"""
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = ['8.8.8.8', '1.1.1.1']  # Χρήση αξιόπιστων DNS
            
            try:
                answers = resolver.resolve(self.τομέας, 'CNAME')
                for answer in answers:
                    cname = str(answer.target).rstrip('.')
                    
                    # Έλεγχος αν το CNAME δείχνει σε γνωστές ευάλωτες υπηρεσίες
                    ευάλωτοι_τομείς = [
                        'github.io', 'herokuapp.com', 'aws.amazon.com',
                        'azurewebsites.net', 'cloudapp.net', 's3.amazonaws.com'
                    ]
                    
                    if any(ευάλωτος_τομέας in cname for ευάλωτος_τομέας in ευάλωτοι_τομείς):
                        # Δοκιμή του τομέα
                        async with httpx.AsyncClient(verify=False, timeout=10) as client:
                            try:
                                resp = await client.get(self.στόχος)
                                resp_text = resp.text.lower()
                                
                                for παρόχος, αποτυπώματα in TAKEOVER_SIGS.items():
                                    for αποτύπωμα in αποτυπώματα:
                                        if αποτύπωμα.lower() in resp_text:
                                            self.καταγραφή(Εύρημα(
                                                "Ανάληψη_Υποτομέα", "Κρίσιμη", self.στόχος,
                                                f"Πάροχος: {παρόχος}, CNAME: {cname}",
                                                απόδειξη_εκμετάλλευσης=f"Το CNAME δείχνει στο {cname} που είναι ευάλωτο σε ανάληψη",
                                                αποκατάσταση=f"Αφαιρέστε την εγγραφή CNAME ή διεκδικήστε την υπηρεσία"
                                            ))
                                            return
                            except Exception:
                                pass
                                
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                pass
                
        except Exception as e:
            pass

    async def εξαγωγή_js_σημείων_πρόσβασης(self, client, url, html_περιεχόμενο):
        """Βελτιωμένη ανάλυση JS με ανάλυση AST (απλοποιημένη)"""
        soup = BeautifulSoup(html_περιεχόμενο, 'html.parser')
        
        # Εύρεση όλων των ετικετών script
        scripts = soup.find_all('script')
        
        for script in scripts:
            src = script.get('src')
            if src:
                js_url = urljoin(url, src)
                try:
                    response = await client.get(js_url)
                    if response.status_code == 200:
                        js_περιεχόμενο = response.text
                        
                        # Εξαγωγή σημείων πρόσβασης με διάφορα μοτίβα
                        μοτίβα = [
                            r'(?:["\'])(\/[a-zA-Z0-9_\-\.\/]+\.(?:json|api|rest|graphql))["\']',
                            r'(?:url|endpoint|api)[:=]\s*["\']([^"\']+)["\']',
                            r'fetch\(["\']([^"\']+)["\']',
                            r'axios\.(?:get|post|put|delete)\(["\']([^"\']+)["\']',
                            r'\.ajax\([^{]*url:\s*["\']([^"\']+)["\']'
                        ]
                        
                        όλα_τα_σημεία_πρόσβασης = set()
                        for μοτίβο in μοτίβα:
                            ταίριασμα = re.findall(μοτίβο, js_περιεχόμενο, re.IGNORECASE)
                            for match in ταίριασμα:
                                if isinstance(match, tuple):
                                    match = match[0]
                                if match.startswith('/') or match.startswith('http'):
                                    πλήρη_url = urljoin(js_url, match)
                                    όλα_τα_σημεία_πρόσβασης.add(πλήρη_url)
                        
                        # Φιλτράρισμα ενδιαφέροντων σημείων πρόσβασης
                        ενδιαφέροντα = [ep for ep in όλα_τα_σημεία_πρόσβασης if any(
                            λέξη_κλειδί in ep.lower() for λέξη_κλειδί in 
                            ['api', 'admin', 'auth', 'token', 'user', 'account', 'config']
                        )]
                        
                        if ενδιαφέροντα:
                            self.js_σημεία_πρόσβασης.update(ενδιαφέροντα)
                            δείγμα = list(ενδιαφέροντα)[:3]
                            self.καταγραφή(Εύρημα(
                                "Διαρροή_JS_Σημείου_Πρόσβασης", "Χαμηλή", js_url,
                                f"Βρέθηκαν {len(ενδιαφέροντα)} σημεία πρόσβασης. Δείγμα: {', '.join(δείγμα)}"
                            ))
                            
                except Exception:
                    continue

    async def αναζήτηση_ιστοτόπου(self, client, αρχικό_url, μέγιστο_βάθος=2):
        """Βελτιωμένη αναζήτηση ιστοτόπου με έλεγχο βάθους"""
        επισκεφθέντα = set()
        προς_επίσκεψη = [(αρχικό_url, 0)]
        
        while προς_επίσκεψη:
            τρέχον_url, βάθος = προς_επίσκεψη.pop(0)
            
            if τρέχον_url in επισκεφθέντα or βάθος > μέγιστο_βάθος:
                continue
            
            επισκεφθέντα.add(τρέχον_url)
            
            try:
                response = await client.get(τρέχον_url)
                self.στατιστικά["απαντήσεις_που_λήφθηκαν"] += 1
                
                if response.status_code == 200:
                    # Εξαγωγή συνδέσμων
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        πλήρες_url = urljoin(τρέχον_url, href)
                        
                        # Ακολουθούν μόνο σύνδεσμοι ίδιου τομέα
                        if self.τομέας in πλήρες_url and πλήρες_url not in επισκεφθέντα:
                            προς_επίσκεψη.append((πλήρες_url, βάθος + 1))
                            
                    # Έλεγχος για φόρμες
                    φόρμες = soup.find_all('form')
                    if φόρμες:
                        self.καταγραφή(Εύρημα(
                            "Βρέθηκαν_Φόρμες", "Πληροφορία", τρέχον_url,
                            f"Βρέθηκαν {len(φόρμες)} φόρμες. Ελέγξτε για ευπάθειες XSS/CSRF"
                        ))
                        
            except Exception:
                continue
        
        self.διερευνημένα_url.update(επισκεφθέντα)
        return επισκεφθέντα

    async def έλεγχος_για_ευπάθειες(self, client, url, κείμενο, headers):
        """Έλεγχος για κοινά μοτίβα ευπάθειας"""
        
        # Μοτίβα SQL Injection σε απόκριση
        for τύπος_ευπάθειας, μοτίβα in VULN_PATTERNS.items():
            for μοτίβο in μοτίβα:
                if re.search(μοτίβο, κείμενο, re.IGNORECASE):
                    self.καταγραφή(Εύρημα(
                        f"Πιθανό_{τύπος_ευπάθειας}", "Μέτρια", url,
                        f"Ταιριασμένο μοτίβο: {μοτίβο[:50]}...",
                        αποκατάσταση=f"Εφαρμόστε κατάλληλη επικύρωση εισόδου και κωδικοποίηση εξόδου"
                    ))
        
        # Έλεγχος για λειτουργία debug
        λέξεις_κλειδιά_debug = ['debug', 'development', 'testing', 'staging']
        if any(λέξη_κλειδί in κείμενο.lower() for λέξη_κλειδί in λέξεις_κλειδιά_debug):
            self.καταγραφή(Εύρημα(
                "Λειτουργία_Debug", "Χαμηλή", url,
                "Εντοπίστηκε λειτουργία debug ή ανάπτυξης",
                αποκατάσταση="Απενεργοποιήστε τη λειτουργία debug σε παραγωγή"
            ))

    async def βίαιη_επίθεση_καταλόγων(self, client):
        """Βίαιη επίθεση καταλόγων με κοινή λίστα λέξεων"""
        λίστα_λέξεων = [
            "admin", "login", "wp-admin", "administrator", "dashboard",
            "api", "v1", "v2", "graphql", "rest", "swagger",
            "config", "settings", "env", "backup", "dump",
            "test", "dev", "stage", "prod", "demo",
            "uploads", "files", "images", "assets", "static",
            "phpmyadmin", "mysql", "pma", "sql",
            ".git", ".svn", ".hg", ".env", "robots.txt"
        ]
        
        επεκτάσεις = ["", ".php", ".html", ".jsp", ".asp", ".aspx", ".py", ".rb"]
        
        ευρεθέντες_κατάλογοι = []
        
        async def έλεγχος_καταλόγου(διαδρομή):
            πλήρες_url = urljoin(self.στόχος, διαδρομή)
            try:
                resp = await client.get(πλήρες_url)
                if resp.status_code in [200, 301, 302, 403]:
                    if resp.status_code == 200:
                        ευρεθέντες_κατάλογοι.append(πλήρες_url)
                        self.καταγραφή(Εύρημα(
                            "Βρέθηκε_Κατάλογος", "Πληροφορία", πλήρες_url,
                            f"Κατάσταση: {resp.status_code}, Μέγεθος: {len(resp.text)} bytes"
                        ))
                    elif resp.status_code == 403:
                        self.καταγραφή(Εύρημα(
                            "Απαγορευμένος_Κατάλογος", "Χαμηλή", πλήρες_url,
                            "Απαγορεύεται η πρόσβαση (403) - πιθανή κακή διαμόρφωση"
                        ))
            except Exception:
                pass
        
        # Δημιουργία όλων των διαδρομών προς έλεγχο
        εργασίες = []
        for λέξη in λίστα_λέξεων:
            for επέκταση in επεκτάσεις:
                εργασίες.append(έλεγχος_καταλόγου(f"/{λέξη}{επέκταση}"))
                # Επίσης έλεγχος με τελικό slash
                εργασίες.append(έλεγχος_καταλόγου(f"/{λέξη}{επέκταση}/"))
        
        # Εκτέλεση σε ομάδες
        μέγεθος_ομάδας = 50
        for i in range(0, len(εργασίες), μέγεθος_ομάδας):
            ομάδα = εργασίες[i:i + μέγεθος_ομάδας]
            await asyncio.gather(*ομάδα)
            await asyncio.sleep(0.1)  # Περιορισμός ρυθμού
        
        return ευρεθέντες_κατάλογοι

    async def έλεγχος_ευαίσθητων_αρχείων(self, client):
        """Έλεγχος για έκθεση ευαίσθητων αρχείων"""
        ευάλωτα_αρχεία = []
        
        async def έλεγχος_αρχείου(διαδρομή_αρχείου):
            πλήρες_url = urljoin(self.στόχος, διαδρομή_αρχείου)
            try:
                resp = await client.get(πλήρες_url, follow_redirects=True)
                
                if resp.status_code == 200:
                    περιεχόμενο = resp.text
                    μέγεθος = len(resp.content)
                    
                    # Παράβλεψη εάν είναι πολύ μικρό (μπορεί να είναι σελίδα σφάλματος)
                    if μέγεθος < 100:
                        return
                    
                    # Έλεγχος για συγκεκριμένους τύπους αρχείων
                    if διαδρομή_αρχείου.endswith('.env') or '/.env' in διαδρομή_αρχείου:
                        self.καταγραφή(Εύρημα(
                            "Εκτεθειμένο_Αρχείο_Env", "Υψηλή", πλήρες_url,
                            f"Εκτεθειμένο αρχείο περιβάλλοντος ({μέγεθος} bytes)",
                            αποκατάσταση="Αφαιρέστε το αρχείο .env από τη ρίζα ιστού ή περιορίστε την πρόσβαση"
                        ))
                        ευάλωτα_αρχεία.append(πλήρες_url)
                        
                        # Εξαγωγή πιθανών μυστικών
                        for όνομα_μυστικού, μοτίβο in SECRET_REGEX.items():
                            ταίριασμα = re.findall(μοτίβο, περιεχόμενο)
                            if ταίριασμα:
                                for match in ταίριασμα[:3]:  # Περιορισμός εξόδου
                                    self.καταγραφή(Εύρημα(
                                        "Διαρροή_Μυστικού", "Κρίσιμη", πλήρες_url,
                                        f"{όνομα_μυστικού}: {match[:50]}...",
                                        αποκατάσταση="Περιστρέψτε αμέσως όλα τα εκτεθειμένα κλειδιά"
                                    ))
                    
                    elif διαδρομή_αρχείου.endswith('.git/config'):
                        self.καταγραφή(Εύρημα(
                            "Εκτεθειμένο_Config_Git", "Υψηλή", πλήρες_url,
                            "Εκτεθειμένο αρχείο διαμόρφωσης Git",
                            αποκατάσταση="Αφαιρέστε τον κατάλογο .git από τη ρίζα ιστού"
                        ))
                        
                    elif διαδρομή_αρχείου.endswith('phpinfo.php'):
                        self.καταγραφή(Εύρημα(
                            "Εκτεθειμένο_PHPInfo", "Μέτρια", πλήρες_url,
                            "Εκτεθειμένη σελίδα PHPInfo - αποκαλύπτει τη διαμόρφωση του διακομιστή",
                            αποκατάσταση="Αφαιρέστε το phpinfo.php από παραγωγή"
                        ))
                        
                    elif 'backup' in διαδρομή_αρχείου.lower() or 'dump' in διαδρομή_αρχείου.lower():
                        self.καταγραφή(Εύρημα(
                            "Εκτεθειμένο_Αρχείο_Αντιγράφου", "Υψηλή", πλήρες_url,
                            f"Εκτεθειμένο αρχείο αντιγράφου ασφαλείας ({μέγεθος} bytes)",
                            αποκατάσταση="Αφαιρέστε αρχεία αντιγράφων από προσβάσιμες τοποθεσίες ιστού"
                        ))
                        
            except Exception:
                pass
        
        # Έλεγχος όλων των ευαίσθητων διαδρομών
        εργασίες = [έλεγχος_αρχείου(διαδρομή) for διαδρομή in ΕΥΑΙΣΘΗΤΑ_ΑΡΧΕΙΑ]
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Έλεγχος ευαίσθητων αρχείων...", total=len(εργασίες))
            
            # Επεξεργασία σε ομάδες
            μέγεθος_ομάδας = 20
            for i in range(0, len(εργασίες), μέγεθος_ομάδας):
                ομάδα = εργασίες[i:i + μέγεθος_ομάδας]
                await asyncio.gather(*ομάδα)
                progress.update(task, advance=len(ομάδα))
        
        return ευάλωτα_αρχεία

    async def έλεγχος_cors(self, client, url):
        """Έλεγχος για κακές διαμορφώσεις CORS"""
        try:
            # Δοκιμή με αυθαίρετη προέλευση
            δοκιμαστικές_επικεφαλίδες = self.επικεφαλίδες.copy()
            δοκιμαστικές_επικεφαλίδες["Origin"] = "https://evil.com"
            
            response = await client.get(url, headers=δοκιμαστικές_επικεφαλίδες)
            
            acao = response.headers.get("Access-Control-Allow-Origin")
            acac = response.headers.get("Access-Control-Allow-Credentials", "").lower()
            
            if acao == "*" and acac == "true":
                self.καταγραφή(Εύρημα(
                    "Κακή_Διαμόρφωση_CORS", "Υψηλή", url,
                    "Το CORS επιτρέπει διαπιστευτήρια με μπαλαντέρ προέλευση",
                    αποκατάσταση="Περιορίστε τις προελεύσεις CORS και αποφύγετε τη χρήση διαπιστευτηρίων με μπαλαντέρ"
                ))
            elif acao == "*":
                self.καταγραφή(Εύρημα(
                    "Κακή_Διαμόρφωση_CORS", "Μέτρια", url,
                    "Το CORS χρησιμοποιεί μπαλαντέρ προέλευση",
                    αποκατάσταση="Χρησιμοποιήστε συγκεκριμένες προελεύσεις αντί για μπαλαντέρ"
                ))
            elif "evil.com" in str(acao):
                self.καταγραφή(Εύρημα(
                    "Κακή_Διαμόρφωση_CORS", "Κρίσιμη", url,
                    f"Εντοπίστηκε αντανάκλαση προέλευσης: {acao}",
                    αποκατάσταση="Επικυρώστε σωστά τις προελεύσεις CORS"
                ))
                    
        except Exception:
            pass

    async def έλεγχος_μεθόδων_http(self, client, url):
        """Έλεγχος για επικίνδυνες μεθόδους HTTP"""
        επικίνδυνες_μέθοδοι = ["PUT", "DELETE", "TRACE", "CONNECT"]
        
        for μέθοδος in επικίνδυνες_μέθοδοι:
            try:
                response = await client.request(μέθοδος, url, timeout=5)
                if response.status_code in [200, 201, 204]:
                    self.καταγραφή(Εύρημα(
                        "Επικίνδυνη_Μέθοδος_HTTP", "Μέτρια", url,
                        f"Επιτρέπεται η μέθοδος {μέθοδος}",
                        αποκατάσταση="Απενεργοποιήστε τις μη απαραίτητες μεθόδους HTTP"
                    ))
            except Exception:
                continue

    # --- Κύριος Οργανωτής Σάρωσης ---
    async def ολοκληρωμένη_σάρωση(self):
        """Οργάνωση όλων των ενοτήτων σάρωσης"""
        
        console.print(Panel(f"[bold cyan]Εκκίνηση Ολοκληρωμένης Σάρωσης[/bold cyan]\n"
                          f"Στόχος: [green]{self.στόχος}[/green]\n"
                          f"Τομέας: [green]{self.τομέας}[/green]\n"
                          f"Έξοδος: [green]{self.κατάλογος_εξόδου}[/green]",
                          title="Bug Hunter V3"))
        
        async with httpx.AsyncClient(
            verify=False,  # Προειδοποίηση: Απενεργοποιημένη επαλήθευση SSL για δοκιμές
            limits=self.όρια,
            headers=self.επικεφαλίδες,
            timeout=30.0,
            follow_redirects=True
        ) as client:
            
            # Αρχική αίτηση
            try:
                αρχική_απάντηση = await client.get(self.στόχος)
                self.στατιστικά["αποστολές_αιτήσεων"] += 1
                
                console.print(f"[green]✓[/green] Συνδέθηκε στον στόχο. Κατάσταση: {αρχική_απάντηση.status_code}")
                
            except Exception as e:
                console.print(f"[red]✗[/red] Δεν ήταν δυνατή η σύνδεση με {self.στόχος}: {e}")
                return
            
            # Εκτέλεση όλων των ενοτήτων σάρωσης
            ενότητες = []
            
            if self.διαμόρφωση.get('tech_detect', True):
                ενότητες.append(self.ανίχνευση_στοίβας_τεχνολογιών(client, self.στόχος, αρχική_απάντηση.text, αρχική_απάντηση.headers))
            
            if self.διαμόρφωση.get('security_headers', True):
                ενότητες.append(self.έλεγχος_ασφαλιστικών_επικεφαλίδων(client, self.στόχος, αρχική_απάντηση.headers))
            
            if self.διαμόρφωση.get('cors_check', True):
                ενότητες.append(self.έλεγχος_cors(client, self.στόχος))
            
            if self.διαμόρφωση.get('http_methods', True):
                ενότητες.append(self.έλεγχος_μεθόδων_http(client, self.στόχος))
            
            if self.διαμόρφωση.get('vuln_check', True):
                ενότητες.append(self.έλεγχος_για_ευπάθειες(client, self.στόχος, αρχική_απάντηση.text, αρχική_απάντηση.headers))
            
            # Εκτέλεση αρχικών ενοτήτων
            if ενότητες:
                await asyncio.gather(*ενότητες)
            
            # Εκτέλεση εντατικών σαρώσεων διαδοχικά
            if self.διαμόρφωση.get('port_scan', True):
                console.print("\n[cyan][*][/cyan] Εκκίνηση σάρωσης θυρών...")
                await self.βελτιωμένη_σάρωση_θυρών()
            
            if self.διαμόρφωση.get('takeover_check', True):
                console.print("[cyan][*][/cyan] Έλεγχος για ανάληψη υποτομέα...")
                await self.έλεγχος_ανάληψης_υποτομέα()
            
            if self.διαμόρφωση.get('js_analyze', True):
                console.print("[cyan][*][/cyan] Ανάλυση αρχείων JavaScript...")
                await self.εξαγωγή_js_σημείων_πρόσβασης(client, self.στόχος, αρχική_απάντηση.text)
            
            if self.διαμόρφωση.get('sensitive_files', True):
                console.print("[cyan][*][/cyan] Έλεγχος για ευαίσθητα αρχεία...")
                await self.έλεγχος_ευαίσθητων_αρχείων(client)
            
            if self.διαμόρφωση.get('directory_brute', True):
                console.print("[cyan][*][/cyan] Εκτέλεση βίαιης επίθεσης καταλόγων...")
                await self.βίαιη_επίθεση_καταλόγων(client)
            
            if self.διαμόρφωση.get('crawl', True) and self.διαμόρφωση.get('crawl_depth', 1) > 0:
                console.print(f"[cyan][*][/cyan] Αναζήτηση (βάθος: {self.διαμόρφωση.get('crawl_depth', 1)})...")
                await self.αναζήτηση_ιστοτόπου(client, self.στόχος, max_depth=self.διαμόρφωση.get('crawl_depth', 1))
        
        # Δημιουργία αναφοράς
        self.δημιουργία_βελτιωμένης_αναφοράς()

    # --- Βελτιωμένη Αναφορά ---
    def δημιουργία_βελτιωμένης_αναφοράς(self):
        """Δημιουργία ολοκληρωμένης αναφοράς HTML"""
        
        # Υπολογισμός στατιστικών σάρωσης
        διάρκεια_σάρωσης = datetime.now() - self.στατιστικά["χρόνος_εκκίνησης"]
        
        # Καταμέτρηση σοβαροτήτων
        καταμέτρηση_σοβαροτήτων = {}
        for εύρημα in self.ευρήματα:
            σοβαρότητα = εύρημα.get('σοβαρότητα', 'Πληροφορία')
            καταμέτρηση_σοβαροτήτων[σοβαρότητα] = καταμέτρηση_σοβαροτήτων.get(σοβαρότητα, 0) + 1
        
        # Κατανομή κατηγοριών
        καταμέτρηση_κατηγοριών = {}
        for εύρημα in self.ευρήματα:
            κατηγορία = εύρημα.get('κατηγορία', 'Άγνωστη')
            καταμέτρηση_κατηγοριών[κατηγορία] = καταμέτρηση_κατηγοριών.get(κατηγορία, 0) + 1
        
        # Πρότυπο HTML
        html_template = """
<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Αναφορά Bug Hunter - {{ στόχος }}</title>
    <style>
        :root {
            --κρίσιμη: #dc3545;
            --υψηλή: #fd7e14;
            --μέτρια: #ffc107;
            --χαμηλή: #28a745;
            --πληροφορία: #17a2b8;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 15px; 
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            position: relative;
            overflow: hidden;
        }
        .container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 5px;
            background: linear-gradient(90deg, var(--κρίσιμη), var(--υψηλή), var(--μέτρια), var(--χαμηλή), var(--πληροφορία));
        }
        .header { 
            text-align: center; 
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }
        .header h1 { 
            color: #333; 
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .header .subtitle {
            color: #666;
            font-size: 1.1em;
        }
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
            margin-bottom: 40px;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #e9ecef;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .stat-number { 
            font-size: 3em; 
            font-weight: bold; 
            display: block;
            margin-bottom: 10px;
        }
        .stat-label { 
            color: #666; 
            font-size: 1em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .severity-card.Κρίσιμη { border-top: 4px solid var(--κρίσιμη); }
        .severity-card.Υψηλή { border-top: 4px solid var(--υψηλή); }
        .severity-card.Μέτρια { border-top: 4px solid var(--μέτρια); }
        .severity-card.Χαμηλή { border-top: 4px solid var(--χαμηλή); }
        .severity-card.Πληροφορία { border-top: 4px solid var(--πληροφορία); }
        .severity-count.Κρίσιμη { color: var(--κρίσιμη); }
        .severity-count.Υψηλή { color: var(--υψηλή); }
        .severity-count.Μέτρια { color: var(--μέτρια); }
        .severity-count.Χαμηλή { color: var(--χαμηλή); }
        .severity-count.Πληροφορία { color: var(--πληροφορία); }
        .summary-section { 
            background: #f8f9fa; 
            padding: 25px; 
            border-radius: 10px; 
            margin-bottom: 40px;
        }
        .summary-section h3 { margin-bottom: 20px; color: #333; }
        .tech-list { display: flex; flex-wrap: wrap; gap: 10px; }
        .tech-tag { 
            background: #e9ecef; 
            padding: 8px 15px; 
            border-radius: 20px; 
            font-size: 0.9em;
        }
        .tech-tag.version { background: #d4edda; color: #155724; }
        table { 
            width: 100%; 
            border-collapse: separate; 
            border-spacing: 0;
            margin-top: 20px;
        }
        th { 
            background: #f1f3f4; 
            padding: 15px; 
            text-align: left; 
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #dee2e6;
        }
        td { 
            padding: 15px; 
            border-bottom: 1px solid #eee;
            vertical-align: top;
        }
        tr:hover { background: #f8f9fa; }
        .severity-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: 600;
            color: white;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .severity-badge.Κρίσιμη { background: var(--κρίσιμη); }
        .severity-badge.Υψηλή { background: var(--υψηλή); }
        .severity-badge.Μέτρια { background: var(--μέτρια); }
        .severity-badge.Χαμηλή { background: var(--χαμηλή); }
        .severity-badge.Πληροφορία { background: var(--πληροφορία); }
        .details-popup {
            cursor: pointer;
            color: #007bff;
            text-decoration: underline dotted;
        }
        .popup-content {
            display: none;
            position: absolute;
            background: white;
            border: 1px solid #ccc;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            z-index: 1000;
            max-width: 400px;
        }
        .timestamp { color: #666; font-size: 0.9em; }
        .export-buttons { 
            text-align: center; 
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }
        .btn { 
            display: inline-block; 
            padding: 10px 25px; 
            margin: 0 10px; 
            background: #007bff; 
            color: white; 
            text-decoration: none; 
            border-radius: 5px; 
            transition: background 0.3s;
        }
        .btn:hover { background: #0056b3; }
        .btn-json { background: #6f42c1; }
        .btn-json:hover { background: #563d7c; }
        .btn-csv { background: #28a745; }
        .btn-csv:hover { background: #1e7e34; }
        .port-list { 
            display: flex; 
            flex-wrap: wrap; 
            gap: 10px; 
            margin-top: 10px;
        }
        .port-item { 
            background: #e9ecef; 
            padding: 8px 15px; 
            border-radius: 5px;
            font-family: monospace;
        }
        .risk-meter {
            height: 10px;
            background: #e9ecef;
            border-radius: 5px;
            margin: 20px 0;
            overflow: hidden;
        }
        .risk-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--χαμηλή), var(--μέτρια), var(--υψηλή), var(--κρίσιμη));
            width: {{ ποσοστό_κινδύνου }}%;
        }
        @media (max-width: 768px) {
            .container { padding: 15px; }
            .stats-grid { grid-template-columns: 1fr; }
            table { font-size: 0.9em; }
        }
    </style>
    <script>
        function showDetails(id) {
            var popup = document.getElementById('details-' + id);
            popup.style.display = popup.style.display === 'block' ? 'none' : 'block';
        }
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(function() {
                alert('Αντιγράφηκε στο πρόχειρο!');
            });
        }
        function filterTable(severity) {
            var rows = document.querySelectorAll('#findings-table tr');
            rows.forEach(function(row, index) {
                if (index === 0) return; // Παράβλεψη κεφαλίδας
                if (severity === 'all' || row.querySelector('.severity-badge').classList.contains(severity)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐛 Αναφορά Bug Hunter</h1>
            <div class="subtitle">
                <strong>Στόχος:</strong> {{ στόχος }}<br>
                <strong>Ημερομηνία Σάρωσης:</strong> {{ ημερομηνία_σάρωσης }}<br>
                <strong>Διάρκεια:</strong> {{ διάρκεια }}
            </div>
        </div>
        
        <div class="risk-meter">
            <div class="risk-fill"></div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-number">{{ πλήθος_ευρημάτων }}</span>
                <span class="stat-label">Σύνολο Ευρημάτων</span>
            </div>
            <div class="stat-card severity-card Κρίσιμη">
                <span class="stat-number severity-count Κρίσιμη">{{ καταμέτρηση_σοβαροτήτων.Κρίσιμη or 0 }}</span>
                <span class="stat-label">Κρίσιμα</span>
            </div>
            <div class="stat-card severity-card Υψηλή">
                <span class="stat-number severity-count Υψηλή">{{ καταμέτρηση_σοβαροτήτων.Υψηλή or 0 }}</span>
                <span class="stat-label">Υψηλά</span>
            </div>
            <div class="stat-card severity-card Μέτρια">
                <span class="stat-number severity-count Μέτρια">{{ καταμέτρηση_σοβαροτήτων.Μέτρια or 0 }}</span>
                <span class="stat-label">Μέτρια</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{{ τεχνολογίες|length }}</span>
                <span class="stat-label">Τεχνολογίες</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{{ ανοιχτές_θύρες|length }}</span>
                <span class="stat-label">Ανοιχτές Θύρες</span>
            </div>
        </div>
        
        <div class="summary-section">
            <h3>🎯 Περίληψη Στόχου</h3>
            <p><strong>Τομέας:</strong> {{ τομέας }}</p>
            <p><strong>Διαμόρφωση Σάρωσης:</strong> {{ σύνοψη_διαμόρφωσης }}</p>
            
            <h3>🔧 Ανιχνευμένες Τεχνολογίες</h3>
            <div class="tech-list">
                {% for τεχνολογία in τεχνολογίες %}
                <div class="tech-tag {% if τεχνολογία.έκδοση %}version{% endif %}">
                    {{ τεχνολογία.όνομα }}{% if τεχνολογία.έκδοση %} ({{ τεχνολογία.έκδοση }}){% endif %}
                </div>
                {% endfor %}
            </div>
            
            <h3>🔓 Ανοιχτές Θύρες</h3>
            <div class="port-list">
                {% for θύρα in ανοιχτές_θύρες %}
                <div class="port-item" title="{{ θύρα.banner }}">
                    {{ θύρα.θύρα }} ({{ θύρα.υπηρεσία }})
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div style="margin: 30px 0;">
            <button onclick="filterTable('all')" class="btn">Όλα</button>
            <button onclick="filterTable('Κρίσιμη')" class="btn" style="background: var(--κρίσιμη);">Κρίσιμα</button>
            <button onclick="filterTable('Υψηλή')" class="btn" style="background: var(--υψηλή);">Υψηλά</button>
            <button onclick="filterTable('Μέτρια')" class="btn" style="background: var(--μέτρια);">Μέτρια</button>
            <button onclick="filterTable('Χαμηλή')" class="btn" style="background: var(--χαμηλή);">Χαμηλά</button>
        </div>
        
        <h3>📋 Ευρήματα</h3>
        <table id="findings-table">
            <thead>
                <tr>
                    <th>Σοβαρότητα</th>
                    <th>Κατηγορία</th>
                    <th>URL</th>
                    <th>Λεπτομέρειες</th>
                    <th>Χρόνος</th>
                </tr>
            </thead>
            <tbody>
                {% for ε in ευρήματα %}
                <tr>
                    <td><span class="severity-badge {{ ε.σοβαρότητα }}">{{ ε.σοβαρότητα }}</span></td>
                    <td>{{ ε.κατηγορία }}</td>
                    <td>
                        <a href="{{ ε.url }}" target="_blank">{{ ε.url|truncate(40) }}</a>
                        {% if ε.βεβαιότητα != 'Μέτρια' %}
                        <br><small>Βεβαιότητα: {{ ε.βεβαιότητα }}</small>
                        {% endif %}
                    </td>
                    <td>
                        {{ ε.λεπτομέρειες|truncate(60) }}
                        {% if ε.λεπτομέρειες|length > 60 %}
                        <span class="details-popup" onclick="showDetails('{{ loop.index }}')">[...]</span>
                        <div id="details-{{ loop.index }}" class="popup-content">
                            <strong>Λεπτομέρειες:</strong><br>{{ ε.λεπτομέρειες }}<br><br>
                            {% if ε.απόδειξη_εκμετάλλευσης %}
                            <strong>Απόδειξη Εκμετάλλευσης:</strong><br>{{ ε.απόδειξη_εκμετάλλευσης }}<br>
                            {% endif %}
                            {% if ε.αποκατάσταση %}
                            <strong>Αποκατάσταση:</strong><br>{{ ε.αποκατάσταση }}
                            {% endif %}
                        </div>
                        {% endif %}
                    </td>
                    <td class="timestamp">{{ ε.χρονική_σήμανση }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <div class="export-buttons">
            <a href="ευρήματα.json" class="btn btn-json">Εξαγωγή JSON</a>
            <a href="ευρήματα.csv" class="btn btn-csv">Εξαγωγή CSV</a>
            <a href="αναφορά.pdf" class="btn">Δημιουργία PDF</a>
        </div>
        
        <div style="margin-top: 40px; text-align: center; color: #666; font-size: 0.9em;">
            <p>Δημιουργήθηκε από το Bug Hunter V3 | Εργαλείο Αξιολόγησης Ασφαλείας</p>
            <p>Μόνο για εξουσιοδοτημένο έλεγχο. Η αναφορά περιέχει ευαίσθητες πληροφορίες.</p>
        </div>
    </div>
</body>
</html>
"""
        
        from jinja2 import Template
        
        # Υπολογισμός ποσοστού κινδύνου (απλή ευριστική)
        βαθμολογία_κινδύνου = 0
        for εύρημα in self.ευρήματα:
            if εύρημα['σοβαρότητα'] == 'Κρίσιμη':
                βαθμολογία_κινδύνου += 10
            elif εύρημα['σοβαρότητα'] == 'Υψηλή':
                βαθμολογία_κινδύνου += 5
            elif εύρημα['σοβαρότητα'] == 'Μέτρια':
                βαθμολογία_κινδύνου += 2
            elif εύρημα['σοβαρότητα'] == 'Χαμηλή':
                βαθμολογία_κινδύνου += 1
        
        ποσοστό_κινδύνου = min(βαθμολογία_κινδύνου, 100)
        
        # Προετοιμασία δεδομένων για το πρότυπο
        σύνοψη_διαμόρφωσης = []
        if self.διαμόρφωση.get('port_scan'):
            σύνοψη_διαμόρφωσης.append("Σάρωση Θυρών")
        if self.διαμόρφωση.get('js_analyze'):
            σύνοψη_διαμόρφωσης.append("Ανάλυση JS")
        if self.διαμόρφωση.get('takeover_check'):
            σύνοψη_διαμόρφωσης.append("Ανάληψη Υποτομέα")
        if self.διαμόρφωση.get('crawl'):
            σύνοψη_διαμόρφωσης.append(f"Αναζήτηση (βάθος={self.διαμόρφωση.get('crawl_depth', 1)})")
        
        t = Template(html_template)
        έξοδος = t.render(
            στόχος=self.στόχος,
            τομέας=self.τομέας,
            ημερομηνία_σάρωσης=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            διάρκεια=str(διάρκεια_σάρωσης).split('.')[0],
            ευρήματα=self.ευρήματα,
            πλήθος_ευρημάτων=len(self.ευρήματα),
            καταμέτρηση_σοβαροτήτων=καταμέτρηση_σοβαροτήτων,
            τεχνολογίες=self.τεχνολογίες,
            ανοιχτές_θύρες=self.ανοιχτές_θύρες,
            ποσοστό_κινδύνου=ποσοστό_κινδύνου,
            σύνοψη_διαμόρφωσης=", ".join(σύνοψη_διαμόρφωσης) if σύνοψη_διαμόρφωσης else "Προκαθορισμένη"
        )
        
        αρχείο_αναφοράς = os.path.join(self.κατάλογος_εξόδου, "αναφορά.html")
        with open(αρχείο_αναφοράς, "w", encoding="utf-8") as f:
            f.write(έξοδος)
        
        # Επίσης αποθήκευση ακατέργαστων ευρημάτων ως JSON
        with open(os.path.join(self.κατάλογος_εξόδου, "ευρήματα.json"), "w", encoding="utf-8") as f:
            json.dump({
                "στόχος": self.στόχος,
                "ημερομηνία_σάρωσης": datetime.now().isoformat(),
                "διάρκεια": str(διάρκεια_σάρωσης),
                "ευρήματα": self.ευρήματα,
                "τεχνολογίες": self.τεχνολογίες,
                "ανοιχτές_θύρες": self.ανοιχτές_θύρες,
                "στατιστικά": self.στατιστικά
            }, f, indent=2, default=str)
        
        console.print(f"\n[green]✓[/green] Δημιουργήθηκε αναφορά HTML: [underline]{αρχείο_αναφοράς}[/underline]")
        console.print(f"[green]✓[/green] Διαθέσιμη εξαγωγή JSON: [underline]{os.path.join(self.κατάλογος_εξόδου, 'ευρήματα.json')}[/underline]")
        
        return αρχείο_αναφοράς

# ---------------- Βελτιωμένο GUI ----------------
def βελτιωμένο_ui_curses(stdscr):
    """Βελτιωμένο curses περιβάλλον με καλύτερη εμπειρία χρήστη"""
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    
    # Ορισμός χρωματικών ζευγών
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.init_pair(5, curses.COLOR_RED, -1)
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)
    
    CYAN = curses.color_pair(1)
    CYAN_REV = curses.color_pair(2)
    GREEN = curses.color_pair(3)
    YELLOW = curses.color_pair(4)
    RED = curses.color_pair(5)
    MAGENTA = curses.color_pair(6)
    
    διαμόρφωση = {
        "target": "",
        "concurrency": 50,
        "port_scan": True,
        "js_analyze": True,
        "takeover_check": True,
        "sensitive_files": True,
        "directory_brute": True,
        "crawl": True,
        "crawl_depth": 2,
        "tech_detect": True,
        "security_headers": True,
        "cors_check": True,
        "http_methods": True,
        "vuln_check": True
    }
    
    στοιχεία_μενού = [
        ("URL Στόχου", "target", "str"),
        ("Ταυτόχρονες Συνδέσεις", "concurrency", "toggle", [25, 50, 100]),
        ("Σάρωση Θυρών", "port_scan", "bool"),
        ("Ανάλυση JS", "js_analyze", "bool"),
        ("Έλεγχος Ανάληψης Υποτομέα", "takeover_check", "bool"),
        ("Ευαίσθητα Αρχεία", "sensitive_files", "bool"),
        ("Βίαιη Επίθεση Καταλόγων", "directory_brute", "bool"),
        ("Αναζήτηση Ιστοτόπου", "crawl", "bool"),
        ("Βάθος Αναζήτησης", "crawl_depth", "toggle", [1, 2, 3]),
        ("Ανίχνευση Τεχνολογιών", "tech_detect", "bool"),
        ("Ασφαλιστικές Επικεφαλίδες", "security_headers", "bool"),
        ("Έλεγχος CORS", "cors_check", "bool"),
        ("Μέθοδοι HTTP", "http_methods", "bool"),
        ("Έλεγχοι Ευπάθειας", "vuln_check", "bool"),
        ("[ ΕΚΚΙΝΗΣΗ ΟΛΟΚΛΗΡΩΜΕΝΗΣ ΣΑΡΩΣΗΣ ]", "start", "action"),
        ("[ ΓΡΗΓΟΡΗ ΣΑΡΩΣΗ (Συνιστάται) ]", "quick", "action"),
        ("[ ΦΟΡΤΩΣΗ ΔΙΑΜΟΡΦΩΣΗΣ ]", "load", "action"),
        ("[ ΑΠΟΘΗΚΕΥΣΗ ΔΙΑΜΟΡΦΩΣΗΣ ]", "save", "action"),
        ("[ ΕΞΟΔΟΣ ]", "exit", "action")
    ]
    
    τρέχουσα_σειρά = 0
    σελίδα_διαμόρφωσης = 0
    στοιχεία_ανά_σελίδα = 15
    
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Τίτλος
        τίτλος = " BUG HUNTER ULTIMATE V3 "
        υπότιτλος = " Σύνθετος Σαρωτής Ευπαθειών "
        stdscr.attron(CYAN | curses.A_BOLD)
        stdscr.addstr(1, width//2 - len(τίτλος)//2, τίτλος)
        stdscr.addstr(2, width//2 - len(υπότιτλος)//2, υπότιτλος)
        stdscr.attroff(CYAN | curses.A_BOLD)
        
        # Σχεδίαση μενού με σελιδοποίηση
        αρχικός_δείκτης = σελίδα_διαμόρφωσης * στοιχεία_ανά_σελίδα
        τελικός_δείκτης = min(αρχικός_δείκτης + στοιχεία_ανά_σελίδα, len(στοιχεία_μενού))
        
        for idx in range(αρχικός_δείκτης, τελικός_δείκτης):
            στοιχείο, κλειδί, τύπος_στοιχείου, *επιπλέον = στοιχεία_μενού[idx]
            y = 5 + (idx - αρχικός_δείκτης)
            
            # Προετοιμασία τιμής εμφάνισης
            if τύπος_στοιχείου == "str":
                τιμή = διαμόρφωση[κλειδί] if διαμόρφωση[κλειδί] else "<δεν ορίστηκε>"
            elif τύπος_στοιχείου == "bool":
                τιμή = "✓ ΕΝΕΡΓΟΠΟΙΗΜΕΝΟ" if διαμόρφωση[κλειδί] else "✗ ΑΠΕΝΕΡΓΟΠΟΙΗΜΕΝΟ"
            elif τύπος_στοιχείου == "toggle":
                επιλογές = επιπλέον[0]
                τρέχουσα_τιμή = διαμόρφωση[κλειδί]
                if τρέχουσα_τιμή in επιλογές:
                    τρέχων_δείκτης = επιλογές.index(τρέχουσα_τιμή)
                    τιμή = f"{τρέχουσα_τιμή} ({τρέχων_δείκτης+1}/{len(επιλογές)})"
                else:
                    τιμή = str(τρέχουσα_τιμή)
            elif τύπος_στοιχείου == "action":
                τιμή = ""
            else:
                τιμή = str(διαμόρφωση.get(κλειδί, ""))
            
            # Περικοπή εάν είναι πολύ μεγάλο
            εμφάνιση = f"{στοιχείο:30} {τιμή}"
            if len(εμφάνιση) > width - 10:
                εμφάνιση = εμφάνιση[:width - 13] + "..."
            
            x = width//2 - len(εμφάνιση)//2
            
            if idx == τρέχουσα_σειρά:
                stdscr.attron(CYAN_REV)
                stdscr.addstr(y, x, εμφάνιση)
                stdscr.attroff(CYAN_REV)
            else:
                # Χρωματικός κωδικός κατά τύπο
                if τύπος_στοιχείου == "action":
                    if "ΕΚΚΙΝΗΣΗ" in στοιχείο or "ΣΑΡΩΣΗ" in στοιχείο:
                        stdscr.attron(GREEN | curses.A_BOLD)
                    elif "ΕΞΟΔΟΣ" in στοιχείο:
                        stdscr.attron(RED | curses.A_BOLD)
                    else:
                        stdscr.attron(MAGENTA)
                stdscr.addstr(y, x, εμφάνιση)
                if τύπος_στοιχείου == "action":
                    if "ΕΚΚΙΝΗΣΗ" in στοιχείο or "ΣΑΡΩΣΗ" in στοιχείο:
                        stdscr.attroff(GREEN | curses.A_BOLD)
                    elif "ΕΞΟΔΟΣ" in στοιχείο:
                        stdscr.attroff(RED | curses.A_BOLD)
                    else:
                        stdscr.attroff(MAGENTA)
        
        # Δείκτης σελίδας
        συνολικές_σελίδες = (len(στοιχεία_μενού) + στοιχεία_ανά_σελίδα - 1) // στοιχεία_ανά_σελίδα
        if συνολικές_σελίδες > 1:
            πληροφορία_σελίδας = f" Σελίδα {σελίδα_διαμόρφωσης + 1}/{συνολικές_σελίδες} "
            stdscr.addstr(height - 3, width//2 - len(πληροφορία_σελίδας)//2, πληροφορία_σελίδας, curses.A_REVERSE)
        
        # Κείμενο βοήθειας
        κείμενο_βοήθειας = "↑↓: Πλοήγηση  Enter: Επιλογή  Space: Εναλλαγή  q: Έξοδος  s: Έναρξη"
        stdscr.addstr(height - 2, width//2 - len(κείμενο_βοήθειας)//2, κείμενο_βοήθειας, curses.A_DIM)
        
        key = stdscr.getch()
        
        if key == curses.KEY_UP and τρέχουσα_σειρά > 0:
            τρέχουσα_σειρά -= 1
            if τρέχουσα_σειρά < αρχικός_δείκτης:
                σελίδα_διαμόρφωσης = max(0, σελίδα_διαμόρφωσης - 1)
        elif key == curses.KEY_DOWN and τρέχουσα_σειρά < len(στοιχεία_μενού) - 1:
            τρέχουσα_σειρά += 1
            if τρέχουσα_σειρά >= τελικός_δείκτης:
                σελίδα_διαμόρφωσης = min(συνολικές_σελίδες - 1, σελίδα_διαμόρφωσης + 1)
        elif key in [10, 13]:  # Enter
            στοιχείο, κλειδί, τύπος_στοιχείου, *επιπλέον = στοιχεία_μενού[τρέχουσα_σειρά]
            
            if τύπος_στοιχείου == "str":
                curses.echo()
                stdscr.addstr(height - 5, width//2 - 10, " " * 50)
                stdscr.addstr(height - 5, width//2 - 10, f"{στοιχείο}: ")
                stdscr.refresh()
                input_str = stdscr.getstr(height - 5, width//2 - 10 + len(στοιχείο) + 2, 100)
                διαμόρφωση[κλειδί] = input_str.decode('utf-8').strip()
                curses.noecho()
            elif τύπος_στοιχείου == "bool":
                διαμόρφωση[κλειδί] = not διαμόρφωση[κλειδί]
            elif τύπος_στοιχείου == "toggle":
                επιλογές = επιπλέον[0]
                τρέχουσα_τιμή = διαμόρφωση[κλειδί]
                if τρέχουσα_τιμή in επιλογές:
                    τρέχων_δείκτης = επιλογές.index(τρέχουσα_τιμή)
                    διαμόρφωση[κλειδί] = επιλογές[(τρέχων_δείκτης + 1) % len(επιλογές)]
                else:
                    διαμόρφωση[κλειδί] = επιλογές[0]
            elif τύπος_στοιχείου == "action":
                if κλειδί == "start":
                    if διαμόρφωση["target"]:
                        break
                    else:
                        # Εμφάνιση σφάλματος
                        stdscr.addstr(height - 5, width//2 - 15, "Παρακαλώ ορίστε πρώτα τον στόχο URL!", RED | curses.A_BOLD)
                        stdscr.getch()
                elif κλειδί == "quick":
                    # Ορισμός προκαθορισμένων ρυθμίσεων γρήγορης σάρωσης
                    διαμόρφωση.update({
                        "concurrency": 50,
                        "port_scan": True,
                        "js_analyze": True,
                        "sensitive_files": True,
                        "crawl": True,
                        "crawl_depth": 1,
                        "tech_detect": True
                    })
                    if διαμόρφωση["target"]:
                        break
                elif κλειδί == "load":
                    # Φόρτωση διαμόρφωσης από αρχείο
                    try:
                        curses.echo()
                        stdscr.addstr(height - 5, width//2 - 15, "Αρχείο διαμόρφωσης: ")
                        file_path = stdscr.getstr(height - 5, width//2 - 2, 100).decode('utf-8')
                        if os.path.exists(file_path):
                            with open(file_path, 'r') as f:
                                loaded = json.load(f)
                                διαμόρφωση.update(loaded)
                        curses.noecho()
                    except:
                        pass
                elif κλειδί == "save":
                    # Αποθήκευση διαμόρφωσης σε αρχείο
                    try:
                        curses.echo()
                        stdscr.addstr(height - 5, width//2 - 15, "Αποθήκευση σε: ")
                        file_path = stdscr.getstr(height - 5, width//2 - 7, 100).decode('utf-8')
                        with open(file_path, 'w') as f:
                            json.dump(διαμόρφωση, f, indent=2)
                        curses.noecho()
                    except:
                        pass
                elif κλειδί == "exit":
                    sys.exit(0)
        elif key == 32:  # Space
            # Εναλλαγή boolean στοιχείων
            στοιχείο, κλειδί, τύπος_στοιχείου, *επιπλέον = στοιχεία_μενού[τρέχουσα_σειρά]
            if τύπος_στοιχείου == "bool":
                διαμόρφωση[κλειδί] = not διαμόρφωση[κλειδί]
        elif key in [81, 113]:  # Q or q
            if Confirm.ask("Έξοδος από το Bug Hunter?"):
                sys.exit(0)
    
    return διαμόρφωση

def γρήγορη_λειτουργία_cli():
    """Γρήγορο περιβάλλον γραμμής εντολών"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bug Hunter Ultimate V3")
    parser.add_argument("στόχος", help="URL ή τομέας στόχου")
    parser.add_argument("-o", "--output", help="Κατάλογος εξόδου")
    parser.add_argument("--quick", action="store_true", help="Λειτουργία γρήγορης σάρωσης")
    parser.add_argument("--full", action="store_true", help="Πλήρης ολοκληρωμένη σάρωση")
    parser.add_argument("--no-port-scan", action="store_true", help="Απενεργοποίηση σάρωσης θυρών")
    parser.add_argument("--concurrency", type=int, default=50, help="Ταυτόχρονες συνδέσεις")
    parser.add_argument("--save-config", help="Αποθήκευση διαμόρφωσης σε αρχείο")
    parser.add_argument("--load-config", help="Φόρτωση διαμόρφωσης από αρχείο")
    
    args = parser.parse_args()
    
    # Προκαθορισμένη διαμόρφωση
    διαμόρφωση = {
        "target": args.στόχος,
        "concurrency": args.concurrency,
        "port_scan": not args.no_port_scan,
        "js_analyze": True,
        "takeover_check": True,
        "sensitive_files": True,
        "directory_brute": not args.quick,
        "crawl": True,
        "crawl_depth": 1 if args.quick else 2,
        "tech_detect": True,
        "security_headers": True,
        "cors_check": True,
        "http_methods": not args.quick,
        "vuln_check": True
    }
    
    if args.full:
        διαμόρφωση.update({
            "crawl_depth": 3,
            "directory_brute": True,
            "concurrency": 100
        })
    
    if args.load_config and os.path.exists(args.load_config):
        with open(args.load_config, 'r') as f:
            loaded = json.load(f)
            διαμόρφωση.update(loaded)
    
    if args.save_config:
        with open(args.save_config, 'w') as f:
            json.dump(διαμόρφωση, f, indent=2)
    
    return διαμόρφωση

# ---------------- Κύρια Είσοδος ----------------
if __name__ == "__main__":
    try:
        console.print(Panel.fit(
            "[bold cyan]🐛 BUG HUNTER ULTIMATE V3[/bold cyan]\n"
            "[yellow]Σύνθετος Σαρωτής Ευπαθειών[/yellow]\n"
            "[dim]Μόνο για εξουσιοδοτημένο έλεγχο ασφαλείας[/dim]",
            title="Καλωσήρθατε",
            border_style="cyan"
        ))
        
        # Ανάλυση γραμμής εντολών ή εκκίνηση UI
        if len(sys.argv) > 1:
            διαμόρφωση = γρήγορη_λειτουργία_cli()
        else:
            console.print("\n[cyan]Επιλέξτε λειτουργία περιβάλλοντος:[/cyan]")
            console.print("1. Διαδραστικό Τερματικό UI (Συνιστάται)")
            console.print("2. Γρήγορη Λειτουργία CLI")
            console.print("3. Φόρτωση από αρχείο διαμόρφωσης")
            
            επιλογή = Prompt.ask("Επιλογή", choices=["1", "2", "3"], default="1")
            
            if επιλογή == "1":
                διαμόρφωση = curses.wrapper(βελτιωμένο_ui_curses)
            elif επιλογή == "2":
                στόχος = Prompt.ask("URL Στόχου")
                διαμόρφωση = {
                    "target": στόχος,
                    "concurrency": 50,
                    "port_scan": True,
                    "js_analyze": True,
                    "takeover_check": True,
                    "sensitive_files": True,
                    "directory_brute": True,
                    "crawl": True,
                    "crawl_depth": 2,
                    "tech_detect": True,
                    "security_headers": True,
                    "cors_check": True,
                    "http_methods": True,
                    "vuln_check": True
                }
            elif επιλογή == "3":
                αρχείο_διαμόρφωσης = Prompt.ask("Διαδρομή αρχείου διαμόρφωσης")
                with open(αρχείο_διαμόρφωσης, 'r') as f:
                    διαμόρφωση = json.load(f)
        
        # Ρύθμιση καταλόγου εξόδου
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        ασφαλής_στόχος = re.sub(r"[^\w\-]", "_", διαμόρφωση['target'][:30])
        if διαμόρφωση.get('output'):
            διαδρομή_εξόδου = διαμόρφωση['output']
        else:
            διαδρομή_εξόδου = os.path.join(os.getcwd(), f"σάρωση_{ασφαλής_στόχος}_{ts}")
        
        # Δημιουργία σαρωτή και εκτέλεση
        σαρωτής = ΣύνθετοςΣαρωτής(διαμόρφωση['target'], διαδρομή_εξόδου, διαμόρφωση)
        
        console.rule("[bold cyan]Εκκίνηση Σάρωσης[/bold cyan]")
        console.print(f"Στόχος: [green]{διαμόρφωση['target']}[/green]")
        console.print(f"Έξοδος: [underline]{διαδρομή_εξόδου}[/underline]")
        console.print(f"Λειτουργία: [yellow]{'Γρήγορη' if διαμόρφωση.get('crawl_depth', 2) == 1 else 'Ολοκληρωμένη'}[/yellow]")
        console.rule()
        
        # Εκτέλεση της σάρωσης
        asyncio.run(σαρωτής.ολοκληρωμένη_σάρωση())
        
        # Περίληψη
        console.rule("[bold green]Ολοκλήρωση Σάρωσης[/bold green]")
        
        # Εμφάνιση πίνακα περίληψης
        if σαρωτής.ευρήματα:
            table = Table(title="Περίληψη Σάρωσης")
            table.add_column("Σοβαρότητα", style="bold")
            table.add_column("Πλήθος", justify="right")
            table.add_column("Παράδειγμα", style="dim")
            
            ομάδες_σοβαροτήτων = {}
            for εύρημα in σαρωτής.ευρήματα:
                σοβαρότητα = εύρημα['σοβαρότητα']
                if σοβαρότητα not in ομάδες_σοβαροτήτων:
                    ομάδες_σοβαροτήτων[σοβαρότητα] = []
                ομάδες_σοβαροτήτων[σοβαρότητα].append(εύρημα)
            
            for σοβαρότητα in ["Κρίσιμη", "Υψηλή", "Μέτρια", "Χαμηλή", "Πληροφορία"]:
                if σοβαρότητα in ομάδες_σοβαροτήτων:
                    πλήθος = len(ομάδες_σοβαροτήτων[σοβαρότητα])
                    παράδειγμα = ομάδες_σοβαροτήτων[σοβαρότητα][0]['κατηγορία'][:30]
                    
                    χρώμα = {
                        "Κρίσιμη": "red",
                        "Υψηλή": "orange1",
                        "Μέτρια": "yellow",
                        "Χαμηλή": "green",
                        "Πληροφορία": "blue"
                    }.get(σοβαρότητα, "white")
                    
                    table.add_row(
                        f"[{χρώμα}]{σοβαρότητα}[/{χρώμα}]",
                        str(πλήθος),
                        παράδειγμα
                    )
            
            console.print(table)
        
        console.print(f"\n[green]Δημιουργήθηκαν αναφορές στο:[/green] [underline]{διαδρομή_εξόδου}[/underline]")
        console.print(f"[yellow]Συνολικά ευρήματα:[/yellow] {len(σαρωτής.ευρήματα)}")
        console.print(f"[yellow]Ανιχνεύθηκαν τεχνολογίες:[/yellow] {len(σαρωτής.τεχνολογίες)}")
        console.print(f"[yellow]Βρέθηκαν ανοιχτές θύρες:[/yellow] {len(σαρωτής.ανοιχτές_θύρες)}")
        
        if any(f['σοβαρότητα'] == 'Κρίσιμη' for f in σαρωτής.ευρήματα):
            console.print("\n[bold red]⚠  ΕΝΤΟΠΙΣΤΗΚΑΝ ΚΡΙΣΙΜΑ ΕΥΡΗΜΑΤΑ! Απαιτείται άμεση δράση![/bold red]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow][!] Η σάρωση διακόπηκε από τον χρήστη.[/yellow]")
    except Exception as e:
        console.print(f"[red][!] Σφάλμα: {e}[/red]")
        if Confirm.ask("Εμφάνιση λεπτομερούς ιχνογραφήματος;"):
            console.print_exception()
    finally:
        console.print("\n[dim]Το Bug Hunter ολοκληρώθηκε. Θυμηθείτε: Με μεγάλη δύναμη έρχεται και μεγάλη ευθύνη.[/dim]")