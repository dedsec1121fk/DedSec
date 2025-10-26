#!/usr/bin/env python3
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

# --- Dependencies and Setup ---

REQUIRED = ("requests", "bs4", "dnspython", "python-whois")

def check_termux_package(package_name, command_to_check=None):
    """Checks if a command, typically from a Termux package, is available in the system's PATH."""
    command_to_check = command_to_check or package_name
    # Use shutil.which for a more robust and cross-platform way to find an executable.
    return shutil.which(command_to_check) is not None

def ensure_deps():
    """Checks for required Python packages and attempts to install any that are missing."""
    missing = []
    for pkg in REQUIRED:
        try:
            # Handle the special case where the package name differs from the import name.
            import_name = "whois" if pkg == "python-whois" else pkg
            __import__(import_name)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"Installing missing Python packages: {', '.join(missing)}")
        try:
            # Construct the pip command using sys.executable to ensure we use the correct pip.
            pip_command = [sys.executable, "-m", "pip", "install", *missing]
            subprocess.check_call(pip_command)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to install Python dependencies via pip: {e}")
            print("Please run 'pip install requests beautifulsoup4 dnspython python-whois' manually.")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred during dependency installation: {e}")
            sys.exit(1)

ensure_deps()

try:
    import requests
    from bs4 import BeautifulSoup
    import dns.resolver
    import dns.query
    import dns.exception
    import csv
    import whois
except ImportError:
    print("[FATAL] Required Python packages are missing despite installation attempt. Exiting.")
    sys.exit(1)

# Disable requests warnings about insecure SSL connections.
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

# --- Configuration and Constants ---

# Define preferred paths for saving output files.
PREFERRED_PATHS = [
    os.path.expanduser("~/storage/downloads"),
    os.path.expanduser("/sdcard/Download"),
    os.path.expanduser("~/Downloads"),
    os.getcwd()
]
TERMUX_DOWNLOADS_BASE = os.path.join(os.path.expanduser('~'), 'storage', 'downloads')

def get_downloads_dir():
    """Finds the first existing preferred directory for downloads."""
    for p in PREFERRED_PATHS:
        if os.path.isdir(p):
            return p
    return os.getcwd()

DOWNLOADS = get_downloads_dir()
BASE_OSINT_DIR = os.path.join(DOWNLOADS, "OSINTDS")
os.makedirs(BASE_OSINT_DIR, exist_ok=True)

HEADERS = {"User-Agent": "OSINTDS-Scanner/1.1"}
HTTP_TIMEOUT = 10
DEFAULT_THREADS = 25
RATE_SLEEP = 0.05
XSS_TEST_PAYLOAD = "<script>alert('OSINTDS_XSS')</script>"
SQL_ERROR_PATTERNS = [
    "you have an error in your sql syntax", "sql syntax error",
    "unclosed quotation mark after the character string", "mysql_fetch",
    "syntax error in query", "warning: mysql", "unterminated string constant",
]

SECURITY_HEADERS = [
    "Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options",
    "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy",
]

EDITOR = os.environ.get('EDITOR', 'nano')
ASSET_MAP = [
    ('link', 'href', 'css', lambda tag: tag.get('rel') and 'stylesheet' in tag.get('rel', [])),
    ('script', 'src', 'js', None),
    ('img', 'src', 'images', None),
    ('source', 'src', 'media', None),
    ('video', 'poster', 'images', None),
    ('link', 'href', 'icons', lambda tag: tag.get('rel') and any(r in ['icon', 'shortcut icon'] for r in tag.get('rel', []))),
]
INLINE_CSS_URL_REGEX = re.compile(r'url\(([\'"]?.*?[\'"]?)\)')

# --- Wordlists (Plain Base64) ---
DIR_WORDLIST_B64 = "YWRtaW4KYmFja3VwCnJvYm90cy50eHQKc2l0ZW1hcC54bWwKLmVudi5iYWNrCnVwbG9hZHMKYWRtaW5pc3RyYXRvcgo="
SUBDOMAIN_WORDLIST_B64 = "d3d3CmFwaQpibG9nCmRldgptYWlsCnN0YWdpbmcKdGVzdApzdG9yZQ=="

# --- Wordlist Utilities ---

