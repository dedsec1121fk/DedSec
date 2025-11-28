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
import hashlib
import random
import string
import struct
import select  # Προστέθηκε για το SSH Defender
import math    # Προστέθηκε για το SSH Defender
import queue
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor # Προστέθηκε για το SSH Defender
import html
import tempfile
import webbrowser
import shutil


# --- Εισαγωγές Εξαρτήσεων & Καθολικές Σημαίες ---
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
csv = None # Για την ενότητα OSINTDS

# 1. Colorama
try:
    from colorama import Fore, Style, Back, init
    init()
    COLORS_AVAILABLE = True
except ImportError:
    # Εφεδρική λύση αν το colorama δεν είναι εγκατεστημένο
    class DummyColor:
        def __getattr__(self, name): return ''
    Fore = Back = Style = DummyColor()

# 2. Δυναμικές προσπάθειες εισαγωγής για άλλες ενότητες
def _try_import(module_name, global_var_name):
    """Εισάγει δυναμικά μια ενότητα και ορίζει μια καθολική σημαία."""
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
_try_import('csv', 'csv') # Για την ενότητα OSINTDS


# ==============================================================================
# SSH DEFENDER - ΚΑΘΟΛΙΚΕΣ ΣΤΑΘΕΡΕΣ
# ==============================================================================

# Καταταγμένη λίστα γνωστών θυρών SSH/Honeypot για εναλλαγή
FAMOUS_SSH_PORTS = [
    22,    # Standard SSH
    2222,  # Common alternative SSH
    80,    # HTTP (often scanned by bots looking for any open port)
    443,   # HTTPS (often scanned by bots looking for any open port)
    21,    # FTP (often brute-forced)
    23     # Telnet (often brute-forced)
]

# Διαμόρφωση (Οι διαδρομές θα οριστούν από την κλάση AdvancedNetworkTools)
HOST = '0.0.0.0'
# BASE_DIR, LOG_DIR, STATS_FILE are now set dynamically in run_ssh_defender
EMPTY_CHECK_INTERVAL = 60  # 1 λεπτό

# Κοινά SSH banners για μίμηση πραγματικών διακομιστών
SSH_BANNERS = [
    b"SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.3\r\n",
    b"SSH-2.0-OpenSSH_7.4p1 Debian-10+deb9u7\r\n", 
    b"SSH-2.0-OpenSSH_7.9p1 FreeBSD-20200824\r\n",
    b"SSH-2.0-libssh-0.9.3\r\n"
]

# Όρια επίθεσης
MAX_ATTEMPTS = 5         # Μέγιστες προσπάθειες πριν την καταγραφή πλήρους αρχείου καταγραφής/απαγόρευση IP
ATTACK_THRESHOLD = 50    # Αριθμός προσπαθειών σε 5 λεπτά για την ενεργοποίηση προειδοποίησης/διακοπή κύκλου


# ==============================================================================
# SSH DEFENDER - Κλάση Καταγραφικού (Logger)
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
        """Φορτώνει αθροιστικά στατιστικά από το αρχείο JSON."""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"total_attacks": 0, "ip_stats": {}, "port_stats": {}}

    def save_stats(self):
        """Αποθηκεύει αθροιστικά στατιστικά στο αρχείο JSON."""
        with self.lock:
            try:
                with open(self.stats_file, 'w') as f:
                    json.dump(self.attack_stats, f, indent=4)
            except IOError as e:
                print(f"Σφάλμα κατά την αποθήκευση του αρχείου στατιστικών: {e}")

    def log_attempt(self, ip, port, message, is_full_log=False):
        """Καταγράφει μια μεμονωμένη προσπάθεια σύνδεσης και ενημερώνει τα στατιστικά."""
        timestamp = datetime.now().isoformat()
        
        with self.lock:
            # 1. Ενημέρωση προσπαθειών συνεδρίας
            self.current_session_attempts[ip] = self.current_session_attempts.get(ip, 0) + 1
            
            # 2. Ενημέρωση αθροιστικών στατιστικών
            self.attack_stats['total_attacks'] = self.attack_stats.get('total_attacks', 0) + 1
            
            # Στατιστικά IP
            ip_data = self.attack_stats['ip_stats'].setdefault(ip, {"count": 0, "last_attempt": None, "first_attempt": timestamp})
            ip_data['count'] += 1
            ip_data['last_attempt'] = timestamp
            
            # Στατιστικά Θυρών
            port_key = str(port)
            self.attack_stats['port_stats'].setdefault(port_key, 0)
            self.attack_stats['port_stats'][port_key] += 1
            
            # 3. Εγγραφή αρχείου καταγραφής αν ζητηθεί πλήρες αρχείο καταγραφής ή αν πληρείται το όριο
            if is_full_log:
                log_filename = os.path.join(self.log_dir, f"{ip}.log")
                try:
                    with open(log_filename, 'a') as f:
                        f.write(f"[{timestamp}] PORT:{port} - {message}\n")
                except IOError as e:
                    print(f"Σφάλμα κατά την εγγραφή του αρχείου καταγραφής: {e}")
                    
            # 4. Αποθήκευση αθροιστικών στατιστικών περιοδικά
            if self.attack_stats['total_attacks'] % 10 == 0:
                self.save_stats()
                
    def get_session_total_attempts(self):
        """Επιστρέφει τον συνολικό αριθμό προσπαθειών στην τρέχουσα συνεδρία."""
        return sum(self.current_session_attempts.values())

    def get_current_attempts(self):
        """Επιστρέφει τον αριθμό των προσπαθειών και τον χρόνο που έχει περάσει από την έναρξη της συνεδρίας."""
        attempts = self.get_session_total_attempts()
        time_elapsed = time.time() - self.session_start_time
        return attempts, time_elapsed
        
    def reset_session_stats(self):
        """Επαναφέρει τα στατιστικά στοιχεία ανά συνεδρία (χρησιμοποιείται κατά την εναλλαγή θυρών)."""
        with self.lock:
            self.current_session_attempts = {}
            self.session_start_time = time.time()
            
    def get_cumulative_stats_summary(self):
        """Επιστρέφει μια μορφοποιημένη περίληψη των αθροιστικών στατιστικών."""
        total = self.attack_stats.get('total_attacks', 0)
        
        # Λήψη κορυφαίων 3 IP
        ip_list = sorted(self.attack_stats['ip_stats'].items(), key=lambda item: item[1]['count'], reverse=True)
        top_ips = [f"{ip} ({data['count']} attempts)" for ip, data in ip_list[:3]]
        
        # Λήψη κορυφαίων 3 Θυρών
        port_list = sorted(self.attack_stats['port_stats'].items(), key=lambda item: item[1], reverse=True)
        top_ports = [f"{port} ({count} attacks)" for port, count in port_list[:3]]
        
        return {
            "Σύνολο Επιθέσεων": total,
            "Κορυφαίες Επιτιθέμενες IP": top_ips if top_ips else ["Δ/Υ"],
            "Κορυφαίες Στοχευμένες Θύρες": top_ports if top_ports else ["Δ/Υ"]
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
        
        # Ο βασικός κατάλογος χειρίζεται από το logger

    def _handle_connection(self, client_socket, addr):
        """Χειρίζεται την αλληλεπίδραση με έναν συνδεόμενο πελάτη (τη λογική honeypot)."""
        ip, port = addr
        
        # Επιλέγει ένα τυχαίο banner για να μιμηθεί έναν πραγματικό διακομιστή SSH
        banner = random.choice(SSH_BANNERS)
        
        try:
            # 1. Στέλνει αμέσως το SSH banner
            client_socket.sendall(banner)
            
            # 2. Ξεκινά διαδραστική συνεδρία (περιμένει για εισαγωγή)
            attempt_count = 0
            
            while self.running:
                # Χρήση select για μη μπλοκαριστική ανάγνωση με χρονικό όριο
                ready_to_read, _, _ = select.select([client_socket], [], [], 3.0)
                
                if ready_to_read:
                    data = client_socket.recv(1024)
                    if not data:
                        break # Η σύνδεση έκλεισε από τον πελάτη
                        
                    data_str = data.decode('utf-8', errors='ignore').strip()
                    self.logger.log_attempt(ip, self.current_port, f"Δεδομένα Ελήφθησαν: '{data_str}'")
                    
                    attempt_count += 1
                    
                    # Καταγραφή πλήρους συνεδρίας αν επιτευχθούν οι μέγιστες προσπάθειες για αυτήν τη σύνδεση
                    is_full_log = (attempt_count >= MAX_ATTEMPTS)
                    
                    # Ενημέρωση του logger με λεπτομέρειες προσπάθειας
                    self.logger.log_attempt(ip, self.current_port, f"Προσπάθεια {attempt_count}: {data_str}", is_full_log=is_full_log)
                    
                    # Απάντηση με SSH KEXINIT ή παρόμοια απάντηση για προσομοίωση ενός πραγματικού διακομιστή
                    # Απλή απάντηση για να παραμείνει ανοιχτή η σύνδεση για περισσότερες προσπάθειες brute-force
                    if data_str.startswith("SSH"):
                         # Προσομοίωση απάντησης KEXINIT (τυχαίο 16-byte cookie, κ.λπ.)
                        kex_response = b'SSH-2.0-SSH Defender\r\n' 
                        client_socket.sendall(kex_response)
                        
                    elif data_str.lower().startswith(("user", "root", "admin", "login")):
                        # Απλή απάντηση για προτροπή κωδικού πρόσβασης
                        client_socket.sendall(b"Password:\r\n") 
                        
                    elif data_str.startswith("password"):
                        # Απλή απάντηση σφάλματος
                         client_socket.sendall(b"Permission denied, please try again.\r\n")

                    # Εάν αυτή η σύνδεση υφίσταται έντονο brute-force, κλείστε την
                    if attempt_count >= MAX_ATTEMPTS * 2:
                        break

                else:
                    # Χρονικό όριο, κλείσιμο σύνδεσης
                    break 

        except socket.timeout:
            self.logger.log_attempt(ip, self.current_port, "Έληξε το χρονικό όριο σύνδεσης.")
        except ConnectionResetError:
            self.logger.log_attempt(ip, self.current_port, "Η σύνδεση επαναφέρθηκε από τον ομότιμο.")
        except Exception as e:
            self.logger.log_attempt(ip, self.current_port, f"Μη χειριζόμενο σφάλμα σύνδεσης: {e}")
        finally:
            client_socket.close()

    def start_port_listener(self, port):
        """Ξεκινά τον κύριο ακροατή socket σε μια συγκεκριμένη θύρα."""
        if self.listener_thread or self.listener_socket:
            self.stop_all_ports()
        
        self.current_port = port
        
        try:
            self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listener_socket.bind((self.host, port))
            self.listener_socket.listen(5)
            print(f"{Fore.GREEN}✅ Το SSH Defender ακούει στο {self.host}:{port}...{Style.RESET_ALL}")
            self.running = True
            self.logger.reset_session_stats()
            
            self.listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
            self.listener_thread.start()
            
        except OSError as e:
            print(f"{Fore.RED}❌ Σφάλμα δέσμευσης στη θύρα {port}: {e}. (Ίσως τρέχει άλλη διεργασία ή δεν έχετε δικαιώματα;){Style.RESET_ALL}")
            self.running = False
            self.listener_socket = None
            self.current_port = None
            
        except Exception as e:
            print(f"{Fore.RED}❌ Μη χειριζόμενο σφάλμα κατά την εκκίνηση του ακροατή στη θύρα {port}: {e}{Style.RESET_ALL}")
            self.running = False
            self.listener_socket = None
            self.current_port = None

    def _listener_loop(self):
        """Ο κύριος βρόχος για την αποδοχή συνδέσεων."""
        while self.running:
            try:
                # Χρήση select για αναμονή συνδέσεων με χρονικό όριο
                ready_to_read, _, _ = select.select([self.listener_socket], [], [], 1.0)
                
                if ready_to_read and self.listener_socket in ready_to_read:
                    client_socket, addr = self.listener_socket.accept()
                    # Υποβολή του χειριστή σύνδεσης στην πισίνα νημάτων
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
        """Τερματίζει το socket ακροατή και το thread."""
        self.running = False
        if self.listener_socket:
            try:
                # Ξεμπλοκάρισμα της κλήσης accept
                self.listener_socket.shutdown(socket.SHUT_RDWR)
                self.listener_socket.close()
                self.listener_socket = None
                if self.listener_thread and self.listener_thread.is_alive():
                    self.listener_thread.join(timeout=2)
            except Exception:
                pass # Αγνοήστε τα σφάλματα στο κλείσιμο
        self.current_port = None
        self.executor.shutdown(wait=False, cancel_futures=True)
        # Επαναδημιουργία executor για εκκαθάριση παλιών νημάτων, αν είναι απαραίτητο για επανεκκίνηση TUI
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=50)


    def run_port_cycle(self):
        """Εκτελεί την εναλλαγή μέσω μιας λίστας γνωστών θυρών."""
        self.cycle_mode = True
        
        for port_index, port in enumerate(FAMOUS_SSH_PORTS):
            
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}  ΕΝΑΡΞΗ ΠΑΡΑΚΟΛΟΥΘΗΣΗΣ ΣΤΗ ΘΥΡΑ: {port}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            self.start_port_listener(port)
            if not self.running:
                # Δεν ήταν δυνατή η δέσμευση, παράλειψη στην επόμενη θύρα
                continue 
            
            start_time = time.time()
            
            # Βρόχος παρακολούθησης για 5 λεπτά (ή μέχρι να χτυπηθεί ένα όριο επίθεσης)
            while time.time() - start_time < 5 * 60:
                time.sleep(EMPTY_CHECK_INTERVAL) # Έλεγχος κάθε λεπτό
                
                attempts, time_elapsed = self.logger.get_current_attempts()
                
                if attempts > ATTACK_THRESHOLD:
                    print(f"\n\n{Fore.RED}🚨 ΕΝΤΟΠΙΣΤΗΚΕ ΚΡΙΣΙΜΗ ΕΠΙΘΕΣΗ στη θύρα {port}!{Style.RESET_ALL}")
                    print(f"   {attempts} προσπάθειες σε {int(time_elapsed)} δευτερόλεπτα.")
                    print(f"{Fore.YELLOW}   Μεταγωγή σε λειτουργία μόνιμης παρακολούθησης για αυτήν τη θύρα.{Style.RESET_ALL}")
                    
                    self.stop_all_ports()
                    self.cycle_mode = False
                    
                    # Επανεκκίνηση του ακροατή για μόνιμη παρακολούθηση
                    self.start_port_listener(port)
                    input(f"{Fore.YELLOW}Πατήστε Enter για να σταματήσει η παρακολούθηση...{Style.RESET_ALL}")
                    self.running = False
                    break # Έξοδος από τον βρόχο εναλλαγής
                
            if not self.cycle_mode: # Αν βγήκαμε λόγω κρίσιμης επίθεσης
                break

            if port_index == len(FAMOUS_SSH_PORTS) - 1:
                print(f"\n\n{Fore.GREEN}✅ Ολοκληρώθηκε η παρακολούθηση όλων των γνωστών θυρών χωρίς σημαντικές επιθέσεις. Το Defender τερματίζεται.{Style.RESET_ALL}")
                self.running = False
                break # Έξοδος από τον βρόχο εναλλαγής
                
            # Καμία επίθεση: Ζητήστε από τον χρήστη να αλλάξει
            next_port = FAMOUS_SSH_PORTS[port_index + 1]
            user_input = input(f"\n\n{Fore.YELLOW}⏰ Πέρασαν 5 λεπτά στη θύρα {port} χωρίς επιθέσεις.\nΘέλετε να μεταβείτε στην επόμενη γνωστή θύρα ({next_port}); (ν/ο): {Style.RESET_ALL}")
            
            self.stop_all_ports()
            
            if user_input.lower() not in ['y', 'ν', 'υ']: # Προσθήκη 'ν' και 'υ' για ναι/yes
                print(f"\n{Fore.RED}🛑 Ο χρήστης επέλεξε να σταματήσει τον κύκλο θυρών. Το Defender τερματίζεται.{Style.RESET_ALL}")
                self.running = False
                break
            
        # Τελικός Καθαρισμός
        self.running = False
        self.stop_all_ports()
        self.logger.save_stats()
        print(f"\n{Fore.GREEN}✅ Το SSH Defender τερματίστηκε.{Style.RESET_ALL}")


