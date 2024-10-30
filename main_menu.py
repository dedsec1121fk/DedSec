import os

def display_menu():
    # Define menu options with padding to center them
    options = [
        "DedSec's Chat", "DedSec Database", "Back Camera",
        "Front Camera", "Donation Phishing", "OSINTDS",
        "NAIOVUM", "Customization", "T-Login", "Exit"
    ]
    # Print each option with consistent alignment
    print("\n" + "="*30)  # Separator for a cleaner menu look
    for i, option in enumerate(options):
        print(f"{i}. {option.center(20)}")
    print("="*30 + "\n")

def execute_option(option):
    base_path = "/data/data/com.termux/files/home/DedSec/Scripts"
    script_paths = {
        '1': 'dedsecs_chat.py',
        '2': 'dedsec_database.py',
        '3': 'back_camera.py',
        '4': 'front_camera.py',
        '5': 'donation_phishing.py',
        '6': 'osintds.py',
        '7': 'naiovum.py',
        '8': 'customization.py',
        '9': 't-login.py'
    }

    if option in script_paths:
        script_name = script_paths[option]
        script_path = os.path.join(base_path, script_name)
        if os.path.exists(script_path):
            os.system(f'cd {base_path} && python {script_name}')
        else:
            print(f"Script {script_name} not found in {base_path}")
    elif option == '0':
        print("Exiting...")
    else:
        print("Invalid option. Please try again.")

def main():
    # Check if "cd ~/DedSec/ && python main_menu.py" is already in bash.bashrc
    bashrc_path = "/data/data/com.termux/files/usr/etc/bash.bashrc"
    main_menu_command = "cd ~/DedSec/ && python main_menu.py"

    # Read the contents of bash.bashrc to check if the command already exists
    try:
        with open(bashrc_path, "r") as bashrc_file:
            bashrc_content = bashrc_file.read()
    except FileNotFoundError:
        bashrc_content = ""

    if main_menu_command not in bashrc_content:
        # Append command to bash.bashrc if it doesn't exist
        with open(bashrc_path, "a") as bashrc_file:
            bashrc_file.write(f"\n{main_menu_command}\n")

    # Ensure the Scripts directory exists
    scripts_dir = "/data/data/com.termux/files/home/DedSec/Scripts"
    os.makedirs(scripts_dir, exist_ok=True)

    # Display menu and prompt user for selection
    while True:
        display_menu()
        choice = input("Select an option: ")
        if choice == '0':
            break
        execute_option(choice)

if __name__ == "__main__":
    main()
