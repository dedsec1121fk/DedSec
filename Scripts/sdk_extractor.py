import os
import shutil

def extract_sdk():
    # Updated Source directory
    source_dir = os.path.expanduser("~/DedSec/SDK")
    
    # Target directory in Downloads
    target_dir = os.path.expanduser("~/storage/downloads/Extracted_SDK")
    
    if not os.path.exists(source_dir):
        print(f"Source directory does not exist: {source_dir}")
        return
    
    print("All files from DedSec/SDK will be extracted to your Downloads folder.")
    confirm = input("Do you want to proceed? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Operation cancelled.")
        return
    
    # If target exists, remove it
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
        print(f"Existing folder '{target_dir}' removed.")
    
    # Create target directory
    os.makedirs(target_dir)
    print(f"Created target directory: {target_dir}")
    
    # Walk through SDK and copy everything
    for root, dirs, files in os.walk(source_dir):
        relative_path = os.path.relpath(root, source_dir)
        dest_root = os.path.join(target_dir, relative_path)
        
        if not os.path.exists(dest_root):
            os.makedirs(dest_root)
        
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_root, file)
            shutil.copy2(src_file, dest_file)
            print(f"Copied: {src_file} -> {dest_file}")
    
    print("Extraction completed successfully. Check your Downloads folder at Extracted_SDK.")

def main():
    extract_sdk()

if __name__ == "__main__":
    main()
