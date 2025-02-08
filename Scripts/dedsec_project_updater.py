import os
import subprocess

# Path to the DedSec directory
dedsec_dir = "/data/data/com.termux/files/home/DedSec"

# GitHub repository URL
repo_url = "https://github.com/dedsec1121fk/DedSec"

# Function to clone or update the repository
def sync_dedsec():
    if not os.path.exists(dedsec_dir):
        # If DedSec directory doesn't exist, clone the repo
        print("Cloning the DedSec repository...")
        subprocess.run(["git", "clone", repo_url, dedsec_dir])
    else:
        # If DedSec directory exists, pull the latest changes
        print("Pulling the latest changes from DedSec repository...")
        subprocess.run(["git", "-C", dedsec_dir, "fetch", "--all"])
        subprocess.run(["git", "-C", dedsec_dir, "reset", "--hard", "origin/main"])
        print("Repository synced: Any removed or updated files will now be reflected.")

# Sync the DedSec repository
sync_dedsec()
