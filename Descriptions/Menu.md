# DedSec Script Launcher

This Python script (`menu.py`) allows you to manage and run various Python scripts stored in a specific directory (`~/DedSec/Scripts`). Upon execution, it ensures that your environment is properly set up by adding an entry to the `bash.bashrc` file to automatically navigate to the script directory and run the menu on startup.

## Features

- **Startup Setup**: Automatically adds a line to the `bash.bashrc` file to run the `menu.py` script on startup.
- **Script Menu**: Displays a list of all available Python scripts (except `menu.py`) within the `~/DedSec/Scripts` directory.
- **Script Execution**: Allows you to select and execute a script directly from the menu.
- **Error Handling**: Provides error messages for missing files or directories and invalid script choices.

## Requirements

To use this script, you'll need:

- **Python 3.x**: The script is written in Python and requires Python 3 to run.
- **Termux (Android)**: The script is designed for use in Termux. You must have Termux installed on your Android device.
- **Directory Structure**:
  - The script expects a directory at `~/DedSec/Scripts` containing Python scripts you want to run.

## Installation

Follow the steps below to install and use the script:

1. **Clone the repository**:

    If you haven't done so already, clone the repository to your local machine or Android device:

    ```bash
    git clone https://github.com/yourusername/dedsec-script-launcher.git
    cd dedsec-script-launcher
    ```

2. **Prepare the Scripts Directory**:

    - Create a folder at `~/DedSec/Scripts`.
    - Place all your Python scripts (except `menu.py`) inside this directory.

    Example directory structure:

    ```
    ~/DedSec/Scripts/
        script1.py
        script2.py
        script3.py
    ```

3. **Run the Script**:

    To start the launcher, simply run the `menu.py` script:

    ```bash
    python3 menu.py
    ```

    The script will ensure that the startup setup is complete by adding the necessary line to the `bash.bashrc` file.

4. **Startup Setup**:

    After running the script, it will add a line to your `bash.bashrc` file to ensure that the menu runs every time you open a new Termux session:

    ```
    cd /data/data/com.termux/files/home/DedSec/Scripts && python menu.py
    ```

    This ensures that when you launch Termux, the script menu will appear automatically.

## How It Works

- **Startup Line Setup**: The script checks if the necessary line is present in the `bash.bashrc` file to run the `menu.py` script on startup. If the line is missing, it adds it.
  
- **Menu Display**: The script scans the `~/DedSec/Scripts` directory for Python files (excluding `menu.py`) and presents them as selectable options in a terminal menu. Each script is formatted with a title, where underscores (`_`) are replaced by spaces, and the first letter of each word is capitalized.

- **Script Execution**: After selecting a script, the script is executed directly within the Termux environment, using `python script_name.py`.

- **Exit Option**: The menu also provides an option to exit the program.

### Menu Options:

- **Select a Script**: Type the number corresponding to the script you want to run.
- **Exit**: Type `0` to exit the program.

## Error Handling

- **Missing `bash.bashrc` or `Scripts` Folder**: If the script cannot find the `bash.bashrc` or `~/DedSec/Scripts` folder, it will notify you with an error message and terminate.
- **Invalid Script Selection**: If you enter an invalid choice (a number outside the list), the script will ask you to try again.
- **Missing Scripts**: If no Python scripts are found in the `~/DedSec/Scripts` directory, the script will display a message saying "No scripts found in the Scripts folder."

## Troubleshooting

- **Permission Errors**: Ensure that you have the necessary permissions to modify files in the Termux environment, especially the `bash.bashrc` file.
- **Script Not Executing**: If a script does not run, ensure that the Python file is located inside the `~/DedSec/Scripts` directory and is a valid `.py` file.

## Customizing Your Scripts

You can personalize your experience by:

- Adding as many Python scripts as you like to the `~/DedSec/Scripts` directory.
- Renaming scripts or organizing them in subdirectories.
- Modifying the launcher to add more features, such as error handling for specific scripts or including additional commands for each script.