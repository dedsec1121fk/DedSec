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

# Enhanced colors
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
        """Check if Python version is sufficient"""
        if sys.version_info < (3, 6):
            print(f"{Colors.RED}[!] Python 3.6 or higher is required{Colors.RESET}")
            return False
        print(f"{Colors.GREEN}[+] Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detected{Colors.RESET}")
        return True

    def is_package_installed(self, package_name):
        """Check if a package is installed"""
        try:
            importlib.import_module(package_name)
            return True
        except ImportError:
            return False

    def install_package(self, package_name, pip_name=None):
        """Install a package using pip"""
        if pip_name is None:
            pip_name = package_name
        
        print(f"{Colors.YELLOW}[~] Installing {package_name}...{Colors.RESET}")
        try:
            # Try using pip with current Python interpreter
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 
                '--upgrade', pip_name
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"{Colors.GREEN}[+] Successfully installed {package_name}{Colors.RESET}")
            return True
        except subprocess.CalledProcessError:
            try:
                # Try without upgrade flag
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', pip_name
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"{Colors.GREEN}[+] Successfully installed {package_name}{Colors.RESET}")
                return True
            except subprocess.CalledProcessError as e:
                print(f"{Colors.RED}[!] Failed to install {package_name}: {e}{Colors.RESET}")
                return False

    def install_all_dependencies(self):
        """Install all required dependencies"""
        print(f"{Colors.CYAN}[*] Checking and installing dependencies...{Colors.RESET}")
        
        # Check Python version first
        if not self.check_python_version():
            return False

        # Install required packages
        missing_required = []
        for package_name, pip_name in self.required_packages.items():
            if not self.is_package_installed(package_name):
                missing_required.append((package_name, pip_name))
        
        if missing_required:
            print(f"{Colors.YELLOW}[!] Missing {len(missing_required)} required packages{Colors.RESET}")
            for package_name, pip_name in missing_required:
                if not self.install_package(package_name, pip_name):
                    print(f"{Colors.RED}[!] Critical dependency {package_name} failed to install{Colors.RESET}")
                    return False
        
        # Install optional packages
        missing_optional = []
        for package_name, pip_name in self.optional_packages.items():
            if not self.is_package_installed(package_name):
                missing_optional.append((package_name, pip_name))
        
        if missing_optional:
            print(f"{Colors.YELLOW}[!] Missing {len(missing_optional)} optional packages{Colors.RESET}")
            for package_name, pip_name in missing_optional:
                self.install_package(package_name, pip_name)
        
        # Verify all critical packages are installed
        for package_name in self.required_packages.keys():
            if not self.is_package_installed(package_name):
                print(f"{Colors.RED}[!] Critical package {package_name} is still missing{Colors.RESET}")
                return False
        
        print(f"{Colors.GREEN}[+] All dependencies are ready!{Colors.RESET}")
        return True

    def check_system_dependencies(self):
        """Check system-level dependencies"""
        print(f"{Colors.CYAN}[*] Checking system dependencies...{Colors.RESET}")
        
        # Check for internet connectivity
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            print(f"{Colors.GREEN}[+] Internet connectivity: OK{Colors.RESET}")
        except OSError:
            print(f"{Colors.RED}[!] No internet connectivity{Colors.RESET}")
            return False

        # Check pip availability
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', '--version'], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"{Colors.GREEN}[+] Pip: OK{Colors.RESET}")
        except subprocess.CalledProcessError:
            print(f"{Colors.RED}[!] Pip is not available{Colors.RESET}")
            return False

        return True

def auto_install_dependencies():
    """Automatically install all required dependencies"""
    dependency_manager = DependencyManager()
    
    print(f"{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}║{Colors.MAGENTA}                  DEPENDENCY CHECK{Colors.CYAN}                           ║{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}╚══════════════════════════════════════════════════════════════╝{Colors.RESET}")
    
    # Check system dependencies first
    if not dependency_manager.check_system_dependencies():
        print(f"{Colors.RED}[!] System dependencies check failed{Colors.RESET}")
        return False
    
    # Install Python dependencies
    if not dependency_manager.install_all_dependencies():
        print(f"{Colors.RED}[!] Failed to install all dependencies{Colors.RESET}")
        return False
    
    # Final verification
    print(f"{Colors.CYAN}[*] Final dependency verification...{Colors.RESET}")
    for package_name in dependency_manager.required_packages.keys():
        if dependency_manager.is_package_installed(package_name):
            print(f"{Colors.GREEN}[✓] {package_name}: OK{Colors.RESET}")
        else:
            print(f"{Colors.RED}[✗] {package_name}: MISSING{Colors.RESET}")
            return False
    
    print(f"{Colors.GREEN}{Colors.BOLD}[+] All dependencies installed successfully!{Colors.RESET}")
    return True

