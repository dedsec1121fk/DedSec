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
    b"SSH-2.0-OpenSSH_7.9p1 Raspbian-10\r\n",
    b"SSH-2.0-dropbear_2019.78\r\n"
]

class SSHAttackLogger:
    def __init__(self):
        self.ensure_directories()
        self.attack_stats = self.load_stats()
        
    def ensure_directories(self):
        """Create necessary directories"""
        os.makedirs(LOG_DIR, exist_ok=True)
        
    def load_stats(self):
        """Load attack statistics from file"""
        try:
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE, 'r') as f:
                    data = json.load(f)
                    # Convert list back to set
                    if "unique_ips" in data:
                        data["unique_ips"] = set(data["unique_ips"])
                    return data
        except:
            pass
        return {
            "total_attacks": 0, 
            "unique_ips": set(), 
            "first_seen": "", 
            "last_seen": "",
            "ports_with_attacks": set(),
            "total_ports": 0
        }
    
    def save_stats(self):
        """Save attack statistics to file"""
        try:
            # Convert sets to lists for JSON serialization
            stats = self.attack_stats.copy()
            stats["unique_ips"] = list(stats["unique_ips"])
            stats["ports_with_attacks"] = list(stats["ports_with_attacks"])
            with open(STATS_FILE, 'w') as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            print(f"Σφάλμα κατά την αποθήκευση των στατιστικών: {e}")
    
    def get_log_path(self, ip_address, port):
        """Generate log file path based on current date/time"""
        now = datetime.now()
        date_dir = os.path.join(LOG_DIR, now.strftime("%d-%m-%Y"))
        os.makedirs(date_dir, exist_ok=True)
        
        if ip_address:
            filename = f"{now.strftime('%H-%M')}_{ip_address.replace('.', '_')}_port{port}.txt"
        else:
            filename = f"{now.strftime('%H-%M')}_port{port}_no_attack.txt"
        
        return os.path.join(date_dir, filename)
    
    def log_attack(self, ip_address, port, data, banner_used):
        """Log attack details with comprehensive information"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_path = self.get_log_path(ip_address, port)
        
        # Update statistics
        self.attack_stats["total_attacks"] += 1
        self.attack_stats["unique_ips"].add(ip_address)
        self.attack_stats["ports_with_attacks"].add(port)
        
        if not self.attack_stats["first_seen"]:
            self.attack_stats["first_seen"] = timestamp
        self.attack_stats["last_seen"] = timestamp
        
        # Create detailed log entry
        log_entry = f"""🚨 ΕΙΔΟΠΟΙΗΣΗ ΑΜΥΝΤΗΡΑ SSH 🚨

📅 Χρονοσφραγίδα: {timestamp}
🌐 IP Επιτιθέμενου: {ip_address}:{port}
🛡️  Banner που χρησιμοποιήθηκε: {banner_used.decode().strip()}
📊 Μέγεθος Δεδομένων: {len(data)} bytes

📡 Ακατέργαστα Δεδομένα (Hex):
{data.hex()[:500]}...

📡 Ακατέργαστα Δεδομένα (ASCII):
{self.safe_decode(data)[:200]}

📈 Στατιστικά Συνεδρίας:
• Συνολικές Επιθέσεις: {self.attack_stats['total_attacks']}
• Μοναδικές IP: {len(self.attack_stats['unique_ips'])}
• Πρώτη Επίθεση: {self.attack_stats['first_seen']}
• Τελευταία Επίθεση: {self.attack_stats['last_seen']}

{'='*60}

