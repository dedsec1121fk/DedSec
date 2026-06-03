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
import atexit

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
GITHUB_ACCOUNT_CONFIG_PATH = os.path.join(HOME_DIR, ".dedsec_github_account.json")
TERMUX_USAGE_STATS_PATH = os.path.join(HOME_DIR, ".dedsec_termux_usage_stats.json")
TERMUX_USAGE_SCAN_ROOT = HOME_DIR
SETTINGS_SESSION_START = time.time()
ACHIEVEMENTS_STATE_PATH = os.path.join(HOME_DIR, ".dedsec_achievements.json")
ACHIEVEMENTS_PID_PATH = os.path.join(HOME_DIR, ".dedsec_achievements.pid")
ACHIEVEMENTS_WATCHDOG_PID_PATH = os.path.join(HOME_DIR, ".dedsec_achievements_watchdog.pid")
ACHIEVEMENTS_ENSURE_LOCK_PATH = os.path.join(HOME_DIR, ".dedsec_achievements_ensure.lock")
ACHIEVEMENTS_LOG_PATH = os.path.join(HOME_DIR, ".dedsec_achievements.log")
ACHIEVEMENTS_NOTIFICATION_MAX_INDIVIDUAL = 5
ACHIEVEMENTS_NOTIFICATION_ID_BASE = 112100
ACHIEVEMENTS_SCAN_INTERVAL_SECONDS = 60
ACHIEVEMENTS_WATCHDOG_INTERVAL_SECONDS = 15
ACHIEVEMENTS_PROMPT_GUARD_INTERVAL_SECONDS = 30
ACHIEVEMENTS_STALE_DAEMON_SECONDS = 300
ACHIEVEMENTS_STALE_WATCHDOG_SECONDS = 120
ACHIEVEMENTS_FILE_SCAN_LIMIT = 5000
ACHIEVEMENTS_BASHRC_START_MARKER = "# --- DedSec Achievements Background Checker (Set by Settings.py) ---"
ACHIEVEMENTS_BASHRC_END_MARKER = "# --- End DedSec Achievements Background Checker ---"
ACHIEVEMENTS_TROPHY_TIERS = ("beginner", "easy", "normal", "hard", "very_hard", "godlike")
ACHIEVEMENTS_TROPHY_TIER_LABELS = {
    "beginner": "Beginner",
    "easy": "Easy",
    "normal": "Normal",
    "hard": "Hard",
    "very_hard": "Very Hard",
    "godlike": "Godlike",
}
ACHIEVEMENTS_TROPHY_TIER_SHORT = {
    "beginner": "B",
    "easy": "E",
    "normal": "N",
    "hard": "H",
    "very_hard": "VH",
    "godlike": "GOD",
}
ACHIEVEMENTS_TROPHY_TIER_POINTS = {
    "beginner": 5,
    "easy": 10,
    "normal": 20,
    "hard": 35,
    "very_hard": 60,
    "godlike": 100,
}

# Dedicated notification/test trophies. These let users verify that each
# difficulty rank unlocks and sends Termux:API notifications correctly.
# Future updates must not remove or rename these IDs/events, because they are
# saved forever in ~/.dedsec_achievements.json after they unlock.
ACHIEVEMENTS_TEST_TROPHIES = [
    {"number": "1", "difficulty": "beginner", "event": "test_trophy_beginner", "id": "test_1_beginner_trophy", "title": "Test 1 Achievement", "description": "Run Test 1 in Termux to verify Beginner trophy notifications.", "aliases": ("1", "beginner", "begginer", "b")},
    {"number": "2", "difficulty": "easy", "event": "test_trophy_easy", "id": "test_2_easy_trophy", "title": "Test 2 Achievement", "description": "Run Test 2 in Termux to verify Easy trophy notifications.", "aliases": ("2", "easy", "e")},
    {"number": "3", "difficulty": "normal", "event": "test_trophy_normal", "id": "test_3_normal_trophy", "title": "Test 3 Achievement", "description": "Run Test 3 in Termux to verify Normal trophy notifications.", "aliases": ("3", "normal", "n")},
    {"number": "4", "difficulty": "hard", "event": "test_trophy_hard", "id": "test_4_hard_trophy", "title": "Test 4 Achievement", "description": "Run Test 4 in Termux to verify Hard trophy notifications.", "aliases": ("4", "hard", "h")},
    {"number": "5", "difficulty": "very_hard", "event": "test_trophy_very_hard", "id": "test_5_very_hard_trophy", "title": "Test 5 Achievement", "description": "Run Test 5 in Termux to verify Very Hard trophy notifications.", "aliases": ("5", "veryhard", "very_hard", "very-hard", "very", "vh")},
    {"number": "6", "difficulty": "godlike", "event": "test_trophy_godlike", "id": "test_6_godlike_trophy", "title": "Test 6 Achievement", "description": "Run Test 6 in Termux to verify Godlike trophy notifications.", "aliases": ("6", "godlike", "god", "g")},
]

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

# --- VPN / Tor Utilities (taken from Free Internet.py and adapted for Settings.py) ---
NETWORK_CONFIG_PATH = os.path.join(HOME_DIR, ".dedsec_network_utilities.json")
NETWORK_DATA_DIR = os.path.join(HOME_DIR, ".dedsec_network_utilities")
NETWORK_PROXY_CACHE_FILE = os.path.join(NETWORK_DATA_DIR, "proxy_cache.json")
NETWORK_PROXY_STATE_FILE = os.path.join(NETWORK_DATA_DIR, "proxy_state.json")
NETWORK_TOR_LOG_PATH = os.path.join(NETWORK_DATA_DIR, "tor.log")
NETWORK_TOR_DATA_DIR = os.path.join(NETWORK_DATA_DIR, "tor_data")
NETWORK_PROXY_API = "https://api.proxyscrape.com/v3/free-proxy-list/get"
NETWORK_PROXY_CACHE_TTL = 240
NETWORK_BAD_PROXY_TTL = 1800
NETWORK_MIN_PROXY_POOL = 10
NETWORK_MAX_PROXY_TESTS = 10
NETWORK_TOR_SOCKS_PORT = 9050
NETWORK_BASHRC_START_MARKER = "# --- DedSec VPN and Tor Utilities (Set by Settings.py) ---"
NETWORK_BASHRC_END_MARKER = "# --- End DedSec VPN and Tor Utilities ---"
NETWORK_SESSION_GUARD_INTERVAL_SECONDS = 30
NETWORK_SESSION_GUARD_COMMAND = "--network-session-guard"
NETWORK_COUNTRIES = {
    "US": "United States",
    "DE": "Germany",
    "GB": "United Kingdom",
    "FR": "France",
    "NL": "Netherlands",
    "JP": "Japan",
    "IN": "India",
    "BR": "Brazil",
    "AU": "Australia",
    "GR": "Greece",
    "CA": "Canada",
    "SE": "Sweden",
    "CH": "Switzerland",
    "IT": "Italy",
    "ES": "Spain",
}
NETWORK_TOR_PROCESS = None

# --- Sponsors-Only shortcuts ---
SPONSORS_TIERS = {
    "3": {
        "key": "3",
        "label": "Sponsors-Only $3 Tier",
        "short_label": "$3 Tier",
        "repo_full_name": "DedSec-Project-Official/Sponsors-Only-3",
        "repo_url": "https://github.com/DedSec-Project-Official/Sponsors-Only-3",
        "git_url": "https://github.com/DedSec-Project-Official/Sponsors-Only-3.git",
        "root_name": "Sponsors-Only-3",
        "old_root_names": ["Sponsors-Only-3-main", "Sponsors-Only-main", "Sponsors-Only"],
    },
    "9": {
        "key": "9",
        "label": "Sponsors-Only $9 Tier",
        "short_label": "$9 Tier",
        "repo_full_name": "DedSec-Project-Official/Sponsors-Only-9",
        "repo_url": "https://github.com/DedSec-Project-Official/Sponsors-Only-9",
        "git_url": "https://github.com/DedSec-Project-Official/Sponsors-Only-9.git",
        "root_name": "Sponsors-Only-9",
        "old_root_names": ["Sponsors-Only-9-main"],
    },
}
SPONSORS_TIER_ORDER = ("3", "9")
# Backwards-compatible aliases for older code paths. The default points to the $3 tier.
SPONSORS_REPO_FULL_NAME = SPONSORS_TIERS["3"]["repo_full_name"]
SPONSORS_REPO_URL = SPONSORS_TIERS["3"]["repo_url"]
SPONSORS_REPO_GIT_URL = SPONSORS_TIERS["3"]["git_url"]
SPONSORS_ROOT_NAME = SPONSORS_TIERS["3"]["root_name"]
SPONSORS_OLD_ROOT_NAMES = SPONSORS_TIERS["3"]["old_root_names"]
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
    "Access Sponsors-Only Scripts": "Πρόσβαση στα Sponsors-Only Scripts",
    "Checking Sponsors-Only access...": "Έλεγχος πρόσβασης στα Sponsors-Only...",
    "GitHub is not connected yet. Connect GitHub now? (y/n): ": "Το GitHub δεν είναι συνδεδεμένο ακόμα. Σύνδεση τώρα; (y/n): ",
    "GitHub connection is required for Sponsors-Only scripts.": "Απαιτείται σύνδεση GitHub για τα Sponsors-Only scripts.",
    "Sponsors-Only access confirmed.": "Η πρόσβαση στα Sponsors-Only επιβεβαιώθηκε.",
    "You do not have access to the Sponsors-Only repository yet.": "Δεν έχετε ακόμα πρόσβαση στο Sponsors-Only repository.",
    "Make sure you are sponsoring with the connected GitHub account.": "Βεβαιωθείτε ότι είστε sponsor με τον συνδεδεμένο GitHub λογαριασμό.",
    "Choose Sponsors-Only tier": "Επιλέξτε Sponsors-Only tier",
    "Download Sponsors-Only $3 Tier": "Λήψη Sponsors-Only $3 Tier",
    "Download Sponsors-Only $9 Tier": "Λήψη Sponsors-Only $9 Tier",
    "Check access to both sponsor tiers": "Έλεγχος πρόσβασης και στα δύο sponsor tiers",
    "Checking Sponsors-Only access for": "Έλεγχος πρόσβασης Sponsors-Only για",
    "Access available": "Η πρόσβαση είναι διαθέσιμη",
    "Access denied": "Η πρόσβαση απορρίφθηκε",
    "Invalid sponsor tier.": "Μη έγκυρο sponsor tier.",
    "Downloading Sponsors-Only scripts...": "Λήψη των Sponsors-Only scripts...",
    "Sponsors-Only scripts downloaded to": "Τα Sponsors-Only scripts κατέβηκαν στο",
    "Failed to download Sponsors-Only scripts": "Αποτυχία λήψης των Sponsors-Only scripts",
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
    "Achievements": "Επιτεύγματα",
    "Trophy rank": "Βαθμός τροπαίου",
    "Trophy points": "Πόντοι τροπαίου",
    "Beginner": "Αρχάριο",
    "Easy": "Εύκολο",
    "Normal": "Κανονικό",
    "Hard": "Δύσκολο",
    "Very Hard": "Πολύ Δύσκολο",
    "Godlike": "Θεϊκό",
    "Beginner Trophies": "Αρχάρια Τρόπαια",
    "Easy Trophies": "Εύκολα Τρόπαια",
    "Normal Trophies": "Κανονικά Τρόπαια",
    "Hard Trophies": "Δύσκολα Τρόπαια",
    "Very Hard Trophies": "Πολύ Δύσκολα Τρόπαια",
    "Godlike Trophies": "Θεϊκά Τρόπαια",
    "Trophy Difficulty Map": "Χάρτης Δυσκολίας Τροπαίων",
    "Unlock 10 Beginner trophies.": "Ξεκλείδωσε 10 αρχάρια τρόπαια.",
    "Unlock 15 Easy trophies.": "Ξεκλείδωσε 15 εύκολα τρόπαια.",
    "Unlock 20 Normal trophies.": "Ξεκλείδωσε 20 κανονικά τρόπαια.",
    "Unlock 15 Hard trophies.": "Ξεκλείδωσε 15 δύσκολα τρόπαια.",
    "Unlock 10 Very Hard trophies.": "Ξεκλείδωσε 10 πολύ δύσκολα τρόπαια.",
    "Unlock 5 Godlike trophies.": "Ξεκλείδωσε 5 θεϊκά τρόπαια.",
    "Trophy score": "Σκορ τροπαίων",
    "Difficulty summary": "Σύνοψη δυσκολίας",
    "Achievement unlocked": "Επίτευγμα ξεκλειδώθηκε",
    "Achievements menu opened": "Άνοιξε το μενού επιτευγμάτων",
    "Hidden Achievement": "Κρυφό Επίτευγμα",
    "Keep using DedSec Project to reveal this.": "Συνέχισε να χρησιμοποιείς το DedSec Project για να αποκαλυφθεί.",
    "Background checker": "Έλεγχος στο παρασκήνιο",
    "Enabled": "Ενεργό",
    "Disabled": "Ανενεργό",
    "Unlocked": "Ξεκλειδωμένο",
    "Locked": "Κλειδωμένο",
    "Hidden": "Κρυφό",
    "Progress": "Πρόοδος",
    "Check achievements now": "Έλεγχος επιτευγμάτων τώρα",
    "Restart constant checker": "Επανεκκίνηση μόνιμου ελέγχου",
    "Constant checker repaired.": "Ο μόνιμος έλεγχος επισκευάστηκε.",
    "Forced ON": "Υποχρεωτικά ενεργό",
    "Disable background checker": "Απενεργοποίηση ελέγχου παρασκηνίου",
    "Enable background checker": "Ενεργοποίηση ελέγχου παρασκηνίου",
    "Show achievement log": "Προβολή ιστορικού επιτευγμάτων",
    "No achievement log yet.": "Δεν υπάρχει ακόμα ιστορικό επιτευγμάτων.",
    "Achievements checked.": "Τα επιτεύγματα ελέγχθηκαν.",
    "Background achievement checker enabled.": "Ο έλεγχος επιτευγμάτων στο παρασκήνιο ενεργοποιήθηκε.",
    "Background achievement checker disabled.": "Ο έλεγχος επιτευγμάτων στο παρασκήνιο απενεργοποιήθηκε.",
    "Daemon status": "Κατάσταση daemon",
    "Watchdog status": "Κατάσταση watchdog",
    "Termux:API notification support": "Υποστήριξη ειδοποιήσεων Termux:API",
    "Achievement notifications": "Ειδοποιήσεις επιτευγμάτων",
    "Notifications sent": "Ειδοποιήσεις που στάλθηκαν",
    "Supported": "Υποστηρίζεται",
    "Not available": "Μη διαθέσιμο",
    "Unlocked achievements": "Ξεκλειδωμένα επιτεύγματα",
    "new achievements unlocked": "νέα επιτεύγματα ξεκλειδώθηκαν",
    "Tap or return to Termux to view your trophies.": "Πάτησε ή γύρνα στο Termux για να δεις τα τρόπαιά σου.",
    "Install Termux:API and the termux-api package to receive unlock notifications.": "Εγκατέστησε το Termux:API και το πακέτο termux-api για να λαμβάνεις ειδοποιήσεις ξεκλειδώματος.",
    "Running": "Τρέχει",
    "Stopped": "Σταματημένο",
    "Guardian Process": "Διαδικασία Φύλακας",
    "Keep the watchdog alive so achievements restart if the checker crashes.": "Κράτα ζωντανό το watchdog ώστε τα επιτεύγματα να επανεκκινούν αν ο έλεγχος πέσει.",
    "Unbreakable Watch": "Άσπαστη Παρακολούθηση",
    "Let the watchdog recover or verify the checker 25 times while Termux is open.": "Άφησε το watchdog να επαναφέρει ή να επιβεβαιώσει τον έλεγχο 25 φορές όσο το Termux είναι ανοιχτό.",
    "Still Watching": "Ακόμα Παρακολουθεί",
    "Let the watchdog recover or verify the checker 100 times while Termux is open.": "Άφησε το watchdog να επαναφέρει ή να επιβεβαιώσει τον έλεγχο 100 φορές όσο το Termux είναι ανοιχτό.",
    "Self-Healing Engine": "Αυτοθεραπευόμενος Μηχανισμός",
    "Have the watchdog restart the checker after a crash or manual kill.": "Κάνε το watchdog να ξαναξεκινήσει τον έλεγχο μετά από crash ή χειροκίνητο κλείσιμο.",
    "Watcher Marathon": "Μαραθώνιος Παρακολούθησης",
    "Keep the achievement watchdog alive for 500 pulses.": "Κράτα ζωντανό το achievement watchdog για 500 παλμούς.",
    "Trophy Ping": "Ήχος Τροπαίου",
    "Receive your first Termux notification for an unlocked achievement.": "Λάβε την πρώτη σου ειδοποίηση Termux για ξεκλειδωμένο επίτευγμα.",
    "Notification Chain": "Αλυσίδα Ειδοποιήσεων",
    "Receive 10 achievement unlock notifications through Termux:API.": "Λάβε 10 ειδοποιήσεις ξεκλειδώματος επιτευγμάτων μέσω Termux:API.",
    "Trophy Broadcast": "Εκπομπή Τροπαίων",
    "Receive 50 achievement unlock notifications through Termux:API.": "Λάβε 50 ειδοποιήσεις ξεκλειδώματος επιτευγμάτων μέσω Termux:API.",
    "Achievement Test Commands": "Εντολές Δοκιμής Επιτευγμάτων",
    "Run these in Termux to test each difficulty notification:": "Τρέξε αυτά στο Termux για να δοκιμάσεις κάθε ειδοποίηση δυσκολίας:",
    "Difficulty": "Δυσκολία",
    "Achievement already unlocked": "Το επίτευγμα έχει ήδη ξεκλειδωθεί",
    "Achievement test notification sent.": "Η δοκιμαστική ειδοποίηση επιτεύγματος στάλθηκε.",
    "Achievement test notification could not be sent. Install Termux:API and pkg install termux-api.": "Η δοκιμαστική ειδοποίηση επιτεύγματος δεν μπόρεσε να σταλεί. Εγκατέστησε το Termux:API και κάνε pkg install termux-api.",
    "Unknown achievement test. Use Test 1 to Test 6.": "Άγνωστη δοκιμή επιτεύγματος. Χρησιμοποίησε Test 1 έως Test 6.",
    "Test 1 Achievement": "Επίτευγμα Test 1",
    "Test 2 Achievement": "Επίτευγμα Test 2",
    "Test 3 Achievement": "Επίτευγμα Test 3",
    "Test 4 Achievement": "Επίτευγμα Test 4",
    "Test 5 Achievement": "Επίτευγμα Test 5",
    "Test 6 Achievement": "Επίτευγμα Test 6",
    "Run Test 1 in Termux to verify Beginner trophy notifications.": "Τρέξε Test 1 στο Termux για να δοκιμάσεις τις ειδοποιήσεις τροπαίου Beginner.",
    "Run Test 2 in Termux to verify Easy trophy notifications.": "Τρέξε Test 2 στο Termux για να δοκιμάσεις τις ειδοποιήσεις τροπαίου Easy.",
    "Run Test 3 in Termux to verify Normal trophy notifications.": "Τρέξε Test 3 στο Termux για να δοκιμάσεις τις ειδοποιήσεις τροπαίου Normal.",
    "Run Test 4 in Termux to verify Hard trophy notifications.": "Τρέξε Test 4 στο Termux για να δοκιμάσεις τις ειδοποιήσεις τροπαίου Hard.",
    "Run Test 5 in Termux to verify Very Hard trophy notifications.": "Τρέξε Test 5 στο Termux για να δοκιμάσεις τις ειδοποιήσεις τροπαίου Very Hard.",
    "Run Test 6 in Termux to verify Godlike trophy notifications.": "Τρέξε Test 6 στο Termux για να δοκιμάσεις τις ειδοποιήσεις τροπαίου Godlike.",
    "First Launch": "Πρώτη Εκκίνηση",
    "Open Settings.py and start the DedSec control center.": "Άνοιξε το Settings.py και ξεκίνα το κέντρο ελέγχου του DedSec.",
    "Trophy Room": "Δωμάτιο Τροπαίων",
    "Open the Achievements menu for the first time.": "Άνοιξε το μενού Επιτευγμάτων για πρώτη φορά.",
    "Style Shifter": "Αλλαγή Στυλ",
    "Change the menu style from the default list view.": "Άλλαξε το στυλ μενού από την προεπιλεγμένη λίστα.",
    "Greek Signal": "Ελληνικό Σήμα",
    "Switch the DedSec Project language to Greek.": "Άλλαξε τη γλώσσα του DedSec Project στα Ελληνικά.",
    "GitHub Link": "Σύνδεση GitHub",
    "Connect a GitHub account inside Settings.py.": "Σύνδεσε έναν GitHub λογαριασμό μέσα από το Settings.py.",
    "Stats Online": "Στατιστικά Online",
    "Run the Termux Usage Stats scanner at least once.": "Τρέξε τον σαρωτή στατιστικών χρήσης Termux τουλάχιστον μία φορά.",
    "Script Builder": "Χτίστης Scripts",
    "Keep at least 10 Python scripts inside the DedSec workspace.": "Κράτα τουλάχιστον 10 Python scripts μέσα στον χώρο εργασίας DedSec.",
    "Legacy Keeper": "Φύλακας Legacy",
    "Create a DedSec Project Legacy save archive in Downloads.": "Δημιούργησε ένα DedSec Project Legacy save archive στα Downloads.",
    "Sponsor Gate": "Πύλη Sponsor",
    "Have a Sponsors-Only folder available locally.": "Έχε διαθέσιμο τοπικά έναν φάκελο Sponsors-Only.",
    "Ghost Network": "Δίκτυο Φάντασμα",
    "Enable VPN or Tor utilities from Settings.py.": "Ενεργοποίησε τα VPN ή Tor εργαλεία από το Settings.py.",
    "Command Veteran": "Βετεράνος Εντολών",
    "Reach 100 commands in Termux history or tracked stats.": "Φτάσε 100 εντολές στο ιστορικό Termux ή στα καταγεγραμμένα στατιστικά.",
    "Seven Boots": "Επτά Εκκινήσεις",
    "Open Settings.py seven different times.": "Άνοιξε το Settings.py επτά διαφορετικές φορές.",
    "Bilingual Operator": "Δίγλωσσος Operator",
    "Use both English and Greek language modes.": "Χρησιμοποίησε και την Αγγλική και την Ελληνική λειτουργία γλώσσας.",
    "Script Collector": "Συλλέκτης Scripts",
    "Keep 25 runnable scripts in the DedSec workspace.": "Κράτα 25 εκτελέσιμα scripts στον χώρο εργασίας DedSec.",
    "Night Operator": "Νυχτερινός Operator",
    "Use DedSec Project between midnight and 5 AM.": "Χρησιμοποίησε το DedSec Project μεταξύ μεσάνυχτα και 5 π.μ.",
    "OS Pilot": "Πιλότος OS",
    "Select DedSec OS as the menu style.": "Επίλεξε το DedSec OS ως στυλ μενού.",
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
    "GitHub Account": "Λογαριασμός GitHub",
    "Termux Usage Stats": "Στατιστικά Χρήσης Termux",
    "VPN & Tor Utilities": "Εργαλεία VPN & Tor",
    "Network Utilities": "Εργαλεία Δικτύου",
    "Tor Connection": "Σύνδεση Tor",
    "VPN Connection": "Σύνδεση VPN",
    "Enable Tor Connection": "Ενεργοποίηση Σύνδεσης Tor",
    "Disable Tor Connection": "Απενεργοποίηση Σύνδεσης Tor",
    "Enable VPN Connection": "Ενεργοποίηση Σύνδεσης VPN",
    "Disable VPN Connection": "Απενεργοποίηση Σύνδεσης VPN",
    "Choose VPN Location": "Επιλογή Τοποθεσίας VPN",
    "Renew VPN Proxies": "Ανανέωση VPN Proxies",
    "Update VPN/Tor Tools": "Ενημέρωση Εργαλείων VPN/Tor",
    "Show VPN/Tor Status": "Εμφάνιση Κατάστασης VPN/Tor",
    "Enabled": "Ενεργό",
    "Disabled": "Ανενεργό",
    "Running": "Τρέχει",
    "Stopped": "Σταματημένο",
    "Country": "Χώρα",
    "Current proxy": "Τρέχον proxy",
    "No proxy selected": "Δεν έχει επιλεγεί proxy",
    "New sessions": "Νέες συνεδρίες",
    "Covered by bash.bashrc hook": "Καλύπτονται από hook στο bash.bashrc",
    "Network exports updated. Restart Termux or open a new shell to apply them everywhere.": "Οι ρυθμίσεις δικτύου ενημερώθηκαν. Κάντε επανεκκίνηση του Termux ή ανοίξτε νέο shell για να εφαρμοστούν παντού.",
    "Tor support ready.": "Η υποστήριξη Tor είναι έτοιμη.",
    "Tor started on 127.0.0.1:9050.": "Το Tor ξεκίνησε στο 127.0.0.1:9050.",
    "Tor is already running.": "Το Tor ήδη τρέχει.",
    "Tor stopped.": "Το Tor σταμάτησε.",
    "Tor was not started by this app.": "Το Tor δεν ξεκίνησε από αυτή την εφαρμογή.",
    "VPN proxy ready": "Το VPN proxy είναι έτοιμο",
    "Saved VPN proxy reused without retesting.": "Το αποθηκευμένο VPN proxy χρησιμοποιήθηκε ξανά χωρίς νέο τεστ.",
    "Saved proxy was previously marked as bad. Searching for a new one.": "Το αποθηκευμένο proxy είχε σημειωθεί ως προβληματικό. Αναζήτηση νέου.",
    "VPN is disabled. Proxies were refreshed but no proxy was activated.": "Το VPN είναι ανενεργό. Τα proxies ανανεώθηκαν αλλά δεν ενεργοποιήθηκε κανένα proxy.",
    "No working proxy found for this country right now. Try renew or choose another location.": "Δεν βρέθηκε λειτουργικό proxy για αυτή τη χώρα τώρα. Δοκιμάστε ανανέωση ή επιλέξτε άλλη τοποθεσία.",
    "Selected VPN location": "Επιλεγμένη τοποθεσία VPN",
    "Network tools checked.": "Τα εργαλεία δικτύου ελέγχθηκαν.",
    "Connect GitHub Account": "Σύνδεση Λογαριασμού GitHub",
    "Disconnect GitHub Account": "Αποσύνδεση Λογαριασμού GitHub",
    "Show GitHub Stats": "Εμφάνιση Στατιστικών GitHub",
    "GitHub account connected": "Ο λογαριασμός GitHub συνδέθηκε",
    "GitHub account disconnected": "Ο λογαριασμός GitHub αποσυνδέθηκε",
    "GitHub is not connected yet.": "Το GitHub δεν έχει συνδεθεί ακόμα.",
    "GitHub username": "Όνομα χρήστη GitHub",
    "Total stars": "Σύνολο αστεριών",
    "Total forks": "Σύνολο forks",
    "Total watchers": "Σύνολο watchers",
    "Total commits": "Σύνολο commits",
    "Rank": "Κατάταξη",
    "Repositories counted": "Αποθετήρια που μετρήθηκαν",
    "Prompt automatically updated to GitHub username.": "Το prompt ενημερώθηκε αυτόματα στο όνομα χρήστη GitHub.",
    "Back": "Πίσω",
    "Connected as": "Συνδεδεμένος ως",
    "Not connected": "Μη συνδεδεμένο",
    "Tracking since": "Παρακολούθηση από",
    "Tracked time": "Χρόνος παρακολούθησης",
    "Settings runtime tracked": "Χρόνος χρήσης Settings που καταγράφηκε",
    "Files scanned": "Αρχεία που σαρώθηκαν",
    "Files created": "Αρχεία που δημιουργήθηκαν",
    "Files edited": "Αρχεία που επεξεργάστηκαν",
    "Files deleted": "Αρχεία που διαγράφηκαν",
    "Latest created": "Τελευταία δημιουργημένα",
    "Latest edited": "Τελευταία επεξεργασμένα",
    "Latest deleted": "Τελευταία διαγραμμένα",
    "Programming languages used": "Γλώσσες προγραμματισμού που χρησιμοποιήθηκαν",
    "Shell commands found": "Εντολές shell που βρέθηκαν",
    "Most active folders": "Πιο ενεργοί φάκελοι",
    "First scan created. Run this again later to detect created/edited/deleted files.": "Δημιουργήθηκε η πρώτη σάρωση. Τρέξτε το ξανά αργότερα για εντοπισμό δημιουργημένων/επεξεργασμένων/διαγραμμένων αρχείων.",
    "Press Enter to continue...": "Πατήστε Enter για συνέχεια...",    "Update process completed successfully": "Η διαδικασία ενημέρωσης ολοκληρώθηκε με επιτυχία",
    "Forcing a full update...": "Επιβολή πλήρους ενημέρωσης...",
    "Customizations applied successfully! ": "Οι προσαρμογές εφαρμόστηκαν με επιτυχία! ",
    "Please restart Termux for changes to take full effect": "Παρακαλώ επανεκκινήστε το Termux για να εφαρμοστούν πλήρως οι αλλαγές",
    "Invalid selection or non-executable script.": "Μη έγκυρη επιλογή ή μη εκτελέσιμο script.",
    "Terminal window is too small.": "Το παράθυρο του τερματικού είναι πολύ μικρό.",
    "Unknown": "Άγνωστο",
    "\nScript terminated by KeyboardInterrupt. Exiting gracefully...": "\nΤο script τερματίστηκε λόγω KeyboardInterrupt. Έξοδος με ασφάλεια...",

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


def safe_curses_addstr(stdscr, y, x, text, attr=0):
    """Draws curses text safely on small/mobile terminal sizes."""
    try:
        height, width = stdscr.getmaxyx()
        if y < 0 or y >= height or width <= 0:
            return
        x = max(0, x)
        if x >= width:
            return
        safe_text = str(text)[:max(0, width - x - 1)]
        if not safe_text:
            return
        if attr:
            stdscr.addstr(y, x, safe_text, attr)
        else:
            stdscr.addstr(y, x, safe_text)
    except Exception:
        pass

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

def get_sponsor_tier_config(tier_key):
    """Returns the sponsor tier configuration for 3 or 9."""
    tier_key = str(tier_key or "").replace("$", "").strip()
    return SPONSORS_TIERS.get(tier_key)


def get_sponsors_tier_root_path(tier_key):
    """Returns the Termux home folder path for a sponsor tier."""
    config = get_sponsor_tier_config(tier_key)
    if not config:
        return None
    return os.path.join(HOME_DIR, config["root_name"])


def get_sponsors_display_entries():
    """Returns visible Sponsors-Only folders as menu entries."""
    entries = []
    for tier_key in SPONSORS_TIER_ORDER:
        config = get_sponsor_tier_config(tier_key)
        root_path = get_sponsors_tier_root_path(tier_key)
        if config and root_path and os.path.isdir(root_path):
            entries.append((format_display_name(config["root_name"], root_path), f"go_sponsors:{tier_key}"))
    return entries


def get_sponsors_display_name():
    """Backwards-compatible single Sponsors-Only label for older code paths."""
    entries = get_sponsors_display_entries()
    return entries[0][0] if entries else None


def get_sponsors_go_token_for_display_name(display_name):
    """Maps a visible Sponsors-Only menu label back to its tier navigation token."""
    for label, go_token in get_sponsors_display_entries():
        if display_name == label:
            return go_token
    return None


