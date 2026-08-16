#!/usr/bin/env python3
import os
import sys
import time
import random
import socket
import threading
import struct
import ssl
import base64
import hashlib
import json
import urllib.parse
import ipaddress
import subprocess
import importlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Βελτιωμένα χρώματα
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class DependencyManager:
    def __init__(self):
        self.required_packages = {
            'requests': 'requests',
            'urllib3': 'urllib3',
            'websocket-client': 'websocket-client',
            'psutil': 'psutil'
        }
        self.optional_packages = {
            'numpy': 'numpy',
            'pandas': 'pandas'
        }

    def check_python_version(self):
        """Έλεγχος έκδοσης Python"""
        if sys.version_info < (3, 6):
            print(f"{Colors.RED}[!] Απαιτείται Python 3.6 ή νεότερη{Colors.RESET}")
            return False
        print(f"{Colors.GREEN}[+] Βρέθηκε Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}{Colors.RESET}")
        return True

    def is_package_installed(self, package_name):
        """Έλεγχος εγκατάστασης πακέτου"""
        try:
            importlib.import_module(package_name)
            return True
        except ImportError:
            return False

    def install_package(self, package_name, pip_name=None):
        """Εγκατάσταση πακέτου με pip"""
        if pip_name is None:
            pip_name = package_name
        
        print(f"{Colors.YELLOW}[~] Εγκατάσταση {package_name}...{Colors.RESET}")
        try:
            # Προσπάθεια εγκατάστασης με pip
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 
                '--upgrade', pip_name
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"{Colors.GREEN}[+] Επιτυχής εγκατάσταση {package_name}{Colors.RESET}")
            return True
        except subprocess.CalledProcessError:
            try:
                # Προσπάθεια χωρίς αναβάθμιση
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', pip_name
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"{Colors.GREEN}[+] Επιτυχής εγκατάσταση {package_name}{Colors.RESET}")
                return True
            except subprocess.CalledProcessError as e:
                print(f"{Colors.RED}[!] Αποτυχία εγκατάστασης {package_name}: {e}{Colors.RESET}")
                return False

    def install_all_dependencies(self):
        """Εγκατάσταση όλων των απαραίτητων εξαρτήσεων"""
        print(f"{Colors.CYAN}[*] Έλεγχος και εγκατάσταση εξαρτήσεων...{Colors.RESET}")
        
        # Έλεγχος έκδοσης Python πρώτα
        if not self.check_python_version():
            return False

        # Εγκατάσταση απαραίτητων πακέτων
        missing_required = []
        for package_name, pip_name in self.required_packages.items():
            if not self.is_package_installed(package_name):
                missing_required.append((package_name, pip_name))
        
        if missing_required:
            print(f"{Colors.YELLOW}[!] Λείπουν {len(missing_required)} απαραίτητα πακέτα{Colors.RESET}")
            for package_name, pip_name in missing_required:
                if not self.install_package(package_name, pip_name):
                    print(f"{Colors.RED}[!] Κρίσιμο πακέτο {package_name} απέτυχε να εγκατασταθεί{Colors.RESET}")
                    return False
        
        # Εγκατάσταση προαιρετικών πακέτων
        missing_optional = []
        for package_name, pip_name in self.optional_packages.items():
            if not self.is_package_installed(package_name):
                missing_optional.append((package_name, pip_name))
        
        if missing_optional:
            print(f"{Colors.YELLOW}[!] Λείπουν {len(missing_optional)} προαιρετικά πακέτα{Colors.RESET}")
            for package_name, pip_name in missing_optional:
                self.install_package(package_name, pip_name)
        
        # Επαλήθευση όλων των κρίσιμων πακέτων
        for package_name in self.required_packages.keys():
            if not self.is_package_installed(package_name):
                print(f"{Colors.RED}[!] Κρίσιμο πακέτο {package_name} ακόμα λείπει{Colors.RESET}")
                return False
        
        print(f"{Colors.GREEN}[+] Όλες οι εξαρτήσεις είναι έτοιμες!{Colors.RESET}")
        return True

    def check_system_dependencies(self):
        """Έλεγχος εξαρτήσεων συστήματος"""
        print(f"{Colors.CYAN}[*] Έλεγχος εξαρτήσεων συστήματος...{Colors.RESET}")
        
        # Έλεγχος σύνδεσης internet
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            print(f"{Colors.GREEN}[+] Σύνδεση internet: OK{Colors.RESET}")
        except OSError:
            print(f"{Colors.RED}[!] Δεν υπάρχει σύνδεση internet{Colors.RESET}")
            return False

        # Έλεγχος διαθεσιμότητας pip
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', '--version'], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"{Colors.GREEN}[+] Pip: OK{Colors.RESET}")
        except subprocess.CalledProcessError:
            print(f"{Colors.RED}[!] Το pip δεν είναι διαθέσιμο{Colors.RESET}")
            return False

        return True

