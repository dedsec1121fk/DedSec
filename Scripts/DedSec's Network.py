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
    Automatically install all required dependencies without root.
    """
    print(f"{Fore.CYAN}🛠️ DedSec Toolkit - Dependency Installer{Style.RESET_ALL}")
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
        print(f"\n{Fore.CYAN}[*] Checking Termux packages...{Style.RESET_ALL}")
        try:
            subprocess.run(['pkg', 'install', '-y'] + termux_packages, capture_output=True)
            print(f"    {Fore.GREEN}✅ Termux packages installed.{Style.RESET_ALL}")
        except Exception as e:
            print(f"    {Fore.YELLOW}⚠️ Error installing system packages: {e}{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}[*] Installing Python dependencies...{Style.RESET_ALL}")
    for package in pip_packages:
        print(f"    [*] Checking {package}...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], capture_output=True)
            print(f"    {Fore.GREEN}✅ {package} ready.{Style.RESET_ALL}")
        except Exception as e:
            print(f"    {Fore.RED}❌ Failed to install {package}: {e}{Style.RESET_ALL}")
    
    print(f"\n{Fore.GREEN}🎉 Installation complete! Restarting...{Style.RESET_ALL}")
    time.sleep(2)
    return True

# --- TUI Helpers ---
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
        
        # Title
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

# --- Main Logic ---

class AdvancedNetworkTools:
    def __init__(self):
        # Save Directory Setup
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
        
        # Menu Style Preference (Default: 'list' if available, else 'number')
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

    # --- Tool: Internet & Networking ---
    
    def run_internet_speed_test(self):
        print(f"\n{Fore.CYAN}⚡️ SPEED TEST{Style.RESET_ALL}")
        if not SPEEDTEST_AVAILABLE:
            print(f"{Fore.RED}❌ 'speedtest-cli' not installed.{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")
            return

        try:
            print(f"[*] Selecting best server...")
            st = speedtest.Speedtest()
            st.get_best_server()
            print(f"[*] Testing Download...")
            dl = st.download() / 1_000_000
            print(f"[*] Testing Upload...")
            ul = st.upload() / 1_000_000
            ping = st.results.ping
            
            print(f"\n{Fore.GREEN}✅ RESULTS:{Style.RESET_ALL}")
            print(f"  Ping:     {ping:.2f} ms")
            print(f"  Download: {Fore.GREEN}{dl:.2f} Mbps{Style.RESET_ALL}")
            print(f"  Upload:   {Fore.GREEN}{ul:.2f} Mbps{Style.RESET_ALL}")
            print(f"  ISP:      {st.results.client['isp']}")
        except Exception as e:
            print(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

    def get_external_ip_info(self):
        print(f"\n{Fore.CYAN}🗺️ IP INFORMATION{Style.RESET_ALL}")
        if not REQUESTS_AVAILABLE: return
        try:
            data = requests.get("http://ip-api.com/json/", timeout=10).json()
            if data.get('status') == 'success':
                print(f"\n{Fore.GREEN}✅ External IP Found:{Style.RESET_ALL}")
                print(f"  IP:       {data.get('query')}")
                print(f"  ISP:      {data.get('isp')}")
                print(f"  Location: {data.get('city')}, {data.get('country')}")
                print(f"  Org:      {data.get('org')}")
            else:
                print(f"{Fore.RED}❌ Failed to retrieve info.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Connection failed: {e}{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

    def subnet_calculator(self):
        print(f"\n{Fore.CYAN}🧮 SUBNET CALCULATOR{Style.RESET_ALL}")
        ip_input = input(f"{Fore.WHITE}Enter IP/CIDR (e.g. 192.168.1.0/24): {Style.RESET_ALL}").strip()
        
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
            
            print(f"\n{Fore.GREEN}✅ Calculation:{Style.RESET_ALL}")
            print(f"  Network:   {int_to_ip(network_int)}")
            print(f"  Broadcast: {int_to_ip(broadcast_int)}")
            print(f"  Netmask:   {int_to_ip(mask_int)}")
            print(f"  Usable:    {max(0, 2**(32-cidr) - 2)} hosts")
        except:
            print(f"{Fore.RED}❌ Invalid format.{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

    def enhanced_port_scanner(self):
        """Python-based TCP Connect Scanner (Works without root)"""
        print(f"\n{Fore.CYAN}🔍 PORT SCANNER (TCP){Style.RESET_ALL}")
        target = input(f"{Fore.WHITE}Target IP/Hostname: {Style.RESET_ALL}").strip()
        if not target: return

        try:
            target_ip = socket.gethostbyname(target)
            print(f"[*] Resolving {target} -> {target_ip}")
        except:
            print(f"{Fore.RED}❌ Host not found.{Style.RESET_ALL}")
            return

        mode = input(f"{Fore.WHITE}Scan: (1) Top Ports, (2) Range 1-1024: {Style.RESET_ALL}").strip()
        if mode == '1':
            ports = [int(p) for p in self.config['top_ports'].split(',')]
        elif mode == '2':
            ports = range(1, 1025)
        else:
            ports = [21, 22, 80, 443]

        print(f"[*] Scanning {len(ports)} ports with {self.max_workers} threads...")
        
        def scan_port(port):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(self.scan_timeout)
                    if s.connect_ex((target_ip, port)) == 0:
                        try:
                            serv = socket.getservbyport(port)
                        except: serv = "unknown"
                        return port, serv
            except: pass
            return None

        open_ports = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(scan_port, p) for p in ports]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res:
                    print(f"  {Fore.GREEN}[+] Port {res[0]} OPEN ({res[1]}){Style.RESET_ALL}")
                    open_ports.append(res)

        if open_ports:
            self.record_audit_finding(target, 'Port Scan', f"{len(open_ports)} Ports Open", str(open_ports), 'Info')
        
        input(f"\n{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

    # --- Tool: OSINT & Info Gathering ---

    def get_whois_info(self):
        print(f"\n{Fore.CYAN}👤 WHOIS LOOKUP{Style.RESET_ALL}")
        if not WHOIS_AVAILABLE: 
            print("Module missing."); return
        domain = input("Domain: ").strip()
        if domain:
            try:
                w = whois.whois(domain)
                print(f"\n{Fore.GREEN}✅ Registrar: {w.registrar}{Style.RESET_ALL}")
                print(f"   Creation Date: {w.creation_date}")
                print(f"   Emails: {w.emails}")
            except Exception as e:
                print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

    def get_dns_records(self):
        print(f"\n{Fore.CYAN}🌐 DNS RECORDS{Style.RESET_ALL}")
        if not DNS_AVAILABLE: return
        domain = input("Domain: ").strip()
        if domain:
            for r in ['A', 'AAAA', 'MX', 'TXT', 'NS']:
                try:
                    answers = dns_resolver.resolve(domain, r)
                    print(f"{Fore.CYAN}[{r}]{Style.RESET_ALL}")
                    for d in answers: print(f"  {d}")
                except: pass
        input(f"\n{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

    def web_crawler(self):
        print(f"\n{Fore.CYAN}🕷️ WEB CRAWLER{Style.RESET_ALL}")
        if not REQUESTS_AVAILABLE or not BS4_AVAILABLE: return
        url = input("Start URL: ").strip()
        if not url.startswith('http'): url = 'https://' + url
        
        print(f"[*] Crawling (Max 50 links)...")
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
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

    def subdomain_enum(self):
        print(f"\n{Fore.CYAN}🔎 SUBDOMAIN ENUMERATION{Style.RESET_ALL}")
        if not DNS_AVAILABLE: return
        domain = input("Domain: ").strip()
        
        subs = ['www', 'mail', 'ftp', 'webmail', 'smtp', 'pop', 'ns1', 'dev', 'test', 'api', 'admin', 'blog', 'shop']
        print(f"[*] Checking common subdomains...")
        
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
                    print(f"{Fore.GREEN}[+] Found: {f.result()}{Style.RESET_ALL}")
                    self.record_audit_finding(domain, 'Subdomain', 'Found', f.result(), 'Info')
        
        input(f"\n{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

    def reverse_ip_lookup(self):
        print(f"\n{Fore.CYAN}🔄 REVERSE IP LOOKUP{Style.RESET_ALL}")
        target = input("Target IP/Domain: ").strip()
        try:
            r = requests.get(f"https://api.hackertarget.com/reverseiplookup/?q={target}", timeout=10)
            if 'error' not in r.text.lower() and 'no records' not in r.text.lower():
                print(f"\n{Fore.GREEN}✅ Domains on this IP:{Style.RESET_ALL}")
                for line in r.text.splitlines():
                    print(f"  - {line}")
            else:
                print(f"{Fore.YELLOW}No records found.{Style.RESET_ALL}")
        except:
            print(f"{Fore.RED}API Error.{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

    # --- Tool: Web Security & Vulnerabilities ---

    def http_headers(self):
        print(f"\n{Fore.CYAN}📋 HEADER ANALYZER{Style.RESET_ALL}")
        url = input("URL: ").strip()
        if not url.startswith('http'): url = 'https://' + url
        try:
            r = requests.get(url, timeout=5)
            h = r.headers
            security = ['Strict-Transport-Security', 'X-Frame-Options', 'Content-Security-Policy']
            
            print(f"\n{Fore.GREEN}[+] Security Headers:{Style.RESET_ALL}")
            for s in security:
                if s in h: print(f"  {Fore.GREEN}✔ {s}: Found{Style.RESET_ALL}")
                else: print(f"  {Fore.RED}✖ {s}: Missing{Style.RESET_ALL}")
            
            if 'Server' in h:
                print(f"{Fore.YELLOW}[!] Server Leak: {h['Server']}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

    def sql_injector(self):
        print(f"\n{Fore.CYAN}💉 SQL INJECTION TESTER (Basic){Style.RESET_ALL}")
        url = input(f"URL with param (e.g. site.com?id=1): ").strip()
        if '?' not in url: 
            print("Need URL parameters."); return
        
        payloads = ["'", "\"", "' OR '1'='1", " OR 1=1"]
        errors = ['sql', 'mysql', 'syntax', 'ora-']
        
        print(f"[*] Testing payloads...")
        vuln = False
        for p in payloads:
            target = url + p
            try:
                r = requests.get(target, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
                if any(e in r.text.lower() for e in errors):
                    print(f"{Fore.RED}[!] Vulnerable to Error-Based SQLi with: {p}{Style.RESET_ALL}")
                    vuln = True
                    break
            except: pass
        
        if not vuln: print(f"{Fore.GREEN}No obvious error-based vulnerabilities.{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

    def xss_scanner(self):
        print(f"\n{Fore.CYAN}🎯 XSS SCANNER (Reflected){Style.RESET_ALL}")
        url = input(f"URL with param (e.g. site.com?q=test): ").strip()
        if '?' not in url: return
        
        base, params = url.split('?', 1)
        key = params.split('=')[0]
        payload = "<script>alert('XSS')</script>"
        target = f"{base}?{key}={payload}"
        
        print(f"[*] Sending payload...")
        try:
            r = requests.get(target, timeout=5)
            if payload in r.text:
                print(f"{Fore.RED}[!] Reflected XSS Found!{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}Payload not reflected.{Style.RESET_ALL}")
        except: pass
        input(f"\n{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

    def cms_detect(self):
        print(f"\n{Fore.CYAN}🧬 CMS DETECTOR{Style.RESET_ALL}")
        url = input("URL: ").strip()
        if not url.startswith('http'): url = 'https://' + url
        try:
            r = requests.get(url, timeout=5)
            text = r.text.lower()
            if 'wp-content' in text: print(f"{Fore.GREEN}Detected: WordPress{Style.RESET_ALL}")
            elif 'joomla' in text: print(f"{Fore.GREEN}Detected: Joomla{Style.RESET_ALL}")
            elif 'drupal' in text: print(f"{Fore.GREEN}Detected: Drupal{Style.RESET_ALL}")
            elif 'shopify' in text: print(f"{Fore.GREEN}Detected: Shopify{Style.RESET_ALL}")
            else: print(f"{Fore.YELLOW}Unknown CMS.{Style.RESET_ALL}")
        except: pass
        input(f"\n{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

    # --- Tool: SSH Auditing ---

    def ssh_brute(self):
        print(f"\n{Fore.CYAN}🔐 SSH BRUTE FORCE (Paramiko){Style.RESET_ALL}")
        if not PARAMIKO_AVAILABLE: 
            print("Paramiko missing."); return
        
        host = input("Host IP: ").strip()
        user = input("Username: ").strip()
        passwords = ['admin', '123456', 'password', 'root', 'toor', '1234']
        
        print(f"[*] Trying common passwords...")
        for pwd in passwords:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(host, username=user, password=pwd, timeout=3)
                print(f"\n{Fore.GREEN}✅ CRACKED: {user}:{pwd}{Style.RESET_ALL}")
                ssh.close()
                break
            except: 
                print(f"  [-] Failed: {pwd}")
        
        input(f"\n{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

    # --- Tool: Management ---

    def view_logs(self):
        print(f"\n{Fore.CYAN}📊 AUDIT LOGS{Style.RESET_ALL}")
        try:
            with sqlite3.connect(self.audit_db_name) as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM audit_results ORDER BY timestamp DESC LIMIT 20")
                rows = cur.fetchall()
                for r in rows:
                    print(f"[{r[6]}] {r[2]} - {r[3]} ({r[5]})")
        except: pass
        input(f"\n{Fore.YELLOW}Press Enter...{Style.RESET_ALL}")

    def change_menu_style(self):
        print(f"\n{Fore.CYAN}🎨 CHOOSE MENU STYLE{Style.RESET_ALL}")
        print(f"{Fore.WHITE}1. Interactive List (Requires Curses/TUI){Style.RESET_ALL}")
        print(f"{Fore.WHITE}2. Choose By Number (Classic CLI){Style.RESET_ALL}")
        
        choice = input(f"\n{Fore.WHITE}Select option (1-2): {Style.RESET_ALL}").strip()
        
        if choice == '1':
            if CURSES_AVAILABLE:
                self.menu_style = 'list'
                print(f"{Fore.GREEN}✅ Menu style set to Interactive List.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ Curses not available. Cannot switch to List style.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Install ncurses-utils or run in a compatible terminal.{Style.RESET_ALL}")
        elif choice == '2':
            self.menu_style = 'number'
            print(f"{Fore.GREEN}✅ Menu style set to Choose By Number.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Invalid selection.{Style.RESET_ALL}")
            
        time.sleep(1.5)

    # --- Main Menu ---

    def run(self):
        while True:
            options = [
                "--- NETWORK & CONNECTIVITY ---", # 0
                "Port Scanner (TCP)",             # 1
                "Subnet Calculator",              # 2
                "Internet Speed Test",            # 3
                "External IP Info",               # 4
                "--- OSINT & RECON ---",          # 5
                "WHOIS Lookup",                   # 6
                "DNS Records",                    # 7
                "Subdomain Enumeration",          # 8
                "Reverse IP Lookup",              # 9
                "Web Crawler",                    # 10
                "--- WEB SECURITY ---",           # 11
                "HTTP Header Analyzer",           # 12
                "CMS Detector",                   # 13
                "SQL Injection Tester",           # 14
                "Reflected XSS Scanner",          # 15
                "SSH Brute Force",                # 16
                "--- SYSTEM ---",                 # 17
                "View Audit Logs",                # 18
                "Change Menu Style",              # 19
                "Exit"                            # 20
            ]

            # Logic to decide Menu Rendering Style
            sel = -1
            if CURSES_AVAILABLE and self.menu_style == 'list':
                sel = curses.wrapper(_draw_curses_menu, "DedSec Network Tool (Lite)", options)
            else:
                # Number Selection Style
                print(f"\n{Fore.CYAN}{'='*40}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}   DEDSEC TOOLKIT - SELECT BY NUMBER{Style.RESET_ALL}")
                print(f"{Fore.CYAN}{'='*40}{Style.RESET_ALL}")
                
                valid_indices = []
                for i, o in enumerate(options):
                    if o.startswith("---"):
                        print(f"{Fore.YELLOW}{o}{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.WHITE}{i:2}. {o}{Style.RESET_ALL}")
                        valid_indices.append(i)
                
                try:
                    choice_input = input(f"\n{Fore.CYAN}Select option > {Style.RESET_ALL}").strip()
                    if choice_input:
                        sel = int(choice_input)
                except ValueError:
                    sel = -1

            # Mapping Selection to Functions
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
                print(f"{Fore.GREEN}Goodbye.{Style.RESET_ALL}")
                break
            
            if sel in opt_map:
                try:
                    opt_map[sel]()
                except KeyboardInterrupt:
                    print(f"\n{Fore.YELLOW}Operation Cancelled.{Style.RESET_ALL}")
            elif sel != -1 and not options[sel].startswith("---"):
                print(f"{Fore.RED}Invalid selection.{Style.RESET_ALL}")
                time.sleep(1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        auto_install_dependencies()
        sys.exit()

    try:
        app = AdvancedNetworkTools()
        app.run()
    except KeyboardInterrupt:
        print("\nExiting.")
    except Exception as e:
        print(f"Error: {e}")
        if not REQUESTS_AVAILABLE:
            print(f"Run 'python {sys.argv[0]} --install' to fix dependencies.")