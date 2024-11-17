import os

def display_main_menu():
    print("\n" + "="*40)
    print("              Main Menu              ")
    print("="*40)
    print("1) Chatrooms")
    print("2) Hacks")
    print("3) Tools")
    print("4) Settings & Customization")
    print("5) Exit")
    print("="*40 + "\n")

def display_sub_menu(main_choice):
    if main_choice == '1':
        print("\nChatrooms")
        print("1) DedSec's Chat (Limited to 8 People)")
        print("2) Fox Chat (Unlimited People)")
    elif main_choice == '2':
        print("\nHacks")
        print("1) Back Camera Hack")
        print("2) Front Camera Hack")
        print("3) Sound Recording Hack")
        print("4) Gallery Hack")
        print("5) Donation Phishing")
    elif main_choice == '3':
        print("\nTools")
        print("1) DedSec Database")
        print("2) OSINTDS")
    elif main_choice == '4':
        print("\nSettings & Customization")
        print("1) T-Login")
        print("2) Customization")
        print("3) NAIOVUM")
    print("="*40 + "\n")

def execute_option(main_choice, sub_choice):
    base_path = "/data/data/com.termux/files/home/DedSec/Scripts"
    script_paths = {
        '1_1': 'dedsecs_chat.py',
        '1_2': 'fox_chat.py',
        '2_1': 'back_camera.py',
        '2_2': 'front_camera.py',
        '2_3': 'sound_recording.py',
        '2_4': 'gallery.py',
        '2_5': 'donation_phishing.py',
        '3_1': 'dedsec_database.py',
        '3_2': 'osintds.py',
        '4_1': 't-login.py',
        '4_2': 'customization.py',
        '4_3': 'naiovum.py'
    }

    key = f"{main_choice}_{sub_choice}"
    if key in script_paths:
        script_name = script_paths[key]
        script_path = os.path.join(base_path, script_name)
        if os.path.exists(script_path):
            os.system(f'cd {base_path} && python {script_name}')
        else:
            print(f"Script {script_name} not found in {base_path}")
    elif main_choice == '5':
        print("Exiting...")
    else:
        print("Invalid option. Please try again.")

def main():
    bashrc_path = "/data/data/com.termux/files/usr/etc/bash.bashrc"
    main_menu_command = "cd ~/DedSec/ && python main_menu.py"

    # Check if main menu command is in bash.bashrc, add if not
    try:
        with open(bashrc_path, "r") as bashrc_file:
            bashrc_content = bashrc_file.read()
    except FileNotFoundError:
        bashrc_content = ""

    if main_menu_command not in bashrc_content:
        with open(bashrc_path, "a") as bashrc_file:
            bashrc_file.write(f"\n{main_menu_command}\n")

    # Ensure the Scripts directory exists
    scripts_dir = "/data/data/com.termux/files/home/DedSec/Scripts"
    os.makedirs(scripts_dir, exist_ok=True)

    # Display menu and prompt user for selection
    while True:
        display_main_menu()
        main_choice = input("Select a main option (1-5): ")
        if main_choice == '5':
            print("Exiting...")
            break
        elif main_choice in ['1', '2', '3', '4']:
            display_sub_menu(main_choice)
            sub_choice = input("Select a sub-option: ")
            execute_option(main_choice, sub_choice)
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()