def auto_install_dependencies():
    """Αυτόματη εγκατάσταση όλων των απαραίτητων εξαρτήσεων"""
    dependency_manager = DependencyManager()
    
    print(f"{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}║{Colors.MAGENTA}                  ΕΛΕΓΧΟΣ ΕΞΑΡΤΗΣΕΩΝ{Colors.CYAN}                           ║{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}╚══════════════════════════════════════════════════════════════╝{Colors.RESET}")
    
    # Έλεγχος εξαρτήσεων συστήματος πρώτα
    if not dependency_manager.check_system_dependencies():
        print(f"{Colors.RED}[!] Ο έλεγχος εξαρτήσεων συστήματος απέτυχε{Colors.RESET}")
        return False
    
    # Εγκατάσταση Python εξαρτήσεων
    if not dependency_manager.install_all_dependencies():
        print(f"{Colors.RED}[!] Αποτυχία εγκατάστασης όλων των εξαρτήσεων{Colors.RESET}")
        return False
    
    # Τελική επαλήθευση
    print(f"{Colors.CYAN}[*] Τελική επαλήθευση εξαρτήσεων...{Colors.RESET}")
    for package_name in dependency_manager.required_packages.keys():
        if dependency_manager.is_package_installed(package_name):
            print(f"{Colors.GREEN}[✓] {package_name}: OK{Colors.RESET}")
        else:
            print(f"{Colors.RED}[✗] {package_name}: ΛΕΙΠΕΙ{Colors.RESET}")
            return False
    
    print(f"{Colors.GREEN}{Colors.BOLD}[+] Όλες οι εξαρτήσεις εγκαταστάθηκαν επιτυχώς!{Colors.RESET}")
    return True

# Εισαγωγή απαιτούμενων πακέτων μετά την εξασφάλιση ότι είναι εγκατεστημένα
try:
    import requests
    from urllib3.util.retry import Retry
    from requests.adapters import HTTPAdapter
    import psutil
except ImportError as e:
    print(f"{Colors.RED}[!] Λείπει κρίσιμη εξάρτηση: {e}{Colors.RESET}")
    print(f"{Colors.YELLOW}[!] Εκτελέστε ξανά το script για αυτόματη εγκατάσταση{Colors.RESET}")
    sys.exit(1)