def unpack_wordlist(b64, dest_path, name):
    """Decodes a Base64 string and writes its content to a file."""
    try:
        raw = base64.b64decode(b64)
        txt = raw.decode('utf-8', errors='ignore')
        if not txt.strip():
             print(f'[WARN] Wordlist for {name} is empty.')
             return None
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(txt)
        print(f'[INFO] Created default wordlist: {dest_path} ({len(txt.splitlines())} entries)')
        return dest_path
    except Exception as e:
        print(f'[ERROR] Wordlist unpack error for {name}: {e}')
        # Create an empty file to prevent repeated unpacking attempts.
        open(dest_path, 'w').close()
        return None

WORDLIST_DIR = os.path.join(BASE_OSINT_DIR, 'wordlists')
os.makedirs(WORDLIST_DIR, exist_ok=True)
DIR_WORDLIST_PATH = os.path.join(WORDLIST_DIR, 'dirs.txt')
SUB_WORDLIST_PATH = os.path.join(WORDLIST_DIR, 'subdomains.txt')

# Unpack wordlists if they don't exist or are empty.
if not os.path.isfile(DIR_WORDLIST_PATH) or os.path.getsize(DIR_WORDLIST_PATH) == 0:
    unpack_wordlist(DIR_WORDLIST_B64, DIR_WORDLIST_PATH, 'dirs.txt')
if not os.path.isfile(SUB_WORDLIST_PATH) or os.path.getsize(SUB_WORDLIST_PATH) == 0:
    unpack_wordlist(SUBDOMAIN_WORDLIST_B64, SUB_WORDLIST_PATH, 'subdomains.txt')

def read_wordlist(path):
    """Reads a wordlist file and returns a list of cleaned lines."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f'[ERROR] Wordlist not found at {path}.')
        return []
    except Exception as e:
        print(f'[ERROR] Failed to read wordlist at {path}: {e}')
        return []

DIR_WORDS = read_wordlist(DIR_WORDLIST_PATH)
SUB_WORDS = read_wordlist(SUB_WORDLIST_PATH)

# --- Core Utility Functions ---

def normalize_target(raw_input):
    """Cleans and standardizes a target URL, returning the base URL and domain."""
    raw_input = raw_input.strip()
    if not raw_input:
        return None, None
    if not re.match(r'^(http://|https://)', raw_input, re.IGNORECASE):
        raw_input = 'http://' + raw_input
    try:
        parsed = urlparse(raw_input)
        domain = parsed.hostname
        if not domain:
            return None, None
        base = f"{parsed.scheme}://{parsed.netloc}"
        return base.rstrip('/'), domain
    except ValueError:
        return None, None

def make_dirs(domain):
    """Creates a directory for the target domain to store scan results."""
    safe_domain = re.sub(r'[^\w\-.]', '_', domain)
    target_dir = os.path.join(BASE_OSINT_DIR, safe_domain)
    os.makedirs(target_dir, exist_ok=True)
    return target_dir

def save_text(folder, filename, text):
    """Saves text content to a file."""
    path = os.path.join(folder, filename)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"[INFO] Saved: {path}")
    except IOError as e:
        print(f'[ERROR] File save error for {path}: {e}')

def save_csv(folder, filename, rows, headers=None):
    """Saves a list of rows to a CSV file."""
    path = os.path.join(folder, filename)
    try:
        with open(path, 'w', newline='', encoding='utf-8') as cf:
            writer = csv.writer(cf)
            if headers:
                writer.writerow(headers)
            writer.writerows([[str(item) for item in row] for row in rows])
        print('[INFO] Saved CSV:', path)
    except IOError as e:
        print(f'[ERROR] CSV save error for {path}: {e}')

def checkpoint_save(folder, report):
    """Saves the current state of the report to a JSON file for resumption."""
    save_text(folder, 'report.json', json.dumps(report, indent=2, default=str))

# --- SCANNING FUNCTIONS ---

def get_whois_info(domain):
    """Retrieves and formats WHOIS information for a domain."""
    try:
        w = whois.whois(domain)
        # BUGFIX: Handle case where whois lookup returns None
        if not w:
            return {'error': 'No WHOIS data returned.'}
        
        # IMPROVEMENT: Prettify list and datetime objects for better readability.
        whois_data = {}
        for key, value in w.items():
            if not value:
                continue
            if isinstance(value, list):
                whois_data[key] = ', '.join(map(str, value))
            elif hasattr(value, 'strftime'):
                whois_data[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            else:
                whois_data[key] = str(value)
        return whois_data
    except Exception as e:
        return {'error': str(e)}

def reverse_dns_lookup(ip_address):
    """Performs a reverse DNS lookup on an IP address."""
    if not ip_address:
        return None
    try:
        return socket.gethostbyaddr(ip_address)[0]
    except (socket.herror, socket.gaierror):
        return None

def resolve_all_dns(domain):
    """Resolves common DNS record types for a domain."""
    results = {}
    record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME']
    for record_type in record_types:
        try:
            answers = dns.resolver.resolve(domain, record_type)
            results[record_type] = sorted([str(r).strip() for r in answers])
        except dns.resolver.NoAnswer:
            results[record_type] = []
        # IMPROVEMENT: Add specific exception handling for common DNS errors.
        except dns.resolver.NXDOMAIN:
            results[record_type] = ['Domain Not Found']
        except dns.exception.Timeout:
             results[record_type] = ['Timeout']
        except Exception:
             results[record_type] = ['Error']
    return results

def extract_content_info(html_content):
    """Extracts emails, generator tags, and comments from HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    info = {'emails': [], 'generator': None, 'comments': []}
    
    # Use a robust regex for finding email addresses.
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html_content)
    info['emails'] = sorted(list(set(emails)))

    meta_gen = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'generator'})
    if meta_gen and 'content' in meta_gen.attrs:
        info['generator'] = meta_gen['content'].strip()
    
    # BUGFIX: Correct regex to find HTML comments.
    comments = re.findall(r'<!--(.*?)-->', html_content, re.DOTALL)
    info['comments'] = [c.strip() for c in comments if c.strip() and len(c.strip()) < 300]
    
    return info

