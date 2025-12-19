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

# --- Configuration ---
FOLDER_NAME = "File Type Checker"
MAX_FILE_SIZE_LIMIT = 50 * 1024 * 1024 * 1024  # 50 GB Limit
ANALYSIS_RAM_LIMIT = 200 * 1024 * 1024         # Only load 200MB into RAM for pattern scanning
QUARANTINE_THRESHOLD = 7
VIRUSTOTAL_API_KEY = "" 

# --- Cross-Platform Setup ---
def get_target_dir():
    if os.path.exists('/data/data/com.termux/files/home'):
        return "/sdcard/Download/" + FOLDER_NAME
    return os.path.join(os.path.expanduser("~"), "Downloads", FOLDER_NAME)

TARGET_DIR = get_target_dir()

def install_dependencies():
    print(f"\033[96m[*] Checking dependencies...\033[0m")
    required = ['rich', 'requests', 'exifread']
    for lib in required:
        try:
            __import__(lib)
        except ImportError:
            print(f"\033[93m[!] Installing '{lib}'...\033[0m")
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
    print(f"Critical Error: {e}")
    sys.exit(1)

console = Console()

# --- Magic Byte Detection ---
def get_file_mime(filepath, data_head):
    hex_head = binascii.hexlify(data_head[:16]).decode().upper()
    
    signatures = {
        "FFD8FF": ("image/jpeg", "JPEG Image"),
        "89504E47": ("image/png", "PNG Image"),
        "25504446": ("application/pdf", "PDF Document"),
        "504B0304": ("application/zip", "ZIP Archive"),
        "4D5A": ("application/x-dosexec", "Windows Executable"),
        "7F454C46": ("application/x-elf", "Linux/Android Executable"),
        "52617221": ("application/x-rar", "RAR Archive"),
        "D0CF11E0": ("application/msword", "Legacy Office Doc"),
        "CAFEBABE": ("application/java", "Java Class/Mach-O"),
    }
    
    for sig, (mime, desc) in signatures.items():
        if hex_head.startswith(sig):
            return mime, desc
            
    if shutil.which("file"):
        try:
            mime = subprocess.check_output(["file", "-b", "--mime-type", filepath], stderr=subprocess.DEVNULL).decode().strip()
            return mime, "System Identified"
        except: pass
        
    return "unknown/data", "Unknown Binary"