# ==============================================================================
# ΤΕΛΟΣ ΚΩΔΙΚΑ SSH DEFENDER
# ==============================================================================


def auto_install_dependencies():
    """
    Αυτόματη εγκατάσταση όλων των απαιτούμενων εξαρτήσεων χωρίς root.
    Βελτιστοποιημένο για να εγκαθιστά μόνο ό,τι είναι απαραίτητο.
    """
    print(f"{Fore.CYAN}🛠️ ΠΡΟΗΓΜΕΝΑ ΕΡΓΑΛΕΙΑ ΔΙΚΤΥΟΥ - Αυτόματη Εγκατάσταση Εξαρτήσεων{Style.RESET_ALL}")
    print("="*70)
    print(f"{Fore.YELLOW}Αυτό θα εγκαταστήσει όλα τα απαιτούμενα πακέτα χωρίς πρόσβαση root.{Style.RESET_ALL}")
    
    is_termux = os.path.exists('/data/data/com.termux')
    
    # Πακέτα συστήματος για το Termux (δεν απαιτείται root)
    # Το nmap συμπεριλαμβάνεται για το εργαλείο περιτυλίγματος Nmap
    termux_packages = [
        'python', 'python-pip', 'curl', 'wget', 'nmap', 
        'inetutils', 'openssl-tool', 'ncurses-utils'
    ]
    
    # Πακέτα Python (pip) - Καθαρισμένη λίστα *μόνο* των χρησιμοποιούμενων εξαρτήσεων
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
            # Χειρισμός ενσωματωμένων ονομάτων ενοτήτων όπως dns.resolver
            base_module = module_name.split('.')[0]
            importlib.import_module(base_module)
            print(f"    {Fore.GREEN}✅ Το {package} είναι ήδη εγκατεστημένο{Style.RESET_ALL}")
        except ImportError:
            print(f"    [*] Εγκατάσταση {package}...")
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', package],
                    capture_output=True, text=True, timeout=180
                )
                if result.returncode == 0:
                    print(f"    {Fore.GREEN}✅ Το {package} εγκαταστάθηκε επιτυχώς{Style.RESET_ALL}")
                else:
                    print(f"    {Fore.YELLOW}⚠️ Δεν ήταν δυνατή η εγκατάσταση του {package}. Σφάλμα: {result.stderr.splitlines()[-1]}{Style.RESET_ALL}")
            except Exception as e:
                print(f"    {Fore.RED}❌ Αποτυχία εγκατάστασης {package}: {e}{Style.RESET_ALL}")
    
    # Τελικός έλεγχος εξαρτήσεων
    print(f"\n{Fore.CYAN}[*] Τελικός έλεγχος εξαρτήσεων...{Style.RESET_ALL}")
    try:
        import requests
        print(f"    {Fore.GREEN}✅ requests{Style.RESET_ALL}")
    except ImportError:
        print(f"    {Fore.RED}❌ requests{Style.RESET_ALL}")
    
    print(f"\n{Fore.GREEN}🎉 Η εγκατάσταση ολοκληρώθηκε! Εκκίνηση εφαρμογής...{Style.RESET_ALL}")
    time.sleep(2)
    return True


