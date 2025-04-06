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
Music Artists:BFR TEAM,PLANNO MAN,MOUTRO,VG,KouNouPi,ADDICTED,JAVASPA.ZY.A2.N,ICE,Lefka City,HXLX,Giannis Vardis,Astero Christofidou
Art Artist:Christina Chatzidimitriou
Voice Overs:Dimitra Isxuropoulou,Pantelis Myrsiniotis
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
        f"PS1='🌐 \\[\\e[1;36m\\]\\d \\[\\e[0m\\]⏰ "
        f"\\[\\e[1;32m\\]\\t \\[\\e[0m\\]💻 "
        f"\\[\\e[1;34m\\]{username} \\[\\e[0m\\]📂 "
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
# Helper: Categorize Scripts
# ------------------------------
def categorize_scripts(scripts):
    """
    Returns a tuple of (general_scripts, categorized_dict) where:
      - general_scripts: list of scripts that do NOT match any category keyword.
      - categorized_dict: dictionary mapping category names to a list of scripts.
    """
    categories = {
        "Chats": lambda name: "chat" in name.lower(),
        "Location Phishing": lambda name: "location" in name.lower(),
        "Camera Phishing": lambda name: "camera" in name.lower(),
        "Microphone Phishing": lambda name: "microphone" in name.lower(),
    }
    general = []
    categorized = {cat: [] for cat in categories}
    for script in scripts:
        added = False
        for cat, test in categories.items():
            if test(script):
                categorized[cat].append(script)
                added = True
        if not added:
            general.append(script)
    return general, categorized

# ------------------------------
# Custom select_option using fzf with "e" binding for back
# ------------------------------
def select_option(options, header, allow_back=False):
    input_text = "\n".join(options)
    bind_str = " --bind=e:abort" if allow_back else ""
    try:
        result = subprocess.run(f"fzf --header='{header}'{bind_str}", input=input_text,
                                  shell=True, capture_output=True, text=True)
        # If non-zero exit code, assume "e" was pressed and user wants to go back
        if result.returncode != 0:
            return "back"
    except Exception as e:
        print("Error running fzf:", e)
        return None
    return result.stdout.strip()

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
    ensure_bashrc_setup()
    try:
        all_scripts = [f for f in os.listdir(scripts_path) if f.endswith(".py")]
        if not all_scripts:
            print("No scripts found in the Scripts folder.")
            return
    except FileNotFoundError:
        print(f"Error: {scripts_path} not found.")
        sys.exit(1)

    # Main loop for the list menu. If user goes back from a submenu, re-display main.
    while True:
        # Separate scripts into general and categorized groups.
        general_scripts, categorized_scripts = categorize_scripts(all_scripts)
        # Build main menu options: list general scripts first...
        main_options = [format_script_name(s) for s in general_scripts]
        # ... then add a separate folder for each category (if any scripts exist).
        category_order = ["Chats", "Location Phishing", "Camera Phishing", "Microphone Phishing"]
        for cat in category_order:
            if categorized_scripts.get(cat):
                main_options.append(f"{cat} [Folder]")
        selected_option = select_option(main_options, "Select a script or folder (e to go back):", allow_back=True)
        if selected_option == "back":
            # At main menu, "back" means exit the script.
            print("Exiting...")
            sys.exit(0)
        # Check if the selection is a folder.
        folder_match = None
        for cat in category_order:
            if categorized_scripts.get(cat) and selected_option.strip() == f"{cat} [Folder]":
                folder_match = cat
                break
        if folder_match:
            # Folder submenu loop.
            while True:
                cat_scripts = categorized_scripts[folder_match]
                cat_options = [format_script_name(s) for s in cat_scripts]
                selected_script_name = select_option(cat_options, f"Select a script from {folder_match} (e to go back):", allow_back=True)
                if selected_script_name == "back":
                    # Go back to main menu.
                    break
                selected_script = next((s for s in cat_scripts if format_script_name(s) == selected_script_name), None)
                if selected_script:
                    try:
                        ret = os.system(f"cd {scripts_path} && python3 {selected_script}")
                        if (ret >> 8) == 2:
                            print("\nScript terminated by KeyboardInterrupt. Exiting gracefully...")
                            sys.exit(0)
                    except KeyboardInterrupt:
                        print("\nKeyboardInterrupt received. Exiting gracefully...")
                        sys.exit(0)
                    return
        else:
            # User selected a general script.
            selected_script = next((s for s in general_scripts if format_script_name(s) == selected_option), None)
            if selected_script:
                try:
                    ret = os.system(f"cd {scripts_path} && python3 {selected_script}")
                    if (ret >> 8) == 2:
                        print("\nScript terminated by KeyboardInterrupt. Exiting gracefully...")
                        sys.exit(0)
                except KeyboardInterrupt:
                    print("\nKeyboardInterrupt received. Exiting gracefully...")
                    sys.exit(0)
                return

# ------------------------------
# New Option: Update Packages & Modules
# ------------------------------
def update_packages_modules():
    pip_command = "pip install flask && pip install blessed && pip install flask-socketio && pip install werkzeug && pip install requests && pip install datetime && pip install geopy && pip install pydub && pip install pycryptodome"
    termux_command = "termux-setup-storage && pkg update -y && pkg upgrade -y && pkg install python git fzf nodejs openssh nano jq wget unzip curl proot openssl aapt"
    print("[+] Installing Python packages and modules...")
    run_command(pip_command)
    print("[+] Installing Termux packages and modules...")
    run_command(termux_command)
    print("[+] Packages and Modules update process completed successfully!")

# ------------------------------
# Main Settings Menu
# ------------------------------
def menu(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    # Removed "Change Menu Style" option; only list style is used.
    menu_options = ["About", "DedSec Project Update", "Update Packages & Modules", "Change Prompt", "Credits", "Exit"]
    current_row = 0
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        title = "Select an option"
        stdscr.addstr(1, width // 2 - len(title) // 2, title)
        for idx, option in enumerate(menu_options):
            x = width // 2 - len(option) // 2
            y = height // 2 - len(menu_options) // 2 + idx
            if idx == current_row:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(y, x, option)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, option)
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu_options) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            return current_row

def main():
    while True:
        selected = curses.wrapper(menu)
        os.system("clear")
        if selected == 0:
            show_about()
        elif selected == 1:
            update_dedsec()
        elif selected == 2:
            update_packages_modules()
        elif selected == 3:
            change_prompt()
        elif selected == 4:
            show_credits()
        elif selected == 5:
            print("Exiting...")
            break
        input("\nPress Enter to return to the settings menu...")

# ------------------------------
# Entry Point
# ------------------------------
if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--menu":
            # Always use list style
            run_list_menu()
        else:
            main()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received. Exiting gracefully...")
        sys.exit(0)

