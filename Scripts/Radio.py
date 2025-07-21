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
current_song = "No station selected / Nothing playing" # More informative default
wave_chars = [' ', '▂', '▃', '▄', '▅', '▆', '▇', '█']
current_volume = 50  # start at 50%
stop_playback_event = threading.Event() # Event to signal playback thread to stop

# --- Dependency auto-install (optional) ---
def auto_install_dependencies():
    try:
        subprocess.run(["pkg", "install", "-y",
                        "git", "mpv", "pulseaudio", "alsa-utils"], check=True)
    except Exception:
        pass  # Fail silently if not possible

def ensure_pulseaudio_running():
    try:
        subprocess.run(["pulseaudio", "--check"], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        subprocess.Popen(["pulseaudio", "--start"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# --- Radio directory (no longer creating 'Radio' folder) ---
def get_stations():
    lst = []
    # Look for subdirectories within the cloned repository path
    if os.path.exists(DEDSEC_RADIO_PATH):
        for item in os.listdir(DEDSEC_RADIO_PATH):
            path = os.path.join(DEDSEC_RADIO_PATH, item)
            if os.path.isdir(path) and any(f.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS) for f in os.listdir(path)):
                lst.append(item)
    return sorted(lst)

# --- Playback ---
def play_station_music(stdscr):
    global current_player_process, is_playing, playback_thread, current_station_index, playback_error_message, current_song, stop_playback_event
    
    stop_music() # Stop any existing playback and clear event

    playback_error_message = None # Clear any previous error message

    if not stations:
        playback_error_message = "No stations found. Update repository."
        current_song = "No station selected"
        return
    if not (0 <= current_station_index < len(stations)):
        current_station_index = 0 # Default to first station if out of bounds

    # Station path is now within the cloned repository
    station_path = os.path.join(DEDSEC_RADIO_PATH, stations[current_station_index])
    song_files = [os.path.join(station_path, f)
                  for f in os.listdir(station_path)
                  if f.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS)]
    if not song_files:
        playback_error_message = f"No supported files in '{stations[current_station_index]}'."
        current_song = "No songs in station"
        return
    
    random.shuffle(song_files) # Shuffle the songs for the station

    def task():
        global current_player_process, is_playing, playback_error_message, current_song, stop_playback_event
        is_playing = True
        current_player_process = None # Ensure it's reset at start of task
        
        try:
            for selected_song_path in song_files: # Loop through shuffled songs
                if stop_playback_event.is_set(): # Check if stop signal received
                    break
                
                current_song = os.path.basename(selected_song_path) # Update current song
                
                # Stop any previous mpv process for clean transition
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
                    time.sleep(0.1) # Wait for song to finish or stop signal
                
        except FileNotFoundError:
            playback_error_message = "'mpv' not found. Please install it."
            current_song = "Error: mpv not found"
        except Exception as e:
            playback_error_message = f"Playback error: {e}"
            current_song = f"Error: {e}"
        finally:
            is_playing = False
            if current_player_process and current_player_process.poll() is None:
                current_player_process.terminate()
                try:
                    current_player_process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    current_player_process.kill()
            current_player_process = None
            if not stop_playback_event.is_set(): # If not stopped by user, means playback finished
                current_song = "Playback finished. Select station again."
            else:
                current_song = "Playback stopped." # Set to stopped if user initiated stop


    playback_thread = threading.Thread(target=task, daemon=True)
    playback_thread.start()

def stop_music():
    global current_player_process, is_playing, current_song, stop_playback_event
    
    if is_playing: # Only set event if something is currently playing
        stop_playback_event.set() # Signal the playback thread to stop
        if playback_thread and playback_thread.is_alive():
            playback_thread.join(timeout=2) # Wait for the thread to finish
    
    if current_player_process and current_player_process.poll() is None:
        current_player_process.terminate()
        try:
            current_player_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            current_player_process.kill()
    
    is_playing = False
    current_player_process = None
    stop_playback_event.clear() # Clear the event for next playback
    current_song = "No station selected / Nothing playing" # Reset on full stop

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
        return f"Volume error: {e}"

def change_volume(action):
    global current_volume
    if action == "increase":
        current_volume = min(100, current_volume + 5)
    elif action == "decrease":
        current_volume = max(0, current_volume - 5)
    return set_volume(current_volume)

# --- Update repository ---
def update_radio_stations(stdscr):
    # No longer ensuring a separate 'Radio' directory
    stdscr.clear()
    stdscr.addstr(0, 0, "Updating DedSec-Radio...")
    stdscr.refresh()
    try:
        # Check if the repository directory exists and contains a .git folder
        if os.path.isdir(DEDSEC_RADIO_PATH) and os.path.isdir(os.path.join(DEDSEC_RADIO_PATH, ".git")):
            subprocess.run(["git", "-C", DEDSEC_RADIO_PATH, "pull"],
                           check=True, stdout=subprocess.DEVNULL)
            msg = "Repository updated."
        else:
            # Clone directly into the home directory, naming it REPO_NAME
            subprocess.run(["git", "clone", GIT_REPO, DEDSEC_RADIO_PATH],
                           check=True, stdout=subprocess.DEVNULL)
            msg = "Repository cloned."
        stdscr.addstr(2, 0, msg) # Display the success message
    except Exception as e:
        stdscr.addstr(2, 0, f"Error: {e}") # Display the error message
    stdscr.addstr(4, 0, "Press any key to return...")
    stdscr.getch()
    global stations
    stations = get_stations()

# --- Display helpers ---
def display_status_message(stdscr, msg, is_error=False):
    h, w = stdscr.getmaxyx()
    try:
        # Place status message at the bottom, centered
        y = h - 1
        x = max(0, (w - len(msg)) // 2)
        draw_safe(stdscr, y, x, msg, curses.A_BOLD if is_error else curses.A_NORMAL)
        stdscr.refresh()
    except curses.error:
        pass # Handle cases where terminal might be too small

def draw_safe(stdscr, y, x, text, attr=0):
    h, w = stdscr.getmaxyx()
    if 0 <= y < h and 0 <= x < w:
        # Ensure text is truncated if it exceeds available width
        max_len = w - x
        if max_len < 0: max_len = 0 # Prevent negative slice
        try:
            stdscr.addstr(y, x, text[:max_len], attr)
        except curses.error:
            pass

def draw_volume_bar(stdscr, y, x, width, volume_percent):
    # Ensure width is at least a minimum for the bar to be visible
    min_bar_display_width = 10 # "[][100%]" requires at least this much space
    if width < min_bar_display_width:
        draw_safe(stdscr, y, x, f"Vol: {volume_percent}%")
        return

    bar_width_chars = max(1, width - 10) # Allocate space for '[]' and '%', ensure at least 1 char for bar
    filled = int(bar_width_chars * volume_percent / 100)
    empty = bar_width_chars - filled
    bar = '[' + '█' * filled + '░' * empty + ']'
    text = f"{bar} {volume_percent}%"
    draw_safe(stdscr, y, x, text)

# --- Main Menu ---
def main_menu(stdscr):
    global stations
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    menu = ["Play Radio", "Update Repository", "Exit"]
    sel = 0

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        # Minimum terminal size check
        min_h, min_w = 10, 40
        if h < min_h or w < min_w:
            draw_safe(stdscr, 0, 0, f"Terminal too small. Min: {min_h}x{min_w}. Current: {h}x{w}")
            draw_safe(stdscr, 1, 0, "Resize and retry.")
            stdscr.refresh()
            time.sleep(0.1) # Small delay to prevent busy loop
            continue # Skip menu drawing until resized

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
                    display_status_message(stdscr, "No stations available. Try updating repository.", True)
                    stdscr.getch()
                else:
                    radio_menu(stdscr)
            elif sel == 1:
                update_radio_stations(stdscr)
            else:
                stop_music()
                break

# --- Radio Menu with Wave & Volume Bar ---
def radio_menu(stdscr):
    global current_station_index, stations, playback_error_message, current_song, current_volume
    curses.curs_set(0)
    play_station_music(stdscr)

    wave_max_len_constant = 40 # Maximum desired visualizer length
    wave = "" # Initialize empty, will be populated on first draw

    last_wave_update = time.time()
    wave_update_interval = 0.1 # Update wave every 0.1 seconds for more dynamism

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        # Minimum terminal size check for radio menu
        min_h_needed = 12 # Base lines + wave + volume + controls (min)
        min_w_needed = 45 # Minimum width for a readable layout
        if h < min_h_needed or w < min_w_needed:
            draw_safe(stdscr, 0, 0, f"Terminal too small. Min: {min_h_needed}x{min_w_needed}. Current: {h}x{w}")
            draw_safe(stdscr, 1, 0, "Resize or press 'q' to go back.")
            stdscr.refresh()
            key = stdscr.getch() # Still allow 'q' to exit
            if key == ord('q'):
                break
            time.sleep(0.1)
            continue

        # Prepare lines for display
        display_lines = []
        display_lines.append("Radio")
        display_lines.append(f"Station: {stations[current_station_index]}")

        # Handle 'Playing Now' text wrapping
        playing_now_prefix = "Playing Now: "
        available_width_for_song = w - len(playing_now_prefix) - 2 # -2 for padding/border
        
        # Ensure available_width_for_song is at least positive for splitting
        if available_width_for_song < 1:
            available_width_for_song = 1 # Smallest possible
            
        if len(current_song) > available_width_for_song:
            # Split into two lines
            first_line_song = current_song[:available_width_for_song]
            second_line_song = current_song[available_width_for_song:]
            
            display_lines.append(f"{playing_now_prefix}{first_line_song}")
            # Center the second line of the song, or just put it under the first
            # For simplicity, let's just indent it or center it. Centering is better.
            display_lines.append(f"{second_line_song}") 
        else:
            display_lines.append(f"{playing_now_prefix}{current_song}")

        # Dynamic wave generation - recalculate max_wave_len_current
        # Ensure max_wave_len_current is at least 1 for the visualizer to draw
        max_wave_len_current = max(1, min(w - 4, wave_max_len_constant))
        if time.time() - last_wave_update > wave_update_interval:
            wave = "|" + "".join(random.choice(wave_chars) for _ in range(max_wave_len_current)) + "|"
            last_wave_update = time.time()
        display_lines.append(wave)

        # Calculate starting y position for content (centered)
        start_y = h // 2 - len(display_lines) // 2

        # Draw main display lines
        for idx, line in enumerate(display_lines):
            y = start_y + idx
            x = w // 2 - len(line) // 2 # Center each line
            draw_safe(stdscr, y, x, line)

        # Volume Bar
        vol_bar_y = start_y + len(display_lines) + 1 # Position below main lines with a gap
        vol_bar_x = max(0, w // 2 - (max_wave_len_current // 2)) # Align with wave if possible
        draw_volume_bar(stdscr, vol_bar_y, vol_bar_x, max_wave_len_current, current_volume) 

        # Controls
        controls = ["(←/→) Change Station", "(↑/↓) Volume (5%)", "(q) Back"]
        controls_start_y = vol_bar_y + 2 # Position below volume bar with a gap

        for i, ctl in enumerate(controls):
            y = controls_start_y + i
            x = w // 2 - len(ctl) // 2
            draw_safe(stdscr, y, x, ctl)

        if playback_error_message:
            display_status_message(stdscr, playback_error_message, True)

        stdscr.refresh()

        # Non-blocking getch to allow wave animation updates
        stdscr.nodelay(True)
        key = stdscr.getch()
        stdscr.nodelay(False) # Set back to blocking for other inputs

        if key == ord('q'):
            stop_music()
            break
        elif key == curses.KEY_LEFT:
            current_station_index = (current_station_index - 1) % len(stations)
            play_station_music(stdscr)
        elif key == curses.KEY_RIGHT:
            current_station_index = (current_station_index + 1) % len(stations)
            play_station_music(stdscr)
        elif key == curses.KEY_UP:
            change_volume("increase")
        elif key == curses.KEY_DOWN:
            change_volume("decrease")
        elif key == -1: # No key pressed, allow a small sleep for animation
            time.sleep(0.05) # Small sleep to reduce CPU usage when no key is pressed

# --- Main ---
if __name__ == "__main__":
    auto_install_dependencies()
    ensure_pulseaudio_running()
    # No longer calling ensure_radio_dir_exists() as the repo will be cloned directly
    stations = get_stations()
    set_volume(current_volume) # Initialize volume on startup
    try:
        curses.wrapper(main_menu)
    except KeyboardInterrupt:
        stop_music()
        print("Exiting...")
    except Exception as e:
        stop_music()
        print(f"Fatal error: {e}")