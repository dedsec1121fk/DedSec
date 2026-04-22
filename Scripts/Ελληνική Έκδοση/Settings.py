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
import time
import socket
import hashlib

# ----------------------------------------------------------------------
# --- CONSTANTS, PATHS, AND GLOBALS ---
# ----------------------------------------------------------------------

REPO_URL_SOURCE_1 = "https://github.com/dedsec1121fk/DedSec.git"
REPO_URL_SOURCE_2 = "https://github.com/sal-scar/DedSec.git"
LOCAL_DIR = "DedSec"
REPO_API_URL_SOURCE_1 = "https://api.github.com/repos/dedsec1121fk/DedSec"
REPO_API_URL_SOURCE_2 = "https://api.github.com/repos/sal-scar/DedSec"

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
SUPPRESS_NEXT_AUTOSTART_PATH = os.path.join(HOME_DIR, ".dedsec_skip_autostart_once")

PROJECT_SAVE_SHARED_STORAGE_PATH = "/storage/emulated/0"
PROJECT_SAVE_DOWNLOADS_PATH = os.path.join(PROJECT_SAVE_SHARED_STORAGE_PATH, "Download")
PROJECT_SAVE_ARCHIVE_NAME = "DedSec Project Legacy Save.zip"
PROJECT_SAVE_WORKDIR = os.path.join(HOME_DIR, ".dedsec_project_legacy_save")
PROJECT_SAVE_BUNDLE_DIRNAME = "DedSec Project Legacy Save"
PROJECT_SAVE_SUCCESS_MESSAGE = "A zip with the save of the DedSec Project Legacy is available in your phone downloads."
PROJECT_SAVE_MAX_EXTRA_COPIES = 6
PROJECT_SAVE_EXCLUDED_TOP_LEVEL_DIRS = {"Android", "Download"}
PROJECT_SAVE_APK_SOURCES = [
    {"filename": "F-Droid.apk", "type": "direct", "url": "https://f-droid.org/F-Droid.apk"},
    {"filename": "Termux.apk", "type": "fdroid_package", "package": "com.termux"},
    {"filename": "Termux_API.apk", "type": "fdroid_package", "package": "com.termux.api"},
    {"filename": "Termux_Styling.apk", "type": "fdroid_package", "package": "com.termux.styling"},
]
PROJECT_SAVE_REPOSITORIES = [
    {"folder_name": "DedSec_dedsec1121fk", "url": "https://github.com/dedsec1121fk/DedSec.git"},
    {"folder_name": "dedsec1121fk.github.io", "url": "https://github.com/dedsec1121fk/dedsec1121fk.github.io.git"},
    {"folder_name": "ded-sec_sal-scar", "url": "https://github.com/sal-scar/ded-sec.git"},
    {"folder_name": "DedSec_sal-scar", "url": "https://github.com/sal-scar/DedSec.git"},
]

# --- Sponsors-Only shortcuts ---
SPONSORS_ROOT_NAME = "Sponsors-Only-main"
SPONSORS_ROOT_PATH = os.path.join(HOME_DIR, SPONSORS_ROOT_NAME)
SPONSORS_ENGLISH_FOLDER_NAME = "English Version"
SPONSORS_GREEK_FOLDER_NAME = "Ελληνική Έκδοση"

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


