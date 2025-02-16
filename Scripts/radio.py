import os
import subprocess
import random
import requests

ADDON_REPO = "https://github.com/dedsec1121fk/DedSec_Radio_Songs_Add-On"
ADDON_DIR = os.path.expanduser("~/DedSec/DedSec_Radio_Songs_Add-On")
DEDSEC_DIR = os.path.expanduser("~/DedSec")

def get_repo_size():
    """Fetch repository size from GitHub API."""
    api_url = "https://api.github.com/repos/dedsec1121fk/DedSec_Radio_Songs_Add-On"
    try:
        response = requests.get(api_url).json()
        if "size" in response:
            size_mb = response["size"] / 1024  # Convert KB to MB
            return f"{size_mb:.2f} MB"
    except:
        pass
    return "Unknown size"

def check_addon():
    """Check if the add-on is downloaded, prompt user if not."""
    if not os.path.exists(ADDON_DIR):
        size = get_repo_size()
        print(f"\nDo you want to download the Radio Add-On that is currently {size}?")
        choice = input("Yes/No: ").strip().lower()
        if choice == "yes":
            print("\nDownloading Add-On...")
            if not os.path.exists(DEDSEC_DIR):
                os.makedirs(DEDSEC_DIR)
            os.system(f"git clone {ADDON_REPO} {ADDON_DIR}")
            print("\nDownload complete!")
        else:
            print("\nThis script requires the add-on to function. Exiting...")
            exit()

def list_radio_stations():
    """List all available radio stations, excluding hidden folders like '.git'."""
    return [f for f in os.listdir(ADDON_DIR) 
            if os.path.isdir(os.path.join(ADDON_DIR, f)) and not f.startswith('.')]

def list_songs(station, shuffle=False):
    """List all songs in the selected radio station."""
    station_path = os.path.join(ADDON_DIR, station)
    songs = [f for f in os.listdir(station_path) if f.endswith(('.mp3', '.wav', '.flac'))]
    
    if shuffle:
        random.shuffle(songs)
    else:
        songs.sort()
    
    return songs

def stop_music():
    subprocess.run(["termux-media-player", "stop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def pause_music():
    subprocess.run(["termux-media-player", "pause"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def resume_music():
    subprocess.run(["termux-media-player", "play"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def play_song(song_path):
    stop_music()
    subprocess.run(["termux-media-player", "play", song_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def radio():
    check_addon()
    
    while True:
        os.system('clear')
        print("═" * 40)
        print("        📻 DedSec Radio 📻        ")
        print("═" * 40)

        stations = list_radio_stations()
        if not stations:
            print("\nNo radio stations found in the add-on folder.")
            return

        for idx, station in enumerate(stations, 1):
            print(f"  {idx}. {station}")

        print("\n  0. Exit Radio")
        print("═" * 40)

        try:
            choice = int(input("\nEnter the number of the Radio Station: "))
            if choice == 0:
                print("\nExiting Radio...")
                stop_music()
                os.system("python menu.py")  # Return to the main menu
                return
            elif 1 <= choice <= len(stations):
                selected_station = stations[choice - 1]
            else:
                print("\nInvalid choice. Try again.")
                continue
        except ValueError:
            print("\nInvalid input. Please enter a number.")
            continue

        shuffle_mode = False
        songs = list_songs(selected_station, shuffle_mode)
        if not songs:
            print(f"\nNo songs found in {selected_station}.")
            input("Press Enter to return to station selection...")
            continue

        song_index = 0
        is_paused = False

        while True:
            os.system('clear')
            print("═" * 40)
            print(f" 📻 Station: {selected_station}  |  Shuffle: {'ON' if shuffle_mode else 'OFF'} ")
            print("═" * 40)

            for idx, song in enumerate(songs, 1):
                print(f"  {idx}. {song}")

            print("\n  [N] Next | [P] Pause | [R] Resume | [S] Shuffle | [B] Back | [E] Exit")
            print("═" * 40)

            try:
                command = input("\nEnter song number or command: ").strip().lower()

                if command == "e":
                    print("\nExiting Radio...")
                    stop_music()
                    os.system("python menu.py")  # Return to the main menu
                    return
                elif command == "b":
                    stop_music()
                    break
                elif command == "n":
                    song_index = (song_index + 1) % len(songs)
                    is_paused = False
                elif command == "p":
                    pause_music()
                    is_paused = True
                    print("\nMusic Paused.")
                elif command == "r":
                    if is_paused:
                        resume_music()
                        is_paused = False
                        print("\nResuming Music.")
                    else:
                        print("\nMusic is not paused.")
                elif command == "s":
                    shuffle_mode = not shuffle_mode
                    songs = list_songs(selected_station, shuffle_mode)
                    song_index = 0
                    print(f"\nShuffle {'enabled' if shuffle_mode else 'disabled'}.")
                    continue
                else:
                    choice = int(command) - 1
                    if 0 <= choice < len(songs):
                        song_index = choice
                        is_paused = False
                    else:
                        print("\nInvalid selection. Try again.")
                        continue

                if not is_paused:
                    song_path = os.path.join(ADDON_DIR, selected_station, songs[song_index])
                    print(f"\nNow Playing: {songs[song_index]}")
                    play_song(song_path)

            except ValueError:
                print("\nInvalid input. Please enter a number or command.")

if __name__ == "__main__":
    radio()

