import os
import subprocess
import threading
import random
import time
import curses
from mutagen.mp3 import MP3
from wcwidth import wcwidth

RADIO_DIR = os.path.expanduser("~/DedSec/Radio")

ASCII_ART_LINES = [
    "═══════════════════════════════════════════",
    "                📻 DedSec Radio 📻           ",
    "═══════════════════════════════════════════"
]

def list_radio_stations():
    return [
        f for f in os.listdir(RADIO_DIR)
        if os.path.isdir(os.path.join(RADIO_DIR, f)) and not f.startswith('.')
    ]

def list_songs(station):
    station_path = os.path.join(RADIO_DIR, station)
    return [f for f in os.listdir(station_path) if f.endswith('.mp3')]

def stop_music():
    subprocess.run(["termux-media-player", "stop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def play_song(song_path, stop_event):
    stop_music()
    process = subprocess.Popen(["termux-media-player", "play", song_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    duration = get_song_duration(song_path)
    start_time = time.time()
    
    while time.time() - start_time < duration:
        if stop_event.is_set():
            process.terminate()
            return
        time.sleep(0.5)  # Check every 0.5 sec if we should stop

def get_song_duration(song_path):
    try:
        return MP3(song_path).info.length  # Duration in seconds
    except:
        return 30.0  # Default fallback

def play_station(station, stop_event, song_display):
    stop_music()
    stop_event.clear()

    songs = list_songs(station)
    if not songs:
        song_display[0] = "No songs found."
        return
    
    random.shuffle(songs)
    for song in songs:
        if stop_event.is_set():
            return  # Stop playing immediately

        song_path = os.path.join(RADIO_DIR, station, song)
        song_display[0] = f"🎶 Now Playing: {song}"
        play_song(song_path, stop_event)

def wrap_text(text, max_width):
    """Wrap text based on display width using wcwidth."""
    lines, current_line, current_width = [], "", 0
    for char in text:
        w = max(wcwidth(char), 1)
        if current_width + w > max_width:
            lines.append(current_line)
            current_line, current_width = char, w
        else:
            current_line += char
            current_width += w
    if current_line:
        lines.append(current_line)
    return lines

def draw_centered_wrapped(stdscr, y, text, width, max_lines=None):
    lines = wrap_text(text, width)
    for i, line in enumerate(lines[:max_lines]):
        x = max((width - sum(max(wcwidth(ch), 1) for ch in line)) // 2, 0)
        stdscr.addstr(y + i, x, line)

def curses_main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(100)

    stations = list_radio_stations()
    if not stations:
        stdscr.addstr(2, 0, "No stations found.")
        stdscr.refresh()
        time.sleep(2)
        return

    current_selection, stop_event = 0, threading.Event()
    song_display, playback_thread = [""], None

    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()

        for i, line in enumerate(ASCII_ART_LINES):
            draw_centered_wrapped(stdscr, i, line, width)

        menu_start = len(ASCII_ART_LINES) + 1
        draw_centered_wrapped(stdscr, menu_start, "Use ↑/↓ to change station, Enter to play, 'q' to quit.", width)

        for idx, station in enumerate(stations):
            text = f"> {station}" if idx == current_selection else f"  {station}"
            y = menu_start + 2 + idx
            if idx == current_selection:
                stdscr.attron(curses.A_REVERSE)
                draw_centered_wrapped(stdscr, y, text, width)
                stdscr.attroff(curses.A_REVERSE)
            else:
                draw_centered_wrapped(stdscr, y, text, width)

        draw_centered_wrapped(stdscr, menu_start + 3 + len(stations), song_display[0], width, max_lines=2)
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_selection > 0:
            current_selection -= 1
        elif key == curses.KEY_DOWN and current_selection < len(stations) - 1:
            current_selection += 1
        elif key in (10, 13):  # Enter key (Play new station)
            stop_event.set()  # Stop the previous song immediately
            
            if playback_thread and playback_thread.is_alive():
                playback_thread.join()  # Ensure the old thread is fully stopped
            
            stop_event.clear()
            playback_thread = threading.Thread(target=play_station, args=(stations[current_selection], stop_event, song_display), daemon=True)
            playback_thread.start()
        elif key in (ord('q'), ord('Q')):  # Quit
            stop_event.set()
            stop_music()
            if playback_thread and playback_thread.is_alive():
                playback_thread.join()
            break

if __name__ == "__main__":
    curses.wrapper(curses_main)

