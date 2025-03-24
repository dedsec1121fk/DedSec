import os
import shutil

def main():
    # Get Termux home directory
    home = os.path.expanduser("~")
    
    # Define the source folder path (including the folder itself)
    source_folder = os.path.join(home, "DedSec", "Extra Content")
    
    # Define the destination folder where the entire folder will be copied
    destination_folder = os.path.join(home, "storage", "downloads", "Extra Content")
    
    # Check if the source folder exists
    if not os.path.exists(source_folder):
        print(f"[X] Source folder not found: {source_folder}")
        return
    
    # Create destination folder if it doesn't exist
    # shutil.copytree can create the folder, but we'll ensure its parent exists
    parent_destination = os.path.join(home, "storage", "downloads")
    if not os.path.exists(parent_destination):
        print(f"[X] Parent destination folder not found: {parent_destination}")
        return
    
    try:
        # Copy the entire folder (including its name and all contents)
        shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)
        print(f"[✓] Extraction complete! 'Extra Content' folder has been copied to: {destination_folder}")
    except Exception as e:
        print(f"[X] Error copying folder: {e}")

if __name__ == '__main__':
    main()

