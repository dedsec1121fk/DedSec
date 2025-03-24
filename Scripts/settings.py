#!/usr/bin/env python3

import os
import sys
import json
import shutil
import subprocess
import requests
import curses
import re
import textwrap
import math
import time

# Global flag to ensure the song plays only once.
song_played = False
CONFIG_FILE = "config.json"

# ------------------------------
# Config File Functions
# ------------------------------

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    else:
        return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print("Error saving config:", e)

# ------------------------------
# Existing Settings Functionality
# ------------------------------

REPO_URL = "https://github.com/dedsec1121fk/DedSec.git"
LOCAL_DIR = "DedSec"
REPO_API_URL = "https://api.github.com/repos/dedsec1121fk/DedSec"

def run_command(command, cwd=None):
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip()

def get_termux_info():
    if shutil.which("termux-info"):
        out, err = run_command("termux-info -j")
        try:
            info = json.loads(out)
            termux_version = info.get("termux_version", info.get("app_version", "Unknown"))
            termux_api_version = info.get("termux_api_version", "Unknown")
        except Exception:
            termux_version = "Unknown"
            termux_api_version = "Unknown"
    else:
        termux_version = "Unknown"
        termux_api_version = "Unknown"
    termux_style_version = "Default"
    return termux_version, termux_api_version, termux_style_version

def get_latest_dedsec_update(path):
    if path and os.path.isdir(path):
        stdout, _ = run_command("git log -1 --format=%cd", cwd=path)
        return stdout if stdout else "Not Available"
    return "DedSec directory not found"

def find_dedsec():
    search_cmd = "find ~ -type d -name 'DedSec' 2>/dev/null"
    output, _ = run_command(search_cmd)
    paths = output.split("\n") if output else []
    return paths[0] if paths else None

def get_github_repo_size():
    try:
        response = requests.get(REPO_API_URL)
        if response.status_code == 200:
            size_kb = response.json().get('size', 0)
            return f"{size_kb / 1024:.2f} MB"
    except Exception:
        pass
    return "Unable to fetch repository size"

def get_termux_size():
    termux_root = "/data/data/com.termux"
    if os.path.exists(termux_root):
        out, err = run_command(f"du -sh {termux_root}")
        size = out.split()[0] if out else "Unknown"
        return size
    else:
        home_dir = os.environ.get("HOME", "~")
        out, err = run_command(f"du -sh {home_dir}")
        size = out.split()[0] if out else "Unknown"
        return size

def get_dedsec_size(path):
    if path and os.path.isdir(path):
        out, err = run_command(f"du -sh {path}")
        size = out.split()[0] if out else "Unknown"
        return size
    return "DedSec directory not found"

def clone_repo():
    print("[+] DedSec not found. Cloning repository...")
    run_command(f"git clone {REPO_URL}")
    return os.path.join(os.getcwd(), LOCAL_DIR)

def force_update_repo(existing_path):
    if existing_path:
        print("[+] DedSec found! Forcing a full update...")
        run_command("git fetch --all", cwd=existing_path)
        run_command("git reset --hard origin/main", cwd=existing_path)
        run_command("git clean -fd", cwd=existing_path)
        run_command("git pull", cwd=existing_path)
        print("[+] Repository fully updated, including README and all other files.")

def update_dedsec():
    repo_size = get_github_repo_size()
    print(f"[+] GitHub repository size: {repo_size}")
    existing_dedsec_path = find_dedsec()
    if existing_dedsec_path:
        run_command("git fetch", cwd=existing_dedsec_path)
        behind_count, _ = run_command("git rev-list HEAD..origin/main --count", cwd=existing_dedsec_path)
        try:
            behind_count = int(behind_count)
        except Exception:
            behind_count = 0
        if behind_count > 0:
            force_update_repo(existing_dedsec_path)
            dedsec_size = get_dedsec_size(existing_dedsec_path)
            print(f"[+] Update applied. DedSec Project Size: {dedsec_size}")
        else:
            print("No available update found.")
    else:
        existing_dedsec_path = clone_repo()
        dedsec_size = get_dedsec_size(existing_dedsec_path)
        print(f"[+] Cloned new DedSec repository. DedSec Project Size: {dedsec_size}")
    print("[+] Update process completed successfully!")
    return existing_dedsec_path

def get_internal_storage():
    df_out, _ = run_command("df -h /data")
    lines = df_out.splitlines()
    if len(lines) >= 2:
        fields = lines[1].split()
        return fields[1]
    return "Unknown"

