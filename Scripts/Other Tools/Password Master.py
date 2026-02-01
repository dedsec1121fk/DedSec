import os
import sys
import subprocess
import string
import secrets
import math
import time
import json
import base64
import getpass
from datetime import datetime

# --- Part 1: Dependency Check & Auto-Install ---
REQUIRED = ["colorama", "zxcvbn", "cryptography"]

def install(package):
    print(f"[+] Installing {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except Exception:
        print(f"[-] Failed to install {package}. Check internet or run 'pkg install build-essential libsodium openssl'.")
        sys.exit(1)

try:
    import colorama
    from colorama import Fore, Back, Style
    from zxcvbn import zxcvbn
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:
    print("[-] Setting up environment...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    for pkg in REQUIRED:
        install(pkg)
    print("[+] Restarting script...")
    os.execv(sys.executable, ['python'] + sys.argv)

colorama.init(autoreset=True)

# --- Part 2: Security & Clipboard Utilities ---

class SecurityUtils:
    @staticmethod
    def clear():
        os.system('clear')

    @staticmethod
    def derive_key(password, salt):
        # Uses PBKDF2HMAC to securely derive a 32-byte key from the Master Password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    @staticmethod
    def encrypt(data, password):
        salt = secrets.token_bytes(16)
        key = SecurityUtils.derive_key(password, salt)
        return salt, Fernet(key).encrypt(json.dumps(data).encode())

    @staticmethod
    def decrypt(salt, token, password):
        try:
            key = SecurityUtils.derive_key(password, salt)
            return json.loads(Fernet(key).decrypt(token).decode())
        except Exception:
            return None

    @staticmethod
    def copy_clipboard(text):
        """Attempts to use Termux API to copy to clipboard."""
        try:
            p = subprocess.Popen(['termux-clipboard-set'], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            p.communicate(input=text.encode('utf-8'))
            return True
        except:
            return False

# --- Part 3: The Logic Core (Generators & Analyzers) ---

class PasswordLogic:
    def get_strength_color(self, score):
        return [Fore.RED, Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN][score]

    def generate_random_string(self, length=16, use_upper=True, use_lower=True, use_digits=True, use_symbols=True):
        """Helper function to generate a string based on rules"""
        chars = ""
        if use_upper: chars += string.ascii_uppercase
        if use_lower: chars += string.ascii_lowercase
        if use_digits: chars += string.digits
        if use_symbols: chars += "!@#$%^&*"
        
        if not chars: return None # Fail safe

        while True:
            pwd = ''.join(secrets.choice(chars) for _ in range(length))
            # Validation check
            valid = True
            if use_upper and not any(c.isupper() for c in pwd): valid = False
            if use_lower and not any(c.islower() for c in pwd): valid = False
            if use_digits and not any(c.isdigit() for c in pwd): valid = False
            if use_symbols and not any(c in "!@#$%^&*" for c in pwd): valid = False
            
            if valid: return pwd

    def analyze(self, password, interactive=True):
        if not password: return 0
        
        results = zxcvbn(password)
        score = results['score']
        crack_time = results['crack_times_display']['offline_slow_hashing_1e4_per_second']
        
        # Entropy calculation based on character pool
        pool = 0
        if any(c.islower() for c in password): pool += 26
        if any(c.isupper() for c in password): pool += 26
        if any(c.isdigit() for c in password): pool += 10
        if any(c in string.punctuation for c in password): pool += 32
        entropy = len(password) * math.log2(pool) if pool > 0 else 0

        if interactive:
            SecurityUtils.clear()
            print(f"\n{Fore.YELLOW}--- PASSWORD ANALYSIS ---{Style.RESET_ALL}")
            color = self.get_strength_color(score)
            print("-" * 40)
            print(f"Password:   {Back.WHITE}{Fore.BLACK} {password} {Style.RESET_ALL}")
            print(f"Score:      {color}{score}/4{Style.RESET_ALL}")
            print(f"Crack Time: {Fore.CYAN}{crack_time}{Style.RESET_ALL} (Offline)")
            print(f"Entropy:    {entropy:.1f} bits")
            
            if results['feedback']['warning']:
                print(f"Warning:    {Fore.RED}{results['feedback']['warning']}{Style.RESET_ALL}")
            if results['feedback']['suggestions']:
                print(f"Tip:        {Fore.YELLOW}{results['feedback']['suggestions'][0]}{Style.RESET_ALL}")
            print("-" * 40)
            input("Press Enter...")
        
        return score

    def generate_random_menu(self):
        SecurityUtils.clear()
        print(f"{Fore.BLUE}--- RANDOM PASSWORD GENERATOR ---{Style.RESET_ALL}")
        
        try:
            length = int(input("Length (default 16): ") or 16)
        except: length = 16
        
        inc_upper = input("Include Uppercase? (y/n): ").lower() == 'y'
        inc_lower = input("Include Lowercase? (y/n): ").lower() == 'y'
        inc_digits = input("Include Digits? (y/n): ").lower() == 'y'
        inc_symbols = input("Include Symbols? (y/n): ").lower() == 'y'
        
        # Fallback if user selects nothing
        if not (inc_upper or inc_lower or inc_digits or inc_symbols):
            print(f"{Fore.RED}No options selected. Defaulting to all.{Style.RESET_ALL}")
            inc_upper = inc_lower = inc_digits = inc_symbols = True
            time.sleep(1)

        pwd = self.generate_random_string(length, inc_upper, inc_lower, inc_digits, inc_symbols)
        
        print(f"\nGenerated: {Back.WHITE}{Fore.BLACK} {pwd} {Style.RESET_ALL}")
        if SecurityUtils.copy_clipboard(pwd): print(f"{Fore.YELLOW}[Copied]{Style.RESET_ALL}")
        self.analyze(pwd, interactive=False)
        input("Enter...")

    def generate_passphrase(self):
        """Generates logic for passphrase, returns string"""
        words = ["correct", "horse", "battery", "staple", "blue", "skies", "mango", "river", 
                 "falcon", "heavy", "metal", "pizza", "sushi", "dragon", "code", "linux", 
                 "solar", "wind", "happy", "sleep", "dream", "night", "watch", "space",
                 "rocket", "tablet", "monitor", "coffee", "sugar", "whiskey", "castle", "knight"]
        
        count = 4
        chosen = [secrets.choice(words) for _ in range(count)]
        chosen[secrets.randbelow(count)] = chosen[secrets.randbelow(count)].capitalize()
        
        pwd = "-".join(chosen)
        pwd += secrets.choice("0123456789") + secrets.choice("!@#$%")
        return pwd

    def generate_passphrase_menu(self):
        SecurityUtils.clear()
        print(f"{Fore.BLUE}--- PASSPHRASE GENERATOR ---{Style.RESET_ALL}")
        pwd = self.generate_passphrase()
        print(f"\nPassphrase: {Back.WHITE}{Fore.BLACK} {pwd} {Style.RESET_ALL}")
        if SecurityUtils.copy_clipboard(pwd): print(f"{Fore.YELLOW}[Copied]{Style.RESET_ALL}")
        self.analyze(pwd, interactive=False)
        input("Enter...")

    def improve_menu(self):
        SecurityUtils.clear()
        print(f"{Fore.MAGENTA}--- PASSWORD IMPROVER ---{Style.RESET_ALL}")
        base = input("Enter password to improve (e.g., 'iloveyou'): ")
        if not base: return

        # 1. Add Salt (Random suffix)
        suffix = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(6))
        
        # 2. Inject Symbol if missing
        temp = base + suffix
        if not any(c in "!@#$%^&*" for c in temp):
            # Insert symbol in the middle
            mid = len(temp) // 2
            temp = temp[:mid] + secrets.choice("!@#$%^&*") + temp[mid:]
        
        improved = temp
        
        # Ensure minimum length of 12
        if len(improved) < 12:
            padding = self.generate_random_string(12 - len(improved))
            improved += padding if padding else "123"
        
        old_score = zxcvbn(base)['score']
        new_score = zxcvbn(improved)['score']
        
        print(f"\n{Fore.YELLOW}Original:{Style.RESET_ALL} {base}")
        print(f"{Fore.GREEN}Improved:{Style.RESET_ALL} {Back.WHITE}{Fore.BLACK} {improved} {Style.RESET_ALL}")
        
        print(f"Strength Upgrade: {self.get_strength_color(old_score)}{old_score}/4{Style.RESET_ALL} -> {self.get_strength_color(new_score)}{new_score}/4{Style.RESET_ALL}")
        
        if SecurityUtils.copy_clipboard(improved):
            print(f"{Fore.YELLOW}[Copied to Clipboard]{Style.RESET_ALL}")
        input("Press Enter...")
        return improved
    
    def tools_menu(self):
        while True:
            SecurityUtils.clear()
            print(f"{Fore.YELLOW}--- SECURITY TOOLS ---{Style.RESET_ALL}")
            print(f"1. {Fore.BLUE}Generate Random Password{Style.RESET_ALL}")
            print(f"2. {Fore.BLUE}Generate Passphrase{Style.RESET_ALL}")
            print(f"3. {Fore.MAGENTA}Password Improver{Style.RESET_ALL}")
            print(f"4. {Fore.CYAN}Password Analyzer{Style.RESET_ALL}")
            print(f"5. Back to Main Menu")

            choice = input("\nSelect Option: ")

            if choice == '1': self.generate_random_menu()
            elif choice == '2': self.generate_passphrase_menu()
            elif choice == '3': self.improve_menu()
            elif choice == '4':
                p = input("Enter password to analyze: ")
                self.analyze(p, interactive=True)
            elif choice == '5': break


# --- Part 4: The Vault (Manager) ---

class Vault:
    def __init__(self):
        self.filename = "my_vault.enc"
        self.data = []
        self.master_pwd = None
        self.logic = PasswordLogic()

    def login(self):
        SecurityUtils.clear()
        if not os.path.exists(self.filename):
            print(f"{Fore.GREEN}[ CREATE NEW VAULT ]{Style.RESET_ALL}")
            p1 = getpass.getpass("Set Master Password: ")
            p2 = getpass.getpass("Confirm: ")
            if p1 == p2 and p1:
                self.master_pwd = p1
                self.save()
                print("Vault created.")
                time.sleep(1)
                return True
            print(f"{Fore.RED}Passwords do not match or empty.{Style.RESET_ALL}")
            time.sleep(1)
            return False
        
        print(f"{Fore.BLUE}[ UNLOCK VAULT ]{Style.RESET_ALL}")
        pwd = getpass.getpass("Master Password: ")
        
        try:
            with open(self.filename, "rb") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"{Fore.RED}Vault file not found.{Style.RESET_ALL}")
            time.sleep(2)
            return False
            
        decrypted = SecurityUtils.decrypt(content[:16], content[16:], pwd)
        if decrypted is not None:
            self.master_pwd = pwd
            self.data = decrypted
            print(f"{Fore.GREEN}Success.{Style.RESET_ALL}")
            time.sleep(0.5)
            return True
        else:
            print(f"{Fore.RED}Wrong password.{Style.RESET_ALL}")
            time.sleep(2)
            return False

    def save(self):
        salt, enc_data = SecurityUtils.encrypt(self.data, self.master_pwd)
        with open(self.filename, "wb") as f:
            f.write(salt + enc_data)
        print(f"{Fore.GREEN}Vault saved!{Style.RESET_ALL}")
        time.sleep(0.5)

    def menu(self):
        while True:
            SecurityUtils.clear()
            print(f"{Fore.CYAN}--- PASSWORD VAULT (Encrypted) ---{Style.RESET_ALL}")
            print(f"Entries: {len(self.data)}")
            print("1. View/Search Entries")
            print("2. Add New Entry")
            print("3. Manage Vault (Export/Import)")
            print("4. Back to Main Menu")
            
            c = input("Option: ")
            if c == '1': self.view_search()
            elif c == '2': self.add()
            elif c == '3': self.manage()
            elif c == '4': break

    def view_search(self):
        while True:
            SecurityUtils.clear()
            print(f"{Fore.GREEN}--- VAULT ENTRIES ---{Style.RESET_ALL}")
            if not self.data:
                print("Vault is empty.")
                input("Enter...")
                return

            search = input("Search (Service/User, Enter for all): ").lower()
            
            print(f"\n{'ID':<4} {'Service':<20} {'Username':<20}")
            print("-" * 50)
            
            found_indices = []
            for i, entry in enumerate(self.data):
                if search in entry['service'].lower() or search in entry['username'].lower():
                    print(f"{Fore.CYAN}{i+1:<4}{Style.RESET_ALL} {entry['service']:<20} {entry['username']:<20}")
                    found_indices.append(i)
            
            if not found_indices and search:
                print(f"{Fore.RED}No results found for '{search}'.{Style.RESET_ALL}")
            
            print("-" * 50)
            print("Actions: (ID) to copy/delete | (B)ack")
            
            choice = input(">> ").lower()
            if choice == 'b': break

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.data):
                    self.show_entry_details(idx)
            except ValueError:
                pass

    def show_entry_details(self, index):
        item = self.data[index]
        
        while True:
            SecurityUtils.clear()
            print(f"{Fore.GREEN}--- DETAILS: {item['service']} ---{Style.RESET_ALL}")
            print(f"Service:  {item['service']}")
            print(f"Username: {item['username']}")
            print(f"Date:     {item['date'] if 'date' in item else 'N/A'}")
            print(f"Password: {Back.WHITE}{Fore.BLACK} {item['password']} {Style.RESET_ALL}")
            print("-" * 30)
            print("1. Copy Password to Clipboard")
            print("2. Delete Entry")
            print("3. Back to List")

            c = input("Option: ")
            if c == '1':
                if SecurityUtils.copy_clipboard(item['password']):
                    print(f"{Fore.YELLOW}[Copied!]{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Copy failed (Termux:API not installed?){Style.RESET_ALL}")
                time.sleep(1)
            elif c == '2':
                if input("Confirm delete? (y/n): ").lower() == 'y':
                    self.data.pop(index)
                    self.save()
                    print(f"{Fore.RED}Entry deleted.{Style.RESET_ALL}")
                    time.sleep(1)
                    return # Exit details and return to list
            elif c == '3':
                break

    def add(self):
        SecurityUtils.clear()
        print(f"\n{Fore.GREEN}[ ADD NEW ENTRY ]{Style.RESET_ALL}")
        service = input("Service/Website: ")
        username = input("Username/Email:  ")
        
        print("\n1. Type password manually")
        print("2. Generate Random password")
        print("3. Generate Passphrase")
        
        c = input("Choice: ")
        pwd = ""
        if c == '2':
            pwd = self.logic.generate_random_string(length=16)
        elif c == '3':
            pwd = self.logic.generate_passphrase()
        else:
            pwd = input("Password: ")
        
        entry = {
            "service": service,
            "username": username,
            "password": pwd,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.data.append(entry)
        self.save()

    def manage(self):
        while True:
            SecurityUtils.clear()
            print(f"{Fore.MAGENTA}--- VAULT MANAGEMENT ---{Style.RESET_ALL}")
            print("1. Export Encrypted Vault (Backup)")
            print("2. Import Encrypted Vault (Restore)")
            print("3. Back")
            
            c = input("Option: ")
            if c == '1': self.export_vault()
            elif c == '2': self.import_vault()
            elif c == '3': break

    def export_vault(self):
        # Determine the correct path
        # Primary: Android/Termux Internal Storage
        backup_dir = "/storage/emulated/0/Download/Password Master Backup"
        
        # Fallback: PC Users (Home directory / Downloads)
        if not os.path.exists("/storage/emulated/0"):
             backup_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'Password Master Backup')

        # Create folder if not exists
        try:
            os.makedirs(backup_dir, exist_ok=True)
        except OSError as e:
            print(f"{Fore.RED}Error creating backup folder: {e}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Tip: Run 'termux-setup-storage' in terminal.{Style.RESET_ALL}")
            input("Press Enter...")
            return

        # Fixed filename to ensure replacement/overwrite
        backup_filename = "vault_backup.enc"
        full_path = os.path.join(backup_dir, backup_filename)
        
        if not os.path.exists(self.filename):
            print(f"{Fore.RED}Vault file not found. Nothing to export.{Style.RESET_ALL}")
            time.sleep(2)
            return

        try:
            with open(self.filename, 'rb') as src, open(full_path, 'wb') as dest:
                dest.write(src.read())
            
            print(f"{Fore.GREEN}Vault exported successfully!{Style.RESET_ALL}")
            print(f"Location: {Fore.YELLOW}{full_path}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Previous backup (if any) was overwritten.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Export failed: {e}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Ensure you have granted storage permissions!{Style.RESET_ALL}")

        input("Press Enter...")

    def import_vault(self):
        import_filename = input("Enter full path/filename to import: ")
        if not os.path.exists(import_filename):
            print(f"{Fore.RED}File not found: {import_filename}{Style.RESET_ALL}")
            time.sleep(2)
            return

        confirm = input(f"Importing will OVERWRITE current vault. Continue? (y/n): ").lower()
        if confirm != 'y': return

        # Verify the file is actually a valid encrypted vault with the master password
        try:
            with open(import_filename, "rb") as f:
                content = f.read()
            
            # Attempt to decrypt the file using the *current* master password
            temp_data = SecurityUtils.decrypt(content[:16], content[16:], self.master_pwd)
            
            if temp_data is None:
                print(f"{Fore.RED}Import failed: The file is not compatible with your current Master Password.{Style.RESET_ALL}")
                input("Press Enter...")
                return

            # Overwrite the main vault file
            with open(self.filename, 'wb') as dest:
                dest.write(content)
            
            # Reload the newly imported data
            self.data = temp_data 
            print(f"{Fore.GREEN}Vault imported and loaded successfully!{Style.RESET_ALL}")
            input("Press Enter...")

        except Exception as e:
            print(f"{Fore.RED}An error occurred during import: {e}{Style.RESET_ALL}")
            time.sleep(2)

# --- Part 5: Main Application ---

def main_menu():
    vault = Vault()
    logic = PasswordLogic()
    
    while True:
        SecurityUtils.clear()
        print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════╗
║  {Fore.YELLOW}PASSWORD HOLDER.py - Security Suite{Fore.CYAN} ║
╚══════════════════════════════════════════════╝{Style.RESET_ALL}
""")
        print(f"1. {Fore.GREEN}Password Manager (Vault){Style.RESET_ALL} - Store encrypted passwords.")
        print(f"2. {Fore.BLUE}Security Tools{Style.RESET_ALL} - Generate, Improve, Analyze.")
        print(f"3. Exit")
        
        choice = input("\nSelect Option: ")
        
        if choice == '1':
            if vault.master_pwd or vault.login():
                vault.menu()
        
        elif choice == '2':
            logic.tools_menu()
            
        elif choice == '3':
            print("Stay safe and secure!")
            sys.exit()

if __name__ == "__main__":
    main_menu()