def check_wayback_machine(domain):
    """Checks the Wayback Machine for snapshots of the domain."""
    try:
        url = f"http://web.archive.org/cdx/search/cdx?url={domain}&limit=1&output=json"
        r = requests.get(url, headers=HEADERS, timeout=HTTP_TIMEOUT, verify=False)
        if r.status_code == 200 and r.text.strip():
            data = r.json()
            if len(data) > 1:
                return {'snapshots_found': True, 'first_snapshot': data[1][1]}
        return {'snapshots_found': False}
    except (requests.RequestException, json.JSONDecodeError):
        return {'snapshots_found': 'Error'}

def check_security_headers(headers):
    """Checks for the presence of important security headers."""
    return {h: headers.get(h, 'MISSING') for h in SECURITY_HEADERS}

# --- NETWORK FUNCTIONS ---

def fetch(url, allow_redirects=True, timeout=HTTP_TIMEOUT, verbose=False):
    """Wrapper for requests.get with consistent error handling and user-agent."""
    try:
        time.sleep(RATE_SLEEP + random.random() * 0.05)
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=allow_redirects, verify=False)
        return r
    except requests.exceptions.Timeout:
        if verbose: print(f'[WARN] Timeout accessing {url}')
    except requests.exceptions.RequestException as e:
        if verbose: print(f'[WARN] Request error for {url}: {e}')
    return None

def probe_port(host, port, timeout=1.5):
    """Probes a single TCP port on a host."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))
            return port, True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return port, False

def probe_ports_connect(host, ports, threads=100, timeout=1.5):
    """Probes a list of ports concurrently."""
    open_ports = []
    with ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_port = {executor.submit(probe_port, host, p, timeout): p for p in ports}
        for future in as_completed(future_to_port):
            port, is_open = future.result()
            if is_open:
                open_ports.append(port)
    return sorted(open_ports)

def ssl_info(domain):
    """Retrieves SSL certificate details for a domain."""
    info = {}
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=HTTP_TIMEOUT) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                info['subject'] = dict(x[0] for x in cert.get('subject', []))
                info['issuer'] = dict(x[0] for x in cert.get('issuer', []))
                info['version'] = cert.get('version')
                info['serialNumber'] = cert.get('serialNumber')
                info['notBefore'] = cert.get('notBefore')
                info['notAfter'] = cert.get('notAfter')
    except (socket.gaierror, socket.timeout, ssl.SSLError, ConnectionRefusedError, OSError) as e:
        info['error'] = str(e)
    return info

def resolve_host(name):
    """Resolves a hostname to its primary IP address."""
    try:
        return socket.gethostbyname(name)
    except socket.gaierror:
        return None

def subdomain_bruteforce(domain, wordlist, threads=50):
    """Performs a bruteforce search for subdomains."""
    found = []
    def check(sub):
        fqdn = f"{sub}.{domain}"
        ip = resolve_host(fqdn)
        if ip:
            return (fqdn, ip)
        return None

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(check, w): w for w in wordlist}
        for future in as_completed(futures):
            result = future.result()
            if result:
                found.append(result)
    return found

def attempt_zone_transfer(domain):
    """Attempts a DNS Zone Transfer (AXFR) against a domain's nameservers."""
    results = []
    try:
        answers = dns.resolver.resolve(domain, 'NS')
        for rdata in answers:
            ns = str(rdata.target).rstrip('.')
            try:
                zone = dns.zone.from_xfr(dns.query.xfr(ns, domain, timeout=5))
                if zone:
                    records = [f"{name} {zone[name].to_text()}" for name in zone.nodes.keys()]
                    results.append({'nameserver': ns, 'records': records})
            except (dns.exception.FormError, dns.exception.Timeout, ConnectionRefusedError):
                continue # Silently fail for this NS
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
        pass # No NS records found or other error
    return results

