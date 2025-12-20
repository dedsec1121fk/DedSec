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

# ---------------- Auto-install deps ----------------
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
        print(f"[*] Installing missing dependencies: {', '.join(missing)}")
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

# ---------------- Enhanced Config & Payloads ----------------

# Extended Tech Signatures with versions
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

# Extended Subdomain Takeover
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

# Extended port list with service detection
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

SENSITIVE_PATHS = [
    # Configuration files
    "/.env", "/.env.local", "/.env.production", "/.env.development",
    "/config.json", "/config.php", "/configuration.php", "/config.yml",
    "/config.yaml", "/settings.py", "/web.config", "/application.ini",
    
    # Version control
    "/.git/config", "/.git/HEAD", "/.git/logs/HEAD", "/.git/index",
    "/.svn/entries", "/.hg/store/00manifest.i",
    
    # Backup files
    "/backup.sql", "/database.sql", "/dump.sql", "/backup.zip",
    "/backup.tar.gz", "/backup.rar", "/site.bak", "/www.rar",
    
    # Log files
    "/logs/access.log", "/error.log", "/debug.log", "/trace.log",
    
    # Admin interfaces
    "/admin/", "/administrator/", "/wp-admin/", "/manager/",
    "/login/", "/cpanel/", "/webmail/", "/phpmyadmin/",
    
    # API endpoints
    "/api/", "/graphql", "/rest/", "/v1/", "/v2/", "/swagger/",
    "/docs/", "/openapi.json", "/api-docs/",
    
    # Miscellaneous
    "/phpinfo.php", "/test.php", "/info.php", "/server-status",
    "/.DS_Store", "/thumbs.db", "/crossdomain.xml", "/clientaccesspolicy.xml",
    "/sitemap.xml", "/robots.txt", "/humans.txt"
]

# Enhanced secret patterns with better validation
SECRET_REGEX = {
    "Google API Key": r"AIza[0-9A-Za-z\-_]{35}",
    "Google OAuth": r"ya29\.[0-9A-Za-z\-_]+",
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "AWS Secret Key": r"(?i)aws_secret_access_key[=:]\s*['\"]?([A-Za-z0-9\/+=]{40})['\"]?",
    "Stripe API Key": r"(?i)stripe_(?:api|secret|private)_key[=:]\s*['\"]?(sk_(?:live|test)_[0-9a-zA-Z]{24})['\"]?",
    "Slack Token": r"xox[baprs]-([0-9a-zA-Z]{10,48})",
    "GitHub Token": r"ghp_[a-zA-Z0-9]{36}",
    "GitHub OAuth": r"github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}",
    "JWT": r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}",
    "SSH Private Key": r"-----BEGIN (?:RSA|DSA|EC|OPENSSH) PRIVATE KEY-----",
    "PGP Private Key": r"-----BEGIN PGP PRIVATE KEY BLOCK-----",
    "Facebook Access Token": r"EAACEdEose0cBA[0-9A-Za-z]+",
    "Twitter API Key": r"(?i)twitter_api_(?:key|secret)[=:]\s*['\"]?([a-zA-Z0-9]{25,50})['\"]?",
    "LinkedIn Client Secret": r"(?i)linkedin_client_secret[=:]\s*['\"]?([a-zA-Z0-9]{16})['\"]?",
    "Mailgun API Key": r"key-[0-9a-f]{32}",
    "Twilio API Key": r"SK[0-9a-fA-F]{32}",
    "Square Access Token": r"sq0atp-[0-9A-Za-z\-_]{22}",
    "Firebase Database Secret": r"(?i)firebase_database_secret[=:]\s*['\"]?([a-zA-Z0-9]{40})['\"]?"
}

# Headers to test for security misconfigurations
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

# Common vulnerabilities patterns
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

# ---------------- Models ----------------
@dataclass
class Finding:
    category: str
    severity: str  # Critical, High, Medium, Low, Info
    url: str
    details: str = ""
    timestamp: str = ""
    confidence: str = "Medium"  # Low, Medium, High
    exploit_poc: str = ""
    remediation: str = ""
    
    def __post_init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@dataclass
class Technology:
    name: str
    version: str = ""
    confidence: int = 0
    locations: List[str] = field(default_factory=list)

