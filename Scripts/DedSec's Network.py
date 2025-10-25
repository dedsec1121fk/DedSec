#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Advanced Network & Security Toolkit
Combined, optimized, and enhanced for Termux.
Runs 100% without root access.
Efficiently designed for low-resource devices (e.g., 2GB RAM).
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
import select  # Added for SSH Defender
import math    # Added for SSH Defender
import queue
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor # Added for SSH Defender
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
csv = None # For OSINTDS module

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
    # Fallback if colorama isn't installed
    class DummyColor:
        def __getattr__(self, name): return ''
    Fore = Back = Style = DummyColor()

# 3. Dynamic import attempts for other modules
def _try_import(module_name, global_var_name):
    """Dynamically imports a module and sets a global flag."""
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
_try_import('csv', 'csv') # For OSINTDS module


# ==============================================================================
# SSH DEFENDER - GLOBAL CONSTANTS
# ==============================================================================

# Ranked list of famous SSH/Honeypot ports for cycling
FAMOUS_SSH_PORTS = [
    22,    # Standard SSH
    2222,  # Common alternative SSH
    80,    # HTTP (often scanned by bots looking for any open port)
    443,   # HTTPS (often scanned by bots looking for any open port)
    21,    # FTP (often brute-forced)
    23     # Telnet (often brute-forced)
]

# Configuration (Paths will be set by the AdvancedNetworkTools class)
HOST = '0.0.0.0'
# BASE_DIR, LOG_DIR, STATS_FILE are now set dynamically in run_ssh_defender
EMPTY_CHECK_INTERVAL = 60  # 1 minute

# Common SSH banners to mimic real servers
SSH_BANNERS = [
    b"SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.3\r\n",
    b"SSH-2.0-OpenSSH_7.4p1 Debian-10+deb9u7\r\n", 
    b"SSH-2.0-OpenSSH_7.9p1 FreeBSD-20200824\r\n",
    b"SSH-2.0-libssh-0.9.3\r\n"
]

# Attack thresholds
MAX_ATTEMPTS = 5         # Max attempts before recording full log/ip ban
ATTACK_THRESHOLD = 50    # Number of attempts in 5 minutes to trigger warning/stop cycle


# ==============================================================================
# SSH DEFENDER - Logger Class
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
        """Loads cumulative stats from JSON file."""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"total_attacks": 0, "ip_stats": {}, "port_stats": {}}

    def save_stats(self):
        """Saves cumulative stats to JSON file."""
        with self.lock:
            try:
                with open(self.stats_file, 'w') as f:
                    json.dump(self.attack_stats, f, indent=4)
            except IOError as e:
                print(f"Error saving stats file: {e}")

    def log_attempt(self, ip, port, message, is_full_log=False):
        """Records a single login attempt and updates statistics."""
        timestamp = datetime.now().isoformat()
        
        with self.lock:
            # 1. Update session attempts
            self.current_session_attempts[ip] = self.current_session_attempts.get(ip, 0) + 1
            
            # 2. Update cumulative stats
            self.attack_stats['total_attacks'] = self.attack_stats.get('total_attacks', 0) + 1
            
            # IP stats
            ip_data = self.attack_stats['ip_stats'].setdefault(ip, {"count": 0, "last_attempt": None, "first_attempt": timestamp})
            ip_data['count'] += 1
            ip_data['last_attempt'] = timestamp
            
            # Port stats
            port_key = str(port)
            self.attack_stats['port_stats'].setdefault(port_key, 0)
            self.attack_stats['port_stats'][port_key] += 1
            
            # 3. Write log file if full log is requested or threshold is met
            if is_full_log:
                log_filename = os.path.join(self.log_dir, f"{ip}.log")
                try:
                    with open(log_filename, 'a') as f:
                        f.write(f"[{timestamp}] PORT:{port} - {message}\n")
                except IOError as e:
                    print(f"Error writing log file: {e}")
                    
            # 4. Save cumulative stats periodically
            if self.attack_stats['total_attacks'] % 10 == 0:
                self.save_stats()
                
    def get_session_total_attempts(self):
        """Returns the total number of attempts in the current session."""
        return sum(self.current_session_attempts.values())

    def get_current_attempts(self):
        """Returns the number of attempts and time elapsed since session start."""
        attempts = self.get_session_total_attempts()
        time_elapsed = time.time() - self.session_start_time
        return attempts, time_elapsed
        
    def reset_session_stats(self):
        """Resets session-based stats (used when cycling ports)."""
        with self.lock:
            self.current_session_attempts = {}
            self.session_start_time = time.time()
            
    def get_cumulative_stats_summary(self):
        """Returns a formatted summary of cumulative stats."""
        total = self.attack_stats.get('total_attacks', 0)
        
        # Get top 3 IPs
        ip_list = sorted(self.attack_stats['ip_stats'].items(), key=lambda item: item[1]['count'], reverse=True)
        top_ips = [f"{ip} ({data['count']} attempts)" for ip, data in ip_list[:3]]
        
        # Get top 3 Ports
        port_list = sorted(self.attack_stats['port_stats'].items(), key=lambda item: item[1], reverse=True)
        top_ports = [f"{port} ({count} attacks)" for port, count in port_list[:3]]
        
        return {
            "Total Attacks": total,
            "Top Attacking IPs": top_ips if top_ips else ["N/A"],
            "Top Targeted Ports": top_ports if top_ports else ["N/A"]
        }

# ==============================================================================
# SSH DEFENDER - Core Logic Class
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
        
        # Base directory is handled by the logger

    def _handle_connection(self, client_socket, addr):
        """Handles the interaction with a connecting client (the honeypot logic)."""
        ip, port = addr
        
        # Select a random banner to mimic a real SSH server
        banner = random.choice(SSH_BANNERS)
        
        try:
            # 1. Send the SSH banner immediately
            client_socket.sendall(banner)
            
            # 2. Start interactive session (wait for input)
            attempt_count = 0
            
            while self.running:
                # Use select for a non-blocking read with a timeout
                ready_to_read, _, _ = select.select([client_socket], [], [], 3.0)
                
                if ready_to_read:
                    data = client_socket.recv(1024)
                    if not data:
                        break # Connection closed by client
                        
                    data_str = data.decode('utf-8', errors='ignore').strip()
                    self.logger.log_attempt(ip, self.current_port, f"Data Received: '{data_str}'")
                    
                    attempt_count += 1
                    
                    # Log full session if max attempts reached for this connection
                    is_full_log = (attempt_count >= MAX_ATTEMPTS)
                    
                    # Update logger with attempt details
                    self.logger.log_attempt(ip, self.current_port, f"Attempt {attempt_count}: {data_str}", is_full_log=is_full_log)
                    
                    # Respond with an SSH KEXINIT or similar response to simulate a real server
                    # Simple response to keep the connection open for more brute-force attempts
                    if data_str.startswith("SSH"):
                         # Simulate a KEXINIT response (random 16-byte cookie, etc.)
                        kex_response = b'SSH-2.0-SSH Defender\r\n' 
                        client_socket.sendall(kex_response)
                        
                    elif data_str.lower().startswith(("user", "root", "admin", "login")):
                        # Simple response to prompt for password
                        client_socket.sendall(b"Password:\r\n") 
                        
                    elif data_str.startswith("password"):
                        # Simple error response
                         client_socket.sendall(b"Permission denied, please try again.\r\n")

                    # If this connection is being brute-forced heavily, close it
                    if attempt_count >= MAX_ATTEMPTS * 2:
                        break

                else:
                    # Timeout, close connection
                    break 

        except socket.timeout:
            self.logger.log_attempt(ip, self.current_port, "Connection timed out.")
        except ConnectionResetError:
            self.logger.log_attempt(ip, self.current_port, "Connection reset by peer.")
        except Exception as e:
            self.logger.log_attempt(ip, self.current_port, f"Unhandled connection error: {e}")
        finally:
            client_socket.close()

    def start_port_listener(self, port):
        """Starts the main socket listener on a specific port."""
        if self.listener_thread or self.listener_socket:
            self.stop_all_ports()
        
        self.current_port = port
        
        try:
            self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listener_socket.bind((self.host, port))
            self.listener_socket.listen(5)
            print(f"{Fore.GREEN}✅ SSH Defender listening on {self.host}:{port}...{Style.RESET_ALL}")
            self.running = True
            self.logger.reset_session_stats()
            
            self.listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
            self.listener_thread.start()
            
        except OSError as e:
            print(f"{Fore.RED}❌ Error binding to port {port}: {e}. (Perhaps another process is running or you lack permissions?){Style.RESET_ALL}")
            self.running = False
            self.listener_socket = None
            self.current_port = None
            
        except Exception as e:
            print(f"{Fore.RED}❌ Unhandled error starting listener on port {port}: {e}{Style.RESET_ALL}")
            self.running = False
            self.listener_socket = None
            self.current_port = None

    def _listener_loop(self):
        """The main loop for accepting connections."""
        while self.running:
            try:
                # Use select to wait for connections with a timeout
                ready_to_read, _, _ = select.select([self.listener_socket], [], [], 1.0)
                
                if ready_to_read and self.listener_socket in ready_to_read:
                    client_socket, addr = self.listener_socket.accept()
                    # Submit the connection handler to the thread pool
                    self.executor.submit(self._handle_connection, client_socket, addr)
                
            except socket.timeout:
                pass # Expected timeout
            except Exception as e:
                if self.running:
                    print(f"\n{Fore.RED}❌ Listener loop error on port {self.current_port}: {e}{Style.RESET_ALL}")
                    # Attempt a clean shutdown if the socket failed
                    self.stop_all_ports()
                    break
        
    def stop_all_ports(self):
        """Shuts down the listener socket and thread."""
        self.running = False
        if self.listener_socket:
            try:
                # Unblock the accept call
                self.listener_socket.shutdown(socket.SHUT_RDWR)
                self.listener_socket.close()
                self.listener_socket = None
                if self.listener_thread and self.listener_thread.is_alive():
                    self.listener_thread.join(timeout=2)
            except Exception:
                pass # Ignore errors on close
        self.current_port = None
        self.executor.shutdown(wait=False, cancel_futures=True)
        # Recreate executor to clear up old threads, if necessary for TUI restart
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=50)


    def run_port_cycle(self):
        """Runs the cycling through a list of famous ports."""
        self.cycle_mode = True
        
        for port_index, port in enumerate(FAMOUS_SSH_PORTS):
            
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}  STARTING MONITORING ON PORT: {port}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            self.start_port_listener(port)
            if not self.running:
                # Could not bind, skip to next port
                continue 
            
            start_time = time.time()
            
            # Monitoring loop for 5 minutes (or until an attack threshold is hit)
            while time.time() - start_time < 5 * 60:
                time.sleep(EMPTY_CHECK_INTERVAL) # Check every minute
                
                attempts, time_elapsed = self.logger.get_current_attempts()
                
                if attempts > ATTACK_THRESHOLD:
                    print(f"\n\n{Fore.RED}🚨 CRITICAL ATTACK DETECTED on port {port}!{Style.RESET_ALL}")
                    print(f"   {attempts} attempts in {int(time_elapsed)} seconds.")
                    print(f"{Fore.YELLOW}   Switching to permanent monitoring mode for this port.{Style.RESET_ALL}")
                    
                    self.stop_all_ports()
                    self.cycle_mode = False
                    
                    # Restart the listener and TUI for permanent monitoring
                    self.start_port_listener(port)
                    self.tui.run() # This call will block until user quits TUI
                    self.running = False
                    break # Exit the cycling loop
                
                # Update TUI (if running) with status
                if hasattr(self, 'tui') and self.tui.running:
                    self.tui.update_display()
                
            if not self.cycle_mode: # If we broke out due to critical attack
                break

            if port_index == len(FAMOUS_SSH_PORTS) - 1:
                print(f"\n\n{Fore.GREEN}✅ Finished monitoring all famous ports without significant attacks. Defender shutting down.{Style.RESET_ALL}")
                self.running = False
                break # Exit the cycling loop
                
            # No attack: Ask user to switch
            next_port = FAMOUS_SSH_PORTS[port_index + 1]
            user_input = input(f"\n\n{Fore.YELLOW}⏰ 5 minutes passed on port {port} without attacks.\nDo you want to switch to the next famous port ({next_port})? (y/n): {Style.RESET_ALL}")
            
            self.stop_all_ports()
            
            if user_input.lower() not in ['y']:
                print(f"\n{Fore.RED}🛑 User chose to stop port cycling. Defender shutting down.{Style.RESET_ALL}")
                self.running = False
                break
            
        # Final Cleanup
        self.running = False
        self.stop_all_ports()
        self.logger.save_stats()
        print(f"\n{Fore.GREEN}✅ SSH Defender terminated.{Style.RESET_ALL}")


# ==============================================================================
# SSH DEFENDER - Terminal User Interface (TUI)
# ==============================================================================

