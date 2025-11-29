#!/usr/bin/env python3
import os
import sys
import json
import shutil
import subprocess
import requests
import curses
import re
import textwrap
import math
import zipfile

# ----------------------------------------------------------------------
# --- CONSTANTS, PATHS, AND GLOBALS ---
# ----------------------------------------------------------------------

REPO_URL = "https://github.com/dedsec1121fk/DedSec.git"
LOCAL_DIR = "DedSec"
REPO_API_URL = "https://api.github.com/repos/dedsec1121fk/DedSec"

# --- Define fixed absolute paths and folder names ---
ENGLISH_BASE_PATH = "/data/data/com.termux/files/home/DedSec/Scripts"
GREEK_FOLDER_NAME = "Ελληνική Έκδοση"
GREEK_PATH_FULL = os.path.join(ENGLISH_BASE_PATH, GREEK_FOLDER_NAME)
SETTINGS_SCRIPT_PATH = os.path.join(ENGLISH_BASE_PATH, "Settings.py")
BASHRC_PATH = "/data/data/com.termux/files/usr/etc/bash.bashrc"
MOTD_PATH = "/data/data/com.termux/files/usr/etc/motd"

# --- Persistent Language Config ---
# Saves language preference to /data/data/com.termux/files/home/Language.json
HOME_DIR = "/data/data/com.termux/files/home"
LANGUAGE_JSON_PATH = os.path.join(HOME_DIR, "Language.json")
BACKUP_ZIP_PATH = os.path.join(HOME_DIR, "Termux.zip")

# Define hidden folder name/path for Greek (Necessary for language toggle)
HIDDEN_GREEK_FOLDER = "." + GREEK_FOLDER_NAME
HIDDEN_GREEK_PATH = os.path.join(ENGLISH_BASE_PATH, HIDDEN_GREEK_FOLDER)

# --- Markers for Auto-Cleanup (Handles aliases and startup) ---
BASHRC_START_MARKER = "# --- DedSec Menu Startup (Set by Settings.py) ---"
BASHRC_END_MARKER = "# --------------------------------------------------"

# --- Language Path Map ---
LANGUAGE_MAP = {
    ENGLISH_BASE_PATH: 'english',
    GREEK_PATH_FULL: 'greek'
}
CURRENT_DISPLAY_LANGUAGE = None
# ----------------------------------------------------

# --- File Type Icons (TEXT BASED - NO EMOJIS) ---
FOLDER_ICON = "[DIR]"
PYTHON_ICON = "[PY]"
JAVASCRIPT_ICON = "[JS]"
SHELL_ICON = "[SH]"
EXECUTABLE_ICON = "[EXEC]"
GENERIC_SCRIPT_ICON = "[FILE]"
HOME_ICON = "[HOME]"

