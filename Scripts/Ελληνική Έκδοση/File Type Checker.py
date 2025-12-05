import os
import sys
import subprocess
import hashlib
import math
import re
import zipfile
import binascii
import struct
import platform
import shutil
import json
from datetime import datetime

# --- Ρυθμίσεις ---
FOLDER_NAME = "File Type Checker"
MAX_FILE_SIZE_LIMIT = 50 * 1024 * 1024 * 1024  # Όριο 50 GB
ANALYSIS_RAM_LIMIT = 200 * 1024 * 1024         # Μόνο 200MB σε RAM για σάρωση προτύπων
QUARANTINE_THRESHOLD = 7
VIRUSTOTAL_API_KEY = "" 

# --- Διασταύρωση πλατφορμών ---
def get_target_dir():
    if os.path.exists('/data/data/com.termux/files/home'):
        return "/sdcard/Download/" + FOLDER_NAME
    return os.path.join(os.path.expanduser("~"), "Downloads", FOLDER_NAME)

TARGET_DIR = get_target_dir()

def install_dependencies():
    print(f"\033[96m[*] Έλεγχος απαιτήσεων...\033[0m")
    required = ['rich', 'requests', 'exifread']
    for lib in required:
        try:
            __import__(lib)
        except ImportError:
            print(f"\033[93m[!] Εγκατάσταση '{lib}'...\033[0m")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

try:
    install_dependencies()
    import requests
    import exifread
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.markup import escape
except Exception as e:
    print(f"Κρίσιμο Σφάλμα: {e}")
    sys.exit(1)

console = Console()

# --- Ανίχνευση Magic Byte ---
def get_file_mime(filepath, data_head):
    hex_head = binascii.hexlify(data_head[:16]).decode().upper()
    
    signatures = {
        "FFD8FF": ("image/jpeg", "Εικόνα JPEG"),
        "89504E47": ("image/png", "Εικόνα PNG"),
        "25504446": ("application/pdf", "Έγγραφο PDF"),
        "504B0304": ("application/zip", "Αρχείο ZIP"),
        "4D5A": ("application/x-dosexec", "Εκτελέσιμο Windows"),
        "7F454C46": ("application/x-elf", "Εκτελέσιμο Linux/Android"),
        "52617221": ("application/x-rar", "Αρχείο RAR"),
        "D0CF11E0": ("application/msword", "Παλαιού τύπου Έγγραφο Office"),
        "CAFEBABE": ("application/java", "Κλάση Java/Mach-O"),
    }
    
    for sig, (mime, desc) in signatures.items():
        if hex_head.startswith(sig):
            return mime, desc
            
    if shutil.which("file"):
        try:
            mime = subprocess.check_output(["file", "-b", "--mime-type", filepath], stderr=subprocess.DEVNULL).decode().strip()
            return mime, "Αναγνωρισμένο από σύστημα"
        except: pass
        
    return "unknown/data", "Άγνωστο δυαδικό"

# --- Πυρήνας Ανάλυσης ---
class GlobalStats:
    total = 0
    risky = 0
    clean = 0

