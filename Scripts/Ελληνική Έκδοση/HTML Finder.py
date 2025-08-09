import os
import tempfile
import subprocess
import sys
from urllib.parse import urljoin, urlparse, unquote
import re
import time

# --- Configuration ---
# Μπορείτε να αλλάξετε το 'nano' σε 'vim' ή σε άλλο πρόγραμμα επεξεργασίας γραμμής εντολών αν προτιμάτε
EDITOR = os.environ.get('EDITOR', 'nano')

# Βασικός κατάλογος για όλες τις λήψεις μέσα στον αποθηκευτικό χώρο του Termux
# Αυτό συνήθως αντιστοιχεί στο /sdcard/Download στη συσκευή σας Android
TERMUX_DOWNLOADS_BASE = os.path.join(os.path.expanduser('~'), 'storage', 'downloads')

# Asset mapping: (tag_name, attribute_name, subdirectory, [optional_filter_function])
# The filter_function takes the BeautifulSoup tag as input and returns True if it matches.
ASSET_MAP = [
    ('link', 'href', 'css', lambda tag: tag.get('rel') and 'stylesheet' in tag['rel']),
    ('script', 'src', 'js', None),
    ('img', 'src', 'images', None),
    ('source', 'src', 'media', None),
    ('video', 'poster', 'images', None),
    ('link', 'href', 'icons', lambda tag: tag.get('rel') and any(r in ['icon', 'shortcut icon'] for r in tag['rel'])),
]

# Regex to find background-image URLs in inline style attributes
INLINE_CSS_URL_REGEX = re.compile(r'url\([\'"]?(.*?[\'"]?)\)')

# --- Helper Functions ---

def display_message(message, color='default'):
    """Prints a message to the console with optional color."""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'default': '\033[0m'
    }
    sys.stdout.write(f"{colors.get(color, colors['default'])}{message}{colors['default']}\n")
    sys.stdout.flush()

def run_command(command, check_success=True, message=None):
    """Runs a shell command and displays messages."""
    if message:
        display_message(message, 'cyan')
    try:
        result = subprocess.run(command, check=check_success, capture_output=True, text=True, shell=True)
        if check_success and result.returncode != 0:
            display_message(f"Η εντολή απέτυχε: {' '.join(command)}\n{result.stderr}", 'red')
            return False
        return True
    except FileNotFoundError:
        display_message(f"Η εντολή δεν βρέθηκε: {command[0].split()[0]}", 'red')
        return False
    except Exception as e:
        display_message(f"Σφάλμα κατά την εκτέλεση της εντολής '{' '.join(command)}': {e}", 'red')
        return False

def check_and_install_pip_package(package_name):
    """Checks if a pip package is installed and offers to install it."""
    try:
        __import__(package_name.split('==')[0].split('<')[0].split('>')[0].split('~')[0])
        display_message(f"Το πακέτο Python '{package_name}' είναι ήδη εγκατεστημένο.", 'green')
        return True
    except ImportError:
        display_message(f"Το πακέτο Python '{package_name}' δεν είναι εγκατεστημένο.", 'yellow')
        choice = input(f"Θέλετε να το εγκαταστήσετε τώρα; (y/n): ").lower().strip()
        if choice == 'y':
            return run_command(f"pip install {package_name}", message=f"Εγκατάσταση του {package_name}...")
        else:
            display_message(f"Το '{package_name}' είναι απαραίτητο για την πλήρη λειτουργικότητα. Έξοδος.", 'red')
            return False