# --- Language Preference Functions ---
def save_language_preference(language):
    """Saves the selected language to a persistent JSON file."""
    try:
        data = {}
        if os.path.exists(LANGUAGE_JSON_PATH):
            with open(LANGUAGE_JSON_PATH, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        
        data['preferred_language'] = language
        
        with open(LANGUAGE_JSON_PATH, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        pass 

def load_language_preference():
    """Loads the preferred language from the persistent JSON file."""
    if os.path.exists(LANGUAGE_JSON_PATH):
        try:
            with open(LANGUAGE_JSON_PATH, "r") as f:
                data = json.load(f)
                return data.get('preferred_language')
        except Exception:
            return None
    return None

# --- Translation Definitions (NO EMOJIS) ---
GREEK_STRINGS = {
    "Select an option": "Επιλέξτε μια επιλογή",
    "About": "Πληροφορίες",
    "DedSec Project Update": "Ενημέρωση Έργου DedSec",
    "Update Packages & Modules": "Ενημέρωση Πακέτων & Modules",
    "Change Prompt": "Αλλαγή Προτροπής",
    "Change Menu Style": "Αλλαγή Στυλ Μενού",
    "Choose Language/Επιλέξτε Γλώσσα": "Choose Language/Επιλέξτε Γλώσσα",
    "Credits": "Συντελεστές",
    "Uninstall DedSec Project": "Απεγκατάσταση Έργου DedSec",
    "Exit": "Έξοδος",
    "System Information": "Πληροφορίες Συστήματος",
    "The Latest DedSec Project Update": "Η Τελευταία Ενημέρωση του Έργου DedSec",
    "DedSec directory not found": "Ο φάκελος DedSec δεν βρέθηκε",
    "Termux Entire Storage": "Συνολικός Χώρος Αποθήκευσης Termux",
    "DedSec Project Size": "Μέγεθος Έργου DedSec",
    "Hardware Details": "Λεπτομέρειες Υλικού",
    "Internal Storage": "Εσωτερικός Χώρος Αποθήκευσης",
    "Processor": "Επεξεργαστής",
    "Ram": "Μνήμη RAM",
    "Carrier": "Πάροχος Δικτύου",
    "Kernel Version": "Έκδοση Πυρήνα (Kernel)",
    "Android Version": "Έκδοση Android",
    "Device Model": "Μοντέλο Συσκευής",
    "Manufacturer": "Κατασκευαστής",
    "Uptime": "Χρόνος Λειτουργίας",
    "Battery": "Μπαταρία",
    "Not available": "Μη διαθέσιμο",
    "User": "Χρήστης",
    "Prompt Username": "Όνομα Χρήστη για την Προτροπή",
    "Username cannot be empty. Please enter a valid username.": "Το Όνομα Χρήστη δεν μπορεί να είναι κενό. Παρακαλώ εισάγετε ένα έγκυρο όνομα.",
    "Changing Prompt...": "Αλλαγή Προτροπής...",
    "Customizations applied successfully!": "Οι προσαρμογές εφαρμόστηκαν επιτυχώς!",
    "Choose Menu Style": "Επιλέξτε Στυλ Μενού",
    "List Style": "Στυλ Λίστας",
    "Grid Style": "Στυλ Πλέγματος",
    "Choose By Number": "Επιλογή με Αριθμό",
    "No menu style selected. Returning to settings menu...": "Δεν επιλέχθηκε στυλ μενού. Επιστρέφοντας στο μενού ρυθμίσεων...",
    "Menu style changed to": "Το στυλ μενού άλλαξε σε",
    "Bash configuration updated.": "Η διαμόρφωση του Bash ενημερώθηκε.",
    "Please restart Termux for changes to take full effect.": "Παρακαλώ επανεκκινήστε το Termux για να εφαρμοστούν πλήρως οι αλλαγές.",
    "Language set to": "Η γλώσσα ορίστηκε σε",
    "Directory": "Ο φάκελος",
    "is now hidden (renamed to": "είναι πλέον κρυφός (μετονομάστηκε σε",
    "is now visible.": "είναι πλέον ορατός.",
    "Error hiding directory": "Σφάλμα απόκρυψης φακέλου",
    "Error unhiding directory": "Σφάλμα εμφάνισης φακέλου",
    "No language selected. Returning to settings menu...": "Δεν επιλέχθηκε γλώσσα. Επιστρέφοντας στο μενού ρυθμίσεων...",
    "No selection made. Exiting.": "Δεν έγινε επιλογή. Έξοδος.",
    "back": "πίσω",
    "Go Back": "Πίσω",
    "No items found in this folder.": "Δεν βρέθηκαν στοιχεία σε αυτόν τον φάκελο.",
    "Error running fzf": "Σφάλμα κατά την εκτέεση του fzf",
    "Invalid selection. Exiting.": "Μη έγκυρη επιλογή. Έξοδος.",
    "Script terminated by KeyboardInterrupt. Exiting gracefully...": "Το script τερματίστηκε λόγω KeyboardInterrupt. Έξοδος...",
    "Cloning repository...": "Κλωνοποίηση αποθετηρίου...",
    "GitHub repository size": "Μέγεθος αποθετηρίου GitHub",
    "DedSec found! Forcing a full update...": "Το DedSec βρέθηκε! Επιβολή πλήρους ενημέρωσης...",
    "Update applied. DedSec Project Size": "Ενημέρωση εφαρμόστηκε. Μέγεθος Έργου DedSec",
    "No available update found.": "Δεν βρέθηκε διαθέσιμη ενημέρωση.",
    "Cloned new DedSec repository. DedSec Project Size": "Κλωνοποιήθηκε νέο αποθετήριο DedSec. Μέγεθος Έργου DedSec",
    "Update process completed successfully!": "Η διαδικασία ενημέρωσης ολοκληρώθηκε επιτυχώς!",
    "Unable to fetch repository size": "Αδυναμία λήψης μεγέθους αποθετηρίου",
    "Installing Python packages and modules...": "Εγκατάσταση πακέτων και modules Python...",
    "Installing Termux packages and modules...": "Εγκατάσταση πακέτων και modules Termux...",
    "Packages and Modules update process completed successfully!": "Η διαδικασία ενημέρωσης πακέτων και modules ολοκληρώθηκε επιτυχώς!",
    "Press Enter to return to the settings menu...": "Πατήστε Enter για επιστροφή στο μενού ρυθμίσεων...",
    "Exiting...": "Γίνεται έξοδος...",
    "Unknown menu style. Use 'list' or 'grid' or 'number'.": "Άγνωστο στυλ μενού. Χρησιμοποιήστε 'list', 'grid' ή 'number'.",
    "Invalid selection or non-executable script. Exiting.": "Μη έγκυρη επιλογή ή μη εκτελέσιμο script. Έξοδος.",
    "This will restore backed-up files and remove the DedSec project. ARE YOU SURE? (y/n): ": "Αυτό θα επαναφέρει αρχεία από το αντίγραφο ασφαλείας και θα αφαιρέσει το έργο DedSec. ΕΙΣΤΕ ΣΙΓΟΥΡΟΙ; (y/n): ",
    "Uninstallation cancelled.": "Η απεγκατάσταση ακυρώθηκε.",
    "Restoring files from Termux.zip...": "Επαναφορά αρχείων από το Termux.zip...",
    "Restored bash.bashrc and motd from backup.": "Επαναφέρθηκαν τα bash.bashrc και motd από το αντίγραφο ασφαλείας.",
    "Removed Termux.zip backup.": "Το αντίγραφο ασφαλείας Termux.zip αφαιρέθηκε.",
    "Error restoring from backup: ": "Σφάλμα κατά την επαναφορά από αντίγραφο ασφαλείας: ",
    "Backup Termux.zip not found. Cleaning up configuration manually...": "Το αντίγραφο ασφαλείας Termux.zip δεν βρέθηκε. Εκκαθάριση διαμόρφωσης μη αυτόματα...",
    "Removing language configuration...": "Αφαίρεση διαμόρφωσης γλώσσας...",
    "Configuration files have been reset.": "Έγινε επαναφορά των αρχείων διαμόρφωσης.",
    "To complete the uninstallation, please exit this script and run the following command:": "Για να ολοκληρώσετε την απεγκατάσταση, βγείτε από αυτό το script και εκτελέστε την ακόλουθη εντολή:",
    "Creating one-time configuration backup to Termux.zip...": "Δημιουργία εφάπαξ αντιγράφου ασφαλείας διαμόρφωσης στο Termux.zip...",
    "Backup successful.": "Το αντίγραφο ασφαλείας δημιουργήθηκε με επιτυχία.",
    "Warning: Failed to create backup: ": "Προειδοποίηση: Αποτυχία δημιουργίας αντιγράφου ασφαλείας: ",
    "Home Scripts": "Scripts Αρχικής",
    "Enter the number of your choice: ": "Εισάγετε τον αριθμό της επιλογής σας: ",
    "Invalid selection. Please try again.": "Μη έγκυρη επιλογή. Παρακαλώ προσπαθήστε ξανά.",
}

# ------------------------------
# Translation Helpers
# ------------------------------
def get_current_language_path():
    """Detects the currently configured startup path from bash.bashrc."""
    try:
        with open(BASHRC_PATH, "r") as f:
            lines = f.readlines()
    except Exception:
        return ENGLISH_BASE_PATH # Default

    start_marker = BASHRC_START_MARKER
    end_marker = BASHRC_END_MARKER
    in_block = False
    
    for line in lines:
        if start_marker in line:
            in_block = True
            continue
        if end_marker in line:
            in_block = False
            break
        
        if in_block and line.strip().startswith('cd '):
            match = re.search(r'cd\s+"([^"]+)"', line)
            if match:
                return match.group(1).strip()
                
    return ENGLISH_BASE_PATH # Default

def get_current_display_language():
    global CURRENT_DISPLAY_LANGUAGE
    lang_from_json = load_language_preference()
    if lang_from_json in ['english', 'greek']:
        CURRENT_DISPLAY_LANGUAGE = lang_from_json
        return CURRENT_DISPLAY_LANGUAGE
    
    current_path = get_current_language_path()
    CURRENT_DISPLAY_LANGUAGE = LANGUAGE_MAP.get(current_path, 'english')
    return CURRENT_DISPLAY_LANGUAGE

def _(text):
    current_lang = get_current_display_language() 
    if current_lang == 'greek':
        return GREEK_STRINGS.get(text, text)
    return text

# ------------------------------

# --- File Type Detection Helper ---
def get_file_icon(filename, full_path):
    """Returns the appropriate icon for a file based on its type."""
    if os.path.isdir(full_path):
        return FOLDER_ICON
    
    if filename.endswith('.py'):
        return PYTHON_ICON
    elif filename.endswith('.js') or filename.endswith('.javascript'):
        return JAVASCRIPT_ICON
    elif filename.endswith('.sh') or filename.endswith('.bash'):
        return SHELL_ICON
    elif os.access(full_path, os.X_OK):
        return EXECUTABLE_ICON
    else:
        return GENERIC_SCRIPT_ICON

def format_display_name(filename, full_path):
    """Formats the display name with icons - only at the start."""
    icon = get_file_icon(filename, full_path)
    return f"{icon} {filename}"

# --- Utility Functions ---

def run_command(command, cwd=None):
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip()

def get_termux_info():
    if shutil.which("termux-info"):
        out, _err = run_command("termux-info -j")
        try:
            info = json.loads(out)
            termux_version = info.get("termux_version", info.get("app_version", "Unknown"))
            termux_api_version = info.get("termux_api_version", "Unknown")
        except Exception:
            termux_version = "Unknown"
            termux_api_version = "Unknown"
    else:
        termux_version = "Unknown"
        termux_api_version = "Unknown"
    termux_style_version = "Default"
    return termux_version, termux_api_version, termux_style_version

def get_latest_dedsec_update(path):
    if path and os.path.isdir(path):
        stdout, _err = run_command("git log -1 --format=%cd", cwd=path)
        return stdout if stdout else _("Not available")
    return _("DedSec directory not found")

def find_dedsec():
    search_cmd = "find ~ -type d -name 'DedSec' 2>/dev/null"
    output, _err = run_command(search_cmd)
    paths = output.split("\n") if output else []
    return paths[0] if paths else None

def get_github_repo_size():
    try:
        response = requests.get(REPO_API_URL)
        if response.status_code == 200:
            size_kb = response.json().get('size', 0)
            return f"{size_kb / 1024:.2f} MB"
    except Exception:
        pass
    return _("Unable to fetch repository size")

def get_termux_size():
    termux_root = "/data/data/com.termux"
    if os.path.exists(termux_root):
        out, _err = run_command(f"du -sh {termux_root}")
        size = out.split()[0] if out else "Unknown"
        return size
    else:
        home_dir = os.environ.get("HOME", "~")
        out, _err = run_command(f"du -sh {home_dir}")
        size = out.split()[0] if out else "Unknown"
        return size

def get_dedsec_size(path):
    if path and os.path.isdir(path):
        out, _err = run_command(f"du -sh {path}")
        size = out.split()[0] if out else "Unknown"
        return size
    return _("DedSec directory not found")

def clone_repo():
    print(f"[+] DedSec not found. {_('Cloning repository...')}")
    run_command(f"git clone {REPO_URL}")
    return os.path.join(os.getcwd(), LOCAL_DIR)

def force_update_repo(existing_path):
    if existing_path:
        print(f"[+] DedSec found! {_('Forcing a full update...')}")
        run_command("git fetch --all", cwd=existing_path)
        run_command("git reset --hard origin/main", cwd=existing_path)
        run_command("git clean -fd", cwd=existing_path)
        run_command("git pull", cwd=existing_path)
        print(f"[+] Repository fully updated, including README and all other files.")

def update_dedsec():
    repo_size = get_github_repo_size()
    print(f"[+] {_('GitHub repository size')}: {repo_size}")
    existing_dedsec_path = find_dedsec()
    if existing_dedsec_path:
        run_command("git fetch", cwd=existing_dedsec_path)
        behind_count, _err = run_command("git rev-list HEAD..origin/main --count", cwd=existing_dedsec_path)
        try:
            behind_count = int(behind_count)
        except Exception:
            behind_count = 0
        if behind_count > 0:
            force_update_repo(existing_dedsec_path)
            dedsec_size = get_dedsec_size(existing_dedsec_path)
            print(f"[+] {_('Update applied. DedSec Project Size')}: {dedsec_size}")
        else:
            print(_("No available update found."))
    else:
        existing_dedsec_path = clone_repo()
        dedsec_size = get_dedsec_size(existing_dedsec_path)
        print(f"[+] {_('Cloned new DedSec repository. DedSec Project Size')}: {dedsec_size}")
    print(f"[+] {_('Update process completed successfully')}!")
    return existing_dedsec_path

def get_internal_storage():
    df_out, _err = run_command("df -h /data")
    lines = df_out.splitlines()
    if len(lines) >= 2:
        fields = lines[1].split()
        return fields[1]
    return "Unknown"

def get_processor_info():
    cpuinfo, _err = run_command("cat /proc/cpuinfo")
    for line in cpuinfo.splitlines():
        if "Hardware" in line:
            return line.split(":", 1)[1].strip()
        if "Processor" in line:
            return line.split(":", 1)[1].strip()
    return "Unknown"

def get_ram_info():
    try:
        meminfo, _err = run_command("cat /proc/meminfo")
        for line in meminfo.splitlines():
            if "MemTotal" in line:
                parts = line.split()
                if len(parts) >= 2:
                    mem_total_kb = parts[1]
                    try:
                        mem_mb = int(mem_total_kb) / 1024
                        return f"{mem_mb:.2f} MB"
                    except Exception:
                        return parts[1] + " kB"
        return "Unknown"
    except Exception:
        return "Unknown"

def get_carrier():
    carrier, _err = run_command("getprop gsm.operator.alpha")
    if not carrier:
        carrier, _err = run_command("getprop ro.cdma.home.operator.alpha")
    return carrier if carrier else "Unknown"

def get_battery_info():
    if shutil.which("termux-battery-status"):
        out, _err = run_command("termux-battery-status")
        try:
            info = json.loads(out)
            level = info.get("percentage", "Unknown")
            status = info.get("status", "Unknown")
            return f"{_('Battery')}: {level}% ({status})"
        except Exception:
            return f"{_('Battery')}: {_('Unknown')}"
    else:
        return f"{_('Battery')}: {_('Not available')}"

def get_hardware_details():
    internal_storage = get_internal_storage()
    processor = get_processor_info()
    ram = get_ram_info()
    carrier = get_carrier()
    kernel_version, _err = run_command("uname -r")
    android_version, _err = run_command("getprop ro.build.version.release")
    device_model, _err = run_command("getprop ro.product.model")
    manufacturer, _err = run_command("getprop ro.product.manufacturer")
    uptime, _err = run_command("uptime -p")
    battery = get_battery_info()
    
    details = (
        f"{_('Internal Storage')}: {internal_storage}\n"
        f"{_('Processor')}: {processor}\n"
        f"{_('Ram')}: {ram}\n"
        f"{_('Carrier')}: {carrier}\n"
        f"{_('Kernel Version')}: {kernel_version}\n"
        f"{_('Android Version')}: {android_version}\n"
        f"{_('Device Model')}: {device_model}\n"
        f"{_('Manufacturer')}: {manufacturer}\n"
        f"{_('Uptime')}: {uptime}\n"
        f"{battery}"
    )
    return details

def get_user():
    output, _err = run_command("whoami")
    return output if output else "Unknown"

def show_about():
    print(f"=== {_('System Information')} ===")
    dedsec_path = find_dedsec()
    latest_update = get_latest_dedsec_update(dedsec_path) if dedsec_path else _("DedSec directory not found")
    print(f"{_('The Latest DedSec Project Update')}: {latest_update}")
    termux_storage = get_termux_size()
    print(f"{_('Termux Entire Storage')}: {termux_storage}")
    dedsec_size = get_dedsec_size(dedsec_path) if dedsec_path else _("DedSec directory not found")
    print(f"{_('DedSec Project Size')}: {dedsec_size}")
    print(f"\n{_('Hardware Details')}:")
    print(get_hardware_details())
    user = get_user()
    print(f"\n{_('User')}: {user}")

def show_credits():
    credits = f"""
=======================================
                {_('Credits').upper()}
=======================================
Creator:dedsec1121fk
Art Artist:Christina Chatzidimitriou
Technical Help:lamprouil, UKI_hunter
=======================================
"""
    print(credits)

# ------------------------------
# Remove MOTD (if exists)
# ------------------------------
def remove_motd():
    etc_path = "/data/data/com.termux/files/usr/etc"
    motd_path = os.path.join(etc_path, "motd")
    if os.path.exists(motd_path):
        os.remove(motd_path)

# ------------------------------
# Change Prompt
# ------------------------------
def modify_bashrc():
    etc_path = "/data/data/com.termux/files/usr/etc"
    os.chdir(etc_path)
    username = input(f"{_('Prompt Username')}: ").strip()
    while not username:
        print(_("Username cannot be empty. Please enter a valid username."))
        username = input(f"{_('Prompt Username')}: ").strip()
    with open("bash.bashrc", "r") as bashrc_file:
        lines = bashrc_file.readlines()

    # New PS1 format
    new_ps1 = (
        f"PS1='\\[\\e[1;36m\\]\\D{{%d/%m/%Y}}-[\\A]-(\\[\\e[1;34m\\]{username}\\[\\e[0m\\])-(\\[\\e[1;33m\\]\\W\\[\\e[0m\\]) : '\n"
    )
    
    with open("bash.bashrc", "w") as bashrc_file:
        ps1_replaced = False
        for line in lines:
            if "PS1=" in line:
                bashrc_file.write(new_ps1)
                ps1_replaced = True
            else:
                bashrc_file.write(line)
        
        if not ps1_replaced:
            bashrc_file.write(new_ps1)


def change_prompt():
    print(f"\n[+] {_('Changing Prompt...')} \n")
    remove_motd()
    modify_bashrc()
    print(f"\n[+] {_('Customizations applied successfully! ')}")

# ------------------------------
# Update bash.bashrc Aliases and Startup
# ------------------------------

def cleanup_bashrc():
    """Removes all DedSec-related blocks and aliases from bash.bashrc."""
    try:
        with open(BASHRC_PATH, "r") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {BASHRC_PATH}: {e}")
        return False

    filtered_lines = []
    regex_pattern = re.compile(r"(cd\s+.*DedSec/Scripts.*python3\s+.*Settings\.py\s+--menu.*|alias\s+(m|e|g)=.*cd\s+.*DedSec/Scripts.*)")
    
    in_marked_block = False

    for line in lines:
        if BASHRC_START_MARKER in line:
            in_marked_block = True
            continue
        if BASHRC_END_MARKER in line:
            in_marked_block = False
            continue
        
        if in_marked_block:
            continue
            
        if not regex_pattern.search(line):
            filtered_lines.append(line)
    
    try:
        with open(BASHRC_PATH, "w") as f:
            f.writelines(filtered_lines)
        return True
    except Exception as e:
        print(f"Error writing to {BASHRC_PATH}: {e}")
        return False

def update_bashrc(current_language_path, current_style):
    try:
        with open(BASHRC_PATH, "r") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {BASHRC_PATH}: {e}")
        return

    filtered_lines = []
    regex_pattern = re.compile(r"(cd\s+.*DedSec/Scripts.*python3\s+.*Settings\.py\s+--menu.*|alias\s+(m|e|g)=.*cd\s+.*DedSec/Scripts.*)")
    
    in_marked_block = False

    for line in lines:
        if BASHRC_START_MARKER in line:
            in_marked_block = True
            continue
        if BASHRC_END_MARKER in line:
            in_marked_block = False
            continue
        
        if in_marked_block:
            continue
            
        if not regex_pattern.search(line):
            filtered_lines.append(line)

    # The new startup command (auto-runs on Termux start)
    # Style can be list, grid, or number
    new_startup = f"cd \"{current_language_path}\" && python3 \"{SETTINGS_SCRIPT_PATH}\" --menu {current_style}\n"
    
    alias_to_add = ""
    if current_language_path == ENGLISH_BASE_PATH:
        alias_to_add = f"alias e='cd \"{ENGLISH_BASE_PATH}\" && python3 \"{SETTINGS_SCRIPT_PATH}\" --menu {current_style}'\n"
    elif current_language_path == GREEK_PATH_FULL:
        alias_to_add = f"alias g='cd \"{GREEK_PATH_FULL}\" && python3 \"{SETTINGS_SCRIPT_PATH}\" --menu {current_style}'\n"

    filtered_lines.append("\n" + BASHRC_START_MARKER + "\n")
    filtered_lines.append(new_startup)
    
    if alias_to_add:
        filtered_lines.append(alias_to_add)
        
    filtered_lines.append(BASHRC_END_MARKER + "\n")
    
    try:
        with open(BASHRC_PATH, "w") as f:
            f.writelines(filtered_lines)
    except Exception as e:
        print(f"Error writing to {BASHRC_PATH}: {e}")

def get_current_menu_style():
    """Detects the current menu style setting from bash.bashrc."""
    try:
        with open(BASHRC_PATH, "r") as f:
            content = f.read()
    except Exception:
        return 'list'

    if '--menu grid' in content:
        return 'grid'
    if '--menu number' in content:
        return 'number'
    return 'list'

# ------------------------------
# Change Menu Style
# ------------------------------
def choose_menu_style(stdscr):
    curses.curs_set(0)
    options = [ _("List Style"), _("Grid Style"), _("Choose By Number")]
    current = 0
    
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        title = _("Choose Menu Style")
        stdscr.addstr(1, width // 2 - len(title) // 2, title)
        
        for idx, option in enumerate(options):
            x = width // 2 - len(option) // 2
            y = height // 2 - len(options) // 2 + idx
            if idx == current:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(y, x, option)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, option)
        
        stdscr.refresh()
        key = stdscr.getch()
        
        if key == curses.KEY_UP and current > 0:
            current -= 1
        elif key == curses.KEY_DOWN and current < len(options) - 1:
            current += 1
        elif key in [10, 13]:
            if current == 0: return "list"
            if current == 1: return "grid"
            if current == 2: return "number"
        elif key in [ord('q'), ord('Q')]:
            return None

def change_menu_style():
    style = curses.wrapper(choose_menu_style)
    if style is None:
        print(_("No menu style selected. Returning to settings menu..."))
        return
        
    current_path = get_current_language_path()
    
    # Update bashrc with new style but same path
    update_bashrc(current_path, style)
    
    print(f"\n[+] {_('Menu style changed to')} {style.capitalize()} {_('Style')}. {_('Bash configuration updated.')}")
    print(f"[{_('Please restart Termux for changes to take full effect')}]")

# ------------------------------
# Choose Language
# ------------------------------
def choose_language(stdscr):
    curses.curs_set(0)
    options = ["English", "Ελληνικά"]
    current = 0
    
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        title = _("Choose Language/Επιλέξτε Γλώσσα")
        stdscr.addstr(1, width // 2 - len(title) // 2, title)
        
        for idx, option in enumerate(options):
            x = width // 2 - len(option) // 2
            y = height // 2 - len(options) // 2 + idx
            if idx == current:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(y, x, option)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, option)
        
        stdscr.refresh()
        key = stdscr.getch()
        
        if key == curses.KEY_UP and current > 0:
            current -= 1
        elif key == curses.KEY_DOWN and current < len(options) - 1:
            current += 1
        elif key in [10, 13]:
            return "english" if current == 0 else "greek"
        elif key in [ord('q'), ord('Q')]:
            return None

def change_language():
    language = curses.wrapper(choose_language)
    if language is None:
        print(_("No language selected. Returning to settings menu..."))
        return

    save_language_preference(language)
    global CURRENT_DISPLAY_LANGUAGE
    CURRENT_DISPLAY_LANGUAGE = language

    if language == 'english':
        if os.path.isdir(GREEK_PATH_FULL):
            try:
                os.rename(GREEK_PATH_FULL, HIDDEN_GREEK_PATH)
                print(f"[+] {_('Directory')} '{GREEK_FOLDER_NAME}' {_('is now hidden (renamed to')} '{HIDDEN_GREEK_FOLDER}').")
            except OSError as e:
                print(f"{_('Error hiding directory')}: {e}")
        target_path = ENGLISH_BASE_PATH
    
    elif language == 'greek':
        if os.path.isdir(HIDDEN_GREEK_PATH):
            try:
                os.rename(HIDDEN_GREEK_PATH, GREEK_PATH_FULL)
                print(f"[+] {_('Directory')} '{GREEK_FOLDER_NAME}' {_('is now visible.')}")
            except OSError as e:
                print(f"{_('Error unhiding directory')}: {e}")
        
        if not os.path.exists(GREEK_PATH_FULL):
             os.makedirs(GREEK_PATH_FULL)
             
        target_path = GREEK_PATH_FULL

    current_style = get_current_menu_style()
    update_bashrc(target_path, current_style)
    
    print(f"\n[+] {_('Language set to')} {language.capitalize()}. {_('Bash configuration updated.')}")
    print(f"[{_('Please restart Termux for changes to take full effect')}]")

# ------------------------------
# Helper for List Menu
# ------------------------------
def browse_directory_list_menu(current_path, base_path):
    items = []
    listing_dir = current_path
    go_back_text = f".. ({_('Go Back')})"

    if os.path.abspath(current_path) == os.path.abspath(HOME_DIR):
        items.append(go_back_text)
        listing_dir = HOME_DIR
    elif os.path.abspath(current_path) == os.path.abspath(base_path):
        items.append(f"{HOME_ICON} {_('Home Scripts')}")
        listing_dir = base_path
    else:
        items.append(go_back_text)
        listing_dir = current_path

    
    for entry in sorted(os.listdir(listing_dir)):
        if entry.startswith('.'):
            continue
            
        full_path = os.path.join(listing_dir, entry)
        
        if os.path.isdir(full_path):
            display_name = format_display_name(entry, full_path)
            items.append(display_name)
        elif os.path.isfile(full_path):
             if entry == "Settings.py" and full_path == SETTINGS_SCRIPT_PATH:
                 display_name = format_display_name(entry, full_path)
                 items.append(display_name)
                 continue
             
             if os.access(full_path, os.X_OK) or entry.endswith(".py") or entry.endswith(".sh"):
                 display_name = format_display_name(entry, full_path)
                 items.append(display_name)
    
    if not items:
        pass

    input_text = "\n".join(items)
    try:
        result = subprocess.run("fzf", input=input_text, shell=True, capture_output=True, text=True)
        selected = result.stdout.strip()
    except Exception as e:
        print(f"{_('Error running fzf')}: {e}")
        return None
    
    if not selected:
        return None
        
    if selected.startswith(".."):
        return "back"
    
    if selected == f"{HOME_ICON} {_('Home Scripts')}":
        return "go_home"
    
    # Extract the actual filename by removing the icon and spaces
    # Format: ICON name
    parts = selected.split(' ', 1)
    if len(parts) >= 2:
        actual_name = parts[1]
    else:
        actual_name = selected
        
    return os.path.join(listing_dir, actual_name)

# ------------------------------
# Integrated List Menu
# ------------------------------
def run_list_menu():
    base_path = os.getcwd()
    current_path = base_path
    while True:
        selected = browse_directory_list_menu(current_path, base_path)
        
        if selected is None:
            print(_("No selection made. Exiting."))
            return
            
        if selected == "back":
            if os.path.abspath(current_path) == os.path.abspath(HOME_DIR):
                current_path = base_path
            else:
                parent = os.path.dirname(current_path)
                if os.path.abspath(parent).startswith(os.path.abspath(base_path)):
                    current_path = parent
                else:
                    current_path = base_path
            continue
        
        if selected == "go_home":
            current_path = HOME_DIR
            continue
            
        if os.path.isdir(selected):
            current_path = selected
            continue
            
        elif os.path.isfile(selected):
            command = ""
            
            if os.path.abspath(current_path) == os.path.abspath(HOME_DIR):
                file_name = os.path.basename(selected)
                if file_name.endswith(".py"):
                    command = f"cd \"{HOME_DIR}\" && python3 \"{file_name}\""
                elif file_name.endswith(".sh"):
                    command = f"cd \"{HOME_DIR}\" && bash \"{file_name}\""
                elif os.access(selected, os.X_OK):
                    command = f"cd \"{HOME_DIR}\" && ./{file_name}"
            else:
                rel_path = os.path.relpath(selected, base_path)
                if rel_path.endswith(".py"):
                    command = f"python3 \"{rel_path}\""
                elif rel_path.endswith(".sh"):
                    command = f"bash \"{rel_path}\""
                elif os.access(selected, os.X_OK):
                    command = f"./\"{rel_path}\""
            
            if command:
                ret = os.system(command)
                
                if (ret >> 8) == 2:
                    print(_("\nScript terminated by KeyboardInterrupt. Exiting gracefully..."))
                    sys.exit(0)
                
                return
            else:
                print(_("Invalid selection or non-executable script. Exiting."))
                return
        else:
            print(_("Invalid selection. Exiting."))
            return

# ------------------------------
# Integrated Number Menu
# ------------------------------
def run_number_menu():
    base_path = os.getcwd()
    current_path = base_path
    
    while True:
        os.system("clear")
        items = []
        listing_dir = current_path
        
        # Determine items to show
        if os.path.abspath(current_path) == os.path.abspath(HOME_DIR):
            listing_dir = HOME_DIR
            items.append((".. (" + _("Go Back") + ")", "back"))
        elif os.path.abspath(current_path) == os.path.abspath(base_path):
            listing_dir = base_path
            items.append((f"{HOME_ICON} {_('Home Scripts')}", "go_home"))
        else:
            listing_dir = current_path
            items.append((".. (" + _("Go Back") + ")", "back"))

        try:
            entries = sorted(os.listdir(listing_dir))
        except OSError:
            entries = []

        for entry in entries:
            if entry.startswith('.'): continue
            full_path = os.path.join(listing_dir, entry)
            
            if os.path.isdir(full_path):
                display_name = format_display_name(entry, full_path)
                items.append((display_name, full_path))
            elif os.path.isfile(full_path):
                if entry == "Settings.py" and full_path == SETTINGS_SCRIPT_PATH:
                    display_name = format_display_name(entry, full_path)
                    items.append((display_name, full_path))
                    continue
                if os.access(full_path, os.X_OK) or entry.endswith(".py") or entry.endswith(".sh"):
                    display_name = format_display_name(entry, full_path)
                    items.append((display_name, full_path))
        
        # Display Menu
        print(f"[{current_path}]\n")
        for i, (name, path) in enumerate(items):
            print(f"{i + 1}. {name}")
        
        print(f"\n0. {_('Exit')}")
        
        try:
            choice_str = input(f"\n{_('Enter the number of your choice: ')}").strip()
            if not choice_str: continue
            choice = int(choice_str)
        except ValueError:
            print(_("Invalid selection. Please try again."))
            input()
            continue
        
        if choice == 0:
            print(_("Exiting..."))
            return

        if 1 <= choice <= len(items):
            selected_name, selected_path = items[choice - 1]
            
            if selected_path == "back":
                if os.path.abspath(current_path) == os.path.abspath(HOME_DIR):
                    current_path = base_path
                else:
                    parent = os.path.dirname(current_path)
                    if os.path.abspath(parent).startswith(os.path.abspath(base_path)):
                        current_path = parent
                    else:
                        current_path = base_path
                continue

            if selected_path == "go_home":
                current_path = HOME_DIR
                continue

            if os.path.isdir(selected_path):
                current_path = selected_path
                continue
            
            if os.path.isfile(selected_path):
                command = ""
                if os.path.abspath(current_path) == os.path.abspath(HOME_DIR):
                    file_name = os.path.basename(selected_path)
                    if file_name.endswith(".py"):
                        command = f"cd \"{HOME_DIR}\" && python3 \"{file_name}\""
                    elif file_name.endswith(".sh"):
                        command = f"cd \"{HOME_DIR}\" && bash \"{file_name}\""
                    elif os.access(selected_path, os.X_OK):
                        command = f"cd \"{HOME_DIR}\" && ./{file_name}"
                else:
                    rel_path = os.path.relpath(selected_path, base_path)
                    if rel_path.endswith(".py"):
                        command = f"python3 \"{rel_path}\""
                    elif rel_path.endswith(".sh"):
                        command = f"bash \"{rel_path}\""
                    elif os.access(selected_path, os.X_OK):
                        command = f"./\"{rel_path}\""
                
                if command:
                    ret = os.system(command)
                    if (ret >> 8) == 2:
                        print(_("\nScript terminated by KeyboardInterrupt. Exiting gracefully..."))
                        sys.exit(0)
                    return
                else:
                    print(_("Invalid selection or non-executable script."))
                    input()
        else:
            print(_("Invalid selection. Please try again."))
            input()

# ------------------------------
# Helper for Grid Menu
# ------------------------------
def list_directory_entries(path, base_path):
    entries = []
    listing_dir = path
    go_back_text = f".. ({_('Go Back')})"
    
    if os.path.abspath(path) == os.path.abspath(HOME_DIR):
        entries.append((go_back_text, "back"))
        listing_dir = HOME_DIR
    elif os.path.abspath(path) == os.path.abspath(base_path):
        entries.append((f"{HOME_ICON} {_('Home Scripts')}", "go_home"))
        listing_dir = base_path
    else:
        entries.append((go_back_text, "back"))
        listing_dir = path

    
    for entry in sorted(os.listdir(listing_dir)):
        if entry.startswith('.'):
            continue
            
        full_path = os.path.join(listing_dir, entry)
        
        if os.path.isdir(full_path):
            display_name = format_display_name(entry, full_path)
            entries.append((display_name, full_path))
        elif os.path.isfile(full_path):
             if entry == "Settings.py" and full_path == SETTINGS_SCRIPT_PATH:
                 display_name = format_display_name(entry, full_path)
                 entries.append((display_name, full_path))
                 continue
             
             if os.access(full_path, os.X_OK) or entry.endswith(".py") or entry.endswith(".sh"):
                 display_name = format_display_name(entry, full_path)
                 entries.append((display_name, full_path))
    return entries

# ------------------------------
# Integrated Grid Menu
# ------------------------------
def run_grid_menu():
    base_path = os.getcwd()

    def draw_box(stdscr, y, x, height, width, highlight=False):
        color = curses.color_pair(2)
        if highlight:
            color = curses.color_pair(1)
        term_height, term_width = stdscr.getmaxyx()
        if y + height > term_height or x + width > term_width:
            return

        for i in range(x, x + width):
            stdscr.addch(y, i, curses.ACS_HLINE, color)
            stdscr.addch(y + height - 1, i, curses.ACS_HLINE, color)
        for j in range(y, y + height):
            stdscr.addch(j, x, curses.ACS_VLINE, color)
            stdscr.addch(j, x + width - 1, curses.ACS_VLINE, color)
        
        try:
            stdscr.addch(y, x, curses.ACS_ULCORNER, color)
            stdscr.addch(y, x + width - 1, curses.ACS_URCORNER, color)
            stdscr.addch(y + height - 1, x, curses.ACS_LLCORNER, color)
            stdscr.addch(y + height - 1, x + width - 1, curses.ACS_LRCORNER, color)
        except curses.error:
            pass

    def draw_grid_menu(stdscr, friendly_names, num_items):
        curses.curs_set(0)
        stdscr.nodelay(0)
        stdscr.timeout(-1)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_MAGENTA, -1)
        curses.init_pair(3, curses.COLOR_WHITE, -1)
        current_index = 0
        while True:
            stdscr.clear()
            term_height, term_width = stdscr.getmaxyx()
            
            ICON_WIDTH = max(15, term_width // 5)
            ICON_HEIGHT = max(7, term_height // 6)
            max_cols = term_width // ICON_WIDTH
            
            if max_cols == 0:
                ICON_WIDTH = term_width
                max_cols = 1
            
            rows_per_page = (term_height - 1) // ICON_HEIGHT
            total_visible_cells = max_cols * rows_per_page
            
            if total_visible_cells <= 0:
                stdscr.addstr(0, 0, _("Terminal window is too small."))
                stdscr.refresh()
                key = stdscr.getch()
                if key in [ord('q'), ord('Q'), 10, 13]:
                    return None
                continue

            page_start_index = (current_index // total_visible_cells) * total_visible_cells
            page_end_index = min(page_start_index + total_visible_cells, num_items)
            
            prev_page_index = max(0, page_start_index - total_visible_cells)
            next_page_index = min(num_items - 1, page_start_index + total_visible_cells)

            for idx_on_page, actual_index in enumerate(range(page_start_index, page_end_index)):
                i = idx_on_page // max_cols
                j = idx_on_page % max_cols
                y = i * ICON_HEIGHT
                x = j * ICON_WIDTH
                
                if y + ICON_HEIGHT >= term_height - 1:
                    continue

                draw_box(stdscr, y, x, ICON_HEIGHT, ICON_WIDTH, highlight=(actual_index == current_index))
                name = friendly_names[actual_index]
                box_text_width = ICON_WIDTH - 4
                wrapped_lines = textwrap.wrap(name, box_text_width)
                
                total_lines = len(wrapped_lines)
                padding_y = (ICON_HEIGHT - total_lines) // 2
                
                for line_idx, line in enumerate(wrapped_lines):
                    line_y = y + padding_y + line_idx
                    padding_x = (ICON_WIDTH - len(line)) // 2
                    line_x = x + padding_x
                    
                    if line_y < term_height - 1 and line_x < term_width:
                        try:
                            display_line = line[:term_width - line_x]
                            stdscr.addstr(line_y, line_x, display_line, curses.color_pair(3))
                        except curses.error:
                            pass
            
            page_info = f" Page {(current_index // total_visible_cells) + 1} / {math.ceil(num_items / total_visible_cells)} "
            instructions = f"Arrow Keys: Move | P/N: Prev/Next Page | Enter: Select | q: Quit | {page_info}"
            try:
                stdscr.addstr(term_height - 1, 0, instructions[:term_width - 1], curses.color_pair(3))
            except curses.error:
                pass
            
            stdscr.refresh()
            
            key = stdscr.getch()
            
            if key == curses.KEY_UP and current_index - max_cols >= 0:
                current_index -= max_cols
            elif key == curses.KEY_DOWN and current_index + max_cols < num_items:
                current_index += max_cols
            elif key == curses.KEY_LEFT and current_index % max_cols > 0:
                current_index -= 1
            elif key == curses.KEY_RIGHT and (current_index % max_cols) < (max_cols - 1) and (current_index + 1) < num_items:
                current_index += 1
            elif key in [ord('p'), ord('P')]:
                current_index = prev_page_index
            elif key in [ord('n'), ord('N')]:
                current_index = next_page_index
            elif key in [10, 13]:
                return current_index
            elif key in [ord('q'), ord('Q')]:
                return None
            elif key == curses.KEY_RESIZE:
                pass

    current_path = base_path
    while True:
        entries = list_directory_entries(current_path, base_path)
        if not entries and os.path.abspath(current_path) == os.path.abspath(base_path):
            print(_("No items found in this folder."))
            return
        elif not entries:
             current_path = os.path.dirname(current_path)
             continue
             
        friendly_names = [entry[0] for entry in entries]
        
        selected_index = curses.wrapper(lambda stdscr: draw_grid_menu(stdscr, friendly_names, len(friendly_names)))
        
        if selected_index is None:
            print(_("No selection made. Exiting."))
            return
        
        selected_entry = entries[selected_index]
        selected_path = selected_entry[1]

        if selected_path == "back":
            if os.path.abspath(current_path) == os.path.abspath(HOME_DIR):
                current_path = base_path
            else:
                current_path = os.path.dirname(current_path)
            continue
        
        if selected_path == "go_home":
            current_path = HOME_DIR
            continue
            
        if os.path.isdir(selected_path):
            current_path = selected_path
            continue
        
        if os.path.isfile(selected_path):
            command = ""
            if os.path.abspath(current_path) == os.path.abspath(HOME_DIR):
                file_name = os.path.basename(selected_path)
                if file_name.endswith(".py"):
                    command = f"cd \"{HOME_DIR}\" && python3 \"{file_name}\""
                elif file_name.endswith(".sh"):
                    command = f"cd \"{HOME_DIR}\" && bash \"{file_name}\""
                elif os.access(selected_path, os.X_OK):
                    command = f"cd \"{HOME_DIR}\" && ./{file_name}"
            else:
                rel_path = os.path.relpath(selected_path, base_path)
                if rel_path.endswith(".py"):
                    command = f"python3 \"{rel_path}\""
                elif rel_path.endswith(".sh"):
                    command = f"bash \"{rel_path}\""
                elif os.access(selected_path, os.X_OK):
                    command = f"./\"{rel_path}\""
        
            if command:
                ret = os.system(command)
                
                if (ret >> 8) == 2:
                    print(_("\nScript terminated by KeyboardInterrupt. Exiting gracefully..."))
                    sys.exit(0)
                
                return 
            else:
                print(_("Invalid selection or non-executable script. Exiting."))
                return

# ------------------------------
# Update Packages & Modules
# ------------------------------
def update_packages_modules():
    pip_command = "pip install blessed bs4 cryptography flask flask-socketio geopy mutagen phonenumbers pycountry pydub pycryptodome requests werkzeug"
    termux_command = "termux-setup-storage && pkg update -y && pkg upgrade -y && pkg install aapt clang cloudflared curl ffmpeg fzf git jq libffi libffi-dev libxml2 libxslt nano ncurses nodejs openssh openssl openssl-tool proot python rust unzip wget zip termux-api -y"
    print(f"[+] {_('Installing Python packages and modules...')} ")
    run_command(pip_command)
    print(f"[+] {_('Installing Termux packages and modules...')} ")
    run_command(termux_command)
    print(f"[+] {_('Packages and Modules update process completed successfully!')}")

# ------------------------------
# --- Backup and Uninstall ---
# ------------------------------

def create_backup_zip_if_not_exists():
    """Creates a zip backup of original config files on first run."""
    if os.path.exists(BACKUP_ZIP_PATH):
        return 
    
    print(_("Creating one-time configuration backup to Termux.zip..."))
    try:
        with zipfile.ZipFile(BACKUP_ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zf:
            if os.path.exists(BASHRC_PATH):
                zf.write(BASHRC_PATH, arcname=BASHRC_PATH)
            if os.path.exists(MOTD_PATH):
                zf.write(MOTD_PATH, arcname=MOTD_PATH)
        print(_("Backup successful."))
    except Exception as e:
        print(f"{_('Warning: Failed to create backup: ')}{e}")

def uninstall_dedsec():
    """Restores config files from backup and instructs user on final folder removal."""
    print(f"--- {_('Uninstall DedSec Project')} ---")
    confirm = input(_("This will restore backed-up files and remove the DedSec project. ARE YOU SURE? (y/n): ")).lower().strip()
    
    if confirm != 'y':
        print(_("Uninstallation cancelled."))
        return False

    if os.path.exists(BACKUP_ZIP_PATH):
        print(_("Restoring files from Termux.zip..."))
        try:
            with zipfile.ZipFile(BACKUP_ZIP_PATH, 'r') as zf:
                zf.extractall("/")
            print(_("Restored bash.bashrc and motd from backup."))
            os.remove(BACKUP_ZIP_PATH)
            print(_("Removed Termux.zip backup."))
        except Exception as e:
            print(f"{_('Error restoring from backup: ')}{e}")
    else:
        print(_("Backup Termux.zip not found. Cleaning up configuration manually..."))
        cleanup_bashrc()

    if os.path.exists(LANGUAGE_JSON_PATH):
        print(_("Removing language configuration..."))
        os.remove(LANGUAGE_JSON_PATH)

    dedsec_path = find_dedsec()
    if not dedsec_path:
        dedsec_path = os.path.join(HOME_DIR, LOCAL_DIR) 

    print("\n" + "="*40)
    print(" [!] UNINSTALLATION ALMOST COMPLETE [!]")
    print("="*40)
    print(_("Configuration files have been reset."))
    print(_("To complete the uninstallation, please exit this script and run the following command:"))
    print(f"\n    rm -rf \"{dedsec_path}\"\n")
    print(_("Exiting..."))
    
    return True

# ------------------------------
# Settings Menu with Different Styles
# ------------------------------
def run_settings_list_menu():
    """Settings menu using list style (curses)"""
    def menu(stdscr):
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        menu_options = [
            _("About"),
            _("DedSec Project Update"),
            _("Update Packages & Modules"),
            _("Change Prompt"),
            _("Change Menu Style"),
            _("Choose Language/Επιλέξτε Γλώσσα"),
            _("Credits"),
            _("Uninstall DedSec Project"),
            _("Exit")
        ]
        current_row = 0
        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()
            title = _("Select an option")
            stdscr.addstr(1, width // 2 - len(title) // 2, title)
            for idx, option in enumerate(menu_options):
                x = width // 2 - len(option) // 2
                y = height // 2 - len(menu_options) // 2 + idx
                if idx == current_row:
                    stdscr.attron(curses.A_REVERSE)
                    stdscr.addstr(y, x, option)
                    stdscr.attroff(curses.A_REVERSE)
                else:
                    stdscr.addstr(y, x, option)
            stdscr.refresh()
            key = stdscr.getch()
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(menu_options) - 1:
                current_row += 1
            elif key in [curses.KEY_ENTER, 10, 13]:
                return current_row
    
    return curses.wrapper(menu)

def run_settings_grid_menu():
    """Settings menu using grid style"""
    def draw_settings_grid_menu(stdscr, options):
        curses.curs_set(0)
        stdscr.nodelay(0)
        stdscr.timeout(-1)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_MAGENTA, -1)
        curses.init_pair(3, curses.COLOR_WHITE, -1)
        
        current_index = 0
        num_items = len(options)
        
        while True:
            stdscr.clear()
            term_height, term_width = stdscr.getmaxyx()
            
            # Grid layout parameters
            ICON_WIDTH = max(25, term_width // 3)
            ICON_HEIGHT = max(5, term_height // 5)
            max_cols = term_width // ICON_WIDTH
            
            if max_cols == 0:
                ICON_WIDTH = term_width
                max_cols = 1
            
            rows_per_page = (term_height - 2) // ICON_HEIGHT
            total_visible_cells = max_cols * rows_per_page
            
            if total_visible_cells <= 0:
                stdscr.addstr(0, 0, _("Terminal window is too small."))
                stdscr.refresh()
                key = stdscr.getch()
                if key in [ord('q'), ord('Q'), 10, 13]:
                    return None
                continue

            # Draw title
            title = _("Select an option")
            try:
                stdscr.addstr(0, term_width // 2 - len(title) // 2, title, curses.color_pair(3))
            except curses.error:
                pass

            page_start_index = (current_index // total_visible_cells) * total_visible_cells
            page_end_index = min(page_start_index + total_visible_cells, num_items)
            
            # Draw grid items
            for idx_on_page, actual_index in enumerate(range(page_start_index, page_end_index)):
                i = idx_on_page // max_cols
                j = idx_on_page % max_cols
                y = 2 + i * ICON_HEIGHT
                x = j * ICON_WIDTH
                
                if y + ICON_HEIGHT >= term_height - 1:
                    continue

                # Draw box
                for box_i in range(x, x + ICON_WIDTH):
                    if box_i < term_width:
                        try:
                            stdscr.addch(y, box_i, curses.ACS_HLINE, curses.color_pair(2))
                            stdscr.addch(y + ICON_HEIGHT - 1, box_i, curses.ACS_HLINE, curses.color_pair(2))
                        except curses.error:
                            pass
                
                for box_j in range(y, y + ICON_HEIGHT):
                    if box_j < term_height - 1:
                        try:
                            stdscr.addch(box_j, x, curses.ACS_VLINE, curses.color_pair(2))
                            stdscr.addch(box_j, x + ICON_WIDTH - 1, curses.ACS_VLINE, curses.color_pair(2))
                        except curses.error:
                            pass
                
                # Draw corners
                try:
                    stdscr.addch(y, x, curses.ACS_ULCORNER, curses.color_pair(2))
                    stdscr.addch(y, x + ICON_WIDTH - 1, curses.ACS_URCORNER, curses.color_pair(2))
                    stdscr.addch(y + ICON_HEIGHT - 1, x, curses.ACS_LLCORNER, curses.color_pair(2))
                    stdscr.addch(y + ICON_HEIGHT - 1, x + ICON_WIDTH - 1, curses.ACS_LRCORNER, curses.color_pair(2))
                except curses.error:
                    pass

                # Highlight current selection
                if actual_index == current_index:
                    for hi in range(y + 1, y + ICON_HEIGHT - 1):
                        for hj in range(x + 1, x + ICON_WIDTH - 1):
                            if hi < term_height - 1 and hj < term_width - 1:
                                try:
                                    stdscr.addch(hi, hj, ' ', curses.color_pair(1))
                                except curses.error:
                                    pass

                # Draw option text
                option_text = options[actual_index]
                box_text_width = ICON_WIDTH - 4
                wrapped_lines = textwrap.wrap(option_text, box_text_width)
                
                total_lines = len(wrapped_lines)
                padding_y = (ICON_HEIGHT - total_lines) // 2
                
                for line_idx, line in enumerate(wrapped_lines):
                    line_y = y + padding_y + line_idx
                    padding_x = (ICON_WIDTH - len(line)) // 2
                    line_x = x + padding_x
                    
                    if line_y < term_height - 1 and line_x < term_width:
                        try:
                            color = curses.color_pair(1) if actual_index == current_index else curses.color_pair(3)
                            stdscr.addstr(line_y, line_x, line[:term_width - line_x], color)
                        except curses.error:
                            pass
            
            # Draw instructions
            instructions = f"Arrow Keys: Move | Enter: Select | q: Quit"
            try:
                stdscr.addstr(term_height - 1, 0, instructions[:term_width - 1], curses.color_pair(3))
            except curses.error:
                pass
            
            stdscr.refresh()
            
            key = stdscr.getch()
            
            if key == curses.KEY_UP and current_index - max_cols >= 0:
                current_index -= max_cols
            elif key == curses.KEY_DOWN and current_index + max_cols < num_items:
                current_index += max_cols
            elif key == curses.KEY_LEFT and current_index % max_cols > 0:
                current_index -= 1
            elif key == curses.KEY_RIGHT and (current_index % max_cols) < (max_cols - 1) and (current_index + 1) < num_items:
                current_index += 1
            elif key in [10, 13]:
                return current_index
            elif key in [ord('q'), ord('Q')]:
                return None
            elif key == curses.KEY_RESIZE:
                pass

    menu_options = [
        _("About"),
        _("DedSec Project Update"),
        _("Update Packages & Modules"),
        _("Change Prompt"),
        _("Change Menu Style"),
        _("Choose Language/Επιλέξτε Γλώσσα"),
        _("Credits"),
        _("Uninstall DedSec Project"),
        _("Exit")
    ]
    
    return curses.wrapper(lambda stdscr: draw_settings_grid_menu(stdscr, menu_options))

def run_settings_number_menu():
    """Settings menu using number style"""
    menu_options = [
        _("About"),
        _("DedSec Project Update"),
        _("Update Packages & Modules"),
        _("Change Prompt"),
        _("Change Menu Style"),
        _("Choose Language/Επιλέξτε Γλώσσα"),
        _("Credits"),
        _("Uninstall DedSec Project"),
        _("Exit")
    ]
    
    while True:
        os.system("clear")
        print(f"=== {_('Select an option')} ===\n")
        for i, option in enumerate(menu_options):
            print(f"{i + 1}. {option}")
        print(f"\n0. {_('Exit')}")
        
        try:
            choice_str = input(f"\n{_('Enter the number of your choice: ')}").strip()
            if not choice_str:
                continue
            choice = int(choice_str)
        except ValueError:
            print(_("Invalid selection. Please try again."))
            input(_("Press Enter to continue..."))
            continue
        
        if choice == 0:
            return 8  # Exit option
        
        if 1 <= choice <= len(menu_options):
            return choice - 1
        else:
            print(_("Invalid selection. Please try again."))
            input(_("Press Enter to continue..."))

def run_settings_menu():
    """Main settings menu that uses the current menu style"""
    current_style = get_current_menu_style()
    
    if current_style == 'grid':
        selected = run_settings_grid_menu()
    elif current_style == 'number':
        selected = run_settings_number_menu()
    else:  # Default to list
        selected = run_settings_list_menu()
    
    return selected

def main():
    while True:
        selected = run_settings_menu()
        if selected is None:
            print(_("Exiting..."))
            break
            
        os.system("clear")
        if selected == 0:
            show_about()
        elif selected == 1:
            update_dedsec()
        elif selected == 2:
            update_packages_modules()
        elif selected == 3:
            change_prompt()
        elif selected == 4:
            change_menu_style()
        elif selected == 5:
            change_language()
        elif selected == 6:
            show_credits()
        elif selected == 7:
            should_exit = uninstall_dedsec()
            if should_exit:
                break
        elif selected == 8:
            print(_("Exiting..."))
            break
        
        if 'should_exit' not in locals() or not should_exit:
            input(f"\n{_('Press Enter to return to the settings menu...')}")

# ------------------------------
# Entry Point
# ------------------------------
if __name__ == "__main__":
    try:
        # Load language preference at startup
        get_current_display_language()
        
        create_backup_zip_if_not_exists()
        
        if len(sys.argv) > 1 and sys.argv[1] == "--menu":
            if len(sys.argv) > 2:
                current_style = sys.argv[2]
                if current_style == "list":
                    run_list_menu()
                    sys.exit(0)
                elif current_style == "grid":
                    run_grid_menu()
                    sys.exit(0)
                elif current_style == "number":
                    run_number_menu()
                    sys.exit(0)
                else:
                    print(_("Unknown menu style. Use 'list' or 'grid' or 'number'."))
                    main()
            else:
                # If no style specified, use the current style from bashrc
                current_style = get_current_menu_style()
                if current_style == 'list':
                    run_list_menu()
                elif current_style == 'grid':
                    run_grid_menu()
                elif current_style == 'number':
                    run_number_menu()
                else:
                    run_list_menu()  # Default fallback
        else:
            main()
    except KeyboardInterrupt:
        print(_("\nScript terminated by KeyboardInterrupt. Exiting gracefully..."))
        sys.exit(0)