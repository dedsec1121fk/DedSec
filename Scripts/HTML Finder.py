import os
import tempfile
import subprocess
import sys
from urllib.parse import urljoin, urlparse, unquote
import re # For regex to handle inline CSS background-image URLs
import time # For small delays

# --- Configuration ---
# You can change 'nano' to 'vim' or another command-line editor if you prefer
EDITOR = os.environ.get('EDITOR', 'nano')

# Base directory for all downloads within Termux storage
# This typically maps to /sdcard/Download on your Android device
TERMUX_DOWNLOADS_BASE = os.path.join(os.path.expanduser('~'), 'storage', 'downloads')

# Asset mapping: (tag_name, attribute_name, subdirectory, [optional_filter_function])
# The filter_function takes the BeautifulSoup tag as input and returns True if it matches.
ASSET_MAP = [
    ('link', 'href', 'css', lambda tag: tag.get('rel') and 'stylesheet' in tag['rel']), # CSS stylesheets
    ('script', 'src', 'js', None),  # JavaScript files
    ('img', 'src', 'images', None), # Images
    ('source', 'src', 'media', None), # Video/audio sources (e.g., in <picture> or <video>)
    ('video', 'poster', 'images', None), # Video poster images
    ('link', 'href', 'icons', lambda tag: tag.get('rel') and any(r in ['icon', 'shortcut icon'] for r in tag['rel'])), # Favicons
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
            display_message(f"Command failed: {' '.join(command)}\n{result.stderr}", 'red')
            return False
        return True
    except FileNotFoundError:
        display_message(f"Command not found: {command[0].split()[0]}", 'red')
        return False
    except Exception as e:
        display_message(f"Error running command '{' '.join(command)}': {e}", 'red')
        return False

def check_and_install_pip_package(package_name):
    """Checks if a pip package is installed and offers to install it."""
    try:
        __import__(package_name.split('==')[0].split('<')[0].split('>')[0].split('~')[0]) # Try importing
        display_message(f"Python package '{package_name}' is already installed.", 'green')
        return True
    except ImportError:
        display_message(f"Python package '{package_name}' is not installed.", 'yellow')
        choice = input(f"Do you want to install it now? (y/n): ").lower().strip()
        if choice == 'y':
            return run_command(f"pip install {package_name}", message=f"Installing {package_name}...")
        else:
            display_message(f"'{package_name}' is required for full functionality. Exiting.", 'red')
            return False

def check_and_install_termux_package(package_name, command_to_check=None):
    """Checks if a Termux package is installed and offers to install it."""
    if command_to_check is None:
        command_to_check = package_name

    # Check if the command exists
    if subprocess.run(f"which {command_to_check}", shell=True, capture_output=True).returncode == 0:
        display_message(f"Termux package '{package_name}' ({command_to_check}) is already installed.", 'green')
        return True
    else:
        display_message(f"Termux package '{package_name}' ({command_to_check}) is not installed.", 'yellow')
        choice = input(f"Do you want to install it now via 'pkg install {package_name}'? (y/n): ").lower().strip()
        if choice == 'y':
            return run_command(f"pkg install {package_name} -y", message=f"Installing {package_name}...")
        else:
            display_message(f"'{package_name}' is required for full functionality. Exiting.", 'red')
            return False

def check_storage_permission():
    """Checks if Termux has storage permission and prompts if not."""
    test_file_path = os.path.join(TERMUX_DOWNLOADS_BASE, f".test_permission_{os.getpid()}")
    try:
        os.makedirs(TERMUX_DOWNLOADS_BASE, exist_ok=True)
        with open(test_file_path, 'w') as f:
            f.write("test")
        os.remove(test_file_path)
        display_message("Storage permission is granted.", 'green')
        return True
    except PermissionError:
        display_message("Storage permission not granted for Termux.", 'red')
        display_message("You need to run 'termux-setup-storage' and grant permission.", 'yellow')
        choice = input("Do you want to run 'termux-setup-storage' now? (y/n): ").lower().strip()
        if choice == 'y':
            run_command("termux-setup-storage", check_success=False, message="Running termux-setup-storage...")
            display_message("Please follow the prompts to grant storage permission. Rerun the script after granting.", 'yellow')
            return False # User needs to restart after granting permission
        else:
            display_message("Storage permission is required to save files. Exiting.", 'red')
            return False
    except Exception as e:
        display_message(f"Error checking storage permission: {e}", 'red')
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
        # display_message(f"Ensured directory exists: {path}", 'cyan') # Too verbose
    except OSError as e:
        display_message(f"Error creating directory '{path}': {e}", 'red')
        return False
    return True

def fetch_html(url):
    """
    Fetches HTML content from the given URL.
    Handles common HTTP and network errors.
    """
    display_message(f"Attempting to fetch HTML from: {url}", 'cyan')
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        display_message("HTML fetched successfully!", 'green')
        return response.text
    except requests.exceptions.HTTPError as e:
        display_message(f"HTTP Error: {e.response.status_code} - {e.response.reason}", 'red')
        display_message("Could not retrieve content. Check the URL.", 'red')
    except requests.exceptions.ConnectionError:
        display_message("Connection Error: Could not connect to the server.", 'red')
        display_message("Please check your internet connection or the URL.", 'red')
    except requests.exceptions.Timeout:
        display_message("Timeout Error: The request took too long to respond.", 'red')
        display_message("The server might be slow or unresponsive.", 'red')
    except requests.exceptions.RequestException as e:
        display_message(f"An unexpected error occurred: {e}", 'red')
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

    # display_message(f"Downloading: {absolute_asset_url} to {local_path}", 'cyan') # Too verbose
    try:
        response = requests.get(absolute_asset_url, stream=True, timeout=10)
        response.raise_for_status()

        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        # display_message(f"Downloaded: {filename}", 'green') # Too verbose
        return os.path.relpath(local_path, os.path.dirname(local_dir))
    except requests.exceptions.RequestException as e:
        display_message(f"Failed to download {absolute_asset_url}: {e}", 'red')
    except IOError as e:
        display_message(f"Failed to save asset to {local_path}: {e}", 'red')
    return None

def process_html_and_download_assets(html_content, base_url, website_dir):
    """
    Parses HTML, downloads assets, and modifies HTML to point to local files.
    Returns the modified HTML content.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    downloaded_urls = set()

    display_message("\nStarting asset download process...", 'blue')

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

    display_message("Asset download and HTML modification complete.", 'green')
    return str(soup)

def edit_html_in_editor(html_content):
    """
    Saves HTML to a temporary file and opens it in the configured command-line editor.
    Returns the modified content after the editor closes.
    """
    if not html_content:
        display_message("No content to edit.", 'yellow')
        return None

    temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8', suffix='.html')
    temp_file_path = temp_file.name
    try:
        temp_file.write(html_content)
        temp_file.close()

        display_message(f"\nOpening HTML in {EDITOR}. Press Ctrl+X (nano) or :wq (vim) to save and exit.", 'yellow')
        display_message(f"File path: {temp_file_path}", 'yellow')

        editor_process = subprocess.run([EDITOR, temp_file_path])

        if editor_process.returncode != 0:
            display_message(f"Editor '{EDITOR}' exited with an error. HTML might not be saved.", 'red')

        with open(temp_file_path, 'r', encoding='utf-8') as f:
            modified_html = f.read()
        display_message("HTML content read from editor.", 'green')
        return modified_html
    except FileNotFoundError:
        display_message(f"Error: Editor '{EDITOR}' not found.", 'red')
        display_message("Please install it (e.g., 'pkg install nano') or set the EDITOR environment variable.", 'red')
    except Exception as e:
        display_message(f"An error occurred during editing: {e}", 'red')
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            display_message(f"Cleaned up temporary file: {temp_file_path}", 'cyan')
    return None

def save_html_to_file(html_content, target_dir, default_filename="index.html"):
    """Saves the HTML content to the specified file within the target directory."""
    if not html_content:
        display_message("No content to save.", 'yellow')
        return

    if not ensure_directory_exists(target_dir):
        return

    filepath = os.path.join(target_dir, default_filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        display_message(f"HTML saved successfully to '{filepath}'", 'green')
        return filepath
    except IOError as e:
        display_message(f"Error saving file: {e}", 'red')
    return None

def preview_html_in_browser(filepath):
    """
    Opens a local HTML file in the default browser using termux-open-url.
    """
    if not filepath or not os.path.exists(filepath):
        display_message("No HTML file found to preview.", 'yellow')
        return

    display_message(f"Opening preview in browser from: {filepath}", 'cyan')
    try:
        subprocess.run(['termux-open-url', f'file://{filepath}'])
        display_message("Preview opened. You might need to switch to your browser app.", 'green')
    except FileNotFoundError:
        display_message("Error: 'termux-open-url' command not found.", 'red')
        display_message("Please ensure 'termux-api' is installed ('pkg install termux-api').", 'red')
    except Exception as e:
        display_message(f"An error occurred during preview: {e}", 'red')

# --- Main Script Logic ---

def main():
    display_message("--- Termux HTML Inspector & Editor with Auto-Setup ---", 'blue')
    display_message("Checking and installing required components...", 'blue')
    time.sleep(1) # Give user time to read

    # 1. Check/Install Python packages
    if not check_and_install_pip_package("requests"):
        return
    if not check_and_install_pip_package("beautifulsoup4"):
        return

    # Now that requests and beautifulsoup4 are confirmed, import them
    global requests, BeautifulSoup
    import requests
    from bs4 import BeautifulSoup

    # 2. Check/Install Termux packages
    if not check_and_install_termux_package(EDITOR, EDITOR): # Check for the editor itself
        return
    if not check_and_install_termux_package("termux-api", "termux-open-url"):
        return

    # 3. Check storage permission
    if not check_storage_permission():
        return # User needs to restart after granting permission

    display_message("\nAll prerequisites met! Starting application...", 'green')
    time.sleep(1)

    initial_url = input("\nEnter the website URL (e.g., https://www.example.com): ").strip()
    if not initial_url:
        display_message("No URL provided. Exiting.", 'red')
        return

    website_name = get_website_name(initial_url)
    website_dir = get_download_base_dir(website_name)
    main_html_filepath = os.path.join(website_dir, "index.html")

    # Fetch initial HTML
    html_content = fetch_html(initial_url)

    if not html_content:
        display_message("Failed to fetch initial HTML. Cannot proceed.", 'red')
        return

    # Main loop for user interaction
    while True:
        display_message("\n--- Options ---", 'blue')
        display_message("1. Download Assets & Save HTML (Creates/Updates Local Copy)", 'default')
        display_message("2. Edit Current HTML", 'default')
        display_message("3. Save Current HTML to File", 'default')
        display_message("4. Preview Current HTML in Browser", 'default')
        display_message("5. Fetch New URL", 'default')
        display_message("6. Exit", 'default')

        choice = input("Enter your choice (1-6): ").strip()

        if choice == '1':
            if not ensure_directory_exists(website_dir):
                display_message("Could not create website directory. Aborting asset download.", 'red')
                continue
            display_message(f"Downloading assets to: {website_dir}", 'blue')
            modified_html_content = process_html_and_download_assets(html_content, initial_url, website_dir)
            if modified_html_content:
                html_content = modified_html_content # Update current HTML to the modified version
                save_html_to_file(html_content, website_dir, "index.html")
            else:
                display_message("Asset download and HTML modification failed.", 'red')
        elif choice == '2':
            modified_html = edit_html_in_editor(html_content)
            if modified_html is not None:
                html_content = modified_html # Update content for subsequent operations
        elif choice == '3':
            save_html_to_file(html_content, website_dir, "index.html")
        elif choice == '4':
            saved_path = save_html_to_file(html_content, website_dir, "index.html")
            if saved_path:
                preview_html_in_browser(saved_path)
        elif choice == '5':
            new_url = input("Enter the new website URL: ").strip()
            if new_url:
                initial_url = new_url
                website_name = get_website_name(initial_url)
                website_dir = get_download_base_dir(website_name)
                main_html_filepath = os.path.join(website_dir, "index.html")
                html_content = fetch_html(initial_url)
                if not html_content:
                    display_message("Failed to fetch new URL. Staying with previous content if any.", 'red')
            else:
                display_message("No new URL provided.", 'yellow')
        elif choice == '6':
            display_message("Exiting the HTML inspector.", 'blue')
            break
        else:
            display_message("Invalid choice. Please enter a number between 1 and 6.", 'red')

if __name__ == "__main__":
    main()
