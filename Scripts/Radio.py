import curses
import os
import subprocess
import random
import threading
import time
import requests
import shutil
import platform
import tempfile

# --- Configuration ---
GITHUB_API_ROOT = "https://api.github.com/repos/dedsec1121fk/DedSec-Radio/contents"
REPO_NAME = "DedSec-Radio"
DEDSEC_RADIO_PATH = os.path.expanduser(f"~/{REPO_NAME}")
PLAY_CMD_BASE = "mpv --no-terminal --no-video"
SUPPORTED_AUDIO_EXTENSIONS = ('.mp3', '.wav', '.flac', '.ogg', '.m4a')
DEP_FLAG_FILE = os.path.join(DEDSEC_RADIO_PATH, ".deps_installed")
NOTIFICATION_TMP_FILE = os.path.join(tempfile.gettempdir(), "radio_notification.txt")

# --- Globals ---
current_station_index = 0
stations = []
current_player_process = None
is_playing = False
playback_thread = None
playback_error_message = None
current_song = "Nothing playing"
wave_chars = [' ', '▂', '▃', '▄', '▅', '▆', '▇', '█']
stop_playback_event = threading.Event()

# --- Pre-run Dependency Checks ---
def check_and_install_dependencies():
    """Checks for required tools and auto-installs them in Termux."""
    if os.path.exists(DEP_FLAG_FILE): return True
    required = {'mpv': 'the music player'}
    is_termux = "com.termux" in os.environ.get("PREFIX", "")
    if is_termux:
        required['termux-api'] = 'for notifications'
    missing = [cmd for cmd in required if not shutil.which(cmd)]
    if not missing:
        open(DEP_FLAG_FILE, 'a').close(); return True
        
    print("--- Missing Dependencies Detected ---")
    installation_performed = False
    for cmd in missing:
        print(f"\n[!] '{cmd}' was not found.")
        if is_termux:
            print(f"    Attempting to auto-install: pkg install {cmd} -y")
            try:
                subprocess.run(["pkg", "install", cmd, "-y"], check=True, capture_output=True)
                print(f"    Successfully installed '{cmd}'.")
                installation_performed = True
            except Exception:
                print(f"    Auto-installation failed. Please run 'pkg install {cmd} -y' manually."); return False
        else:
            print(f"    Please install '{cmd}' using your system's package manager."); return False
            
    if installation_performed:
        open(DEP_FLAG_FILE, 'a').close()
        print("\nDependencies installed. Please restart the script.")
        return False 
    return True

# --- Directory and Station Management ---
def ensure_radio_dir_exists():
    os.makedirs(DEDSEC_RADIO_PATH, exist_ok=True)

def get_stations():
    if not os.path.exists(DEDSEC_RADIO_PATH): return []
    lst = []
    for item in os.listdir(DEDSEC_RADIO_PATH):
        station_path = os.path.join(DEDSEC_RADIO_PATH, item)
        if os.path.isdir(station_path) and not item.startswith('.'):
            try:
                if any(f.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS) for f in os.listdir(station_path)):
                    lst.append(item)
            except OSError: continue
    return sorted(lst)

# --- Notifications (New Self-Contained Method) ---
def show_termux_notification(station, song):
    """Writes details to a temp file and executes an embedded shell script to show the notification."""
    if not shutil.which("termux-notification"): return

    # Write the details to the temp file that the shell script will read
    with open(NOTIFICATION_TMP_FILE, "w") as f:
        f.write(f"DedSec Radio\n")
        f.write(f"Station: {station}\nSong Playing: {song}")

    # This shell script is now embedded inside the Python script
    shell_script = f"""
    #!/data/data/com.termux/files/usr/bin/sh
    sleep 1 # Give the main script a moment to continue
    if [ -f "{NOTIFICATION_TMP_FILE}" ]; then
        TITLE=$(sed -n '1p' "{NOTIFICATION_TMP_FILE}")
        CONTENT=$(sed -n '2p' "{NOTIFICATION_TMP_FILE}")
        termux-notification \\
            --title "$TITLE" \\
            --content "$CONTENT" \\
            --id "dedsec-radio" \\
            --button1 "Previous" --action1 "echo prev" \\
            --button2 "Pause" --action2 "echo pause" \\
            --button3 "Next" --action3 "echo next"
    fi
    """
    # Execute the shell script string in a new, clean environment
    subprocess.Popen(['/data/data/com.termux/files/usr/bin/sh', '-c', shell_script])


