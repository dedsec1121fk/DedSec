import os
import shutil
import subprocess
from blessed import Terminal

# Define paths
EXTRA_CONTENT_FOLDER = "/data/data/com.termux/files/home/DedSec/Extra Content"
DOWNLOADS_FOLDER = "/data/data/com.termux/files/home/storage/downloads"

# Ensure Extra Content Folder exists
if not os.path.exists(EXTRA_CONTENT_FOLDER):
    print(f"Error: {EXTRA_CONTENT_FOLDER} does not exist!")
    exit(1)

term = Terminal()

def list_files(directory):
    """Returns a list of files and folders in a directory."""
    try:
        return os.listdir(directory)
    except PermissionError:
        return ["[Permission Denied]"]

def extract_folder():
    """Extracts the extra content to Downloads."""
    destination = os.path.join(DOWNLOADS_FOLDER, "Extra Content")
    if os.path.exists(destination):
        shutil.rmtree(destination)  # Remove existing extracted folder
    shutil.copytree(EXTRA_CONTENT_FOLDER, destination)
    print(term.green(f"\nExtracted to {destination} successfully!"))
    input("\nPress Enter to exit...")

def view_files():
    """Allows user to browse files interactively."""
    current_path = EXTRA_CONTENT_FOLDER
    while True:
        files = list_files(current_path)
        files.insert(0, ".. (Go Back)")  # Add go-back option

        with term.cbreak(), term.hidden_cursor():
            print(term.clear)
            print(term.bold("Browsing: ") + term.cyan(current_path))
            print("\nUse ↑/↓ to navigate, Enter to open, 'q' to quit.\n")

            index = 0
            while True:
                for i, file in enumerate(files):
                    if i == index:
                        print(term.reverse(file))  # Highlight selection
                    else:
                        print(file)
                
                key = term.inkey()
                if key.code == term.KEY_UP:
                    index = (index - 1) % len(files)
                elif key.code == term.KEY_DOWN:
                    index = (index + 1) % len(files)
                elif key.code == term.KEY_ENTER:
                    selected = files[index]
                    if selected == ".. (Go Back)":
                        if current_path != EXTRA_CONTENT_FOLDER:
                            current_path = os.path.dirname(current_path)
                        break
                    selected_path = os.path.join(current_path, selected)
                    if os.path.isdir(selected_path):
                        current_path = selected_path
                        break
                    else:
                        open_file(selected_path)
                elif key == "q":
                    return

def open_file(filepath):
    """Opens a file based on its type."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in [".mp4", ".mp3", ".wav"]:
        subprocess.run(["termux-media-player", "play", filepath])
    elif ext in [".jpg", ".png", ".gif"]:
        subprocess.run(["termux-open", filepath])
    elif ext in [".txt", ".log"]:
        os.system(f"cat {filepath} | less")
    else:
        print(term.red(f"\nCannot preview {filepath}\n"))

def main():
    """Main menu."""
    options = ["View Files", "Extract to Downloads", "Exit"]
    index = 0

    while True:
        with term.cbreak(), term.hidden_cursor():
            print(term.clear)
            print(term.bold("Extra Content Manager"))
            print("\nUse ↑/↓ to navigate, Enter to select.\n")

            for i, option in enumerate(options):
                if i == index:
                    print(term.reverse(option))  # Highlight selection
                else:
                    print(option)

            key = term.inkey()
            if key.code == term.KEY_UP:
                index = (index - 1) % len(options)
            elif key.code == term.KEY_DOWN:
                index = (index + 1) % len(options)
            elif key.code == term.KEY_ENTER:
                if options[index] == "View Files":
                    view_files()
                elif options[index] == "Extract to Downloads":
                    extract_folder()
                elif options[index] == "Exit":
                    exit()

if __name__ == "__main__":
    main()

