import os
import subprocess
import requests

# Repository details
REPO_URL = "https://github.com/dedsec1121fk/DedSec.git"
LOCAL_DIR = "DedSec"
REPO_API_URL = "https://api.github.com/repos/dedsec1121fk/DedSec"

def run_command(command, cwd=None):
    """Runs a shell command and returns output"""
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip()

def find_dedsec():
    """Searches for an existing DedSec directory in Termux storage"""
    print("[+] Searching for an existing DedSec directory...")
    search_cmd = "find ~ -type d -name 'DedSec' 2>/dev/null"
    output, _ = run_command(search_cmd)

    paths = output.split("\n") if output else []
    if paths:
        print(f"[+] Found DedSec at: {paths[0]}")
        return paths[0]  # Return the first found path
    return None

def get_directory_size(path):
    """Returns the total size of the directory in a human-readable format"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)
    # Convert to a human-readable format (MB, GB)
    if total_size > 1e9:
        return f"{total_size / 1e9:.2f} GB"
    elif total_size > 1e6:
        return f"{total_size / 1e6:.2f} MB"
    else:
        return f"{total_size / 1e3:.2f} KB"

def get_github_repo_size():
    """Gets the size of the GitHub repository using GitHub API"""
    response = requests.get(REPO_API_URL)
    if response.status_code == 200:
        data = response.json()
        size_kb = data.get('size', 0)
        size_mb = size_kb / 1024
        return f"{size_mb:.2f} MB"
    else:
        return "Unable to fetch repository size from GitHub"

def clone_repo():
    """Clones the repository if DedSec does not exist"""
    print("[+] DedSec not found. Cloning repository...")
    run_command(f"git clone {REPO_URL}")
    return os.path.join(os.getcwd(), LOCAL_DIR)

def clone_or_update_repo(existing_path):
    """Clones if DedSec doesn't exist, otherwise updates it"""
    if existing_path:
        print("[+] DedSec found! Checking for update size...")
        current_size = get_directory_size(existing_path)
        print(f"Current size of the repository: {current_size}")

        # Check for changes and get the size of the update
        output, _ = run_command("git fetch --dry-run", cwd=existing_path)
        if output:
            print("[+] Changes detected!")
            # Check the size of the update using git
            run_command("git fetch", cwd=existing_path)
            output, _ = run_command("git diff --stat HEAD..origin/main", cwd=existing_path)
            if output:
                print(f"Update size:\n{output}")
                return True
            else:
                print("[+] No actual changes detected.")
                return False
        else:
            print("[+] No changes detected. Everything is up to date.")
            return False
    else:
        return clone_repo()

def apply_changes(existing_path):
    """Handles additions, modifications, deletions, and untracked files"""
    os.chdir(existing_path)
    
    # Get list of changes (including untracked files)
    output, _ = run_command("git status --porcelain")

    if not output:
        print("[+] No changes to apply.")
    else:
        print("[+] Applying changes...")

        # Process each line of the git status output
        for line in output.split("\n"):
            status, file_path = line[:2], line[3:]

            if status in (" M", "A "):  # Modified or added
                print(f"[UPDATED] {file_path}")
            elif status in ("D "):  # Deleted
                print(f"[DELETED] {file_path}")
                os.remove(file_path)
            elif status == "??":  # Untracked files
                print(f"[NEW FILE] {file_path}")

        print("[+] All changes applied successfully.")
    
    os.chdir("..")

def prompt_user_for_confirmation(update_exists):
    """Prompt the user for confirmation before applying updates"""
    if update_exists:
        user_input = input("[+] An update has been detected. Do you want to apply the changes? (yes/no): ").strip().lower()
        return user_input == 'yes'
    return True

if __name__ == "__main__":
    # Inform user about GitHub repository size before cloning
    repo_size = get_github_repo_size()
    print(f"[+] The size of the GitHub repository is: {repo_size}")

    # Check if DedSec exists and if not, inform the user about cloning
    existing_dedsec_path = find_dedsec()
    
    if existing_dedsec_path:
        # If DedSec exists, show its current size
        print(f"[+] DedSec directory found: {existing_dedsec_path}")
        current_size = get_directory_size(existing_dedsec_path)
        print(f"Current size of the repository: {current_size}")
    else:
        # If DedSec is not found, report and ask for cloning
        print("[+] DedSec directory not found.")
        user_input = input("[+] Do you want to clone the repository? (yes/no): ").strip().lower()
        if user_input == "yes":
            # Clone the repository and display size of the new repository
            existing_dedsec_path = clone_repo()
            current_size = get_directory_size(existing_dedsec_path)
            print(f"Cloned repository size: {current_size}")
        else:
            print("[+] Operation cancelled. Exiting...")
            exit(0)
    
    # Check for updates and show update size
    update_exists = clone_or_update_repo(existing_dedsec_path)
    
    if update_exists and prompt_user_for_confirmation(update_exists):
        apply_changes(existing_dedsec_path)
    else:
        print("[+] No updates applied.")
    
    # Final size after changes
    final_size = get_directory_size(existing_dedsec_path if existing_dedsec_path else LOCAL_DIR)
    print(f"[+] Final size of the repository: {final_size}")