class AdvancedAnalyzer:
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.size = os.path.getsize(filepath)
        self.risk_score = 0
        self.warnings = []
        self.hidden_data = [] 
        self.indicators = [] 
        self.data = b"" # Buffer ανάλυσης (μερικό)
        self.vt_result = "Δ/Υ"
        self.is_quarantined = False
        self.is_partial_read = False
        
        # --- ΕΥΦΥΗΣ ΦΟΡΤΩΣΗ (Βελτιστοποιημένη για 50GB αρχεία) ---
        try:
            with open(filepath, 'rb') as f:
                if self.size <= ANALYSIS_RAM_LIMIT:
                    # Μικρό αρχείο: Διάβασμα όλου
                    self.data = f.read()
                else:
                    # Μεγάλο αρχείο: Διάβασμα μόνο αρχής και τέλους
                    self.is_partial_read = True
                    head_size = ANALYSIS_RAM_LIMIT - (10 * 1024 * 1024) # Κράτηση 10MB για το τέλος
                    self.data = f.read(head_size)
                    
                    try:
                        f.seek(- (10 * 1024 * 1024), 2) # Μετάβαση στο τέλος μείον 10MB
                        self.data += f.read()
                    except: pass # Το αρχείο μπορεί να είναι μικρότερο από όσο νομίζαμε αν αποτύχει η seek
                    
                    self.warnings.append(f"Μεγάλο Αρχείο ({self.size/1024/1024/1024:.2f} GB). Αναλύθηκε μόνο αρχή/τέλος για εξοικονόμηση RAM.")
        except Exception as e:
            self.warnings.append(f"Σφάλμα Ανάγνωσης: {str(e)}")

    def get_hashes(self):
        # HASH ΣΕ ΡΕΥΜΑ (Δεν φορτώνει το αρχείο σε RAM)
        s = hashlib.sha256()
        try:
            with open(self.filepath, 'rb') as f:
                while chunk := f.read(8192 * 1024): # Διάβασμα σε κομμάτια των 8MB
                    s.update(chunk)
            return s.hexdigest()
        except:
            return "ΣΦΑΛΜΑ_HASH"

    def check_virustotal(self, sha256):
        if not VIRUSTOTAL_API_KEY: return
        try:
            url = f"https://www.virustotal.com/api/v3/files/{sha256}"
            headers = {"x-apikey": VIRUSTOTAL_API_KEY}
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                stats = resp.json()['data']['attributes']['last_analysis_stats']
                mal = stats['malicious']
                if mal > 0:
                    self.risk_score += 15
                    self.vt_result = f"[bold red]ΕΠΙΒΛΑΒΕΣ ({mal} μηχανές)[/]"
                    self.warnings.append(f"Το antivirus στο σύννεφο ανίχνευσε {mal} απειλές.")
                else:
                    self.vt_result = "[green]Καθαρό (Σύννεφο)[/]"
        except: pass

    def calculate_entropy(self):
        # Υπολογισμός εντροπίας στα buffered δεδομένα (αρχή/τέλος)
        if not self.data: return 0
        entropy = 0
        # Χρήση δείγματος για ταχύτητα σε μεγάλα buffers
        sample = self.data[:100000] if len(self.data) > 100000 else self.data
        for x in range(256):
            p_x = float(sample.count(x)) / len(sample)
            if p_x > 0: entropy += - p_x * math.log(p_x, 2)
        return entropy

    def analyze_pdf_structure(self):
        try:
            text_data = self.data.decode('latin-1', errors='ignore')
            triggers = {'/JavaScript': 5, '/JS': 5, '/OpenAction': 4, '/Launch': 6, '/URI': 2, '/SubmitForm': 3}
            for keyword, score in triggers.items():
                if keyword in text_data:
                    self.risk_score += score
                    self.warnings.append(f"Ανίχνευση ενεργού περιεχομένου PDF: {keyword}")
        except: pass

    def analyze_office_macros(self):
        if self.data[:4] == b'PK\x03\x04':
            try:
                if zipfile.is_zipfile(self.filepath):
                    with zipfile.ZipFile(self.filepath, 'r') as z:
                        for f in z.namelist():
                            if 'vbaProject.bin' in f or '.bas' in f:
                                self.risk_score += 8
                                self.warnings.append("Ανίχνευση Macro Office (VBA) στη δομή Zip")
                                return
            except: pass
        
        if b'Attribute VB_Name' in self.data:
            self.risk_score += 8
            self.warnings.append("Ανίχνευση παλαιού τύπου Macro Office (VBA)")

    def analyze_pe_header(self):
        if self.data[:2] != b'4D5A': return
        try:
            pe_offset = struct.unpack('<I', self.data[0x3C:0x40])[0]
            if pe_offset + 1000 > len(self.data): return # Εκτός buffer
            
            if self.data[pe_offset:pe_offset+4] != b'PE\x00\x00': return
            ts_offset = pe_offset + 8
            timestamp = struct.unpack('<I', self.data[ts_offset:ts_offset+4])[0]
            
            year = datetime.fromtimestamp(timestamp).year
            if year < 1990 or year > 2030:
                self.warnings.append(f"Ύποπτο έτος μεταγλώττισης: {year} (TimeStomping?)")
                self.risk_score += 3
            else:
                self.indicators.append(f"Μεταγλώττιση: {year}")
                
            header_chunk = self.data[pe_offset:pe_offset+1000]
            suspicious_sections = [b'.upx', b'.themida', b'.vmprotect', b'.aspack']
            for sec in suspicious_sections:
                if sec in header_chunk.lower():
                    self.warnings.append(f"Ανίχνευση συμπιεσμένου εκτελέσιμου: {sec.decode()}")
                    self.risk_score += 4
        except: pass

    def analyze_metadata(self):
        if self.filename.lower().endswith(('.jpg', '.jpeg', '.tif', '.wav')):
            try:
                # Το ExifRead διαβάζει απευθείας το αρχείο, οπότε χειρίζεται μεγάλα αρχεία αυτόματα
                with open(self.filepath, 'rb') as f:
                    tags = exifread.process_file(f, details=False)
                    for tag in tags.keys():
                        if tag in ('Image ImageDescription', 'Image Software', 'Image Artist', 'Image Copyright'):
                            self.hidden_data.append(f"Μεταδεδομένα {tag}: {tags[tag]}")
                        if 'GPS' in tag:
                            self.indicators.append("Βρέθηκαν δεδομένα τοποθεσίας GPS")
            except: pass

    def analyze_steganography_overlay(self, mime):
        eof_signatures = {
            "image/jpeg": b"\xFF\xD9",
            "image/png": b"\x49\x45\x4E\x44\xAE\x42\x60\x82", 
            "application/zip": None 
        }
        
        # Σάρωση του τέλους του BUFFER (που αντιστοιχεί στο τέλος του αρχείου λόγω ανάγνωσης τέλους)
        if mime in eof_signatures and eof_signatures[mime]:
            sig = eof_signatures[mime]
            # Αναζήτηση στα τελευταία 1MB δεδομένων για απόδοση
            search_area = self.data[-1048576:] if len(self.data) > 1048576 else self.data
            end_offset = search_area.rfind(sig)
            
            if end_offset != -1:
                # Υπολογισμός πραγματικών bytes που απομένουν μετά την υπογραφή στην περιοχή αναζήτησης
                actual_end = end_offset + len(sig)
                if actual_end < len(search_area):
                    excess = len(search_area) - actual_end
                    if excess > 100:
                        self.warnings.append(f"[bold red]ΣΤΗΓΜΑΤΟΓΡΑΦΙΑ:[/bold red] Βρέθηκαν {excess} bytes κρυφών δεδομένων μετά το EOF.")
                        self.risk_score += 5

    def analyze_archives(self):
        # Η ZipFile module χειρίζεται αυτόματα μεγάλα αρχεία μέσω ροής
        if zipfile.is_zipfile(self.filepath):
            try:
                with zipfile.ZipFile(self.filepath, 'r') as z:
                    file_list = z.namelist()
                    suspicious_ext = ['.exe', '.vbs', '.bat', '.sh', '.dex', '.so', '.dll', '.ps1']
                    
                    for f in file_list:
                        info = z.getinfo(f)
                        if info.file_size > 0 and info.compress_size > 0:
                            ratio = info.file_size / info.compress_size
                            if ratio > 100:
                                self.warnings.append(f"Πιθανό Zip Bomb: {f} (Αναλογία {ratio:.0f}:1)")
                                self.risk_score += 5

                        for ext in suspicious_ext:
                            if f.lower().endswith(ext):
                                self.warnings.append(f"Το αρχείο περιέχει εκτελέσιμο: {f}")
                                self.risk_score += 3
            except:
                self.warnings.append("Κατεστραμμένο αρχείο ή προστατευμένο ZIP")

    def analyze_strings(self):
        try:
            # Αποκωδικοποίηση μόνο του buffer
            text_data = self.data.decode('utf-8', errors='ignore')
            
            patterns = {
                "IPv4": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
                "Email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                "URL": r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                "Πορτοφόλι Bitcoin": r'\b(bc1|[13])[a-zA-Z0-9]{25,39}\b',
                "Προσωπικό Κλειδί": r'-----BEGIN (RSA|DSA|EC|OPENSSH|PGP) PRIVATE KEY-----',
                "Ασαφής PowerShell": r'(FromBase64String|::Decode|GNwZW|SUVY|IgB8AC|cwB3AGkAdABjAGgA)',
                "WebShell": r'(passthru|exec|shell_exec|eval\(base64_decode)',
                "WinAPI (Malware)": r'(VirtualAlloc|CreateRemoteThread|WriteProcessMemory|ShellExecute|URLDownloadToFile)'
            }

            found_ips = set()
            
            for p_name, p_val in patterns.items():
                matches = re.findall(p_val, text_data, re.IGNORECASE)
                if matches:
                    unique_matches = list(set(matches))[:3]
                    
                    if p_name == "IPv4":
                        for ip in unique_matches:
                            if not ip.startswith(('192.168', '127.0', '10.')): found_ips.add(ip)
                    elif p_name in ["WebShell", "WinAPI (Malware)", "Ασαφής PowerShell"]:
                        self.warnings.append(f"Ανίχνευση ύποπτου {p_name}: {unique_matches}")
                        self.risk_score += 4
                    elif p_name == "Προσωπικό Κλειδί":
                        self.warnings.append("ΚΡΙΤΙΚΟ: Βρέθηκε Κρυπτογραφικό Προσωπικό Κλειδί!")
                        self.risk_score += 10
                    else:
                        self.indicators.append(f"{p_name}: βρέθηκαν {len(matches)}")

            if found_ips:
                self.indicators.append(f"Δημόσιες IPs: {', '.join(list(found_ips)[:3])}")

        except Exception: pass

    def quarantine_file(self):
        if self.risk_score >= QUARANTINE_THRESHOLD:
            try:
                new_name = self.filepath + ".dangerous"
                os.rename(self.filepath, new_name)
                self.filename = os.path.basename(new_name)
                self.filepath = new_name
                self.is_quarantined = True
                self.warnings.append(f"[bold red]Το αρχείο μπήκε αυτόματα σε καραντίνα ως: .dangerous[/]")
            except Exception as e:
                self.warnings.append(f"Αποτυχία καραντίνας: {e}")

    def run(self):
        # Έλεγχος μεγέθους: Μόνο αν αυστηρά μεγαλύτερο από το όριο (50GB)
        if self.size > MAX_FILE_SIZE_LIMIT:
             console.print(f"[red]Παράβλεψη {self.filename}: Πολύ μεγάλο (>50GB)[/]")
             return

        sha256 = self.get_hashes()
        console.print(f"[cyan]>> Ανάλυση {escape(self.filename)}...[/cyan]")
        
        self.check_virustotal(sha256)
        mime, desc = get_file_mime(self.filepath, self.data)
        entropy = self.calculate_entropy()
        
        if entropy > 7.4 and "zip" not in mime and "image" not in mime:
             self.warnings.append(f"Υψηλή εντροπία ({entropy:.2f}): Πιθανό συμπιεσμένο/κρυπτογραφημένο περιεχόμενο.")
             self.risk_score += 3

        # Εκτέλεση ενοτήτων
        self.analyze_metadata()
        self.analyze_steganography_overlay(mime)
        self.analyze_archives()
        self.analyze_strings()
        self.analyze_pdf_structure()
        self.analyze_office_macros()
        self.analyze_pe_header()

        if any(x in mime for x in ["dosexec", "executable", "x-elf"]):
            self.risk_score += 5
            self.warnings.append(f"Το αρχείο είναι εκτελέσιμο δυαδικό ({mime})")

        if re.search(r'\.(exe|bat|sh|vbs|apk)\.[a-z]{3}$', self.filename.lower()):
            self.risk_score += 8
            self.warnings.append("Ανίχνευση διπλής επέκτασης (spoofing)")

        if self.risk_score >= QUARANTINE_THRESHOLD:
            self.quarantine_file()

        self.print_report(sha256, mime, desc, entropy)

    def print_report(self, sha256, mime, desc, entropy):
        if self.risk_score >= 7:
            color = "red"
            verdict = "ΕΠΙΚΙΝΔΥΝΟ"
            GlobalStats.risky += 1
        elif self.risk_score >= 4:
            color = "yellow"
            verdict = "ΎΠΟΠΤΟ"
            GlobalStats.risky += 1
        else:
            color = "green"
            verdict = "ΚΑΘΑΡΟ"
            GlobalStats.clean += 1

        info_table = Table(show_header=False, box=None)
        info_table.add_row("Τύπος", f"{mime} ({desc})")
        info_table.add_row("Εντροπία", f"{entropy:.3f}")
        info_table.add_row("Σύννεφο", self.vt_result)
        
        details = f"[bold {color} size=16]{verdict}[/] (Βαθμολογία: {self.risk_score})"
        
        if self.is_quarantined:
            details += "\n\n[bold white on red] Το αρχείο τέθηκε σε καραντίνα [/]"

        if self.warnings:
            details += "\n\n[bold red]--- ΑΠΕΙΛΕΣ ---[/]"
            for w in self.warnings: details += f"\n[red]![/] {escape(str(w))}"
            
        if self.hidden_data:
            details += "\n\n[bold magenta]--- ΚΡΥΦΑ ΔΕΔΟΜΕΝΑ/ΣΤΗΓΜΑΤΟΓΡΑΦΙΑ ---[/]"
            for h in self.hidden_data: details += f"\n[magenta]*[/] {escape(str(h))}"

        if self.indicators:
            details += "\n\n[bold blue]--- ΠΛΗΡΟΦΟΡΙΕΣ ---[/]"
            for i in self.indicators: details += f"\n[blue]i[/] {escape(str(i))}"

        layout = Layout()
        layout.split_row(
            Layout(Panel(info_table, title="Πληροφορίες Αρχείου")),
            Layout(Panel(details, title="Απόφαση Ανάλυσης", border_style=color))
        )
        
        console.print(Panel(f"[bold]{escape(self.filename)}[/bold]", style=f"on {color} black" if color=="red" else "bold white"))
        console.print(layout)
        console.print(f"[dim]SHA256: {sha256}[/dim]\n")

# --- Κύρια Διαδικασία ---
def main():
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR, exist_ok=True)
        console.print(f"[green]Δημιουργήθηκε φάκελος:[/green] {TARGET_DIR}")
        console.print("[yellow]Τοποθετήστε αρχεία εκεί για σάρωση![/yellow]")
        return

    files = [f for f in os.listdir(TARGET_DIR) if os.path.isfile(os.path.join(TARGET_DIR, f))]
    
    if not files:
        console.print(f"[yellow]Ο φάκελος είναι άδειος: {TARGET_DIR}[/yellow]")
        return

    console.print(f"[bold]Σάρωση {len(files)} αρχείων...[/bold]\n")
    for f in files:
        AdvancedAnalyzer(os.path.join(TARGET_DIR, f)).run()

if __name__ == "__main__":
    main()