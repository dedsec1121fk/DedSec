import os
import subprocess
import random
import requests

ADDON_REPO = "https://github.com/dedsec1121fk/DedSec_Radio_Add-On"
ADDON_DIR = os.path.expanduser("~/DedSec/DedSec_Radio_Songs_Add-On")
DEDSEC_DIR = os.path.expanduser("~/DedSec")

def get_repo_size():
    """Fetch repository size from GitHub API."""
    api_url = "https://api.github.com/repos/dedsec1121fk/DedSec_Radio_Add-On"
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
            os.makedirs(DEDSEC_DIR, exist_ok=True)
            os.system(f"git clone {ADDON_REPO} {ADDON_DIR}")
            print("\nDownload complete!")
        else:
            print("\nThis script requires the add-on to function. Exiting...")
            exit()

def list_radio_stations():
    return [f for f in os.listdir(ADDON_DIR) if os.path.isdir(os.path.join(ADDON_DIR, f)) and not f.startswith('.')]

def list_songs(station, shuffle=False):
    station_path = os.path.join(ADDON_DIR, station)
    songs = [f for f in os.listdir(station_path) if f.endswith(('.mp3', '.wav', '.flac'))]
    return random.sample(songs, len(songs)) if shuffle else sorted(songs)

def stop_music():
    subprocess.run(["termux-media-player", "stop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def play_song(song_path):
    stop_music()
    subprocess.run(["termux-media-player", "play", song_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def search_song():
    query = input("\nEnter song name (or part of it) to search: ").strip().lower()
    if not query:
        return None, None
    print("\nSearching for songs...")
    matching_songs = [(s, song) for s in list_radio_stations() for song in list_songs(s) if query in song.lower()]
    if not matching_songs:
        print("\nNo songs found.")
        return None, None
    for idx, (station, song) in enumerate(matching_songs, 1):
        print(f"  {idx}. {song} (Station: {station})")
    try:
        choice = int(input("\nEnter song number to play or 0 to return: "))
        if choice == 0:
            return None, None
        station, song = matching_songs[choice - 1]
        return station, song
    except (ValueError, IndexError):
        return None, None

def station_interface(selected_station, now_playing="None"):
    """Interface for a station folder; displays the songs and options.
       This function keeps you within the station after a song is selected from search.
    """
    while True:
        songs = list_songs(selected_station)
        os.system('cls' if os.name == 'nt' else 'clear')
        print("═" * 40)
        print(f" 📻 Station: {selected_station} ")
        print("═" * 40)
        for idx, song in enumerate(songs, 1):
            print(f"  {idx}. {song}")
        print(f"\n 🎶 Now Playing: {now_playing} ")
        print("\n  [N] Next | [S] Search | [B] Back | [E] Exit")
        command = input("\nEnter choice: ").strip().lower()
        if command == "e":
            stop_music()
            exit()
        elif command == "b":
            stop_music()
            break
        elif command == "n":
            now_playing = random.choice(songs)
            play_song(os.path.join(ADDON_DIR, selected_station, now_playing))
        elif command == "s":
            station, song = search_song()
            if station and song:
                selected_station = station  # Switch to the new station
                now_playing = song
                play_song(os.path.join(ADDON_DIR, selected_station, now_playing))
        else:
            # If user enters a number, try playing that song
            try:
                choice = int(command)
                if 1 <= choice <= len(songs):
                    now_playing = songs[choice - 1]
                    play_song(os.path.join(ADDON_DIR, selected_station, now_playing))
            except ValueError:
                continue

def radio():
    check_addon()
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("═" * 40)
        print("        📻 DedSec Radio 📻        ")
        print("═" * 40)
        stations = list_radio_stations()
        for idx, station in enumerate(stations, 1):
            print(f"  {idx}. {station}")
        print("\n  S. Search for a Song")
        print("  0. Exit Radio")
        choice = input("\nEnter the station number or 'S' to search: ").strip().lower()
        if choice == "s":
            station, song = search_song()
            if station and song:
                selected_station = station
                now_playing = song
                play_song(os.path.join(ADDON_DIR, selected_station, now_playing))
                station_interface(selected_station, now_playing)
            continue
        try:
            choice = int(choice)
            if choice == 0:
                stop_music()
                break
            selected_station = stations[choice - 1]
        except (ValueError, IndexError):
            continue
        now_playing = "None"
        station_interface(selected_station, now_playing)

if __name__ == "__main__":
    radio()

