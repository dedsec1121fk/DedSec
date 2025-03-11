import os
import subprocess

RADIO_DIR = os.path.expanduser("~/DedSec/Radio")

def list_radio_stations():
    return [f for f in os.listdir(RADIO_DIR)
            if os.path.isdir(os.path.join(RADIO_DIR, f)) and not f.startswith('.')]

def list_songs(station):
    """Optimized song listing using os.scandir to get modification times in one pass."""
    station_path = os.path.join(RADIO_DIR, station)
    songs = []
    with os.scandir(station_path) as entries:
        for entry in entries:
            if entry.is_file() and entry.name.endswith(('.mp3', '.wav', '.flac')):
                songs.append((entry.name, entry.stat().st_mtime))
    songs.sort(key=lambda x: x[1], reverse=True)  # Sort newest to oldest
    return [song[0] for song in songs]

def stop_music():
    subprocess.run(["termux-media-player", "stop"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def play_song(song_path):
    stop_music()
    subprocess.run(["termux-media-player", "play", song_path],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def play_station_songs(station):
    """Play all songs from a station (newest to oldest) with controls for navigation."""
    songs = list_songs(station)
    if not songs:
        print("\nNo songs found in this station.")
        return

    for song in songs:
        song_path = os.path.join(RADIO_DIR, station, song)
        print(f"\n🎶 Now Playing: {song}")
        play_song(song_path)

        while True:
            print("\n  [N] Next Song | [S] Stop & Exit to Menu | [E] Exit Radio")
            command = input("\nEnter choice: ").strip().lower()

            if command == "n":
                break  # Move to the next song
            elif command == "s":
                stop_music()
                return  # Return to the main menu
            elif command == "e":
                stop_music()
                exit()

def radio():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("═" * 40)
        print("        📻 DedSec Radio 📻        ")
        print("═" * 40)
        stations = list_radio_stations()
        for idx, station in enumerate(stations, 1):
            print(f"  {idx}. {station}")
        print("\n  0. Exit Radio")

        choice = input("\nEnter the station number: ").strip()
        try:
            choice = int(choice)
            if choice == 0:
                stop_music()
                break
            selected_station = stations[choice - 1]
        except (ValueError, IndexError):
            continue

        play_station_songs(selected_station)

if __name__ == "__main__":
    radio()