def get_processor_info():
    cpuinfo, _ = run_command("cat /proc/cpuinfo")
    for line in cpuinfo.splitlines():
        if "Hardware" in line:
            return line.split(":", 1)[1].strip()
        if "Processor" in line:
            return line.split(":", 1)[1].strip()
    return "Unknown"

def get_ram_info():
    try:
        meminfo, _ = run_command("cat /proc/meminfo")
        for line in meminfo.splitlines():
            if "MemTotal" in line:
                parts = line.split()
                if len(parts) >= 2:
                    mem_total_kb = parts[1]
                    try:
                        mem_mb = int(mem_total_kb) / 1024
                        return f"{mem_mb:.2f} MB"
                    except Exception:
                        return parts[1] + " kB"
        return "Unknown"
    except Exception:
        return "Unknown"

def get_carrier():
    carrier, _ = run_command("getprop gsm.operator.alpha")
    if not carrier:
        carrier, _ = run_command("getprop ro.cdma.home.operator.alpha")
    return carrier if carrier else "Unknown"

def get_battery_info():
    if shutil.which("termux-battery-status"):
        out, _ = run_command("termux-battery-status")
        try:
            info = json.loads(out)
            level = info.get("percentage", "Unknown")
            status = info.get("status", "Unknown")
            return f"Battery: {level}% ({status})"
        except Exception:
            return "Battery: Unknown"
    else:
        return "Battery: Not available"

def get_hardware_details():
    internal_storage = get_internal_storage()
    processor = get_processor_info()
    ram = get_ram_info()
    carrier = get_carrier()
    kernel_version, _ = run_command("uname -r")
    android_version, _ = run_command("getprop ro.build.version.release")
    device_model, _ = run_command("getprop ro.product.model")
    manufacturer, _ = run_command("getprop ro.product.manufacturer")
    uptime, _ = run_command("uptime -p")
    battery = get_battery_info()
    details = (
        f"Internal Storage: {internal_storage}\n"
        f"Processor: {processor}\n"
        f"Ram: {ram}\n"
        f"Carrier: {carrier}\n"
        f"Kernel Version: {kernel_version}\n"
        f"Android Version: {android_version}\n"
        f"Device Model: {device_model}\n"
        f"Manufacturer: {manufacturer}\n"
        f"Uptime: {uptime}\n"
        f"{battery}"
    )
    return details

def get_user():
    output, _ = run_command("whoami")
    return output if output else "Unknown"

def show_about():
    print("=== System Information ===")
    dedsec_path = find_dedsec()
    latest_update = get_latest_dedsec_update(dedsec_path) if dedsec_path else "DedSec directory not found"
    print(f"The Latest DedSec Project Update: {latest_update}")
    termux_storage = get_termux_size()
    print(f"Termux Entire Storage: {termux_storage}")
    dedsec_size = get_dedsec_size(dedsec_path) if dedsec_path else "DedSec directory not found"
    print(f"DedSec Project Size: {dedsec_size}")
    print("\nHardware Details:")
    print(get_hardware_details())
    user = get_user()
    print(f"\nUser: {user}")

def show_credits():
    credits = """
=======================================
CREDITS
=======================================
Creator:dedsec1121fk
Music Artists:BFR TEAM,PLANNO MAN,MOUTRO,VG,KouNouPi,ADDICTED,JAVASPA.ZY.A2.N,ICE,Lefka City
Main Menu Theme Artist:HXLX
Artist:Christina Chatzidimitriou
Voice Overs:Dimitra Isxuropoulou
Technical Help:lamprouil
=======================================
"""
    print(credits)

# ------------------------------
# Remove MOTD (if exists)
# ------------------------------

def remove_motd():
    etc_path = "/data/data/com.termux/files/usr/etc"
    motd_path = os.path.join(etc_path, "motd")
    if os.path.exists(motd_path):
        os.remove(motd_path)

# ------------------------------
# Change Prompt
# ------------------------------

def modify_bashrc():
    etc_path = "/data/data/com.termux/files/usr/etc"
    os.chdir(etc_path)
    username = input("Prompt Username: ").strip()
    while not username:
        print("Username cannot be empty. Please enter a valid username.")
        username = input("Prompt Username: ").strip()
    with open("bash.bashrc", "r") as bashrc_file:
        lines = bashrc_file.readlines()
    new_ps1 = (
        f"PS1='ðŸŒ� \\[\\e[1;36m\\]\\d \\[\\e[0m\\]â�° "
        f"\\[\\e[1;32m\\]\\t \\[\\e[0m\\]ðŸ’» "
        f"\\[\\e[1;34m\\]{username} \\[\\e[0m\\]ðŸ“‚ "
        f"\\[\\e[1;33m\\]\\W \\[\\e[0m\\] : '\n"
    )
    with open("bash.bashrc", "w") as bashrc_file:
        for line in lines:
            if "PS1=" in line:
                bashrc_file.write(new_ps1)
            else:
                bashrc_file.write(line)