# --- Persistent Menu Autostart Config ---
# Stored in the same Language.json for simplicity/backwards-compatibility.
def save_menu_autostart_preference(enabled: bool):
    """Saves whether the menu should auto-start when Termux opens."""
    try:
        data = {}
        if os.path.exists(LANGUAGE_JSON_PATH):
            with open(LANGUAGE_JSON_PATH, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        data['menu_autostart'] = bool(enabled)
        with open(LANGUAGE_JSON_PATH, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

def load_menu_autostart_preference() -> bool:
    """Loads the menu auto-start preference. Defaults to True."""
    if os.path.exists(LANGUAGE_JSON_PATH):
        try:
            with open(LANGUAGE_JSON_PATH, "r") as f:
                data = json.load(f)
                return bool(data.get('menu_autostart', True))
        except Exception:
            return True
    return True

def enforce_language_folder_visibility():
    """
    Checks the saved language preference and ensures the Greek folder 
    is hidden or visible accordingly before the menu starts.
    """
    preferred_language = load_language_preference()
    
    if preferred_language == 'english':
        # If English is preferred, ensure Greek folder is HIDDEN
        if os.path.isdir(GREEK_PATH_FULL):
            try:
                os.rename(GREEK_PATH_FULL, HIDDEN_GREEK_PATH)
            except OSError:
                pass
    elif preferred_language == 'greek':
        # If Greek is preferred, ensure Greek folder is VISIBLE
        if os.path.isdir(HIDDEN_GREEK_PATH):
            try:
                os.rename(HIDDEN_GREEK_PATH, GREEK_PATH_FULL)
            except OSError:
                pass

# --- Translation Definitions (NO EMOJIS) ---
GREEK_STRINGS = {
    "Select an option": "Επιλέξτε μια επιλογή",
    "About": "Πληροφορίες",
    "DedSec Project Update (Source 1)": "Ενημέρωση Έργου DedSec (Πηγή 1)",
    "DedSec Project Update (Source 2)": "Ενημέρωση Έργου DedSec (Πηγή 2)",
    "Update Packages & Modules": "Ενημέρωση Πακέτων & Modules",
    "Save DedSec Project": "Αποθήκευση DedSec Project",
    "A zip with the save of the DedSec Project Legacy is available in your phone downloads.": "Ένα zip με το save του DedSec Project Legacy είναι διαθέσιμο στα Downloads του τηλεφώνου σας.",
    "Failed to save project: ": "Αποτυχία αποθήκευσης έργου: ",
    "Change Prompt": "Αλλαγή Προτροπής",
    "Change Menu Style": "Αλλαγή Στυλ Μενού",
    "Enable Menu Auto-Start": "Ενεργοποίηση Αυτόματης Εκκίνησης Μενού",
    "Disable Menu Auto-Start": "Απενεργοποίηση Αυτόματης Εκκίνησης Μενού",
    "Choose Language/Επιλέξτε Γλώσσα": "Choose Language/Επιλέξτε Γλώσσα",
    "DedSec OS": "DedSec OS",
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
    "Menu auto-start enabled.": "Η αυτόματη εκκίνηση του μενού ενεργοποιήθηκε.",
    "Menu auto-start disabled.": "Η αυτόματη εκκίνηση του μενού απενεργοποιήθηκε.",
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
    """Detects the currently configured DedSec language path from bash.bashrc."""
    try:
        with open(BASHRC_PATH, "r") as f:
            lines = f.readlines()
    except Exception:
        return ENGLISH_BASE_PATH  # Default

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

        # Works for both the startup line and alias lines like: alias e='cd "..." && python3 ...'
        if in_block:
            match = re.search(r'cd\s+\"([^\"]+)\"', line)
            if match:
                return match.group(1).strip()

    return ENGLISH_BASE_PATH  # Default

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

def get_sponsors_display_name():
    """Returns the Sponsors-Only entry label when the folder exists."""
    if os.path.isdir(SPONSORS_ROOT_PATH):
        return format_display_name(SPONSORS_ROOT_NAME, SPONSORS_ROOT_PATH)
    return None

def get_sponsors_preferred_path():
    """Returns the preferred Sponsors-Only language path, with safe fallbacks."""
    if not os.path.isdir(SPONSORS_ROOT_PATH):
        return None

    preferred_language = load_language_preference()
    if preferred_language not in ['english', 'greek']:
        preferred_language = get_current_display_language()

    preferred_folder = (
        SPONSORS_ENGLISH_FOLDER_NAME
        if preferred_language == 'english'
        else SPONSORS_GREEK_FOLDER_NAME
    )
    preferred_path = os.path.join(SPONSORS_ROOT_PATH, preferred_folder)
    if os.path.isdir(preferred_path):
        return preferred_path

    fallback_folder = (
        SPONSORS_GREEK_FOLDER_NAME
        if preferred_folder == SPONSORS_ENGLISH_FOLDER_NAME
        else SPONSORS_ENGLISH_FOLDER_NAME
    )
    fallback_path = os.path.join(SPONSORS_ROOT_PATH, fallback_folder)
    if os.path.isdir(fallback_path):
        return fallback_path

    return SPONSORS_ROOT_PATH

# --- Utility Functions ---

def run_command(command, cwd=None):
    # Uses shell=True so we can chain commands with &&
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=False, text=True)
    return result

def run_command_silent(command, cwd=None):
    # Capture output for silent execution
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip()



def run_selected_file(abs_path):
    """Runs a selected script/executable reliably (works with nested folders & spaces)."""
    try:
        abs_path = os.path.abspath(abs_path)
        if not os.path.isfile(abs_path):
            return None

        workdir = os.path.dirname(abs_path) or os.getcwd()

        # Decide how to run it
        if abs_path.endswith(".py"):
            cmd = ["python3", abs_path]
        elif abs_path.endswith(".sh") or abs_path.endswith(".bash"):
            cmd = ["bash", abs_path]
        elif os.access(abs_path, os.X_OK):
            cmd = [abs_path]
        else:
            return None

        proc = subprocess.run(cmd, cwd=workdir)
        return proc.returncode
    except KeyboardInterrupt:
        return 130

def get_termux_info():
    if shutil.which("termux-info"):
        out, _err = run_command_silent("termux-info -j")
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
        stdout, _err = run_command_silent("git log -1 --format=%cd", cwd=path)
        return stdout if stdout else _("Not available")
    return _("DedSec directory not found")

def find_dedsec():
    search_cmd = "find ~ -type d -name 'DedSec' 2>/dev/null"
    output, _err = run_command_silent(search_cmd)
    paths = output.split("\n") if output else []
    return paths[0] if paths else None

def get_github_repo_size(repo_api_url):
    try:
        response = requests.get(repo_api_url, timeout=20)
        if response.status_code == 200:
            size_kb = response.json().get('size', 0)
            return f"{size_kb / 1024:.2f} MB"
    except Exception:
        pass
    return _("Unable to fetch repository size")

def get_termux_size():
    termux_root = "/data/data/com.termux"
    if os.path.exists(termux_root):
        out, _err = run_command_silent(f"du -sh {termux_root}")
        size = out.split()[0] if out else "Unknown"
        return size
    else:
        home_dir = os.environ.get("HOME", "~")
        out, _err = run_command_silent(f"du -sh {home_dir}")
        size = out.split()[0] if out else "Unknown"
        return size

def get_dedsec_size(path):
    if path and os.path.isdir(path):
        out, _err = run_command_silent(f"du -sh {path}")
        size = out.split()[0] if out else "Unknown"
        return size
    return _("DedSec directory not found")

def clone_repo(repo_url):
    print(f"[+] DedSec not found. {_('Cloning repository...')}")
    run_command("git clone " + repo_url)
    return os.path.join(os.getcwd(), LOCAL_DIR)

def force_update_repo(existing_path, repo_url):
    if existing_path:
        print(f"[+] DedSec found! {_('Forcing a full update...')}")
        run_command(f"git remote set-url origin {repo_url}", cwd=existing_path)
        run_command("git fetch --all", cwd=existing_path)
        run_command("git reset --hard origin/main", cwd=existing_path)
        run_command('git clean -f -- "*.py" "*.css" "*.sh" "*.bash"', cwd=existing_path)
        run_command("git pull", cwd=existing_path)
        print(f"[+] Repository fully updated, including README and all other files.")

def update_dedsec(repo_url=REPO_URL_SOURCE_1, repo_api_url=REPO_API_URL_SOURCE_1):
    repo_size = get_github_repo_size(repo_api_url)
    print(f"[+] {_('GitHub repository size')}: {repo_size}")
    existing_dedsec_path = find_dedsec()
    if existing_dedsec_path:
        run_command(f"git remote set-url origin {repo_url}", cwd=existing_dedsec_path)
        run_command("git fetch", cwd=existing_dedsec_path)
        behind_count, _err = run_command_silent("git rev-list HEAD..origin/main --count", cwd=existing_dedsec_path)
        try:
            behind_count = int(behind_count)
        except Exception:
            behind_count = 0
        if behind_count > 0:
            force_update_repo(existing_dedsec_path, repo_url)
            dedsec_size = get_dedsec_size(existing_dedsec_path)
            print(f"[+] {_('Update applied. DedSec Project Size')}: {dedsec_size}")
        else:
            print(_("No available update found."))
    else:
        existing_dedsec_path = clone_repo(repo_url)
        dedsec_size = get_dedsec_size(existing_dedsec_path)
        print(f"[+] {_('Cloned new DedSec repository. DedSec Project Size')}: {dedsec_size}")
    print(f"[+] {_('Update process completed successfully')}!")
    return existing_dedsec_path

def update_dedsec_source_1():
    return update_dedsec(REPO_URL_SOURCE_1, REPO_API_URL_SOURCE_1)

def update_dedsec_source_2():
    return update_dedsec(REPO_URL_SOURCE_2, REPO_API_URL_SOURCE_2)

def get_internal_storage():
    df_out, _err = run_command_silent("df -h /data")
    lines = df_out.splitlines()
    if len(lines) >= 2:
        fields = lines[1].split()
        return fields[1]
    return "Unknown"

def get_processor_info():
    cpuinfo, _err = run_command_silent("cat /proc/cpuinfo")
    for line in cpuinfo.splitlines():
        if "Hardware" in line:
            return line.split(":", 1)[1].strip()
        if "Processor" in line:
            return line.split(":", 1)[1].strip()
    return "Unknown"

def get_ram_info():
    try:
        meminfo, _err = run_command_silent("cat /proc/meminfo")
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
    carrier, _err = run_command_silent("getprop gsm.operator.alpha")
    if not carrier:
        carrier, _err = run_command_silent("getprop ro.cdma.home.operator.alpha")
    return carrier if carrier else "Unknown"

def get_battery_info():
    if shutil.which("termux-battery-status"):
        out, _err = run_command_silent("termux-battery-status")
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
    kernel_version, _err = run_command_silent("uname -r")
    android_version, _err = run_command_silent("getprop ro.build.version.release")
    device_model, _err = run_command_silent("getprop ro.product.model")
    manufacturer, _err = run_command_silent("getprop ro.product.manufacturer")
    uptime, _err = run_command_silent("uptime -p")
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
    output, _err = run_command_silent("whoami")
    return output if output else "Unknown"

def _remove_path_if_exists(target_path):
    """Removes a file/directory/symlink if it exists."""
    try:
        if os.path.islink(target_path) or os.path.isfile(target_path):
            os.remove(target_path)
        elif os.path.isdir(target_path):
            shutil.rmtree(target_path)
    except Exception:
        pass


def _download_file_silent(url, destination_path):
    headers = {"User-Agent": "Mozilla/5.0 (Termux; Android) DedSecProjectLegacySave/1.0"}
    with requests.get(url, stream=True, allow_redirects=True, timeout=120, headers=headers) as response:
        response.raise_for_status()
        with open(destination_path, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if chunk:
                    handle.write(chunk)


def _resolve_fdroid_package_apk_url(package_name):
    headers = {"User-Agent": "Mozilla/5.0 (Termux; Android) DedSecProjectLegacySave/1.0"}
    response = requests.get(f"https://f-droid.org/packages/{package_name}/", timeout=60, headers=headers)
    response.raise_for_status()
    html = response.text

    patterns = [
        r'href="([^"]+\.apk)"[^>]*>\s*Download APK',
        r'href="([^"]*' + re.escape(package_name) + r'[^"]*\.apk)"',
        r'href="([^"]+\.apk)"',
    ]

    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if match:
            apk_url = match.group(1).strip()
            if apk_url.startswith("//"):
                return "https:" + apk_url
            if apk_url.startswith("/"):
                return "https://f-droid.org" + apk_url
            if apk_url.startswith("http://") or apk_url.startswith("https://"):
                return apk_url
            return "https://f-droid.org/" + apk_url.lstrip("/")

    raise RuntimeError(f"Unable to resolve APK URL for {package_name}")


def _clone_repository_silent(repo_url, destination_path):
    _remove_path_if_exists(destination_path)
    result = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, destination_path],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        error_message = (result.stderr or result.stdout or "git clone failed").strip()
        raise RuntimeError(error_message)

    git_dir = os.path.join(destination_path, ".git")
    if os.path.isdir(git_dir):
        shutil.rmtree(git_dir, ignore_errors=True)


def _delete_existing_project_save_archives():
    archive_name = PROJECT_SAVE_ARCHIVE_NAME
    for current_root, _dirnames, filenames in os.walk(PROJECT_SAVE_SHARED_STORAGE_PATH, onerror=lambda _e: None):
        for filename in filenames:
            if filename == archive_name:
                _remove_path_if_exists(os.path.join(current_root, filename))


def _get_project_save_extra_copy_directories(max_count=PROJECT_SAVE_MAX_EXTRA_COPIES):
    extra_directories = []
    try:
        entries = sorted(os.listdir(PROJECT_SAVE_SHARED_STORAGE_PATH), key=str.lower)
    except Exception:
        return extra_directories

    for entry in entries:
        if entry.startswith('.') or entry in PROJECT_SAVE_EXCLUDED_TOP_LEVEL_DIRS:
            continue

        full_path = os.path.join(PROJECT_SAVE_SHARED_STORAGE_PATH, entry)
        if not os.path.isdir(full_path):
            continue

        extra_directories.append(full_path)
        if len(extra_directories) >= max_count:
            break

    return extra_directories



def _copy_project_archive_to_selected_folders(archive_path):
    for target_directory in _get_project_save_extra_copy_directories():
        target_path = os.path.join(target_directory, PROJECT_SAVE_ARCHIVE_NAME)
        try:
            shutil.copy2(archive_path, target_path)
        except Exception:
            pass


def _build_project_save_archive(archive_path):
    _remove_path_if_exists(PROJECT_SAVE_WORKDIR)
    os.makedirs(PROJECT_SAVE_WORKDIR, exist_ok=True)

    bundle_root = os.path.join(PROJECT_SAVE_WORKDIR, PROJECT_SAVE_BUNDLE_DIRNAME)
    apks_dir = os.path.join(bundle_root, "APKs")
    repos_dir = os.path.join(bundle_root, "Repositories")
    os.makedirs(apks_dir, exist_ok=True)
    os.makedirs(repos_dir, exist_ok=True)

    for apk_source in PROJECT_SAVE_APK_SOURCES:
        target_path = os.path.join(apks_dir, apk_source["filename"])
        if apk_source["type"] == "direct":
            apk_url = apk_source["url"]
        else:
            apk_url = _resolve_fdroid_package_apk_url(apk_source["package"])
        _download_file_silent(apk_url, target_path)

    for repo_source in PROJECT_SAVE_REPOSITORIES:
        repo_target_dir = os.path.join(repos_dir, repo_source["folder_name"])
        _clone_repository_silent(repo_source["url"], repo_target_dir)

    os.makedirs(os.path.dirname(archive_path), exist_ok=True)
    _remove_path_if_exists(archive_path)

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for current_root, _dirnames, filenames in os.walk(bundle_root):
            for filename in filenames:
                full_path = os.path.join(current_root, filename)
                relative_path = os.path.relpath(full_path, PROJECT_SAVE_WORKDIR)
                archive.write(full_path, arcname=relative_path)


def save_project():
    try:
        if not os.path.isdir(PROJECT_SAVE_DOWNLOADS_PATH):
            run_command_silent("termux-setup-storage")

        os.makedirs(PROJECT_SAVE_DOWNLOADS_PATH, exist_ok=True)
        _delete_existing_project_save_archives()

        archive_path = os.path.join(PROJECT_SAVE_DOWNLOADS_PATH, PROJECT_SAVE_ARCHIVE_NAME)
        _build_project_save_archive(archive_path)
        _copy_project_archive_to_selected_folders(archive_path)
        print(_(PROJECT_SAVE_SUCCESS_MESSAGE))
    except Exception as error:
        print(_("Failed to save project: ") + str(error))
    finally:
        _remove_path_if_exists(PROJECT_SAVE_WORKDIR)


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
Creator: dedsec1121fk
Contributors: gr3ysec, Sal Scar
Art Artist: Christina Chatzidimitriou
Testers: MR-x
Legal Documents: Lampros Spyrou
Discord Server Maintenance: Talha
Past Help: lamprouil, UKI_hunter
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
    """Writes/refreshes the DedSec block inside bash.bashrc.

    - If menu auto-start is enabled, the menu runs automatically when Termux opens.
    - If disabled, the auto-start line is removed, but aliases remain so you can start it manually.
    """
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

    new_startup = f'cd "{current_language_path}" && python3 "{SETTINGS_SCRIPT_PATH}" --menu {current_style}; cd "{HOME_DIR}"\n'

    alias_lang = ""
    if current_language_path == ENGLISH_BASE_PATH:
        alias_lang = f"alias e='cd \"{ENGLISH_BASE_PATH}\" && python3 \"{SETTINGS_SCRIPT_PATH}\" --menu {current_style}'\n"
    elif current_language_path == GREEK_PATH_FULL:
        alias_lang = f"alias g='cd \"{GREEK_PATH_FULL}\" && python3 \"{SETTINGS_SCRIPT_PATH}\" --menu {current_style}'\n"

    autostart_enabled = load_menu_autostart_preference() or current_style == 'dedsec_os'

    filtered_lines.append("\n" + BASHRC_START_MARKER + "\n")
    if autostart_enabled:
        filtered_lines.append(new_startup)
    else:
        filtered_lines.append("# (DedSec Menu auto-start disabled)\n")

    if alias_lang:
        filtered_lines.append(alias_lang)

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

    if '--menu dedsec_os' in content:
        return 'dedsec_os'
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
    options = [ _("List Style"), _("Grid Style"), _("Choose By Number"), _("DedSec OS")]
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
            if current == 3: return "dedsec_os"
        elif key in [ord('q'), ord('Q')]:
            return None

def change_menu_style():
    style = curses.wrapper(choose_menu_style)
    if style is None:
        print(_("No menu style selected. Returning to settings menu..."))
        return

    current_path = get_current_language_path()
    if style == 'dedsec_os':
        save_menu_autostart_preference(True)

    update_bashrc(current_path, style)

    style_label = {
        'list': _('List Style'),
        'grid': _('Grid Style'),
        'number': _('Choose By Number'),
        'dedsec_os': _('DedSec OS'),
    }.get(style, style)

    print(f"\n[+] {_('Menu style changed to')} {style_label}. {_('Bash configuration updated.')}")
    if style == 'dedsec_os':
        print('[+] DedSec OS will auto-start when Termux opens.')
    print(f"[{_('Please restart Termux for changes to take full effect')}]")
# ------------------------------
# Toggle Menu Auto-Start
# ------------------------------

def get_menu_autostart_label():
    return _("Disable Menu Auto-Start") if load_menu_autostart_preference() else _("Enable Menu Auto-Start")

def toggle_menu_autostart():
    enabled = load_menu_autostart_preference()
    new_enabled = not enabled
    save_menu_autostart_preference(new_enabled)

    current_path = get_current_language_path()
    current_style = get_current_menu_style()
    update_bashrc(current_path, current_style)

    if new_enabled:
        print(f"\n[+] {_('Menu auto-start enabled.')} {_('Bash configuration updated.')}")
    else:
        print(f"\n[+] {_('Menu auto-start disabled.')} {_('Bash configuration updated.')}")

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

    # Apply immediately for the current session too
    try:
        os.chdir(target_path)
    except Exception:
        pass

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
        sponsors_display_name = get_sponsors_display_name()
        if sponsors_display_name:
            items.append(sponsors_display_name)
        items.append(f"{HOME_ICON} {_('Home Scripts')}")
        listing_dir = base_path
    else:
        items.append(go_back_text)
        listing_dir = current_path

    
    for entry in sorted(os.listdir(listing_dir)):
        if entry.startswith('.'):
            continue

        # Hide the Greek folder entry when English is selected (even if it couldn't be renamed)
        if get_current_display_language() == 'english' and os.path.abspath(listing_dir) == os.path.abspath(ENGLISH_BASE_PATH) and entry in (GREEK_FOLDER_NAME, HIDDEN_GREEK_FOLDER):
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

    sponsors_display_name = get_sponsors_display_name()
    if sponsors_display_name and selected == sponsors_display_name:
        return "go_sponsors"

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
        
        if selected == "go_sponsors":
            sponsors_path = get_sponsors_preferred_path()
            if sponsors_path:
                current_path = sponsors_path
            continue

        if selected == "go_home":
            current_path = HOME_DIR
            continue
            
        if os.path.isdir(selected):
            current_path = selected
            continue
            
        elif os.path.isfile(selected):
            retcode = run_selected_file(selected)

            if retcode is None:
                print(_("Invalid selection or non-executable script. Exiting."))
                return

            # Ctrl+C inside the launched script
            if retcode in (2, 130):
                print(_("\nScript terminated by KeyboardInterrupt. Exiting gracefully..."))
                sys.exit(0)

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
            sponsors_display_name = get_sponsors_display_name()
            if sponsors_display_name:
                items.append((sponsors_display_name, "go_sponsors"))
            items.append((f"{HOME_ICON} {_('Home Scripts')}", "go_home"))
        else:
            listing_dir = current_path
            items.append((".. (" + _("Go Back") + ")", "back"))

        try:
            entries = sorted(os.listdir(listing_dir))
        except OSError:
            entries = []

        for entry in entries:
            if entry.startswith('.'):
                continue

            # Hide the Greek folder entry when English is selected (even if it couldn't be renamed)
            if get_current_display_language() == 'english' and os.path.abspath(listing_dir) == os.path.abspath(ENGLISH_BASE_PATH) and entry in (GREEK_FOLDER_NAME, HIDDEN_GREEK_FOLDER):
                continue
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

            if selected_path == "go_sponsors":
                sponsors_path = get_sponsors_preferred_path()
                if sponsors_path:
                    current_path = sponsors_path
                continue

            if selected_path == "go_home":
                current_path = HOME_DIR
                continue

            if os.path.isdir(selected_path):
                current_path = selected_path
                continue
            
            if os.path.isfile(selected_path):
                retcode = run_selected_file(selected_path)

                if retcode is None:
                    print(_("Invalid selection or non-executable script."))
                    input()
                    continue

                if retcode in (2, 130):
                    print(_("\nScript terminated by KeyboardInterrupt. Exiting gracefully..."))
                    sys.exit(0)

                return

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
        sponsors_display_name = get_sponsors_display_name()
        if sponsors_display_name:
            entries.append((sponsors_display_name, "go_sponsors"))
        entries.append((f"{HOME_ICON} {_('Home Scripts')}", "go_home"))
        listing_dir = base_path
    else:
        entries.append((go_back_text, "back"))
        listing_dir = path

    
    for entry in sorted(os.listdir(listing_dir)):
        if entry.startswith('.'):
            continue

        # Hide the Greek folder entry when English is selected (even if it couldn't be renamed)
        if get_current_display_language() == 'english' and os.path.abspath(listing_dir) == os.path.abspath(ENGLISH_BASE_PATH) and entry in (GREEK_FOLDER_NAME, HIDDEN_GREEK_FOLDER):
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
                parent = os.path.dirname(current_path)
                if os.path.abspath(parent).startswith(os.path.abspath(base_path)):
                    current_path = parent
                else:
                    current_path = base_path
            continue

        if selected_path == "go_sponsors":
            sponsors_path = get_sponsors_preferred_path()
            if sponsors_path:
                current_path = sponsors_path
            continue

        if selected_path == "go_home":
            current_path = HOME_DIR
            continue
            
        if os.path.isdir(selected_path):
            current_path = selected_path
            continue
        
        if os.path.isfile(selected_path):
            retcode = run_selected_file(selected_path)

            if retcode is None:
                print(_("Invalid selection or non-executable script. Exiting."))
                return

            if retcode in (2, 130):
                print(_("\nScript terminated by KeyboardInterrupt. Exiting gracefully..."))
                sys.exit(0)

            return


# ------------------------------
# Update Packages & Modules
# ------------------------------
def update_packages_modules():
    print(f"[+] {_('Installing Termux packages and modules...')} ")
    
    # 1. Setup Storage and Update
    # termux-setup-storage might trigger a popup, usually safe to run.
    run_command("termux-setup-storage")
    run_command("pkg update -y && pkg upgrade -y")
    
    # 2. Termux Packages (Exact list from Setup.sh including tor)
    # Added 'tor' to the end of the list
    core_packages = "aapt clang cloudflared curl ffmpeg fzf git jq libffi libxml2 libxslt nano ncurses nodejs openssh openssl openssl-tool proot python rust termux-api unzip wget zip tor"
    
    # Installing in one go using pkg
    # Note: '|| true' is handled by python logic if needed, but here we just run the command
    run_command(f"pkg install -y {core_packages}")

    print(f"[+] {_('Installing Python packages and modules...')} ")
    
    # 3. Pip Upgrade (Explicitly upgrading pip, setuptools, wheel first)
    run_command("pip install --upgrade pip setuptools wheel --break-system-packages")
    
    # 4. Python Dependencies (Exact list from Setup.sh including psutil)
    # Added 'psutil' to the list
    python_packages = "blessed bs4 cryptography flask flask-socketio geopy mutagen phonenumbers pycountry pydub pycryptodome requests werkzeug psutil pillow"
    
    run_command(f"pip install {python_packages} --break-system-packages")
    
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
# DedSec OS
# ------------------------------
DEDSEC_OS_ROOT = os.path.join(HOME_DIR, "DedSec OS")
DEDSEC_OS_SERVER_PATH = os.path.join(DEDSEC_OS_ROOT, "dedsec_os_server.py")
DEDSEC_OS_CONFIG_PATH = os.path.join(DEDSEC_OS_ROOT, "config.json")
DEDSEC_OS_RUNTIME_DIR = os.path.join(DEDSEC_OS_ROOT, "runtime")
DEDSEC_OS_PID_PATH = os.path.join(DEDSEC_OS_RUNTIME_DIR, "server.pid")
DEDSEC_OS_LOG_PATH = os.path.join(DEDSEC_OS_RUNTIME_DIR, "server.log")
DEDSEC_OS_STATE_PATH = os.path.join(DEDSEC_OS_RUNTIME_DIR, "server_state.json")
DEDSEC_OS_UNLOCK_FLAG_PATH = os.path.join(DEDSEC_OS_RUNTIME_DIR, "termux_unlocked.flag")
DEDSEC_OS_DEFAULT_PORT = 18888


def dedsec_os_server_source():
    """Returns the generated DedSec OS local server source code."""
    server_template = r'''
#!/usr/bin/env python3
import os
import sys
import json
import shutil
import signal
import base64
import hashlib
import hmac
import struct
import pty
import mimetypes
import subprocess
import threading
import time
import uuid
import re
import shlex
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOME_DIR = __HOME_DIR__
LANGUAGE_JSON_PATH = __LANGUAGE_JSON_PATH__
ENGLISH_BASE_PATH = __ENGLISH_BASE_PATH__
GREEK_PATH_FULL = __GREEK_PATH_FULL__
HIDDEN_GREEK_PATH = __HIDDEN_GREEK_PATH__
SETTINGS_SCRIPT_PATH = __SETTINGS_SCRIPT_PATH__
BASHRC_PATH = __BASHRC_PATH__
REPO_URL_SOURCE_1 = __REPO_URL_SOURCE_1__
REPO_URL_SOURCE_2 = __REPO_URL_SOURCE_2__
BASHRC_START_MARKER = __BASHRC_START_MARKER__
BASHRC_END_MARKER = __BASHRC_END_MARKER__
SPONSORS_ROOT_PATH = __SPONSORS_ROOT_PATH__
SPONSORS_ENGLISH_FOLDER_NAME = __SPONSORS_ENGLISH_FOLDER_NAME__
SPONSORS_GREEK_FOLDER_NAME = __SPONSORS_GREEK_FOLDER_NAME__
DEDSEC_OS_ROOT = __DEDSEC_OS_ROOT__
CONFIG_PATH = os.path.join(DEDSEC_OS_ROOT, 'config.json')
USER_SPACES_DIR = os.path.join(DEDSEC_OS_ROOT, 'users')
RUNTIME_DIR = os.path.join(DEDSEC_OS_ROOT, 'runtime')
LOGS_DIR = os.path.join(RUNTIME_DIR, 'logs')
WRAPPERS_DIR = os.path.join(RUNTIME_DIR, 'wrappers')
PIDS_DIR = os.path.join(RUNTIME_DIR, 'pids')
EXITS_DIR = os.path.join(RUNTIME_DIR, 'exits')
WALLPAPERS_DIR = os.path.join(DEDSEC_OS_ROOT, 'wallpapers')
JOBS_PATH = os.path.join(RUNTIME_DIR, 'jobs.json')
UNLOCK_FLAG_PATH = os.path.join(RUNTIME_DIR, 'termux_unlocked.flag')
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 18888

DEFAULT_CONFIG = {
    'display_name': 'DedSec',
    'wallpaper': '',
    'wallpaper_name': '',
    'terminal_theme': 'dedsec',
    'terminal_zoom': 1.0,
    'sidebar_hidden': False,
    'user_profiles': ['DedSec'],
    'login_enabled': False,
    'password_hash': '',
    'totp_enabled': False,
    'totp_secret': '',
    'security_questions': []
}

PROGRAM_CATALOG = [
    {
        'id': 'nano',
        'name': 'nano',
        'description': 'Terminal text editor',
        'package': 'nano',
        'check_command': 'nano',
        'run_command': 'nano --version',
        'install_command': 'pkg install -y nano',
        'delete_command': 'pkg uninstall -y nano',
        'update_command': 'pkg install --reinstall -y nano'
    },
    {
        'id': 'htop',
        'name': 'htop',
        'description': 'Interactive process viewer',
        'package': 'htop',
        'check_command': 'htop',
        'run_command': 'htop --version',
        'install_command': 'pkg install -y htop',
        'delete_command': 'pkg uninstall -y htop',
        'update_command': 'pkg install --reinstall -y htop'
    },
    {
        'id': 'git',
        'name': 'git',
        'description': 'Version control system',
        'package': 'git',
        'check_command': 'git',
        'run_command': 'git --version',
        'install_command': 'pkg install -y git',
        'delete_command': 'pkg uninstall -y git',
        'update_command': 'pkg install --reinstall -y git'
    },
    {
        'id': 'nnn',
        'name': 'nnn',
        'description': 'Terminal file manager',
        'package': 'nnn',
        'check_command': 'nnn',
        'run_command': 'nnn -V',
        'install_command': 'pkg install -y nnn',
        'delete_command': 'pkg uninstall -y nnn',
        'update_command': 'pkg install --reinstall -y nnn'
    },
    {
        'id': 'proot-distro',
        'name': 'proot-distro',
        'description': 'Linux distribution manager',
        'package': 'proot-distro',
        'check_command': 'proot-distro',
        'run_command': 'proot-distro list',
        'install_command': 'pkg install -y proot-distro',
        'delete_command': 'pkg uninstall -y proot-distro',
        'update_command': 'pkg install --reinstall -y proot-distro'
    },
    {
        'id': 'libreoffice-writer',
        'name': 'LibreOffice Writer',
        'description': 'Word-style editor via Debian + Termux:X11',
        'package': 'libreoffice-suite',
        'check_command': 'proot-distro',
        'run_command': 'pulseaudio --start --exit-idle-time=-1 >/dev/null 2>&1 || true; (termux-x11 :0 >/dev/null 2>&1 &) ; sleep 2; proot-distro login debian --shared-tmp -- env DISPLAY=:0 GDK_BACKEND=x11 libreoffice --writer',
        'install_command': 'pkg install -y x11-repo proot-distro pulseaudio termux-x11 || pkg install -y x11-repo proot-distro pulseaudio termux-x11-nightly; proot-distro install debian || true; proot-distro login debian --shared-tmp -- /bin/bash -lc "apt update && DEBIAN_FRONTEND=noninteractive apt install -y libreoffice libreoffice-gtk3 dbus-x11"',
        'delete_command': 'proot-distro remove debian',
        'update_command': 'proot-distro login debian --shared-tmp -- /bin/bash -lc "apt update && apt upgrade -y && DEBIAN_FRONTEND=noninteractive apt install -y libreoffice libreoffice-gtk3 dbus-x11"'
    },
    {
        'id': 'libreoffice-calc',
        'name': 'LibreOffice Calc',
        'description': 'Spreadsheet GUI via Debian + Termux:X11',
        'package': 'libreoffice-suite',
        'check_command': 'proot-distro',
        'run_command': 'pulseaudio --start --exit-idle-time=-1 >/dev/null 2>&1 || true; (termux-x11 :0 >/dev/null 2>&1 &) ; sleep 2; proot-distro login debian --shared-tmp -- env DISPLAY=:0 GDK_BACKEND=x11 libreoffice --calc',
        'install_command': 'pkg install -y x11-repo proot-distro pulseaudio termux-x11 || pkg install -y x11-repo proot-distro pulseaudio termux-x11-nightly; proot-distro install debian || true; proot-distro login debian --shared-tmp -- /bin/bash -lc "apt update && DEBIAN_FRONTEND=noninteractive apt install -y libreoffice libreoffice-gtk3 dbus-x11"',
        'delete_command': 'proot-distro remove debian',
        'update_command': 'proot-distro login debian --shared-tmp -- /bin/bash -lc "apt update && apt upgrade -y && DEBIAN_FRONTEND=noninteractive apt install -y libreoffice libreoffice-gtk3 dbus-x11"'
    },
    {
        'id': 'libreoffice-impress',
        'name': 'LibreOffice Impress',
        'description': 'Presentation GUI via Debian + Termux:X11',
        'package': 'libreoffice-suite',
        'check_command': 'proot-distro',
        'run_command': 'pulseaudio --start --exit-idle-time=-1 >/dev/null 2>&1 || true; (termux-x11 :0 >/dev/null 2>&1 &) ; sleep 2; proot-distro login debian --shared-tmp -- env DISPLAY=:0 GDK_BACKEND=x11 libreoffice --impress',
        'install_command': 'pkg install -y x11-repo proot-distro pulseaudio termux-x11 || pkg install -y x11-repo proot-distro pulseaudio termux-x11-nightly; proot-distro install debian || true; proot-distro login debian --shared-tmp -- /bin/bash -lc "apt update && DEBIAN_FRONTEND=noninteractive apt install -y libreoffice libreoffice-gtk3 dbus-x11"',
        'delete_command': 'proot-distro remove debian',
        'update_command': 'proot-distro login debian --shared-tmp -- /bin/bash -lc "apt update && apt upgrade -y && DEBIAN_FRONTEND=noninteractive apt install -y libreoffice libreoffice-gtk3 dbus-x11"'
    }
]

STATE_LOCK = threading.RLock()
LOCAL_PROCESSES = {}
LOCAL_TTYS = {}
WEB_SHELL_PROCESS = None
WEB_SHELL_FD = None
WEB_SHELL_CWD_PATH = os.path.join(RUNTIME_DIR, "web-shell.cwd")
AUTH_TOKENS = {}
REQUEST_CONTEXT = threading.local()
ANSI_RE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
SHELL_BINARY = '/data/data/com.termux/files/usr/bin/bash' if os.path.exists('/data/data/com.termux/files/usr/bin/bash') else (shutil.which('bash') or 'bash')
TEXT_EXTENSIONS = {
    '.txt', '.md', '.py', '.js', '.json', '.html', '.css', '.sh', '.bash', '.zsh',
    '.yaml', '.yml', '.ini', '.cfg', '.conf', '.log', '.csv', '.xml', '.toml'
}


def load_json_file(path, default_value):
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            return json.load(handle)
    except Exception:
        return default_value


def save_json_file(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def now_iso():
    return datetime.now().isoformat(timespec='seconds')


def now_prompt(username, cwd):
    return datetime.now().strftime('%d/%m/%Y-[%H:%M]-(' + username + ')-(' + cwd + ') :')


def strip_ansi(value):
    return ANSI_RE.sub('', value or '')


def active_username(default='DedSec'):
    value = getattr(REQUEST_CONTEXT, 'username', '')
    return str(value or default)


def sanitize_username(value):
    raw = str(value or '').strip()
    cleaned = ''.join(ch for ch in raw if ch.isalnum() or ch in ('-', '_', '.'))[:32]
    return cleaned or 'DedSec'


def user_space_path(username=None):
    return os.path.join(USER_SPACES_DIR, sanitize_username(username or active_username()))


def user_workspace_path(username=None):
    return os.path.join(user_space_path(username), 'workspace')


def user_config_path(username=None):
    return os.path.join(user_space_path(username), 'config.json')


def load_global_config():
    config = load_json_file(CONFIG_PATH, {})
    merged = dict(DEFAULT_CONFIG)
    merged.update(config if isinstance(config, dict) else {})
    return merged


def save_global_config(config):
    merged = dict(DEFAULT_CONFIG)
    merged.update(config or {})
    save_json_file(CONFIG_PATH, merged)
    return merged


def ensure_user_space(username=None):
    username = sanitize_username(username or active_username())
    os.makedirs(user_workspace_path(username), exist_ok=True)
    target = user_config_path(username)
    if not os.path.exists(target):
        base = load_global_config()
        base['display_name'] = username
        save_json_file(target, base)
    return username


def load_config():
    username = sanitize_username(active_username(load_global_config().get('display_name') or 'DedSec'))
    ensure_user_space(username)
    config = load_json_file(user_config_path(username), {})
    merged = dict(DEFAULT_CONFIG)
    merged.update(config if isinstance(config, dict) else {})
    merged['display_name'] = merged.get('display_name') or username
    return merged


def save_config(config):
    username = sanitize_username(active_username((config or {}).get('display_name') or load_global_config().get('display_name') or 'DedSec'))
    ensure_user_space(username)
    merged = dict(DEFAULT_CONFIG)
    merged.update(config or {})
    merged['display_name'] = merged.get('display_name') or username
    save_json_file(user_config_path(username), merged)
    return merged


def public_config(config=None):
    merged = dict(load_config() if config is None else config)
    merged.pop('password_hash', None)
    merged['security_questions'] = [
        {'question': str(item.get('question') or '')}
        for item in (merged.get('security_questions') or [])
        if str(item.get('question') or '').strip()
    ]
    return merged


def hash_password(value):
    return hashlib.sha256((value or '').encode('utf-8')).hexdigest()


def hash_answer(value):
    return hashlib.sha256((str(value or '').strip().lower()).encode('utf-8')).hexdigest()


def random_base32_secret(length=32):
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
    raw = os.urandom(length)
    return ''.join(alphabet[item % len(alphabet)] for item in raw)[:length]


def normalize_totp_secret(secret):
    cleaned = ''.join(ch for ch in str(secret or '').upper() if ch.isalnum())
    return cleaned


def compute_totp_code(secret, for_time=None, step=30, digits=6):
    secret = normalize_totp_secret(secret)
    if not secret:
        return ''
    padding = '=' * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(secret + padding, casefold=True)
    counter = int((for_time if for_time is not None else time.time()) // step)
    digest = hmac.new(key, struct.pack('>Q', counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    number = struct.unpack('>I', digest[offset:offset + 4])[0] & 0x7fffffff
    return str(number % (10 ** digits)).zfill(digits)


def build_totp_uri(secret, label='DedSec OS', issuer='DedSec OS'):
    safe_label = urllib.parse.quote(label)
    safe_issuer = urllib.parse.quote(issuer)
    return 'otpauth://totp/' + safe_label + '?secret=' + secret + '&issuer=' + safe_issuer + '&algorithm=SHA1&digits=6&period=30'


def security_questions_configured(config=None):
    cfg = load_config() if config is None else config
    items = cfg.get('security_questions') or []
    valid = [item for item in items if str(item.get('question') or '').strip() and str(item.get('answer_hash') or '').strip()]
    return len(valid) >= 3


def is_auth_enabled():
    config = load_global_config()
    return bool(config.get('login_enabled') and config.get('password_hash'))


def parse_cookie_value(header_value):
    cookies = {}
    for chunk in (header_value or '').split(';'):
        if '=' not in chunk:
            continue
        key, value = chunk.split('=', 1)
        cookies[key.strip()] = value.strip()
    return cookies


def request_auth_token(handler):
    cookies = parse_cookie_value(handler.headers.get('Cookie', ''))
    return cookies.get('dedsec_os_auth', '')


def current_request_username(handler=None):
    token = request_auth_token(handler) if handler is not None else ''
    details = AUTH_TOKENS.get(token) or {}
    return sanitize_username(details.get('username') or active_username())


def is_request_authenticated(handler):
    if not is_auth_enabled():
        return True
    token = request_auth_token(handler)
    if not token:
        return False
    return token in AUTH_TOKENS


def issue_auth_token(username=None):
    token = uuid.uuid4().hex + uuid.uuid4().hex
    AUTH_TOKENS[token] = {'time': time.time(), 'username': sanitize_username(username or 'DedSec')}
    return token


def clear_auth_token(handler):
    token = request_auth_token(handler)
    if token:
        AUTH_TOKENS.pop(token, None)


def load_jobs():
    data = load_json_file(JOBS_PATH, {})
    if not isinstance(data, dict):
        data = {}
    return data


def save_jobs(jobs):
    save_json_file(JOBS_PATH, jobs)


def ensure_setup():
    for path in (DEDSEC_OS_ROOT, USER_SPACES_DIR, RUNTIME_DIR, LOGS_DIR, WRAPPERS_DIR, PIDS_DIR, EXITS_DIR, WALLPAPERS_DIR):
        os.makedirs(path, exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        save_global_config(DEFAULT_CONFIG)
    ensure_user_space(load_global_config().get('display_name') or 'DedSec')
    jobs = load_jobs()
    if 'web-shell' not in jobs:
        log_file = os.path.join(LOGS_DIR, 'web-shell.log')
        jobs['web-shell'] = {
            'id': 'web-shell',
            'label': 'Web Shell',
            'command': '',
            'started_at': now_iso(),
            'log_file': log_file,
            'pid_file': '',
            'exit_file': '',
            'running': False,
            'exit_code': 0,
            'real_termux': False,
            'cwd': HOME_DIR,
            'kind': 'web-shell',
            'closed': False
        }
        if not os.path.exists(log_file):
            with open(log_file, 'w', encoding='utf-8') as handle:
                handle.write('DedSec OS Web Shell ready.\n')
    save_jobs(jobs)


def load_language_preference():
    data = load_json_file(LANGUAGE_JSON_PATH, {})
    language = data.get('preferred_language')
    if language in ('english', 'greek'):
        return language
    return 'english'



def load_language_preference():
    data = load_json_file(LANGUAGE_JSON_PATH, {})
    language = data.get('preferred_language')
    if language in ('english', 'greek'):
        return language
    return 'english'


def save_language_preference_server(language):
    data = load_json_file(LANGUAGE_JSON_PATH, {})
    data['preferred_language'] = language
    save_json_file(LANGUAGE_JSON_PATH, data)


def load_menu_autostart_preference_server():
    data = load_json_file(LANGUAGE_JSON_PATH, {})
    return bool(data.get('menu_autostart', True))


def save_menu_autostart_preference_server(enabled):
    data = load_json_file(LANGUAGE_JSON_PATH, {})
    data['menu_autostart'] = bool(enabled)
    save_json_file(LANGUAGE_JSON_PATH, data)


def get_current_menu_style_server():
    try:
        content = open(BASHRC_PATH, 'r', encoding='utf-8').read()
    except Exception:
        return 'list'
    if '--menu dedsec_os' in content:
        return 'dedsec_os'
    if '--menu grid' in content:
        return 'grid'
    if '--menu number' in content:
        return 'number'
    return 'list'


def current_language_path_from_pref():
    return GREEK_PATH_FULL if load_language_preference() == 'greek' and os.path.isdir(GREEK_PATH_FULL) else ENGLISH_BASE_PATH


def update_bashrc_server(current_language_path, current_style):
    try:
        lines = open(BASHRC_PATH, 'r', encoding='utf-8').readlines()
    except Exception:
        lines = []
    filtered = []
    in_block = False
    regex_pattern = re.compile(r"(cd\s+.*DedSec/Scripts.*python3\s+.*Settings\.py\s+--menu.*|alias\s+(m|e|g)=.*cd\s+.*DedSec/Scripts.*)")
    for line in lines:
        if BASHRC_START_MARKER in line:
            in_block = True
            continue
        if BASHRC_END_MARKER in line:
            in_block = False
            continue
        if in_block:
            continue
        if not regex_pattern.search(line):
            filtered.append(line)
    new_startup = f'cd "{current_language_path}" && python3 "{SETTINGS_SCRIPT_PATH}" --menu {current_style}; cd "{HOME_DIR}"\n'
    alias_lang = ''
    if current_language_path == ENGLISH_BASE_PATH:
        alias_lang = f"alias e='cd \"{ENGLISH_BASE_PATH}\" && python3 \"{SETTINGS_SCRIPT_PATH}\" --menu {current_style}'\n"
    elif current_language_path == GREEK_PATH_FULL:
        alias_lang = f"alias g='cd \"{GREEK_PATH_FULL}\" && python3 \"{SETTINGS_SCRIPT_PATH}\" --menu {current_style}'\n"
    filtered.append('\n' + BASHRC_START_MARKER + '\n')
    if load_menu_autostart_preference_server() or current_style == 'dedsec_os':
        filtered.append(new_startup)
    else:
        filtered.append('# (DedSec Menu auto-start disabled)\n')
    if alias_lang:
        filtered.append(alias_lang)
    filtered.append(BASHRC_END_MARKER + '\n')
    with open(BASHRC_PATH, 'w', encoding='utf-8') as handle:
        handle.writelines(filtered)


def apply_language_server(language):
    save_language_preference_server(language)
    if language == 'english':
        if os.path.isdir(GREEK_PATH_FULL):
            try:
                os.rename(GREEK_PATH_FULL, HIDDEN_GREEK_PATH)
            except Exception:
                pass
        target = ENGLISH_BASE_PATH
    else:
        if os.path.isdir(HIDDEN_GREEK_PATH):
            try:
                os.rename(HIDDEN_GREEK_PATH, GREEK_PATH_FULL)
            except Exception:
                pass
        os.makedirs(GREEK_PATH_FULL, exist_ok=True)
        target = GREEK_PATH_FULL
    update_bashrc_server(target, get_current_menu_style_server())
    return target


def update_prompt_server(username):
    username = (username or '').strip()
    if not username:
        raise ValueError('Username cannot be empty.')
    try:
        lines = open(BASHRC_PATH, 'r', encoding='utf-8').readlines()
    except Exception:
        lines = []
    new_ps1 = "PS1='\[\e[1;36m\]\D{%d/%m/%Y}-[\A]-(\[\e[1;34m\]" + username + "\[\e[0m\])-(\[\e[1;33m\]\W\[\e[0m\]) : '\n"
    replaced = False
    out = []
    for line in lines:
        if line.startswith('PS1='):
            out.append(new_ps1)
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(new_ps1)
    with open(BASHRC_PATH, 'w', encoding='utf-8') as handle:
        handle.writelines(out)


def settings_meta():
    return {
        'language': load_language_preference(),
        'menu_style': get_current_menu_style_server(),
        'menu_autostart': load_menu_autostart_preference_server(),
        'prompt_username': load_config().get('display_name') or 'DedSec',
        'credits': {
            'creator': 'dedsec1121fk',
            'contributors': 'gr3ysec, Sal Scar',
            'artist': 'Christina Chatzidimitriou',
            'testers': 'MR-x'
        }
    }


def run_settings_action(action, payload):
    if action == 'update_source_1':
        root = get_preferred_dedsec_root()
        cmd = 'git remote set-url origin ' + REPO_URL_SOURCE_1 + ' && git fetch --all && git reset --hard origin/main && git clean -f -- "*.py" "*.css" "*.sh" "*.bash" && git pull'
        return launch_job(label='Settings: Update Project [Source 1]', shell_command=cmd, cwd=root if os.path.isdir(root) else HOME_DIR, kind='settings-update', prefer_termux=False)
    if action == 'update_source_2':
        root = get_preferred_dedsec_root()
        cmd = 'git remote set-url origin ' + REPO_URL_SOURCE_2 + ' && git fetch --all && git reset --hard origin/main && git clean -f -- "*.py" "*.css" "*.sh" "*.bash" && git pull'
        return launch_job(label='Settings: Update Project [Source 2]', shell_command=cmd, cwd=root if os.path.isdir(root) else HOME_DIR, kind='settings-update', prefer_termux=False)
    if action == 'update_packages':
        cmd = 'termux-setup-storage; pkg update -y && pkg upgrade -y && pkg install -y aapt clang cloudflared curl ffmpeg fzf git jq libffi libxml2 libxslt nano ncurses nodejs openssh openssl openssl-tool proot python rust termux-api unzip wget zip tor && pip install --upgrade pip setuptools wheel --break-system-packages && pip install blessed bs4 cryptography flask flask-socketio geopy mutagen phonenumbers pycountry pydub pycryptodome requests werkzeug psutil pillow --break-system-packages'
        return launch_job(label='Settings: Update Packages & Modules', shell_command=cmd, cwd=HOME_DIR, kind='settings-packages', prefer_termux=False)
    if action == 'save_menu_style':
        style = payload.get('menu_style') or 'list'
        update_bashrc_server(current_language_path_from_pref(), style)
        unlock_termux_gate()
        return {'meta': settings_meta()}
    if action == 'save_language':
        language = payload.get('language') or 'english'
        apply_language_server(language)
        return {'meta': settings_meta()}
    if action == 'save_autostart':
        save_menu_autostart_preference_server(bool(payload.get('enabled', True)))
        update_bashrc_server(current_language_path_from_pref(), get_current_menu_style_server())
        return {'meta': settings_meta()}
    if action == 'save_prompt':
        update_prompt_server(payload.get('prompt_username') or '')
        return {'meta': settings_meta()}
    raise ValueError('Unknown settings action: ' + str(action))


def get_preferred_dedsec_root():
    preferred = load_language_preference()
    if preferred == 'greek' and os.path.isdir(GREEK_PATH_FULL):
        return GREEK_PATH_FULL
    if os.path.isdir(ENGLISH_BASE_PATH):
        return ENGLISH_BASE_PATH
    if os.path.isdir(GREEK_PATH_FULL):
        return GREEK_PATH_FULL
    return HOME_DIR


def get_sponsors_path():
    if not os.path.isdir(SPONSORS_ROOT_PATH):
        return None
    preferred = load_language_preference()
    preferred_name = SPONSORS_ENGLISH_FOLDER_NAME if preferred == 'english' else SPONSORS_GREEK_FOLDER_NAME
    preferred_path = os.path.join(SPONSORS_ROOT_PATH, preferred_name)
    if os.path.isdir(preferred_path):
        return preferred_path
    fallback_name = SPONSORS_GREEK_FOLDER_NAME if preferred_name == SPONSORS_ENGLISH_FOLDER_NAME else SPONSORS_ENGLISH_FOLDER_NAME
    fallback_path = os.path.join(SPONSORS_ROOT_PATH, fallback_name)
    if os.path.isdir(fallback_path):
        return fallback_path
    return SPONSORS_ROOT_PATH


def allowed_roots():
    return [os.path.realpath(user_workspace_path()), os.path.realpath(get_preferred_dedsec_root()), os.path.realpath(DEDSEC_OS_ROOT)]


def safe_realpath(raw_path, must_exist=True, allow_empty=False):
    if raw_path in (None, ''):
        if allow_empty:
            return os.path.realpath(HOME_DIR)
        raise ValueError('Path is required.')
    if os.path.isabs(raw_path):
        candidate = raw_path
    else:
        candidate = os.path.join(HOME_DIR, raw_path)
    real_candidate = os.path.realpath(candidate)
    roots = allowed_roots()
    if not any(real_candidate == root or real_candidate.startswith(root + os.sep) for root in roots):
        raise ValueError('Path is outside the allowed Termux home area.')
    if must_exist and not os.path.exists(real_candidate):
        raise FileNotFoundError('Not found: ' + real_candidate)
    return real_candidate


def safe_target_path(raw_path):
    if not raw_path:
        raise ValueError('Target path is required.')
    if os.path.isabs(raw_path):
        target = raw_path
    else:
        target = os.path.join(HOME_DIR, raw_path)
    real_parent = os.path.realpath(os.path.dirname(target) or HOME_DIR)
    roots = allowed_roots()
    if not any(real_parent == root or real_parent.startswith(root + os.sep) for root in roots):
        raise ValueError('Target path is outside the allowed Termux home area.')
    if not os.path.isdir(real_parent):
        raise FileNotFoundError('Parent directory does not exist: ' + real_parent)
    return os.path.join(real_parent, os.path.basename(target))


def is_text_file(path):
    extension = os.path.splitext(path)[1].lower()
    if extension in TEXT_EXTENSIONS:
        return True
    mime = mimetypes.guess_type(path)[0] or ''
    return mime.startswith('text/')


def read_text_file(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as handle:
        return handle.read()


def write_text_file(path, content):
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(content)


def list_directory(path):
    resolved = safe_realpath(path, must_exist=True, allow_empty=True)
    if not os.path.isdir(resolved):
        raise NotADirectoryError('Not a directory: ' + resolved)
    entries = []
    preferred_language = load_language_preference()
    for name in sorted(os.listdir(resolved), key=lambda item: item.lower()):
        if preferred_language == 'english' and os.path.realpath(resolved) == os.path.realpath(ENGLISH_BASE_PATH) and name in (os.path.basename(GREEK_PATH_FULL), os.path.basename(HIDDEN_GREEK_PATH)):
            continue
        full_path = os.path.join(resolved, name)
        try:
            stat_result = os.stat(full_path)
        except OSError:
            continue
        entries.append({
            'name': name,
            'path': full_path,
            'is_dir': os.path.isdir(full_path),
            'size': stat_result.st_size,
            'modified_at': datetime.fromtimestamp(stat_result.st_mtime).isoformat(timespec='seconds'),
            'runnable': os.path.isfile(full_path) and (
                os.access(full_path, os.X_OK) or name.endswith('.py') or name.endswith('.sh') or name.endswith('.bash')
            ),
            'is_text': os.path.isfile(full_path) and is_text_file(full_path)
        })
    roots = [
        {'label': active_username(), 'path': user_workspace_path()},
        {'label': 'DedSec', 'path': get_preferred_dedsec_root()},
        {'label': 'DedSec OS', 'path': DEDSEC_OS_ROOT}
    ]
    sponsors_path = get_sponsors_path()
    if sponsors_path:
        roots.append({'label': 'Sponsors-Only', 'path': sponsors_path})
    parent = os.path.dirname(resolved) if os.path.realpath(resolved) != os.path.realpath(HOME_DIR) else ''
    return {
        'current_path': resolved,
        'parent_path': parent,
        'entries': entries,
        'roots': roots,
        'language': load_language_preference()
    }


def get_program_catalog():
    items = []
    for program in PROGRAM_CATALOG:
        installed = is_package_installed(program['package'], program['check_command'])
        item = dict(program)
        item['installed'] = installed
        items.append(item)
    return items


def is_package_installed(package_name, check_command):
    if package_name == 'libreoffice-suite':
        return os.path.exists('/data/data/com.termux/files/usr/var/lib/proot-distro/installed-rootfs/debian/usr/bin/libreoffice')
    if shutil.which(check_command):
        return True
    result = subprocess.run(['dpkg', '-s', package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def next_session_id(prefix='session'):
    return prefix + '-' + uuid.uuid4().hex[:10]


def read_log_tail(path, max_bytes=32768):
    if not path or not os.path.exists(path):
        return ''
    with open(path, 'rb') as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(max(size - max_bytes, 0))
        data = handle.read().decode('utf-8', errors='replace')
    return strip_ansi(data)


def sync_job_state(job):
    session_id = job['id']
    pid_file = job.get('pid_file')
    exit_file = job.get('exit_file')
    proc = LOCAL_PROCESSES.get(session_id)
    if proc is not None and proc.poll() is not None:
        code = proc.returncode
        job['running'] = False
        job['exit_code'] = code
        try:
            with open(exit_file, 'w', encoding='utf-8') as handle:
                handle.write(str(code))
        except Exception:
            pass
        LOCAL_PROCESSES.pop(session_id, None)
    if exit_file and os.path.exists(exit_file):
        try:
            with open(exit_file, 'r', encoding='utf-8') as handle:
                job['exit_code'] = int((handle.read() or '0').strip())
        except Exception:
            job['exit_code'] = job.get('exit_code')
        job['running'] = False
    elif pid_file and os.path.exists(pid_file):
        job['running'] = True
    return job


def get_jobs(include_closed=False):
    global WEB_SHELL_PROCESS, WEB_SHELL_FD
    with STATE_LOCK:
        jobs = load_jobs()
        if 'web-shell' in jobs:
            web_shell = jobs['web-shell']
            web_shell['running'] = WEB_SHELL_PROCESS is not None and WEB_SHELL_PROCESS.poll() is None
            if os.path.exists(WEB_SHELL_CWD_PATH):
                try:
                    web_shell['cwd'] = open(WEB_SHELL_CWD_PATH, 'r', encoding='utf-8').read().strip() or web_shell.get('cwd') or get_preferred_dedsec_root()
                except Exception:
                    pass
            jobs['web-shell'] = web_shell
        for session_id, job in list(jobs.items()):
            if session_id != 'web-shell':
                jobs[session_id] = sync_job_state(job)
                cwd_file = jobs[session_id].get('cwd_file')
                if cwd_file and os.path.exists(cwd_file):
                    try:
                        jobs[session_id]['cwd'] = open(cwd_file, 'r', encoding='utf-8').read().strip() or jobs[session_id].get('cwd')
                    except Exception:
                        pass
        save_jobs(jobs)
        visible = []
        for job in jobs.values():
            if not include_closed and job.get('closed') and job.get('id') != 'web-shell':
                continue
            enriched = dict(job)
            enriched['log_tail'] = read_log_tail(job.get('log_file'))
            visible.append(enriched)
        web_shell = [item for item in visible if item.get('id') == 'web-shell']
        others = sorted([item for item in visible if item.get('id') != 'web-shell'], key=lambda item: item.get('started_at', ''), reverse=True)
        return web_shell + others


def append_session_log(session_id, text):
    with STATE_LOCK:
        jobs = load_jobs()
        job = jobs.get(session_id)
        if not job:
            raise KeyError('Unknown session: ' + session_id)
        log_file = job['log_file']
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'a', encoding='utf-8') as handle:
            handle.write(text)
        save_jobs(jobs)


def ensure_web_shell_session():
    ensure_setup()
    jobs = load_jobs()
    web_shell = jobs['web-shell']
    preferred_cwd = get_preferred_dedsec_root()
    if not os.path.isdir(web_shell.get('cwd') or ''):
        web_shell['cwd'] = preferred_cwd
    web_shell['interactive'] = True
    jobs['web-shell'] = web_shell
    save_jobs(jobs)
    start_web_shell_bridge()
    return web_shell


def start_web_shell_bridge():
    global WEB_SHELL_PROCESS, WEB_SHELL_FD
    if WEB_SHELL_PROCESS is not None and WEB_SHELL_PROCESS.poll() is None and WEB_SHELL_FD is not None:
        return

    cwd = get_preferred_dedsec_root()
    master_fd, slave_fd = pty.openpty()
    env = os.environ.copy()
    env['TERM'] = 'xterm-256color'
    env['PS1'] = ''
    env['PROMPT_COMMAND'] = f'pwd > {WEB_SHELL_CWD_PATH}'

    WEB_SHELL_PROCESS = subprocess.Popen(
        [SHELL_BINARY, '--noprofile', '--norc', '-i'],
        cwd=cwd,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        env=env,
        start_new_session=True,
        close_fds=True,
    )
    os.close(slave_fd)
    WEB_SHELL_FD = master_fd

    jobs = load_jobs()
    web_shell = jobs['web-shell']
    web_shell['running'] = True
    web_shell['interactive'] = True
    web_shell['cwd'] = cwd
    jobs['web-shell'] = web_shell
    save_jobs(jobs)

    def reader():
        global WEB_SHELL_PROCESS, WEB_SHELL_FD
        log_file = web_shell['log_file']
        try:
            while True:
                try:
                    data = os.read(master_fd, 4096)
                except OSError:
                    break
                if not data:
                    break
                with open(log_file, 'a', encoding='utf-8', errors='replace') as handle:
                    handle.write(strip_ansi(data.decode('utf-8', errors='replace')))
        finally:
            code = WEB_SHELL_PROCESS.wait() if WEB_SHELL_PROCESS and WEB_SHELL_PROCESS.poll() is None else (WEB_SHELL_PROCESS.returncode if WEB_SHELL_PROCESS else 0)
            jobs = load_jobs()
            if 'web-shell' in jobs:
                jobs['web-shell']['running'] = False
                jobs['web-shell']['exit_code'] = code
                save_jobs(jobs)
            try:
                os.close(master_fd)
            except Exception:
                pass
            WEB_SHELL_FD = None

    threading.Thread(target=reader, daemon=True).start()


def web_shell_current_cwd():
    if os.path.exists(WEB_SHELL_CWD_PATH):
        try:
            value = open(WEB_SHELL_CWD_PATH, 'r', encoding='utf-8').read().strip()
            if value:
                return value
        except Exception:
            pass
    jobs = load_jobs()
    return jobs.get('web-shell', {}).get('cwd') or get_preferred_dedsec_root()


def queue_web_shell_command(command, echo_prompt=True):
    start_web_shell_bridge()
    cwd = web_shell_current_cwd()
    config = load_config()
    username = config.get('display_name') or os.environ.get('USER') or 'user'
    if echo_prompt:
        append_session_log('web-shell', now_prompt(username, cwd) + ' ' + command + '\n')
    os.write(WEB_SHELL_FD, (command + '\n').encode('utf-8', errors='replace'))
    jobs = load_jobs()
    return jobs.get('web-shell')



def start_interactive_shell_session(cwd=None, label='Shell Session'):
    cwd = safe_realpath(cwd or web_shell_current_cwd() or get_preferred_dedsec_root(), must_exist=True, allow_empty=True)
    job = create_job(label=label, command='bash', cwd=cwd, kind='shell', real_termux=False)
    cwd_file = os.path.join(RUNTIME_DIR, job['id'] + '.cwd')
    master_fd, slave_fd = pty.openpty()
    env = os.environ.copy()
    env['TERM'] = 'xterm-256color'
    env['PS1'] = ''
    env['PROMPT_COMMAND'] = f'pwd > {cwd_file}'

    process = subprocess.Popen(
        [SHELL_BINARY, '--noprofile', '--norc', '-i'],
        cwd=cwd,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        env=env,
        start_new_session=True,
        close_fds=True,
    )
    os.close(slave_fd)
    LOCAL_PROCESSES[job['id']] = process
    LOCAL_TTYS[job['id']] = master_fd
    job['interactive'] = True
    job['cwd_file'] = cwd_file
    with STATE_LOCK:
        jobs = load_jobs()
        jobs[job['id']] = job
        save_jobs(jobs)

    def reader():
        log_file = job['log_file']
        try:
            while True:
                try:
                    data = os.read(master_fd, 4096)
                except OSError:
                    break
                if not data:
                    break
                with open(log_file, 'a', encoding='utf-8', errors='replace') as handle:
                    handle.write(strip_ansi(data.decode('utf-8', errors='replace')))
        finally:
            code = process.wait() if process.poll() is None else process.returncode
            with STATE_LOCK:
                jobs = load_jobs()
                if job['id'] in jobs:
                    jobs[job['id']]['running'] = False
                    jobs[job['id']]['exit_code'] = code
                    save_jobs(jobs)
            LOCAL_PROCESSES.pop(job['id'], None)
            LOCAL_TTYS.pop(job['id'], None)
            try:
                os.close(master_fd)
            except Exception:
                pass

    threading.Thread(target=reader, daemon=True).start()
    append_session_log(job['id'], now_prompt(load_config().get('display_name') or 'user', cwd) + '\n')
    return job


def send_raw_input(session_id, raw_input):
    if raw_input is None:
        raise ValueError('Input cannot be empty.')
    if not isinstance(raw_input, str):
        raw_input = str(raw_input)
    if raw_input == '':
        return get_jobs()[0]
    with STATE_LOCK:
        jobs = load_jobs()
        session = jobs.get(session_id) or jobs.get('web-shell')
        if not session:
            raise KeyError('Session not found.')
        if session_id == 'web-shell' or session.get('kind') == 'web-shell':
            start_web_shell_bridge()
            os.write(WEB_SHELL_FD, raw_input.encode('utf-8', errors='replace'))
            return jobs.get('web-shell')
        if session.get('running') and session_id in LOCAL_TTYS:
            os.write(LOCAL_TTYS[session_id], raw_input.encode('utf-8', errors='replace'))
            return session
        raise ValueError('This session is not accepting input right now.')


def create_job(label, command, cwd, kind='process', real_termux=False):
    session_id = next_session_id('job')
    log_file = os.path.join(LOGS_DIR, session_id + '.log')
    pid_file = os.path.join(PIDS_DIR, session_id + '.pid')
    exit_file = os.path.join(EXITS_DIR, session_id + '.exit')
    job = {
        'id': session_id,
        'label': label,
        'command': command,
        'started_at': now_iso(),
        'log_file': log_file,
        'pid_file': pid_file,
        'exit_file': exit_file,
        'running': True,
        'exit_code': None,
        'real_termux': real_termux,
        'cwd': cwd,
        'cwd_file': '',
        'interactive': False,
        'kind': kind,
        'closed': False
    }
    with STATE_LOCK:
        jobs = load_jobs()
        jobs[session_id] = job
        save_jobs(jobs)
    with open(log_file, 'w', encoding='utf-8') as handle:
        handle.write('[' + now_iso() + '] Starting: ' + command + '\n')
    return job


def build_wrapper_script(job, shell_command, cwd):
    wrapper_path = os.path.join(WRAPPERS_DIR, job['id'] + '.sh')
    content = """#!/data/data/com.termux/files/usr/bin/bash
set +e
LOGFILE=%s
PIDFILE=%s
EXITFILE=%s
mkdir -p %s %s %s
cd %s || {
  echo \"Failed to enter working directory: %s\" >> \"$LOGFILE\"
  echo 1 > \"$EXITFILE\"
  exit 1
}
echo $$ > \"$PIDFILE\"
echo \"[%s] Running: %s\" >> \"$LOGFILE\"
%s >> \"$LOGFILE\" 2>&1
CODE=$?
echo \"[%s] Exit code: $CODE\" >> \"$LOGFILE\"
echo \"$CODE\" > \"$EXITFILE\"
rm -f \"$PIDFILE\"
exit \"$CODE\"
""" % (
        shlex.quote(job['log_file']),
        shlex.quote(job['pid_file']),
        shlex.quote(job['exit_file']),
        shlex.quote(LOGS_DIR),
        shlex.quote(PIDS_DIR),
        shlex.quote(EXITS_DIR),
        shlex.quote(cwd),
        cwd.replace('"', ''),
        now_iso(),
        shell_command.replace('"', '\\"'),
        shell_command,
        now_iso(),
    )
    with open(wrapper_path, 'w', encoding='utf-8') as handle:
        handle.write(content)
    os.chmod(wrapper_path, 0o700)
    return wrapper_path


def try_termux_session(wrapper_path, cwd):
    am_binary = shutil.which('am') or '/system/bin/am'
    if not os.path.exists(am_binary):
        return False, 'Android am command not available.'
    attempts = [
        [
            am_binary, 'startservice', '--user', '0',
            '-n', 'com.termux/com.termux.app.RunCommandService',
            '-a', 'com.termux.RUN_COMMAND',
            '--es', 'com.termux.RUN_COMMAND_PATH', wrapper_path,
            '--es', 'com.termux.RUN_COMMAND_WORKDIR', cwd,
            '--ez', 'com.termux.RUN_COMMAND_BACKGROUND', 'false',
            '--es', 'com.termux.RUN_COMMAND_SESSION_ACTION', '0'
        ],
        [
            am_binary, 'start-foreground-service', '--user', '0',
            '-n', 'com.termux/com.termux.app.RunCommandService',
            '-a', 'com.termux.RUN_COMMAND',
            '--es', 'com.termux.RUN_COMMAND_PATH', wrapper_path,
            '--es', 'com.termux.RUN_COMMAND_WORKDIR', cwd,
            '--ez', 'com.termux.RUN_COMMAND_BACKGROUND', 'false'
        ]
    ]
    last_output = 'No Termux RUN_COMMAND attempt was made.'
    for command in attempts:
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=8)
            last_output = (result.stdout or '') + '\n' + (result.stderr or '')
            if result.returncode != 0:
                continue
            pid_path = wrapper_path.replace('/wrappers/', '/pids/').replace('.sh', '.pid')
            exit_path = wrapper_path.replace('/wrappers/', '/exits/').replace('.sh', '.exit')
            for _ in range(16):
                time.sleep(0.25)
                if os.path.exists(pid_path) or os.path.exists(exit_path):
                    return True, last_output.strip()
        except Exception as exc:
            last_output = str(exc)
    return False, last_output.strip()


def start_local_subprocess(job, wrapper_path, cwd):
    process = subprocess.Popen(
        [SHELL_BINARY, wrapper_path],
        cwd=cwd,
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )
    LOCAL_PROCESSES[job['id']] = process
    return process


def launch_job(label, shell_command, cwd, kind='process', prefer_termux=False):
    cwd = safe_realpath(cwd, must_exist=True, allow_empty=True)
    job = create_job(label=label, command=shell_command, cwd=cwd, kind=kind, real_termux=False)
    wrapper_path = build_wrapper_script(job, shell_command, cwd)
    if prefer_termux:
        success, detail = try_termux_session(wrapper_path, cwd)
        if success:
            job['real_termux'] = True
            with STATE_LOCK:
                jobs = load_jobs()
                jobs[job['id']] = job
                save_jobs(jobs)
            if detail:
                append_session_log(job['id'], '[Termux session] ' + detail + '\n')
            return job
        append_session_log(job['id'], '[Termux session failed, using local fallback] ' + detail + '\n')
    start_local_subprocess(job, wrapper_path, cwd)
    return job


def deduce_run_command(path):
    basename = os.path.basename(path)
    quoted = shlex.quote(path)
    if basename.endswith('.py'):
        return 'python3 ' + quoted
    if basename.endswith('.sh') or basename.endswith('.bash'):
        return 'bash ' + quoted
    if os.access(path, os.X_OK):
        return quoted
    raise ValueError('File is not runnable: ' + path)


def run_dedsec_script(target_path):
    path = safe_realpath(target_path, must_exist=True)
    if not os.path.isfile(path):
        raise FileNotFoundError('Script not found: ' + path)
    command = deduce_run_command(path)
    return queue_web_shell_command('cd ' + shlex.quote(os.path.dirname(path)) + ' && ' + command)


def run_store_program(program_id, action):
    entry = next((item for item in PROGRAM_CATALOG if item['id'] == program_id), None)
    if not entry:
        raise KeyError('Unknown program: ' + program_id)
    key_map = {
        'install': 'install_command',
        'run': 'run_command',
        'delete': 'delete_command',
        'update': 'update_command'
    }
    command_key = key_map.get(action)
    if not command_key:
        raise ValueError('Unsupported action: ' + action)
    shell_command = entry[command_key]
    return launch_job(label='Store: ' + entry['name'] + ' [' + action + ']', shell_command=shell_command, cwd=HOME_DIR, kind='store-' + action, prefer_termux=False)


def kill_pid_tree(pid, sig=signal.SIGTERM):
    try:
        os.killpg(os.getpgid(pid), sig)
        return
    except Exception:
        pass
    try:
        os.kill(pid, sig)
    except Exception:
        pass


def stop_web_shell_bridge():
    global WEB_SHELL_PROCESS, WEB_SHELL_FD
    proc = WEB_SHELL_PROCESS
    fd = WEB_SHELL_FD
    WEB_SHELL_PROCESS = None
    WEB_SHELL_FD = None
    if fd is not None:
        try:
            os.close(fd)
        except Exception:
            pass
    if proc is not None:
        try:
            kill_pid_tree(proc.pid)
        except Exception:
            pass


def collect_termux_session_pids(exclude=None):
    exclude = {int(item) for item in (exclude or []) if str(item).strip().isdigit()}
    candidates = set()
    try:
        result = subprocess.run(['ps', '-A', '-o', 'PID=,ARGS='], capture_output=True, text=True, timeout=6)
        lines = (result.stdout or '').splitlines()
    except Exception:
        lines = []
    patterns = (
        '/data/data/com.termux/files/usr/bin/bash',
        '/data/data/com.termux/files/usr/bin/sh',
        '/data/data/com.termux/files/usr/bin/zsh',
        '/data/data/com.termux/files/usr/bin/fish',
        'dedsec_os_server.py',
        '/runtime/wrappers/',
        'com.termux.app.RunCommandService'
    )
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) < 2:
            continue
        try:
            pid = int(parts[0])
        except Exception:
            continue
        if pid in exclude:
            continue
        args = parts[1]
        if any(pattern in args for pattern in patterns):
            candidates.add(pid)
    for local in list(LOCAL_PROCESSES.values()):
        if local and getattr(local, 'pid', None) and local.pid not in exclude:
            candidates.add(local.pid)
    if WEB_SHELL_PROCESS and getattr(WEB_SHELL_PROCESS, 'pid', None) and WEB_SHELL_PROCESS.pid not in exclude:
        candidates.add(WEB_SHELL_PROCESS.pid)
    return sorted(candidates)


def unlock_termux_gate():
    try:
        os.makedirs(os.path.dirname(UNLOCK_FLAG_PATH), exist_ok=True)
        with open(UNLOCK_FLAG_PATH, 'w', encoding='utf-8') as handle:
            handle.write(now_iso())
    except Exception:
        pass


def force_stop_android_package(package_name):
    am_bin = shutil.which('am') or '/system/bin/am'
    if not os.path.exists(am_bin):
        return False
    try:
        subprocess.run([am_bin, 'force-stop', package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=6)
        return True
    except Exception:
        return False


def delayed_system_exit(server_pid):
    time.sleep(0.35)
    with STATE_LOCK:
        job_ids = [item for item in load_jobs().keys() if item != 'web-shell']
    for job_id in job_ids:
        try:
            stop_job(job_id, close_only=False)
        except Exception:
            pass
    try:
        stop_web_shell_bridge()
    except Exception:
        pass
    for pid in collect_termux_session_pids(exclude={os.getpid(), server_pid}):
        kill_pid_tree(pid)
    try:
        if os.path.exists(JOBS_PATH):
            os.remove(JOBS_PATH)
    except Exception:
        pass
    # Stop Termux API first, then stop Termux itself.
    try:
        force_stop_android_package('com.termux.api')
    except Exception:
        pass
    time.sleep(0.18)
    try:
        force_stop_android_package('com.termux')
    except Exception:
        pass
    try:
        kill_pid_tree(server_pid)
    except Exception:
        os._exit(0)


def request_system_exit():
    threading.Thread(target=delayed_system_exit, args=(os.getpid(),), daemon=True).start()
    return {'status': 'shutting_down'}


def stop_job(session_id, close_only=False):
    with STATE_LOCK:
        jobs = load_jobs()
        job = jobs.get(session_id)
        if not job:
            raise KeyError('Unknown session: ' + session_id)
        if session_id == 'web-shell':
            if close_only:
                return job
            raise ValueError('Web Shell cannot be removed.')
        pid = None
        pid_file = job.get('pid_file')
        if pid_file and os.path.exists(pid_file):
            try:
                with open(pid_file, 'r', encoding='utf-8') as handle:
                    pid = int((handle.read() or '0').strip())
            except Exception:
                pid = None
        proc = LOCAL_PROCESSES.get(session_id)
        tty_fd = LOCAL_TTYS.get(session_id)
        if proc is not None and proc.poll() is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except Exception:
                try:
                    proc.terminate()
                except Exception:
                    pass
        if tty_fd is not None:
            try:
                os.close(tty_fd)
            except Exception:
                pass
            LOCAL_TTYS.pop(session_id, None)
        if pid:
            try:
                os.killpg(pid, signal.SIGTERM)
            except Exception:
                try:
                    os.kill(pid, signal.SIGTERM)
                except Exception:
                    pass
        job['running'] = False
        if close_only:
            job['closed'] = True
        jobs[session_id] = job
        save_jobs(jobs)
        append_session_log(session_id, '[Session stop requested]\n')
        return job


def run_web_shell_command(session_id, command):
    if command is None or not str(command).strip():
        raise ValueError('Command cannot be empty.')
    with STATE_LOCK:
        jobs = load_jobs()
        session = jobs.get(session_id) or jobs.get('web-shell')
        if not session:
            raise KeyError('Session not found.')
        if session.get('kind') != 'web-shell':
            if session.get('running') and session_id in LOCAL_TTYS:
                os.write(LOCAL_TTYS[session_id], (str(command) + '\n').encode('utf-8', errors='replace'))
                return session
            raise ValueError('This session is not accepting input right now.')
        if str(command).strip() == 'clear':
            with open(session['log_file'], 'w', encoding='utf-8') as handle:
                handle.write('')
            return queue_web_shell_command('clear', echo_prompt=False)
        return queue_web_shell_command(str(command))



def collect_battery_status():
    if shutil.which('termux-battery-status'):
        try:
            result = subprocess.run(['termux-battery-status'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                return {'ok': True, 'percentage': data.get('percentage'), 'status': data.get('status') or 'Unknown'}
        except Exception:
            pass
    return {'ok': False, 'percentage': None, 'status': 'Unavailable'}

def collect_notifications():
    if shutil.which('termux-notification-list'):
        try:
            result = subprocess.run(['termux-notification-list'], capture_output=True, text=True, timeout=8)
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                items = data if isinstance(data, list) else []
                cleaned=[]
                for item in items[:30]:
                    if not isinstance(item, dict):
                        continue
                    cleaned.append({'title': str(item.get('title') or item.get('packageName') or 'Notification'), 'text': str(item.get('content') or item.get('text') or ''), 'package': str(item.get('packageName') or '')})
                return {'ok': True, 'items': cleaned}
        except Exception:
            pass
    return {'ok': False, 'items': []}

def collect_info():
    config = load_config()
    uname = os.uname()
    return {
        'server_time': now_iso(),
        'username': os.environ.get('USER') or 'termux',
        'display_name': config.get('display_name') or active_username(),
        'home_dir': user_workspace_path(),
        'dedsec_root': get_preferred_dedsec_root(),
        'language': load_language_preference(),
        'platform': uname.sysname,
        'release': uname.release,
        'machine': uname.machine,
        'termux_prefix': os.environ.get('PREFIX', '/data/data/com.termux/files/usr'),
        'wallpaper': config.get('wallpaper', '')
    }


def send_json(handler, status_code, payload, extra_headers=None):
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    handler.send_response(status_code)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Content-Length', str(len(data)))
    handler.send_header('Cache-Control', 'no-store')
    for key, value in (extra_headers or []):
        handler.send_header(key, value)
    handler.end_headers()
    handler.wfile.write(data)


def parse_json_body(handler):
    length = int(handler.headers.get('Content-Length', '0') or '0')
    raw = handler.rfile.read(length) if length > 0 else b'{}'
    if not raw:
        return {}
    try:
        return json.loads(raw.decode('utf-8'))
    except json.JSONDecodeError as exc:
        raise ValueError('Invalid JSON body: ' + str(exc))


INDEX_HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5, user-scalable=yes, viewport-fit=cover">
  <title>DedSec OS</title>
  <style>
    :root {
      --bg: #000000;
      --panel: rgba(18, 18, 30, 0.52);
      --panel-alt: rgba(14, 14, 24, 0.58);
      --menu-solid: rgba(10, 10, 18, 0.94);
      --border: rgba(205, 147, 255, 0.50);
      --hover-border: rgba(87,214,255,0.35);
      --cyan: #cd93ff;
      --purple: #cd93ff;
      --text: rgba(255, 255, 255, 0.92);
      --muted: rgba(255, 255, 255, 0.74);
      --danger: #ff6b6b;
      --success: #51cf66;
      --warning: #ffd43b;
      --shadow: 0 18px 50px rgba(0,0,0,0.42);
      --holo-lavender: rgba(216,170,255,0.18);
      --holo-gold: rgba(255,198,122,0.10);
      --holo-pink: rgba(255,169,214,0.10);
      --holo-white: rgba(255,255,255,0.05);
      --terminal-bg: #000000;
      --terminal-fg: #f5f7ff;
      --terminal-accent: #cd93ff;
      --sidebar-width: 126px;
      --dock-h: 88px;
      --font-primary: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
      --font-secondary: 'Orbitron', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
      --font-mono: 'Roboto Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
    }
    * { box-sizing: border-box; }
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: var(--bg); border-left: 1px solid var(--border); }
    ::-webkit-scrollbar-thumb { background: var(--border); border: 2px solid var(--bg); }
    ::-webkit-scrollbar-thumb:hover { background: var(--purple); }
    html, body { min-height: 100%; height: auto; margin: 0; font-family: var(--font-primary); background: var(--bg); color: var(--text); overflow-x: hidden; overflow-y: auto; touch-action: pinch-zoom pan-x pan-y; }
    body {
      background-size: cover;
      background-position: center;
      background-repeat: no-repeat;
      overflow-x: hidden;
      overflow-y: auto;
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      background:
        radial-gradient(1200px 420px at 10% -10%, var(--holo-lavender), transparent 60%),
        radial-gradient(900px 320px at 110% 10%, var(--holo-gold), transparent 55%),
        radial-gradient(800px 280px at 40% 120%, var(--holo-pink), transparent 55%),
        linear-gradient(180deg, color-mix(in srgb, var(--bg) 62%, transparent), color-mix(in srgb, var(--bg) 88%, black 12%));
      pointer-events: none;
      z-index: 0;
    }
    #loading { display: none !important; }
    #loading.hidden { opacity: 0; visibility: hidden; pointer-events: none; }
    .spinner {
      width: 56px;
      height: 56px;
      border-radius: 50%;
      border: 3px solid rgba(255,255,255,0.12);
      border-top-color: var(--cyan);
      animation: spin 1s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    #toast {
      position: fixed;
      left: 50%;
      top: 16px;
      transform: translateX(-50%);
      z-index: 9998;
      max-width: min(92vw, 560px);
      padding: 12px 16px;
      border-radius: 14px;
      background: color-mix(in srgb, var(--menu-solid) 94%, black 6%);
      border: 1px solid var(--border);
      box-shadow: var(--shadow);
      color: var(--text);
      opacity: 0;
      pointer-events: none;
      transition: opacity .18s ease, transform .18s ease;
    }
    #toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
    #showSidebarBtn { position: fixed; right: 8px; top: 50%; transform: translateY(-50%); z-index: 60; display: none; min-height: 56px; border-top-right-radius: 0; border-bottom-right-radius: 0; }
    #showSidebarBtn.show-sidebar-visible { display: inline-flex; }
    #app.sidebar-hidden { padding-right: 14px !important; }
    #app.sidebar-hidden .topbar { transform: translateX(150%); pointer-events: none; }
    #app {
      position: relative;
      z-index: 1;
      display: flex;
      flex-direction: column;
      min-height: 100svh;
      padding: 14px calc(var(--sidebar-width) + 28px) 18px 14px;
      gap: 12px;
      background-image: radial-gradient(1200px 420px at 10% -10%, var(--holo-lavender), transparent 60%), radial-gradient(900px 320px at 110% 10%, var(--holo-gold), transparent 55%), radial-gradient(800px 280px at 40% 120%, var(--holo-pink), transparent 55%), linear-gradient(180deg, var(--panel-alt), var(--panel-alt));
    }
    .topbar {
      position: fixed;
      top: 14px;
      right: 14px;
      bottom: 14px;
      width: var(--sidebar-width);
      z-index: 40;
      display: flex;
      flex-direction: column;
      align-items: stretch;
      justify-content: flex-start;
      gap: 10px;
      padding: 14px 10px;
      background: var(--menu-solid);
      border: 1px solid var(--border);
      border-radius: 22px;
      backdrop-filter: blur(14px);
      box-shadow: var(--shadow);
      overflow: auto;
    }
    .topbar::before {
      content: "";
      position: absolute;
      inset: 0;
      background:
        radial-gradient(900px 240px at 15% 0%, var(--holo-lavender), transparent 60%),
        radial-gradient(700px 220px at 85% 0%, var(--holo-gold), transparent 58%),
        linear-gradient(180deg, var(--holo-white), transparent 60%);
      pointer-events: none;
      z-index: 0;
      border-radius: inherit;
    }
    .topbar > * { position: relative; z-index: 1; }
    .brand { display: flex; flex-direction: column; align-items: center; gap: 10px; min-width: 0; text-align:center; }
    .brand svg { width: 28px; height: 28px; flex: 0 0 auto; }
    .brand-title { font-size: 0.98rem; font-weight: 700; letter-spacing: 0.02em; line-height: 1.05; white-space: normal; word-break: break-word; overflow-wrap: anywhere; }
    .topbar-right { display:flex; flex-direction:column; align-items:stretch; gap:8px; margin-left:0; }
    .topbar-right .btn.small { width: 100%; min-width: 0; min-height: 46px; padding: 10px 8px; white-space: normal; overflow-wrap: anywhere; word-break: break-word; hyphens: auto; line-height: 1.2; text-align: center; display: inline-flex; align-items: center; justify-content: center; }
    .subtle { font-size: 0.75rem; color: var(--muted); max-width: 100%; overflow-wrap: anywhere; word-break: break-word; }
    .desktop {
      display: flex;
      flex-direction: column;
      gap: 12px;
      min-height: calc(100svh - 132px);
      flex: 1;
    }
    .screen {
      display: none;
      min-height: calc(100svh - 168px);
      flex: 1;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 26px;
      box-shadow: var(--shadow);
      overflow: hidden;
      backdrop-filter: blur(14px);
      background-image: radial-gradient(900px 240px at 15% 0%, var(--holo-lavender), transparent 60%), radial-gradient(700px 220px at 85% 0%, var(--holo-gold), transparent 58%), linear-gradient(180deg, var(--holo-white), transparent 60%);
    }
    .screen.active { display: flex; flex-direction: column; }
    .screen-header {
      padding: 14px 16px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
      min-width: 0;
    }
    .screen-title { font-size: 1rem; font-weight: 700; max-width: 100%; overflow-wrap: anywhere; word-break: break-word; }
    .toolbar, .stack, .panel-stack { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
    .screen-body {
      padding: 14px;
      overflow: auto;
      display: flex;
      flex-direction: column;
      gap: 14px;
      min-height: 0;
      height: 100%;
    }
    .panel {
      background: var(--panel-alt);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .grid { display: grid; gap: 12px; }
    .grid.apps { grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); }
    .grid.info { grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }
    .app-card, .info-card, .store-card {
      background:
        radial-gradient(1200px 420px at 10% -10%, var(--holo-lavender), transparent 60%),
        radial-gradient(900px 320px at 110% 10%, var(--holo-gold), transparent 55%),
        radial-gradient(800px 280px at 40% 120%, var(--holo-pink), transparent 55%),
        linear-gradient(120deg, transparent 0%, rgba(255,255,255,0.14) 45%, transparent 72%),
        rgba(14, 14, 24, 0.58);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 14px;
      box-shadow: 0 10px 28px rgba(0, 0, 0, 0.22);
      min-width: 0;
      max-width: 100%;
      overflow: hidden;
    }
    .app-card { display: flex; flex-direction: column; gap: 10px; align-items: flex-start; color: var(--text); }
    .app-card svg, .dock-btn svg, .screen-header svg { width: 24px; height: 24px; color: var(--text); }
    .app-card h3, .store-card h3, .info-card h3 { margin: 0; font-size: 0.95rem; color: var(--text); max-width: 100%; overflow-wrap: break-word; word-break: normal; }
    .app-card p, .store-card p, .info-card p { margin: 0; color: var(--muted); font-size: 0.82rem; line-height: 1.35; max-width: 100%; overflow-wrap: anywhere; word-break: normal; white-space: normal; }
    .info-card .info-key { font-weight: 700; color: var(--text); }
    .info-card .info-value { color: var(--muted); overflow-wrap: anywhere; word-break: normal; white-space: normal; line-height: 1.35; }
    .dock {
      position: fixed;
      top: 86px;
      right: 14px;
      width: min(340px, calc(100vw - 28px));
      background: color-mix(in srgb, var(--panel) 92%, black 8%);
      border: 1px solid var(--border);
      border-radius: 22px;
      display: none;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
      padding: 12px;
      backdrop-filter: blur(16px);
      box-shadow: var(--shadow);
      z-index: 20;
    }
    .dock.open { display: grid; }
    #dock, #menuOverlay { display:none !important; }
    .dock-btn {
      border: 0;
      background: transparent;
      color: var(--text);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 6px;
      border-radius: 18px;
      padding: 6px 4px;
      min-width: 0;
      cursor: pointer;
    }
    .dock-btn span { font-size: 0.8rem; line-height: 1.15; text-align: center; word-break: break-word; }
    .dock-btn.active, .dock-btn:hover { background: var(--purple); color: #0b0a12; box-shadow: none; }
    button, input, textarea, select {
      font: inherit;
    }
    .btn, .file-btn {
      border: 1px solid var(--border);
      background: var(--panel);
      color: var(--text);
      border-radius: 14px;
      padding: 10px 12px;
      cursor: pointer;
      min-height: 40px;
      white-space: normal;
      overflow-wrap: anywhere;
      word-break: break-word;
      hyphens: auto;
      line-height: 1.24;
    }
    .btn:hover, .file-btn:hover { border-color: var(--hover-border); background: color-mix(in srgb, var(--terminal-accent) 14%, transparent); }
    .btn.primary { background: var(--purple); border-color: var(--purple); color: #0b0a12; font-weight: 700; }
    .btn.danger { background: rgba(255,111,145,0.12); color: #ffd6df; border-color: rgba(255,111,145,0.35); }
    .btn.small, .file-btn { padding: 8px 10px; font-size: 0.78rem; min-height: 34px; }
    .btn:disabled { opacity: 0.55; cursor: not-allowed; }
    select {
      width: 100%;
      background: color-mix(in srgb, var(--panel-alt) 90%, var(--bg) 10%);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 12px 14px;
      outline: none;
    }
    .field, .field textarea, .field input {
      width: 100%;
    }
    .field {
      display: flex;
      flex-direction: column;
      gap: 8px;
      min-width: 0;
    }
    .field label { font-size: 0.78rem; color: var(--muted); white-space: normal; overflow-wrap: anywhere; word-break: break-word; line-height: 1.28; }
    input[type="text"], input[type="password"], textarea, input[type="file"] {
      width: 100%;
      background: color-mix(in srgb, var(--panel-alt) 90%, var(--bg) 10%);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 12px 14px;
      outline: none;
    }
    textarea { min-height: 180px; resize: vertical; }
    .pathbar {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      background: rgba(3, 6, 12, 0.72);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 10px 12px;
      font-size: 0.78rem;
      color: var(--muted);
      word-break: normal;
      overflow-wrap: anywhere;
      white-space: normal;
      max-width: 100%;
    }
    .file-list, .terminal-tabs, .store-list { display: flex; flex-direction: column; gap: 10px; }
    .file-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 10px;
      background: rgba(5, 9, 17, 0.78);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 12px;
    }
    .file-row-top { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
    .file-name { font-weight: 600; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .file-meta { color: var(--muted); font-size: 0.76rem; }
    .file-actions { display: flex; flex-wrap: wrap; gap: 8px; }
    .terminal-wrap {
      position: relative;
      display: grid;
      grid-template-rows: minmax(340px, 1fr) auto;
      gap: 12px;
      min-height: 0;
      height: 100%;
      background: var(--terminal-bg);
      border-radius: 18px;
      padding: 12px;
    }
    #terminalTabs, #terminalPrompt { display: none !important; }
    #terminalComposer {
      position: absolute;
      left: -9999px;
      width: 1px;
      height: 1px;
      opacity: 0.01;
    }
    .extra-keys {
      display: grid;
      grid-template-columns: repeat(7, minmax(0, 1fr));
      gap: 8px;
    }
    .extra-key {
      border: 1px solid var(--border);
      background: color-mix(in srgb, var(--panel) 90%, transparent);
      color: var(--text);
      border-radius: 12px;
      min-height: 38px;
      padding: 8px 6px;
      font: inherit;
      cursor: pointer;
    }
    .extra-key.wide { grid-column: span 2; }
    .extra-key.active, .extra-key:hover { background: color-mix(in srgb, var(--terminal-accent) 18%, transparent); border-color: color-mix(in srgb, var(--terminal-accent) 72%, var(--border)); }
    .terminal-tabs { flex-direction: row; overflow-x: auto; padding-bottom: 4px; }
    .tab {
      border: 1px solid var(--border);
      background: var(--panel);
      color: var(--text);
      border-radius: 14px;
      padding: 10px 12px;
      min-width: max-content;
      cursor: pointer;
      text-align: left;
    }
    .tab.active { background: color-mix(in srgb, var(--terminal-accent) 22%, transparent); border-color: color-mix(in srgb, var(--terminal-accent) 52%, var(--border)); }
    .terminal-screen {
      background: transparent;
      color: var(--terminal-fg);
      border-radius: 0;
      border: 0;
      padding: 0;
      margin: 0;
      overflow: auto;
      white-space: pre-wrap;
      font-family: "Cascadia Code", "Fira Code", "Courier New", monospace;
      font-size: 0.85rem;
      line-height: 1.5;
      min-height: 340px;
      max-height: calc(100svh - 310px);
      outline: none;
    }
    .terminal-screen:focus { outline: none; }
    .prompt {
      color: var(--cyan);
      font-family: "Cascadia Code", "Fira Code", "Courier New", monospace;
      font-size: 0.82rem;
      word-break: break-word;
      overflow-wrap: anywhere;
      white-space: pre-wrap;
    }
    .terminal-input-row {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
    }
    .terminal-input-row input { min-width: 0; }
    .sessions-overlay {
      position: absolute;
      inset: 0;
      background: color-mix(in srgb, var(--bg) 74%, transparent);
      backdrop-filter: blur(10px);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 10px;
      z-index: 8;
      border-radius: 22px;
    }
    .sessions-panel {
      width: min(100%, 560px);
      max-height: min(80svh, 640px);
      overflow: auto;
      background: #0e0d18;
      border: 1px solid var(--border);
      border-radius: 22px;
      padding: 14px;
      box-shadow: var(--shadow);
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .sessions-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }
    .store-card { display: flex; flex-direction: column; gap: 12px; }
    #notificationsPanel {
      position: fixed;
      top: 14px;
      right: 126px;
      width: min(360px, calc(100vw - 146px));
      max-height: calc(100svh - 28px);
      overflow: auto;
      background: rgba(10,10,18,0.96);
      border: 1px solid var(--border);
      border-radius: 22px;
      padding: 12px;
      z-index: 30;
      box-shadow: var(--shadow);
    }
    .notif-item { background: rgba(14,14,24,0.85); border:1px solid var(--border); border-radius:16px; padding:10px; display:flex; flex-direction:column; gap:4px; margin-bottom:8px; }
    .notif-title { font-weight:700; font-size:0.86rem; }
    .notif-text,.notif-package { color: var(--muted); font-size:0.76rem; line-height:1.3; word-break: break-word; }
    .store-actions { display: flex; flex-wrap: wrap; gap: 8px; }
    .pathbar, .file-name, .file-meta, .screen-title, .subtle, .info-card h3, .info-card p, .app-card h3, .app-card p, .store-card h3, .store-card p {
      white-space: normal;
      word-break: break-word;
      overflow-wrap: anywhere;
      min-width: 0;
    }
    .info-card, .app-card, .store-card, .panel, .screen-body, .screen-header, .stack, .toolbar { min-width: 0; }
    .login-overlay { position: fixed; inset: 0; z-index: 9997; display: flex; align-items: center; justify-content: center; padding: 18px; background: color-mix(in srgb, var(--bg) 78%, transparent); backdrop-filter: blur(14px); }
    .login-card { width: min(100%, 420px); background: var(--menu-solid); border: 1px solid var(--border); border-radius: 24px; padding: 18px; box-shadow: var(--shadow); display: flex; flex-direction: column; gap: 14px; background-image: radial-gradient(900px 240px at 15% 0%, var(--holo-lavender), transparent 60%), radial-gradient(700px 220px at 85% 0%, var(--holo-gold), transparent 58%), linear-gradient(180deg, var(--holo-white), transparent 60%); }
    .login-card .screen-title { font-size: 1.05rem; color: var(--text); }
    .login-card .panel { background: color-mix(in srgb, var(--panel) 88%, var(--menu-solid) 12%); }
    .login-note { color: var(--muted); font-size: 0.82rem; line-height: 1.4; }
    .login-card input, .login-card select, .login-card textarea { color: var(--text); background: color-mix(in srgb, var(--panel-alt) 90%, var(--bg) 10%); }
    .login-card input::placeholder, .login-card textarea::placeholder { color: var(--muted); opacity: 0.92; }
    .hidden { display: none !important; }
    @media (max-width: 640px) {
      :root { --sidebar-width: 128px; }
      #app { padding: 10px calc(var(--sidebar-width) + 16px) 14px 10px; }
      .topbar { top: 10px; right: 10px; bottom: 10px; width: var(--sidebar-width); padding: 10px 8px; border-radius: 18px; }
      .screen { min-height: 72svh; border-radius: 20px; }
      .screen-body { padding: 12px; }
      .info-card, .app-card, .store-card { padding: 12px; }
      .dock { top: 74px; right: 10px; width: min(320px, calc(100vw - 20px)); grid-template-columns: repeat(2, 1fr); gap: 6px; padding: 8px; border-radius: 22px; }
      .dock-btn { min-height: 62px; }
      .dock-btn span { font-size: 0.68rem; }
      .terminal-screen { min-height: 300px; max-height: calc(100svh - 282px); }
      .extra-keys { grid-template-columns: repeat(4, minmax(0, 1fr)); }
    }
    @media (min-width: 880px) {
      .screen-body.split {
        display: grid;
        grid-template-columns: 1.05fr 1fr;
        align-items: start;
      }
      .file-row {
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: center;
      }
    }
  </style>
  <script>
    (function() {
      var themeName = __BOOT_THEME__;
      var themes = {
        dedsec: { bg: '#000000', fg: '#f5f7ff', accent: '#cd93ff', purple: '#cd93ff', border: 'rgba(205,147,255,0.50)', panel: 'rgba(18,18,30,0.52)', panelAlt: 'rgba(14,14,24,0.58)', menu: 'rgba(10,10,18,0.94)', holo1: 'rgba(216,170,255,0.18)', holo2: 'rgba(255,198,122,0.10)', holo3: 'rgba(255,169,214,0.10)', holo4: 'rgba(255,255,255,0.05)', hover: 'rgba(87,214,255,0.35)', bgMain: '#04050a' },
        cyan: { bg: '#031017', fg: '#def9ff', accent: '#57d6ff', purple: '#57d6ff', border: 'rgba(87,214,255,0.44)', panel: 'rgba(8,20,28,0.60)', panelAlt: 'rgba(6,16,24,0.66)', menu: 'rgba(4,14,22,0.94)', holo1: 'rgba(87,214,255,0.18)', holo2: 'rgba(126,236,255,0.10)', holo3: 'rgba(80,180,255,0.12)', holo4: 'rgba(255,255,255,0.05)', hover: 'rgba(87,214,255,0.44)', bgMain: '#041019' },
        green: { bg: '#020804', fg: '#c8ffd1', accent: '#51cf66', purple: '#51cf66', border: 'rgba(81,207,102,0.42)', panel: 'rgba(10,20,12,0.58)', panelAlt: 'rgba(8,18,10,0.66)', menu: 'rgba(7,15,9,0.94)', holo1: 'rgba(81,207,102,0.16)', holo2: 'rgba(186,255,143,0.10)', holo3: 'rgba(120,255,170,0.10)', holo4: 'rgba(255,255,255,0.04)', hover: 'rgba(81,207,102,0.44)', bgMain: '#040805' },
        amber: { bg: '#120a00', fg: '#ffe7a8', accent: '#ffb347', purple: '#ffb347', border: 'rgba(255,179,71,0.42)', panel: 'rgba(28,18,6,0.58)', panelAlt: 'rgba(22,14,4,0.66)', menu: 'rgba(20,12,4,0.95)', holo1: 'rgba(255,179,71,0.16)', holo2: 'rgba(255,219,128,0.10)', holo3: 'rgba(255,154,86,0.12)', holo4: 'rgba(255,255,255,0.04)', hover: 'rgba(255,179,71,0.44)', bgMain: '#090603' },
        ice: { bg: '#02050a', fg: '#eefbff', accent: '#8be9fd', purple: '#8be9fd', border: 'rgba(139,233,253,0.42)', panel: 'rgba(12,20,30,0.56)', panelAlt: 'rgba(8,16,24,0.64)', menu: 'rgba(6,12,20,0.95)', holo1: 'rgba(139,233,253,0.16)', holo2: 'rgba(180,246,255,0.10)', holo3: 'rgba(160,200,255,0.10)', holo4: 'rgba(255,255,255,0.05)', hover: 'rgba(139,233,253,0.44)', bgMain: '#040812' },
        crimson: { bg: '#110205', fg: '#ffe2e9', accent: '#ff5d7a', purple: '#ff5d7a', border: 'rgba(255,93,122,0.42)', panel: 'rgba(28,10,14,0.58)', panelAlt: 'rgba(22,8,12,0.66)', menu: 'rgba(20,7,10,0.95)', holo1: 'rgba(255,93,122,0.18)', holo2: 'rgba(255,169,96,0.10)', holo3: 'rgba(255,120,160,0.10)', holo4: 'rgba(255,255,255,0.05)', hover: 'rgba(255,93,122,0.44)', bgMain: '#0a0406' },
        neon: { bg: '#020c03', fg: '#ebffd1', accent: '#b8ff4d', purple: '#b8ff4d', border: 'rgba(184,255,77,0.40)', panel: 'rgba(16,24,8,0.58)', panelAlt: 'rgba(12,18,6,0.66)', menu: 'rgba(10,16,5,0.95)', holo1: 'rgba(184,255,77,0.18)', holo2: 'rgba(81,207,102,0.10)', holo3: 'rgba(87,214,255,0.08)', holo4: 'rgba(255,255,255,0.04)', hover: 'rgba(184,255,77,0.42)', bgMain: '#050805' },
        rose: { bg: '#12060f', fg: '#fff0f8', accent: '#ff9ed1', purple: '#ff9ed1', border: 'rgba(255,158,209,0.42)', panel: 'rgba(28,14,24,0.58)', panelAlt: 'rgba(22,10,18,0.66)', menu: 'rgba(20,8,16,0.95)', holo1: 'rgba(255,158,209,0.18)', holo2: 'rgba(216,170,255,0.10)', holo3: 'rgba(255,198,122,0.08)', holo4: 'rgba(255,255,255,0.05)', hover: 'rgba(255,158,209,0.44)', bgMain: '#09050a' },
        ocean: { bg: '#021019', fg: '#defcff', accent: '#4fd8c8', purple: '#4fd8c8', border: 'rgba(79,216,200,0.42)', panel: 'rgba(8,24,28,0.58)', panelAlt: 'rgba(6,18,22,0.66)', menu: 'rgba(5,16,19,0.95)', holo1: 'rgba(79,216,200,0.18)', holo2: 'rgba(87,214,255,0.10)', holo3: 'rgba(69,128,255,0.09)', holo4: 'rgba(255,255,255,0.04)', hover: 'rgba(79,216,200,0.44)', bgMain: '#041018' },
        sunset: { bg: '#120604', fg: '#fff1e0', accent: '#ff8c42', purple: '#ff8c42', border: 'rgba(255,140,66,0.42)', panel: 'rgba(30,14,10,0.58)', panelAlt: 'rgba(24,10,8,0.66)', menu: 'rgba(21,9,7,0.95)', holo1: 'rgba(255,140,66,0.18)', holo2: 'rgba(255,211,115,0.10)', holo3: 'rgba(255,93,122,0.10)', holo4: 'rgba(255,255,255,0.04)', hover: 'rgba(255,140,66,0.44)', bgMain: '#0b0504' },
        slate: { bg: '#05070b', fg: '#eef2ff', accent: '#8b9bb4', purple: '#8b9bb4', border: 'rgba(139,155,180,0.40)', panel: 'rgba(16,19,24,0.60)', panelAlt: 'rgba(12,15,20,0.68)', menu: 'rgba(10,12,18,0.95)', holo1: 'rgba(139,155,180,0.16)', holo2: 'rgba(180,188,204,0.08)', holo3: 'rgba(111,145,178,0.08)', holo4: 'rgba(255,255,255,0.04)', hover: 'rgba(139,155,180,0.42)', bgMain: '#05070a' },
        violet: { bg: '#0f061a', fg: '#f6ebff', accent: '#b57cff', purple: '#b57cff', border: 'rgba(181,124,255,0.40)', panel: 'rgba(26,12,38,0.58)', panelAlt: 'rgba(20,10,30,0.66)', menu: 'rgba(18,8,28,0.95)', holo1: 'rgba(181,124,255,0.18)', holo2: 'rgba(255,169,214,0.10)', holo3: 'rgba(139,233,253,0.08)', holo4: 'rgba(255,255,255,0.04)', hover: 'rgba(181,124,255,0.42)', bgMain: '#08040d' },
        ruby: { bg: '#140305', fg: '#ffe8ee', accent: '#ff4d6d', purple: '#ff4d6d', border: 'rgba(255,77,109,0.42)', panel: 'rgba(34,10,14,0.60)', panelAlt: 'rgba(26,8,10,0.68)', menu: 'rgba(22,7,9,0.95)', holo1: 'rgba(255,77,109,0.18)', holo2: 'rgba(255,140,66,0.10)', holo3: 'rgba(255,198,122,0.08)', holo4: 'rgba(255,255,255,0.04)', hover: 'rgba(255,77,109,0.44)', bgMain: '#0a0405' },
        forest: { bg: '#031108', fg: '#e5ffef', accent: '#35c759', purple: '#35c759', border: 'rgba(53,199,89,0.42)', panel: 'rgba(10,28,16,0.58)', panelAlt: 'rgba(8,22,12,0.66)', menu: 'rgba(7,18,10,0.95)', holo1: 'rgba(53,199,89,0.18)', holo2: 'rgba(184,255,77,0.08)', holo3: 'rgba(79,216,200,0.08)', holo4: 'rgba(255,255,255,0.04)', hover: 'rgba(53,199,89,0.44)', bgMain: '#041008' },
        midnight: { bg: '#020814', fg: '#eaf3ff', accent: '#5aa9ff', purple: '#5aa9ff', border: 'rgba(90,169,255,0.42)', panel: 'rgba(8,18,34,0.60)', panelAlt: 'rgba(6,14,28,0.68)', menu: 'rgba(5,11,22,0.95)', holo1: 'rgba(90,169,255,0.18)', holo2: 'rgba(139,233,253,0.10)', holo3: 'rgba(181,124,255,0.08)', holo4: 'rgba(255,255,255,0.04)', hover: 'rgba(90,169,255,0.44)', bgMain: '#040912' },
        ghost: { bg: '#f5f7fb', fg: '#111827', accent: '#4b5563', purple: '#d7dde8', border: 'rgba(75,85,99,0.26)', panel: 'rgba(255,255,255,0.68)', panelAlt: 'rgba(245,247,251,0.78)', menu: 'rgba(255,255,255,0.92)', holo1: 'rgba(203,213,225,0.28)', holo2: 'rgba(255,255,255,0.34)', holo3: 'rgba(148,163,184,0.18)', holo4: 'rgba(255,255,255,0.55)', hover: 'rgba(75,85,99,0.34)', bgMain: '#e8edf5' }
      };
      var theme = themes[themeName] || themes.dedsec;
      var root = document.documentElement.style;
      root.setProperty('--bg', theme.bgMain || theme.bg);
      root.setProperty('--panel', theme.panel);
      root.setProperty('--panel-alt', theme.panelAlt);
      root.setProperty('--menu-solid', theme.menu);
      root.setProperty('--border', theme.border);
      root.setProperty('--hover-border', theme.hover || theme.border);
      root.setProperty('--cyan', theme.accent);
      root.setProperty('--purple', theme.purple || theme.accent);
      root.setProperty('--holo-lavender', theme.holo1);
      root.setProperty('--holo-gold', theme.holo2);
      root.setProperty('--holo-pink', theme.holo3);
      root.setProperty('--holo-white', theme.holo4);
      root.setProperty('--terminal-bg', theme.bg);
      root.setProperty('--terminal-fg', theme.fg);
      root.setProperty('--terminal-accent', theme.accent);
      root.setProperty('--text', theme.text || theme.fg);
      root.setProperty('--muted', theme.muted || theme.fg);
    })();
  </script>
</head>
<body>
  <div id="loading">
    <div class="spinner"></div>
    <div style="font-weight:700;font-size:1.08rem;">Welcome to DedSec OS</div>
    <div class="subtle">Loading secure local environment... please wait 10 seconds.</div>
  </div>
  <div id="loginOverlay" class="login-overlay hidden">
    <div class="login-card">
      <div class="screen-title" id="loginTitle">Login required</div>
      <div class="login-note" id="loginNote">Enter your password to unlock DedSec OS.</div>
      <div class="field">
        <label id="loginUsernameLabel" for="loginUsernameInput">Username</label>
        <input type="text" id="loginUsernameInput" list="loginProfilesList" placeholder="Username">
        <datalist id="loginProfilesList"></datalist>
      </div>
      <div class="field">
        <label id="loginPasswordLabel" for="loginPasswordInput">Password</label>
        <input type="password" id="loginPasswordInput" placeholder="Password">
      </div>
      <div class="field hidden" id="loginOtpField">
        <label id="loginOtpLabel" for="loginOtpInput">Authenticator code</label>
        <input type="text" id="loginOtpInput" inputmode="numeric" autocomplete="one-time-code" placeholder="123456">
      </div>
      <div class="toolbar">
        <button class="btn primary" id="loginSubmitBtn">Unlock</button>
        <button class="btn" id="forgotPasswordBtn">Forgot password?</button>
      </div>
      <div class="panel hidden" id="recoveryPanel">
        <div class="screen-title" id="recoveryTitle" style="font-size:0.92rem;">Password recovery</div>
        <div class="login-note" id="recoveryNote">Answer all 3 security questions to reset your password.</div>
        <div class="field">
          <label id="recoveryQuestion1Label" for="recoveryQuestion1Input">Question 1</label>
          <input type="text" id="recoveryQuestion1Input" placeholder="Question 1" readonly>
        </div>
        <div class="field">
          <label id="recoveryAnswer1Label" for="recoveryAnswer1Input">Answer 1</label>
          <input type="password" id="recoveryAnswer1Input" placeholder="Answer 1">
        </div>
        <div class="field">
          <label id="recoveryQuestion2Label" for="recoveryQuestion2Input">Question 2</label>
          <input type="text" id="recoveryQuestion2Input" placeholder="Question 2" readonly>
        </div>
        <div class="field">
          <label id="recoveryAnswer2Label" for="recoveryAnswer2Input">Answer 2</label>
          <input type="password" id="recoveryAnswer2Input" placeholder="Answer 2">
        </div>
        <div class="field">
          <label id="recoveryQuestion3Label" for="recoveryQuestion3Input">Question 3</label>
          <input type="text" id="recoveryQuestion3Input" placeholder="Question 3" readonly>
        </div>
        <div class="field">
          <label id="recoveryAnswer3Label" for="recoveryAnswer3Input">Answer 3</label>
          <input type="password" id="recoveryAnswer3Input" placeholder="Answer 3">
        </div>
        <div class="field">
          <label id="recoveryNewPasswordLabel" for="recoveryNewPasswordInput">New password</label>
          <input type="password" id="recoveryNewPasswordInput" placeholder="New password">
        </div>
        <div class="toolbar">
          <button class="btn primary" id="recoverySubmitBtn">Reset password</button>
        </div>
      </div>
    </div>
  </div>
  <div id="toast"></div>
  <button class="btn small" id="showSidebarBtn">Show Bar</button>
  <div id="app">
    <div class="topbar">
      <div class="brand">
        <div>
          <div class="brand-title">DedSec OS</div>
        </div>
      </div>
      <div class="topbar-right">
        <button class="btn small" id="batteryLabel">--%</button>
        <button class="btn small danger" id="exitDedsecOsBtn">Exit</button>
        <button class="btn small" id="notificationsBtn">Notifications</button>
        <button class="btn small" id="fullscreenTopBtn">Full Screen</button>
        <button class="btn small" id="hideSidebarBtn">Hide Bar</button>
        <button class="btn small sidebar-app-btn" data-side-app="settings">Settings</button>
        <button class="btn small sidebar-app-btn" data-side-app="terminal">Terminal</button>
        <button class="btn small sidebar-app-btn" data-side-app="apps">DedSec Apps</button>
        <button class="btn small" id="backNavBtn">Back</button>
      </div>
    </div>
    <div id="notificationsPanel" class="hidden"></div>
    <div class="dock" id="dock"></div>
    <div class="desktop">
      <section class="screen" data-app="system">
        <div class="screen-header" style="justify-content:flex-start;">
          <div class="toolbar">
            <button class="btn small" id="refreshSystemBtn">Refresh</button>
          </div>
        </div>
        <div class="screen-body" id="systemBody"></div>
      </section>

      <section class="screen" data-app="files">
        <div class="screen-header">
          <div class="stack">
            <div class="screen-title" id="filesTitle">Files</div>
            <div class="subtle" id="filesSubtle">Browse and edit text files safely</div>
          </div>
          <div class="toolbar">
            <button class="btn small" id="filesRefreshBtn">Refresh</button>
            <button class="btn small" id="filesNewFolderBtn">New Folder</button>
            <button class="btn small" id="filesNewFileBtn">New File</button>
            <button class="btn small" id="filesPasteBtn">Paste</button>
          </div>
        </div>
        <div class="screen-body split">
          <div class="panel">
            <div class="pathbar" id="filesPath"></div>
            <div class="panel-stack" id="filesRoots"></div>
            <div class="file-list" id="filesList"></div>
          </div>
          <div class="panel">
            <div class="stack" style="justify-content:space-between;align-items:center;">
              <div>
                <div class="screen-title" id="editorTitle" style="font-size:0.92rem;">Editor</div>
                <div class="subtle" id="editorPath">No file opened</div>
              </div>
              <div class="toolbar">
                <button class="btn small" id="editorSaveBtn">Save</button>
              </div>
            </div>
            <textarea id="editorArea" placeholder="Open a text file to edit it."></textarea>
          </div>
        </div>
      </section>

      <section class="screen" data-app="terminal">
        <div class="screen-header" style="justify-content:flex-end;">
          <div class="toolbar">
            <button class="btn small" id="terminalRefreshBtn">Refresh</button>
            <button class="btn small" id="terminalSessionsBtn">See Sessions</button>
          </div>
        </div>
        <div class="screen-body">
          <div class="terminal-wrap" id="terminalWrap">
            <div class="terminal-tabs" id="terminalTabs"></div>
            <div class="prompt" id="terminalPrompt"></div>
            <pre class="terminal-screen" id="terminalOutput" tabindex="0"></pre>
            <textarea id="terminalComposer" autocapitalize="off" autocomplete="off" autocorrect="off" spellcheck="false"></textarea>
            <div class="extra-keys" id="terminalExtraKeys">
              <button class="extra-key" data-seq="">ESC</button>
              <button class="extra-key" data-seq="/">/</button>
              <button class="extra-key" data-seq="-">-</button>
              <button class="extra-key" data-seq="[H">HOME</button>
              <button class="extra-key" data-seq="[A">↑</button>
              <button class="extra-key" data-seq="[F">END</button>
              <button class="extra-key" data-seq="[5~">PGUP</button>
              <button class="extra-key" data-seq="	">TAB</button>
              <button class="extra-key toggle" id="ctrlToggleKey">CTRL</button>
              <button class="extra-key toggle" id="altToggleKey">ALT</button>
              <button class="extra-key" data-seq="[D">←</button>
              <button class="extra-key" data-seq="[B">↓</button>
              <button class="extra-key" data-seq="[C">→</button>
              <button class="extra-key" data-seq="[6~">PGDN</button>
              <button class="extra-key" id="terminalBottomBtn">BOTTOM</button>
              <button class="extra-key" data-seq="">BKSP</button>
              <button class="extra-key wide" data-seq="
">ENTER</button>
            </div>
            <div class="sessions-overlay hidden" id="sessionsOverlay">
              <div class="sessions-panel">
                <div class="sessions-header">
                  <div class="screen-title" id="sessionsTitle" style="font-size:0.92rem;">Sessions</div>
                  <div class="toolbar">
                    <button class="btn small" id="sessionsNewBtn">New Session</button>
                    <button class="btn small" id="sessionsCloseBtn">Close</button>
                  </div>
                </div>
                <div class="store-list" id="sessionsList"></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="screen active" data-app="apps">
        <div class="screen-header">
          <div class="stack">
            <div class="screen-title" id="appsTitle">DedSec Apps</div>
            <div class="subtle" id="appsSubtle">Browse project folders and run scripts</div>
          </div>
          <div class="toolbar">
            <button class="btn small" id="appsRefreshBtn">Refresh</button>
          </div>
        </div>
        <div class="screen-body">
          <div class="pathbar" id="appsPath"></div>
          <div class="panel-stack" id="appsRoots"></div>
          <div class="file-list" id="appsList"></div>
        </div>
      </section>

      <section class="screen" data-app="store">
        <div class="screen-header">
          <div class="stack">
            <div class="screen-title" id="storeTitle">Linux Store</div>
            <div class="subtle" id="storeSubtle">Real Termux package actions</div>
          </div>
          <div class="toolbar">
            <button class="btn small" id="storeRefreshBtn">Refresh</button>
          </div>
        </div>
        <div class="screen-body">
          <div class="store-list" id="storeList"></div>
        </div>
      </section>

      <section class="screen" data-app="settings">
        <div class="screen-header">
          <div class="stack">
            <div class="screen-title" id="settingsTitle">Settings</div>
            <div class="subtle" id="settingsSubtle">Identity and wallpaper</div>
          </div>
        </div>
        <div class="screen-body">
          <div class="panel">
            <div class="field">
              <label id="displayNameLabel" for="displayNameInput">Display name</label>
              <input type="text" id="displayNameInput" list="userProfilesList" placeholder="DedSec">
              <datalist id="userProfilesList"></datalist>
            </div>
            <div class="field">
              <label id="terminalThemeLabel" for="terminalThemeSelect">Terminal colors</label>
              <select id="terminalThemeSelect">
                <option value="dedsec">DedSec Purple</option>
                <option value="cyan">Cyan Frost</option>
                <option value="green">Matrix Green</option>
                <option value="amber">Amber Signal</option>
                <option value="ice">Ice Blue</option>
                <option value="crimson">Crimson Night</option>
                <option value="neon">Neon Lime</option>
                <option value="rose">Rose Glow</option>
                <option value="ocean">Ocean Depth</option>
                <option value="sunset">Sunset Gold</option>
                <option value="slate">Slate Steel</option>
                <option value="ghost">Ghost White</option>
                <option value="violet">Violet Pulse</option>
                <option value="ruby">Ruby Red</option>
                <option value="forest">Forest Mist</option>
                <option value="midnight">Midnight Blue</option>
              </select>
            </div>
            <div class="field">
              <label id="wallpaperInputLabel" for="wallpaperInput">Wallpaper URL or local path</label>
              <input type="text" id="wallpaperInput" placeholder="https://... or /path/to/image.jpg">
            </div>
            <div class="field">
              <label id="wallpaperUploadLabel" for="wallpaperUpload">Wallpaper image upload</label>
              <input type="file" id="wallpaperUpload" accept="image/*">
            </div>
            <label class="subtle" style="display:flex;gap:8px;align-items:center;"><input type="checkbox" id="loginEnabledChk"> Require login password</label>
            <div class="field">
              <label id="loginPasswordSettingLabel" for="loginPasswordSetting">New password</label>
              <input type="password" id="loginPasswordSetting" placeholder="Leave blank to keep current password">
            </div>
            <label class="subtle" style="display:flex;gap:8px;align-items:center;"><input type="checkbox" id="totpEnabledChk"> Enable authenticator app (2FA)</label>
            <div class="field">
              <label id="totpSecretLabel" for="totpSecretDisplay">Authenticator secret</label>
              <input type="text" id="totpSecretDisplay" placeholder="Will be generated after saving" readonly>
            </div>
            <div class="field">
              <label id="securityQuestion1SettingLabel" for="securityQuestion1Setting">Security question 1</label>
              <input type="text" id="securityQuestion1Setting" placeholder="Question 1">
            </div>
            <div class="field">
              <label id="securityAnswer1SettingLabel" for="securityAnswer1Setting">Answer 1</label>
              <input type="password" id="securityAnswer1Setting" placeholder="Answer 1">
            </div>
            <div class="field">
              <label id="securityQuestion2SettingLabel" for="securityQuestion2Setting">Security question 2</label>
              <input type="text" id="securityQuestion2Setting" placeholder="Question 2">
            </div>
            <div class="field">
              <label id="securityAnswer2SettingLabel" for="securityAnswer2Setting">Answer 2</label>
              <input type="password" id="securityAnswer2Setting" placeholder="Answer 2">
            </div>
            <div class="field">
              <label id="securityQuestion3SettingLabel" for="securityQuestion3Setting">Security question 3</label>
              <input type="text" id="securityQuestion3Setting" placeholder="Question 3">
            </div>
            <div class="field">
              <label id="securityAnswer3SettingLabel" for="securityAnswer3Setting">Answer 3</label>
              <input type="password" id="securityAnswer3Setting" placeholder="Answer 3">
            </div>
            <div class="toolbar">
              <button class="btn primary" id="saveSettingsBtn">Save settings</button>
              <button class="btn" id="resetWallpaperBtn">Reset wallpaper</button>
              <button class="btn" id="toggleFullscreenBtn">Toggle Full Screen</button>
            </div>
          </div>
          <div class="panel">
            <div class="screen-title" style="font-size:0.92rem;">Project & Menu</div>
            <div class="field">
              <label for="webPromptUsername">Prompt username</label>
              <input type="text" id="webPromptUsername" placeholder="DedSec">
            </div>
            <div class="field">
              <label for="webLanguageSelect">Language</label>
              <select id="webLanguageSelect">
                <option value="english">English</option>
                <option value="greek">Ελληνικά</option>
              </select>
            </div>
            <div class="field">
              <label for="webMenuStyleSelect">Menu style</label>
              <select id="webMenuStyleSelect">
                <option value="list">List Style</option>
                <option value="grid">Grid Style</option>
                <option value="number">Choose By Number</option>
                <option value="dedsec_os">DedSec OS</option>
              </select>
            </div>
            <label class="subtle" style="display:flex;gap:8px;align-items:center;"><input type="checkbox" id="webAutostartChk"> Menu auto-start</label>
            <div class="toolbar">
              <button class="btn" id="savePromptBtn">Save Prompt</button>
              <button class="btn" id="saveLanguageBtn">Apply Language</button>
              <button class="btn" id="saveMenuStyleBtn">Apply Menu Style</button>
              <button class="btn" id="saveAutostartBtn">Save Auto-Start</button>
            </div>
          </div>
          <div class="panel">
            <div class="screen-title" style="font-size:0.92rem;">Project Actions</div>
            <div class="toolbar">
              <button class="btn" id="updateSource1Btn">Update Project (Source 1)</button>
              <button class="btn" id="updateSource2Btn">Update Project (Source 2)</button>
              <button class="btn" id="updatePackagesBtn">Update Packages & Modules</button>
            </div>
          </div>
          <div class="panel">
            <div class="screen-title" style="font-size:0.92rem;">Credits</div>
            <div class="subtle" id="creditsBlock">Creator: dedsec1121fk
Contributors: gr3ysec, Sal Scar
Art Artist: Christina Chatzidimitriou
Testers: MR-x</div>
          </div>
        </div>
      </section>
    </div>
  </div>


  <script>
    var state = {
      activeApp: 'apps',
      info: null,
      config: null,
      filesPath: '',
      appsPath: '',
      currentFilePath: '',
      jobs: [],
      selectedSessionId: 'web-shell',
      clipboard: null,
      loadingHidden: true,
      loadingStartedAt: Date.now(),
      authRequired: false,
      authenticated: false,
      booted: false,
      uiBound: false,
      authStatus: null,
      recoveryQuestions: [],
      terminalZoom: 1,
      ctrlArmed: false,
      altArmed: false,
      terminalRefreshTimer: null,
      lastApp: 'apps'
    };

    var I18N = {
      en: {
        'System':'System','Phone-first local workspace':'Phone-first local workspace','Refresh':'Refresh','Files':'Files','Browse and edit text files safely':'Browse and edit text files safely','New Folder':'New Folder','New File':'New File','Paste':'Paste','Editor':'Editor','No file opened':'No file opened','Open a text file to edit it.':'Open a text file to edit it.','Save':'Save','See Sessions':'See Sessions','Sessions':'Sessions','New Session':'New Session','Close':'Close','DedSec Apps':'DedSec Apps','Browse project folders and run scripts':'Browse project folders and run scripts','Linux Store':'Linux Store','Real Termux package actions':'Real Termux package actions','Settings':'Settings','Identity and wallpaper':'Identity and wallpaper','Display name':'Display name','Terminal colors':'Terminal colors','Wallpaper URL or local path':'Wallpaper URL or local path','Wallpaper image upload':'Wallpaper image upload','Save settings':'Save settings','Reset wallpaper':'Reset wallpaper','Toggle Full Screen':'Toggle Full Screen','Apps':'Apps','Open':'Open','Folder':'Folder','File':'File','Runnable file':'Runnable file','Run':'Run','Copy':'Copy','Move':'Move','Delete':'Delete','Go back':'Go back','Installed':'Installed','Not installed':'Not installed','Package':'Package','Running':'Running','Exit':'Exit','No sessions found.':'No sessions found.','Open a text file first':'Open a text file first','File saved':'File saved','Clipboard is empty':'Clipboard is empty','Paste complete':'Paste complete','Move queued':'Move queued','Delete this item?':'Delete this item?','Deleted':'Deleted','Settings saved':'Settings saved','Wallpaper reset':'Wallpaper reset','Folder name':'Folder name','File name':'File name','Copied to clipboard':'Copied to clipboard','Launched':'Launched','Hide Bar':'Hide Bar','Show Bar':'Show Bar','Full Screen':'Full Screen','Project & Menu':'Project & Menu','Prompt username':'Prompt username','Language':'Language','Menu style':'Menu style','Menu auto-start':'Menu auto-start','Save Prompt':'Save Prompt','Apply Language':'Apply Language','Apply Menu Style':'Apply Menu Style','Save Auto-Start':'Save Auto-Start','Project Actions':'Project Actions','Update Project (Source 1)':'Update Project (Source 1)','Update Project (Source 2)':'Update Project (Source 2)','Update Packages & Modules':'Update Packages & Modules','Credits':'Credits','Saved':'Saved','List Style':'List Style','Grid Style':'Grid Style','Choose By Number':'Choose By Number','DedSec OS':'DedSec OS','Back':'Back','Notifications':'Notifications','Login required':'Login required','Enter your password to unlock DedSec OS.':'Enter your password to unlock DedSec OS.','Username':'Username','Password':'Password','Unlock':'Unlock','Require login password':'Require login password','New password':'New password','Leave blank to keep current password':'Leave blank to keep current password','Wrong password':'Wrong password','Authenticator code':'Authenticator code','Forgot password?':'Forgot password?','Password recovery':'Password recovery','Answer all 3 security questions to reset your password.':'Answer all 3 security questions to reset your password.','Question 1':'Question 1','Question 2':'Question 2','Question 3':'Question 3','Answer 1':'Answer 1','Answer 2':'Answer 2','Answer 3':'Answer 3','Reset password':'Reset password','Enable authenticator app (2FA)':'Enable authenticator app (2FA)','Authenticator secret':'Authenticator secret','Security question 1':'Security question 1','Security question 2':'Security question 2','Security question 3':'Security question 3','Recovery answers do not match.':'Recovery answers do not match.','A 6-digit authenticator code is required.':'A 6-digit authenticator code is required.','Full':'Full','Split':'Split','Terminal':'Terminal','Store':'Store','Theme':'Theme','Menu':'Menu'
      },
      el: {
        'System':'Σύστημα','Phone-first local workspace':'Τοπικός χώρος εργασίας για κινητό','Refresh':'Ανανέωση','Files':'Αρχεία','Browse and edit text files safely':'Περιήγηση και ασφαλής επεξεργασία αρχείων κειμένου','New Folder':'Νέος Φάκελος','New File':'Νέο Αρχείο','Paste':'Επικόλληση','Editor':'Επεξεργαστής','No file opened':'Δεν έχει ανοιχτεί αρχείο','Open a text file to edit it.':'Ανοίξτε ένα αρχείο κειμένου για επεξεργασία.','Save':'Αποθήκευση','See Sessions':'Προβολή Συνεδριών','Sessions':'Συνεδρίες','New Session':'Νέα Συνεδρία','Close':'Κλείσιμο','DedSec Apps':'Εφαρμογές DedSec','Browse project folders and run scripts':'Περιηγηθείτε στους φακέλους του project και εκτελέστε scripts','Linux Store':'Κατάστημα Linux','Real Termux package actions':'Πραγματικές ενέργειες πακέτων Termux','Settings':'Ρυθμίσεις','Identity and wallpaper':'Ταυτότητα και ταπετσαρία','Display name':'Όνομα εμφάνισης','Terminal colors':'Χρώματα τερματικού','Wallpaper URL or local path':'URL ταπετσαρίας ή τοπική διαδρομή','Wallpaper image upload':'Μεταφόρτωση εικόνας ταπετσαρίας','Save settings':'Αποθήκευση ρυθμίσεων','Reset wallpaper':'Επαναφορά ταπετσαρίας','Toggle Full Screen':'Εναλλαγή πλήρους οθόνης','Apps':'Εφαρμογές','Open':'Άνοιγμα','Folder':'Φάκελος','File':'Αρχείο','Runnable file':'Εκτελέσιμο αρχείο','Run':'Εκτέλεση','Copy':'Αντιγραφή','Move':'Μετακίνηση','Delete':'Διαγραφή','Go back':'Επιστροφή','Installed':'Εγκατεστημένο','Not installed':'Μη εγκατεστημένο','Package':'Πακέτο','Running':'Εκτελείται','Exit':'Έξοδος','No sessions found.':'Δεν βρέθηκαν συνεδρίες.','Open a text file first':'Ανοίξτε πρώτα ένα αρχείο κειμένου','File saved':'Το αρχείο αποθηκεύτηκε','Clipboard is empty':'Το πρόχειρο είναι άδειο','Paste complete':'Η επικόλληση ολοκληρώθηκε','Move queued':'Η μετακίνηση μπήκε σε αναμονή','Delete this item?':'Διαγραφή αυτού του στοιχείου;','Deleted':'Διαγράφηκε','Settings saved':'Οι ρυθμίσεις αποθηκεύτηκαν','Wallpaper reset':'Η ταπετσαρία επαναφέρθηκε','Folder name':'Όνομα φακέλου','File name':'Όνομα αρχείου','Copied to clipboard':'Αντιγράφηκε στο πρόχειρο','Launched':'Εκκινήθηκε','Hide Bar':'Απόκρυψη μπάρας','Show Bar':'Εμφάνιση μπάρας','Full Screen':'Πλήρης οθόνη','Project & Menu':'Έργο & Μενού','Prompt username':'Όνομα προτροπής','Language':'Γλώσσα','Menu style':'Στυλ μενού','Menu auto-start':'Αυτόματη εκκίνηση μενού','Save Prompt':'Αποθήκευση προτροπής','Apply Language':'Εφαρμογή γλώσσας','Apply Menu Style':'Εφαρμογή στυλ μενού','Save Auto-Start':'Αποθήκευση αυτόματης εκκίνησης','Project Actions':'Ενέργειες έργου','Update Project (Source 1)':'Ενημέρωση έργου (Πηγή 1)','Update Project (Source 2)':'Ενημέρωση έργου (Πηγή 2)','Update Packages & Modules':'Ενημέρωση πακέτων & modules','Credits':'Συντελεστές','Saved':'Αποθηκεύτηκε','List Style':'Στυλ λίστας','Grid Style':'Στυλ πλέγματος','Choose By Number':'Επιλογή με αριθμό','DedSec OS':'DedSec OS','Back':'Πίσω','Notifications':'Ειδοποιήσεις','Login required':'Απαιτείται σύνδεση','Enter your password to unlock DedSec OS.':'Εισαγάγετε τον κωδικό σας για να ξεκλειδώσετε το DedSec OS.','Username':'Όνομα χρήστη','Password':'Κωδικός','Unlock':'Ξεκλείδωμα','Require login password':'Απαίτηση κωδικού σύνδεσης','New password':'Νέος κωδικός','Leave blank to keep current password':'Αφήστε κενό για να διατηρηθεί ο τωρινός κωδικός','Wrong password':'Λάθος κωδικός','Authenticator code':'Κωδικός εφαρμογής Authenticator','Forgot password?':'Ξεχάσατε τον κωδικό;','Password recovery':'Ανάκτηση κωδικού','Answer all 3 security questions to reset your password.':'Απαντήστε και στις 3 ερωτήσεις ασφαλείας για επαναφορά του κωδικού.','Question 1':'Ερώτηση 1','Question 2':'Ερώτηση 2','Question 3':'Ερώτηση 3','Answer 1':'Απάντηση 1','Answer 2':'Απάντηση 2','Answer 3':'Απάντηση 3','Reset password':'Επαναφορά κωδικού','Enable authenticator app (2FA)':'Ενεργοποίηση εφαρμογής Authenticator (2FA)','Authenticator secret':'Μυστικό Authenticator','Security question 1':'Ερώτηση ασφαλείας 1','Security question 2':'Ερώτηση ασφαλείας 2','Security question 3':'Ερώτηση ασφαλείας 3','Recovery answers do not match.':'Οι απαντήσεις ανάκτησης δεν ταιριάζουν.','A 6-digit authenticator code is required.':'Απαιτείται 6-ψήφιος κωδικός Authenticator.','Full':'Πλήρης','Split':'Διαίρεση','Terminal':'Τερματικό','Store':'Κατάστημα','Theme':'Θέμα','Menu':'Μενού'
      }
    };

    function currentLang() {
      return state.info && state.info.language === 'greek' ? 'el' : 'en';
    }

    function t(key) {
      var lang = currentLang();
      return (I18N[lang] && I18N[lang][key]) || (I18N.en && I18N.en[key]) || key;
    }

    var APP_META = [
      { id: 'system', label: 'System' },
      { id: 'files', label: 'Files' },
      { id: 'terminal', label: 'Terminal' },
      { id: 'apps', label: 'DedSec Apps' },
      { id: 'store', label: 'Linux Store' },
      { id: 'settings', label: 'Settings' }
    ];

    function applyTranslations() {
      var map = {
        systemTitle:'System', systemSubtle:'Phone-first local workspace', backNavBtn:'Back', batteryLabel:'--%', notificationsBtn:'Notifications', fullscreenTopBtn:'Full Screen', hideSidebarBtn:'Hide Bar', showSidebarBtn:'Show Bar', splitModeBtn:'Split', refreshSystemBtn:'Refresh', filesTitle:'Files', filesSubtle:'Browse and edit text files safely', filesRefreshBtn:'Refresh', filesNewFolderBtn:'New Folder', filesNewFileBtn:'New File', filesPasteBtn:'Paste', editorTitle:'Editor', editorSaveBtn:'Save', terminalRefreshBtn:'Refresh', terminalSessionsBtn:'See Sessions', sessionsTitle:'Sessions', sessionsNewBtn:'New Session', sessionsCloseBtn:'Close', appsTitle:'DedSec Apps', appsSubtle:'Browse project folders and run scripts', appsRefreshBtn:'Refresh', storeTitle:'Linux Store', storeSubtle:'Real Termux package actions', storeRefreshBtn:'Refresh', settingsTitle:'Settings', settingsSubtle:'Identity and wallpaper', displayNameLabel:'Display name', terminalThemeLabel:'Terminal colors', wallpaperInputLabel:'Wallpaper URL or local path', wallpaperUploadLabel:'Wallpaper image upload', saveSettingsBtn:'Save settings', resetWallpaperBtn:'Reset wallpaper', toggleFullscreenBtn:'Toggle Full Screen', webPromptUsernameLabel:'Prompt username', exitDedsecOsBtn:'Exit', loginTitle:'Login required', loginNote:'Enter your password to unlock DedSec OS.', loginUsernameLabel:'Username', loginPasswordLabel:'Password', loginSubmitBtn:'Unlock', loginPasswordSettingLabel:'New password', loginOtpLabel:'Authenticator code', forgotPasswordBtn:'Forgot password?', recoveryTitle:'Password recovery', recoveryNote:'Answer all 3 security questions to reset your password.', recoveryQuestion1Label:'Question 1', recoveryQuestion2Label:'Question 2', recoveryQuestion3Label:'Question 3', recoveryAnswer1Label:'Answer 1', recoveryAnswer2Label:'Answer 2', recoveryAnswer3Label:'Answer 3', recoveryNewPasswordLabel:'New password', recoverySubmitBtn:'Reset password', totpSecretLabel:'Authenticator secret', securityQuestion1SettingLabel:'Security question 1', securityQuestion2SettingLabel:'Security question 2', securityQuestion3SettingLabel:'Security question 3', securityAnswer1SettingLabel:'Answer 1', securityAnswer2SettingLabel:'Answer 2', securityAnswer3SettingLabel:'Answer 3'
      };
      Object.keys(map).forEach(function(id){ var node=document.getElementById(id); if(node) node.textContent=t(map[id]); });
      var ep=document.getElementById('editorPath'); if (ep && !state.currentFilePath) ep.textContent=t('No file opened');
      var ea=document.getElementById('editorArea'); if (ea) ea.placeholder=t('Open a text file to edit it.');
      document.querySelectorAll('.sidebar-app-btn').forEach(function(btn){ var key=btn.getAttribute('data-side-app'); var map={system:'System',files:'Files',terminal:'Terminal',apps:'DedSec Apps',store:'Linux Store',settings:'Settings'}; btn.textContent=t(map[key]||key); });
    }

    function iconSvg(name) {
      var map = {
        system: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="3" y="4" width="18" height="12" rx="2"></rect><path d="M8 20h8"></path><path d="M12 16v4"></path></svg>',
        files: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M4 7.5A2.5 2.5 0 0 1 6.5 5H11l2 2h4.5A2.5 2.5 0 0 1 20 9.5v7A2.5 2.5 0 0 1 17.5 19h-11A2.5 2.5 0 0 1 4 16.5v-9Z"></path></svg>',
        terminal: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="m5 7 4 4-4 4"></path><path d="M11 17h8"></path><rect x="3" y="4" width="18" height="16" rx="2"></rect></svg>',
        apps: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="4" y="4" width="6" height="6" rx="1"></rect><rect x="14" y="4" width="6" height="6" rx="1"></rect><rect x="4" y="14" width="6" height="6" rx="1"></rect><rect x="14" y="14" width="6" height="6" rx="1"></rect></svg>',
        store: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M5 7h14l-1 12H6L5 7Z"></path><path d="M9 7V5a3 3 0 0 1 6 0v2"></path></svg>',
        settings: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M12 8.5A3.5 3.5 0 1 0 12 15.5A3.5 3.5 0 1 0 12 8.5Z"></path><path d="M19.4 15a1 1 0 0 0 .2 1.1l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1 1 0 0 0-1.1-.2 1 1 0 0 0-.6.9V20a2 2 0 1 1-4 0v-.2a1 1 0 0 0-.6-.9 1 1 0 0 0-1.1.2l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1 1 0 0 0 .2-1.1 1 1 0 0 0-.9-.6H4a2 2 0 1 1 0-4h.2a1 1 0 0 0 .9-.6 1 1 0 0 0-.2-1.1l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1 1 0 0 0 1.1.2 1 1 0 0 0 .6-.9V4a2 2 0 1 1 4 0v.2a1 1 0 0 0 .6.9 1 1 0 0 0 1.1-.2l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1 1 0 0 0-.2 1.1 1 1 0 0 0 .9.6H20a2 2 0 1 1 0 4h-.2a1 1 0 0 0-.9.6Z"></path></svg>'
      };
      return map[name] || map.system;
    }

    function renderBatteryStatus() {
      var label = document.getElementById('batteryLabel');
      if (!label) return;
      apiGet('/api/status').then(function(data){
        var pct = data && data.battery && data.battery.percentage;
        if (pct != null) {
          label.textContent = String(pct) + '%';
          return;
        }
        if (navigator.getBattery) {
          navigator.getBattery().then(function(battery){
            label.textContent = Math.round((battery.level || 0) * 100) + '%';
          }).catch(function(){ label.textContent = '--%'; });
        } else {
          label.textContent = '--%';
        }
      }).catch(function(){
        if (navigator.getBattery) {
          navigator.getBattery().then(function(battery){
            label.textContent = Math.round((battery.level || 0) * 100) + '%';
          }).catch(function(){ label.textContent = '--%'; });
        } else {
          label.textContent = '--%';
        }
      });
    }

    function renderNotificationsPanel(items) { var panel=document.getElementById('notificationsPanel'); if(!panel) return; var list=items||[]; panel.innerHTML='<div class="panel"><div class="stack" style="justify-content:space-between;align-items:center;"><div class="screen-title" style="font-size:0.92rem;">'+ escapeHtml(t('Sessions')) +'</div><button class="btn small" id="notificationsCloseBtn">'+ escapeHtml(t('Close')) +'</button></div>' + (list.length ? list.map(function(item){ return '<div class="notif-item"><div class="notif-title">'+ escapeHtml(item.title) +'</div><div class="notif-text">'+ escapeHtml(item.text||'') +'</div><div class="notif-package">'+ escapeHtml(item.package||'') +'</div></div>'; }).join('') : '<div class="notif-item"><div class="notif-title">No notifications</div></div>') + '</div>'; panel.classList.remove('hidden'); var c=document.getElementById('notificationsCloseBtn'); if(c) c.addEventListener('click', function(){ panel.classList.add('hidden');}); }

    function showLoginOverlay() {
      var overlay = document.getElementById('loginOverlay');
      if (overlay) overlay.classList.remove('hidden');
      var input = document.getElementById('loginPasswordInput');
      if (input) { input.value = ''; window.setTimeout(function(){ input.focus(); }, 60); }
    }

    function hideLoginOverlay() {
      var overlay = document.getElementById('loginOverlay');
      if (overlay) overlay.classList.add('hidden');
    }

    function hideLoading() {
      state.loadingHidden = true;
      var node = document.getElementById('loading');
      if (node) node.classList.add('hidden');
      if (state.authRequired && !state.authenticated) showLoginOverlay();
    }


    function applyTerminalZoom() {
      var output = document.getElementById('terminalOutput');
      var prompt = document.getElementById('terminalPrompt');
      var input = document.getElementById('terminalInput');
      if (output) output.style.fontSize = (0.85 * state.terminalZoom) + 'rem';
      if (prompt) prompt.style.fontSize = (0.82 * state.terminalZoom) + 'rem';
      if (input) input.style.fontSize = (1.0 * state.terminalZoom) + 'rem';
    }

    function bindTerminalPinchZoom() {
      var target = document.getElementById('terminalOutput');
      if (!target) return;
      var pinchStart = null;
      var baseZoom = 1;
      function dist(t1, t2) {
        var dx = t1.clientX - t2.clientX;
        var dy = t1.clientY - t2.clientY;
        return Math.sqrt(dx * dx + dy * dy);
      }
      target.addEventListener('touchstart', function(event) {
        if (event.touches.length === 2) {
          pinchStart = dist(event.touches[0], event.touches[1]);
          baseZoom = state.terminalZoom;
        }
      }, { passive: true });
      target.addEventListener('touchmove', function(event) {
        if (event.touches.length === 2 && pinchStart) {
          var factor = dist(event.touches[0], event.touches[1]) / pinchStart;
          state.terminalZoom = Math.max(0.8, Math.min(2.5, baseZoom * factor));
          applyTerminalZoom();
          if (bindTerminalPinchZoom._saveTimer) clearTimeout(bindTerminalPinchZoom._saveTimer);
          bindTerminalPinchZoom._saveTimer = setTimeout(saveUiPrefs, 300);
          event.preventDefault();
        }
      }, { passive: false });
      target.addEventListener('touchend', function() { pinchStart = null; }, { passive: true });
      target.addEventListener('touchcancel', function() { pinchStart = null; }, { passive: true });
    }

    function showToast(message, isError) {
      var toast = document.getElementById('toast');
      toast.textContent = message;
      toast.style.borderColor = isError ? 'rgba(255,111,145,0.35)' : 'rgba(87,214,255,0.35)';
      toast.classList.add('show');
      window.clearTimeout(showToast._timer);
      showToast._timer = window.setTimeout(function(){ toast.classList.remove('show'); }, 2600);
    }

    async function apiGet(url) {
      var res = await fetch(url, { cache: 'no-store' });
      var data = await res.json();
      if (!res.ok || data.ok === false) throw new Error(data.error || ('Request failed: ' + res.status));
      return data;
    }

    async function apiPost(url, body) {
      var res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body || {})
      });
      var data = await res.json();
      if (!res.ok || data.ok === false) throw new Error(data.error || ('Request failed: ' + res.status));
      return data;
    }

    function escapeHtml(value) {
      return String(value || '').replace(/[&<>"']/g, function(ch) {
        return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch];
      });
    }

    function setActiveApp(appId) {
      if (state.activeApp && state.activeApp !== appId) state.lastApp = state.activeApp;
      state.activeApp = appId;
      document.querySelectorAll('.screen').forEach(function(node) {
        node.classList.toggle('active', node.getAttribute('data-app') === appId);
      });
      document.querySelectorAll('.dock-btn').forEach(function(node) { node.classList.toggle('active', node.getAttribute('data-app') === appId); });
      document.querySelectorAll('.sidebar-app-btn').forEach(function(node){ node.classList.toggle('primary', node.getAttribute('data-side-app') === appId); });
    }


    function bindMenuToggle() {
      var button = document.getElementById('menuToggleBtn');
      var dock = document.getElementById('dock');
      var fullButton = document.getElementById('fullscreenTopBtn');
      document.querySelectorAll('.sidebar-app-btn').forEach(function(btn){
        btn.addEventListener('click', function(event){
          event.stopPropagation();
          setActiveApp(btn.getAttribute('data-side-app'));
        });
      });
      if (fullButton) {
        fullButton.addEventListener('click', async function(event){
          event.stopPropagation();
          try {
            if (!document.fullscreenElement) {
              await document.documentElement.requestFullscreen();
              showToast(t('Toggle Full Screen'));
            } else {
              await document.exitFullscreen();
              showToast(t('Toggle Full Screen'));
            }
          } catch (err) { handleError(err); }
        });
      }
      if (!button || !dock) return;
      button.addEventListener('click', function(event) {
        event.stopPropagation();
        dock.classList.toggle('open');
      });
      document.addEventListener('click', function(event) {
        if (button && !dock.contains(event.target) && event.target !== button) {
          dock.classList.remove('open');
        }
      });
    }

    function renderDock() {
      var dock = document.getElementById('dock');
      dock.innerHTML = APP_META.map(function(app) {
        return '<button class="dock-btn' + (app.id === state.activeApp ? ' active' : '') + '" data-app="' + app.id + '">' + iconSvg(app.id) + '<span>' + escapeHtml(t(app.label)) + '</span></button>';
      }).join('');
      dock.querySelectorAll('.dock-btn').forEach(function(btn) {
        btn.addEventListener('click', function() { setActiveApp(btn.getAttribute('data-app')); dock.classList.remove('open'); });
      });
    }

    function applyWallpaper(config) {
      var wallpaper = (config && config.wallpaper) ? config.wallpaper : '';
      document.body.style.backgroundImage = wallpaper ? 'url("' + wallpaper.replace(/"/g, '%22') + '")' : 'radial-gradient(circle at top, rgba(82,63,170,0.35), rgba(4,5,10,1))';
      document.getElementById('wallpaperInput').value = (config && config.wallpaper) || '';
      document.getElementById('displayNameInput').value = (config && config.display_name) || 'DedSec';
      document.getElementById('terminalThemeSelect').value = (config && config.terminal_theme) || 'dedsec';
      var loginEnabled = document.getElementById('loginEnabledChk'); if (loginEnabled) loginEnabled.checked = !!(config && config.login_enabled);
      var loginPasswordSetting = document.getElementById('loginPasswordSetting'); if (loginPasswordSetting) loginPasswordSetting.value = '';
      var totpEnabled = document.getElementById('totpEnabledChk'); if (totpEnabled) totpEnabled.checked = !!(config && config.totp_enabled);
      var totpSecretDisplay = document.getElementById('totpSecretDisplay'); if (totpSecretDisplay) totpSecretDisplay.value = (config && config.totp_secret) || '';
      var sq = (config && Array.isArray(config.security_questions)) ? config.security_questions : [];
      ['1','2','3'].forEach(function(num, idx){
        var q = document.getElementById('securityQuestion' + num + 'Setting');
        var a = document.getElementById('securityAnswer' + num + 'Setting');
        if (q) q.value = (sq[idx] && sq[idx].question) || '';
        if (a) a.value = '';
      });
      renderUserProfiles(config);
      applyTerminalTheme((config && config.terminal_theme) || 'dedsec');
    }

    function renderUserProfiles(config) {
      var list = document.getElementById('userProfilesList');
      var profiles = (config && Array.isArray(config.user_profiles)) ? config.user_profiles : [];
      list.innerHTML = profiles.map(function(name){ return '<option value="' + escapeHtml(name) + '"></option>'; }).join('');
    }

    function applySidebarVisibility(hidden) {
      state.sidebarHidden = !!hidden;
      var app = document.getElementById('app');
      if (app) app.classList.toggle('sidebar-hidden', state.sidebarHidden);
      var showBtn = document.getElementById('showSidebarBtn');
      if (showBtn) showBtn.classList.toggle('show-sidebar-visible', state.sidebarHidden);
    }

    async function saveUiPrefs() {
      try { await apiPost('/api/config', { terminal_zoom: state.terminalZoom, sidebar_hidden: state.sidebarHidden }); } catch (err) {}
    }

    function applyTerminalTheme(themeName) {
      var themes = {
        dedsec: { bg: '#000000', fg: '#f5f7ff', accent: '#cd93ff', purple: '#cd93ff', border: 'rgba(205,147,255,0.50)', panel: 'rgba(18,18,30,0.52)', panelAlt: 'rgba(14,14,24,0.58)', menu: 'rgba(10,10,18,0.94)', holo1: 'rgba(216,170,255,0.18)', holo2: 'rgba(255,198,122,0.10)', holo3: 'rgba(255,169,214,0.10)', holo4: 'rgba(255,255,255,0.05)', hover: 'rgba(87,214,255,0.35)', bgMain: '#04050a' },
        cyan: { bg: '#031017', fg: '#def9ff', accent: '#57d6ff', purple: '#57d6ff', border: 'rgba(87,214,255,0.44)', panel: 'rgba(8,20,28,0.60)', panelAlt: 'rgba(6,16,24,0.66)', menu: 'rgba(4,14,22,0.94)', holo1: 'rgba(87,214,255,0.18)', holo2: 'rgba(126,236,255,0.10)', holo3: 'rgba(80,180,255,0.12)', holo4: 'rgba(255,255,255,0.05)', hover: 'rgba(87,214,255,0.44)', bgMain: '#041019' },
        green: { bg: '#020804', fg: '#c8ffd1', accent: '#51cf66', purple: '#51cf66', border: 'rgba(81,207,102,0.42)', panel: 'rgba(10,20,12,0.58)', panelAlt: 'rgba(8,18,10,0.66)', menu: 'rgba(7,15,9,0.94)', holo1: 'rgba(81,207,102,0.16)', holo2: 'rgba(186,255,143,0.10)', holo3: 'rgba(120,255,170,0.10)', holo4: 'rgba(255,255,255,0.04)', hover: 'rgba(81,207,102,0.44)', bgMain: '#040805' },
        amber: { bg: '#120a00', fg: '#ffe7a8', accent: '#ffb347', purple: '#ffb347', border: 'rgba(255,179,71,0.42)', panel: 'rgba(28,18,6,0.58)', panelAlt: 'rgba(22,14,4,0.66)', menu: 'rgba(20,12,4,0.95)', holo1: 'rgba(255,179,71,0.16)', holo2: 'rgba(255,219,128,0.10)', holo3: 'rgba(255,154,86,0.12)', holo4: 'rgba(255,255,255,0.04)', hover: 'rgba(255,179,71,0.44)', bgMain: '#090603' },
        ice: { bg: '#02050a', fg: '#eefbff', accent: '#8be9fd', purple: '#8be9fd', border: 'rgba(139,233,253,0.42)', panel: 'rgba(12,20,30,0.56)', panelAlt: 'rgba(8,16,24,0.64)', menu: 'rgba(6,12,20,0.95)', holo1: 'rgba(139,233,253,0.16)', holo2: 'rgba(180,246,255,0.10)', holo3: 'rgba(160,200,255,0.10)', holo4: 'rgba(255,255,255,0.05)', hover: 'rgba(139,233,253,0.44)', bgMain: '#040812' },
        crimson: { bg: '#110205', fg: '#ffe2e9', accent: '#ff5d7a', purple: '#ff5d7a', border: 'rgba(255,93,122,0.42)', panel: 'rgba(28,10,14,0.58)', panelAlt: 'rgba(22,8,12,0.66)', menu: 'rgba(20,7,10,0.95)', holo1: 'rgba(255,93,122,0.18)', holo2: 'rgba(255,169,96,0.10)', holo3: 'rgba(255,120,160,0.10)', holo4: 'rgba(255,255,255,0.05)', hover: 'rgba(255,93,122,0.44)', bgMain: '#0a0406' },
        neon: { bg: '#020c03', fg: '#ebffd1', accent: '#b8ff4d', purple: '#b8ff4d', border: 'rgba(184,255,77,0.40)', panel: 'rgba(16,24,8,0.58)', panelAlt: 'rgba(12,18,6,0.66)', menu: 'rgba(10,16,5,0.95)', holo1: 'rgba(184,255,77,0.18)', holo2: 'rgba(81,207,102,0.10)', holo3: 'rgba(87,214,255,0.08)', holo4: 'rgba(255,255,255,0.04)', hover: 'rgba(184,255,77,0.42)', bgMain: '#050805' },
        rose: { bg: '#12060f', fg: '#fff0f8', accent: '#ff9ed1', purple: '#ff9ed1', border: 'rgba(255,158,209,0.42)', panel: 'rgba(28,14,24,0.58)', panelAlt: 'rgba(22,10,18,0.66)', menu: 'rgba(20,8,16,0.95)', holo1: 'rgba(255,158,209,0.18)', holo2: 'rgba(216,170,255,0.10)', holo3: 'rgba(255,198,122,0.08)', holo4: 'rgba(255,255,255,0.05)', hover: 'rgba(255,158,209,0.44)', bgMain: '#09050a' },
        ocean: { bg: '#021019', fg: '#defcff', accent: '#4fd8c8', purple: '#4fd8c8', border: 'rgba(79,216,200,0.42)', panel: 'rgba(8,24,28,0.58)', panelAlt: 'rgba(6,18,22,0.66)', menu: 'rgba(5,16,19,0.95)', holo1: 'rgba(79,216,200,0.18)', holo2: 'rgba(87,214,255,0.10)', holo3: 'rgba(69,128,255,0.09)', holo4: 'rgba(255,255,255,0.04)', hover: 'rgba(79,216,200,0.44)', bgMain: '#041018' },
        sunset: { bg: '#120604', fg: '#fff1e0', accent: '#ff8c42', purple: '#ff8c42', border: 'rgba(255,140,66,0.42)', panel: 'rgba(30,14,10,0.58)', panelAlt: 'rgba(24,10,8,0.66)', menu: 'rgba(21,9,7,0.95)', holo1: 'rgba(255,140,66,0.18)', holo2: 'rgba(255,211,115,0.10)', holo3: 'rgba(255,93,122,0.10)', holo4: 'rgba(255,255,255,0.04)', hover: 'rgba(255,140,66,0.44)', bgMain: '#0b0504' },
        slate: { bg: '#05070b', fg: '#eef2ff', accent: '#8b9bb4', purple: '#8b9bb4', border: 'rgba(139,155,180,0.40)', panel: 'rgba(16,19,24,0.60)', panelAlt: 'rgba(12,15,20,0.68)', menu: 'rgba(10,12,18,0.95)', holo1: 'rgba(139,155,180,0.16)', holo2: 'rgba(180,188,204,0.08)', holo3: 'rgba(111,145,178,0.08)', holo4: 'rgba(255,255,255,0.04)', hover: 'rgba(139,155,180,0.42)', bgMain: '#05070a' },
        violet: { bg: '#0f061a', fg: '#f6ebff', accent: '#b57cff', purple: '#b57cff', border: 'rgba(181,124,255,0.40)', panel: 'rgba(26,12,38,0.58)', panelAlt: 'rgba(20,10,30,0.66)', menu: 'rgba(18,8,28,0.95)', holo1: 'rgba(181,124,255,0.18)', holo2: 'rgba(255,169,214,0.10)', holo3: 'rgba(139,233,253,0.08)', holo4: 'rgba(255,255,255,0.04)', hover: 'rgba(181,124,255,0.42)', bgMain: '#08040d' },
        ruby: { bg: '#140305', fg: '#ffe8ee', accent: '#ff4d6d', purple: '#ff4d6d', border: 'rgba(255,77,109,0.42)', panel: 'rgba(34,10,14,0.60)', panelAlt: 'rgba(26,8,10,0.68)', menu: 'rgba(22,7,9,0.95)', holo1: 'rgba(255,77,109,0.18)', holo2: 'rgba(255,140,66,0.10)', holo3: 'rgba(255,198,122,0.08)', holo4: 'rgba(255,255,255,0.04)', hover: 'rgba(255,77,109,0.44)', bgMain: '#0a0405' },
        forest: { bg: '#031108', fg: '#e5ffef', accent: '#35c759', purple: '#35c759', border: 'rgba(53,199,89,0.42)', panel: 'rgba(10,28,16,0.58)', panelAlt: 'rgba(8,22,12,0.66)', menu: 'rgba(7,18,10,0.95)', holo1: 'rgba(53,199,89,0.18)', holo2: 'rgba(184,255,77,0.08)', holo3: 'rgba(79,216,200,0.08)', holo4: 'rgba(255,255,255,0.04)', hover: 'rgba(53,199,89,0.44)', bgMain: '#041008' },
        midnight: { bg: '#020814', fg: '#eaf3ff', accent: '#5aa9ff', purple: '#5aa9ff', border: 'rgba(90,169,255,0.42)', panel: 'rgba(8,18,34,0.60)', panelAlt: 'rgba(6,14,28,0.68)', menu: 'rgba(5,11,22,0.95)', holo1: 'rgba(90,169,255,0.18)', holo2: 'rgba(139,233,253,0.10)', holo3: 'rgba(181,124,255,0.08)', holo4: 'rgba(255,255,255,0.04)', hover: 'rgba(90,169,255,0.44)', bgMain: '#040912' },
        ghost: { bg: '#f5f7fb', fg: '#111827', accent: '#4b5563', purple: '#d7dde8', border: 'rgba(75,85,99,0.26)', panel: 'rgba(255,255,255,0.68)', panelAlt: 'rgba(245,247,251,0.78)', menu: 'rgba(255,255,255,0.92)', holo1: 'rgba(203,213,225,0.28)', holo2: 'rgba(255,255,255,0.34)', holo3: 'rgba(148,163,184,0.18)', holo4: 'rgba(255,255,255,0.55)', hover: 'rgba(75,85,99,0.34)', bgMain: '#e8edf5' }
      };
      var theme = themes[themeName] || themes.dedsec;
      var root = document.documentElement.style;
      root.setProperty('--bg', theme.bgMain || theme.bg);
      root.setProperty('--panel', theme.panel);
      root.setProperty('--panel-alt', theme.panelAlt);
      root.setProperty('--menu-solid', theme.menu);
      root.setProperty('--border', theme.border);
      root.setProperty('--hover-border', theme.hover || theme.border);
      root.setProperty('--cyan', theme.accent);
      root.setProperty('--purple', theme.purple || theme.accent);
      root.setProperty('--holo-lavender', theme.holo1);
      root.setProperty('--holo-gold', theme.holo2);
      root.setProperty('--holo-pink', theme.holo3);
      root.setProperty('--holo-white', theme.holo4);
      root.setProperty('--terminal-bg', theme.bg);
      root.setProperty('--terminal-fg', theme.fg);
      root.setProperty('--terminal-accent', theme.accent);
      root.setProperty('--text', theme.text || theme.fg);
      root.setProperty('--muted', theme.muted || theme.fg);
      document.documentElement.setAttribute('data-terminal-theme', themeName);
      try { localStorage.setItem('dedsec_os_terminal_theme', themeName); } catch (err) {}
      document.body.style.backgroundColor = theme.bgMain || theme.bg;
    }

    function renderSystem() {
      if (!state.info) return;
      var body = document.getElementById('systemBody');
      var cards = [
        ['Display Name', state.info.display_name || 'DedSec'],
        ['Language', state.info.language || 'english'],
        ['DedSec Root', state.info.dedsec_root || 'Unavailable'],
        ['Home', state.info.home_dir || 'Unavailable'],
        ['Platform', (state.info.platform || '') + ' ' + (state.info.release || '')],
        ['Machine', state.info.machine || 'Unknown']
      ].map(function(item) {
        return '<div class="info-card"><h3>' + escapeHtml(item[0]) + '</h3><p>' + escapeHtml(item[1]) + '</p></div>';
      }).join('');

      var apps = APP_META.map(function(app) {
        return '<button class="app-card launch-app" data-app="' + app.id + '">' + iconSvg(app.id) + '<h3>' + escapeHtml(t(app.label)) + '</h3><p>Open ' + escapeHtml(t(app.label)) + '</p></button>';
      }).join('');

      body.innerHTML = '' +
        '<div class="panel">' +
          '<div class="grid info">' + cards + '</div>' +
        '</div>' +
        '<div class="panel">' +
          '<div class="screen-title" style="font-size:0.92rem;">' + escapeHtml(t('Apps')) + '</div>' +
          '<div class="grid apps">' + apps + '</div>' +
        '</div>';
      body.querySelectorAll('.launch-app').forEach(function(btn) {
        btn.addEventListener('click', function(){ setActiveApp(btn.getAttribute('data-app')); });
      });
    }

    function pathButtons(roots, onPick) {
      return (roots || []).map(function(root) {
        return '<button class="btn small root-btn" data-path="' + escapeHtml(root.path) + '">' + escapeHtml(root.label) + '</button>';
      }).join('');
    }

    function bindRootButtons(containerId, handler) {
      var host = document.getElementById(containerId);
      host.querySelectorAll('.root-btn').forEach(function(btn){
        btn.addEventListener('click', function(){ handler(btn.getAttribute('data-path')); });
      });
    }

    async function loadFiles(path) {
      var url = '/api/files';
      if (path) url += '?path=' + encodeURIComponent(path);
      var data = await apiGet(url);
      state.filesPath = data.current_path;
      document.getElementById('filesPath').textContent = data.current_path;
      document.getElementById('filesRoots').innerHTML = pathButtons(data.roots || []);
      bindRootButtons('filesRoots', function(newPath){ loadFiles(newPath).catch(handleError); });
      var parentButton = data.parent_path ? '<button class="btn small" id="filesParentBtn">Up</button>' : '';
      var rows = data.entries.map(function(entry) {
        var title = '<div><div class="file-name">' + escapeHtml(entry.name) + '</div><div class="file-meta">' + (entry.is_dir ? t('Folder') : t('File')) + ' • ' + escapeHtml(entry.modified_at || '') + '</div></div>';
        var actions = [];
        if (entry.is_dir) {
          actions.push('<button class="file-btn open-dir" data-path="' + escapeHtml(entry.path) + '">Open</button>');
        } else {
          if (entry.is_text) actions.push('<button class="file-btn open-file" data-path="' + escapeHtml(entry.path) + '">Edit</button>');
          if (entry.runnable) actions.push('<button class="file-btn run-dedsec" data-path="' + escapeHtml(entry.path) + '">Run</button>');
        }
        actions.push('<button class="file-btn copy-item" data-path="' + escapeHtml(entry.path) + '">Copy</button>');
        actions.push('<button class="file-btn move-item" data-path="' + escapeHtml(entry.path) + '">Move</button>');
        actions.push('<button class="file-btn danger-item delete-item" data-path="' + escapeHtml(entry.path) + '">Delete</button>');
        return '<div class="file-row"><div class="file-row-top">' + title + '</div><div class="file-actions">' + actions.join('') + '</div></div>';
      }).join('');
      document.getElementById('filesList').innerHTML = parentButton + rows;
      bindFileActions();
    }

    function bindFileActions() {
      var parentBtn = document.getElementById('filesParentBtn');
      if (parentBtn) {
        parentBtn.addEventListener('click', function(){
          apiGet('/api/files?path=' + encodeURIComponent(state.filesPath)).then(function(data){
            if (data.parent_path) return loadFiles(data.parent_path);
          }).catch(handleError);
        });
      }
      document.querySelectorAll('.open-dir').forEach(function(btn) {
        btn.addEventListener('click', function(){ loadFiles(btn.getAttribute('data-path')).catch(handleError); });
      });
      document.querySelectorAll('.open-file').forEach(function(btn) {
        btn.addEventListener('click', async function(){
          try {
            var data = await apiPost('/api/fs/read', { path: btn.getAttribute('data-path') });
            state.currentFilePath = data.path;
            document.getElementById('editorPath').textContent = data.path;
            document.getElementById('editorArea').value = data.content || '';
            setActiveApp('files');
          } catch (err) { handleError(err); }
        });
      });
      document.querySelectorAll('.copy-item').forEach(function(btn) {
        btn.addEventListener('click', function(){
          state.clipboard = { mode: 'copy', path: btn.getAttribute('data-path') };
          showToast(t('Copied to clipboard'));
        });
      });
      document.querySelectorAll('.move-item').forEach(function(btn) {
        btn.addEventListener('click', function(){
          state.clipboard = { mode: 'move', path: btn.getAttribute('data-path') };
          showToast(t('Move queued'));
        });
      });
      document.querySelectorAll('.delete-item').forEach(function(btn) {
        btn.addEventListener('click', async function(){
          if (!window.confirm(t('Delete this item?'))) return;
          try {
            await apiPost('/api/fs/delete', { path: btn.getAttribute('data-path') });
            await loadFiles(state.filesPath);
            showToast(t('Deleted'));
          } catch (err) { handleError(err); }
        });
      });
      document.querySelectorAll('.run-dedsec').forEach(function(btn) {
        btn.addEventListener('click', function(){ runDedSec(btn.getAttribute('data-path')); });
      });
    }

    async function loadApps(path) {
      var url = '/api/files';
      if (path) url += '?path=' + encodeURIComponent(path);
      var data = await apiGet(url);
      if (!path) {
        state.appsPath = (data.roots.find(function(root){ return root.label === 'DedSec'; }) || {}).path || data.current_path;
        data = await apiGet('/api/files?path=' + encodeURIComponent(state.appsPath));
      } else {
        state.appsPath = data.current_path;
      }
      document.getElementById('appsPath').textContent = data.current_path;
      document.getElementById('appsRoots').innerHTML = pathButtons(data.roots || []);
      bindRootButtons('appsRoots', function(newPath){ loadApps(newPath).catch(handleError); });
      var rows = [];
      if (data.parent_path) {
        rows.push('<div class="file-row"><div class="file-row-top"><div><div class="file-name">..</div><div class="file-meta">Go back</div></div></div><div class="file-actions"><button class="file-btn open-app-dir" data-path="' + escapeHtml(data.parent_path) + '">Open</button></div></div>');
      }
      rows = rows.concat(data.entries.map(function(entry) {
        var actions = [];
        if (entry.is_dir) {
          actions.push('<button class="file-btn open-app-dir" data-path="' + escapeHtml(entry.path) + '">Open</button>');
        }
        if (!entry.is_dir && entry.runnable) {
          actions.push('<button class="file-btn run-app-script" data-path="' + escapeHtml(entry.path) + '">Run</button>');
        }
        return '<div class="file-row"><div class="file-row-top"><div><div class="file-name">' + escapeHtml(entry.name) + '</div><div class="file-meta">' + (entry.is_dir ? t('Folder') : (entry.runnable ? t('Runnable file') : t('File'))) + '</div></div></div><div class="file-actions">' + actions.join('') + '</div></div>';
      }));
      document.getElementById('appsList').innerHTML = rows.join('');
      document.querySelectorAll('.open-app-dir').forEach(function(btn){
        btn.addEventListener('click', function(){ loadApps(btn.getAttribute('data-path')).catch(handleError); });
      });
      document.querySelectorAll('.run-app-script').forEach(function(btn){
        btn.addEventListener('click', function(){ runDedSec(btn.getAttribute('data-path')); });
      });
    }

    async function runDedSec(path) {
      try {
        var data = await apiPost('/api/dedsec/run', { path: path });
        await refreshJobs(data.session.id);
        setActiveApp('terminal');
        showToast(t('Launched') + ' ' + (data.session.label || 'session'));
      } catch (err) { handleError(err); }
    }

    async function loadStore() {
      var data = await apiGet('/api/programs');
      var items = data.programs || [];
      document.getElementById('storeList').innerHTML = items.map(function(program) {
        var actions = [
          '<button class="file-btn install-program" data-id="' + escapeHtml(program.id) + '">Install</button>',
          '<button class="file-btn run-program" data-id="' + escapeHtml(program.id) + '">Run</button>',
          '<button class="file-btn delete-program" data-id="' + escapeHtml(program.id) + '">Delete</button>',
          '<button class="file-btn update-program" data-id="' + escapeHtml(program.id) + '">Update</button>'
        ].join('');
        return '<div class="store-card"><h3>' + escapeHtml(program.name) + '</h3><p>' + escapeHtml(program.description || '') + '</p><div class="subtle">Package: ' + escapeHtml(program.package) + ' • ' + (program.installed ? t('Installed') : t('Not installed')) + '</div><div class="store-actions">' + actions + '</div></div>';
      }).join('');
      document.querySelectorAll('.install-program, .run-program, .delete-program, .update-program').forEach(function(btn) {
        btn.addEventListener('click', async function(){
          try {
            var action = btn.className.indexOf('install-program') >= 0 ? 'install' : btn.className.indexOf('run-program') >= 0 ? 'run' : btn.className.indexOf('delete-program') >= 0 ? 'delete' : 'update';
            var endpoint = '/api/programs/' + action;
            var data = await apiPost(endpoint, { program_id: btn.getAttribute('data-id') });
            await loadStore();
            await refreshJobs(data.session.id);
            setActiveApp('terminal');
          } catch (err) { handleError(err); }
        });
      });
    }

    async function refreshJobs(focusSessionId) {
      var data = await apiGet('/api/jobs');
      state.jobs = data.jobs || [];
      if (focusSessionId) state.selectedSessionId = focusSessionId;
      if (!state.jobs.some(function(item){ return item.id === state.selectedSessionId; })) {
        state.selectedSessionId = 'web-shell';
      }
      renderTerminal();
    }

    function renderSessionsOverlay() {
      var host = document.getElementById('sessionsList');
      if (!host) return;
      host.innerHTML = (state.jobs || []).map(function(job) {
        var status = job.running ? t('Running') : (t('Exit') + ' ' + (job.exit_code == null ? '?' : job.exit_code));
        var closeBtn = job.id === 'web-shell' ? '' : '<button class="btn small danger" data-close="' + escapeHtml(job.id) + '">Close</button>';
        return '<div class="store-card">'
          + '<div class="file-row-top"><div><div class="file-name">' + escapeHtml(job.label) + '</div><div class="file-meta">' + escapeHtml(status) + '</div></div></div>'
          + '<div class="store-actions">'
          + '<button class="btn small" data-open="' + escapeHtml(job.id) + '">' + escapeHtml(t('Open')) + '</button>'
          + closeBtn
          + '</div></div>';
      }).join('') || '<div class="store-card"><p>' + escapeHtml(t('No sessions found.')) + '</p></div>';
      host.querySelectorAll('[data-open]').forEach(function(btn) {
        btn.addEventListener('click', function(){
          state.selectedSessionId = btn.getAttribute('data-open');
          document.getElementById('sessionsOverlay').classList.add('hidden');
          renderTerminal();
        });
      });
      host.querySelectorAll('[data-close]').forEach(function(btn) {
        btn.addEventListener('click', async function(){
          try {
            await apiPost('/api/jobs/stop', { session_id: btn.getAttribute('data-close'), close_only: true });
            await refreshJobs('web-shell');
            renderSessionsOverlay();
          } catch (err) { handleError(err); }
        });
      });
    }

    function scheduleTerminalRefresh() {
      if (state.terminalRefreshTimer) clearTimeout(state.terminalRefreshTimer);
      state.terminalRefreshTimer = setTimeout(function(){ refreshJobs(state.selectedSessionId).catch(function(){}); }, 140);
    }

    async function sendTerminalInputRaw(raw) {
      if (!raw) return;
      try {
        await apiPost('/api/terminal/input', { session_id: state.selectedSessionId, input: raw });
        scheduleTerminalRefresh();
      } catch (err) { handleError(err); }
    }

    function keySeq(name) {
      var map = {
        enter: '\r',
        backspace: '\u007f',
        tab: '\t',
        esc: '\u001b',
        up: '\u001b[A',
        down: '\u001b[B',
        left: '\u001b[D',
        right: '\u001b[C',
        home: '\u001b[H',
        end: '\u001b[F',
        pgup: '\u001b[5~',
        pgdn: '\u001b[6~',
        slash: '/',
        dash: '-'
      };
      return map[name] || name || '';
    }

    function consumeModifiers(value) {
      var output = value;
      if (state.ctrlArmed) {
        state.ctrlArmed = false;
        document.getElementById('ctrlToggleKey').classList.remove('active');
        if (value.length === 1) {
          var upper = value.toUpperCase();
          var code = upper.charCodeAt(0);
          if (code >= 64 && code <= 95) output = String.fromCharCode(code - 64);
        }
      }
      if (state.altArmed) {
        state.altArmed = false;
        document.getElementById('altToggleKey').classList.remove('active');
        output = '' + output;
      }
      return output;
    }

    function focusTerminalComposer() {
      var composer = document.getElementById('terminalComposer');
      composer.focus();
    }

    function scrollTerminalToBottom() {
      var output = document.getElementById('terminalOutput');
      if (!output) return;
      output.scrollTop = output.scrollHeight;
      output.focus({ preventScroll: true });
    }

    function renderTerminal() {
      var selected = state.jobs.find(function(item){ return item.id === state.selectedSessionId; }) || state.jobs[0];
      if (!selected) return;
      state.selectedSessionId = selected.id;
      document.getElementById('terminalOutput').textContent = selected.log_tail || '';
      var canAcceptInput = selected.kind === 'web-shell' || selected.running;
      document.getElementById('terminalComposer').disabled = !canAcceptInput;
      document.getElementById('terminalExtraKeys').style.opacity = canAcceptInput ? '1' : '0.55';
      renderSessionsOverlay();
      applyTerminalZoom();
    }

    async function loadWebSettingsMeta() {
      try {
        var data = await apiGet('/api/settings/meta');
        var meta = data.meta || {};
        var el;
        el = document.getElementById('webPromptUsername'); if (el) el.value = meta.prompt_username || (state.config && state.config.display_name) || 'DedSec';
        el = document.getElementById('webLanguageSelect'); if (el) el.value = meta.language || 'english';
        el = document.getElementById('webMenuStyleSelect'); if (el) el.value = meta.menu_style || 'list';
        el = document.getElementById('webAutostartChk'); if (el) el.checked = !!meta.menu_autostart;
      } catch (err) { handleError(err); }
    }

    async function runSettingsAction(action, extra) {
      var payload = Object.assign({ action: action }, extra || {});
      var data = await apiPost('/api/settings/action', payload);
      if (data.session) {
        await refreshJobs(data.session.id);
        setActiveApp('terminal');
      } else if (data.meta) {
        showToast(t('Saved'));
        await loadWebSettingsMeta();
      }
    }

    async function saveEditor() {
      if (!state.currentFilePath) {
        showToast(t('Open a text file first'), true);
        return;
      }
      try {
        await apiPost('/api/fs/write', { path: state.currentFilePath, content: document.getElementById('editorArea').value });
        showToast(t('File saved'));
        await loadFiles(state.filesPath);
      } catch (err) { handleError(err); }
    }

    async function pasteClipboard() {
      if (!state.clipboard) {
        showToast(t('Clipboard is empty'), true);
        return;
      }
      var source = state.clipboard.path;
      var name = source.split('/').pop();
      var destination = state.filesPath.replace(/\/$/, '') + '/' + name;
      try {
        var endpoint = state.clipboard.mode === 'move' ? '/api/fs/move' : '/api/fs/copy';
        await apiPost(endpoint, { source: source, destination: destination });
        state.clipboard = null;
        await loadFiles(state.filesPath);
        showToast(t('Paste complete'));
      } catch (err) { handleError(err); }
    }

    async function saveSettings() {
      try {
        var profiles = Array.from(document.querySelectorAll('#userProfilesList option')).map(function(node){ return node.value; }).filter(Boolean);
        var currentName = document.getElementById('displayNameInput').value.trim();
        if (currentName && profiles.indexOf(currentName) === -1) profiles.push(currentName);
        var payload = {
          display_name: currentName,
          wallpaper: document.getElementById('wallpaperInput').value.trim(),
          terminal_theme: document.getElementById('terminalThemeSelect').value,
          terminal_zoom: state.terminalZoom,
          sidebar_hidden: state.sidebarHidden,
          user_profiles: profiles,
          login_enabled: document.getElementById('loginEnabledChk').checked,
          login_password: document.getElementById('loginPasswordSetting').value,
          totp_enabled: document.getElementById('totpEnabledChk').checked,
          security_questions: [
            { question: document.getElementById('securityQuestion1Setting').value, answer: document.getElementById('securityAnswer1Setting').value },
            { question: document.getElementById('securityQuestion2Setting').value, answer: document.getElementById('securityAnswer2Setting').value },
            { question: document.getElementById('securityQuestion3Setting').value, answer: document.getElementById('securityAnswer3Setting').value }
          ]
        };
        var fileInput = document.getElementById('wallpaperUpload');
        if (fileInput.files && fileInput.files[0]) {
          payload.wallpaper_upload = await readFileAsDataUrl(fileInput.files[0]);
          payload.wallpaper_filename = fileInput.files[0].name;
        }
        var data = await apiPost('/api/config', payload);
        state.config = data.config;
        if (state.info) state.info.display_name = data.config.display_name;
        applyWallpaper(state.config);
        applyTranslations();
        renderSystem();
        showToast(t('Settings saved'));
      } catch (err) { handleError(err); }
    }

    function readFileAsDataUrl(file) {
      return new Promise(function(resolve, reject) {
        var reader = new FileReader();
        reader.onload = function(){ resolve(reader.result); };
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    }

    function handleError(error) {
      console.error(error);
      showToast(error.message || String(error), true);
      hideLoading();
    }

    function closeWebFaceView() {
      window.setTimeout(function(){
        try { window.open('', '_self'); } catch (err) {}
        try { window.close(); } catch (err) {}
        window.location.replace('about:blank');
      }, 220);
    }

    async function exitDedsecOs() {
      var question = currentLang() === 'el'
        ? 'Να κλείσει το DedSec OS, να τερματιστεί πρώτα το Termux API και μετά το ίδιο το Termux;'
        : 'Close DedSec OS, stop Termux API first, and then stop Termux itself?';
      if (!window.confirm(question)) return;
      try {
        await apiPost('/api/system/exit', {});
      } catch (err) {
        console.warn(err);
      }
      closeWebFaceView();
    }

    function populateRecoveryQuestions() {
      var questions = state.recoveryQuestions || [];
      ['1','2','3'].forEach(function(num, idx){
        var questionInput = document.getElementById('recoveryQuestion' + num + 'Input');
        if (questionInput) questionInput.value = (questions[idx] && questions[idx].question) || '';
      });
    }

    function toggleRecoveryPanel(show) {
      var panel = document.getElementById('recoveryPanel');
      if (panel) panel.classList.toggle('hidden', !show);
      if (show) populateRecoveryQuestions();
    }

    async function submitLogin() {
      var input = document.getElementById('loginPasswordInput');
      var otpInput = document.getElementById('loginOtpInput');
      try {
        await apiPost('/api/auth/login', { username: document.getElementById('loginUsernameInput').value.trim(), password: input ? input.value : '', otp: otpInput ? otpInput.value : '' });
        state.authenticated = true;
        state.authRequired = false;
        hideLoginOverlay();
        await bootApp();
      } catch (err) {
        showToast(err.message || t('Wrong password'), true);
        if (input) { input.value = ''; input.focus(); }
        if (otpInput) otpInput.value = '';
      }
    }

    async function submitRecovery() {
      try {
        await apiPost('/api/auth/recover', {
          username: document.getElementById('loginUsernameInput').value.trim(),
          answers: [
            document.getElementById('recoveryAnswer1Input').value,
            document.getElementById('recoveryAnswer2Input').value,
            document.getElementById('recoveryAnswer3Input').value
          ],
          new_password: document.getElementById('recoveryNewPasswordInput').value
        });
        state.authenticated = true;
        state.authRequired = false;
        hideLoginOverlay();
        await bootApp();
      } catch (err) {
        showToast(err.message || t('Recovery answers do not match.'), true);
      }
    }

    function bindLoginUi() {
      var btn = document.getElementById('loginSubmitBtn');
      if (btn && !btn.dataset.bound) {
        btn.dataset.bound = '1';
        btn.addEventListener('click', function(){ submitLogin().catch(handleError); });
      }
      ['loginUsernameInput','loginPasswordInput','loginOtpInput'].forEach(function(id){
        var input = document.getElementById(id);
        if (input && !input.dataset.bound) {
          input.dataset.bound = '1';
          input.addEventListener('keydown', function(event){ if (event.key === 'Enter') { event.preventDefault(); submitLogin().catch(handleError); } });
        }
      });
      var forgotBtn = document.getElementById('forgotPasswordBtn');
      if (forgotBtn && !forgotBtn.dataset.bound) {
        forgotBtn.dataset.bound = '1';
        forgotBtn.addEventListener('click', function(){ toggleRecoveryPanel(true); });
      }
      var recoveryBtn = document.getElementById('recoverySubmitBtn');
      if (recoveryBtn && !recoveryBtn.dataset.bound) {
        recoveryBtn.dataset.bound = '1';
        recoveryBtn.addEventListener('click', function(){ submitRecovery().catch(handleError); });
      }
    }

    async function bootApp() {
      try {
        var results = await Promise.all([
          apiGet('/api/info'),
          apiGet('/api/config'),
          apiGet('/api/jobs')
        ]);
        state.info = results[0];
        state.config = results[1].config;
        state.jobs = results[2].jobs || [];
        applyWallpaper(state.config);
        applyTranslations();
        renderSystem();
        await loadFiles(state.info.dedsec_root || state.info.home_dir);
        await loadApps(state.info.dedsec_root || state.info.home_dir);
        await loadStore();
        renderTerminal();
        await loadWebSettingsMeta();
        applyTerminalZoom();
        if (!state.uiBound) {
          bindUi();
          bindTerminalPinchZoom();
          bindMenuToggle();
          state.uiBound = true;
        }
        focusTerminalComposer();
        state.booted = true;
      } catch (err) {
        handleError(err);
      } finally {
        hideLoading();
      }
    }

    async function init() {
      renderDock();
      bindLoginUi();
      try {
        var auth = await apiGet('/api/auth/status');
        state.authStatus = auth;
        state.recoveryQuestions = auth.security_questions || [];
        if (auth.config) {
          state.config = auth.config;
          applyWallpaper(state.config);
        }
        var profileList = document.getElementById('loginProfilesList'); if (profileList) profileList.innerHTML = (auth.profiles || []).map(function(name){ return '<option value="' + escapeHtml(name) + '"></option>'; }).join('');
        state.authRequired = !!auth.enabled && !auth.authenticated;
        state.authenticated = !!auth.authenticated;
        var otpField = document.getElementById('loginOtpField'); if (otpField) otpField.classList.toggle('hidden', !auth.totp_enabled);
        if (state.authRequired) {
          applyTranslations();
          populateRecoveryQuestions();
          hideLoading();
          return;
        }
        await bootApp();
      } catch (err) {
        handleError(err);
      }
    }

    function updateClock() {
      var now = new Date();
      document.getElementById('clock').textContent = now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
    }

    function bindUi() {
      var batteryBtn = document.getElementById('batteryLabel'); if (batteryBtn) renderBatteryStatus();
      var alertsBtn = document.getElementById('notificationsBtn'); if (alertsBtn) alertsBtn.addEventListener('click', async function(){ try { var data=await apiGet('/api/notifications'); renderNotificationsPanel((data.notifications && data.notifications.items) || []); } catch(err){ handleError(err); } });
      var hideSidebarBtn = document.getElementById('hideSidebarBtn'); if (hideSidebarBtn) hideSidebarBtn.addEventListener('click', function(){ applySidebarVisibility(true); saveUiPrefs(); });
      var showSidebarBtn = document.getElementById('showSidebarBtn'); if (showSidebarBtn) showSidebarBtn.addEventListener('click', function(){ applySidebarVisibility(false); saveUiPrefs(); });
      var backBtn = document.getElementById('backNavBtn'); if (backBtn) backBtn.addEventListener('click', function(){ if (state.lastApp) setActiveApp(state.lastApp); });
      document.getElementById('refreshSystemBtn').addEventListener('click', async function(){
        try { state.info = await apiGet('/api/info'); renderSystem(); } catch (err) { handleError(err); }
      });
      document.getElementById('filesRefreshBtn').addEventListener('click', function(){ loadFiles(state.filesPath).catch(handleError); });
      document.getElementById('filesNewFolderBtn').addEventListener('click', async function(){
        var name = window.prompt(t('Folder name'));
        if (!name) return;
        try {
          await apiPost('/api/fs/mkdir', { path: state.filesPath.replace(/\/$/, '') + '/' + name });
          await loadFiles(state.filesPath);
        } catch (err) { handleError(err); }
      });
      document.getElementById('filesNewFileBtn').addEventListener('click', async function(){
        var name = window.prompt(t('File name'));
        if (!name) return;
        try {
          await apiPost('/api/fs/newfile', { path: state.filesPath.replace(/\/$/, '') + '/' + name, content: '' });
          await loadFiles(state.filesPath);
        } catch (err) { handleError(err); }
      });
      document.getElementById('filesPasteBtn').addEventListener('click', pasteClipboard);
      document.getElementById('editorSaveBtn').addEventListener('click', saveEditor);
      document.getElementById('terminalRefreshBtn').addEventListener('click', function(){ refreshJobs().catch(handleError); });
      document.getElementById('terminalSessionsBtn').addEventListener('click', function(){
        document.getElementById('sessionsOverlay').classList.remove('hidden');
        renderSessionsOverlay();
      });
      document.getElementById('sessionsCloseBtn').addEventListener('click', function(){
        document.getElementById('sessionsOverlay').classList.add('hidden');
      });
      document.getElementById('sessionsNewBtn').addEventListener('click', async function(){
        try {
          var data = await apiPost('/api/jobs/new-shell', { cwd: (state.info && state.info.dedsec_root) || (state.info && state.info.home_dir) || '/' });
          document.getElementById('sessionsOverlay').classList.add('hidden');
          await refreshJobs((data.session && data.session.id) || state.selectedSessionId);
          focusTerminalComposer();
        } catch (err) { handleError(err); }
      });
      document.getElementById('sessionsOverlay').addEventListener('click', function(event){
        if (event.target === this) this.classList.add('hidden');
      });
      document.getElementById('terminalOutput').addEventListener('click', focusTerminalComposer);
      document.getElementById('terminalWrap').addEventListener('click', function(event){
        if (!event.target.closest('.extra-key') && !event.target.closest('.btn')) focusTerminalComposer();
      });
      document.getElementById('terminalOutput').addEventListener('keydown', function(event){ event.preventDefault(); focusTerminalComposer(); });
      var composer = document.getElementById('terminalComposer');
      composer.addEventListener('keydown', async function(event){
        if (event.key === 'Enter') { event.preventDefault(); await sendTerminalInputRaw(consumeModifiers(keySeq('enter'))); this.value=''; return; }
        if (event.key === 'Backspace') { event.preventDefault(); await sendTerminalInputRaw(consumeModifiers(keySeq('backspace'))); this.value=''; return; }
        if (event.key === 'Tab') { event.preventDefault(); await sendTerminalInputRaw(consumeModifiers(keySeq('tab'))); this.value=''; return; }
        if (event.key === 'Escape') { event.preventDefault(); await sendTerminalInputRaw(consumeModifiers(keySeq('esc'))); this.value=''; return; }
        if (event.key === 'ArrowUp') { event.preventDefault(); await sendTerminalInputRaw(consumeModifiers(keySeq('up'))); this.value=''; return; }
        if (event.key === 'ArrowDown') { event.preventDefault(); await sendTerminalInputRaw(consumeModifiers(keySeq('down'))); this.value=''; return; }
        if (event.key === 'ArrowLeft') { event.preventDefault(); await sendTerminalInputRaw(consumeModifiers(keySeq('left'))); this.value=''; return; }
        if (event.key === 'ArrowRight') { event.preventDefault(); await sendTerminalInputRaw(consumeModifiers(keySeq('right'))); this.value=''; return; }
        if (event.ctrlKey && event.key && event.key.length === 1) { event.preventDefault(); await sendTerminalInputRaw(String.fromCharCode(event.key.toUpperCase().charCodeAt(0) - 64)); this.value=''; return; }
      });
      composer.addEventListener('input', async function(){
        var value = this.value;
        if (!value) return;
        this.value = '';
        await sendTerminalInputRaw(consumeModifiers(value));
      });
      document.querySelectorAll('#terminalExtraKeys [data-key], #terminalExtraKeys [data-seq]').forEach(function(btn){
        btn.addEventListener('click', async function(event){
          event.stopPropagation();
          var rawSeq = btn.getAttribute('data-seq');
          var keyName = btn.getAttribute('data-key');
          if (rawSeq !== null) {
            await sendTerminalInputRaw(consumeModifiers(rawSeq));
          } else if (keyName) {
            await sendTerminalInputRaw(consumeModifiers(keySeq(keyName)));
          }
          focusTerminalComposer();
        });
      });
      var terminalBottomBtn = document.getElementById('terminalBottomBtn');
      if (terminalBottomBtn) {
        terminalBottomBtn.addEventListener('click', function(event){
          event.stopPropagation();
          scrollTerminalToBottom();
          focusTerminalComposer();
        });
      }
      document.getElementById('ctrlToggleKey').addEventListener('click', function(event){
        event.stopPropagation();
        state.ctrlArmed = !state.ctrlArmed;
        this.classList.toggle('active', state.ctrlArmed);
        if (state.ctrlArmed) { state.altArmed = false; document.getElementById('altToggleKey').classList.remove('active'); }
        focusTerminalComposer();
      });
      document.getElementById('altToggleKey').addEventListener('click', function(event){
        event.stopPropagation();
        state.altArmed = !state.altArmed;
        this.classList.toggle('active', state.altArmed);
        if (state.altArmed) { state.ctrlArmed = false; document.getElementById('ctrlToggleKey').classList.remove('active'); }
        focusTerminalComposer();
      });
      document.getElementById('appsRefreshBtn').addEventListener('click', function(){ loadApps(state.appsPath).catch(handleError); });
      document.getElementById('storeRefreshBtn').addEventListener('click', function(){ loadStore().catch(handleError); });
      document.getElementById('saveSettingsBtn').addEventListener('click', saveSettings);
      var savePromptBtn = document.getElementById('savePromptBtn'); if (savePromptBtn) savePromptBtn.addEventListener('click', function(){ runSettingsAction('save_prompt', { prompt_username: document.getElementById('webPromptUsername').value.trim() }).catch(handleError); });
      var saveLanguageBtn = document.getElementById('saveLanguageBtn'); if (saveLanguageBtn) saveLanguageBtn.addEventListener('click', function(){ runSettingsAction('save_language', { language: document.getElementById('webLanguageSelect').value }).catch(handleError); });
      var saveMenuStyleBtn = document.getElementById('saveMenuStyleBtn'); if (saveMenuStyleBtn) saveMenuStyleBtn.addEventListener('click', function(){ runSettingsAction('save_menu_style', { menu_style: document.getElementById('webMenuStyleSelect').value }).catch(handleError); });
      var saveAutostartBtn = document.getElementById('saveAutostartBtn'); if (saveAutostartBtn) saveAutostartBtn.addEventListener('click', function(){ runSettingsAction('save_autostart', { enabled: document.getElementById('webAutostartChk').checked }).catch(handleError); });
      var updateSource1Btn = document.getElementById('updateSource1Btn'); if (updateSource1Btn) updateSource1Btn.addEventListener('click', function(){ runSettingsAction('update_source_1').catch(handleError); });
      var updateSource2Btn = document.getElementById('updateSource2Btn'); if (updateSource2Btn) updateSource2Btn.addEventListener('click', function(){ runSettingsAction('update_source_2').catch(handleError); });
      var updatePackagesBtn = document.getElementById('updatePackagesBtn'); if (updatePackagesBtn) updatePackagesBtn.addEventListener('click', function(){ runSettingsAction('update_packages').catch(handleError); });
      var exitDedsecOsBtn = document.getElementById('exitDedsecOsBtn'); if (exitDedsecOsBtn) exitDedsecOsBtn.addEventListener('click', function(){ exitDedsecOs().catch(handleError); });
      document.getElementById('resetWallpaperBtn').addEventListener('click', async function(){
        try {
          var data = await apiPost('/api/config', { reset_wallpaper: true, display_name: document.getElementById('displayNameInput').value.trim() });
          state.config = data.config;
          applyWallpaper(state.config);
          showToast(t('Wallpaper reset'));
        } catch (err) { handleError(err); }
      });
      document.getElementById('toggleFullscreenBtn').addEventListener('click', async function(){
        try {
          if (!document.fullscreenElement) {
            await document.documentElement.requestFullscreen();
            showToast('Full screen enabled');
          } else {
            await document.exitFullscreen();
            showToast('Full screen disabled');
          }
        } catch (err) { handleError(err); }
      });
      var systemBody = document.getElementById('systemBody');
      var pressTimer = null;
      systemBody.addEventListener('pointerdown', function(){
        pressTimer = window.setTimeout(function(){ document.getElementById('wallpaperUpload').click(); }, 650);
      });
      ['pointerup', 'pointerleave', 'pointercancel'].forEach(function(type){
        systemBody.addEventListener(type, function(){ if (pressTimer) { clearTimeout(pressTimer); pressTimer = null; } });
      });
      document.getElementById('wallpaperUpload').addEventListener('change', function(){
        if (this.files && this.files[0]) saveSettings().catch(handleError);
      });
      document.getElementById('terminalThemeSelect').addEventListener('change', function(){ applyTerminalTheme(this.value); });
      renderBatteryStatus();
      window.setInterval(function(){ refreshJobs().catch(function(){}); }, 2500);
      window.setInterval(function(){ renderBatteryStatus(); }, 15000);
    }

    window.addEventListener('pageshow', function(){ setTimeout(hideLoading, 120); });
    document.addEventListener('readystatechange', function(){ if (document.readyState === 'complete') setTimeout(hideLoading, 120); });
    window.setTimeout(hideLoading, 10000);
    init();
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    server_version = 'DedSecOS/1.0'

    def log_message(self, format_string, *args):
        return

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            route = parsed.path
            params = urllib.parse.parse_qs(parsed.query)
            if route == '/api/auth/status':
                cfg = load_global_config()
                send_json(self, 200, {'ok': True, 'enabled': is_auth_enabled(), 'authenticated': is_request_authenticated(self), 'totp_enabled': bool(cfg.get('totp_enabled')), 'security_questions': public_config(cfg).get('security_questions', []), 'profiles': cfg.get('user_profiles', []), 'config': public_config(cfg)})
                return
            REQUEST_CONTEXT.username = current_request_username(self)
            if route != '/' and is_auth_enabled() and not is_request_authenticated(self):
                send_json(self, 401, {'ok': False, 'error': 'Authentication required.'})
                return
            if route == '/':
                boot_theme = json.dumps((public_config().get('terminal_theme') or 'dedsec'))
                content = INDEX_HTML.replace('__BOOT_THEME__', boot_theme, 1).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(content)
                return
            if route == '/api/info':
                send_json(self, 200, collect_info())
                return
            if route == '/api/config':
                send_json(self, 200, {'ok': True, 'config': public_config()})
                return
            if route == '/api/programs':
                send_json(self, 200, {'ok': True, 'programs': get_program_catalog()})
                return
            if route == '/api/files':
                target_path = params.get('path', [''])[0]
                send_json(self, 200, {'ok': True, **list_directory(target_path)})
                return
            if route == '/api/jobs':
                send_json(self, 200, {'ok': True, 'jobs': get_jobs()})
                return
            if route == '/api/settings/meta':
                send_json(self, 200, {'ok': True, 'meta': settings_meta()})
                return
            if route == '/api/status':
                send_json(self, 200, {'ok': True, 'battery': collect_battery_status()})
                return
            if route == '/api/notifications':
                send_json(self, 200, {'ok': True, 'notifications': collect_notifications()})
                return
            if route.startswith('/wallpapers/'):
                filename = os.path.basename(route[len('/wallpapers/'):])
                target = os.path.join(WALLPAPERS_DIR, filename)
                if not os.path.isfile(target):
                    send_json(self, 404, {'ok': False, 'error': 'Wallpaper not found.'})
                    return
                with open(target, 'rb') as handle:
                    content = handle.read()
                mime = mimetypes.guess_type(target)[0] or 'application/octet-stream'
                self.send_response(200)
                self.send_header('Content-Type', mime)
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(content)
                return
            send_json(self, 404, {'ok': False, 'error': 'Unknown GET route: ' + route})
        except Exception as exc:
            send_json(self, 400, {'ok': False, 'error': str(exc)})

    def do_POST(self):
        try:
            payload = parse_json_body(self)
            route = self.path
            if route == '/api/auth/login':
                config = load_global_config()
                username = sanitize_username(payload.get('username') or config.get('display_name') or 'DedSec')
                password = payload.get('password') or ''
                otp = str(payload.get('otp') or '').strip()
                if not config.get('login_enabled') or not config.get('password_hash'):
                    token = issue_auth_token(username)
                    send_json(self, 200, {'ok': True, 'authenticated': True}, extra_headers=[('Set-Cookie', 'dedsec_os_auth=' + token + '; Path=/; HttpOnly; SameSite=Lax')])
                    return
                if hash_password(password) != config.get('password_hash'):
                    send_json(self, 403, {'ok': False, 'error': 'Wrong password.'})
                    return
                if config.get('totp_enabled'):
                    if not (otp.isdigit() and len(otp) == 6):
                        send_json(self, 403, {'ok': False, 'error': 'A 6-digit authenticator code is required.'})
                        return
                    current = compute_totp_code(config.get('totp_secret') or '')
                    previous = compute_totp_code(config.get('totp_secret') or '', for_time=time.time() - 30)
                    next_code = compute_totp_code(config.get('totp_secret') or '', for_time=time.time() + 30)
                    if otp not in {current, previous, next_code}:
                        send_json(self, 403, {'ok': False, 'error': 'A 6-digit authenticator code is required.'})
                        return
                token = issue_auth_token(username)
                unlock_termux_gate()
                send_json(self, 200, {'ok': True, 'authenticated': True}, extra_headers=[('Set-Cookie', 'dedsec_os_auth=' + token + '; Path=/; HttpOnly; SameSite=Lax')])
                return
            if route == '/api/auth/recover':
                config = load_config()
                answers = payload.get('answers') if isinstance(payload.get('answers'), list) else []
                questions = config.get('security_questions') or []
                if len(answers) < 3 or len(questions) < 3:
                    send_json(self, 400, {'ok': False, 'error': 'Recovery answers do not match.'})
                    return
                for idx in range(3):
                    if hash_answer(answers[idx] if idx < len(answers) else '') != str(questions[idx].get('answer_hash') or ''):
                        send_json(self, 403, {'ok': False, 'error': 'Recovery answers do not match.'})
                        return
                new_password = str(payload.get('new_password') or '').strip()
                if not new_password:
                    send_json(self, 400, {'ok': False, 'error': 'New password is required.'})
                    return
                config['login_enabled'] = True
                config['password_hash'] = hash_password(new_password)
                config = save_config(config)
                token = issue_auth_token(username)
                unlock_termux_gate()
                send_json(self, 200, {'ok': True, 'authenticated': True, 'config': public_config(global_cfg)}, extra_headers=[('Set-Cookie', 'dedsec_os_auth=' + token + '; Path=/; HttpOnly; SameSite=Lax')])
                return
            REQUEST_CONTEXT.username = current_request_username(self)
            if is_auth_enabled() and not is_request_authenticated(self):
                send_json(self, 401, {'ok': False, 'error': 'Authentication required.'})
                return
            if route == '/api/terminal/run':
                session_id = payload.get('session_id') or 'web-shell'
                session = run_web_shell_command(session_id, payload.get('command', ''))
                send_json(self, 200, {'ok': True, 'session': session})
                return
            if route == '/api/terminal/input':
                session_id = payload.get('session_id') or 'web-shell'
                session = send_raw_input(session_id, payload.get('input', ''))
                send_json(self, 200, {'ok': True, 'session': session})
                return
            if route == '/api/jobs/new-shell':
                session = start_interactive_shell_session(cwd=payload.get('cwd') or web_shell_current_cwd(), label=(payload.get('label') or 'Shell Session'))
                send_json(self, 200, {'ok': True, 'session': session})
                return
            if route == '/api/config':
                config = load_config()
                global_config = load_global_config()
                display_name = sanitize_username((payload.get('display_name') or '').strip() or active_username())
                config['display_name'] = display_name
                profiles = payload.get('user_profiles') if isinstance(payload.get('user_profiles'), list) else global_config.get('user_profiles', [])
                if display_name not in profiles:
                    profiles.append(display_name)
                global_config['user_profiles'] = [sanitize_username(item) for item in profiles if str(item).strip()]
                global_config['display_name'] = display_name
                REQUEST_CONTEXT.username = display_name
                ensure_user_space(display_name)
                terminal_theme = (payload.get('terminal_theme') or '').strip()
                if terminal_theme:
                    config['terminal_theme'] = terminal_theme
                if payload.get('terminal_zoom') is not None:
                    try:
                        config['terminal_zoom'] = max(0.8, min(2.5, float(payload.get('terminal_zoom'))))
                    except Exception:
                        pass
                if payload.get('sidebar_hidden') is not None:
                    config['sidebar_hidden'] = bool(payload.get('sidebar_hidden'))
                if payload.get('login_enabled') is not None:
                    global_config['login_enabled'] = bool(payload.get('login_enabled'))
                login_password = payload.get('login_password')
                if global_config.get('login_enabled'):
                    if str(login_password or '').strip():
                        global_config['password_hash'] = hash_password(str(login_password))
                    elif not global_config.get('password_hash'):
                        raise ValueError('A password is required when login protection is enabled.')
                else:
                    global_config['password_hash'] = ''
                    global_config['totp_enabled'] = False
                if payload.get('totp_enabled') is not None:
                    global_config['totp_enabled'] = bool(payload.get('totp_enabled')) and bool(global_config.get('login_enabled'))
                if global_config.get('totp_enabled') and not str(global_config.get('totp_secret') or '').strip():
                    global_config['totp_secret'] = random_base32_secret()
                if not global_config.get('totp_enabled'):
                    global_config['totp_secret'] = global_config.get('totp_secret') or ''
                raw_questions = payload.get('security_questions') if isinstance(payload.get('security_questions'), list) else []
                updated_questions = []
                existing_questions = global_config.get('security_questions') or []
                for idx in range(3):
                    incoming = raw_questions[idx] if idx < len(raw_questions) and isinstance(raw_questions[idx], dict) else {}
                    previous = existing_questions[idx] if idx < len(existing_questions) and isinstance(existing_questions[idx], dict) else {}
                    question = str(incoming.get('question') or previous.get('question') or '').strip()
                    answer_raw = str(incoming.get('answer') or '').strip()
                    answer_hash = hash_answer(answer_raw) if answer_raw else str(previous.get('answer_hash') or '')
                    if question or answer_hash:
                        updated_questions.append({'question': question, 'answer_hash': answer_hash})
                global_config['security_questions'] = updated_questions
                if global_config.get('login_enabled') and not security_questions_configured(global_config):
                    raise ValueError('Please set 3 security questions and answers.')
                if payload.get('reset_wallpaper'):
                    config['wallpaper'] = ''
                    config['wallpaper_name'] = ''
                wallpaper_value = (payload.get('wallpaper') or '').strip()
                if wallpaper_value:
                    config['wallpaper'] = wallpaper_value
                    config['wallpaper_name'] = os.path.basename(wallpaper_value)
                upload_data = payload.get('wallpaper_upload')
                if upload_data:
                    if ',' in upload_data:
                        _, encoded = upload_data.split(',', 1)
                    else:
                        encoded = upload_data
                    binary = base64.b64decode(encoded)
                    filename = payload.get('wallpaper_filename') or ('wallpaper-' + uuid.uuid4().hex[:8] + '.png')
                    filename = os.path.basename(filename)
                    target = os.path.join(WALLPAPERS_DIR, filename)
                    with open(target, 'wb') as handle:
                        handle.write(binary)
                    config['wallpaper'] = '/wallpapers/' + filename
                    config['wallpaper_name'] = filename
                save_global_config(global_config)
                config = save_config(config)
                send_json(self, 200, {'ok': True, 'config': public_config(config)})
                return
            if route == '/api/fs/read':
                path = safe_realpath(payload.get('path'), must_exist=True)
                if os.path.isdir(path):
                    raise IsADirectoryError('Cannot read a directory.')
                if not is_text_file(path):
                    raise ValueError('Only text files can be opened in the editor.')
                send_json(self, 200, {'ok': True, 'path': path, 'content': read_text_file(path)})
                return
            if route == '/api/fs/write':
                path = safe_realpath(payload.get('path'), must_exist=True)
                if os.path.isdir(path):
                    raise IsADirectoryError('Cannot write to a directory.')
                write_text_file(path, payload.get('content', ''))
                send_json(self, 200, {'ok': True, 'path': path})
                return
            if route == '/api/fs/mkdir':
                target = safe_target_path(payload.get('path'))
                os.makedirs(target, exist_ok=False)
                send_json(self, 200, {'ok': True, 'path': target})
                return
            if route == '/api/fs/newfile':
                target = safe_target_path(payload.get('path'))
                if os.path.exists(target):
                    raise FileExistsError('File already exists: ' + target)
                write_text_file(target, payload.get('content', ''))
                send_json(self, 200, {'ok': True, 'path': target})
                return
            if route == '/api/fs/delete':
                path = safe_realpath(payload.get('path'), must_exist=True)
                if path == os.path.realpath(HOME_DIR):
                    raise ValueError('Refusing to delete the Termux home directory.')
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                send_json(self, 200, {'ok': True})
                return
            if route == '/api/fs/copy':
                source = safe_realpath(payload.get('source'), must_exist=True)
                destination = safe_target_path(payload.get('destination'))
                if os.path.exists(destination):
                    raise FileExistsError('Destination already exists: ' + destination)
                if os.path.isdir(source):
                    shutil.copytree(source, destination)
                else:
                    shutil.copy2(source, destination)
                send_json(self, 200, {'ok': True, 'destination': destination})
                return
            if route == '/api/fs/move':
                source = safe_realpath(payload.get('source'), must_exist=True)
                destination = safe_target_path(payload.get('destination'))
                if os.path.exists(destination):
                    raise FileExistsError('Destination already exists: ' + destination)
                shutil.move(source, destination)
                send_json(self, 200, {'ok': True, 'destination': destination})
                return
            if route == '/api/jobs/stop':
                job = stop_job(payload.get('session_id'), bool(payload.get('close_only')))
                send_json(self, 200, {'ok': True, 'session': job})
                return
            if route == '/api/system/exit':
                send_json(self, 200, {'ok': True, **request_system_exit()})
                return
            if route == '/api/programs/install':
                job = run_store_program(payload.get('program_id'), 'install')
                send_json(self, 200, {'ok': True, 'session': job})
                return
            if route == '/api/programs/run':
                job = run_store_program(payload.get('program_id'), 'run')
                send_json(self, 200, {'ok': True, 'session': job})
                return
            if route == '/api/programs/delete':
                job = run_store_program(payload.get('program_id'), 'delete')
                send_json(self, 200, {'ok': True, 'session': job})
                return
            if route == '/api/programs/update':
                job = run_store_program(payload.get('program_id'), 'update')
                send_json(self, 200, {'ok': True, 'session': job})
                return
            if route == '/api/dedsec/run':
                job = run_dedsec_script(payload.get('path'))
                send_json(self, 200, {'ok': True, 'session': job})
                return
            if route == '/api/settings/action':
                result = run_settings_action(payload.get('action'), payload)
                if isinstance(result, dict) and 'id' not in result and 'session' not in result:
                    send_json(self, 200, {'ok': True, **result})
                else:
                    send_json(self, 200, {'ok': True, 'session': result})
                return
            send_json(self, 404, {'ok': False, 'error': 'Unknown POST route: ' + route})
        except Exception as exc:
            send_json(self, 400, {'ok': False, 'error': str(exc)})


def run_server():
    ensure_setup()
    ensure_web_shell_session()
    httpd = ThreadingHTTPServer(('0.0.0.0', PORT), Handler)
    print('DedSec OS listening on http://127.0.0.1:' + str(PORT), flush=True)
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()
'''
    replacements = {
        '__HOME_DIR__': repr(HOME_DIR),
        '__LANGUAGE_JSON_PATH__': repr(LANGUAGE_JSON_PATH),
        '__ENGLISH_BASE_PATH__': repr(ENGLISH_BASE_PATH),
        '__GREEK_PATH_FULL__': repr(GREEK_PATH_FULL),
        '__HIDDEN_GREEK_PATH__': repr(HIDDEN_GREEK_PATH),
        '__SETTINGS_SCRIPT_PATH__': repr(SETTINGS_SCRIPT_PATH),
        '__BASHRC_PATH__': repr(BASHRC_PATH),
        '__REPO_URL_SOURCE_1__': repr(REPO_URL_SOURCE_1),
        '__REPO_URL_SOURCE_2__': repr(REPO_URL_SOURCE_2),
        '__BASHRC_START_MARKER__': repr(BASHRC_START_MARKER),
        '__BASHRC_END_MARKER__': repr(BASHRC_END_MARKER),
        '__SPONSORS_ROOT_PATH__': repr(SPONSORS_ROOT_PATH),
        '__SPONSORS_ENGLISH_FOLDER_NAME__': repr(SPONSORS_ENGLISH_FOLDER_NAME),
        '__SPONSORS_GREEK_FOLDER_NAME__': repr(SPONSORS_GREEK_FOLDER_NAME),
        '__DEDSEC_OS_ROOT__': repr(DEDSEC_OS_ROOT),
    }
    for token, value in replacements.items():
        server_template = server_template.replace(token, value)
    return textwrap.dedent(server_template).lstrip()


def ensure_dedsec_os_files():
    os.makedirs(DEDSEC_OS_ROOT, exist_ok=True)
    os.makedirs(DEDSEC_OS_RUNTIME_DIR, exist_ok=True)
    if not os.path.exists(DEDSEC_OS_CONFIG_PATH):
        with open(DEDSEC_OS_CONFIG_PATH, 'w', encoding='utf-8') as handle:
            json.dump({'display_name': get_user(), 'wallpaper': '', 'wallpaper_name': '', 'terminal_theme': 'dedsec', 'login_enabled': False, 'password_hash': '', 'totp_enabled': False, 'totp_secret': '', 'security_questions': []}, handle, indent=4, ensure_ascii=False)
    server_source = dedsec_os_server_source()
    with open(DEDSEC_OS_SERVER_PATH, 'w', encoding='utf-8') as handle:
        handle.write(server_source)
    os.chmod(DEDSEC_OS_SERVER_PATH, 0o700)
    return DEDSEC_OS_SERVER_PATH


def find_free_local_port(start_port=DEDSEC_OS_DEFAULT_PORT, end_port=18949):
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if sock.connect_ex(('127.0.0.1', port)) != 0:
                return port
    raise RuntimeError('No free local port available for DedSec OS.')


def is_port_listening(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(('127.0.0.1', port)) == 0


def open_local_url(url):
    commands = []
    if shutil.which('termux-open-url'):
        commands.append(['termux-open-url', url])
    if shutil.which('am') or os.path.exists('/system/bin/am'):
        am_bin = shutil.which('am') or '/system/bin/am'
        commands.append([am_bin, 'start', '--user', '0', '-a', 'android.intent.action.VIEW', '-d', url])
    if shutil.which('xdg-open'):
        commands.append(['xdg-open', url])
    for command in commands:
        try:
            result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8)
            if result.returncode == 0:
                return True
        except Exception:
            continue
    return False


def launch_dedsec_os():
    print('[+] Launching DedSec OS...')
    server_path = ensure_dedsec_os_files()
    current_hash = hashlib.sha256(open(server_path, 'rb').read()).hexdigest()

    existing_state = {}
    if os.path.exists(DEDSEC_OS_STATE_PATH):
        try:
            with open(DEDSEC_OS_STATE_PATH, 'r', encoding='utf-8') as handle:
                existing_state = json.load(handle)
        except Exception:
            existing_state = {}

    existing_pid = int(existing_state.get('pid', 0) or 0)
    existing_port = int(existing_state.get('port', 0) or 0)
    existing_hash = existing_state.get('server_hash')

    if existing_pid and existing_port and is_port_listening(existing_port) and existing_hash == current_hash:
        url = 'http://127.0.0.1:' + str(existing_port)
        browser_url = url + '/?v=' + str(int(time.time()))
        print('[+] DedSec OS server already running at: ' + url)
        open_local_url(browser_url)
        print('[+] Termux remains locked until login in the web interface or a menu style change unlocks it.')
        for _ in range(60 * 60 * 8):
            if os.path.exists(DEDSEC_OS_UNLOCK_FLAG_PATH):
                try:
                    os.remove(DEDSEC_OS_UNLOCK_FLAG_PATH)
                except Exception:
                    pass
                break
            time.sleep(1)
        return url

    if existing_pid:
        try:
            os.kill(existing_pid, 15)
            time.sleep(0.5)
        except Exception:
            pass

    port = find_free_local_port()
    server_log_handle = open(DEDSEC_OS_LOG_PATH, 'a', encoding='utf-8')
    process = subprocess.Popen(
        ['python3', server_path, str(port)],
        cwd=DEDSEC_OS_ROOT,
        stdout=server_log_handle,
        stderr=server_log_handle,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )
    server_log_handle.close()
    with open(DEDSEC_OS_PID_PATH, 'w', encoding='utf-8') as handle:
        handle.write(str(process.pid))
    with open(DEDSEC_OS_STATE_PATH, 'w', encoding='utf-8') as handle:
        json.dump({'pid': process.pid, 'port': port, 'server_hash': current_hash}, handle)
    url = 'http://127.0.0.1:' + str(port)
    started = False
    for _ in range(40):
        if process.poll() is not None:
            break
        if is_port_listening(port):
            started = True
            break
        time.sleep(0.15)
    if not started:
        raise RuntimeError('DedSec OS local server failed to start. Check ' + DEDSEC_OS_LOG_PATH)
    if os.path.exists(DEDSEC_OS_UNLOCK_FLAG_PATH):
        try:
            os.remove(DEDSEC_OS_UNLOCK_FLAG_PATH)
        except Exception:
            pass
    browser_url = url + '/?v=' + str(int(time.time()))
    browser_opened = open_local_url(browser_url)
    print('[+] DedSec OS server running at: ' + url)
    if not browser_opened:
        print('[+] Open this URL in your browser: ' + browser_url)
    print('[+] Termux remains locked until login in the web interface or a menu style change unlocks it.')
    for _ in range(60 * 60 * 8):
        if os.path.exists(DEDSEC_OS_UNLOCK_FLAG_PATH):
            try:
                os.remove(DEDSEC_OS_UNLOCK_FLAG_PATH)
            except Exception:
                pass
            break
        if process.poll() is not None:
            break
        time.sleep(1)
    return url


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
            _("DedSec Project Update (Source 1)"),
            _("DedSec Project Update (Source 2)"),
            _("Update Packages & Modules"),
            _("Save DedSec Project"),
            _("Change Prompt"),
            _("Change Menu Style"),
            get_menu_autostart_label(),
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
        _("DedSec Project Update (Source 1)"),
        _("DedSec Project Update (Source 2)"),
        _("Update Packages & Modules"),
        _("Save DedSec Project"),
        _("Change Prompt"),
        _("Change Menu Style"),
        get_menu_autostart_label(),
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
        _("DedSec Project Update (Source 1)"),
        _("DedSec Project Update (Source 2)"),
        _("Update Packages & Modules"),
        _("Save DedSec Project"),
        _("Change Prompt"),
        _("Change Menu Style"),
        get_menu_autostart_label(),
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
            return len(menu_options) - 1  # Exit option
        
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
        should_exit = False
        pause_without_text = False

        selected = run_settings_menu()
        if selected is None:
            print(_("Exiting..."))
            break

        os.system("clear")
        if selected == 0:
            show_about()
        elif selected == 1:
            update_dedsec_source_1()
        elif selected == 2:
            update_dedsec_source_2()
        elif selected == 3:
            update_packages_modules()
        elif selected == 4:
            save_project()
            pause_without_text = True
        elif selected == 5:
            change_prompt()
        elif selected == 6:
            change_menu_style()
        elif selected == 7:
            toggle_menu_autostart()
        elif selected == 8:
            change_language()
        elif selected == 9:
            show_credits()
        elif selected == 10:
            should_exit = uninstall_dedsec()
            if should_exit:
                break
        elif selected == 11:
            print(_("Exiting..."))
            break

        if not should_exit:
            if pause_without_text:
                input()
            else:
                input(f"\n{_('Press Enter to return to the settings menu...')}")

# ------------------------------
# Entry Point
# ------------------------------
if __name__ == "__main__":
    try:
        # Load language preference at startup
        get_current_display_language()
        
        # --- NEW: Enforce Language Folder Visibility ---
        enforce_language_folder_visibility()
        
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
                elif current_style == "dedsec_os":
                    launch_dedsec_os()
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
                elif current_style == 'dedsec_os':
                    launch_dedsec_os()
                else:
                    run_list_menu()  # Default fallback
        else:
            main()
    except KeyboardInterrupt:
        print(_("\nScript terminated by KeyboardInterrupt. Exiting gracefully..."))
        sys.exit(0)