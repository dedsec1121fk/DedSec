#!/data/data/com.termux/files/usr/bin/bash

# --- 1. Termux Environment Setup and Core Packages ---
echo "1. Setting up storage, updating, and installing core packages..."

# Enable storage access and perform updates
termux-setup-storage
pkg update -y && pkg upgrade -y

# List of essential packages (including tor as specified in Settings.py)
CORE_PACKAGES="aapt clang cloudflared curl ffmpeg fzf git jq libffi libxml2 libxslt nano ncurses nodejs openssh openssl openssl-tool proot python rust termux-api unzip wget zip tor"

# Install Termux packages. '|| true' ensures the script continues on package failure.
pkg install -y $CORE_PACKAGES || true

echo "Termux package installation complete. Continuing to Python setup..."

# --- 2. Python Package Setup ---
echo "2. Upgrading pip, setuptools, and wheel..."

# Upgrade pip and required build dependencies.
pip install --upgrade pip setuptools wheel --break-system-packages

# --- 3. Python Package Installation ---
echo "3. Installing the target Python dependencies..."

# Python packages list from Settings.py (including psutil and pillow)
PYTHON_PACKAGES="blessed bs4 cryptography flask flask-socketio geopy mutagen phonenumbers pycountry pydub pycryptodome requests werkzeug psutil pillow"

# Install all packages.
pip install $PYTHON_PACKAGES --break-system-packages

if [ $? -eq 0 ]; then
    echo "SUCCESS: All Python dependencies installed successfully! 🎉"
else
    echo "WARNING: Python package installation had errors (see log above). Attempting to proceed."
fi

# --- 4. Execution Logic ---
# Path is relative to the current directory (which is assumed to be 'DedSec').
SCRIPT_PATH="./Scripts/Settings.py"

echo "4. Attempting to run $SCRIPT_PATH..."

# First attempt to run the script
if [ -f "$SCRIPT_PATH" ]; then
    python "$SCRIPT_PATH"
    EXEC_STATUS=$?
else
    echo "ERROR: Script file not found at $SCRIPT_PATH. Cannot execute."
    EXEC_STATUS=1 # Set status to error if file is missing
fi

# Check if the execution failed (status non-zero)
if [ $EXEC_STATUS -ne 0 ]; then
    echo "Execution failed or script was not found (Exit Code: $EXEC_STATUS). Installing 'requests' package."
    
    # Run the fallback command
    pip install requests --break-system-packages
    
    # Second attempt to run the script
    echo "Retrying script execution..."
    
    if [ -f "$SCRIPT_PATH" ]; then
        python "$SCRIPT_PATH"
        if [ $? -eq 0 ]; then
            echo "SUCCESS: Script ran successfully after installing 'requests'."
        else
            echo "FINAL ERROR: Script failed again after installing 'requests'."
        fi
    else
        echo "FINAL ERROR: Script file not found after installation attempt."
    fi
else
    echo "SUCCESS: Script ran successfully on the first attempt."
fi