def change_prompt():
    print("\n[+] Changing Prompt...\n")
    remove_motd()
    modify_bashrc()
    print("\n[+] Customizations applied successfully!")

# ------------------------------
# New Option: Change Menu Style (using arrow keys)
# ------------------------------

def choose_menu_style_curses(stdscr):
    curses.curs_set(0)
    options = ["List Style", "Grid Style"]
    current = 0
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        title = "Choose Menu Style"
        stdscr.addstr(1, width // 2 - len(title) // 2, title)
        for idx, option in enumerate(options):
            x = width // 2 - len(option) // 2
            y = height // 2 - len(options) // 2 + idx
            if idx == current:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(y, x, option)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, option)
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP and current > 0:
            current -= 1
        elif key == curses.KEY_DOWN and current < len(options) - 1:
            current += 1
        elif key in [10, 13]:
            return "list" if current == 0 else "grid"
        elif key in [ord('q'), ord('Q')]:
            return None

def change_menu_style():
    style = curses.wrapper(choose_menu_style_curses)
    if style is None:
        print("No menu style selected. Returning to settings menu...")
        input("\nPress Enter to return to the settings menu...")
        return update_bashrc_for_menu_style(style)
    # Delete the external menu files since they're now integrated
    for file_name in ["menu.py", "grid_menu.py"]:
        try:
            if os.path.exists(file_name):
                os.remove(file_name)
        except Exception:
            pass
    print(f"\n[+] Menu style changed to {style.capitalize()} Style. Bash configuration updated.")
    input("\nPress Enter to return to the settings menu...")

def update_bashrc_for_menu_style(style):
    bashrc_path = "/data/data/com.termux/files/usr/etc/bash.bashrc"
    scripts_path = "/data/data/com.termux/files/home/DedSec/Scripts"
    if style == "list":
        new_startup = f"cd {scripts_path} && python3 settings.py --menu list"
        new_alias = f"alias m='cd ~/DedSec/Scripts && python3 settings.py --menu list'"
    else:
        new_startup = f"cd {scripts_path} && python3 settings.py --menu grid"
        new_alias = f"alias m='cd ~/DedSec/Scripts && python3 settings.py --menu grid'"
    try:
        with open(bashrc_path, "r") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {bashrc_path}: {e}")
        return
    filtered_lines = []
    # Remove any previous lines that launch settings.py with --menu
    for line in lines:
        if re.search(r"python3\s+settings\.py\s+--menu", line) or re.search(r"alias\s+m=.*python3\s+settings\.py\s+--menu", line):
            continue
        filtered_lines.append(line)
    filtered_lines.append("\n" + new_startup + "\n")
    filtered_lines.append(new_alias + "\n")
    try:
        with open(bashrc_path, "w") as f:
            f.writelines(filtered_lines)
    except Exception as e:
        print(f"Error writing to {bashrc_path}: {e}")

# ------------------------------
# New Option: Change Main Menu Music
# ------------------------------