def clear_termux_notification():
    if shutil.which("termux-notification-remove"):
        subprocess.Popen(["termux-notification-remove", "dedsec-radio"])

# --- Playback Logic ---
def play_station_music():
    global current_player_process, is_playing, playback_thread, playback_error_message, current_song
    stop_music()
    playback_error_message = None
    if not stations or not (0 <= current_station_index < len(stations)): return

    station_path = os.path.join(DEDSEC_RADIO_PATH, stations[current_station_index])
    song_files = [os.path.join(station_path, f) for f in os.listdir(station_path) if f.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS)]
    if not song_files:
        playback_error_message = f"No music in '{stations[current_station_index]}'."; return
    random.shuffle(song_files)

    def playback_task():
        global current_player_process, is_playing, current_song, playback_error_message
        is_playing = True
        for song_path in song_files:
            if stop_playback_event.is_set(): break
            current_song = os.path.basename(song_path)
            station_name = stations[current_station_index]
            show_termux_notification(station_name, current_song)
            try:
                command = PLAY_CMD_BASE.split() + [song_path]
                current_player_process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                while current_player_process.poll() is None:
                    if stop_playback_event.is_set(): current_player_process.terminate(); break
                    time.sleep(0.1)
            except Exception as e:
                playback_error_message = f"Playback Error: {e}"; break
        is_playing = False
        current_song = "Nothing playing"
        clear_termux_notification()

    playback_thread = threading.Thread(target=playback_task, daemon=True)
    playback_thread.start()

def stop_music():
    global current_player_process, is_playing
    stop_playback_event.set()
    if current_player_process and current_player_process.poll() is None:
        try:
            current_player_process.terminate()
            current_player_process.wait(timeout=1)
        except (subprocess.TimeoutExpired, ProcessLookupError): current_player_process.kill()
    if playback_thread and playback_thread.is_alive(): playback_thread.join(timeout=1)
    is_playing = False
    current_player_process = None
    stop_playback_event.clear()

# --- UI Drawing and Menus ---
def draw_centered_text(stdscr, y, text, attr=0):
    h, w = stdscr.getmaxyx()
    if y >= h or y < 0: return
    x = (w - len(text)) // 2
    display_text = text[:w-1]
    try: stdscr.addstr(y, x, display_text, attr)
    except curses.error: pass

def draw_menu(stdscr, title, menu_items, sel_index, scroll_offset=0):
    stdscr.clear(); h, w = stdscr.getmaxyx()
    menu_area_y_start, menu_area_y_end = 3, h - 2
    menu_height = menu_area_y_end - menu_area_y_start
    if menu_height < 1: return
    draw_centered_text(stdscr, 1, title, curses.A_BOLD)
    for i in range(menu_height):
        item_index = scroll_offset + i
        if item_index >= len(menu_items): break
        item_text, y = menu_items[item_index], menu_area_y_start + i
        attr = curses.color_pair(1) if item_index == sel_index else 0
        draw_centered_text(stdscr, y, item_text, attr)
    if len(menu_items) > menu_height:
        if scroll_offset > 0: draw_centered_text(stdscr, menu_area_y_start, "↑")
        if scroll_offset + menu_height < len(menu_items): draw_centered_text(stdscr, menu_area_y_end, "↓")
    stdscr.refresh()

def handle_menu(stdscr, title, menu_items):
    sel_index, scroll_offset = 0, 0
    while True:
        h, w = stdscr.getmaxyx()
        menu_height = h - 5
        if sel_index < scroll_offset: scroll_offset = sel_index
        if sel_index >= scroll_offset + menu_height: scroll_offset = sel_index - menu_height + 1
        draw_menu(stdscr, title, menu_items, sel_index, scroll_offset)
        key = stdscr.getch()
        if key == curses.KEY_UP: sel_index = (sel_index - 1 + len(menu_items)) % len(menu_items)
        elif key == curses.KEY_DOWN: sel_index = (sel_index + 1) % len(menu_items)
        elif key in [ord('q'), curses.KEY_LEFT]: return None
        elif key in [10, 13, curses.KEY_RIGHT]: return menu_items[sel_index]

