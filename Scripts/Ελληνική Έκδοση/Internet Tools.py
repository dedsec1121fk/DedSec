#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import importlib
import time
from datetime import datetime, timedelta
import json
import re
import sqlite3
import threading
from collections import deque
import socket
from urllib.parse import urlparse, urljoin
import base64
import hashlib
import random
import string
import struct
import select

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
dns = None

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

# 3. Dynamic import attempts for other modules
def _try_import(module_name, global_var_name):
    try:
        module = importlib.import_module(module_name)
        globals()[global_var_name] = module
        return True
    except ImportError:
        return False

SPEEDTEST_AVAILABLE = _try_import('speedtest', 'speedtest')
REQUESTS_AVAILABLE = _try_import('requests', 'requests')
BS4_AVAILABLE = _try_import('bs4', 'bs4_module')
if BS4_AVAILABLE:
    BeautifulSoup = bs4_module.BeautifulSoup
PARAMIKO_AVAILABLE = _try_import('paramiko', 'paramiko')
WHOIS_AVAILABLE = _try_import('whois', 'whois')
DNS_AVAILABLE = _try_import('dns.resolver', 'dns_resolver')


def auto_install_dependencies():
    """Automatically install required non-root dependencies."""
    print(f"{Fore.CYAN}🛠️ ΕΡΓΑΛΕΙΑ ΔΙΚΤΥΟΥ - Αυτόματη Εγκατάσταση Εξαρτήσεων{Style.RESET_ALL}")
    print("="*60)

    is_termux = os.path.exists('/data/data/com.termux')
    
    # Non-root system packages for Termux
    required_packages = ['ncurses', 'inetutils', 'openssl-tool']
    
    # Python (pip) packages
    required_pip_packages = [
        'requests', 'colorama', 'speedtest-cli', 'beautifulsoup4',
        'paramiko', 'python-whois', 'dnspython'
    ]
    
    # Check if python/sqlite3 is available
    try:
        import sqlite3
    except ImportError:
        if is_termux:
            required_packages.append('python')

    # Install system packages (Termux specific)
    if required_packages and is_termux:
        print(f"\n[*] Εγκατάσταση πακέτων συστήματος: {', '.join(required_packages)}")
        try:
            subprocess.run(['pkg', 'install', '-y'] + required_packages, check=True, capture_output=True, text=True, timeout=120)
            print("✅ Τα πακέτα συστήματος ελέγχθηκαν/εγκαταστάθηκαν με επιτυχία.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Αποτυχία εγκατάστασης πακέτων συστήματος: {e.stderr}")
        except Exception as e:
            print(f"❌ Παρουσιάστηκε σφάλμα κατά την εγκατάσταση πακέτων συστήματος: {e}")

    # Install pip packages
    print(f"\n[*] Εγκατάσταση πακέτων Python: {', '.join(required_pip_packages)}")
    for package in required_pip_packages:
        module_name = package.replace('-', '_').replace('4', '')
        if module_name == 'beautifulsoup': module_name = 'bs4'
        if module_name == 'dnspython': module_name = 'dns'

        try:
            importlib.import_module(module_name)
            print(f"✅ Το {package} είναι ήδη εγκατεστημένο.")
        except ImportError:
            print(f"[*] Εγκατάσταση {package}...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                             check=True, capture_output=True, text=True, timeout=300)
                print(f"✅ Το {package} εγκαταστάθηκε με επιτυχία.")
                time.sleep(1)
            except Exception as e:
                print(f"❌ Αποτυχία εγκατάστασης του {package}. Ορισμένες λειτουργίες ενδέχεται να είναι απενεργοποιημένες. Σφάλμα: {e}")
                
    print("\n✅ Όλες οι βασικές εξαρτήσεις ελέγχθηκαν.")
    if not CURSES_AVAILABLE:
        print(f"{Fore.YELLOW}⚠️ ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Το module 'curses' της Python δεν βρέθηκε. Το μενού TUI δεν μπορεί να εκτελεστεί.{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Όλοι οι έλεγχοι ολοκληρώθηκαν. Εκκίνηση της εφαρμογής...{Style.RESET_ALL}")
    time.sleep(2)
    return True

# --- Global Curses Helpers ---
def _reset_curses_state(stdscr):
    """Initializes and resets required terminal settings for TUI."""
    if not CURSES_AVAILABLE: return
    curses.cbreak()
    curses.noecho()
    stdscr.keypad(True)
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK) # Default
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Title
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Highlight text
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN)  # Highlight background

