import os
import random
import subprocess

def list_folders(directory):
    return [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]

def play_music(folder_path):
    files = [f for f in os.listdir(folder_path) if f.endswith(('.mp3', '.wav', '.flac'))]
    random.shuffle(files)
    return files

def stop_music():
    subprocess.run(["termux-media-player", "stop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def radio_mode():
    base_dir = os.path.expanduser("~/DedSec/Radio Mode")
    
    while True:
        os.system('clear')
        print("═" * 40)
        print("        🎵 DedSec Radio Mode 🎵        ")
        print("═" * 40)
        print("\nSelect a Station:")
        folders = list_folders(base_dir)
        
        if not folders:
            print("No folders found in the Radio Mode directory.")
            return
        
        for idx, folder in enumerate(folders, 1):
            print(f"  {idx}. {folder}")
        
        print("\n  0. Exit Radio Mode")
        print("═" * 40)
        
        try:
            choice = int(input("\nEnter the number of the folder: "))
        except ValueError:
            print("\nInvalid input. Please enter a number.")
            input("Press Enter to try again...")
            continue
        
        if choice == 0:
            print("\nExiting Radio Mode...")
            stop_music()
            break
        
        if choice < 1 or choice > len(folders):
            print("\nInvalid choice. Try again.")
            input("Press Enter to return to the station list...")
            continue
        
        selected_folder = os.path.join(base_dir, folders[choice - 1])
        songs = play_music(selected_folder)
        
        if not songs:
            print(f"\nNo audio files found in {folders[choice - 1]}.")
            input("Press Enter to return to the station list...")
            continue
        
        print(f"\nNow Playing from {folders[choice - 1]}...")
        song_index = 0
        
        while True:
            if song_index < len(songs):
                current_song = songs[song_index]
                song_path = os.path.join(selected_folder, current_song)
                print("\n" + "═" * 40)
                print(f"  🎶 Now Playing: {current_song}")
                print("═" * 40)
                
                # Play the current song
                stop_music()
                subprocess.run(["termux-media-player", "play", song_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                print("\nNo more songs in the folder. Restarting shuffle...")
                songs = play_music(selected_folder)
                song_index = 0
                continue
            
            print("\nOptions:")
            print("  [S] Stop")
            print("  [C] Continue")
            print("  [B] Back to Station Choice")
            print("  [E] Exit Radio")
            print("═" * 40)
            
            command = input("Your choice: ").strip().upper()
            
            if command == "S":
                stop_music()
                print("\nRadio stopped.")
            elif command == "C":
                print("\nContinuing Radio...")
                song_index += 1
                continue
            elif command == "B":
                stop_music()
                print("\nReturning to Station Choice...")
                break
            elif command == "E":
                stop_music()
                print("\nExiting Radio...")
                return
            else:
                print("\nInvalid command. Try again.")
                continue

if __name__ == "__main__":
    radio_mode()
