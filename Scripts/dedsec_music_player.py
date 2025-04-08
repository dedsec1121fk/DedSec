#!/usr/bin/env python3
import os
import curses
import subprocess
import shutil
import random

# Define supported sound file extensions
SOUND_EXTENSIONS = ('.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac')

HEADER = "DedSec Music Player"

def find_music_folders(root):
    """
    Walk through the directory tree starting at root and collect all folders 
    that contain at least one sound file.
    """
    music_folders = []
    for dirpath, _, filenames in os.walk(root):
        if any(f.lower().endswith(SOUND_EXTENSIONS) for f in filenames):
            music_folders.append(dirpath)
    return music_folders

def list_sound_files(folder):
    """
    List only the sound files in the specified folder.
    """
    return [f for f in os.listdir(folder)
            if f.lower().endswith(SOUND_EXTENSIONS) and os.path.isfile(os.path.join(folder, f))]

def play_music_command(file_path):
    """
    Launch the Termux media player to play a file.
    Returns a subprocess.Popen object.
    """
    # Check if termux-media-player exists
    if shutil.which("termux-media-player") is None:
        raise FileNotFoundError("termux-media-player command not found. Please install the termux-api package.")
    return subprocess.Popen(["termux-media-player", "play", file_path])

def stop_music():
    """
    Issue a stop command to Termux media player.
    """
    subprocess.run(["termux-media-player", "stop"])

def display_menu(stdscr, options, title, include_back=False):
    """
    Display a vertical menu using curses.
    A header ("DedSec Music Player") is shown at the top.
    If include_back is True, an extra option "Back to folders" is appended.
    
    Returns:
       - An index (0 to len(options)-1) if a normal option is selected.
       - -1 if "Back to folders" is selected.
       - None if user presses 'q'.
    """
    curses.curs_set(0)
    # Make a local copy of options if we need to add the back option.
    menu_options = options.copy()
    if include_back:
        menu_options.append("Back to folders")
    current = 0
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        # Display header
        header_x = max(0, width // 2 - len(HEADER) // 2)
        stdscr.addnstr(0, header_x, HEADER, width - header_x, curses.A_BOLD)
        # Display title below header
        title_x = max(0, width // 2 - len(title) // 2)
        stdscr.addnstr(2, title_x, title, width - title_x, curses.A_BOLD)
        # Calculate starting row for centering options (start at row 4)
        start_y = 4 + (height - 4 - len(menu_options)) // 2
        for idx, option in enumerate(menu_options):
            # Truncate option if it's too long for the screen
            option_display = option if len(option) <= width - 2 else option[:width - 5] + "..."
            x = max(0, width // 2 - len(option_display) // 2)
            y = start_y + idx
            if y >= height - 1:
                continue  # Avoid writing outside the window
            if idx == current:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addnstr(y, x, option_display, width - x)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addnstr(y, x, option_display, width - x)
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP and current > 0:
            current -= 1
        elif key == curses.KEY_DOWN and current < len(menu_options) - 1:
            current += 1
        elif key in [10, 13]:
            # If back option was included and selected, return -1.
            if include_back and current == len(menu_options) - 1:
                return -1
            else:
                return current
        elif key in [ord('q'), ord('Q')]:
            return None

def playlist_controls(stdscr, playlist, folder, start_index):
    """
    Controls playback of the playlist.
    Use:
       n: Next song
       p: Previous song
       r: Shuffle playlist and restart
       b: Back to folders (exit playlist)
       s: Stop playback and exit program
       
    Once a song is launched, the player waits (blocking) for a key press.
    """
    current = start_index
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        song = playlist[current]
        msg = f"Now playing: {song}"
        instructions = "Controls: n=Next, p=Previous, r=Shuffle, b=Back to folders, s=Stop"
        stdscr.addnstr(0, 0, HEADER, width - 1, curses.A_BOLD)
        stdscr.addnstr(2, 0, msg, width - 1)
        stdscr.addnstr(4, 0, instructions, width - 1)
        stdscr.refresh()

        # Launch the current song
        file_path = os.path.join(folder, song)
        try:
            proc = play_music_command(file_path)
        except FileNotFoundError as e:
            stdscr.addnstr(6, 0, str(e), width - 1)
            stdscr.refresh()
            stdscr.getch()
            return "back"
        
        # Wait for user input (blocking)
        key = stdscr.getch()

        # Stop current playback before switching
        stop_music()

        if key in [ord('n'), ord('N')]:
            current = (current + 1) % len(playlist)
        elif key in [ord('p'), ord('P')]:
            current = (current - 1) % len(playlist)
        elif key in [ord('r'), ord('R')]:
            random.shuffle(playlist)
            current = 0
        elif key in [ord('b'), ord('B')]:
            return "back"
        elif key in [ord('s'), ord('S')]:
            return "stop"
        # If an unrecognized key is pressed, continue with the same song.

def main_curses(stdscr):
    """
    Main curses UI:
      - First, select a folder (displaying folder names).
      - Then, select a sound file from inside that folder (with an extra "Back to folders" option).
      - Then, control playback with playlist_controls.
      After exiting the playlist, you return to the folder selection menu.
    """
    while True:
        root = os.path.expanduser("~")
        music_folders = find_music_folders(root)
        if not music_folders:
            stdscr.clear()
            stdscr.addnstr(0, 0, f"{HEADER}\nNo music folders found in {root}", curses.COLS - 1)
            stdscr.refresh()
            stdscr.getch()
            return

        # Display folder selection menu (using folder basenames)
        folder_labels = [os.path.basename(folder) or folder for folder in music_folders]
        folder_index = display_menu(stdscr, folder_labels, "Select a folder containing music")
        if folder_index is None:
            break
        chosen_folder = music_folders[folder_index]

        # List only the sound files in the chosen folder.
        sound_files = list_sound_files(chosen_folder)
        if not sound_files:
            stdscr.clear()
            stdscr.addnstr(0, 0, f"{HEADER}\nNo sound files found in the selected folder.", curses.COLS - 1)
            stdscr.refresh()
            stdscr.getch()
            continue

        # In the file selection menu, include an extra "Back to folders" option.
        file_index = display_menu(stdscr, sound_files, "Select a sound file to start", include_back=True)
        if file_index is None:
            break
        # If user selected "Back to folders", go back.
        if file_index == -1:
            continue

        result = playlist_controls(stdscr, sound_files, chosen_folder, file_index)
        if result == "stop":
            break
        # If "back" is returned from playlist_controls, loop back to folder selection.
        stdscr.clear()
        stdscr.addnstr(0, 0, "Returning to folder selection...", curses.COLS - 1)
        stdscr.refresh()
        curses.napms(1000)

def main():
    curses.wrapper(main_curses)

if __name__ == "__main__":
    main()