"""
        # Write to file
        try:
            with open(log_path, 'w') as f:
                f.write(log_entry)
            self.save_stats()
        except Exception as e:
            print(f"Σφάλμα εγγραφής αρχείου καταγραφής: {e}")
        
        return log_path
    
    def log_empty_port(self, port):
        """Log that a port received no attacks"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_path = self.get_log_path(None, port)
        
        log_entry = f"""📭 ΑΝΑΦΟΡΑ ΠΑΡΑΚΟΛΟΥΘΗΣΗΣ ΘΥΡΑΣ

📅 Χρονοσφραγίδα: {timestamp}
🌐 Θύρα: {port}
🚨 Κατάσταση: ΔΕΝ ΕΝΤΟΠΙΣΤΗΚΑΝ ΕΠΙΘΕΣΕΙΣ
💡 Σημείωση: Αυτή η θύρα παρακολουθήθηκε αλλά δεν δέχθηκε προσπάθειες σύνδεσης
    στα τελευταία {EMPTY_CHECK_INTERVAL} δευτερόλεπτα.

📊 Γενικά Στατιστικά:
• Συνολικές Επιθέσεις: {self.attack_stats['total_attacks']}
• Μοναδικές IP: {len(self.attack_stats['unique_ips'])}
• Ενεργές Θύρες Επίθεσης: {len(self.attack_stats['ports_with_attacks'])}

{'='*60}

"""
        try:
            with open(log_path, 'w') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Σφάλμα εγγραφής κενού αρχείου καταγραφής: {e}")
        
        return log_path
    
    def safe_decode(self, data):
        """Safely decode bytes to ASCII, replacing non-printable characters"""
        return ''.join(chr(b) if 32 <= b <= 126 else f'\\x{b:02x}' for b in data)

class PortListener:
    def __init__(self, port, logger, defender):
        self.port = port
        self.logger = logger
        self.defender = defender
        self.server_socket = None
        self.running = False
        self.thread = None
        self.connection_count = 0
        self.last_activity = None
        
    def start(self):
        """Start listening on this port"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((HOST, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)
            self.running = True
            
            self.thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.thread.start()
            return True
            
        except Exception as e:
            # Handle error, especially if port is already in use (EADDRINUSE)
            print(f"❌ Αποτυχία εκκίνησης της θύρας {self.port}: {e}")
            return False
    
    def _listen_loop(self):
        """Main listening loop for this port"""
        while self.running and self.defender.running:
            try:
                client_socket, address = self.server_socket.accept()
                self.connection_count += 1
                self.last_activity = time.time()
                
                # Handle connection in separate thread
                client_thread = threading.Thread(
                    target=self.defender.handle_connection,
                    args=(client_socket, address, self.port),
                    daemon=True
                )
                client_thread.start()
                
            except socket.timeout:
                continue
            except Exception:
                if self.running:
                    pass
    
    def stop(self):
        """Stop listening on this port"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()