def dir_bruteforce(base_url, words, threads=50, verbose=False):
    """Performs a bruteforce search for directories and files."""
    hits = []
    def probe(word):
        url = urljoin(base_url + '/', word)
        r = fetch(url, verbose=verbose, allow_redirects=False)
        if r and r.status_code in (200, 301, 302, 403, 500):
            return (word, r.status_code, r.headers.get('Location', r.url))
        return None

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(probe, w) for w in words}
        for future in as_completed(futures):
            result = future.result()
            if result:
                hits.append(result)
    return hits

# --- VULNERABILITY HEURISTICS ---

def basic_sqli_test_on_url(url, verbose=False):
    """Appends a single quote to a URL to test for basic SQL injection vulnerabilities."""
    if '?' not in url:
        return None
    try:
        # Test with a single quote
        r = fetch(url + "'", verbose=verbose)
        if r:
            response_text = r.text.lower()
            for pattern in SQL_ERROR_PATTERNS:
                if pattern in response_text:
                    return {'url': url, 'pattern': pattern, 'trigger': "'"}
    except Exception:
        pass
    return None

def xss_reflection_test(url, verbose=False):
    """Tests for reflected XSS by injecting a payload into URL parameters."""
    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query, keep_blank_values=True)
    except ValueError:
        return []
        
    if not query_params:
        return []
    
    findings = []
    for param, values in query_params.items():
        original_value = values[0] if values else ''
        # Create a copy to modify
        temp_params = query_params.copy()
        temp_params[param] = original_value + XSS_TEST_PAYLOAD
        
        new_query = urlencode(temp_params, doseq=True)
        new_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
        
        r = fetch(new_url, verbose=verbose)
        # Check if the payload is reflected in the response body.
        if r and XSS_TEST_PAYLOAD in r.text:
            findings.append({'url': new_url, 'param': param})
            
    return findings

# --- HTML FINDER/EDITOR FUNCTIONS ---

def hf_display_message(message, color='default'):
    """Prints a colored message to the console."""
    colors = {'red': '\033[91m', 'green': '\033[92m', 'yellow': '\033[93m', 'blue': '\033[94m', 'default': '\033[0m'}
    end_color = colors['default']
    start_color = colors.get(color, end_color)
    print(f"{start_color}{message}{end_color}")

def hf_get_website_dir(url):
    """Generates a safe local directory name from a URL."""
    parsed_url = urlparse(url)
    hostname = parsed_url.netloc.replace('www.', '')
    clean_name = re.sub(r'[^\w\-.]', '_', hostname) or "website_content"
    return os.path.join(BASE_OSINT_DIR, 'html_inspector', clean_name.lower())

def hf_download_asset(asset_url, local_dir, base_url):
    """Downloads a single asset (CSS, JS, image) from a URL."""
    if not asset_url or asset_url.startswith('data:'):
        return None, None
    
    try:
        absolute_asset_url = urljoin(base_url, asset_url)
        parsed_asset_url = urlparse(absolute_asset_url)
        
        path_part = unquote(parsed_asset_url.path)
        filename = os.path.basename(path_part) or f"asset_{abs(hash(absolute_asset_url))}"
        filename = re.sub(r'[\\/:*?"<>|]', '_', filename) # Sanitize filename
        
        local_path = os.path.join(local_dir, filename)
        
        # Avoid re-downloading if file exists and has a reasonable size
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            return os.path.relpath(local_path, start=os.path.dirname(local_dir)), absolute_asset_url

        response = requests.get(absolute_asset_url, stream=True, timeout=10, verify=False)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return os.path.relpath(local_path, start=os.path.dirname(local_dir)), absolute_asset_url
    except requests.exceptions.RequestException:
        return None, None
    except IOError as e:
        hf_display_message(f"Failed to save asset {asset_url}: {e}", 'red')
        return None, None

