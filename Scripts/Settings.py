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
Music Artists:BFR TEAM,PLANNO MAN,KouNouPi,ADDICTED,JAVASPA,ICE,Lefka City,HXLX,Giannis Vardis,Lavyrinthos,Komis X,GR$,Sakin,XALILOP1,Family Lockations,Christina Markesini,Dafne Kritharas,NANCIIE,Grave_North,YungKapa,Aroy,Pi Thita,Ecostones Band,Bossikan,B-Mat,Stamatis Kapiris
Art Artist:Christina Chatzidimitriou
Voice Overs:Dimitra Isxuropoulou
Technical Help:lamprouil,UKI_hunter
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
        return
    update_bashrc_for_menu_style(style)
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
        new_startup = f"cd {scripts_path} && python3 Settings.py --menu list"
        new_alias = f"alias m='cd ~/DedSec/Scripts && python3 Settings.py --menu list'"
    else:
        new_startup = f"cd {scripts_path} && python3 Settings.py --menu grid"
        new_alias = f"alias m='cd ~/DedSec/Scripts && python3 Settings.py --menu grid'"
    try:
        with open(bashrc_path, "r") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {bashrc_path}: {e}")
        return
    filtered_lines = []
    # Remove any previous lines that launch Settings.py with --menu
    for line in lines:
        if re.search(r"python3\s+Settings\.py\s+--menu", line, re.IGNORECASE) or re.search(r"alias\s+m=.*python3\s+Settings\.py\s+--menu", line, re.IGNORECASE):
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
# Helper for List Menu: Browse folders and scripts using fzf
# ------------------------------
def browse_directory_list_menu(current_path, base_path):
    """
    Lists subfolders and .py files in the given directory.
    Returns a full path for the selected item.
    Folders are marked with '[FOLDER] ' and an option '.. (Go Back)' is shown if not in the base.
    """
    items = []
    if os.path.abspath(current_path) != os.path.abspath(base_path):
        items.append(".. (Go Back)")
    for entry in sorted(os.listdir(current_path)):
        full_path = os.path.join(current_path, entry)
        if os.path.isdir(full_path):
            items.append(f"[FOLDER] {entry}")
        elif entry.endswith(".py"):
            items.append(entry)
    if not items:
        print("No items found in this folder.")
        return None
    input_text = "\n".join(items)
    try:
        result = subprocess.run("fzf", input=input_text, shell=True, capture_output=True, text=True)
        selected = result.stdout.strip()
    except Exception as e:
        print("Error running fzf:", e)
        return None
    if not selected:
        return None
    if selected.startswith(".."):
        return "back"
    if selected.startswith("[FOLDER] "):
        dirname = selected[len("[FOLDER] "):]
        return os.path.join(current_path, dirname)
    else:
        return os.path.join(current_path, selected)

# ------------------------------
# Integrated List Menu (from menu.py) with folder navigation
# ------------------------------
def run_list_menu():
    bashrc_path = "/data/data/com.termux/files/usr/etc/bash.bashrc"
    base_path = "/data/data/com.termux/files/home/DedSec/Scripts"
    def ensure_bashrc_setup():
        if os.path.exists(bashrc_path):
            with open(bashrc_path, "r") as file:
                content = file.read()
            startup_line = f"cd {base_path} && python3 Settings.py --menu list"
            alias_line = "alias m='cd ~/DedSec/Scripts && python3 Settings.py --menu list'"
            if startup_line not in content:
                with open(bashrc_path, "a") as file:
                    file.write("\n" + startup_line + "\n")
            if alias_line not in content:
                with open(bashrc_path, "a") as file:
                    file.write("\n" + alias_line + "\n")
        else:
            print(f"Error: {bashrc_path} not found.")
            sys.exit(1)
    ensure_bashrc_setup()
    
    current_path = base_path
    while True:
        selected = browse_directory_list_menu(current_path, base_path)
        if selected is None:
            print("No selection made. Exiting.")
            return
        if selected == "back":
            # Go back to parent if possible.
            parent = os.path.dirname(current_path)
            if os.path.abspath(parent).startswith(os.path.abspath(base_path)):
                current_path = parent
            else:
                current_path = base_path
            continue
        if os.path.isdir(selected):
            current_path = selected
            continue
        elif os.path.isfile(selected) and selected.endswith(".py"):
            # Execute the selected script using a relative path from the base folder.
            rel_path = os.path.relpath(selected, base_path)
            command = f"cd \"{base_path}\" && python3 \"{rel_path}\""
            ret = os.system(command)
            if (ret >> 8) == 2:
                print("\nScript terminated by KeyboardInterrupt. Exiting gracefully...")
                sys.exit(0)
            return
        else:
            print("Invalid selection. Exiting.")
            return

