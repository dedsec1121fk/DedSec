#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import importlib
import time
from datetime import datetime
import json
import re
import sqlite3
import threading
from collections import deque
import socket
from urllib.parse import urlparse, urljoin, quote, unquote, parse_qs, urlencode, urlunparse
import base64
import random
import string
import queue
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import html
import tempfile
import webbrowser
import shutil
import zipfile

# --- Dependency Imports & Global Flags ---
CURSES_AVAILABLE = False
COLORS_AVAILABLE = False
SPEEDTEST_AVAILABLE = False
BS4_AVAILABLE = False
REQUESTS_AVAILABLE = False
PARAMIKO_AVAILABLE = False
WHOIS_AVAILABLE = False
DNS_AVAILABLE = False

speedtest = None
requests = None
BeautifulSoup = None
paramiko = None
whois = None
dns_resolver = None
csv = None 

# 1. Curses (TUI)
try:
    import curses
    CURSES_AVAILABLE = True
except ImportError:
    pass

# 2. Colorama
try:
    from colorama import Fore, Style, Back, init
    init()
    COLORS_AVAILABLE = True
except ImportError:
    class DummyColor:
        def __getattr__(self, name): return ''
    Fore = Back = Style = DummyColor()

# 3. Dynamic import attempts
def _try_import(module_name, global_var_name):
    try:
        module = importlib.import_module(module_name)
        globals()[global_var_name] = module
        return True
    except ImportError:
        return False

SPEEDTEST_AVAILABLE = _try_import('speedtest', 'speedtest')
REQUESTS_AVAILABLE = _try_import('requests', 'requests')
if REQUESTS_AVAILABLE:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
BS4_AVAILABLE = _try_import('bs4', 'bs4_module')
if BS4_AVAILABLE:
    BeautifulSoup = bs4_module.BeautifulSoup
PARAMIKO_AVAILABLE = _try_import('paramiko', 'paramiko')
WHOIS_AVAILABLE = _try_import('whois', 'whois')
DNS_AVAILABLE = _try_import('dns.resolver', 'dns_resolver')
_try_import('csv', 'csv') 


