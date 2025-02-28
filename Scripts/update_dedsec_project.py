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
    """Searches for an existing DedSec directory"""
    search_cmd = "find ~ -type d -name 'DedSec' 2>/dev/null"
    output, _ = run_command(search_cmd)
    paths = output.split("\n") if output else []
    return paths[0] if paths else None  # Return the first found path

def get_github_repo_size():
    """Gets the size of the GitHub repository using GitHub API"""
    response = requests.get(REPO_API_URL)
    if response.status_code == 200:
        size_kb = response.json().get('size', 0)
        return f"{size_kb / 1024:.2f} MB"
    return "Unable to fetch repository size"

def clone_repo():
    """Clones the repository"""
    print("[+] DedSec not found. Cloning repository...")
    run_command(f"git clone {REPO_URL}")
    return os.path.join(os.getcwd(), LOCAL_DIR)

def force_update_repo(existing_path):
    """Forcefully updates the repository to ensure all files, including README, are updated"""
    if existing_path:
        print("[+] DedSec found! Forcing a full update...")

        # Reset to the latest version
        run_command("git fetch --all", cwd=existing_path)
        run_command("git reset --hard origin/main", cwd=existing_path)
        run_command("git clean -fd", cwd=existing_path)  # Remove untracked files
        run_command("git pull", cwd=existing_path)  # Final pull to ensure everything is synced

        print("[+] Repository fully updated, including README and all other files.")

if __name__ == "__main__":
    # Inform user about GitHub repository size
    repo_size = get_github_repo_size()
    print(f"[+] GitHub repository size: {repo_size}")

    # Find or clone repository
    existing_dedsec_path = find_dedsec()
    if existing_dedsec_path:
        force_update_repo(existing_dedsec_path)
    else:
        existing_dedsec_path = clone_repo()

    print("[+] Update process completed successfully!")

