import os
import shutil

def extract_images():
    source_dir = os.path.expanduser("~/DedSec/Images")
    target_dir = os.path.expanduser("~/storage/downloads/Extracted_Images")
    
    if not os.path.exists(source_dir):
        print(f"Source directory does not exist: {source_dir}")
        return
    
    print("Images will be extracted to your Downloads folder. Check your Files app.")
    confirm = input("Do you want to proceed? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Operation cancelled.")
        return
    
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
        print(f"Existing folder '{target_dir}' removed.")
    
    os.makedirs(target_dir)
    print(f"Created target directory: {target_dir}")
    
    for root, dirs, files in os.walk(source_dir):
        relative_path = os.path.relpath(root, source_dir)
        dest_root = os.path.join(target_dir, relative_path)
        
        if not os.path.exists(dest_root):
            os.makedirs(dest_root)
        
        for file in files:
            if file.lower().endswith((".jpg", ".png", ".jpeg", ".gif", ".bmp")):
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_root, file)
                shutil.copy2(src_file, dest_file)
                print(f"Extracted: {src_file} -> {dest_file}")
    
    print("Extraction completed successfully. Check your Downloads folder.")

def main():
    extract_images()

if __name__ == "__main__":
    main()
