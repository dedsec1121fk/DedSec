# DedSec Sync Script

This Python script is designed to help you easily sync the **DedSec** GitHub repository on your local machine. It checks if the repository already exists and either clones it or pulls the latest updates to ensure your local copy is up-to-date with the main branch.

## Features:
- **Cloning the repository**: If the DedSec repository doesn't already exist on the specified path, the script will clone it from the official GitHub URL.
- **Updating the repository**: If the repository already exists, the script will fetch the latest changes from the remote and reset your local copy to match the remote main branch exactly, ensuring you have the most up-to-date version of the code.
- **Automatic path handling**: The script handles the path where the repository should be located, ensuring that your local environment remains organized.

If the DedSec repository doesn't exist at the specified path, it will be cloned. If it does exist, it will be updated with the latest changes from the main branch.

## How it Works:
- The script checks if the **DedSec** directory exists at the specified path.
- If not, it runs `git clone` to create a fresh copy of the repository.
- If the directory exists, it runs `git fetch --all` and `git reset --hard origin/main` to ensure your local repository matches the latest changes from the main branch, including any updates or removals.