# ---------------- Extended Scanner ----------------
class AdvancedScanner:
    def __init__(self, target: str, out_dir: str, config: dict):
        self.target = target if target.startswith("http") else "https://" + target
        parsed = urlparse(self.target)
        self.domain = parsed.netloc
        self.base_url = f"{parsed.scheme}://{parsed.netloc}"
        self.out_dir = out_dir
        self.config = config
        
        self.findings = []
        self.technologies = []
        self.js_endpoints = set()
        self.open_ports = []
        self.subdomains = set()
        self.crawled_urls = set()
        self.sensitive_files = []
        self.secrets_found = []
        
        # Performance tuning
        self.limits = httpx.Limits(
            max_connections=config.get('concurrency', 50),
            max_keepalive_connections=20
        )
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # Create output structure
        os.makedirs(self.out_dir, exist_ok=True)
        os.makedirs(os.path.join(self.out_dir, "screenshots"), exist_ok=True)
        os.makedirs(os.path.join(self.out_dir, "data"), exist_ok=True)
        
        # Initialize counters
        self.stats = {
            "requests_sent": 0,
            "responses_received": 0,
            "errors": 0,
            "start_time": datetime.now()
        }

    def log(self, finding: Finding):
        """Log findings with rich formatting"""
        self.findings.append(asdict(finding))
        
        # Color coding for console
        color_map = {
            "Critical": "red",
            "High": "orange1",
            "Medium": "yellow",
            "Low": "green",
            "Info": "blue"
        }
        
        console.print(f"[{color_map.get(finding.severity, 'white')}][{finding.severity}][/{color_map.get(finding.severity, 'white')}] "
                     f"{finding.category}: {finding.url}")
        if finding.details:
            console.print(f"   Details: {finding.details}")
        
        # Log to file
        log_file = os.path.join(self.out_dir, "findings.jsonl")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(finding), ensure_ascii=False) + "\n")
        
        # Also log to CSV for easier analysis
        csv_file = os.path.join(self.out_dir, "findings.csv")
        if not os.path.exists(csv_file):
            with open(csv_file, "w", encoding="utf-8") as f:
                f.write("timestamp,severity,category,url,details,confidence\n")
        
        with open(csv_file, "a", encoding="utf-8") as f:
            f.write(f"{finding.timestamp},{finding.severity},{finding.category},{finding.url},{finding.details},{finding.confidence}\n")

    # --- Enhanced Modules ---

    async def check_security_headers(self, client, url, headers):
        """Check for missing security headers"""
        missing = []
        for header in SECURITY_HEADERS:
            if header not in headers:
                missing.append(header)
        
        if missing:
            self.log(Finding(
                "Missing_Security_Headers", "Medium", url,
                f"Missing headers: {', '.join(missing)}",
                remediation="Implement missing security headers"
            ))

    async def detect_tech_stack(self, client, url, text, headers):
        """Enhanced technology detection with version fingerprinting"""
        detected = []
        h_str = json.dumps(dict(headers)).lower()
        
        for tech, sigs in TECH_SIGS.items():
            tech_found = False
            version = ""
            
            # Check headers
            for h in sigs.get('headers', []):
                if h.lower() in h_str:
                    tech_found = True
            
            # Check body
            for b in sigs.get('body', []):
                if b in text:
                    tech_found = True
            
            # Extract version if possible
            if tech_found and 'version_regex' in sigs:
                matches = re.findall(sigs['version_regex'], text, re.IGNORECASE)
                if matches:
                    version = matches[0][0] if isinstance(matches[0], tuple) else matches[0]
            
            if tech_found:
                detected.append((tech, version))
        
        # Store technologies
        for tech, version in detected:
            self.technologies.append({
                "name": tech,
                "version": version,
                "confidence": "High" if version else "Medium"
            })
        
        if detected:
            tech_str = ", ".join([f"{t} {v}" if v else t for t, v in detected])
            self.log(Finding("Tech_Stack", "Info", url, f"Detected: {tech_str}"))

    async def enhanced_port_scan(self):
        """Enhanced port scanning with service detection and banner grabbing"""
        open_ports = []
        
        async def check_port(port):
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.domain, port),
                    timeout=2.0
                )
                
                # Try to grab banner
                writer.write(b"\r\n\r\n")
                await writer.drain()
                try:
                    banner = await asyncio.wait_for(reader.read(1024), timeout=1.0)
                    banner = banner.decode('utf-8', errors='ignore').strip()
                except:
                    banner = ""
                
                service = COMMON_PORTS.get(port, "Unknown")
                open_ports.append({
                    "port": port,
                    "service": service,
                    "banner": banner[:100] if banner else ""
                })
                
                writer.close()
                await writer.wait_closed()
                
                # Log finding
                if banner:
                    self.log(Finding(
                        "Open_Port", "Low", f"{self.domain}:{port}",
                        f"Service: {service}, Banner: {banner[:50]}..."
                    ))
                else:
                    self.log(Finding(
                        "Open_Port", "Info", f"{self.domain}:{port}",
                        f"Service: {service}"
                    ))
                    
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                pass
            except Exception as e:
                pass
        
        # Scan common ports
        ports = list(COMMON_PORTS.keys())
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Port scanning...", total=len(ports))
            
            # Batch processing for speed
            batch_size = 100
            for i in range(0, len(ports), batch_size):
                batch = ports[i:i + batch_size]
                await asyncio.gather(*[check_port(p) for p in batch])
                progress.update(task, advance=len(batch))
        
        self.open_ports = open_ports
        return open_ports

    async def check_subdomain_takeover(self):
        """Enhanced subdomain takeover detection"""
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = ['8.8.8.8', '1.1.1.1']  # Use reliable DNS
            
            try:
                answers = resolver.resolve(self.domain, 'CNAME')
                for answer in answers:
                    cname = str(answer.target).rstrip('.')
                    
                    # Check if CNAME points to known vulnerable services
                    vulnerable_domains = [
                        'github.io', 'herokuapp.com', 'aws.amazon.com',
                        'azurewebsites.net', 'cloudapp.net', 's3.amazonaws.com'
                    ]
                    
                    if any(vuln_domain in cname for vuln_domain in vulnerable_domains):
                        # Test the domain
                        async with httpx.AsyncClient(verify=False, timeout=10) as client:
                            try:
                                resp = await client.get(self.target)
                                resp_text = resp.text.lower()
                                
                                for provider, fingerprints in TAKEOVER_SIGS.items():
                                    for fingerprint in fingerprints:
                                        if fingerprint.lower() in resp_text:
                                            self.log(Finding(
                                                "Subdomain_Takeover", "Critical", self.target,
                                                f"Provider: {provider}, CNAME: {cname}",
                                                exploit_poc=f"CNAME points to {cname} which is vulnerable to takeover",
                                                remediation=f"Remove the CNAME record or claim the service"
                                            ))
                                            return
                            except Exception:
                                pass
                                
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                pass
                
        except Exception as e:
            pass

    async def extract_js_endpoints(self, client, url, html_content):
        """Enhanced JS analysis with AST parsing (simplified)"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all script tags
        scripts = soup.find_all('script')
        
        for script in scripts:
            src = script.get('src')
            if src:
                js_url = urljoin(url, src)
                try:
                    response = await client.get(js_url)
                    if response.status_code == 200:
                        js_content = response.text
                        
                        # Extract endpoints with various patterns
                        patterns = [
                            r'(?:["\'])(\/[a-zA-Z0-9_\-\.\/]+\.(?:json|api|rest|graphql))["\']',
                            r'(?:url|endpoint|api)[:=]\s*["\']([^"\']+)["\']',
                            r'fetch\(["\']([^"\']+)["\']',
                            r'axios\.(?:get|post|put|delete)\(["\']([^"\']+)["\']',
                            r'\.ajax\([^{]*url:\s*["\']([^"\']+)["\']'
                        ]
                        
                        all_endpoints = set()
                        for pattern in patterns:
                            matches = re.findall(pattern, js_content, re.IGNORECASE)
                            for match in matches:
                                if isinstance(match, tuple):
                                    match = match[0]
                                if match.startswith('/') or match.startswith('http'):
                                    full_url = urljoin(js_url, match)
                                    all_endpoints.add(full_url)
                        
                        # Filter interesting endpoints
                        interesting = [ep for ep in all_endpoints if any(
                            keyword in ep.lower() for keyword in 
                            ['api', 'admin', 'auth', 'token', 'user', 'account', 'config']
                        )]
                        
                        if interesting:
                            self.js_endpoints.update(interesting)
                            sample = list(interesting)[:3]
                            self.log(Finding(
                                "JS_Endpoint_Leak", "Low", js_url,
                                f"Found {len(interesting)} endpoints. Sample: {', '.join(sample)}"
                            ))
                            
                except Exception:
                    continue

    async def crawl_spider(self, client, start_url, max_depth=2):
        """Enhanced web spider with depth control"""
        visited = set()
        to_visit = [(start_url, 0)]
        
        while to_visit:
            current_url, depth = to_visit.pop(0)
            
            if current_url in visited or depth > max_depth:
                continue
            
            visited.add(current_url)
            
            try:
                response = await client.get(current_url)
                self.stats["responses_received"] += 1
                
                if response.status_code == 200:
                    # Extract links
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(current_url, href)
                        
                        # Only follow same-domain links
                        if self.domain in full_url and full_url not in visited:
                            to_visit.append((full_url, depth + 1))
                            
                    # Check for forms
                    forms = soup.find_all('form')
                    if forms:
                        self.log(Finding(
                            "Forms_Found", "Info", current_url,
                            f"Found {len(forms)} forms. Check for XSS/CSRF vulnerabilities"
                        ))
                        
            except Exception:
                continue
        
        self.crawled_urls.update(visited)
        return visited

    async def check_for_vulnerabilities(self, client, url, text, headers):
        """Check for common vulnerability patterns"""
        
        # SQL Injection patterns in response
        for vuln_type, patterns in VULN_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    self.log(Finding(
                        f"Potential_{vuln_type}", "Medium", url,
                        f"Pattern matched: {pattern[:50]}...",
                        remediation=f"Implement proper input validation and output encoding"
                    ))
        
        # Check for debug mode
        debug_keywords = ['debug', 'development', 'testing', 'staging']
        if any(keyword in text.lower() for keyword in debug_keywords):
            self.log(Finding(
                "Debug_Mode", "Low", url,
                "Debug or development mode detected",
                remediation="Disable debug mode in production"
            ))

    async def directory_bruteforce(self, client):
        """Directory brute-forcing with common wordlist"""
        wordlist = [
            "admin", "login", "wp-admin", "administrator", "dashboard",
            "api", "v1", "v2", "graphql", "rest", "swagger",
            "config", "settings", "env", "backup", "dump",
            "test", "dev", "stage", "prod", "demo",
            "uploads", "files", "images", "assets", "static",
            "phpmyadmin", "mysql", "pma", "sql",
            ".git", ".svn", ".hg", ".env", "robots.txt"
        ]
        
        extensions = ["", ".php", ".html", ".jsp", ".asp", ".aspx", ".py", ".rb"]
        
        found_dirs = []
        
        async def check_dir(path):
            full_url = urljoin(self.target, path)
            try:
                resp = await client.get(full_url)
                if resp.status_code in [200, 301, 302, 403]:
                    if resp.status_code == 200:
                        found_dirs.append(full_url)
                        self.log(Finding(
                            "Directory_Found", "Info", full_url,
                            f"Status: {resp.status_code}, Size: {len(resp.text)} bytes"
                        ))
                    elif resp.status_code == 403:
                        self.log(Finding(
                            "Directory_Forbidden", "Low", full_url,
                            "Access forbidden (403) - potential misconfiguration"
                        ))
            except Exception:
                pass
        
        # Generate all paths to check
        tasks = []
        for word in wordlist:
            for ext in extensions:
                tasks.append(check_dir(f"/{word}{ext}"))
                # Also check with trailing slash
                tasks.append(check_dir(f"/{word}{ext}/"))
        
        # Run in batches
        batch_size = 50
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            await asyncio.gather(*batch)
            await asyncio.sleep(0.1)  # Rate limiting
        
        return found_dirs

    async def check_sensitive_files(self, client):
        """Check for sensitive file exposure"""
        vulnerable_files = []
        
        async def check_file(file_path):
            full_url = urljoin(self.target, file_path)
            try:
                resp = await client.get(full_url, follow_redirects=True)
                
                if resp.status_code == 200:
                    content = resp.text
                    size = len(resp.content)
                    
                    # Skip if too small (might be error page)
                    if size < 100:
                        return
                    
                    # Check for specific file types
                    if file_path.endswith('.env') or '/.env' in file_path:
                        self.log(Finding(
                            "Env_File_Exposed", "High", full_url,
                            f"Environment file exposed ({size} bytes)",
                            remediation="Remove .env file from web root or restrict access"
                        ))
                        vulnerable_files.append(full_url)
                        
                        # Extract potential secrets
                        for secret_name, pattern in SECRET_REGEX.items():
                            matches = re.findall(pattern, content)
                            if matches:
                                for match in matches[:3]:  # Limit output
                                    self.log(Finding(
                                        "Secret_Leak", "Critical", full_url,
                                        f"{secret_name}: {match[:50]}...",
                                        remediation="Rotate all exposed keys immediately"
                                    ))
                    
                    elif file_path.endswith('.git/config'):
                        self.log(Finding(
                            "Git_Config_Exposed", "High", full_url,
                            "Git configuration file exposed",
                            remediation="Remove .git directory from web root"
                        ))
                        
                    elif file_path.endswith('phpinfo.php'):
                        self.log(Finding(
                            "PHPInfo_Exposed", "Medium", full_url,
                            "PHPInfo page exposed - reveals server configuration",
                            remediation="Remove phpinfo.php from production"
                        ))
                        
                    elif 'backup' in file_path.lower() or 'dump' in file_path.lower():
                        self.log(Finding(
                            "Backup_File_Exposed", "High", full_url,
                            f"Backup file exposed ({size} bytes)",
                            remediation="Remove backup files from web-accessible locations"
                        ))
                        
            except Exception:
                pass
        
        # Check all sensitive paths
        tasks = [check_file(path) for path in SENSITIVE_PATHS]
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Checking sensitive files...", total=len(tasks))
            
            # Process in batches
            batch_size = 20
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                await asyncio.gather(*batch)
                progress.update(task, advance=len(batch))
        
        return vulnerable_files

    async def perform_cors_check(self, client, url):
        """Check for CORS misconfigurations"""
        try:
            # Test with arbitrary origin
            test_headers = self.headers.copy()
            test_headers["Origin"] = "https://evil.com"
            
            response = await client.get(url, headers=test_headers)
            
            acao = response.headers.get("Access-Control-Allow-Origin")
            acac = response.headers.get("Access-Control-Allow-Credentials", "").lower()
            
            if acao == "*" and acac == "true":
                self.log(Finding(
                    "CORS_Misconfiguration", "High", url,
                    "CORS allows credentials with wildcard origin",
                    remediation="Restrict CORS origins and avoid using credentials with wildcard"
                ))
            elif acao == "*":
                self.log(Finding(
                    "CORS_Misconfiguration", "Medium", url,
                    "CORS uses wildcard origin",
                    remediation="Use specific origins instead of wildcard"
                ))
            elif "evil.com" in str(acao):
                self.log(Finding(
                    "CORS_Misconfiguration", "Critical", url,
                    f"Origin reflection detected: {acao}",
                    remediation="Validate CORS origins properly"
                ))
                    
        except Exception:
            pass

    async def check_http_methods(self, client, url):
        """Check for dangerous HTTP methods"""
        dangerous_methods = ["PUT", "DELETE", "TRACE", "CONNECT"]
        
        for method in dangerous_methods:
            try:
                response = await client.request(method, url, timeout=5)
                if response.status_code in [200, 201, 204]:
                    self.log(Finding(
                        "Dangerous_HTTP_Method", "Medium", url,
                        f"{method} method allowed",
                        remediation="Disable unnecessary HTTP methods"
                    ))
            except Exception:
                continue

    # --- Main Scan Orchestrator ---
    async def comprehensive_scan(self):
        """Orchestrate all scan modules"""
        
        console.print(Panel(f"[bold cyan]Starting Comprehensive Scan[/bold cyan]\n"
                          f"Target: [green]{self.target}[/green]\n"
                          f"Domain: [green]{self.domain}[/green]\n"
                          f"Output: [green]{self.out_dir}[/green]",
                          title="Bug Hunter V3"))
        
        async with httpx.AsyncClient(
            verify=False,  # Warning: SSL verification disabled for testing
            limits=self.limits,
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True
        ) as client:
            
            # Initial request
            try:
                initial_response = await client.get(self.target)
                self.stats["requests_sent"] += 1
                
                console.print(f"[green]✓[/green] Connected to target. Status: {initial_response.status_code}")
                
            except Exception as e:
                console.print(f"[red]✗[/red] Could not connect to {self.target}: {e}")
                return
            
            # Run all scan modules
            modules = []
            
            if self.config.get('tech_detect', True):
                modules.append(self.detect_tech_stack(client, self.target, initial_response.text, initial_response.headers))
            
            if self.config.get('security_headers', True):
                modules.append(self.check_security_headers(client, self.target, initial_response.headers))
            
            if self.config.get('cors_check', True):
                modules.append(self.perform_cors_check(client, self.target))
            
            if self.config.get('http_methods', True):
                modules.append(self.check_http_methods(client, self.target))
            
            if self.config.get('vuln_check', True):
                modules.append(self.check_for_vulnerabilities(client, self.target, initial_response.text, initial_response.headers))
            
            # Run initial modules
            if modules:
                await asyncio.gather(*modules)
            
            # Run resource-intensive scans sequentially
            if self.config.get('port_scan', True):
                console.print("\n[cyan][*][/cyan] Starting port scan...")
                await self.enhanced_port_scan()
            
            if self.config.get('takeover_check', True):
                console.print("[cyan][*][/cyan] Checking for subdomain takeover...")
                await self.check_subdomain_takeover()
            
            if self.config.get('js_analyze', True):
                console.print("[cyan][*][/cyan] Analyzing JavaScript files...")
                await self.extract_js_endpoints(client, self.target, initial_response.text)
            
            if self.config.get('sensitive_files', True):
                console.print("[cyan][*][/cyan] Checking for sensitive files...")
                await self.check_sensitive_files(client)
            
            if self.config.get('directory_brute', True):
                console.print("[cyan][*][/cyan] Performing directory brute force...")
                await self.directory_bruteforce(client)
            
            if self.config.get('crawl', True) and self.config.get('crawl_depth', 1) > 0:
                console.print(f"[cyan][*][/cyan] Crawling (depth: {self.config.get('crawl_depth', 1)})...")
                await self.crawl_spider(client, self.target, max_depth=self.config.get('crawl_depth', 1))
        
        # Generate report
        self.generate_enhanced_report()

    # --- Enhanced Reporting ---
    def generate_enhanced_report(self):
        """Generate comprehensive HTML report"""
        
        # Calculate scan statistics
        scan_duration = datetime.now() - self.stats["start_time"]
        
        # Severity counts
        severity_counts = {}
        for finding in self.findings:
            severity = finding.get('severity', 'Info')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Category breakdown
        category_counts = {}
        for finding in self.findings:
            category = finding.get('category', 'Unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # HTML Template
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bug Hunter Report - {{ target }}</title>
    <style>
        :root {
            --critical: #dc3545;
            --high: #fd7e14;
            --medium: #ffc107;
            --low: #28a745;
            --info: #17a2b8;
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
            background: linear-gradient(90deg, var(--critical), var(--high), var(--medium), var(--low), var(--info));
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
        .severity-card.Critical { border-top: 4px solid var(--critical); }
        .severity-card.High { border-top: 4px solid var(--high); }
        .severity-card.Medium { border-top: 4px solid var(--medium); }
        .severity-card.Low { border-top: 4px solid var(--low); }
        .severity-card.Info { border-top: 4px solid var(--info); }
        .severity-count.Critical { color: var(--critical); }
        .severity-count.High { color: var(--high); }
        .severity-count.Medium { color: var(--medium); }
        .severity-count.Low { color: var(--low); }
        .severity-count.Info { color: var(--info); }
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
        .severity-badge.Critical { background: var(--critical); }
        .severity-badge.High { background: var(--high); }
        .severity-badge.Medium { background: var(--medium); }
        .severity-badge.Low { background: var(--low); }
        .severity-badge.Info { background: var(--info); }
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
            background: linear-gradient(90deg, var(--low), var(--medium), var(--high), var(--critical));
            width: {{ risk_percentage }}%;
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
                alert('Copied to clipboard!');
            });
        }
        function filterTable(severity) {
            var rows = document.querySelectorAll('#findings-table tr');
            rows.forEach(function(row, index) {
                if (index === 0) return; // Skip header
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
            <h1>🐛 Bug Hunter Report</h1>
            <div class="subtitle">
                <strong>Target:</strong> {{ target }}<br>
                <strong>Scan Date:</strong> {{ scan_date }}<br>
                <strong>Duration:</strong> {{ duration }}
            </div>
        </div>
        
        <div class="risk-meter">
            <div class="risk-fill"></div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-number">{{ findings_count }}</span>
                <span class="stat-label">Total Findings</span>
            </div>
            <div class="stat-card severity-card Critical">
                <span class="stat-number severity-count Critical">{{ severity_counts.Critical or 0 }}</span>
                <span class="stat-label">Critical</span>
            </div>
            <div class="stat-card severity-card High">
                <span class="stat-number severity-count High">{{ severity_counts.High or 0 }}</span>
                <span class="stat-label">High</span>
            </div>
            <div class="stat-card severity-card Medium">
                <span class="stat-number severity-count Medium">{{ severity_counts.Medium or 0 }}</span>
                <span class="stat-label">Medium</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{{ technologies|length }}</span>
                <span class="stat-label">Technologies</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{{ open_ports|length }}</span>
                <span class="stat-label">Open Ports</span>
            </div>
        </div>
        
        <div class="summary-section">
            <h3>🎯 Target Summary</h3>
            <p><strong>Domain:</strong> {{ domain }}</p>
            <p><strong>Scan Configuration:</strong> {{ config_summary }}</p>
            
            <h3>🔧 Detected Technologies</h3>
            <div class="tech-list">
                {% for tech in technologies %}
                <div class="tech-tag {% if tech.version %}version{% endif %}">
                    {{ tech.name }}{% if tech.version %} ({{ tech.version }}){% endif %}
                </div>
                {% endfor %}
            </div>
            
            <h3>🔓 Open Ports</h3>
            <div class="port-list">
                {% for port in open_ports %}
                <div class="port-item" title="{{ port.banner }}">
                    {{ port.port }} ({{ port.service }})
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div style="margin: 30px 0;">
            <button onclick="filterTable('all')" class="btn">All</button>
            <button onclick="filterTable('Critical')" class="btn" style="background: var(--critical);">Critical</button>
            <button onclick="filterTable('High')" class="btn" style="background: var(--high);">High</button>
            <button onclick="filterTable('Medium')" class="btn" style="background: var(--medium);">Medium</button>
            <button onclick="filterTable('Low')" class="btn" style="background: var(--low);">Low</button>
        </div>
        
        <h3>📋 Findings</h3>
        <table id="findings-table">
            <thead>
                <tr>
                    <th>Severity</th>
                    <th>Category</th>
                    <th>URL</th>
                    <th>Details</th>
                    <th>Time</th>
                </tr>
            </thead>
            <tbody>
                {% for f in findings %}
                <tr>
                    <td><span class="severity-badge {{ f.severity }}">{{ f.severity }}</span></td>
                    <td>{{ f.category }}</td>
                    <td>
                        <a href="{{ f.url }}" target="_blank">{{ f.url|truncate(40) }}</a>
                        {% if f.confidence != 'Medium' %}
                        <br><small>Confidence: {{ f.confidence }}</small>
                        {% endif %}
                    </td>
                    <td>
                        {{ f.details|truncate(60) }}
                        {% if f.details|length > 60 %}
                        <span class="details-popup" onclick="showDetails('{{ loop.index }}')">[...]</span>
                        <div id="details-{{ loop.index }}" class="popup-content">
                            <strong>Details:</strong><br>{{ f.details }}<br><br>
                            {% if f.exploit_poc %}
                            <strong>PoC:</strong><br>{{ f.exploit_poc }}<br>
                            {% endif %}
                            {% if f.remediation %}
                            <strong>Remediation:</strong><br>{{ f.remediation }}
                            {% endif %}
                        </div>
                        {% endif %}
                    </td>
                    <td class="timestamp">{{ f.timestamp }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <div class="export-buttons">
            <a href="findings.json" class="btn btn-json">Export JSON</a>
            <a href="findings.csv" class="btn btn-csv">Export CSV</a>
            <a href="report.pdf" class="btn">Generate PDF</a>
        </div>
        
        <div style="margin-top: 40px; text-align: center; color: #666; font-size: 0.9em;">
            <p>Generated by Bug Hunter V3 | Security Assessment Tool</p>
            <p>For authorized testing only. Report contains sensitive information.</p>
        </div>
    </div>
</body>
</html>
"""
        
        from jinja2 import Template
        
        # Calculate risk percentage (simple heuristic)
        risk_score = 0
        for finding in self.findings:
            if finding['severity'] == 'Critical':
                risk_score += 10
            elif finding['severity'] == 'High':
                risk_score += 5
            elif finding['severity'] == 'Medium':
                risk_score += 2
            elif finding['severity'] == 'Low':
                risk_score += 1
        
        risk_percentage = min(risk_score, 100)
        
        # Prepare data for template
        config_summary = []
        if self.config.get('port_scan'):
            config_summary.append("Port Scan")
        if self.config.get('js_analyze'):
            config_summary.append("JS Analysis")
        if self.config.get('takeover_check'):
            config_summary.append("Subdomain Takeover")
        if self.config.get('crawl'):
            config_summary.append(f"Crawl (depth={self.config.get('crawl_depth', 1)})")
        
        t = Template(html_template)
        output = t.render(
            target=self.target,
            domain=self.domain,
            scan_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            duration=str(scan_duration).split('.')[0],
            findings=self.findings,
            findings_count=len(self.findings),
            severity_counts=severity_counts,
            technologies=self.technologies,
            open_ports=self.open_ports,
            risk_percentage=risk_percentage,
            config_summary=", ".join(config_summary) if config_summary else "Default"
        )
        
        report_file = os.path.join(self.out_dir, "report.html")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(output)
        
        # Also save raw findings as JSON
        with open(os.path.join(self.out_dir, "findings.json"), "w", encoding="utf-8") as f:
            json.dump({
                "target": self.target,
                "scan_date": datetime.now().isoformat(),
                "duration": str(scan_duration),
                "findings": self.findings,
                "technologies": self.technologies,
                "open_ports": self.open_ports,
                "stats": self.stats
            }, f, indent=2, default=str)
        
        console.print(f"\n[green]✓[/green] HTML Report generated: [underline]{report_file}[/underline]")
        console.print(f"[green]✓[/green] JSON export available: [underline]{os.path.join(self.out_dir, 'findings.json')}[/underline]")
        
        return report_file