def check_and_install_termux_package(package_name, command_to_check=None):
    """Checks if a Termux package is installed and offers to install it."""
    if command_to_check is None:
        command_to_check = package_name

    if subprocess.run(f"which {command_to_check}", shell=True, capture_output=True).returncode == 0:
        display_message(f"Το πακέτο Termux '{package_name}' ({command_to_check}) είναι ήδη εγκατεστημένο.", 'green')
        return True
    else:
        display_message(f"Το πακέτο Termux '{package_name}' ({command_to_check}) δεν είναι εγκατεστημένο.", 'yellow')
        choice = input(f"Θέλετε να το εγκαταστήσετε τώρα μέσω του 'pkg install {package_name}'; (y/n): ").lower().strip()
        if choice == 'y':
            return run_command(f"pkg install {package_name} -y", message=f"Εγκατάσταση του {package_name}...")
        else:
            display_message(f"Το '{package_name}' είναι απαραίτητο για την πλήρη λειτουργικότητα. Έξοδος.", 'red')
            return False

def check_storage_permission():
    """Checks if Termux has storage permission and prompts if not."""
    test_file_path = os.path.join(TERMUX_DOWNLOADS_BASE, f".test_permission_{os.getpid()}")
    try:
        os.makedirs(TERMUX_DOWNLOADS_BASE, exist_ok=True)
        with open(test_file_path, 'w') as f:
            f.write("test")
        os.remove(test_file_path)
        display_message("Η άδεια αποθήκευσης έχει παραχωρηθεί.", 'green')
        return True
    except PermissionError:
        display_message("Η άδεια αποθήκευσης δεν έχει παραχωρηθεί για το Termux.", 'red')
        display_message("Πρέπει να εκτελέσετε το 'termux-setup-storage' και να παραχωρήσετε την άδεια.", 'yellow')
        choice = input("Θέλετε να εκτελέσετε το 'termux-setup-storage' τώρα; (y/n): ").lower().strip()
        if choice == 'y':
            run_command("termux-setup-storage", check_success=False, message="Εκτέλεση του termux-setup-storage...")
            display_message("Παρακαλώ ακολουθήστε τις οδηγίες για να παραχωρήσετε την άδεια αποθήκευσης. Επανεκκινήστε το script μετά την παραχώρηση.", 'yellow')
            return False
        else:
            display_message("Η άδεια αποθήκευσης είναι απαραίτητη για την αποθήκευση αρχείων. Έξοδος.", 'red')
            return False
    except Exception as e:
        display_message(f"Σφάλμα κατά τον έλεγχο της άδειας αποθήκευσης: {e}", 'red')
        return False

def get_website_name(url):
    """Extracts a clean, filesystem-friendly name from a URL."""
    parsed_url = urlparse(url)
    hostname = parsed_url.netloc
    if hostname.startswith('www.'):
        hostname = hostname[4:]
    clean_name = hostname.replace('.', '_').replace(':', '_')
    if not clean_name:
        path_segments = [s for s in parsed_url.path.split('/') if s]
        if path_segments:
            clean_name = path_segments[0].replace('.', '_').replace(':', '_')
        else:
            clean_name = "website_content"
    return clean_name.lower()

def get_download_base_dir(website_name):
    """Constructs the full path for the website's download directory."""
    return os.path.join(TERMUX_DOWNLOADS_BASE, website_name)

def ensure_directory_exists(path):
    """Creates a directory if it doesn't exist."""
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as e:
        display_message(f"Σφάλμα κατά τη δημιουργία του καταλόγου '{path}': {e}", 'red')
        return False
    return True

def fetch_html(url):
    """
    Fetches HTML content from the given URL.
    Handles common HTTP and network errors.
    """
    display_message(f"Προσπάθεια λήψης HTML από: {url}", 'cyan')
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        display_message("Το HTML λήφθηκε με επιτυχία!", 'green')
        return response.text
    except requests.exceptions.HTTPError as e:
        display_message(f"Σφάλμα HTTP: {e.response.status_code} - {e.response.reason}", 'red')
        display_message("Δεν ήταν δυνατή η ανάκτηση του περιεχομένου. Ελέγξτε το URL.", 'red')
    except requests.exceptions.ConnectionError:
        display_message("Σφάλμα Σύνδεσης: Δεν ήταν δυνατή η σύνδεση στον διακομιστή.", 'red')
        display_message("Παρακαλώ ελέγξτε τη σύνδεσή σας στο διαδίκτυο ή το URL.", 'red')
    except requests.exceptions.Timeout:
        display_message("Σφάλμα Χρονικού Ορίου: Η αίτηση χρειάστηκε πολύ χρόνο για να απαντήσει.", 'red')
        display_message("Ο διακομιστής μπορεί να είναι αργός ή να μην ανταποκρίνεται.", 'red')
    except requests.exceptions.RequestException as e:
        display_message(f"Προέκυψε ένα απροσδόκητο σφάλμα: {e}", 'red')
    return None