# ------------------------------
# Helper for Grid Menu: List directory entries
# ------------------------------
def list_directory_entries(path, base_path):
    """
    Returns a list of tuples (display_name, full_path) for directories and .py files in the given path.
    Directories are prefixed with "[FOLDER] " and a ".. (Go Back)" option is included if not at the base.
    """
    entries = []
    if os.path.abspath(path) != os.path.abspath(base_path):
        entries.append((".. (Go Back)", None))
    for entry in sorted(os.listdir(path)):
        full = os.path.join(path, entry)
        if os.path.isdir(full):
            entries.append((f"[FOLDER] {entry}", full))
        elif entry.endswith(".py"):
            entries.append((entry, full))
    return entries

# ------------------------------
# Integrated Grid Menu (from grid_menu.py) with folder navigation
# ------------------------------
def run_grid_menu():
    bashrc_path = "/data/data/com.termux/files/usr/etc/bash.bashrc"
    base_path = "/data/data/com.termux/files/home/DedSec/Scripts"
    def ensure_bashrc_setup():
        if os.path.exists(bashrc_path):
            with open(bashrc_path, "r") as file:
                content = file.read()
            startup_line = f"cd {base_path} && python3 Settings.py --menu grid"
            alias_line = "alias m='cd ~/DedSec/Scripts && python3 Settings.py --menu grid'"
            if startup_line not in content:
                with open(bashrc_path, "a") as file:
                    file.write("\n" + startup_line + "\n")
            if alias_line not in content:
                with open(bashrc_path, "a") as file:
                    file.write("\n" + alias_line + "\n")
        else:
            print(f"Error: {bashrc_path} not found.")
            sys.exit(1)
    def draw_box(stdscr, y, x, height, width, highlight=False):
        color = curses.color_pair(2)
        if highlight:
            color = curses.color_pair(1)
        for i in range(x, x + width):
            stdscr.addch(y, i, curses.ACS_HLINE, color)
            stdscr.addch(y + height - 1, i, curses.ACS_HLINE, color)
        for j in range(y, y + height):
            stdscr.addch(j, x, curses.ACS_VLINE, color)
            stdscr.addch(j, x + width - 1, curses.ACS_VLINE, color)
        stdscr.addch(y, x, curses.ACS_ULCORNER, color)
        stdscr.addch(y, x + width - 1, curses.ACS_URCORNER, color)
        stdscr.addch(y + height - 1, x, curses.ACS_LLCORNER, color)
        stdscr.addch(y + height - 1, x + width - 1, curses.ACS_LRCORNER, color)
    def draw_grid_menu(stdscr, friendly_names, num_items):
        curses.curs_set(0)
        stdscr.nodelay(0)
        stdscr.timeout(-1)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_MAGENTA, -1)
        curses.init_pair(3, curses.COLOR_WHITE, -1)
        current_index = 0
        while True:
            stdscr.clear()
            term_height, term_width = stdscr.getmaxyx()
            ICON_WIDTH = max(15, term_width // 5)
            ICON_HEIGHT = max(7, term_height // 6)
            max_cols = term_width // ICON_WIDTH
            total_visible_cells = max_cols * (term_height // ICON_HEIGHT)
            page_start_index = (current_index // total_visible_cells) * total_visible_cells
            page_end_index = min(page_start_index + total_visible_cells, num_items)
            for idx_on_page, actual_index in enumerate(range(page_start_index, page_end_index)):
                i = idx_on_page // max_cols
                j = idx_on_page % max_cols
                y = i * ICON_HEIGHT
                x = j * ICON_WIDTH
                draw_box(stdscr, y, x, ICON_HEIGHT, ICON_WIDTH, highlight=(actual_index == current_index))
                name = friendly_names[actual_index]
                box_text_width = ICON_WIDTH - 4
                wrapped_lines = textwrap.wrap(name, box_text_width)
                total_lines = len(wrapped_lines)
                padding_y = (ICON_HEIGHT - total_lines) // 2
                for line_idx, line in enumerate(wrapped_lines):
                    line_y = y + padding_y + line_idx
                    padding_x = (ICON_WIDTH - len(line)) // 2
                    line_x = x + padding_x
                    if line_y < term_height - 1 and line_x < term_width - len(line):
                        try:
                            stdscr.addstr(line_y, line_x, line, curses.color_pair(3))
                        except curses.error:
                            pass
            page_info = f" Page {(current_index // total_visible_cells) + 1} / {math.ceil(num_items / total_visible_cells)} "
            instructions = f"Arrow Keys: Move | Enter: Select | q: Quit | {page_info}"
            try:
                stdscr.addstr(term_height - 1, 0, instructions[:term_width - 1], curses.color_pair(3))
            except curses.error:
                pass
            stdscr.refresh()
            key = stdscr.getch()
            if key == curses.KEY_UP and current_index - max_cols >= 0:
                current_index -= max_cols
            elif key == curses.KEY_DOWN and current_index + max_cols < num_items:
                current_index += max_cols
            elif key == curses.KEY_LEFT and current_index % max_cols > 0:
                current_index -= 1
            elif key == curses.KEY_RIGHT and (current_index % max_cols) < (max_cols - 1) and (current_index + 1) < num_items:
                current_index += 1
            elif key in [10, 13]:
                return current_index
            elif key in [ord('q'), ord('Q')]:
                return None
            elif key == curses.KEY_RESIZE:
                pass
    ensure_bashrc_setup()
    
    current_path = base_path
    while True:
        entries = list_directory_entries(current_path, base_path)
        if not entries:
            print("No entries found in this folder.")
            return
        friendly_names = [entry[0] for entry in entries]
        selected_index = curses.wrapper(lambda stdscr: draw_grid_menu(stdscr, friendly_names, len(friendly_names)))
        if selected_index is None:
            print("No selection made. Exiting.")
            return
        selected_entry = entries[selected_index]
        if selected_entry[0].startswith(".."):
            if os.path.abspath(current_path) != os.path.abspath(base_path):
                current_path = os.path.dirname(current_path)
            else:
                current_path = base_path
            continue
        if selected_entry[0].startswith("[DIR]"):
            current_path = selected_entry[1]
            continue
        # Otherwise, it's a file.
        rel_path = os.path.relpath(selected_entry[1], base_path)
        command = f"cd \"{base_path}\" && python3 \"{rel_path}\""
        ret = os.system(command)
        if (ret >> 8) == 2:
            print("\nScript terminated by KeyboardInterrupt. Exiting gracefully...")
            sys.exit(0)
        return

# ------------------------------
# New Option: Update Packages & Modules
# ------------------------------
def update_packages_modules():
    pip_command = "pip install flask && pip install blessed && pip install flask-socketio && pip install werkzeug && pip install requests && pip install datetime && pip install geopy && pip install pydub && pip install pycryptodome && pip install mutagen && pip install cryptography && pip install phonenumbers && pip install pycountry"
    termux_command = "termux-setup-storage && pkg update -y && pkg upgrade -y && pkg install python git fzf nodejs openssh nano jq wget unzip curl proot openssl aapt rust cloudflared"
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
    menu_options = ["About", "DedSec Project Update", "Update Packages & Modules", "Change Prompt", "Change Menu Style", "Credits", "Exit"]
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
            change_menu_style()
        elif selected == 5:
            show_credits()
        elif selected == 6:
            print("Exiting...")
            break
        input("\nPress Enter to return to the settings menu...")

# ------------------------------
# Entry Point
# ------------------------------
if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--menu":
            if len(sys.argv) > 2:
                if sys.argv[2] == "list":
                    run_list_menu()
                elif sys.argv[2] == "grid":
                    run_grid_menu()
                else:
                    print("Unknown menu style. Use 'list' or 'grid'.")
            else:
                main()
        else:
            main()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received. Exiting gracefully...")
        sys.exit(0)