# --- Analysis Core ---
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
        self.data = b"" # Analysis Buffer (Partial)
        self.vt_result = "N/A"
        self.is_quarantined = False
        self.is_partial_read = False
        
        # --- SMART LOADING (Optimized for 50GB files) ---
        try:
            with open(filepath, 'rb') as f:
                if self.size <= ANALYSIS_RAM_LIMIT:
                    # Small file: Read all
                    self.data = f.read()
                else:
                    # Large file: Read Head + Tail only
                    self.is_partial_read = True
                    head_size = ANALYSIS_RAM_LIMIT - (10 * 1024 * 1024) # Reserve 10MB for tail
                    self.data = f.read(head_size)
                    
                    try:
                        f.seek(- (10 * 1024 * 1024), 2) # Go to end minus 10MB
                        self.data += f.read()
                    except: pass # File might be smaller than we thought if seek fails
                    
                    self.warnings.append(f"Large File ({self.size/1024/1024/1024:.2f} GB). Analyzed Head/Tail only to save RAM.")
        except Exception as e:
            self.warnings.append(f"Read Error: {str(e)}")

    def get_hashes(self):
        # STREAMING HASH (Does not load file into RAM)
        s = hashlib.sha256()
        try:
            with open(self.filepath, 'rb') as f:
                while chunk := f.read(8192 * 1024): # Read in 8MB chunks
                    s.update(chunk)
            return s.hexdigest()
        except:
            return "HASH_ERROR"

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
                    self.vt_result = f"[bold red]MALICIOUS ({mal} engines)[/]"
                    self.warnings.append(f"Cloud antivirus detected {mal} threats.")
                else:
                    self.vt_result = "[green]Clean (Cloud)[/]"
        except: pass

    def calculate_entropy(self):
        # Calculate entropy on the buffered data (Head/Tail)
        if not self.data: return 0
        entropy = 0
        # Use a sample for speed on large buffers
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
                    self.warnings.append(f"PDF Active Content detected: {keyword}")
        except: pass

    def analyze_office_macros(self):
        if self.data[:4] == b'PK\x03\x04':
            try:
                if zipfile.is_zipfile(self.filepath):
                    with zipfile.ZipFile(self.filepath, 'r') as z:
                        for f in z.namelist():
                            if 'vbaProject.bin' in f or '.bas' in f:
                                self.risk_score += 8
                                self.warnings.append("Office Macro (VBA) Detected in Zip Structure")
                                return
            except: pass
        
        if b'Attribute VB_Name' in self.data:
            self.risk_score += 8
            self.warnings.append("Legacy Office Macro (VBA) Detected")

    def analyze_pe_header(self):
        if self.data[:2] != b'4D5A': return
        try:
            pe_offset = struct.unpack('<I', self.data[0x3C:0x40])[0]
            if pe_offset + 1000 > len(self.data): return # Header outside of buffer
            
            if self.data[pe_offset:pe_offset+4] != b'PE\x00\x00': return
            ts_offset = pe_offset + 8
            timestamp = struct.unpack('<I', self.data[ts_offset:ts_offset+4])[0]
            
            year = datetime.fromtimestamp(timestamp).year
            if year < 1990 or year > 2030:
                self.warnings.append(f"Suspicious Compilation Year: {year} (TimeStomping?)")
                self.risk_score += 3
            else:
                self.indicators.append(f"Compiled: {year}")
                
            header_chunk = self.data[pe_offset:pe_offset+1000]
            suspicious_sections = [b'.upx', b'.themida', b'.vmprotect', b'.aspack']
            for sec in suspicious_sections:
                if sec in header_chunk.lower():
                    self.warnings.append(f"Packed Binary Detected: {sec.decode()}")
                    self.risk_score += 4
        except: pass

    def analyze_metadata(self):
        if self.filename.lower().endswith(('.jpg', '.jpeg', '.tif', '.wav')):
            try:
                # ExifRead reads the file path directly, so it handles large files automatically
                with open(self.filepath, 'rb') as f:
                    tags = exifread.process_file(f, details=False)
                    for tag in tags.keys():
                        if tag in ('Image ImageDescription', 'Image Software', 'Image Artist', 'Image Copyright'):
                            self.hidden_data.append(f"Metadata {tag}: {tags[tag]}")
                        if 'GPS' in tag:
                            self.indicators.append("GPS Location Data Found")
            except: pass

    def analyze_steganography_overlay(self, mime):
        eof_signatures = {
            "image/jpeg": b"\xFF\xD9",
            "image/png": b"\x49\x45\x4E\x44\xAE\x42\x60\x82", 
            "application/zip": None 
        }
        
        # Scan the end of our BUFFER (which corresponds to end of file due to Tail read)
        if mime in eof_signatures and eof_signatures[mime]:
            sig = eof_signatures[mime]
            # Search in the last 1MB of data for performance
            search_area = self.data[-1048576:] if len(self.data) > 1048576 else self.data
            end_offset = search_area.rfind(sig)
            
            if end_offset != -1:
                # Calculate actual bytes remaining after sig in the search area
                actual_end = end_offset + len(sig)
                if actual_end < len(search_area):
                    excess = len(search_area) - actual_end
                    if excess > 100:
                        self.warnings.append(f"[bold red]STEGANOGRAPHY ALERT:[/bold red] {excess} bytes of hidden data found after EOF.")
                        self.risk_score += 5

    def analyze_archives(self):
        # ZipFile module handles large files via streaming automatically
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
                                self.warnings.append(f"Possible Zip Bomb: {f} (Ratio {ratio:.0f}:1)")
                                self.risk_score += 5

                        for ext in suspicious_ext:
                            if f.lower().endswith(ext):
                                self.warnings.append(f"Archive contains executable: {f}")
                                self.risk_score += 3
            except:
                self.warnings.append("Corrupt Archive or Protected Zip")

    def analyze_strings(self):
        try:
            # Decode only the buffer
            text_data = self.data.decode('utf-8', errors='ignore')
            
            patterns = {
                "IPv4": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
                "Email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                "URL": r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                "Bitcoin Wallet": r'\b(bc1|[13])[a-zA-Z0-9]{25,39}\b',
                "Private Key": r'-----BEGIN (RSA|DSA|EC|OPENSSH|PGP) PRIVATE KEY-----',
                "PowerShell Obfuscation": r'(FromBase64String|::Decode|GNwZW|SUVY|IgB8AC|cwB3AGkAdABjAGgA)',
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
                    elif p_name in ["WebShell", "WinAPI (Malware)", "PowerShell Obfuscation"]:
                        self.warnings.append(f"Suspicious {p_name} detected: {unique_matches}")
                        self.risk_score += 4
                    elif p_name == "Private Key":
                        self.warnings.append("CRITICAL: Private Cryptographic Key Found!")
                        self.risk_score += 10
                    else:
                        self.indicators.append(f"{p_name}: {len(matches)} found")

            if found_ips:
                self.indicators.append(f"Public IPs: {', '.join(list(found_ips)[:3])}")

        except Exception: pass

    def quarantine_file(self):
        if self.risk_score >= QUARANTINE_THRESHOLD:
            try:
                new_name = self.filepath + ".dangerous"
                os.rename(self.filepath, new_name)
                self.filename = os.path.basename(new_name)
                self.filepath = new_name
                self.is_quarantined = True
                self.warnings.append(f"[bold red]File Auto-Quarantined to: .dangerous[/]")
            except Exception as e:
                self.warnings.append(f"Quarantine Failed: {e}")

    def run(self):
        # Size Check: Only if strictly greater than limit, but we set limit to 50GB
        if self.size > MAX_FILE_SIZE_LIMIT:
             console.print(f"[red]Skipping {self.filename}: Too massive (>50GB)[/]")
             return

        sha256 = self.get_hashes()
        console.print(f"[cyan]>> Analyzing {escape(self.filename)}...[/cyan]")
        
        self.check_virustotal(sha256)
        mime, desc = get_file_mime(self.filepath, self.data)
        entropy = self.calculate_entropy()
        
        if entropy > 7.4 and "zip" not in mime and "image" not in mime:
             self.warnings.append(f"High Entropy ({entropy:.2f}): Likely Packed/Encrypted payload.")
             self.risk_score += 3

        # Run Modules
        self.analyze_metadata()
        self.analyze_steganography_overlay(mime)
        self.analyze_archives()
        self.analyze_strings()
        self.analyze_pdf_structure()
        self.analyze_office_macros()
        self.analyze_pe_header()

        if any(x in mime for x in ["dosexec", "executable", "x-elf"]):
            self.risk_score += 5
            self.warnings.append(f"File is an Executable Binary ({mime})")

        if re.search(r'\.(exe|bat|sh|vbs|apk)\.[a-z]{3}$', self.filename.lower()):
            self.risk_score += 8
            self.warnings.append("Double Extension Spoofing Detected")

        if self.risk_score >= QUARANTINE_THRESHOLD:
            self.quarantine_file()

        self.print_report(sha256, mime, desc, entropy)

    def print_report(self, sha256, mime, desc, entropy):
        if self.risk_score >= 7:
            color = "red"
            verdict = "DANGEROUS"
            GlobalStats.risky += 1
        elif self.risk_score >= 4:
            color = "yellow"
            verdict = "SUSPICIOUS"
            GlobalStats.risky += 1
        else:
            color = "green"
            verdict = "CLEAN"
            GlobalStats.clean += 1

        info_table = Table(show_header=False, box=None)
        info_table.add_row("Type", f"{mime} ({desc})")
        info_table.add_row("Entropy", f"{entropy:.3f}")
        info_table.add_row("Cloud", self.vt_result)
        
        details = f"[bold {color} size=16]{verdict}[/] (Score: {self.risk_score})"
        
        if self.is_quarantined:
            details += "\n\n[bold white on red] FILE QUARANTINED [/]"

        if self.warnings:
            details += "\n\n[bold red]--- THREATS ---[/]"
            for w in self.warnings: details += f"\n[red]![/] {escape(str(w))}"
            
        if self.hidden_data:
            details += "\n\n[bold magenta]--- HIDDEN DATA/STEGO ---[/]"
            for h in self.hidden_data: details += f"\n[magenta]*[/] {escape(str(h))}"

        if self.indicators:
            details += "\n\n[bold blue]--- INTEL ---[/]"
            for i in self.indicators: details += f"\n[blue]i[/] {escape(str(i))}"

        layout = Layout()
        layout.split_row(
            Layout(Panel(info_table, title="File Info")),
            Layout(Panel(details, title="Analysis Verdict", border_style=color))
        )
        
        console.print(Panel(f"[bold]{escape(self.filename)}[/bold]", style=f"on {color} black" if color=="red" else "bold white"))
        console.print(layout)
        console.print(f"[dim]SHA256: {sha256}[/dim]\n")

# --- Main Loop ---
def main():
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR, exist_ok=True)
        console.print(f"[green]Created folder:[/green] {TARGET_DIR}")
        console.print("[yellow]Put files there to scan![/yellow]")
        return

    files = [f for f in os.listdir(TARGET_DIR) if os.path.isfile(os.path.join(TARGET_DIR, f))]
    
    if not files:
        console.print(f"[yellow]Folder empty: {TARGET_DIR}[/yellow]")
        return

    console.print(f"[bold]Scanning {len(files)} files...[/bold]\n")
    for f in files:
        AdvancedAnalyzer(os.path.join(TARGET_DIR, f)).run()

if __name__ == "__main__":
    main()