class CursesTUI:
    def __init__(self, defender):
        self.defender = defender
        self.stdscr = None
        self.running = False
        
    def init_curses(self):
        """Initialize curses"""
        # Only re-initialize if not already running (for cycling)
        if self.stdscr is None:
            self.stdscr = curses.initscr()
            curses.noecho()
            curses.cbreak()
            # FIXED: Corrected curses.cursor(0) to the correct function curses.curs_set(0)
            curses.curs_set(0)
            self.stdscr.keypad(True)
            self.stdscr.nodelay(1)
        self.running = True
        
    def cleanup_curses(self):
        """Cleanup curses"""
        if self.stdscr:
            # Reset terminal state
            curses.nocbreak()
            self.stdscr.keypad(False)
            curses.echo()
            curses.endwin()
            self.stdscr = None
            self.running = False
            
    def draw_dashboard(self):
        """Draw the main dashboard"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        # Title
        title = "🛡️ ΑΜΥΝΤΗΡΑΣ SSH - HONEYPOT ΘΥΡΩΝ 🛡️"
        self.stdscr.addstr(0, (width - len(title)) // 2, title)
        
        # Status section
        self.stdscr.addstr(2, 2, "📊 ΣΤΑΤΙΣΤΙΚΑ ΠΡΑΓΜΑΤΙΚΟΥ ΧΡΟΝΟΥ")
        self.stdscr.addstr(3, 2, "─" * (width - 4))
        
        stats = self.defender.logger.attack_stats
        
        # Left column - General stats
        self.stdscr.addstr(4, 2, f"• Τρέχουσα Θύρα: {self.defender.current_port}")
        self.stdscr.addstr(5, 2, f"• Συνολικές Επιθέσεις: {stats['total_attacks']}")
        self.stdscr.addstr(6, 2, f"• Μοναδικές IP: {len(stats['unique_ips'])}")
        
        # Right column - Connection stats
        self.stdscr.addstr(4, width//2, f"• Ενεργές Συνδέσεις: {len(self.defender.active_connections)}")
        self.stdscr.addstr(5, width//2, f"• Χρόνος Λειτουργίας: {self.defender.get_uptime()}")
        
        # Timer Display for current cycle
        if self.defender.in_cycle_mode:
            remaining = int(5 * 60 - (time.time() - self.defender.cycle_start_time))
            if remaining > 0:
                self.stdscr.addstr(7, width//2, f"⏱️ Χρονόμετρο Κύκλου: {remaining:03d} δευτ. απομένουν")
            else:
                 self.stdscr.addstr(7, width//2, f"⏱️ Χρονόμετρο Κύκλου: Αναμονή για Εντολή...")
        
        # Recent activity section
        self.stdscr.addstr(9, 2, "🔥 ΠΡΟΣΦΑΤΗ ΔΡΑΣΤΗΡΙΟΤΗΤΑ")
        self.stdscr.addstr(10, 2, "─" * (width - 4))
        
        # Show recent attacks (last 10)
        recent_attacks = self.defender.recent_activities[-10:]
        for i, activity in enumerate(recent_attacks):
            if 12 + i < height - 3:
                self.stdscr.addstr(12 + i, 2, activity[:width-4])
        
        # Controls section at bottom
        controls = "ΧΕΙΡΙΣΜΟΣ: [Q]uit (Έξοδος) | [R]efresh (Ανανέωση) | [S]tats (Στατιστικά)"
        if height > 2:
            self.stdscr.addstr(height-2, (width - len(controls)) // 2, controls)
        
        self.stdscr.refresh()
        
    def run(self):
        """Main TUI loop (runs in a thread)"""
        try:
            self.init_curses()
            last_refresh = 0
            
            while self.defender.running and self.running:
                current_time = time.time()
                
                # Refresh display every 0.5 seconds
                if current_time - last_refresh > 0.5:
                    self.draw_dashboard()
                    last_refresh = current_time
                
                # Check for user input
                try:
                    key = self.stdscr.getch()
                    if key != -1:
                        if key in [ord('q'), ord('Q')]:
                            self.defender.running = False
                            break
                        elif key in [ord('r'), ord('R')]:
                            self.draw_dashboard()
                        elif key in [ord('s'), ord('S')]:
                            self.show_detailed_stats()
                except:
                    pass
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            self.defender.running = False
        finally:
            # Cleanup is handled by the main defender loop when cycling
            if self.stdscr:
                 self.cleanup_curses()

    # show_detailed_stats remains the same
    def show_detailed_stats(self):
        """Show detailed statistics screen"""
        if not self.stdscr:
            return
            
        height, width = self.stdscr.getmaxyx()
        self.stdscr.clear()
        
        stats = self.defender.logger.attack_stats
        
        self.stdscr.addstr(0, (width - 25) // 2, "📈 ΛΕΠΤΟΜΕΡΗ ΣΤΑΤΙΣΤΙΚΑ")
        
        row = 2
        self.stdscr.addstr(row, 2, f"Συνολικές Επιθέσεις: {stats['total_attacks']}"); row += 1
        self.stdscr.addstr(row, 2, f"Μοναδικές IP: {len(stats['unique_ips'])}"); row += 1
        self.stdscr.addstr(row, 2, f"Θύρες με Επιθέσεις: {len(stats['ports_with_attacks'])}"); row += 1
        self.stdscr.addstr(row, 2, f"Πρώτη Επίθεση: {stats['first_seen']}"); row += 1
        self.stdscr.addstr(row, 2, f"Τελευταία Επίθεση: {stats['last_seen']}"); row += 1
        self.stdscr.addstr(row, 2, f"Χρόνος Λειτουργίας: {self.defender.get_uptime()}"); row += 2
        
        # Show some unique IPs
        self.stdscr.addstr(row, 2, "Πρόσφατες IP:"); row += 1
        for ip in list(stats['unique_ips'])[:10]:
            if row < height - 2:
                self.stdscr.addstr(row, 4, ip); row += 1
        
        self.stdscr.addstr(height-2, 2, "Πατήστε οποιοδήποτε πλήκτρο για επιστροφή...")
        self.stdscr.refresh()
        
        self.stdscr.nodelay(0)
        self.stdscr.getch()
        self.stdscr.nodelay(1)


class SSHDefender:
    def __init__(self):
        self.logger = SSHAttackLogger()
        self.running = False
        self.port_listeners = []
        self.active_connections = []
        self.connection_lock = threading.Lock()
        self.recent_activities = []
        self.start_time = None
        self.current_port = None
        self.attack_detected_in_cycle = False # Flag for port cycling logic
        self.in_cycle_mode = False
        self.cycle_start_time = 0
        
    def get_uptime(self):
        """Get formatted uptime"""
        if not self.start_time:
            return "0s"
        uptime = time.time() - self.start_time
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def get_random_banner(self):
        """Return a random SSH banner"""
        import random
        return random.choice(SSH_BANNERS)
    
    # simulate_ssh_handshake remains the same
    def simulate_ssh_handshake(self, client_socket):
        """Simulate parts of SSH handshake to keep attackers engaged"""
        try:
            # Send SSH banner
            banner = self.get_random_banner()
            client_socket.send(banner)
            
            # Wait for client protocol version
            data = client_socket.recv(1024)
            
            # Send some SSH key exchange init (simplified)
            if data.startswith(b"SSH-"):
                kex_init = bytes.fromhex(
                    "000001140a140a00000000000000000000000000000000"
                    "6469666669652d68656c6c6d616e2d67726f7570312d73"
                    "6861310000000f7373682d7273612c7373682d64737300"
                )
                client_socket.send(kex_init)
                
            return data, banner
            
        except socket.timeout:
            return b"", banner
        except Exception as e:
            return b"", banner
    
    def handle_connection(self, client_socket, address, port):
        """Handle individual SSH connection attempts"""
        ip, client_port = address
        
        # Track active connection
        with self.connection_lock:
            self.active_connections.append(client_socket)
        
        collected_data = b""
        
        try:
            client_socket.settimeout(10.0)
            
            # Simulate SSH handshake and collect initial data
            initial_data, banner_used = self.simulate_ssh_handshake(client_socket)
            collected_data += initial_data
            
            # Continue collecting data
            start_time = time.time()
            while time.time() - start_time < 8 and self.running:
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    collected_data += data
                    
                    if any(pattern in data.lower() for pattern in [b"root", b"admin", b"password", b"ssh"]):
                        log_path = self.logger.log_attack(ip, port, collected_data, banner_used)
                        self.attack_detected_in_cycle = True # Flag set on attack
                        activity_msg = f"🚨 {ip}:{port} -> {os.path.basename(log_path)}"
                        self.recent_activities.append(activity_msg)
                        if len(self.recent_activities) > 20:
                            self.recent_activities.pop(0)
                        
                except socket.timeout:
                    continue
                except:
                    break
            
            # Final log
            if collected_data and self.running:
                log_path = self.logger.log_attack(ip, port, collected_data, banner_used)
                self.attack_detected_in_cycle = True # Flag set on attack
                activity_msg = f"📨 {ip}:{port} -> {os.path.basename(log_path)}"
                self.recent_activities.append(activity_msg)
                if len(self.recent_activities) > 20:
                    self.recent_activities.pop(0)
                
        except Exception as e:
            if self.running:
                pass
        finally:
            with self.connection_lock:
                if client_socket in self.active_connections:
                    self.active_connections.remove(client_socket)
            client_socket.close()
    
    # empty_check_loop removed as it conflicts with 5-minute cycle logic
    
    def start_port_listener(self, port):
        """Starts listening on a single specified port."""
        self.stop_all_ports() # Ensure any previous listener is stopped
        
        listener = PortListener(port, self.logger, self)
        if listener.start():
            self.port_listeners.append(listener)
            return True
        return False
    
    def stop_all_ports(self):
        """Stop all port listeners"""
        for listener in self.port_listeners:
            listener.stop()
        
        with self.connection_lock:
            for conn in self.active_connections:
                try:
                    conn.close()
                except:
                    pass
            self.active_connections.clear()
        
        self.port_listeners.clear()
    
    def start_defender(self):
        """Start the SSH Defender with the port cycling logic"""
        self.running = True
        self.start_time = time.time()
        self.tui = CursesTUI(self)
        
        print("🎮 Έναρξη Curses TUI...")
        
        # Main port cycling loop
        for port_index, port in enumerate(FAMOUS_SSH_PORTS):
            if not self.running:
                break
                
            self.current_port = port
            self.attack_detected_in_cycle = False
            self.in_cycle_mode = True
            
            print(f"\n📢 Έναρξη ακρόασης στη θύρα {port} (Διάσημη Θύρα {port_index + 1}/{len(FAMOUS_SSH_PORTS)})")
            
            if not self.start_port_listener(port):
                continue # Skip to next port if bind failed
            
            # Start TUI loop in a thread to display the dashboard concurrently
            tui_thread = threading.Thread(target=self.tui.run, daemon=True)
            tui_thread.start()
            
            # Start timer loop (5 minutes)
            self.cycle_start_time = time.time()
            cycle_duration = 5 * 60 # 5 minutes
            
            while time.time() - self.cycle_start_time < cycle_duration and not self.attack_detected_in_cycle and self.running:
                time.sleep(1)

            # Stop the TUI and cleanup before asking for input
            self.tui.running = False
            tui_thread.join()
            
            # --- Decision Point ---
            if self.attack_detected_in_cycle:
                # Attack detected: Stay on this port and continue monitoring indefinitely
                print(f"\n\n🔥 Εντοπίστηκε επίθεση στη θύρα {port}. Συνέχιση μόνιμης παρακολούθησης...")
                self.in_cycle_mode = False
                
                # Restart the listener and TUI for permanent monitoring
                self.start_port_listener(port)
                self.tui.run() # This call will block until user quits TUI
                self.running = False
                break # Exit the cycling loop
            
            if port_index == len(FAMOUS_SSH_PORTS) - 1:
                print("\n\n✅ Ολοκληρώθηκε η παρακολούθηση όλων των διάσημων θυρών χωρίς σημαντικές επιθέσεις. Τερματισμός Αμυντήρα.")
                self.running = False
                break # Exit the cycling loop
                
            # No attack: Ask user to switch
            next_port = FAMOUS_SSH_PORTS[port_index + 1]
            user_input = input(f"\n\n⏰ Πέρασαν 5 λεπτά στη θύρα {port} χωρίς επιθέσεις.\nΘέλετε να μεταβείτε στην επόμενη διάσημη θύρα ({next_port}); (y/n ή ν/ο): ")
            
            self.stop_all_ports()
            
            if user_input.lower() not in ['y', 'ν']:
                print("\n🛑 Ο χρήστης επέλεξε να σταματήσει την εναλλαγή θυρών. Τερματισμός Αμυντήρα.")
                self.running = False
                break
            
        # Final Cleanup
        self.running = False
        self.stop_all_ports()
        self.logger.save_stats()
        print("\n✅ Ο Αμυντήρας SSH τερματίστηκε")

def main():
    print("Εκκίνηση Αμυντήρα SSH - Honeypot Θυρών...")
    defender = SSHDefender()
    defender.start_defender()

if __name__ == "__main__":
    main()