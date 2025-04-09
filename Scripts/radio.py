#!/usr/bin/env python3
import os
import subprocess
import threading
import random
import time
import curses
import requests
import json
from mutagen.mp3 import MP3
from wcwidth import wcwidth

# ------------------------------
# Repository Download and Update Logic
# ------------------------------

REPO_URL = "https://github.com/dedsec1121fk/DedSec-Radio"
REPO_API_URL = "https://api.github.com/repos/dedsec1121fk/DedSec-Radio"
# Repository will be cloned into ~/Radio (not within any DedSec folder)
LOCAL_DIR = os.path.expanduser("~/Radio")

def run_command(command, cwd=None):
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return "", str(e)

def get_github_repo_size():
    try:
        response = requests.get(REPO_API_URL)
        if response.status_code == 200:
            size_kb = response.json().get('size', 0)
            return f"{size_kb / 1024:.2f} MB"
    except Exception:
        pass
    return "Unable to fetch repository size"

def clone_repo():
    print("[+] Radio repository not found. Cloning repository...")
    os.chdir(os.path.expanduser("~"))
    run_command(f"git clone {REPO_URL} Radio")
    return LOCAL_DIR

def force_update_repo(existing_path):
    if existing_path:
        print("[+] Radio repository found! Forcing a full update...")
        run_command("git fetch --all", cwd=existing_path)
        # The reset command will update all files to match origin/main and remove local changes.
        run_command("git reset --hard origin/main", cwd=existing_path)
        # Clean untracked files and directories (i.e. delete files/folders that are no longer in the repo)
        run_command("git clean -fd", cwd=existing_path)
        # Finally, pull any new commits.
        run_command("git pull", cwd=existing_path)
        print("[+] Repository fully updated.")

def update_repo():
    repo_size = get_github_repo_size()
    print(f"[+] GitHub repository size: {repo_size}")
    if os.path.isdir(LOCAL_DIR):
        run_command("git fetch", cwd=LOCAL_DIR)
        behind_count, _ = run_command("git rev-list HEAD..origin/main --count", cwd=LOCAL_DIR)
        try:
            behind_count = int(behind_count)
        except Exception:
            behind_count = 0
        if behind_count > 0:
            force_update_repo(LOCAL_DIR)
        else:
            print("[+] No available update found.")
    else:
        clone_repo()
    dedsec_size, _ = run_command(f"du -sh {LOCAL_DIR}")
    print(f"[+] Radio repository current size: {dedsec_size}")
    print("[+] Update process completed successfully!")
    time.sleep(2)

# ------------------------------
# Radio Player Functionality
# ------------------------------

# The repository directory where radio stations (folders) are stored.
RADIO_DIR = LOCAL_DIR

ASCII_ART_LINES = [
    "═══════════════════════════════════════════",
    "                📻 DedSec Radio 📻           ",
    "═══════════════════════════════════════════"
]

def list_radio_stations():
    if not os.path.isdir(RADIO_DIR):
        return []
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
    # Stop any previous playback and start new one.
    stop_music()
    try:
        process = subprocess.Popen(["termux-media-player", "play", song_path],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("Error: termux-media-player command not found.")
        return

    # Monitor playback using metadata from the Android player.
    while True:
        if stop_event.is_set():
            process.terminate()
            break

        try:
            result = subprocess.run(["termux-media-player", "metadata"],
                                    capture_output=True, text=True, timeout=1)
        except Exception:
            time.sleep(0.5)
            continue

        pos, dur = None, None
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

def prompt_download(stdscr):
    """
    Display the repository size and prompt the user with Y or N to download it.
    Returns True if the user chooses to download, False otherwise.
    """
    repo_size = get_github_repo_size()
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    prompt = f"Repository not found. Repo size: {repo_size}. Download? (y/n): "
    stdscr.addstr(height // 2, max((width - len(prompt)) // 2, 0), prompt)
    stdscr.refresh()
    while True:
        key = stdscr.getch()
        if key in (ord('y'), ord('Y')):
            clone_repo()
            stdscr.addstr(height // 2 + 1, max((width - 26) // 2, 0), "Downloading repository...")
            stdscr.refresh()
            time.sleep(2)
            return True
        elif key in (ord('n'), ord('N')):
            return False

def curses_main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(100)

    # Check if the repository exists.
    if not os.path.isdir(RADIO_DIR):
        download_choice = prompt_download(stdscr)
        if not download_choice:
            stdscr.erase()
            stdscr.addstr(0, 0, "Repository not downloaded. Returning to menu...")
            stdscr.refresh()
            time.sleep(2)
            return  # Exit the radio player (back to main menu if integrated)
    else:
        update_repo()

    stations = list_radio_stations()
    if not stations:
        stdscr.erase()
        stdscr.addstr(2, 0, "No stations found. Please check the repository content.")
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
        elif key in (10, 13):  # Enter key to play the selected station
            stop_event.set()  # Stop any current playback
            if playback_thread and playback_thread.is_alive():
                playback_thread.join(timeout=2)
            stop_event.clear()
            playback_thread = threading.Thread(target=play_station,
                                                 args=(stations[current_selection], stop_event, song_display),
                                                 daemon=True)
            playback_thread.start()
        elif key in (ord('q'), ord('Q')):
            stop_event.set()
            stop_music()
            if playback_thread and playback_thread.is_alive():
                playback_thread.join(timeout=2)
            break

if __name__ == "__main__":
    curses.wrapper(curses_main)

