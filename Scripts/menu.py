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

# Categorize scripts based on keywords in their names
def categorize_scripts(scripts):
    categories = {
        "Chatting": [],
        "Camera Hacking": [],
        "Microphone Hacking": [],
        "Location Hacking": [],
        "Other Features": []
    }
    
    for script in scripts:
        if "chat" in script.lower():
            categories["Chatting"].append(script)
        elif "camera" in script.lower():
            categories["Camera Hacking"].append(script)
        elif "microphone" in script.lower() or "recording" in script.lower():
            categories["Microphone Hacking"].append(script)
        elif "location" in script.lower():
            categories["Location Hacking"].append(script)
        else:
            categories["Other Features"].append(script)
    
    return categories

# Display the menu based on the categories
def display_categories_menu(categories):
    print("\nAvailable Categories:")
    for idx, category in enumerate(categories, 1):
        print(f"{idx}) {category}")
    print("0) Exit")
    
    choice = input("Select a category: ")
    return choice, categories

# Display scripts in a selected category
def display_scripts_in_category(category, scripts):
    print(f"\nScripts in {category}:")
    if not scripts:
        print(f"No scripts found in {category}.")
        return []
    
    for i, script in enumerate(scripts, 1):
        print(f"{i}) {format_script_name(script)}")
    print("0) Back to Categories")
    return scripts

# Main function
def main():
    ensure_bashrc_setup()
    
    # List all .py files except menu.py
    try:
        scripts = [f for f in os.listdir(scripts_path) if f.endswith(".py") and f != "menu.py"]
        if not scripts:
            print("\nNo scripts found in the Scripts folder.")
            return
    except FileNotFoundError:
        print(f"Error: {scripts_path} not found.")
        exit(1)

    categories = categorize_scripts(scripts)
    
    while True:
        choice, categories = display_categories_menu(categories)
        
        if choice == "0":
            print("Exiting...")
            exit(0)
        elif choice.isdigit() and 1 <= int(choice) <= len(categories):
            category_name = list(categories.keys())[int(choice) - 1]
            scripts_in_category = categories[category_name]
            while True:
                scripts_in_category = display_scripts_in_category(category_name, scripts_in_category)
                if not scripts_in_category:
                    break
                script_choice = input("Select a script to execute: ")
                if script_choice == "0":
                    break
                elif script_choice.isdigit() and 1 <= int(script_choice) <= len(scripts_in_category):
                    script_name = scripts_in_category[int(script_choice) - 1]
                    os.system(f"cd {scripts_path} && python {script_name}")
                else:
                    print("Invalid option. Please try again.")
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()