def download_asset(asset_url, local_dir, base_url):
    """
    Downloads a single asset and saves it to the specified local directory.
    Returns the relative path to the saved asset or None on failure.
    """
    if not asset_url or asset_url.startswith('data:'):
        return None

    absolute_asset_url = urljoin(base_url, asset_url)
    parsed_asset_url = urlparse(absolute_asset_url)

    filename = os.path.basename(parsed_asset_url.path)
    if not filename:
        filename = 'index' + os.path.splitext(parsed_asset_url.path)[1]
        if not filename or filename == 'index':
            filename = 'asset' + str(abs(hash(absolute_asset_url)))

    filename = unquote(filename.split('?')[0].split('#')[0])
    filename = re.sub(r'[\\/:*?"<>|]', '_', filename)
    if not filename:
        filename = 'unknown_asset_' + str(abs(hash(absolute_asset_url)))

    local_path = os.path.join(local_dir, filename)

    counter = 1
    original_local_path = local_path
    while os.path.exists(local_path):
        name, ext = os.path.splitext(original_local_path)
        local_path = f"{name}_{counter}{ext}"
        counter += 1

    try:
        response = requests.get(absolute_asset_url, stream=True, timeout=10)
        response.raise_for_status()

        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return os.path.relpath(local_path, os.path.dirname(local_dir))
    except requests.exceptions.RequestException as e:
        display_message(f"Αποτυχία λήψης του {absolute_asset_url}: {e}", 'red')
    except IOError as e:
        display_message(f"Αποτυχία αποθήκευσης του αρχείου στοιχείου στο {local_path}: {e}", 'red')
    return None