# --- Station Management Logic ---
def _fetch_repo_dir(path=""):
    url = f"{GITHUB_API_ROOT}/{path}".rstrip("/"); response = requests.get(url, timeout=15); response.raise_for_status(); return response.json()

def _download_file_with_progress(stdscr, file_info, local_path):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    if os.path.exists(local_path) and os.path.getsize(local_path) == file_info.get('size', -1): return True, "Skipped"
    try:
        with requests.get(file_info['download_url'], stream=True, timeout=30) as r:
            r.raise_for_status()
            total_size, downloaded_size = int(r.headers.get('content-length', 0)), 0
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk); downloaded_size += len(chunk)
                    percent = (downloaded_size / total_size * 100) if total_size > 0 else 100
                    draw_menu(stdscr, "Downloading", [f"'{file_info['name']}': {percent:.0f}%"], -1)
        return True, "Downloaded"
    except Exception as e: return False, f"Error: {e}"

def download_or_update_station(stdscr, station_name, is_update=False):
    global stations; target_path = os.path.join(DEDSEC_RADIO_PATH, station_name); os.makedirs(target_path, exist_ok=True)
    try: files_in_repo = [f for f in _fetch_repo_dir(station_name) if f['type'] == 'file']
    except requests.exceptions.RequestException as e:
        draw_menu(stdscr, "Error", [f"Could not fetch file list for '{station_name}'", str(e), "Press any key..."], -1); stdscr.getch(); return
    download_count = 0
    for i, file_info in enumerate(files_in_repo):
        draw_menu(stdscr, f"Downloading '{station_name}'", [f"File {i+1}/{len(files_in_repo)}: {file_info['name']}"], -1)
        success, message = _download_file_with_progress(stdscr, file_info, os.path.join(target_path, file_info['name']))
        if message == "Downloaded": download_count += 1
        elif not success:
            draw_menu(stdscr, "Download Failed", [f"Failed on: {file_info['name']}", message, "Press any key..."], -1); stdscr.getch(); return
    if not is_update:
        draw_menu(stdscr, "Download Complete", [f"Downloaded {download_count} new file(s) for '{station_name}'.", "Press any key..."], -1); stdscr.getch()
    stations = get_stations(); return download_count

def download_new_station(stdscr):
    draw_menu(stdscr, "Download Station", ["Fetching..."], -1)
    try:
        available_stations = sorted([item['name'] for item in _fetch_repo_dir() if item['type'] == 'dir'])
        to_download = [s for s in available_stations if s not in stations]
        if not to_download:
            draw_menu(stdscr, "Download Station", ["No new stations to download."], -1); stdscr.getch(); return
        station_name = handle_menu(stdscr, "Select a station (q to cancel):", to_download)
        if station_name: download_or_update_station(stdscr, station_name)
    except requests.exceptions.RequestException as e:
        draw_menu(stdscr, "Network Error", [f"Could not fetch station list: {e}", "Press any key..."], -1); stdscr.getch()

def update_existing_stations(stdscr):
    if not stations:
        draw_menu(stdscr, "Update", ["No stations downloaded to update."], -1); stdscr.getch(); return
    draw_menu(stdscr, "Update Stations", [f"Preparing to update {len(stations)} station(s)..."], -1); time.sleep(1.5)
    total_updated = 0
    for station_name in stations:
        updated_count = download_or_update_station(stdscr, station_name, is_update=True)
        if updated_count is not None: total_updated += updated_count
    final_message = [f"Update process finished.", f"{total_updated} file(s) were updated.", "Press any key..."]
    draw_menu(stdscr, "Update Complete", final_message, -1); stdscr.getch()