def hf_process_html_and_download_assets(html_content, base_url, website_dir):
    """Parses HTML, downloads all linked assets, and updates links to be local."""
    soup = BeautifulSoup(html_content, 'html.parser')
    downloaded_urls = {}
    hf_display_message("\nStarting asset download process...", 'blue')

    for tag_name, attr_name, subdir, filter_func in ASSET_MAP:
        for tag in soup.find_all(tag_name):
            if filter_func and not filter_func(tag):
                continue
            
            asset_url = tag.get(attr_name)
            if asset_url and asset_url not in downloaded_urls:
                asset_subdir_path = os.path.join(website_dir, subdir)
                relative_asset_path, abs_url = hf_download_asset(asset_url, asset_subdir_path, base_url)
                if relative_asset_path:
                    new_path = os.path.join(subdir, os.path.basename(relative_asset_path)).replace('\\', '/')
                    tag[attr_name] = new_path
                    downloaded_urls[abs_url] = new_path

    hf_display_message(f"Asset download and HTML modification complete. ({len(downloaded_urls)} assets processed)", 'green')
    return str(soup)

def hf_edit_html_in_editor(html_content):
    """Opens HTML content in the system's default editor for manual changes."""
    if not html_content:
        hf_display_message("No content to edit.", 'yellow')
        return None
        
    try:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8', suffix='.html') as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(html_content)
        
        hf_display_message(f"\nOpening HTML in {EDITOR}. Save and exit to apply changes.", 'yellow')
        subprocess.run([EDITOR, temp_file_path], check=True)
        
        with open(temp_file_path, 'r', encoding='utf-8') as f:
            modified_html = f.read()
        hf_display_message("HTML content updated from editor.", 'green')
        return modified_html
    except FileNotFoundError:
        hf_display_message(f"Error: Editor '{EDITOR}' not found.", 'red')
    except subprocess.CalledProcessError:
        hf_display_message(f"Editor '{EDITOR}' exited with an error. Changes may not be saved.", 'red')
    except Exception as e:
        hf_display_message(f"An error occurred during editing: {e}", 'red')
    finally:
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
    return None