def main_app_loop():
    """Κύριο σημείο εισόδου της εφαρμογής"""
    
    class AdvancedNetworkTools:
        def __init__(self):
            # Ορισμός και δημιουργία ενός αποκλειστικού καταλόγου αποθήκευσης
            is_termux = os.path.exists('/data/data/com.termux')
            if is_termux:
                base_dir = os.path.expanduser('~')
                self.save_dir = os.path.join(base_dir, "DedSec's Network")
            else:
                self.save_dir = os.path.join(os.getcwd(), "DedSec's Network")

            if not os.path.exists(self.save_dir):
                print(f"{Fore.CYAN}[*] Δημιουργία καταλόγου αποθήκευσης στη διεύθυνση: {self.save_dir}{Style.RESET_ALL}")
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
            
            print(f"{Fore.GREEN}✅ Τα Προηγμένα Εργαλεία Δικτύου αρχικοποιήθηκαν επιτυχώς{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📂 Όλα τα αρχεία θα αποθηκευτούν στη διεύθυνση: {self.save_dir}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}⚡️ Τα νήματα εργασίας σάρωσης ορίστηκαν σε: {self.max_workers}{Style.RESET_ALL}")
            
        # --- Διαχείριση Διαμόρφωσης & Βάσης Δεδομένων ---
        def load_config(self):
            default_config = {
                "scan_interval": 60, "alert_on_new_network": True,
                "dns_test_server": "https://ipleak.net/json/",
                "port_scan_threads": 20, # Διατηρείται για συμβατότητα, αλλά χρησιμοποιούμε max_scan_workers
                "max_scan_workers": 15,  # Όριο αποδοτικής πισίνας νημάτων
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

        # --- Wi-Fi, Τοπικό Δίκτυο, και Εργαλεία Κινητής (Δεν απαιτείται Root) ---
        def _run_termux_command(self, command, timeout=15):
            """Βοηθητική συνάρτηση για την εκτέλεση εντολών Termux API."""
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
            if signal_dBm >= -50: return f"{Fore.GREEN}Εξαιρετική{Style.RESET_ALL}"
            if signal_dBm >= -65: return f"{Fore.YELLOW}Καλή{Style.RESET_ALL}"
            if signal_dBm >= -75: return f"{Fore.MAGENTA}Μέτρια{Style.RESET_ALL}"
            return f"{Fore.RED}Αδύναμη{Style.RESET_ALL}"
        
        def scan_via_termux_api(self):
            networks = []
            output = self._run_termux_command(['termux-wifi-scaninfo'])
            if output and output.strip().startswith('['):
                try:
                    scan_data = json.loads(output)
                    for network in scan_data:
                        networks.append({
                            'bssid': network.get('bssid', 'Unknown').upper(), 'ssid': network.get('ssid', 'Hidden'),
                            'signal': network.get('rssi', 0), 'channel': self.frequency_to_channel(network.get('frequency', 0)),
                            'encryption': network.get('security', 'Unknown')
                        })
                except json.JSONDecodeError:
                    pass # Αγνοήστε κατεστραμμένη έξοδο JSON
            return networks

        def get_current_connection_info(self):
            output = self._run_termux_command(['termux-wifi-connectioninfo'])
            if output and output.strip().startswith('{'):
                try:
                    conn_info = json.loads(output)
                    return {
                        'bssid': conn_info.get('bssid', 'Δ/Υ').upper(), 'ssid': conn_info.get('ssid', 'Not Connected'),
                        'signal': conn_info.get('rssi', 0), 'channel': self.frequency_to_channel(conn_info.get('frequency', 0)),
                        'encryption': conn_info.get('security', 'Δ/Υ'), 'is_current': True
                    }
                except json.JSONDecodeError:
                    pass
            return None

        def passive_network_scan(self):
            print(f"{Fore.YELLOW}[*] Εκκίνηση παθητικής σάρωσης Wi-Fi... (Απαιτείται Termux:API){Style.RESET_ALL}")
            networks_found = {}
            for net in self.scan_via_termux_api(): 
                networks_found[net['bssid']] = net
            
            current_network = self.get_current_connection_info()
            if current_network and current_network['bssid'] != 'Δ/Υ':
                networks_found[current_network['bssid']] = current_network
            
            if not networks_found:
                print(f"{Fore.RED}❌ Δεν βρέθηκαν δίκτυα. Βεβαιωθείτε ότι το Wi-Fi είναι ενεργοποιημένο και ότι το Termux:API είναι εγκατεστημένο και ρυθμισμένο.{Style.RESET_ALL}")

            return list(networks_found.values())
        
        def update_network_database(self, network):
            bssid = network['bssid']
            if bssid == 'Unknown': return

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
                if network.get('encryption', 'Unknown').upper() in ['WEP', 'OPEN', '']:
                    threats.append({'bssid': network['bssid'], 'ssid': network['ssid'], 'reason': f"Αδύναμη Κρυπτογράφηση ({network['encryption'] or 'Ανοιχτό'})", 'level': 'HIGH'})
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
                    color, status = Fore.GREEN, "ΕΜΠΙΣΤΕΥΤΟ"
                else:
                    color, status = Fore.WHITE, "ΠΑΡΑΤΗΡΗΘΗΚΕ"
                
                if enc.upper() in ['WEP', 'OPEN', '']:
                    enc_status = f"{Fore.RED}{enc or 'Ανοιχτό'} (ΜΗ ΑΣΦΑΛΕΣ!){Style.RESET_ALL}"
                elif 'WPA3' in enc:
                    enc_status = f"{Fore.GREEN}{enc}{Style.RESET_ALL}"
                else:
                    enc_status = f"{Fore.YELLOW}{enc}{Style.RESET_ALL}"
                    
                print(f"{color}--- ΔΙΚΤΥΟ {i}: {ssid or 'Κρυφό SSID'} {Style.RESET_ALL} (BSSID: {bssid}) ---")
                print(f"  Σήμα: {signal}dBm ({self.get_signal_quality(signal)}) | Κανάλι: {net['channel']}")
                print(f"  Κρυπτογράφηση: {enc_status}")
                print(f"  Κατάσταση: {color}{status}{Style.RESET_ALL}")
                
                for threat in (t for t in threats if t['bssid'] == bssid):
                    t_color = Fore.RED if threat['level'] == 'HIGH' else Fore.YELLOW
                    print(f"{t_color}  🚨 ΑΠΕΙΛΗ ({threat['level']}): {threat['reason']}{Style.RESET_ALL}")
                print("-" * 65)

        def single_wifi_scan(self):
            networks = self.passive_network_scan()
            if networks:
                threats = self.analyze_networks(networks)
                self.display_network_info(networks, threats)
            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")

        def view_current_connection(self):
            print(f"\n{Fore.CYAN}🔗 ΤΡΕΧΟΥΣΑ ΣΥΝΔΕΣΗ WI-FI{Style.RESET_ALL}")
            print("="*50)
            current_info = self.get_current_connection_info()
            if not current_info or current_info['ssid'] == 'Not Connected':
                print(f"{Fore.RED}❌ Δεν είστε συνδεδεμένοι σε δίκτυο Wi-Fi.{Style.RESET_ALL}")
            else:
                bssid = current_info['bssid']
                trust_status = f"{Fore.GREEN}ΕΜΠΙΣΤΕΥΤΟ{Style.RESET_ALL}" if bssid in self.trusted_bssids else f"{Fore.YELLOW}ΑΓΝΩΣΤΟ{Style.RESET_ALL}"
                print(f"  SSID:        {current_info['ssid']}")
                print(f"  BSSID:       {bssid}")
                print(f"  Σήμα:      {current_info['signal']}dBm ({self.get_signal_quality(current_info['signal'])})")
                print(f"  Κρυπτογράφηση:  {current_info['encryption']}")
                print(f"  Εμπιστοσύνη: {trust_status}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")

        def toggle_wifi(self):
            print(f"\n{Fore.CYAN}🔄 ΕΝΑΛΛΑΓΗ WI-FI (Termux:API){Style.RESET_ALL}")
            if not os.path.exists('/data/data/com.termux'):
                print(f"{Fore.RED}❌ Αυτή η λειτουργία απαιτεί την εφαρμογή Termux:API.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")
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
            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")

        def get_mobile_data_info(self):
            print(f"\n{Fore.CYAN}📱 ΠΛΗΡΟΦΟΡΙΕΣ ΔΕΔΟΜΕΝΩΝ ΚΙΝΗΤΗΣ / SIM (Termux:API){Style.RESET_ALL}")
            print("="*50)
            if not os.path.exists('/data/data/com.termux'):
                print(f"{Fore.RED}❌ Αυτή η λειτουργία απαιτεί την εφαρμογή Termux:API.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")
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
                    print(f"{Fore.YELLOW}[!] Δεν ήταν δυνατή η ανάλυση των πληροφοριών συσκευής.{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}[!] Δεν ήταν δυνατή η ανάκτηση πληροφοριών συσκευής/SIM. Χωρίς SIM;{Style.RESET_ALL}")

            # Πληροφορίες Κεραίας Κινητής Τηλεφωνίας
            cell_info_out = self._run_termux_command(['termux-telephony-cellinfo'])
            if cell_info_out:
                try:
                    data = json.loads(cell_info_out)
                    print(f"\n{Fore.CYAN}--- Κοντινές Κεραίες Κινητής Τηλεφωνίας ---{Style.RESET_ALL}")
                    if not data.get('cells'):
                         print("  Δεν υπάρχουν διαθέσιμες πληροφορίες για κεραίες κινητής τηλεφωνίας.")
                    for cell in data.get('cells', []):
                        cell_type = cell.get('type', 'Δ/Υ').upper()
                        strength = cell.get('dbm', 'Δ/Υ')
                        print(f"  - Τύπος: {cell_type} | Ισχύς: {strength} dBm ({self.get_signal_quality(strength)})")
                except json.JSONDecodeError:
                    print(f"{Fore.YELLOW}[!] Δεν ήταν δυνατή η ανάλυση των πληροφοριών κεραίας.{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}[!] Δεν ήταν δυνατή η ανάκτηση πληροφοριών κεραίας.{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")

        # --- Ενισχυμένα Εργαλεία Σάρωσης Δικτύου τύπου NMAP (Δεν απαιτείται Root) ---
        def nmap_wrapper(self):
            """Περιτύλιγμα για το δυαδικό αρχείο 'nmap' που εγκαταστάθηκε μέσω pkg."""
            print(f"\n{Fore.CYAN}⚡ ΠΕΡΙΤΥΛΙΓΜΑ ΣΑΡΩΤΗ NMAP{Style.RESET_ALL}")
            # Έλεγχος αν υπάρχει το nmap
            try:
                nmap_check = subprocess.run(['nmap', '--version'], capture_output=True, text=True, timeout=5)
                print(f"{Fore.GREEN}✅ Το Nmap βρέθηκε: {nmap_check.stdout.splitlines()[0]}{Style.RESET_ALL}")
            except (FileNotFoundError, subprocess.CalledProcessError):
                print(f"{Fore.RED}❌ Το δυαδικό αρχείο Nmap δεν βρέθηκε. Εγκαταστήστε το μέσω της εντολής 'pkg install nmap' στο Termux.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")
                return

            args = input(f"{Fore.WHITE}Εισάγετε ορίσματα Nmap (π.χ., -Pn -sV 192.168.1.1/24): {Style.RESET_ALL}").strip()
            if not args: return

            print(f"[*] Η σάρωση Nmap ξεκίνησε. Το αποτέλεσμα θα εμφανιστεί παρακάτω:{Style.RESET_ALL}")
            print("-" * 50)
            
            try:
                # Χρήση sys.executable για να διασφαλιστεί ότι τρέχει στο σωστό περιβάλλον, αν και το nmap είναι δυαδικό συστήματος.
                # Εδώ, η απλή εκτέλεση είναι καλύτερη.
                process = subprocess.Popen(
                    ['nmap'] + args.split(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Εκτύπωση αποτελεσμάτων σε πραγματικό χρόνο
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        print(output.strip())
                
                # Εκτύπωση σφαλμάτων
                stderr_output = process.stderr.read()
                if stderr_output:
                    print(f"\n{Fore.RED}--- NMAP ERROR OUTPUT ---{Style.RESET_ALL}")
                    print(stderr_output.strip())
                    
                result = process.wait()
                print(f"\n{Fore.GREEN}✅ Η σάρωση Nmap ολοκληρώθηκε με κωδικό εξόδου {result}.{Style.RESET_ALL}")

            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα κατά την εκτέλεση της σάρωσης Nmap: {e}{Style.RESET_ALL}")
                
            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")

        def run_port_scan(self):
            print(f"\n{Fore.CYAN}📶 Σάρωση Θυρών (TCP Connect){Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Σημείωση: Για περισσότερη ισχύ, χρησιμοποιήστε το εργαλείο περιτυλίγματος Nmap.{Style.RESET_ALL}")
            target = input(f"{Fore.WHITE}Εισάγετε στόχο IP ή όνομα κεντρικού υπολογιστή: {Style.RESET_ALL}").strip()
            if not target: return

            try:
                target_ip = socket.gethostbyname(target)
                print(f"[*] Επίλυση {target} σε {target_ip}")
            except socket.gaierror:
                print(f"{Fore.RED}❌ Δεν ήταν δυνατή η επίλυση του ονόματος κεντρικού υπολογιστή.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")
                return

            port_choice = input(f"{Fore.WHITE}Εισάγετε θύρες: (1) Κορυφαίες, (2) 1-1024, (3) Προσαρμοσμένη (π.χ., 80,443,1-100): {Style.RESET_ALL}").strip()
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

            print(f"[*] Σάρωση του {target_ip} σε {len(ports_to_scan)} θύρες TCP χρησιμοποιώντας {self.max_workers} νήματα εργασίας...")
            open_ports = {} # Χρησιμοποιήστε λεξικό για αποθήκευση port: service

            def get_banner(sock):
                """Προσπαθεί να ανακτήσει ένα banner ή απλά να επιστρέψει μια ένδειξη υπηρεσίας."""
                try:
                    # Προσπάθεια ανάγνωσης μικρού buffer για banner
                    data = sock.recv(1024) 
                    return data.decode('utf-8', errors='ignore').strip().split('\n')[0][:50]
                except socket.timeout:
                    return "Υπηρεσία εντοπίστηκε (Χωρίς banner)"
                except Exception:
                    return "Υπηρεσία εντοπίστηκε"

            def tcp_connect_scan(port):
                """Συνάρτηση εργασίας για σάρωση TCP connect"""
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(self.scan_timeout)
                        if sock.connect_ex((target_ip, port)) == 0:
                            banner = get_banner(sock)
                            open_ports[port] = banner
                            print(f"{Fore.GREEN}[+] Θύρα {port}/TCP είναι ανοιχτή. Banner: {banner}{Style.RESET_ALL}")
                except Exception:
                    pass # Αγνοήστε όλα τα άλλα σφάλματα

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                executor.map(tcp_connect_scan, sorted(list(ports_to_scan)))

            print("\n" + "="*50)
            if open_ports:
                print(f"{Fore.GREEN}✅ Σάρωση ολοκληρώθηκε. Βρέθηκαν ανοιχτές θύρες στο {target_ip}:{Style.RESET_ALL}")
                for port, banner in sorted(open_ports.items()):
                    print(f"  {Fore.CYAN}* {port:5d} - {banner}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Δεν βρέθηκαν ανοιχτές θύρες στο {target_ip}.{Style.RESET_ALL}")
            print("="*50)

            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")

        def network_discovery(self):
            """Προηγμένη ανακάλυψη δικτύου χρησιμοποιώντας πολλαπλές τεχνικές - ΑΠΟΔΟΤΙΚΗ ΠΙΣΙΝΑ ΝΗΜΑΤΩΝ"""
            print(f"\n{Fore.CYAN}🌐 ΠΡΟΗΓΜΕΝΗ ΑΝΑΚΑΛΥΨΗ ΔΙΚΤΥΟΥ{Style.RESET_ALL}")
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
            except Exception as e:
                print(f"{Fore.RED}❌ Δεν ήταν δυνατός ο προσδιορισμός της τοπικής IP: {e}{Style.RESET_ALL}")
                return

            # Υποθέστε ένα τυπικό δίκτυο /24
            network_base = '.'.join(local_ip.split('.')[:-1]) + '.'
            print(f"[*] Η IP σας: {local_ip}")
            print(f"[*] Σάρωση δικτύου: {network_base}0/24 χρησιμοποιώντας {self.max_workers} νήματα εργασίας...")

            discovered_hosts = {} # ip: [reason]
            common_ports = [22, 80, 443, 8080, 3389, 445]
            lock = threading.Lock()

            def discover_host(ip):
                """Συνάρτηση εργασίας για σάρωση ενός μόνο κεντρικού υπολογιστή με πολλαπλές μεθόδους."""
                if ip == local_ip: return # Παράλειψη της τοπικής IP

                reasons = []
                # Μέθοδος 1: ICMP Ping
                try:
                    subprocess.run(['ping', '-c', '1', '-W', '1', ip], capture_output=True, timeout=2, check=True)
                    reasons.append("ICMP")
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    pass # Ο κεντρικός υπολογιστής είναι εκτός λειτουργίας ή δεν απαντά στο ping

                # Μέθοδος 2: TCP Port Probe
                for port in common_ports:
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                            sock.settimeout(0.5) # Ταχύτερο χρονικό όριο για ανακάλυψη
                            if sock.connect_ex((ip, port)) == 0:
                                reasons.append(f"TCP/{port}")
                                break # Ένας ανοιχτός αρκεί
                    except:
                        pass

                if reasons:
                    with lock:
                        discovered_hosts[ip] = reasons
                        print(f"  {Fore.GREEN}[+] {ip:15}{Style.RESET_ALL} - Ενεργός (Βρέθηκε μέσω: {', '.join(reasons)})")

            try:
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    # Σάρωση όλων των πιθανών IP στο δίκτυο /24 (1 έως 254)
                    ip_range = [network_base + str(i) for i in range(1, 255)]
                    list(executor.map(discover_host, ip_range)) # Χρήση list() για να περιμένουμε να τελειώσουν όλα
            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα κατά την εκτέλεση της ανακάλυψης: {e}{Style.RESET_ALL}")
                
            print("\n" + "="*50)
            if discovered_hosts:
                print(f"{Fore.GREEN}--- Ενεργοί Κεντρικοί Υπολογιστές Βρέθηκαν ({len(discovered_hosts)}) ---{Style.RESET_ALL}")
                for ip, reasons in sorted(discovered_hosts.items()):
                    print(f"  {Fore.CYAN}* {ip:15} (Εντοπίστηκε μέσω: {', '.join(reasons)}){Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Δεν βρέθηκαν άλλοι ενεργοί κεντρικοί υπολογιστές στο δίκτυο.{Style.RESET_ALL}")
            print("="*50)

            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")


        def subnet_calculator(self):
            print(f"\n{Fore.CYAN}🧮 ΥΠΟΛΟΓΙΣΤΗΣ ΥΠΟΔΙΚΤΥΟΥ{Style.RESET_ALL}")
            ip_cidr_str = input(f"{Fore.WHITE}Εισάγετε IP/CIDR (π.χ., 192.168.1.5/24): {Style.RESET_ALL}").strip()
            if not ip_cidr_str: return

            try:
                if '/' not in ip_cidr_str:
                    print(f"{Fore.RED}❌ Μη έγκυρη μορφή IP/CIDR.{Style.RESET_ALL}")
                    return

                ip_str, cidr_str = ip_cidr_str.split('/')
                cidr = int(cidr_str)
                if not (0 <= cidr <= 32):
                     print(f"{Fore.RED}❌ Το CIDR πρέπει να είναι μεταξύ 0 και 32.{Style.RESET_ALL}")
                     return

                # Συνάρτηση μετατροπής IP σε integer
                def ip_to_int(ip):
                    return struct.unpack("!I", socket.inet_aton(ip))[0]

                ip_int = ip_to_int(ip_str)

                # Υπολογισμός μάσκας, διεύθυνσης δικτύου και broadcast
                mask_int = 0xFFFFFFFF << (32 - cidr) & 0xFFFFFFFF
                network_int = ip_int & mask_int
                broadcast_int = network_int | (~mask_int & 0xFFFFFFFF)

                # Συνάρτηση μετατροπής integer σε IP
                def int_to_ip(ip_int_val):
                    return '.'.join([str((ip_int_val >> (i << 3)) & 0xFF) for i in (3, 2, 1, 0)])

                network_addr = int_to_ip(network_int)
                broadcast_addr = int_to_ip(broadcast_int)
                subnet_mask = int_to_ip(mask_int)
                total_hosts = 2 ** (32 - cidr)
                usable_hosts = max(0, total_hosts - 2) # Αφαίρεση Network και Broadcast

                print(f"\n{Fore.GREEN}📊 ΑΠΟΤΕΛΕΣΜΑΤΑ ΥΠΟΛΟΓΙΣΜΟΥ ΥΠΟΔΙΚΤΥΟΥ:{Style.RESET_ALL}")
                print(f" Διεύθυνση: {ip_str}/{cidr}")
                print(f" Μάσκα Υποδικτύου: {subnet_mask}")
                print(f" Διεύθυνση Δικτύου: {network_addr}")
                print(f" Διεύθυνση Broadcast: {broadcast_addr}")
                print(f" Συνολικοί Κεντρικοί Υπολογιστές: {total_hosts}")
                print(f" Χρησιμοποιήσιμοι Κεντρικοί Υπολογιστές: {usable_hosts}")
                
                if usable_hosts > 0:
                    first_host = int_to_ip(network_int + 1)
                    last_host = int_to_ip(broadcast_int - 1)
                    print(f" Εύρος Κεντρικών Υπολογιστών: {first_host} - {last_host}")

            except (ValueError, socket.error) as e:
                print(f"{Fore.RED}❌ Σφάλμα κατά τον υπολογισμό του υποδικτύου: {e}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα κατά τον υπολογισμό του υποδικτύου: {e}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")

        # --- Internet & Διαγνωστικά (Δεν απαιτείται Root) ---
        def run_internet_speed_test(self):
            print(f"\n{Fore.CYAN}⚡️ ΕΚΤΕΛΕΣΗ ΔΟΚΙΜΗΣ ΤΑΧΥΤΗΤΑΣ INTERNET...{Style.RESET_ALL}")
            if not SPEEDTEST_AVAILABLE or not speedtest:
                print(f"{Fore.RED}❌ Η ενότητα 'speedtest-cli' δεν είναι διαθέσιμη.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")
                return
            try:
                st = speedtest.Speedtest()
                print(f"{Fore.YELLOW}[*] Εύρεση καλύτερου διακομιστή...{Style.RESET_ALL}")
                st.get_best_server()
                print(f"{Fore.YELLOW}[*] Εκτέλεση δοκιμής λήψης...{Style.RESET_ALL}")
                download_speed = st.download() / 1_000_000
                print(f"{Fore.YELLOW}[*] Εκτέλεση δοκιμής αποστολής...{Style.RESET_ALL}")
                upload_speed = st.upload() / 1_000_000

                print(f"\n{Fore.GREEN}📊 ΑΠΟΤΕΛΕΣΜΑΤΑ ΔΟΚΙΜΗΣ ΤΑΧΥΤΗΤΑΣ:{Style.RESET_ALL}")
                print(f" Λήψη: {download_speed:.2f} Mbps")
                print(f" Αποστολή: {upload_speed:.2f} Mbps")
                print(f" Καθυστέρηση: {st.results.ping:.2f} ms")
                print(f" Server: {st.results.server['name']} ({st.results.server['country']})")

            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα κατά την εκτέλεση της δοκιμής ταχύτητας: {e}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")

        def run_dns_leak_test(self):
            print(f"\n{Fore.CYAN}🌐 ΔΗΜΟΣΙΑ IP & ΔΟΚΙΜΗ ΔΙΑΡΡΟΗΣ DNS{Style.RESET_ALL}")
            if not REQUESTS_AVAILABLE or not requests:
                print(f"{Fore.RED}❌ Η ενότητα 'requests' δεν είναι διαθέσιμη.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")
                return

            test_url = self.config['dns_test_server']
            print(f"[*] Ανάκτηση δεδομένων από: {test_url}")
            
            try:
                response = requests.get(test_url, timeout=10, verify=False)
                if response.status_code == 200:
                    data = response.json()
                    
                    if data:
                        print(f"\n{Fore.GREEN}📊 ΑΠΟΤΕΛΕΣΜΑΤΑ ΔΗΜΟΣΙΑΣ IP:{Style.RESET_ALL}")
                        print(f" Δημόσια Διεύθυνση IP: {data.get('ip')}")
                        print(f" Τοποθεσία (Περίπου): {data.get('city')}, {data.get('country')}")
                        print(f" ISP (Πάροχος): {data.get('asn_owner')}")

                        # Απλοϊκή Έκδοση Δοκιμής Διαρροής DNS (ελέγχει μόνο μία IP)
                        dns_ip = data.get('ip_address')
                        if dns_ip and dns_ip != data.get('ip'):
                            print(f"{Fore.RED}🚨 ΠΙΘΑΝΗ ΔΙΑΡΡΟΗ DNS: Η IP του DNS ({dns_ip}) δεν ταιριάζει με τη δημόσια IP.{Style.RESET_ALL}")
                        
                        
                    else:
                        print(f"{Fore.RED}❌ Δεν ελήφθησαν δεδομένα ή μη έγκυρο JSON.{Style.RESET_ALL}")

                else:
                    print(f"{Fore.RED}❌ Δεν ήταν δυνατή η εκτέλεση της δοκιμής διαρροής DNS. Ελέγξτε URL/Σύνδεση. (Status: {response.status_code}){Style.RESET_ALL}")

            except requests.exceptions.Timeout:
                print(f"{Fore.RED}❌ Έληξε το χρονικό όριο κατά τη δοκιμή διαρροής DNS.{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα κατά τη δοκιμή διαρροής DNS: {e}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")

        def run_whois_lookup(self):
            print(f"\n{Fore.CYAN}🔗 ΕΚΤΕΛΕΣΗ ΑΝΑΖΗΤΗΣΗΣ WHOIS...{Style.RESET_ALL}")
            if not WHOIS_AVAILABLE or not whois:
                print(f"{Fore.RED}❌ Η ενότητα 'python-whois' δεν είναι διαθέσιμη.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")
                return

            target = input(f"{Fore.WHITE}Εισάγετε τομέα ή διεύθυνση IP: {Style.RESET_ALL}").strip()
            if not target: return

            try:
                # Ο whois.query() μπορεί να επιστρέψει None ή να προκαλέσει εξαίρεση για μη έγκυρο τομέα
                result = whois.query(target)

                print(f"\n{Fore.GREEN}--- ΑΠΟΤΕΛΕΣΜΑΤΑ WHOIS για {target} ---{Style.RESET_ALL}")
                if result:
                    # Προβολή βασικών πεδίων (προσαρμογή όπως απαιτείται)
                    print(f"  Domain Name:         {result.name}")
                    print(f"  Registrar:           {result.registrar}")
                    print(f"  Creation Date:       {result.creation_date}")
                    print(f"  Expiration Date:     {result.expiration_date}")
                    print(f"  Last Updated:        {result.last_updated}")
                    print(f"  Name Servers:        {', '.join(result.name_servers)}")
                    print(f"  Organization:        {result.registrar_organization}")
                    # Εάν είναι IP, θα έχει λιγότερα πεδία, το whois χειρίζεται και τα δύο.
                else:
                    print(f"{Fore.RED}❌ Δεν βρέθηκε εγγραφή WHOIS για το {target}.{Style.RESET_ALL}")

            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα κατά την αναζήτηση WHOIS: {e}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")

        def run_dns_lookup(self):
            print(f"\n{Fore.CYAN}🔍 ΕΚΤΕΛΕΣΗ ΑΝΑΖΗΤΗΣΗΣ DNS...{Style.RESET_ALL}")
            if not DNS_AVAILABLE or not dns_resolver:
                print(f"{Fore.RED}❌ Η ενότητα 'dnspython' δεν είναι διαθέσιμη.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")
                return

            name = input(f"{Fore.WHITE}Εισάγετε όνομα κεντρικού υπολογιστή ή τομέα (π.χ., google.com): {Style.RESET_ALL}").strip()
            record_type = input(f"{Fore.WHITE}Εισάγετε τύπο εγγραφής (A, MX, NS, TXT, CNAME, κ.λπ. - προεπιλογή A): {Style.RESET_ALL}").strip().upper() or 'A'
            
            if not name: return

            try:
                # Δημιουργία ανάλυσης με προεπιλεγμένους διακομιστές DNS (π.χ., από το /etc/resolv.conf ή Google DNS)
                resolver = dns_resolver.Resolver()
                answers = resolver.resolve(name, record_type)
                
                print(f"\n{Fore.GREEN}--- ΑΠΟΤΕΛΕΣΜΑΤΑ DNS για {name} ({record_type}) ---{Style.RESET_ALL}")
                for rdata in answers:
                    print(f"  Απάντηση: {rdata.to_text()}")
                    
            except dns_resolver.NoAnswer:
                print(f"{Fore.YELLOW}Δεν βρέθηκε απάντηση για τον τύπο εγγραφής {record_type}.{Style.RESET_ALL}")
            except dns_resolver.NXDOMAIN:
                print(f"{Fore.RED}❌ Δεν υπάρχει τομέας ({name}).{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα κατά την αναζήτηση DNS: {e}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")

        def run_traceroute(self):
            print(f"\n{Fore.CYAN}🗺️ ΕΚΤΕΛΕΣΗ TRACEROUTE...{Style.RESET_ALL}")
            target = input(f"{Fore.WHITE}Εισάγετε στόχο IP ή όνομα κεντρικού υπολογιστή για το traceroute: {Style.RESET_ALL}").strip()
            if not target: return

            # Το Termux χρησιμοποιεί το 'traceroute' (ή 'inetutils-traceroute')
            command = ['traceroute', target]
            
            print(f"[*] Το Traceroute στο {target} ξεκίνησε. Τα αποτελέσματα μπορεί να διαφέρουν ανάλογα με την πλατφόρμα:{Style.RESET_ALL}")
            print("-" * 50)
            
            try:
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        print(output.strip())
                
                process.wait()

            except FileNotFoundError:
                print(f"{Fore.RED}❌ Η εντολή 'traceroute' δεν βρέθηκε. Εγκαταστήστε την (π.χ., 'pkg install traceroute' ή 'pkg install inetutils').{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα κατά την εκτέλεση του traceroute: {e}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")

        # --- Συλλογή Πληροφοριών (Δεν απαιτείται Root) ---
        def run_osintds_scanner(self):
            """Περιτύλιγμα για το εργαλείο σαρωτή OSINTDS."""
            print(f"\n{Fore.CYAN} launching OSINTDS Scanner...{Style.RESET_ALL}")
            time.sleep(1) 

            # --- ΛΟΓΙΚΗ OSINTDS - Ενθυλακωμένη σε αυτήν τη μέθοδο ---

            # --- Διαμόρφωση και Σταθερές ---
            PREFERRED_PATHS = [ 
                os.path.expanduser("~/storage/downloads"),
                os.path.expanduser("/sdcard/Download"),
                os.path.expanduser("~/Downloads"),
                self.save_dir # Χρήση του καταλόγου αποθήκευσης της εφαρμογής
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
                "unclosed quotation mark after the character string", 
                "mysql_fetch", "syntax error in query", "warning: mysql", 
                "unterminated string constant",
            ]
            SECURITY_HEADERS = [
                "Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options",
                "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy",
            ]
            EDITOR = os.environ.get('EDITOR', 'nano')
            
            ASSET_MAP = [
                ('link', 'href', 'css', lambda tag: tag.get('rel') and 'stylesheet' in tag.get('rel')),
                ('script', 'src', 'js', lambda tag: True),
                ('img', 'src', 'image', lambda tag: True),
            ]

            DIR_WORDLIST_PATH = os.path.join(self.wordlist_dir, "common_dirs.txt")
            SUB_WORDLIST_PATH = os.path.join(self.wordlist_dir, "common_subs.txt")

            # --- Βοηθητικές Συναρτήσεις OSINTDS ---

            def _create_default_wordlists():
                # Δημιουργία απλών wordlists αν δεν υπάρχουν
                if not os.path.exists(DIR_WORDLIST_PATH):
                    with open(DIR_WORDLIST_PATH, 'w') as f:
                        f.write('admin\nlogin\napi\nrobots.txt\nsitemap.xml\nbackup\n')
                if not os.path.exists(SUB_WORDLIST_PATH):
                    with open(SUB_WORDLIST_PATH, 'w') as f:
                        f.write('www\ndev\ntest\napi\nmail\n')

            _create_default_wordlists()

            def get_user_choice(prompt, default):
                user_input = input(f"{Fore.WHITE}{prompt} ({default}): {Style.RESET_ALL}").strip()
                return user_input if user_input else default

            def read_wordlist(path):
                if not os.path.exists(path):
                    print(f"{Fore.YELLOW}[WARNING] Wordlist not found: {path}. Using minimal defaults.{Style.RESET_ALL}")
                    if 'dirs' in path: return ['admin', 'login']
                    if 'subs' in path: return ['www', 'dev']
                    return []
                try:
                    with open(path, 'r') as f:
                        return [line.strip() for line in f if line.strip()]
                except Exception as e:
                    print(f"[ERROR] Could not read wordlist {path}: {e}")
                    return []

            def normalize_url(url):
                try:
                    parsed = urlparse(url)
                    if not parsed.scheme:
                        parsed = urlparse('http://' + url)
                    domain = parsed.hostname
                    if not domain: return None, None
                    base = f"{parsed.scheme}://{parsed.netloc}"
                    return base.rstrip('/'), domain
                except ValueError:
                    return None, None

            def make_dirs(domain):
                safe_domain = re.sub(r'[^\w\-.]', '_', domain)
                target_dir = os.path.join(BASE_OSINT_DIR, safe_domain)
                os.makedirs(target_dir, exist_ok=True)
                return target_dir

            def save_text(folder, filename, text):
                path = os.path.join(folder, filename)
                try:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    print(f"[ΠΛΗΡΟΦΟΡΙΑ] Αποθηκεύτηκε: {path}")
                except IOError as e:
                    print(f'[ΣΦΑΛΜΑ] Σφάλμα αποθήκευσης αρχείου για {path}: {e}')

            def save_json(folder, filename, data):
                path = os.path.join(folder, filename)
                try:
                    with open(path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4)
                    print(f"[ΠΛΗΡΟΦΟΡΙΑ] Αποθηκεύτηκε: {path}")
                except IOError as e:
                    print(f'[ΣΦΑΛΜΑ] Σφάλμα αποθήκευσης αρχείου για {path}: {e}')

            def save_csv(folder, filename, rows, headers=None):
                if not csv: 
                    print(f"[ΣΦΑΛΜΑ] CSV module not available for saving CSV.")
                    return
                path = os.path.join(folder, filename)
                try:
                    with open(path, 'w', newline='', encoding='utf-8') as cf:
                        writer = csv.writer(cf)
                        if headers:
                            writer.writerow(headers)
                        writer.writerows(rows)
                    print(f"[ΠΛΗΡΟΦΟΡΙΑ] Αποθηκεύτηκε: {path}")
                except IOError as e:
                    print(f'[ΣΦΑΛΜΑ] Σφάλμα αποθήκευσης CSV για {path}: {e}')

            def generate_html_report(report, folder):
                html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Αναφορά OSINTDS για {html.escape(report.get('domain', 'Δ/Υ'))}</title>
    <style>body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Oxygen-Sans,Ubuntu,Cantarell,"Helvetica Neue",sans-serif;line-height:1.6;color:#333;max-width:1200px;margin:0 auto;padding:20px;background-color:#f9f9f9}}h1,h2,h3{{color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:10px}}h1{{font-size:2.5em}}pre{{background-color:#ecf0f1;padding:1em;border:1px solid #bdc3c7;border-radius:5px;white-space:pre-wrap;word-wrap:break-word;font-family:"Courier New",Courier,monospace}}ul,ol{{padding-left:20px}}li{{margin-bottom:5px}}.card{{background-color:#fff;border:1px solid #ddd;border-radius:8px;padding:20px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,0.1)}}</style>
</head>
<body>
    <h1>Αναφορά OSINTDS για {html.escape(report.get('domain', 'Δ/Υ'))}</h1>
    <div class="card">
        <h2>Περίληψη</h2>
        <ul>
            <li><strong>Στόχος URL:</strong> {html.escape(report.get('target_url', 'N/A'))}</li>
            <li><strong>Τομέας:</strong> {html.escape(report.get('domain', 'N/A'))}</li>
            <li><strong>IP Διεύθυνση:</strong> {html.escape(report.get('ip_address', 'N/A'))}</li>
            <li><strong>Στάτους Κώδικας:</strong> {report.get('status_code', 'N/A')}</li>
            <li><strong>Τίτλος Σελίδας:</strong> {html.escape(report.get('page_title', 'N/A'))}</li>
        </ul>
    </div>
    <div class="card">
        <h2>Διαμορφώσεις Διακομιστή</h2>
        <ul>
            <li><strong>Διακομιστής:</strong> {html.escape(report.get('server_header', 'N/A'))}</li>
            <li><strong>Γλώσσα:</strong> {html.escape(report.get('content_language', 'N/A'))}</li>
            <li><strong>Cookies:</strong>
                <pre>{html.escape(json.dumps(report.get('cookies', {}), indent=2))}</pre>
            </li>
            <li><strong>Κεφαλίδες Ασφαλείας που Λείπουν:</strong> {', '.join(report.get('missing_security_headers', ['N/A']))}</li>
        </ul>
    </div>
    <div class="card">
        <h2>Ανακάλυψη Καταλόγων (Status Code 200/301/302)</h2>
        <ul>
            { "".join([f'<li><a href="{html.escape(d["url"])}">{html.escape(d["path"])}</a> (Code: {d["status"]})</li>' for d in report.get('discovered_paths', [])]) or "<li>Δεν βρέθηκαν κοινοί κατάλογοι.</li>" }
        </ul>
    </div>
    <div class="card">
        <h2>Ανακάλυψη Υποτομέων</h2>
        <ul>
            { "".join([f'<li>{html.escape(s)}</li>' for s in report.get('subdomains', [])]) or "<li>Δεν βρέθηκαν υποτομείς.</li>" }
        </ul>
    </div>
    <div class="card">
        <h2>Σύνδεσμοι & Πόροι</h2>
        <ul>
            <li><strong>Σύνολο Εσωτερικών Συνδέσμων:</strong> {len(report.get('internal_links', []))}</li>
            <li><strong>Σύνολο Εξωτερικών Συνδέσμων:</strong> {len(report.get('external_links', []))}</li>
            <li><strong>Assets (CSS, JS, Εικόνες):</strong>
                <ul>
                    { "".join([f'<li>{html.escape(a["type"])}: {html.escape(a["url"])}</li>' for a in report.get('assets', [])]) or "<li>Δεν βρέθηκαν σημαντικά assets.</li>" }
                </ul>
            </li>
        </ul>
    </div>
    <div class="card">
        <h2>Ευπάθειες & Σημειώσεις</h2>
        <ul>
            { "".join([f'<li><strong>{html.escape(v["type"])}:</strong> {html.escape(v["message"])} ({html.escape(v.get("url", ""))})</li>' for v in report.get('vulnerabilities', [])]) or "<li>Δεν βρέθηκαν άμεσες ευπάθειες.</li>" }
        </ul>
    </div>
    <footer><p>Generated by OSINTDS Scanner at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p></footer>
</body>
</html>
"""
                save_text(folder, 'report.html', html_content)
                # Εγγραφή ευρήματος ελέγχου για την αναφορά
                self.record_audit_finding(
                    report.get('domain', 'N/A'), 'OSINTDS Scan', 'HTML Report Generated',
                    f'Full OSINTDS report saved to {os.path.join(folder, "report.html")}', 'Informational'
                )


            # --- Core Scan Logic ---

            def check_url(url, method='GET', data=None, allow_redirects=True, verbose=False):
                if not REQUESTS_AVAILABLE: return None, None
                try:
                    response = requests.request(
                        method, url, data=data, headers=HEADERS, timeout=HTTP_TIMEOUT, 
                        allow_redirects=allow_redirects, verify=False # Αγνοήστε τα σφάλματα SSL για σάρωση
                    )
                    if verbose: print(f"[{response.status_code}] {url}")
                    return response, None
                except requests.exceptions.Timeout:
                    return None, "Timeout"
                except requests.exceptions.RequestException as e:
                    return None, str(e)

            def get_base_info(target_url, verbose=False):
                report = {'target_url': target_url}
                
                # 1. Βασική ανάκτηση και ανάλυση URL
                base, domain = normalize_url(target_url)
                if not base:
                    print(f"{Fore.RED}❌ Invalid target URL: {target_url}{Style.RESET_ALL}")
                    return None, None
                report['base_url'] = base
                report['domain'] = domain
                
                # 2. Πρώτη αίτηση για κεφαλίδες και περιεχόμενο
                if verbose: print(f"[*] Fetching base URL: {base}")
                response, error = check_url(base, verbose=verbose)
                if error:
                    report['vulnerabilities'] = [{'type': 'Connection Error', 'message': f"Could not connect: {error}"}]
                    return report, make_dirs(domain)

                report['status_code'] = response.status_code
                
                # 3. Πληροφορίες διακομιστή
                server_header = response.headers.get('Server', 'N/A')
                report['server_header'] = server_header
                report['content_language'] = response.headers.get('Content-Language', 'N/A')
                report['cookies'] = response.cookies.get_dict()
                
                # 4. Έλεγχος κεφαλίδων ασφαλείας
                missing_headers = [h for h in SECURITY_HEADERS if h not in response.headers]
                report['missing_security_headers'] = missing_headers
                if missing_headers:
                    report.setdefault('vulnerabilities', []).append({
                        'type': 'Security Headers Missing', 
                        'message': f"Missing headers: {', '.join(missing_headers)}",
                        'level': 'MEDIUM'
                    })
                
                # 5. Ανάλυση HTML
                if BS4_AVAILABLE:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    report['page_title'] = soup.title.string.strip() if soup.title else 'N/A'
                    
                    # 6. Ανάκτηση Assets, Συνδέσμων
                    links, assets = [], []
                    for link in soup.find_all(['a', 'link', 'script', 'img']):
                        href_attr = link.get('href') if link.name in ['a', 'link'] else link.get('src')
                        if not href_attr or href_attr.startswith(('mailto:', '#', 'tel:')): continue
                        
                        full_url = urljoin(base, href_attr)
                        if domain in full_url:
                            if link.name == 'a':
                                links.append({'type': 'internal', 'url': full_url})
                            else:
                                for tag_name, attr, asset_type, check in ASSET_MAP:
                                    if link.name == tag_name and check(link):
                                        assets.append({'type': asset_type, 'url': full_url})
                                        break
                        elif full_url.startswith(('http', 'https')):
                            if link.name == 'a':
                                links.append({'type': 'external', 'url': full_url})
                                
                    report['internal_links'] = list(set(d['url'] for d in links if d['type'] == 'internal'))
                    report['external_links'] = list(set(d['url'] for d in links if d['type'] == 'external'))
                    report['assets'] = assets
                    
                # 7. Αναζήτηση ευπαθειών SQLi/XSS (απλή)
                if any(p in response.text.lower() for p in SQL_ERROR_PATTERNS):
                    report.setdefault('vulnerabilities', []).append({
                        'type': 'Potential SQLi', 
                        'message': "SQL error pattern detected in response body.",
                        'level': 'HIGH'
                    })
                
                # 8. Ανάκτηση IP
                try:
                    report['ip_address'] = socket.gethostbyname(domain)
                except Exception:
                    report['ip_address'] = 'N/A'

                return report, make_dirs(domain)


            def run_subdomain_brute(base_report, sub_words, threads, verbose):
                domain = base_report['domain']
                subdomains = set()
                lock = threading.Lock()

                def check_subdomain(sub):
                    if not sub: return
                    test_domain = f"{sub}.{domain}"
                    try:
                        # Χρήση dns_resolver για έλεγχο A record
                        if DNS_AVAILABLE:
                            dns_resolver.resolve(test_domain, 'A', lifetime=2.0)
                            with lock:
                                subdomains.add(test_domain)
                                if verbose: print(f"{Fore.GREEN}[SUB FOUND] {test_domain}{Style.RESET_ALL}")
                        else:
                            # Fallback με socket (λιγότερο αξιόπιστο για wildcard)
                            socket.gethostbyname(test_domain)
                            with lock:
                                subdomains.add(test_domain)
                                if verbose: print(f"{Fore.GREEN}[SUB FOUND] {test_domain} (Socket){Style.RESET_ALL}")

                    except (dns_resolver.NXDOMAIN, socket.gaierror):
                        pass # Δεν βρέθηκε
                    except Exception as e:
                        if verbose: print(f"[ERROR] Subdomain check failed for {test_domain}: {e}")

                if verbose: print(f"[*] Starting subdomain bruteforce on {domain} with {len(sub_words)} words...")
                with ThreadPoolExecutor(max_workers=threads) as executor:
                    list(executor.map(check_subdomain, sub_words))
                
                base_report['subdomains'] = sorted(list(subdomains))

            def run_directory_brute(base_report, dir_words, threads, verbose):
                base_url = base_report['base_url']
                discovered_paths = []
                lock = threading.Lock()

                def check_path(path):
                    if not path: return
                    test_url = f"{base_url}/{path.lstrip('/')}"
                    response, error = check_url(test_url, verbose=verbose, allow_redirects=True)
                    
                    if response and (response.status_code == 200 or 300 <= response.status_code < 400):
                        # 200 (OK), 301 (Moved Permanently), 302 (Found)
                        with lock:
                            discovered_paths.append({'path': path, 'url': response.url, 'status': response.status_code})
                            if verbose or response.status_code == 200:
                                print(f"{Fore.GREEN}[PATH FOUND] {test_url} (Code: {response.status_code}){Style.RESET_ALL}")
                    elif error and verbose:
                        print(f"[ERROR] Path check failed for {test_url}: {error}")
                
                if verbose: print(f"[*] Starting directory bruteforce on {base_url} with {len(dir_words)} paths...")
                with ThreadPoolExecutor(max_workers=threads) as executor:
                    list(executor.map(check_path, dir_words))

                base_report['discovered_paths'] = discovered_paths


            def run_checks(target, threads, full_ports, out_formats, dir_words, sub_words, verbose):
                
                report, folder = get_base_info(target, verbose)
                if not report: return None, None
                
                if 'sub' in full_ports:
                    run_subdomain_brute(report, sub_words, threads, verbose)

                if 'dir' in full_ports:
                    run_directory_brute(report, dir_words, threads, verbose)
                
                print(f"\n{Fore.GREEN}✅ OSINTDS Scan Complete.{Style.RESET_ALL}")
                print(f"   Results saved in: {folder}")
                
                if 'json' in out_formats:
                    save_json(folder, 'report.json', report)
                if 'html' in out_formats:
                    generate_html_report(report, folder)
                if 'csv' in out_formats:
                    # Αποθήκευση λίστας συνδέσμων ως CSV
                    link_rows = [[link] for link in report.get('internal_links', []) + report.get('external_links', [])]
                    save_csv(folder, 'links.csv', link_rows, ['URL'])
                
                return report, folder


            # --- ΤΕΛΟΣ ΛΟΓΙΚΗΣ OSINTDS ---

            # --- Είσοδος Χρήστη OSINTDS ---
            if not REQUESTS_AVAILABLE:
                print(f"{Fore.RED}❌ Η ενότητα 'requests' απαιτείται για τη λειτουργία OSINTDS.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")
                return

            print(f"{Fore.CYAN}--- ΡΥΘΜΙΣΕΙΣ OSINTDS ---{Style.RESET_ALL}")
            target_input = get_user_choice('Εισάγετε στόχο URL ή τομέα', 'https://example.com')
            threads = int(get_user_choice(f'Αριθμός νημάτων (1-{self.max_workers})', str(min(25, self.max_workers))))
            full_ports_raw = get_user_choice('Ενεργοποίηση brute-force (sub, dir); (comma-separated)', 'dir')
            full_ports = {p.strip() for p in full_ports_raw.lower().split(',')}

            # Λήψη διαδρομών λιστών λέξεων
            dir_wordlist_path = get_user_choice('Διαδρομή προς τη λίστα λέξεων καταλόγων;', DIR_WORDLIST_PATH)
            sub_wordlist_path = get_user_choice('Διαδρομή προς τη λίστα λέξεων υποτομέων;', SUB_WORDLIST_PATH)
            
            # Ενεργοποίηση λεπτομερούς λειτουργίας
            verbose = input(f'{Fore.WHITE}Ενεργοποίηση λεπτομερούς λειτουργίας για εντοπισμό σφαλμάτων; (ν/Ο): {Style.RESET_ALL}').strip().lower().startswith('y')

            out_formats_raw = get_user_choice('Μορφές εξόδου (json,html,csv);', 'json,html,csv')
            out_formats = {f.strip() for f in out_formats_raw.split(',') if f.strip()}

            dir_words, sub_words = read_wordlist(dir_wordlist_path), read_wordlist(sub_wordlist_path)

            print(f"\n{Fore.YELLOW}ΑΠΟΠΟΙΗΣΗ ΕΥΘΥΝΗΣ: Σαρώστε μόνο στόχους που σας ανήκουν ή έχετε ρητή άδεια για δοκιμή.{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Εκκίνηση σάρωσης OSINT. Αυτό μπορεί να πάρει λίγο χρόνο...{Style.RESET_ALL}")
            
            # Εκτέλεση του σαρωτή
            report, folder = run_checks(target=target_input, threads=threads, full_ports=full_ports, out_formats=out_formats, dir_words=dir_words, sub_words=sub_words, verbose=verbose)

            if folder and 'html' in out_formats and webbrowser.get('w3m').name != 'w3m': # w3m είναι ο προεπιλεγμένος του Termux
                 try:
                     report_path = os.path.join(folder, 'report.html')
                     if os.path.exists(report_path):
                         print(f"\n{Fore.YELLOW}[*] Opening HTML report in default browser: {report_path}{Style.RESET_ALL}")
                         webbrowser.open_new_tab(f'file://{report_path}')
                 except Exception as e:
                     print(f"[WARNING] Could not open web browser automatically: {e}")

            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")
            

        def directory_bruteforcer(self):
            """Directory and file bruteforcer - ΑΠΟΔΟΤΙΚΗ ΠΙΣΙΝΑ ΝΗΜΑΤΩΝ"""
            print(f"\n{Fore.CYAN}📁 BRUTEFORCER ΚΑΤΑΛΟΓΩΝ{Style.RESET_ALL}")
            if not REQUESTS_AVAILABLE:
                print(f"{Fore.RED}❌ Η ενότητα 'requests' απαιτείται.{Style.RESET_ALL}")
                return

            base_url = input(f"{Fore.WHITE}Εισάγετε βασικό URL (π.χ., http://example.com): {Style.RESET_ALL}").strip()
            if not base_url.startswith(('http://', 'https://')):
                base_url = 'http://' + base_url
            if base_url.endswith('/'):
                base_url = base_url[:-1]

            common_paths = [ # Μια μικρή ενσωματωμένη λίστα
                'admin', 'administrator', 'login', 'wp-admin', 'phpmyadmin', 'cpanel', 
                'webmail', 'backup', 'test', 'dev', 'api', 'uploads', 'images', 'css', 
                'js', 'includes', 'logs', 'config', 'install', 'phpinfo.php', 'info.php',
                '.git', '.svn', 'robots.txt', 'sitemap.xml'
            ]
            
            list_choice = input(f"{Fore.WHITE}Χρήση (1) Κοινής ενσωματωμένης λίστας ή (2) Προσαρμοσμένης λίστας λέξεων (αρχείο); (1/2): {Style.RESET_ALL}").strip()
            wordlist = common_paths
            if list_choice == '2':
                wordlist_path = input(f"{Fore.WHITE}Εισάγετε διαδρομή αρχείου λίστας λέξεων: {Style.RESET_ALL}").strip()
                try:
                    with open(wordlist_path, 'r') as f:
                        wordlist = [line.strip() for line in f if line.strip()]
                    if not wordlist:
                        print(f"{Fore.RED}❌ Η προσαρμοσμένη λίστα λέξεων είναι κενή.{Style.RESET_ALL}")
                        return
                except FileNotFoundError:
                    print(f"{Fore.RED}❌ Το αρχείο λίστας λέξεων δεν βρέθηκε.{Style.RESET_ALL}")
                    return

            print(f"[*] Εκκίνηση directory bruteforce στο {base_url} με {len(wordlist)} διαδρομές και {self.max_workers} νήματα εργασίας...")

            found_paths = {}
            lock = threading.Lock()
            
            def check_path(path):
                url = f"{base_url}/{path.lstrip('/')}"
                try:
                    response = requests.get(url, headers=HEADERS, timeout=self.scan_timeout, verify=False, allow_redirects=True)
                    if response.status_code in [200, 301, 302]: # Επιτυχία ή ανακατεύθυνση
                        with lock:
                            if url not in found_paths: # Μόνο η πρώτη ανακαλύψεις
                                found_paths[url] = response.status_code
                                print(f"{Fore.GREEN}[+] Βρέθηκε ({response.status_code}): {url}{Style.RESET_ALL}")
                                self.record_audit_finding(
                                    base_url, 'Directory Bruteforce', f'Found Path {path}',
                                    f'Path returned status code {response.status_code}: {url}', 
                                    'Medium' if response.status_code == 200 else 'Informational'
                                )
                except requests.exceptions.RequestException:
                    pass # Αγνοήστε τα σφάλματα σύνδεσης

            try:
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    list(executor.map(check_path, wordlist))
            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα κατά τη διάρκεια του bruteforce: {e}{Style.RESET_ALL}")
                
            print(f"\n{Fore.GREEN}✅ Η Σάρωση Bruteforce Ολοκληρώθηκε.{Style.RESET_ALL}")
            if not found_paths:
                print(f"{Fore.YELLOW}Δεν βρέθηκαν κοινοί κατάλογοι.{Style.RESET_ALL}")

            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")

        def ssh_bruteforcer(self):
            print(f"\n{Fore.CYAN}🔐 SSH BRUTEFORCER (Χωρίς Banner){Style.RESET_ALL}")
            if not PARAMIKO_AVAILABLE or not paramiko:
                print(f"{Fore.RED}❌ Η ενότητα 'paramiko' απαιτείται για τη λειτουργικότητα SSH.{Style.RESET_ALL}")
                return

            target = input(f"{Fore.WHITE}Εισάγετε στόχο SSH IP/Όνομα κεντρικού υπολογιστή: {Style.RESET_ALL}").strip()
            port_input = input(f"{Fore.WHITE}Εισάγετε θύρα SSH (προεπιλογή 22): {Style.RESET_ALL}").strip()
            port = int(port_input) if port_input.isdigit() else 22
            
            username_input = input(f"{Fore.WHITE}Εισάγετε Όνομα Χρήστη (ή διαδρομή αρχείου): {Style.RESET_ALL}").strip()
            password_input = input(f"{Fore.WHITE}Εισάγετε Κωδικό Πρόσβασης (ή διαδρομή αρχείου): {Style.RESET_ALL}").strip()
            
            # Βοηθητική συνάρτηση για τη φόρτωση λιστών
            def load_creds(input_str, default_list):
                if os.path.exists(input_str):
                    try:
                        with open(input_str, 'r') as f:
                            return [line.strip() for line in f if line.strip()]
                    except Exception as e:
                        print(f"{Fore.RED}❌ Σφάλμα φόρτωσης αρχείου: {e}{Style.RESET_ALL}")
                        return []
                elif not input_str:
                    return default_list.split(',')
                else:
                    return [input_str]

            usernames = load_creds(username_input, self.config['common_usernames'])
            passwords = load_creds(password_input, self.config['common_passwords'])

            if not usernames or not passwords:
                print(f"{Fore.RED}❌ Δεν υπάρχουν ονόματα χρηστών ή κωδικοί πρόσβασης για δοκιμή.{Style.RESET_ALL}")
                return

            print(f"[*] Προσπάθεια brute-force στο {target}:{port} με {len(usernames)} ονόματα χρηστών και {len(passwords)} κωδικούς πρόσβασης... (Max Workers: {self.max_workers})")

            found_password = None
            lock = threading.Lock()

            def attempt_login(user_pass_tuple):
                nonlocal found_password
                user, password = user_pass_tuple

                if found_password: return # Διακοπή αν βρέθηκε

                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                try:
                    # Απενεργοποιήστε την προσπάθεια φόρτωσης κλειδιών συστήματος για ταχύτερη σύνδεση
                    client.connect(target, port=port, username=user, password=password, timeout=1.0, look_for_keys=False, allow_agent=False)
                    
                    with lock:
                        if not found_password:
                            found_password = (user, password)
                            print(f"\n{Fore.GREEN}🎉 [ΕΠΙΤΥΧΙΑ] Τα διαπιστευτήρια βρέθηκαν! {user}:{password}{Style.RESET_ALL}")
                            self.record_audit_finding(
                                target, 'SSH Bruteforce', 'Successful Login',
                                f'Credentials found: {user}:{password}', 'Critical'
                            )
                            # Ανάγκαση τερματισμού
                            raise Exception("SUCCESS_BREAK")

                except paramiko.AuthenticationException:
                    with lock:
                        print(f"  [FAIL] Αποτυχία ελέγχου ταυτότητας: {user}:{password}")
                except Exception as e:
                    if str(e) == "SUCCESS_BREAK":
                        return
                    with lock:
                        if 'timeout' in str(e).lower() or 'refused' in str(e).lower():
                            print(f"  [ERROR] Σφάλμα σύνδεσης/χρονομέτρησης για {target}:{port} - {e}")
                        # else: # Εξαιρέσεις γενικά
                            # print(f"  [ERROR] Unhandled SSH error for {user}:{password}: {e}")
                finally:
                    client.close()

            try:
                credentials_to_test = [(u, p) for u in usernames for p in passwords]
                
                # Δημιουργία μιας πισίνας νήματος για τη δοκιμή διαπιστευτηρίων
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    # Χρήση list() για να περιμένουμε να τελειώσουν όλες οι εργασίες
                    list(executor.map(attempt_login, credentials_to_test))

            except Exception as e:
                # Μόνο για να πιάσουμε το SUCCESS_BREAK αν πεταχτεί από το map
                if str(e) != "SUCCESS_BREAK":
                    print(f"{Fore.RED}❌ Unhandled error during SSH bruteforce: {e}{Style.RESET_ALL}")

            if not found_password:
                print(f"{Fore.RED}❌ Δεν βρέθηκε έγκυρος κωδικός πρόσβασης στην κοινή λίστα.{Style.RESET_ALL}")

            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")

        # --- Διαχείριση Δεδομένων & Βάσης Δεδομένων (Δεν απαιτείται Root) ---
        def view_audit_logs(self):
            print(f"\n{Fore.CYAN}📊 ΑΡΧΕΙΑ ΚΑΤΑΓΡΑΦΗΣ & ΕΥΡΗΜΑΤΑ ΕΛΕΓΧΟΥ{Style.RESET_ALL}")
            with sqlite3.connect(self.audit_db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT target, audit_type, finding_title, description, severity, timestamp 
                    FROM audit_results 
                    ORDER BY timestamp DESC 
                    LIMIT 50
                ''')
                rows = cursor.fetchall()

                if not rows:
                    print(f"{Fore.YELLOW}Δεν υπάρχουν ευρήματα ελέγχου ακόμη.{Style.RESET_ALL}")
                else:
                    print(f"{Fore.GREEN}Πρόσφατα Ευρήματα Ελέγχου:{Style.RESET_ALL}")
                    for row in rows:
                        target, audit_type, title, desc, severity, timestamp = row
                        color = Fore.RED if severity == 'Critical' else Fore.YELLOW if severity in ['High', 'Medium'] else Fore.GREEN
                        
                        print(f"\n{color}[{severity}] {audit_type} - {title}{Style.RESET_ALL}")
                        print(f"  Στόχος: {target}")
                        print(f"  Περιγραφή: {desc}")
                        print(f"  Ώρα: {timestamp}")

            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")

        def export_audit_logs(self):
            print(f"\n{Fore.CYAN}💾 ΕΞΑΓΩΓΗ ΑΡΧΕΙΩΝ ΚΑΤΑΓΡΑΦΗΣ ΕΛΕΓΧΟΥ{Style.RESET_ALL}")
            export_file = os.path.join(self.save_dir, f"audit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            
            try:
                with sqlite3.connect(self.audit_db_name) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM audit_results ORDER BY timestamp DESC')
                    rows = cursor.fetchall()

                    with open(export_file, 'w', encoding='utf-8') as f:
                        f.write("ΠΡΟΗΓΜΕΝΑ ΕΡΓΑΛΕΙΑ ΔΙΚΤΥΟΥ - ΕΞΑΓΩΓΗ ΑΡΧΕΙΩΝ ΚΑΤΑΓΡΑΦΗΣ ΕΛΕΓΧΟΥ\n")
                        f.write(f"Ημερομηνία Εξαγωγής: {datetime.now()}\n")
                        f.write("="*60 + "\n\n")

                        for row in rows:
                            f.write(f"Target: {row[1]}\n")
                            f.write(f"Type: {row[2]}\n")
                            f.write(f"Title: {row[3]}\n")
                            f.write(f"Description: {row[4]}\n")
                            f.write(f"Severity: {row[5]}\n")
                            f.write(f"Time: {row[6]}\n")
                            f.write("-" * 50 + "\n")
                
                print(f"{Fore.GREEN}✅ Τα αρχεία καταγραφής ελέγχου εξήχθησαν στο {export_file}{Style.RESET_ALL}")

            except Exception as e:
                print(f"{Fore.RED}❌ Σφάλμα κατά την εξαγωγή αρχείων καταγραφής: {e}{Style.RESET_ALL}")

            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")

        def manage_trusted_networks(self):
            print(f"\n{Fore.CYAN}⭐ ΔΙΑΧΕΙΡΙΣΗ ΕΜΠΙΣΤΕΥΤΩΝ ΔΙΚΤΥΩΝ{Style.RESET_ALL}")
            print("1. Προσθήκη εμπιστευτού BSSID")
            print("2. Αφαίρεση εμπιστευτού BSSID")
            print("3. Προβολή εμπιστευτών BSSID")
            choice = input(f"{Fore.WHITE}Επιλέξτε επιλογή (1-3): {Style.RESET_ALL}").strip()
            
            if choice == '1':
                bssid = input(f"{Fore.WHITE}Εισάγετε BSSID προς προσθήκη (π.χ., AA:BB:CC:DD:EE:FF): {Style.RESET_ALL}").strip().upper()
                if not re.match(r'^([0-9A-F]{2}:){5}[0-9A-F]{2}$', bssid):
                    print(f"{Fore.RED}❌ Μη έγκυρη μορφή BSSID.{Style.RESET_ALL}")
                    return
                
                if bssid in self.trusted_bssids:
                    print(f"{Fore.YELLOW}Το BSSID βρίσκεται ήδη στη λίστα εμπιστευτών.{Style.RESET_ALL}")
                else:
                    self.trusted_bssids.add(bssid)
                    self.known_networks['trusted_bssids'] = list(self.trusted_bssids)
                    self.save_known_networks()
                    print(f"{Fore.GREEN}✅ Το {bssid} προστέθηκε στα εμπιστευτά δίκτυα.{Style.RESET_ALL}")

            elif choice == '2':
                if self.trusted_bssids:
                    print(f"{Fore.YELLOW}Τρέχοντα εμπιστευτά BSSID:{Style.RESET_ALL}")
                    for bssid in self.trusted_bssids:
                        print(f" - {bssid}")
                    bssid = input(f"{Fore.WHITE}Εισάγετε BSSID προς αφαίρεση: {Style.RESET_ALL}").strip().upper()
                    
                    if bssid in self.trusted_bssids:
                        self.trusted_bssids.remove(bssid)
                        self.known_networks['trusted_bssids'] = list(self.trusted_bssids)
                        self.save_known_networks()
                        print(f"{Fore.GREEN}✅ Το {bssid} αφαιρέθηκε από τα εμπιστευτά δίκτυα.{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}❌ Το BSSID δεν βρέθηκε στη λίστα εμπιστευτών.{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}Δεν υπάρχουν εμπιστευτά δίκτυα προς αφαίρεση.{Style.RESET_ALL}")

            elif choice == '3':
                if self.trusted_bssids:
                    print(f"{Fore.GREEN}✅ Εμπιστευτά Δίκτυα:{Style.RESET_ALL}")
                    for bssid in self.trusted_bssids:
                        print(f" - {bssid}")
                else:
                    print(f"{Fore.YELLOW}Δεν έχουν διαμορφωθεί εμπιστευτά δίκτυα.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ Μη έγκυρη επιλογή.{Style.RESET_ALL}")

            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")

        def clear_database(self):
            print(f"\n{Fore.RED}🧹 ΕΚΚΑΘΑΡΙΣΗ ΒΑΣΗΣ ΔΕΔΟΜΕΝΩΝ{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Αυτό θα διαγράψει όλο το ιστορικό σάρωσης και τα αρχεία καταγραφής ελέγχου.{Style.RESET_ALL}")
            confirm = input(f"{Fore.WHITE}Πληκτρολογήστε 'DELETE' για επιβεβαίωση: {Style.RESET_ALL}").strip()
            
            if confirm == 'DELETE':
                try:
                    with sqlite3.connect(self.wifi_db_name) as conn:
                        cursor = conn.cursor()
                        cursor.execute('DELETE FROM network_scans')
                        conn.commit()
                    with sqlite3.connect(self.audit_db_name) as conn:
                        cursor = conn.cursor()
                        cursor.execute('DELETE FROM audit_results')
                        conn.commit()
                    
                    print(f"{Fore.GREEN}✅ Όλες οι βάσεις δεδομένων εκκαθαρίστηκαν.{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}❌ Σφάλμα κατά την εκκαθάριση βάσεων δεδομένων: {e}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Η λειτουργία εκκαθάρισης ακυρώθηκε.{Style.RESET_ALL}")

            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")

        def system_settings(self):
            while True:
                print(f"\n{Fore.CYAN}⚙️ ΡΥΘΜΙΣΕΙΣ & ΔΙΑΜΟΡΦΩΣΗ ΣΥΣΤΗΜΑΤΟΣ{Style.RESET_ALL}")
                print(f"{Fore.CYAN}--- Τρέχουσα Διαμόρφωση ---{Style.RESET_ALL}")
                print(f"1. Διάστημα Σάρωσης (δευτερόλεπτα): {self.config['scan_interval']}")
                print(f"2. Μέγιστος Αριθμός Νημάτων Εργασίας Σάρωσης: {self.config['max_scan_workers']}")
                print(f"3. Κορυφαίες Θύρες (Σάρωση Θυρών): {self.config['top_ports']}")
                print(f"4. Κοινά Ονόματα Χρηστών (Bruteforce): {self.config['common_usernames']}")
                print(f"5. Κοινοί Κωδικοί Πρόσβασης (Bruteforce): {self.config['common_passwords']}")
                print(f"6. Επαναφορά στις προεπιλογές")
                print(f"0. Επιστροφή στο Κύριο Μενού")
                print("-" * 50)
                
                choice = input(f"{Fore.WHITE}Επιλέξτε επιλογή (0-6): {Style.RESET_ALL}").strip()
                
                if choice == '0':
                    return

                if choice == '1':
                    try:
                        interval = int(input(f"{Fore.WHITE}Νέο διάστημα σάρωσης (δευτερόλεπτα): {Style.RESET_ALL}").strip())
                        self.config['scan_interval'] = max(10, interval) # Ελάχιστο 10 δευτερόλεπτα
                    except ValueError:
                        print(f"{Fore.RED}❌ Μη έγκυρος αριθμός.{Style.RESET_ALL}")
                elif choice == '2':
                    try:
                        threads = int(input(f"{Fore.WHITE}Νέος μέγιστος αριθμός νημάτων εργασίας σάρωσης: {Style.RESET_ALL}").strip())
                        # Όριο νήματος από 1 έως 100
                        self.config['max_scan_workers'] = max(1, min(100, threads))
                        self.max_workers = self.config['max_scan_workers']
                    except ValueError:
                        print(f"{Fore.RED}❌ Μη έγκυρος αριθμός.{Style.RESET_ALL}")
                elif choice == '3':
                    ports = input(f"{Fore.WHITE}Νέες κορυφαίες θύρες (χωρισμένες με κόμμα): {Style.RESET_ALL}").strip()
                    if ports:
                        self.config['top_ports'] = ports
                elif choice == '4':
                    usernames = input(f"{Fore.WHITE}Νέα κοινά ονόματα χρηστών (χωρισμένα με κόμμα): {Style.RESET_ALL}").strip()
                    if usernames:
                        self.config['common_usernames'] = usernames
                elif choice == '5':
                    passwords = input(f"{Fore.WHITE}Νέοι κοινοί κωδικοί πρόσβασης (χωρισμένοι με κόμμα): {Style.RESET_ALL}").strip()
                    if passwords:
                        self.config['common_passwords'] = passwords
                elif choice == '6':
                    print(f"{Fore.YELLOW}Επαναφορά στις προεπιλογές...{Style.RESET_ALL}")
                    self.load_config() # Επαναφόρτωση προεπιλογών
                else:
                    print(f"{Fore.RED}❌ Μη έγκυρη επιλογή.{Style.RESET_ALL}")
                    continue

                self.save_config()
                print(f"{Fore.GREEN}✅ Η διαμόρφωση ενημερώθηκε.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")

        def show_about(self):
            print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
            print(f"{Fore.CYAN} ΠΡΟΗΓΜΕΝΗ ΕΡΓΑΛΕΙΟΘΗΚΗ ΔΙΚΤΥΟΥ & ΑΣΦΑΛΕΙΑΣ{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Έκδοση: Combined & Optimized v2.0{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Σκοπός: Παροχή εργαλείων ασφάλειας δικτύου χωρίς απαιτήσεις root{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Συμβατότητα: Linux, Termux (Android){Style.RESET_ALL}")
            print(f"\n{Fore.CYAN}Βασικές Ενότητες:{Style.RESET_ALL}")
            print(f"  - SSH Defender (Honeypot): Παρακολούθηση brute-force επιθέσεων.")
            print(f"  - Network Scanner: Σάρωση θυρών και ανακάλυψη κεντρικών υπολογιστών.")
            print(f"  - Wi-Fi/Mobile Info: Χρήση Termux:API για τοπικές πληροφορίες.")
            print(f"  - OSINTDS Scanner: Συλλογή πληροφοριών URL και δοκιμή ευπαθειών.")
            
            print(f"\n{Fore.YELLOW}Απαιτούμενες Εξαρτήσεις (μερικές): requests, colorama, paramiko, dnspython, python-whois.{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")


        def display_menu(self):
            menu_options = [
                # Wi-Fi / Τοπικό
                "Μία Σάρωση Wi-Fi", 
                "Προβολή Τρέχουσας Σύνδεσης", 
                "Εναλλαγή Wi-Fi (Termux:API)",
                "Προβολή Πληροφοριών Κινητής/SIM (Termux:API)",
                "--- Σάρωση Δικτύου & Ανακάλυψη ---",
                "Περιτύλιγμα Nmap (Απαιτείται το πακέτο 'nmap')",
                "Σάρωση Θυρών TCP (Γρήγορη)",
                "Προηγμένη Ανακάλυψη Δικτύου",
                "Υπολογιστής Υποδικτύου",
                "--- Internet & Διαγνωστικά ---",
                "Εκτέλεση Δοκιμής Ταχύτητας Internet",
                "Δημόσια IP & Δοκιμή Διαρροής DNS",
                "Αναζήτηση WHOIS",
                "Αναζήτηση DNS",
                "Traceroute",
                "--- Ασφάλεια & Έλεγχος ---",
                "Σαρωτής OSINTDS",
                "Directory Bruteforcer",
                "SSH Bruteforcer (Κωδικός/Λίστα Λέξεων)",
                "--- Honeypot / Άμυνα ---",
                "Εκτέλεση SSH Defender (Honeypot)",
                "--- Δεδομένα & Διαχείριση ---",
                "Προβολή Αρχείων Καταγραφής Ελέγχου",
                "Εξαγωγή Αρχείων Καταγραφής Ελέγχου",
                "Διαχείριση Εμπιστευτών Δικτύων",
                "Εκκαθάριση Βάσης Δεδομένων Σάρωσης/Ελέγχου",
                "--- Σύστημα & Έξοδος ---",
                "Ρυθμίσεις Συστήματος",
                "Σχετικά με Αυτό το Εργαλείο",
                "Έξοδος (Q/0)" # 0 is also exit
            ]

            while True:
                # Καθαρισμός οθόνης (προαιρετικό)
                # os.system('clear' if os.name != 'nt' else 'cls')

                # Απλές επιλογές μενού κειμένου
                print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
                print(f"{Fore.CYAN} ΠΡΟΗΓΜΕΝΗ ΕΡΓΑΛΕΙΟΘΗΚΗ ΔΙΚΤΥΟΥ & ΑΣΦΑΛΕΙΑΣ{Style.RESET_ALL}")
                print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
                
                for i, option in enumerate(menu_options):
                    if option.startswith("---"):
                        print(f"{Fore.YELLOW}{option}{Style.RESET_ALL}")
                    else:
                        # 0 για Έξοδο, οπότε η αρίθμηση ξεκινά από 1
                        idx = i if i <= 3 else i - 1 if i <= 8 else i - 2 if i <= 15 else i - 3 if i <= 19 else i - 4 if i <= 24 else i - 5 
                        
                        if option.endswith("(Q/0)"):
                            print(f"{Fore.WHITE}{0:2}. {option}{Style.RESET_ALL}")
                        elif option.startswith("---"):
                            continue
                        else:
                             print(f"{Fore.WHITE}{idx:2}. {option}{Style.RESET_ALL}")
                        

                print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
                
                user_input = input(f"{Fore.WHITE}Επιλέξτε επιλογή (0-{len(menu_options)-5}): {Style.RESET_ALL}").strip()

                if user_input.lower() in ['0', 'q']:
                    break

                try:
                    selected_idx = int(user_input)
                except ValueError:
                    selected_idx = -1

                # Χειροκίνητη αντιστοίχιση επιλογής σε μεθόδους
                if selected_idx == 1:
                    self.single_wifi_scan()
                elif selected_idx == 2:
                    self.view_current_connection()
                elif selected_idx == 3:
                    self.toggle_wifi()
                elif selected_idx == 4:
                    self.get_mobile_data_info()
                elif selected_idx == 5:
                    self.nmap_wrapper()
                elif selected_idx == 6:
                    self.run_port_scan()
                elif selected_idx == 7:
                    self.network_discovery()
                elif selected_idx == 8:
                    self.subnet_calculator()
                elif selected_idx == 9:
                    self.run_internet_speed_test()
                elif selected_idx == 10:
                    self.run_dns_leak_test()
                elif selected_idx == 11:
                    self.run_whois_lookup()
                elif selected_idx == 12:
                    self.run_dns_lookup()
                elif selected_idx == 13:
                    self.run_traceroute()
                elif selected_idx == 14:
                    self.run_osintds_scanner()
                elif selected_idx == 15:
                    self.directory_bruteforcer()
                elif selected_idx == 16:
                    self.ssh_bruteforcer()
                elif selected_idx == 17:
                    # SSH Defender requires ThreadPoolExecutor, which is handled internally
                    # Needs a new executor specifically for the SSH Defender class
                    defender_executor = concurrent.futures.ThreadPoolExecutor(max_workers=50)
                    logger = Logger(
                        log_dir=os.path.join(self.save_dir, "ssh_defender_logs"), 
                        stats_file=os.path.join(self.save_dir, "ssh_defender_stats.json")
                    )
                    defender = SSHDefender(HOST, logger, defender_executor)
                    
                    print(f"\n{Fore.CYAN}--- SSH DEFENDER START ---{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}  1. Run Port Cycle (Rotate famous ports){Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}  2. Run Permanent Honeypot on Port 22{Style.RESET_ALL}")
                    defender_choice = input(f"{Fore.WHITE}  Select option (1/2): {Style.RESET_ALL}").strip()
                    
                    if defender_choice == '1':
                        defender.run_port_cycle()
                    elif defender_choice == '2':
                        defender.start_port_listener(22)
                        input(f"\n{Fore.YELLOW}Press Enter to stop monitoring...{Style.RESET_ALL}")
                        defender.stop_all_ports()
                        defender.logger.save_stats()
                        print(f"\n{Fore.GREEN}✅ SSH Defender terminated.{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}❌ Invalid choice. Returning to main menu.{Style.RESET_ALL}")
                        defender.stop_all_ports()
                        defender.logger.save_stats()
                        
                    # Εκτύπωση τελικών στατιστικών
                    summary = defender.logger.get_cumulative_stats_summary()
                    print(f"\n{Fore.CYAN}--- SSH DEFENDER CUMULATIVE STATS ---{Style.RESET_ALL}")
                    for key, value in summary.items():
                        if isinstance(value, list):
                            print(f"  {key}:")
                            for item in value:
                                print(f"    - {item}")
                        else:
                            print(f"  {key}: {value}")
                    print(f"{Fore.CYAN}---------------------------------------{Style.RESET_ALL}")
                    input(f"\n{Fore.YELLOW}Πατήστε Enter για να συνεχίσετε...{Style.RESET_ALL}")

                elif selected_idx == 18:
                    self.view_audit_logs()
                elif selected_idx == 19:
                    self.export_audit_logs()
                elif selected_idx == 20:
                    self.manage_trusted_networks()
                elif selected_idx == 21:
                    self.clear_database()
                elif selected_idx == 22:
                    self.system_settings()
                elif selected_idx == 23:
                    self.show_about()
                else:
                    print(f"{Fore.RED}❌ Άκυρη επιλογή: {user_input}{Style.RESET_ALL}")
                    time.sleep(1)


    if len(sys.argv) > 1 and sys.argv[1] == '--install-deps':
        auto_install_dependencies()
        print(f"\n{Fore.GREEN}Please run the script again to start the application.{Style.RESET_ALL}")
        return

    # Έλεγχος αν υπάρχει το colorama για να μην εκτυπώνουμε τίποτα χωρίς χρώμα
    try:
        from colorama import Fore, Style
    except ImportError:
        class DummyColor:
            def __getattr__(self, name): return ''
        Fore = Back = Style = DummyColor()

    # Έλεγχος για Termux
    is_termux = os.path.exists('/data/data/com.termux')
    
    # Μήνυμα καλωσορίσματος
    print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}           ΠΡΟΗΓΜΕΝΗ ΕΡΓΑΛΕΙΟΘΗΚΗ ΔΙΚΤΥΟΥ & ΑΣΦΑΛΕΙΑΣ{Style.RESET_ALL}")
    print(f"{Fore.CYAN}                   Συνδυασμένη & Βελτιστοποιημένη v2.0{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Πλατφόρμα: {'Termux (Android)' if is_termux else 'Linux'}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Απαιτήσεις: Δεν χρειάζεται πρόσβαση root!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Αρχικοποίηση...{Style.RESET_ALL}")
    
    # Έλεγχος για κρίσιμες εξαρτήσεις που λείπουν
    missing_critical = []
    if not REQUESTS_AVAILABLE:
        missing_critical.append("requests")
    
    if missing_critical:
        print(f"\n{Fore.RED}❌ Λείπουν κρίσιμες εξαρτήσεις:{Style.RESET_ALL}")
        for dep in missing_critical:
            print(f"  - {dep}")
        print(f"\n{Fore.YELLOW}Εκτελέστε: python {sys.argv[0]} --install-deps{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Ή εγκαταστήστε τα πακέτα που λείπουν χειροκίνητα.{Style.RESET_ALL}")
        sys.exit(1)
    
    # Όλα καλά, εκκίνηση εφαρμογής
    try:
        app = AdvancedNetworkTools()
        app.display_menu()
    except Exception as e:
        print(f"\n{Fore.RED}❌ Ένα μη αναμενόμενο σφάλμα συνέβη: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main_app_loop()