# ---------------- Enhanced UI ----------------
def enhanced_curses_ui(stdscr):
    """Enhanced curses interface with better UX"""
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    
    # Define color pairs
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
    
    config = {
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
    
    menu_items = [
        ("Target URL", "target", "str"),
        ("Concurrency", "concurrency", "toggle", [25, 50, 100]),
        ("Port Scanning", "port_scan", "bool"),
        ("JS Analysis", "js_analyze", "bool"),
        ("Subdomain Takeover", "takeover_check", "bool"),
        ("Sensitive Files", "sensitive_files", "bool"),
        ("Directory Brute Force", "directory_brute", "bool"),
        ("Web Crawling", "crawl", "bool"),
        ("Crawl Depth", "crawl_depth", "toggle", [1, 2, 3]),
        ("Tech Detection", "tech_detect", "bool"),
        ("Security Headers", "security_headers", "bool"),
        ("CORS Check", "cors_check", "bool"),
        ("HTTP Methods", "http_methods", "bool"),
        ("Vulnerability Checks", "vuln_check", "bool"),
        ("[ START COMPREHENSIVE SCAN ]", "start", "action"),
        ("[ QUICK SCAN (Recommended) ]", "quick", "action"),
        ("[ LOAD CONFIGURATION ]", "load", "action"),
        ("[ SAVE CONFIGURATION ]", "save", "action"),
        ("[ EXIT ]", "exit", "action")
    ]
    
    current_row = 0
    config_page = 0
    items_per_page = 15
    
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Title
        title = " BUG HUNTER ULTIMATE V3 "
        subtitle = " Advanced Vulnerability Scanner "
        stdscr.attron(CYAN | curses.A_BOLD)
        stdscr.addstr(1, width//2 - len(title)//2, title)
        stdscr.addstr(2, width//2 - len(subtitle)//2, subtitle)
        stdscr.attroff(CYAN | curses.A_BOLD)
        
        # Draw menu with pagination
        start_idx = config_page * items_per_page
        end_idx = min(start_idx + items_per_page, len(menu_items))
        
        for idx in range(start_idx, end_idx):
            item, key, item_type, *extra = menu_items[idx]
            y = 5 + (idx - start_idx)
            
            # Prepare display value
            if item_type == "str":
                val = config[key] if config[key] else "<not set>"
            elif item_type == "bool":
                val = "✓ ON" if config[key] else "✗ OFF"
            elif item_type == "toggle":
                options = extra[0]
                current_val = config[key]
                if current_val in options:
                    current_idx = options.index(current_val)
                    val = f"{current_val} ({current_idx+1}/{len(options)})"
                else:
                    val = str(current_val)
            elif item_type == "action":
                val = ""
            else:
                val = str(config.get(key, ""))
            
            # Truncate if too long
            display = f"{item:30} {val}"
            if len(display) > width - 10:
                display = display[:width - 13] + "..."
            
            x = width//2 - len(display)//2
            
            if idx == current_row:
                stdscr.attron(CYAN_REV)
                stdscr.addstr(y, x, display)
                stdscr.attroff(CYAN_REV)
            else:
                # Color code by type
                if item_type == "action":
                    if "START" in item or "SCAN" in item:
                        stdscr.attron(GREEN | curses.A_BOLD)
                    elif "EXIT" in item:
                        stdscr.attron(RED | curses.A_BOLD)
                    else:
                        stdscr.attron(MAGENTA)
                stdscr.addstr(y, x, display)
                if item_type == "action":
                    if "START" in item or "SCAN" in item:
                        stdscr.attroff(GREEN | curses.A_BOLD)
                    elif "EXIT" in item:
                        stdscr.attroff(RED | curses.A_BOLD)
                    else:
                        stdscr.attroff(MAGENTA)
        
        # Page indicator
        total_pages = (len(menu_items) + items_per_page - 1) // items_per_page
        if total_pages > 1:
            page_info = f" Page {config_page + 1}/{total_pages} "
            stdscr.addstr(height - 3, width//2 - len(page_info)//2, page_info, curses.A_REVERSE)
        
        # Help text
        help_text = "↑↓: Navigate  Enter: Select  Space: Toggle  q: Quit  s: Start"
        stdscr.addstr(height - 2, width//2 - len(help_text)//2, help_text, curses.A_DIM)
        
        key = stdscr.getch()
        
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
            if current_row < start_idx:
                config_page = max(0, config_page - 1)
        elif key == curses.KEY_DOWN and current_row < len(menu_items) - 1:
            current_row += 1
            if current_row >= end_idx:
                config_page = min(total_pages - 1, config_page + 1)
        elif key in [10, 13]:  # Enter
            item, key, item_type, *extra = menu_items[current_row]
            
            if item_type == "str":
                curses.echo()
                stdscr.addstr(height - 5, width//2 - 10, " " * 50)
                stdscr.addstr(height - 5, width//2 - 10, f"{item}: ")
                stdscr.refresh()
                input_str = stdscr.getstr(height - 5, width//2 - 10 + len(item) + 2, 100)
                config[key] = input_str.decode('utf-8').strip()
                curses.noecho()
            elif item_type == "bool":
                config[key] = not config[key]
            elif item_type == "toggle":
                options = extra[0]
                current_val = config[key]
                if current_val in options:
                    current_idx = options.index(current_val)
                    config[key] = options[(current_idx + 1) % len(options)]
                else:
                    config[key] = options[0]
            elif item_type == "action":
                if key == "start":
                    if config["target"]:
                        break
                    else:
                        # Show error
                        stdscr.addstr(height - 5, width//2 - 15, "Please set target URL first!", RED | curses.A_BOLD)
                        stdscr.getch()
                elif key == "quick":
                    # Set quick scan defaults
                    config.update({
                        "concurrency": 50,
                        "port_scan": True,
                        "js_analyze": True,
                        "sensitive_files": True,
                        "crawl": True,
                        "crawl_depth": 1,
                        "tech_detect": True
                    })
                    if config["target"]:
                        break
                elif key == "load":
                    # Load config from file
                    try:
                        curses.echo()
                        stdscr.addstr(height - 5, width//2 - 15, "Config file: ")
                        file_path = stdscr.getstr(height - 5, width//2 - 2, 100).decode('utf-8')
                        if os.path.exists(file_path):
                            with open(file_path, 'r') as f:
                                loaded = json.load(f)
                                config.update(loaded)
                        curses.noecho()
                    except:
                        pass
                elif key == "save":
                    # Save config to file
                    try:
                        curses.echo()
                        stdscr.addstr(height - 5, width//2 - 15, "Save to: ")
                        file_path = stdscr.getstr(height - 5, width//2 - 7, 100).decode('utf-8')
                        with open(file_path, 'w') as f:
                            json.dump(config, f, indent=2)
                        curses.noecho()
                    except:
                        pass
                elif key == "exit":
                    sys.exit(0)
        elif key == 32:  # Space
            # Toggle boolean items
            item, key, item_type, *extra = menu_items[current_row]
            if item_type == "bool":
                config[key] = not config[key]
        elif key in [81, 113]:  # Q or q
            if Confirm.ask("Exit Bug Hunter?"):
                sys.exit(0)
    
    return config

def quick_cli_mode():
    """Quick command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bug Hunter Ultimate V3")
    parser.add_argument("target", help="Target URL or domain")
    parser.add_argument("-o", "--output", help="Output directory")
    parser.add_argument("--quick", action="store_true", help="Quick scan mode")
    parser.add_argument("--full", action="store_true", help="Full comprehensive scan")
    parser.add_argument("--no-port-scan", action="store_true", help="Disable port scanning")
    parser.add_argument("--concurrency", type=int, default=50, help="Concurrent connections")
    parser.add_argument("--save-config", help="Save configuration to file")
    parser.add_argument("--load-config", help="Load configuration from file")
    
    args = parser.parse_args()
    
    # Default config
    config = {
        "target": args.target,
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
        config.update({
            "crawl_depth": 3,
            "directory_brute": True,
            "concurrency": 100
        })
    
    if args.load_config and os.path.exists(args.load_config):
        with open(args.load_config, 'r') as f:
            loaded = json.load(f)
            config.update(loaded)
    
    if args.save_config:
        with open(args.save_config, 'w') as f:
            json.dump(config, f, indent=2)
    
    return config

# ---------------- Main Entry Point ----------------
if __name__ == "__main__":
    try:
        console.print(Panel.fit(
            "[bold cyan]🐛 BUG HUNTER ULTIMATE V3[/bold cyan]\n"
            "[yellow]Advanced Vulnerability Scanner[/yellow]\n"
            "[dim]For authorized security testing only[/dim]",
            title="Welcome",
            border_style="cyan"
        ))
        
        # Parse command line or start UI
        if len(sys.argv) > 1:
            config = quick_cli_mode()
        else:
            console.print("\n[cyan]Select interface mode:[/cyan]")
            console.print("1. Interactive Terminal UI (Recommended)")
            console.print("2. Quick CLI Mode")
            console.print("3. Load from config file")
            
            choice = Prompt.ask("Choice", choices=["1", "2", "3"], default="1")
            
            if choice == "1":
                config = curses.wrapper(enhanced_curses_ui)
            elif choice == "2":
                target = Prompt.ask("Target URL")
                config = {
                    "target": target,
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
            elif choice == "3":
                config_file = Prompt.ask("Config file path")
                with open(config_file, 'r') as f:
                    config = json.load(f)
        
        # Setup output directory
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_target = re.sub(r"[^\w\-]", "_", config['target'][:30])
        if config.get('output'):
            out_path = config['output']
        else:
            out_path = os.path.join(os.getcwd(), f"scan_{safe_target}_{ts}")
        
        # Create scanner and run
        scanner = AdvancedScanner(config['target'], out_path, config)
        
        console.rule("[bold cyan]Starting Scan[/bold cyan]")
        console.print(f"Target: [green]{config['target']}[/green]")
        console.print(f"Output: [underline]{out_path}[/underline]")
        console.print(f"Mode: [yellow]{'Quick' if config.get('crawl_depth', 2) == 1 else 'Comprehensive'}[/yellow]")
        console.rule()
        
        # Run the scan
        asyncio.run(scanner.comprehensive_scan())
        
        # Summary
        console.rule("[bold green]Scan Complete[/bold green]")
        
        # Show summary table
        if scanner.findings:
            table = Table(title="Scan Summary")
            table.add_column("Severity", style="bold")
            table.add_column("Count", justify="right")
            table.add_column("Example", style="dim")
            
            severity_groups = {}
            for finding in scanner.findings:
                sev = finding['severity']
                if sev not in severity_groups:
                    severity_groups[sev] = []
                severity_groups[sev].append(finding)
            
            for severity in ["Critical", "High", "Medium", "Low", "Info"]:
                if severity in severity_groups:
                    count = len(severity_groups[severity])
                    example = severity_groups[severity][0]['category'][:30]
                    
                    color = {
                        "Critical": "red",
                        "High": "orange1",
                        "Medium": "yellow",
                        "Low": "green",
                        "Info": "blue"
                    }.get(severity, "white")
                    
                    table.add_row(
                        f"[{color}]{severity}[/{color}]",
                        str(count),
                        example
                    )
            
            console.print(table)
        
        console.print(f"\n[green]Reports generated in:[/green] [underline]{out_path}[/underline]")
        console.print(f"[yellow]Total findings:[/yellow] {len(scanner.findings)}")
        console.print(f"[yellow]Technologies detected:[/yellow] {len(scanner.technologies)}")
        console.print(f"[yellow]Open ports found:[/yellow] {len(scanner.open_ports)}")
        
        if any(f['severity'] == 'Critical' for f in scanner.findings):
            console.print("\n[bold red]⚠  CRITICAL FINDINGS DETECTED! Immediate action required![/bold red]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow][!] Scan interrupted by user.[/yellow]")
    except Exception as e:
        console.print(f"[red][!] Error: {e}[/red]")
        if Confirm.ask("Show detailed traceback?"):
            console.print_exception()
    finally:
        console.print("\n[dim]Bug Hunter completed. Remember: With great power comes great responsibility.[/dim]")