def process_html_and_download_assets(html_content, base_url, website_dir):
    """
    Parses HTML, downloads assets, and modifies HTML to point to local files.
    Returns the modified HTML content.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    downloaded_urls = set()

    display_message("\nΈναρξη διαδικασίας λήψης στοιχείων...", 'blue')

    for tag_name, attr_name, subdir, filter_func in ASSET_MAP:
        for tag in soup.find_all(tag_name):
            if filter_func and not filter_func(tag):
                continue

            asset_url = tag.get(attr_name)
            if asset_url and asset_url not in downloaded_urls:
                asset_subdir_path = os.path.join(website_dir, subdir)
                if not ensure_directory_exists(asset_subdir_path):
                    continue

                relative_asset_path = download_asset(asset_url, asset_subdir_path, base_url)
                if relative_asset_path:
                    tag[attr_name] = os.path.join(subdir, os.path.basename(relative_asset_path)).replace('\\', '/')
                    downloaded_urls.add(asset_url)

    for tag in soup.find_all(attrs={'style': True}):
        style_attr = tag['style']
        matches = INLINE_CSS_URL_REGEX.findall(style_attr)
        for url_match in matches:
            clean_url = url_match.strip("'\"")
            if clean_url and clean_url not in downloaded_urls:
                asset_subdir_path = os.path.join(website_dir, 'images')
                if not ensure_directory_exists(asset_subdir_path):
                    continue

                relative_asset_path = download_asset(clean_url, asset_subdir_path, base_url)
                if relative_asset_path:
                    new_url_in_style = os.path.join('images', os.path.basename(relative_asset_path)).replace('\\', '/')
                    tag['style'] = style_attr.replace(url_match, new_url_in_style)
                    downloaded_urls.add(clean_url)

    display_message("Η λήψη στοιχείων και η τροποποίηση του HTML ολοκληρώθηκαν.", 'green')
    return str(soup)

def edit_html_in_editor(html_content):
    """
    Saves HTML to a temporary file and opens it in the configured command-line editor.
    Returns the modified content after the editor closes.
    """
    if not html_content:
        display_message("Δεν υπάρχει περιεχόμενο για επεξεργασία.", 'yellow')
        return None

    temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8', suffix='.html')
    temp_file_path = temp_file.name
    try:
        temp_file.write(html_content)
        temp_file.close()

        display_message(f"\nΆνοιγμα HTML στο {EDITOR}. Πατήστε Ctrl+X (nano) ή :wq (vim) για αποθήκευση και έξοδο.", 'yellow')
        display_message(f"Διαδρομή αρχείου: {temp_file_path}", 'yellow')

        editor_process = subprocess.run([EDITOR, temp_file_path])

        if editor_process.returncode != 0:
            display_message(f"Το πρόγραμμα επεξεργασίας '{EDITOR}' τερμάτισε με σφάλμα. Το HTML ενδέχεται να μην έχει αποθηκευτεί.", 'red')

        with open(temp_file_path, 'r', encoding='utf-8') as f:
            modified_html = f.read()
        display_message("Το περιεχόμενο HTML διαβάστηκε από το πρόγραμμα επεξεργασίας.", 'green')
        return modified_html
    except FileNotFoundError:
        display_message(f"Σφάλμα: Το πρόγραμμα επεξεργασίας '{EDITOR}' δεν βρέθηκε.", 'red')
        display_message("Παρακαλώ εγκαταστήστε το (π.χ. 'pkg install nano') ή ορίστε τη μεταβλητή περιβάλλοντος EDITOR.", 'red')
    except Exception as e:
        display_message(f"Προέκυψε σφάλμα κατά την επεξεργασία: {e}", 'red')
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            display_message(f"Καθαρίστηκε το προσωρινό αρχείο: {temp_file_path}", 'cyan')
    return None

def save_html_to_file(html_content, target_dir, default_filename="index.html"):
    """Saves the HTML content to the specified file within the target directory."""
    if not html_content:
        display_message("Δεν υπάρχει περιεχόμενο για αποθήκευση.", 'yellow')
        return

    if not ensure_directory_exists(target_dir):
        return

    filepath = os.path.join(target_dir, default_filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        display_message(f"Το HTML αποθηκεύτηκε με επιτυχία στο '{filepath}'", 'green')
        return filepath
    except IOError as e:
        display_message(f"Σφάλμα κατά την αποθήκευση του αρχείου: {e}", 'red')
    return None

def preview_html_in_browser(filepath):
    """
    Opens a local HTML file in the default browser using termux-open-url.
    """
    if not filepath or not os.path.exists(filepath):
        display_message("Δεν βρέθηκε αρχείο HTML για προεπισκόπηση.", 'yellow')
        return

    display_message(f"Άνοιγμα προεπισκόπησης στο πρόγραμμα περιήγησης από: {filepath}", 'cyan')
    try:
        subprocess.run(['termux-open-url', f'file://{filepath}'])
        display_message("Η προεπισκόπηση άνοιξε. Ίσως χρειαστεί να μεταβείτε στην εφαρμογή του προγράμματος περιήγησής σας.", 'green')
    except FileNotFoundError:
        display_message("Σφάλμα: Η εντολή 'termux-open-url' δεν βρέθηκε.", 'red')
        display_message("Παρακαλώ βεβαιωθείτε ότι το 'termux-api' είναι εγκατεστημένο ('pkg install termux-api').", 'red')
    except Exception as e:
        display_message(f"Προέκυψε σφάλμα κατά την προεπισκόπηση: {e}", 'red')

# --- Main Script Logic ---

def main():
    display_message("--- Termux HTML Inspector & Editor with Auto-Setup ---", 'blue')
    display_message("Έλεγχος και εγκατάσταση απαραίτητων στοιχείων...", 'blue')
    time.sleep(1)

    # 1. Check/Install Python packages
    if not check_and_install_pip_package("requests"):
        return
    if not check_and_install_pip_package("beautifulsoup4"):
        return

    global requests, BeautifulSoup
    import requests
    from bs4 import BeautifulSoup

    # 2. Check/Install Termux packages
    if not check_and_install_termux_package(EDITOR, EDITOR):
        return
    if not check_and_install_termux_package("termux-api", "termux-open-url"):
        return

    # 3. Check storage permission
    if not check_storage_permission():
        return

    display_message("\nΌλες οι προϋποθέσεις πληρούνται! Εκκίνηση της εφαρμογής...", 'green')
    time.sleep(1)

    initial_url = input("\nΕισάγετε το URL της ιστοσελίδας (π.χ. https://www.example.com): ").strip()
    if not initial_url:
        display_message("Δεν δόθηκε URL. Έξοδος.", 'red')
        return

    website_name = get_website_name(initial_url)
    website_dir = get_download_base_dir(website_name)
    main_html_filepath = os.path.join(website_dir, "index.html")

    html_content = fetch_html(initial_url)

    if not html_content:
        display_message("Αποτυχία λήψης του αρχικού HTML. Δεν είναι δυνατή η συνέχεια.", 'red')
        return

    # Main loop for user interaction
    while True:
        display_message("\n--- Επιλογές ---", 'blue')
        display_message("1. Λήψη στοιχείων & Αποθήκευση HTML (Δημιουργεί/Ενημερώνει Τοπικό Αντίγραφο)", 'default')
        display_message("2. Επεξεργασία του τρέχοντος HTML", 'default')
        display_message("3. Αποθήκευση του τρέχοντος HTML σε αρχείο", 'default')
        display_message("4. Προεπισκόπηση του τρέχοντος HTML στο πρόγραμμα περιήγησης", 'default')
        display_message("5. Λήψη νέου URL", 'default')
        display_message("6. Έξοδος", 'default')

        choice = input("Εισάγετε την επιλογή σας (1-6): ").strip()

        if choice == '1':
            if not ensure_directory_exists(website_dir):
                display_message("Δεν ήταν δυνατή η δημιουργία του καταλόγου της ιστοσελίδας. Ματαίωση λήψης στοιχείων.", 'red')
                continue
            display_message(f"Λήψη στοιχείων στο: {website_dir}", 'blue')
            modified_html_content = process_html_and_download_assets(html_content, initial_url, website_dir)
            if modified_html_content:
                html_content = modified_html_content
                save_html_to_file(html_content, website_dir, "index.html")
            else:
                display_message("Η λήψη στοιχείων και η τροποποίηση του HTML απέτυχαν.", 'red')
        elif choice == '2':
            modified_html = edit_html_in_editor(html_content)
            if modified_html is not None:
                html_content = modified_html
        elif choice == '3':
            save_html_to_file(html_content, website_dir, "index.html")
        elif choice == '4':
            saved_path = save_html_to_file(html_content, website_dir, "index.html")
            if saved_path:
                preview_html_in_browser(saved_path)
        elif choice == '5':
            new_url = input("Εισάγετε το νέο URL της ιστοσελίδας: ").strip()
            if new_url:
                initial_url = new_url
                website_name = get_website_name(initial_url)
                website_dir = get_download_base_dir(website_name)
                main_html_filepath = os.path.join(website_dir, "index.html")
                html_content = fetch_html(initial_url)
                if not html_content:
                    display_message("Αποτυχία λήψης νέου URL. Παραμένει το προηγούμενο περιεχόμενο αν υπάρχει.", 'red')
            else:
                display_message("Δεν δόθηκε νέο URL.", 'yellow')
        elif choice == '6':
            display_message("Έξοδος από τον ελεγκτή HTML.", 'blue')
            break
        else:
            display_message("Μη έγκυρη επιλογή. Παρακαλώ εισάγετε έναν αριθμό από το 1 έως το 6.", 'red')

if __name__ == "__main__":
    main()