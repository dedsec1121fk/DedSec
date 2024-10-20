#!/data/data/com.termux/files/usr/bin/python

import os
import hashlib
import sys

# Paths
cred_dir = "/data/data/com.termux/files/usr/share/login"
cred_file = os.path.join(cred_dir, "credentials.enc")
LOGIN_SCRIPT_PATH = "/data/data/com.termux/files/usr/bin/login"
BASH_PROFILE_PATH = os.path.expanduser("~/.bash_profile")

# Function to hash a string using SHA-256
def hash_string(s):
    return hashlib.sha256(s.encode()).hexdigest()

# Function to set up a new username and password
def setup_credentials():
    print("Setting up new username and password...")
    username = input("Enter new username: ")
    passone = input("Enter new password: ")
    passtwo = input("Repeat password: ")

    if passone != passtwo:
        print("Passwords do not match. Try again.")
        return

    # Create credentials directory if it doesn't exist
    os.makedirs(cred_dir, exist_ok=True)

    # Hash and store username and password
    hashed_username = hash_string(username)
    hashed_password = hash_string(passone)

    with open(cred_file, 'w') as f:
        f.write(f"{hashed_username}\n{hashed_password}\n")

    print("Username and password setup completed.")

# Function to validate login credentials
def validate_login():
    if not os.path.exists(cred_file):
        print("No credentials found, please set them up first.")
        setup_credentials()
        sys.exit(0)

    username = input("Enter Username: ")
    password = input("Enter Password: ")

    hashed_username = hash_string(username)
    hashed_password = hash_string(password)

    with open(cred_file, 'r') as f:
        stored_username = f.readline().strip()
        stored_password = f.readline().strip()

    if hashed_username == stored_username and hashed_password == stored_password:
        os.system('clear')  # Clear the screen on successful login
        os.execlp("bash", "bash", "-l")  # Continue to shell without showing login screen
    else:
        print("Invalid credentials.")
        sys.exit(1)  # Close terminal on invalid credentials

# Function to create the login script
def create_login_script():
    script_content = f"""#!/data/data/com.termux/files/usr/bin/python

import os
import hashlib
import sys

cred_dir = "{cred_dir}"
cred_file = os.path.join(cred_dir, "credentials.enc")

def hash_string(s):
    return hashlib.sha256(s.encode()).hexdigest()

def validate_login():
    if not os.path.exists(cred_file):
        print("No credentials found.")
        sys.exit(1)

    username = input("Enter Username: ")
    password = input("Enter Password: ")

    hashed_username = hash_string(username)
    hashed_password = hash_string(password)

    with open(cred_file, 'r') as f:
        stored_username = f.readline().strip()
        stored_password = f.readline().strip()

    if hashed_username == stored_username and hashed_password == stored_password:
        os.system('clear')  # Clear the screen on successful login
        os.execlp("bash", "bash", "-l")
    else:
        print("Invalid credentials.")
        sys.exit(1)

validate_login()
"""
    with open(LOGIN_SCRIPT_PATH, 'w') as f:
        f.write(script_content)
    os.chmod(LOGIN_SCRIPT_PATH, 0o700)
    print(f"Created login script at {LOGIN_SCRIPT_PATH}")

# Function to set login execution in bash_profile
def setup_login_execution():
    if not os.path.exists(LOGIN_SCRIPT_PATH):
        create_login_script()

    # Check if login script is already in .bash_profile
    with open(BASH_PROFILE_PATH, 'a+') as f:
        f.seek(0)  # Move to the beginning of the file
        if LOGIN_SCRIPT_PATH not in f.read():
            f.write(f"exec {LOGIN_SCRIPT_PATH}\n")
            print(f"Login script set to run in {BASH_PROFILE_PATH}")

# Function to delete the login screen and credentials
def delete_login_screen():
    print("Removing login screen setup...")

    # Remove login script
    if os.path.exists(LOGIN_SCRIPT_PATH):
        os.remove(LOGIN_SCRIPT_PATH)

    # Remove credentials
    if os.path.exists(cred_file):
        os.remove(cred_file)

    # Remove login execution from bash_profile
    with open(BASH_PROFILE_PATH, 'r') as f:
        lines = f.readlines()
    with open(BASH_PROFILE_PATH, 'w') as f:
        for line in lines:
            if LOGIN_SCRIPT_PATH not in line:
                f.write(line)

    print("Login screen and credentials deleted.")

# Main menu function
def main_menu():
    while True:
        print("1) Setup new username and password")
        print("2) Delete login screen and credentials")
        print("3) Exit")
        option = input("Select an option (1-3): ")

        if option == "1":
            setup_credentials()
            setup_login_execution()
        elif option == "2":
            delete_login_screen()
        elif option == "3":
            print("Exiting.")
            break
        else:
            print("Invalid option. Please try again.")

# Run the main menu
if __name__ == "__main__":
    main_menu()