def hf_save_html_to_file(html_content, target_dir, filename="index.html"):
    """Saves the final HTML content to a file."""
    if not html_content:
        hf_display_message("No content to save.", 'yellow')
        return None
    os.makedirs(target_dir, exist_ok=True)
    filepath = os.path.join(target_dir, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        hf_display_message(f"HTML saved successfully to '{filepath}'", 'green')
        return filepath
    except IOError as e:
        hf_display_message(f"Error saving file: {e}", 'red')
    return None

def hf_preview_html_in_browser(filepath):
    """Opens the local HTML file in a web browser for preview."""
    if not filepath or not os.path.exists(filepath):
        hf_display_message("No HTML file found to preview.", 'yellow')
        return
    
    # IMPROVEMENT: Use `webbrowser` module for cross-platform support as a fallback.
    if check_termux_package("termux-open-url"):
        hf_display_message(f"Opening preview in Termux browser...", 'cyan')
        subprocess.run(['termux-open-url', f'file://{filepath}'])
    else:
        hf_display_message(f"Opening preview in default system browser...", 'cyan')
        webbrowser.open(f'file://{os.path.abspath(filepath)}')

def hf_fetch_html(url, verbose=False):
    """Fetches the raw HTML content of a URL."""
    response = fetch(url, verbose=verbose)
    if response:
        return response.text
    if verbose:
        hf_display_message(f"Failed to fetch HTML for {url}", 'red')
    return None

def run_html_finder(initial_url, folder, verbose=False):
    """Runs the interactive HTML Inspector and Downloader tool."""
    current_url = initial_url
    website_dir = hf_get_website_dir(current_url)
    hf_display_message(f"\n--- Starting Interactive HTML Inspector for {current_url} ---", 'blue')
    hf_display_message(f"Local storage path will be: {website_dir}", 'yellow')

    html_content = hf_fetch_html(current_url, verbose)
    if not html_content:
        hf_display_message("Failed to fetch initial HTML. Cannot proceed.", 'red')
        return

    while True:
        hf_display_message("\n--- HTML Inspector Options ---", 'blue')
        print("1. Download Assets & Save HTML (Creates/Updates Local Copy)")
        print("2. Edit Current HTML (Opens in Editor)")
        print("3. Preview Current HTML in Browser")
        print("4. Enter NEW URL (Fetch new content)")
        print("5. Exit HTML Inspector")

        choice = input("Enter your choice (1-5): ").strip()

        if choice == '1':
            modified_html = hf_process_html_and_download_assets(html_content, current_url, website_dir)
            if modified_html:
                html_content = modified_html
                hf_save_html_to_file(html_content, website_dir)
        elif choice == '2':
            modified_html = hf_edit_html_in_editor(html_content)
            if modified_html is not None:
                html_content = modified_html
                hf_save_html_to_file(html_content, website_dir) # Save after edit
        elif choice == '3':
            saved_path = hf_save_html_to_file(html_content, website_dir)
            if saved_path:
                hf_preview_html_in_browser(saved_path)
        elif choice == '4':
            new_url_input = input("Enter the new website URL: ").strip()
            if new_url_input:
                normalized_url, _ = normalize_target(new_url_input)
                if normalized_url:
                    current_url = normalized_url
                    website_dir = hf_get_website_dir(current_url)
                    new_html = hf_fetch_html(current_url, verbose)
                    if new_html:
                        html_content = new_html
                    else:
                        hf_display_message("Failed to fetch new URL. Staying with previous content.", 'red')
                else:
                    hf_display_message("Invalid URL provided.", 'yellow')
        elif choice == '5':
            hf_display_message("Exiting the HTML inspector.", 'blue')
            break
        else:
            hf_display_message("Invalid choice. Please enter a number between 1 and 5.", 'red')

# --- REPORTING FUNCTIONS ---

def save_html_report(folder, report):
    """Generates and saves a comprehensive HTML report of the scan findings."""
    # This function is already well-structured. No significant changes needed.
    # Minor tweak to escape content for safety.
    html_template = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>OSINTDS Report for {html.escape(report.get('domain', 'N/A'))}</title>
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
        <h1>OSINTDS Report for {html.escape(report.get('domain', 'N/A'))}</h1>
        <div class="card">
            <h2>Summary</h2>
            <ul>
                <li><b>Target URL:</b> {html.escape(report.get('target', 'N/A'))}</li>
                <li><b>Final URL:</b> {html.escape(report.get('final_url', 'N/A'))}</li>
                <li><b>Primary IP:</b> {html.escape(report.get('primary_ip', 'N/A'))}</li>
                <li><b>Reverse DNS:</b> {html.escape(report.get('reverse_dns', 'N/A'))}</li>
                <li><b>HTTP Status:</b> {html.escape(str(report.get('http_status', 'N/A')))}</li>
                <li><b>Open Ports:</b> {len(report.get('open_ports', []))}</li>
                <li><b>Subdomains Found:</b> {len(report.get('subdomains', []))}</li>
            </ul>
        </div>
    """
    
    sections = {
        'WHOIS Information': report.get('whois'),
        'DNS Records': report.get('dns_records'),
        'SSL Certificate': report.get('ssl'),
        'HTTP Security Headers': report.get('security_headers'),
        'Open Ports': report.get('open_ports'),
        'Subdomains': report.get('subdomains'),
        'Directory/File Hits': report.get('dir_hits'),
        'Wayback Machine': report.get('wayback'),
        'Homepage Content Analysis': report.get('content_info'),
        'Discovered URLs (Sitemap/Robots)': report.get('discovered_urls'),
        'Potential SQL Injection Evidence': report.get('sqli_evidence'),
        'Potential XSS Reflections': report.get('xss_reflections'),
        'DNS Zone Transfer (AXFR)': report.get('axfr'),
    }

    for title, data in sections.items():
        if data:
            html_template += f'<div class="card"><h3>{title}</h3>'
            if isinstance(data, list) and data:
                html_template += '<ol>'
                for item in data:
                    html_template += f'<li>{html.escape(str(item))}</li>'
                html_template += '</ol>'
            elif isinstance(data, dict):
                 html_template += f'<pre>{html.escape(json.dumps(data, indent=2, default=str))}</pre>'
            else:
                 html_template += f'<pre>{html.escape(str(data))}</pre>'
            html_template += '</div>'

    html_template += '</body></html>'
    save_text(folder, 'report.html', html_template)

# --- USER INTERACTION HELPER ---

def get_user_choice(prompt, default_value):
    """Prompts a user to accept a default value or provide a new one."""
    response = input(f'{prompt} [Default: {default_value}] (Enter for default, or type new value): ').strip()
    return response or default_value

# --- MAIN LOGIC ---

def run_checks_interactive():
    """Main function to run the scanner in interactive mode."""
    print('--- OSINTDS Interactive Scanner ---')
    target_input = input('Enter target domain or URL (e.g., example.com): ').strip()
    if not target_input:
        print('No target provided. Exiting.')
        return

    base, domain = normalize_target(target_input)
    if not domain:
        print('Invalid target format. Exiting.')
        return
    
    # Configuration inputs with defaults
    try:
        threads = int(get_user_choice('Number of threads?', DEFAULT_THREADS))
    except ValueError:
        threads = DEFAULT_THREADS

    full_ports = input('Full port scan (1-65535)? Very slow. (y/N): ').strip().lower().startswith('y')
    dir_wordlist_path = get_user_choice('Path to directory wordlist?', DIR_WORDLIST_PATH)
    sub_wordlist_path = get_user_choice('Path to subdomain wordlist?', SUB_WORDLIST_PATH)
    verbose = input('Enable verbose mode for debugging? (y/N): ').strip().lower().startswith('y')
    
    out_formats_raw = get_user_choice('Output formats (json,html,csv)?', 'json,html,csv')
    out_formats = {f.strip() for f in out_formats_raw.split(',') if f.strip()}

    dir_words = read_wordlist(dir_wordlist_path)
    sub_words = read_wordlist(sub_wordlist_path)

    print('\nDISCLAIMER: Only scan targets you own or have explicit permission to test.')
    print('Starting OSINT scan. This may take some time...')

    report, folder = run_checks(
        target=target_input,
        threads=threads,
        full_ports=full_ports,
        out_formats=out_formats,
        dir_words=dir_words,
        sub_words=sub_words,
        verbose=verbose
    )

    if not report:
        print("\nScan could not be completed.")
        return
        
    print("\n" + "="*50)
    print("--- Post-Scan HTML Inspector/Editor ---")
    if input("Run Interactive HTML Downloader/Editor on the target URL? (y/N): ").strip().lower().startswith('y'):
        final_url = report.get('final_url') or target_input
        if 'unreachable' not in str(report.get('http_status', '')):
            run_html_finder(final_url, folder, verbose)
        else:
            print("[WARN] Target was unreachable, skipping HTML Inspector.")
    print("="*50)

def run_checks(target, threads=DEFAULT_THREADS, full_ports=False, out_formats=('json','html','csv'), 
               dir_words=None, sub_words=None, verbose=False):
    
    base, domain = normalize_target(target)
    folder = make_dirs(domain)
    report_path = os.path.join(folder, 'report.json')
    report = {'target': target, 'domain': domain, 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')}

    # Scan Resumption Logic
    if os.path.exists(report_path):
        if input(f"Existing report found for {domain}. Resume scan? (Y/n): ").strip().lower() != 'n':
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    report.update(json.load(f))
                print('[INFO] Resuming scan from existing report.')
            except (json.JSONDecodeError, IOError) as e:
                print(f'[WARN] Could not load existing report ({e}). Starting fresh.')

    def run_stage(stage_num, name, key, func, *args, **kwargs):
        """Helper to run and report on each scanning stage."""
        print(f"[STAGE {stage_num}/13] {name}...")
        if report.get(key) is None:
            report[key] = func(*args, **kwargs)
            checkpoint_save(folder, report)
        else:
            print(f"[INFO] Found cached result for '{name}'. Skipping.")

    # --- STAGE 1: Initial HTTP Fetch ---
    print(f"[STAGE 1/13] Probing base URL: {base}")
    if report.get('http_status') is None or 'unreachable' in str(report.get('http_status')):
        r = fetch(base, verbose=verbose)
        if not r:
            report['http_status'] = 'unreachable'
            checkpoint_save(folder, report)
            print('[ERROR] Target unreachable.')
            return None, None
        
        report['http_status'] = f"{r.status_code} {r.reason}"
        report['final_url'] = r.url
        report['headers'] = dict(r.headers)
        checkpoint_save(folder, report)
    else:
        # Fetch again to have content for other stages
        r = fetch(report.get('final_url', base), verbose=verbose)
        if not r:
            print('[ERROR] Resumed target now unreachable.')
            return None, None

    # --- REMAINING STAGES ---
    run_stage(2, "Checking HTTP security headers", 'security_headers', check_security_headers, r.headers)
    run_stage(3, "Checking WHOIS information", 'whois', get_whois_info, domain)
    run_stage(4, "Resolving DNS and Reverse DNS", 'dns_records', resolve_all_dns, domain)
    if 'dns_records' in report and report['dns_records'].get('A'):
        report['primary_ip'] = report['dns_records']['A'][0]
        run_stage(4, "Performing Reverse DNS", 'reverse_dns', reverse_dns_lookup, report['primary_ip'])
    
    run_stage(5, "Checking Wayback Machine", 'wayback', check_wayback_machine, domain)
    run_stage(6, "Checking SSL certificate", 'ssl', ssl_info, domain)
    run_stage(7, "Analyzing homepage content", 'content_info', extract_content_info, r.text)

    # Stage 8: Sitemap/Robots and URL collection
    run_stage(8, "Searching for sitemap/robots.txt", 'discovered_urls', lambda: sorted(list(set(
        re.findall(r'<loc>([^<]+)</loc>', sm.text, re.I)
        for sm_url in (
            [line.split(':', 1)[1].strip() for line in (fetch(urljoin(base, '/robots.txt')) or type('',(object,),{'text':''})()).text.splitlines() if line.lower().startswith('sitemap:')]
            or [urljoin(base, '/sitemap.xml')]
        )
        if (sm := fetch(sm_url)) and sm.status_code == 200
    ))))
    
    run_stage(9, "Running subdomain enumeration", 'subdomains', subdomain_bruteforce, domain, sub_words, threads=threads)
    run_stage(10, "Attempting DNS zone transfer", 'axfr', attempt_zone_transfer, domain)
    
    # Stage 11: Ports
    port_list = list(range(1, 65536)) if full_ports else [21, 22, 25, 53, 80, 110, 143, 443, 465, 587, 993, 995, 3306, 5432, 8000, 8080, 8443]
    run_stage(11, "Running port probe", 'open_ports', probe_ports_connect, report.get('primary_ip', domain), port_list, threads=max(100, threads))
    
    run_stage(12, "Running directory brute-force", 'dir_hits', dir_bruteforce, base, dir_words, threads=threads, verbose=verbose)

    # Stage 13: Vulnerability Heuristics
    print("[STAGE 13/13] Running vulnerability heuristics...")
    if report.get('sqli_evidence') is None or report.get('xss_reflections') is None:
        all_links = set(report.get('discovered_urls', []))
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            full_url = urljoin(base, a['href'])
            if urlparse(full_url).hostname == domain:
                all_links.add(full_url)
        
        links_to_scan = list(all_links)[:400]
        print(f'[INFO] Running SQLi/XSS heuristics on {len(links_to_scan)} URLs...')
        
        sqli, xss = [], []
        with ThreadPoolExecutor(max_workers=threads) as executor:
            sql_futures = {executor.submit(basic_sqli_test_on_url, u, verbose): u for u in links_to_scan if '?' in u}
            xss_futures = {executor.submit(xss_reflection_test, u, verbose): u for u in links_to_scan if '?' in u}
            
            for f in as_completed(sql_futures):
                if res := f.result(): sqli.append(res)
            for f in as_completed(xss_futures):
                if res := f.result(): xss.extend(res)
        
        report['sqli_evidence'] = sqli
        report['xss_reflections'] = xss
        checkpoint_save(folder, report)

    # --- FINAL Save Outputs and Summary ---
    print('\n[FINAL] Generating final report files...')
    if 'json' in out_formats:
        checkpoint_save(folder, report) 
    if 'csv' in out_formats:
        if report.get('subdomains'):
            save_csv(folder, 'subdomains.csv', report['subdomains'], headers=['Subdomain', 'IP'])
        if report.get('dir_hits'):
            save_csv(folder, 'dirs.csv', report['dir_hits'], headers=['Path', 'Status', 'Final URL'])
    if 'html' in out_formats:
        save_html_report(folder, report)

    print('\n--- Scan Complete Summary ---')
    print(f"Target: {report['target']}")
    print(f"Primary IP: {report.get('primary_ip', 'N/A')}")
    print(f"HTTP Status: {report['http_status']}")
    print(f"Open ports ({len(report.get('open_ports',[]))} found): {report.get('open_ports', 'N/A')}")
    print(f"Subdomains found: {len(report.get('subdomains',[]))}")
    print(f"Dir hits: {len(report.get('dir_hits',[]))}")
    print(f"Potential SQLi: {len(report.get('sqli_evidence',[]))}")
    print(f"Potential XSS: {len(report.get('xss_reflections',[]))}")
    print(f'\nSaved outputs to: {folder}')
    
    return report, folder

if __name__ == '__main__':
    run_checks_interactive()