def change_main_menu_music():
    global song_played
    def choose_music_option(stdscr):
        curses.curs_set(0)
        options = ["On", "Off"]
        current = 0
        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()
            title = "Main Menu Music: Choose an option"
            stdscr.addstr(1, width // 2 - len(title) // 2, title)
            for idx, option in enumerate(options):
                x = width // 2 - len(option) // 2
                y = height // 2 - len(options) // 2 + idx
                if idx == current:
                    stdscr.attron(curses.A_REVERSE)
                    stdscr.addstr(y, x, option)
                    stdscr.attroff(curses.A_REVERSE)
                else:
                    stdscr.addstr(y, x, option)
            stdscr.refresh()
            key = stdscr.getch()
            if key == curses.KEY_UP and current > 0:
                current -= 1
            elif key == curses.KEY_DOWN and current < len(options) - 1:
                current += 1
            elif key in [10, 13]:
                return options[current].lower()  # returns "on" or "off"
            elif key in [ord('q'), ord('Q')]:
                return None
    current_setting = load_config().get("main_menu_music", "on")
    new_setting = curses.wrapper(choose_music_option)
    if new_setting is None:
        print("No change made to Main Menu Music setting.")
    else:
        config = load_config()
        config["main_menu_music"] = new_setting
        save_config(config)
        if new_setting == "off":
            run_command("termux-media-player stop")
            song_played = False
            print("Main Menu Music turned Off. Music stopped.")
        elif new_setting == "on":
            if not song_played:
                dedsec_dir = os.path.join(os.path.expanduser("~"), "DedSec")
                music_file = os.path.join(dedsec_dir, "JOIN US WE ARE DEDSEC By HXLX.mp3")
                if not os.path.exists(music_file):
                    print(f"Error: File not found at {music_file}")
                else:
                    run_command("termux-media-player stop")
                    run_command("termux-volume music 15")
                    time.sleep(1)
                    run_command(f'termux-media-player play "{music_file}"')
                song_played = True
            print("Main Menu Music turned On. Music will play on startup.")
    input("\nPress Enter to return to the settings menu...")

# ------------------------------
# Integrated List Menu (from menu.py)
# ------------------------------

def run_list_menu():
    bashrc_path = "/data/data/com.termux/files/usr/etc/bash.bashrc"
    scripts_path = "/data/data/com.termux/files/home/DedSec/Scripts"

    def ensure_bashrc_setup():
        if os.path.exists(bashrc_path):
            with open(bashrc_path, "r") as file:
                content = file.read()
            startup_line = f"cd {scripts_path} && python3 settings.py --menu list"
            alias_line = "alias m='cd ~/DedSec/Scripts && python3 settings.py --menu list'"
            if startup_line not in content:
                with open(bashrc_path, "a") as file:
                    file.write("\n" + startup_line + "\n")
            if alias_line not in content:
                with open(bashrc_path, "a") as file:
                    file.write("\n" + alias_line + "\n")
        else:
            print(f"Error: {bashrc_path} not found.")
            sys.exit(1)

    def format_script_name(script_name):
        name = script_name.replace(".py", "").replace("_", " ").title()
        return re.sub(r'dedsec', 'DedSec', name, flags=re.IGNORECASE)

    def select_option(options, header):
        input_text = "\n".join(options)
        try:
            result = subprocess.run(f"fzf --header='{header}'", input=input_text, shell=True, capture_output=True, text=True)
        except Exception as e:
            print("Error running fzf:", e)
            return None
        return result.stdout.strip()

    ensure_bashrc_setup()

    try:
        scripts = [f for f in os.listdir(scripts_path) if f.endswith(".py")]
        if not scripts:
            print("No scripts found in the Scripts folder.")
            return
    except FileNotFoundError:
        print(f"Error: {scripts_path} not found.")
        sys.exit(1)
    scripts.sort(key=lambda s: format_script_name(s).lower())
    friendly_scripts = [format_script_name(script) for script in scripts]
    selected_script_name = select_option(friendly_scripts, "Select a script to execute (Use arrow keys to choose):")
    if not selected_script_name:
        print("No selection made. Exiting.")
        return
    selected_script = next((s for s in scripts if format_script_name(s) == selected_script_name), None)
    if not selected_script:
        print("Selected script not found.")
        return
    try:
        ret = os.system(f"cd {scripts_path} && python3 {selected_script}")
        if (ret >> 8) == 2:
            print("\nScript terminated by KeyboardInterrupt. Exiting gracefully...")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received. Exiting gracefully...")
        sys.exit(0)

# ------------------------------
# Integrated Grid Menu (from grid_menu.py)
# ------------------------------

def run_grid_menu():
    bashrc_path = "/data/data/com.termux/files/usr/etc/bash.bashrc"
    scripts_path = "/data/data/com.termux/files/home/DedSec/Scripts"

    def ensure_bashrc_setup():
        if os.path.exists(bashrc_path):
            with open(bashrc_path, "r") as file:
                content = file.read()
            startup_line = f"cd {scripts_path} && python3 settings.py --menu grid"
            alias_line = "alias m='cd ~/DedSec/Scripts && python3 settings.py --menu grid'"
            if startup_line not in content:
                with open(bashrc_path, "a") as file:
                    file.write("\n" + startup_line + "\n")
            if alias_line not in content:
                with open(bashrc_path, "a") as file:
                    file.write("\n" + alias_line + "\n")
        else:
            print(f"Error: {bashrc_path} not found.")
            sys.exit(1)

    def format_script_name(script_name):
        name = script_name.replace(".py", "").replace("_", " ").title()
        return re.sub(r'dedsec', 'DedSec', name, flags=re.IGNORECASE)

    def draw_box(stdscr, y, x, height, width, highlight=False):
        color = curses.color_pair(2)
        if highlight:
            color = curses.color_pair(1)
        for i in range(x, x + width):
            stdscr.addch(y, i, curses.ACS_HLINE, color)
            stdscr.addch(y + height - 1, i, curses.ACS_HLINE, color)
    