def get_sponsors_existing_root_paths():
    """Returns all downloaded Sponsors-Only tier root folders."""
    paths = []
    for tier_key in SPONSORS_TIER_ORDER:
        root_path = get_sponsors_tier_root_path(tier_key)
        if root_path and os.path.isdir(root_path):
            paths.append(root_path)
    return paths


def get_sponsors_preferred_path(tier_key=None):
    """Returns the preferred Sponsors-Only language path, with safe fallbacks."""
    if tier_key is None:
        for candidate_tier in SPONSORS_TIER_ORDER:
            candidate_root = get_sponsors_tier_root_path(candidate_tier)
            if candidate_root and os.path.isdir(candidate_root):
                tier_key = candidate_tier
                break

    config = get_sponsor_tier_config(tier_key)
    root_path = get_sponsors_tier_root_path(tier_key)
    if not config or not root_path or not os.path.isdir(root_path):
        return None

    preferred_language = load_language_preference()
    if preferred_language not in ['english', 'greek']:
        preferred_language = get_current_display_language()

    preferred_folder = (
        SPONSORS_ENGLISH_FOLDER_NAME
        if preferred_language == 'english'
        else SPONSORS_GREEK_FOLDER_NAME
    )
    preferred_path = os.path.join(root_path, preferred_folder)
    if os.path.isdir(preferred_path):
        return preferred_path

    fallback_folder = (
        SPONSORS_GREEK_FOLDER_NAME
        if preferred_folder == SPONSORS_ENGLISH_FOLDER_NAME
        else SPONSORS_ENGLISH_FOLDER_NAME
    )
    fallback_path = os.path.join(root_path, fallback_folder)
    if os.path.isdir(fallback_path):
        return fallback_path

    return root_path

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



def _add_accessible_sponsor_repositories_to_project_save(repos_dir):
    """Checks both Sponsors-Only tiers and adds the ones the connected GitHub account can access."""
    status_lines = ["Sponsors-Only access check for DedSec Project Legacy Save:"]
    try:
        if not shutil.which("gh") or not github_auth_status():
            status_lines.append("- GitHub is not connected in gh, so sponsor repositories were not included.")
            status_path = os.path.join(repos_dir, "Sponsors-Only Access Status.txt")
            with open(status_path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(status_lines) + "\n")
            return

        if not shutil.which("git") and not ensure_pkg_command("git", "git"):
            status_lines.append("- git is not available, so sponsor repositories were not included.")
            status_path = os.path.join(repos_dir, "Sponsors-Only Access Status.txt")
            with open(status_path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(status_lines) + "\n")
            return

        token = github_token_for_sponsors()
        if not token:
            status_lines.append("- GitHub token could not be read, so sponsor repositories were not included.")
            status_path = os.path.join(repos_dir, "Sponsors-Only Access Status.txt")
            with open(status_path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(status_lines) + "\n")
            return

        for tier_key in SPONSORS_TIER_ORDER:
            config = get_sponsor_tier_config(tier_key)
            if not config:
                continue

            rc, out = run_sponsors_git_command(["ls-remote", config["git_url"], "HEAD"], token)
            target_dir = os.path.join(repos_dir, config["root_name"])
            if rc == 0:
                _remove_path_if_exists(target_dir)
                clone_rc, clone_out = run_sponsors_git_command(
                    ["clone", "--depth", "1", config["git_url"], target_dir],
                    token
                )
                if clone_rc == 0 and os.path.isdir(target_dir):
                    git_dir = os.path.join(target_dir, ".git")
                    if os.path.isdir(git_dir):
                        shutil.rmtree(git_dir, ignore_errors=True)
                    status_lines.append(f"- {config['label']}: access confirmed and repository included.")
                else:
                    _remove_path_if_exists(target_dir)
                    status_lines.append(f"- {config['label']}: access confirmed, but clone failed.")
            else:
                message = (out or "no access").strip().splitlines()[-1]
                status_lines.append(f"- {config['label']}: no access or token approval required. ({message})")

    except Exception as error:
        status_lines.append("- Sponsor access check failed: " + str(error))

    status_path = os.path.join(repos_dir, "Sponsors-Only Access Status.txt")
    try:
        with open(status_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(status_lines) + "\n")
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

    _add_accessible_sponsor_repositories_to_project_save(repos_dir)

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
Contributors: gr3ysec
Art Artists: Christina Chatzidimitriou, 3A
Legal Documents: Lampros Spyrou
Discord Server Maintenance: Talha
Past Help: Sal Scar, lamprouil, UKI_hunter
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
def sanitize_prompt_username(username):
    """Keeps the Termux prompt safe while preserving normal GitHub usernames."""
    username = (username or "").strip()
    username = re.sub(r"[^A-Za-z0-9_.@-]", "_", username)
    return username[:48] or "DedSec"


def build_dedsec_ps1(username):
    username = sanitize_prompt_username(username)
    return (
        f"PS1='\\[\\e[1;36m\\]\\D{{%d/%m/%Y}}-[\\A]-(\\[\\e[1;34m\\]{username}\\[\\e[0m\\])-(\\[\\e[1;33m\\]\\W\\[\\e[0m\\]) : '\n"
    )


def set_prompt_username(username):
    """Updates bash.bashrc PS1 without asking for input."""
    username = sanitize_prompt_username(username)
    remove_motd()
    try:
        os.makedirs(os.path.dirname(BASHRC_PATH), exist_ok=True)
        if os.path.exists(BASHRC_PATH):
            with open(BASHRC_PATH, "r") as bashrc_file:
                lines = bashrc_file.readlines()
        else:
            lines = []

        new_ps1 = build_dedsec_ps1(username)
        with open(BASHRC_PATH, "w") as bashrc_file:
            ps1_replaced = False
            for line in lines:
                if line.strip().startswith("PS1="):
                    bashrc_file.write(new_ps1)
                    ps1_replaced = True
                else:
                    bashrc_file.write(line)
            if not ps1_replaced:
                bashrc_file.write(new_ps1)
        return True
    except Exception as error:
        print(f"[!] Failed to update prompt: {error}")
        return False


def modify_bashrc():
    username = input(f"{_('Prompt Username')}: ").strip()
    while not username:
        print(_("Username cannot be empty. Please enter a valid username."))
        username = input(f"{_('Prompt Username')}: ").strip()
    set_prompt_username(username)


def change_prompt():
    print(f"\n[+] {_('Changing Prompt...')} \n")
    modify_bashrc()
    print(f"\n[+] {_('Customizations applied successfully! ')}")

# ------------------------------
# GitHub Account + Stats
# ------------------------------
def run_process(command, cwd=None, capture=True, check=False):
    """Safer subprocess helper for commands that do not need shell expansion."""
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.STDOUT if capture else None,
            check=check,
        )
        return completed.returncode, (completed.stdout or "").strip()
    except Exception as error:
        return 1, str(error)


def ensure_pkg_command(binary_name, package_name=None):
    """Install a Termux package only when the binary is missing."""
    if shutil.which(binary_name):
        return True
    package_name = package_name or binary_name
    print(f"[*] Installing {package_name} ...")
    run_process(["pkg", "update", "-y"], capture=False, check=False)
    run_process(["pkg", "install", "-y", package_name], capture=False, check=False)
    return shutil.which(binary_name) is not None


def load_github_account_config():
    try:
        if os.path.exists(GITHUB_ACCOUNT_CONFIG_PATH):
            with open(GITHUB_ACCOUNT_CONFIG_PATH, "r", encoding="utf-8") as handle:
                data = json.load(handle)
                if isinstance(data, dict):
                    return data
    except Exception:
        pass
    return {}


def save_github_account_config(data):
    try:
        with open(GITHUB_ACCOUNT_CONFIG_PATH, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
    except Exception:
        pass


def remove_github_account_config():
    try:
        if os.path.exists(GITHUB_ACCOUNT_CONFIG_PATH):
            os.remove(GITHUB_ACCOUNT_CONFIG_PATH)
    except Exception:
        pass


def github_cli_available():
    return ensure_pkg_command("gh", "gh")


def github_auth_status():
    if not shutil.which("gh"):
        return False
    rc, _out = run_process(["gh", "auth", "status", "--hostname", "github.com"], capture=True, check=False)
    return rc == 0


def github_current_username():
    if not shutil.which("gh"):
        return ""
    rc, out = run_process(["gh", "api", "user", "--jq", ".login"], capture=True, check=False)
    if rc == 0 and out:
        return out.strip().splitlines()[-1].strip()
    return ""


def github_auth_token():
    if not shutil.which("gh"):
        return ""
    rc, out = run_process(["gh", "auth", "token"], capture=True, check=False)
    if rc == 0 and out:
        return out.strip().splitlines()[-1].strip()
    return ""


def connect_github_account():
    print("=== " + _("Connect GitHub Account") + " ===")
    if not github_cli_available():
        print("[!] GitHub CLI (gh) could not be installed. Run manually: pkg install gh")
        return

    if not github_auth_status():
        print("[*] Starting GitHub device/web login, same style as Dead Switch.")
        print("[*] Follow the instructions that GitHub CLI prints in Termux.")
        run_process(["gh", "auth", "login", "--hostname", "github.com", "--git-protocol", "https", "--web"], capture=False, check=False)

    if not github_auth_status():
        print("[!] Login was not completed. Run manually: gh auth login --hostname github.com --git-protocol https --web")
        return

    username = github_current_username()
    if not username:
        print("[!] GitHub connected, but username could not be detected yet.")
        return

    save_github_account_config({
        "connected": True,
        "username": username,
        "connected_at": time.time(),
        "prompt_auto_username": True,
    })
    if set_prompt_username(username):
        print("[+] " + _("Prompt automatically updated to GitHub username."))
    print(f"[+] {_('GitHub account connected')}: {username}")


def disconnect_github_account():
    print("=== " + _("Disconnect GitHub Account") + " ===")
    config = load_github_account_config()
    current_user = config.get("username") or github_current_username()

    answer = input("Disconnect GitHub from this Termux device? (y/n): ").strip().lower()
    if answer not in ("y", "yes"):
        print("[*] Cancelled.")
        return

    if shutil.which("gh"):
        commands = [
            ["gh", "auth", "logout", "--hostname", "github.com", "--yes"],
            ["gh", "auth", "logout", "-h", "github.com", "-y"],
        ]
        for command in commands:
            rc, _out = run_process(command, capture=True, check=False)
            if rc == 0:
                break

    remove_github_account_config()
    if current_user:
        print(f"[+] {_('GitHub account disconnected')}: {current_user}")
    else:
        print("[+] " + _("GitHub account disconnected"))


def apply_github_prompt_if_connected():
    """Called at startup so a connected GitHub account keeps the prompt name synced."""
    config = load_github_account_config()
    if not config.get("connected") or not config.get("prompt_auto_username", True):
        return
    username = config.get("username") or github_current_username()
    if username:
        set_prompt_username(username)


def fetch_github_account_stats():
    if not github_cli_available() or not github_auth_status():
        return None, _("GitHub is not connected yet.")

    username = github_current_username()
    token = github_auth_token()
    if not username or not token:
        return None, "Could not read GitHub username/token from gh."

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "DedSec-Settings-Termux",
    }
    query = """
    query($cursor: String) {
      viewer {
        login
        repositories(first: 100, after: $cursor, ownerAffiliations: OWNER, orderBy: {field: UPDATED_AT, direction: DESC}) {
          pageInfo { hasNextPage endCursor }
          nodes {
            name
            stargazerCount
            forkCount
            watchers { totalCount }
            defaultBranchRef {
              target {
                ... on Commit {
                  history { totalCount }
                }
              }
            }
          }
        }
      }
    }
    """

    cursor = None
    pages = 0
    repo_count = 0
    total_stars = 0
    total_forks = 0
    total_watchers = 0
    total_commits = 0

    while True:
        pages += 1
        if pages > 25:
            break
        try:
            response = requests.post(
                "https://api.github.com/graphql",
                headers=headers,
                json={"query": query, "variables": {"cursor": cursor}},
                timeout=35,
            )
            if response.status_code >= 400:
                return None, f"GitHub API error {response.status_code}: {response.text[:300]}"
            payload = response.json()
        except Exception as error:
            return None, str(error)

        if payload.get("errors"):
            return None, json.dumps(payload.get("errors"), ensure_ascii=False)[:500]

        viewer = payload.get("data", {}).get("viewer", {})
        repos = viewer.get("repositories", {})
        for repo in repos.get("nodes") or []:
            repo_count += 1
            total_stars += int(repo.get("stargazerCount") or 0)
            total_forks += int(repo.get("forkCount") or 0)
            total_watchers += int(((repo.get("watchers") or {}).get("totalCount")) or 0)
            default_branch = repo.get("defaultBranchRef") or {}
            target = default_branch.get("target") or {}
            history = target.get("history") or {}
            total_commits += int(history.get("totalCount") or 0)

        page_info = repos.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        if not cursor:
            break

    rank = calculate_github_rank(total_stars, total_forks, total_watchers, total_commits, repo_count)
    return {
        "username": username,
        "repositories": repo_count,
        "stars": total_stars,
        "forks": total_forks,
        "watchers": total_watchers,
        "commits": total_commits,
        "rank": rank,
    }, None


def calculate_github_rank(stars, forks, watchers, commits, repo_count):
    score = (stars * 8) + (forks * 5) + (watchers * 2) + (commits * 0.03) + (repo_count * 2)
    thresholds = [
        (2500, "S++"), (1600, "S+"), (1000, "S"),
        (650, "A++"), (400, "A+"), (250, "A"), (150, "A-"),
        (90, "B+"), (50, "B"), (25, "B-"), (10, "C"),
    ]
    for needed, label in thresholds:
        if score >= needed:
            return label
    return "D"


def show_github_stats():
    print("=== " + _("Show GitHub Stats") + " ===")
    stats, error = fetch_github_account_stats()
    if error:
        print("[!] " + str(error))
        return
    print(f"{_('GitHub username')}: {stats['username']}")
    print(f"{_('Repositories counted')}: {stats['repositories']}")
    print(f"{_('Total stars')}: {stats['stars']}")
    print(f"{_('Total forks')}: {stats['forks']}")
    print(f"{_('Total watchers')}: {stats['watchers']}")
    print(f"{_('Total commits')}: {stats['commits']}")
    print(f"{_('Rank')}: {stats['rank']}")


def github_account_menu():
    while True:
        os.system("clear")
        config = load_github_account_config()
        detected_user = github_current_username() if shutil.which("gh") and github_auth_status() else ""
        username = config.get("username") or detected_user
        status = f"{_('Connected as')}: {username}" if username else _("Not connected")
        print("=== " + _("GitHub Account") + " ===")
        print(status + "\n")
        options = [
            _("Connect GitHub Account"),
            _("Disconnect GitHub Account"),
            _("Show GitHub Stats"),
            _("Back"),
        ]
        for index, option in enumerate(options, start=1):
            print(f"{index}. {option}")
        choice = input("\n> ").strip()
        if choice == "1":
            connect_github_account()
        elif choice == "2":
            disconnect_github_account()
        elif choice == "3":
            show_github_stats()
        elif choice == "4" or choice == "0":
            return
        else:
            print(_("Invalid selection. Please try again."))
        input("\n" + _("Press Enter to continue..."))



def ensure_github_connected_for_sponsors():
    """Uses the existing gh login flow before accessing Sponsors-Only content."""
    if not github_cli_available():
        print("[!] GitHub CLI (gh) could not be installed. Run manually: pkg install gh")
        return False

    if github_auth_status():
        username = github_current_username()
        config = load_github_account_config()
        if username and (not config.get("connected") or config.get("username") != username):
            save_github_account_config({
                "connected": True,
                "username": username,
                "connected_at": config.get("connected_at", time.time()),
                "prompt_auto_username": config.get("prompt_auto_username", True),
            })
        return True

    answer = input(_("GitHub is not connected yet. Connect GitHub now? (y/n): ")).strip().lower()
    if answer not in ("y", "yes"):
        print(_("GitHub connection is required for Sponsors-Only scripts."))
        return False

    connect_github_account()
    return github_auth_status()


def github_token_for_sponsors():
    """Returns the active gh token without printing it."""
    token = github_auth_token()
    return (token or "").strip()


def _write_sponsors_git_askpass(token):
    """Creates a temporary GIT_ASKPASS helper so private git access avoids gh GraphQL."""
    askpass_path = os.path.join(HOME_DIR, f".dedsec_sponsors_askpass_{os.getpid()}.py")
    script = """#!/usr/bin/env python3
import os
import sys
prompt = " ".join(sys.argv[1:]).lower()
if "username" in prompt:
    print("x-access-token")
else:
    print(os.environ.get("DEDSEC_GITHUB_TOKEN", ""))
"""
    with open(askpass_path, "w", encoding="utf-8") as handle:
        handle.write(script)
    try:
        os.chmod(askpass_path, 0o700)
    except Exception:
        pass
    return askpass_path


def run_sponsors_git_command(git_args, token, cwd=None):
    """Runs git with the authenticated GitHub token using GIT_ASKPASS."""
    askpass_path = _write_sponsors_git_askpass(token)
    env = os.environ.copy()
    env["GIT_ASKPASS"] = askpass_path
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["DEDSEC_GITHUB_TOKEN"] = token
    try:
        completed = subprocess.run(
            ["git"] + list(git_args),
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            env=env,
        )
        return completed.returncode, (completed.stdout or "").strip()
    except Exception as error:
        return 1, str(error)
    finally:
        try:
            os.remove(askpass_path)
        except Exception:
            pass


def sponsors_repo_access_status(tier_key="3"):
    """Returns (has_access, message) for a private Sponsors-Only tier repository."""
    config = get_sponsor_tier_config(tier_key)
    if not config:
        return False, _("Invalid sponsor tier.")

    if not github_cli_available() or not github_auth_status():
        return False, _("GitHub is not connected yet.")

    if not ensure_pkg_command("git", "git"):
        return False, "git could not be installed. Run manually: pkg install git"

    token = github_token_for_sponsors()
    if not token:
        return False, "Could not read GitHub token. Run manually: gh auth refresh -h github.com -s repo"

    rc, out = run_sponsors_git_command(["ls-remote", config["git_url"], "HEAD"], token)
    if rc == 0:
        success_message = _("Sponsors-Only access confirmed.") + f" ({config['label']})"
        try:
            achievements_remember_sponsor_access(tier_key, True, success_message)
        except Exception:
            pass
        return True, success_message

    message = (out or "").strip()
    if "saml" in message.lower() or "sso" in message.lower():
        message = "GitHub access exists but the token may need SSO approval for the organization. Open GitHub in browser and authorize the gh token for this organization."
    elif not message or "repository not found" in message.lower() or "authentication failed" in message.lower():
        message = _("You do not have access to the Sponsors-Only repository yet.")
    try:
        achievements_remember_sponsor_access(tier_key, False, message)
    except Exception:
        pass
    return False, message


def remove_old_sponsors_copies(tier_key="3", include_final=True):
    config = get_sponsor_tier_config(tier_key)
    if not config:
        return

    names = list(config.get("old_root_names") or [])
    if include_final:
        names.insert(0, config["root_name"])

    seen = set()
    for name in names:
        if not name or name in seen:
            continue
        seen.add(name)
        target = os.path.join(HOME_DIR, name)
        _remove_path_if_exists(target)


def clone_sponsors_repository(tier_key="3"):
    config = get_sponsor_tier_config(tier_key)
    if not config:
        return False, _("Invalid sponsor tier.")

    if not ensure_pkg_command("git", "git"):
        return False, "git could not be installed. Run manually: pkg install git"

    token = github_token_for_sponsors()
    if not token:
        return False, "Could not read GitHub token. Run manually: gh auth refresh -h github.com -s repo"

    root_path = get_sponsors_tier_root_path(tier_key)
    temp_target = root_path + ".download"
    _remove_path_if_exists(temp_target)

    rc, out = run_sponsors_git_command(
        ["clone", "--depth", "1", config["git_url"], temp_target],
        token,
    )
    if rc == 0 and os.path.isdir(temp_target):
        remove_old_sponsors_copies(tier_key=tier_key, include_final=True)
        try:
            os.rename(temp_target, root_path)
        except Exception:
            shutil.move(temp_target, root_path)
        return True, _("Sponsors-Only scripts downloaded to") + ": " + root_path

    _remove_path_if_exists(temp_target)
    message = (out or "").strip()
    if not message:
        message = "git clone failed"
    if "unexpected eof" in message.lower():
        message += "\\nNetwork dropped during download. Try again; the old Sponsors-Only folder was kept if it existed."
    return False, message


def check_all_sponsor_tier_access():
    for tier_key in SPONSORS_TIER_ORDER:
        config = get_sponsor_tier_config(tier_key)
        if not config:
            continue
        print(f"\n[*] {_('Checking Sponsors-Only access for')} {config['label']}...")
        has_access, access_message = sponsors_repo_access_status(tier_key)
        if has_access:
            print("[+] " + _("Access available") + ": " + config["label"])
        else:
            print("[!] " + _("Access denied") + ": " + config["label"])
        if access_message:
            print(access_message)


def access_sponsors_only_scripts(tier_key=None):
    print("=== " + _("Access Sponsors-Only Scripts") + " ===")

    if not ensure_github_connected_for_sponsors():
        return

    selected_tier = str(tier_key or "").replace("$", "").strip()
    if not selected_tier:
        while True:
            print("\n" + _("Choose Sponsors-Only tier"))
            print("1. " + _("Download Sponsors-Only $3 Tier"))
            print("2. " + _("Download Sponsors-Only $9 Tier"))
            print("3. " + _("Check access to both sponsor tiers"))
            print("0. " + _("Back"))
            choice = input(_("Enter the number of your choice: ")).strip().lower()

            if choice == "1":
                selected_tier = "3"
                break
            if choice == "2":
                selected_tier = "9"
                break
            if choice == "3":
                check_all_sponsor_tier_access()
                return
            if choice in ("0", "b", "back", "q", "quit"):
                return
            print(_("Invalid selection. Please try again."))

    config = get_sponsor_tier_config(selected_tier)
    if not config:
        print("[!] " + _("Invalid sponsor tier."))
        return

    print(f"{_('Checking Sponsors-Only access for')} {config['label']}...")
    has_access, access_message = sponsors_repo_access_status(selected_tier)
    if not has_access:
        print("[!] " + _("You do not have access to the Sponsors-Only repository yet."))
        if access_message:
            print(access_message)
        print(_("Make sure you are sponsoring with the connected GitHub account."))
        return

    print(access_message)
    print(_("Downloading Sponsors-Only scripts..."))
    ok, message = clone_sponsors_repository(selected_tier)
    if ok:
        print("[+] " + message)
    else:
        print("[!] " + _("Failed to download Sponsors-Only scripts") + ": " + message)

# ------------------------------
# Termux Usage Stats
# ------------------------------
LANGUAGE_BY_EXTENSION = {
    ".py": "Python", ".sh": "Shell", ".bash": "Bash", ".zsh": "Zsh",
    ".js": "JavaScript", ".mjs": "JavaScript", ".ts": "TypeScript",
    ".html": "HTML", ".htm": "HTML", ".css": "CSS", ".scss": "SCSS",
    ".json": "JSON", ".yaml": "YAML", ".yml": "YAML", ".xml": "XML",
    ".java": "Java", ".kt": "Kotlin", ".c": "C", ".h": "C/C++ Header",
    ".cpp": "C++", ".cc": "C++", ".hpp": "C++ Header", ".cs": "C#",
    ".go": "Go", ".rs": "Rust", ".php": "PHP", ".rb": "Ruby",
    ".lua": "Lua", ".sql": "SQL", ".md": "Markdown", ".txt": "Text",
}

TERMUX_STATS_SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".cache", ".npm", ".local",
    "venv", ".venv", "env", ".env", ".gradle", "build", "dist",
}


def format_duration(seconds):
    try:
        seconds = int(max(0, seconds))
    except Exception:
        seconds = 0
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs or not parts:
        parts.append(f"{secs}s")
    return " ".join(parts)


def format_timestamp(timestamp):
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(timestamp)))
    except Exception:
        return "Unknown"


def load_termux_usage_stats():
    try:
        if os.path.exists(TERMUX_USAGE_STATS_PATH):
            with open(TERMUX_USAGE_STATS_PATH, "r", encoding="utf-8") as handle:
                data = json.load(handle)
                if isinstance(data, dict):
                    return data
    except Exception:
        pass
    return {}


