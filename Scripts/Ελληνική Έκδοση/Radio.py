import curses
import os
import subprocess
import random
import threading
import time

# --- Configuration ---
# Changed to download directly into home directory
GIT_REPO = "https://github.com/dedsec1121fk/DedSec-Radio"
REPO_NAME = "DedSec-Radio"
# DEDSEC_RADIO_PATH is now directly in the home directory
DEDSEC_RADIO_PATH = os.path.expanduser(f"~/{REPO_NAME}")
PLAY_CMD_BASE = "mpv --no-terminal --no-video"
SUPPORTED_AUDIO_EXTENSIONS = ('.mp3', '.wav', '.flac', '.ogg', '.m4a')

# --- Globals ---
current_station_index = 0
stations = []
current_player_process = None
is_playing = False
playback_thread = None
playback_error_message = None
current_song = "Δεν έχει επιλεγεί σταθμός / Δεν παίζει τίποτα"
wave_chars = [' ', '▂', '▃', '▄', '▅', '▆', '▇', '█']
current_volume = 50
stop_playback_event = threading.Event()

# --- Dependency auto-install (optional) ---
def auto_install_dependencies():
    try:
        subprocess.run(["pkg", "install", "-y",
                        "git", "mpv", "pulseaudio", "alsa-utils"], check=True)
    except Exception:
        pass

