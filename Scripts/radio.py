import os
import subprocess
import requests

ADDON_REPO = "https://github.com/dedsec1121fk/DedSec_Radio_Add-On"
ADDON_DIR = os.path.expanduser("~/DedSec/DedSec_Radio_Songs_Add-On")
DEDSEC_DIR = os.path.expanduser("~/DedSec")

def internet_available():
    """Check if the internet is accessible."""
    try:
        requests.get("https://api.github.com", timeout=5)
        return True
    except requests.RequestException:
        return False

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

def update_addon():
    """Check for updates in the Add-On repository and prompt the user to update."""
    if not internet_available():
        return
    if os.path.exists(ADDON_DIR) and os.path.exists(os.path.join(ADDON_DIR, ".git")):
        # Change to the add-on directory to run git commands
        current_dir = os.getcwd()
        os.chdir(ADDON_DIR)
        # Fetch updates from the remote repository
        subprocess.run(["git", "fetch"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Determine the current branch (e.g., main or master)
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                capture_output=True, text=True).stdout.strip()
        # Get a summary of differences between local and remote
        result = subprocess.run(["git", "diff", "--stat", f"HEAD", f"origin/{branch}"],
                                capture_output=True, text=True)
        diff_stat = result.stdout.strip()
        if diff_stat:
            print("\nAdd-On updates available:")
            print(diff_stat)
            choice = input("\nDo you want to update the Add-On? Yes/No: ").strip().lower()
            if choice == "yes":
                subprocess.run(["git", "pull"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("\nAdd-On updated successfully!")
            else:
                print("\nContinuing without updating the Add-On...")
        else:
            print("\nNo updates available for the Add-On.")
        os.chdir(current_dir)

def check_addon():
    """Ensure the Add-On is present; if not, prompt for download.
    If it exists, check for any updates."""
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
    else:
        update_addon()

def list_radio_stations():
    return [f for f in os.listdir(ADDON_DIR)
            if os.path.isdir(os.path.join(ADDON_DIR, f)) and not f.startswith('.')]

def list_songs(station):
    """Optimized song listing using os.scandir to get modification times in one pass."""
    station_path = os.path.join(ADDON_DIR, station)
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
        song_path = os.path.join(ADDON_DIR, station, song)
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
    check_addon()
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

