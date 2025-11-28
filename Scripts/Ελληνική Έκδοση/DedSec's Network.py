#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Προηγμένο Εργαλείο Δικτύων & Ασφάλειας
Συνδυασμένο, βελτιστοποιημένο και βελτιωμένο για Termux.
Λειτουργεί 100% χωρίς δικαιώματα root.
Βελτιστοποιημένο για συσκευές με περιορισμένους πόρους (π.χ. 2GB RAM).
"""

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
import hashlib
import random
import string
import struct
import select  # Προστέθηκε για SSH Defender
import math    # Προστέθηκε για SSH Defender
import queue
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor # Προστέθηκε για SSH Defender
import html
import tempfile
import webbrowser
import shutil


# --- Εισαγωγές Εξαρτήσεων & Παγκόσμιες Σημαίες ---
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
csv = None # Για το module OSINTDS

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
    # Εφεδρική λύση αν το colorama δεν είναι εγκατεστημένο
    class DummyColor:
        def __getattr__(self, name): return ''
    Fore = Back = Style = DummyColor()

# 3. Δυναμικές απόπειρες εισαγωγής για άλλα modules
def _try_import(module_name, global_var_name):
    """Δυναμική εισαγωγή module και ρύθμιση παγκόσμιας σημαίας."""
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
_try_import('csv', 'csv') # Για το module OSINTDS


# ==============================================================================
# SSH DEFENDER - ΠΑΓΚΟΣΜΙΕΣ ΣΤΑΘΕΡΕΣ
# ==============================================================================

# Κατάταξη γνωστών θυρών SSH/Honeypot για κυκλική εναλλαγή
FAMOUS_SSH_PORTS = [
    22,    # Τυπική SSH
    2222,  # Κοινή εναλλακτική SSH
    80,    # HTTP (συχνά σαρώνεται από bots που ψάχνουν για ανοιχτές θύρες)
    443,   # HTTPS (συχνά σαρώνεται από bots που ψάχνουν για ανοιχτές θύρες)
    21,    # FTP (συχνά brute-force)
    23     # Telnet (συχνά brute-force)
]

# Διαμόρφωση (Οι διαδρομές θα οριστούν από την κλάση AdvancedNetworkTools)
HOST = '0.0.0.0'
# BASE_DIR, LOG_DIR, STATS_FILE ορίζονται δυναμικά στο run_ssh_defender
EMPTY_CHECK_INTERVAL = 60  # 1 λεπτό

# Κοινά banners SSH για προσομοίωση πραγματικών διακομιστών
SSH_BANNERS = [
    b"SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.3\r\n",
    b"SSH-2.0-OpenSSH_7.4p1 Debian-10+deb9u7\r\n", 
    b"SSH-2.0-OpenSSH_7.9p1 FreeBSD-20200824\r\n",
    b"SSH-2.0-libssh-0.9.3\r\n"
]

# Όρια επίθεσης
MAX_ATTEMPTS = 5         # Μέγιστες απόπειρες πριν την καταγραφή πλήρους log/απαγόρευση IP
ATTACK_THRESHOLD = 50    # Αριθμός απόπειρων σε 5 λεπτά για ενεργοποίηση προειδοποίησης/διακοπή κύκλου


# ==============================================================================
# SSH DEFENDER - Κλάση Καταγραφής
# ==============================================================================

class Logger:
    def __init__(self, log_dir, stats_file):
        self.log_dir = log_dir
        self.stats_file = stats_file
        os.makedirs(self.log_dir, exist_ok=True)
        self.lock = threading.Lock()
        self.attack_stats = self.load_stats()
        self.current_session_attempts = {} # {ip: count}
        self.session_start_time = time.time()

    def load_stats(self):
        """Φόρτωση σωρευτικών στατιστικών από αρχείο JSON."""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"total_attacks": 0, "ip_stats": {}, "port_stats": {}}

    def save_stats(self):
        """Αποθήκευση σωρευτικών στατιστικών σε αρχείο JSON."""
        with self.lock:
            try:
                with open(self.stats_file, 'w') as f:
                    json.dump(self.attack_stats, f, indent=4)
            except IOError as e:
                print(f"Σφάλμα αποθήκευσης αρχείου στατιστικών: {e}")

    def log_attempt(self, ip, port, message, is_full_log=False):
        """Καταγραφή μίας απόπειρας σύνδεσης και ενημέρωση στατιστικών."""
        timestamp = datetime.now().isoformat()
        
        with self.lock:
            # 1. Ενημέρωση απόπειρων συνεδρίας
            self.current_session_attempts[ip] = self.current_session_attempts.get(ip, 0) + 1
            
            # 2. Ενημέρωση σωρευτικών στατιστικών
            self.attack_stats['total_attacks'] = self.attack_stats.get('total_attacks', 0) + 1
            
            # Στατιστικά IP
            ip_data = self.attack_stats['ip_stats'].setdefault(ip, {"count": 0, "last_attempt": None, "first_attempt": timestamp})
            ip_data['count'] += 1
            ip_data['last_attempt'] = timestamp
            
            # Στατιστικά θύρας
            port_key = str(port)
            self.attack_stats['port_stats'].setdefault(port_key, 0)
            self.attack_stats['port_stats'][port_key] += 1
            
            # 3. Εγγραφή αρχείου log αν ζητηθεί πλήρες log ή φτάσει το όριο
            if is_full_log:
                log_filename = os.path.join(self.log_dir, f"{ip}.log")
                try:
                    with open(log_filename, 'a') as f:
                        f.write(f"[{timestamp}] ΘΥΡΑ:{port} - {message}\n")
                except IOError as e:
                    print(f"Σφάλμα εγγραφής αρχείου log: {e}")
                    
            # 4. Περιοδική αποθήκευση σωρευτικών στατιστικών
            if self.attack_stats['total_attacks'] % 10 == 0:
                self.save_stats()
                
    def get_session_total_attempts(self):
        """Επιστρέφει τον συνολικό αριθμό απόπειρων στην τρέχουσα συνεδρία."""
        return sum(self.current_session_attempts.values())

    def get_current_attempts(self):
        """Επιστρέφει τον αριθμό απόπειρων και τον χρόνο που έχει περάσει από την έναρξη της συνεδρίας."""
        attempts = self.get_session_total_attempts()
        time_elapsed = time.time() - self.session_start_time
        return attempts, time_elapsed
        
    def reset_session_stats(self):
        """Επαναφορά στατιστικών συνεδρίας (χρησιμοποιείται κατά την κυκλική εναλλαγή θυρών)."""
        with self.lock:
            self.current_session_attempts = {}
            self.session_start_time = time.time()
            
    def get_cumulative_stats_summary(self):
        """Επιστρέφει μια μορφοποιημένη σύνοψη σωρευτικών στατιστικών."""
        total = self.attack_stats.get('total_attacks', 0)
        
        # Κορυφαίες 3 IP
        ip_list = sorted(self.attack_stats['ip_stats'].items(), key=lambda item: item[1]['count'], reverse=True)
        top_ips = [f"{ip} ({data['count']} απόπειρες)" for ip, data in ip_list[:3]]
        
        # Κορυφαίες 3 Θύρες
        port_list = sorted(self.attack_stats['port_stats'].items(), key=lambda item: item[1], reverse=True)
        top_ports = [f"{port} ({count} επιθέσεις)" for port, count in port_list[:3]]
        
        return {
            "Συνολικές Επιθέσεις": total,
            "Κορυφαίες IP Επιτιθέμενων": top_ips if top_ips else ["Δ/Υ"],
            "Κορυφαίες Θύρες Στόχοι": top_ports if top_ports else ["Δ/Υ"]
        }

# ==============================================================================
# SSH DEFENDER - Κλάση Βασικής Λογικής
# ==============================================================================

class SSHDefender:
    
    def __init__(self, host, logger, executor):
        self.host = host
        self.logger = logger
        self.running = False
        self.listener_thread = None
        self.listener_socket = None
        self.cycle_mode = False
        self.executor = executor
        self.current_port = None
        
        # Ο βασικός κατάλογος χειρίζεται από τον logger

    def _handle_connection(self, client_socket, addr):
        """Χειρίζεται την αλληλεπίδραση με έναν συνδεόμενο πελάτη (η λογική του honeypot)."""
        ip, port = addr
        
        # Επιλογή τυχαίου banner για προσομοίωση πραγματικού διακομιστή SSH
        banner = random.choice(SSH_BANNERS)
        
        try:
            # 1. Αποστολή του banner SSH αμέσως
            client_socket.sendall(banner)
            
            # 2. Έναρξη διαδραστικής συνεδρίας (αναμονή για εισαγωγή)
            attempt_count = 0
            
            while self.running:
                # Χρήση select για μη αποκλειστική ανάγνωση με χρονικό όριο
                ready_to_read, _, _ = select.select([client_socket], [], [], 3.0)
                
                if ready_to_read:
                    data = client_socket.recv(1024)
                    if not data:
                        break # Αποσύνδεση από τον πελάτη
                        
                    data_str = data.decode('utf-8', errors='ignore').strip()
                    self.logger.log_attempt(ip, self.current_port, f"Δεδομένα Λήφθηκαν: '{data_str}'")
                    
                    attempt_count += 1
                    
                    # Καταγραφή πλήρους συνεδρίας αν φτάσει ο μέγιστος αριθμός απόπειρων για αυτή τη σύνδεση
                    is_full_log = (attempt_count >= MAX_ATTEMPTS)
                    
                    # Ενημέρωση καταγραφέα με λεπτομέρειες απόπειρας
                    self.logger.log_attempt(ip, self.current_port, f"Απόπειρα {attempt_count}: {data_str}", is_full_log=is_full_log)
                    
                    # Απάντηση με KEXINIT SSH ή παρόμοια απόκριση για προσομοίωση πραγματικού διακομιστή
                    # Απλή απόκριση για να κρατήσει ανοιχτή τη σύνδεση για περισσότερες απόπειρες brute-force
                    if data_str.startswith("SSH"):
                         # Προσομοίωση απόκρισης KEXINIT (τυχαίο cookie 16-byte, κλπ.)
                        kex_response = b'SSH-2.0-SSH Defender\r\n' 
                        client_socket.sendall(kex_response)
                        
                    elif data_str.lower().startswith(("user", "root", "admin", "login")):
                        # Απλή απόκριση για προτροπή εισαγωγής κωδικού
                        client_socket.sendall(b"Κωδικός:\r\n") 
                        
                    elif data_str.startswith("password"):
                        # Απλή απόκριση σφάλματος
                         client_socket.sendall(b"Απαγορευμένη πρόσβαση, δοκιμάστε ξανά.\r\n")

                    # Αν αυτή η σύνδεση δέχεται έντονο brute-force, κλείστε τη
                    if attempt_count >= MAX_ATTEMPTS * 2:
                        break

                else:
                    # Χρονικό όριο, κλείσιμο σύνδεσης
                    break 

        except socket.timeout:
            self.logger.log_attempt(ip, self.current_port, "Η σύνδεση έληξε.")
        except ConnectionResetError:
            self.logger.log_attempt(ip, self.current_port, "Η σύνδεση επαναφέρθηκε από τον συνδεόμενο.")
        except Exception as e:
            self.logger.log_attempt(ip, self.current_port, f"Μη αναμενόμενο σφάλμα σύνδεσης: {e}")
        finally:
            client_socket.close()

    def start_port_listener(self, port):
        """Εκκίνηση του κύριου ακροατή socket σε συγκεκριμένη θύρα."""
        if self.listener_thread or self.listener_socket:
            self.stop_all_ports()
        
        self.current_port = port
        
        try:
            self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listener_socket.bind((self.host, port))
            self.listener_socket.listen(5)
            print(f"{Fore.GREEN}✅ SSH Defender ακούει στο {self.host}:{port}...{Style.RESET_ALL}")
            self.running = True
            self.logger.reset_session_stats()
            
            self.listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
            self.listener_thread.start()
            
        except OSError as e:
            print(f"{Fore.RED}❌ Σφάλμα σύνδεσης στη θύρα {port}: {e}. (Ίσως εκτελείται άλλη διεργασία ή δεν έχετε δικαιώματα;){Style.RESET_ALL}")
            self.running = False
            self.listener_socket = None
            self.current_port = None
            
        except Exception as e:
            print(f"{Fore.RED}❌ Μη αναμενόμενο σφάλμα εκκίνησης ακροατή στη θύρα {port}: {e}{Style.RESET_ALL}")
            self.running = False
            self.listener_socket = None
            self.current_port = None

    def _listener_loop(self):
        """Ο κύριος βρόχος για αποδοχή συνδέσεων."""
        while self.running:
            try:
                # Χρήση select για αναμονή συνδέσεων με χρονικό όριο
                ready_to_read, _, _ = select.select([self.listener_socket], [], [], 1.0)
                
                if ready_to_read and self.listener_socket in ready_to_read:
                    client_socket, addr = self.listener_socket.accept()
                    # Υποβολή του χειριστή σύνδεσης στην ομάδα νημάτων
                    self.executor.submit(self._handle_connection, client_socket, addr)
                
            except socket.timeout:
                pass # Αναμενόμενο χρονικό όριο
            except Exception as e:
                if self.running:
                    print(f"\n{Fore.RED}❌ Σφάλμα βρόχου ακροατή στη θύρα {self.current_port}: {e}{Style.RESET_ALL}")
                    # Προσπάθεια καθαρού τερματισμού αν το socket απέτυχε
                    self.stop_all_ports()
                    break
        
    def stop_all_ports(self):
        """Τερματισμός του ακροατή socket και νήματος."""
        self.running = False
        if self.listener_socket:
            try:
                # Ξεκλείδωμα της κλήσης accept
                self.listener_socket.shutdown(socket.SHUT_RDWR)
                self.listener_socket.close()
                self.listener_socket = None
                if self.listener_thread and self.listener_thread.is_alive():
                    self.listener_thread.join(timeout=2)
            except Exception:
                pass # Αγνόηση σφαλμάτων κατά το κλείσιμο
        self.current_port = None
        self.executor.shutdown(wait=False, cancel_futures=True)
        # Επανδημιουργία executor για εκκαθάριση παλιών νημάτων, αν απαιτείται για επανεκκίνηση TUI
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=50)


    def run_port_cycle(self):
        """Εκτέλεση κυκλικής εναλλαγής μέσω λίστας γνωστών θυρών."""
        self.cycle_mode = True
        
        for port_index, port in enumerate(FAMOUS_SSH_PORTS):
            
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}  ΕΝΑΡΞΗ ΠΑΡΑΚΟΛΟΥΘΗΣΗΣ ΣΤΗ ΘΥΡΑ: {port}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            self.start_port_listener(port)
            if not self.running:
                # Δεν μπόρεσε να δεσμευτεί, μετάβαση στην επόμενη θύρα
                continue 
            
            start_time = time.time()
            
            # Βρόχος παρακολούθησης για 5 λεπτά (ή μέχρι να φτάσει το όριο επίθεσης)
            while time.time() - start_time < 5 * 60:
                time.sleep(EMPTY_CHECK_INTERVAL) # Έλεγχος κάθε λεπτό
                
                attempts, time_elapsed = self.logger.get_current_attempts()
                
                if attempts > ATTACK_THRESHOLD:
                    print(f"\n\n{Fore.RED}🚨 ΕΝΤΟΠΙΣΤΗΚΕ ΚΡΙΣΙΜΗ ΕΠΙΘΕΣΗ στη θύρα {port}!{Style.RESET_ALL}")
                    print(f"   {attempts} απόπειρες σε {int(time_elapsed)} δευτερόλεπτα.")
                    print(f"{Fore.YELLOW}   Εναλλαγή σε λειτουργία μόνιμης παρακολούθησης για αυτή τη θύρα.{Style.RESET_ALL}")
                    
                    self.stop_all_ports()
                    self.cycle_mode = False
                    
                    # Επανεκκίνηση του ακροατή και TUI για μόνιμη παρακολούθηση
                    self.start_port_listener(port)
                    self.tui.run() # Αυτή η κλήση θα μπλοκάρει μέχρι ο χρήστης να κλείσει το TUI
                    self.running = False
                    break # Έξοδος από τον βρόχο κυκλικής εναλλαγής
                
                # Ενημέρωση TUI (αν εκτελείται) με την κατάσταση
                if hasattr(self, 'tui') and self.tui.running:
                    self.tui.update_display()
                
            if not self.cycle_mode: # Αν βγήκαμε λόγω κρίσιμης επίθεσης
                break

            if port_index == len(FAMOUS_SSH_PORTS) - 1:
                print(f"\n\n{Fore.GREEN}✅ Ολοκληρώθηκε η παρακολούθηση όλων των γνωστών θυρών χωρίς σημαντικές επιθέσεις. Ο Defender τερματίζει.{Style.RESET_ALL}")
                self.running = False
                break # Έξοδος από τον βρόχο κυκλικής εναλλαγής
                
            # Χωρίς επίθεση: Ερώτηση χρήστη για εναλλαγή
            next_port = FAMOUS_SSH_PORTS[port_index + 1]
            user_input = input(f"\n\n{Fore.YELLOW}⏰ Πέρασαν 5 λεπτά στη θύρα {port} χωρίς επιθέσεις.\nΘέλετε να μεταβείτε στην επόμενη γνωστή θύρα ({next_port}); (ν/ο): {Style.RESET_ALL}")
            
            self.stop_all_ports()
            
            if user_input.lower() not in ['ν', 'y']:
                print(f"\n{Fore.RED}🛑 Ο χρήστης επέλεξε να σταματήσει την κυκλική εναλλαγή. Ο Defender τερματίζει.{Style.RESET_ALL}")
                self.running = False
                break
            
        # Τελικός καθαρισμός
        self.running = False
        self.stop_all_ports()
        self.logger.save_stats()
        print(f"\n{Fore.GREEN}✅ SSH Defender τερματίστηκε.{Style.RESET_ALL}")


# ==============================================================================
# SSH DEFENDER - Διεπαφή Χρήστη Τερματικού (TUI)
# ==============================================================================

class DefenderTUI:
    
    def __init__(self, stdscr, defender):
        self.stdscr = stdscr
        self.defender = defender
        self.running = True
        self._init_curses()

    def _init_curses(self):
        """Προετοιμασία ρυθμίσεων curses και χρωμάτων."""
        curses.cbreak()
        curses.noecho()
        self.stdscr.keypad(True)
        try:
            curses.curs_set(0) # Απόκρυψη δρομέα
        except curses.error:
            pass
            
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK) # Προεπιλογή
            curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Τίτλος
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Προειδοποίηση/Στατιστικά
            curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)   # Επίθεση/Κρίσιμο
            curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK) # Επιτυχία

    def update_display(self):
        """Εκκαθάριση και επανασχεδιασμός της οθόνης TUI."""
        try:
            self.stdscr.clear()
            h, w = self.stdscr.getmaxyx()
            if h < 20 or w < 50:
                self.stdscr.addstr(0, 0, "Το τερματικό είναι πολύ μικρό...")
                self.stdscr.refresh()
                return
        except curses.error:
            return # Παράβλεψη απόδοσης αν το τερματικό αλλάζει μέγεθος

        try:
            # 1. Μπάρα Τίτλου
            title = " SSH Defender - Honeypot Monitor "
            self.stdscr.attron(curses.A_BOLD | curses.color_pair(2))
            self.stdscr.addstr(0, w//2 - len(title)//2, title)
            self.stdscr.addstr(0, w - 18, f"Θύρα: {self.defender.current_port or 'Δ/Υ'}".ljust(17))
            self.stdscr.attroff(curses.A_BOLD | curses.color_pair(2))
            
            # 2. Στατιστικά Συνεδρίας
            attempts, time_elapsed = self.defender.logger.get_current_attempts()
            status_color = curses.color_pair(5) if attempts < ATTACK_THRESHOLD * 0.2 else curses.color_pair(3)
            if attempts > ATTACK_THRESHOLD * 0.5:
                status_color = curses.color_pair(4)

            session_title = " Στατιστικά Συνεδρίας "
            self.stdscr.attron(curses.A_BOLD | status_color)
            self.stdscr.addstr(2, w//2 - len(session_title)//2, session_title)
            self.stdscr.attroff(curses.A_BOLD | status_color)
            
            self.stdscr.addstr(3, 2, f"Συνολικές Απόπειρες: {attempts}")
            self.stdscr.addstr(4, 2, f"Χρόνος που πέρασε: {self._format_time(time_elapsed)}")
            self.stdscr.addstr(5, 2, f"Όριο Επίθεσης: {ATTACK_THRESHOLD} απόπειρες / 5 λεπτά")
            
            # Μπάρα Προόδου (Απλοποιημένη)
            bar_len = w - 4
            progress_ratio = min(1.0, attempts / ATTACK_THRESHOLD)
            fill_len = int(bar_len * progress_ratio)
            
            self.stdscr.addstr(6, 2, "Επίπεδο Επίθεσης: ")
            self.stdscr.attron(status_color | curses.A_REVERSE)
            self.stdscr.addstr(6, 16, " " * fill_len)
            self.stdscr.attroff(status_color | curses.A_REVERSE)
            self.stdscr.addstr(6, 16 + fill_len, " " * (bar_len - fill_len - 15))

            # 3. Σωρευτικά Στατιστικά
            cumulative_stats = self.defender.logger.get_cumulative_stats_summary()
            stats_title = " Σωρευτικά Στατιστικά "
            self.stdscr.attron(curses.A_BOLD | curses.color_pair(3))
            self.stdscr.addstr(8, w//2 - len(stats_title)//2, stats_title)
            self.stdscr.attroff(curses.A_BOLD | curses.color_pair(3))
            
            self.stdscr.addstr(9, 2, f"Συνολικές Επιθέσεις που Καταγράφηκαν: {cumulative_stats['Συνολικές Επιθέσεις']}")
            
            y_start = 10
            self.stdscr.addstr(y_start, 2, "Κορυφαίες IP:")
            for i, ip_stat in enumerate(cumulative_stats['Κορυφαίες IP Επιτιθέμενων']):
                if y_start + i < h - 2:
                    self.stdscr.addstr(y_start + i, 12, ip_stat)
                
            y_start += 4
            self.stdscr.addstr(y_start, 2, "Κορυφαίες Θύρες:")
            for i, port_stat in enumerate(cumulative_stats['Κορυφαίες Θύρες Στόχοι']):
                if y_start + i < h - 2:
                    self.stdscr.addstr(y_start + i, 12, port_stat)

            # 4. Μπάρα Κατάστασης/Συντομεύσεων
            status_text = "q: Έξοδος | s: Αποθήκευση Στατιστικών"
            self.stdscr.attron(curses.A_REVERSE)
            self.stdscr.addstr(h-1, 0, status_text.ljust(w))
            self.stdscr.attroff(curses.A_REVERSE)
            
            self.stdscr.refresh()
        except curses.error:
            pass # Αγνόηση σφαλμάτων (π.χ., εγγραφή εκτός οθόνης κατά την αλλαγή μεγέθους)

    def _format_time(self, seconds):
        """Μορφοποίηση δευτερολέπτων σε συμβολοσειρά Ω:Λ:Δ."""
        s = int(seconds)
        h = s // 3600
        s %= 3600
        m = s // 60
        s %= 60
        return f"{h:02}:{m:02}:{s:02}"
        
    def run(self):
        """Ο βρόχος αλληλεπίδρασης TUI."""
        self.running = True
        self.stdscr.nodelay(True) # Μη αποκλειστική εισαγωγή
        
        while self.running and self.defender.running:
            try:
                self.update_display()
                key = self.stdscr.getch()
                
                if key == ord('q') or key == ord('Q') or key == 27:
                    self.running = False
                    self.defender.running = False # Σήμα τερματισμού για defender
                    break
                elif key == ord('s') or key == ord('S'):
                    self.defender.logger.save_stats()
                    self._display_message("Τα στατιστικά αποθηκεύτηκαν επιτυχώς.")
                
                time.sleep(0.5) # Ρυθμός ανανέωσης
            except KeyboardInterrupt:
                self.running = False
                self.defender.running = False
            except curses.error:
                pass # Αγνόηση σφαλμάτων TUI
            
        self.stdscr.nodelay(False)

    def _display_message(self, message):
        """Εμφάνιση μηνύματος και αναμονή για πάτημα πλήκτρου."""
        curses.curs_set(0)
        self.stdscr.nodelay(False)
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        
        lines = message.split('\n')
        
        # Κέντρο και εμφάνιση γραμμών
        for i, line in enumerate(lines):
            y = h//2 - len(lines)//2 + i
            x = w//2 - len(line)//2
            if 0 <= y < h:
                try:
                    self.stdscr.addstr(y, x, line)
                except curses.error:
                    pass
                    
        # Μήνυμα αναμονής για πάτημα πλήκτρου
        wait_msg = "Πατήστε οποιοδήποτε πλήκτρο για συνέχεια..."
        self.stdscr.attron(curses.A_REVERSE)
        self.stdscr.addstr(h-1, 0, wait_msg.ljust(w))
        self.stdscr.attroff(curses.A_REVERSE)
        
        self.stdscr.refresh()
        try:
            self.stdscr.getch()
        except KeyboardInterrupt:
            pass
        self.stdscr.nodelay(True)

# ==============================================================================
# ΤΕΛΟΣ ΚΩΔΙΚΑ SSH DEFENDER
# ==============================================================================


def auto_install_dependencies():
    """
    Αυτόματη εγκατάσταση όλων των απαιτούμενων εξαρτήσεων χωρίς root.
    Βελτιστοποιημένη για εγκατάσταση μόνο των απαραίτητων.
    """
    print(f"{Fore.CYAN}🛠️ ΠΡΟΧΩΡΗΜΕΝΑ ΔΙΚΤΥΑΚΑ ΕΡΓΑΛΕΙΑ - Αυτόματη Εγκατάσταση Εξαρτήσεων{Style.RESET_ALL}")
    print("="*70)
    print(f"{Fore.YELLOW}Αυτό θα εγκαταστήσει όλα τα απαιτούμενα πακέτα χωρίς δικαιώματα root.{Style.RESET_ALL}")
    
    is_termux = os.path.exists('/data/data/com.termux')
    
    # Πακέτα συστήματος για Termux (χωρίς root)
    # Το nmap περιλαμβάνεται για το εργαλείο Nmap Wrapper
    termux_packages = [
        'python', 'python-pip', 'curl', 'wget', 'nmap', 
        'inetutils', 'openssl-tool', 'ncurses-utils'
    ]
    
    # Πακέτα Python (pip) - Καθαρισμένη λίστα *μόνο* από χρησιμοποιούμενες εξαρτήσεις
    pip_packages = [
        'requests', 'colorama', 'speedtest-cli', 'beautifulsoup4',
        'paramiko', 'python-whois', 'dnspython'
    ]
    
    # Εγκατάσταση πακέτων Termux
    if is_termux and termux_packages:
        print(f"\n{Fore.CYAN}[*] Εγκατάσταση/ενημέρωση πακέτων Termux...{Style.RESET_ALL}")
        try:
            subprocess.run(
                ['pkg', 'install', '-y'] + termux_packages,
                capture_output=True, text=True, timeout=300
            )
            print(f"    {Fore.GREEN}✅ Τα πακέτα Termux ελέγχθηκαν.{Style.RESET_ALL}")
        except Exception as e:
            print(f"    {Fore.YELLOW}⚠️ Δεν ήταν δυνατή η εγκατάσταση όλων των πακέτων Termux: {e}{Style.RESET_ALL}")
    
    # Εγκατάσταση πακέτων Python
    print(f"\n{Fore.CYAN}[*] Εγκατάσταση πακέτων Python (pip)...{Style.RESET_ALL}")
    for package in pip_packages:
        module_name_map = {
            'beautifulsoup4': 'bs4',
            'dnspython': 'dns.resolver',
            'speedtest-cli': 'speedtest',
            'python-whois': 'whois'
        }
        module_name = module_name_map.get(package, package.replace('-', '_'))

        try:
            # Χειρισμός εμφωλευμένων ονομάτων modules όπως dns.resolver
            base_module = module_name.split('.')[0]
            importlib.import_module(base_module)
            print(f"    {Fore.GREEN}✅ {package} είναι ήδη εγκατεστημένο{Style.RESET_ALL}")
        except ImportError:
            print(f"    [*] Εγκατάσταση {package}...")
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', package],
                    capture_output=True, text=True, timeout=180
                )
                if result.returncode == 0:
                    print(f"    {Fore.GREEN}✅ {package} εγκαταστάθηκε επιτυχώς{Style.RESET_ALL}")
                else:
                    print(f"    {Fore.YELLOW}⚠️ Δεν ήταν δυνατή η εγκατάσταση {package}. Σφάλμα: {result.stderr.splitlines()[-1]}{Style.RESET_ALL}")
            except Exception as e:
                print(f"    {Fore.RED}❌ Αποτυχία εγκατάστασης {package}: {e}{Style.RESET_ALL}")
    
    # Τελικός έλεγχος εξαρτήσεων
    print(f"\n{Fore.CYAN}[*] Τελικός έλεγχος εξαρτήσεων...{Style.RESET_ALL}")
    global CURSES_AVAILABLE
    try:
        import curses
        CURSES_AVAILABLE = True
        print(f"    {Fore.GREEN}✅ curses (TUI){Style.RESET_ALL}")
    except ImportError:
        print(f"    {Fore.RED}❌ curses (TUI) - Το TUI ΘΑ ΑΠΟΤΥΧΕΙ!{Style.RESET_ALL}")
        print(f"    {Fore.YELLOW}Στο Termux, εκτελέστε: pkg install ncurses-utils{Style.RESET_ALL}")
    
    if not CURSES_AVAILABLE:
        print(f"\n{Fore.RED}ΚΡΙΣΙΜΟ: Το module 'curses' δεν βρέθηκε. Το TUI δεν μπορεί να εκτελεστεί.{Style.RESET_ALL}")
        return False
    
    print(f"\n{Fore.GREEN}🎉 Η εγκατάσταση ολοκληρώθηκε! Εκκίνηση εφαρμογής...{Style.RESET_ALL}")
    time.sleep(2)
    return True

# --- Βοηθητικές Συναρτήσεις Curses ---
def _reset_curses_state(stdscr):
    """Προετοιμασία και επαναφορά απαιτούμενων ρυθμίσεων τερματικού για TUI."""
    if not CURSES_AVAILABLE: return
    curses.cbreak()
    curses.noecho()
    stdscr.keypad(True)
    try:
        curses.curs_set(0) # Απόκρυψη δρομέα
    except curses.error:
        pass # Αγνόηση αν δεν υποστηρίζεται
    
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK) # Προεπιλογή
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Τίτλος
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Επισήμανση κειμένου
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN)  # Επισήμανση φόντου

def _draw_curses_menu(stdscr, title, options):
    """Γενικός χειριστής μενού curses για πλοήγηση και επιλογή."""
    current_row_idx = 0
    
    def print_menu(screen, selected_idx):
        screen.clear()
        h, w = screen.getmaxyx()
        
        title_text = f" {title} "
        x_title = max(0, w//2 - len(title_text)//2)
        
        if 1 < h:
            screen.attron(curses.A_BOLD | curses.color_pair(2))
            screen.addstr(1, x_title, title_text)
            screen.attroff(curses.A_BOLD | curses.color_pair(2))
            
        if 2 < h:
            screen.addstr(2, max(0, w//2 - 25), "=" * 50)

        for idx, option in enumerate(options):
            y = 4 + idx
            if y >= h - 1: break # Σταμάτημα αν το μενού ξεπεράσει την οθόνη
            
            display_option = option.ljust(40)
            x = max(0, w//2 - len(display_option)//2)
            
            # Προσθήκη διαχωριστικών
            if option.startswith("---"):
                screen.attron(curses.color_pair(3))
                screen.addstr(y, max(0, w//2 - 20), option)
                screen.attroff(curses.color_pair(3))
                continue
            
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
        try:
            print_menu(stdscr, current_row_idx)
            key = stdscr.getch()

            if key == curses.KEY_UP:
                current_row_idx = (current_row_idx - 1) % len(options)
                # Παράβλεψη διαχωριστικών
                while options[current_row_idx].startswith("---"):
                    current_row_idx = (current_row_idx - 1) % len(options)
            elif key == curses.KEY_DOWN:
                current_row_idx = (current_row_idx + 1) % len(options)
                # Παράβλεψη διαχωριστικών
                while options[current_row_idx].startswith("---"):
                    current_row_idx = (current_row_idx + 1) % len(options)
            elif key == curses.KEY_ENTER or key in [10, 13]:
                return current_row_idx
            elif key == curses.KEY_RESIZE:
                # Χειρισμός αλλαγής μεγέθους τερματικού
                pass
        except curses.error:
             # Χειρισμός σφαλμάτων αλλαγής μεγέθους τερματικού
            time.sleep(0.1)


def main_app_loop():
    """Κύριο σημείο εισόδου εφαρμογής"""
    
    class AdvancedNetworkTools:
        def __init__(self):
            # Ορισμός και δημιουργία αποθετηρίου αποθήκευσης
            is_termux = os.path.exists('/data/data/com.termux')
            if is_termux:
                base_dir = os.path.expanduser('~')
                self.save_dir = os.path.join(base_dir, "DedSec's Network")
            else:
                self.save_dir = os.path.join(os.getcwd(), "DedSec's Network")

            if not os.path.exists(self.save_dir):
                print(f"{Fore.CYAN}[*] Δημιουργία αποθετηρίου αποθήκευσης στο: {self.save_dir}{Style.RESET_ALL}")
                os.makedirs(self.save_dir)
            
            self.wifi_db_name = os.path.join(self.save_dir, "wifi_scans.db")
            self.config_file = os.path.join(self.save_dir, "network_tools_config.json")
            self.known_networks_file = os.path.join(self.save_dir, "known_networks.json")
            self.audit_db_name = os.path.join(self.save_dir, "audit_results.db")
            self.wordlist_dir = os.path.join(self.save_dir, "wordlists")

            if not os.path.exists(self.wordlist_dir):
                os.makedirs(self.wordlist_dir)

            self.init_wifi_database()
            self.init_audit_database()
            self.load_config()
            self.load_known_networks()
            
            self.trusted_bssids = set(self.known_networks.get("trusted_bssids", []))
            self.current_networks = {}
            
            # Για αποδοτική σάρωση
            self.max_workers = self.config.get('max_scan_workers', 15)
            self.scan_timeout = self.config.get('scan_timeout', 1)
            
            print(f"{Fore.GREEN}✅ Τα Προηγμένα Δικτυακά Εργαλεία προετοιμάστηκαν επιτυχώς{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📂 Όλα τα αρχεία θα αποθηκευτούν στο: {self.save_dir}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}⚡️ Νήματα σάρωσης ορίστηκαν σε: {self.max_workers}{Style.RESET_ALL}")
            
        # --- Διαχείριση Διαμόρφωσης & Βάσης Δεδομένων ---
        def load_config(self):
            default_config = {
                "scan_interval": 60, "alert_on_new_network": True,
                "dns_test_server": "https://ipleak.net/json/",
                "port_scan_threads": 20, # Διατηρήθηκε για συμβατότητα, αλλά χρησιμοποιούμε max_scan_workers
                "max_scan_workers": 15,  # Όριο αποδοτικής ομάδας νημάτων
                "scan_timeout": 1,       # Χρονικό όριο socket σε δευτερόλεπτα
                "top_ports": "21,22,23,25,53,80,110,143,443,445,993,995,1723,3306,3389,5900,8080",
                "common_usernames": "admin,root,user,administrator,test,guest",
                "common_passwords": "admin,123456,password,1234,12345,123456789,letmein,1234567,123,abc123"
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
                print(f"{Fore.RED}❌ Σφάλμα ΒΔ: Αποτυχία καταγραφής ευρήματος ελέγχου: {e}{Style.RESET_ALL}")

        # --- Εργαλεία Wi-Fi, Τοπικού Δικτύου και Κινητής Τηλεφωνίας (Χωρίς Root) ---
        def _run_termux_command(self, command, timeout=15):
            """Βοηθητική για εκτέλεση εντολών Termux API."""
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=True)
                return result.stdout
            except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass
            return None

        def frequency_to_channel(self, freq):
            if 2412 <= freq <= 2472: return (freq - 2412) // 5 + 1
            if 5170 <= freq <= 5825: return (freq - 5170) // 5 + 34
            return 0

        def get_signal_quality(self, signal_dBm):
            if not isinstance(signal_dBm, int): return f"{Fore.WHITE}Δ/Υ{Style.RESET_ALL}"
            if signal_dBm >= -50: return f"{Fore.GREEN}Εξαιρετικό{Style.RESET_ALL}"
            if signal_dBm >= -65: return f"{Fore.YELLOW}Καλό{Style.RESET_ALL}"
            if signal_dBm >= -75: return f"{Fore.MAGENTA}Μέτριο{Style.RESET_ALL}"
            return f"{Fore.RED}Αδύναμο{Style.RESET_ALL}"
        
        def scan_via_termux_api(self):
            networks = []
            output = self._run_termux_command(['termux-wifi-scaninfo'])
            if output and output.strip().startswith('['):
                try:
                    scan_data = json.loads(output)
                    for network in scan_data:
                        networks.append({
                            'bssid': network.get('bssid', 'Άγνωστο').upper(), 'ssid': network.get('ssid', 'Κρυφό'),
                            'signal': network.get('rssi', 0), 'channel': self.frequency_to_channel(network.get('frequency', 0)),
                            'encryption': network.get('security', 'Άγνωστο')
                        })
                except json.JSONDecodeError:
                    pass # Αγνόηση κατεστραμμένης εξόδου JSON
            return networks

        def get_current_connection_info(self):
            output = self._run_termux_command(['termux-wifi-connectioninfo'])
            if output and output.strip().startswith('{'):
                try:
                    conn_info = json.loads(output)
                    return {
                        'bssid': conn_info.get('bssid', 'Δ/Υ').upper(), 'ssid': conn_info.get('ssid', 'Μη Συνδεδεμένο'),
                        'signal': conn_info.get('rssi', 0), 'channel': self.frequency_to_channel(conn_info.get('frequency', 0)),
                        'encryption': conn_info.get('security', 'Δ/Υ'), 'is_current': True
                    }
                except json.JSONDecodeError:
                    pass
            return None

        def passive_network_scan(self):
            print(f"{Fore.YELLOW}[*] Έναρξη παθητικής σάρωσης Wi-Fi... (Απαιτεί Termux:API){Style.RESET_ALL}")
            networks_found = {}
            for net in self.scan_via_termux_api(): 
                networks_found[net['bssid']] = net
            
            current_network = self.get_current_connection_info()
            if current_network and current_network['bssid'] != 'Δ/Υ':
                networks_found[current_network['bssid']] = current_network
            
            if not networks_found:
                print(f"{Fore.RED}❌ Δεν βρέθηκαν δίκτυα. Βεβαιωθείτε ότι το Wi-Fi είναι ενεργοποιημένο και το Termux:API είναι εγκατεστημένο και ρυθμισμένο.{Style.RESET_ALL}")

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
                    threats.append({'bssid': network['bssid'], 'ssid': network['ssid'], 'reason': 'Ύποπτο SSID', 'level': 'ΜΕΣΑΙΟ'})
                if network.get('encryption', 'Άγνωστο').upper() in ['WEP', 'OPEN', '']:
                    threats.append({'bssid': network['bssid'], 'ssid': network['ssid'], 'reason': f'Αδύναμη Κρυπτογράφηση ({network["encryption"] or "Ανοιχτό"})', 'level': 'ΥΨΗΛΟ'})
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
                bssid, ssid, signal, enc = net['bssid'], net['ssid'], net['signal'], net.get('encryption', 'Δ/Υ')
                
                if net.get('is_current'):
                    color, status = Fore.GREEN, "ΣΥΝΔΕΔΕΜΕΝΟ"
                elif bssid in threat_bssids:
                    color, status = Fore.RED, "ΕΝΕΡΓΗ ΑΠΕΙΛΗ"
                elif bssid in self.trusted_bssids:
                    color, status = Fore.GREEN, "ΕΜΠΙΣΤΟ"
                else:
                    color, status = Fore.WHITE, "ΠΑΡΑΤΗΡΗΘΕΝ"
                
                if enc.upper() in ['WEP', 'OPEN', '']:
                    enc_status = f"{Fore.RED}{enc or 'Ανοιχτό'} (ΑΝΑΣΦΑΛΕΣ!){Style.RESET_ALL}"
                elif 'WPA3' in enc:
                    enc_status = f"{Fore.GREEN}{enc}{Style.RESET_ALL}"
                else:
                    enc_status = f"{Fore.YELLOW}{enc}{Style.RESET_ALL}"
                    
                print(f"{color}--- ΔΙΚΤΥΟ {i}: {ssid or 'Κρυφό SSID'} {Style.RESET_ALL} (BSSID: {bssid}) ---")
                print(f"  Σήμα: {signal}dBm ({self.get_signal_quality(signal)}) | Κανάλι: {net['channel']}")
                print(f"  Κρυπτογράφηση: {enc_status}")
                print(f"  Κατάσταση: {color}{status}{Style.RESET_ALL}")
                
                for threat in (t for t in threats if t['bssid'] == bssid):
                    t_color = Fore.RED if threat['level'] == 'ΥΨΗΛΟ' else Fore.YELLOW
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
                print(f"  Σήμα:      {current_info['signal']}dBm ({self.get_signal_quality(current_info['signal'])})")
                print(f"  Κρυπτογράφηση:  {current_info['encryption']}")
                print(f"  Εμπιστοσύνη: {trust_status}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def toggle_wifi(self):
            print(f"\n{Fore.CYAN}🔄 ΕΝΕΡΓΟΠΟΙΗΣΗ/ΑΠΕΝΕΡΓΟΠΟΙΗΣΗ WI-FI (Termux:API){Style.RESET_ALL}")
            if not os.path.exists('/data/data/com.termux'):
                print(f"{Fore.RED}❌ Αυτή η λειτουργία απαιτεί την εφαρμογή Termux:API.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                return

            choice = input(f"{Fore.WHITE}Ενεργοποίηση/Απενεργοποίηση Wi-Fi [on/off]; {Style.RESET_ALL}").strip().lower()
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

        def get_mobile_data_info(self):
            print(f"\n{Fore.CYAN}📱 ΠΛΗΡΟΦΟΡΙΕΣ ΚΙΝΗΤΗΣ ΣΥΝΔΕΣΗΣ / SIM (Termux:API){Style.RESET_ALL}")
            print("="*50)
            if not os.path.exists('/data/data/com.termux'):
                print(f"{Fore.RED}❌ Αυτή η λειτουργία απαιτεί την εφαρμογή Termux:API.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                return

            # Πληροφορίες Συσκευής
            device_info_out = self._run_termux_command(['termux-telephony-deviceinfo'])
            if device_info_out:
                try:
                    data = json.loads(device_info_out)
                    print(f"{Fore.CYAN}--- Πληροφορίες Συσκευής & SIM ---{Style.RESET_ALL}")
                    print(f"  Πάροχος Δικτύου:   {data.get('network_operator_name', 'Δ/Υ')}")
                    print(f"  Πάροχος SIM:       {data.get('sim_operator_name', 'Δ/Υ')}")
                    print(f"  Τύπος Τηλεφώνου:         {data.get('phone_type', 'Δ/Υ')}")
                    print(f"  Τύπος Δικτύου:       {data.get('data_network_type', 'Δ/Υ')}")
                    print(f"  Κατάσταση Δεδομένων:         {data.get('data_state', 'Δ/Υ')}")
                except json.JSONDecodeError:
                    print(f"{Fore.YELLOW}[!] Δεν ήταν δυνατή η ανάλυση πληροφοριών συσκευής.{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}[!] Δεν ήταν δυνατή η ανάκτηση πληροφοριών συσκευής/SIM. Χωρίς SIM;{Style.RESET_ALL}")

            # Πληροφορίες Πύργων Κινητής
            cell_info_out = self._run_termux_command(['termux-telephony-cellinfo'])
            if cell_info_out:
                try:
                    data = json.loads(cell_info_out)
                    print(f"\n{Fore.CYAN}--- Κοντινοί Πύργοι Κινητής ---{Style.RESET_ALL}")
                    if not data.get('cells'):
                         print("  Δεν υπάρχουν πληροφορίες πύργων κινητής.")
                    for cell in data.get('cells', []):
                        cell_type = cell.get('type', 'Δ/Υ').upper()
                        strength = cell.get('dbm', 'Δ/Υ')
                        print(f"  - Τύπος: {cell_type} | Σήμα: {strength} dBm ({self.get_signal_quality(strength)})")
                except json.JSONDecodeError:
                    print(f"{Fore.YELLOW}[!] Δεν ήταν δυνατή η ανάλυση πληροφοριών πύργων.{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}[!] Δεν ήταν δυνατή η ανάκτηση πληροφοριών πύργων.{Style.RESET_ALL}")

            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        # --- Βελτιωμένα Εργαλεία Σάρωσης Δικτύου τύπου NMAP (Χωρίς Root) ---
        
        def nmap_wrapper(self):
            """Wrapper για το δυαδικό 'nmap' που εγκαθίσταται μέσω pkg."""
            print(f"\n{Fore.CYAN}⚡ ΣΑΡΩΤΗΣ NMAP{Style.RESET_ALL}")
            
            # Έλεγχος ύπαρξης nmap
            try:
                nmap_check = subprocess.run(['nmap', '--version'], capture_output=True, text=True, timeout=5)
                print(f"{Fore.GREEN}✅ Βρέθηκε Nmap: {nmap_check.stdout.splitlines()[0]}{Style.RESET_ALL}")
            except (FileNotFoundError, Exception):
                print(f"{Fore.RED}❌ Δεν βρέθηκε το δυαδικό Nmap!{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Παρακαλώ εγκαταστήστε το μέσω του εγκαταστάτη εξαρτήσεων ή χειροκίνητα ('pkg install nmap').{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                return

            target = input(f"{Fore.WHITE}Εισάγετε IP ή όνομα υπολογιστή στόχου: {Style.RESET_ALL}").strip()
            if not target:
                return

            print(f"\n{Fore.CYAN}Επιλέξτε Τύπο Σάρωσης:{Style.RESET_ALL}")
            print("1. Σάρωση Ping (Ανακάλυψη Υπολογιστών) [-sn]")
            print("2. Γρήγορη Σάρωση (Κορυφαίες θύρες, OS/Υπηρεσία) [-T4 -A -F]")
            print("3. Εντατική Σάρωση (Όλες οι 1000 θύρες, OS/Υπηρεσία) [-T4 -A]")
            print("4. Προσαρμοσμένες Σημαίες")
            
            scan_choice = input(f"{Fore.WHITE}Επιλέξτε τύπο σάρωσης (1-4): {Style.RESET_ALL}").strip()
            
            nmap_flags = []
            if scan_choice == '1':
                nmap_flags = ['-sn']
            elif scan_choice == '2':
                nmap_flags = ['-T4', '-A', '-F']
            elif scan_choice == '3':
                nmap_flags = ['-T4', '-A']
            elif scan_choice == '4':
                custom = input(f"{Fore.WHITE}Εισάγετε προσαρμοσμένες σημαίες nmap (π.χ., -sV -p 80,443): {Style.RESET_ALL}").strip()
                nmap_flags = custom.split()
            else:
                print(f"{Fore.RED}❌ Μη έγκυρη επιλογή.{Style.RESET_ALL}")
                return

            command = ['nmap'] + nmap_flags + [target]
            print(f"\n{Fore.YELLOW}[*] Εκτέλεση: {' '.join(command)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            try:
                # Εκτέλεση nmap και εκτύπωση εξόδου γραμμή προς γραμμή
                with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1) as proc:
                    for line in proc.stdout:
                        print(line, end='')
                
                print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}✅ Η σάρωση Nmap ολοκληρώθηκε.{Style.RESET_ALL}")
                
                # Δεν μπορούμε να το αναλύσουμε εύκολα, οπότε απλώς καταγράφουμε τη δράση
                self.record_audit_finding(target, 'Σάρωση Nmap', f"Τύπος σάρωσης: {' '.join(nmap_flags)}", "Εκτελέστηκε σάρωση Nmap. Δείτε την έξοδο κονσόλας.", 'Ενημερωτικό')
                
            except Exception as e:
                print(f"{Fore.RED}❌ Η σάρωση Nmap απέτυχε: {e}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def enhanced_port_scanner(self):
            """Βελτιωμένος σαρωτής θυρών με ανίχνευση υπηρεσιών - ΑΠΟΔΟΤΙΚΗ ΟΜΑΔΑ ΝΗΜΑΤΩΝ"""
            print(f"\n{Fore.CYAN}🔍 ΒΕΛΤΙΩΜΕΝΟΣ ΣΑΡΩΤΗΣ ΘΥΡΩΝ (Βασισμένος σε Python){Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Σημείωση: Για περισσότερη δύναμη, χρησιμοποιήστε το εργαλείο Nmap Wrapper.{Style.RESET_ALL}")
            
            target = input(f"{Fore.WHITE}Εισάγετε IP ή όνομα υπολογιστή στόχου: {Style.RESET_ALL}").strip()
            if not target: return

            try:
                target_ip = socket.gethostbyname(target)
                print(f"[*] Ανάλυση {target} σε {target_ip}")
            except socket.gaierror:
                print(f"{Fore.RED}❌ Δεν ήταν δυνατή η ανάλυση του ονόματος υπολογιστή.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                return

            port_choice = input(f"{Fore.WHITE}Εισάγετε θύρες: (1) Κορυφαίες, (2) 1-1024, (3) Προσαρμοσμένες (π.χ., 80,443,1-100): {Style.RESET_ALL}").strip()
            
            ports_to_scan = set()
            if port_choice == '1':
                ports_to_scan = set(int(p) for p in self.config['top_ports'].split(','))
            elif port_choice == '2':
                ports_to_scan = set(range(1, 1025))
            else:
                try:
                    for part in port_choice.split(','):
                        if '-' in part:
                            start, end = map(int, part.split('-'))
                            ports_to_scan.update(range(start, end + 1))
                        else:
                            ports_to_scan.add(int(part))
                except ValueError:
                    print(f"{Fore.RED}❌ Μη έγκυρη μορφή θύρας.{Style.RESET_ALL}")
                    return

            print(f"[*] Σάρωση {target_ip} στις {len(ports_to_scan)} θύρες TCP χρησιμοποιώντας {self.max_workers} εργάτες...")
            
            open_ports = {} # Χρήση λεξικού για αποθήκευση θύρας: υπηρεσία
            
            def tcp_connect_scan(port):
                """Συνάρτηση εργασίας για σάρωση TCP connect"""
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(self.scan_timeout)
                        if sock.connect_ex((target_ip, port)) == 0:
                            # Η θύρα είναι ανοιχτή, δοκιμή λήψης banner
                            try:
                                service = self.grab_banner(sock, port)
                                return (port, service)
                            except:
                                return (port, "Άγνωστο")
                except:
                    pass
                return None
            
            # --- ΑΠΟΔΟΤΙΚΗ ΟΜΑΔΑ ΝΗΜΑΤΩΝ ---
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_port = {executor.submit(tcp_connect_scan, port): port for port in ports_to_scan}
                for future in concurrent.futures.as_completed(future_to_port):
                    result = future.result()
                    if result:
                        port, service = result
                        open_ports[port] = service
                        print(f"  {Fore.GREEN}[+] Θύρα {port:5}{Style.RESET_ALL} - ΑΝΟΙΧΤΗ - {service}")
            
            # Εμφάνιση αποτελεσμάτων
            print(f"\n{Fore.GREEN}✅ Η σάρωση TCP ολοκληρώθηκε!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            if open_ports:
                print(f"Βρέθηκαν {len(open_ports)} ανοιχτές θύρες:")
                for port in sorted(open_ports.keys()):
                    service = open_ports[port]
                    print(f"  Θύρα {port:5} - {Fore.GREEN}ΑΝΟΙΧΤΗ{Style.RESET_ALL} - {service}")
                    self.record_audit_finding(target, 'Βελτιωμένη Σάρωση Θυρών', f'Ανοιχτή Θύρα: {port}', f'Η θύρα {port} ({service}) είναι ανοιχτή', 'Ενημερωτικό')
            else:
                print("Δεν βρέθηκαν ανοιχτές θύρες.")
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def grab_banner(self, sock, port):
            """Προσπάθεια λήψης banner υπηρεσίας από ανοιχτή θύρα"""
            try:
                # Αποστολή ανιχνευτή βάσει θύρας
                if port in [80, 8080]:
                    sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
                elif port in [443, 8443]:
                    return "HTTPS (SSL)" # Δεν μπορεί να ληφθεί banner χωρίς SSL wrapper
                
                banner = sock.recv(1024).decode('utf-8', errors='ignore').strip().split('\n')[0]
                
                if banner:
                    return banner[:60] + "..." if len(banner) > 60 else banner
                elif port == 21: return "FTP"
                elif port == 22: return "SSH"
                elif port == 25: return "SMTP"
                elif port == 53: return "DNS"
                elif port == 110: return "POP3"
                elif port == 143: return "IMAP"
                else: return "Ανιχνεύτηκε υπηρεσία"
            except socket.timeout:
                return "Ανιχνεύτηκε υπηρεσία (Χωρίς banner)"
            except Exception:
                return "Ανιχνεύτηκε υπηρεσία"

        def network_discovery(self):
            """Προηγμένη ανακάλυψη δικτύου χρησιμοποιώντας πολλαπλές τεχνικές - ΑΠΟΔΟΤΙΚΗ ΟΜΑΔΑ ΝΗΜΑΤΩΝ"""
            print(f"\n{Fore.CYAN}🌐 ΠΡΟΧΩΡΗΜΕΝΗ ΑΝΑΚΑΛΥΨΗ ΔΙΚΤΥΟΥ{Style.RESET_ALL}")
            
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
            print(f"[*] Σάρωση δικτύου: {network_base}0/24 χρησιμοποιώντας {self.max_workers} εργάτες...")
            
            discovered_hosts = {} # ip: [λόγος]
            common_ports = [22, 80, 443, 8080, 3389, 445]
            lock = threading.Lock()

            def discover_host(ip):
                """Συνάρτηση εργασίας για σάρωση ενός μόνο υπολογιστή με πολλαπλές μεθόδους."""
                reasons = []
                
                # Μέθοδος 1: ICMP Ping
                try:
                    subprocess.run(['ping', '-c', '1', '-W', '1', ip], 
                                 capture_output=True, timeout=2, check=True)
                    reasons.append("ICMP")
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    pass # Ο υπολογιστής είναι εκτός λειτουργίας ή δεν ανταποκρίνεται στο ping

                # Μέθοδος 2: Δοκιμή Θύρας TCP
                for port in common_ports:
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                            sock.settimeout(0.5) # Ταχύτερο χρονικό όριο για ανακάλυψη
                            if sock.connect_ex((ip, port)) == 0:
                                reasons.append(f"TCP/{port}")
                    except:
                        pass
                
                if reasons:
                    with lock:
                        discovered_hosts[ip] = reasons
                        print(f"  {Fore.GREEN}[+] {ip:15}{Style.RESET_ALL} - Ενεργό (Βρέθηκε μέσω: {', '.join(reasons)})")

            # --- ΑΠΟΔΟΤΙΚΗ ΟΜΑΔΑ ΝΗΜΑΤΩΝ ---
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(discover_host, network_base + str(i)) for i in range(1, 255) if network_base + str(i) != local_ip]
                # Αναμονή για ολοκλήρωση όλων
                for future in concurrent.futures.as_completed(futures):
                    pass # Τα αποτελέσματα εκτυπώνονται ζωντανά
            
            print(f"\n{Fore.GREEN}✅ Η ανακάλυψη δικτύου ολοκληρώθηκε!{Style.RESET_ALL}")
            print(f"Ανακαλύφθηκαν {len(discovered_hosts)} ενεργοί υπολογιστές (εκτός από εσάς):")
            for host in sorted(discovered_hosts.keys()):
                print(f"  - {host:15} ({', '.join(discovered_hosts[host])})")
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def subnet_calculator(self):
            """Υπολογιστής υποδικτύου και εργαλείο πληροφοριών δικτύου"""
            print(f"\n{Fore.CYAN}🧮 ΥΠΟΛΟΓΙΣΤΗΣ ΥΠΟΔΙΚΤΥΟΥ{Style.RESET_ALL}")
            
            ip_input = input(f"{Fore.WHITE}Εισάγετε διεύθυνση IP με CIDR (π.χ., 192.168.1.0/24): {Style.RESET_ALL}").strip()
            
            if not ip_input or '/' not in ip_input:
                print(f"{Fore.RED}❌ Παρακαλώ χρησιμοποιήστε τη μορφή: IP/CIDR{Style.RESET_ALL}")
                return
            
            try:
                ip_str, cidr_str = ip_input.split('/')
                cidr = int(cidr_str)
                if not (0 <= cidr <= 32):
                    raise ValueError("Το CIDR πρέπει να είναι μεταξύ 0 και 32")
                
                ip_parts = list(map(int, ip_str.split('.')))
                if len(ip_parts) != 4 or any(not (0 <= p <= 255) for p in ip_parts):
                    raise ValueError("Μη έγκυρη διεύθυνση IP")

                ip_int = (ip_parts[0] << 24) + (ip_parts[1] << 16) + (ip_parts[2] << 8) + ip_parts[3]
                
                mask_int = (0xFFFFFFFF << (32 - cidr)) & 0xFFFFFFFF
                
                network_int = ip_int & mask_int
                broadcast_int = network_int | ~mask_int & 0xFFFFFFFF
                
                def int_to_ip(ip_int_val):
                    return '.'.join([str((ip_int_val >> (i << 3)) & 0xFF) for i in (3, 2, 1, 0)])
                
                network_addr = int_to_ip(network_int)
                broadcast_addr = int_to_ip(broadcast_int)
                subnet_mask = int_to_ip(mask_int)
                
                total_hosts = 2 ** (32 - cidr)
                usable_hosts = max(0, total_hosts - 2)
                
                print(f"\n{Fore.GREEN}📊 ΑΠΟΤΕΛΕΣΜΑΤΑ ΥΠΟΛΟΓΙΣΜΟΥ ΥΠΟΔΙΚΤΥΟΥ:{Style.RESET_ALL}")
                print(f"  Διεύθυνση:            {ip_str}/{cidr}")
                print(f"  Μάσκα Υποδικτύου:        {subnet_mask}")
                print(f"  Διεύθυνση Δικτύου:    {network_addr}")
                print(f"  Διεύθυνση Broadcast:  {broadcast_addr}")
                print(f"  Συνολικοί Υπολογιστές:        {total_hosts}")
                print(f"  Χρησιμοποιήσιμοι Υπολογιστές:       {usable_hosts}")
                
                if usable_hosts > 0:
                    first_host = int_to_ip(network_int + 1)
                    last_host = int_to_ip(broadcast_int - 1)
                    print(f"  Εύρος Υπολογιστών:         {first_host} - {last_host}")
                
            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα υπολογισμού υποδικτύου: {e}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        # --- Διαδίκτυο & Διαγνωστικά (Χωρίς Root) ---
        def run_internet_speed_test(self):
            print(f"\n{Fore.CYAN}⚡️ ΕΚΤΕΛΕΣΗ ΔΟΚΙΜΗΣ ΤΑΧΥΤΗΤΑΣ ΔΙΑΔΙΚΤΥΟΥ...{Style.RESET_ALL}")
            if not SPEEDTEST_AVAILABLE or not speedtest:
                print(f"{Fore.RED}❌ Το module 'speedtest-cli' δεν είναι διαθέσιμο.{Style.RESET_ALL}")
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
                print(f"  Ping:       {ping:.2f} ms")
                print(f"  Λήψη:   {Fore.GREEN}{download_speed:.2f} Mbps{Style.RESET_ALL}")
                print(f"  Αποστολή:     {Fore.GREEN}{upload_speed:.2f} Mbps{Style.RESET_ALL}")
                print("="*50)
            except Exception as e:
                print(f"{Fore.RED}❌ Η δοκιμή ταχύτητας απέτυχε: {e}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def get_external_ip_info(self):
            print(f"\n{Fore.CYAN}🗺️ ΛΗΨΗ ΠΛΗΡΟΦΟΡΙΩΝ ΕΞΩΤΕΡΙΚΗΣ IP...{Style.RESET_ALL}")
            if not REQUESTS_AVAILABLE:
                print(f"{Fore.RED}❌ Το module 'requests' δεν είναι διαθέσιμο.{Style.RESET_ALL}")
                return
            try:
                data = requests.get("http://ip-api.com/json/", timeout=10).json()
                if data.get('status') == 'success':
                    print(f"\n{Fore.GREEN}✅ Πληροφορίες Εξωτερικής IP:{Style.RESET_ALL}")
                    print(f"  Διεύθυνση IP:   {data.get('query')}")
                    print(f"  ISP/Πάροχος: {data.get('isp')}")
                    print(f"  Τοποθεσία:     {data.get('city')}, {data.get('regionName')}, {data.get('country')}")
                    print(f"  Οργανισμός: {data.get('org')}")
                else:
                    print(f"{Fore.RED}❌ Αποτυχία λήψης πληροφοριών IP.{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Αποτυχία σύνδεσης με την υπηρεσία IP: {e}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
            
        def run_network_diagnostics(self):
            print(f"\n{Fore.CYAN}📶 ΔΙΑΓΝΩΣΤΙΚΑ ΔΙΚΤΥΟΥ{Style.RESET_ALL}")
            host = input(f"{Fore.WHITE}Εισάγετε υπολογιστή ή IP για δοκιμή (π.χ., google.com): {Style.RESET_ALL}").strip()
            if not host: return
            
            print(f"\n{Fore.CYAN}>>> Εκτέλεση δοκιμής PING στον {host}...{Style.RESET_ALL}")
            try:
                result = subprocess.run(['ping', '-c', '4', host], capture_output=True, text=True, timeout=10)
                print(result.stdout if result.returncode == 0 else result.stderr)
            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα εκτέλεσης ping: {e}{Style.RESET_ALL}")
            
            print(f"\n{Fore.CYAN}>>> Εκτέλεση δοκιμής TRACEROUTE στον {host}...{Style.RESET_ALL}")
            try:
                # Χρήση -n για αποφυγή ανάλυσης DNS, που είναι ταχύτερη
                result = subprocess.run(['traceroute', '-n', host], capture_output=True, text=True, timeout=30)
                print(result.stdout if result.returncode == 0 else result.stderr)
            except FileNotFoundError:
                print(f"{Fore.RED}❌ Το 'traceroute' δεν βρέθηκε. Παρακαλώ εγκαταστήστε το 'inetutils' (pkg install inetutils){Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα εκτέλεσης traceroute: {e}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        # --- Συλλογή Πληροφοριών (Χωρίς Root) ---
        def run_osintds_scanner(self):
            """Wrapper για το εργαλείο σάρωσης OSINTDS."""
            print(f"\n{Fore.CYAN}Εκκίνηση Σαρωτή OSINTDS...{Style.RESET_ALL}")
            time.sleep(1)

            # --- ΛΟΓΙΚΗ OSINTDS - Ενσωματωμένη σε αυτή τη μέθοδο ---
            
            # --- Διαμόρφωση και Σταθερές ---
            PREFERRED_PATHS = [
                os.path.expanduser("~/storage/downloads"),
                os.path.expanduser("/sdcard/Download"),
                os.path.expanduser("~/Downloads"),
                self.save_dir # Χρήση του αποθετηρίου αποθήκευσης της εφαρμογής
            ]

            def get_downloads_dir():
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

            DIR_WORDLIST_B64 = "YWRtaW4KYmFja3VwCnJvYm90cy50eHQKc2l0ZW1hcC54bWwKLmVudi5iYWNrCnVwbG9hZHMKYWRtaW5pc3RyYXRvcgo="
            SUBDOMAIN_WORDLIST_B64 = "d3d3CmFwaQpibG9nCmRldgptYWlsCnN0YWdpbmcKdGVzdApzdG9yZQ=="

            def unpack_wordlist(b64, dest_path, name):
                try:
                    raw = base64.b64decode(b64)
                    txt = raw.decode('utf-8', errors='ignore')
                    if not txt.strip():
                        print(f'[ΠΡΟΣΟΧΗ] Η λίστα λέξεων για {name} είναι κενή.')
                        return None
                    with open(dest_path, 'w', encoding='utf-8') as f:
                        f.write(txt)
                    print(f'[ΠΛΗΡΟΦΟΡΙΑ] Δημιουργήθηκε προεπιλεγμένη λίστα λέξεων: {dest_path} ({len(txt.splitlines())} εγγραφές)')
                    return dest_path
                except Exception as e:
                    print(f'[ΣΦΑΛΜΑ] Σφάλμα αποσυμπίεσης λίστας λέξεων για {name}: {e}')
                    open(dest_path, 'w').close()
                    return None

            WORDLIST_DIR = os.path.join(BASE_OSINT_DIR, 'wordlists')
            os.makedirs(WORDLIST_DIR, exist_ok=True)
            DIR_WORDLIST_PATH = os.path.join(WORDLIST_DIR, 'dirs.txt')
            SUB_WORDLIST_PATH = os.path.join(WORDLIST_DIR, 'subdomains.txt')

            if not os.path.isfile(DIR_WORDLIST_PATH) or os.path.getsize(DIR_WORDLIST_PATH) == 0:
                unpack_wordlist(DIR_WORDLIST_B64, DIR_WORDLIST_PATH, 'dirs.txt')
            if not os.path.isfile(SUB_WORDLIST_PATH) or os.path.getsize(SUB_WORDLIST_PATH) == 0:
                unpack_wordlist(SUBDOMAIN_WORDLIST_B64, SUB_WORDLIST_PATH, 'subdomains.txt')

            def read_wordlist(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return [line.strip() for line in f if line.strip()]
                except FileNotFoundError:
                    print(f'[ΣΦΑΛΜΑ] Η λίστα λέξεων δεν βρέθηκε στο {path}.')
                    return []
                except Exception as e:
                    print(f'[ΣΦΑΛΜΑ] Αποτυχία ανάγνωσης λίστας λέξεων στο {path}: {e}')
                    return []

            # --- Βασικές Βοηθητικές Συναρτήσεις ---
            def normalize_target(raw_input):
                raw_input = raw_input.strip()
                if not raw_input: return None, None
                if not re.match(r'^(http://|https://)', raw_input, re.IGNORECASE):
                    raw_input = 'http://' + raw_input
                try:
                    parsed = urlparse(raw_input)
                    domain = parsed.hostname
                    if not domain: return None, None
                    base = f"{parsed.scheme}://{parsed.netloc}"
                    return base.rstrip('/'), domain
                except ValueError: return None, None

            def make_dirs(domain):
                safe_domain = re.sub(r'[^\w\-.]', '_', domain)
                target_dir = os.path.join(BASE_OSINT_DIR, safe_domain)
                os.makedirs(target_dir, exist_ok=True)
                return target_dir

            def save_text(folder, filename, text):
                path = os.path.join(folder, filename)
                try:
                    with open(path, 'w', encoding='utf-8') as f: f.write(text)
                    print(f"[ΠΛΗΡΟΦΟΡΙΑ] Αποθηκεύτηκε: {path}")
                except IOError as e: print(f'[ΣΦΑΛΜΑ] Σφάλμα αποθήκευσης αρχείου για {path}: {e}')

            def save_csv(folder, filename, rows, headers=None):
                path = os.path.join(folder, filename)
                try:
                    with open(path, 'w', newline='', encoding='utf-8') as cf:
                        writer = csv.writer(cf)
                        if headers: writer.writerow(headers)
                        writer.writerows([[str(item) for item in row] for row in rows])
                    print('[ΠΛΗΡΟΦΟΡΙΑ] Αποθηκεύτηκε CSV:', path)
                except IOError as e: print(f'[ΣΦΑΛΜΑ] Σφάλμα αποθήκευσης CSV για {path}: {e}')

            def checkpoint_save(folder, report):
                save_text(folder, 'report.json', json.dumps(report, indent=2, default=str))

            # --- ΣΥΝΑΡΤΗΣΕΙΣ ΣΑΡΩΣΗΣ ---
            def get_whois_info_osint(domain):
                try:
                    w = whois.whois(domain)
                    if not w: return {'error': 'Δεν επιστράφηκαν δεδομένα WHOIS.'}
                    whois_data = {}
                    for key, value in w.items():
                        if not value: continue
                        if isinstance(value, list):
                            whois_data[key] = ', '.join(map(str, value))
                        elif hasattr(value, 'strftime'):
                            whois_data[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                        else: whois_data[key] = str(value)
                    return whois_data
                except Exception as e: return {'error': str(e)}

            def reverse_dns_lookup(ip_address):
                if not ip_address: return None
                try: return socket.gethostbyaddr(ip_address)[0]
                except (socket.herror, socket.gaierror): return None

            def resolve_all_dns(domain):
                results = {}
                record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA']
                for record_type in record_types:
                    try:
                        answers = dns_resolver.resolve(domain, record_type)
                        results[record_type] = sorted([str(r).strip() for r in answers])
                    except dns_resolver.NoAnswer: results[record_type] = []
                    except dns_resolver.NXDOMAIN: results[record_type] = ['Domain Not Found']
                    except dns_resolver.Timeout: results[record_type] = ['Timeout']
                    except Exception: results[record_type] = ['Error']
                return results

            def extract_content_info(html_content):
                soup = BeautifulSoup(html_content, 'html.parser')
                info = {'emails': [], 'generator': None, 'comments': []}
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html_content)
                info['emails'] = sorted(list(set(emails)))
                meta_gen = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'generator'})
                if meta_gen and 'content' in meta_gen.attrs:
                    info['generator'] = meta_gen['content'].strip()
                comments = re.findall(r'', html_content, re.DOTALL)
                info['comments'] = [c.strip() for c in comments if c.strip() and len(c.strip()) < 300]
                return info

            def check_wayback_machine(domain):
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
                return {h: headers.get(h, 'MISSING') for h in SECURITY_HEADERS}

            def fetch(url, allow_redirects=True, timeout=HTTP_TIMEOUT, verbose=False):
                try:
                    time.sleep(RATE_SLEEP + random.random() * 0.05)
                    r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=allow_redirects, verify=False)
                    return r
                except requests.exceptions.Timeout:
                    if verbose: print(f'[ΠΡΟΣΟΧΗ] Χρονικό όριο πρόσβασης {url}')
                except requests.exceptions.RequestException as e:
                    if verbose: print(f'[ΠΡΟΣΟΧΗ] Σφάλμα αίτησης για {url}: {e}')
                return None

            def probe_port(host, port, timeout=1.5):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(timeout)
                        s.connect((host, port))
                        return port, True
                except (socket.timeout, ConnectionRefusedError, OSError):
                    return port, False

            def probe_ports_connect(host, ports, threads=100, timeout=1.5):
                open_ports = []
                with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
                    future_to_port = {executor.submit(probe_port, host, p, timeout): p for p in ports}
                    for future in concurrent.futures.as_completed(future_to_port):
                        port, is_open = future.result()
                        if is_open: open_ports.append(port)
                return sorted(open_ports)

            def ssl_info(domain):
                info = {}
                try:
                    import ssl
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
                except (socket.gaierror, socket.timeout, ssl.SSLError, ConnectionRefusedError, OSError, ImportError) as e:
                    info['error'] = str(e)
                return info

            def resolve_host(name):
                try: return socket.gethostbyname(name)
                except socket.gaierror: return None

            def subdomain_bruteforce_osint(domain, wordlist, threads=50):
                found = []
                def check(sub):
                    fqdn = f"{sub}.{domain}"
                    ip = resolve_host(fqdn)
                    if ip: return (fqdn, ip)
                    return None
                with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
                    futures = {executor.submit(check, w): w for w in wordlist}
                    for future in concurrent.futures.as_completed(futures):
                        result = future.result()
                        if result: found.append(result)
                return found

            def attempt_zone_transfer(domain):
                results = []
                try:
                    answers = dns_resolver.resolve(domain, 'NS')
                    for rdata in answers:
                        ns = str(rdata.target).rstrip('.')
                        try:
                            zone = dns.zone.from_xfr(dns.query.xfr(ns, domain, timeout=5))
                            if zone:
                                records = [f"{name} {zone[name].to_text()}" for name in zone.nodes.keys()]
                                results.append({'nameserver': ns, 'records': records})
                        except (dns.exception.FormError, dns.exception.Timeout, ConnectionRefusedError):
                            continue
                except (dns_resolver.NoAnswer, dns_resolver.NXDOMAIN, dns_resolver.Timeout):
                    pass
                return results

            def dir_bruteforce(base_url, words, threads=50, verbose=False):
                hits = []
                def probe(word):
                    url = urljoin(base_url + '/', word)
                    r = fetch(url, verbose=verbose, allow_redirects=False)
                    if r and r.status_code in (200, 301, 302, 403, 500):
                        return (word, r.status_code, r.headers.get('Location', r.url))
                    return None
                with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
                    futures = {executor.submit(probe, w) for w in words}
                    for future in concurrent.futures.as_completed(futures):
                        result = future.result()
                        if result: hits.append(result)
                return hits

            def basic_sqli_test_on_url(url, verbose=False):
                if '?' not in url: return None
                try:
                    r = fetch(url + "'", verbose=verbose)
                    if r:
                        response_text = r.text.lower()
                        for pattern in SQL_ERROR_PATTERNS:
                            if pattern in response_text:
                                return {'url': url, 'pattern': pattern, 'trigger': "'"}
                except Exception: pass
                return None

            def xss_reflection_test(url, verbose=False):
                try:
                    parsed = urlparse(url)
                    query_params = parse_qs(parsed.query, keep_blank_values=True)
                except ValueError: return []
                if not query_params: return []
                findings = []
                for param, values in query_params.items():
                    original_value = values[0] if values else ''
                    temp_params = query_params.copy()
                    temp_params[param] = original_value + XSS_TEST_PAYLOAD
                    new_query = urlencode(temp_params, doseq=True)
                    new_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
                    r = fetch(new_url, verbose=verbose)
                    if r and XSS_TEST_PAYLOAD in r.text:
                        findings.append({'url': new_url, 'param': param})
                return findings
            
            def check_termux_package(package_name, command_to_check=None):
                command_to_check = command_to_check or package_name
                return shutil.which(command_to_check) is not None

            def hf_display_message(message, color='default'):
                colors = {'red': Fore.RED, 'green': Fore.GREEN, 'yellow': Fore.YELLOW, 'blue': Fore.CYAN, 'default': Style.RESET_ALL}
                print(f"{colors.get(color, colors['default'])}{message}{Style.RESET_ALL}")

            def hf_get_website_dir(url):
                parsed_url = urlparse(url)
                hostname = parsed_url.netloc.replace('www.', '')
                clean_name = re.sub(r'[^\w\-.]', '_', hostname) or "website_content"
                return os.path.join(BASE_OSINT_DIR, 'html_inspector', clean_name.lower())

            def hf_download_asset(asset_url, local_dir, base_url):
                if not asset_url or asset_url.startswith('data:'): return None, None
                try:
                    absolute_asset_url = urljoin(base_url, asset_url)
                    parsed_asset_url = urlparse(absolute_asset_url)
                    path_part = unquote(parsed_asset_url.path)
                    filename = os.path.basename(path_part) or f"asset_{abs(hash(absolute_asset_url))}"
                    filename = re.sub(r'[\\/:*?"<>|]', '_', filename)
                    local_path = os.path.join(local_dir, filename)
                    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                        return os.path.relpath(local_path, start=os.path.dirname(local_dir)), absolute_asset_url
                    response = requests.get(absolute_asset_url, stream=True, timeout=10, verify=False)
                    response.raise_for_status()
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    with open(local_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192): f.write(chunk)
                    return os.path.relpath(local_path, start=os.path.dirname(local_dir)), absolute_asset_url
                except requests.exceptions.RequestException: return None, None
                except IOError as e:
                    hf_display_message(f"Αποτυχία αποθήκευσης στοιχείου {asset_url}: {e}", 'red')
                    return None, None

            def hf_process_html_and_download_assets(html_content, base_url, website_dir):
                soup = BeautifulSoup(html_content, 'html.parser')
                downloaded_urls = {}
                hf_display_message("\nΈναρξη διαδικασίας λήψης στοιχείων...", 'blue')
                for tag_name, attr_name, subdir, filter_func in ASSET_MAP:
                    for tag in soup.find_all(tag_name):
                        if filter_func and not filter_func(tag): continue
                        asset_url = tag.get(attr_name)
                        if asset_url and asset_url not in downloaded_urls:
                            asset_subdir_path = os.path.join(website_dir, subdir)
                            relative_asset_path, abs_url = hf_download_asset(asset_url, asset_subdir_path, base_url)
                            if relative_asset_path:
                                new_path = os.path.join(subdir, os.path.basename(relative_asset_path)).replace('\\', '/')
                                tag[attr_name] = new_path
                                downloaded_urls[abs_url] = new_path
                hf_display_message(f"Ολοκληρώθηκε η λήψη στοιχείων και τροποποίηση HTML. ({len(downloaded_urls)} στοιχεία επεξεργάστηκαν)", 'green')
                return str(soup)

            def hf_edit_html_in_editor(html_content):
                if not html_content:
                    hf_display_message("Δεν υπάρχει περιεχόμενο για επεξεργασία.", 'yellow')
                    return None
                try:
                    with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8', suffix='.html') as temp_file:
                        temp_file_path = temp_file.name
                        temp_file.write(html_content)
                    hf_display_message(f"\nΆνοιγμα HTML στον {EDITOR}. Αποθηκεύστε και κλείστε για εφαρμογή αλλαγών.", 'yellow')
                    subprocess.run([EDITOR, temp_file_path], check=True)
                    with open(temp_file_path, 'r', encoding='utf-8') as f:
                        modified_html = f.read()
                    hf_display_message("Το περιεχόμενο HTML ενημερώθηκε από τον επεξεργαστή.", 'green')
                    return modified_html
                except FileNotFoundError: hf_display_message(f"Σφάλμα: Ο επεξεργαστής '{EDITOR}' δεν βρέθηκε.", 'red')
                except subprocess.CalledProcessError: hf_display_message(f"Ο επεξεργαστής '{EDITOR}' τερμάτισε με σφάλμα. Οι αλλαγές μπορεί να μην αποθηκεύτηκαν.", 'red')
                except Exception as e: hf_display_message(f"Παρουσιάστηκε σφάλμα κατά την επεξεργασία: {e}", 'red')
                finally:
                    if 'temp_file_path' in locals() and os.path.exists(temp_file_path): os.remove(temp_file_path)
                return None

            def hf_save_html_to_file(html_content, target_dir, filename="index.html"):
                if not html_content:
                    hf_display_message("Δεν υπάρχει περιεχόμενο για αποθήκευση.", 'yellow')
                    return None
                os.makedirs(target_dir, exist_ok=True)
                filepath = os.path.join(target_dir, filename)
                try:
                    with open(filepath, 'w', encoding='utf-8') as f: f.write(html_content)
                    hf_display_message(f"Το HTML αποθηκεύτηκε επιτυχώς στο '{filepath}'", 'green')
                    return filepath
                except IOError as e:
                    hf_display_message(f"Σφάλμα αποθήκευσης αρχείου: {e}", 'red')
                    return None
            
            def hf_preview_html_in_browser(filepath):
                if not filepath or not os.path.exists(filepath):
                    hf_display_message("Δεν βρέθηκε αρχείο HTML για προεπισκόπηση.", 'yellow')
                    return
                if check_termux_package("termux-open-url"):
                    hf_display_message(f"Άνοιγμα προεπισκόπησης στο πρόγραμμα περιήγησης Termux...", 'blue')
                    subprocess.run(['termux-open-url', f'file://{filepath}'])
                else:
                    hf_display_message(f"Άνοιγμα προεπισκόπησης στο προεπιλεγμένο πρόγραμμα περιήγησης συστήματος...", 'blue')
                    webbrowser.open(f'file://{os.path.abspath(filepath)}')

            def hf_fetch_html(url, verbose=False):
                response = fetch(url, verbose=verbose)
                if response: return response.text
                if verbose: hf_display_message(f"Αποτυχία λήψης HTML για {url}", 'red')
                return None

            def run_html_finder(initial_url, folder, verbose=False):
                current_url = initial_url
                website_dir = hf_get_website_dir(current_url)
                hf_display_message(f"\n--- Έναρξη Διαδραστικού Επιθεωρητή HTML για {current_url} ---", 'blue')
                hf_display_message(f"Η τοπική διαδρομή αποθήκευσης θα είναι: {website_dir}", 'yellow')
                html_content = hf_fetch_html(current_url, verbose)
                if not html_content:
                    hf_display_message("Αποτυχία λήψης αρχικού HTML. Δεν είναι δυνατή η συνέχεια.", 'red')
                    return
                while True:
                    hf_display_message("\n--- Επιλογές Επιθεωρητή HTML ---", 'blue')
                    print("1. Λήψη Στοιχείων & Αποθήκευση HTML (Δημιουργία/Ενημέρωση Τοπικού Αντιγράφου)")
                    print("2. Επεξεργασία Τρέχοντος HTML (Άνοιγμα σε Επεξεργαστή)")
                    print("3. Προεπισκόπηση Τρέχοντος HTML σε Πρόγραμμα Περιήγησης")
                    print("4. Εισαγωγή ΝΕΑΣ URL (Λήψη νέου περιεχομένου)")
                    print("5. Έξοδος από τον Επιθεωρητή HTML")
                    choice = input("Εισάγετε την επιλογή σας (1-5): ").strip()
                    if choice == '1':
                        modified_html = hf_process_html_and_download_assets(html_content, current_url, website_dir)
                        if modified_html:
                            html_content = modified_html
                            hf_save_html_to_file(html_content, website_dir)
                    elif choice == '2':
                        modified_html = hf_edit_html_in_editor(html_content)
                        if modified_html is not None:
                            html_content = modified_html
                            hf_save_html_to_file(html_content, website_dir)
                    elif choice == '3':
                        saved_path = hf_save_html_to_file(html_content, website_dir)
                        if saved_path: hf_preview_html_in_browser(saved_path)
                    elif choice == '4':
                        new_url_input = input("Εισάγετε τη νέα URL ιστότοπου: ").strip()
                        if new_url_input:
                            normalized_url, _ = normalize_target(new_url_input)
                            if normalized_url:
                                current_url, website_dir = normalized_url, hf_get_website_dir(normalized_url)
                                new_html = hf_fetch_html(current_url, verbose)
                                if new_html: html_content = new_html
                                else: hf_display_message("Αποτυχία λήψης νέας URL. Παραμένει το προηγούμενο περιεχόμενο.", 'red')
                            else: hf_display_message("Παρέχθηκε μη έγκυρη URL.", 'yellow')
                    elif choice == '5':
                        hf_display_message("Έξοδος από τον επιθεωρητή HTML.", 'blue')
                        break
                    else: hf_display_message("Μη έγκυρη επιλογή. Παρακαλώ εισάγετε αριθμό μεταξύ 1 και 5.", 'red')

            def save_html_report(folder, report):
                html_template = f"""
                <html><head><meta charset="utf-8"><title>Αναφορά OSINTDS για {html.escape(report.get('domain', 'Δ/Υ'))}</title>
                <style>body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Oxygen-Sans,Ubuntu,Cantarell,"Helvetica Neue",sans-serif;line-height:1.6;color:#333;max-width:1200px;margin:0 auto;padding:20px;background-color:#f9f9f9}}h1,h2,h3{{color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:10px}}h1{{font-size:2.5em}}pre{{background-color:#ecf0f1;padding:1em;border:1px solid #bdc3c7;border-radius:5px;white-space:pre-wrap;word-wrap:break-word;font-family:"Courier New",Courier,monospace}}ul,ol{{padding-left:20px}}li{{margin-bottom:5px}}.card{{background-color:#fff;border:1px solid #ddd;border-radius:8px;padding:20px;margin-bottom:20px;box-shadow:0 2px4px rgba(0,0,0,0.1)}}</style>
                </head><body><h1>Αναφορά OSINTDS για {html.escape(report.get('domain', 'Δ/Υ'))}</h1><div class="card"><h2>Σύνοψη</h2><ul>
                <li><b>URL Στόχος:</b> {html.escape(report.get('target', 'Δ/Υ'))}</li><li><b>Τελική URL:</b> {html.escape(report.get('final_url', 'Δ/Υ'))}</li>
                <li><b>Κύρια IP:</b> {html.escape(report.get('primary_ip', 'Δ/Υ'))}</li><li><b>Αντίστροφο DNS:</b> {html.escape(report.get('reverse_dns', 'Δ/Υ'))}</li>
                <li><b>Κατάσταση HTTP:</b> {html.escape(str(report.get('http_status', 'Δ/Υ')))}</li><li><b>Ανοιχτές Θύρες:</b> {len(report.get('open_ports', []))}</li>
                <li><b>Υποτομείς που Βρέθηκαν:</b> {len(report.get('subdomains', []))}</li></ul></div>"""
                sections = {
                    'Πληροφορίες WHOIS': report.get('whois'),'Εγγραφές DNS': report.get('dns_records'),'Πιστοποιητικό SSL': report.get('ssl'),
                    'Κεφαλίδες Ασφαλείας HTTP': report.get('security_headers'),'Ανοιχτές Θύρες': report.get('open_ports'),'Υποτομείς': report.get('subdomains'),
                    'Ευρήματα Καταλόγου/Αρχείου': report.get('dir_hits'),'Wayback Machine': report.get('wayback'),'Ανάλυση Περιεχομένου Αρχικής Σελίδας': report.get('content_info'),
                    'URL που Ανακαλύφθηκαν (Sitemap/Robots)': report.get('discovered_urls'),'Πιθανά Στοιχεία SQL Injection': report.get('sqli_evidence'),
                    'Πιθανές Αναστολές XSS': report.get('xss_reflections'),'Μεταφορά Ζώνης DNS (AXFR)': report.get('axfr'),
                }
                for title, data in sections.items():
                    if data:
                        html_template += f'<div class="card"><h3>{title}</h3>'
                        if isinstance(data, list) and data:
                            html_template += '<ol>' + ''.join(f'<li>{html.escape(str(item))}</li>' for item in data) + '</ol>'
                        elif isinstance(data, dict):
                            html_template += f'<pre>{html.escape(json.dumps(data, indent=2, default=str))}</pre>'
                        else:
                            html_template += f'<pre>{html.escape(str(data))}</pre>'
                        html_template += '</div>'
                html_template += '</body></html>'
                save_text(folder, 'report.html', html_template)

            def get_user_choice(prompt, default_value):
                response = input(f'{prompt} [Προεπιλογή: {default_value}] (Enter για προεπιλογή, ή πληκτρολογήστε νέα τιμή): ').strip()
                return response or default_value

            def run_checks(target, threads=DEFAULT_THREADS, full_ports=False, out_formats=('json','html','csv'), dir_words=None, sub_words=None, verbose=False):
                base, domain = normalize_target(target)
                folder = make_dirs(domain)
                report_path = os.path.join(folder, 'report.json')
                report = {'target': target, 'domain': domain, 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')}
                if os.path.exists(report_path):
                    if input(f"Βρέθηκε υπάρχουσα αναφορά για {domain}. Συνέχιση σάρωσης; (Ν/ο): ").strip().lower() != 'ο':
                        try:
                            with open(report_path, 'r', encoding='utf-8') as f: report.update(json.load(f))
                            print('[ΠΛΗΡΟΦΟΡΙΑ] Συνέχιση σάρωσης από υπάρχουσα αναφορά.')
                        except (json.JSONDecodeError, IOError) as e: print(f'[ΠΡΟΣΟΧΗ] Δεν ήταν δυνατή η φόρτωση της υπάρχουσας αναφοράς ({e}). Έναρξη από την αρχή.')
                def run_stage(stage_num, name, key, func, *args, **kwargs):
                    print(f"[ΣΤΑΔΙΟ {stage_num}/13] {name}...")
                    if report.get(key) is None:
                        report[key] = func(*args, **kwargs)
                        checkpoint_save(folder, report)
                    else: print(f"[ΠΛΗΡΟΦΟΡΙΑ] Βρέθηκε αποθηκευμένο αποτέλεσμα για '{name}'. Παράβλεψη.")
                print(f"[ΣΤΑΔΙΟ 1/13] Δοκιμή βασικής URL: {base}")
                if report.get('http_status') is None or 'unreachable' in str(report.get('http_status')):
                    r = fetch(base, verbose=verbose)
                    if not r:
                        report['http_status'] = 'unreachable'
                        checkpoint_save(folder, report)
                        print('[ΣΦΑΛΜΑ] Ο στόχος είναι απρόσιτος.')
                        return None, None
                    report['http_status'], report['final_url'], report['headers'] = f"{r.status_code} {r.reason}", r.url, dict(r.headers)
                    checkpoint_save(folder, report)
                else:
                    r = fetch(report.get('final_url', base), verbose=verbose)
                    if not r:
                        print('[ΣΦΑΛΜΑ] Ο επαναληφθείς στόχος είναι τώρα απρόσιτος.')
                        return None, None
                run_stage(2, "Έλεγχος κεφαλίδων ασφαλείας HTTP", 'security_headers', check_security_headers, r.headers)
                run_stage(3, "Έλεγχος πληροφοριών WHOIS", 'whois', get_whois_info_osint, domain)
                run_stage(4, "Ανάλυση DNS και Αντίστροφου DNS", 'dns_records', resolve_all_dns, domain)
                if 'dns_records' in report and report['dns_records'].get('A'):
                    report['primary_ip'] = report['dns_records']['A'][0]
                    run_stage(4, "Εκτέλεση Αντίστροφου DNS", 'reverse_dns', reverse_dns_lookup, report['primary_ip'])
                run_stage(5, "Έλεγχος Wayback Machine", 'wayback', check_wayback_machine, domain)
                run_stage(6, "Έλεγχος πιστοποιητικού SSL", 'ssl', ssl_info, domain)
                run_stage(7, "Ανάλυση περιεχομένου αρχικής σελίδας", 'content_info', extract_content_info, r.text)
                run_stage(8, "Αναζήτηση sitemap/robots.txt", 'discovered_urls', lambda: sorted(list(set(re.findall(r'<loc>([^<]+)</loc>', sm.text, re.I) for sm_url in ([line.split(':', 1)[1].strip() for line in (fetch(urljoin(base, '/robots.txt')) or type('',(object,),{'text':''})()).text.splitlines() if line.lower().startswith('sitemap:')] or [urljoin(base, '/sitemap.xml')]) if (sm := fetch(sm_url)) and sm.status_code == 200))))
                run_stage(9, "Εκτέλεση απαρίθμησης υποτομέων", 'subdomains', subdomain_bruteforce_osint, domain, sub_words, threads=threads)
                run_stage(10, "Προσπάθεια μεταφοράς ζώνης DNS", 'axfr', attempt_zone_transfer, domain)
                port_list = list(range(1, 65536)) if full_ports else [21, 22, 25, 53, 80, 110, 143, 443, 465, 587, 993, 995, 3306, 5432, 8000, 8080, 8443]
                run_stage(11, "Εκτέλεση δοκιμής θυρών", 'open_ports', probe_ports_connect, report.get('primary_ip', domain), port_list, threads=max(100, threads))
                run_stage(12, "Εκτέλεση ωμής βίας καταλόγων", 'dir_hits', dir_bruteforce, base, dir_words, threads=threads, verbose=verbose)
                print("[ΣΤΑΔΙΟ 13/13] Εκτέλεση ευρετικών ευπαθειών...")
                if report.get('sqli_evidence') is None or report.get('xss_reflections') is None:
                    all_links = set(report.get('discovered_urls', [])); soup = BeautifulSoup(r.text, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        full_url = urljoin(base, a['href'])
                        if urlparse(full_url).hostname == domain: all_links.add(full_url)
                    links_to_scan = list(all_links)[:400]
                    print(f'[ΠΛΗΡΟΦΟΡΙΑ] Εκτέλεση ευρετικών SQLi/XSS σε {len(links_to_scan)} URL...')
                    sqli, xss = [], []
                    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
                        sql_futures = {executor.submit(basic_sqli_test_on_url, u, verbose): u for u in links_to_scan if '?' in u}
                        xss_futures = {executor.submit(xss_reflection_test, u, verbose): u for u in links_to_scan if '?' in u}
                        for f in concurrent.futures.as_completed(sql_futures):
                            if res := f.result(): sqli.append(res)
                        for f in concurrent.futures.as_completed(xss_futures):
                            if res := f.result(): xss.extend(res)
                    report['sqli_evidence'], report['xss_reflections'] = sqli, xss; checkpoint_save(folder, report)
                print('\n[ΤΕΛΙΚΟ] Δημιουργία τελικών αρχείων αναφοράς...')
                if 'json' in out_formats: checkpoint_save(folder, report)
                if 'csv' in out_formats:
                    if report.get('subdomains'): save_csv(folder, 'subdomains.csv', report['subdomains'], headers=['Υποτομέας', 'IP'])
                    if report.get('dir_hits'): save_csv(folder, 'dirs.csv', report['dir_hits'], headers=['Διαδρομή', 'Κατάσταση', 'Τελική URL'])
                if 'html' in out_formats: save_html_report(folder, report)
                print('\n--- Σύνοψη Ολοκλήρωσης Σάρωσης ---'); print(f"Στόχος: {report['target']}"); print(f"Κύρια IP: {report.get('primary_ip', 'Δ/Υ')}"); print(f"Κατάσταση HTTP: {report['http_status']}"); print(f"Ανοιχτές θύρες ({len(report.get('open_ports',[]))} βρέθηκαν): {report.get('open_ports', 'Δ/Υ')}"); print(f"Υποτομείς που βρέθηκαν: {len(report.get('subdomains',[]))}"); print(f"Ευρήματα καταλόγων: {len(report.get('dir_hits',[]))}"); print(f"Πιθανό SQLi: {len(report.get('sqli_evidence',[]))}"); print(f"Πιθανό XSS: {len(report.get('xss_reflections',[]))}"); print(f'\nΑποθηκεύτηκαν τα αποτελέσματα στο: {folder}')
                return report, folder

            # --- Κύριο διαδραστικό σημείο εισόδου για OSINTDS ---
            print('--- Διαδραστικός Σαρωτής OSINTDS ---')
            target_input = input('Εισάγετε τομέα ή URL στόχο (π.χ., example.com): ').strip()
            if not target_input:
                print('Δεν παρέχθηκε στόχος. Έξοδος.')
                return
            base, domain = normalize_target(target_input)
            if not domain:
                print('Μη έγκυρη μορφή στόχου. Έξοδος.')
                return
            try: threads = int(get_user_choice('Αριθμός νημάτων;', DEFAULT_THREADS))
            except ValueError: threads = DEFAULT_THREADS
            full_ports = input('Πλήρης σάρωση θυρών (1-65535); Πολύ αργή. (ν/Ο): ').strip().lower().startswith('ν')
            dir_wordlist_path = get_user_choice('Διαδρομή προς λίστα λέξεων καταλόγου;', DIR_WORDLIST_PATH)
            sub_wordlist_path = get_user_choice('Διαδρομή προς λίστα λέξεων υποτομέων;', SUB_WORDLIST_PATH)
            verbose = input('Ενεργοποίηση λειτουργίας λεπτομερειών για αποσφαλμάτωση; (ν/Ο): ').strip().lower().startswith('ν')
            out_formats_raw = get_user_choice('Μορφές εξόδου (json,html,csv);', 'json,html,csv')
            out_formats = {f.strip() for f in out_formats_raw.split(',') if f.strip()}
            dir_words, sub_words = read_wordlist(dir_wordlist_path), read_wordlist(sub_wordlist_path)
            print('\nΑΠΑΓΟΡΕΥΣΗ: Σαρώστε μόνο στόχους που σας ανήκουν ή έχετε ρητή άδεια να δοκιμάσετε.')
            print('Έναρξη σάρωσης OSINT. Αυτό μπορεί να πάρει λίγο χρόνο...')
            report, folder = run_checks(target=target_input, threads=threads, full_ports=full_ports, out_formats=out_formats, dir_words=dir_words, sub_words=sub_words, verbose=verbose)
            if not report:
                print("\nΗ σάρωση δεν μπόρεσε να ολοκληρωθεί.")
                return
            print("\n" + "="*50); print("--- Μετα-Σάρωση Επιθεωρητής/Επεξεργαστής HTML ---")
            if input("Εκτέλεση Διαδραστικού Λήπτη/Επεξεργαστή HTML στη URL στόχο; (ν/Ο): ").strip().lower().startswith('ν'):
                final_url = report.get('final_url') or target_input
                if 'unreachable' not in str(report.get('http_status', '')):
                    run_html_finder(final_url, folder, verbose)
                else: print("[ΠΡΟΣΟΧΗ] Ο στόχος ήταν απρόσιτος, παράβλεψη Επιθεωρητή HTML.")
            print("="*50)

            # Αφού ολοκληρωθεί το εργαλείο, ερώτηση για επιστροφή στο κύριο μενού
            input(f"\n{Fore.YELLOW}Η σάρωση OSINTDS ολοκληρώθηκε. Πατήστε Enter για επιστροφή στο κύριο μενού...{Style.RESET_ALL}")


        def get_whois_info(self):
            print(f"\n{Fore.CYAN}👤 ΑΝΑΖΗΤΗΣΗ WHOIS{Style.RESET_ALL}")
            if not WHOIS_AVAILABLE:
                print(f"{Fore.RED}❌ Το module 'python-whois' δεν είναι διαθέσιμο.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                return

            domain = input(f"{Fore.WHITE}Εισάγετε τομέα για εύρεση πληροφοριών WHOIS: {Style.RESET_ALL}").strip()
            if not domain: return

            try:
                w = whois.whois(domain)
                if not w:
                    print(f"{Fore.RED}❌ Δεν βρέθηκαν πληροφορίες WHOIS για {domain}.{Style.RESET_ALL}")
                    return

                print(f"\n{Fore.GREEN}📋 Πληροφορίες WHOIS για {domain}:{Style.RESET_ALL}")
                print("="*60)
                if w.domain_name: print(f"  Τομέας: {w.domain_name}")
                if w.registrar: print(f"  Μητρώο: {w.registrar}")
                if w.creation_date: 
                    if isinstance(w.creation_date, list):
                        print(f"  Ημερομηνία Δημιουργίας: {w.creation_date[0]}")
                    else:
                        print(f"  Ημερομηνία Δημιουργίας: {w.creation_date}")
                if w.expiration_date:
                    if isinstance(w.expiration_date, list):
                        print(f"  Ημερομηνία Λήξης: {w.expiration_date[0]}")
                    else:
                        print(f"  Ημερομηνία Λήξης: {w.expiration_date}")
                if w.name_servers: 
                    if isinstance(w.name_servers, list):
                        print(f"  Διακομιστές Ονομάτων: {', '.join(w.name_servers)}")
                    else:
                        print(f"  Διακομιστές Ονομάτων: {w.name_servers}")
                if w.status: 
                    if isinstance(w.status, list):
                        print(f"  Κατάσταση: {', '.join(w.status)}")
                    else:
                        print(f"  Κατάσταση: {w.status}")
                if w.emails: print(f"  Email Επαφής: {w.emails}")
                if w.org: print(f"  Οργανισμός: {w.org}")
                if w.country: print(f"  Χώρα: {w.country}")
                print("="*60)

                self.record_audit_finding(domain, 'Αναζήτηση WHOIS', 'Ανακτήθηκαν πληροφορίες WHOIS', f'Βρέθηκαν πληροφορίες WHOIS για {domain}', 'Ενημερωτικό')

            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα κατά την αναζήτηση WHOIS: {e}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def get_dns_info(self):
            print(f"\n{Fore.CYAN}🌐 ΑΝΑΖΗΤΗΣΗ ΠΛΗΡΟΦΟΡΙΩΝ DNS{Style.RESET_ALL}")
            if not DNS_AVAILABLE:
                print(f"{Fore.RED}❌ Το module 'dnspython' δεν είναι διαθέσιμο.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                return

            domain = input(f"{Fore.WHITE}Εισάγετε τομέα για εύρεση πληροφοριών DNS: {Style.RESET_ALL}").strip()
            if not domain: return

            try:
                resolver = dns_resolver.Resolver()
                resolver.timeout = 5
                resolver.lifetime = 5
                
                print(f"\n{Fore.GREEN}📋 Πληροφορίες DNS για {domain}:{Style.RESET_ALL}")
                print("="*60)
                
                record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA']
                
                for record_type in record_types:
                    try:
                        answers = resolver.resolve(domain, record_type)
                        print(f"  {record_type}:")
                        for rdata in answers:
                            print(f"    {rdata}")
                    except dns_resolver.NoAnswer:
                        print(f"  {record_type}: Δεν βρέθηκαν εγγραφές")
                    except dns_resolver.NXDOMAIN:
                        print(f"  {record_type}: Τομέας δεν υπάρχει")
                    except dns_resolver.Timeout:
                        print(f"  {record_type}: Χρονικό όριο")
                    except Exception as e:
                        print(f"  {record_type}: Σφάλμα - {e}")
                print("="*60)
                
                self.record_audit_finding(domain, 'Αναζήτηση DNS', 'Ανακτήθηκαν πληροφορίες DNS', f'Βρέθηκαν εγγραφές DNS για {domain}', 'Ενημερωτικό')

            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα κατά την αναζήτηση DNS: {e}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        # --- Εργαλεία Ασφαλείας (Χωρίς Root) ---
        def run_ssh_brute_force(self):
            print(f"\n{Fore.CYAN}🔓 ΕΡΓΑΛΕΙΟ BRUTE FORCE SSH (Για δοκιμές αυθεντικοποίησης){Style.RESET_ALL}")
            print(f"{Fore.YELLOW}ΣΗΜΕΙΩΣΗ: Χρησιμοποιήστε ΜΟΝΟ σε συστήματα που σας ανήκουν ή έχετε άδεια να δοκιμάσετε.{Style.RESET_ALL}")
            
            if not PARAMIKO_AVAILABLE:
                print(f"{Fore.RED}❌ Το module 'paramiko' δεν είναι διαθέσιμο.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                return

            target = input(f"{Fore.WHITE}Εισάγετε IP/όνομα υπολογιστή SSH: {Style.RESET_ALL}").strip()
            if not target: return
            
            port_input = input(f"{Fore.WHITE}Θύρα SSH [22]: {Style.RESET_ALL}").strip()
            port = int(port_input) if port_input.isdigit() else 22
            
            usernames_input = input(f"{Fore.WHITE}Λίστα ονομάτων χρήστη (διαχωρισμός με κόμμα) [admin,root]: {Style.RESET_ALL}").strip()
            usernames = [u.strip() for u in usernames_input.split(',')] if usernames_input else ['admin', 'root']
            
            passwords_input = input(f"{Fore.WHITE}Λίστα κωδικών πρόσβασης (διαχωρισμός με κόμμα) [admin,123456]: {Style.RESET_ALL}").strip()
            passwords = [p.strip() for p in passwords_input.split(',')] if passwords_input else ['admin', '123456']
            
            print(f"\n[*] Έναρξη δοκιμής SSH Brute Force στο {target}:{port}...")
            print(f"[*] Ονόματα χρήστη: {', '.join(usernames)}")
            print(f"[*] Κωδικοί πρόσβασης: {', '.join(passwords)}")
            
            found_credentials = []
            total_attempts = len(usernames) * len(passwords)
            current_attempt = 0
            
            for username in usernames:
                for password in passwords:
                    current_attempt += 1
                    print(f"[{current_attempt}/{total_attempts}] Δοκιμή {username}:{password}")
                    
                    try:
                        client = paramiko.SSHClient()
                        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        client.connect(target, port=port, username=username, password=password, timeout=10)
                        
                        print(f"\n{Fore.GREEN}✅ ΒΡΕΘΗΚΑΝ ΕΠΙΤΥΧΗΣ ΔΙΑΠΙΣΤΕΥΤΙΚΑ!{Style.RESET_ALL}")
                        print(f"   Χρήστης: {username}")
                        print(f"   Κωδικός: {password}")
                        found_credentials.append((username, password))
                        client.close()
                        break  # Σταματήστε για αυτό το όνομα χρήστη αν βρεθεί
                        
                    except paramiko.AuthenticationException:
                        pass  # Αποτυχία πιστοποίησης, συνέχεια
                    except Exception as e:
                        print(f"{Fore.RED}❌ Σφάλμα σύνδεσης: {e}{Style.RESET_ALL}")
                        break
                    finally:
                        client.close() if 'client' in locals() else None
            
            if found_credentials:
                print(f"\n{Fore.GREEN}🎯 ΒΡΕΘΗΚΑΝ ΕΠΙΤΥΧΗΣ ΔΙΑΠΙΣΤΕΥΤΙΚΑ:{Style.RESET_ALL}")
                for user, pwd in found_credentials:
                    print(f"   {user}:{pwd}")
                self.record_audit_finding(target, 'SSH Brute Force', 'Επιτυχής εύρεση διαπιστευτηρίων', f'Βρέθηκαν διαπιστευτήρια: {found_credentials}', 'ΥΨΗΛΟ')
            else:
                print(f"\n{Fore.RED}❌ Δεν βρέθηκαν έγκυρα διαπιστευτήρια.{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def run_vulnerability_scanner(self):
            print(f"\n{Fore.CYAN}🛡️ ΕΡΓΑΛΕΙΟ ΣΚΑΝΙΣΜΑΤΟΣ ΕΥΠΑΘΕΙΩΝ{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}ΣΗΜΕΙΩΣΗ: Αυτό είναι ένα βασικό εργαλείο ελέγχου ασφαλείας.{Style.RESET_ALL}")
            
            target = input(f"{Fore.WHITE}Εισάγετε URL ή IP για έλεγχο ευπάθειας: {Style.RESET_ALL}").strip()
            if not target: return
            
            # Προσθήκη προθέματος http:// αν λείπει
            if not target.startswith(('http://', 'https://')):
                target = 'http://' + target
            
            print(f"\n[*] Έναρξη σάρωσης ευπάθειας για {target}...")
            vulnerabilities = []
            
            try:
                # 1. Έλεγχος για κοινές ευάλωτες θύρες
                common_vuln_ports = [21, 22, 23, 80, 443, 8080, 8443]
                for port in common_vuln_ports:
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                            sock.settimeout(2)
                            if sock.connect_ex((urlparse(target).hostname, port)) == 0:
                                vulnerabilities.append((port, f"Θύρα {port} είναι ανοιχτή", "ΜΕΣΑΙΟ"))
                    except:
                        pass
                
                # 2. Έλεγχος HTTP Security Headers
                if REQUESTS_AVAILABLE:
                    try:
                        response = requests.get(target, timeout=10, verify=False)
                        headers = response.headers
                        
                        security_headers = {
                            'Strict-Transport-Security': 'Μη ρυθμισμένο HSTS',
                            'Content-Security-Policy': 'Μη ρυθμισμένο CSP', 
                            'X-Frame-Options': 'Μη ρυθμισμένο X-Frame-Options',
                            'X-Content-Type-Options': 'Μη ρυθμισμένο X-Content-Type-Options'
                        }
                        
                        for header, desc in security_headers.items():
                            if header not in headers:
                                vulnerabilities.append((header, desc, "ΧΑΜΗΛΟ"))
                    except:
                        pass
                
                # 3. Έλεγχος για πιθανές ευπάθειες πληροφοριών
                info_leak_paths = ['/.git/', '/.env', '/backup/', '/admin/', '/phpinfo.php']
                for path in info_leak_paths:
                    try:
                        test_url = target.rstrip('/') + path
                        response = requests.get(test_url, timeout=5, verify=False)
                        if response.status_code == 200:
                            vulnerabilities.append((path, f"Πιθανή διαρροή πληροφοριών σε {path}", "ΜΕΣΑΙΟ"))
                    except:
                        pass
                        
            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα κατά τη σάρωση: {e}{Style.RESET_ALL}")
            
            # Εμφάνιση αποτελεσμάτων
            if vulnerabilities:
                print(f"\n{Fore.RED}🚨 ΒΡΕΘΗΚΑΝ ΕΥΠΑΘΕΙΕΣ:{Style.RESET_ALL}")
                for vuln in vulnerabilities:
                    color = Fore.RED if vuln[2] == "ΥΨΗΛΟ" else Fore.YELLOW if vuln[2] == "ΜΕΣΑΙΟ" else Fore.WHITE
                    print(f"  {color}• {vuln[0]}: {vuln[1]} [{vuln[2]}]{Style.RESET_ALL}")
                    self.record_audit_finding(target, 'Σάρωση Ευπάθειας', vuln[1], f'Βρέθηκε ευπάθεια: {vuln[0]} - {vuln[1]}', vuln[2])
            else:
                print(f"\n{Fore.GREEN}✅ Δεν βρέθηκαν προφανείς ευπάθειες.{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        # --- Εργαλεία Παρακολούθησης & Καταγραφής (Χωρίς Root) ---
        def view_audit_logs(self):
            print(f"\n{Fore.CYAN}📋 ΠΡΟΒΟΛΗ ΑΠΟΤΕΛΕΣΜΑΤΩΝ ΕΛΕΓΧΩΝ ΑΣΦΑΛΕΙΑΣ{Style.RESET_ALL}")
            
            try:
                with sqlite3.connect(self.audit_db_name) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT id, timestamp, target, audit_type, finding_title, severity 
                        FROM audit_results ORDER BY timestamp DESC LIMIT 50
                    ''')
                    results = cursor.fetchall()
                    
                    if not results:
                        print(f"{Fore.YELLOW}Δεν υπάρχουν καταγεγραμμένα αποτελέσματα ελέγχων ακόμη.{Style.RESET_ALL}")
                        input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                        return
                    
                    print(f"\n{Fore.GREEN}📊 Τελευταία {len(results)} Αποτελέσματα Ελέγχων:{Style.RESET_ALL}")
                    print("="*100)
                    print(f"{'Ημερομηνία':<20} {'Στόχος':<25} {'Τύπος':<15} {'Εύρημα':<25} {'Βαρύτητα':<10}")
                    print("-"*100)
                    
                    for row in results:
                        id, timestamp, target, audit_type, title, severity = row
                        # Περικοπή μεγάλων πεδίων για ευανάγνωστη εμφάνιση
                        target_disp = (target[:22] + '...') if len(target) > 25 else target
                        title_disp = (title[:22] + '...') if len(title) > 25 else title
                        audit_type_disp = (audit_type[:12] + '...') if len(audit_type) > 15 else audit_type
                        
                        # Χρώμα βάσει βαρύτητας
                        severity_color = Fore.RED if severity == 'ΥΨΗΛΟ' else Fore.YELLOW if severity == 'ΜΕΣΑΙΟ' else Fore.GREEN
                        
                        print(f"{timestamp[:19]:<20} {target_disp:<25} {audit_type_disp:<15} {title_disp:<25} {severity_color}{severity:<10}{Style.RESET_ALL}")
                    
                    print("="*100)
                    
                    # Επιλογή λεπτομερειών
                    choice = input(f"\n{Fore.WHITE}Εισάγετε ID ευρήματος για λεπτομέρειες (ή Enter για έξοδο): {Style.RESET_ALL}").strip()
                    if choice and choice.isdigit():
                        cursor.execute('SELECT * FROM audit_results WHERE id = ?', (int(choice),))
                        detail = cursor.fetchone()
                        if detail:
                            print(f"\n{Fore.CYAN}📄 ΛΕΠΤΟΜΕΡΕΙΕΣ ΕΥΡΗΜΑΤΟΣ ID {detail[0]}:{Style.RESET_ALL}")
                            print("="*60)
                            print(f"  Στόχος: {detail[1]}")
                            print(f"  Τύπος Ελέγχου: {detail[2]}")
                            print(f"  Τίτλος Ευρήματος: {detail[3]}")
                            print(f"  Περιγραφή: {detail[4]}")
                            print(f"  Βαρύτητα: {detail[5]}")
                            print(f"  Χρονική σήμανση: {detail[6]}")
                            print("="*60)
            
            except sqlite3.Error as e:
                print(f"{Fore.RED}❌ Σφάλμα πρόσβασης βάσης δεδομένων: {e}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def export_audit_logs(self):
            print(f"\n{Fore.CYAN}💾 ΕΞΑΓΩΓΗ ΑΠΟΤΕΛΕΣΜΑΤΩΝ ΕΛΕΓΧΩΝ{Style.RESET_ALL}")
            
            export_file = os.path.join(self.save_dir, f"audit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            
            try:
                with sqlite3.connect(self.audit_db_name) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM audit_results ORDER BY timestamp DESC')
                    results = cursor.fetchall()
                    
                    if not results:
                        print(f"{Fore.YELLOW}Δεν υπάρχουν δεδομένα για εξαγωγή.{Style.RESET_ALL}")
                        input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                        return
                    
                    # Εγγραφή CSV
                    with open(export_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(['ID', 'Στόχος', 'Τύπος Ελέγχου', 'Τίτλος Ευρήματος', 'Περιγραφή', 'Βαρύτητα', 'Χρονική Σήμανση'])
                        writer.writerows(results)
                    
                    print(f"{Fore.GREEN}✅ Τα αποτελέσματα εξήχθησαν επιτυχώς στο: {export_file}{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}📊 Συνολικές εγγραφές: {len(results)}{Style.RESET_ALL}")
                    
            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα εξαγωγής: {e}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def clear_audit_logs(self):
            print(f"\n{Fore.CYAN}🗑️ ΕΚΚΑΘΑΡΙΣΗ ΑΠΟΤΕΛΕΣΜΑΤΩΝ ΕΛΕΓΧΩΝ{Style.RESET_ALL}")
            
            confirm = input(f"{Fore.RED}⚠️ Είστε σίγουρος ότι θέλετε να διαγράψετε όλα τα αποτελέσματα ελέγχων; (ν/ο): {Style.RESET_ALL}").strip().lower()
            
            if confirm == 'ν':
                try:
                    with sqlite3.connect(self.audit_db_name) as conn:
                        cursor = conn.cursor()
                        cursor.execute('DELETE FROM audit_results')
                        conn.commit()
                    print(f"{Fore.GREEN}✅ Τα αποτελέσματα ελέγχων διαγράφηκαν.{Style.RESET_ALL}")
                except sqlite3.Error as e:
                    print(f"{Fore.RED}❌ Σφάλμα κατά τη διαγραφή: {e}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Η εκκαθάριση ακυρώθηκε.{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def view_wifi_history(self):
            print(f"\n{Fore.CYAN}📶 ΙΣΤΟΡΙΚΟ ΣΑΡΩΣΕΩΝ WI-FI{Style.RESET_ALL}")
            
            try:
                with sqlite3.connect(self.wifi_db_name) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT bssid, ssid, signal_strength, channel, encryption, 
                               first_seen, last_seen, is_trusted 
                        FROM network_scans 
                        ORDER BY last_seen DESC LIMIT 50
                    ''')
                    networks = cursor.fetchall()
                    
                    if not networks:
                        print(f"{Fore.YELLOW}Δεν υπάρχουν καταγεγραμμένα δίκτυα Wi-Fi.{Style.RESET_ALL}")
                        input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                        return
                    
                    print(f"\n{Fore.GREEN}🌐 Τελευταία {len(networks)} Καταγεγραμμένα Δίκτυα:{Style.RESET_ALL}")
                    print("="*120)
                    print(f"{'SSID':<25} {'BSSID':<20} {'Σήμα':<8} {'Κανάλι':<8} {'Κρυπτογρ.':<12} {'Τελευταία Εμφ.':<20} {'Εμπιστοσύνη':<12}")
                    print("-"*120)
                    
                    for net in networks:
                        bssid, ssid, signal, channel, encryption, first_seen, last_seen, trusted = net
                        
                        ssid_disp = (ssid[:22] + '...') if ssid and len(ssid) > 25 else (ssid or 'Κρυφό')
                        bssid_disp = bssid[:17] + '...' if len(bssid) > 20 else bssid
                        signal_disp = f"{signal} dBm" if signal else "Δ/Υ"
                        channel_disp = str(channel) if channel else "Δ/Υ"
                        encryption_disp = (encryption[:10] + '...') if encryption and len(encryption) > 12 else (encryption or 'Δ/Υ')
                        last_seen_disp = last_seen[:19] if last_seen else "Δ/Υ"
                        trust_disp = f"{Fore.GREEN}Εμπιστο{Style.RESET_ALL}" if trusted else f"{Fore.YELLOW}Άγνωστο{Style.RESET_ALL}"
                        
                        print(f"{ssid_disp:<25} {bssid_disp:<20} {signal_disp:<8} {channel_disp:<8} {encryption_disp:<12} {last_seen_disp:<20} {trust_disp:<12}")
                    
                    print("="*120)
                    
            except sqlite3.Error as e:
                print(f"{Fore.RED}❌ Σφάλμα πρόσβασης βάσης δεδομένων: {e}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def manage_trusted_networks(self):
            print(f"\n{Fore.CYAN}🔐 ΔΙΑΧΕΙΡΙΣΗ ΕΜΠΙΣΤΩΝ ΔΙΚΤΥΩΝ{Style.RESET_ALL}")
            
            while True:
                print(f"\n{Fore.CYAN}Τρέχοντα Εμπιστα Δίκτυα ({len(self.trusted_bssids)}):{Style.RESET_ALL}")
                if self.trusted_bssids:
                    for bssid in list(self.trusted_bssids)[:10]:  # Εμφάνιση μόνο των πρώτων 10
                        print(f"  - {bssid}")
                    if len(self.trusted_bssids) > 10:
                        print(f"  ... και {len(self.trusted_bssids) - 10} ακόμη")
                else:
                    print(f"  {Fore.YELLOW}Δεν υπάρχουν εμπιστα δίκτυα{Style.RESET_ALL}")
                
                print(f"\n{Fore.CYAN}Επιλογές:{Style.RESET_ALL}")
                print("  1. Προσθήκη BSSID στα εμπιστα")
                print("  2. Αφαίρεση BSSID από τα εμπιστα") 
                print("  3. Εξαγωγή λίστας εμπίστων δικτύων")
                print("  4. Επαναφορά προεπιλεγμένων")
                print("  5. Επιστροφή")
                
                choice = input(f"\n{Fore.WHITE}Επιλέξτε ενέργεια (1-5): {Style.RESET_ALL}").strip()
                
                if choice == '1':
                    bssid = input(f"{Fore.WHITE}Εισάγετε BSSID για προσθήκη: {Style.RESET_ALL}").strip().upper()
                    if bssid:
                        self.trusted_bssids.add(bssid)
                        self.known_networks['trusted_bssids'] = list(self.trusted_bssids)
                        self.save_known_networks()
                        print(f"{Fore.GREEN}✅ Το BSSID προστέθηκε στα εμπιστα{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}❌ Μη έγκυρο BSSID{Style.RESET_ALL}")
                        
                elif choice == '2':
                    bssid = input(f"{Fore.WHITE}Εισάγετε BSSID για αφαίρεση: {Style.RESET_ALL}").strip().upper()
                    if bssid in self.trusted_bssids:
                        self.trusted_bssids.remove(bssid)
                        self.known_networks['trusted_bssids'] = list(self.trusted_bssids)
                        self.save_known_networks()
                        print(f"{Fore.GREEN}✅ Το BSSID αφαιρέθηκε από τα εμπιστα{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}❌ Το BSSID δεν βρέθηκε στη λίστα{Style.RESET_ALL}")
                        
                elif choice == '3':
                    export_file = os.path.join(self.save_dir, f"trusted_networks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                    try:
                        with open(export_file, 'w') as f:
                            for bssid in self.trusted_bssids:
                                f.write(bssid + '\n')
                        print(f"{Fore.GREEN}✅ Η λίστα εξήχθη στο: {export_file}{Style.RESET_ALL}")
                    except Exception as e:
                        print(f"{Fore.RED}❌ Σφάλμα εξαγωγής: {e}{Style.RESET_ALL}")
                        
                elif choice == '4':
                    confirm = input(f"{Fore.RED}⚠️ Επαναφορά προεπιλεγμένων ρυθμίσεων; (ν/ο): {Style.RESET_ALL}").strip().lower()
                    if confirm == 'ν':
                        self.trusted_bssids = set()
                        self.known_networks = {
                            "trusted_bssids": [], 
                            "trusted_ssids": ["Home", "Work"],
                            "suspicious_ssids": ["Free WiFi", "Public WiFi"]
                        }
                        self.save_known_networks()
                        print(f"{Fore.GREEN}✅ Οι ρυθμίσεις επαναφέρθηκαν{Style.RESET_ALL}")
                        
                elif choice == '5':
                    break
                else:
                    print(f"{Fore.RED}❌ Μη έγκυρη επιλογή{Style.RESET_ALL}")

        # --- Ρυθμίσεις & Βελτιστοποιήσεις (Χωρίς Root) ---
        def configure_tools(self):
            print(f"\n{Fore.CYAN}⚙️ ΡΥΘΜΙΣΕΙΣ ΕΡΓΑΛΕΙΩΝ{Style.RESET_ALL}")
            
            while True:
                print(f"\n{Fore.CYAN}Τρέχουσες Ρυθμίσεις:{Style.RESET_ALL}")
                print(f"  1. Νήματα Σάρωσης: {self.config.get('max_scan_workers', 15)}")
                print(f"  2. Χρονικό Όριο Σάρωσης: {self.config.get('scan_timeout', 1)} δευτερόλεπτα")
                print(f"  3. Κορυφαίες Θύρες: {self.config.get('top_ports', '21,22,23,25,53,80,110,143,443,445,993,995,1723,3306,3389,5900,8080')}")
                print(f"  4. Κοινά Ονόματα Χρήστη: {self.config.get('common_usernames', 'admin,root,user,administrator,test,guest')}")
                print(f"  5. Κοινοί Κωδικοί Πρόσβασης: {self.config.get('common_passwords', 'admin,123456,password,1234,12345,123456789,letmein,1234567,123,abc123')}")
                print(f"  6. Ειδοποίηση για Νέα Δίκτυα: {'Ναι' if self.config.get('alert_on_new_network', True) else 'Όχι'}")
                print(f"  7. Διακομιστής Δοκιμής DNS: {self.config.get('dns_test_server', 'https://ipleak.net/json/')}")
                print(f"  8. Επιστροφή")
                
                choice = input(f"\n{Fore.WHITE}Επιλέξτε ρύθμιση για αλλαγή (1-8): {Style.RESET_ALL}").strip()
                
                if choice == '1':
                    try:
                        new_value = int(input(f"{Fore.WHITE}Νέα τιμή για νήματα σάρωσης [15]: {Style.RESET_ALL}").strip() or "15")
                        if 1 <= new_value <= 100:
                            self.config['max_scan_workers'] = new_value
                            self.max_workers = new_value
                            self.save_config()
                            print(f"{Fore.GREEN}✅ Τα νήματα σάρωσης ορίστηκαν σε: {new_value}{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.RED}❌ Η τιμή πρέπει να είναι μεταξύ 1 και 100{Style.RESET_ALL}")
                    except ValueError:
                        print(f"{Fore.RED}❌ Μη έγκυρος αριθμός{Style.RESET_ALL}")
                        
                elif choice == '2':
                    try:
                        new_value = float(input(f"{Fore.WHITE}Νέο χρονικό όριο σάρωσης [1.0]: {Style.RESET_ALL}").strip() or "1.0")
                        if 0.1 <= new_value <= 10.0:
                            self.config['scan_timeout'] = new_value
                            self.scan_timeout = new_value
                            self.save_config()
                            print(f"{Fore.GREEN}✅ Το χρονικό όριο σάρωσης ορίστηκε σε: {new_value}{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.RED}❌ Η τιμή πρέπει να είναι μεταξύ 0.1 και 10.0{Style.RESET_ALL}")
                    except ValueError:
                        print(f"{Fore.RED}❌ Μη έγκυρος αριθμός{Style.RESET_ALL}")
                        
                elif choice == '3':
                    new_ports = input(f"{Fore.WHITE}Νέες κορυφαίες θύρες (διαχωρισμός με κόμμα): {Style.RESET_ALL}").strip()
                    if new_ports:
                        try:
                            # Επικύρωση ότι είναι αριθμοί
                            ports = [int(p.strip()) for p in new_ports.split(',')]
                            if all(1 <= p <= 65535 for p in ports):
                                self.config['top_ports'] = new_ports
                                self.save_config()
                                print(f"{Fore.GREEN}✅ Οι κορυφαίες θύρες ενημερώθηκαν{Style.RESET_ALL}")
                            else:
                                print(f"{Fore.RED}❌ Οι θύρες πρέπει να είναι μεταξύ 1 και 65535{Style.RESET_ALL}")
                        except ValueError:
                            print(f"{Fore.RED}❌ Μη έγκυρη μορφή θυρών{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}❌ Δεν εισήχθησαν θύρες{Style.RESET_ALL}")
                        
                elif choice == '4':
                    new_usernames = input(f"{Fore.WHITE}Νέα ονόματα χρήστη (διαχωρισμός με κόμμα): {Style.RESET_ALL}").strip()
                    if new_usernames:
                        self.config['common_usernames'] = new_usernames
                        self.save_config()
                        print(f"{Fore.GREEN}✅ Τα ονόματα χρήστη ενημερώθηκαν{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}❌ Δεν εισήχθησαν ονόματα χρήστη{Style.RESET_ALL}")
                        
                elif choice == '5':
                    new_passwords = input(f"{Fore.WHITE}Νέοι κωδικοί πρόσβασης (διαχωρισμός με κόμμα): {Style.RESET_ALL}").strip()
                    if new_passwords:
                        self.config['common_passwords'] = new_passwords
                        self.save_config()
                        print(f"{Fore.GREEN}✅ Οι κωδικοί πρόσβασης ενημερώθηκαν{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}❌ Δεν εισήχθησαν κωδικοί πρόσβασης{Style.RESET_ALL}")
                        
                elif choice == '6':
                    current = self.config.get('alert_on_new_network', True)
                    new_value = not current
                    self.config['alert_on_new_network'] = new_value
                    self.save_config()
                    status = "ενεργοποιημένες" if new_value else "απενεργοποιημένες"
                    print(f"{Fore.GREEN}✅ Οι ειδοποιήσεις για νέα δίκτυα είναι τώρα {status}{Style.RESET_ALL}")
                    
                elif choice == '7':
                    new_server = input(f"{Fore.WHITE}Νέος διακομιστής δοκιμής DNS: {Style.RESET_ALL}").strip()
                    if new_server:
                        self.config['dns_test_server'] = new_server
                        self.save_config()
                        print(f"{Fore.GREEN}✅ Ο διακομιστής DNS ενημερώθηκε{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}❌ Δεν εισήχθη διακομιστής{Style.RESET_ALL}")
                        
                elif choice == '8':
                    break
                else:
                    print(f"{Fore.RED}❌ Μη έγκυρη επιλογή{Style.RESET_ALL}")

        def system_info(self):
            print(f"\n{Fore.CYAN}🖥️ ΠΛΗΡΟΦΟΡΙΕΣ ΣΥΣΤΗΜΑΤΟΣ{Style.RESET_ALL}")
            print("="*50)
            
            # Πληροφορίες συστήματος
            try:
                import platform
                system = platform.system()
                release = platform.release()
                version = platform.version()
                machine = platform.machine()
                processor = platform.processor()
                
                print(f"{Fore.GREEN}Σύστημα:{Style.RESET_ALL}")
                print(f"  OS: {system} {release}")
                print(f"  Έκδοση: {version}")
                print(f"  Αρχιτεκτονική: {machine}")
                if processor and processor != '': print(f"  Επεξεργαστής: {processor}")
            except:
                print(f"{Fore.RED}  Δεν ήταν δυνατή η ανάκτηση πληροφοριών συστήματος{Style.RESET_ALL}")
            
            # Πληροφορίες Python
            print(f"\n{Fore.GREEN}Python:{Style.RESET_ALL}")
            print(f"  Έκδοση: {sys.version.split()[0]}")
            print(f"  Διαδρομή: {sys.executable}")
            
            # Πληροφορίες δικτύου
            print(f"\n{Fore.GREEN}Δίκτυο:{Style.RESET_ALL}")
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                print(f"  Τοπική IP: {local_ip}")
            except:
                print(f"  Τοπική IP: Δ/Υ")
            
            # Κατάσταση εξαρτήσεων
            print(f"\n{Fore.GREEN}Εξαρτήσεις:{Style.RESET_ALL}")
            deps = [
                ('colorama', COLORS_AVAILABLE),
                ('speedtest-cli', SPEEDTEST_AVAILABLE),
                ('requests', REQUESTS_AVAILABLE),
                ('beautifulsoup4', BS4_AVAILABLE),
                ('paramiko', PARAMIKO_AVAILABLE),
                ('python-whois', WHOIS_AVAILABLE),
                ('dnspython', DNS_AVAILABLE),
                ('curses', CURSES_AVAILABLE)
            ]
            
            for dep, available in deps:
                status = f"{Fore.GREEN}✅{Style.RESET_ALL}" if available else f"{Fore.RED}❌{Style.RESET_ALL}"
                print(f"  {dep:<15} {status}")
            
            # Πληροφορίες αποθηκευτικού χώρου
            print(f"\n{Fore.GREEN}Αποθηκευτικός Χώρος:{Style.RESET_ALL}")
            try:
                total, used, free = shutil.disk_usage(self.save_dir)
                print(f"  Σύνολο: {total // (2**30)} GB")
                print(f"  Χρησιμοποιημένο: {used // (2**30)} GB")
                print(f"  Ελεύθερο: {free // (2**30)} GB")
                print(f"  Αποθετήριο: {self.save_dir}")
            except:
                print(f"  Δεν ήταν δυνατή η ανάκτηση πληροφοριών δίσκου")
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

        def run_ssh_defender(self):
            """Εκκίνηση του SSH Defender Honeypot."""
            print(f"\n{Fore.CYAN}🛡️ ΕΚΚΙΝΗΣΗ SSH DEFENDER HONEYPOT{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}ΣΗΜΕΙΩΣΗ: Αυτό το εργαλείο δημιουργεί ένα honeypot SSH για καταγραφή επιθέσεων.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}       Χρησιμοποιήστε το ΜΟΝΟ για εκπαιδευτικούς σκοπούς και σε δίκτυα που σας ανήκουν.{Style.RESET_ALL}")
            
            # Ρύθμιση διαδρομών αποθήκευσης
            base_defender_dir = os.path.join(self.save_dir, "SSH_Defender")
            log_dir = os.path.join(base_defender_dir, "logs")
            stats_file = os.path.join(base_defender_dir, "attack_stats.json")
            os.makedirs(log_dir, exist_ok=True)
            
            # Ερώτηση για λειτουργία
            print(f"\n{Fore.CYAN}Επιλογές Λειτουργίας:{Style.RESET_ALL}")
            print("1. Κυκλική Εναλλαγή Θυρών (Αυτόματη εναλλαγή σε γνωστές θύρες)")
            print("2. Μία Θύρα (Παρακολούθηση μίας συγκεκριμένης θύρας)")
            print("3. Τερματισμός Όλων των Τρεχόντων Honeypots")
            
            mode_choice = input(f"\n{Fore.WHITE}Επιλέξτε λειτουργία (1-3): {Style.RESET_ALL}").strip()
            
            # Αρχικοποίηση components
            logger = Logger(log_dir, stats_file)
            executor = ThreadPoolExecutor(max_workers=50)
            defender = SSHDefender(HOST, logger, executor)
            
            if mode_choice == '1':
                print(f"\n{Fore.GREEN}🚀 Εκκίνηση SSH Defender σε λειτουργία Κυκλικής Εναλλαγής...{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Θύρες που θα παρακολουθηθούν: {', '.join(map(str, FAMOUS_SSH_PORTS))}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Καταγραφές: {log_dir}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Στατιστικά: {stats_file}{Style.RESET_ALL}")
                
                input(f"\n{Fore.YELLOW}Πατήστε Enter για έναρξη παρακολούθησης...{Style.RESET_ALL}")
                
                # Εκκίνηση κυκλικής εναλλαγής
                defender.run_port_cycle()
                
            elif mode_choice == '2':
                try:
                    port = int(input(f"{Fore.WHITE}Εισάγετε θύρα παρακολούθησης [22]: {Style.RESET_ALL}").strip() or "22")
                except ValueError:
                    port = 22
                    
                print(f"\n{Fore.GREEN}🚀 Εκκίνηση SSH Defender στη θύρα {port}...{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Καταγραφές: {log_dir}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Στατιστικά: {stats_file}{Style.RESET_ALL}")
                
                input(f"\n{Fore.YELLOW}Πατήστε Enter για έναρξη παρακολούθησης...{Style.RESET_ALL}")
                
                # Εκκίνηση παρακολούθησης μίας θύρας με TUI
                defender.start_port_listener(port)
                if defender.running:
                    # Εκκίνηση TUI
                    if CURSES_AVAILABLE:
                        try:
                            curses.wrapper(lambda stdscr: DefenderTUI(stdscr, defender).run())
                        except KeyboardInterrupt:
                            print(f"\n{Fore.YELLOW}Λήψη σήματος διακοπής...{Style.RESET_ALL}")
                        except Exception as e:
                            print(f"\n{Fore.RED}Σφάλμα TUI: {e}{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}❌ Το TUI δεν είναι διαθέσιμο. Χρήση βασικής λειτουργίας.{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}Πατήστε Ctrl+C για τερματισμό...{Style.RESET_ALL}")
                        try:
                            while defender.running:
                                time.sleep(1)
                        except KeyboardInterrupt:
                            print(f"\n{Fore.YELLOW}Λήψη σήματος διακοπής...{Style.RESET_ALL}")
                    
                    defender.stop_all_ports()
                else:
                    print(f"{Fore.RED}❌ Αποτυχία εκκίνησης ακροατή.{Style.RESET_ALL}")
                    
            elif mode_choice == '3':
                print(f"\n{Fore.YELLOW}Τερματισμός τυχόν τρεχόντων honeypots...{Style.RESET_ALL}")
                defender.stop_all_ports()
                print(f"{Fore.GREEN}✅ Ολοκληρώθηκε ο τερματισμός.{Style.RESET_ALL}")
                
            else:
                print(f"{Fore.RED}❌ Μη έγκυρη επιλογή.{Style.RESET_ALL}")
                return
            
            # Τελική αποθήκευση στατιστικών
            logger.save_stats()
            print(f"\n{Fore.GREEN}✅ Το SSH Defender τερμάτισε.{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📊 Τελικά Στατιστικά:{Style.RESET_ALL}")
            stats_summary = logger.get_cumulative_stats_summary()
            print(f"  Συνολικές Επιθέσεις: {stats_summary['Συνολικές Επιθέσεις']}")
            print(f"  Κορυφαίες IP: {', '.join(stats_summary['Κορυφαίες IP Επιτιθέμενων'][:3])}")
            print(f"  Κορυφαίες Θύρες: {', '.join(stats_summary['Κορυφαίες Θύρες Στόχοι'][:3])}")
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για επιστροφή στο κύριο μενού...{Style.RESET_ALL}")

        def display_main_menu(self):
            """Εμφάνιση του κύριου μενού με χρήση curses ή fallback σε απλό μενού."""
            if not CURSES_AVAILABLE:
                return self._display_fallback_menu()
            
            try:
                # Χρήση curses για TUI
                menu_choice = curses.wrapper(self._curses_main_menu)
                return menu_choice
            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα TUI: {e}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Πτώση σε απλό μενού...{Style.RESET_ALL}")
                return self._display_fallback_menu()

        def _curses_main_menu(self, stdscr):
            """Curses TUI για το κύριο μενού."""
            _reset_curses_state(stdscr)
            
            menu_title = "ΠΡΟΧΩΡΗΜΕΝΑ ΔΙΚΤΥΑΚΑ ΕΡΓΑΛΕΙΑ"
            menu_subtitle = "Βελτιστοποιημένο για Termux & Συσκευές με Περιορισμένους Πόρους"
            
            menu_options = [
                "--- ΕΡΓΑΛΕΙΑ WI-FI & ΚΙΝΗΤΗΣ ---",
                "1. Σάρωση Wi-Fi (Παθητική)",
                "2. Προβολή Τρέχουσας Σύνδεσης", 
                "3. Ενεργοποίηση/Απενεργοποίηση Wi-Fi",
                "4. Πληροφορίες Κινητής Σύνδεσης & SIM",
                "",
                "--- ΣΑΡΩΣΕΙΣ ΔΙΚΤΥΟΥ & ΑΝΑΚΑΛΥΨΗ ---",
                "5. Σαρωτής Nmap Wrapper",
                "6. Βελτιωμένος Σαρωτής Θυρών",
                "7. Ανακάλυψη Δικτύου",
                "8. Υπολογιστής Υποδικτύου",
                "",
                "--- ΔΙΑΔΙΚΤΥΟ & ΔΙΑΓΝΩΣΤΙΚΑ ---", 
                "9. Δοκιμή Ταχύτητας Διαδικτύου",
                "10. Πληροφορίες Εξωτερικής IP",
                "11. Διαγνωστικά Δικτύου (Ping/Traceroute)",
                "",
                "--- ΣΥΛΛΟΓΗ ΠΛΗΡΟΦΟΡΙΩΝ (OSINT) ---",
                "12. Σαρωτής OSINTDS (Προηγμένος)",
                "13. Αναζήτηση WHOIS",
                "14. Αναζήτηση Πληροφοριών DNS",
                "",
                "--- ΕΡΓΑΛΕΙΑ ΑΣΦΑΛΕΙΑΣ ---",
                "15. SSH Defender Honeypot",
                "16. Brute Force SSH (Δοκιμές Πιστοποίησης)",
                "17. Σάρωση Ευπάθειας",
                "",
                "--- ΠΑΡΑΚΟΛΟΥΘΗΣΗ & ΚΑΤΑΓΡΑΦΕΣ ---", 
                "18. Προβολή Αποτελεσμάτων Ελέγχων",
                "19. Εξαγωγή Αποτελεσμάτων Ελέγχων",
                "20. Εκκαθάριση Αποτελεσμάτων Ελέγχων", 
                "21. Ιστορικό Σαρώσεων Wi-Fi",
                "22. Διαχείριση Εμπίστων Δικτύων",
                "",
                "--- ΡΥΘΜΙΣΕΙΣ & ΒΕΛΤΙΩΣΕΙΣ ---",
                "23. Ρύθμιση Εργαλείων",
                "24. Πληροφορίες Συστήματος",
                "25. Αυτόματη Εγκατάσταση Εξαρτήσεων",
                "",
                "26. Έξοδος"
            ]
            
            return _draw_curses_menu(stdscr, menu_title, menu_options)

        def _display_fallback_menu(self):
            """Απλό μενού fallback χωρίς curses."""
            print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'ΠΡΟΧΩΡΗΜΕΝΑ ΔΙΚΤΥΑΚΑ ΕΡΓΑΛΕΙΑ':^70}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{'Βελτιστοποιημένο για Termux & Συσκευές με Περιορισμένους Πόρους':^70}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
            
            print(f"\n{Fore.CYAN}--- ΕΡΓΑΛΕΙΑ WI-FI & ΚΙΝΗΤΗΣ ---{Style.RESET_ALL}")
            print(" 1. Σάρωση Wi-Fi (Παθητική)")
            print(" 2. Προβολή Τρέχουσας Σύνδεσης")
            print(" 3. Ενεργοποίηση/Απενεργοποίηση Wi-Fi") 
            print(" 4. Πληροφορίες Κινητής Σύνδεσης & SIM")
            
            print(f"\n{Fore.CYAN}--- ΣΑΡΩΣΕΙΣ ΔΙΚΤΥΟΥ & ΑΝΑΚΑΛΥΨΗ ---{Style.RESET_ALL}")
            print(" 5. Σαρωτής Nmap Wrapper")
            print(" 6. Βελτιωμένος Σαρωτής Θυρών")
            print(" 7. Ανακάλυψη Δικτύου")
            print(" 8. Υπολογιστής Υποδικτύου")
            
            print(f"\n{Fore.CYAN}--- ΔΙΑΔΙΚΤΥΟ & ΔΙΑΓΝΩΣΤΙΚΑ ---{Style.RESET_ALL}")
            print(" 9. Δοκιμή Ταχύτητας Διαδικτύου")
            print("10. Πληροφορίες Εξωτερικής IP")
            print("11. Διαγνωστικά Δικτύου (Ping/Traceroute)")
            
            print(f"\n{Fore.CYAN}--- ΣΥΛΛΟΓΗ ΠΛΗΡΟΦΟΡΙΩΝ (OSINT) ---{Style.RESET_ALL}")
            print("12. Σαρωτής OSINTDS (Προηγμένος)")
            print("13. Αναζήτηση WHOIS") 
            print("14. Αναζήτηση Πληροφοριών DNS")
            
            print(f"\n{Fore.CYAN}--- ΕΡΓΑΛΕΙΑ ΑΣΦΑΛΕΙΑΣ ---{Style.RESET_ALL}")
            print("15. SSH Defender Honeypot")
            print("16. Brute Force SSH (Δοκιμές Πιστοποίησης)")
            print("17. Σάρωση Ευπάθειας")
            
            print(f"\n{Fore.CYAN}--- ΠΑΡΑΚΟΛΟΥΘΗΣΗ & ΚΑΤΑΓΡΑΦΕΣ ---{Style.RESET_ALL}")
            print("18. Προβολή Αποτελεσμάτων Ελέγχων")
            print("19. Εξαγωγή Αποτελεσμάτων Ελέγχων")
            print("20. Εκκαθάριση Αποτελεσμάτων Ελέγχων")
            print("21. Ιστορικό Σαρώσεων Wi-Fi")
            print("22. Διαχείριση Εμπίστων Δικτύων")
            
            print(f"\n{Fore.CYAN}--- ΡΥΘΜΙΣΕΙΣ & ΒΕΛΤΙΩΣΕΙΣ ---{Style.RESET_ALL}")
            print("23. Ρύθμιση Εργαλείων")
            print("24. Πληροφορίες Συστήματος")
            print("25. Αυτόματη Εγκατάσταση Εξαρτήσεων")
            
            print(f"\n{Fore.CYAN}--- ΕΞΟΔΟΣ ---{Style.RESET_ALL}")
            print("26. Έξοδος")
            print(f"{Fore.CYAN}{'-'*70}{Style.RESET_ALL}")
            
            try:
                choice = int(input(f"\n{Fore.WHITE}Επιλέξτε ενέργεια (1-26): {Style.RESET_ALL}").strip())
                return choice - 1  # Για συμβατότητα με το index του curses menu
            except ValueError:
                return -1

    # --- Αρχικοποίηση και Κύριος Βρόχος ---
    def main():
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'ΠΡΟΧΩΡΗΜΕΝΑ ΔΙΚΤΥΑΚΑ ΕΡΓΑΛΕΙΑ':^70}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'Βελτιστοποιημένο για Termux & Συσκευές με Περιορισμένους Πόρους':^70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        
        # Έλεγχος για Termux
        is_termux = os.path.exists('/data/data/com.termux')
        if is_termux:
            print(f"{Fore.GREEN}✅ Εντοπίστηκε Termux Environment{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠️  Δεν εντοπίστηκε Termux. Ορισμένες λειτουργίες μπορεί να μην λειτουργούν.{Style.RESET_ALL}")
        
        # Έλεγχος εξαρτήσεων
        if not CURSES_AVAILABLE:
            print(f"{Fore.RED}⚠️  Προειδοποίηση: Το 'curses' δεν είναι διαθέσιμο. Θα χρησιμοποιηθεί απλό μενού.{Style.RESET_ALL}")
        
        # Αρχικοποίηση εργαλείων
        try:
            tools = AdvancedNetworkTools()
        except Exception as e:
            print(f"{Fore.RED}❌ Σφάλμα αρχικοποίησης: {e}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Παρακαλώ ελέγξτε τα δικαιώματα και τον αποθηκευτικό χώρο.{Style.RESET_ALL}")
            input(f"{Fore.YELLOW}Πατήστε Enter για έξοδο...{Style.RESET_ALL}")
            return
        
        # Κύριος βρόχος εφαρμογής
        while True:
            try:
                choice = tools.display_main_menu()
                
                if choice == 0:    # Σάρωση Wi-Fi
                    tools.single_wifi_scan()
                elif choice == 1:  # Προβολή Τρέχουσας Σύνδεσης
                    tools.view_current_connection()
                elif choice == 2:  # Ενεργοποίηση/Απενεργοποίηση Wi-Fi
                    tools.toggle_wifi()
                elif choice == 3:  # Πληροφορίες Κινητής Σύνδεσης & SIM
                    tools.get_mobile_data_info()
                elif choice == 4:  # Σαρωτής Nmap Wrapper
                    tools.nmap_wrapper()
                elif choice == 5:  # Βελτιωμένος Σαρωτής Θυρών
                    tools.enhanced_port_scanner()
                elif choice == 6:  # Ανακάλυψη Δικτύου
                    tools.network_discovery()
                elif choice == 7:  # Υπολογιστής Υποδικτύου
                    tools.subnet_calculator()
                elif choice == 8:  # Δοκιμή Ταχύτητας Διαδικτύου
                    tools.run_internet_speed_test()
                elif choice == 9:  # Πληροφορίες Εξωτερικής IP
                    tools.get_external_ip_info()
                elif choice == 10: # Διαγνωστικά Δικτύου
                    tools.run_network_diagnostics()
                elif choice == 11: # Σαρωτής OSINTDS
                    tools.run_osintds_scanner()
                elif choice == 12: # Αναζήτηση WHOIS
                    tools.get_whois_info()
                elif choice == 13: # Αναζήτηση Πληροφοριών DNS
                    tools.get_dns_info()
                elif choice == 14: # SSH Defender Honeypot
                    tools.run_ssh_defender()
                elif choice == 15: # Brute Force SSH
                    tools.run_ssh_brute_force()
                elif choice == 16: # Σάρωση Ευπάθειας
                    tools.run_vulnerability_scanner()
                elif choice == 17: # Προβολή Αποτελεσμάτων Ελέγχων
                    tools.view_audit_logs()
                elif choice == 18: # Εξαγωγή Αποτελεσμάτων Ελέγχων
                    tools.export_audit_logs()
                elif choice == 19: # Εκκαθάριση Αποτελεσμάτων Ελέγχων
                    tools.clear_audit_logs()
                elif choice == 20: # Ιστορικό Σαρώσεων Wi-Fi
                    tools.view_wifi_history()
                elif choice == 21: # Διαχείριση Εμπίστων Δικτύων
                    tools.manage_trusted_networks()
                elif choice == 22: # Ρύθμιση Εργαλείων
                    tools.configure_tools()
                elif choice == 23: # Πληροφορίες Συστήματος
                    tools.system_info()
                elif choice == 24: # Αυτόματη Εγκατάσταση Εξαρτήσεων
                    auto_install_dependencies()
                elif choice == 25: # Έξοδος
                    print(f"\n{Fore.GREEN}✅ Έξοδος από τα Προηγμένα Δικτυακά Εργαλεία. Αντίο!{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED}❌ Μη έγκυρη επιλογή. Παρακαλώ επιλέξτε από 1-26.{Style.RESET_ALL}")
                    input(f"{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")
                    
            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}Λήψη σήματος διακοπής...{Style.RESET_ALL}")
                confirm = input(f"{Fore.YELLOW}Είστε σίγουρος ότι θέλετε να τερματίσετε; (ν/ο): {Style.RESET_ALL}").strip().lower()
                if confirm == 'ν':
                    print(f"{Fore.GREEN}✅ Έξοδος...{Style.RESET_ALL}")
                    break
            except Exception as e:
                print(f"\n{Fore.RED}❌ Μη αναμενόμενο σφάλμα: {e}{Style.RESET_ALL}")
                import traceback
                traceback.print_exc()
                input(f"{Fore.YELLOW}Πατήστε Enter για συνέχεια...{Style.RESET_ALL}")

    if __name__ == "__main__":
        main()

# Εκτέλεση της εφαρμογής
if __name__ == "__main__":
    main_app_loop()