def ensure_pulseaudio_running():
    try:
        subprocess.run(["pulseaudio", "--check"], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        subprocess.Popen(["pulseaudio", "--start"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# --- Radio directory (no longer creating 'Radio' folder) ---
def get_stations():
    lst = []
    if os.path.exists(DEDSEC_RADIO_PATH):
        for item in os.listdir(DEDSEC_RADIO_PATH):
            path = os.path.join(DEDSEC_RADIO_PATH, item)
            if os.path.isdir(path) and any(f.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS) for f in os.listdir(path)):
                lst.append(item)
    return sorted(lst)

# --- Playback ---
def play_station_music(stdscr):
    global current_player_process, is_playing, playback_thread, current_station_index, playback_error_message, current_song, stop_playback_event
    
    stop_music()

    playback_error_message = None

    if not stations:
        playback_error_message = "Δεν βρέθηκαν σταθμοί. Ενημερώστε το αποθετήριο."
        current_song = "Δεν έχει επιλεγεί σταθμός"
        return
    if not (0 <= current_station_index < len(stations)):
        current_station_index = 0

    station_path = os.path.join(DEDSEC_RADIO_PATH, stations[current_station_index])
    song_files = [os.path.join(station_path, f)
                  for f in os.listdir(station_path)
                  if f.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS)]
    if not song_files:
        playback_error_message = f"Δεν υπάρχουν υποστηριζόμενα αρχεία στον '{stations[current_station_index]}'."
        current_song = "Δεν υπάρχουν τραγούδια στον σταθμό"
        return
    
    random.shuffle(song_files)

    def task():
        global current_player_process, is_playing, playback_error_message, current_song, stop_playback_event
        is_playing = True
        current_player_process = None
        
        try:
            for selected_song_path in song_files:
                if stop_playback_event.is_set():
                    break
                
                current_song = os.path.basename(selected_song_path)
                
                if current_player_process and current_player_process.poll() is None:
                    current_player_process.terminate()
                    try:
                        current_player_process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        current_player_process.kill()
                current_player_process = None

                parts = PLAY_CMD_BASE.split() + [selected_song_path]
                current_player_process = subprocess.Popen(parts,
                                                          stdout=subprocess.DEVNULL,
                                                          stderr=subprocess.DEVNULL)
                
                while current_player_process.poll() is None and not stop_playback_event.is_set():
                    time.sleep(0.1)
                
        except FileNotFoundError:
            playback_error_message = "Το 'mpv' δεν βρέθηκε. Παρακαλώ εγκαταστήστε το."
            current_song = "Σφάλμα: mpv δεν βρέθηκε"
        except Exception as e:
            playback_error_message = f"Σφάλμα αναπαραγωγής: {e}"
            current_song = f"Σφάλμα: {e}"
        finally:
            is_playing = False
            if current_player_process and current_player_process.poll() is None:
                current_player_process.terminate()
                try:
                    current_player_process.wait(timeout=1)
                    current_player_process.kill()
            current_player_process = None
            if not stop_playback_event.is_set():
                current_song = "Η αναπαραγωγή τελείωσε. Επιλέξτε ξανά σταθμό."
            else:
                current_song = "Η αναπαραγωγή σταμάτησε."


    playback_thread = threading.Thread(target=task, daemon=True)
    playback_thread.start()

def stop_music():
    global current_player_process, is_playing, current_song, stop_playback_event
    
    if is_playing:
        stop_playback_event.set()
        if playback_thread and playback_thread.is_alive():
            playback_thread.join(timeout=2)
    
    if current_player_process and current_player_process.poll() is None:
        current_player_process.terminate()
        try:
            current_player_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            current_player_process.kill()
    
    is_playing = False
    current_player_process = None
    stop_playback_event.clear()
    current_song = "Δεν έχει επιλεγεί σταθμός / Δεν παίζει τίποτα"

# --- Volume control using amixer ---
def set_volume(volume_percent):
    volume = max(0, min(100, volume_percent))
    try:
        if volume == 0:
            subprocess.run(["amixer", "set", "Master", "mute"],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(["amixer", "set", "Master", "unmute"],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["amixer", "sset", "Master", f"{volume}%"],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        return f"Σφάλμα έντασης: {e}"

# --- Update repository ---
def update_radio_stations(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "Ενημέρωση DedSec-Radio...")
    stdscr.refresh()
    try:
        if os.path.isdir(DEDSEC_RADIO_PATH) and os.path.isdir(os.path.join(DEDSEC_RADIO_PATH, ".git")):
            subprocess.run(["git", "-C", DEDSEC_RADIO_PATH, "pull"],
                           check=True, stdout=subprocess.DEVNULL)
            msg = "Το αποθετήριο ενημερώθηκε."
        else:
            subprocess.run(["git", "clone", GIT_REPO, DEDSEC_RADIO_PATH],
                           check=True, stdout=subprocess.DEVNULL)
            msg = "Το αποθετήριο κλωνοποιήθηκε."
        stdscr.addstr(2, 0, msg)
    except Exception as e:
        stdscr.addstr(2, 0, f"Σφάλμα: {e}")
    stdscr.addstr(4, 0, "Πατήστε οποιοδήποτε πλήκτρο για επιστροφή...")
    stdscr.getch()
    global stations
    stations = get_stations()

# --- Display helpers ---
def display_status_message(stdscr, msg, is_error=False):
    h, w = stdscr.getmaxyx()
    try:
        y = h - 1
        x = max(0, (w - len(msg)) // 2)
        draw_safe(stdscr, y, x, msg, curses.A_BOLD if is_error else curses.A_NORMAL)
        stdscr.refresh()
    except curses.error:
        pass

def draw_safe(stdscr, y, x, text, attr=0):
    h, w = stdscr.getmaxyx()
    if 0 <= y < h and 0 <= x < w:
        max_len = w - x
        if max_len < 0: max_len = 0
        try:
            stdscr.addstr(y, x, text[:max_len], attr)
        except curses.error:
            pass

# --- Main Menu ---
def main_menu(stdscr):
    global stations
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    menu = ["Αναπαραγωγή Ραδιοφώνου", "Ενημέρωση Αποθετηρίου", "Έξοδος"]
    sel = 0

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        min_h, min_w = 10, 40
        if h < min_h or w < min_w:
            draw_safe(stdscr, 0, 0, f"Το τερματικό είναι πολύ μικρό. Ελάχιστο: {min_h}x{min_w}. Τρέχον: {h}x{w}")
            draw_safe(stdscr, 1, 0, "Αλλάξτε το μέγεθος και δοκιμάστε ξανά.")
            stdscr.refresh()
            time.sleep(0.1)
            continue

        for i, item in enumerate(menu):
            y = h//2 - len(menu)//2 + i
            x = w//2 - len(item)//2
            attr = curses.color_pair(1) if i == sel else 0
            draw_safe(stdscr, y, x, item, attr)

        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP:
            sel = (sel - 1) % len(menu)
        elif key == curses.KEY_DOWN:
            sel = (sel + 1) % len(menu)
        elif key in (10, 13):
            if sel == 0:
                if not stations:
                    display_status_message(stdscr, "Δεν υπάρχουν διαθέσιμοι σταθμοί. Δοκιμάστε να ενημερώσετε το αποθετήριο.", True)
                    stdscr.getch()
                else:
                    radio_menu(stdscr)
            elif sel == 1:
                update_radio_stations(stdscr)
            else:
                stop_music()
                break

# --- Radio Menu with Wave ---
def radio_menu(stdscr):
    global current_station_index, stations, playback_error_message, current_song, current_volume
    curses.curs_set(0)
    play_station_music(stdscr)

    wave_max_len_constant = 40
    wave = ""

    last_wave_update = time.time()
    wave_update_interval = 0.1

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        min_h_needed = 12
        min_w_needed = 45
        if h < min_h_needed or w < min_w_needed:
            draw_safe(stdscr, 0, 0, f"Το τερματικό είναι πολύ μικρό. Ελάχιστο: {min_h_needed}x{min_w_needed}. Τρέχον: {h}x{w}")
            draw_safe(stdscr, 1, 0, "Αλλάξτε το μέγεθος ή πατήστε 'q' για επιστροφή.")
            stdscr.refresh()
            key = stdscr.getch()
            if key == ord('q'):
                break
            time.sleep(0.1)
            continue

        display_lines = []
        display_lines.append("Ραδιόφωνο")
        display_lines.append(f"Σταθμός: {stations[current_station_index]}")

        playing_now_prefix = "Τώρα παίζει: "
        available_width_for_song = w - len(playing_now_prefix) - 2
        
        if available_width_for_song < 1:
            available_width_for_song = 1
            
        if len(current_song) > available_width_for_song:
            first_line_song = current_song[:available_width_for_song]
            second_line_song = current_song[available_width_for_song:]
            
            display_lines.append(f"{playing_now_prefix}{first_line_song}")
            display_lines.append(f"{second_line_song}") 
        else:
            display_lines.append(f"{playing_now_prefix}{current_song}")

        max_wave_len_current = max(1, min(w - 4, wave_max_len_constant))
        if time.time() - last_wave_update > wave_update_interval:
            wave = "|" + "".join(random.choice(wave_chars) for _ in range(max_wave_len_current)) + "|"
            last_wave_update = time.time()
        display_lines.append(wave)

        start_y = h // 2 - len(display_lines) // 2

        for idx, line in enumerate(display_lines):
            y = start_y + idx
            x = w // 2 - len(line) // 2
            draw_safe(stdscr, y, x, line)

        controls = ["(←/→) Αλλαγή Σταθμού", "(q) Πίσω"]
        controls_start_y = start_y + len(display_lines) + 2

        for i, ctl in enumerate(controls):
            y = controls_start_y + i
            x = w // 2 - len(ctl) // 2
            draw_safe(stdscr, y, x, ctl)

        if playback_error_message:
            display_status_message(stdscr, playback_error_message, True)

        stdscr.refresh()

        stdscr.nodelay(True)
        key = stdscr.getch()
        stdscr.nodelay(False)

        if key == ord('q'):
            stop_music()
            break
        elif key == curses.KEY_LEFT:
            current_station_index = (current_station_index - 1) % len(stations)
            play_station_music(stdscr)
        elif key == curses.KEY_RIGHT:
            current_station_index = (current_station_index + 1) % len(stations)
            play_station_music(stdscr)
        elif key == -1:
            time.sleep(0.05)

# --- Main ---
if __name__ == "__main__":
    auto_install_dependencies()
    ensure_pulseaudio_running()
    stations = get_stations()
    set_volume(current_volume)
    try:
        curses.wrapper(main_menu)
    except KeyboardInterrupt:
        stop_music()
        print("Έξοδος...")
    except Exception as e:
        stop_music()
        print(f"Θανάσιμο σφάλμα: {e}")