class DefenderTUI:
    
    def __init__(self, stdscr, defender):
        self.stdscr = stdscr
        self.defender = defender
        self.running = True
        self._init_curses()

    def _init_curses(self):
        """Initializes curses settings and colors."""
        curses.cbreak()
        curses.noecho()
        self.stdscr.keypad(True)
        try:
            curses.curs_set(0) # Hide cursor
        except curses.error:
            pass
            
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK) # Default
            curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Title
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Warning/Stats
            curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)   # Attack/Critical
            curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK) # Success

    def update_display(self):
        """Clears and redraws the TUI screen."""
        try:
            self.stdscr.clear()
            h, w = self.stdscr.getmaxyx()
            if h < 20 or w < 50:
                self.stdscr.addstr(0, 0, "Terminal too small...")
                self.stdscr.refresh()
                return
        except curses.error:
            return # Skip render if terminal is resizing

        try:
            # 1. Title Bar
            title = " SSH Defender - Honeypot Monitor "
            self.stdscr.attron(curses.A_BOLD | curses.color_pair(2))
            self.stdscr.addstr(0, w//2 - len(title)//2, title)
            self.stdscr.addstr(0, w - 18, f"Port: {self.defender.current_port or 'N/A'}".ljust(17))
            self.stdscr.attroff(curses.A_BOLD | curses.color_pair(2))
            
            # 2. Session Stats
            attempts, time_elapsed = self.defender.logger.get_current_attempts()
            status_color = curses.color_pair(5) if attempts < ATTACK_THRESHOLD * 0.2 else curses.color_pair(3)
            if attempts > ATTACK_THRESHOLD * 0.5:
                status_color = curses.color_pair(4)

            session_title = " Session Statistics "
            self.stdscr.attron(curses.A_BOLD | status_color)
            self.stdscr.addstr(2, w//2 - len(session_title)//2, session_title)
            self.stdscr.attroff(curses.A_BOLD | status_color)
            
            self.stdscr.addstr(3, 2, f"Total Attempts: {attempts}")
            self.stdscr.addstr(4, 2, f"Time Elapsed: {self._format_time(time_elapsed)}")
            self.stdscr.addstr(5, 2, f"Attack Threshold: {ATTACK_THRESHOLD} attempts / 5 mins")
            
            # Progress Bar (Simplified)
            bar_len = w - 4
            progress_ratio = min(1.0, attempts / ATTACK_THRESHOLD)
            fill_len = int(bar_len * progress_ratio)
            
            self.stdscr.addstr(6, 2, "Attack Level: ")
            self.stdscr.attron(status_color | curses.A_REVERSE)
            self.stdscr.addstr(6, 16, " " * fill_len)
            self.stdscr.attroff(status_color | curses.A_REVERSE)
            self.stdscr.addstr(6, 16 + fill_len, " " * (bar_len - fill_len - 15))

            # 3. Cumulative Stats
            cumulative_stats = self.defender.logger.get_cumulative_stats_summary()
            stats_title = " Cumulative Statistics "
            self.stdscr.attron(curses.A_BOLD | curses.color_pair(3))
            self.stdscr.addstr(8, w//2 - len(stats_title)//2, stats_title)
            self.stdscr.attroff(curses.A_BOLD | curses.color_pair(3))
            
            self.stdscr.addstr(9, 2, f"Total Attacks Recorded: {cumulative_stats['Total Attacks']}")
            
            y_start = 10
            self.stdscr.addstr(y_start, 2, "Top IPs:")
            for i, ip_stat in enumerate(cumulative_stats['Top Attacking IPs']):
                if y_start + i < h - 2:
                    self.stdscr.addstr(y_start + i, 12, ip_stat)
                
            y_start += 4
            self.stdscr.addstr(y_start, 2, "Top Ports:")
            for i, port_stat in enumerate(cumulative_stats['Top Targeted Ports']):
                if y_start + i < h - 2:
                    self.stdscr.addstr(y_start + i, 12, port_stat)

            # 4. Status/Key Bindings Bar
            status_text = "q: Quit | s: Save Stats"
            self.stdscr.attron(curses.A_REVERSE)
            self.stdscr.addstr(h-1, 0, status_text.ljust(w))
            self.stdscr.attroff(curses.A_REVERSE)
            
            self.stdscr.refresh()
        except curses.error:
            pass # Ignore errors (e.g., writing outside screen on resize)

    def _format_time(self, seconds):
        """Formats seconds into H:M:S string."""
        s = int(seconds)
        h = s // 3600
        s %= 3600
        m = s // 60
        s %= 60
        return f"{h:02}:{m:02}:{s:02}"
        
    def run(self):
        """The TUI interaction loop."""
        self.running = True
        self.stdscr.nodelay(True) # Non-blocking input
        
        while self.running and self.defender.running:
            try:
                self.update_display()
                key = self.stdscr.getch()
                
                if key == ord('q') or key == ord('Q') or key == 27:
                    self.running = False
                    self.defender.running = False # Signal defender to stop
                    break
                elif key == ord('s') or key == ord('S'):
                    self.defender.logger.save_stats()
                    self._display_message("Statistics saved successfully.")
                
                time.sleep(0.5) # Refresh rate
            except KeyboardInterrupt:
                self.running = False
                self.defender.running = False
            except curses.error:
                pass # Ignore TUI errors
            
        self.stdscr.nodelay(False)

    def _display_message(self, message):
        """Displays a message and waits for a keypress."""
        curses.curs_set(0)
        self.stdscr.nodelay(False)
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        
        lines = message.split('\n')
        
        # Center and display lines
        for i, line in enumerate(lines):
            y = h//2 - len(lines)//2 + i
            x = w//2 - len(line)//2
            if 0 <= y < h:
                try:
                    self.stdscr.addstr(y, x, line)
                except curses.error:
                    pass
                    
        # Wait for keypress message
        wait_msg = "Press any key to continue..."
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
# END OF SSH DEFENDER CODE
# ==============================================================================


def auto_install_dependencies():
    """
    Automatically install all required dependencies without root.
    Optimized to only install what is necessary.
    """
    print(f"{Fore.CYAN}🛠️ ADVANCED NETWORK TOOLS - Automatic Dependency Installation{Style.RESET_ALL}")
    print("="*70)
    print(f"{Fore.YELLOW}This will install all required packages without root access.{Style.RESET_ALL}")
    
    is_termux = os.path.exists('/data/data/com.termux')
    
    # System packages for Termux (no root required)
    # nmap is included for the Nmap Wrapper tool
    termux_packages = [
        'python', 'python-pip', 'curl', 'wget', 'nmap', 
        'inetutils', 'openssl-tool', 'ncurses-utils'
    ]
    
    # Python packages (pip) - Cleaned list of *only* used dependencies
    pip_packages = [
        'requests', 'colorama', 'speedtest-cli', 'beautifulsoup4',
        'paramiko', 'python-whois', 'dnspython'
    ]
    
    # Install Termux packages
    if is_termux and termux_packages:
        print(f"\n{Fore.CYAN}[*] Installing/updating Termux packages...{Style.RESET_ALL}")
        try:
            subprocess.run(
                ['pkg', 'install', '-y'] + termux_packages,
                capture_output=True, text=True, timeout=300
            )
            print(f"    {Fore.GREEN}✅ Termux packages checked.{Style.RESET_ALL}")
        except Exception as e:
            print(f"    {Fore.YELLOW}⚠️ Could not install all Termux packages: {e}{Style.RESET_ALL}")
    
    # Install Python packages
    print(f"\n{Fore.CYAN}[*] Installing Python (pip) packages...{Style.RESET_ALL}")
    for package in pip_packages:
        module_name_map = {
            'beautifulsoup4': 'bs4',
            'dnspython': 'dns.resolver',
            'speedtest-cli': 'speedtest',
            'python-whois': 'whois'
        }
        module_name = module_name_map.get(package, package.replace('-', '_'))

        try:
            # Handle nested module names like dns.resolver
            base_module = module_name.split('.')[0]
            importlib.import_module(base_module)
            print(f"    {Fore.GREEN}✅ {package} already installed{Style.RESET_ALL}")
        except ImportError:
            print(f"    [*] Installing {package}...")
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', package],
                    capture_output=True, text=True, timeout=180
                )
                if result.returncode == 0:
                    print(f"    {Fore.GREEN}✅ {package} installed successfully{Style.RESET_ALL}")
                else:
                    print(f"    {Fore.YELLOW}⚠️ Could not install {package}. Error: {result.stderr.splitlines()[-1]}{Style.RESET_ALL}")
            except Exception as e:
                print(f"    {Fore.RED}❌ Failed to install {package}: {e}{Style.RESET_ALL}")
    
    # Final dependency check
    print(f"\n{Fore.CYAN}[*] Final dependency check...{Style.RESET_ALL}")
    global CURSES_AVAILABLE
    try:
        import curses
        CURSES_AVAILABLE = True
        print(f"    {Fore.GREEN}✅ curses (TUI){Style.RESET_ALL}")
    except ImportError:
        print(f"    {Fore.RED}❌ curses (TUI) - TUI WILL FAIL!{Style.RESET_ALL}")
        print(f"    {Fore.YELLOW}On Termux, run: pkg install ncurses-utils{Style.RESET_ALL}")
    
    if not CURSES_AVAILABLE:
        print(f"\n{Fore.RED}CRITICAL: 'curses' module not found. The TUI cannot run.{Style.RESET_ALL}")
        return False
    
    print(f"\n{Fore.GREEN}🎉 Installation complete! Starting application...{Style.RESET_ALL}")
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
        curses.curs_set(0) # Hide cursor
    except curses.error:
        pass # Ignore if not supported
    
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
        x_title = max(0, w//2 - len(title_text)//2)
        
        if 1 < h:
            screen.attron(curses.A_BOLD | curses.color_pair(2))
            screen.addstr(1, x_title, title_text)
            screen.attroff(curses.A_BOLD | curses.color_pair(2))
            
        if 2 < h:
            screen.addstr(2, max(0, w//2 - 25), "=" * 50)

        for idx, option in enumerate(options):
            y = 4 + idx
            if y >= h - 1: break # Stop if menu overflows screen
            
            display_option = option.ljust(40)
            x = max(0, w//2 - len(display_option)//2)
            
            # Add separators
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
                # Skip separators
                while options[current_row_idx].startswith("---"):
                    current_row_idx = (current_row_idx - 1) % len(options)
            elif key == curses.KEY_DOWN:
                current_row_idx = (current_row_idx + 1) % len(options)
                # Skip separators
                while options[current_row_idx].startswith("---"):
                    current_row_idx = (current_row_idx + 1) % len(options)
            elif key == curses.KEY_ENTER or key in [10, 13]:
                return current_row_idx
            elif key == curses.KEY_RESIZE:
                # Handle terminal resize
                pass
        except curses.error:
             # Handle terminal resize errors gracefully
            time.sleep(0.1)


def main_app_loop():
    """Main application entry point"""
    
    class AdvancedNetworkTools:
        def __init__(self):
            # Define and create a dedicated save directory
            is_termux = os.path.exists('/data/data/com.termux')
            if is_termux:
                base_dir = os.path.expanduser('~')
                self.save_dir = os.path.join(base_dir, "DedSec's Network")
            else:
                self.save_dir = os.path.join(os.getcwd(), "DedSec's Network")

            if not os.path.exists(self.save_dir):
                print(f"{Fore.CYAN}[*] Creating save directory at: {self.save_dir}{Style.RESET_ALL}")
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
            
            # For efficient scanning
            self.max_workers = self.config.get('max_scan_workers', 15)
            self.scan_timeout = self.config.get('scan_timeout', 1)
            
            print(f"{Fore.GREEN}✅ Advanced Network Tools initialized successfully{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📂 All files will be saved in: {self.save_dir}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}⚡️ Scan worker threads set to: {self.max_workers}{Style.RESET_ALL}")
            
        # --- Configuration & Database Management ---
        def load_config(self):
            default_config = {
                "scan_interval": 60, "alert_on_new_network": True,
                "dns_test_server": "https://ipleak.net/json/",
                "port_scan_threads": 20, # Kept for compatibility, but we use max_scan_workers
                "max_scan_workers": 15,  # Efficient thread pool limit
                "scan_timeout": 1,       # Socket timeout in seconds
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
                print(f"{Fore.RED}❌ DB Error: Failed to record audit finding: {e}{Style.RESET_ALL}")

        # --- Wi-Fi, Local Network, and Mobile Tools (No Root Required) ---
        def _run_termux_command(self, command, timeout=15):
            """Helper to run Termux API commands."""
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
            if not isinstance(signal_dBm, int): return f"{Fore.WHITE}N/A{Style.RESET_ALL}"
            if signal_dBm >= -50: return f"{Fore.GREEN}Excellent{Style.RESET_ALL}"
            if signal_dBm >= -65: return f"{Fore.YELLOW}Good{Style.RESET_ALL}"
            if signal_dBm >= -75: return f"{Fore.MAGENTA}Fair{Style.RESET_ALL}"
            return f"{Fore.RED}Weak{Style.RESET_ALL}"
        
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
                    pass # Ignore corrupted JSON output
            return networks

        def get_current_connection_info(self):
            output = self._run_termux_command(['termux-wifi-connectioninfo'])
            if output and output.strip().startswith('{'):
                try:
                    conn_info = json.loads(output)
                    return {
                        'bssid': conn_info.get('bssid', 'N/A').upper(), 'ssid': conn_info.get('ssid', 'Not Connected'),
                        'signal': conn_info.get('rssi', 0), 'channel': self.frequency_to_channel(conn_info.get('frequency', 0)),
                        'encryption': conn_info.get('security', 'N/A'), 'is_current': True
                    }
                except json.JSONDecodeError:
                    pass
            return None

        def passive_network_scan(self):
            print(f"{Fore.YELLOW}[*] Starting passive Wi-Fi scan... (Requires Termux:API){Style.RESET_ALL}")
            networks_found = {}
            for net in self.scan_via_termux_api(): 
                networks_found[net['bssid']] = net
            
            current_network = self.get_current_connection_info()
            if current_network and current_network['bssid'] != 'N/A':
                networks_found[current_network['bssid']] = current_network
            
            if not networks_found:
                print(f"{Fore.RED}❌ No networks found. Ensure Wi-Fi is on and Termux:API is installed and configured.{Style.RESET_ALL}")

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
                    threats.append({'bssid': network['bssid'], 'ssid': network['ssid'], 'reason': 'Suspicious SSID', 'level': 'MEDIUM'})
                if network.get('encryption', 'Unknown').upper() in ['WEP', 'OPEN', '']:
                    threats.append({'bssid': network['bssid'], 'ssid': network['ssid'], 'reason': f"Weak Encryption ({network['encryption'] or 'Open'})", 'level': 'HIGH'})
            return threats

        def display_network_info(self, networks, threats):
            print(f"\n{Fore.CYAN}{'='*65}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📊 WI-FI SCAN RESULTS (Total: {len(networks)}){Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*65}{Style.RESET_ALL}")
            
            threat_bssids = {t['bssid'] for t in threats}
            
            sorted_networks = sorted(networks, key=lambda net: (
                not net.get('is_current', False), 
                net['bssid'] not in threat_bssids,
                net['bssid'] not in self.trusted_bssids,
                -net.get('signal', -100)
            ))
            
            for i, net in enumerate(sorted_networks, 1):
                bssid, ssid, signal, enc = net['bssid'], net['ssid'], net['signal'], net.get('encryption', 'N/A')
                
                if net.get('is_current'):
                    color, status = Fore.GREEN, "CONNECTED"
                elif bssid in threat_bssids:
                    color, status = Fore.RED, "ACTIVE THREAT"
                elif bssid in self.trusted_bssids:
                    color, status = Fore.GREEN, "TRUSTED"
                else:
                    color, status = Fore.WHITE, "OBSERVED"
                
                if enc.upper() in ['WEP', 'OPEN', '']:
                    enc_status = f"{Fore.RED}{enc or 'Open'} (INSECURE!){Style.RESET_ALL}"
                elif 'WPA3' in enc:
                    enc_status = f"{Fore.GREEN}{enc}{Style.RESET_ALL}"
                else:
                    enc_status = f"{Fore.YELLOW}{enc}{Style.RESET_ALL}"
                    
                print(f"{color}--- NETWORK {i}: {ssid or 'Hidden SSID'} {Style.RESET_ALL} (BSSID: {bssid}) ---")
                print(f"  Signal: {signal}dBm ({self.get_signal_quality(signal)}) | Channel: {net['channel']}")
                print(f"  Encryption: {enc_status}")
                print(f"  Status: {color}{status}{Style.RESET_ALL}")
                
                for threat in (t for t in threats if t['bssid'] == bssid):
                    t_color = Fore.RED if threat['level'] == 'HIGH' else Fore.YELLOW
                    print(f"{t_color}  🚨 THREAT ({threat['level']}): {threat['reason']}{Style.RESET_ALL}")
                print("-" * 65)

        def single_wifi_scan(self):
            networks = self.passive_network_scan()
            if networks:
                threats = self.analyze_networks(networks)
                self.display_network_info(networks, threats)
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        def view_current_connection(self):
            print(f"\n{Fore.CYAN}🔗 CURRENT WI-FI CONNECTION{Style.RESET_ALL}")
            print("="*50)
            current_info = self.get_current_connection_info()
            if not current_info or current_info['ssid'] == 'Not Connected':
                print(f"{Fore.RED}❌ You are not connected to a Wi-Fi network.{Style.RESET_ALL}")
            else:
                bssid = current_info['bssid']
                trust_status = f"{Fore.GREEN}TRUSTED{Style.RESET_ALL}" if bssid in self.trusted_bssids else f"{Fore.YELLOW}UNKNOWN{Style.RESET_ALL}"
                print(f"  SSID:        {current_info['ssid']}")
                print(f"  BSSID:       {bssid}")
                print(f"  Signal:      {current_info['signal']}dBm ({self.get_signal_quality(current_info['signal'])})")
                print(f"  Encryption:  {current_info['encryption']}")
                print(f"  Trust: {trust_status}")
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        def toggle_wifi(self):
            print(f"\n{Fore.CYAN}🔄 TOGGLE WI-FI (Termux:API){Style.RESET_ALL}")
            if not os.path.exists('/data/data/com.termux'):
                print(f"{Fore.RED}❌ This feature requires the Termux:API application.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                return

            choice = input(f"{Fore.WHITE}Enable/Disable Wi-Fi [on/off]? {Style.RESET_ALL}").strip().lower()
            if choice == 'on':
                print("[*] Enabling Wi-Fi...")
                self._run_termux_command(['termux-wifi-enable', 'true'])
                print(f"{Fore.GREEN}✅ Wi-Fi enabled.{Style.RESET_ALL}")
            elif choice == 'off':
                print("[*] Disabling Wi-Fi...")
                self._run_termux_command(['termux-wifi-enable', 'false'])
                print(f"{Fore.GREEN}✅ Wi-Fi disabled.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ Invalid choice.{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        def get_mobile_data_info(self):
            print(f"\n{Fore.CYAN}📱 MOBILE DATA / SIM INFO (Termux:API){Style.RESET_ALL}")
            print("="*50)
            if not os.path.exists('/data/data/com.termux'):
                print(f"{Fore.RED}❌ This feature requires the Termux:API application.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                return

            # Device Info
            device_info_out = self._run_termux_command(['termux-telephony-deviceinfo'])
            if device_info_out:
                try:
                    data = json.loads(device_info_out)
                    print(f"{Fore.CYAN}--- Device & SIM Info ---{Style.RESET_ALL}")
                    print(f"  Network Operator:   {data.get('network_operator_name', 'N/A')}")
                    print(f"  SIM Operator:       {data.get('sim_operator_name', 'N/A')}")
                    print(f"  Phone Type:         {data.get('phone_type', 'N/A')}")
                    print(f"  Network Type:       {data.get('data_network_type', 'N/A')}")
                    print(f"  Data State:         {data.get('data_state', 'N/A')}")
                except json.JSONDecodeError:
                    print(f"{Fore.YELLOW}[!] Could not parse device info.{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}[!] Could not retrieve device/SIM info. No SIM?{Style.RESET_ALL}")

            # Cell Tower Info
            cell_info_out = self._run_termux_command(['termux-telephony-cellinfo'])
            if cell_info_out:
                try:
                    data = json.loads(cell_info_out)
                    print(f"\n{Fore.CYAN}--- Nearby Cell Towers ---{Style.RESET_ALL}")
                    if not data.get('cells'):
                         print("  No cell tower information available.")
                    for cell in data.get('cells', []):
                        cell_type = cell.get('type', 'N/A').upper()
                        strength = cell.get('dbm', 'N/A')
                        print(f"  - Type: {cell_type} | Strength: {strength} dBm ({self.get_signal_quality(strength)})")
                except json.JSONDecodeError:
                    print(f"{Fore.YELLOW}[!] Could not parse tower info.{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}[!] Could not retrieve tower info.{Style.RESET_ALL}")

            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        # --- Enhanced NMAP-like Network Scanning Tools (No Root Required) ---
        
        def nmap_wrapper(self):
            """Wrapper for the 'nmap' binary installed via pkg."""
            print(f"\n{Fore.CYAN}⚡ NMAP SCANNER WRAPPER{Style.RESET_ALL}")
            
            # Check if nmap exists
            try:
                nmap_check = subprocess.run(['nmap', '--version'], capture_output=True, text=True, timeout=5)
                print(f"{Fore.GREEN}✅ Nmap found: {nmap_check.stdout.splitlines()[0]}{Style.RESET_ALL}")
            except (FileNotFoundError, Exception):
                print(f"{Fore.RED}❌ Nmap binary not found!{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Please install it via the dependency installer or manually ('pkg install nmap').{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                return

            target = input(f"{Fore.WHITE}Enter target IP or hostname: {Style.RESET_ALL}").strip()
            if not target:
                return

            print(f"\n{Fore.CYAN}Select Scan Type:{Style.RESET_ALL}")
            print("1. Ping Scan (Host Discovery) [-sn]")
            print("2. Quick Scan (Top ports, OS/Service) [-T4 -A -F]")
            print("3. Intense Scan (All 1000 ports, OS/Service) [-T4 -A]")
            print("4. Custom Flags")
            
            scan_choice = input(f"{Fore.WHITE}Select scan type (1-4): {Style.RESET_ALL}").strip()
            
            nmap_flags = []
            if scan_choice == '1':
                nmap_flags = ['-sn']
            elif scan_choice == '2':
                nmap_flags = ['-T4', '-A', '-F']
            elif scan_choice == '3':
                nmap_flags = ['-T4', '-A']
            elif scan_choice == '4':
                custom = input(f"{Fore.WHITE}Enter custom nmap flags (e.g., -sV -p 80,443): {Style.RESET_ALL}").strip()
                nmap_flags = custom.split()
            else:
                print(f"{Fore.RED}❌ Invalid choice.{Style.RESET_ALL}")
                return

            command = ['nmap'] + nmap_flags + [target]
            print(f"\n{Fore.YELLOW}[*] Executing: {' '.join(command)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            try:
                # Run nmap and print output line by line
                with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1) as proc:
                    for line in proc.stdout:
                        print(line, end='')
                
                print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}✅ Nmap scan complete.{Style.RESET_ALL}")
                
                # We can't parse this easily, so we just log the action
                self.record_audit_finding(target, 'Nmap Scan', f"Scan type: {' '.join(nmap_flags)}", "Nmap scan executed. See console output.", 'Informational')
                
            except Exception as e:
                print(f"{Fore.RED}❌ Nmap scan failed: {e}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        def enhanced_port_scanner(self):
            """Enhanced port scanner with service detection - EFFICIENT THREAD POOL"""
            print(f"\n{Fore.CYAN}🔍 ENHANCED PORT SCANNER (Python-based){Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Note: For more power, use the Nmap Wrapper tool.{Style.RESET_ALL}")
            
            target = input(f"{Fore.WHITE}Enter target IP or hostname: {Style.RESET_ALL}").strip()
            if not target: return

            try:
                target_ip = socket.gethostbyname(target)
                print(f"[*] Resolving {target} to {target_ip}")
            except socket.gaierror:
                print(f"{Fore.RED}❌ Could not resolve hostname.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                return

            port_choice = input(f"{Fore.WHITE}Enter ports: (1) Top, (2) 1-1024, (3) Custom (e.g., 80,443,1-100): {Style.RESET_ALL}").strip()
            
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
                    print(f"{Fore.RED}❌ Invalid port format.{Style.RESET_ALL}")
                    return

            print(f"[*] Scanning {target_ip} on {len(ports_to_scan)} TCP ports using {self.max_workers} workers...")
            
            open_ports = {} # Use dict to store port: service
            
            def tcp_connect_scan(port):
                """Worker function for TCP connect scan"""
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(self.scan_timeout)
                        if sock.connect_ex((target_ip, port)) == 0:
                            # Port is open, try to grab banner
                            try:
                                service = self.grab_banner(sock, port)
                                return (port, service)
                            except:
                                return (port, "Unknown")
                except:
                    pass
                return None
            
            # --- EFFICIENT THREAD POOL ---
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_port = {executor.submit(tcp_connect_scan, port): port for port in ports_to_scan}
                for future in concurrent.futures.as_completed(future_to_port):
                    result = future.result()
                    if result:
                        port, service = result
                        open_ports[port] = service
                        print(f"  {Fore.GREEN}[+] Port {port:5}{Style.RESET_ALL} - OPEN - {service}")
            
            # Display results
            print(f"\n{Fore.GREEN}✅ TCP scan complete!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            if open_ports:
                print(f"Found {len(open_ports)} open ports:")
                for port in sorted(open_ports.keys()):
                    service = open_ports[port]
                    print(f"  Port {port:5} - {Fore.GREEN}OPEN{Style.RESET_ALL} - {service}")
                    self.record_audit_finding(target, 'Enhanced Port Scan', f'Open Port: {port}', f'Port {port} ({service}) is open', 'Informational')
            else:
                print("No open ports found.")
            
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        def grab_banner(self, sock, port):
            """Attempt to grab service banner from open port"""
            try:
                # Send probe based on port
                if port in [80, 8080]:
                    sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
                elif port in [443, 8443]:
                    return "HTTPS (SSL)" # Can't grab banner without SSL wrapper
                
                banner = sock.recv(1024).decode('utf-8', errors='ignore').strip().split('\n')[0]
                
                if banner:
                    return banner[:60] + "..." if len(banner) > 60 else banner
                elif port == 21: return "FTP"
                elif port == 22: return "SSH"
                elif port == 25: return "SMTP"
                elif port == 53: return "DNS"
                elif port == 110: return "POP3"
                elif port == 143: return "IMAP"
                else: return "Service detected"
            except socket.timeout:
                return "Service detected (No banner)"
            except Exception:
                return "Service detected"

        def network_discovery(self):
            """Advanced network discovery using multiple techniques - EFFICIENT THREAD POOL"""
            print(f"\n{Fore.CYAN}🌐 ADVANCED NETWORK DISCOVERY{Style.RESET_ALL}")
            
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
            except Exception as e:
                print(f"{Fore.RED}❌ Could not determine local IP: {e}{Style.RESET_ALL}")
                return
            
            network_base = '.'.join(local_ip.split('.')[:-1]) + '.'
            print(f"[*] Your IP: {local_ip}")
            print(f"[*] Scanning network: {network_base}0/24 using {self.max_workers} workers...")
            
            discovered_hosts = {} # ip: [reason]
            common_ports = [22, 80, 443, 8080, 3389, 445]
            lock = threading.Lock()

            def discover_host(ip):
                """Worker function to scan a single host with multiple methods."""
                reasons = []
                
                # Method 1: ICMP Ping
                try:
                    subprocess.run(['ping', '-c', '1', '-W', '1', ip], 
                                 capture_output=True, timeout=2, check=True)
                    reasons.append("ICMP")
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    pass # Host is down or not responding to ping

                # Method 2: TCP Port Probe
                for port in common_ports:
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                            sock.settimeout(0.5) # Faster timeout for discovery
                            if sock.connect_ex((ip, port)) == 0:
                                reasons.append(f"TCP/{port}")
                    except:
                        pass
                
                if reasons:
                    with lock:
                        discovered_hosts[ip] = reasons
                        print(f"  {Fore.GREEN}[+] {ip:15}{Style.RESET_ALL} - Active (Found via: {', '.join(reasons)})")

            # --- EFFICIENT THREAD POOL ---
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(discover_host, network_base + str(i)) for i in range(1, 255) if network_base + str(i) != local_ip]
                # Wait for all to complete
                for future in concurrent.futures.as_completed(futures):
                    pass # Results are printed live
            
            print(f"\n{Fore.GREEN}✅ Network discovery complete!{Style.RESET_ALL}")
            print(f"Discovered {len(discovered_hosts)} active hosts (besides you):")
            for host in sorted(discovered_hosts.keys()):
                print(f"  - {host:15} ({', '.join(discovered_hosts[host])})")
            
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        def subnet_calculator(self):
            """Subnet calculator and network information tool"""
            print(f"\n{Fore.CYAN}🧮 SUBNET CALCULATOR{Style.RESET_ALL}")
            
            ip_input = input(f"{Fore.WHITE}Enter IP address with CIDR (e.g., 192.168.1.0/24): {Style.RESET_ALL}").strip()
            
            if not ip_input or '/' not in ip_input:
                print(f"{Fore.RED}❌ Please use the format: IP/CIDR{Style.RESET_ALL}")
                return
            
            try:
                ip_str, cidr_str = ip_input.split('/')
                cidr = int(cidr_str)
                if not (0 <= cidr <= 32):
                    raise ValueError("CIDR must be between 0 and 32")
                
                ip_parts = list(map(int, ip_str.split('.')))
                if len(ip_parts) != 4 or any(not (0 <= p <= 255) for p in ip_parts):
                    raise ValueError("Invalid IP address")

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
                
                print(f"\n{Fore.GREEN}📊 SUBNET CALCULATION RESULTS:{Style.RESET_ALL}")
                print(f"  Address:            {ip_str}/{cidr}")
                print(f"  Subnet Mask:        {subnet_mask}")
                print(f"  Network Address:    {network_addr}")
                print(f"  Broadcast Address:  {broadcast_addr}")
                print(f"  Total Hosts:        {total_hosts}")
                print(f"  Usable Hosts:       {usable_hosts}")
                
                if usable_hosts > 0:
                    first_host = int_to_ip(network_int + 1)
                    last_host = int_to_ip(broadcast_int - 1)
                    print(f"  Host Range:         {first_host} - {last_host}")
                
            except Exception as e:
                print(f"{Fore.RED}❌ Error calculating subnet: {e}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        # --- Internet & Diagnostics (No Root Required) ---
        def run_internet_speed_test(self):
            print(f"\n{Fore.CYAN}⚡️ RUNNING INTERNET SPEED TEST...{Style.RESET_ALL}")
            if not SPEEDTEST_AVAILABLE or not speedtest:
                print(f"{Fore.RED}❌ 'speedtest-cli' module is not available.{Style.RESET_ALL}")
                input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                return

            try:
                st = speedtest.Speedtest()
                print(f"{Fore.YELLOW}[*] Finding best server...{Style.RESET_ALL}")
                st.get_best_server()
                print(f"{Fore.YELLOW}[*] Running download test...{Style.RESET_ALL}")
                download_speed = st.download() / 1_000_000
                print(f"{Fore.YELLOW}[*] Running upload test...{Style.RESET_ALL}")
                upload_speed = st.upload() / 1_000_000
                ping = st.results.ping
                
                print(f"\n{Fore.GREEN}✅ SPEED TEST COMPLETE!{Style.RESET_ALL}")
                print("="*50)
                print(f"  Server: {st.results.server['name']} ({st.results.server['country']})")
                print(f"  Ping:       {ping:.2f} ms")
                print(f"  Download:   {Fore.GREEN}{download_speed:.2f} Mbps{Style.RESET_ALL}")
                print(f"  Upload:     {Fore.GREEN}{upload_speed:.2f} Mbps{Style.RESET_ALL}")
                print("="*50)
            except Exception as e:
                print(f"{Fore.RED}❌ Speed test failed: {e}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        def get_external_ip_info(self):
            print(f"\n{Fore.CYAN}🗺️ GETTING EXTERNAL IP INFO...{Style.RESET_ALL}")
            if not REQUESTS_AVAILABLE:
                print(f"{Fore.RED}❌ 'requests' module is not available.{Style.RESET_ALL}")
                return
            try:
                data = requests.get("http://ip-api.com/json/", timeout=10).json()
                if data.get('status') == 'success':
                    print(f"\n{Fore.GREEN}✅ External IP Information:{Style.RESET_ALL}")
                    print(f"  IP Address:   {data.get('query')}")
                    print(f"  ISP/Provider: {data.get('isp')}")
                    print(f"  Location:     {data.get('city')}, {data.get('regionName')}, {data.get('country')}")
                    print(f"  Organization: {data.get('org')}")
                else:
                    print(f"{Fore.RED}❌ Failed to retrieve IP info.{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Failed to connect to IP service: {e}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            
        def run_network_diagnostics(self):
            print(f"\n{Fore.CYAN}📶 NETWORK DIAGNOSTICS{Style.RESET_ALL}")
            host = input(f"{Fore.WHITE}Enter host or IP to test (e.g., google.com): {Style.RESET_ALL}").strip()
            if not host: return
            
            print(f"\n{Fore.CYAN}>>> Running PING test to {host}...{Style.RESET_ALL}")
            try:
                result = subprocess.run(['ping', '-c', '4', host], capture_output=True, text=True, timeout=10)
                print(result.stdout if result.returncode == 0 else result.stderr)
            except Exception as e:
                print(f"{Fore.RED}❌ Error running ping: {e}{Style.RESET_ALL}")
            
            print(f"\n{Fore.CYAN}>>> Running TRACEROUTE test to {host}...{Style.RESET_ALL}")
            try:
                # Use -n to avoid DNS resolution, which is faster
                result = subprocess.run(['traceroute', '-n', host], capture_output=True, text=True, timeout=30)
                print(result.stdout if result.returncode == 0 else result.stderr)
            except FileNotFoundError:
                print(f"{Fore.RED}❌ 'traceroute' not found. Please install 'inetutils' (pkg install inetutils){Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Error running traceroute: {e}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        # --- Information Gathering (No Root Required) ---
        def run_osintds_scanner(self):
            """Wrapper for the OSINTDS scanner tool."""
            print(f"\n{Fore.CYAN} launching OSINTDS Scanner...{Style.RESET_ALL}")
            time.sleep(1)

            # --- OSINTDS LOGIC - Encapsulated in this method ---
            
            # --- Configuration and Constants ---
            PREFERRED_PATHS = [
                os.path.expanduser("~/storage/downloads"),
                os.path.expanduser("/sdcard/Download"),
                os.path.expanduser("~/Downloads"),
                self.save_dir # Use the app's save dir
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
                        print(f'[WARN] Wordlist for {name} is empty.')
                        return None
                    with open(dest_path, 'w', encoding='utf-8') as f:
                        f.write(txt)
                    print(f'[INFO] Created default wordlist: {dest_path} ({len(txt.splitlines())} entries)')
                    return dest_path
                except Exception as e:
                    print(f'[ERROR] Wordlist unpack error for {name}: {e}')
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
                    print(f'[ERROR] Wordlist not found at {path}.')
                    return []
                except Exception as e:
                    print(f'[ERROR] Failed to read wordlist at {path}: {e}')
                    return []

            # --- Core Utility Functions ---
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
                    print(f"[INFO] Saved: {path}")
                except IOError as e: print(f'[ERROR] File save error for {path}: {e}')

            def save_csv(folder, filename, rows, headers=None):
                path = os.path.join(folder, filename)
                try:
                    with open(path, 'w', newline='', encoding='utf-8') as cf:
                        writer = csv.writer(cf)
                        if headers: writer.writerow(headers)
                        writer.writerows([[str(item) for item in row] for row in rows])
                    print('[INFO] Saved CSV:', path)
                except IOError as e: print(f'[ERROR] CSV save error for {path}: {e}')

            def checkpoint_save(folder, report):
                save_text(folder, 'report.json', json.dumps(report, indent=2, default=str))

            # --- SCANNING FUNCTIONS ---
            def get_whois_info_osint(domain):
                try:
                    w = whois.whois(domain)
                    if not w: return {'error': 'No WHOIS data returned.'}
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
                    if verbose: print(f'[WARN] Timeout accessing {url}')
                except requests.exceptions.RequestException as e:
                    if verbose: print(f'[WARN] Request error for {url}: {e}')
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
                    hf_display_message(f"Failed to save asset {asset_url}: {e}", 'red')
                    return None, None

            def hf_process_html_and_download_assets(html_content, base_url, website_dir):
                soup = BeautifulSoup(html_content, 'html.parser')
                downloaded_urls = {}
                hf_display_message("\nStarting asset download process...", 'blue')
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
                hf_display_message(f"Asset download and HTML modification complete. ({len(downloaded_urls)} assets processed)", 'green')
                return str(soup)

            def hf_edit_html_in_editor(html_content):
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
                except FileNotFoundError: hf_display_message(f"Error: Editor '{EDITOR}' not found.", 'red')
                except subprocess.CalledProcessError: hf_display_message(f"Editor '{EDITOR}' exited with an error. Changes may not be saved.", 'red')
                except Exception as e: hf_display_message(f"An error occurred during editing: {e}", 'red')
                finally:
                    if 'temp_file_path' in locals() and os.path.exists(temp_file_path): os.remove(temp_file_path)
                return None

            def hf_save_html_to_file(html_content, target_dir, filename="index.html"):
                if not html_content:
                    hf_display_message("No content to save.", 'yellow')
                    return None
                os.makedirs(target_dir, exist_ok=True)
                filepath = os.path.join(target_dir, filename)
                try:
                    with open(filepath, 'w', encoding='utf-8') as f: f.write(html_content)
                    hf_display_message(f"HTML saved successfully to '{filepath}'", 'green')
                    return filepath
                except IOError as e:
                    hf_display_message(f"Error saving file: {e}", 'red')
                    return None
            
            def hf_preview_html_in_browser(filepath):
                if not filepath or not os.path.exists(filepath):
                    hf_display_message("No HTML file found to preview.", 'yellow')
                    return
                if check_termux_package("termux-open-url"):
                    hf_display_message(f"Opening preview in Termux browser...", 'blue')
                    subprocess.run(['termux-open-url', f'file://{filepath}'])
                else:
                    hf_display_message(f"Opening preview in default system browser...", 'blue')
                    webbrowser.open(f'file://{os.path.abspath(filepath)}')

            def hf_fetch_html(url, verbose=False):
                response = fetch(url, verbose=verbose)
                if response: return response.text
                if verbose: hf_display_message(f"Failed to fetch HTML for {url}", 'red')
                return None

            def run_html_finder(initial_url, folder, verbose=False):
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
                            hf_save_html_to_file(html_content, website_dir)
                    elif choice == '3':
                        saved_path = hf_save_html_to_file(html_content, website_dir)
                        if saved_path: hf_preview_html_in_browser(saved_path)
                    elif choice == '4':
                        new_url_input = input("Enter the new website URL: ").strip()
                        if new_url_input:
                            normalized_url, _ = normalize_target(new_url_input)
                            if normalized_url:
                                current_url, website_dir = normalized_url, hf_get_website_dir(normalized_url)
                                new_html = hf_fetch_html(current_url, verbose)
                                if new_html: html_content = new_html
                                else: hf_display_message("Failed to fetch new URL. Staying with previous content.", 'red')
                            else: hf_display_message("Invalid URL provided.", 'yellow')
                    elif choice == '5':
                        hf_display_message("Exiting the HTML inspector.", 'blue')
                        break
                    else: hf_display_message("Invalid choice. Please enter a number between 1 and 5.", 'red')

            def save_html_report(folder, report):
                html_template = f"""
                <html><head><meta charset="utf-8"><title>OSINTDS Report for {html.escape(report.get('domain', 'N/A'))}</title>
                <style>body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Oxygen-Sans,Ubuntu,Cantarell,"Helvetica Neue",sans-serif;line-height:1.6;color:#333;max-width:1200px;margin:0 auto;padding:20px;background-color:#f9f9f9}}h1,h2,h3{{color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:10px}}h1{{font-size:2.5em}}pre{{background-color:#ecf0f1;padding:1em;border:1px solid #bdc3c7;border-radius:5px;white-space:pre-wrap;word-wrap:break-word;font-family:"Courier New",Courier,monospace}}ul,ol{{padding-left:20px}}li{{margin-bottom:5px}}.card{{background-color:#fff;border:1px solid #ddd;border-radius:8px;padding:20px;margin-bottom:20px;box-shadow:0 2px4px rgba(0,0,0,0.1)}}</style>
                </head><body><h1>OSINTDS Report for {html.escape(report.get('domain', 'N/A'))}</h1><div class="card"><h2>Summary</h2><ul>
                <li><b>Target URL:</b> {html.escape(report.get('target', 'N/A'))}</li><li><b>Final URL:</b> {html.escape(report.get('final_url', 'N/A'))}</li>
                <li><b>Primary IP:</b> {html.escape(report.get('primary_ip', 'N/A'))}</li><li><b>Reverse DNS:</b> {html.escape(report.get('reverse_dns', 'N/A'))}</li>
                <li><b>HTTP Status:</b> {html.escape(str(report.get('http_status', 'N/A')))}</li><li><b>Open Ports:</b> {len(report.get('open_ports', []))}</li>
                <li><b>Subdomains Found:</b> {len(report.get('subdomains', []))}</li></ul></div>"""
                sections = {
                    'WHOIS Information': report.get('whois'),'DNS Records': report.get('dns_records'),'SSL Certificate': report.get('ssl'),
                    'HTTP Security Headers': report.get('security_headers'),'Open Ports': report.get('open_ports'),'Subdomains': report.get('subdomains'),
                    'Directory/File Hits': report.get('dir_hits'),'Wayback Machine': report.get('wayback'),'Homepage Content Analysis': report.get('content_info'),
                    'Discovered URLs (Sitemap/Robots)': report.get('discovered_urls'),'Potential SQL Injection Evidence': report.get('sqli_evidence'),
                    'Potential XSS Reflections': report.get('xss_reflections'),'DNS Zone Transfer (AXFR)': report.get('axfr'),
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
                response = input(f'{prompt} [Default: {default_value}] (Enter for default, or type new value): ').strip()
                return response or default_value

            def run_checks(target, threads=DEFAULT_THREADS, full_ports=False, out_formats=('json','html','csv'), dir_words=None, sub_words=None, verbose=False):
                base, domain = normalize_target(target)
                folder = make_dirs(domain)
                report_path = os.path.join(folder, 'report.json')
                report = {'target': target, 'domain': domain, 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')}
                if os.path.exists(report_path):
                    if input(f"Existing report found for {domain}. Resume scan? (Y/n): ").strip().lower() != 'n':
                        try:
                            with open(report_path, 'r', encoding='utf-8') as f: report.update(json.load(f))
                            print('[INFO] Resuming scan from existing report.')
                        except (json.JSONDecodeError, IOError) as e: print(f'[WARN] Could not load existing report ({e}). Starting fresh.')
                def run_stage(stage_num, name, key, func, *args, **kwargs):
                    print(f"[STAGE {stage_num}/13] {name}...")
                    if report.get(key) is None:
                        report[key] = func(*args, **kwargs)
                        checkpoint_save(folder, report)
                    else: print(f"[INFO] Found cached result for '{name}'. Skipping.")
                print(f"[STAGE 1/13] Probing base URL: {base}")
                if report.get('http_status') is None or 'unreachable' in str(report.get('http_status')):
                    r = fetch(base, verbose=verbose)
                    if not r:
                        report['http_status'] = 'unreachable'
                        checkpoint_save(folder, report)
                        print('[ERROR] Target unreachable.')
                        return None, None
                    report['http_status'], report['final_url'], report['headers'] = f"{r.status_code} {r.reason}", r.url, dict(r.headers)
                    checkpoint_save(folder, report)
                else:
                    r = fetch(report.get('final_url', base), verbose=verbose)
                    if not r:
                        print('[ERROR] Resumed target now unreachable.')
                        return None, None
                run_stage(2, "Checking HTTP security headers", 'security_headers', check_security_headers, r.headers)
                run_stage(3, "Checking WHOIS information", 'whois', get_whois_info_osint, domain)
                run_stage(4, "Resolving DNS and Reverse DNS", 'dns_records', resolve_all_dns, domain)
                if 'dns_records' in report and report['dns_records'].get('A'):
                    report['primary_ip'] = report['dns_records']['A'][0]
                    run_stage(4, "Performing Reverse DNS", 'reverse_dns', reverse_dns_lookup, report['primary_ip'])
                run_stage(5, "Checking Wayback Machine", 'wayback', check_wayback_machine, domain)
                run_stage(6, "Checking SSL certificate", 'ssl', ssl_info, domain)
                run_stage(7, "Analyzing homepage content", 'content_info', extract_content_info, r.text)
                run_stage(8, "Searching for sitemap/robots.txt", 'discovered_urls', lambda: sorted(list(set(re.findall(r'<loc>([^<]+)</loc>', sm.text, re.I) for sm_url in ([line.split(':', 1)[1].strip() for line in (fetch(urljoin(base, '/robots.txt')) or type('',(object,),{'text':''})()).text.splitlines() if line.lower().startswith('sitemap:')] or [urljoin(base, '/sitemap.xml')]) if (sm := fetch(sm_url)) and sm.status_code == 200))))
                run_stage(9, "Running subdomain enumeration", 'subdomains', subdomain_bruteforce_osint, domain, sub_words, threads=threads)
                run_stage(10, "Attempting DNS zone transfer", 'axfr', attempt_zone_transfer, domain)
                port_list = list(range(1, 65536)) if full_ports else [21, 22, 25, 53, 80, 110, 143, 443, 465, 587, 993, 995, 3306, 5432, 8000, 8080, 8443]
                run_stage(11, "Running port probe", 'open_ports', probe_ports_connect, report.get('primary_ip', domain), port_list, threads=max(100, threads))
                run_stage(12, "Running directory brute-force", 'dir_hits', dir_bruteforce, base, dir_words, threads=threads, verbose=verbose)
                print("[STAGE 13/13] Running vulnerability heuristics...")
                if report.get('sqli_evidence') is None or report.get('xss_reflections') is None:
                    all_links = set(report.get('discovered_urls', [])); soup = BeautifulSoup(r.text, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        full_url = urljoin(base, a['href'])
                        if urlparse(full_url).hostname == domain: all_links.add(full_url)
                    links_to_scan = list(all_links)[:400]
                    print(f'[INFO] Running SQLi/XSS heuristics on {len(links_to_scan)} URLs...')
                    sqli, xss = [], []
                    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
                        sql_futures = {executor.submit(basic_sqli_test_on_url, u, verbose): u for u in links_to_scan if '?' in u}
                        xss_futures = {executor.submit(xss_reflection_test, u, verbose): u for u in links_to_scan if '?' in u}
                        for f in concurrent.futures.as_completed(sql_futures):
                            if res := f.result(): sqli.append(res)
                        for f in concurrent.futures.as_completed(xss_futures):
                            if res := f.result(): xss.extend(res)
                    report['sqli_evidence'], report['xss_reflections'] = sqli, xss; checkpoint_save(folder, report)
                print('\n[FINAL] Generating final report files...')
                if 'json' in out_formats: checkpoint_save(folder, report)
                if 'csv' in out_formats:
                    if report.get('subdomains'): save_csv(folder, 'subdomains.csv', report['subdomains'], headers=['Subdomain', 'IP'])
                    if report.get('dir_hits'): save_csv(folder, 'dirs.csv', report['dir_hits'], headers=['Path', 'Status', 'Final URL'])
                if 'html' in out_formats: save_html_report(folder, report)
                print('\n--- Scan Complete Summary ---'); print(f"Target: {report['target']}"); print(f"Primary IP: {report.get('primary_ip', 'N/A')}"); print(f"HTTP Status: {report['http_status']}"); print(f"Open ports ({len(report.get('open_ports',[]))} found): {report.get('open_ports', 'N/A')}"); print(f"Subdomains found: {len(report.get('subdomains',[]))}"); print(f"Dir hits: {len(report.get('dir_hits',[]))}"); print(f"Potential SQLi: {len(report.get('sqli_evidence',[]))}"); print(f"Potential XSS: {len(report.get('xss_reflections',[]))}"); print(f'\nSaved outputs to: {folder}')
                return report, folder

            # --- Main interactive entry point for OSINTDS ---
            print('--- OSINTDS Interactive Scanner ---')
            target_input = input('Enter target domain or URL (e.g., example.com): ').strip()
            if not target_input:
                print('No target provided. Exiting.')
                return
            base, domain = normalize_target(target_input)
            if not domain:
                print('Invalid target format. Exiting.')
                return
            try: threads = int(get_user_choice('Number of threads?', DEFAULT_THREADS))
            except ValueError: threads = DEFAULT_THREADS
            full_ports = input('Full port scan (1-65535)? Very slow. (y/N): ').strip().lower().startswith('y')
            dir_wordlist_path = get_user_choice('Path to directory wordlist?', DIR_WORDLIST_PATH)
            sub_wordlist_path = get_user_choice('Path to subdomain wordlist?', SUB_WORDLIST_PATH)
            verbose = input('Enable verbose mode for debugging? (y/N): ').strip().lower().startswith('y')
            out_formats_raw = get_user_choice('Output formats (json,html,csv)?', 'json,html,csv')
            out_formats = {f.strip() for f in out_formats_raw.split(',') if f.strip()}
            dir_words, sub_words = read_wordlist(dir_wordlist_path), read_wordlist(sub_wordlist_path)
            print('\nDISCLAIMER: Only scan targets you own or have explicit permission to test.')
            print('Starting OSINT scan. This may take some time...')
            report, folder = run_checks(target=target_input, threads=threads, full_ports=full_ports, out_formats=out_formats, dir_words=dir_words, sub_words=sub_words, verbose=verbose)
            if not report:
                print("\nScan could not be completed.")
                return
            print("\n" + "="*50); print("--- Post-Scan HTML Inspector/Editor ---")
            if input("Run Interactive HTML Downloader/Editor on the target URL? (y/N): ").strip().lower().startswith('y'):
                final_url = report.get('final_url') or target_input
                if 'unreachable' not in str(report.get('http_status', '')):
                    run_html_finder(final_url, folder, verbose)
                else: print("[WARN] Target was unreachable, skipping HTML Inspector.")
            print("="*50)

            # After the tool finishes, prompt to return to the main menu
            input(f"\n{Fore.YELLOW}OSINTDS scan finished. Press Enter to return to the main menu...{Style.RESET_ALL}")


        def get_whois_info(self):
            print(f"\n{Fore.CYAN}👤 WHOIS LOOKUP{Style.RESET_ALL}")
            if not WHOIS_AVAILABLE:
                print(f"{Fore.RED}❌ 'python-whois' module is not available.{Style.RESET_ALL}")
                return
            
            domain = input(f"{Fore.WHITE}Enter domain to look up (e.g., google.com): {Style.RESET_ALL}").strip()
            if not domain: return
            try:
                print(f"[*] Querying WHOIS records for {domain}...")
                w = whois.whois(domain)
                print(f"\n{Fore.GREEN}✅ WHOIS Information for {domain}:{Style.RESET_ALL}")
                if w.text:
                    # Print raw text if available, as it's often more complete
                    print(w.text)
                else:
                    # Fallback to parsed attributes
                    for key, value in w.items():
                        if value:
                            print(f"  {str(key).replace('_', ' ').title()}: {value}")
            except Exception as e:
                print(f"{Fore.RED}❌ WHOIS lookup failed: {e}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        def get_dns_records(self):
            print(f"\n{Fore.CYAN}🌐 DNS RECORD LOOKUP{Style.RESET_ALL}")
            if not DNS_AVAILABLE:
                print(f"{Fore.RED}❌ 'dnspython' module is not available.{Style.RESET_ALL}")
                return
            
            domain = input(f"{Fore.WHITE}Enter domain to query (e.g., google.com): {Style.RESET_ALL}").strip()
            if not domain: return

            record_types = ['A', 'AAAA', 'MX', 'TXT', 'NS', 'CNAME', 'SOA']
            print(f"{Fore.GREEN}✅ DNS Records for {domain}:{Style.RESET_ALL}")
            for rtype in record_types:
                try:
                    answers = dns_resolver.resolve(domain, rtype)
                    print(f"{Fore.CYAN}  --- {rtype} Records ---{Style.RESET_ALL}")
                    for rdata in answers:
                        print(f"    {rdata.to_text()}")
                except (dns_resolver.NoAnswer, dns_resolver.NXDOMAIN):
                    print(f"{Fore.YELLOW}  --- No {rtype} Records found ---{Style.RESET_ALL}")
                except Exception:
                    pass # Ignore other errors like timeout
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            
        def web_crawler(self):
            print(f"\n{Fore.CYAN}🕷️ WEB CRAWLER / LINK EXTRACTOR{Style.RESET_ALL}")
            if not REQUESTS_AVAILABLE or not BS4_AVAILABLE:
                print(f"{Fore.RED}❌ 'requests' and 'beautifulsoup4' modules are required.{Style.RESET_ALL}")
                return

            start_url = input(f"{Fore.WHITE}Enter starting URL to crawl: {Style.RESET_ALL}").strip()
            if not start_url.startswith(('http://', 'https://')):
                start_url = 'https://' + start_url
            
            try:
                max_links = int(input(f"{Fore.WHITE}Enter max links to find (default 50): {Style.RESET_ALL}").strip() or 50)
            except ValueError:
                max_links = 50
            
            try:
                domain_name = urlparse(start_url).netloc
            except:
                print(f"{Fore.RED}❌ Invalid URL format.{Style.RESET_ALL}")
                return
                
            crawled = set()
            to_crawl = deque([start_url])
            internal_links = set()
            external_links = set()
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}

            print(f"[*] Crawling {start_url} (domain: {domain_name})...")
            
            try:
                while to_crawl and len(internal_links) < max_links:
                    url = to_crawl.popleft()
                    if url in crawled: continue
                    
                    crawled.add(url)
                    print(f"  {Fore.YELLOW}> Visiting: {url}{Style.RESET_ALL}")
                    
                    response = requests.get(url, timeout=5, headers=headers)
                    if 'text/html' not in response.headers.get('Content-Type', ''):
                        continue

                    soup = BeautifulSoup(response.content, "html.parser")
                    
                    for a_tag in soup.findAll("a"):
                        href = a_tag.attrs.get("href")
                        if not href: continue
                        
                        href = urljoin(url, href).split('#')[0] # Join relative URLs and remove fragments
                        
                        if href.startswith(('mailto:', 'tel:')):
                            continue

                        if domain_name in href:
                            if href not in internal_links:
                                internal_links.add(href)
                                if href not in crawled:
                                    to_crawl.append(href)
                        else:
                            external_links.add(href)
            except KeyboardInterrupt:
                print(f"\n{Fore.RED}Crawl stopped by user.{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Crawl stopped due to error: {e}{Style.RESET_ALL}")

            print(f"\n{Fore.GREEN}✅ Crawl complete.{Style.RESET_ALL}")
            print(f"\n{Fore.CYAN}--- Found {len(internal_links)} Internal Links ---{Style.RESET_ALL}")
            for link in sorted(list(internal_links)):
                print(f"  - {link}")
            print(f"\n{Fore.CYAN}--- Found {len(external_links)} External Links ---{Style.RESET_ALL}")
            for link in sorted(list(external_links)):
                print(f"  - {link}")
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        def subdomain_bruteforcer(self):
            """Subdomain enumeration tool - EFFICIENT THREAD POOL"""
            print(f"\n{Fore.CYAN}🔎 SUBDOMAIN ENUMERATION{Style.RESET_ALL}")
            if not DNS_AVAILABLE:
                print(f"{Fore.RED}❌ 'dnspython' module is required.{Style.RESET_ALL}")
                return

            domain = input(f"{Fore.WHITE}Enter domain to scan (e.g., example.com): {Style.RESET_ALL}").strip()
            if not domain: return

            common_subdomains = [
                'www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop', 'ns1', 'webdisk',
                'ns2', 'cpanel', 'whm', 'autodiscover', 'm', 'imap', 'test', 'dev', 'admin',
                'blog', 'pop3', 'shop', 'api', 'cdn', 'stats', 'support', 'beta', 'sql', 'secure'
            ] # Shortened list for mobile efficiency

            print(f"[*] Scanning {domain} for {len(common_subdomains)} common subdomains using {self.max_workers} workers...")
            
            found_subdomains = {} # domain: ip
            lock = threading.Lock()

            def check_subdomain(subdomain):
                full_domain = f"{subdomain}.{domain}"
                try:
                    answers = dns_resolver.resolve(full_domain, 'A')
                    ip = str(answers[0])
                    with lock:
                        found_subdomains[full_domain] = ip
                        print(f"{Fore.GREEN}[+] Found: {full_domain:30} -> {ip}{Style.RESET_ALL}")
                except:
                    pass # NXDOMAIN, NoAnswer, Timeout

            # --- EFFICIENT THREAD POOL ---
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(check_subdomain, sub) for sub in common_subdomains]
                for future in concurrent.futures.as_completed(futures):
                    pass # Results are printed live

            print(f"\n{Fore.GREEN}✅ Scan complete! Found {len(found_subdomains)} subdomains.{Style.RESET_ALL}")
            
            if found_subdomains:
                for domain_name, ip in found_subdomains.items():
                    self.record_audit_finding(domain, 'Subdomain Enumeration', f'Found subdomain: {domain_name}', f'IP: {ip}', 'Informational')

            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        def directory_bruteforcer(self):
            """Directory and file bruteforcer - EFFICIENT THREAD POOL"""
            print(f"\n{Fore.CYAN}📁 DIRECTORY BRUTEFORCER{Style.RESET_ALL}")
            if not REQUESTS_AVAILABLE:
                print(f"{Fore.RED}❌ 'requests' module is required.{Style.RESET_ALL}")
                return

            base_url = input(f"{Fore.WHITE}Enter base URL (e.g., http://example.com): {Style.RESET_ALL}").strip()
            if not base_url.startswith(('http://', 'https://')):
                base_url = 'http://' + base_url
            if base_url.endswith('/'):
                base_url = base_url[:-1]

            common_paths = [
                'admin', 'administrator', 'login', 'wp-admin', 'phpmyadmin', 'cpanel', 'webmail',
                'backup', 'test', 'dev', 'api', 'uploads', 'images', 'css', 'js', 'includes',
                'logs', 'config', 'install', 'phpinfo.php', 'robots.txt', 'sitemap.xml',
                '.htaccess', '.git/config', '.env', 'wp-config.php', 'config.json'
            ] # Shortened list

            print(f"[*] Scanning {base_url} for {len(common_paths)} common paths using {self.max_workers} workers...")
            
            found_paths = {} # url: status_code
            lock = threading.Lock()
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}

            def check_path(path):
                test_url = f"{base_url}/{path}"
                try:
                    response = requests.get(test_url, timeout=3, headers=headers, allow_redirects=False)
                    if response.status_code in [200, 301, 302, 403, 500]:
                        status_color = Fore.GREEN if response.status_code == 200 else Fore.YELLOW
                        with lock:
                            found_paths[test_url] = response.status_code
                            print(f"{status_color}[{response.status_code}] {test_url}{Style.RESET_ALL}")
                except requests.exceptions.RequestException:
                    pass

            # --- EFFICIENT THREAD POOL ---
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(check_path, path) for path in common_paths]
                for future in concurrent.futures.as_completed(futures):
                    pass

            print(f"\n{Fore.GREEN}✅ Scan complete! Found {len(found_paths)} accessible paths.{Style.RESET_ALL}")
            for url, status in found_paths.items():
                severity = 'Medium' if status == 200 else 'Low' if status == 403 else 'Informational'
                if '.git' in url or '.env' in url or 'config' in url:
                    severity = 'High'
                self.record_audit_finding(base_url, 'Directory Brute Force', f'Found: {url}', f'Status: {status}', severity)
                
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
        
        def reverse_ip_lookup(self):
            """Finds domains hosted on the same IP using an external API."""
            print(f"\n{Fore.CYAN}🔄 REVERSE IP LOOKUP{Style.RESET_ALL}")
            if not REQUESTS_AVAILABLE:
                print(f"{Fore.RED}❌ 'requests' module is required.{Style.RESET_ALL}")
                return
            
            target = input(f"{Fore.WHITE}Enter domain or IP address: {Style.RESET_ALL}").strip()
            if not target: return
            
            print(f"[*] Querying API for domains on {target}...")
            api_url = f"https://api.hackertarget.com/reverseiplookup/?q={target}"
            
            try:
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200 and 'error' not in response.text.lower():
                    domains = response.text.splitlines()
                    print(f"\n{Fore.GREEN}✅ Found {len(domains)} domains:{Style.RESET_ALL}")
                    for domain in domains:
                        print(f"  - {domain}")
                        self.record_audit_finding(target, 'Reverse IP', 'Found Domain', domain, 'Informational')
                elif 'no records found' in response.text.lower():
                     print(f"{Fore.YELLOW}No other domains found on this IP.{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}❌ API Error: {response.text}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Failed to query API: {e}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            
        def cms_detector(self):
            """Detects common Content Management Systems."""
            print(f"\n{Fore.CYAN}🧬 CMS DETECTOR{Style.RESET_ALL}")
            if not REQUESTS_AVAILABLE:
                print(f"{Fore.RED}❌ 'requests' module is required.{Style.RESET_ALL}")
                return

            target = input(f"{Fore.WHITE}Enter target URL (e.g., http://example.com): {Style.RESET_ALL}").strip()
            if not target.startswith(('http://', 'https://')):
                target = 'http://' + target
            
            print(f"[*] Analyzing {target} for CMS signatures...")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
            
            cms_found = None
            try:
                # Check WordPress
                wp_url = urljoin(target, '/wp-includes/wlwmanifest.xml')
                if requests.get(wp_url, timeout=3, headers=headers).status_code == 200:
                    cms_found = "WordPress"
                
                if not cms_found:
                    # Check Joomla
                    joomla_url = urljoin(target, '/administrator/manifests/files/joomla.xml')
                    if requests.get(joomla_url, timeout=3, headers=headers).status_code == 200:
                        cms_found = "Joomla"
                
                if not cms_found:
                    # Check Drupal
                    drupal_url = urljoin(target, '/misc/drupal.js')
                    if 'Drupal' in requests.get(drupal_url, timeout=3, headers=headers).text:
                        cms_found = "Drupal"
                
                # Check page source for meta generator tags
                if not cms_found:
                    response = requests.get(target, timeout=3, headers=headers)
                    if 'name="generator" content="WordPress' in response.text:
                        cms_found = "WordPress"
                    elif 'name="generator" content="Joomla' in response.text:
                        cms_found = "Joomla"
                    elif 'name="Generator" content="Drupal' in response.text:
                        cms_found = "Drupal"
                    elif 'Shopify' in response.text:
                        cms_found = "Shopify"
                        
                if cms_found:
                    print(f"\n{Fore.GREEN}✅ Detected CMS: {cms_found}{Style.RESET_ALL}")
                    self.record_audit_finding(target, 'CMS Detection', 'CMS Detected', cms_found, 'Informational')
                else:
                    print(f"\n{Fore.YELLOW}Could not identify a common CMS.{Style.RESET_ALL}")

            except Exception as e:
                print(f"{Fore.RED}❌ Scan failed: {e}{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        # --- Security Auditing Tools (No Root Required) ---
        def http_header_analyzer(self):
            print(f"\n{Fore.CYAN}📋 HTTP SECURITY HEADER ANALYZER{Style.RESET_ALL}")
            if not REQUESTS_AVAILABLE:
                print(f"{Fore.RED}❌ 'requests' module is not available.{Style.RESET_ALL}")
                return
            
            url = input(f"{Fore.WHITE}Enter URL to analyze (e.g., https://google.com): {Style.RESET_ALL}").strip()
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, timeout=10, headers=headers, allow_redirects=True)
                headers = response.headers
                print(f"\n{Fore.GREEN}✅ Analyzing headers for {response.url}{Style.RESET_ALL}")
                
                security_headers = {
                    'Strict-Transport-Security': 'Enforces HTTPS.',
                    'Content-Security-Policy': 'Prevents XSS.',
                    'X-Content-Type-Options': 'Prevents MIME-sniffing.',
                    'X-Frame-Options': 'Protects against clickjacking.',
                    'Referrer-Policy': 'Controls referrer info.',
                    'Permissions-Policy': 'Controls browser features.'
                }

                for header, desc in security_headers.items():
                    if header in headers:
                        print(f"{Fore.GREEN}[✔] {header}: Found{Style.RESET_ALL}")
                        self.record_audit_finding(url, 'Header Analysis', f'Header Found: {header}', f"Value: {headers[header]}", 'Informational')
                    else:
                        print(f"{Fore.RED}[❌] {header}: Missing{Style.RESET_ALL} - {desc}")
                        self.record_audit_finding(url, 'Header Analysis', f'Missing Header: {header}', desc, 'Medium')
                
                if 'Server' in headers:
                    print(f"{Fore.YELLOW}[!] Exposed Server Banner: {headers['Server']}{Style.RESET_ALL}")
                    self.record_audit_finding(url, 'Header Analysis', 'Exposed Server Banner', f"Server: {headers['Server']}", 'Low')
                if 'X-Powered-By' in headers:
                    print(f"{Fore.YELLOW}[!] Exposed Tech: {headers['X-Powered-By']}{Style.RESET_ALL}")
                    self.record_audit_finding(url, 'Header Analysis', 'Exposed Tech', f"X-Powered-By: {headers['X-Powered-By']}", 'Low')

            except Exception as e:
                print(f"{Fore.RED}❌ Failed to analyze URL: {e}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        def vulnerability_scanner(self):
            """Basic web vulnerability scanner - No root required"""
            print(f"\n{Fore.CYAN}🔍 WEB VULNERABILITY SCANNER (BASIC){Style.RESET_ALL}")
            if not REQUESTS_AVAILABLE:
                print(f"{Fore.RED}❌ 'requests' module is required.{Style.RESET_ALL}")
                return

            target = input(f"{Fore.WHITE}Enter target URL (e.g., http://example.com): {Style.RESET_ALL}").strip()
            if not target.startswith(('http://', 'https://')):
                target = 'http://' + target

            print(f"[*] Scanning {target} for common vulnerabilities...")
            vulnerabilities_found = []
            headers = {'User-Agent': 'Mozilla/5.0'}

            # 1. Test for SQL Injection (Error-based)
            sql_payload = "'"
            test_url = f"{target}/?id=1{sql_payload}" # Common parameter
            try:
                response = requests.get(test_url, timeout=5, headers=headers)
                if any(error in response.text.lower() for error in ['sql', 'mysql', 'syntax', 'ora-']):
                    vulnerabilities_found.append(('SQL Injection (Error-based)', test_url, 'High'))
            except:
                pass

            # 2. Test for XSS (Reflected)
            xss_payload = "<script>alert('XSS')</script>"
            test_url = f"{target}/?s={xss_payload}" # Common parameter
            try:
                response = requests.get(test_url, timeout=5, headers=headers)
                if xss_payload in response.text:
                    vulnerabilities_found.append(('XSS (Reflected)', test_url, 'Medium'))
            except:
                pass

            # 3. Test for Directory Traversal
            trav_payload = "../../../../etc/passwd"
            test_url = f"{target}/?file={trav_payload}"
            try:
                response = requests.get(test_url, timeout=5, headers=headers)
                if 'root:x:0:0:' in response.text:
                    vulnerabilities_found.append(('Directory Traversal', test_url, 'High'))
            except:
                pass
            
            # 4. Check for robots.txt
            try:
                response = requests.get(urljoin(target, '/robots.txt'), timeout=5, headers=headers)
                if response.status_code == 200 and 'Disallow:' in response.text:
                    vulnerabilities_found.append(('Informative robots.txt', urljoin(target, '/robots.txt'), 'Low'))
            except:
                pass

            # Display results
            if vulnerabilities_found:
                print(f"\n{Fore.RED}🚨 POTENTIAL VULNERABILITIES FOUND:{Style.RESET_ALL}")
                for vuln_type, url, severity in vulnerabilities_found:
                    color = Fore.RED if severity == 'High' else Fore.YELLOW
                    print(f"{color}[{severity}] {vuln_type}:{Style.RESET_ALL} (Payload: {url})")
                    self.record_audit_finding(target, 'Vulnerability Scan', vuln_type, f"Found at {url}", severity)
            else:
                print(f"{Fore.GREEN}✅ No obvious (basic) vulnerabilities detected.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Note: This is a basic scanner. Use dedicated tools for a real audit.{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        def sql_injection_tester(self):
            """Focused SQL injection testing tool"""
            print(f"\n{Fore.CYAN}💉 SQL INJECTION TESTER{Style.RESET_ALL}")
            if not REQUESTS_AVAILABLE:
                print(f"{Fore.RED}❌ 'requests' module is required.{Style.RESET_ALL}")
                return

            target_url = input(f"{Fore.WHITE}Enter target URL with parameter (e.g., http://site.com/page.php?id=1): {Style.RESET_ALL}").strip()
            if '?' not in target_url or '=' not in target_url:
                print(f"{Fore.RED}❌ URL must contain a parameter (e.g., ?id=1){Style.RESET_ALL}")
                return

            base_url, param_part = target_url.split('?', 1)
            param_name, original_value = param_part.split('=', 1)
            
            print(f"[*] Testing parameter '{param_name}' on {base_url}")
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            payloads = {
                "'": "Basic syntax error",
                "' OR '1'='1": "Boolean-based",
                "' AND 1=1--": "Comment-based",
                "' AND (SELECT 1 FROM (SELECT(SLEEP(5)))a)--": "Time-based (5s)"
            }

            vulnerable = False
            for payload, desc in payloads.items():
                test_url = f"{base_url}?{param_name}={original_value}{payload}"
                print(f"[*] Testing: {desc}")
                
                try:
                    start_time = time.time()
                    response = requests.get(test_url, timeout=10, headers=headers)
                    response_time = time.time() - start_time

                    if any(error in response.text.lower() for error in ['sql', 'mysql', 'syntax', 'ora-']):
                        print(f"{Fore.RED}[!] Potential SQLi (Error-based): {desc}{Style.RESET_ALL}")
                        self.record_audit_finding(target_url, 'SQL Injection', desc, f"Payload: {payload}", 'High')
                        vulnerable = True
                    elif response_time > 5:
                        print(f"{Fore.RED}[!] Potential SQLi (Time-based): {desc}{Style.RESET_ALL}")
                        self.record_audit_finding(target_url, 'SQL Injection', f"Time-Based: {desc}", f"Response time: {response_time:.2f}s", 'High')
                        vulnerable = True
                except requests.exceptions.Timeout:
                    print(f"{Fore.RED}[!] Potential SQLi (Time-based): {desc} - Request timed out > 10s{Style.RESET_ALL}")
                    self.record_audit_finding(target_url, 'SQL Injection', f"Timeout-Based: {desc}", "Request timed out", 'High')
                    vulnerable = True
                except Exception as e:
                    print(f"[!] Error testing {desc}: {e}")

            if not vulnerable:
                print(f"{Fore.GREEN}✅ No SQL injection vulnerabilities detected.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}🚨 SQL injection vulnerabilities may exist!{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        def xss_scanner(self):
            """Focused XSS scanner"""
            print(f"\n{Fore.CYAN}🎯 XSS SCANNER{Style.RESET_ALL}")
            if not REQUESTS_AVAILABLE:
                print(f"{Fore.RED}❌ 'requests' module is required.{Style.RESET_ALL}")
                return

            target_url = input(f"{Fore.WHITE}Enter target URL with parameter (e.g., http://site.com/search?q=test): {Style.RESET_ALL}").strip()
            if '?' not in target_url or '=' not in target_url:
                print(f"{Fore.RED}❌ URL must contain a parameter (e.g., ?q=test){Style.RESET_ALL}")
                return

            base_url, param_part = target_url.split('?', 1)
            param_name, original_value = param_part.split('=', 1)
            
            print(f"[*] Testing parameter '{param_name}' on {base_url}")
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            payloads = [
                "<script>alert('XSS')</script>",
                "\"><script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "onmouseover=alert('XSS')",
                "<img src=x onerror=alert('XSS')>"
            ]

            vulnerable = False
            for payload in payloads:
                test_url = f"{base_url}?{param_name}={payload}"
                print(f"[*] Testing: {payload[:20]}...")
                
                try:
                    response = requests.get(test_url, timeout=5, headers=headers)
                    if payload in response.text:
                        print(f"{Fore.RED}[!] Potential XSS: Payload reflected{Style.RESET_ALL}")
                        self.record_audit_finding(target_url, 'XSS Scan', 'Reflected XSS', f"Payload: {payload}", 'Medium')
                        vulnerable = True
                except Exception as e:
                    print(f"[!] Error testing {payload}: {e}")

            if not vulnerable:
                print(f"{Fore.GREEN}✅ No XSS vulnerabilities detected.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}🚨 XSS vulnerabilities may exist!{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        def ssh_brute_forcer(self):
            """SSH brute force tool - No root required"""
            print(f"\n{Fore.CYAN}🔐 SSH BRUTE FORCER{Style.RESET_ALL}")
            if not PARAMIKO_AVAILABLE:
                print(f"{Fore.RED}❌ 'paramiko' module is required.{Style.RESET_ALL}")
                return

            host = input(f"{Fore.WHITE}Enter SSH host (IP or domain): {Style.RESET_ALL}").strip()
            port = int(input(f"{Fore.WHITE}Enter SSH port (default 22): {Style.RESET_ALL}").strip() or 22)
            username = input(f"{Fore.WHITE}Enter username to test: {Style.RESET_ALL}").strip()
            
            print(f"[*] Testing SSH {host}:{port} with username '{username}'")
            
            common_passwords = ['admin', '123456', 'password', '1234', '12345', '123456789', 'letmein', '1234567', '123', 'abc123']
            
            found_password = None
            for password in common_passwords:
                try:
                    print(f"[*] Trying: {password}")
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(host, port=port, username=username, password=password, timeout=5)
                    
                    found_password = password
                    print(f"\n{Fore.GREEN}✅ SUCCESS! Password found: {password}{Style.RESET_ALL}")
                    self.record_audit_finding(host, 'SSH Brute Force', 'Successful Login', f"User: {username}, Password: {password}", 'Critical')
                    ssh.close()
                    break
                except paramiko.AuthenticationException:
                    pass
                except Exception as e:
                    print(f"[!] Connection error: {e}")
                    break
            
            if not found_password:
                print(f"{Fore.RED}❌ No valid password found in common list.{Style.RESET_ALL}")
            
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        # --- Data & Database Management (No Root Required) ---
        def view_audit_logs(self):
            print(f"\n{Fore.CYAN}📊 AUDIT LOGS & FINDINGS{Style.RESET_ALL}")
            with sqlite3.connect(self.audit_db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT target, audit_type, finding_title, description, severity, timestamp 
                    FROM audit_results ORDER BY timestamp DESC LIMIT 50
                ''')
                rows = cursor.fetchall()
                
                if not rows:
                    print(f"{Fore.YELLOW}No audit findings yet.{Style.RESET_ALL}")
                else:
                    print(f"{Fore.GREEN}Recent Audit Findings:{Style.RESET_ALL}")
                    for row in rows:
                        target, audit_type, title, desc, severity, timestamp = row
                        color = Fore.RED if severity == 'Critical' else Fore.YELLOW if severity in ['High', 'Medium'] else Fore.GREEN
                        print(f"\n{color}[{severity}] {audit_type} - {title}{Style.RESET_ALL}")
                        print(f"  Target: {target}")
                        print(f"  Description: {desc}")
                        print(f"  Time: {timestamp}")
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        def export_audit_logs(self):
            print(f"\n{Fore.CYAN}💾 EXPORT AUDIT LOGS{Style.RESET_ALL}")
            export_file = os.path.join(self.save_dir, f"audit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            try:
                with sqlite3.connect(self.audit_db_name) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM audit_results ORDER BY timestamp DESC')
                    rows = cursor.fetchall()
                    
                    with open(export_file, 'w', encoding='utf-8') as f:
                        f.write("ADVANCED NETWORK TOOLS - AUDIT LOG EXPORT\n")
                        f.write(f"Export Date: {datetime.now()}\n")
                        f.write("="*60 + "\n\n")
                        for row in rows:
                            f.write(f"Target: {row[1]}\n")
                            f.write(f"Type: {row[2]}\n")
                            f.write(f"Finding: {row[3]}\n")
                            f.write(f"Description: {row[4]}\n")
                            f.write(f"Severity: {row[5]}\n")
                            f.write(f"Timestamp: {row[6]}\n")
                            f.write("-"*40 + "\n")
                print(f"{Fore.GREEN}✅ Audit logs exported to: {export_file}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Export failed: {e}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        def view_wifi_history(self):
            print(f"\n{Fore.CYAN}📶 WI-FI SCAN HISTORY{Style.RESET_ALL}")
            with sqlite3.connect(self.wifi_db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT bssid, ssid, signal_strength, channel, encryption, first_seen, last_seen, is_trusted 
                    FROM network_scans ORDER BY last_seen DESC LIMIT 50
                ''')
                rows = cursor.fetchall()
                
                if not rows:
                    print(f"{Fore.YELLOW}No Wi-Fi scan history yet.{Style.RESET_ALL}")
                else:
                    print(f"{Fore.GREEN}Recent Wi-Fi Networks:{Style.RESET_ALL}")
                    for row in rows:
                        bssid, ssid, signal, channel, enc, first_seen, last_seen, trusted = row
                        trust_status = f"{Fore.GREEN}TRUSTED{Style.RESET_ALL}" if trusted else f"{Fore.YELLOW}UNKNOWN{Style.RESET_ALL}"
                        print(f"\n{Fore.CYAN}--- {ssid or 'Hidden'} ---{Style.RESET_ALL}")
                        print(f"  BSSID: {bssid}")
                        print(f"  Signal: {signal}dBm | Channel: {channel}")
                        print(f"  Encryption: {enc}")
                        print(f"  First Seen: {first_seen}")
                        print(f"  Last Seen: {last_seen}")
                        print(f"  Status: {trust_status}")
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        def manage_trusted_networks(self):
            print(f"\n{Fore.CYAN}🔒 MANAGE TRUSTED NETWORKS{Style.RESET_ALL}")
            print("1. Add trusted network")
            print("2. Remove trusted network") 
            print("3. View trusted networks")
            choice = input(f"{Fore.WHITE}Select option (1-3): {Style.RESET_ALL}").strip()
            
            if choice == '1':
                bssid = input(f"{Fore.WHITE}Enter BSSID to trust (e.g., AA:BB:CC:DD:EE:FF): {Style.RESET_ALL}").strip().upper()
                if re.match(r'^([0-9A-F]{2}:){5}[0-9A-F]{2}$', bssid):
                    self.trusted_bssids.add(bssid)
                    self.known_networks['trusted_bssids'] = list(self.trusted_bssids)
                    self.save_known_networks()
                    print(f"{Fore.GREEN}✅ Added {bssid} to trusted networks.{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}❌ Invalid BSSID format.{Style.RESET_ALL}")
                    
            elif choice == '2':
                if self.trusted_bssids:
                    print(f"{Fore.YELLOW}Current trusted BSSIDs:{Style.RESET_ALL}")
                    for bssid in self.trusted_bssids:
                        print(f"  - {bssid}")
                    bssid = input(f"{Fore.WHITE}Enter BSSID to remove: {Style.RESET_ALL}").strip().upper()
                    if bssid in self.trusted_bssids:
                        self.trusted_bssids.remove(bssid)
                        self.known_networks['trusted_bssids'] = list(self.trusted_bssids)
                        self.save_known_networks()
                        print(f"{Fore.GREEN}✅ Removed {bssid} from trusted networks.{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}❌ BSSID not found in trusted list.{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}No trusted networks to remove.{Style.RESET_ALL}")
                    
            elif choice == '3':
                if self.trusted_bssids:
                    print(f"{Fore.GREEN}✅ Trusted Networks:{Style.RESET_ALL}")
                    for bssid in self.trusted_bssids:
                        print(f"  - {bssid}")
                else:
                    print(f"{Fore.YELLOW}No trusted networks configured.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ Invalid choice.{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        def clear_database(self):
            print(f"\n{Fore.RED}🧹 CLEAR DATABASE{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}This will delete all scan history and audit logs.{Style.RESET_ALL}")
            confirm = input(f"{Fore.WHITE}Type 'DELETE' to confirm: {Style.RESET_ALL}").strip()
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
                    print(f"{Fore.GREEN}✅ All databases cleared.{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}❌ Error clearing databases: {e}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Clear operation cancelled.{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        # --- SSH Defender Integration ---
        def run_ssh_defender(self):
            """Starts the SSH Defender Honeypot system."""
            print(f"\n{Fore.CYAN}🛡️ LAUNCHING SSH DEFENDER HONEYPOT{Style.RESET_ALL}")
            time.sleep(1)

            # Set up SSH Defender directories inside our save directory
            ssh_base_dir = os.path.join(self.save_dir, "SSH_Defender")
            log_dir = os.path.join(ssh_base_dir, "logs")
            stats_file = os.path.join(ssh_base_dir, "attack_stats.json")
            
            os.makedirs(log_dir, exist_ok=True)
            
            # Initialize logger and executor
            logger = Logger(log_dir, stats_file)
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=50)
            
            # Initialize SSH Defender
            defender = SSHDefender(HOST, logger, executor)
            
            print(f"\n{Fore.CYAN}SSH Defender Options:{Style.RESET_ALL}")
            print("1. Start on specific port")
            print("2. Cycle through famous ports (5 minutes each)")
            print("3. Start with TUI (Terminal User Interface)")
            
            choice = input(f"{Fore.WHITE}Select mode (1-3): {Style.RESET_ALL}").strip()
            
            if choice == '1':
                try:
                    port = int(input(f"{Fore.WHITE}Enter port to listen on: {Style.RESET_ALL}").strip())
                    if not (1 <= port <= 65535):
                        raise ValueError("Port must be between 1 and 65535")
                    defender.start_port_listener(port)
                    input(f"{Fore.YELLOW}Press Enter to stop listening...{Style.RESET_ALL}")
                    defender.running = False
                    defender.stop_all_ports()
                except ValueError as e:
                    print(f"{Fore.RED}❌ Invalid port: {e}{Style.RESET_ALL}")
            
            elif choice == '2':
                print(f"\n{Fore.YELLOW}[*] Starting port cycling mode...{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Will cycle through famous ports every 5 minutes.{Style.RESET_ALL}")
                defender.run_port_cycle()
            
            elif choice == '3':
                if not CURSES_AVAILABLE:
                    print(f"{Fore.RED}❌ TUI mode requires 'curses' module.{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}On Termux, run: pkg install ncurses-utils{Style.RESET_ALL}")
                    return
                
                try:
                    port = int(input(f"{Fore.WHITE}Enter port to listen on: {Style.RESET_ALL}").strip())
                    if not (1 <= port <= 65535):
                        raise ValueError("Port must be between 1 and 65535")
                    
                    defender.start_port_listener(port)
                    if defender.running:
                        print(f"{Fore.GREEN}✅ SSH Defender TUI started on port {port}{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}Press 'q' to quit, 's' to save stats.{Style.RESET_ALL}")
                        
                        # Initialize and run TUI
                        def tui_wrapper(stdscr):
                            defender.tui = DefenderTUI(stdscr, defender)
                            defender.tui.run()
                        
                        curses.wrapper(tui_wrapper)
                        defender.running = False
                        defender.stop_all_ports()
                except ValueError as e:
                    print(f"{Fore.RED}❌ Invalid port: {e}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ Invalid choice.{Style.RESET_ALL}")
            
            # Cleanup
            defender.stop_all_ports()
            logger.save_stats()
            print(f"\n{Fore.GREEN}✅ SSH Defender terminated.{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        # --- Settings & Configuration ---
        def edit_configuration(self):
            print(f"\n{Fore.CYAN}⚙️ EDIT CONFIGURATION{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Current Configuration:{Style.RESET_ALL}")
            for key, value in self.config.items():
                print(f"  {key}: {value}")
            
            print(f"\n{Fore.CYAN}Options:{Style.RESET_ALL}")
            print("1. Edit scan interval")
            print("2. Edit port scan threads")
            print("3. Edit top ports list")
            print("4. Edit common usernames")
            print("5. Edit common passwords")
            print("6. Reset to defaults")
            
            choice = input(f"{Fore.WHITE}Select option (1-6): {Style.RESET_ALL}").strip()
            
            if choice == '1':
                try:
                    interval = int(input(f"{Fore.WHITE}New scan interval (seconds): {Style.RESET_ALL}").strip())
                    self.config['scan_interval'] = max(10, interval)
                except ValueError:
                    print(f"{Fore.RED}❌ Invalid number.{Style.RESET_ALL}")
                    
            elif choice == '2':
                try:
                    threads = int(input(f"{Fore.WHITE}New max scan workers: {Style.RESET_ALL}").strip())
                    self.config['max_scan_workers'] = max(1, min(100, threads))
                    self.max_workers = self.config['max_scan_workers']
                except ValueError:
                    print(f"{Fore.RED}❌ Invalid number.{Style.RESET_ALL}")
                    
            elif choice == '3':
                ports = input(f"{Fore.WHITE}New top ports (comma-separated): {Style.RESET_ALL}").strip()
                if ports:
                    self.config['top_ports'] = ports
                    
            elif choice == '4':
                usernames = input(f"{Fore.WHITE}New common usernames (comma-separated): {Style.RESET_ALL}").strip()
                if usernames:
                    self.config['common_usernames'] = usernames
                    
            elif choice == '5':
                passwords = input(f"{Fore.WHITE}New common passwords (comma-separated): {Style.RESET_ALL}").strip()
                if passwords:
                    self.config['common_passwords'] = passwords
                    
            elif choice == '6':
                print(f"{Fore.YELLOW}Resetting to defaults...{Style.RESET_ALL}")
                self.load_config() # Reload defaults
            else:
                print(f"{Fore.RED}❌ Invalid choice.{Style.RESET_ALL}")
                return
                
            self.save_config()
            print(f"{Fore.GREEN}✅ Configuration updated.{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        def show_about(self):
            print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}           ADVANCED NETWORK & SECURITY TOOLKIT{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Version: 2.0 (Combined & Optimized){Style.RESET_ALL}")
            print(f"{Fore.WHITE}Platform: Termux (Android) & Linux{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Author: DedSec Team{Style.RESET_ALL}")
            print(f"{Fore.WHITE}Save Directory: {self.save_dir}{Style.RESET_ALL}")
            print(f"\n{Fore.YELLOW}Features:{Style.RESET_ALL}")
            print("  ✓ Wi-Fi & Network Scanning (No Root)")
            print("  ✓ Port Scanning & Network Discovery")
            print("  ✓ Internet Diagnostics & Speed Testing")
            print("  ✓ OSINT & Information Gathering")
            print("  ✓ Web Security & Vulnerability Scanning")
            print("  ✓ SSH Defender Honeypot System")
            print("  ✓ Comprehensive Audit Logging")
            print(f"\n{Fore.GREEN}All tools work without root access!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

        def run(self):
            """Main application loop with TUI menu."""
            while True:
                try:
                    # Main menu options
                    menu_options = [
                        "--- WI-FI & LOCAL NETWORK TOOLS ---",
                        "Single Wi-Fi Scan",
                        "View Current Connection",
                        "Toggle Wi-Fi (Termux:API)",
                        "Mobile Data & SIM Info",
                        "--- NETWORK SCANNING & DISCOVERY ---",
                        "Nmap Wrapper",
                        "Enhanced Port Scanner",
                        "Network Discovery",
                        "Subnet Calculator",
                        "--- INTERNET & DIAGNOSTICS ---",
                        "Internet Speed Test",
                        "External IP Information",
                        "Network Diagnostics (Ping/Traceroute)",
                        "--- INFORMATION GATHERING (OSINT) ---",
                        "OSINTDS Scanner",
                        "WHOIS Lookup",
                        "DNS Record Lookup",
                        "Web Crawler / Link Extractor",
                        "Subdomain Bruteforcer",
                        "Directory Bruteforcer",
                        "Reverse IP Lookup",
                        "CMS Detector",
                        "--- SECURITY AUDITING TOOLS ---",
                        "HTTP Header Analyzer",
                        "Vulnerability Scanner (Basic)",
                        "SQL Injection Tester",
                        "XSS Scanner",
                        "SSH Brute Forcer",
                        "SSH Defender Honeypot",
                        "--- DATA & MANAGEMENT ---",
                        "View Audit Logs",
                        "Export Audit Logs",
                        "View Wi-Fi History",
                        "Manage Trusted Networks",
                        "Clear Database",
                        "--- SETTINGS & CONFIG ---",
                        "Edit Configuration",
                        "Show About / System Info",
                        "Exit"
                    ]

                    if CURSES_AVAILABLE:
                        # Use curses TUI
                        selected_idx = curses.wrapper(_draw_curses_menu, "ADVANCED NETWORK TOOLS", menu_options)
                    else:
                        # Fallback to simple text menu
                        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
                        print(f"{Fore.CYAN}           ADVANCED NETWORK & SECURITY TOOLKIT{Style.RESET_ALL}")
                        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
                        for i, option in enumerate(menu_options):
                            if option.startswith("---"):
                                print(f"{Fore.YELLOW}{option}{Style.RESET_ALL}")
                            else:
                                print(f"{Fore.WHITE}{i:2}. {option}{Style.RESET_ALL}")
                        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
                        try:
                            selected_idx = int(input(f"{Fore.WHITE}Select option (0-{len(menu_options)-1}): {Style.RESET_ALL}").strip())
                        except ValueError:
                            selected_idx = -1

                    # Map selection to methods
                    if selected_idx == 0 or menu_options[selected_idx] == "Single Wi-Fi Scan":
                        self.single_wifi_scan()
                    elif selected_idx == 1 or menu_options[selected_idx] == "View Current Connection":
                        self.view_current_connection()
                    elif selected_idx == 2 or menu_options[selected_idx] == "Toggle Wi-Fi (Termux:API)":
                        self.toggle_wifi()
                    elif selected_idx == 3 or menu_options[selected_idx] == "Mobile Data & SIM Info":
                        self.get_mobile_data_info()
                    elif selected_idx == 4 or menu_options[selected_idx] == "Nmap Wrapper":
                        self.nmap_wrapper()
                    elif selected_idx == 5 or menu_options[selected_idx] == "Enhanced Port Scanner":
                        self.enhanced_port_scanner()
                    elif selected_idx == 6 or menu_options[selected_idx] == "Network Discovery":
                        self.network_discovery()
                    elif selected_idx == 7 or menu_options[selected_idx] == "Subnet Calculator":
                        self.subnet_calculator()
                    elif selected_idx == 8 or menu_options[selected_idx] == "Internet Speed Test":
                        self.run_internet_speed_test()
                    elif selected_idx == 9 or menu_options[selected_idx] == "External IP Information":
                        self.get_external_ip_info()
                    elif selected_idx == 10 or menu_options[selected_idx] == "Network Diagnostics (Ping/Traceroute)":
                        self.run_network_diagnostics()
                    elif selected_idx == 11 or menu_options[selected_idx] == "OSINTDS Scanner":
                        self.run_osintds_scanner()
                    elif selected_idx == 12 or menu_options[selected_idx] == "WHOIS Lookup":
                        self.get_whois_info()
                    elif selected_idx == 13 or menu_options[selected_idx] == "DNS Record Lookup":
                        self.get_dns_records()
                    elif selected_idx == 14 or menu_options[selected_idx] == "Web Crawler / Link Extractor":
                        self.web_crawler()
                    elif selected_idx == 15 or menu_options[selected_idx] == "Subdomain Bruteforcer":
                        self.subdomain_bruteforcer()
                    elif selected_idx == 16 or menu_options[selected_idx] == "Directory Bruteforcer":
                        self.directory_bruteforcer()
                    elif selected_idx == 17 or menu_options[selected_idx] == "Reverse IP Lookup":
                        self.reverse_ip_lookup()
                    elif selected_idx == 18 or menu_options[selected_idx] == "CMS Detector":
                        self.cms_detector()
                    elif selected_idx == 19 or menu_options[selected_idx] == "HTTP Header Analyzer":
                        self.http_header_analyzer()
                    elif selected_idx == 20 or menu_options[selected_idx] == "Vulnerability Scanner (Basic)":
                        self.vulnerability_scanner()
                    elif selected_idx == 21 or menu_options[selected_idx] == "SQL Injection Tester":
                        self.sql_injection_tester()
                    elif selected_idx == 22 or menu_options[selected_idx] == "XSS Scanner":
                        self.xss_scanner()
                    elif selected_idx == 23 or menu_options[selected_idx] == "SSH Brute Forcer":
                        self.ssh_brute_forcer()
                    elif selected_idx == 24 or menu_options[selected_idx] == "SSH Defender Honeypot":
                        self.run_ssh_defender()
                    elif selected_idx == 25 or menu_options[selected_idx] == "View Audit Logs":
                        self.view_audit_logs()
                    elif selected_idx == 26 or menu_options[selected_idx] == "Export Audit Logs":
                        self.export_audit_logs()
                    elif selected_idx == 27 or menu_options[selected_idx] == "View Wi-Fi History":
                        self.view_wifi_history()
                    elif selected_idx == 28 or menu_options[selected_idx] == "Manage Trusted Networks":
                        self.manage_trusted_networks()
                    elif selected_idx == 29 or menu_options[selected_idx] == "Clear Database":
                        self.clear_database()
                    elif selected_idx == 30 or menu_options[selected_idx] == "Edit Configuration":
                        self.edit_configuration()
                    elif selected_idx == 31 or menu_options[selected_idx] == "Show About / System Info":
                        self.show_about()
                    elif selected_idx == 32 or menu_options[selected_idx] == "Exit":
                        print(f"\n{Fore.GREEN}👋 Thank you for using Advanced Network Tools!{Style.RESET_ALL}")
                        break
                    else:
                        print(f"{Fore.RED}❌ Invalid selection.{Style.RESET_ALL}")
                        input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

                except KeyboardInterrupt:
                    print(f"\n\n{Fore.YELLOW}🛑 Application interrupted by user.{Style.RESET_ALL}")
                    confirm = input(f"{Fore.WHITE}Exit the application? (y/N): {Style.RESET_ALL}").strip().lower()
                    if confirm == 'y':
                        print(f"{Fore.GREEN}👋 Goodbye!{Style.RESET_ALL}")
                        break

    # Initialize and run the application
    if not CURSES_AVAILABLE:
        print(f"{Fore.YELLOW}⚠️  Curses TUI not available. Using fallback text menu.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}   For full TUI experience, install: pkg install ncurses-utils{Style.RESET_ALL}")
        time.sleep(2)

    app = AdvancedNetworkTools()
    app.run()

if __name__ == "__main__":
    # Check for dependency installation
    if len(sys.argv) > 1 and sys.argv[1] == "--install-deps":
        auto_install_dependencies()
        sys.exit(0)
    
    # Check if we're in Termux
    is_termux = os.path.exists('/data/data/com.termux')
    
    # Welcome message
    print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}           ADVANCED NETWORK & SECURITY TOOLKIT{Style.RESET_ALL}")
    print(f"{Fore.CYAN}                   Combined & Optimized v2.0{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Platform: {'Termux (Android)' if is_termux else 'Linux'}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Requirements: No root access needed!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Initializing...{Style.RESET_ALL}")
    
    # Check for missing critical dependencies
    missing_critical = []
    if not CURSES_AVAILABLE:
        missing_critical.append("curses (TUI)")
    if not REQUESTS_AVAILABLE:
        missing_critical.append("requests")
    
    if missing_critical:
        print(f"\n{Fore.RED}❌ Missing critical dependencies:{Style.RESET_ALL}")
        for dep in missing_critical:
            print(f"  - {dep}")
        print(f"\n{Fore.YELLOW}Run: python {sys.argv[0]} --install-deps{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Or manually install missing packages.{Style.RESET_ALL}")
        sys.exit(1)
    
    # All good, start the app
    try:
        main_app_loop()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}🛑 Application closed by user.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n\n{Fore.RED}💥 Unexpected error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()