def delete_station_menu(stdscr):
    global stations
    while True:
        stations = get_stations()
        if not stations:
            draw_menu(stdscr, "Downloaded Stations", ["No stations downloaded yet.", "Press any key..."], -1); stdscr.getch(); return
        display_list = stations + ["Back"]
        selected = handle_menu(stdscr, "Select a station to delete (q to cancel):", display_list)
        if selected is None or selected == "Back": return
        station_to_delete = selected
        confirm_title = f"Delete '{station_to_delete}'?"; confirm_message = ["This action cannot be undone.", "Are you sure? [y/N]"]
        draw_menu(stdscr, confirm_title, confirm_message, -1)
        key = stdscr.getch()
        if key == ord('y') or key == ord('Y'):
            try:
                shutil.rmtree(os.path.join(DEDSEC_RADIO_PATH, station_to_delete))
                draw_menu(stdscr, "Success", [f"Successfully deleted '{station_to_delete}'.", "Press any key..."], -1); stdscr.getch()
            except Exception as e:
                draw_menu(stdscr, "Error", [f"Could not delete station:", f"{e}", "Press any key..."], -1); stdscr.getch()
        else:
            draw_menu(stdscr, "Cancelled", [f"Deletion of '{station_to_delete}' cancelled.", "Press any key..."], -1); stdscr.getch()

def manage_stations_menu(stdscr):
    while True:
        menu_items = ["Download new station", "Update all stations", "Manage downloaded stations", "Back"]
        selected = handle_menu(stdscr, "Manage Stations", menu_items)
        if selected == "Download new station": download_new_station(stdscr)
        elif selected == "Update all stations": update_existing_stations(stdscr)
        elif selected == "Manage downloaded stations": delete_station_menu(stdscr)
        elif selected in ["Back", None]: break

def main_menu(stdscr):
    global stations
    while True:
        stations = get_stations()
        selected = handle_menu(stdscr, "DedSec Radio", ["Play Radio", "Manage Stations", "Exit"])
        if selected == "Play Radio":
            if stations: radio_menu(stdscr)
            else: draw_menu(stdscr, "Notice", ["No stations downloaded.", "Use 'Manage Stations' to get some.", "Press any key..."], -1); stdscr.getch()
        elif selected == "Manage Stations": manage_stations_menu(stdscr)
        elif selected in ["Exit", None]: break

def radio_menu(stdscr):
    global current_station_index, current_song, playback_error_message
    stdscr.nodelay(True); play_station_music(); last_wave_update = time.time(); wave = ""
    while True:
        key = stdscr.getch()
        if key == ord('q'): break
        elif key == curses.KEY_RIGHT:
            if stations: current_station_index = (current_station_index + 1) % len(stations); play_station_music()
        elif key == curses.KEY_LEFT:
            if stations: current_station_index = (current_station_index - 1 + len(stations)) % len(stations); play_station_music()
        stdscr.clear(); h, w = stdscr.getmaxyx()
        station_name = stations[current_station_index] if stations else "None"
        draw_centered_text(stdscr, h // 2 - 3, f"Station: {station_name}", curses.A_BOLD)
        draw_centered_text(stdscr, h // 2 - 1, "Now Playing:")
        draw_centered_text(stdscr, h // 2, current_song)
        if time.time() - last_wave_update > 0.1:
            max_wave_len = min(w - 4, 60)
            wave = "".join(random.choice(wave_chars) for _ in range(max_wave_len)); last_wave_update = time.time()
        draw_centered_text(stdscr, h // 2 + 2, wave)
        controls = "Controls: [←] Prev | [→] Next | [q] Back"
        draw_centered_text(stdscr, h - 2, controls)
        if playback_error_message: draw_centered_text(stdscr, h - 4, f"Error: {playback_error_message}", curses.A_BOLD)
        stdscr.refresh(); time.sleep(0.05)
    stdscr.nodelay(False); stop_music()

def main_curses_app(stdscr):
    curses.curs_set(0); curses.start_color(); curses.use_default_colors(); curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE) 
    main_menu(stdscr)

if __name__ == "__main__":
    ensure_radio_dir_exists()
    if not check_and_install_dependencies(): exit(1)
    try: import requests
    except ImportError:
        print("[!] Python library 'requests' not installed. Attempting to install...")
        try:
            subprocess.run(["pip", "install", "requests"], check=True, capture_output=True)
            print("Successfully installed 'requests'. Please restart the script.")
        except Exception as e: print(f"Failed to install 'requests'. Please run: pip install requests\nError: {e}")
        exit(1)
    try: curses.wrapper(main_curses_app)
    except curses.error as e: print(f"\nTerminal error: {e}"); print("Your terminal might be too small or not fully supported.")
    except KeyboardInterrupt: print("\nExiting...")
    finally:
        stop_music()
        clear_termux_notification()