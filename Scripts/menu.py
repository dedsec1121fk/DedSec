#!/usr/bin/env python3
import os
import subprocess

# Define paths
bashrc_path = "/data/data/com.termux/files/usr/etc/bash.bashrc"
scripts_path = "/data/data/com.termux/files/home/DedSec/Scripts"
startup_line = f"cd {scripts_path} && python menu.py"

def ensure_bashrc_setup():
    if os.path.exists(bashrc_path):
        with open(bashrc_path, "r") as file:
            content = file.read()
        if startup_line not in content:
            with open(bashrc_path, "a") as file:
                file.write(f"\n{startup_line}\n")
    else:
        print(f"Error: {bashrc_path} not found.")
        exit(1)

def format_script_name(script_name):
    """Converts a script filename to a friendly name."""
    return script_name.replace(".py", "").replace("_", " ").title()

def select_option(options, header):
    """
    Uses fzf to let the user select one option from a newline-separated list.
    The user can use arrow keys for navigation.
    """
    input_text = "\n".join(options)
    try:
        result = subprocess.run(f"fzf --header='{header}'", input=input_text,
                                  shell=True, capture_output=True, text=True)
    except Exception as e:
        print("Error running fzf:", e)
        return None
    return result.stdout.strip()

def main():
    ensure_bashrc_setup()

    try:
        # List all .py files in the Scripts folder, excluding this menu script
        scripts = [f for f in os.listdir(scripts_path) if f.endswith(".py") and f != "menu.py"]
        if not scripts:
            print("No scripts found in the Scripts folder.")
            return
    except FileNotFoundError:
        print(f"Error: {scripts_path} not found.")
        exit(1)

    # Sort the scripts alphabetically based on their friendly names
    scripts.sort(key=lambda s: format_script_name(s).lower())
    friendly_scripts = [format_script_name(script) for script in scripts]

    # Use fzf to let the user choose a script using arrow keys
    selected_script_name = select_option(friendly_scripts, "Select a script to execute (Use arrow keys to choose):")
    if not selected_script_name:
        print("No selection made. Exiting.")
        return

    # Map the friendly name back to the actual script filename
    selected_script = next((s for s in scripts if format_script_name(s) == selected_script_name), None)
    if not selected_script:
        print("Selected script not found.")
        return

    os.system(f"cd {scripts_path} && python {selected_script}")

if __name__ == "__main__":
    main()
