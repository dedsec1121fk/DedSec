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

# --- Μέρος 1: Έλεγχος Εξαρτήσεων & Αυτόματη Εγκατάσταση ---
REQUIRED = ["colorama", "zxcvbn", "cryptography"]

def install(package):
    print(f"[+] Εγκατάσταση του {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except Exception:
        print(f"[-] Αποτυχία εγκατάστασης του {package}. Ελέγξτε τη σύνδεση ή εκτελέστε 'pkg install build-essential libsodium openssl'.")
        sys.exit(1)

try:
    import colorama
    from colorama import Fore, Back, Style
    from zxcvbn import zxcvbn
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
except ImportError:
    print("[-] Ρύθμιση περιβάλλοντος...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    for pkg in REQUIRED:
        install(pkg)
    print("[+] Επανεκκίνηση σεναρίου...")
    os.execv(sys.executable, ['python'] + sys.argv)

colorama.init(autoreset=True)

# --- Μέρος 2: Ασφάλεια & Εργαλεία Πρόχειρου ---

class SecurityUtils:
    @staticmethod
    def clear():
        os.system('clear')

    @staticmethod
    def derive_key(password, salt):
        # Χρησιμοποιεί PBKDF2HMAC για να εξάγει με ασφάλεια ένα κλειδί 32-byte από τον Κύριο Κωδικό
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
        """Προσπαθεί να χρησιμοποιήσει το Termux API για αντιγραφή στο πρόχειρο."""
        try:
            p = subprocess.Popen(['termux-clipboard-set'], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            p.communicate(input=text.encode('utf-8'))
            return True
        except:
            return False

# --- Μέρος 3: Ο Βασικός Κώδικας (Δημιουργοί & Αναλυτές) ---

class PasswordLogic:
    def get_strength_color(self, score):
        return [Fore.RED, Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN][score]

    def generate_random_string(self, length=16, use_upper=True, use_lower=True, use_digits=True, use_symbols=True):
        """Βοηθητική συνάρτηση για δημιουργία συμβολοσειράς βάσει κανόνων"""
        chars = ""
        if use_upper: chars += string.ascii_uppercase
        if use_lower: chars += string.ascii_lowercase
        if use_digits: chars += string.digits
        if use_symbols: chars += "!@#$%^&*"
        
        if not chars: return None # Ασφάλεια

        while True:
            pwd = ''.join(secrets.choice(chars) for _ in range(length))
            # Έλεγχος εγκυρότητας
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
        
        # Υπολογισμός εντροπίας βάσει συνόλου χαρακτήρων
        pool = 0
        if any(c.islower() for c in password): pool += 26
        if any(c.isupper() for c in password): pool += 26
        if any(c.isdigit() for c in password): pool += 10
        if any(c in string.punctuation for c in password): pool += 32
        entropy = len(password) * math.log2(pool) if pool > 0 else 0

        if interactive:
            SecurityUtils.clear()
            print(f"\n{Fore.YELLOW}--- ΑΝΑΛΥΣΗ ΚΩΔΙΚΟΠΡΟΣΤΑΣΙΑΣ ---{Style.RESET_ALL}")
            color = self.get_strength_color(score)
            print("-" * 40)
            print(f"Κωδικός:   {Back.WHITE}{Fore.BLACK} {password} {Style.RESET_ALL}")
            print(f"Βαθμολογία: {color}{score}/4{Style.RESET_ALL}")
            print(f"Χρόνος Κρακάρισμα: {Fore.CYAN}{crack_time}{Style.RESET_ALL} (Offline)")
            print(f"Εντροπία:    {entropy:.1f} bits")
            
            if results['feedback']['warning']:
                print(f"Προειδοποίηση:    {Fore.RED}{results['feedback']['warning']}{Style.RESET_ALL}")
            if results['feedback']['suggestions']:
                print(f"Συμβουλή:        {Fore.YELLOW}{results['feedback']['suggestions'][0]}{Style.RESET_ALL}")
            print("-" * 40)
            input("Πατήστε Enter...")
        
        return score

    def generate_random_menu(self):
        SecurityUtils.clear()
        print(f"{Fore.BLUE}--- ΔΗΜΙΟΥΡΓΟΣ ΤΥΧΑΙΟΥ ΚΩΔΙΚΟΥ ---{Style.RESET_ALL}")
        
        try:
            length = int(input("Μήκος (προεπιλογή 16): ") or 16)
        except: length = 16
        
        inc_upper = input("Περιλαμβάνεται κεφαλαία; (ν/ο): ").lower() == 'ν'
        inc_lower = input("Περιλαμβάνεται πεζά; (ν/ο): ").lower() == 'ν'
        inc_digits = input("Περιλαμβάνονται ψηφία; (ν/ο): ").lower() == 'ν'
        inc_symbols = input("Περιλαμβάνονται σύμβολα; (ν/ο): ").lower() == 'ν'
        
        # Επιστροφή αν ο χρήστης δεν επιλέξει τίποτα
        if not (inc_upper or inc_lower or inc_digits or inc_symbols):
            print(f"{Fore.RED}Δεν επιλέχθηκαν επιλογές. Χρήση όλων.{Style.RESET_ALL}")
            inc_upper = inc_lower = inc_digits = inc_symbols = True
            time.sleep(1)

        pwd = self.generate_random_string(length, inc_upper, inc_lower, inc_digits, inc_symbols)
        
        print(f"\nΔημιουργήθηκε: {Back.WHITE}{Fore.BLACK} {pwd} {Style.RESET_ALL}")
        if SecurityUtils.copy_clipboard(pwd): print(f"{Fore.YELLOW}[Αντιγράφηκε]{Style.RESET_ALL}")
        self.analyze(pwd, interactive=False)
        input("Enter...")

    def generate_passphrase(self):
        """Δημιουργεί λογική για φράση-κλειδί, επιστρέφει συμβολοσειρά"""
        words = ["καλημέρα", "ήλιος", "θάλασσα", "βουνό", "δάσος", "ποτάμι", 
                 "παράθυρο", "πορτοκάλι", "λεμόνι", "βαρέλι", "αρκούδα", 
                 "φεγγάρι", "αστέρι", "σύννεφο", "βροχή", "χιονιά", 
                 "καράβι", "αεροπλάνο", "τραίνο", "αυτοκίνητο", "ποδήλατο",
                 "βιβλίο", "στυλό", "χαρτί", "υπολογιστής", "οθόνη", "πληκτρολόγιο",
                 "ποτήρι", "πιάτο", "κουτάλι", "μαχαίρι", "πλατεία"]
        
        count = 4
        chosen = [secrets.choice(words) for _ in range(count)]
        chosen[secrets.randbelow(count)] = chosen[secrets.randbelow(count)].capitalize()
        
        pwd = "-".join(chosen)
        pwd += secrets.choice("0123456789") + secrets.choice("!@#$%")
        return pwd

    def generate_passphrase_menu(self):
        SecurityUtils.clear()
        print(f"{Fore.BLUE}--- ΔΗΜΙΟΥΡΓΟΣ ΦΡΑΣΗΣ-ΚΛΕΙΔΙΟΥ ---{Style.RESET_ALL}")
        pwd = self.generate_passphrase()
        print(f"\nΦράση-Κλειδί: {Back.WHITE}{Fore.BLACK} {pwd} {Style.RESET_ALL}")
        if SecurityUtils.copy_clipboard(pwd): print(f"{Fore.YELLOW}[Αντιγράφηκε]{Style.RESET_ALL}")
        self.analyze(pwd, interactive=False)
        input("Enter...")

    def improve_menu(self):
        SecurityUtils.clear()
        print(f"{Fore.MAGENTA}--- ΒΕΛΤΙΩΤΗΣ ΚΩΔΙΚΩΝ ---{Style.RESET_ALL}")
        base = input("Εισάγετε κωδικό για βελτίωση (π.χ., 'αγαπώσενα'): ")
        if not base: return

        # 1. Προσθήκη Αλατιού (Τυχαία επίληξη)
        suffix = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(6))
        
        # 2. Εισαγωγή Συμβόλου αν λείπει
        temp = base + suffix
        if not any(c in "!@#$%^&*" for c in temp):
            # Εισαγωγή συμβόλου στη μέση
            mid = len(temp) // 2
            temp = temp[:mid] + secrets.choice("!@#$%^&*") + temp[mid:]
        
        improved = temp
        
        # Εξασφάλιση ελάχιστου μήκους 12
        if len(improved) < 12:
            padding = self.generate_random_string(12 - len(improved))
            improved += padding if padding else "123"
        
        old_score = zxcvbn(base)['score']
        new_score = zxcvbn(improved)['score']
        
        print(f"\n{Fore.YELLOW}Αρχικός:{Style.RESET_ALL} {base}")
        print(f"{Fore.GREEN}Βελτιωμένος:{Style.RESET_ALL} {Back.WHITE}{Fore.BLACK} {improved} {Style.RESET_ALL}")
        
        print(f"Αναβάθμιση Ισχύος: {self.get_strength_color(old_score)}{old_score}/4{Style.RESET_ALL} -> {self.get_strength_color(new_score)}{new_score}/4{Style.RESET_ALL}")
        
        if SecurityUtils.copy_clipboard(improved):
            print(f"{Fore.YELLOW}[Αντιγράφηκε στο Πρόχειρο]{Style.RESET_ALL}")
        input("Πατήστε Enter...")
        return improved
    
    def tools_menu(self):
        while True:
            SecurityUtils.clear()
            print(f"{Fore.YELLOW}--- ΕΡΓΑΛΕΙΑ ΑΣΦΑΛΕΙΑΣ ---{Style.RESET_ALL}")
            print(f"1. {Fore.BLUE}Δημιουργία Τυχαίου Κωδικού{Style.RESET_ALL}")
            print(f"2. {Fore.BLUE}Δημιουργία Φράσης-Κλειδιού{Style.RESET_ALL}")
            print(f"3. {Fore.MAGENTA}Βελτιωτής Κωδικού{Style.RESET_ALL}")
            print(f"4. {Fore.CYAN}Αναλυτής Κωδικού{Style.RESET_ALL}")
            print(f"5. Επιστροφή στο Κύριο Μενού")

            choice = input("\nΕπιλογή: ")

            if choice == '1': self.generate_random_menu()
            elif choice == '2': self.generate_passphrase_menu()
            elif choice == '3': self.improve_menu()
            elif choice == '4':
                p = input("Εισάγετε κωδικό για ανάλυση: ")
                self.analyze(p, interactive=True)
            elif choice == '5': break


# --- Μέρος 4: Το Θωρακισμένο (Διαχειριστής) ---

class Vault:
    def __init__(self):
        self.filename = "my_vault.enc"
        self.data = []
        self.master_pwd = None
        self.logic = PasswordLogic()

    def login(self):
        SecurityUtils.clear()
        if not os.path.exists(self.filename):
            print(f"{Fore.GREEN}[ ΔΗΜΙΟΥΡΓΙΑ ΝΕΟΥ ΘΩΡΑΚΙΣΜΕΝΟΥ ]{Style.RESET_ALL}")
            p1 = getpass.getpass("Ορίστε Κύριο Κωδικό: ")
            p2 = getpass.getpass("Επιβεβαίωση: ")
            if p1 == p2 and p1:
                self.master_pwd = p1
                self.save()
                print("Το θωρακισμένο δημιουργήθηκε.")
                time.sleep(1)
                return True
            print(f"{Fore.RED}Οι κωδικοί δεν ταιριάζουν ή είναι κενόι.{Style.RESET_ALL}")
            time.sleep(1)
            return False
        
        print(f"{Fore.BLUE}[ ΞΕΚΛΕΙΔΩΜΑ ΘΩΡΑΚΙΣΜΕΝΟΥ ]{Style.RESET_ALL}")
        pwd = getpass.getpass("Κύριος Κωδικός: ")
        
        try:
            with open(self.filename, "rb") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"{Fore.RED}Το αρχείο θωρακισμένου δεν βρέθηκε.{Style.RESET_ALL}")
            time.sleep(2)
            return False
            
        decrypted = SecurityUtils.decrypt(content[:16], content[16:], pwd)
        if decrypted is not None:
            self.master_pwd = pwd
            self.data = decrypted
            print(f"{Fore.GREEN}Επιτυχία.{Style.RESET_ALL}")
            time.sleep(0.5)
            return True
        else:
            print(f"{Fore.RED}Λάθος κωδικός.{Style.RESET_ALL}")
            time.sleep(2)
            return False

    def save(self):
        salt, enc_data = SecurityUtils.encrypt(self.data, self.master_pwd)
        with open(self.filename, "wb") as f:
            f.write(salt + enc_data)
        print(f"{Fore.GREEN}Το θωρακισμένο αποθηκεύτηκε!{Style.RESET_ALL}")
        time.sleep(0.5)

    def menu(self):
        while True:
            SecurityUtils.clear()
            print(f"{Fore.CYAN}--- ΘΩΡΑΚΙΣΜΕΝΟ ΚΩΔΙΚΩΝ (Κρυπτογραφημένο) ---{Style.RESET_ALL}")
            print(f"Εγγραφές: {len(self.data)}")
            print("1. Προβολή/Αναζήτηση Εγγραφών")
            print("2. Προσθήκη Νέας Εγγραφής")
            print("3. Διαχείριση Θωρακισμένου (Εξαγωγή/Εισαγωγή)")
            print("4. Επιστροφή στο Κύριο Μενού")
            
            c = input("Επιλογή: ")
            if c == '1': self.view_search()
            elif c == '2': self.add()
            elif c == '3': self.manage()
            elif c == '4': break

    def view_search(self):
        while True:
            SecurityUtils.clear()
            print(f"{Fore.GREEN}--- ΕΓΓΡΑΦΕΣ ΘΩΡΑΚΙΣΜΕΝΟΥ ---{Style.RESET_ALL}")
            if not self.data:
                print("Το θωρακισμένο είναι άδειο.")
                input("Enter...")
                return

            search = input("Αναζήτηση (Υπηρεσία/Χρήστης, Enter για όλα): ").lower()
            
            print(f"\n{'ID':<4} {'Υπηρεσία':<20} {'Χρήστης':<20}")
            print("-" * 50)
            
            found_indices = []
            for i, entry in enumerate(self.data):
                if search in entry['service'].lower() or search in entry['username'].lower():
                    print(f"{Fore.CYAN}{i+1:<4}{Style.RESET_ALL} {entry['service']:<20} {entry['username']:<20}")
                    found_indices.append(i)
            
            if not found_indices and search:
                print(f"{Fore.RED}Δεν βρέθηκαν αποτελέσματα για '{search}'.{Style.RESET_ALL}")
            
            print("-" * 50)
            print("Ενέργειες: (ID) για αντιγραφή/διαγραφή | (Π)ίσω")
            
            choice = input(">> ").lower()
            if choice == 'π' or choice == 'b': break

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
            print(f"{Fore.GREEN}--- ΛΕΠΤΟΜΕΡΕΙΕΣ: {item['service']} ---{Style.RESET_ALL}")
            print(f"Υπηρεσία:  {item['service']}")
            print(f"Χρήστης: {item['username']}")
            print(f"Ημερομηνία:     {item['date'] if 'date' in item else 'N/A'}")
            print(f"Κωδικός: {Back.WHITE}{Fore.BLACK} {item['password']} {Style.RESET_ALL}")
            print("-" * 30)
            print("1. Αντιγραφή Κωδικού στο Πρόχειρο")
            print("2. Διαγραφή Εγγραφής")
            print("3. Επιστροφή στη Λίστα")

            c = input("Επιλογή: ")
            if c == '1':
                if SecurityUtils.copy_clipboard(item['password']):
                    print(f"{Fore.YELLOW}[Αντιγράφηκε!]{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Αποτυχία αντιγραφής (Termux:API δεν είναι εγκατεστημένο?){Style.RESET_ALL}")
                time.sleep(1)
            elif c == '2':
                if input("Επιβεβαίωση διαγραφής; (ν/ο): ").lower() == 'ν':
                    self.data.pop(index)
                    self.save()
                    print(f"{Fore.RED}Η εγγραφή διαγράφηκε.{Style.RESET_ALL}")
                    time.sleep(1)
                    return # Έξοδος από λεπτομέρειες και επιστροφή στη λίστα
            elif c == '3':
                break

    def add(self):
        SecurityUtils.clear()
        print(f"\n{Fore.GREEN}[ ΠΡΟΣΘΗΚΗ ΝΕΑΣ ΕΓΓΡΑΦΗΣ ]{Style.RESET_ALL}")
        service = input("Υπηρεσία/Ιστότοπος: ")
        username = input("Χρήστης/Email:  ")
        
        print("\n1. Χειροκίνητη εισαγωγή κωδικού")
        print("2. Δημιουργία τυχαίου κωδικού")
        print("3. Δημιουργία φράσης-κλειδιού")
        
        c = input("Επιλογή: ")
        pwd = ""
        if c == '2':
            pwd = self.logic.generate_random_string(length=16)
        elif c == '3':
            pwd = self.logic.generate_passphrase()
        else:
            pwd = input("Κωδικός: ")
        
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
            print(f"{Fore.MAGENTA}--- ΔΙΑΧΕΙΡΙΣΗ ΘΩΡΑΚΙΣΜΕΝΟΥ ---{Style.RESET_ALL}")
            print("1. Εξαγωγή Κρυπτογραφημένου Θωρακισμένου (Αντίγραφο Ασφαλείας)")
            print("2. Εισαγωγή Κρυπτογραφημένου Θωρακισμένου (Επαναφορά)")
            print("3. Πίσω")
            
            c = input("Επιλογή: ")
            if c == '1': self.export_vault()
            elif c == '2': self.import_vault()
            elif c == '3': break

    def export_vault(self):
        # Καθορισμός σωστής διαδρομής
        # Πρωταρχική: Εσωτερική Αποθήκευση Android/Termux
        backup_dir = "/storage/emulated/0/Download/Αντίγραφο Ασφαλείας Password Master"
        
        # Επιστροφή: Χρήστες PC (Κύριος κατάλογος / Λήψεις)
        if not os.path.exists("/storage/emulated/0"):
             backup_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'Αντίγραφο Ασφαλείας Password Master')

        # Δημιουργία φακέλου αν δεν υπάρχει
        try:
            os.makedirs(backup_dir, exist_ok=True)
        except OSError as e:
            print(f"{Fore.RED}Σφάλμα δημιουργίας φακέλου αντιγράφου ασφαλείας: {e}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Συμβουλή: Εκτελέστε 'termux-setup-storage' στο τερματικό.{Style.RESET_ALL}")
            input("Πατήστε Enter...")
            return

        # Σταθερό όνομα αρχείου για εξασφάλιση αντικατάστασης
        backup_filename = "αντίγραφο_ασφαλείας_θωρακισμένου.enc"
        full_path = os.path.join(backup_dir, backup_filename)
        
        if not os.path.exists(self.filename):
            print(f"{Fore.RED}Το αρχείο θωρακισμένου δεν βρέθηκε. Δεν υπάρχει τίποτα προς εξαγωγή.{Style.RESET_ALL}")
            time.sleep(2)
            return

        try:
            with open(self.filename, 'rb') as src, open(full_path, 'wb') as dest:
                dest.write(src.read())
            
            print(f"{Fore.GREEN}Το θωρακισμένο εξήχθη επιτυχώς!{Style.RESET_ALL}")
            print(f"Τοποθεσία: {Fore.YELLOW}{full_path}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Το προηγούμενο αντίγραφο ασφαλείας (αν υπήρχε) αντικαταστάθηκε.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Αποτυχία εξαγωγής: {e}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Βεβαιωθείτε ότι έχετε παραχωρήσει δικαιώματα αποθήκευσης!{Style.RESET_ALL}")

        input("Πατήστε Enter...")

    def import_vault(self):
        import_filename = input("Εισάγετε πλήρη διαδρομή/όνομα αρχείου για εισαγωγή: ")
        if not os.path.exists(import_filename):
            print(f"{Fore.RED}Το αρχείο δεν βρέθηκε: {import_filename}{Style.RESET_ALL}")
            time.sleep(2)
            return

        confirm = input(f"Η εισαγωγή θα ΑΝΤΙΚΑΤΑΣΤΗΣΕΙ το τρέχον θωρακισμένο. Συνέχεια; (ν/ο): ").lower()
        if confirm != 'ν': return

        # Επαλήθευση ότι το αρχείο είναι έγκυρο κρυπτογραφημένο θωρακισμένο με τον κύριο κωδικό
        try:
            with open(import_filename, "rb") as f:
                content = f.read()
            
            # Προσπάθεια αποκρυπτογράφησης με τον *τρέχοντα* κύριο κωδικό
            temp_data = SecurityUtils.decrypt(content[:16], content[16:], self.master_pwd)
            
            if temp_data is None:
                print(f"{Fore.RED}Αποτυχία εισαγωγής: Το αρχείο δεν είναι συμβατό με τον τρέχοντα Κύριο Κωδικό.{Style.RESET_ALL}")
                input("Πατήστε Enter...")
                return

            # Αντικατάσταση του κύριου αρχείου θωρακισμένου
            with open(self.filename, 'wb') as dest:
                dest.write(content)
            
            # Επαναφόρτωση των νέων δεδομένων
            self.data = temp_data 
            print(f"{Fore.GREEN}Το θωρακισμένο εισήχθη και φορτώθηκε επιτυχώς!{Style.RESET_ALL}")
            input("Πατήστε Enter...")

        except Exception as e:
            print(f"{Fore.RED}Προέκυψε σφάλμα κατά την εισαγωγή: {e}{Style.RESET_ALL}")
            time.sleep(2)

# --- Μέρος 5: Κύρια Εφαρμογή ---

def main_menu():
    vault = Vault()
    logic = PasswordLogic()
    
    while True:
        SecurityUtils.clear()
        print(f"""
{Fore.CYAN}╔════════════════════════════════════════════════════╗
║  {Fore.YELLOW}Password Master - Σουίτα Ασφαλείας{Fore.CYAN}          ║
╚════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")
        print(f"1. {Fore.GREEN}Διαχειριστής Κωδικών (Θωρακισμένο){Style.RESET_ALL} - Αποθήκευση κρυπτογραφημένων κωδικών.")
        print(f"2. {Fore.BLUE}Εργαλεία Ασφαλείας{Style.RESET_ALL} - Δημιουργία, Βελτίωση, Ανάλυση.")
        print(f"3. Έξοδος")
        
        choice = input("\nΕπιλογή: ")
        
        if choice == '1':
            if vault.master_pwd or vault.login():
                vault.menu()
        
        elif choice == '2':
            logic.tools_menu()
            
        elif choice == '3':
            print("Μείνε ασφαλής!")
            sys.exit()

if __name__ == "__main__":
    main_menu()