def auto_install_dependencies():
    """
    Automatically install all required dependencies without root.
    """
    print(f"{Fore.CYAN}🛠️ DedSec Toolkit - Εγκατάσταση Εξαρτήσεων{Style.RESET_ALL}")
    print("="*60)
    
    is_termux = os.path.exists('/data/data/com.termux')
    
    # System packages for Termux
    termux_packages = ['python', 'python-pip', 'openssl-tool', 'ncurses-utils']
    
    # Python packages
    pip_packages = [
        'requests', 'colorama', 'speedtest-cli', 'beautifulsoup4',
        'paramiko', 'python-whois', 'dnspython'
    ]
    
    if is_termux:
        print(f"\n{Fore.CYAN}[*] Έλεγχος πακέτων Termux...{Style.RESET_ALL}")
        try:
            subprocess.run(['pkg', 'install', '-y'] + termux_packages, capture_output=True)
            print(f"    {Fore.GREEN}✅ Τα πακέτα Termux εγκαταστάθηκαν.{Style.RESET_ALL}")
        except Exception as e:
            print(f"    {Fore.YELLOW}⚠️ Σφάλμα εγκατάστασης πακέτων συστήματος: {e}{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}[*] Εγκατάσταση βιβλιοθηκών Python...{Style.RESET_ALL}")
    for package in pip_packages:
        print(f"    [*] Έλεγχος για {package}...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], capture_output=True)
            print(f"    {Fore.GREEN}✅ {package} έτοιμο.{Style.RESET_ALL}")
        except Exception as e:
            print(f"    {Fore.RED}❌ Αποτυχία εγκατάστασης {package}: {e}{Style.RESET_ALL}")
    
    print(f"\n{Fore.GREEN}🎉 Η εγκατάσταση ολοκληρώθηκε! Επανεκκίνηση...{Style.RESET_ALL}")
    time.sleep(2)
    return True

# --- TUI Helpers ---
def _draw_curses_menu(stdscr, title, options):
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK) 
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK) 
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) 
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN) 
    
    current_row = 0
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        # Center Title
        title_x = max(0, (w // 2) - (len(title) // 2))
        stdscr.attron(curses.A_BOLD | curses.color_pair(2))
        stdscr.addstr(1, title_x, title)
        stdscr.attroff(curses.A_BOLD | curses.color_pair(2))
        
        # Centered Horizontal Rule
        rule = "=" * min(w - 4, 50)
        rule_x = max(0, (w // 2) - (len(rule) // 2))
        stdscr.addstr(2, rule_x, rule)

        for idx, option in enumerate(options):
            y = 4 + idx
            if y >= h - 1: break
            
            # Formatting options to look uniform and centered
            if option.startswith("---"):
                text = option
            else:
                text = f"[ {option} ]"
            
            x = max(0, (w // 2) - (len(text) // 2))
            
            if option.startswith("---"):
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(y, x, text)
                stdscr.attroff(curses.color_pair(3))
            elif idx == current_row:
                stdscr.attron(curses.A_BOLD | curses.color_pair(4))
                stdscr.addstr(y, x, text)
                stdscr.attroff(curses.A_BOLD | curses.color_pair(4))
            else:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, x, text)
                stdscr.attroff(curses.color_pair(1))
        
        stdscr.refresh()
        
        key = stdscr.getch()
        if key == curses.KEY_UP:
            current_row = (current_row - 1) % len(options)
            while options[current_row].startswith("---"):
                current_row = (current_row - 1) % len(options)
        elif key == curses.KEY_DOWN:
            current_row = (current_row + 1) % len(options)
            while options[current_row].startswith("---"):
                current_row = (current_row + 1) % len(options)
        elif key == curses.KEY_ENTER or key in [10, 13]:
            return current_row

# --- Main Logic ---

class AdvancedNetworkTools:
    def __init__(self):
        # Save Directory Setup
        self.is_termux = os.path.exists('/data/data/com.termux')
        if self.is_termux:
            base_dir = os.path.expanduser('~')
            self.save_dir = os.path.join(base_dir, "DedSec_Tools")
        else:
            self.save_dir = os.path.join(os.getcwd(), "DedSec_Tools")

        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        
        self.config_file = os.path.join(self.save_dir, "config.json")
        self.audit_db_name = os.path.join(self.save_dir, "audit_results.db")
        self.wordlist_dir = os.path.join(self.save_dir, "wordlists")
        if not os.path.exists(self.wordlist_dir): os.makedirs(self.wordlist_dir)

        self.init_audit_database()
        self.load_config()
        
        self.max_workers = self.config.get('max_scan_workers', 15)
        self.scan_timeout = self.config.get('scan_timeout', 1.5)
        self.menu_style = 'list' if CURSES_AVAILABLE else 'number'

    def load_config(self):
        default_config = {
            "max_scan_workers": 20,
            "scan_timeout": 1.5,
            "top_ports": "21,22,23,25,53,80,110,143,443,445,993,995,1723,3306,3389,5900,8080",
            "common_usernames": "admin,root,user,administrator,test,guest",
        }
        self.config = default_config
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f: self.config.update(json.load(f))
            except: pass
        self.save_config()

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f: json.dump(self.config, f, indent=4)
        except: pass
    
    def init_audit_database(self):
        with sqlite3.connect(self.audit_db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_results (
                    id INTEGER PRIMARY KEY, target TEXT, audit_type TEXT,
                    finding_title TEXT, description TEXT, severity TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def record_audit_finding(self, target, audit_type, title, desc, severity):
        try:
            with sqlite3.connect(self.audit_db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO audit_results (target, audit_type, finding_title, description, severity) VALUES (?, ?, ?, ?, ?)',
                    (target, audit_type, title, desc, severity)
                )
                conn.commit()
        except Exception: pass

    # --- Tool: Website Downloader (Recursive) ---

    def website_downloader(self):
        print(f"\n{Fore.CYAN}📥 ΛΗΨΗ ΙΣΤΟΣΕΛΙΔΩΝ (ΑΝΑΔΡΟΜΙΚΑ){Style.RESET_ALL}")
        if not REQUESTS_AVAILABLE or not BS4_AVAILABLE:
            print(f"{Fore.RED}❌ Λείπουν τα Requests/BS4.{Style.RESET_ALL}"); return

        # Directory Setup
        if self.is_termux:
            storage_path = "/sdcard/Download/Websites"
        else:
            storage_path = os.path.join(os.path.expanduser("~"), "Downloads", "Websites")

        if not os.path.exists(storage_path):
            try: os.makedirs(storage_path)
            except: storage_path = os.path.join(self.save_dir, "Websites")
            if not os.path.exists(storage_path): os.makedirs(storage_path)

        url = input(f"{Fore.WHITE}URL Στόχου: {Style.RESET_ALL}").strip()
        if not url.startswith('http'): url = 'http://' + url
        
        try:
            max_depth = int(input(f"{Fore.WHITE}Βάθος Ανίχνευσης (1=Μια Σελίδα, 2+=Αναδρομικά): {Style.RESET_ALL}") or "1")
        except: max_depth = 1

        domain = urlparse(url).netloc
        folder_name = domain.replace(".", "_")
        target_folder = os.path.join(storage_path, folder_name)
        if not os.path.exists(target_folder): os.makedirs(target_folder)

        visited = set()
        to_visit = deque([(url, 1)])
        
        print(f"[*] Λήψη σε: {target_folder}")

        while to_visit:
            curr_url, depth = to_visit.popleft()
            if curr_url in visited or depth > max_depth: continue
            visited.add(curr_url)

            try:
                print(f"  {Fore.GREEN}[+]{Style.RESET_ALL} Λήψη: {curr_url}")
                r = requests.get(curr_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                
                # Determine file name
                parsed_path = urlparse(curr_url).path
                fname = os.path.basename(parsed_path) or "index.html"
                if not fname.endswith(".html"): fname += ".html"
                
                with open(os.path.join(target_folder, fname), "wb") as f:
                    f.write(r.content)

                soup = BeautifulSoup(r.content, 'html.parser')
                
                # Recursion
                if depth < max_depth:
                    for a in soup.find_all('a', href=True):
                        full_link = urljoin(curr_url, a['href'])
                        if urlparse(full_link).netloc == domain:
                            to_visit.append((full_link, depth + 1))

                # Assets
                tags = {'img': 'src', 'link': 'href', 'script': 'src'}
                for tag, attr in tags.items():
                    for item in soup.find_all(tag, **{attr: True}):
                        asset_url = urljoin(curr_url, item.get(attr))
                        asset_name = os.path.basename(urlparse(asset_url).path)
                        if asset_name:
                            try:
                                asset_r = requests.get(asset_url, timeout=5)
                                with open(os.path.join(target_folder, asset_name), "wb") as f:
                                    f.write(asset_r.content)
                            except: pass
            except: pass

        # ZIP Feature
        do_zip = input(f"\n{Fore.WHITE}Συμπίεση σε ZIP; (y/n): {Style.RESET_ALL}").lower()
        if do_zip == 'y':
            zip_name = f"{target_folder}.zip"
            with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(target_folder):
                    for file in files:
                        zipf.write(os.path.join(root, file), arcname=file)
            print(f"{Fore.GREEN}✅ Το ZIP δημιουργήθηκε: {zip_name}{Style.RESET_ALL}")

        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    # --- Tool: Internet & Networking (Originals) ---
    
    def run_internet_speed_test(self):
        print(f"\n{Fore.CYAN}⚡️ ΕΛΕΓΧΟΣ ΤΑΧΥΤΗΤΑΣ{Style.RESET_ALL}")
        if not SPEEDTEST_AVAILABLE:
            print(f"{Fore.RED}❌ Το 'speedtest-cli' δεν είναι εγκατεστημένο.{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}"); return
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            dl = st.download() / 1_000_000
            ul = st.upload() / 1_000_000
            print(f"\n{Fore.GREEN}✅ ΑΠΟΤΕΛΕΣΜΑΤΑ:{Style.RESET_ALL}\n  Ping: {st.results.ping}ms\n  DL: {dl:.2f} Mbps\n  UL: {ul:.2f} Mbps")
        except Exception as e: print(f"{Fore.RED}❌ Σφάλμα: {e}{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def get_external_ip_info(self):
        print(f"\n{Fore.CYAN}🗺️ ΠΛΗΡΟΦΟΡΙΕΣ IP{Style.RESET_ALL}")
        if not REQUESTS_AVAILABLE: return
        try:
            data = requests.get("http://ip-api.com/json/", timeout=10).json()
            if data.get('status') == 'success':
                print(f"\n{Fore.GREEN}✅ Εξωτερική IP: {data.get('query')}{Style.RESET_ALL}\n  ISP: {data.get('isp')}\n  Τοποθεσία: {data.get('city')}, {data.get('country')}")
        except: pass
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def subnet_calculator(self):
        print(f"\n{Fore.CYAN}🧮 ΥΠΟΛΟΓΙΣΤΗΣ ΥΠΟΔΙΚΤΥΟΥ{Style.RESET_ALL}")
        ip_input = input(f"Εισάγετε IP/CIDR: ").strip()
        try:
            ip_str, cidr_str = ip_input.split('/')
            cidr = int(cidr_str)
            ip_parts = list(map(int, ip_str.split('.')))
            ip_int = (ip_parts[0] << 24) + (ip_parts[1] << 16) + (ip_parts[2] << 8) + ip_parts[3]
            mask_int = (0xFFFFFFFF << (32 - cidr)) & 0xFFFFFFFF
            network_int = ip_int & mask_int
            broadcast_int = network_int | ~mask_int & 0xFFFFFFFF
            int_to_ip = lambda val: '.'.join([str((val >> (i << 3)) & 0xFF) for i in (3, 2, 1, 0)])
            print(f"Network: {int_to_ip(network_int)}\nBroadcast: {int_to_ip(broadcast_int)}\nMask: {int_to_ip(mask_int)}")
        except: print(f"{Fore.RED}Μη έγκυρη μορφή.{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def enhanced_port_scanner(self):
        print(f"\n{Fore.CYAN}🔍 ΣΑΡΩΤΗΣ ΘΥΡΩΝ (TCP){Style.RESET_ALL}")
        target = input("Στόχος: ").strip()
        if not target: return
        try:
            target_ip = socket.gethostbyname(target)
            ports = [int(p) for p in self.config['top_ports'].split(',')]
            def scan(port):
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(self.scan_timeout)
                    if s.connect_ex((target_ip, port)) == 0:
                        print(f"  {Fore.GREEN}[+] Θύρα {port} ΑΝΟΙΧΤΗ{Style.RESET_ALL}")
            with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
                ex.map(scan, ports)
        except: pass
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def get_whois_info(self):
        print(f"\n{Fore.CYAN}👤 ΑΝΑΖΗΤΗΣΗ WHOIS{Style.RESET_ALL}")
        if not WHOIS_AVAILABLE: return
        domain = input("Domain: ").strip()
        try:
            w = whois.whois(domain)
            print(f"Καταχωρητής: {w.registrar}\nEmails: {w.emails}")
        except: pass
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def get_dns_records(self):
        print(f"\n{Fore.CYAN}🌐 ΕΓΓΡΑΦΕΣ DNS{Style.RESET_ALL}")
        if not DNS_AVAILABLE: return
        domain = input("Domain: ").strip()
        for r in ['A', 'MX', 'TXT']:
            try:
                ans = dns_resolver.resolve(domain, r)
                print(f"[{r}]: " + ", ".join([str(d) for d in ans]))
            except: pass
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def web_crawler(self):
        print(f"\n{Fore.CYAN}🕷️ WEB CRAWLER{Style.RESET_ALL}")
        url = input("URL: ").strip()
        if not url.startswith('http'): url = 'https://' + url
        try:
            r = requests.get(url, timeout=5)
            soup = BeautifulSoup(r.content, 'html.parser')
            for a in soup.find_all('a', href=True)[:20]:
                print(f"  - {urljoin(url, a['href'])}")
        except: pass
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def subdomain_enum(self):
        print(f"\n{Fore.CYAN}🔎 ΑΠΑΡΙΘΜΗΣΗ ΥΠΟΤΟΜΕΩΝ (SUBDOMAINS){Style.RESET_ALL}")
        domain = input("Domain: ").strip()
        subs = ['www', 'mail', 'dev', 'api', 'admin']
        def check(s):
            try: socket.gethostbyname(f"{s}.{domain}")
            except: return None
            return f"{s}.{domain}"
        with ThreadPoolExecutor(max_workers=10) as ex:
            results = ex.map(check, subs)
            for res in results:
                if res: print(f"{Fore.GREEN}[+] {res}{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def reverse_ip_lookup(self):
        print(f"\n{Fore.CYAN}🔄 ΑΝΤΙΣΤΡΟΦΗ ΑΝΑΖΗΤΗΣΗ IP{Style.RESET_ALL}")
        target = input("Στόχος: ").strip()
        try:
            r = requests.get(f"https://api.hackertarget.com/reverseiplookup/?q={target}", timeout=10)
            print(r.text)
        except: pass
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def http_headers(self):
        print(f"\n{Fore.CYAN}📋 ΑΝΑΛΥΣΗ ΚΕΦΑΛΙΔΩΝ (HEADERS){Style.RESET_ALL}")
        url = input("URL: ").strip()
        try:
            r = requests.get(url, timeout=5)
            for k, v in r.headers.items(): print(f"{k}: {v}")
        except: pass
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def sql_injector(self):
        print(f"\n{Fore.CYAN}💉 ΕΛΕΓΧΟΣ SQL INJECTION{Style.RESET_ALL}")
        url = input("URL με παράμετρο: ").strip()
        if '?' in url:
            payload = url + "'"
            try:
                r = requests.get(payload, timeout=5)
                if "sql" in r.text.lower(): print(f"{Fore.RED}[!] Ευπάθεια εντοπίστηκε!{Style.RESET_ALL}")
                else: print("Καμία προφανής ευπάθεια.")
            except: pass
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def xss_scanner(self):
        print(f"\n{Fore.CYAN}🎯 ΣΑΡΩΤΗΣ XSS{Style.RESET_ALL}")
        url = input("URL με παράμετρο: ").strip()
        payload = "<script>alert(1)</script>"
        if '?' in url:
            try:
                r = requests.get(url + payload, timeout=5)
                if payload in r.text: print(f"{Fore.RED}[!] Βρέθηκε XSS!{Style.RESET_ALL}")
                else: print("Ασφαλές.")
            except: pass
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def cms_detect(self):
        print(f"\n{Fore.CYAN}🧬 ΑΝΙΧΝΕΥΣΗ CMS{Style.RESET_ALL}")
        url = input("URL: ").strip()
        try:
            r = requests.get(url, timeout=5).text.lower()
            if 'wp-content' in r: print("WordPress")
            elif 'joomla' in r: print("Joomla")
            else: print("Άγνωστο")
        except: pass
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def ssh_brute(self):
        print(f"\n{Fore.CYAN}🔐 SSH BRUTE FORCE{Style.RESET_ALL}")
        if not PARAMIKO_AVAILABLE: return
        host = input("Host: ").strip()
        user = input("User: ").strip()
        for p in ['123456', 'admin', 'password']:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(host, username=user, password=p, timeout=3)
                print(f"{Fore.GREEN}ΣΠΑΣΤΗΚΕ: {p}{Style.RESET_ALL}"); ssh.close(); break
            except: pass
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def view_logs(self):
        print(f"\n{Fore.CYAN}📊 ΑΡΧΕΙΑ ΕΛΕΓΧΟΥ (LOGS){Style.RESET_ALL}")
        try:
            with sqlite3.connect(self.audit_db_name) as conn:
                for r in conn.execute("SELECT * FROM audit_results LIMIT 10"): print(r)
        except: pass
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def change_menu_style(self):
        self.menu_style = 'number' if self.menu_style == 'list' else 'list'
        print(f"Το στυλ άλλαξε σε: {self.menu_style}")
        time.sleep(1)

    # --- Main Menu ---

    def run(self):
        while True:
            options = [
                "--- ΔΙΚΤΥΟ & ΣΥΝΔΕΣΙΜΟΤΗΤΑ ---", # 0
                "Σαρωτής Θυρών (TCP)",            # 1
                "Υπολογιστής Υποδικτύου",         # 2
                "Έλεγχος Ταχύτητας Internet",     # 3
                "Πληροφορίες Εξωτερικής IP",      # 4
                "Λήψη Ιστοσελίδας (Αναδρομική)",  # 5
                "--- OSINT & ΑΝΑΓΝΩΡΙΣΗ ---",     # 6
                "Αναζήτηση WHOIS",                # 7
                "Εγγραφές DNS",                   # 8
                "Απαρίθμηση Υποτομέων",           # 9
                "Αντίστροφη Αναζήτηση IP",        # 10
                "Web Crawler (Ανιχνευτής)",       # 11
                "--- ΑΣΦΑΛΕΙΑ WEB ---",           # 12
                "Ανάλυση Κεφαλίδων HTTP",         # 13
                "Ανίχνευση CMS",                  # 14
                "Έλεγχος SQL Injection",          # 15
                "Σαρωτής Reflected XSS",          # 16
                "SSH Brute Force",                # 17
                "--- ΣΥΣΤΗΜΑ ---",                # 18
                "Προβολή Αρχείων Ελέγχου",        # 19
                "Αλλαγή Στυλ Μενού",              # 20
                "Έξοδος"                          # 21
            ]

            sel = -1
            if CURSES_AVAILABLE and self.menu_style == 'list':
                sel = curses.wrapper(_draw_curses_menu, "DedSec Network Tool (Lite)", options)
            else:
                print(f"\n{Fore.CYAN}   DEDSEC TOOLKIT - ΕΠΙΛΟΓΗ ΜΕ ΑΡΙΘΜΟ{Style.RESET_ALL}")
                for i, o in enumerate(options):
                    if o.startswith("---"): print(f"{Fore.YELLOW}{o}{Style.RESET_ALL}")
                    else: print(f"{Fore.WHITE}{i:2}. {o}{Style.RESET_ALL}")
                try: sel = int(input(f"\nΕπιλέξτε > ").strip())
                except: sel = -1

            # Mapping Selection to Functions
            opt_map = {
                1: self.enhanced_port_scanner, 2: self.subnet_calculator, 3: self.run_internet_speed_test,
                4: self.get_external_ip_info, 5: self.website_downloader, 7: self.get_whois_info,
                8: self.get_dns_records, 9: self.subdomain_enum, 10: self.reverse_ip_lookup,
                11: self.web_crawler, 13: self.http_headers, 14: self.cms_detect,
                15: self.sql_injector, 16: self.xss_scanner, 17: self.ssh_brute,
                19: self.view_logs, 20: self.change_menu_style
            }

            if sel == 21: break
            if sel in opt_map:
                try: opt_map[sel]()
                except KeyboardInterrupt: print("\nΑκυρώθηκε.")
            elif sel != -1 and not options[sel].startswith("---"):
                print(f"{Fore.RED}Μη έγκυρη επιλογή.{Style.RESET_ALL}"); time.sleep(1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        auto_install_dependencies()
        sys.exit()
    try:
        app = AdvancedNetworkTools()
        app.run()
    except KeyboardInterrupt: print("\nΈξοδος.")