class AdvancedLoadTester:
    def __init__(self):
        self.config_file = "load_test_config.json"
        self.target_ip = ""
        self.target_port = 80
        self.threads = 50
        self.duration = 30
        self.packet_size = 1024
        self.rate_limit = 100  # Αιτήματα ανά δευτερόλεπτο ανά νήμα
        self.timeout = 10
        self.user_agents = self.load_user_agents()
        self.stats = {
            'requests_sent': 0,
            'requests_successful': 0,
            'requests_failed': 0,
            'total_bytes': 0,
            'start_time': None,
            'end_time': None,
            'response_times': []
        }
        self.system_stats = {
            'cpu_percent': 0,
            'memory_percent': 0,
            'network_io': (0, 0)
        }
        self.running = False
        self.load_config()

    def load_user_agents(self):
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/537.36",
        ]

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.target_ip = config.get('target_ip', '')
                    self.target_port = config.get('target_port', 80)
                    self.threads = config.get('threads', 50)
                    self.duration = config.get('duration', 30)
        except:
            pass

    def save_config(self):
        config = {
            'target_ip': self.target_ip,
            'target_port': self.target_port,
            'threads': self.threads,
            'duration': self.duration
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except:
            pass

    def get_system_stats(self):
        """Λήψη στατιστικών συστήματος"""
        try:
            self.system_stats['cpu_percent'] = psutil.cpu_percent(interval=0.1)
            self.system_stats['memory_percent'] = psutil.virtual_memory().percent
            net_io = psutil.net_io_counters()
            self.system_stats['network_io'] = (net_io.bytes_sent, net_io.bytes_recv)
        except:
            pass

    def create_http_session(self):
        """Δημιουργία βελτιστοποιημένης HTTP session με connection pooling"""
        session = requests.Session()
        
        # Ρύθμιση στρατηγικής επανάληψης
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # Ρύθμιση adapter με connection pooling
        adapter = HTTPAdapter(
            pool_connections=100,
            pool_maxsize=100,
            max_retries=retry_strategy
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Προεπιλεγμένα headers
        session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
        })
        
        return session

    def realistic_http_flood(self, target_ip, target_port, duration):
        """Προχωρημένο HTTP load test με ρεαλιστικά μοτίβα"""
        end_time = time.time() + duration
        session = self.create_http_session()
        scheme = "https" if target_port == 443 else "http"
        base_url = f"{scheme}://{target_ip}:{target_port}"
        
        # Ρεαλιστικά endpoints για ιστοσελίδα
        endpoints = [
            '/', '/home', '/index.html', '/about', '/contact',
            '/products', '/services', '/blog', '/api/health',
            '/static/css/main.css', '/static/js/app.js',
            '/images/logo.png', '/api/v1/users', '/api/v1/products'
        ]
        
        # Ρεαλιστικά μοτίβα αιτημάτων
        request_patterns = [
            {'method': 'GET', 'endpoint': random.choice(endpoints)},
            {'method': 'POST', 'endpoint': '/api/v1/login', 'data': {'username': 'test', 'password': 'test'}},
            {'method': 'GET', 'endpoint': '/api/v1/products'},
            {'method': 'HEAD', 'endpoint': random.choice(endpoints)},
        ]
        
        while time.time() < end_time and self.running:
            try:
                pattern = random.choice(request_patterns)
                url = f"{base_url}{pattern['endpoint']}"
                
                start_time = time.time()
                
                if pattern['method'] == 'GET':
                    response = session.get(url, timeout=self.timeout)
                elif pattern['method'] == 'POST':
                    response = session.post(url, json=pattern.get('data', {}), timeout=self.timeout)
                elif pattern['method'] == 'HEAD':
                    response = session.head(url, timeout=self.timeout)
                
                response_time = (time.time() - start_time) * 1000  # Μετατροπή σε χιλιοστά δευτερολέπτου
                
                self.stats['requests_sent'] += 1
                self.stats['total_bytes'] += len(response.content) if hasattr(response, 'content') else 0
                self.stats['response_times'].append(response_time)
                
                if 200 <= response.status_code < 400:
                    self.stats['requests_successful'] += 1
                else:
                    self.stats['requests_failed'] += 1
                
                # Προσαρμοστικός περιορισμός ρυθμού βάσει απόκρισης
                if response.status_code == 429:  # Πάρα πολλά αιτήματα
                    time.sleep(1)
                elif response.status_code >= 500:
                    time.sleep(0.1)
                
            except requests.exceptions.RequestException as e:
                self.stats['requests_failed'] += 1
                self.stats['requests_sent'] += 1
            except Exception as e:
                self.stats['requests_failed'] += 1
                self.stats['requests_sent'] += 1
            
            # Περιορισμός ρυθμού
            time.sleep(1.0 / self.rate_limit)

    def websocket_load_test(self, target_ip, target_port, duration):
        """Δοκιμή φόρτωσης WebSocket"""
        end_time = time.time() + duration
        
        # Έλεγχος διαθεσιμότητας websocket-client
        try:
            import websocket
        except ImportError:
            print(f"{Colors.RED}[!] Το websocket-client δεν είναι διαθέσιμο. Εγκατάσταση...{Colors.RESET}")
            dependency_manager = DependencyManager()
            if not dependency_manager.install_package('websocket-client'):
                print(f"{Colors.RED}[!] Αποτυχία εγκατάστασης websocket-client{Colors.RESET}")
                return
            import websocket

        scheme = "wss" if target_port == 443 else "ws"
        ws_url = f"{scheme}://{target_ip}:{target_port}/ws"
        
        while time.time() < end_time and self.running:
            try:
                ws = websocket.create_connection(ws_url, timeout=self.timeout)
                
                # Αποστολή μηνυμάτων δοκιμής
                for i in range(10):
                    if time.time() > end_time:
                        break
                    message = json.dumps({"type": "ping", "data": f"test_{i}"})
                    ws.send(message)
                    self.stats['requests_sent'] += 1
                    self.stats['requests_successful'] += 1
                    time.sleep(0.1)
                
                ws.close()
                
            except Exception as e:
                self.stats['requests_failed'] += 1
                self.stats['requests_sent'] += 1

    def database_query_simulation(self, target_ip, target_port, duration):
        """Προσομοίωση εργασιών με βάση δεδομένων"""
        end_time = time.time() + duration
        session = self.create_http_session()
        scheme = "https" if target_port == 443 else "http"
        base_url = f"{scheme}://{target_ip}:{target_port}"
        
        # Endpoints που απαιτούν βάση δεδομένων (συνηθισμένα σε web apps)
        db_endpoints = [
            '/api/v1/users/search?q=test',
            '/api/v1/products/filter?category=all&page=1',
            '/api/v1/orders/history?userId=123',
            '/api/v1/reports/dashboard',
            '/api/v1/analytics/visitors'
        ]
        
        while time.time() < end_time and self.running:
            try:
                endpoint = random.choice(db_endpoints)
                url = f"{base_url}{endpoint}"
                
                start_time = time.time()
                response = session.get(url, timeout=self.timeout)
                response_time = (time.time() - start_time) * 1000
                
                self.stats['requests_sent'] += 1
                self.stats['total_bytes'] += len(response.content)
                self.stats['response_times'].append(response_time)
                
                if 200 <= response.status_code < 400:
                    self.stats['requests_successful'] += 1
                else:
                    self.stats['requests_failed'] += 1
                
            except Exception as e:
                self.stats['requests_failed'] += 1
                self.stats['requests_sent'] += 1
            
            time.sleep(1.0 / self.rate_limit)

    def file_upload_simulation(self, target_ip, target_port, duration):
        """Προσομοίωση αποστολής αρχείων"""
        end_time = time.time() + duration
        session = self.create_http_session()
        scheme = "https" if target_port == 443 else "http"
        base_url = f"{scheme}://{target_ip}:{target_port}"
        
        while time.time() < end_time and self.running:
            try:
                # Δημιουργία τυχαίων δεδομένων αρχείου
                file_size = random.randint(1024, 10240)  # 1KB έως 10KB
                file_data = os.urandom(file_size)
                files = {'file': ('test_file.jpg', file_data, 'image/jpeg')}
                
                start_time = time.time()
                response = session.post(f"{base_url}/api/v1/upload", files=files, timeout=self.timeout)
                response_time = (time.time() - start_time) * 1000
                
                self.stats['requests_sent'] += 1
                self.stats['total_bytes'] += file_size
                self.stats['response_times'].append(response_time)
                
                if 200 <= response.status_code < 400:
                    self.stats['requests_successful'] += 1
                else:
                    self.stats['requests_failed'] += 1
                
            except Exception as e:
                self.stats['requests_failed'] += 1
                self.stats['requests_sent'] += 1
            
            time.sleep(2.0 / self.rate_limit)  # Πιο αργός ρυθμός για αποστολές

    def mixed_workload_test(self, target_ip, target_port, duration):
        """Συνδυασμένο φόρτο εργασίας που προσομοιώνει πραγματική συμπεριφορά χρήστη"""
        end_time = time.time() + duration
        session = self.create_http_session()
        scheme = "https" if target_port == 443 else "http"
        base_url = f"{scheme}://{target_ip}:{target_port}"
        
        workload_patterns = [
            # Πλοήγηση σελίδων
            lambda: session.get(f"{base_url}{random.choice(['/', '/home', '/about'])}", timeout=self.timeout),
            # Κλήσεις API
            lambda: session.get(f"{base_url}/api/v1/{random.choice(['products', 'users', 'stats'])}", timeout=self.timeout),
            # Αναζητήσεις
            lambda: session.get(f"{base_url}/search?q={random.choice(['test', 'product', 'user'])}", timeout=self.timeout),
        ]
        
        while time.time() < end_time and self.running:
            try:
                pattern = random.choice(workload_patterns)
                
                start_time = time.time()
                response = pattern()
                response_time = (time.time() - start_time) * 1000
                
                self.stats['requests_sent'] += 1
                self.stats['total_bytes'] += len(response.content) if hasattr(response, 'content') else 0
                self.stats['response_times'].append(response_time)
                
                if 200 <= response.status_code < 400:
                    self.stats['requests_successful'] += 1
                else:
                    self.stats['requests_failed'] += 1
                
                # Ρεαλιστικός χρόνος σκέψης χρήστη
                time.sleep(random.uniform(0.5, 3.0))
                
            except Exception as e:
                self.stats['requests_failed'] += 1
                self.stats['requests_sent'] += 1
                time.sleep(1)

    def start_load_test(self, test_type):
        """Εκκίνηση ολοκληρωμένης δοκιμής φόρτωσης"""
        if not self.target_ip:
            print(f"{Colors.RED}[!] Παρακαλώ ρυθμίστε πρώτα τον στόχο!{Colors.RESET}")
            return False

        print(f"{Colors.GREEN}[+] Εκκίνηση {test_type} δοκιμής φόρτωσης στο {self.target_ip}:{self.target_port}{Colors.RESET}")
        print(f"{Colors.YELLOW}[!] Διάρκεια: {self.duration}s | Νήματα: {self.threads} | Ρυθμός: {self.rate_limit} αίτημα/s/νήμα{Colors.RESET}")
        
        # Επαναφορά στατιστικών
        self.stats = {
            'requests_sent': 0,
            'requests_successful': 0,
            'requests_failed': 0,
            'total_bytes': 0,
            'start_time': datetime.now(),
            'end_time': None,
            'response_times': []
        }
        
        self.running = True
        
        test_methods = {
            "HTTP Load": self.realistic_http_flood,
            "WebSocket Load": self.websocket_load_test,
            "Database Simulation": self.database_query_simulation,
            "File Upload": self.file_upload_simulation,
            "Mixed Workload": self.mixed_workload_test,
        }
        
        test_func = test_methods.get(test_type)
        if not test_func:
            print(f"{Colors.RED}[!] Άγνωστος τύπος δοκιμής!{Colors.RESET}")
            return False
        
        # Εκκίνηση νήματος παρακολούθησης συστήματος
        system_thread = threading.Thread(target=self.system_monitor)
        system_thread.daemon = True
        system_thread.start()
        
        # Εκκίνηση νημάτων δοκιμής
        threads = []
        for i in range(self.threads):
            thread = threading.Thread(
                target=test_func,
                args=(self.target_ip, self.target_port, self.duration)
            )
            thread.daemon = True
            threads.append(thread)
            thread.start()
        
        # Παρακολούθηση προόδου
        self.monitor_test()
        
        return True

    def system_monitor(self):
        """Παρακολούθηση πόρων συστήματος κατά τη δοκιμή"""
        while self.running:
            self.get_system_stats()
            time.sleep(2)

    def monitor_test(self):
        """Παρακολούθηση προόδου δοκιμής με λεπτομερή μετρικά"""
        start_time = time.time()
        last_requests = 0
        last_bytes = 0
        
        try:
            while time.time() - start_time < self.duration and self.running:
                elapsed = int(time.time() - start_time)
                remaining = self.duration - elapsed
                
                current_requests = self.stats['requests_sent']
                current_bytes = self.stats['total_bytes']
                
                rps = current_requests - last_requests
                bps = (current_bytes - last_bytes) * 8
                mbps = bps / 1000000
                
                last_requests = current_requests
                last_bytes = current_bytes
                
                success_rate = (self.stats['requests_successful'] / max(self.stats['requests_sent'], 1)) * 100
                
                # Υπολογισμός ποσοστημορίων χρόνου απόκρισης
                if self.stats['response_times']:
                    avg_response = sum(self.stats['response_times']) / len(self.stats['response_times'])
                    sorted_times = sorted(self.stats['response_times'])
                    p95 = sorted_times[int(len(sorted_times) * 0.95)]
                else:
                    avg_response = p95 = 0
                
                print(f"{Colors.CYAN}[~] {elapsed}s/{self.duration}s | "
                      f"Αιτ: {current_requests} | RPS: {rps}/s | "
                      f"Επιτυχία: {success_rate:.1f}% | "
                      f"Μέσος ΧΡ: {avg_response:.1f}ms | P95: {p95:.1f}ms | "
                      f"Εύρος: {mbps:.2f} Mbps | "
                      f"CPU: {self.system_stats['cpu_percent']:.1f}% | "
                      f"RAM: {self.system_stats['memory_percent']:.1f}%{Colors.RESET}", end='\r')
                
                time.sleep(1)
        
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}[!] Δοκιμή διακόπηκε από χρήστη{Colors.RESET}")
        
        self.stats['end_time'] = datetime.now()
        self.running = False
        self.show_test_summary()

    def show_test_summary(self):
        """Εμφάνιση ολοκληρωμένων αποτελεσμάτων δοκιμής"""
        if not self.stats['start_time'] or not self.stats['end_time']:
            return
            
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        total_requests = self.stats['requests_sent']
        success_rate = (self.stats['requests_successful'] / max(total_requests, 1)) * 100
        
        if self.stats['response_times']:
            avg_response = sum(self.stats['response_times']) / len(self.stats['response_times'])
            sorted_times = sorted(self.stats['response_times'])
            p50 = sorted_times[int(len(sorted_times) * 0.50)]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
        else:
            avg_response = p50 = p95 = p99 = 0
        
        rps = total_requests / duration if duration > 0 else 0
        bandwidth_mbps = (self.stats['total_bytes'] * 8) / duration / 1000000 if duration > 0 else 0
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}[+] ΠΕΡΙΛΗΨΗ ΔΟΚΙΜΗΣ ΦΟΡΤΩΣΗΣ{Colors.RESET}")
        print(f"{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗")
        print(f"║ {Colors.WHITE}Στόχος: {self.target_ip}:{self.target_port}{Colors.CYAN}{' ' * (50 - len(f'{self.target_ip}:{self.target_port}'))}║")
        print(f"║ {Colors.WHITE}Διάρκεια: {duration:.2f} δευτερόλεπτα{' ' * 40}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}Σύνολο Αιτημάτων: {total_requests}{' ' * 42}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}Επιτυχημένα: {self.stats['requests_successful']} ({success_rate:.1f}%){' ' * 35}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}Αποτυχημένα: {self.stats['requests_failed']}{' ' * 46}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}Αιτήματα/Δευτερόλεπτο: {rps:.2f}{' ' * 41}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}Εύρος Ζώνης: {bandwidth_mbps:.2f} Mbps{' ' * 37}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}Μέσος Χρόνος Απόκρισης: {avg_response:.1f}ms{' ' * 37}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}P50 Χρόνος Απόκρισης: {p50:.1f}ms{' ' * 38}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}P95 Χρόνος Απόκρισης: {p95:.1f}ms{' ' * 38}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}P99 Χρόνος Απόκρισης: {p99:.1f}ms{' ' * 38}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}Μέγιστη Χρήση CPU: {self.system_stats['cpu_percent']:.1f}%{' ' * 38}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}Μέγιστη Χρήση RAM: {self.system_stats['memory_percent']:.1f}%{' ' * 37}{Colors.CYAN}║")
        print(f"╚══════════════════════════════════════════════════════════════╝{Colors.RESET}")

