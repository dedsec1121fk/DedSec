## Overview

This script customizes the Termux environment by modifying the **MOTD** (Message of the Day) and **bash.bashrc** files. The changes include adding ASCII art to the MOTD and customizing the bash prompt for a personalized look.

---

## Purpose

1. **MOTD Customization**: Displays a custom ASCII art message whenever a new Termux session is started.
2. **Bash Prompt Customization**: Updates the command prompt to show:
   - Current date 🌐
   - Time ⏰
   - Custom username 💻
   - Current working directory 📂

---

## Features

- **Custom ASCII Art**: The new MOTD replaces the default message with a sleek design.
- **Enhanced Bash Prompt**: Displays useful information with a modern look using emojis and colors.
- **Automatic Configuration**: The script automates file modifications to eliminate manual edits.

---

## Workflow

1. **Modify MOTD**:
   - Deletes the existing `motd` file.
   - Creates a new `motd` file with custom ASCII art.

2. **Update Bash Prompt**:
   - Edits the `bash.bashrc` file to replace the existing `PS1` variable with a new, enhanced prompt.

---

## Code Breakdown

### MOTD Customization
- **Path**: `/data/data/com.termux/files/usr/etc/motd`
- **Action**:
  - Deletes the default `motd` file.
  - Writes a new file containing the following ASCII art:
    ```
      ___         _ ___           _ _ ___ _ 
     |   \ ___ __| / __| ___ __  / / |_  ) |
     | |) / -_) _` \__ \/ -_) _| | | |/ /| |
     |___/\___\__,_|___/\___\__| |_|_/___|_|
    ```

### Bash Prompt Customization
- **Path**: `/data/data/com.termux/files/usr/etc/bash.bashrc`
- **Action**:
  - Locates the `PS1=` line and replaces it with:
    ```
    PS1='🌐 \[\e[1;36m\]\d \[\e[0m\]⏰ \[\e[1;32m\]\t \[\e[0m\]💻 \[\e[1;34m\]dedsec1121fk \[\e[0m\]📂 \[\e[1;33m\]\W \[\e[0m\] : '
    ```
  - The new prompt includes:
    - **Date** (`\d`): Displays the current date.
    - **Time** (`\t`): Shows the current time.
    - **Custom Username** (`dedsec1121fk`): Personalized identifier.
    - **Working Directory** (`\W`): Displays the current directory name.
    - Colors for clear visibility.

---

## Setup Instructions

### Prerequisites
- A Termux environment installed on your Android device.
- Python 3 installed in Termux.

### Steps
1. **Clone or Create the Script**:
   Save the Python script in Termux as `customize_termux.py`.

2. **Run the Script**:
   Execute the script using:
   ```bash
   python customize_termux.py
   ```

3. **Verify Customizations**:
   - Restart Termux to see the new MOTD.
   - Open a new session to verify the updated bash prompt.

---

## Troubleshooting

- **Permission Denied**:
  Ensure the script has permission to modify files:
  ```bash
  chmod +x customize_termux.py
  ```
- **Revert Changes**:
  Restore the original files by:
  - Replacing the `bash.bashrc` with a backup (if available).
  - Removing the custom `motd` file.

---