# Now import the required packages after ensuring they're installed
try:
    import requests
    from urllib3.util.retry import Retry
    from requests.adapters import HTTPAdapter
    import psutil
except ImportError as e:
    print(f"{Colors.RED}[!] Missing critical dependency: {e}{Colors.RESET}")
    print(f"{Colors.YELLOW}[!] Run the script again to auto-install dependencies{Colors.RESET}")
    sys.exit(1)

class AdvancedLoadTester:
    def __init__(self):
        self.config_file = "load_test_config.json"
        self.target_ip = ""
        self.target_port = 80
        self.threads = 50
        self.duration = 30
        self.packet_size = 1024
        self.rate_limit = 100  # Requests per second per thread
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
        """Get current system statistics"""
        try:
            self.system_stats['cpu_percent'] = psutil.cpu_percent(interval=0.1)
            self.system_stats['memory_percent'] = psutil.virtual_memory().percent
            net_io = psutil.net_io_counters()
            self.system_stats['network_io'] = (net_io.bytes_sent, net_io.bytes_recv)
        except:
            pass

    def create_http_session(self):
        """Create optimized HTTP session with connection pooling"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # Configure adapter with connection pooling
        adapter = HTTPAdapter(
            pool_connections=100,
            pool_maxsize=100,
            max_retries=retry_strategy
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
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
        """Advanced HTTP load test with realistic patterns"""
        end_time = time.time() + duration
        session = self.create_http_session()
        scheme = "https" if target_port == 443 else "http"
        base_url = f"{scheme}://{target_ip}:{target_port}"
        
        # Realistic endpoints for a website
        endpoints = [
            '/', '/home', '/index.html', '/about', '/contact',
            '/products', '/services', '/blog', '/api/health',
            '/static/css/main.css', '/static/js/app.js',
            '/images/logo.png', '/api/v1/users', '/api/v1/products'
        ]
        
        # Realistic request patterns
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
                
                response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                self.stats['requests_sent'] += 1
                self.stats['total_bytes'] += len(response.content) if hasattr(response, 'content') else 0
                self.stats['response_times'].append(response_time)
                
                if 200 <= response.status_code < 400:
                    self.stats['requests_successful'] += 1
                else:
                    self.stats['requests_failed'] += 1
                
                # Adaptive rate limiting based on response
                if response.status_code == 429:  # Too Many Requests
                    time.sleep(1)
                elif response.status_code >= 500:
                    time.sleep(0.1)
                
            except requests.exceptions.RequestException as e:
                self.stats['requests_failed'] += 1
                self.stats['requests_sent'] += 1
            except Exception as e:
                self.stats['requests_failed'] += 1
                self.stats['requests_sent'] += 1
            
            # Rate limiting
            time.sleep(1.0 / self.rate_limit)

    def websocket_load_test(self, target_ip, target_port, duration):
        """WebSocket connection load test"""
        end_time = time.time() + duration
        
        # Check if websocket-client is available
        try:
            import websocket
        except ImportError:
            print(f"{Colors.RED}[!] websocket-client not available. Installing...{Colors.RESET}")
            dependency_manager = DependencyManager()
            if not dependency_manager.install_package('websocket-client'):
                print(f"{Colors.RED}[!] Failed to install websocket-client{Colors.RESET}")
                return
            import websocket

        scheme = "wss" if target_port == 443 else "ws"
        ws_url = f"{scheme}://{target_ip}:{target_port}/ws"
        
        while time.time() < end_time and self.running:
            try:
                ws = websocket.create_connection(ws_url, timeout=self.timeout)
                
                # Send test messages
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
        """Simulate database-intensive operations"""
        end_time = time.time() + duration
        session = self.create_http_session()
        scheme = "https" if target_port == 443 else "http"
        base_url = f"{scheme}://{target_ip}:{target_port}"
        
        # Database-intensive endpoints (common in web apps)
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
        """Simulate file upload operations"""
        end_time = time.time() + duration
        session = self.create_http_session()
        scheme = "https" if target_port == 443 else "http"
        base_url = f"{scheme}://{target_ip}:{target_port}"
        
        while time.time() < end_time and self.running:
            try:
                # Generate random file data
                file_size = random.randint(1024, 10240)  # 1KB to 10KB
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
            
            time.sleep(2.0 / self.rate_limit)  # Slower rate for uploads

    def mixed_workload_test(self, target_ip, target_port, duration):
        """Combined workload simulating real user behavior"""
        end_time = time.time() + duration
        session = self.create_http_session()
        scheme = "https" if target_port == 443 else "http"
        base_url = f"{scheme}://{target_ip}:{target_port}"
        
        workload_patterns = [
            # Browse pages
            lambda: session.get(f"{base_url}{random.choice(['/', '/home', '/about'])}", timeout=self.timeout),
            # API calls
            lambda: session.get(f"{base_url}/api/v1/{random.choice(['products', 'users', 'stats'])}", timeout=self.timeout),
            # Search queries
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
                
                # Realistic user think time
                time.sleep(random.uniform(0.5, 3.0))
                
            except Exception as e:
                self.stats['requests_failed'] += 1
                self.stats['requests_sent'] += 1
                time.sleep(1)

    def start_load_test(self, test_type):
        """Start comprehensive load testing"""
        if not self.target_ip:
            print(f"{Colors.RED}[!] Please configure target first!{Colors.RESET}")
            return False

        print(f"{Colors.GREEN}[+] Starting {test_type} load test on {self.target_ip}:{self.target_port}{Colors.RESET}")
        print(f"{Colors.YELLOW}[!] Duration: {self.duration}s | Threads: {self.threads} | Rate: {self.rate_limit} req/s/thread{Colors.RESET}")
        
        # Reset stats
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
            print(f"{Colors.RED}[!] Unknown test type!{Colors.RESET}")
            return False
        
        # Start system monitoring thread
        system_thread = threading.Thread(target=self.system_monitor)
        system_thread.daemon = True
        system_thread.start()
        
        # Start test threads
        threads = []
        for i in range(self.threads):
            thread = threading.Thread(
                target=test_func,
                args=(self.target_ip, self.target_port, self.duration)
            )
            thread.daemon = True
            threads.append(thread)
            thread.start()
        
        # Monitor progress
        self.monitor_test()
        
        return True

    def system_monitor(self):
        """Monitor system resources during test"""
        while self.running:
            self.get_system_stats()
            time.sleep(2)

    def monitor_test(self):
        """Monitor test progress with detailed metrics"""
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
                
                # Calculate response time percentiles
                if self.stats['response_times']:
                    avg_response = sum(self.stats['response_times']) / len(self.stats['response_times'])
                    sorted_times = sorted(self.stats['response_times'])
                    p95 = sorted_times[int(len(sorted_times) * 0.95)]
                else:
                    avg_response = p95 = 0
                
                print(f"{Colors.CYAN}[~] {elapsed}s/{self.duration}s | "
                      f"Reqs: {current_requests} | RPS: {rps}/s | "
                      f"Success: {success_rate:.1f}% | "
                      f"Avg RT: {avg_response:.1f}ms | P95: {p95:.1f}ms | "
                      f"BW: {mbps:.2f} Mbps | "
                      f"CPU: {self.system_stats['cpu_percent']:.1f}% | "
                      f"RAM: {self.system_stats['memory_percent']:.1f}%{Colors.RESET}", end='\r')
                
                time.sleep(1)
        
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}[!] Test interrupted by user{Colors.RESET}")
        
        self.stats['end_time'] = datetime.now()
        self.running = False
        self.show_test_summary()

    def show_test_summary(self):
        """Display comprehensive test results"""
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
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}[+] LOAD TEST SUMMARY{Colors.RESET}")
        print(f"{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗")
        print(f"║ {Colors.WHITE}Target: {self.target_ip}:{self.target_port}{Colors.CYAN}{' ' * (50 - len(f'{self.target_ip}:{self.target_port}'))}║")
        print(f"║ {Colors.WHITE}Duration: {duration:.2f} seconds{' ' * 40}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}Total Requests: {total_requests}{' ' * 42}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}Successful: {self.stats['requests_successful']} ({success_rate:.1f}%){' ' * 35}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}Failed: {self.stats['requests_failed']}{' ' * 46}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}Requests/Second: {rps:.2f}{' ' * 41}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}Bandwidth: {bandwidth_mbps:.2f} Mbps{' ' * 37}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}Avg Response Time: {avg_response:.1f}ms{' ' * 37}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}P50 Response Time: {p50:.1f}ms{' ' * 38}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}P95 Response Time: {p95:.1f}ms{' ' * 38}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}P99 Response Time: {p99:.1f}ms{' ' * 38}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}Peak CPU Usage: {self.system_stats['cpu_percent']:.1f}%{' ' * 38}{Colors.CYAN}║")
        print(f"║ {Colors.WHITE}Peak RAM Usage: {self.system_stats['memory_percent']:.1f}%{' ' * 37}{Colors.CYAN}║")
        print(f"╚══════════════════════════════════════════════════════════════╝{Colors.RESET}")

def print_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}║{Colors.MAGENTA}               ADVANCED LOAD TESTING FRAMEWORK{Colors.CYAN}               ║{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}║{Colors.YELLOW}           With Auto-Dependency Installation{Colors.CYAN}                ║{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}║{Colors.GREEN}           Realistic Workloads | Performance Metrics{Colors.CYAN}         ║{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}╚══════════════════════════════════════════════════════════════╝{Colors.RESET}")
    print()

def get_input(prompt, default="", input_type=str):
    try:
        user_input = input(f"{Colors.CYAN}[?] {prompt} [{default}]: {Colors.RESET}").strip()
        if not user_input:
            return default
        return input_type(user_input)
    except ValueError:
        print(f"{Colors.RED}[!] Invalid input, using default: {default}{Colors.RESET}")
        return default

def main():
    # Auto-install dependencies on first run
    try:
        import requests
        import urllib3
        import psutil
        print(f"{Colors.GREEN}[+] All dependencies are already installed{Colors.RESET}")
    except ImportError:
        print(f"{Colors.YELLOW}[!] Some dependencies are missing{Colors.RESET}")
        if not auto_install_dependencies():
            print(f"{Colors.RED}[!] Failed to install dependencies. Exiting.{Colors.RESET}")
            sys.exit(1)
    
    print_banner()
    tester = AdvancedLoadTester()
    
    while True:
        print(f"\n{Colors.MAGENTA}{Colors.BOLD}=== ADVANCED LOAD TESTING FRAMEWORK ==={Colors.RESET}")
        print(f"{Colors.GREEN}1.  Configure Target")
        print(f"2.  HTTP Load Test")
        print(f"3.  WebSocket Load Test")
        print(f"4.  Database Query Simulation")
        print(f"5.  File Upload Simulation")
        print(f"6.  Mixed Workload Test")
        print(f"7.  Set Rate Limit")
        print(f"8.  Show Configuration")
        print(f"9.  Save Configuration")
        print(f"10. Install/Update Dependencies")
        print(f"11. Exit{Colors.RESET}")
        
        choice = input(f"\n{Colors.CYAN}[?] Select option: {Colors.RESET}").strip()
        
        if choice == "1":
            print(f"\n{Colors.YELLOW}[!] Configure Testing Parameters{Colors.RESET}")
            tester.target_ip = get_input("Target IP/Hostname", tester.target_ip)
            tester.target_port = get_input("Target Port", tester.target_port, int)
            tester.threads = get_input("Threads", tester.threads, int)
            tester.duration = get_input("Duration (seconds)", tester.duration, int)
            tester.rate_limit = get_input("Requests per second per thread", tester.rate_limit, int)
            
        elif choice in ["2", "3", "4", "5", "6"]:
            if not tester.target_ip:
                print(f"{Colors.RED}[!] Please configure target first!{Colors.RESET}")
                continue
            
            test_types = {
                "2": "HTTP Load",
                "3": "WebSocket Load",
                "4": "Database Simulation",
                "5": "File Upload",
                "6": "Mixed Workload"
            }
            
            test_type = test_types[choice]
            
            print(f"{Colors.YELLOW}[!] Starting {test_type} test on YOUR OWN WEBSITE{Colors.RESET}")
            print(f"{Colors.YELLOW}[!] Make sure you have permission to test this target{Colors.RESET}")
            
            confirm = input(f"{Colors.YELLOW}[!] Start {test_type} test? (y/N): {Colors.RESET}").strip().lower()
            if confirm == 'y':
                tester.start_load_test(test_type)
            else:
                print(f"{Colors.RED}[!] Test cancelled{Colors.RESET}")
            
        elif choice == "7":
            tester.rate_limit = get_input("Requests per second per thread", tester.rate_limit, int)
            print(f"{Colors.GREEN}[+] Rate limit set to {tester.rate_limit} req/s/thread{Colors.RESET}")
            
        elif choice == "8":
            print(f"\n{Colors.YELLOW}[!] Current Configuration:{Colors.RESET}")
            print(f"Target: {tester.target_ip}:{tester.target_port}")
            print(f"Threads: {tester.threads}")
            print(f"Duration: {tester.duration}s")
            print(f"Rate Limit: {tester.rate_limit} req/s/thread")
            print(f"Timeout: {tester.timeout}s")
            
        elif choice == "9":
            tester.save_config()
            print(f"{Colors.GREEN}[+] Configuration saved!{Colors.RESET}")
            
        elif choice == "10":
            print(f"{Colors.YELLOW}[!] Installing/updating dependencies...{Colors.RESET}")
            if auto_install_dependencies():
                print(f"{Colors.GREEN}[+] Dependencies updated successfully!{Colors.RESET}")
            else:
                print(f"{Colors.RED}[!] Failed to update dependencies{Colors.RESET}")
            
        elif choice == "11":
            print(f"{Colors.GREEN}[+] Goodbye!{Colors.RESET}")
            break
            
        else:
            print(f"{Colors.RED}[!] Invalid option!{Colors.RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}[!] Interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}[!] Error: {e}{Colors.RESET}")