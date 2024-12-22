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

# Display the menu with a centered title
def display_menu():
    terminal_width = os.get_terminal_size().columns  # Get terminal width
    title = "DedSec's Main Menu"
    centered_title = title.center(terminal_width)  # Center the title

    print(centered_title)
    print("1) DedSec's Chat")
    print("2) Fox Chat")
    print("3) Back Camera")
    print("4) Front Camera")
    print("5) Sound Recording")
    print("6) Location")
    print("7) DedSec Database")
    print("8) Donation Phishing")
    print("9) OSINTDS")
    print("10) T-Login")
    print("11) Customization")
    print("0) Exit")

# Execute the selected option
def execute_option(option):
    scripts = [
        "dedsecs_chat.py",
        "fox_chat.py",
        "back_camera.py",
        "front_camera.py",
        "sound_recording.py",
        "location.py",
        "dedsec_database.py",
        "donation_phising.py",
        "osintds.py",
        "t-login.py",
        "customization.py"
    ]

    if option == 0:
        print("Exiting...")
        exit(0)
    elif 1 <= option <= 11:
        script = scripts[option - 1]
        os.system(f"cd /data/data/com.termux/files/home/DedSec/Scripts && python \"{script}\"")
    else:
        print("Invalid option. Please try again.")

# Main function
def main():
    ensure_bashrc_setup()
    while True:
        display_menu()
        try:
            choice = int(input("Select an option: "))
            execute_option(choice)
        except ValueError:
            print("Please enter a valid number.")

if __name__ == "__main__":
    main()
