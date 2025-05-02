#!/usr/bin/env python3
import os
import sys
import time
import shutil

# Paths and constants
HOME = os.path.expanduser("~")
BASH_PROFILE = os.path.join(HOME, ".bash_profile")
BASHRC_GLOBAL = "/data/data/com.termux/files/usr/etc/bash.bashrc"
LOADING_SCREEN_START = "# >>> Termux ASCII-ART LOADING SCREEN START"
LOADING_SCREEN_END = "# <<< Termux ASCII-ART LOADING SCREEN END"

ART1 = r"""
         |
    pN▒g▒p▒g▒▒g▒ge
   ▒▒▒▒▒▒▒▓▓▒▒▒▒▒
 _0▒▓▒▓▒▓▓▒▒▒▒▒▒▒!
 4▒▒▒▒▒▓▓▓▒▓▓▒▒▒▒▒Y
 |` ~~#00▓▓0▒MMM"M|
       `gM▓M7
|       00Q0       |
#▒____g▒0▓▓P______0
#▒0g_p#▓▓04▒▒&,__M#
0▒▒▒▒▒00   ]0▒▒▒▒00
 |\j▒▒0'   '0▒▒▒4M'
  |\#▒▒&▒▒gg▒▒0& |
 " ▒▒00▒▒▒▒00▒▒'d
 %  ¼▒  ~P▒¼▒▒|¼¼|
 M▒9▒,▒▒ ]▒] *▒j,g
 l▒g▒▒] @▒9
  ~▒0▒▒▒p ▒g▒
    @▓▒▒▒▒▒  ▒▒▓
     M0▓▓  ▓▓^
       `
"""

# Helpers
def get_terminal_width():
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80

def center_ascii(art):
    width = get_terminal_width()
    return "\n".join(" " * max(0, ((width - len(line)) // 2)) + line for line in art.strip("\n").splitlines())

def strip_loading_screen_block(lines):
    in_block = False
    new = []
    for line in lines:
        if line.strip() == LOADING_SCREEN_START:
            in_block = True
            continue
        if line.strip() == LOADING_SCREEN_END:
            in_block = False
            continue
        if not in_block:
            new.append(line)
    return new

def read_lines(path):
    return open(path).readlines() if os.path.exists(path) else []

def write_lines(path, lines):
    with open(path, "w") as f:
        f.writelines(lines)

# Bashrc patch logic
def patch_bashrc():
    if not os.path.exists(BASHRC_GLOBAL):
        return
    lines = read_lines(BASHRC_GLOBAL)
    for i, line in enumerate(lines):
        if "Settings.py" in line and "sleep" not in line:
            lines[i] = f"(sleep 12; {line.strip()}) &\n"
            write_lines(BASHRC_GLOBAL, lines)
            break

def revert_bashrc():
    if not os.path.exists(BASHRC_GLOBAL):
        return
    lines = read_lines(BASHRC_GLOBAL)
    for i, line in enumerate(lines):
        if "sleep 12;" in line and "Settings.py" in line:
            cmd = line.strip().removeprefix("(sleep 12;").removesuffix(") &")
            lines[i] = cmd.strip() + "\n"
            write_lines(BASHRC_GLOBAL, lines)
            break

# Install/remove logic
def install_loading_screen(seconds):
    lines = read_lines(BASH_PROFILE)
    lines = strip_loading_screen_block(lines)

    loading_screen_script = [
        f"{LOADING_SCREEN_START}\n",
        "clear\n",
        "cat << 'EOF'\n",
        center_ascii(ART1) + "\nEOF\n",
        f"sleep {seconds}\nclear\n",
        "python3 -c \"import os; os.system('sed -i \\\"/sleep 12;.*Settings.py/d\\\" \\\"/data/data/com.termux/files/usr/etc/bash.bashrc\\\"')\"\n",
        f"{LOADING_SCREEN_END}\n"
    ]

    write_lines(BASH_PROFILE, loading_screen_script + lines)
    patch_bashrc()
    print(f"✅ Loading Screen installed with delay of {seconds} seconds.")

def install_custom_loading_screen(seconds):
    print("Paste your custom ASCII art below. Press Enter when done.")
    
    # Collect user input for the ASCII art
    custom_art = ""
    while True:
        line = input()
        if line.strip() == "":
            break  # End input when the user presses Enter on an empty line
        custom_art += line + "\n"

    lines = read_lines(BASH_PROFILE)
    lines = strip_loading_screen_block(lines)

    loading_screen_script = [
        f"{LOADING_SCREEN_START}\n",
        "clear\n",
        "cat << 'EOF'\n",
        center_ascii(custom_art) + "\nEOF\n",
        f"sleep {seconds}\nclear\n",
        "python3 -c \"import os; os.system('sed -i \\\"/sleep 12;.*Settings.py/d\\\" \\\"/data/data/com.termux/files/usr/etc/bash.bashrc\\\"')\"\n",
        f"{LOADING_SCREEN_END}\n"
    ]

    write_lines(BASH_PROFILE, loading_screen_script + lines)
    patch_bashrc()
    print(f"✅ Custom Loading Screen installed with delay of {seconds} seconds.")

def remove_loading_screen():
    if os.path.exists(BASH_PROFILE):
        lines = read_lines(BASH_PROFILE)
        lines = strip_loading_screen_block(lines)
        write_lines(BASH_PROFILE, lines)
        print("🗑️  Loading Screen removed.")
    revert_bashrc()

def update_delay(seconds):
    lines = read_lines(BASH_PROFILE)
    new_lines = []
    in_loading_screen = False

    for line in lines:
        if LOADING_SCREEN_START in line:
            in_loading_screen = True
        if LOADING_SCREEN_END in line:
            in_loading_screen = False

        if in_loading_screen and "sleep" in line:
            line = f"sleep {seconds}\n"
        new_lines.append(line)

    write_lines(BASH_PROFILE, new_lines)
    print(f"✅ Loading Screen delay updated to {seconds} seconds.")

# Menu
def main():
    print("Custom Loading Screen")
    print("1) Install Loading Screen")
    print("2) Remove Loading Screen")
    print("3) Exit")
    print("4) Install Loading Screen With Custom ASCII Art")
    print("5) Update Loading Screen Delay")
    choice = input("Select: ").strip()

    if choice == "1":
        install_loading_screen(10)  # Default 10 seconds delay
    elif choice == "2":
        remove_loading_screen()
    elif choice == "4":
        install_custom_loading_screen(10)  # Default 10 seconds delay
    elif choice == "5":
        seconds = int(input("Enter the number of seconds for the Loading Screen delay: ").strip())
        update_delay(seconds)  # Update delay without reinstalling Loading Screen or custom art
    else:
        print("Bye.")

if __name__ == "__main__":
    main()