def _draw_curses_menu(stdscr, title, options):
    """Generic curses menu handler for navigation and selection."""
    current_row_idx = 0
    
    def print_menu(screen, selected_idx):
        screen.clear()
        h, w = screen.getmaxyx()
        
        title_text = f" {title} "
        x_title = w//2 - len(title_text)//2
        
        if 1 < h:
            screen.attron(curses.A_BOLD | curses.color_pair(2))
            screen.addstr(1, x_title, title_text)
            screen.attroff(curses.A_BOLD | curses.color_pair(2))
            
        if 2 < h:
            screen.addstr(2, w//2 - 25, "=" * 50)

        for idx, option in enumerate(options):
            y = 4 + idx
            if y >= h - 1: break
            
            # Add separators
            if option.startswith("---"):
                screen.attron(curses.color_pair(3))
                screen.addstr(y, w//2 - 20, option)
                screen.attroff(curses.color_pair(3))
                continue
            
            display_option = option.ljust(40)
            x = w//2 - len(display_option)//2
            
            if idx == selected_idx:
                screen.attron(curses.A_BOLD | curses.color_pair(4))
                screen.addstr(y, x, display_option)
                screen.attroff(curses.A_BOLD | curses.color_pair(4))
            else:
                screen.attron(curses.color_pair(1))
                screen.addstr(y, x, display_option)
                screen.attroff(curses.color_pair(1))
        screen.refresh()

    while True:
        print_menu(stdscr, current_row_idx)
        key = stdscr.getch()

        if key == curses.KEY_UP:
            current_row_idx = (current_row_idx - 1) % len(options)
            while options[current_row_idx].startswith("---"):
                current_row_idx = (current_row_idx - 1) % len(options)
        elif key == curses.KEY_DOWN:
            current_row_idx = (current_row_idx + 1) % len(options)
            while options[current_row_idx].startswith("---"):
                current_row_idx = (current_row_idx + 1) % len(options)
        elif key == curses.KEY_ENTER or key in [10, 13]:
            return current_row_idx

def main_internet_tools():
    """Main application entry point"""
    
    class InternetTools:
        def __init__(self):
            # Define and create a dedicated save directory
            is_termux = os.path.exists('/data/data/com.termux')
            if is_termux:
                base_dir = os.path.expanduser('~')
                self.save_dir = os.path.join(base_dir, "Internet Tools Files")
            else:
                self.save_dir = os.path.join(os.getcwd(), "Internet_Tools_Files")

            if not os.path.exists(self.save_dir):
                print(f"{Fore.CYAN}[*] Δημιουργία καταλόγου αποθήκευσης στη διεύθυνση: {self.save_dir}{Style.RESET_ALL}")
                os.makedirs(self.save_dir)
            
            # Point file paths to the new save directory
            self.wifi_db_name = os.path.join(self.save_dir, "wifi_tester.db")
            self.config_file = os.path.join(self.save_dir, "internet_tools_config.json")
            self.known_networks_file = os.path.join(self.save_dir, "known_networks.json")
            self.audit_db_name = os.path.join(self.save_dir, "audit_results.db")

            self.init_wifi_database()
            self.init_audit_database()
            self.load_config()
            self.load_known_networks()
            
            self.trusted_bssids = set(self.known_networks.get("trusted_bssids", []))
            self.current_networks = {}
            
            print(f"{Fore.GREEN}✅ Τα Εργαλεία Δικτύου αρχικοποιήθηκαν με επιτυχία{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📂 Όλα τα αρχεία θα αποθηκευτούν σε: {self.save_dir}{Style.RESET_ALL}")
            
        # --- Configuration & Database Management ---
        def load_config(self):
            default_config = {
                "scan_interval": 60, "alert_on_new_network": True,
                "max_network_age": 3600, "auto_learn_networks": True, 
                "dns_test_server": "https://ipleak.net/json/",
                "port_scan_threads": 20, "top_ports": "21,22,23,25,53,80,110,143,443,445,993,995,1723,3306,3389,5900,8080",
                "subdomain_wordlist": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/DNS/subdomains-top1mil-5000.txt"
            }
            self.config = default_config
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r') as f: self.config.update(json.load(f))
                except Exception: pass
            self.save_config()

        def save_config(self):
            try:
                with open(self.config_file, 'w') as f: json.dump(self.config, f, indent=4)
            except Exception: pass
        
        def load_known_networks(self):
            default_networks = {
                "trusted_bssids": [], "trusted_ssids": ["Home", "Work"], 
                "suspicious_ssids": ["Free WiFi", "Public WiFi"]
            }
            self.known_networks = default_networks
            if os.path.exists(self.known_networks_file):
                try:
                    with open(self.known_networks_file, 'r') as f: self.known_networks.update(json.load(f))
                except Exception: pass
            self.save_known_networks()
        
        def save_known_networks(self):
            try:
                with open(self.known_networks_file, 'w') as f: json.dump(self.known_networks, f, indent=4)
            except Exception: pass
        
        def init_wifi_database(self):
            with sqlite3.connect(self.wifi_db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS network_scans (
                        bssid TEXT PRIMARY KEY, ssid TEXT, signal_strength INTEGER, channel INTEGER,
                        encryption TEXT, first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_trusted BOOLEAN DEFAULT 0
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_events (
                        id INTEGER PRIMARY KEY, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        event_type TEXT, event_description TEXT, bssid TEXT, ssid TEXT, severity TEXT
                    )
                ''')
                conn.commit()
        
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
            except sqlite3.Error as e:
                print(f"{Fore.RED}❌ Σφάλμα DB: Αποτυχία καταγραφής ευρήματος ελέγχου: {e}{Style.RESET_ALL}")
        
        # --- Wi-Fi, Local Network, and Mobile Tools ---
        def _run_termux_command(self, command, timeout=15):
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
                if result.returncode == 0:
                    return result.stdout
            except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
                pass
            return None

        def frequency_to_channel(self, freq):
            if 2412 <= freq <= 2472: return (freq - 2412) // 5 + 1
            if 5170 <= freq <= 5825: return (freq - 5170) // 5 + 34
            return 0

        def get_signal_quality(self, signal_dBm):
            if not isinstance(signal_dBm, int): return f"{Fore.WHITE}N/A{Style.RESET_ALL}"
            if signal_dBm >= -50: return f"{Fore.GREEN}Εξαιρετική{Style.RESET_ALL}"
            if signal_dBm >= -65: return f"{Fore.YELLOW}Καλή{Style.RESET_ALL}"
            if signal_dBm >= -75: return f"{Fore.MAGENTA}Μέτρια{Style.RESET_ALL}"
            return f"{Fore.RED}Αδύναμη{Style.RESET_ALL}"
        
        def scan_via_termux_api(self):
            networks = []
            output = self._run_termux_command(['termux-wifi-scaninfo'])
            if output and output.strip().startswith('['):
                scan_data = json.loads(output)
                for network in scan_data:
                    networks.append({
                        'bssid': network.get('bssid', 'Άγνωστο').upper(), 'ssid': network.get('ssid', 'Κρυφό'),
                        'signal': network.get('rssi', 0), 'channel': self.frequency_to_channel(network.get('frequency', 0)),
                        'encryption': network.get('security', 'Άγνωστη')
                    })
            return networks

        def get_current_connection_info(self):
            output = self._run_termux_command(['termux-wifi-connectioninfo'])
            if output and output.strip().startswith('{'):
                conn_info = json.loads(output)
                return {
                    'bssid': conn_info.get('bssid', 'N/A').upper(), 'ssid': conn_info.get('ssid', 'Μη Συνδεδεμένο'),
                    'signal': conn_info.get('rssi', 0), 'channel': self.frequency_to_channel(conn_info.get('frequency', 0)),
                    'encryption': conn_info.get('security', 'N/A'), 'is_current': True
                }
            return None

        def passive_network_scan(self):
            print(f"{Fore.YELLOW}[*] Έναρξη παθητικής σάρωσης Wi-Fi...{Style.RESET_ALL}")
            networks_found = {}
            for net in self.scan_via_termux_api(): 
                networks_found[net['bssid']] = net
            
            current_network = self.get_current_connection_info()
            if current_network and current_network['bssid'] != 'N/A':
                networks_found[current_network['bssid']] = current_network
            
            if not networks_found:
                print(f"{Fore.RED}❌ Δεν βρέθηκαν δίκτυα. Βεβαιωθείτε ότι το Wi-Fi είναι ενεργοποιημένο και το Termux:API είναι εγκατεστημένο.{Style.RESET_ALL}")

            return list(networks_found.values())
        
        def update_network_database(self, network):
            bssid = network['bssid']
            if bssid == 'Άγνωστο': return

            with sqlite3.connect(self.wifi_db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM network_scans WHERE bssid = ?', (bssid,))
                exists = cursor.fetchone()
                
                is_trusted = 1 if bssid in self.trusted_bssids else 0
                
                if exists:
                    cursor.execute('''
                        UPDATE network_scans SET ssid = ?, signal_strength = ?, channel = ?, 
                        encryption = ?, last_seen = CURRENT_TIMESTAMP, is_trusted = ? 
                        WHERE bssid = ?
                    ''', (network['ssid'], network['signal'], network['channel'], network['encryption'], is_trusted, bssid))
                else:
                    cursor.execute('''
                        INSERT INTO network_scans (bssid, ssid, signal_strength, channel, encryption, is_trusted) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (bssid, network['ssid'], network['signal'], network['channel'], network['encryption'], is_trusted))
        
        def analyze_networks(self, networks):
            threats = []
            for network in networks:
                self.update_network_database(network)
                if network.get('ssid', '').lower() in self.known_networks.get("suspicious_ssids", []):
                    threats.append({'bssid': network['bssid'], 'ssid': network['ssid'], 'reason': 'Ύποπτο SSID', 'level': 'MEDIUM'})
                if network.get('encryption', 'Άγνωστη') in ['WEP', 'Open']:
                    threats.append({'bssid': network['bssid'], 'ssid': network['ssid'], 'reason': f"Αδύναμη Κρυπτογράφηση ({network['encryption']})", 'level': 'HIGH'})
            return threats

        def display_network_info(self, networks, threats):
            print(f"\n{Fore.CYAN}{'='*65}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📊 ΑΠΟΤΕΛΕΣΜΑΤΑ ΣΑΡΩΣΗΣ WI-FI (Σύνολο: {len(networks)}){Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*65}{Style.RESET_ALL}")
            
            threat_bssids = {t['bssid'] for t in threats}
            
            sorted_networks = sorted(networks, key=lambda net: (
                not net.get('is_current', False), 
                net['bssid'] not in threat_bssids,
                net['bssid'] not in self.trusted_bssids,
                -net.get('signal', -100)
            ))
            
            for i, net in enumerate(sorted_networks, 1):
                bssid, ssid, signal, enc = net['bssid'], net['ssid'], net['signal'], net['encryption']
                status_flags = []
                
                if net.get('is_current'):
                    color, status = Fore.GREEN, "ΣΥΝΔΕΔΕΜΕΝΟ"
                elif bssid in threat_bssids:
                    color, status = Fore.RED, "ΕΝΕΡΓΗ ΑΠΕΙΛΗ"
                elif bssid in self.trusted_bssids:
                    color, status = Fore.GREEN, "ΕΜΠΙΣΤΟ"
                else:
                    color, status = Fore.WHITE, "ΠΑΡΑΤΗΡΗΘΗΚΕ"
                
                status_flags.append(f"{color}{status}{Style.RESET_ALL}")
                
                if enc in ['WEP', 'Open']:
                    enc_status = f"{Fore.RED}{enc} (ΜΗ ΑΣΦΑΛΕΣ!){Style.RESET_ALL}"
                elif 'WPA3' in enc:
                    enc_status = f"{Fore.GREEN}{enc}{Style.RESET_ALL}"
                else:
                    enc_status = f"{Fore.YELLOW}{enc}{Style.RESET_ALL}"
                    
                print(f"{color}--- ΔΙΚΤΥΟ {i}: {ssid or 'Κρυφό SSID'} {Style.RESET_ALL} (BSSID: {bssid}) ---")
                print(f"  Σήμα: {signal}dBm ({self.get_signal_quality(signal)}) | Κανάλι: {net['channel']}")
                print(f"  Κρυπτογράφηση: {enc_status}")
                print(f"  Κατάσταση: {' | '.join(status_flags)}")
                
                network_threats = [t for t in threats if t['bssid'] == bssid]
                for threat in network_threats:
                    t_color = Fore.RED if threat['level'] == 'HIGH' else Fore.YELLOW
                    print(f"{t_color}  🚨 ΑΠΕΙΛΗ ({threat['level']}): {threat['reason']}{Style.RESET_ALL}")
                print("-" * 65)

        def single_wifi_scan(self):
            networks = self.passive_network_scan()
            if networks:
                threats = self.analyze_networks(networks)
                self.display_network_info(networks, threats)
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def view_current_connection(self):
            print(f"\n{Fore.CYAN}🔗 ΤΡΕΧΟΥΣΑ ΣΥΝΔΕΣΗ WI-FI{Style.RESET_ALL}")
            print("="*50)
            current_info = self.get_current_connection_info()
            if not current_info or current_info['ssid'] == 'Μη Συνδεδεμένο':
                print(f"{Fore.RED}❌ Δεν είστε συνδεδεμένοι σε δίκτυο Wi-Fi.{Style.RESET_ALL}")
            else:
                bssid = current_info['bssid']
                trust_status = f"{Fore.GREEN}ΕΜΠΙΣΤΟ{Style.RESET_ALL}" if bssid in self.trusted_bssids else f"{Fore.YELLOW}ΑΓΝΩΣΤΟ{Style.RESET_ALL}"
                print(f"  SSID:        {current_info['ssid']}")
                print(f"  BSSID:       {bssid}")
                print(f"  Σήμα:        {current_info['signal']}dBm ({self.get_signal_quality(current_info['signal'])})")
                print(f"  Κρυπτογρ.:   {current_info['encryption']}")
                print(f"  Εμπιστοσύνη: {trust_status}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def toggle_wifi(self):
            print(f"\n{Fore.CYAN}🔄 ΕΝΑΛΛΑΓΗ WI-FI{Style.RESET_ALL}")
            if not os.path.exists('/data/data/com.termux'):
                print(f"{Fore.RED}❌ Αυτή η λειτουργία απαιτεί την εφαρμογή Termux:API.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                return

            choice = input(f"{Fore.WHITE}Ενεργοποίηση/Απενεργοποίηση Wi-Fi [on/off]? {Style.RESET_ALL}").strip().lower()
            if choice == 'on':
                print("[*] Ενεργοποίηση Wi-Fi...")
                self._run_termux_command(['termux-wifi-enable', 'true'])
                print(f"{Fore.GREEN}✅ Το Wi-Fi ενεργοποιήθηκε.{Style.RESET_ALL}")
            elif choice == 'off':
                print("[*] Απενεργοποίηση Wi-Fi...")
                self._run_termux_command(['termux-wifi-enable', 'false'])
                print(f"{Fore.GREEN}✅ Το Wi-Fi απενεργοποιήθηκε.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ Μη έγκυρη επιλογή.{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def scan_local_network(self):
            print(f"\n{Fore.CYAN}🌐 ΣΑΡΩΣΗ ΤΟΠΙΚΟΥ ΔΙΚΤΥΟΥ ΓΙΑ ΣΥΣΚΕΥΕΣ{Style.RESET_ALL}")
            
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
            except Exception as e:
                print(f"{Fore.RED}❌ Δεν ήταν δυνατός ο προσδιορισμός της τοπικής διεύθυνσης IP: {e}{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                return

            print(f"[*] Η τοπική σας IP είναι {local_ip}. Σάρωση του υποδικτύου /24...")
            ip_prefix = '.'.join(local_ip.split('.')[:-1]) + '.'
            
            active_hosts = []
            lock = threading.Lock()

            def ping_host(ip):
                command = ['ping', '-c', '1', '-W', '1', ip]
                try:
                    output = subprocess.run(command, capture_output=True, text=True, timeout=2)
                    if output.returncode == 0:
                        with lock:
                            active_hosts.append(ip)
                            print(f"{Fore.GREEN}[+] Βρέθηκε κεντρικός υπολογιστής: {ip}{Style.RESET_ALL}")
                except (subprocess.TimeoutExpired, Exception):
                    pass
            
            threads = []
            for i in range(1, 255):
                ip_to_scan = ip_prefix + str(i)
                if ip_to_scan == local_ip: continue
                thread = threading.Thread(target=ping_host, args=(ip_to_scan,))
                threads.append(thread)
                thread.start()
            
            print(f"[*] Η σάρωση ξεκίνησε για {ip_prefix}1-254. Παρακαλώ περιμένετε...")
            for t in threads:
                t.join()

            print(f"\n{Fore.GREEN}✅ Η σάρωση ολοκληρώθηκε!{Style.RESET_ALL}")
            if active_hosts:
                print(f"Βρέθηκαν {len(active_hosts)} ενεργοί κεντρικοί υπολογιστές (εκτός από εσάς):")
                for host in sorted(active_hosts):
                    print(f"  - {host}")
            else:
                print("Δεν βρέθηκαν άλλοι ενεργοί κεντρικοί υπολογιστές στο δίκτυο.")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def get_mobile_data_info(self):
            print(f"\n{Fore.CYAN}📱 ΠΛΗΡΟΦΟΡΙΕΣ ΔΙΚΤΥΟΥ ΚΙΝΗΤΗΣ / SIM{Style.RESET_ALL}")
            print("="*50)
            if not os.path.exists('/data/data/com.termux'):
                print(f"{Fore.RED}❌ Αυτή η λειτουργία απαιτεί την εφαρμογή Termux:API.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                return

            # Device Info
            device_info_out = self._run_termux_command(['termux-telephony-deviceinfo'])
            if device_info_out:
                try:
                    data = json.loads(device_info_out)
                    print(f"{Fore.CYAN}--- Πληροφορίες Συσκευής & SIM ---{Style.RESET_ALL}")
                    print(f"  Πάροχος Δικτύου:   {data.get('network_operator_name', 'N/A')}")
                    print(f"  Πάροχος SIM:        {data.get('sim_operator_name', 'N/A')}")
                    print(f"  Τύπος Τηλεφώνου:    {data.get('phone_type', 'N/A')}")
                    print(f"  Τύπος Δικτύου:      {data.get('data_network_type', 'N/A')}")
                    print(f"  Κατάσταση Δεδομένων: {data.get('data_state', 'N/A')}")
                except json.JSONDecodeError:
                    print(f"{Fore.YELLOW}[!] Δεν ήταν δυνατή η ανάλυση των πληροφοριών της συσκευής.{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}[!] Δεν ήταν δυνατή η ανάκτηση πληροφοριών συσκευής/SIM. Δεν υπάρχει SIM;{Style.RESET_ALL}")

            # Cell Tower Info
            cell_info_out = self._run_termux_command(['termux-telephony-cellinfo'])
            if cell_info_out:
                try:
                    data = json.loads(cell_info_out)
                    print(f"\n{Fore.CYAN}--- Κοντινοί Πύργοι Κινητής Τηλεφωνίας ---{Style.RESET_ALL}")
                    if not data.get('cells'):
                         print("  Δεν υπάρχουν διαθέσιμες πληροφορίες για πύργους κινητής τηλεφωνίας.")
                    for cell in data.get('cells', []):
                        cell_type = cell.get('type', 'N/A').upper()
                        strength = cell.get('dbm', 'N/A')
                        print(f"  - Τύπος: {cell_type} | Ισχύς: {strength} dBm ({self.get_signal_quality(strength)})")
                except json.JSONDecodeError:
                    print(f"{Fore.YELLOW}[!] Δεν ήταν δυνατή η ανάλυση των πληροφοριών των πύργων.{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}[!] Δεν ήταν δυνατή η ανάκτηση πληροφοριών των πύργων.{Style.RESET_ALL}")

            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        # --- Enhanced NMAP-like Network Scanning Tools ---
        def enhanced_port_scanner(self):
            """Enhanced port scanner with service detection and OS fingerprinting simulation"""
            print(f"\n{Fore.CYAN}🔍 ΒΕΛΤΙΩΜΕΝΟΣ ΣΑΡΩΤΗΣ ΘΥΡΩΝ (NMAP-LIKE){Style.RESET_ALL}")
            
            target = input(f"{Fore.WHITE}Εισαγάγετε IP στόχου ή όνομα κεντρικού υπολογιστή: {Style.RESET_ALL}").strip()
            if not target:
                return

            try:
                target_ip = socket.gethostbyname(target)
                print(f"[*] Επίλυση {target} σε {target_ip}")
            except socket.gaierror:
                print(f"{Fore.RED}❌ Δεν ήταν δυνατή η επίλυση του ονόματος κεντρικού υπολογιστή.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                return

            # Scan type selection
            print(f"\n{Fore.CYAN}Επιλέξτε Τύπο Σάρωσης:{Style.RESET_ALL}")
            print("1. TCP Connect Scan (Τυπική)")
            print("2. TCP SYN Scan (Stealth - Προσομοίωση)")
            print("3. UDP Scan (Βασική)")
            print("4. Πλήρης Σάρωση (TCP+Ανίχνευση Υπηρεσιών)")
            
            scan_choice = input(f"{Fore.WHITE}Επιλέξτε τύπο σάρωσης (1-4): {Style.RESET_ALL}").strip()
            
            # Port selection
            print(f"\n{Fore.CYAN}Επιλογή Θυρών:{Style.RESET_ALL}")
            print("1. Κοινές Θύρες (Top 100)")
            print("2. Θύρες Υπηρεσιών (Web, FTP, SSH, κ.λπ.)")
            print("3. Πλήρες Εύρος (1-1024)")
            print("4. Προσαρμοσμένο Εύρος")
            
            port_choice = input(f"{Fore.WHITE}Επιλέξτε εύρος θυρών (1-4): {Style.RESET_ALL}").strip()
            
            # Define port ranges
            port_presets = {
                '1': [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 995, 
                      1723, 3306, 3389, 5900, 8080, 8443] + list(range(1, 101)),
                '2': [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 993, 995, 1723, 3306, 
                      3389, 5900, 8080, 8443, 27017, 5432, 9200],
                '3': list(range(1, 1025))
            }
            
            if port_choice == '4':
                custom_range = input(f"{Fore.WHITE}Εισαγάγετε προσαρμοσμένο εύρος (π.χ., 1-1000): {Style.RESET_ALL}").strip()
                try:
                    start, end = map(int, custom_range.split('-'))
                    ports_to_scan = list(range(start, end + 1))
                except ValueError:
                    print(f"{Fore.RED}❌ Μη έγκυρη μορφή εύρους θυρών.{Style.RESET_ALL}")
                    return
            else:
                ports_to_scan = port_presets.get(port_choice, port_presets['1'])
            
            print(f"[*] Σάρωση του {target_ip} σε {len(ports_to_scan)} θύρες...")
            
            open_ports = []
            service_info = {}
            
            def tcp_connect_scan(port):
                """Standard TCP connect scan"""
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(2)
                        result = sock.connect_ex((target_ip, port))
                        if result == 0:
                            open_ports.append(port)
                            # Try to grab banner
                            try:
                                sock.settimeout(3)
                                service = self.grab_banner(sock, port)
                                service_info[port] = service
                            except:
                                service_info[port] = "Άγνωστο"
                            return True
                except:
                    pass
                return False
            
            def udp_scan(port):
                """Basic UDP port scan"""
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                        sock.settimeout(3)
                        # Send empty packet
                        sock.sendto(b'', (target_ip, port))
                        try:
                            data, addr = sock.recvfrom(1024)
                            open_ports.append(port)
                            service_info[port] = "Απόκριση UDP"
                            return True
                        except socket.timeout:
                            # No response could mean open or filtered
                            pass
                except:
                    pass
                return False
            
            # Perform scan based on type
            if scan_choice in ['1', '2', '4']:  # TCP scans
                print(f"[*] Εκτέλεση σάρωσης TCP...")
                threads = []
                for port in ports_to_scan:
                    thread = threading.Thread(target=tcp_connect_scan, args=(port,))
                    threads.append(thread)
                    thread.start()
                    if len(threads) >= self.config['port_scan_threads']:
                        for t in threads:
                            t.join()
                        threads = []
                for t in threads:
                    t.join()
            
            if scan_choice in ['3', '4']:  # UDP scans
                print(f"[*] Εκτέλεση σάρωσης UDP...")
                udp_ports = [53, 67, 68, 69, 123, 161, 162, 514, 5353, 1900]
                for port in udp_ports:
                    if port in ports_to_scan:
                        udp_scan(port)
            
            # Display results
            print(f"\n{Fore.GREEN}✅ Η βελτιωμένη σάρωση ολοκληρώθηκε!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            if open_ports:
                print(f"Βρέθηκαν {len(open_ports)} ανοιχτές θύρες:")
                for port in sorted(open_ports):
                    service = service_info.get(port, "Άγνωστο")
                    status = f"{Fore.GREEN}ΑΝΟΙΧΤΗ{Style.RESET_ALL}"
                    print(f"  Θύρα {port:5} - {status} - {service}")
                    
                    # Record finding
                    self.record_audit_finding(target, 'Βελτιωμένη Σάρωση Θυρών', 
                                            f'Ανοιχτή Θύρα: {port}', 
                                            f'Η θύρα {port} ({service}) είναι ανοιχτή στο {target_ip}', 
                                            'Πληροφορία')
            else:
                print("Δεν βρέθηκαν ανοιχτές θύρες.")
            
            # OS fingerprinting simulation
            if scan_choice in ['2', '4'] and open_ports:
                print(f"\n{Fore.CYAN}🖥️  ΑΝΑΓΝΩΡΙΣΗ ΛΕΙΤΟΥΡΓΙΚΟΥ ΣΥΣΤΗΜΑΤΟΣ (Προσομοίωση){Style.RESET_ALL}")
                predicted_os = self.simulate_os_fingerprinting(open_ports)
                print(f"Προβλεπόμενο ΛΣ: {predicted_os}")
                self.record_audit_finding(target, 'Ανίχνευση ΛΣ', 
                                        'Ανίχνευση Λειτουργικού Συστήματος', 
                                        f'Προβλεπόμενο ΛΣ: {predicted_os}', 
                                        'Πληροφορία')
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def grab_banner(self, sock, port):
            """Attempt to grab service banner from open port"""
            try:
                # Common service probes
                if port == 80 or port == 443:
                    sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').split('\n')[0]
                    return f"HTTP - {banner}"
                elif port == 21:
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                    return f"FTP - {banner}"
                elif port == 22:
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                    return f"SSH - {banner}"
                elif port == 25:
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                    return f"SMTP - {banner}"
                elif port == 53:
                    return "DNS"
                elif port == 443:
                    return "HTTPS"
                else:
                    # Generic banner grab
                    sock.settimeout(2)
                    try:
                        banner = sock.recv(256).decode('utf-8', errors='ignore').strip()
                        if banner:
                            return banner[:50] + "..." if len(banner) > 50 else banner
                    except:
                        pass
                    return "Εντοπίστηκε υπηρεσία"
            except:
                return "Εντοπίστηκε υπηρεσία"

        def simulate_os_fingerprinting(self, open_ports):
            """Simulate basic OS fingerprinting based on open ports"""
            # Common port patterns for different OSes
            os_patterns = {
                'Windows': [135, 139, 445, 3389],
                'Linux/Unix': [22, 111, 513, 514],
                'Συσκευή Δικτύου': [23, 80, 443, 161, 162],
                'Web Server': [80, 443, 8080, 8443],
                'Database Server': [1433, 1521, 3306, 5432, 27017]
            }
            
            scores = {}
            for os_name, ports in os_patterns.items():
                score = len(set(open_ports) & set(ports))
                scores[os_name] = score
            
            # Also consider port ranges
            if any(port in range(135, 140) for port in open_ports):
                scores['Windows'] += 2
            if 22 in open_ports:
                scores['Linux/Unix'] += 2
            
            if scores:
                best_match = max(scores.items(), key=lambda x: x[1])
                confidence = "Υψηλή" if best_match[1] > 2 else "Μέτρια" if best_match[1] > 0 else "Χαμηλή"
                return f"{best_match[0]} (βεβαιότητα {confidence})"
            
            return "Άγνωστο ΛΣ"

        def network_discovery(self):
            """Advanced network discovery using multiple techniques"""
            print(f"\n{Fore.CYAN}🌐 ΠΡΟΗΓΜΕΝΗ ΑΝΑΚΑΛΥΨΗ ΔΙΚΤΥΟΥ{Style.RESET_ALL}")
            
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
            except Exception as e:
                print(f"{Fore.RED}❌ Δεν ήταν δυνατός ο προσδιορισμός της τοπικής IP: {e}{Style.RESET_ALL}")
                return
            
            network_base = '.'.join(local_ip.split('.')[:-1]) + '.'
            
            print(f"[*] Η IP σας: {local_ip}")
            print(f"[*] Σάρωση δικτύου: {network_base}0/24")
            print(f"[*] Χρήση πολλαπλών μεθόδων ανακάλυψης...")
            
            discovered_hosts = set()
            
            # Method 1: ICMP Ping
            print(f"\n{Fore.YELLOW}[1/3] Σάρωση ICMP Ping...{Style.RESET_ALL}")
            def ping_host(ip):
                try:
                    subprocess.run(['ping', '-c', '1', '-W', '1', ip], 
                                 capture_output=True, timeout=2)
                    discovered_hosts.add(ip)
                    print(f"  {Fore.GREEN}[+] {ip} - Ενεργός (ICMP){Style.RESET_ALL}")
                except:
                    pass
            
            # Method 2: TCP SYN to common ports
            print(f"{Fore.YELLOW}[2/3] Ανακάλυψη Θυρών TCP...{Style.RESET_ALL}")
            def tcp_probe(ip, port):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(1)
                        if sock.connect_ex((ip, port)) == 0:
                            discovered_hosts.add(ip)
                            print(f"  {Fore.GREEN}[+] {ip} - Ενεργός (TCP/{port}){Style.RESET_ALL}")
                            return True
                except:
                    pass
                return False
            
            # Method 3: ARP discovery (if available)
            print(f"{Fore.YELLOW}[3/3] Ανακάλυψη ARP...{Style.RESET_ALL}")
            def arp_discovery(ip):
                try:
                    # This is a simulated ARP discovery for non-root
                    # Real ARP requires root privileges
                    if tcp_probe(ip, 80) or tcp_probe(ip, 443) or tcp_probe(ip, 22):
                        print(f"  {Fore.GREEN}[+] {ip} - Ενεργός (Προσομοίωση ARP){Style.RESET_ALL}")
                except:
                    pass
            
            # Run all discovery methods
            threads = []
            common_ports = [22, 23, 80, 443, 3389, 8080]
            
            for i in range(1, 255):
                ip = network_base + str(i)
                if ip == local_ip:
                    continue
                    
                # Ping
                t = threading.Thread(target=ping_host, args=(ip,))
                threads.append(t)
                t.start()
                
                # TCP probes
                for port in common_ports:
                    t = threading.Thread(target=tcp_probe, args=(ip, port))
                    threads.append(t)
                    t.start()
                
                # ARP simulation
                t = threading.Thread(target=arp_discovery, args=(ip,))
                threads.append(t)
                t.start()
                
                # Limit concurrent threads
                if len(threads) > 50:
                    for t in threads:
                        t.join()
                    threads = []
            
            for t in threads:
                t.join()
            
            print(f"\n{Fore.GREEN}✅ Η ανακάλυψη δικτύου ολοκληρώθηκε!{Style.RESET_ALL}")
            print(f"Ανακαλύφθηκαν {len(discovered_hosts)} ενεργοί κεντρικοί υπολογιστές:")
            for host in sorted(discovered_hosts):
                print(f"  - {host}")
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def subnet_calculator(self):
            """Subnet calculator and network information tool"""
            print(f"\n{Fore.CYAN}🧮 ΥΠΟΛΟΓΙΣΤΗΣ ΥΠΟΔΙΚΤΥΟΥ{Style.RESET_ALL}")
            
            ip_input = input(f"{Fore.WHITE}Εισαγάγετε διεύθυνση IP με CIDR (π.χ., 192.168.1.0/24): {Style.RESET_ALL}").strip()
            
            if not ip_input or '/' not in ip_input:
                print(f"{Fore.RED}❌ Παρακαλώ χρησιμοποιήστε τη μορφή: IP/CIDR{Style.RESET_ALL}")
                return
            
            try:
                ip_str, cidr_str = ip_input.split('/')
                cidr = int(cidr_str)
                
                # Convert IP to integer
                ip_parts = list(map(int, ip_str.split('.')))
                ip_int = (ip_parts[0] << 24) + (ip_parts[1] << 16) + (ip_parts[2] << 8) + ip_parts[3]
                
                # Calculate subnet mask
                mask_int = (0xFFFFFFFF << (32 - cidr)) & 0xFFFFFFFF
                mask_parts = [
                    (mask_int >> 24) & 0xFF,
                    (mask_int >> 16) & 0xFF,
                    (mask_int >> 8) & 0xFF,
                    mask_int & 0xFF
                ]
                subnet_mask = '.'.join(map(str, mask_parts))
                
                # Calculate network and broadcast addresses
                network_int = ip_int & mask_int
                broadcast_int = network_int | (0xFFFFFFFF >> cidr)
                
                def int_to_ip(ip_int):
                    return '.'.join([
                        str((ip_int >> 24) & 0xFF),
                        str((ip_int >> 16) & 0xFF),
                        str((ip_int >> 8) & 0xFF),
                        str(ip_int & 0xFF)
                    ])
                
                network_addr = int_to_ip(network_int)
                broadcast_addr = int_to_ip(broadcast_int)
                
                # Calculate usable hosts
                total_hosts = 2 ** (32 - cidr)
                usable_hosts = total_hosts - 2 if total_hosts > 2 else total_hosts
                
                # Display results
                print(f"\n{Fore.GREEN}📊 ΑΠΟΤΕΛΕΣΜΑΤΑ ΥΠΟΛΟΓΙΣΜΟΥ ΥΠΟΔΙΚΤΥΟΥ:{Style.RESET_ALL}")
                print(f"  Διεύθυνση IP:           {ip_str}")
                print(f"  Σημειογραφία CIDR:       /{cidr}")
                print(f"  Μάσκα Υποδικτύου:        {subnet_mask}")
                print(f"  Διεύθυνση Δικτύου:      {network_addr}")
                print(f"  Διεύθυνση Broadcast:    {broadcast_addr}")
                print(f"  Συνολικοί Υπολογιστές:  {total_hosts}")
                print(f"  Χρήσιμοι Υπολογιστές:   {usable_hosts}")
                
                if usable_hosts > 0:
                    first_host = int_to_ip(network_int + 1)
                    last_host = int_to_ip(broadcast_int - 1)
                    print(f"  Πρώτος Χρήσιμος:         {first_host}")
                    print(f"  Τελευταίος Χρήσιμος:    {last_host}")
                
            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα στον υπολογισμό του υποδικτύου: {e}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        # --- Internet & Diagnostics ---
        def run_internet_speed_test(self):
            print(f"\n{Fore.CYAN}⚡️ ΕΚΤΕΛΕΣΗ ΔΟΚΙΜΗΣ ΤΑΧΥΤΗΤΑΣ INTERNET...{Style.RESET_ALL}")
            if not SPEEDTEST_AVAILABLE or not speedtest:
                print(f"{Fore.RED}❌ Το module 'speedtest-cli' δεν είναι διαθέσιμο. Εκτελέστε τον εγκαταστάτη εξαρτήσεων.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                return

            try:
                st = speedtest.Speedtest()
                print(f"{Fore.YELLOW}[*] Εύρεση καλύτερου διακομιστή...{Style.RESET_ALL}")
                st.get_best_server()
                print(f"{Fore.YELLOW}[*] Εκτέλεση δοκιμής λήψης...{Style.RESET_ALL}")
                download_speed = st.download() / 1_000_000
                print(f"{Fore.YELLOW}[*] Εκτέλεση δοκιμής αποστολής...{Style.RESET_ALL}")
                upload_speed = st.upload() / 1_000_000
                ping = st.results.ping
                
                print(f"\n{Fore.GREEN}✅ Η ΔΟΚΙΜΗ ΤΑΧΥΤΗΤΑΣ ΟΛΟΚΛΗΡΩΘΗΚΕ!{Style.RESET_ALL}")
                print("="*50)
                print(f"  Διακομιστής: {st.results.server['name']} ({st.results.server['country']})")
                print(f"  Ping:         {ping:.2f} ms")
                print(f"  Λήψη:         {Fore.GREEN}{download_speed:.2f} Mbps{Style.RESET_ALL}")
                print(f"  Αποστολή:     {Fore.GREEN}{upload_speed:.2f} Mbps{Style.RESET_ALL}")
                print("="*50)
            except Exception as e:
                print(f"{Fore.RED}❌ Η δοκιμή ταχύτητας απέτυχε: {e}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def get_external_ip_info(self):
            print(f"\n{Fore.CYAN}🗺️ ΛΗΨΗ ΠΛΗΡΟΦΟΡΙΩΝ ΕΞΩΤΕΡΙΚΗΣ IP...{Style.RESET_ALL}")
            if not REQUESTS_AVAILABLE:
                print(f"{Fore.RED}❌ Το module 'requests' δεν είναι διαθέσιμο.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                return
            try:
                data = requests.get("http://ip-api.com/json/", timeout=10).json()
                if data.get('status') == 'success':
                    print(f"\n{Fore.GREEN}✅ Πληροφορίες Εξωτερικής IP:{Style.RESET_ALL}")
                    print(f"  Διεύθυνση IP:   {data.get('query')}")
                    print(f"  ISP/Πάροχος:    {data.get('isp')}")
                    print(f"  Τοποθεσία:       {data.get('city')}, {data.get('country')}")
                else:
                    print(f"{Fore.RED}❌ Αποτυχία ανάκτησης πληροφοριών IP.{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Αποτυχία σύνδεσης με την υπηρεσία IP: {e}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
            
        def run_network_diagnostics(self):
            print(f"\n{Fore.CYAN}📶 ΔΙΑΓΝΩΣΤΙΚΑ ΔΙΚΤΥΟΥ{Style.RESET_ALL}")
            host = input(f"{Fore.WHITE}Εισαγάγετε όνομα κεντρικού υπολογιστή ή IP για δοκιμή (π.χ., google.com): {Style.RESET_ALL}").strip()
            if not host: return
            
            print(f"\n{Fore.CYAN}>>> Εκτέλεση δοκιμής PING στο {host}...{Style.RESET_ALL}")
            try:
                result = subprocess.run(['ping', '-c', '4', host], capture_output=True, text=True, timeout=10)
                print(result.stdout if result.returncode == 0 else result.stderr)
            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα κατά την εκτέλεση του ping: {e}{Style.RESET_ALL}")
            
            print(f"\n{Fore.CYAN}>>> Εκτέλεση δοκιμής TRACEROUTE στο {host}...{Style.RESET_ALL}")
            try:
                result = subprocess.run(['traceroute', '-n', host], capture_output=True, text=True, timeout=30)
                print(result.stdout if result.returncode == 0 else result.stderr)
            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα κατά την εκτέλεση του traceroute. Βεβαιωθείτε ότι το 'inetutils' είναι εγκατεστημένο: {e}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        # --- Information Gathering ---
        def get_whois_info(self):
            print(f"\n{Fore.CYAN}👤 ΑΝΑΖΗΤΗΣΗ WHOIS{Style.RESET_ALL}")
            if not WHOIS_AVAILABLE:
                print(f"{Fore.RED}❌ Το module 'python-whois' δεν είναι διαθέσιμο.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                return
            
            domain = input(f"{Fore.WHITE}Εισαγάγετε τομέα για αναζήτηση (π.χ., google.com): {Style.RESET_ALL}").strip()
            if not domain: return
            try:
                w = whois.whois(domain)
                print(f"{Fore.GREEN}✅ Πληροφορίες WHOIS για το {domain}:{Style.RESET_ALL}")
                for key, value in w.items():
                    if value:
                        print(f"  {str(key).replace('_', ' ').title()}: {value}")
            except Exception as e:
                print(f"{Fore.RED}❌ Η αναζήτηση WHOIS απέτυχε: {e}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def get_dns_records(self):
            print(f"\n{Fore.CYAN}🌐 ΑΝΑΖΗΤΗΣΗ ΕΓΓΡΑΦΩΝ DNS{Style.RESET_ALL}")
            if not DNS_AVAILABLE:
                print(f"{Fore.RED}❌ Το module 'dnspython' δεν είναι διαθέσιμο.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                return
            
            domain = input(f"{Fore.WHITE}Εισαγάγετε τομέα για ερώτημα (π.χ., google.com): {Style.RESET_ALL}").strip()
            if not domain: return

            record_types = ['A', 'AAAA', 'MX', 'TXT', 'NS', 'CNAME']
            print(f"{Fore.GREEN}✅ Εγγραφές DNS για το {domain}:{Style.RESET_ALL}")
            for rtype in record_types:
                try:
                    answers = dns_resolver.resolve(domain, rtype)
                    print(f"{Fore.CYAN}  --- Εγγραφές {rtype} ---{Style.RESET_ALL}")
                    for rdata in answers:
                        print(f"    {rdata.to_text()}")
                except (dns_resolver.NoAnswer, dns_resolver.NXDOMAIN):
                    print(f"{Fore.YELLOW}  --- Δεν βρέθηκαν εγγραφές {rtype} ---{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}  --- Σφάλμα κατά το ερώτημα για εγγραφές {rtype}: {e} ---{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
            
        # --- Security Auditing Tools (Non-Root) ---
        def port_scanner(self):
            print(f"\n{Fore.CYAN}🔎 ΣΑΡΩΤΗΣ ΘΥΡΩΝ{Style.RESET_ALL}")
            target = input(f"{Fore.WHITE}Εισαγάγετε IP στόχου ή όνομα κεντρικού υπολογιστή: {Style.RESET_ALL}").strip()
            if not target: return
            
            try:
                target_ip = socket.gethostbyname(target)
                print(f"[*] Επίλυση {target} σε {target_ip}")
            except socket.gaierror:
                print(f"{Fore.RED}❌ Δεν ήταν δυνατή η επίλυση του ονόματος κεντρικού υπολογιστή.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                return

            port_range_str = input(f"{Fore.WHITE}Εισαγάγετε εύρος θυρών (π.χ., 1-1024) ή 'top' για κοινές θύρες: {Style.RESET_ALL}").strip().lower()
            
            ports_to_scan = []
            if port_range_str == 'top':
                ports_to_scan = [int(p) for p in self.config['top_ports'].split(',')]
            else:
                try:
                    start, end = map(int, port_range_str.split('-'))
                    ports_to_scan = range(start, end + 1)
                except ValueError:
                    print(f"{Fore.RED}❌ Μη έγκυρη μορφή εύρους θυρών.{Style.RESET_ALL}")
                    input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                    return
            
            open_ports = []
            print(f"[*] Σάρωση του {target_ip} σε {len(list(ports_to_scan))} θύρες...")
            
            def scan_port(port):
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    if sock.connect_ex((target_ip, port)) == 0:
                        open_ports.append(port)

            threads = []
            for port in ports_to_scan:
                thread = threading.Thread(target=scan_port, args=(port,))
                threads.append(thread)
                thread.start()
                if len(threads) >= self.config['port_scan_threads']:
                    for t in threads: t.join()
                    threads = []
            for t in threads: t.join()

            print(f"\n{Fore.GREEN}✅ Η σάρωση ολοκληρώθηκε!{Style.RESET_ALL}")
            if open_ports:
                print(f"Βρέθηκαν {len(open_ports)} ανοιχτές θύρες:")
                for port in sorted(open_ports):
                    try:
                        service = socket.getservbyport(port, 'tcp')
                    except OSError:
                        service = "Άγνωστο"
                    print(f"  {Fore.GREEN}Θύρα {port}{Style.RESET_ALL} ({service}) είναι ΑΝΟΙΧΤΗ")
                    self.record_audit_finding(target, 'Σάρωση Θυρών', f'Ανοιχτή Θύρα: {port}/{service}', f'Η θύρα {port} είναι ανοιχτή στο {target_ip}', 'Πληροφορία')
            else:
                print("Δεν βρέθηκαν ανοιχτές θύρες στο καθορισμένο εύρος.")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def http_header_analyzer(self):
            print(f"\n{Fore.CYAN}📋 ΑΝΑΛΥΤΗΣ ΚΕΦΑΛΙΔΩΝ ΑΣΦΑΛΕΙΑΣ HTTP{Style.RESET_ALL}")
            if not REQUESTS_AVAILABLE:
                print(f"{Fore.RED}❌ Το module 'requests' δεν είναι διαθέσιμο.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                return
            
            url = input(f"{Fore.WHITE}Εισαγάγετε URL για ανάλυση (π.χ., https://google.com): {Style.RESET_ALL}").strip()
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            try:
                response = requests.get(url, timeout=10, allow_redirects=True)
                headers = response.headers
                print(f"\n{Fore.GREEN}✅ Ανάλυση κεφαλίδων για {response.url}{Style.RESET_ALL}")
                
                security_headers = {
                    'Strict-Transport-Security': {'present': False, 'desc': 'Επιβάλλει το HTTPS, αποτρέποντας επιθέσεις υποβάθμισης.'},
                    'Content-Security-Policy': {'present': False, 'desc': 'Αποτρέπει το XSS καθορίζοντας πηγές περιεχομένου.'},
                    'X-Content-Type-Options': {'present': False, 'desc': 'Αποτρέπει επιθέσεις MIME-sniffing.'},
                    'X-Frame-Options': {'present': False, 'desc': 'Προστατεύει από επιθέσεις clickjacking.'},
                    'Referrer-Policy': {'present': False, 'desc': 'Ελέγχει πόσες πληροφορίες referrer αποστέλλονται.'},
                    'Permissions-Policy': {'present': False, 'desc': 'Ελέγχει ποιες δυνατότητες του προγράμματος περιήγησης μπορούν να χρησιμοποιηθούν.'}
                }

                for header, info in security_headers.items():
                    if header in headers:
                        info['present'] = True
                        print(f"{Fore.GREEN}[✔] {header}: Βρέθηκε{Style.RESET_ALL}")
                        self.record_audit_finding(url, 'Ανάλυση Κεφαλίδων', f'Βρέθηκε Κεφαλίδα: {header}', f"Τιμή: {headers[header]}", 'Πληροφορία')
                    else:
                        print(f"{Fore.RED}[❌] {header}: Λείπει{Style.RESET_ALL} - {info['desc']}")
                        self.record_audit_finding(url, 'Ανάλυση Κεφαλίδων', f'Λείπει Κεφαλίδα: {header}', info['desc'], 'Μέτρια')
                
                if 'Server' in headers:
                    print(f"{Fore.YELLOW}[!] Εκτεθειμένο Banner Διακομιστή: {headers['Server']}{Style.RESET_ALL}")
                    self.record_audit_finding(url, 'Ανάλυση Κεφαλίδων', 'Εκτεθειμένο Banner Διακομιστή', f"Διακομιστής: {headers['Server']}", 'Χαμηλή')

            except Exception as e:
                print(f"{Fore.RED}❌ Αποτυχία ανάλυσης URL: {e}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
        
        def web_crawler(self):
            print(f"\n{Fore.CYAN}🕷️ WEB CRAWLER / ΕΞΑΓΩΓΕΑΣ ΣΥΝΔΕΣΜΩΝ{Style.RESET_ALL}")
            if not REQUESTS_AVAILABLE or not BS4_AVAILABLE:
                print(f"{Fore.RED}❌ Απαιτούνται τα modules 'requests' και 'beautifulsoup4'.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                return

            start_url = input(f"{Fore.WHITE}Εισαγάγετε αρχικό URL για ανίχνευση: {Style.RESET_ALL}").strip()
            if not start_url.startswith(('http://', 'https://')):
                start_url = 'https://' + start_url
            
            max_links = int(input(f"{Fore.WHITE}Εισαγάγετε μέγιστο αριθμό συνδέσμων προς εύρεση: {Style.RESET_ALL}").strip() or 50)
            
            domain_name = urlparse(start_url).netloc
            crawled = set()
            to_crawl = deque([start_url])
            internal_links = set()

            print(f"[*] Ανίχνευση του {start_url} (τομέας: {domain_name})...")
            
            try:
                while to_crawl and len(internal_links) < max_links:
                    url = to_crawl.popleft()
                    if url in crawled: continue
                    
                    crawled.add(url)
                    print(f"  > Επίσκεψη: {url}")
                    
                    response = requests.get(url, timeout=5)
                    soup = BeautifulSoup(response.content, "html.parser")
                    
                    for a_tag in soup.findAll("a"):
                        href = a_tag.attrs.get("href")
                        if not href: continue
                        
                        href = urljoin(url, href)
                        parsed_href = urlparse(href)
                        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
                        
                        if domain_name in href and href not in internal_links:
                            internal_links.add(href)
                            if href not in crawled:
                                to_crawl.append(href)
            except Exception as e:
                print(f"{Fore.RED}Η ανίχνευση σταμάτησε λόγω σφάλματος: {e}{Style.RESET_ALL}")

            print(f"\n{Fore.GREEN}✅ Η ανίχνευση ολοκληρώθηκε. Βρέθηκαν {len(internal_links)} εσωτερικοί σύνδεσμοι:{Style.RESET_ALL}")
            for link in sorted(list(internal_links)):
                print(f"  - {link}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
            
        # --- Utility Tools ---
        def generate_password(self):
            print(f"\n{Fore.CYAN}🔑 ΓΕΝΝΗΤΡΙΑ ΚΩΔΙΚΩΝ ΠΡΟΣΒΑΣΗΣ{Style.RESET_ALL}")
            try:
                length = int(input(f"{Fore.WHITE}Εισαγάγετε μήκος κωδικού (π.χ., 16): {Style.RESET_ALL}").strip())
                if length < 8:
                    print(f"{Fore.YELLOW}Προειδοποίηση: Οι κωδικοί πρόσβασης με λιγότερους από 8 χαρακτήρες είναι αδύναμοι.{Style.RESET_ALL}")
                
                chars = string.ascii_letters + string.digits + string.punctuation
                password = ''.join(random.choice(chars) for _ in range(length))
                
                print(f"\n{Fore.GREEN}Δημιουργημένος Κωδικός:{Style.RESET_ALL} {password}")
            except ValueError:
                print(f"{Fore.RED}❌ Μη έγκυρο μήκος. Παρακαλώ εισαγάγετε έναν αριθμό.{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def hashing_tool(self):
            print(f"\n{Fore.CYAN}🧮 ΕΡΓΑΛΕΙΟ ΚΑΤΑΚΕΡΜΑΤΙΣΜΟΥ (HASHING){Style.RESET_ALL}")
            text_to_hash = input(f"{Fore.WHITE}Εισαγάγετε κείμενο για κατακερματισμό: {Style.RESET_ALL}")
            if not text_to_hash: return

            print("\n--- Hashes ---")
            print(f"  MD5:    {hashlib.md5(text_to_hash.encode()).hexdigest()}")
            print(f"  SHA1:   {hashlib.sha1(text_to_hash.encode()).hexdigest()}")
            print(f"  SHA256: {hashlib.sha256(text_to_hash.encode()).hexdigest()}")
            print(f"  SHA512: {hashlib.sha512(text_to_hash.encode()).hexdigest()}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

# Made by DedSec Project/dedsec1121fk!

        # --- Main Dashboard & Menu Logic ---
        def show_dashboard(self):
            if not CURSES_AVAILABLE:
                print(f"\n{Fore.RED}❌ ΚΡΙΣΙΜΟ ΣΦΑΛΜΑ: Το module 'curses' απαιτείται για το μενού TUI αλλά δεν είναι διαθέσιμο.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Αυτό το εργαλείο δεν μπορεί να εκτελεστεί χωρίς τη γραφική του διεπαφή.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Στο Termux, παρακαλώ εγκαταστήστε το εκτελώντας: 'pkg install ncurses-utils'{Style.RESET_ALL}")
                sys.exit(1)

            stdscr = None
            try:
                stdscr = curses.initscr()
                _reset_curses_state(stdscr)

                MENU_OPTIONS = [
                    "--- WI-FI & ΤΟΠΙΚΟ ΔΙΚΤΥΟ ---",
                    "📡 Σάρωση για Δίκτυα Wi-Fi",
                    "🔗 Προβολή Τρέχουσας Σύνδεσης Wi-Fi",
                    "🔄 Εναλλαγή Wi-Fi (Ενεργό/Ανενεργό)",
                    "🌐 Σάρωση Τοπικού Δικτύου για Συσκευές",
                    "--- ΑΝΑΚΑΛΥΨΗ ΔΙΚΤΥΟΥ ---",
                    "🔍 Βελτιωμένος Σαρωτής Θυρών (NMAP-like)",
                    "🌐 Προηγμένη Ανακάλυψη Δικτύου",
                    "🧮 Υπολογιστής Υποδικτύου",
                    "--- ΚΙΝΗΤΗ & ΤΗΛΕΦΩΝΙΑ ---",
                    "📱 Πληροφορίες Δικτύου Κινητής / SIM",
                    "--- INTERNET & ΔΙΑΓΝΩΣΤΙΚΑ ---",
                    "⚡️ Δοκιμή Ταχύτητας Internet",
                    "📶 Διαγνωστικά Δικτύου (Ping/Traceroute)",
                    "🗺️ Λήψη Εξωτερικής IP / Γεω-πληροφοριών",
                    "--- ΣΥΛΛΟΓΗ ΠΛΗΡΟΦΟΡΙΩΝ ---",
                    "👤 Αναζήτηση WHOIS Τομέα",
                    "🌐 Αναζήτηση Εγγραφών DNS",
                    "🕷️ Web Crawler / Εξαγωγέας Συνδέσμων",
                    "--- ΕΛΕΓΧΟΣ ΑΣΦΑΛΕΙΑΣ ---",
                    "🔎 Σαρωτής Θυρών",
                    "📋 Αναλυτής Κεφαλίδων Ασφαλείας HTTP",
                    "--- ΒΟΗΘΗΤΙΚΑ ΕΡΓΑΛΕΙΑ ---",
                    "🔑 Γεννήτρια Κωδικών Πρόσβασης",
                    "🧮 Εργαλείο Κατακερματισμού (Hashing)",
                    "--- ΕΞΟΔΟΣ ---",
                    "❌ Έξοδος"
                ]
                
                while True:
                    selection_index = _draw_curses_menu(stdscr, "ΠΙΝΑΚΑΣ ΕΛΕΓΧΟΥ ΕΡΓΑΛΕΙΩΝ ΔΙΚΤΥΟΥ", MENU_OPTIONS)
                    curses.endwin()
                    
                    action_map = {
                        1: self.single_wifi_scan,
                        2: self.view_current_connection,
                        3: self.toggle_wifi,
                        4: self.scan_local_network,
                        6: self.enhanced_port_scanner,
                        7: self.network_discovery,
                        8: self.subnet_calculator,
                        10: self.get_mobile_data_info,
                        12: self.run_internet_speed_test,
                        13: self.run_network_diagnostics,
                        14: self.get_external_ip_info,
                        16: self.get_whois_info,
                        17: self.get_dns_records,
                        18: self.web_crawler,
                        20: self.port_scanner,
                        21: self.http_header_analyzer,
                        23: self.generate_password,
                        24: self.hashing_tool,
                        26: lambda: True # Exit condition
                    }
                    
                    action = action_map.get(selection_index)
                    if action:
                        if action(): # If action returns True, it's the exit signal
                            print(f"\n{Fore.GREEN}👋 Ευχαριστούμε που χρησιμοποιήσατε τα Εργαλεία Δικτύου!{Style.RESET_ALL}")
                            break
                    
                    if selection_index != 26:
                        stdscr = curses.initscr()
                        _reset_curses_state(stdscr)

            except Exception as e:
                if stdscr: curses.endwin()
                print(f"{Fore.RED}❌ Παρουσιάστηκε ένα απρόσμενο σφάλμα TUI: {e}{Style.RESET_ALL}")
            finally:
                if stdscr and not stdscr.isendwin():
                     curses.endwin()

    print(f"\n{Fore.GREEN}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}        ΕΡΓΑΛΕΙΑ ΔΙΚΤΥΟΥ - ΕΤΟΙΜΑ!{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'='*50}{Style.RESET_ALL}")
    
    app = InternetTools()
    app.show_dashboard()


def main():
    """Main entry point - auto installs and runs the main application."""
    try:
        if auto_install_dependencies():
            main_internet_tools()
        else:
            print("❌ Αποτυχία εγκατάστασης εξαρτήσεων. Ελέγξτε τη σύνδεσή σας και τα δικαιώματα.")
            sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n\n👋 Η συνεδρία τερματίστηκε από τον χρήστη.")
    except Exception as e:
        print(f"\n💥 Παρουσιάστηκε ένα απρόσμενο σφάλμα στην κύρια εκτέλεση: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()