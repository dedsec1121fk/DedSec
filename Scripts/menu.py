import os

# Define the absolute path for bash.bashrc and DedSec/Scripts
bashrc_path = "/data/data/com.termux/files/usr/etc/bash.bashrc"
startup_line = "cd /data/data/com.termux/files/home/DedSec/Scripts && python menu.py"

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

# Display the main menu
def display_main_menu():
    print("\nDedSec's Main Menu")
    print("1) Chats")
    print("2) Data Collection")
    print("3) Tools")
    print("4) Settings")
    print("0) Exit")

# Display sub-menus
def display_chats_menu():
    print("\n1) DedSec's Chat")
    print("2) Fox Chat")
    print("0) Go Back")

def display_data_collection_menu():
    print("\n1) Front Camera")
    print("2) Back Camera")
    print("3) Sound Recording")
    print("4) Location")
    print("5) Donation Phishing")
    print("0) Go Back")

def display_tools_menu():
    print("\n1) DedSec Database")
    print("2) Radio Mode")
    print("0) Go Back")

def display_settings_menu():
    print("\n1) Customization")
    print("2) T-Login")
    print("0) Go Back")

# Execute sub-menu options
def execute_script(script_name):
    os.system(f"cd /data/data/com.termux/files/home/DedSec/Scripts && python {script_name}")

# Handle sub-menus
def handle_chats_menu():
    while True:
        display_chats_menu()
        choice = input("Select an option: ")
        if choice == "1":
            execute_script("dedsecs_chat.py")
        elif choice == "2":
            execute_script("fox_chat.py")
        elif choice == "0":
            break
        else:
            print("Invalid option. Please try again.")

def handle_data_collection_menu():
    while True:
        display_data_collection_menu()
        choice = input("Select an option: ")
        scripts = {
            "1": "front_camera.py",
            "2": "back_camera.py",
            "3": "sound_recording.py",
            "4": "location.py",
            "5": "donation_phishing.py",
        }
        if choice in scripts:
            execute_script(scripts[choice])
        elif choice == "0":
            break
        else:
            print("Invalid option. Please try again.")

def handle_tools_menu():
    while True:
        display_tools_menu()
        choice = input("Select an option: ")
        if choice == "1":
            execute_script("dedsec_database.py")
        elif choice == "2":
            execute_script("radio_mode.py")
        elif choice == "0":
            break
        else:
            print("Invalid option. Please try again.")

def handle_settings_menu():
    while True:
        display_settings_menu()
        choice = input("Select an option: ")
        if choice == "1":
            execute_script("customization.py")
        elif choice == "2":
            execute_script("t-login.py")
        elif choice == "0":
            break
        else:
            print("Invalid option. Please try again.")

# Main function
def main():
    ensure_bashrc_setup()
    while True:
        display_main_menu()
        choice = input("Select an option: ")
        if choice == "1":
            handle_chats_menu()
        elif choice == "2":
            handle_data_collection_menu()
        elif choice == "3":
            handle_tools_menu()
        elif choice == "4":
            handle_settings_menu()
        elif choice == "0":
            print("Exiting...")
            exit(0)
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