def print_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}║{Colors.MAGENTA}               ΠΡΟΧΩΡΗΜΕΝΟ ΣΥΣΤΗΜΑ ΔΟΚΙΜΗΣ ΦΟΡΤΩΣΗΣ{Colors.CYAN}          ║{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}║{Colors.YELLOW}           Με Αυτόματη Εγκατάσταση Εξαρτήσεων{Colors.CYAN}               ║{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}║{Colors.GREEN}           Ρεαλιστικοί Φόρτοι | Μετρικές Απόδοσης{Colors.CYAN}            ║{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}╚══════════════════════════════════════════════════════════════╝{Colors.RESET}")
    print()

def get_input(prompt, default="", input_type=str):
    try:
        user_input = input(f"{Colors.CYAN}[?] {prompt} [{default}]: {Colors.RESET}").strip()
        if not user_input:
            return default
        return input_type(user_input)
    except ValueError:
        print(f"{Colors.RED}[!] Μη έγκυρη εισαγωγή, χρήση προεπιλογής: {default}{Colors.RESET}")
        return default

def main():
    # Αυτόματη εγκατάσταση εξαρτήσεων στην πρώτη εκτέλεση
    try:
        import requests
        import urllib3
        import psutil
        print(f"{Colors.GREEN}[+] Όλες οι εξαρτήσεις είναι ήδη εγκατεστημένες{Colors.RESET}")
    except ImportError:
        print(f"{Colors.YELLOW}[!] Λείπουν κάποιες εξαρτήσεις{Colors.RESET}")
        if not auto_install_dependencies():
            print(f"{Colors.RED}[!] Αποτυχία εγκατάστασης εξαρτήσεων. Έξοδος.{Colors.RESET}")
            sys.exit(1)
    
    print_banner()
    tester = AdvancedLoadTester()
    
    while True:
        print(f"\n{Colors.MAGENTA}{Colors.BOLD}=== ΠΡΟΧΩΡΗΜΕΝΟ ΣΥΣΤΗΜΑ ΔΟΚΙΜΗΣ ΦΟΡΤΩΣΗΣ ==={Colors.RESET}")
        print(f"{Colors.GREEN}1.  Ρύθμιση Στόχου")
        print(f"2.  Δοκιμή Φόρτωσης HTTP")
        print(f"3.  Δοκιμή Φόρτωσης WebSocket")
        print(f"4.  Προσομοίωση Ερωτήματος Βάσης Δεδομένων")
        print(f"5.  Προσομοίωση Αποστολής Αρχείου")
        print(f"6.  Δοκιμή Μικτού Φόρτου")
        print(f"7.  Ορισμός Περιορισμού Ρυθμού")
        print(f"8.  Εμφάνιση Ρυθμίσεων")
        print(f"9.  Αποθήκευση Ρυθμίσεων")
        print(f"10. Εγκατάσταση/Ενημέρωση Εξαρτήσεων")
        print(f"11. Έξοδος{Colors.RESET}")
        
        choice = input(f"\n{Colors.CYAN}[?] Επιλογή: {Colors.RESET}").strip()
        
        if choice == "1":
            print(f"\n{Colors.YELLOW}[!] Ρύθμιση Παραμέτρων Δοκιμής{Colors.RESET}")
            tester.target_ip = get_input("IP/Όνομα Στόχου", tester.target_ip)
            tester.target_port = get_input("Θύρα Στόχου", tester.target_port, int)
            tester.threads = get_input("Νήματα", tester.threads, int)
            tester.duration = get_input("Διάρκεια (δευτερόλεπτα)", tester.duration, int)
            tester.rate_limit = get_input("Αιτήματα ανά δευτερόλεπτο ανά νήμα", tester.rate_limit, int)
            
        elif choice in ["2", "3", "4", "5", "6"]:
            if not tester.target_ip:
                print(f"{Colors.RED}[!] Παρακαλώ ρυθμίστε πρώτα τον στόχο!{Colors.RESET}")
                continue
            
            test_types = {
                "2": "HTTP Load",
                "3": "WebSocket Load",
                "4": "Database Simulation",
                "5": "File Upload",
                "6": "Mixed Workload"
            }
            
            test_type = test_types[choice]
            
            print(f"{Colors.YELLOW}[!] Εκκίνηση {test_type} δοκιμής στο ΔΙΚΟ ΣΑΣ ΙΣΤΟΤΟΠΟ{Colors.RESET}")
            print(f"{Colors.YELLOW}[!] Βεβαιωθείτε ότι έχετε άδεια να δοκιμάσετε αυτόν τον στόχο{Colors.RESET}")
            
            confirm = input(f"{Colors.YELLOW}[!] Εκκίνηση {test_type} δοκιμής; (y/N): {Colors.RESET}").strip().lower()
            if confirm == 'y':
                tester.start_load_test(test_type)
            else:
                print(f"{Colors.RED}[!] Η δοκιμή ακυρώθηκε{Colors.RESET}")
            
        elif choice == "7":
            tester.rate_limit = get_input("Αιτήματα ανά δευτερόλεπτο ανά νήμα", tester.rate_limit, int)
            print(f"{Colors.GREEN}[+] Ο περιορισμός ρυθμού ορίστηκε σε {tester.rate_limit} αίτημα/s/νήμα{Colors.RESET}")
            
        elif choice == "8":
            print(f"\n{Colors.YELLOW}[!] Τρέχουσες Ρυθμίσεις:{Colors.RESET}")
            print(f"Στόχος: {tester.target_ip}:{tester.target_port}")
            print(f"Νήματα: {tester.threads}")
            print(f"Διάρκεια: {tester.duration}s")
            print(f"Περιορισμός Ρυθμού: {tester.rate_limit} αίτημα/s/νήμα")
            print(f"Χρονικό Όριο: {tester.timeout}s")
            
        elif choice == "9":
            tester.save_config()
            print(f"{Colors.GREEN}[+] Οι ρυθμίσεις αποθηκεύτηκαν!{Colors.RESET}")
            
        elif choice == "10":
            print(f"{Colors.YELLOW}[!] Εγκατάσταση/ενημέρωση εξαρτήσεων...{Colors.RESET}")
            if auto_install_dependencies():
                print(f"{Colors.GREEN}[+] Οι εξαρτήσεις ενημερώθηκαν επιτυχώς!{Colors.RESET}")
            else:
                print(f"{Colors.RED}[!] Αποτυχία ενημέρωσης εξαρτήσεων{Colors.RESET}")
            
        elif choice == "11":
            print(f"{Colors.GREEN}[+] Αντίο!{Colors.RESET}")
            break
            
        else:
            print(f"{Colors.RED}[!] Μη έγκυρη επιλογή!{Colors.RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}[!] Διακόπηκε από χρήστη{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}[!] Σφάλμα: {e}{Colors.RESET}")