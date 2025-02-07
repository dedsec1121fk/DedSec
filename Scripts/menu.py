import os

# Define the absolute path for bash.bashrc and DedSec/Scripts
bashrc_path = "/data/data/com.termux/files/usr/etc/bash.bashrc"
scripts_path = "/data/data/com.termux/files/home/DedSec/Scripts"
startup_line = f"cd {scripts_path} && python menu.py"

# Ensure the line is added to bash.bashrc
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

# Format script names as titles
def format_script_name(script_name):
    base_name = script_name.replace(".py", "").replace("_", " ").title()
    
    # Check and modify "DedSec" as per requirement
    base_name = base_name.replace("Dedsec", "DedSec")
    
    words = base_name.split()
    if words and words[0].endswith("s"):
        words[0] += "'s"
    return " ".join(words)

# Display the menu based on the files in the Scripts folder
def display_scripts_menu():
    try:
        # List all .py files except menu.py
        scripts = [f for f in os.listdir(scripts_path) if f.endswith(".py") and f != "menu.py"]
        if not scripts:
            print("\nNo scripts found in the Scripts folder.")
            return []
        print("\nAvailable Scripts:")
        for i, script in enumerate(scripts, 1):
            print(f"{i}) {format_script_name(script)}")
        print("0) Exit")
        return scripts
    except FileNotFoundError:
        print(f"Error: {scripts_path} not found.")
        exit(1)

# Execute the selected script
def execute_script(script_name):
    os.system(f"cd {scripts_path} && python {script_name}")

# Main function
def main():
    ensure_bashrc_setup()
    while True:
        scripts = display_scripts_menu()
        if not scripts:
            break
        choice = input("Select a script to execute: ")
        if choice == "0":
            print("Exiting...")
            exit(0)
        elif choice.isdigit() and 1 <= int(choice) <= len(scripts):
            script_name = scripts[int(choice) - 1]
            execute_script(script_name)
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()

