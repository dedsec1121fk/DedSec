#!/usr/bin/env python3
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
    try:
        subprocess.run(["termux-media-player", "stop"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("Error: termux-media-player command not found.")

def play_song(song_path, stop_event):
    # Stop any previous playback and start a new one
    stop_music()
    try:
        process = subprocess.Popen(["termux-media-player", "play", song_path],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("Error: termux-media-player command not found.")
        return

    # Monitor playback using metadata from the Android player
    while True:
        if stop_event.is_set():
            process.terminate()
            break

        try:
            result = subprocess.run(["termux-media-player", "metadata"],
                                    capture_output=True, text=True, timeout=1)
        except Exception:
            # In case of an error or timeout, wait briefly and try again.
            time.sleep(0.5)
            continue

        pos, dur = None, None
        # Parse the metadata output for "position" and "duration"
        for line in result.stdout.splitlines():
            if line.startswith("position:"):
                try:
                    pos = float(line.split(":", 1)[1].strip())
                except ValueError:
                    pos = None
            elif line.startswith("duration:"):
                try:
                    dur = float(line.split(":", 1)[1].strip())
                except ValueError:
                    dur = None

        # If both values are available and the current position exceeds or equals duration, break.
        if pos is not None and dur is not None and pos >= dur:
            break

        time.sleep(0.5)

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
        try:
            stdscr.addstr(y + i, x, line)
        except curses.error:
            pass

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

    current_selection = 0
    stop_event = threading.Event()
    song_display = [""]
    playback_thread = None

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
        elif key in (10, 13):  # Enter key (play new station)
            stop_event.set()  # Signal the current playback to stop
            if playback_thread and playback_thread.is_alive():
                playback_thread.join(timeout=2)
            stop_event.clear()
            playback_thread = threading.Thread(target=play_station,
                                                 args=(stations[current_selection], stop_event, song_display),
                                                 daemon=True)
            playback_thread.start()
        elif key in (ord('q'), ord('Q')):  # Quit
            stop_event.set()
            stop_music()
            if playback_thread and playback_thread.is_alive():
                playback_thread.join(timeout=2)
            break

if __name__ == "__main__":
    curses.wrapper(curses_main)