def save_termux_usage_stats(data):
    try:
        with open(TERMUX_USAGE_STATS_PATH, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
    except Exception:
        pass


def should_skip_stats_path(full_path):
    base = os.path.basename(full_path)
    if full_path in (TERMUX_USAGE_STATS_PATH, GITHUB_ACCOUNT_CONFIG_PATH, LANGUAGE_JSON_PATH):
        return True
    if base.endswith((".pyc", ".pyo")):
        return True
    return False


def collect_termux_file_snapshot(max_files=20000):
    root = TERMUX_USAGE_SCAN_ROOT if os.path.isdir(TERMUX_USAGE_SCAN_ROOT) else os.path.expanduser("~")
    snapshot = {}
    language_counts = {}
    language_bytes = {}
    folder_counts = {}
    newest_files = []
    scanned = 0

    for current_root, dirnames, filenames in os.walk(root, topdown=True, onerror=lambda _e: None):
        dirnames[:] = [d for d in dirnames if d not in TERMUX_STATS_SKIP_DIRS and not d.startswith(".")]
        for filename in filenames:
            if scanned >= max_files:
                return snapshot, language_counts, language_bytes, folder_counts, newest_files
            full_path = os.path.join(current_root, filename)
            if should_skip_stats_path(full_path):
                continue
            try:
                stat = os.stat(full_path)
                rel_path = os.path.relpath(full_path, root)
            except Exception:
                continue
            ext = os.path.splitext(filename)[1].lower()
            language = LANGUAGE_BY_EXTENSION.get(ext)
            snapshot[rel_path] = {
                "size": int(stat.st_size),
                "mtime": int(stat.st_mtime),
                "ext": ext,
            }
            if language:
                language_counts[language] = language_counts.get(language, 0) + 1
                language_bytes[language] = language_bytes.get(language, 0) + int(stat.st_size)
            folder = os.path.dirname(rel_path) or "."
            folder_counts[folder] = folder_counts.get(folder, 0) + 1
            newest_files.append((int(stat.st_mtime), rel_path))
            scanned += 1

    newest_files.sort(reverse=True)
    return snapshot, language_counts, language_bytes, folder_counts, newest_files[:10]


def summarize_bash_history():
    history_paths = [
        os.path.join(HOME_DIR, ".bash_history"),
        os.path.join(HOME_DIR, ".zsh_history"),
    ]
    total_commands = 0
    command_counts = {}
    for history_path in history_paths:
        try:
            if not os.path.exists(history_path):
                continue
            with open(history_path, "r", encoding="utf-8", errors="ignore") as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if not line:
                        continue
                    if ";" in line and line.startswith(": "):
                        line = line.split(";", 1)[1].strip()
                    command = line.split()[0] if line.split() else ""
                    if command:
                        total_commands += 1
                        command_counts[command] = command_counts.get(command, 0) + 1
        except Exception:
            continue
    top_commands = sorted(command_counts.items(), key=lambda item: item[1], reverse=True)[:10]
    return total_commands, top_commands


def update_termux_usage_stats():
    now = time.time()
    stats = load_termux_usage_stats()
    first_scan = float(stats.get("first_scan") or now)
    previous_snapshot = stats.get("snapshot") if isinstance(stats.get("snapshot"), dict) else {}

    current_snapshot, language_counts, language_bytes, folder_counts, newest_files = collect_termux_file_snapshot()
    current_paths = set(current_snapshot.keys())
    previous_paths = set(previous_snapshot.keys())

    is_first_scan = not bool(previous_snapshot)
    created = sorted(current_paths - previous_paths) if not is_first_scan else []
    deleted = sorted(previous_paths - current_paths) if not is_first_scan else []
    edited = []
    if not is_first_scan:
        for rel_path in sorted(current_paths & previous_paths):
            old = previous_snapshot.get(rel_path) or {}
            new = current_snapshot.get(rel_path) or {}
            if old.get("size") != new.get("size") or old.get("mtime") != new.get("mtime"):
                edited.append(rel_path)

    totals = stats.get("totals") if isinstance(stats.get("totals"), dict) else {}
    totals["created"] = int(totals.get("created", 0)) + len(created)
    totals["deleted"] = int(totals.get("deleted", 0)) + len(deleted)
    totals["edited"] = int(totals.get("edited", 0)) + len(edited)

    total_commands, top_commands = summarize_bash_history()
    stats.update({
        "first_scan": first_scan,
        "last_scan": now,
        "scan_count": int(stats.get("scan_count", 0)) + 1,
        "snapshot": current_snapshot,
        "totals": totals,
        "latest": {
            "created": created[:20],
            "deleted": deleted[:20],
            "edited": edited[:20],
            "is_first_scan": is_first_scan,
        },
        "language_counts": language_counts,
        "language_bytes": language_bytes,
        "folder_counts": folder_counts,
        "newest_files": newest_files,
        "total_commands": total_commands,
        "top_commands": top_commands,
    })
    save_termux_usage_stats(stats)
    return stats


def _record_termux_settings_session_time():
    try:
        stats = load_termux_usage_stats()
        runtime = max(0, time.time() - SETTINGS_SESSION_START)
        stats["settings_runtime_seconds"] = float(stats.get("settings_runtime_seconds", 0.0)) + runtime
        if "first_scan" not in stats:
            stats["first_scan"] = SETTINGS_SESSION_START
        stats["last_seen"] = time.time()
        save_termux_usage_stats(stats)
    except Exception:
        pass



# ------------------------------
# DedSec Achievements System
# ------------------------------
# FUTURE UPDATE WARNING:
# Do not delete old achievement IDs, rename existing IDs, or weaken the earn checks.
# Old IDs are saved forever in ~/.dedsec_achievements.json. Future updates must append
# new achievement definitions or carefully extend condition logic without breaking users
# who already earned achievements. Hidden achievements must stay hidden until earned.
ACHIEVEMENTS_DEFINITIONS = [
    # Core / startup
    {"id": "first_launch", "title": "First Launch", "description": "Open Settings.py and start the DedSec control center.", "hidden": False, "condition": "always"},
    {"id": "background_awake", "title": "Background Awake", "description": "Keep the achievement checker enabled in the background.", "hidden": False, "check": "context_truthy", "key": "background_enabled"},
    {"id": "daemon_pulse", "title": "Daemon Pulse", "description": "Let the background checker complete at least 3 silent scans.", "hidden": False, "check": "event_at_least", "event": "background_checks", "value": 3},
    {"id": "constant_watch", "title": "Constant Watch", "description": "Let the background checker complete 20 silent scans.", "hidden": True, "check": "event_at_least", "event": "background_checks", "value": 20},
    {"id": "always_watching", "title": "Always Watching", "description": "Let the background checker complete 100 silent scans.", "hidden": True, "check": "event_at_least", "event": "background_checks", "value": 100},
    {"id": "trophy_room", "title": "Trophy Room", "description": "Open the Achievements menu for the first time.", "hidden": False, "condition": "achievement_menu_opened"},
    {"id": "trophy_inspector", "title": "Trophy Inspector", "description": "Manually check achievements 5 times.", "hidden": False, "check": "event_at_least", "event": "manual_checks", "value": 5},
    {"id": "log_reader", "title": "Log Reader", "description": "Open the achievement log from the trophy room.", "hidden": False, "check": "event_at_least", "event": "achievement_log_opened", "value": 1},
    {"id": "switch_operator", "title": "Switch Operator", "description": "Enable or disable the achievement background checker at least once.", "hidden": False, "check": "event_at_least", "event": "background_toggle", "value": 1},

    # Settings usage
    {"id": "settings_apprentice", "title": "Settings Apprentice", "description": "Open Settings.py 3 different times.", "hidden": False, "check": "event_at_least", "event": "settings_started", "value": 3},
    {"id": "seven_boots", "title": "Seven Boots", "description": "Open Settings.py seven different times.", "hidden": True, "condition": "settings_started_7"},
    {"id": "settings_regular", "title": "Settings Regular", "description": "Open Settings.py 25 different times.", "hidden": False, "check": "event_at_least", "event": "settings_started", "value": 25},
    {"id": "settings_veteran", "title": "Settings Veteran", "description": "Open Settings.py 50 different times.", "hidden": False, "check": "event_at_least", "event": "settings_started", "value": 50},
    {"id": "settings_legend", "title": "Settings Legend", "description": "Open Settings.py 100 different times.", "hidden": True, "check": "event_at_least", "event": "settings_started", "value": 100},
    {"id": "menu_roamer", "title": "Menu Roamer", "description": "Use 10 settings menu actions.", "hidden": False, "check": "event_at_least", "event": "settings_actions", "value": 10},
    {"id": "menu_master", "title": "Menu Master", "description": "Use 50 settings menu actions.", "hidden": True, "check": "event_at_least", "event": "settings_actions", "value": 50},

    # Menu styles / language
    {"id": "style_shifter", "title": "Style Shifter", "description": "Change the menu style from the default list view.", "hidden": False, "condition": "changed_menu_style"},
    {"id": "grid_operator", "title": "Grid Operator", "description": "Use the grid menu style.", "hidden": False, "check": "context_equals", "key": "menu_style", "value": "grid"},
    {"id": "number_commander", "title": "Number Commander", "description": "Use the numbered menu style.", "hidden": False, "check": "context_equals", "key": "menu_style", "value": "number"},
    {"id": "os_pilot", "title": "OS Pilot", "description": "Select DedSec OS as the menu style.", "hidden": True, "condition": "dedsec_os_style"},
    {"id": "greek_signal", "title": "Greek Signal", "description": "Switch the DedSec Project language to Greek.", "hidden": False, "condition": "greek_language"},
    {"id": "english_signal", "title": "English Signal", "description": "Use the DedSec Project in English language mode.", "hidden": False, "check": "context_equals", "key": "language", "value": "english"},
    {"id": "bilingual_operator", "title": "Bilingual Operator", "description": "Use both English and Greek language modes.", "hidden": True, "condition": "both_languages_seen"},

    # GitHub / sponsors / project save
    {"id": "github_link", "title": "GitHub Link", "description": "Connect a GitHub account inside Settings.py.", "hidden": False, "condition": "github_connected"},
    {"id": "github_identity", "title": "GitHub Identity", "description": "Keep a connected GitHub username saved for the DedSec prompt.", "hidden": False, "check": "context_truthy", "key": "github_username"},
    {"id": "legacy_keeper", "title": "Legacy Keeper", "description": "Create a DedSec Project Legacy save archive in Downloads.", "hidden": False, "condition": "project_save_exists"},
    {"id": "archive_stack", "title": "Archive Stack", "description": "Keep at least 3 DedSec Project Legacy save archives in Downloads.", "hidden": False, "check": "context_at_least", "key": "project_save_archives", "value": 3},
    {"id": "backup_vault", "title": "Backup Vault", "description": "Keep at least 7 DedSec Project Legacy save archives in Downloads.", "hidden": True, "check": "context_at_least", "key": "project_save_archives", "value": 7},
    {"id": "sponsor_gate", "title": "Sponsor Gate", "description": "Have a Sponsors-Only folder available locally.", "hidden": False, "condition": "sponsors_local"},
    {"id": "tier_three", "title": "Tier Three", "description": "Have the Sponsors-Only $3 tier folder available locally.", "hidden": False, "check": "context_truthy", "key": "sponsor_3_local"},
    {"id": "tier_nine", "title": "Tier Nine", "description": "Have the Sponsors-Only $9 tier folder available locally.", "hidden": False, "check": "context_truthy", "key": "sponsor_9_local"},
    {"id": "full_sponsor_access", "title": "Full Sponsor Access", "description": "Have both $3 and $9 sponsor tier folders available locally.", "hidden": True, "check": "all_truthy", "keys": ["sponsor_3_local", "sponsor_9_local"]},

    # Usage stats
    {"id": "stats_online", "title": "Stats Online", "description": "Run the Termux Usage Stats scanner at least once.", "hidden": False, "condition": "usage_stats_started"},
    {"id": "stats_repeat", "title": "Stats Repeat", "description": "Run the Termux Usage Stats scanner 5 times.", "hidden": False, "check": "context_at_least", "key": "usage_scan_count", "value": 5},
    {"id": "stats_machine", "title": "Stats Machine", "description": "Run the Termux Usage Stats scanner 20 times.", "hidden": True, "check": "context_at_least", "key": "usage_scan_count", "value": 20},
    {"id": "runtime_worker", "title": "Runtime Worker", "description": "Spend 30 tracked minutes inside Settings.py.", "hidden": False, "check": "context_at_least", "key": "settings_runtime_seconds", "value": 1800},
    {"id": "runtime_marathon", "title": "Runtime Marathon", "description": "Spend 2 tracked hours inside Settings.py.", "hidden": True, "check": "context_at_least", "key": "settings_runtime_seconds", "value": 7200},

    # Files and coding activity
    {"id": "script_builder", "title": "Script Builder", "description": "Keep at least 10 Python scripts inside the DedSec workspace.", "hidden": False, "condition": "python_scripts_10"},
    {"id": "script_collector", "title": "Script Collector", "description": "Keep 25 runnable scripts in the DedSec workspace.", "hidden": True, "condition": "runnable_scripts_25"},
    {"id": "code_armory", "title": "Code Armory", "description": "Keep at least 50 Python scripts inside the DedSec workspace.", "hidden": False, "check": "context_at_least", "key": "python_file_count", "value": 50},
    {"id": "code_fortress", "title": "Code Fortress", "description": "Keep at least 100 Python scripts inside the DedSec workspace.", "hidden": True, "check": "context_at_least", "key": "python_file_count", "value": 100},
    {"id": "runnable_army", "title": "Runnable Army", "description": "Keep 50 runnable Python or shell scripts in the DedSec workspace.", "hidden": True, "check": "context_at_least", "key": "runnable_file_count", "value": 50},
    {"id": "shell_runner", "title": "Shell Runner", "description": "Keep at least 5 shell scripts in the DedSec workspace.", "hidden": False, "check": "context_at_least", "key": "shell_file_count", "value": 5},
    {"id": "web_builder", "title": "Web Builder", "description": "Keep at least 5 HTML files in the DedSec workspace.", "hidden": False, "check": "context_at_least", "key": "html_file_count", "value": 5},
    {"id": "style_artist", "title": "Style Artist", "description": "Keep at least 5 CSS files in the DedSec workspace.", "hidden": False, "check": "context_at_least", "key": "css_file_count", "value": 5},
    {"id": "javascript_operator", "title": "JavaScript Operator", "description": "Keep at least 5 JavaScript files in the DedSec workspace.", "hidden": False, "check": "context_at_least", "key": "js_file_count", "value": 5},
    {"id": "json_keeper", "title": "JSON Keeper", "description": "Keep at least 10 JSON files in the DedSec workspace.", "hidden": False, "check": "context_at_least", "key": "json_file_count", "value": 10},
    {"id": "polyglot_code", "title": "Polyglot Code", "description": "Use at least 3 programming/file languages in tracked stats.", "hidden": False, "check": "context_at_least", "key": "language_type_count", "value": 3},
    {"id": "seven_languages", "title": "Seven Languages", "description": "Use at least 7 programming/file languages in tracked stats.", "hidden": True, "check": "context_at_least", "key": "language_type_count", "value": 7},
    {"id": "organized_workspace", "title": "Organized Workspace", "description": "Have activity across at least 10 tracked folders.", "hidden": False, "check": "context_at_least", "key": "folder_type_count", "value": 10},
    {"id": "file_creator", "title": "File Creator", "description": "Create at least 1 tracked file after the first stats scan.", "hidden": False, "check": "context_at_least", "key": "files_created_total", "value": 1},
    {"id": "file_editor", "title": "File Editor", "description": "Edit at least 5 tracked files after the first stats scan.", "hidden": False, "check": "context_at_least", "key": "files_edited_total", "value": 5},
    {"id": "cleaner", "title": "Cleaner", "description": "Delete at least 1 tracked file after the first stats scan.", "hidden": True, "check": "context_at_least", "key": "files_deleted_total", "value": 1},

    # Terminal commands
    {"id": "command_rookie", "title": "Command Rookie", "description": "Reach 25 commands in Termux history or tracked stats.", "hidden": False, "check": "context_at_least", "key": "total_commands", "value": 25},
    {"id": "command_veteran", "title": "Command Veteran", "description": "Reach 100 commands in Termux history or tracked stats.", "hidden": True, "condition": "commands_100"},
    {"id": "terminal_addict", "title": "Terminal Addict", "description": "Reach 500 commands in Termux history or tracked stats.", "hidden": False, "check": "context_at_least", "key": "total_commands", "value": 500},
    {"id": "terminal_legend", "title": "Terminal Legend", "description": "Reach 1000 commands in Termux history or tracked stats.", "hidden": True, "check": "context_at_least", "key": "total_commands", "value": 1000},

    # Network utilities
    {"id": "ghost_network", "title": "Ghost Network", "description": "Enable VPN or Tor utilities from Settings.py.", "hidden": False, "condition": "network_enabled"},
    {"id": "tor_operator", "title": "Tor Operator", "description": "Enable Tor utilities from Settings.py.", "hidden": False, "check": "context_truthy", "key": "tor_enabled"},
    {"id": "vpn_operator", "title": "VPN Operator", "description": "Enable VPN utilities from Settings.py.", "hidden": False, "check": "context_truthy", "key": "vpn_enabled"},
    {"id": "greek_route", "title": "Greek Route", "description": "Choose Greece as the saved VPN location.", "hidden": True, "check": "context_equals", "key": "vpn_country", "value": "GR"},
    {"id": "random_route", "title": "Random Route", "description": "Use random VPN country selection.", "hidden": True, "check": "context_equals", "key": "vpn_country", "value": "RANDOM"},

    # Time-based hidden trophies
    {"id": "morning_shift", "title": "Morning Shift", "description": "Use DedSec Project between 5 AM and noon.", "hidden": False, "check": "context_between", "key": "hour", "min": 5, "max": 11},
    {"id": "afternoon_builder", "title": "Afternoon Builder", "description": "Use DedSec Project between noon and 6 PM.", "hidden": False, "check": "context_between", "key": "hour", "min": 12, "max": 17},
    {"id": "late_shift", "title": "Late Shift", "description": "Use DedSec Project between 6 PM and midnight.", "hidden": False, "check": "context_between", "key": "hour", "min": 18, "max": 23},
    {"id": "night_operator", "title": "Night Operator", "description": "Use DedSec Project between midnight and 5 AM.", "hidden": True, "condition": "night_time"},
]


# Extra achievements for complete DedSec Project coverage.
# FUTURE UPDATE WARNING: append to these lists only; do not remove IDs or change earn keys.
ACHIEVEMENTS_PROJECT_ROOT = os.path.dirname(ENGLISH_BASE_PATH)
ACHIEVEMENTS_SPONSOR_ACCESS_REFRESH_SECONDS = 21600
ACHIEVEMENTS_PROJECT_COMPONENTS = [{'id': 'readme',
  'title': 'README Keeper',
  'description': 'Keep the main README.md available in the DedSec Project.',
  'relative': 'README.md',
  'kind': 'file',
  'category': 'documentation',
  'hidden': False},
 {'id': 'security_policy',
  'title': 'Security Policy',
  'description': 'Keep SECURITY.md available in the DedSec Project.',
  'relative': 'SECURITY.md',
  'kind': 'file',
  'category': 'documentation',
  'hidden': False},
 {'id': 'license_file',
  'title': 'License Holder',
  'description': 'Keep LICENSE.txt available in the DedSec Project.',
  'relative': 'LICENSE.txt',
  'kind': 'file',
  'category': 'documentation',
  'hidden': False},
 {'id': 'setup_sh',
  'title': 'Setup Launcher',
  'description': 'Keep Setup.sh available for first-time setup.',
  'relative': 'Setup.sh',
  'kind': 'file',
  'category': 'setup',
  'hidden': False},
 {'id': 'funding_file',
  'title': 'Funding Signal',
  'description': 'Keep the GitHub funding file available.',
  'relative': '.github/FUNDING.yml',
  'kind': 'file',
  'category': 'setup',
  'hidden': False},
 {'id': 'instructions_en',
  'title': 'Contributor Guide EN',
  'description': 'Keep the English contributor instructions available.',
  'relative': 'Important Documents/Instructions For Contributors EN.txt',
  'kind': 'file',
  'category': 'documentation',
  'hidden': False},
 {'id': 'instructions_gr',
  'title': 'Contributor Guide GR',
  'description': 'Keep the Greek contributor instructions available.',
  'relative': 'Important Documents/Instructions For Contributors GR.txt',
  'kind': 'file',
  'category': 'documentation',
  'hidden': False},
 {'id': 'legal_en',
  'title': 'Legal Document EN',
  'description': 'Keep the English legal disclaimer document available.',
  'relative': 'Important Documents/Legal Disclaimer English Version.docx',
  'kind': 'file',
  'category': 'documentation',
  'hidden': False},
 {'id': 'legal_gr',
  'title': 'Legal Document GR',
  'description': 'Keep the Greek legal disclaimer document available.',
  'relative': 'Important Documents/Legal Disclaimer Greek Version.docx',
  'kind': 'file',
  'category': 'documentation',
  'hidden': False},
 {'id': 'termux_book_en',
  'title': 'Termux Book EN',
  'description': 'Keep the English Master Termux PDF available.',
  'relative': 'Important Documents/Master Termux In 7 Days English.pdf',
  'kind': 'file',
  'category': 'documentation',
  'hidden': False},
 {'id': 'termux_book_gr',
  'title': 'Termux Book GR',
  'description': 'Keep the Greek Master Termux PDF available.',
  'relative': 'Important Documents/Master Termux In 7 Days Greek.pdf',
  'kind': 'file',
  'category': 'documentation',
  'hidden': False},
 {'id': 'settings_py',
  'title': 'Settings Core',
  'description': 'Keep Settings.py available in the DedSec Project.',
  'relative': 'Scripts/Settings.py',
  'kind': 'file',
  'category': 'core',
  'hidden': False},
 {'id': 'butsystem_py',
  'title': 'ButSystem Core',
  'description': 'Keep ButSystem.py available in the DedSec Project.',
  'relative': 'Scripts/ButSystem.py',
  'kind': 'file',
  'category': 'core',
  'hidden': False},
 {'id': 'dedsec_market_py',
  'title': 'DedSec Market Core',
  'description': 'Keep DedSec Market.py available in the DedSec Project.',
  'relative': 'Scripts/DedSec Market.py',
  'kind': 'file',
  'category': 'core',
  'hidden': False},
 {'id': 'extra_content_py',
  'title': 'Extra Content Core',
  'description': 'Keep Extra Content.py available in the DedSec Project.',
  'relative': 'Scripts/Extra Content.py',
  'kind': 'file',
  'category': 'core',
  'hidden': False},
 {'id': 'dev_dead_switch',
  'title': 'Dead Switch',
  'description': 'Keep Dead Switch.py available inside Developer Base.',
  'relative': 'Scripts/Developer Base/Dead Switch.py',
  'kind': 'file',
  'category': 'developer_base',
  'hidden': False},
 {'id': 'dev_devices_finder',
  'title': 'Devices Finder',
  'description': 'Keep Devices Finder.py available inside Developer Base.',
  'relative': 'Scripts/Developer Base/Devices Finder.py',
  'kind': 'file',
  'category': 'developer_base',
  'hidden': False},
 {'id': 'dev_file_converter',
  'title': 'File Converter',
  'description': 'Keep File Converter.py available inside Developer Base.',
  'relative': 'Scripts/Developer Base/File Converter.py',
  'kind': 'file',
  'category': 'developer_base',
  'hidden': False},
 {'id': 'dev_file_type_checker',
  'title': 'File Type Checker',
  'description': 'Keep File Type Checker.py available inside Developer Base.',
  'relative': 'Scripts/Developer Base/File Type Checker.py',
  'kind': 'file',
  'category': 'developer_base',
  'hidden': False},
 {'id': 'dev_free_internet',
  'title': 'Free Internet',
  'description': 'Keep Free Internet.py available inside Developer Base.',
  'relative': 'Scripts/Developer Base/Free Internet.py',
  'kind': 'file',
  'category': 'developer_base',
  'hidden': False},
 {'id': 'dev_mobile_desktop',
  'title': 'Mobile Desktop',
  'description': 'Keep Mobile Desktop.py available inside Developer Base.',
  'relative': 'Scripts/Developer Base/Mobile Desktop.py',
  'kind': 'file',
  'category': 'developer_base',
  'hidden': False},
 {'id': 'dev_mobile_developer_setup',
  'title': 'Mobile Developer Setup',
  'description': 'Keep Mobile Developer Setup.py available inside Developer Base.',
  'relative': 'Scripts/Developer Base/Mobile Developer Setup.py',
  'kind': 'file',
  'category': 'developer_base',
  'hidden': False},
 {'id': 'dev_simple_websites_creator',
  'title': 'Simple Websites Creator',
  'description': 'Keep Simple Websites Creator.py available inside Developer Base.',
  'relative': 'Scripts/Developer Base/Simple Websites Creator.py',
  'kind': 'file',
  'category': 'developer_base',
  'hidden': False},
 {'id': 'dev_smart_notes',
  'title': 'Smart Notes',
  'description': 'Keep Smart Notes.py available inside Developer Base.',
  'relative': 'Scripts/Developer Base/Smart Notes.py',
  'kind': 'file',
  'category': 'developer_base',
  'hidden': False},
 {'id': 'dev_tree_explorer',
  'title': 'Tree Explorer',
  'description': 'Keep Tree Explorer.py available inside Developer Base.',
  'relative': 'Scripts/Developer Base/Tree Explorer.py',
  'kind': 'file',
  'category': 'developer_base',
  'hidden': False},
 {'id': 'net_bug_hunter',
  'title': 'Bug Hunter',
  'description': 'Keep Bug Hunter.py available inside Network Tools.',
  'relative': 'Scripts/Network Tools/Bug Hunter.py',
  'kind': 'file',
  'category': 'network_tools',
  'hidden': False},
 {'id': 'net_connections',
  'title': 'Connections',
  'description': 'Keep Connections.py available inside Network Tools.',
  'relative': 'Scripts/Network Tools/Connections.py',
  'kind': 'file',
  'category': 'network_tools',
  'hidden': False},
 {'id': 'net_dark',
  'title': 'Dark',
  'description': 'Keep Dark.py available inside Network Tools.',
  'relative': 'Scripts/Network Tools/Dark.py',
  'kind': 'file',
  'category': 'network_tools',
  'hidden': False},
 {'id': 'net_dedsec_s_network',
  'title': "DedSec's Network",
  'description': "Keep DedSec's Network.py available inside Network Tools.",
  'relative': "Scripts/Network Tools/DedSec's Network.py",
  'kind': 'file',
  'category': 'network_tools',
  'hidden': False},
 {'id': 'net_digital_footprint_finder',
  'title': 'Digital Footprint Finder',
  'description': 'Keep Digital Footprint Finder.py available inside Network Tools.',
  'relative': 'Scripts/Network Tools/Digital Footprint Finder.py',
  'kind': 'file',
  'category': 'network_tools',
  'hidden': False},
 {'id': 'net_link_shield',
  'title': 'Link Shield',
  'description': 'Keep Link Shield.py available inside Network Tools.',
  'relative': 'Scripts/Network Tools/Link Shield.py',
  'kind': 'file',
  'category': 'network_tools',
  'hidden': False},
 {'id': 'net_masker',
  'title': 'Masker',
  'description': 'Keep Masker.py available inside Network Tools.',
  'relative': 'Scripts/Network Tools/Masker.py',
  'kind': 'file',
  'category': 'network_tools',
  'hidden': False},
 {'id': 'net_qr_code_generator',
  'title': 'QR Code Generator',
  'description': 'Keep QR Code Generator.py available inside Network Tools.',
  'relative': 'Scripts/Network Tools/QR Code Generator.py',
  'kind': 'file',
  'category': 'network_tools',
  'hidden': False},
 {'id': 'net_sod',
  'title': 'Sod',
  'description': 'Keep Sod.py available inside Network Tools.',
  'relative': 'Scripts/Network Tools/Sod.py',
  'kind': 'file',
  'category': 'network_tools',
  'hidden': False},
 {'id': 'net_store_scrapper',
  'title': 'Store Scrapper',
  'description': 'Keep Store Scrapper.py available inside Network Tools.',
  'relative': 'Scripts/Network Tools/Store Scrapper.py',
  'kind': 'file',
  'category': 'network_tools',
  'hidden': False},
 {'id': 'game_buzz',
  'title': 'Buzz',
  'description': 'Keep Buzz.py available inside Games.',
  'relative': 'Scripts/Games/Buzz.py',
  'kind': 'file',
  'category': 'games',
  'hidden': False},
 {'id': 'game_ctf_god',
  'title': 'CTF God',
  'description': 'Keep CTF God.py available inside Games.',
  'relative': 'Scripts/Games/CTF God.py',
  'kind': 'file',
  'category': 'games',
  'hidden': False},
 {'id': 'game_detective',
  'title': 'Detective',
  'description': 'Keep Detective.py available inside Games.',
  'relative': 'Scripts/Games/Detective.py',
  'kind': 'file',
  'category': 'games',
  'hidden': False},
 {'id': 'game_tamagotchi',
  'title': 'Tamagotchi',
  'description': 'Keep Tamagotchi.py available inside Games.',
  'relative': 'Scripts/Games/Tamagotchi.py',
  'kind': 'file',
  'category': 'games',
  'hidden': False},
 {'id': 'game_terminal_arcade',
  'title': 'Terminal Arcade',
  'description': 'Keep Terminal Arcade.py available inside Games.',
  'relative': 'Scripts/Games/Terminal Arcade.py',
  'kind': 'file',
  'category': 'games',
  'hidden': False},
 {'id': 'other_android_app_launcher',
  'title': 'Android App Launcher',
  'description': 'Keep Android App Launcher.py available inside Other Tools.',
  'relative': 'Scripts/Other Tools/Android App Launcher.py',
  'kind': 'file',
  'category': 'other_tools',
  'hidden': False},
 {'id': 'other_loading_screen',
  'title': 'Loading Screen',
  'description': 'Keep Loading Screen.py available inside Other Tools.',
  'relative': 'Scripts/Other Tools/Loading Screen.py',
  'kind': 'file',
  'category': 'other_tools',
  'hidden': False},
 {'id': 'other_password_master',
  'title': 'Password Master',
  'description': 'Keep Password Master.py available inside Other Tools.',
  'relative': 'Scripts/Other Tools/Password Master.py',
  'kind': 'file',
  'category': 'other_tools',
  'hidden': False},
 {'id': 'other_termux_backup_restore',
  'title': 'Termux Backup Restore',
  'description': 'Keep Termux Backup Restore.py available inside Other Tools.',
  'relative': 'Scripts/Other Tools/Termux Backup Restore.py',
  'kind': 'file',
  'category': 'other_tools',
  'hidden': False},
 {'id': 'other_termux_repair_wizard',
  'title': 'Termux Repair Wizard',
  'description': 'Keep Termux Repair Wizard.py available inside Other Tools.',
  'relative': 'Scripts/Other Tools/Termux Repair Wizard.py',
  'kind': 'file',
  'category': 'other_tools',
  'hidden': False},
 {'id': 'fake_fake_apple_icloud_page',
  'title': 'Fake Apple iCloud Page',
  'description': 'Keep Fake Apple iCloud Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake Apple iCloud Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_discord_nitro_page',
  'title': 'Fake Discord Nitro Page',
  'description': 'Keep Fake Discord Nitro Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake Discord Nitro Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_epic_games_page',
  'title': 'Fake Epic Games Page',
  'description': 'Keep Fake Epic Games Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake Epic Games Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_facebook_friends_page',
  'title': 'Fake Facebook Friends Page',
  'description': 'Keep Fake Facebook Friends Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake Facebook Friends Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_free_robux_page',
  'title': 'Fake Free Robux Page',
  'description': 'Keep Fake Free Robux Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake Free Robux Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_github_pro_page',
  'title': 'Fake GitHub Pro Page',
  'description': 'Keep Fake GitHub Pro Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake GitHub Pro Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_google_free_money_page',
  'title': 'Fake Google Free Money Page',
  'description': 'Keep Fake Google Free Money Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake Google Free Money Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_instagram_followers_page',
  'title': 'Fake Instagram Followers Page',
  'description': 'Keep Fake Instagram Followers Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake Instagram Followers Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_metamask_page',
  'title': 'Fake MetaMask Page',
  'description': 'Keep Fake MetaMask Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake MetaMask Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_microsoft_365_page',
  'title': 'Fake Microsoft 365 Page',
  'description': 'Keep Fake Microsoft 365 Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake Microsoft 365 Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_onlyfans_page',
  'title': 'Fake OnlyFans Page',
  'description': 'Keep Fake OnlyFans Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake OnlyFans Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_paypal_page',
  'title': 'Fake PayPal Page',
  'description': 'Keep Fake PayPal Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake PayPal Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_pinterest_pro_page',
  'title': 'Fake Pinterest Pro Page',
  'description': 'Keep Fake Pinterest Pro Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake Pinterest Pro Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_playstation_network_page',
  'title': 'Fake PlayStation Network Page',
  'description': 'Keep Fake PlayStation Network Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake PlayStation Network Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_reddit_karma_page',
  'title': 'Fake Reddit Karma Page',
  'description': 'Keep Fake Reddit Karma Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake Reddit Karma Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_snapchat_friends_page',
  'title': 'Fake Snapchat Friends Page',
  'description': 'Keep Fake Snapchat Friends Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake Snapchat Friends Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_steam_games_page',
  'title': 'Fake Steam Games Page',
  'description': 'Keep Fake Steam Games Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake Steam Games Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_steam_wallet_page',
  'title': 'Fake Steam Wallet Page',
  'description': 'Keep Fake Steam Wallet Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake Steam Wallet Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_tik_tok_followers_page',
  'title': 'Fake Tik Tok Followers Page',
  'description': 'Keep Fake Tik Tok Followers Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake Tik Tok Followers Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_trust_wallet_page',
  'title': 'Fake Trust Wallet Page',
  'description': 'Keep Fake Trust Wallet Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake Trust Wallet Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_twitch_subs_page',
  'title': 'Fake Twitch Subs Page',
  'description': 'Keep Fake Twitch Subs Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake Twitch Subs Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_twitter_followers_page',
  'title': 'Fake Twitter Followers Page',
  'description': 'Keep Fake Twitter Followers Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake Twitter Followers Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_what_s_up_dude_page',
  'title': "Fake What's Up Dude Page",
  'description': "Keep Fake What's Up Dude Page.py available inside Fake Pages.",
  'relative': "Scripts/Fake Pages/Fake What's Up Dude Page.py",
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_xbox_live_page',
  'title': 'Fake Xbox Live Page',
  'description': 'Keep Fake Xbox Live Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake Xbox Live Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'fake_fake_youtube_subscribers_page',
  'title': 'Fake YouTube Subscribers Page',
  'description': 'Keep Fake YouTube Subscribers Page.py available inside Fake Pages.',
  'relative': 'Scripts/Fake Pages/Fake YouTube Subscribers Page.py',
  'kind': 'file',
  'category': 'fake_pages',
  'hidden': True},
 {'id': 'capture_fake_back_camera_page',
  'title': 'Fake Back Camera Page',
  'description': 'Keep Fake Back Camera Page.py available inside Personal Information Capture.',
  'relative': 'Scripts/Personal Information Capture/Fake Back Camera Page.py',
  'kind': 'file',
  'category': 'personal_capture',
  'hidden': True},
 {'id': 'capture_fake_back_camera_video_page',
  'title': 'Fake Back Camera Video Page',
  'description': 'Keep Fake Back Camera Video Page.py available inside Personal Information Capture.',
  'relative': 'Scripts/Personal Information Capture/Fake Back Camera Video Page.py',
  'kind': 'file',
  'category': 'personal_capture',
  'hidden': True},
 {'id': 'capture_fake_card_details_page',
  'title': 'Fake Card Details Page',
  'description': 'Keep Fake Card Details Page.py available inside Personal Information Capture.',
  'relative': 'Scripts/Personal Information Capture/Fake Card Details Page.py',
  'kind': 'file',
  'category': 'personal_capture',
  'hidden': True},
 {'id': 'capture_fake_chrome_verification_page',
  'title': 'Fake Chrome Verification Page',
  'description': 'Keep Fake Chrome Verification Page.py available inside Personal Information Capture.',
  'relative': 'Scripts/Personal Information Capture/Fake Chrome Verification Page.py',
  'kind': 'file',
  'category': 'personal_capture',
  'hidden': True},
 {'id': 'capture_fake_data_grabber_page',
  'title': 'Fake Data Grabber Page',
  'description': 'Keep Fake Data Grabber Page.py available inside Personal Information Capture.',
  'relative': 'Scripts/Personal Information Capture/Fake Data Grabber Page.py',
  'kind': 'file',
  'category': 'personal_capture',
  'hidden': True},
 {'id': 'capture_fake_discord_verification_page',
  'title': 'Fake Discord Verification Page',
  'description': 'Keep Fake Discord Verification Page.py available inside Personal Information Capture.',
  'relative': 'Scripts/Personal Information Capture/Fake Discord Verification Page.py',
  'kind': 'file',
  'category': 'personal_capture',
  'hidden': True},
 {'id': 'capture_fake_facebook_verification_page',
  'title': 'Fake Facebook Verification Page',
  'description': 'Keep Fake Facebook Verification Page.py available inside Personal Information Capture.',
  'relative': 'Scripts/Personal Information Capture/Fake Facebook Verification Page.py',
  'kind': 'file',
  'category': 'personal_capture',
  'hidden': True},
 {'id': 'capture_fake_front_camera_page',
  'title': 'Fake Front Camera Page',
  'description': 'Keep Fake Front Camera Page.py available inside Personal Information Capture.',
  'relative': 'Scripts/Personal Information Capture/Fake Front Camera Page.py',
  'kind': 'file',
  'category': 'personal_capture',
  'hidden': True},
 {'id': 'capture_fake_front_camera_video_page',
  'title': 'Fake Front Camera Video Page',
  'description': 'Keep Fake Front Camera Video Page.py available inside Personal Information Capture.',
  'relative': 'Scripts/Personal Information Capture/Fake Front Camera Video Page.py',
  'kind': 'file',
  'category': 'personal_capture',
  'hidden': True},
 {'id': 'capture_fake_google_location_page',
  'title': 'Fake Google Location Page',
  'description': 'Keep Fake Google Location Page.py available inside Personal Information Capture.',
  'relative': 'Scripts/Personal Information Capture/Fake Google Location Page.py',
  'kind': 'file',
  'category': 'personal_capture',
  'hidden': True},
 {'id': 'capture_fake_instagram_verification_page',
  'title': 'Fake Instagram Verification Page',
  'description': 'Keep Fake Instagram Verification Page.py available inside Personal Information Capture.',
  'relative': 'Scripts/Personal Information Capture/Fake Instagram Verification Page.py',
  'kind': 'file',
  'category': 'personal_capture',
  'hidden': True},
 {'id': 'capture_fake_location_page',
  'title': 'Fake Location Page',
  'description': 'Keep Fake Location Page.py available inside Personal Information Capture.',
  'relative': 'Scripts/Personal Information Capture/Fake Location Page.py',
  'kind': 'file',
  'category': 'personal_capture',
  'hidden': True},
 {'id': 'capture_fake_microphone_page',
  'title': 'Fake Microphone Page',
  'description': 'Keep Fake Microphone Page.py available inside Personal Information Capture.',
  'relative': 'Scripts/Personal Information Capture/Fake Microphone Page.py',
  'kind': 'file',
  'category': 'personal_capture',
  'hidden': True},
 {'id': 'capture_fake_onlyfans_verification_page',
  'title': 'Fake OnlyFans Verification Page',
  'description': 'Keep Fake OnlyFans Verification Page.py available inside Personal Information Capture.',
  'relative': 'Scripts/Personal Information Capture/Fake OnlyFans Verification Page.py',
  'kind': 'file',
  'category': 'personal_capture',
  'hidden': True},
 {'id': 'capture_fake_steam_verification_page',
  'title': 'Fake Steam Verification Page',
  'description': 'Keep Fake Steam Verification Page.py available inside Personal Information Capture.',
  'relative': 'Scripts/Personal Information Capture/Fake Steam Verification Page.py',
  'kind': 'file',
  'category': 'personal_capture',
  'hidden': True},
 {'id': 'capture_fake_twitch_verification_page',
  'title': 'Fake Twitch Verification Page',
  'description': 'Keep Fake Twitch Verification Page.py available inside Personal Information Capture.',
  'relative': 'Scripts/Personal Information Capture/Fake Twitch Verification Page.py',
  'kind': 'file',
  'category': 'personal_capture',
  'hidden': True},
 {'id': 'capture_fake_youtube_verification_page',
  'title': 'Fake YouTube Verification Page',
  'description': 'Keep Fake YouTube Verification Page.py available inside Personal Information Capture.',
  'relative': 'Scripts/Personal Information Capture/Fake YouTube Verification Page.py',
  'kind': 'file',
  'category': 'personal_capture',
  'hidden': True},
 {'id': 'extra_images',
  'title': 'Image Archive',
  'description': 'Keep the Extra Content image archive available.',
  'relative': 'Extra Content/Images',
  'kind': 'dir',
  'category': 'extra_content',
  'hidden': False},
 {'id': 'slots_demos',
  'title': 'Slots Demo Archive',
  'description': 'Keep the Slots Pages Demos folder available.',
  'relative': 'Extra Content/Slots Pages Demos',
  'kind': 'dir',
  'category': 'extra_content',
  'hidden': False},
 {'id': 'unused_scripts_archive',
  'title': 'Unused Script Archive',
  'description': 'Keep the Unused Scripts archive available.',
  'relative': 'Extra Content/Unused Scripts',
  'kind': 'dir',
  'category': 'extra_content',
  'hidden': True},
 {'id': 'greek_version_folder',
  'title': 'Greek Version Vault',
  'description': 'Keep the Greek version folder available.',
  'relative': 'Scripts/Ελληνική Έκδοση',
  'kind': 'dir',
  'category': 'greek_version',
  'hidden': False,
  'relative_options': ['Scripts/Ελληνική Έκδοση', 'Scripts/.Ελληνική Έκδοση']},
 {'id': 'greek_settings',
  'title': 'Greek Settings',
  'description': 'Keep the Greek Settings.py available.',
  'relative': 'Scripts/Ελληνική Έκδοση/Settings.py',
  'kind': 'file',
  'category': 'greek_version',
  'hidden': False,
  'relative_options': ['Scripts/Ελληνική Έκδοση/Settings.py', 'Scripts/.Ελληνική Έκδοση/Settings.py']},
 {'id': 'greek_butsystem',
  'title': 'Greek ButSystem',
  'description': 'Keep the Greek ButSystem.py available.',
  'relative': 'Scripts/Ελληνική Έκδοση/ButSystem.py',
  'kind': 'file',
  'category': 'greek_version',
  'hidden': False,
  'relative_options': ['Scripts/Ελληνική Έκδοση/ButSystem.py', 'Scripts/.Ελληνική Έκδοση/ButSystem.py']},
 {'id': 'greek_dedsec_market',
  'title': 'Greek DedSec Market',
  'description': 'Keep the Greek DedSec Market.py available.',
  'relative': 'Scripts/Ελληνική Έκδοση/DedSec Market.py',
  'kind': 'file',
  'category': 'greek_version',
  'hidden': False,
  'relative_options': ['Scripts/Ελληνική Έκδοση/DedSec Market.py', 'Scripts/.Ελληνική Έκδοση/DedSec Market.py']},
 {'id': 'greek_extra_content',
  'title': 'Greek Extra Content',
  'description': 'Keep the Greek Extra Content.py available.',
  'relative': 'Scripts/Ελληνική Έκδοση/Extra Content.py',
  'kind': 'file',
  'category': 'greek_version',
  'hidden': False,
  'relative_options': ['Scripts/Ελληνική Έκδοση/Extra Content.py', 'Scripts/.Ελληνική Έκδοση/Extra Content.py']}]

ACHIEVEMENTS_DEFINITIONS.extend([{'id': 'dedsec_project_25',
  'title': 'Project Scout',
  'description': 'Have at least 25 named DedSec Project components available.',
  'hidden': False,
  'check': 'context_at_least',
  'key': 'project_component_count',
  'value': 25},
 {'id': 'dedsec_project_50',
  'title': 'Project Operator',
  'description': 'Have at least 50 named DedSec Project components available.',
  'hidden': False,
  'check': 'context_at_least',
  'key': 'project_component_count',
  'value': 50},
 {'id': 'dedsec_project_75',
  'title': 'Project Archivist',
  'description': 'Have at least 75 named DedSec Project components available.',
  'hidden': True,
  'check': 'context_at_least',
  'key': 'project_component_count',
  'value': 75},
 {'id': 'dedsec_project_full',
  'title': 'Full DedSec Project',
  'description': 'Have every tracked DedSec Project component available.',
  'hidden': True,
  'check': 'context_at_least',
  'key': 'project_component_count',
  'value': 95},
 {'id': 'project_categories_5',
  'title': 'Five Wings Online',
  'description': 'Have files present in at least 5 DedSec Project categories.',
  'hidden': False,
  'check': 'context_at_least',
  'key': 'project_category_count',
  'value': 5},
 {'id': 'project_categories_10',
  'title': 'Whole Project Map',
  'description': 'Have files present across at least 10 DedSec Project categories.',
  'hidden': True,
  'check': 'context_at_least',
  'key': 'project_category_count',
  'value': 10},
 {'id': 'documentation_complete',
  'title': 'Documentation Complete',
  'description': 'Keep the main README, security, license, legal docs, and Termux books available.',
  'hidden': False,
  'check': 'context_at_least',
  'key': 'category_documentation_count',
  'value': 9},
 {'id': 'core_four',
  'title': 'Core Four',
  'description': 'Keep all four main DedSec scripts available.',
  'hidden': False,
  'check': 'context_at_least',
  'key': 'category_core_count',
  'value': 4},
 {'id': 'developer_base_complete',
  'title': 'Developer Base Complete',
  'description': 'Keep all Developer Base scripts available.',
  'hidden': False,
  'check': 'context_at_least',
  'key': 'category_developer_base_count',
  'value': 10},
 {'id': 'network_tools_complete',
  'title': 'Network Tools Complete',
  'description': 'Keep all Network Tools scripts available.',
  'hidden': False,
  'check': 'context_at_least',
  'key': 'category_network_tools_count',
  'value': 10},
 {'id': 'games_complete',
  'title': 'Arcade Shelf Complete',
  'description': 'Keep all DedSec game scripts available.',
  'hidden': False,
  'check': 'context_at_least',
  'key': 'category_games_count',
  'value': 5},
 {'id': 'other_tools_complete',
  'title': 'Utility Shelf Complete',
  'description': 'Keep all Other Tools scripts available.',
  'hidden': False,
  'check': 'context_at_least',
  'key': 'category_other_tools_count',
  'value': 5},
 {'id': 'fake_pages_collection',
  'title': 'Fake Pages Collection',
  'description': 'Keep at least 20 Fake Pages scripts available.',
  'hidden': True,
  'check': 'context_at_least',
  'key': 'category_fake_pages_count',
  'value': 20},
 {'id': 'fake_pages_full_collection',
  'title': 'Full Fake Pages Collection',
  'description': 'Keep the full Fake Pages script collection available.',
  'hidden': True,
  'check': 'context_at_least',
  'key': 'category_fake_pages_count',
  'value': 25},
 {'id': 'capture_collection',
  'title': 'Capture Collection',
  'description': 'Keep at least 10 Personal Information Capture scripts available.',
  'hidden': True,
  'check': 'context_at_least',
  'key': 'category_personal_capture_count',
  'value': 10},
 {'id': 'capture_full_collection',
  'title': 'Full Capture Collection',
  'description': 'Keep the full Personal Information Capture script collection available.',
  'hidden': True,
  'check': 'context_at_least',
  'key': 'category_personal_capture_count',
  'value': 17},
 {'id': 'greek_version_complete',
  'title': 'Greek Version Complete',
  'description': 'Keep the Greek main files and Greek version folder available.',
  'hidden': False,
  'check': 'context_at_least',
  'key': 'category_greek_version_count',
  'value': 5},
 {'id': 'extra_content_ready',
  'title': 'Extra Content Ready',
  'description': 'Keep the Extra Content folders available.',
  'hidden': False,
  'check': 'context_at_least',
  'key': 'category_extra_content_count',
  'value': 2},
 {'id': 'project_component_readme',
  'title': 'README Keeper',
  'description': 'Keep the main README.md available in the DedSec Project.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_readme'},
 {'id': 'project_component_security_policy',
  'title': 'Security Policy',
  'description': 'Keep SECURITY.md available in the DedSec Project.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_security_policy'},
 {'id': 'project_component_license_file',
  'title': 'License Holder',
  'description': 'Keep LICENSE.txt available in the DedSec Project.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_license_file'},
 {'id': 'project_component_setup_sh',
  'title': 'Setup Launcher',
  'description': 'Keep Setup.sh available for first-time setup.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_setup_sh'},
 {'id': 'project_component_funding_file',
  'title': 'Funding Signal',
  'description': 'Keep the GitHub funding file available.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_funding_file'},
 {'id': 'project_component_instructions_en',
  'title': 'Contributor Guide EN',
  'description': 'Keep the English contributor instructions available.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_instructions_en'},
 {'id': 'project_component_instructions_gr',
  'title': 'Contributor Guide GR',
  'description': 'Keep the Greek contributor instructions available.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_instructions_gr'},
 {'id': 'project_component_legal_en',
  'title': 'Legal Document EN',
  'description': 'Keep the English legal disclaimer document available.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_legal_en'},
 {'id': 'project_component_legal_gr',
  'title': 'Legal Document GR',
  'description': 'Keep the Greek legal disclaimer document available.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_legal_gr'},
 {'id': 'project_component_termux_book_en',
  'title': 'Termux Book EN',
  'description': 'Keep the English Master Termux PDF available.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_termux_book_en'},
 {'id': 'project_component_termux_book_gr',
  'title': 'Termux Book GR',
  'description': 'Keep the Greek Master Termux PDF available.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_termux_book_gr'},
 {'id': 'project_component_settings_py',
  'title': 'Settings Core',
  'description': 'Keep Settings.py available in the DedSec Project.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_settings_py'},
 {'id': 'project_component_butsystem_py',
  'title': 'ButSystem Core',
  'description': 'Keep ButSystem.py available in the DedSec Project.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_butsystem_py'},
 {'id': 'project_component_dedsec_market_py',
  'title': 'DedSec Market Core',
  'description': 'Keep DedSec Market.py available in the DedSec Project.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_dedsec_market_py'},
 {'id': 'project_component_extra_content_py',
  'title': 'Extra Content Core',
  'description': 'Keep Extra Content.py available in the DedSec Project.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_extra_content_py'},
 {'id': 'project_component_dev_dead_switch',
  'title': 'Dead Switch',
  'description': 'Keep Dead Switch.py available inside Developer Base.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_dev_dead_switch'},
 {'id': 'project_component_dev_devices_finder',
  'title': 'Devices Finder',
  'description': 'Keep Devices Finder.py available inside Developer Base.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_dev_devices_finder'},
 {'id': 'project_component_dev_file_converter',
  'title': 'File Converter',
  'description': 'Keep File Converter.py available inside Developer Base.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_dev_file_converter'},
 {'id': 'project_component_dev_file_type_checker',
  'title': 'File Type Checker',
  'description': 'Keep File Type Checker.py available inside Developer Base.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_dev_file_type_checker'},
 {'id': 'project_component_dev_free_internet',
  'title': 'Free Internet',
  'description': 'Keep Free Internet.py available inside Developer Base.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_dev_free_internet'},
 {'id': 'project_component_dev_mobile_desktop',
  'title': 'Mobile Desktop',
  'description': 'Keep Mobile Desktop.py available inside Developer Base.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_dev_mobile_desktop'},
 {'id': 'project_component_dev_mobile_developer_setup',
  'title': 'Mobile Developer Setup',
  'description': 'Keep Mobile Developer Setup.py available inside Developer Base.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_dev_mobile_developer_setup'},
 {'id': 'project_component_dev_simple_websites_creator',
  'title': 'Simple Websites Creator',
  'description': 'Keep Simple Websites Creator.py available inside Developer Base.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_dev_simple_websites_creator'},
 {'id': 'project_component_dev_smart_notes',
  'title': 'Smart Notes',
  'description': 'Keep Smart Notes.py available inside Developer Base.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_dev_smart_notes'},
 {'id': 'project_component_dev_tree_explorer',
  'title': 'Tree Explorer',
  'description': 'Keep Tree Explorer.py available inside Developer Base.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_dev_tree_explorer'},
 {'id': 'project_component_net_bug_hunter',
  'title': 'Bug Hunter',
  'description': 'Keep Bug Hunter.py available inside Network Tools.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_net_bug_hunter'},
 {'id': 'project_component_net_connections',
  'title': 'Connections',
  'description': 'Keep Connections.py available inside Network Tools.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_net_connections'},
 {'id': 'project_component_net_dark',
  'title': 'Dark',
  'description': 'Keep Dark.py available inside Network Tools.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_net_dark'},
 {'id': 'project_component_net_dedsec_s_network',
  'title': "DedSec's Network",
  'description': "Keep DedSec's Network.py available inside Network Tools.",
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_net_dedsec_s_network'},
 {'id': 'project_component_net_digital_footprint_finder',
  'title': 'Digital Footprint Finder',
  'description': 'Keep Digital Footprint Finder.py available inside Network Tools.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_net_digital_footprint_finder'},
 {'id': 'project_component_net_link_shield',
  'title': 'Link Shield',
  'description': 'Keep Link Shield.py available inside Network Tools.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_net_link_shield'},
 {'id': 'project_component_net_masker',
  'title': 'Masker',
  'description': 'Keep Masker.py available inside Network Tools.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_net_masker'},
 {'id': 'project_component_net_qr_code_generator',
  'title': 'QR Code Generator',
  'description': 'Keep QR Code Generator.py available inside Network Tools.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_net_qr_code_generator'},
 {'id': 'project_component_net_sod',
  'title': 'Sod',
  'description': 'Keep Sod.py available inside Network Tools.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_net_sod'},
 {'id': 'project_component_net_store_scrapper',
  'title': 'Store Scrapper',
  'description': 'Keep Store Scrapper.py available inside Network Tools.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_net_store_scrapper'},
 {'id': 'project_component_game_buzz',
  'title': 'Buzz',
  'description': 'Keep Buzz.py available inside Games.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_game_buzz'},
 {'id': 'project_component_game_ctf_god',
  'title': 'CTF God',
  'description': 'Keep CTF God.py available inside Games.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_game_ctf_god'},
 {'id': 'project_component_game_detective',
  'title': 'Detective',
  'description': 'Keep Detective.py available inside Games.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_game_detective'},
 {'id': 'project_component_game_tamagotchi',
  'title': 'Tamagotchi',
  'description': 'Keep Tamagotchi.py available inside Games.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_game_tamagotchi'},
 {'id': 'project_component_game_terminal_arcade',
  'title': 'Terminal Arcade',
  'description': 'Keep Terminal Arcade.py available inside Games.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_game_terminal_arcade'},
 {'id': 'project_component_other_android_app_launcher',
  'title': 'Android App Launcher',
  'description': 'Keep Android App Launcher.py available inside Other Tools.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_other_android_app_launcher'},
 {'id': 'project_component_other_loading_screen',
  'title': 'Loading Screen',
  'description': 'Keep Loading Screen.py available inside Other Tools.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_other_loading_screen'},
 {'id': 'project_component_other_password_master',
  'title': 'Password Master',
  'description': 'Keep Password Master.py available inside Other Tools.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_other_password_master'},
 {'id': 'project_component_other_termux_backup_restore',
  'title': 'Termux Backup Restore',
  'description': 'Keep Termux Backup Restore.py available inside Other Tools.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_other_termux_backup_restore'},
 {'id': 'project_component_other_termux_repair_wizard',
  'title': 'Termux Repair Wizard',
  'description': 'Keep Termux Repair Wizard.py available inside Other Tools.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_other_termux_repair_wizard'},
 {'id': 'project_component_fake_fake_apple_icloud_page',
  'title': 'Fake Apple iCloud Page',
  'description': 'Keep Fake Apple iCloud Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_apple_icloud_page'},
 {'id': 'project_component_fake_fake_discord_nitro_page',
  'title': 'Fake Discord Nitro Page',
  'description': 'Keep Fake Discord Nitro Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_discord_nitro_page'},
 {'id': 'project_component_fake_fake_epic_games_page',
  'title': 'Fake Epic Games Page',
  'description': 'Keep Fake Epic Games Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_epic_games_page'},
 {'id': 'project_component_fake_fake_facebook_friends_page',
  'title': 'Fake Facebook Friends Page',
  'description': 'Keep Fake Facebook Friends Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_facebook_friends_page'},
 {'id': 'project_component_fake_fake_free_robux_page',
  'title': 'Fake Free Robux Page',
  'description': 'Keep Fake Free Robux Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_free_robux_page'},
 {'id': 'project_component_fake_fake_github_pro_page',
  'title': 'Fake GitHub Pro Page',
  'description': 'Keep Fake GitHub Pro Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_github_pro_page'},
 {'id': 'project_component_fake_fake_google_free_money_page',
  'title': 'Fake Google Free Money Page',
  'description': 'Keep Fake Google Free Money Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_google_free_money_page'},
 {'id': 'project_component_fake_fake_instagram_followers_page',
  'title': 'Fake Instagram Followers Page',
  'description': 'Keep Fake Instagram Followers Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_instagram_followers_page'},
 {'id': 'project_component_fake_fake_metamask_page',
  'title': 'Fake MetaMask Page',
  'description': 'Keep Fake MetaMask Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_metamask_page'},
 {'id': 'project_component_fake_fake_microsoft_365_page',
  'title': 'Fake Microsoft 365 Page',
  'description': 'Keep Fake Microsoft 365 Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_microsoft_365_page'},
 {'id': 'project_component_fake_fake_onlyfans_page',
  'title': 'Fake OnlyFans Page',
  'description': 'Keep Fake OnlyFans Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_onlyfans_page'},
 {'id': 'project_component_fake_fake_paypal_page',
  'title': 'Fake PayPal Page',
  'description': 'Keep Fake PayPal Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_paypal_page'},
 {'id': 'project_component_fake_fake_pinterest_pro_page',
  'title': 'Fake Pinterest Pro Page',
  'description': 'Keep Fake Pinterest Pro Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_pinterest_pro_page'},
 {'id': 'project_component_fake_fake_playstation_network_page',
  'title': 'Fake PlayStation Network Page',
  'description': 'Keep Fake PlayStation Network Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_playstation_network_page'},
 {'id': 'project_component_fake_fake_reddit_karma_page',
  'title': 'Fake Reddit Karma Page',
  'description': 'Keep Fake Reddit Karma Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_reddit_karma_page'},
 {'id': 'project_component_fake_fake_snapchat_friends_page',
  'title': 'Fake Snapchat Friends Page',
  'description': 'Keep Fake Snapchat Friends Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_snapchat_friends_page'},
 {'id': 'project_component_fake_fake_steam_games_page',
  'title': 'Fake Steam Games Page',
  'description': 'Keep Fake Steam Games Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_steam_games_page'},
 {'id': 'project_component_fake_fake_steam_wallet_page',
  'title': 'Fake Steam Wallet Page',
  'description': 'Keep Fake Steam Wallet Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_steam_wallet_page'},
 {'id': 'project_component_fake_fake_tik_tok_followers_page',
  'title': 'Fake Tik Tok Followers Page',
  'description': 'Keep Fake Tik Tok Followers Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_tik_tok_followers_page'},
 {'id': 'project_component_fake_fake_trust_wallet_page',
  'title': 'Fake Trust Wallet Page',
  'description': 'Keep Fake Trust Wallet Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_trust_wallet_page'},
 {'id': 'project_component_fake_fake_twitch_subs_page',
  'title': 'Fake Twitch Subs Page',
  'description': 'Keep Fake Twitch Subs Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_twitch_subs_page'},
 {'id': 'project_component_fake_fake_twitter_followers_page',
  'title': 'Fake Twitter Followers Page',
  'description': 'Keep Fake Twitter Followers Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_twitter_followers_page'},
 {'id': 'project_component_fake_fake_what_s_up_dude_page',
  'title': "Fake What's Up Dude Page",
  'description': "Keep Fake What's Up Dude Page.py available inside Fake Pages.",
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_what_s_up_dude_page'},
 {'id': 'project_component_fake_fake_xbox_live_page',
  'title': 'Fake Xbox Live Page',
  'description': 'Keep Fake Xbox Live Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_xbox_live_page'},
 {'id': 'project_component_fake_fake_youtube_subscribers_page',
  'title': 'Fake YouTube Subscribers Page',
  'description': 'Keep Fake YouTube Subscribers Page.py available inside Fake Pages.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_fake_fake_youtube_subscribers_page'},
 {'id': 'project_component_capture_fake_back_camera_page',
  'title': 'Fake Back Camera Page',
  'description': 'Keep Fake Back Camera Page.py available inside Personal Information Capture.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_capture_fake_back_camera_page'},
 {'id': 'project_component_capture_fake_back_camera_video_page',
  'title': 'Fake Back Camera Video Page',
  'description': 'Keep Fake Back Camera Video Page.py available inside Personal Information Capture.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_capture_fake_back_camera_video_page'},
 {'id': 'project_component_capture_fake_card_details_page',
  'title': 'Fake Card Details Page',
  'description': 'Keep Fake Card Details Page.py available inside Personal Information Capture.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_capture_fake_card_details_page'},
 {'id': 'project_component_capture_fake_chrome_verification_page',
  'title': 'Fake Chrome Verification Page',
  'description': 'Keep Fake Chrome Verification Page.py available inside Personal Information Capture.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_capture_fake_chrome_verification_page'},
 {'id': 'project_component_capture_fake_data_grabber_page',
  'title': 'Fake Data Grabber Page',
  'description': 'Keep Fake Data Grabber Page.py available inside Personal Information Capture.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_capture_fake_data_grabber_page'},
 {'id': 'project_component_capture_fake_discord_verification_page',
  'title': 'Fake Discord Verification Page',
  'description': 'Keep Fake Discord Verification Page.py available inside Personal Information Capture.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_capture_fake_discord_verification_page'},
 {'id': 'project_component_capture_fake_facebook_verification_page',
  'title': 'Fake Facebook Verification Page',
  'description': 'Keep Fake Facebook Verification Page.py available inside Personal Information Capture.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_capture_fake_facebook_verification_page'},
 {'id': 'project_component_capture_fake_front_camera_page',
  'title': 'Fake Front Camera Page',
  'description': 'Keep Fake Front Camera Page.py available inside Personal Information Capture.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_capture_fake_front_camera_page'},
 {'id': 'project_component_capture_fake_front_camera_video_page',
  'title': 'Fake Front Camera Video Page',
  'description': 'Keep Fake Front Camera Video Page.py available inside Personal Information Capture.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_capture_fake_front_camera_video_page'},
 {'id': 'project_component_capture_fake_google_location_page',
  'title': 'Fake Google Location Page',
  'description': 'Keep Fake Google Location Page.py available inside Personal Information Capture.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_capture_fake_google_location_page'},
 {'id': 'project_component_capture_fake_instagram_verification_page',
  'title': 'Fake Instagram Verification Page',
  'description': 'Keep Fake Instagram Verification Page.py available inside Personal Information Capture.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_capture_fake_instagram_verification_page'},
 {'id': 'project_component_capture_fake_location_page',
  'title': 'Fake Location Page',
  'description': 'Keep Fake Location Page.py available inside Personal Information Capture.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_capture_fake_location_page'},
 {'id': 'project_component_capture_fake_microphone_page',
  'title': 'Fake Microphone Page',
  'description': 'Keep Fake Microphone Page.py available inside Personal Information Capture.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_capture_fake_microphone_page'},
 {'id': 'project_component_capture_fake_onlyfans_verification_page',
  'title': 'Fake OnlyFans Verification Page',
  'description': 'Keep Fake OnlyFans Verification Page.py available inside Personal Information Capture.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_capture_fake_onlyfans_verification_page'},
 {'id': 'project_component_capture_fake_steam_verification_page',
  'title': 'Fake Steam Verification Page',
  'description': 'Keep Fake Steam Verification Page.py available inside Personal Information Capture.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_capture_fake_steam_verification_page'},
 {'id': 'project_component_capture_fake_twitch_verification_page',
  'title': 'Fake Twitch Verification Page',
  'description': 'Keep Fake Twitch Verification Page.py available inside Personal Information Capture.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_capture_fake_twitch_verification_page'},
 {'id': 'project_component_capture_fake_youtube_verification_page',
  'title': 'Fake YouTube Verification Page',
  'description': 'Keep Fake YouTube Verification Page.py available inside Personal Information Capture.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_capture_fake_youtube_verification_page'},
 {'id': 'project_component_extra_images',
  'title': 'Image Archive',
  'description': 'Keep the Extra Content image archive available.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_extra_images'},
 {'id': 'project_component_slots_demos',
  'title': 'Slots Demo Archive',
  'description': 'Keep the Slots Pages Demos folder available.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_slots_demos'},
 {'id': 'project_component_unused_scripts_archive',
  'title': 'Unused Script Archive',
  'description': 'Keep the Unused Scripts archive available.',
  'hidden': True,
  'check': 'context_truthy',
  'key': 'component_unused_scripts_archive'},
 {'id': 'project_component_greek_version_folder',
  'title': 'Greek Version Vault',
  'description': 'Keep the Greek version folder available.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_greek_version_folder'},
 {'id': 'project_component_greek_settings',
  'title': 'Greek Settings',
  'description': 'Keep the Greek Settings.py available.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_greek_settings'},
 {'id': 'project_component_greek_butsystem',
  'title': 'Greek ButSystem',
  'description': 'Keep the Greek ButSystem.py available.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_greek_butsystem'},
 {'id': 'project_component_greek_dedsec_market',
  'title': 'Greek DedSec Market',
  'description': 'Keep the Greek DedSec Market.py available.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_greek_dedsec_market'},
 {'id': 'project_component_greek_extra_content',
  'title': 'Greek Extra Content',
  'description': 'Keep the Greek Extra Content.py available.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'component_greek_extra_content'},
 {'id': 'sponsor_access_checked',
  'title': 'Sponsor Gate Scanner',
  'description': 'Check Sponsors-Only access from the sponsor menu or background checker.',
  'hidden': False,
  'check': 'event_at_least',
  'event': 'sponsor_access_checks',
  'value': 1},
 {'id': 'sponsor_3_access_verified',
  'title': '$3 Access Verified',
  'description': 'Verify access to the Sponsors-Only $3 tier repository.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'sponsor_3_access'},
 {'id': 'sponsor_9_access_verified',
  'title': '$9 Access Verified',
  'description': 'Verify access to the Sponsors-Only $9 tier repository.',
  'hidden': False,
  'check': 'context_truthy',
  'key': 'sponsor_9_access'},
 {'id': 'sponsor_both_access_verified',
  'title': 'Dual Sponsor Access',
  'description': 'Verify access to both sponsor tier repositories.',
  'hidden': True,
  'check': 'all_truthy',
  'keys': ['sponsor_3_access', 'sponsor_9_access']},
 {'id': 'sponsor_3_script_cache',
  'title': '$3 Script Cache',
  'description': 'Have at least 5 Python files in the local $3 sponsor tier folder.',
  'hidden': False,
  'check': 'context_at_least',
  'key': 'sponsor_3_python_count',
  'value': 5},
 {'id': 'sponsor_3_script_armory',
  'title': '$3 Script Armory',
  'description': 'Have at least 15 Python files in the local $3 sponsor tier folder.',
  'hidden': True,
  'check': 'context_at_least',
  'key': 'sponsor_3_python_count',
  'value': 15},
 {'id': 'sponsor_9_script_cache',
  'title': '$9 Script Cache',
  'description': 'Have at least 2 Python files in the local $9 sponsor tier folder.',
  'hidden': False,
  'check': 'context_at_least',
  'key': 'sponsor_9_python_count',
  'value': 2},
 {'id': 'sponsor_9_script_armory',
  'title': '$9 Script Armory',
  'description': 'Have at least 5 Python files in the local $9 sponsor tier folder.',
  'hidden': True,
  'check': 'context_at_least',
  'key': 'sponsor_9_python_count',
  'value': 5},
 {'id': 'sponsor_total_collection',
  'title': 'Sponsor Collection',
  'description': 'Have at least 20 sponsor Python files available locally across both tiers.',
  'hidden': True,
  'check': 'context_at_least',
  'key': 'sponsor_total_python_count',
  'value': 20},
 {'id': 'sponsor_dlc_complete',
  'title': 'Sponsor DLC Complete',
  'description': 'Have both sponsor tiers available locally and access verified.',
  'hidden': True,
  'check': 'all_truthy',
  'keys': ['sponsor_3_local', 'sponsor_9_local', 'sponsor_3_access', 'sponsor_9_access']},
 {'id': 'daemon_five_starts',
  'title': 'Daemon Survivor',
  'description': 'Let the achievements daemon start at least 5 times.',
  'hidden': True,
  'check': 'event_at_least',
  'event': 'daemon_starts',
  'value': 5},
 {'id': 'watchtower_500',
  'title': 'Watchtower 500',
  'description': 'Let the background checker complete 500 silent scans.',
  'hidden': True,
  'check': 'event_at_least',
  'event': 'background_checks',
  'value': 500}])

# Extra persistence achievements for the self-healing background engine.
# Future updates: append more achievements below this block, but do not rename
# these IDs because already-earned trophies are saved by ID in .dedsec_achievements.json.
ACHIEVEMENTS_DEFINITIONS.extend([
    {
        "id": "guardian_process",
        "title": "Guardian Process",
        "description": "Keep the watchdog alive so achievements restart if the checker crashes.",
        "hidden": False,
        "check": "event_at_least",
        "event": "watchdog_starts",
        "value": 1,
    },
    {
        "id": "unbreakable_watch",
        "title": "Unbreakable Watch",
        "description": "Let the watchdog recover or verify the checker 25 times while Termux is open.",
        "hidden": False,
        "check": "event_at_least",
        "event": "watchdog_pulses",
        "value": 25,
    },
    {
        "id": "still_watching",
        "title": "Still Watching",
        "description": "Let the watchdog recover or verify the checker 100 times while Termux is open.",
        "hidden": True,
        "check": "event_at_least",
        "event": "watchdog_pulses",
        "value": 100,
    },
    {
        "id": "self_healing_engine",
        "title": "Self-Healing Engine",
        "description": "Have the watchdog restart the checker after a crash or manual kill.",
        "hidden": True,
        "check": "event_at_least",
        "event": "watchdog_restarts",
        "value": 1,
    },
    {
        "id": "watcher_marathon",
        "title": "Watcher Marathon",
        "description": "Keep the achievement watchdog alive for 500 pulses.",
        "hidden": True,
        "check": "event_at_least",
        "event": "watchdog_pulses",
        "value": 500,
    },
    {
        "id": "constant_guard_installed",
        "title": "Constant Guard",
        "description": "Let Settings.py install and repair the always-on achievement guard.",
        "hidden": False,
        "check": "event_at_least",
        "event": "constant_ensure",
        "value": 1,
    },
    {
        "id": "constant_guard_25",
        "title": "Still Online",
        "description": "Let the constant guard verify the achievement engine 25 times.",
        "hidden": False,
        "check": "event_at_least",
        "event": "constant_ensure",
        "value": 25,
    },
    {
        "id": "constant_guard_100",
        "title": "Always Watching",
        "description": "Let the constant guard verify the achievement engine 100 times.",
        "hidden": True,
        "check": "event_at_least",
        "event": "constant_ensure",
        "value": 100,
    },
    {
        "id": "constant_guard_500",
        "title": "No Sleep Protocol",
        "description": "Let the constant guard verify the achievement engine 500 times.",
        "hidden": True,
        "check": "event_at_least",
        "event": "constant_ensure",
        "value": 500,
    },
    {
        "id": "daemon_stale_repair",
        "title": "Daemon Repaired",
        "description": "Let constant mode repair a stale achievement daemon.",
        "hidden": True,
        "check": "event_at_least",
        "event": "daemon_stale_restarts",
        "value": 1,
    },
    {
        "id": "watchdog_stale_repair",
        "title": "Watchdog Repaired",
        "description": "Let constant mode repair a stale achievement watchdog.",
        "hidden": True,
        "check": "event_at_least",
        "event": "watchdog_stale_restarts",
        "value": 1,
    },
])



ACHIEVEMENTS_DEFINITIONS.extend([
    {
        "id": "notification_first_ping",
        "title": "Trophy Ping",
        "description": "Receive your first Termux notification for an unlocked achievement.",
        "hidden": False,
        "check": "event_at_least",
        "event": "notification_success",
        "value": 1,
    },
    {
        "id": "notification_chain_10",
        "title": "Notification Chain",
        "description": "Receive 10 achievement unlock notifications through Termux:API.",
        "hidden": False,
        "check": "event_at_least",
        "event": "notification_success",
        "value": 10,
    },
    {
        "id": "notification_broadcast_50",
        "title": "Trophy Broadcast",
        "description": "Receive 50 achievement unlock notifications through Termux:API.",
        "hidden": True,
        "check": "event_at_least",
        "event": "notification_success",
        "value": 50,
    },
])


def achievements_normalize_trophy_tier(value):
    value = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "beginner": "beginner",
        "begginer": "beginner",
        "starter": "beginner",
        "easy": "easy",
        "normal": "normal",
        "medium": "normal",
        "hard": "hard",
        "veryhard": "very_hard",
        "very_hard": "very_hard",
        "very": "very_hard",
        "god": "godlike",
        "god_like": "godlike",
        "godlike": "godlike",
    }
    return aliases.get(value, "normal")


def achievements_trophy_tier_label(tier):
    tier = achievements_normalize_trophy_tier(tier)
    return _(ACHIEVEMENTS_TROPHY_TIER_LABELS.get(tier, "Normal"))


def achievements_trophy_tier_points(tier):
    tier = achievements_normalize_trophy_tier(tier)
    return int(ACHIEVEMENTS_TROPHY_TIER_POINTS.get(tier, 20))


def achievements_auto_trophy_tier(achievement):
    """Assigns a stable PS3-style difficulty rank to older achievements.

    FUTURE UPDATE WARNING: append new trophies with an explicit difficulty when possible.
    Do not remove this automatic mapper, because older achievement IDs rely on it to
    keep a stable Beginner/Easy/Normal/Hard/Very Hard/Godlike rank without rewriting
    the saved unlock data.
    """
    existing = achievement.get("difficulty") or achievement.get("tier") or achievement.get("rank")
    if existing:
        return achievements_normalize_trophy_tier(existing)

    achievement_id = str(achievement.get("id", "")).lower()
    title = str(achievement.get("title", "")).lower()
    description = str(achievement.get("description", "")).lower()
    category = str(achievement.get("category", "")).lower()
    check = str(achievement.get("check", "")).lower()
    key = str(achievement.get("key", "")).lower()
    event = str(achievement.get("event", "")).lower()
    text = " ".join([achievement_id, title, description, category, key, event])
    title_id = " ".join([achievement_id, title])
    try:
        value = float(achievement.get("value", 0) or 0)
    except Exception:
        value = 0.0
    hidden = bool(achievement.get("hidden"))

    if check == "always" or achievement.get("condition") in ("always", "achievement_menu_opened"):
        return "beginner"
    if not hidden and value <= 1 and check in ("event_at_least", "context_truthy", "context_equals"):
        return "beginner"
    if not hidden and value <= 3 and check == "event_at_least":
        return "beginner"

    if any(word in title_id for word in ("godlike", "legend", "full_dedsec_project", "full dedsec project", "watcher_marathon", "trophy_broadcast")):
        return "godlike"
    if "dedsec_project_full" in achievement_id or "full_sponsor_access" in achievement_id:
        return "godlike"
    if any(word in title_id for word in ("fortress", "marathon", "broadcast", "complete", "very hard", "both tiers")):
        return "very_hard"
    if value >= 500:
        return "godlike"
    if value >= 100:
        return "very_hard"
    if value >= 50:
        return "hard"
    if value >= 20:
        return "normal" if not hidden else "hard"
    if value >= 10:
        return "easy" if not hidden else "normal"

    if "sponsor" in text:
        if "9" in achievement_id or "tier_nine" in achievement_id:
            return "very_hard"
        return "hard"
    if any(word in title_id for word in ("master", "veteran", "chain", "vault")):
        return "hard" if hidden else "normal"
    if hidden:
        return "normal"
    return "easy"


def achievements_apply_trophy_tiers():
    seen_ids = set()
    stable = []
    for achievement in ACHIEVEMENTS_DEFINITIONS:
        achievement_id = achievement.get("id")
        if not achievement_id or achievement_id in seen_ids:
            continue
        seen_ids.add(achievement_id)
        tier = achievements_auto_trophy_tier(achievement)
        achievement["difficulty"] = tier
        achievement["points"] = achievements_trophy_tier_points(tier)
        stable.append(achievement)
    ACHIEVEMENTS_DEFINITIONS[:] = stable




def achievements_milestone_difficulty(index, total):
    if index <= 0:
        return "beginner"
    if index == 1:
        return "easy"
    if index == 2:
        return "normal"
    if index == 3:
        return "hard"
    if index == 4:
        return "very_hard"
    return "godlike"


def achievements_add_event_milestones(event_name, title_prefix, description_unit, values):
    for index, value in enumerate(values):
        difficulty = achievements_milestone_difficulty(index, len(values))
        ACHIEVEMENTS_DEFINITIONS.append({
            "id": "milestone_event_" + event_name + "_" + str(value),
            "title": title_prefix + " " + str(value),
            "description": "Reach " + str(value) + " " + description_unit + ".",
            "hidden": difficulty in ("hard", "very_hard", "godlike"),
            "check": "event_at_least",
            "event": event_name,
            "value": value,
            "difficulty": difficulty,
        })


def achievements_add_context_milestones(key, title_prefix, description_unit, values):
    for index, value in enumerate(values):
        difficulty = achievements_milestone_difficulty(index, len(values))
        ACHIEVEMENTS_DEFINITIONS.append({
            "id": "milestone_context_" + key + "_" + str(value),
            "title": title_prefix + " " + str(value),
            "description": "Reach " + str(value) + " " + description_unit + ".",
            "hidden": difficulty in ("hard", "very_hard", "godlike"),
            "check": "context_at_least",
            "key": key,
            "value": value,
            "difficulty": difficulty,
        })


# Extra milestone trophies keep the system rich across every DedSec Project area.
# Future updates may append more milestones, but must not remove or rename these IDs.
achievements_add_event_milestones("settings_started", "Settings Sessions", "Settings.py launches", [1, 5, 10, 25, 50, 100])
achievements_add_event_milestones("settings_actions", "Menu Actions", "settings menu actions", [5, 25, 50, 100, 250, 500])
achievements_add_event_milestones("background_checks", "Background Scans", "background achievement scans", [5, 25, 100, 250, 500, 1000])
achievements_add_event_milestones("watchdog_pulses", "Watchdog Pulses", "watchdog pulses", [5, 25, 100, 250, 500, 1000])
achievements_add_event_milestones("constant_ensure", "Constant Repairs", "constant checker repair checks", [5, 25, 100, 250, 500, 1000])
achievements_add_event_milestones("manual_checks", "Manual Checks", "manual achievement checks", [1, 10, 25, 50, 100, 250])
achievements_add_event_milestones("achievement_log_opened", "Log Opens", "achievement log opens", [1, 5, 10, 25, 50, 100])
achievements_add_event_milestones("notification_success", "Notification Pings", "successful Termux:API notifications", [1, 5, 10, 25, 50, 100])

achievements_add_context_milestones("project_component_count", "Project Components", "tracked DedSec Project components", [10, 25, 50, 75, 95])
achievements_add_context_milestones("python_file_count", "Python Files", "Python files in the DedSec workspace", [10, 25, 50, 100, 200])
achievements_add_context_milestones("runnable_file_count", "Runnable Files", "runnable Python or shell files", [10, 25, 50, 100, 200])
achievements_add_context_milestones("markdown_file_count", "Markdown Files", "Markdown documentation files", [5, 10, 25, 50, 100])
achievements_add_context_milestones("text_file_count", "Text Files", "text/database notes", [10, 25, 50, 100, 250])
achievements_add_context_milestones("usage_scan_count", "Usage Scans", "Termux usage scans", [1, 5, 10, 25, 50])
achievements_add_context_milestones("project_save_archives", "Legacy Saves", "DedSec Legacy save archives", [1, 3, 5, 7, 10])
achievements_add_context_milestones("sponsor_total_python_count", "Sponsor Scripts", "local sponsor Python scripts", [1, 5, 10, 25, 50])
achievements_add_context_milestones("settings_runtime_seconds", "Runtime Seconds", "tracked Settings.py runtime seconds", [600, 1800, 3600, 7200, 14400])

ACHIEVEMENTS_DEFINITIONS.extend([
    {
        "id": "score_250",
        "title": "Trophy Score 250",
        "description": "Earn at least 250 total trophy points.",
        "hidden": False,
        "check": "trophy_score_at_least",
        "value": 250,
        "difficulty": "beginner",
    },
    {
        "id": "score_500",
        "title": "Trophy Score 500",
        "description": "Earn at least 500 total trophy points.",
        "hidden": False,
        "check": "trophy_score_at_least",
        "value": 500,
        "difficulty": "easy",
    },
    {
        "id": "score_1000",
        "title": "Trophy Score 1000",
        "description": "Earn at least 1000 total trophy points.",
        "hidden": False,
        "check": "trophy_score_at_least",
        "value": 1000,
        "difficulty": "normal",
    },
    {
        "id": "score_2500",
        "title": "Trophy Score 2500",
        "description": "Earn at least 2500 total trophy points.",
        "hidden": True,
        "check": "trophy_score_at_least",
        "value": 2500,
        "difficulty": "hard",
    },
    {
        "id": "score_5000",
        "title": "Trophy Score 5000",
        "description": "Earn at least 5000 total trophy points.",
        "hidden": True,
        "check": "trophy_score_at_least",
        "value": 5000,
        "difficulty": "very_hard",
    },
    {
        "id": "score_10000",
        "title": "Trophy Score 10000",
        "description": "Earn at least 10000 total trophy points.",
        "hidden": True,
        "check": "trophy_score_at_least",
        "value": 10000,
        "difficulty": "godlike",
    },
])

ACHIEVEMENTS_DEFINITIONS.extend([
    {
        "id": "tier_beginner_collector_10",
        "title": "Beginner Trophies",
        "description": "Unlock 10 Beginner trophies.",
        "hidden": False,
        "check": "unlocked_tier_at_least",
        "tier": "beginner",
        "value": 10,
        "difficulty": "beginner",
    },
    {
        "id": "tier_easy_collector_15",
        "title": "Easy Trophies",
        "description": "Unlock 15 Easy trophies.",
        "hidden": False,
        "check": "unlocked_tier_at_least",
        "tier": "easy",
        "value": 15,
        "difficulty": "easy",
    },
    {
        "id": "tier_normal_collector_20",
        "title": "Normal Trophies",
        "description": "Unlock 20 Normal trophies.",
        "hidden": False,
        "check": "unlocked_tier_at_least",
        "tier": "normal",
        "value": 20,
        "difficulty": "normal",
    },
    {
        "id": "tier_hard_collector_15",
        "title": "Hard Trophies",
        "description": "Unlock 15 Hard trophies.",
        "hidden": True,
        "check": "unlocked_tier_at_least",
        "tier": "hard",
        "value": 15,
        "difficulty": "hard",
    },
    {
        "id": "tier_very_hard_collector_10",
        "title": "Very Hard Trophies",
        "description": "Unlock 10 Very Hard trophies.",
        "hidden": True,
        "check": "unlocked_tier_at_least",
        "tier": "very_hard",
        "value": 10,
        "difficulty": "very_hard",
    },
    {
        "id": "tier_godlike_collector_5",
        "title": "Godlike Trophies",
        "description": "Unlock 5 Godlike trophies.",
        "hidden": True,
        "check": "unlocked_tier_at_least",
        "tier": "godlike",
        "value": 5,
        "difficulty": "godlike",
    },
])

# Manual test trophies for checking every difficulty rank and Termux:API notifications.
# Keep these IDs/events stable forever; they are a safe diagnostic feature and should
# not affect normal DedSec Project progression.
for test_trophy in ACHIEVEMENTS_TEST_TROPHIES:
    ACHIEVEMENTS_DEFINITIONS.append({
        "id": test_trophy["id"],
        "title": test_trophy["title"],
        "description": test_trophy["description"],
        "hidden": False,
        "check": "event_at_least",
        "event": test_trophy["event"],
        "value": 1,
        "difficulty": test_trophy["difficulty"],
        "category": "achievement_tests",
    })

achievements_apply_trophy_tiers()
ACHIEVEMENTS_BY_ID = {achievement.get("id"): achievement for achievement in ACHIEVEMENTS_DEFINITIONS if achievement.get("id")}


def achievements_default_state():
    return {
        "version": 3,
        "background_enabled": True,
        "events": {},
        "seen_languages": [],
        "unlocked": {},
        "last_checked": 0,
        "last_daemon_heartbeat": 0,
        "last_watchdog_heartbeat": 0,
    }


def achievements_load_state():
    state = achievements_default_state()
    try:
        if os.path.exists(ACHIEVEMENTS_STATE_PATH):
            with open(ACHIEVEMENTS_STATE_PATH, "r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                state.update(loaded)
    except Exception:
        pass

    if not isinstance(state.get("events"), dict):
        state["events"] = {}
    if not isinstance(state.get("seen_languages"), list):
        state["seen_languages"] = []
    if not isinstance(state.get("unlocked"), dict):
        state["unlocked"] = {}
    if "background_enabled" not in state:
        state["background_enabled"] = True
    return state


def achievements_save_state(state):
    try:
        os.makedirs(os.path.dirname(ACHIEVEMENTS_STATE_PATH), exist_ok=True)
        with open(ACHIEVEMENTS_STATE_PATH, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=4, ensure_ascii=False)
    except Exception:
        pass


def achievements_log(message):
    try:
        with open(ACHIEVEMENTS_LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(format_timestamp(time.time()) + " - " + str(message) + "\n")
    except Exception:
        pass


def achievements_record_event(event_name, amount=1):
    state = achievements_load_state()
    events = state.setdefault("events", {})
    try:
        events[event_name] = int(events.get(event_name, 0)) + int(amount)
    except Exception:
        events[event_name] = int(amount)
    events["last_event_at"] = int(time.time())

    language = load_language_preference() or get_current_display_language() or "english"
    if language not in state.setdefault("seen_languages", []):
        state["seen_languages"].append(language)

    achievements_save_state(state)
    return state


def achievements_deduplicate_paths(paths):
    cleaned = []
    seen = set()
    for path in paths or []:
        if not path:
            continue
        try:
            path_abs = os.path.abspath(os.path.expanduser(str(path)))
        except Exception:
            continue
        if path_abs in seen:
            continue
        seen.add(path_abs)
        cleaned.append(path_abs)
    return cleaned


def achievements_project_root_from_cwd():
    """Return a DedSec project root only when the current folder is clearly inside it.

    Line-by-line review note: v8 scanned os.getcwd() directly. That could become
    very slow if the user opened Termux inside a huge folder like Downloads.
    Keep the always-on achievement checker light by only accepting cwd when it
    is inside the known DedSec project tree.
    """
    try:
        cwd = os.path.abspath(os.getcwd())
        known_roots = achievements_deduplicate_paths([
            ACHIEVEMENTS_PROJECT_ROOT,
            os.path.join(HOME_DIR, "DedSec"),
            os.path.dirname(ENGLISH_BASE_PATH),
            ENGLISH_BASE_PATH,
        ])
        for root in known_roots:
            if cwd == root or cwd.startswith(root + os.sep):
                return root if os.path.basename(root).lower() != "scripts" else os.path.dirname(root)
        parts = cwd.split(os.sep)
        for index, part in enumerate(parts):
            if part.lower() == "dedsec":
                candidate = os.sep.join(parts[:index + 1]) or os.sep
                if candidate.startswith(HOME_DIR):
                    return candidate
    except Exception:
        pass
    return None


def achievements_safe_scan_roots(extra_roots=None, include_sponsors=True):
    """Small, safe root list for the constant background checker.

    Future updates must avoid full-device scans here. The daemon runs forever,
    so scanning /storage/emulated/0, /sdcard, HOME, or random cwd folders can
    drain battery and make Termux feel frozen.
    """
    roots = [
        ACHIEVEMENTS_PROJECT_ROOT,
        os.path.join(HOME_DIR, "DedSec"),
        os.path.dirname(ENGLISH_BASE_PATH),
        ENGLISH_BASE_PATH,
    ]
    cwd_project = achievements_project_root_from_cwd()
    if cwd_project:
        roots.append(cwd_project)
    if include_sponsors:
        try:
            roots.append(SPONSORS_ROOT_PATH)
            for tier_key in SPONSORS_TIERS.keys():
                preferred = get_sponsors_preferred_path(tier_key)
                root_path = get_sponsors_tier_root_path(tier_key)
                if preferred:
                    roots.append(preferred)
                if root_path:
                    roots.append(root_path)
        except Exception:
            pass
    if extra_roots:
        roots.extend(extra_roots)
    return [root for root in achievements_deduplicate_paths(roots) if os.path.isdir(root)]


def achievements_count_files(roots, extensions=None, executable_only=False, limit=ACHIEVEMENTS_FILE_SCAN_LIMIT):
    count = 0
    seen = set()
    extensions = tuple(extensions or [])
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        root_abs = os.path.abspath(root)
        if root_abs in seen:
            continue
        seen.add(root_abs)
        for current_root, dirnames, filenames in os.walk(root_abs, topdown=True, onerror=lambda _e: None):
            dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in ("__pycache__", "node_modules", ".git")]
            for filename in filenames:
                if filename.startswith("."):
                    continue
                full_path = os.path.join(current_root, filename)
                if extensions and not filename.lower().endswith(extensions):
                    continue
                if executable_only and not (os.access(full_path, os.X_OK) or filename.endswith((".py", ".sh"))):
                    continue
                count += 1
                if count >= limit:
                    return count
    return count


def achievements_sponsor_tier_exists(tier_key):
    paths = []
    try:
        tier_key = str(tier_key)
        tier = SPONSORS_TIERS.get(tier_key, {})
        preferred = get_sponsors_preferred_path(tier_key)
        root_path = get_sponsors_tier_root_path(tier_key)
        if preferred:
            paths.append(preferred)
        if root_path:
            paths.append(root_path)
        root_name = tier.get("root_name")
        if root_name:
            paths.append(os.path.join(HOME_DIR, root_name))
        for old_name in tier.get("old_root_names", []):
            paths.append(os.path.join(HOME_DIR, old_name))
    except Exception:
        pass
    return any(os.path.isdir(path) for path in paths if path)


def achievements_sponsors_local_exists():
    paths = []
    try:
        for tier_key, tier in SPONSORS_TIERS.items():
            preferred = get_sponsors_preferred_path(tier_key)
            root_path = get_sponsors_tier_root_path(tier_key)
            if preferred:
                paths.append(preferred)
            if root_path:
                paths.append(root_path)
            root_name = tier.get("root_name")
            if root_name:
                paths.append(os.path.join(HOME_DIR, root_name))
        paths.extend([SPONSORS_ROOT_PATH, os.path.join(HOME_DIR, "DedSec Sponsors-Only Scripts")])
    except Exception:
        paths.append(SPONSORS_ROOT_PATH)
    return any(os.path.isdir(path) for path in paths if path)



def achievements_project_roots():
    """Returns likely DedSec project roots without expensive full-device scans."""
    return achievements_safe_scan_roots(include_sponsors=False)


def achievements_component_exists(component):
    relatives = component.get("relative_options") or [component.get("relative", "")]
    kind = component.get("kind", "file")
    for root in achievements_project_roots():
        for relative in relatives:
            if not relative:
                continue
            full_path = os.path.join(root, relative)
            if kind == "dir" and os.path.isdir(full_path):
                return True
            if kind != "dir" and os.path.isfile(full_path):
                return True
    return False


def achievements_project_component_context():
    context = {}
    category_counts = {}
    total = 0
    for component in ACHIEVEMENTS_PROJECT_COMPONENTS:
        component_id = component.get("id", "")
        exists = achievements_component_exists(component)
        context["component_" + component_id] = exists
        if exists:
            total += 1
            category = component.get("category", "project")
            category_counts[category] = int(category_counts.get(category, 0)) + 1
    context["project_component_count"] = total
    context["project_component_total"] = len(ACHIEVEMENTS_PROJECT_COMPONENTS)
    context["project_category_count"] = len([name for name, count in category_counts.items() if int(count or 0) > 0])
    for category, count in category_counts.items():
        safe_category = re.sub(r"[^a-zA-Z0-9_]+", "_", str(category)).strip("_").lower()
        context["category_" + safe_category + "_count"] = int(count or 0)
    return context


def achievements_sponsor_tier_roots(tier_key):
    paths = []
    try:
        tier_key = str(tier_key)
        tier = SPONSORS_TIERS.get(tier_key, {})
        preferred = get_sponsors_preferred_path(tier_key)
        root_path = get_sponsors_tier_root_path(tier_key)
        for candidate in (preferred, root_path, os.path.join(HOME_DIR, tier.get("root_name", ""))):
            if candidate:
                paths.append(candidate)
        for old_name in tier.get("old_root_names", []):
            paths.append(os.path.join(HOME_DIR, old_name))
    except Exception:
        pass
    seen = set()
    clean = []
    for path in paths:
        if not path:
            continue
        path = os.path.abspath(path)
        if path not in seen:
            seen.add(path)
            clean.append(path)
    return clean


def achievements_remember_sponsor_access(tier_key, has_access, message=""):
    """Caches sponsor access results so achievements can unlock even after the menu closes."""
    try:
        tier_key = str(tier_key)
        if tier_key not in SPONSORS_TIERS:
            return
        state = achievements_load_state()
        sponsor_access = state.setdefault("sponsor_access", {})
        sponsor_access[tier_key] = {
            "has_access": bool(has_access),
            "checked_at": time.time(),
            "message": str(message or "")[:300],
        }
        events = state.setdefault("events", {})
        events["sponsor_access_checks"] = int(events.get("sponsor_access_checks", 0)) + 1
        achievements_save_state(state)
    except Exception:
        pass


def achievements_maybe_refresh_sponsor_access(state):
    """Lightweight background sponsor check. It never installs packages and only refreshes every few hours."""
    now = time.time()
    sponsor_access = state.setdefault("sponsor_access", {})
    result = {}
    changed = False

    for tier_key in SPONSORS_TIER_ORDER:
        cached = sponsor_access.get(str(tier_key), {}) if isinstance(sponsor_access, dict) else {}
        local_access = achievements_sponsor_tier_exists(tier_key)
        result[str(tier_key)] = bool(local_access or cached.get("has_access"))

    if not (shutil.which("gh") and shutil.which("git")):
        return result
    if not github_auth_status():
        return result

    token = github_token_for_sponsors()
    if not token:
        return result

    for tier_key in SPONSORS_TIER_ORDER:
        tier_key = str(tier_key)
        cached = sponsor_access.get(tier_key, {}) if isinstance(sponsor_access, dict) else {}
        last_checked = float(cached.get("checked_at", 0) or 0)
        if now - last_checked < ACHIEVEMENTS_SPONSOR_ACCESS_REFRESH_SECONDS:
            continue
        config = get_sponsor_tier_config(tier_key)
        if not config:
            continue
        try:
            rc, out = run_sponsors_git_command(["ls-remote", config["git_url"], "HEAD"], token)
            has_access = rc == 0
            sponsor_access[tier_key] = {
                "has_access": bool(has_access),
                "checked_at": now,
                "message": (out or "")[:300],
            }
            result[tier_key] = bool(result.get(tier_key) or has_access)
            changed = True
        except Exception as error:
            sponsor_access[tier_key] = {
                "has_access": bool(result.get(tier_key)),
                "checked_at": now,
                "message": str(error)[:300],
            }
            changed = True

    if changed:
        events = state.setdefault("events", {})
        events["sponsor_access_checks"] = int(events.get("sponsor_access_checks", 0)) + 1
        achievements_save_state(state)
    return result

def achievements_network_config():
    try:
        config = network_load_config()
        return config if isinstance(config, dict) else {}
    except Exception:
        return {}


def achievements_network_enabled():
    config = achievements_network_config()
    return bool(config.get("tor_enabled") or config.get("vpn_enabled"))


def achievements_count_project_save_archives():
    count = 0
    try:
        if os.path.isdir(PROJECT_SAVE_DOWNLOADS_PATH):
            for filename in os.listdir(PROJECT_SAVE_DOWNLOADS_PATH):
                lower = filename.lower()
                if "dedsec" in lower and "save" in lower and lower.endswith(".zip"):
                    count += 1
    except Exception:
        pass
    return count


def achievements_build_context(state):
    stats = load_termux_usage_stats()
    script_roots = achievements_safe_scan_roots(include_sponsors=True)

    github_config = load_github_account_config()
    language = load_language_preference() or get_current_display_language() or "english"
    menu_style = get_current_menu_style()
    total_commands = int(stats.get("total_commands", 0) or 0)
    history_path = os.path.join(HOME_DIR, ".bash_history")
    zsh_history_path = os.path.join(HOME_DIR, ".zsh_history")
    if os.path.exists(history_path) or os.path.exists(zsh_history_path):
        total_commands = max(total_commands, summarize_bash_history()[0])

    totals = stats.get("totals") if isinstance(stats.get("totals"), dict) else {}
    language_counts = stats.get("language_counts") if isinstance(stats.get("language_counts"), dict) else {}
    folder_counts = stats.get("folder_counts") if isinstance(stats.get("folder_counts"), dict) else {}
    network_config = achievements_network_config()
    component_context = achievements_project_component_context()
    sponsor_access = achievements_maybe_refresh_sponsor_access(state)
    sponsor_3_roots = achievements_sponsor_tier_roots("3")
    sponsor_9_roots = achievements_sponsor_tier_roots("9")
    sponsor_3_python_count = achievements_count_files(sponsor_3_roots, extensions=(".py",), executable_only=False)
    sponsor_9_python_count = achievements_count_files(sponsor_9_roots, extensions=(".py",), executable_only=False)

    context = {
        "language": language,
        "menu_style": menu_style,
        "background_enabled": bool(state.get("background_enabled", True)),
        "last_daemon_heartbeat": float(state.get("last_daemon_heartbeat", 0) or 0),
        "github_connected": bool(github_config.get("connected") or github_config.get("username")),
        "github_username": github_config.get("username", ""),
        "usage_scan_count": int(stats.get("scan_count", 0) or 0),
        "settings_runtime_seconds": float(stats.get("settings_runtime_seconds", 0) or 0),
        "total_commands": total_commands,
        "python_file_count": achievements_count_files(script_roots, extensions=(".py",), executable_only=False),
        "runnable_file_count": achievements_count_files(script_roots, extensions=(".py", ".sh"), executable_only=True),
        "shell_file_count": achievements_count_files(script_roots, extensions=(".sh",), executable_only=False),
        "html_file_count": achievements_count_files(script_roots, extensions=(".html", ".htm"), executable_only=False),
        "css_file_count": achievements_count_files(script_roots, extensions=(".css",), executable_only=False),
        "js_file_count": achievements_count_files(script_roots, extensions=(".js",), executable_only=False),
        "json_file_count": achievements_count_files(script_roots, extensions=(".json",), executable_only=False),
        "language_type_count": len([name for name, value in language_counts.items() if int(value or 0) > 0]),
        "folder_type_count": len([name for name, value in folder_counts.items() if int(value or 0) > 0]),
        "files_created_total": int(totals.get("created", 0) or 0),
        "files_edited_total": int(totals.get("edited", 0) or 0),
        "files_deleted_total": int(totals.get("deleted", 0) or 0),
        "project_save_exists": os.path.exists(os.path.join(PROJECT_SAVE_DOWNLOADS_PATH, PROJECT_SAVE_ARCHIVE_NAME)),
        "project_save_archives": achievements_count_project_save_archives(),
        "sponsors_local": achievements_sponsors_local_exists(),
        "sponsor_3_local": achievements_sponsor_tier_exists("3"),
        "sponsor_9_local": achievements_sponsor_tier_exists("9"),
        "sponsor_3_access": bool(sponsor_access.get("3")),
        "sponsor_9_access": bool(sponsor_access.get("9")),
        "sponsor_3_python_count": sponsor_3_python_count,
        "sponsor_9_python_count": sponsor_9_python_count,
        "sponsor_total_python_count": sponsor_3_python_count + sponsor_9_python_count,
        "network_enabled": achievements_network_enabled(),
        "tor_enabled": bool(network_config.get("tor_enabled")),
        "vpn_enabled": bool(network_config.get("vpn_enabled")),
        "vpn_country": str(network_config.get("vpn_country") or network_config.get("country") or "").upper(),
        "hour": int(time.localtime().tm_hour),
    }
    context.update(component_context)
    return context


def achievements_number(value, default=0):
    try:
        return float(value)
    except Exception:
        return float(default)


def achievements_condition_met(achievement, context, state):
    condition = achievement.get("condition")
    events = state.get("events", {}) if isinstance(state.get("events"), dict) else {}

    # Legacy string conditions are kept forever so old achievement IDs remain compatible.
    if condition == "always":
        return True
    if condition == "achievement_menu_opened":
        return int(events.get("achievement_menu_opened", 0)) >= 1
    if condition == "changed_menu_style":
        return context.get("menu_style") not in ("", "list")
    if condition == "greek_language":
        return context.get("language") == "greek"
    if condition == "github_connected":
        return bool(context.get("github_connected"))
    if condition == "usage_stats_started":
        return int(context.get("usage_scan_count", 0)) >= 1
    if condition == "python_scripts_10":
        return int(context.get("python_file_count", 0)) >= 10
    if condition == "project_save_exists":
        return bool(context.get("project_save_exists"))
    if condition == "sponsors_local":
        return bool(context.get("sponsors_local"))
    if condition == "network_enabled":
        return bool(context.get("network_enabled"))
    if condition == "commands_100":
        return int(context.get("total_commands", 0)) >= 100
    if condition == "settings_started_7":
        return int(events.get("settings_started", 0)) >= 7
    if condition == "both_languages_seen":
        seen = set(state.get("seen_languages", []))
        return "english" in seen and "greek" in seen
    if condition == "runnable_scripts_25":
        return int(context.get("runnable_file_count", 0)) >= 25
    if condition == "night_time":
        return 0 <= int(context.get("hour", 12)) < 5
    if condition == "dedsec_os_style":
        return context.get("menu_style") == "dedsec_os"

    # Generic condition engine for future achievements. Add new achievements by appending
    # ACHIEVEMENTS_DEFINITIONS entries; do not rewrite/remove existing IDs, earn rules,
    # background daemon, or watchdog logic. Existing users keep trophies by achievement ID.
    check = achievement.get("check")
    key = achievement.get("key")
    if check == "event_at_least":
        return int(events.get(achievement.get("event", ""), 0)) >= int(achievement.get("value", 1))
    if check == "context_at_least":
        return achievements_number(context.get(key, 0)) >= achievements_number(achievement.get("value", 0))
    if check == "context_truthy":
        return bool(context.get(key))
    if check == "context_equals":
        return str(context.get(key, "")).lower() == str(achievement.get("value", "")).lower()
    if check == "context_between":
        value = achievements_number(context.get(key, 0))
        return achievements_number(achievement.get("min", value)) <= value <= achievements_number(achievement.get("max", value))
    if check == "all_truthy":
        return all(bool(context.get(item)) for item in achievement.get("keys", []))
    if check == "unlocked_tier_at_least":
        target_tier = achievements_normalize_trophy_tier(achievement.get("tier") or achievement.get("difficulty"))
        unlocked = state.get("unlocked", {}) if isinstance(state.get("unlocked"), dict) else {}
        count = 0
        for unlocked_id in unlocked.keys():
            unlocked_achievement = ACHIEVEMENTS_BY_ID.get(unlocked_id)
            if unlocked_achievement and achievements_normalize_trophy_tier(unlocked_achievement.get("difficulty")) == target_tier:
                count += 1
        return count >= int(achievement.get("value", 1))
    if check == "trophy_score_at_least":
        unlocked = state.get("unlocked", {}) if isinstance(state.get("unlocked"), dict) else {}
        score = 0
        for unlocked_id in unlocked.keys():
            unlocked_achievement = ACHIEVEMENTS_BY_ID.get(unlocked_id)
            if unlocked_achievement:
                score += achievements_trophy_tier_points(unlocked_achievement.get("difficulty"))
        return score >= int(achievement.get("value", 1))
    return False


def achievements_notifications_available():
    """Return True when Termux:API notification command is available.

    Termux notifications require both the Termux:API Android app and the
    termux-api package inside Termux. Missing support must never break
    achievement unlocks or the always-on daemon.
    """
    return bool(shutil.which("termux-notification"))


def achievements_notification_text(achievement):
    title = _(achievement.get("title", "Achievement"))
    description = _(achievement.get("description", ""))
    tier_label = achievements_trophy_tier_label(achievement.get("difficulty"))
    points = achievements_trophy_tier_points(achievement.get("difficulty"))
    rank_line = _("Trophy rank") + ": " + tier_label + " | " + _("Trophy points") + ": " + str(points)
    if description:
        content = title + " - " + rank_line + " - " + description
    else:
        content = title + " - " + rank_line
    return title, content


def achievements_send_notification(title, content, notification_id=None):
    if not achievements_notifications_available():
        achievements_log(_("Install Termux:API and the termux-api package to receive unlock notifications."))
        achievements_record_event("notification_unavailable")
        return False
    try:
        if notification_id is None:
            digest = hashlib.sha1((str(title) + str(content) + str(time.time())).encode("utf-8", errors="ignore")).hexdigest()
            notification_id = ACHIEVEMENTS_NOTIFICATION_ID_BASE + (int(digest[:5], 16) % 10000)
        safe_title = str(title)[:80]
        safe_content = str(content)[:240]
        command = [
            "termux-notification",
            "--id",
            str(notification_id),
            "--title",
            safe_title,
            "--content",
            safe_content,
            "--priority",
            "high",
        ]
        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8)
        if result.returncode != 0:
            achievements_record_event("notification_errors")
            achievements_log("Achievement notification command failed with exit code: " + str(result.returncode))
            return False
        achievements_record_event("notification_success")
        achievements_log(_("Achievement notifications") + ": " + safe_title)
        return True
    except Exception as error:
        achievements_record_event("notification_errors")
        achievements_log("Achievement notification failed: " + str(error))
        return False


def achievements_notify_unlocks(newly_unlocked):
    if not newly_unlocked:
        return
    # Send individual PS3-style pings for small unlock batches. If a first scan
    # unlocks many trophies at once, send a compact bilingual summary instead
    # of flooding the phone with hundreds of notifications.
    if len(newly_unlocked) <= ACHIEVEMENTS_NOTIFICATION_MAX_INDIVIDUAL:
        for achievement in newly_unlocked:
            title, content = achievements_notification_text(achievement)
            achievements_send_notification(_("Achievement unlocked"), content)
        return
    sample_titles = []
    for achievement in newly_unlocked[:ACHIEVEMENTS_NOTIFICATION_MAX_INDIVIDUAL]:
        sample_titles.append(_(achievement.get("title", "Achievement")))
    summary_title = _("Unlocked achievements")
    summary_content = str(len(newly_unlocked)) + " " + _("new achievements unlocked")
    if sample_titles:
        summary_content += ": " + ", ".join(sample_titles)
    summary_content += ". " + _("Tap or return to Termux to view your trophies.")
    achievements_send_notification(summary_title, summary_content, ACHIEVEMENTS_NOTIFICATION_ID_BASE)


def achievements_test_command(value):
    """Unlock/send a test trophy notification for one difficulty rank.

    Usage from Termux after the bash hook is installed:
      Test 1  -> Beginner
      Test 2  -> Easy
      Test 3  -> Normal
      Test 4  -> Hard
      Test 5  -> Very Hard
      Test 6  -> Godlike

    Direct usage also works:
      python3 Settings.py --achievement-test 1
    """
    raw = str(value or "").strip().lower().replace(" ", "_")
    if not raw:
        raw = "1"
    selected = None
    for item in ACHIEVEMENTS_TEST_TROPHIES:
        aliases = [str(alias).lower().replace(" ", "_") for alias in item.get("aliases", ())]
        if raw in aliases:
            selected = item
            break
    if not selected:
        print(_("Unknown achievement test. Use Test 1 to Test 6."))
        print("Test 1 = " + achievements_trophy_tier_label("beginner"))
        print("Test 2 = " + achievements_trophy_tier_label("easy"))
        print("Test 3 = " + achievements_trophy_tier_label("normal"))
        print("Test 4 = " + achievements_trophy_tier_label("hard"))
        print("Test 5 = " + achievements_trophy_tier_label("very_hard"))
        print("Test 6 = " + achievements_trophy_tier_label("godlike"))
        return False

    achievement_id = selected["id"]
    state = achievements_load_state()
    was_unlocked = achievement_id in (state.get("unlocked", {}) if isinstance(state.get("unlocked"), dict) else {})

    achievements_record_event(selected["event"])
    achievements_record_event("achievement_test_commands")
    newly_unlocked = achievements_check_and_unlock(silent=False, source="test_" + selected["number"])

    tier_label = achievements_trophy_tier_label(selected["difficulty"])
    notification_title = _("Achievement unlocked") if not was_unlocked else _("Achievement already unlocked")
    # Keep the test notification simple and clear, exactly for checking Termux:API.
    notification_content = _(selected["title"]) + " - " + _("Difficulty") + ": " + tier_label

    # Always send one explicit test ping. This avoids the v8 false-positive case
    # where a fresh unlock could print "sent" even when Termux:API was missing.
    # It may create one extra notification on a fresh test unlock, but it makes
    # the command a reliable notification test for every difficulty.
    sent = achievements_send_notification(notification_title, notification_content)

    print("=== " + _("Achievement Test Commands") + " ===")
    print(_(selected["title"]))
    print(_("Difficulty") + ": " + tier_label)
    if was_unlocked:
        print(_("Achievement already unlocked"))
    if sent:
        print(_("Achievement test notification sent."))
    else:
        print(_("Achievement test notification could not be sent. Install Termux:API and pkg install termux-api."))
    return True


def achievements_print_unlock(achievement):
    title = _(achievement.get("title", "Achievement"))
    description = _(achievement.get("description", ""))
    tier_label = achievements_trophy_tier_label(achievement.get("difficulty"))
    points = achievements_trophy_tier_points(achievement.get("difficulty"))
    width = 58
    print("\n" + "=" * width)
    print("[ PS3 STYLE TROPHY ] " + _("Achievement unlocked"))
    print("- " + title)
    print("- " + _("Trophy rank") + ": " + tier_label + " | " + _("Trophy points") + ": " + str(points))
    if description:
        for line in textwrap.wrap(description, width - 4):
            print("  " + line)
    print("=" * width + "\n")


def achievements_check_and_unlock(silent=False, source="manual"):
    state = achievements_load_state()
    state["last_checked"] = time.time()
    events = state.setdefault("events", {})
    if source == "background":
        state["last_daemon_heartbeat"] = time.time()
        events["background_checks"] = int(events.get("background_checks", 0)) + 1
    elif source == "manual":
        events["manual_checks"] = int(events.get("manual_checks", 0)) + 1
    elif source:
        events["checks_" + str(source)] = int(events.get("checks_" + str(source), 0)) + 1

    language = load_language_preference() or get_current_display_language() or "english"
    if language not in state.setdefault("seen_languages", []):
        state["seen_languages"].append(language)

    context = achievements_build_context(state)
    newly_unlocked = []
    unlocked = state.setdefault("unlocked", {})

    for achievement in ACHIEVEMENTS_DEFINITIONS:
        achievement_id = achievement.get("id")
        if not achievement_id or achievement_id in unlocked:
            continue
        if achievements_condition_met(achievement, context, state):
            unlocked[achievement_id] = {
                "unlocked_at": time.time(),
                "source": source,
                "title": achievement.get("title", achievement_id),
            }
            newly_unlocked.append(achievement)
            achievements_log(_("Achievement unlocked") + ": " + achievement.get("title", achievement_id))

    achievements_save_state(state)

    if newly_unlocked:
        achievements_notify_unlocks(newly_unlocked)

    if newly_unlocked and not silent:
        for achievement in newly_unlocked:
            achievements_print_unlock(achievement)
    return newly_unlocked


def achievements_total_counts():
    state = achievements_load_state()
    unlocked = state.get("unlocked", {}) if isinstance(state.get("unlocked"), dict) else {}
    return len(unlocked), len(ACHIEVEMENTS_DEFINITIONS)


def achievements_pid_alive(pid):
    try:
        pid = int(pid)
        if pid <= 0:
            return False
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def achievements_pid_matches(pid, required_flag=None):
    """Return True only when the PID is alive and appears to be this Settings.py worker.

    Termux can reuse PIDs after a process dies. This extra check prevents a stale
    .pid file from fooling Settings.py into thinking the checker is still alive.
    If Android blocks /proc access, alive PID is accepted as a safe fallback.
    """
    if not achievements_pid_alive(pid):
        return False
    if not required_flag:
        return True
    try:
        with open(f"/proc/{int(pid)}/cmdline", "rb") as handle:
            raw = handle.read().replace(b"\x00", b" ").decode("utf-8", errors="replace")
        if required_flag in raw and os.path.basename(SETTINGS_SCRIPT_PATH) in raw:
            return True
        return False
    except Exception:
        return True


def achievements_read_pid(path):
    try:
        if not os.path.exists(path):
            return 0
        with open(path, "r", encoding="utf-8") as handle:
            return int(handle.read().strip() or "0")
    except Exception:
        return 0


def achievements_daemon_running():
    return achievements_pid_matches(achievements_read_pid(ACHIEVEMENTS_PID_PATH), "--achievements-daemon")


def achievements_watchdog_running():
    return achievements_pid_matches(achievements_read_pid(ACHIEVEMENTS_WATCHDOG_PID_PATH), "--achievements-watchdog")


def achievements_touch_heartbeat(name):
    try:
        state = achievements_load_state()
        if name == "daemon":
            state["last_daemon_heartbeat"] = int(time.time())
        elif name == "watchdog":
            state["last_watchdog_heartbeat"] = int(time.time())
        achievements_save_state(state)
    except Exception:
        pass


def achievements_force_background_enabled():
    """Achievements are designed to run constantly while Termux is open."""
    state = achievements_load_state()
    if not state.get("background_enabled", True):
        state["background_enabled"] = True
        achievements_save_state(state)
        achievements_log("Achievements constant mode forced background checker back ON.")
    return state


def achievements_try_wake_lock():
    """Request Termux wake lock when available so the checker keeps running more reliably.

    This does not require root. If Termux:API is not installed, the call is silently skipped.
    Android can still stop everything if Termux itself is force-closed or battery settings kill it.
    """
    try:
        if not shutil.which("termux-wake-lock"):
            return False
        state = achievements_load_state()
        now = time.time()
        last = float(state.get("last_wake_lock_request", 0) or 0)
        if now - last < 3600:
            return True
        subprocess.Popen(
            ["termux-wake-lock"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        state["last_wake_lock_request"] = now
        achievements_save_state(state)
        return True
    except Exception as error:
        achievements_log("Achievements wake-lock request skipped: " + str(error))
        return False


def achievements_acquire_ensure_lock():
    """Prevent prompt hooks from spawning many simultaneous repair checks."""
    try:
        if os.path.exists(ACHIEVEMENTS_ENSURE_LOCK_PATH):
            try:
                age = time.time() - os.path.getmtime(ACHIEVEMENTS_ENSURE_LOCK_PATH)
                if age > 20:
                    os.remove(ACHIEVEMENTS_ENSURE_LOCK_PATH)
            except Exception:
                pass
        fd = os.open(ACHIEVEMENTS_ENSURE_LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode("utf-8"))
        return fd
    except FileExistsError:
        return None
    except Exception:
        return None


def achievements_release_ensure_lock(fd):
    try:
        if fd is not None:
            os.close(fd)
    except Exception:
        pass
    try:
        if os.path.exists(ACHIEVEMENTS_ENSURE_LOCK_PATH):
            os.remove(ACHIEVEMENTS_ENSURE_LOCK_PATH)
    except Exception:
        pass


def achievements_kill_stale_worker(pid_path, heartbeat_key, stale_seconds, label):
    """Restart workers that are alive by PID but stopped sending heartbeats."""
    try:
        pid = achievements_read_pid(pid_path)
        if not pid or not achievements_pid_alive(pid):
            if os.path.exists(pid_path):
                os.remove(pid_path)
            return False

        state = achievements_load_state()
        now = time.time()
        last_heartbeat = float(state.get(heartbeat_key, 0) or 0)
        if last_heartbeat <= 0:
            try:
                file_age = now - os.path.getmtime(pid_path)
            except Exception:
                file_age = 0
            if file_age < stale_seconds:
                return False
        elif now - last_heartbeat < stale_seconds:
            return False

        try:
            os.kill(pid, 15)
            time.sleep(0.2)
        except Exception:
            pass
        try:
            if achievements_pid_alive(pid):
                os.kill(pid, 9)
        except Exception:
            pass
        try:
            if os.path.exists(pid_path):
                os.remove(pid_path)
        except Exception:
            pass
        achievements_record_event(label + "_stale_restarts")
        achievements_log("Achievements constant mode restarted stale " + label + ".")
        return True
    except Exception as error:
        achievements_log("Achievements stale-worker repair error: " + str(error))
        return False


def achievements_repair_stale_workers():
    achievements_kill_stale_worker(ACHIEVEMENTS_PID_PATH, "last_daemon_heartbeat", ACHIEVEMENTS_STALE_DAEMON_SECONDS, "daemon")
    achievements_kill_stale_worker(ACHIEVEMENTS_WATCHDOG_PID_PATH, "last_watchdog_heartbeat", ACHIEVEMENTS_STALE_WATCHDOG_SECONDS, "watchdog")


def achievements_update_startup_hook():
    """Install a Termux shell hook so achievements keep repairing themselves.

    The block starts the constant checker when a shell opens and also adds a small
    PROMPT_COMMAND guard. Every normal Termux prompt can re-check the workers, so
    if the daemon and watchdog were killed while Termux remained open, the next
    prompt will relaunch them. Future updates must not remove this block unless
    another always-on achievement supervisor replaces it.
    """
    try:
        os.makedirs(os.path.dirname(BASHRC_PATH), exist_ok=True)
        content = ""
        if os.path.exists(BASHRC_PATH):
            with open(BASHRC_PATH, "r", encoding="utf-8", errors="replace") as handle:
                content = handle.read()
        pattern = re.escape(ACHIEVEMENTS_BASHRC_START_MARKER) + r".*?" + re.escape(ACHIEVEMENTS_BASHRC_END_MARKER) + r"\n?"
        content = re.sub(pattern, "", content, flags=re.DOTALL)

        safe_settings_path = SETTINGS_SCRIPT_PATH.replace('"', '\\"')
        block_lines = [
            "",
            ACHIEVEMENTS_BASHRC_START_MARKER,
            f'DEDSEC_ACHIEVEMENTS_SETTINGS="{safe_settings_path}"',
            "DEDSEC_ACHIEVEMENTS_LAST=0",
            "dedsec_achievements_constant_guard() {",
            "    local now=\"$(date +%s 2>/dev/null || echo 0)\"",
            f"    local interval=\"{ACHIEVEMENTS_PROMPT_GUARD_INTERVAL_SECONDS}\"",
            "    if [ -z \"$now\" ]; then now=0; fi",
            "    if [ -z \"$DEDSEC_ACHIEVEMENTS_LAST\" ]; then DEDSEC_ACHIEVEMENTS_LAST=0; fi",
            "    if [ $((now - DEDSEC_ACHIEVEMENTS_LAST)) -ge $interval ]; then",
            "        DEDSEC_ACHIEVEMENTS_LAST=\"$now\"",
            "        if [ -f \"$DEDSEC_ACHIEVEMENTS_SETTINGS\" ]; then",
            "            (python3 \"$DEDSEC_ACHIEVEMENTS_SETTINGS\" --achievements-ensure >/dev/null 2>&1 &)",
            "        fi",
            "    fi",
            "}",
            "dedsec_achievements_constant_guard",
            "Test() {",
            "    if [ -f \"$DEDSEC_ACHIEVEMENTS_SETTINGS\" ]; then",
            "        python3 \"$DEDSEC_ACHIEVEMENTS_SETTINGS\" --achievement-test \"$1\"",
            "    else",
            "        echo \"DedSec Settings.py not found.\"",
            "    fi",
            "}",
            "Test1() { Test 1; }",
            "Test2() { Test 2; }",
            "Test3() { Test 3; }",
            "Test4() { Test 4; }",
            "Test5() { Test 5; }",
            "Test6() { Test 6; }",
            "case \"$PROMPT_COMMAND\" in",
            "    *dedsec_achievements_constant_guard*) ;;",
            "    *) PROMPT_COMMAND=\"dedsec_achievements_constant_guard${PROMPT_COMMAND:+;$PROMPT_COMMAND}\" ;;",
            "esac",
            ACHIEVEMENTS_BASHRC_END_MARKER,
            "",
        ]
        block = "\n".join(block_lines)
        content = content.rstrip() + "\n" + block
        with open(BASHRC_PATH, "w", encoding="utf-8") as handle:
            handle.write(content)
    except Exception as error:
        achievements_log("Failed to update achievements startup hook: " + str(error))

def achievements_ensure_constant_background_checker(silent=True, install_hook=True):
    """Force the achievement engine to stay alive while Termux is open.

    It keeps background mode enabled, repairs stale PID files, starts the watchdog,
    starts the daemon, and installs the Termux shell prompt guard. This function is
    intentionally safe to call often from Settings.py and from bash.bashrc.
    """
    fd = achievements_acquire_ensure_lock()
    if fd is None:
        return achievements_watchdog_running() and achievements_daemon_running()
    try:
        achievements_force_background_enabled()
        if install_hook:
            achievements_update_startup_hook()
        achievements_try_wake_lock()
        achievements_repair_stale_workers()
        watchdog_ok = achievements_start_watchdog_if_needed(silent=True, install_hook=False)
        daemon_ok = achievements_start_daemon_if_needed(silent=True, install_hook=False)
        if watchdog_ok and daemon_ok:
            achievements_record_event("constant_ensure")
            if not silent:
                print(_("Background achievement checker enabled."))
            return True
        return False
    except Exception as error:
        achievements_log("Achievements constant checker repair failed: " + str(error))
        if not silent:
            print("[!] " + str(error))
        return False
    finally:
        achievements_release_ensure_lock(fd)

def achievements_stop_pid_file(pid_path, signal_number=15):
    try:
        pid = achievements_read_pid(pid_path)
        if pid and achievements_pid_alive(pid):
            os.kill(pid, signal_number)
        if os.path.exists(pid_path):
            os.remove(pid_path)
    except Exception:
        pass


def achievements_stop_daemon():
    achievements_stop_pid_file(ACHIEVEMENTS_PID_PATH)
    achievements_stop_pid_file(ACHIEVEMENTS_WATCHDOG_PID_PATH)


def achievements_start_daemon_if_needed(silent=True, install_hook=True):
    state = achievements_force_background_enabled()
    if install_hook:
        achievements_update_startup_hook()
    if not state.get("background_enabled", True):
        return False
    if achievements_daemon_running():
        return True
    try:
        log_handle = open(ACHIEVEMENTS_LOG_PATH, "a", encoding="utf-8")
        try:
            subprocess.Popen(
                [sys.executable, SETTINGS_SCRIPT_PATH, "--achievements-daemon"],
                stdin=subprocess.DEVNULL,
                stdout=log_handle,
                stderr=log_handle,
                cwd=HOME_DIR,
                start_new_session=True,
            )
        finally:
            log_handle.close()
        achievements_record_event("daemon_starts")
        if not silent:
            print(_("Background achievement checker enabled."))
        return True
    except Exception as error:
        achievements_log("Failed to start achievements daemon: " + str(error))
        if not silent:
            print("[!] " + str(error))
        return False


def achievements_start_watchdog_if_needed(silent=True, install_hook=True):
    state = achievements_force_background_enabled()
    if install_hook:
        achievements_update_startup_hook()
    if not state.get("background_enabled", True):
        return False
    if achievements_watchdog_running():
        achievements_start_daemon_if_needed(silent=True, install_hook=False)
        return True
    try:
        log_handle = open(ACHIEVEMENTS_LOG_PATH, "a", encoding="utf-8")
        try:
            subprocess.Popen(
                [sys.executable, SETTINGS_SCRIPT_PATH, "--achievements-watchdog"],
                stdin=subprocess.DEVNULL,
                stdout=log_handle,
                stderr=log_handle,
                cwd=HOME_DIR,
                start_new_session=True,
            )
        finally:
            log_handle.close()
        achievements_record_event("watchdog_starts")
        achievements_start_daemon_if_needed(silent=True, install_hook=False)
        if not silent:
            print(_("Background achievement checker enabled."))
        return True
    except Exception as error:
        achievements_log("Failed to start achievements watchdog: " + str(error))
        if not silent:
            print("[!] " + str(error))
        return False


def achievements_sleep_with_disable_check(seconds):
    # Constant mode: do not stop just because an old state file says disabled.
    # This intentionally sleeps in small chunks so KeyboardInterrupt / process kills are responsive.
    deadline = time.time() + max(1, int(seconds))
    while time.time() < deadline:
        achievements_force_background_enabled()
        time.sleep(min(1, max(0.1, deadline - time.time())))
    return True


def achievements_run_daemon():
    try:
        with open(ACHIEVEMENTS_PID_PATH, "w", encoding="utf-8") as handle:
            handle.write(str(os.getpid()))
        achievements_force_background_enabled()
        achievements_try_wake_lock()
        achievements_log("Achievements background checker started.")
        while True:
            try:
                achievements_force_background_enabled()
                achievements_touch_heartbeat("daemon")
                if not achievements_watchdog_running():
                    achievements_start_watchdog_if_needed(silent=True, install_hook=False)
                    achievements_record_event("daemon_restarted_watchdog")
                achievements_check_and_unlock(silent=True, source="background")
            except Exception as error:
                achievements_record_event("daemon_errors")
                achievements_log("Achievements daemon loop recovered after error: " + str(error))
            if not achievements_sleep_with_disable_check(ACHIEVEMENTS_SCAN_INTERVAL_SECONDS):
                break
    except KeyboardInterrupt:
        achievements_log("Achievements daemon interrupted.")
    except Exception as error:
        achievements_log("Achievements daemon fatal wrapper error: " + str(error))
    finally:
        try:
            if os.path.exists(ACHIEVEMENTS_PID_PATH):
                with open(ACHIEVEMENTS_PID_PATH, "r", encoding="utf-8") as handle:
                    saved_pid = handle.read().strip()
                if saved_pid == str(os.getpid()):
                    os.remove(ACHIEVEMENTS_PID_PATH)
        except Exception:
            pass
        achievements_log("Achievements background checker stopped.")


def achievements_run_watchdog():
    try:
        with open(ACHIEVEMENTS_WATCHDOG_PID_PATH, "w", encoding="utf-8") as handle:
            handle.write(str(os.getpid()))
        achievements_force_background_enabled()
        achievements_try_wake_lock()
        achievements_log("Achievements watchdog started.")
        while True:
            try:
                achievements_force_background_enabled()
                achievements_touch_heartbeat("watchdog")
                was_running = achievements_daemon_running()
                achievements_start_daemon_if_needed(silent=True, install_hook=False)
                if not was_running and achievements_daemon_running():
                    achievements_record_event("watchdog_restarts")
                    achievements_log("Achievements watchdog restarted the checker.")
                achievements_record_event("watchdog_pulses")
            except Exception as error:
                achievements_log("Achievements watchdog recovered after error: " + str(error))
            if not achievements_sleep_with_disable_check(ACHIEVEMENTS_WATCHDOG_INTERVAL_SECONDS):
                break
    except KeyboardInterrupt:
        achievements_log("Achievements watchdog interrupted.")
    except Exception as error:
        achievements_log("Achievements watchdog fatal wrapper error: " + str(error))
    finally:
        try:
            if os.path.exists(ACHIEVEMENTS_WATCHDOG_PID_PATH):
                with open(ACHIEVEMENTS_WATCHDOG_PID_PATH, "r", encoding="utf-8") as handle:
                    saved_pid = handle.read().strip()
                if saved_pid == str(os.getpid()):
                    os.remove(ACHIEVEMENTS_WATCHDOG_PID_PATH)
        except Exception:
            pass
        achievements_log("Achievements watchdog stopped.")


def achievements_toggle_background_checker():
    # Constant mode: this option repairs/restarts the checker instead of disabling it.
    # Future updates must keep achievements running while Termux is open.
    achievements_record_event("background_toggle")
    state = achievements_load_state()
    state["background_enabled"] = True
    achievements_save_state(state)
    achievements_ensure_constant_background_checker(silent=True)
    achievements_check_and_unlock(silent=False, source="menu")
    print(_("Constant checker repaired."))

def achievements_trophy_summary(state):
    unlocked = state.get("unlocked", {}) if isinstance(state.get("unlocked"), dict) else {}
    summary = {tier: {"total": 0, "unlocked": 0, "points": 0} for tier in ACHIEVEMENTS_TROPHY_TIERS}
    total_points = 0
    earned_points = 0
    for achievement in ACHIEVEMENTS_DEFINITIONS:
        tier = achievements_normalize_trophy_tier(achievement.get("difficulty"))
        points = achievements_trophy_tier_points(tier)
        summary[tier]["total"] += 1
        summary[tier]["points"] += points
        total_points += points
        if achievement.get("id") in unlocked:
            summary[tier]["unlocked"] += 1
            earned_points += points
    return summary, earned_points, total_points


def achievements_format_card(achievement, state):
    achievement_id = achievement.get("id")
    unlocked_data = state.get("unlocked", {}).get(achievement_id)
    is_unlocked = bool(unlocked_data)
    is_hidden = bool(achievement.get("hidden")) and not is_unlocked
    title = _("Hidden Achievement") if is_hidden else _(achievement.get("title", achievement_id))
    description = _("Keep using DedSec Project to reveal this.") if is_hidden else _(achievement.get("description", ""))
    status = _("Unlocked") if is_unlocked else (_("Hidden") if is_hidden else _("Locked"))
    tier_label = _("Hidden") if is_hidden else achievements_trophy_tier_label(achievement.get("difficulty"))
    tier_key = achievements_normalize_trophy_tier(achievement.get("difficulty"))
    tier_short = "???" if is_hidden else ACHIEVEMENTS_TROPHY_TIER_SHORT.get(tier_key, "N")
    points = "???" if is_hidden else str(achievements_trophy_tier_points(tier_key))
    timestamp = ""
    if is_unlocked:
        timestamp = " | " + format_timestamp(float(unlocked_data.get("unlocked_at") or time.time()))
    lines = ["+" + "-" * 60 + "+"]
    lines.append("| " + ("[" + status + "] [" + tier_short + "] " + title + timestamp)[:58].ljust(58) + " |")
    lines.append("|   " + (_("Trophy rank") + ": " + tier_label + " | " + _("Trophy points") + ": " + str(points))[:56].ljust(56) + " |")
    for desc_line in textwrap.wrap(description, 56) or [""]:
        lines.append("|   " + desc_line[:56].ljust(56) + " |")
    lines.append("+" + "-" * 60 + "+")
    return "\n".join(lines)


def achievements_show_log():
    achievements_record_event("achievement_log_opened")
    if not os.path.exists(ACHIEVEMENTS_LOG_PATH):
        print(_("No achievement log yet."))
        return
    try:
        with open(ACHIEVEMENTS_LOG_PATH, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.readlines()[-40:]
        if not lines:
            print(_("No achievement log yet."))
            return
        print("=== " + _("Show achievement log") + " ===\n")
        for line in lines:
            print(line.rstrip())
    except Exception as error:
        print("[!] " + str(error))


def achievements_menu():
    achievements_record_event("achievement_menu_opened")
    achievements_ensure_constant_background_checker(silent=True)
    achievements_check_and_unlock(silent=False, source="menu")
    while True:
        os.system("clear")
        state = achievements_load_state()
        unlocked_count, total_count = achievements_total_counts()
        state["background_enabled"] = True
        achievements_save_state(state)
        checker_status = _("Forced ON")
        daemon_status = _("Running") if achievements_daemon_running() else _("Stopped")
        watchdog_status = _("Running") if achievements_watchdog_running() else _("Stopped")
        print("=== " + _("Achievements") + " ===")
        print(_("Progress") + f": {unlocked_count}/{total_count}")
        tier_summary, earned_points, total_points = achievements_trophy_summary(state)
        print(_("Trophy score") + f": {earned_points}/{total_points}")
        print(_("Difficulty summary") + ":")
        for tier_key in ACHIEVEMENTS_TROPHY_TIERS:
            data = tier_summary.get(tier_key, {})
            print("  - " + achievements_trophy_tier_label(tier_key) + f": {data.get('unlocked', 0)}/{data.get('total', 0)}")
        print(_("Background checker") + f": {checker_status}")
        print(_("Daemon status") + f": {daemon_status}")
        notification_status = _("Supported") if achievements_notifications_available() else _("Not available")
        notification_count = int(state.get("events", {}).get("notification_success", 0)) if isinstance(state.get("events"), dict) else 0
        print(_("Watchdog status") + f": {watchdog_status}")
        print(_("Termux:API notification support") + f": {notification_status}")
        print(_("Notifications sent") + f": {notification_count}")
        print("\n" + _("Achievement Test Commands") + ":")
        print("  " + _("Run these in Termux to test each difficulty notification:"))
        print("  Test 1 = " + achievements_trophy_tier_label("beginner"))
        print("  Test 2 = " + achievements_trophy_tier_label("easy"))
        print("  Test 3 = " + achievements_trophy_tier_label("normal"))
        print("  Test 4 = " + achievements_trophy_tier_label("hard"))
        print("  Test 5 = " + achievements_trophy_tier_label("very_hard"))
        print("  Test 6 = " + achievements_trophy_tier_label("godlike"))
        print("\n" + "PS3 STYLE TROPHY ROOM" + "\n")
        for achievement in ACHIEVEMENTS_DEFINITIONS:
            print(achievements_format_card(achievement, state))
        print("")
        options = [
            _("Check achievements now"),
            _("Restart constant checker"),
            _("Show achievement log"),
            _("Back"),
        ]
        for index, option in enumerate(options, start=1):
            print(str(index) + ". " + option)
        choice = input("\n" + _("Enter the number of your choice: ")).strip()
        os.system("clear")
        if choice == "1":
            achievements_check_and_unlock(silent=False, source="manual")
            print(_("Achievements checked."))
        elif choice == "2":
            achievements_toggle_background_checker()
            achievements_check_and_unlock(silent=False, source="menu")
        elif choice == "3":
            achievements_show_log()
            achievements_check_and_unlock(silent=False, source="menu")
        elif choice == "4" or choice.lower() in ("b", "back", "q", "quit", "0"):
            break
        else:
            print(_("Invalid selection. Please try again."))
        input("\n" + _("Press Enter to continue..."))

def print_limited_paths(title, paths, limit=8):
    print(f"\n{title}:")
    if not paths:
        print("  - None")
        return
    for item in paths[:limit]:
        print(f"  - {item}")
    if len(paths) > limit:
        print(f"  - ... +{len(paths) - limit} more")


def show_termux_usage_stats():
    print("=== " + _("Termux Usage Stats") + " ===")
    stats = update_termux_usage_stats()
    first_scan = float(stats.get("first_scan") or time.time())
    tracked_seconds = time.time() - first_scan
    totals = stats.get("totals", {})
    latest = stats.get("latest", {})

    print(f"{_('Tracking since')}: {format_timestamp(first_scan)}")
    print(f"{_('Tracked time')}: {format_duration(tracked_seconds)}")
    print(f"{_('Settings runtime tracked')}: {format_duration(stats.get('settings_runtime_seconds', 0))}")
    print(f"{_('Files scanned')}: {len(stats.get('snapshot', {}))}")
    print(f"{_('Files created')}: {totals.get('created', 0)} (+{len(latest.get('created', []))} latest scan)")
    print(f"{_('Files edited')}: {totals.get('edited', 0)} (+{len(latest.get('edited', []))} latest scan)")
    print(f"{_('Files deleted')}: {totals.get('deleted', 0)} (+{len(latest.get('deleted', []))} latest scan)")
    print(f"{_('Shell commands found')}: {stats.get('total_commands', 0)}")

    if latest.get("is_first_scan"):
        print("\n[*] " + _("First scan created. Run this again later to detect created/edited/deleted files."))

    print("\n" + _("Programming languages used") + ":")
    language_counts = stats.get("language_counts", {})
    language_bytes = stats.get("language_bytes", {})
    if language_counts:
        for language, count in sorted(language_counts.items(), key=lambda item: item[1], reverse=True)[:15]:
            size_kb = language_bytes.get(language, 0) / 1024
            print(f"  - {language}: {count} files ({size_kb:.1f} KB)")
    else:
        print("  - None detected yet")

    print("\nTop shell commands:")
    top_commands = stats.get("top_commands", [])
    if top_commands:
        for command, count in top_commands:
            print(f"  - {command}: {count}")
    else:
        print("  - None detected yet")

    print("\n" + _("Most active folders") + ":")
    folder_counts = stats.get("folder_counts", {})
    for folder, count in sorted(folder_counts.items(), key=lambda item: item[1], reverse=True)[:10]:
        print(f"  - {folder}: {count} files")
    if not folder_counts:
        print("  - None")

    print_limited_paths(_("Latest created"), latest.get("created", []))
    print_limited_paths(_("Latest edited"), latest.get("edited", []))
    print_limited_paths(_("Latest deleted"), latest.get("deleted", []))

atexit.register(_record_termux_settings_session_time)

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
        if BASHRC_START_MARKER in line or ACHIEVEMENTS_BASHRC_START_MARKER in line or NETWORK_BASHRC_START_MARKER in line:
            in_marked_block = True
            continue
        if BASHRC_END_MARKER in line or ACHIEVEMENTS_BASHRC_END_MARKER in line or NETWORK_BASHRC_END_MARKER in line:
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
        safe_curses_addstr(stdscr, 1, width // 2 - len(title) // 2, title)
        
        for idx, option in enumerate(options):
            x = width // 2 - len(option) // 2
            y = height // 2 - len(options) // 2 + idx
            if idx == current:
                stdscr.attron(curses.A_REVERSE)
                safe_curses_addstr(stdscr, y, x, option)
                stdscr.attroff(curses.A_REVERSE)
            else:
                safe_curses_addstr(stdscr, y, x, option)
        
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
        safe_curses_addstr(stdscr, 1, width // 2 - len(title) // 2, title)
        
        for idx, option in enumerate(options):
            x = width // 2 - len(option) // 2
            y = height // 2 - len(options) // 2 + idx
            if idx == current:
                stdscr.attron(curses.A_REVERSE)
                safe_curses_addstr(stdscr, y, x, option)
                stdscr.attroff(curses.A_REVERSE)
            else:
                safe_curses_addstr(stdscr, y, x, option)
        
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
        for sponsors_display_name, _go_token in get_sponsors_display_entries():
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

    sponsors_go_token = get_sponsors_go_token_for_display_name(selected)
    if sponsors_go_token:
        return sponsors_go_token

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
        
        if isinstance(selected, str) and selected.startswith("go_sponsors:"):
            sponsors_path = get_sponsors_preferred_path(selected.split(":", 1)[1])
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
            for sponsors_display_name, sponsors_go_token in get_sponsors_display_entries():
                items.append((sponsors_display_name, sponsors_go_token))
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

            if isinstance(selected_path, str) and selected_path.startswith("go_sponsors:"):
                sponsors_path = get_sponsors_preferred_path(selected_path.split(":", 1)[1])
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
        for sponsors_display_name, sponsors_go_token in get_sponsors_display_entries():
            entries.append((sponsors_display_name, sponsors_go_token))
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
                safe_curses_addstr(stdscr, 0, 0, _("Terminal window is too small."))
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
                            safe_curses_addstr(stdscr, line_y, line_x, display_line, curses.color_pair(3))
                        except curses.error:
                            pass
            
            page_info = f" Page {(current_index // total_visible_cells) + 1} / {math.ceil(num_items / total_visible_cells)} "
            instructions = f"Arrow Keys: Move | P/N: Prev/Next Page | Enter: Select | q: Quit | {page_info}"
            try:
                safe_curses_addstr(stdscr, term_height - 1, 0, instructions[:term_width - 1], curses.color_pair(3))
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

        if isinstance(selected_path, str) and selected_path.startswith("go_sponsors:"):
            sponsors_path = get_sponsors_preferred_path(selected_path.split(":", 1)[1])
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
    python_packages = "blessed bs4 cryptography flask flask-socketio geopy mutagen phonenumbers pycountry pydub pycryptodome requests werkzeug psutil pillow pysocks"
    
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
import atexit
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
SPONSORS_TIERS = __SPONSORS_TIERS__
SPONSORS_TIER_ORDER = __SPONSORS_TIER_ORDER__
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
    new_ps1 = "PS1='\\[\\e[1;36m\\]\\D{%d/%m/%Y}-[\\A]-(\\[\\e[1;34m\\]" + username + "\\[\\e[0m\\])-(\\[\\e[1;33m\\]\\W\\[\\e[0m\\]) : '\\n"
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
            'art_artists': 'Christina Chatzidimitriou',
            'legal_documents': 'Lampros Spyrou',
            'discord_server_maintenance': 'Talha',
            'past_help': 'lamprouil, UKI_hunter'
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
        cmd = 'termux-setup-storage; pkg update -y && pkg upgrade -y && pkg install -y aapt clang cloudflared curl ffmpeg fzf git jq libffi libxml2 libxslt nano ncurses nodejs openssh openssl openssl-tool proot python rust termux-api unzip wget zip tor && pip install --upgrade pip setuptools wheel --break-system-packages && pip install blessed bs4 cryptography flask flask-socketio geopy mutagen phonenumbers pycountry pydub pycryptodome requests werkzeug psutil pillow pysocks --break-system-packages'
        return launch_job(label='Settings: Update Packages & Modules', shell_command=cmd, cwd=HOME_DIR, kind='settings-packages', prefer_termux=False)
    if action == 'access_sponsors':
        tier = str(payload.get('tier') or '3').replace('$', '').strip()
        config = SPONSORS_TIERS.get(tier)
        if not config:
            raise ValueError('Invalid sponsor tier.')
        repo_url = config['git_url']
        final_path = os.path.join(HOME_DIR, config['root_name'])
        temp_path = final_path + '.download'
        old_paths = [os.path.join(HOME_DIR, item) for item in (config.get('old_root_names') or [])]
        old_paths_text = ' '.join(shlex.quote(item) for item in old_paths)
        cmd = f"""pkg install -y gh git >/dev/null 2>&1 || true
if ! gh auth status --hostname github.com >/dev/null 2>&1; then
  echo "GitHub is not connected. Open Settings.py from Termux and use Access Sponsors-Only Scripts so it can ask you to connect."
  exit 1
fi
TOKEN="$(gh auth token 2>/dev/null)"
if [ -z "$TOKEN" ]; then
  echo "Could not read GitHub token. Run: gh auth refresh -h github.com -s repo"
  exit 1
fi
ASK="$HOME/.dedsec_sponsors_askpass_$$.sh"
cleanup(){{ rm -f "$ASK"; }}
trap cleanup EXIT
cat > "$ASK" <<'DEDSEC_ASKPASS'
#!/usr/bin/env sh
case "$1" in
  *Username*) echo x-access-token ;;
  *) echo "$DEDSEC_GITHUB_TOKEN" ;;
esac
DEDSEC_ASKPASS
chmod 700 "$ASK"
if ! GIT_ASKPASS="$ASK" GIT_TERMINAL_PROMPT=0 DEDSEC_GITHUB_TOKEN="$TOKEN" git ls-remote {shlex.quote(repo_url)} HEAD >/dev/null 2>&1; then
  echo "You do not have access to {config['label']} yet, or GitHub SSO/token access must be approved."
  exit 1
fi
rm -rf {shlex.quote(temp_path)}
if GIT_ASKPASS="$ASK" GIT_TERMINAL_PROMPT=0 DEDSEC_GITHUB_TOKEN="$TOKEN" git clone --depth 1 {shlex.quote(repo_url)} {shlex.quote(temp_path)}; then
  rm -rf {shlex.quote(final_path)} {old_paths_text}
  mv {shlex.quote(temp_path)} {shlex.quote(final_path)}
  echo "Sponsors-Only {config['short_label']} scripts downloaded to: {final_path}"
else
  echo "Failed to download Sponsors-Only {config['short_label']} scripts. Old copy was kept if it existed."
  rm -rf {shlex.quote(temp_path)}
  exit 1
fi
"""
        return launch_job(label='Settings: Access Sponsors-Only ' + config['short_label'], shell_command=cmd, cwd=HOME_DIR, kind='settings-sponsors', prefer_termux=False)
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


def get_sponsor_tier_config(tier_key):
    return SPONSORS_TIERS.get(str(tier_key or '').replace('$', '').strip())


def get_sponsors_tier_root_path(tier_key):
    config = get_sponsor_tier_config(tier_key)
    if not config:
        return None
    return os.path.join(HOME_DIR, config['root_name'])


def get_sponsors_path(tier_key=None):
    if tier_key is None:
        for candidate in SPONSORS_TIER_ORDER:
            root = get_sponsors_tier_root_path(candidate)
            if root and os.path.isdir(root):
                tier_key = candidate
                break

    root_path = get_sponsors_tier_root_path(tier_key)
    if not root_path or not os.path.isdir(root_path):
        return None

    preferred = load_language_preference()
    preferred_name = SPONSORS_ENGLISH_FOLDER_NAME if preferred == 'english' else SPONSORS_GREEK_FOLDER_NAME
    preferred_path = os.path.join(root_path, preferred_name)
    if os.path.isdir(preferred_path):
        return preferred_path

    fallback_name = SPONSORS_GREEK_FOLDER_NAME if preferred_name == SPONSORS_ENGLISH_FOLDER_NAME else SPONSORS_ENGLISH_FOLDER_NAME
    fallback_path = os.path.join(root_path, fallback_name)
    if os.path.isdir(fallback_path):
        return fallback_path
    return root_path


def get_existing_sponsors_paths():
    paths = []
    for tier_key in SPONSORS_TIER_ORDER:
        root = get_sponsors_tier_root_path(tier_key)
        if root and os.path.isdir(root):
            paths.append(root)
    return paths


def allowed_roots():
    roots = [os.path.realpath(user_workspace_path()), os.path.realpath(get_preferred_dedsec_root()), os.path.realpath(DEDSEC_OS_ROOT)]
    roots.extend(os.path.realpath(path) for path in get_existing_sponsors_paths())
    return roots


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
    for tier_key in SPONSORS_TIER_ORDER:
        config = SPONSORS_TIERS.get(tier_key)
        sponsors_path = get_sponsors_path(tier_key)
        if config and sponsors_path:
            roots.append({'label': config['root_name'], 'path': sponsors_path})
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
              <button class="btn" id="accessSponsors3Btn">Download Sponsors $3 Tier</button>
              <button class="btn" id="accessSponsors9Btn">Download Sponsors $9 Tier</button>
            </div>
          </div>
          <div class="panel">
            <div class="screen-title" style="font-size:0.92rem;">Credits</div>
            <div class="subtle" id="creditsBlock">Creator: dedsec1121fk
Contributors: gr3ysec, Sal Scar
Art Artists: Christina Chatzidimitriou
Legal Documents: Lampros Spyrou
Discord Server Maintenance: Talha
Past Help: lamprouil, UKI_hunter</div>
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
        'System':'System','Phone-first local workspace':'Phone-first local workspace','Refresh':'Refresh','Files':'Files','Browse and edit text files safely':'Browse and edit text files safely','New Folder':'New Folder','New File':'New File','Paste':'Paste','Editor':'Editor','No file opened':'No file opened','Open a text file to edit it.':'Open a text file to edit it.','Save':'Save','See Sessions':'See Sessions','Sessions':'Sessions','New Session':'New Session','Close':'Close','DedSec Apps':'DedSec Apps','Browse project folders and run scripts':'Browse project folders and run scripts','Linux Store':'Linux Store','Real Termux package actions':'Real Termux package actions','Settings':'Settings','Identity and wallpaper':'Identity and wallpaper','Display name':'Display name','Terminal colors':'Terminal colors','Wallpaper URL or local path':'Wallpaper URL or local path','Wallpaper image upload':'Wallpaper image upload','Save settings':'Save settings','Reset wallpaper':'Reset wallpaper','Toggle Full Screen':'Toggle Full Screen','Apps':'Apps','Open':'Open','Folder':'Folder','File':'File','Runnable file':'Runnable file','Run':'Run','Copy':'Copy','Move':'Move','Delete':'Delete','Go back':'Go back','Installed':'Installed','Not installed':'Not installed','Package':'Package','Running':'Running','Exit':'Exit','No sessions found.':'No sessions found.','Open a text file first':'Open a text file first','File saved':'File saved','Clipboard is empty':'Clipboard is empty','Paste complete':'Paste complete','Move queued':'Move queued','Delete this item?':'Delete this item?','Deleted':'Deleted','Settings saved':'Settings saved','Wallpaper reset':'Wallpaper reset','Folder name':'Folder name','File name':'File name','Copied to clipboard':'Copied to clipboard','Launched':'Launched','Hide Bar':'Hide Bar','Show Bar':'Show Bar','Full Screen':'Full Screen','Project & Menu':'Project & Menu','Prompt username':'Prompt username','Language':'Language','Menu style':'Menu style','Menu auto-start':'Menu auto-start','Save Prompt':'Save Prompt','Apply Language':'Apply Language','Apply Menu Style':'Apply Menu Style','Save Auto-Start':'Save Auto-Start','Project Actions':'Project Actions','Update Project (Source 1)':'Update Project (Source 1)','Update Project (Source 2)':'Update Project (Source 2)','Update Packages & Modules':'Update Packages & Modules','Download Sponsors $3 Tier':'Download Sponsors $3 Tier','Download Sponsors $9 Tier':'Download Sponsors $9 Tier','Credits':'Credits','Saved':'Saved','List Style':'List Style','Grid Style':'Grid Style','Choose By Number':'Choose By Number','DedSec OS':'DedSec OS','Back':'Back','Notifications':'Notifications','Login required':'Login required','Enter your password to unlock DedSec OS.':'Enter your password to unlock DedSec OS.','Username':'Username','Password':'Password','Unlock':'Unlock','Require login password':'Require login password','New password':'New password','Leave blank to keep current password':'Leave blank to keep current password','Wrong password':'Wrong password','Authenticator code':'Authenticator code','Forgot password?':'Forgot password?','Password recovery':'Password recovery','Answer all 3 security questions to reset your password.':'Answer all 3 security questions to reset your password.','Question 1':'Question 1','Question 2':'Question 2','Question 3':'Question 3','Answer 1':'Answer 1','Answer 2':'Answer 2','Answer 3':'Answer 3','Reset password':'Reset password','Enable authenticator app (2FA)':'Enable authenticator app (2FA)','Authenticator secret':'Authenticator secret','Security question 1':'Security question 1','Security question 2':'Security question 2','Security question 3':'Security question 3','Recovery answers do not match.':'Recovery answers do not match.','A 6-digit authenticator code is required.':'A 6-digit authenticator code is required.','Full':'Full','Split':'Split','Terminal':'Terminal','Store':'Store','Theme':'Theme','Menu':'Menu'
      },
      el: {
        'System':'Σύστημα','Phone-first local workspace':'Τοπικός χώρος εργασίας για κινητό','Refresh':'Ανανέωση','Files':'Αρχεία','Browse and edit text files safely':'Περιήγηση και ασφαλής επεξεργασία αρχείων κειμένου','New Folder':'Νέος Φάκελος','New File':'Νέο Αρχείο','Paste':'Επικόλληση','Editor':'Επεξεργαστής','No file opened':'Δεν έχει ανοιχτεί αρχείο','Open a text file to edit it.':'Ανοίξτε ένα αρχείο κειμένου για επεξεργασία.','Save':'Αποθήκευση','See Sessions':'Προβολή Συνεδριών','Sessions':'Συνεδρίες','New Session':'Νέα Συνεδρία','Close':'Κλείσιμο','DedSec Apps':'Εφαρμογές DedSec','Browse project folders and run scripts':'Περιηγηθείτε στους φακέλους του project και εκτελέστε scripts','Linux Store':'Κατάστημα Linux','Real Termux package actions':'Πραγματικές ενέργειες πακέτων Termux','Settings':'Ρυθμίσεις','Identity and wallpaper':'Ταυτότητα και ταπετσαρία','Display name':'Όνομα εμφάνισης','Terminal colors':'Χρώματα τερματικού','Wallpaper URL or local path':'URL ταπετσαρίας ή τοπική διαδρομή','Wallpaper image upload':'Μεταφόρτωση εικόνας ταπετσαρίας','Save settings':'Αποθήκευση ρυθμίσεων','Reset wallpaper':'Επαναφορά ταπετσαρίας','Toggle Full Screen':'Εναλλαγή πλήρους οθόνης','Apps':'Εφαρμογές','Open':'Άνοιγμα','Folder':'Φάκελος','File':'Αρχείο','Runnable file':'Εκτελέσιμο αρχείο','Run':'Εκτέλεση','Copy':'Αντιγραφή','Move':'Μετακίνηση','Delete':'Διαγραφή','Go back':'Επιστροφή','Installed':'Εγκατεστημένο','Not installed':'Μη εγκατεστημένο','Package':'Πακέτο','Running':'Εκτελείται','Exit':'Έξοδος','No sessions found.':'Δεν βρέθηκαν συνεδρίες.','Open a text file first':'Ανοίξτε πρώτα ένα αρχείο κειμένου','File saved':'Το αρχείο αποθηκεύτηκε','Clipboard is empty':'Το πρόχειρο είναι άδειο','Paste complete':'Η επικόλληση ολοκληρώθηκε','Move queued':'Η μετακίνηση μπήκε σε αναμονή','Delete this item?':'Διαγραφή αυτού του στοιχείου;','Deleted':'Διαγράφηκε','Settings saved':'Οι ρυθμίσεις αποθηκεύτηκαν','Wallpaper reset':'Η ταπετσαρία επαναφέρθηκε','Folder name':'Όνομα φακέλου','File name':'Όνομα αρχείου','Copied to clipboard':'Αντιγράφηκε στο πρόχειρο','Launched':'Εκκινήθηκε','Hide Bar':'Απόκρυψη μπάρας','Show Bar':'Εμφάνιση μπάρας','Full Screen':'Πλήρης οθόνη','Project & Menu':'Έργο & Μενού','Prompt username':'Όνομα προτροπής','Language':'Γλώσσα','Menu style':'Στυλ μενού','Menu auto-start':'Αυτόματη εκκίνηση μενού','Save Prompt':'Αποθήκευση προτροπής','Apply Language':'Εφαρμογή γλώσσας','Apply Menu Style':'Εφαρμογή στυλ μενού','Save Auto-Start':'Αποθήκευση αυτόματης εκκίνησης','Project Actions':'Ενέργειες έργου','Update Project (Source 1)':'Ενημέρωση έργου (Πηγή 1)','Update Project (Source 2)':'Ενημέρωση έργου (Πηγή 2)','Update Packages & Modules':'Ενημέρωση πακέτων & modules','Download Sponsors $3 Tier':'Λήψη Sponsors $3 Tier','Download Sponsors $9 Tier':'Λήψη Sponsors $9 Tier','Credits':'Συντελεστές','Saved':'Αποθηκεύτηκε','List Style':'Στυλ λίστας','Grid Style':'Στυλ πλέγματος','Choose By Number':'Επιλογή με αριθμό','DedSec OS':'DedSec OS','Back':'Πίσω','Notifications':'Ειδοποιήσεις','Login required':'Απαιτείται σύνδεση','Enter your password to unlock DedSec OS.':'Εισαγάγετε τον κωδικό σας για να ξεκλειδώσετε το DedSec OS.','Username':'Όνομα χρήστη','Password':'Κωδικός','Unlock':'Ξεκλείδωμα','Require login password':'Απαίτηση κωδικού σύνδεσης','New password':'Νέος κωδικός','Leave blank to keep current password':'Αφήστε κενό για να διατηρηθεί ο τωρινός κωδικός','Wrong password':'Λάθος κωδικός','Authenticator code':'Κωδικός εφαρμογής Authenticator','Forgot password?':'Ξεχάσατε τον κωδικό;','Password recovery':'Ανάκτηση κωδικού','Answer all 3 security questions to reset your password.':'Απαντήστε και στις 3 ερωτήσεις ασφαλείας για επαναφορά του κωδικού.','Question 1':'Ερώτηση 1','Question 2':'Ερώτηση 2','Question 3':'Ερώτηση 3','Answer 1':'Απάντηση 1','Answer 2':'Απάντηση 2','Answer 3':'Απάντηση 3','Reset password':'Επαναφορά κωδικού','Enable authenticator app (2FA)':'Ενεργοποίηση εφαρμογής Authenticator (2FA)','Authenticator secret':'Μυστικό Authenticator','Security question 1':'Ερώτηση ασφαλείας 1','Security question 2':'Ερώτηση ασφαλείας 2','Security question 3':'Ερώτηση ασφαλείας 3','Recovery answers do not match.':'Οι απαντήσεις ανάκτησης δεν ταιριάζουν.','A 6-digit authenticator code is required.':'Απαιτείται 6-ψήφιος κωδικός Authenticator.','Full':'Πλήρης','Split':'Διαίρεση','Terminal':'Τερματικό','Store':'Κατάστημα','Theme':'Θέμα','Menu':'Μενού'
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
      var accessSponsors3Btn = document.getElementById('accessSponsors3Btn'); if (accessSponsors3Btn) accessSponsors3Btn.addEventListener('click', function(){ runSettingsAction('access_sponsors', { tier: '3' }).catch(handleError); });
      var accessSponsors9Btn = document.getElementById('accessSponsors9Btn'); if (accessSponsors9Btn) accessSponsors9Btn.addEventListener('click', function(){ runSettingsAction('access_sponsors', { tier: '9' }).catch(handleError); });
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
        '__SPONSORS_TIERS__': repr(SPONSORS_TIERS),
        '__SPONSORS_TIER_ORDER__': repr(SPONSORS_TIER_ORDER),
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
# VPN / Tor Utilities
# ------------------------------
def network_ensure_dirs():
    try:
        os.makedirs(NETWORK_DATA_DIR, exist_ok=True)
        os.makedirs(NETWORK_TOR_DATA_DIR, exist_ok=True)
    except Exception:
        pass


def network_load_json(path, default_value):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
                return data
    except Exception:
        pass
    return default_value


def network_save_json(path, data):
    network_ensure_dirs()
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
    except Exception:
        pass


def network_default_config():
    return {
        "tor_enabled": False,
        "vpn_enabled": False,
        "country": "US",
        "proxy": "",
        "last_proxy_refresh": 0,
        "last_tools_update": 0,
    }


def network_load_config():
    config = network_default_config()
    saved = network_load_json(NETWORK_CONFIG_PATH, {})
    if isinstance(saved, dict):
        config.update(saved)
    country = str(config.get("country") or "US").upper()
    if country not in NETWORK_COUNTRIES:
        country = "US"
    config["country"] = country
    config["tor_enabled"] = bool(config.get("tor_enabled", False))
    config["vpn_enabled"] = bool(config.get("vpn_enabled", False))
    config["proxy"] = str(config.get("proxy") or "")
    return config


def network_save_config(config):
    clean = network_default_config()
    if isinstance(config, dict):
        clean.update(config)
    clean["country"] = str(clean.get("country") or "US").upper()
    clean["tor_enabled"] = bool(clean.get("tor_enabled", False))
    clean["vpn_enabled"] = bool(clean.get("vpn_enabled", False))
    clean["proxy"] = str(clean.get("proxy") or "")
    network_save_json(NETWORK_CONFIG_PATH, clean)


def network_run(command, capture=False):
    try:
        return subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.STDOUT if capture else None,
        )
    except Exception:
        return None


def network_is_termux():
    prefix = os.environ.get("PREFIX", "")
    return "com.termux" in prefix or "TERMUX_VERSION" in os.environ or os.path.isdir("/data/data/com.termux")


def network_install_python_package(package_name):
    result = network_run([sys.executable, "-m", "pip", "install", "--upgrade", package_name], capture=True)
    return bool(result and result.returncode == 0)


def network_update_tools(silent=False):
    messages = []
    if network_is_termux() and shutil.which("pkg"):
        if not silent:
            print("[*] pkg update ...")
        network_run(["pkg", "update", "-y"])
        network_run(["pkg", "install", "-y", "tor", "openssl", "curl", "wget"])
        messages.append("Termux packages checked")
    if not network_pysocks_available():
        if not silent:
            print("[*] Installing PySocks ...")
        if network_install_python_package("pysocks"):
            messages.append("PySocks checked")
    if not silent:
        print(_("Network tools checked."))
    config = network_load_config()
    config["last_tools_update"] = int(time.time())
    network_save_config(config)
    return messages


def network_local_port_open(host, port, timeout=0.5):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def network_tor_binary():
    return shutil.which("tor")


def network_pysocks_available():
    try:
        import socks  # noqa: F401
        return True
    except Exception:
        return False


def network_tor_running():
    global NETWORK_TOR_PROCESS
    if NETWORK_TOR_PROCESS and NETWORK_TOR_PROCESS.poll() is None and network_local_port_open("127.0.0.1", NETWORK_TOR_SOCKS_PORT):
        return True
    if network_local_port_open("127.0.0.1", NETWORK_TOR_SOCKS_PORT):
        return True
    if NETWORK_TOR_PROCESS and NETWORK_TOR_PROCESS.poll() is not None:
        NETWORK_TOR_PROCESS = None
    return False


def network_install_tor_support(silent=False):
    if not network_tor_binary() or not network_pysocks_available():
        network_update_tools(silent=silent)
    if not network_tor_binary():
        return False, "Tor binary not found. In Termux run: pkg install tor"
    if not network_pysocks_available():
        return False, "PySocks is missing. Run: pip install pysocks"
    return True, _("Tor support ready.")


def network_start_tor(silent=False):
    global NETWORK_TOR_PROCESS
    ok, msg = network_install_tor_support(silent=silent)
    if not ok:
        return False, msg
    if network_tor_running():
        return True, _("Tor is already running.")
    try:
        network_ensure_dirs()
        log_handle = open(NETWORK_TOR_LOG_PATH, "ab")
        NETWORK_TOR_PROCESS = subprocess.Popen(
            [
                network_tor_binary(),
                "--SocksPort", "127.0.0.1:" + str(NETWORK_TOR_SOCKS_PORT),
                "--DataDirectory", NETWORK_TOR_DATA_DIR,
            ],
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            close_fds=True,
        )
        for _ in range(40):
            if network_tor_running():
                return True, _("Tor started on 127.0.0.1:9050.")
            if NETWORK_TOR_PROCESS and NETWORK_TOR_PROCESS.poll() is not None:
                break
            time.sleep(0.5)
        return False, "Tor did not finish bootstrapping yet. Check " + NETWORK_TOR_LOG_PATH
    except Exception as error:
        return False, "Could not start Tor: " + str(error)


def network_stop_tor():
    global NETWORK_TOR_PROCESS
    stopped = False
    if NETWORK_TOR_PROCESS and NETWORK_TOR_PROCESS.poll() is None:
        try:
            NETWORK_TOR_PROCESS.terminate()
            NETWORK_TOR_PROCESS.wait(timeout=5)
            stopped = True
        except Exception:
            try:
                NETWORK_TOR_PROCESS.kill()
                stopped = True
            except Exception:
                pass
        NETWORK_TOR_PROCESS = None

    # If Tor is still listening but was started earlier, try a safe pkill in Termux.
    if network_local_port_open("127.0.0.1", NETWORK_TOR_SOCKS_PORT) and shutil.which("pkill"):
        try:
            subprocess.run(["pkill", "-f", "tor.*SocksPort"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.4)
            stopped = True
        except Exception:
            pass

    if stopped:
        return True, _("Tor stopped.")
    return False, _("Tor was not started by this app.")


def network_tor_proxy():
    return "socks5h://127.0.0.1:" + str(NETWORK_TOR_SOCKS_PORT)


def network_fetch_proxies_from_proxyscrape_v4(country):
    params = {
        "request": "display_proxies",
        "proxy_format": "protocolipport",
        "format": "json",
        "protocol": "http",
        "timeout": 10000,
        "country": (country or "all").lower(),
        "anonymity": "elite",
    }
    out = []
    try:
        response = requests.get("https://api.proxyscrape.com/v4/free-proxy-list/get", params=params, timeout=12)
        data = response.json()
        for item in data.get("proxies", [])[:80]:
            ip = item.get("ip")
            port = item.get("port")
            proto = item.get("protocol") or "http"
            if ip and port and proto in ("http", "https"):
                out.append(proto + "://" + str(ip) + ":" + str(port))
    except Exception:
        pass
    return out


def network_fetch_proxies_from_proxyscrape_legacy(country):
    params = {
        "protocol": "http",
        "country": str(country or "US").upper(),
        "anonymity": "elite",
        "timeout": 10000,
        "format": "json",
    }
    out = []
    try:
        response = requests.get(NETWORK_PROXY_API, params=params, timeout=12)
        data = response.json()
        for item in data.get("proxies", [])[:60]:
            ip = item.get("ip")
            port = item.get("port")
            proto = item.get("protocol") or "http"
            if ip and port and proto in ("http", "https"):
                out.append(proto + "://" + str(ip) + ":" + str(port))
    except Exception:
        pass
    return out


def network_fetch_proxies_from_geonode(country):
    params = {
        "limit": 80,
        "page": 1,
        "sort_by": "lastChecked",
        "sort_type": "desc",
        "filterLastChecked": 90,
        "country": str(country or "US").upper(),
        "protocols": "http,https",
    }
    out = []
    try:
        response = requests.get("https://proxylist.geonode.com/api/proxy-list", params=params, timeout=12)
        data = response.json()
        for item in data.get("data", [])[:80]:
            ip = item.get("ip")
            port = item.get("port")
            protocols = item.get("protocols") or []
            proto = "https" if "https" in protocols else "http"
            if ip and port:
                out.append(proto + "://" + str(ip) + ":" + str(port))
    except Exception:
        pass
    return out


def network_load_proxy_state():
    state = network_load_json(NETWORK_PROXY_STATE_FILE, {})
    return state if isinstance(state, dict) else {}


def network_save_proxy_state(state):
    network_save_json(NETWORK_PROXY_STATE_FILE, state)


def network_get_bad_proxy_map(country):
    key = str(country or "US").upper()
    state = network_load_proxy_state()
    bucket = state.get(key, {}) if isinstance(state.get(key, {}), dict) else {}
    now = int(time.time())
    cleaned = {}
    for proxy, expiry in bucket.items():
        try:
            if int(expiry) > now:
                cleaned[proxy] = int(expiry)
        except Exception:
            pass
    if cleaned != bucket:
        if cleaned:
            state[key] = cleaned
        elif key in state:
            del state[key]
        network_save_proxy_state(state)
    return cleaned


def network_mark_proxy_bad(country, proxy, ttl=NETWORK_BAD_PROXY_TTL):
    if not proxy:
        return
    state = network_load_proxy_state()
    key = str(country or "US").upper()
    bucket = state.setdefault(key, {})
    bucket[proxy] = int(time.time()) + int(ttl)
    network_save_proxy_state(state)


def network_mark_proxy_good(country, proxy):
    state = network_load_proxy_state()
    key = str(country or "US").upper()
    bucket = state.get(key, {})
    if proxy in bucket:
        del bucket[proxy]
        if bucket:
            state[key] = bucket
        elif key in state:
            del state[key]
        network_save_proxy_state(state)


def network_is_proxy_marked_bad(country, proxy):
    if not proxy:
        return True
    return proxy in network_get_bad_proxy_map(country)


def network_fetch_proxy_pool(country, force_refresh=False):
    network_ensure_dirs()
    cache = network_load_json(NETWORK_PROXY_CACHE_FILE, {})
    key = str(country or "US").upper()
    now = int(time.time())
    cached = cache.get(key) if isinstance(cache, dict) else None
    gathered = []

    if (not force_refresh) and cached and now - int(cached.get("ts", 0)) < NETWORK_PROXY_CACHE_TTL:
        gathered = cached.get("items", [])
    else:
        seen = set()
        for loader in (network_fetch_proxies_from_proxyscrape_v4, network_fetch_proxies_from_geonode, network_fetch_proxies_from_proxyscrape_legacy):
            for proxy in loader(key):
                if proxy and proxy not in seen:
                    seen.add(proxy)
                    gathered.append(proxy)
        if isinstance(cache, dict):
            cache[key] = {"ts": now, "items": gathered}
            network_save_json(NETWORK_PROXY_CACHE_FILE, cache)

    bad = network_get_bad_proxy_map(key)
    clean = [proxy for proxy in gathered if proxy not in bad]
    return clean


def network_test_proxy(proxy):
    try:
        response = requests.get(
            "https://api.ipify.org",
            timeout=7,
            proxies={"http": proxy, "https": proxy},
            headers={"User-Agent": "DedSec Settings Network Check/1.0"},
        )
        return response.status_code == 200 and bool(response.text.strip())
    except Exception:
        return False


def network_select_working_proxy(country, force_refresh=False, silent=False):
    pool = network_fetch_proxy_pool(country, force_refresh=force_refresh)
    if not pool:
        return "", _("No working proxy found for this country right now. Try renew or choose another location.")
    tests = 0
    for proxy in pool:
        tests += 1
        if not silent:
            print("[*] Testing VPN proxy " + str(tests) + "/" + str(min(len(pool), NETWORK_MAX_PROXY_TESTS)) + " ...")
        if network_test_proxy(proxy):
            network_mark_proxy_good(country, proxy)
            return proxy, _("VPN proxy ready") + ": " + proxy
        network_mark_proxy_bad(country, proxy)
        if tests >= NETWORK_MAX_PROXY_TESTS:
            break

    return "", _("No working proxy found for this country right now. Try renew or choose another location.")


def network_remove_bashrc_export_block(content):
    pattern = re.compile(
        re.escape(NETWORK_BASHRC_START_MARKER) + r".*?" + re.escape(NETWORK_BASHRC_END_MARKER) + r"\n?",
        re.DOTALL,
    )
    return pattern.sub("", content)


def network_apply_bashrc_exports():
    """Write VPN/Tor proxy exports and a new-session guard into bash.bashrc.

    New shells cannot inherit variables from the already-running Settings.py
    process, so this writes the current proxy state into bash.bashrc. It also
    installs a small shell guard that quietly starts Tor again when Tor is
    enabled and a new Termux session opens. Tor takes priority over the HTTP
    proxy because it is the safer route when both are enabled.
    """
    config = network_load_config()
    try:
        os.makedirs(os.path.dirname(BASHRC_PATH), exist_ok=True)
        if os.path.exists(BASHRC_PATH):
            with open(BASHRC_PATH, "r", encoding="utf-8") as handle:
                content = handle.read()
        else:
            content = ""
        content = network_remove_bashrc_export_block(content).rstrip() + "\n\n"

        exports = []
        if config.get("tor_enabled"):
            tor_proxy = network_tor_proxy()
            exports.extend([
                'export ALL_PROXY="' + tor_proxy + '"',
                'export all_proxy="' + tor_proxy + '"',
                'export HTTP_PROXY="' + tor_proxy + '"',
                'export HTTPS_PROXY="' + tor_proxy + '"',
                'export http_proxy="' + tor_proxy + '"',
                'export https_proxy="' + tor_proxy + '"',
                'export DEDSEC_NETWORK_MODE="tor"',
            ])
        elif config.get("vpn_enabled") and config.get("proxy"):
            proxy = str(config.get("proxy"))
            exports.extend([
                'export HTTP_PROXY="' + proxy + '"',
                'export HTTPS_PROXY="' + proxy + '"',
                'export http_proxy="' + proxy + '"',
                'export https_proxy="' + proxy + '"',
                "unset ALL_PROXY",
                "unset all_proxy",
                'export DEDSEC_NETWORK_MODE="vpn"',
            ])
        else:
            exports.extend([
                "unset HTTP_PROXY",
                "unset HTTPS_PROXY",
                "unset http_proxy",
                "unset https_proxy",
                "unset ALL_PROXY",
                "unset all_proxy",
                'export DEDSEC_NETWORK_MODE="off"',
            ])

        safe_settings_path = SETTINGS_SCRIPT_PATH.replace('"', '\\"')
        guard_lines = [
            'DEDSEC_NETWORK_SETTINGS="' + safe_settings_path + '"',
            "DEDSEC_NETWORK_LAST=0",
            "dedsec_network_session_guard() {",
            "    local now=\"$(date +%s 2>/dev/null || echo 0)\"",
            "    local interval=\"" + str(NETWORK_SESSION_GUARD_INTERVAL_SECONDS) + "\"",
            "    if [ -z \"$now\" ]; then now=0; fi",
            "    if [ -z \"$DEDSEC_NETWORK_LAST\" ]; then DEDSEC_NETWORK_LAST=0; fi",
            "    if [ $((now - DEDSEC_NETWORK_LAST)) -ge $interval ]; then",
            "        DEDSEC_NETWORK_LAST=\"$now\"",
            "        if [ -f \"$DEDSEC_NETWORK_SETTINGS\" ]; then",
            "            (python3 \"$DEDSEC_NETWORK_SETTINGS\" " + NETWORK_SESSION_GUARD_COMMAND + " >/dev/null 2>&1 &)",
            "        fi",
            "    fi",
            "}",
            "dedsec_network_session_guard",
            "case \"$PROMPT_COMMAND\" in",
            "    *dedsec_network_session_guard*) ;;",
            "    *) PROMPT_COMMAND=\"dedsec_network_session_guard${PROMPT_COMMAND:+;$PROMPT_COMMAND}\" ;;",
            "esac",
        ]

        block = NETWORK_BASHRC_START_MARKER + "\n" + "\n".join(exports + guard_lines) + "\n" + NETWORK_BASHRC_END_MARKER + "\n"
        with open(BASHRC_PATH, "w", encoding="utf-8") as handle:
            handle.write(content + block)
    except Exception as error:
        print("[!] Failed to update network exports: " + str(error))

def network_status_lines():
    config = network_load_config()
    country = config.get("country", "US")
    lines = [
        _("Tor Connection") + ": " + (_("Enabled") if config.get("tor_enabled") else _("Disabled")) + " / " + (_("Running") if network_tor_running() else _("Stopped")),
        _("VPN Connection") + ": " + (_("Enabled") if config.get("vpn_enabled") else _("Disabled")),
        _("Country") + ": " + country + " - " + NETWORK_COUNTRIES.get(country, country),
        _("Current proxy") + ": " + (config.get("proxy") or _("No proxy selected")),
        _("New sessions") + ": " + _("Covered by bash.bashrc hook"),
    ]
    return lines


def network_print_status():
    print("=== " + _("Network Utilities") + " ===")
    for line in network_status_lines():
        print(line)


def network_enable_tor():
    config = network_load_config()
    ok, msg = network_start_tor(silent=False)
    if ok:
        config["tor_enabled"] = True
        # Tor takes priority over the HTTP proxy because it is more private when active.
        network_save_config(config)
        network_apply_bashrc_exports()
    print(msg)
    if ok:
        print(_("Network exports updated. Restart Termux or open a new shell to apply them everywhere."))


def network_disable_tor():
    config = network_load_config()
    ok, msg = network_stop_tor()
    config["tor_enabled"] = False
    network_save_config(config)
    network_apply_bashrc_exports()
    print(msg)
    print(_("Network exports updated. Restart Termux or open a new shell to apply them everywhere."))


def network_enable_vpn(force_refresh=False):
    config = network_load_config()
    country = config.get("country", "US")
    existing_proxy = str(config.get("proxy") or "").strip()

    # Do not test the saved proxy every time. Reuse it unless the user renews
    # proxies, changes country, has no saved proxy, or it was previously marked bad.
    if existing_proxy and not force_refresh and not network_is_proxy_marked_bad(country, existing_proxy):
        config["vpn_enabled"] = True
        config["proxy"] = existing_proxy
        network_save_config(config)
        network_apply_bashrc_exports()
        print(_("VPN proxy ready") + ": " + existing_proxy)
        print(_("Saved VPN proxy reused without retesting."))
        print(_("Network exports updated. Restart Termux or open a new shell to apply them everywhere."))
        return

    if existing_proxy and network_is_proxy_marked_bad(country, existing_proxy):
        print(_("Saved proxy was previously marked as bad. Searching for a new one."))

    proxy, msg = network_select_working_proxy(country, force_refresh=force_refresh, silent=False)
    if proxy:
        config["vpn_enabled"] = True
        config["proxy"] = proxy
        config["last_proxy_refresh"] = int(time.time())
        network_save_config(config)
        network_apply_bashrc_exports()
    print(msg)
    if proxy:
        print(_("Network exports updated. Restart Termux or open a new shell to apply them everywhere."))


def network_disable_vpn():
    config = network_load_config()
    config["vpn_enabled"] = False
    config["proxy"] = ""
    network_save_config(config)
    network_apply_bashrc_exports()
    print(_("VPN Connection") + ": " + _("Disabled"))
    print(_("Network exports updated. Restart Termux or open a new shell to apply them everywhere."))


def network_choose_vpn_location():
    config = network_load_config()
    countries = sorted(NETWORK_COUNTRIES.items(), key=lambda item: item[1].lower())
    print("=== " + _("Choose VPN Location") + " ===")
    for index, (code, name) in enumerate(countries, start=1):
        current = " *" if code == config.get("country") else ""
        print(str(index) + ". " + code + " - " + name + current)
    choice = input(_("Enter the number of your choice: ")).strip()
    try:
        selected_index = int(choice) - 1
        if selected_index < 0 or selected_index >= len(countries):
            raise ValueError()
    except Exception:
        print(_("Invalid selection. Please try again."))
        return

    country_code, country_name = countries[selected_index]
    config["country"] = country_code
    config["proxy"] = ""
    network_save_config(config)
    print(_("Selected VPN location") + ": " + country_code + " - " + country_name)

    if config.get("vpn_enabled"):
        network_enable_vpn(force_refresh=True)


def network_renew_vpn_proxies():
    config = network_load_config()
    country = config.get("country", "US")
    if config.get("vpn_enabled"):
        network_enable_vpn(force_refresh=True)
        return

    # Refresh the pool without turning VPN on when the user has VPN disabled.
    pool = network_fetch_proxy_pool(country, force_refresh=True)
    print(str(len(pool)) + " proxies cached for " + country + ".")
    print(_("VPN is disabled. Proxies were refreshed but no proxy was activated."))


def network_renew_tools_and_connections():
    network_update_tools(silent=False)
    config = network_load_config()
    if config.get("tor_enabled"):
        ok, msg = network_start_tor(silent=False)
        print(msg)
    if config.get("vpn_enabled"):
        network_enable_vpn(force_refresh=True)
    else:
        # Refresh the currently selected country pool even if VPN is off.
        country = config.get("country", "US")
        pool = network_fetch_proxy_pool(country, force_refresh=True)
        print(str(len(pool)) + " proxies cached for " + country + ".")
    network_apply_bashrc_exports()


def network_autostart_if_enabled(silent=True):
    config = network_load_config()
    changed = False
    if config.get("tor_enabled"):
        network_start_tor(silent=silent)
        changed = True
    if config.get("vpn_enabled"):
        country = config.get("country", "US")
        proxy = str(config.get("proxy") or "").strip()
        if (not proxy) or network_is_proxy_marked_bad(country, proxy):
            new_proxy, _msg = network_select_working_proxy(country, force_refresh=False, silent=True)
            if new_proxy:
                config["proxy"] = new_proxy
                config["last_proxy_refresh"] = int(time.time())
                network_save_config(config)
                changed = True
        # When a saved proxy exists and is not marked bad, do not test it on startup.
    if changed or config.get("tor_enabled") or config.get("vpn_enabled"):
        network_apply_bashrc_exports()


def network_session_guard():
    """Quietly refresh VPN/Tor support for new Termux sessions.

    This is called from bash.bashrc. It keeps the saved proxy exports current and
    restarts Tor if Tor was enabled but the process is not listening anymore. It
    does not print anything because it runs during shell startup/prompt repair.
    """
    try:
        network_autostart_if_enabled(silent=True)
        network_apply_bashrc_exports()
        return True
    except Exception:
        return False


def network_utilities_menu():
    while True:
        os.system("clear")
        network_print_status()
        config = network_load_config()
        options = [
            _("Disable Tor Connection") if config.get("tor_enabled") else _("Enable Tor Connection"),
            _("Disable VPN Connection") if config.get("vpn_enabled") else _("Enable VPN Connection"),
            _("Choose VPN Location"),
            _("Renew VPN Proxies"),
            _("Update VPN/Tor Tools"),
            _("Show VPN/Tor Status"),
            _("Back"),
        ]
        print("")
        for index, option in enumerate(options, start=1):
            print(str(index) + ". " + option)
        choice = input("\n" + _("Enter the number of your choice: ")).strip()

        os.system("clear")
        if choice == "1":
            if config.get("tor_enabled"):
                network_disable_tor()
            else:
                network_enable_tor()
        elif choice == "2":
            if config.get("vpn_enabled"):
                network_disable_vpn()
            else:
                network_enable_vpn(force_refresh=False)
        elif choice == "3":
            network_choose_vpn_location()
        elif choice == "4":
            network_renew_vpn_proxies()
        elif choice == "5":
            network_renew_tools_and_connections()
        elif choice == "6":
            network_print_status()
        elif choice == "7" or choice.lower() in ("b", "back", "q", "quit"):
            break
        else:
            print(_("Invalid selection. Please try again."))
        input("\n" + _("Press Enter to continue..."))


# ----------------------------------------------------------------------
# --- QUIET INTERNAL SECTION: ORTHODOX PRAYER REFERENCE NOTES ---
# ----------------------------------------------------------------------
# Ordinary source comments only. This section is not connected to menus,
# logs, notifications, achievements, prompts, startup hooks, or UI output.
# Future updates should keep this section non-executable and should not
# treat these notes as feature logic.
#
# Greek - Πάτερ ἡμῶν:
# Πάτερ ἡμῶν ὁ ἐν τοῖς οὐρανοῖς,
# ἁγιασθήτω τὸ ὄνομά σου·
# ἐλθέτω ἡ βασιλεία σου·
# γενηθήτω τὸ θέλημά σου,
# ὡς ἐν οὐρανῷ καὶ ἐπὶ τῆς γῆς·
# τὸν ἄρτον ἡμῶν τὸν ἐπιούσιον
# δὸς ἡμῖν σήμερον·
# καὶ ἄφες ἡμῖν τὰ ὀφειλήματα ἡμῶν,
# ὡς καὶ ἡμεῖς ἀφίεμεν τοῖς ὀφειλέταις ἡμῶν·
# καὶ μὴ εἰσενέγκῃς ἡμᾶς εἰς πειρασμόν,
# ἀλλὰ ῥῦσαι ἡμᾶς ἀπὸ τοῦ πονηροῦ.
# Ἀμήν.
#
# English - The Lord's Prayer:
# Our Father, who art in heaven,
# hallowed be Thy name;
# Thy kingdom come;
# Thy will be done on earth as it is in heaven;
# give us this day our daily bread;
# and forgive us our debts, as we forgive our debtors;
# and lead us not into temptation,
# but deliver us from the evil one.
# Amen.
#
# Greek - Πιστεύω εἰς ἕνα Θεόν:
# Πιστεύω εἰς ἕνα Θεόν, Πατέρα, Παντοκράτορα,
# ποιητὴν οὐρανοῦ καὶ γῆς, ὁρατῶν τε πάντων καὶ ἀοράτων.
# Καὶ εἰς ἕνα Κύριον Ἰησοῦν Χριστόν,
# τὸν Υἱὸν τοῦ Θεοῦ τὸν Μονογενῆ,
# τὸν ἐκ τοῦ Πατρὸς γεννηθέντα πρὸ πάντων τῶν αἰώνων.
# Φῶς ἐκ Φωτός, Θεὸν ἀληθινὸν ἐκ Θεοῦ ἀληθινοῦ,
# γεννηθέντα, οὐ ποιηθέντα, ὁμοούσιον τῷ Πατρί,
# δι' οὗ τὰ πάντα ἐγένετο.
# Τὸν δι' ἡμᾶς τοὺς ἀνθρώπους καὶ διὰ τὴν ἡμετέραν σωτηρίαν
# κατελθόντα ἐκ τῶν οὐρανῶν,
# καὶ σαρκωθέντα ἐκ Πνεύματος Ἁγίου καὶ Μαρίας τῆς Παρθένου,
# καὶ ἐνανθρωπήσαντα.
# Σταυρωθέντα τε ὑπὲρ ἡμῶν ἐπὶ Ποντίου Πιλάτου,
# καὶ παθόντα, καὶ ταφέντα.
# Καὶ ἀναστάντα τῇ τρίτῃ ἡμέρᾳ κατὰ τὰς Γραφάς.
# Καὶ ἀνελθόντα εἰς τοὺς οὐρανούς,
# καὶ καθεζόμενον ἐκ δεξιῶν τοῦ Πατρός.
# Καὶ πάλιν ἐρχόμενον μετὰ δόξης κρῖναι ζῶντας καὶ νεκρούς,
# οὗ τῆς βασιλείας οὐκ ἔσται τέλος.
# Καὶ εἰς τὸ Πνεῦμα τὸ Ἅγιον, τὸ Κύριον, τὸ Ζωοποιόν,
# τὸ ἐκ τοῦ Πατρὸς ἐκπορευόμενον,
# τὸ σὺν Πατρὶ καὶ Υἱῷ συμπροσκυνούμενον καὶ συνδοξαζόμενον,
# τὸ λαλῆσαν διὰ τῶν Προφητῶν.
# Εἰς μίαν, ἁγίαν, καθολικὴν καὶ ἀποστολικὴν Ἐκκλησίαν.
# Ὁμολογῶ ἓν βάπτισμα εἰς ἄφεσιν ἁμαρτιῶν.
# Προσδοκῶ ἀνάστασιν νεκρῶν.
# Καὶ ζωὴν τοῦ μέλλοντος αἰῶνος. Ἀμήν.
#
# English - The Creed:
# I believe in one God, the Father Almighty,
# Maker of heaven and earth, and of all things visible and invisible.
# And in one Lord Jesus Christ, the only-begotten Son of God,
# begotten of the Father before all ages.
# Light from Light, true God from true God,
# begotten, not made, of one essence with the Father,
# through whom all things were made.
# For us human beings and for our salvation He came down from heaven,
# and was incarnate by the Holy Spirit and the Virgin Mary,
# and became human.
# He was crucified for us under Pontius Pilate, suffered, and was buried.
# And He rose on the third day according to the Scriptures.
# And He ascended into heaven and sits at the right hand of the Father.
# And He shall come again with glory to judge the living and the dead,
# and His kingdom shall have no end.
# And in the Holy Spirit, the Lord, the Giver of Life,
# who proceeds from the Father,
# who together with the Father and the Son is worshipped and glorified,
# who spoke through the Prophets.
# In one, holy, catholic, and apostolic Church.
# I confess one baptism for the forgiveness of sins.
# I await the resurrection of the dead.
# And the life of the age to come. Amen.
#
# Greek - Δόξα σοι / Ἀναστήτω ὁ Θεός:
# Δόξα σοι, ὁ Θεὸς ἡμῶν, δόξα σοι.
# Ἀναστήτω ὁ Θεός, καὶ διασκορπισθήτωσαν οἱ ἐχθροὶ αὐτοῦ,
# καὶ φυγέτωσαν ἀπὸ προσώπου αὐτοῦ οἱ μισοῦντες αὐτόν.
# Ὡς ἐκλείπει καπνός, ἐκλιπέτωσαν·
# ὡς τήκεται κηρὸς ἀπὸ προσώπου πυρός,
# οὕτως ἀπολοῦνται οἱ ἁμαρτωλοὶ ἀπὸ προσώπου τοῦ Θεοῦ·
# καὶ οἱ δίκαιοι εὐφρανθήτωσαν.
#
# English - Glory to You / Let God arise:
# Glory to You, our God, glory to You.
# Let God arise, and let His enemies be scattered;
# let those who hate Him flee from before His face.
# As smoke vanishes, so let them vanish;
# as wax melts before fire,
# so let sinners perish before the face of God;
# and let the righteous rejoice.
# ----------------------------------------------------------------------

# ------------------------------
# Settings Menu with Different Styles
# ------------------------------
def ensure_required_settings_menu_items(options):
    """Keeps important Settings entries visible even if older lists are reused."""
    sponsors_label = _("Access Sponsors-Only Scripts")
    if sponsors_label not in options:
        try:
            update_packages_index = options.index(_("Update Packages & Modules"))
            options.insert(update_packages_index + 1, sponsors_label)
        except ValueError:
            options.insert(4, sponsors_label)
    return options

def get_settings_options():
    options = [
        _("About"),
        _("DedSec Project Update (Source 1)"),
        _("DedSec Project Update (Source 2)"),
        _("Update Packages & Modules"),
        _("Access Sponsors-Only Scripts"),
        _("Save DedSec Project"),
        _("Change Prompt"),
        _("GitHub Account"),
        _("Termux Usage Stats"),
        _("Achievements"),
        _("VPN & Tor Utilities"),
        _("Change Menu Style"),
        get_menu_autostart_label(),
        _("Choose Language/Επιλέξτε Γλώσσα"),
        _("Credits"),
        _("Uninstall DedSec Project"),
        _("Exit")
    ]
    return ensure_required_settings_menu_items(options)


def run_settings_list_menu():
    """Settings menu using list style (curses)"""
    def menu(stdscr):
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        menu_options = get_settings_options()
        current_row = 0
        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()
            title = _("Select an option")
            safe_curses_addstr(stdscr, 1, width // 2 - len(title) // 2, title)
            for idx, option in enumerate(menu_options):
                x = width // 2 - len(option) // 2
                y = height // 2 - len(menu_options) // 2 + idx
                if idx == current_row:
                    stdscr.attron(curses.A_REVERSE)
                    safe_curses_addstr(stdscr, y, x, option)
                    stdscr.attroff(curses.A_REVERSE)
                else:
                    safe_curses_addstr(stdscr, y, x, option)
            stdscr.refresh()
            key = stdscr.getch()
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(menu_options) - 1:
                current_row += 1
            elif key in [curses.KEY_ENTER, 10, 13]:
                return current_row
            elif key in [ord('q'), ord('Q')]:
                return None
    
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
                safe_curses_addstr(stdscr, 0, 0, _("Terminal window is too small."))
                stdscr.refresh()
                key = stdscr.getch()
                if key in [ord('q'), ord('Q'), 10, 13]:
                    return None
                continue

            # Draw title
            title = _("Select an option")
            try:
                safe_curses_addstr(stdscr, 0, term_width // 2 - len(title) // 2, title, curses.color_pair(3))
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
                            safe_curses_addstr(stdscr, line_y, line_x, line[:term_width - line_x], color)
                        except curses.error:
                            pass
            
            # Draw instructions
            instructions = f"Arrow Keys: Move | Enter: Select | q: Quit"
            try:
                safe_curses_addstr(stdscr, term_height - 1, 0, instructions[:term_width - 1], curses.color_pair(3))
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

    menu_options = get_settings_options()
    
    return curses.wrapper(lambda stdscr: draw_settings_grid_menu(stdscr, menu_options))

def run_settings_number_menu():
    """Settings menu using number style"""
    menu_options = get_settings_options()
    
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
        achievements_ensure_constant_background_checker(silent=True, install_hook=False)
        should_exit = False
        pause_without_text = False

        selected = run_settings_menu()
        if selected is None:
            print(_("Exiting..."))
            break

        os.system("clear")
        achievements_record_event("settings_actions")
        achievements_record_event("settings_choice_" + str(selected))
        if selected == 0:
            show_about()
        elif selected == 1:
            update_dedsec_source_1()
        elif selected == 2:
            update_dedsec_source_2()
        elif selected == 3:
            update_packages_modules()
        elif selected == 4:
            access_sponsors_only_scripts()
        elif selected == 5:
            save_project()
            pause_without_text = True
        elif selected == 6:
            change_prompt()
        elif selected == 7:
            github_account_menu()
        elif selected == 8:
            show_termux_usage_stats()
        elif selected == 9:
            achievements_menu()
        elif selected == 10:
            network_utilities_menu()
        elif selected == 11:
            change_menu_style()
        elif selected == 12:
            toggle_menu_autostart()
        elif selected == 13:
            change_language()
        elif selected == 14:
            show_credits()
        elif selected == 15:
            should_exit = uninstall_dedsec()
            if should_exit:
                break
        elif selected == 16:
            print(_("Exiting..."))
            break

        achievements_ensure_constant_background_checker(silent=True, install_hook=False)
        achievements_check_and_unlock(silent=False, source="settings_action")

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

        if len(sys.argv) > 1 and sys.argv[1] == NETWORK_SESSION_GUARD_COMMAND:
            network_session_guard()
            sys.exit(0)

        if len(sys.argv) > 1 and sys.argv[1] in ("--achievement-test", "--achievements-test", "--test-achievement"):
            test_value = sys.argv[2] if len(sys.argv) > 2 else "1"
            achievements_ensure_constant_background_checker(silent=True, install_hook=False)
            ok = achievements_test_command(test_value)
            sys.exit(0 if ok else 1)

        if len(sys.argv) > 1 and sys.argv[1] == "--achievements-start":
            achievements_ensure_constant_background_checker(silent=True, install_hook=False)
            sys.exit(0)

        if len(sys.argv) > 1 and sys.argv[1] == "--achievements-ensure":
            achievements_ensure_constant_background_checker(silent=True, install_hook=False)
            sys.exit(0)

        if len(sys.argv) > 1 and sys.argv[1] == "--achievements-watchdog":
            achievements_run_watchdog()
            sys.exit(0)

        if len(sys.argv) > 1 and sys.argv[1] == "--achievements-daemon":
            achievements_run_daemon()
            sys.exit(0)
        
        create_backup_zip_if_not_exists()
        apply_github_prompt_if_connected()
        network_autostart_if_enabled(silent=True)
        achievements_record_event("settings_started")
        achievements_ensure_constant_background_checker(silent=True)
        achievements_check_and_unlock(silent=True, source="startup")
        
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