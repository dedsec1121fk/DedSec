#!/usr/bin/env python3
import socket
import threading
import hashlib
import os
import json
from datetime import datetime
import time
import select
import sys
import curses
import math
from concurrent.futures import ThreadPoolExecutor

# ==============================================================================
# Port Configuration and Cycle List
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

# Configuration (RAM detection/massive range removed)
HOST = '0.0.0.0'
BASE_DIR = "/storage/emulated/0/Download/SSH Defender"
LOG_DIR = os.path.join(BASE_DIR, "logs")
STATS_FILE = os.path.join(BASE_DIR, "attack_stats.json")
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
# Logger Class
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
# SSH Defender Core Logic
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
        
        # Ensure base directory exists
        os.makedirs(BASE_DIR, exist_ok=True)

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
            print(f"✅ SSH Defender listening on {self.host}:{port}...")
            self.running = True
            self.logger.reset_session_stats()
            
            self.listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
            self.listener_thread.start()
            
        except OSError as e:
            print(f"❌ Error binding to port {port}: {e}. (Perhaps another process is running or you lack permissions?)")
            self.running = False
            self.listener_socket = None
            self.current_port = None
            
        except Exception as e:
            print(f"❌ Unhandled error starting listener on port {port}: {e}")
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
                    print(f"\n❌ Listener loop error on port {self.current_port}: {e}")
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
        self.executor = ThreadPoolExecutor(max_workers=50)


    def run_port_cycle(self):
        """Runs the cycling through a list of famous ports."""
        self.cycle_mode = True
        
        for port_index, port in enumerate(FAMOUS_SSH_PORTS):
            
            print(f"\n========================================================")
            print(f"  STARTING MONITORING ON PORT: {port}")
            print(f"========================================================")
            
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
                    print(f"\n\n🚨 CRITICAL ATTACK DETECTED on port {port}!")
                    print(f"   {attempts} attempts in {int(time_elapsed)} seconds.")
                    print("   Switching to permanent monitoring mode for this port.")
                    
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
                print("\n\n✅ Finished monitoring all famous ports without significant attacks. Defender shutting down.")
                self.running = False
                break # Exit the cycling loop
                
            # No attack: Ask user to switch
            next_port = FAMOUS_SSH_PORTS[port_index + 1]
            user_input = input(f"\n\n⏰ 5 minutes passed on port {port} without attacks.\nDo you want to switch to the next famous port ({next_port})? (y/n): ")
            
            self.stop_all_ports()
            
            if user_input.lower() not in ['y']:
                print("\n🛑 User chose to stop port cycling. Defender shutting down.")
                self.running = False
                break
            
        # Final Cleanup
        self.running = False
        self.stop_all_ports()
        self.logger.save_stats()
        print("\n✅ SSH Defender terminated.")


# ==============================================================================
# Terminal User Interface (TUI)
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
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        
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
            self.stdscr.addstr(y_start + i, 12, ip_stat)
            
        y_start += 4
        self.stdscr.addstr(y_start, 2, "Top Ports:")
        for i, port_stat in enumerate(cumulative_stats['Top Targeted Ports']):
            self.stdscr.addstr(y_start + i, 12, port_stat)

        # 4. Status/Key Bindings Bar
        status_text = "q: Quit | s: Save Stats | c: Port Cycle (if applicable)"
        self.stdscr.attron(curses.A_REVERSE)
        self.stdscr.addstr(h-1, 0, status_text.ljust(w))
        self.stdscr.attroff(curses.A_REVERSE)
        
        self.stdscr.refresh()

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
            self.update_display()
            key = self.stdscr.getch()
            
            if key == ord('q') or key == ord('Q') or key == 27:
                self.running = False
                break
            elif key == ord('s') or key == ord('S'):
                self.defender.logger.save_stats()
                self._display_message("Statistics saved successfully.")
            elif key == ord('c') or key == ord('C'):
                # Only allow this option if running in a single port after a cycle stopped
                if not self.defender.cycle_mode and self.defender.current_port not in FAMOUS_SSH_PORTS:
                    self.running = False
                    self.defender.running = False # Signal to the main loop to stop listener and exit

            time.sleep(0.5) # Refresh rate
            
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
        self.stdscr.getch()
        self.stdscr.nodelay(True)

# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    
    # 1. Setup
    logger = Logger(LOG_DIR, STATS_FILE)
    executor = ThreadPoolExecutor(max_workers=50)
    defender = SSHDefender(HOST, logger, executor)

    # 2. Main menu / initial choice
    print("\n" + "="*50)
    print("        SSH Defender - Honeypot")
    print("="*50)
    print(f"Stats/Logs are saved to: {BASE_DIR}")
    print("\nSelect Mode:")
    print("1. Start Port Cycling (Recommended: Listens on famous ports, cycles every 5 mins)")
    print(f"2. Start Permanent Monitoring on a single port (Default: {FAMOUS_SSH_PORTS[0]})")
    print("3. View Cumulative Attack Statistics")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()

    if choice == '1':
        print("\nStarting Port Cycling Mode...")
        # Create TUI instance and attach it to the defender before running the cycle
        def wrapper(stdscr):
            defender.tui = DefenderTUI(stdscr, defender)
            defender.run_port_cycle()

        try:
            curses.wrapper(wrapper)
        except Exception as e:
            print(f"An error occurred during TUI execution: {e}")
            defender.stop_all_ports()
            defender.logger.save_stats()
            
    elif choice == '2':
        default_port = str(FAMOUS_SSH_PORTS[0])
        port_input = input(f"Enter port to monitor permanently (default: {default_port}): ").strip()
        try:
            port = int(port_input) if port_input else FAMOUS_SSH_PORTS[0]
        except ValueError:
            print("Invalid port number. Exiting.")
            sys.exit(1)
            
        defender.cycle_mode = False
        defender.start_port_listener(port)
        
        if defender.running:
            def wrapper(stdscr):
                defender.tui = DefenderTUI(stdscr, defender)
                defender.tui.run()
                
            try:
                curses.wrapper(wrapper)
            except Exception as e:
                print(f"An error occurred during TUI execution: {e}")
            finally:
                defender.stop_all_ports()
                defender.logger.save_stats()
                print("\n✅ SSH Defender terminated.")

    elif choice == '3':
        print("\n--- Cumulative Attack Statistics ---")
        summary = logger.get_cumulative_stats_summary()
        for key, value in summary.items():
            if isinstance(value, list):
                print(f"\n{key}:")
                for item in value:
                    print(f"  - {item}")
            else:
                print(f"{key}: {value}")
        print("\nPress ENTER to exit...")
        input()
        
    elif choice == '4':
        print("\nExiting SSH Defender. Goodbye!")
    else:
        print("\nInvalid choice. Exiting.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSession terminated by user (Ctrl+C).")
    except Exception as e:
        print(f"\n\n💥 An unexpected error occurred in the main execution: {e}")
        import traceback
        traceback.print_exc()