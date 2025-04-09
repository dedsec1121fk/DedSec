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
Creator: dedsec1121fk
Music Artists: BFR TEAM, PLANNO MAN, MOUTRO, VG, KouNouPi, ADDICTED, JAVASPA.ZY.A2.N, ICE, Lefka City, HXLX, Giannis Vardis,Astero Christofidou
Art Artist: Christina Chatzidimitriou
Voice Overs: Dimitra Isxuropoulou, Pantelis Myrsiniotis
Technical Help: lamprouil
=======================================
"""
    print(credits)

# ------------------------------
# Remove MOTD (if exists)
# ------------------------------
def remove_motd():
    etc_path = "/data/data/com.termux/files/usr/etc"
    # List of files related to welcome messages that should be removed
    files_to_remove = ["motd", "termux-banner"]
    for filename in files_to_remove:
        file_path = os.path.join(etc_path, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

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
# Change Menu Style
# ------------------------------
def choose_menu_style_curses(stdscr):
    curses.curs_set(0)
    options = ["List Style", "Grid Style"]
    current = 0
    while True:
        stdscr.erase()
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

def change_menu_style():
    style = curses.wrapper(choose_menu_style_curses)
    if style is None:
        print("No menu style selected. Returning to settings menu...")
        input("\nPress Enter to return to the settings menu...")
        return
    update_bashrc_for_menu_style(style)
    for file_name in ["menu.py", "grid_menu.py"]:
        try:
            if os.path.exists(file_name):
                os.remove(file_name)
        except Exception:
            pass
    print(f"\n[+] Menu style changed to {style.capitalize()} Style. Bash configuration updated.")
    input("\nPress Enter to return to the settings menu...")

# ------------------------------
# New Combined Menu for Scripts and Folders
# ------------------------------
# Define category filters with new names.
CATEGORIES = {
    "Anonymous Chats": lambda name: "chat" in name.lower(),
    "Camera Phishing": lambda name: "camera" in name.lower(),
    "Microphone Phishing": lambda name: "microphone" in name.lower(),
    "Location Phishing": lambda name: "location" in name.lower(),
}

def format_script_name(script_name):
    # Format the name for display.
    name = script_name.replace(".py", "").replace("_", " ").title()
    return re.sub(r'dedsec', 'DedSec', name, flags=re.IGNORECASE)

def get_all_scripts(scripts_path):
    try:
        return [f for f in os.listdir(scripts_path) if f.endswith(".py")]
    except FileNotFoundError:
        print(f"Error: {scripts_path} not found.")
        sys.exit(1)

def build_combined_menu(scripts):
    """
    Build a list of menu items.
    Each item is a tuple: (display_name, type, data)
    Type can be "folder" or "script".
    For folder items, data is the category name.
    For script items, data is the script filename.
    
    Scripts matching any category filter will not be shown individually;
    they appear only in the folder.
    Folders are added in the following order:
      Anonymous Chats, Camera Phishing, Microphone Phishing, Location Phishing.
    Then uncategorized scripts are appended.
    """
    menu_items = []
    category_scripts = {cat: [] for cat in CATEGORIES}
    uncategorized = []
    # Build lists.
    for script in scripts:
        matched = False
        for cat, filt in CATEGORIES.items():
            if filt(script):
                category_scripts[cat].append(script)
                matched = True
        if not matched:
            uncategorized.append(script)
    # Add folders in desired order.
    order = ["Anonymous Chats", "Camera Phishing", "Microphone Phishing", "Location Phishing"]
    for cat in order:
        if category_scripts.get(cat):
            menu_items.append((f"{cat} [Folder]", "folder", cat))
    # Then add uncategorized scripts.
    for script in sorted(uncategorized, key=lambda s: format_script_name(s).lower()):
        menu_items.append((format_script_name(script), "script", script))
    return menu_items, category_scripts

# --- List mode using fzf ---
def run_combined_list_menu():
    scripts_path = "/data/data/com.termux/files/home/DedSec/Scripts"
    all_scripts = get_all_scripts(scripts_path)
    menu_items, category_scripts = build_combined_menu(all_scripts)
    display_list = [item[0] for item in menu_items]
    try:
        result = subprocess.run("fzf --header='Select an item (arrow keys to choose):'",
                                  input="\n".join(display_list),
                                  shell=True, capture_output=True, text=True)
    except Exception as e:
        print("Error running fzf:", e)
        return
    selection = result.stdout.strip()
    if not selection:
        print("No selection made.")
        return
    for display, typ, data in menu_items:
        if display == selection:
            if typ == "script":
                os.system(f"cd {scripts_path} && python3 {data}")
                return
            elif typ == "folder":
                sub_scripts = category_scripts.get(data, [])
                if not sub_scripts:
                    print(f"No scripts in folder {data}.")
                    return
                sub_display = [format_script_name(s) for s in sorted(sub_scripts, key=lambda s: format_script_name(s).lower())]
                try:
                    sub_result = subprocess.run(f"fzf --header='Select a script from {data} (press ESC to go back):'",
                                                input="\n".join(sub_display),
                                                shell=True, capture_output=True, text=True)
                except Exception as e:
                    print("Error running fzf:", e)
                    return
                sub_selection = sub_result.stdout.strip()
                if not sub_selection:
                    run_combined_list_menu()
                    return
                for s in sub_scripts:
                    if format_script_name(s) == sub_selection:
                        os.system(f"cd {scripts_path} && python3 {s}")
                        return
            break

# --- Grid mode using curses ---
def run_combined_grid_menu():
    scripts_path = "/data/data/com.termux/files/home/DedSec/Scripts"
    while True:
        all_scripts = get_all_scripts(scripts_path)
        menu_items, category_scripts = build_combined_menu(all_scripts)
        display_names = [item[0] for item in menu_items]
        selected_index = curses.wrapper(draw_grid_menu, display_names, len(display_names))
        if selected_index is None:
            return
        selected_item = menu_items[selected_index]
        if selected_item[1] == "script":
            os.system(f"cd {scripts_path} && python3 {selected_item[2]}")
            return
        elif selected_item[1] == "folder":
            while True:
                sub_scripts = category_scripts.get(selected_item[2], [])
                if not sub_scripts:
                    print(f"No scripts in folder {selected_item[2]}.")
                    break
                sub_display = [format_script_name(s) for s in sorted(sub_scripts, key=lambda s: format_script_name(s).lower())]
                sub_index = curses.wrapper(draw_grid_menu, sub_display, len(sub_display))
                if sub_index is None:
                    break
                os.system(f"cd {scripts_path} && python3 {sub_scripts[sub_index]}")
                return

# --- Grid drawing function (using rounded boxes and erase for reduced flicker) ---
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
        stdscr.erase()
        term_height, term_width = stdscr.getmaxyx()
        ICON_WIDTH = max(15, term_width // 5)
        ICON_HEIGHT = max(7, term_height // 6)
        max_cols = term_width // ICON_WIDTH
        total_visible = max_cols * (term_height // ICON_HEIGHT)
        page_start = (current_index // total_visible) * total_visible
        page_end = min(page_start + total_visible, num_items)
        for idx, actual_index in enumerate(range(page_start, page_end)):
            i = idx // max_cols
            j = idx % max_cols
            y = i * ICON_HEIGHT
            x = j * ICON_WIDTH
            draw_box(stdscr, y, x, ICON_HEIGHT, ICON_WIDTH, highlight=(actual_index == current_index))
            name = friendly_names[actual_index]
            box_width = ICON_WIDTH - 4
            wrapped = textwrap.wrap(name, box_width)
            pad_y = (ICON_HEIGHT - len(wrapped)) // 2
            for li, line in enumerate(wrapped):
                line_x = x + (ICON_WIDTH - len(line)) // 2
                line_y = y + pad_y + li
                if line_y < term_height:
                    try:
                        stdscr.addstr(line_y, line_x, line, curses.color_pair(3))
                    except curses.error:
                        pass
        page_info = f" Page {(current_index // total_visible) + 1} / {math.ceil(num_items / total_visible)} "
        instructions = f"Arrow keys: Move | Enter: Select | e: Back | {page_info}"
        try:
            stdscr.addstr(term_height-1, 0, instructions[:term_width-1], curses.color_pair(3))
        except curses.error:
            pass
        stdscr.refresh()
        curses.doupdate()
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
        elif key in [ord('e'), ord('E'), ord('q'), ord('Q')]:
            return None
        elif key == curses.KEY_RESIZE:
            pass

def draw_box(stdscr, y, x, height, width, highlight=False):
    color = curses.color_pair(2)
    if highlight:
        color = curses.color_pair(1)
    horizontal = "─"
    vertical = "│"
    tl = "╭"
    tr = "╮"
    bl = "╰"
    br = "╯"
    for i in range(x+1, x+width-1):
        stdscr.addstr(y, i, horizontal, color)
        stdscr.addstr(y+height-1, i, horizontal, color)
    for j in range(y+1, y+height-1):
        stdscr.addstr(j, x, vertical, color)
        stdscr.addstr(j, x+width-1, vertical, color)
    stdscr.addstr(y, x, tl, color)
    stdscr.addstr(y, x+width-1, tr, color)
    stdscr.addstr(y+height-1, x, bl, color)
    stdscr.addstr(y+height-1, x+width-1, br, color)

# ------------------------------
# Update Packages & Modules
# ------------------------------
def update_packages_modules():
    pip_command = ("pip install flask && pip install blessed && pip install flask-socketio && "
                   "pip install werkzeug && pip install requests && pip install datetime && "
                   "pip install geopy && pip install pydub && pip install pycryptodome && pip install mutagen")
    termux_command = ("termux-setup-storage && pkg update -y && pkg upgrade -y && "
                      "pkg install python git fzf nodejs openssh nano jq wget unzip curl proot openssl aapt")
    print("[+] Installing Python packages and modules...")
    run_command(pip_command)
    print("[+] Installing Termux packages and modules...")
    run_command(termux_command)
    print("[+] Packages and Modules update process completed successfully!")

# ------------------------------
# Main Settings Menu (curses)
# ------------------------------
def menu(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    options = ["About", "DedSec Project Update", "Update Packages & Modules", "Change Prompt", "Change Menu Style", "Credits", "Exit"]
    current = 0
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        title = "Select an option"
        stdscr.addstr(1, w//2 - len(title)//2, title)
        for idx, opt in enumerate(options):
            x = w//2 - len(opt)//2
            y = h//2 - len(options)//2 + idx
            if idx == current:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(y, x, opt)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, opt)
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP and current > 0:
            current -= 1
        elif key == curses.KEY_DOWN and current < len(options)-1:
            current += 1
        elif key in [10, 13]:
            return current

def main_menu():
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
            mode = "list"
            if len(sys.argv) > 2:
                if sys.argv[2] in ["list", "grid"]:
                    mode = sys.argv[2]
                else:
                    print("Unknown menu style. Use 'list' or 'grid'.")
                    sys.exit(1)
            if mode == "list":
                run_combined_list_menu()
            else:
                run_combined_grid_menu()
        else:
            main_menu()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received. Exiting gracefully...")
        sys.exit(0)

