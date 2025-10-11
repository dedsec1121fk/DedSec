#!/usr/bin/env python3
import os
import subprocess
import re
import concurrent.futures
import tempfile
import sys

# NOTE: This script is now intended to be run *directly* on an Android device
# inside a shell environment like Termux.

def get_installed_apps():
    """
    Retrieves a mapping of package names to their APK paths using a native shell command.
    """
    package_map = {}
    cmd = "cmd package list packages --user 0 -e -f"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        output = result.stdout.strip()
    except Exception as e:
        print("Error running package list command:", e)
        return package_map

    for line in output.splitlines():
        line = line.strip()
        if line.startswith("package:"):
            line = line[len("package:"):]
        # Replace '.apk=' with '.apk ' for easier splitting
        line = line.replace(".apk=", ".apk ")
        if " " in line:
            apk_path, package = line.split(" ", 1)
            package_map[package.strip()] = apk_path.strip()
    return package_map

def get_launchable_packages():
    """
    Retrieves a dictionary mapping package names to their full launchable component
    using a native shell command.
    """
    launchable = {}
    cmd = "cmd package query-activities --user 0 --brief -a android.intent.action.MAIN -c android.intent.category.LAUNCHER"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        output = result.stdout.strip()
    except Exception as e:
        print("Error running query-activities command:", e)
        return launchable

    for line in output.splitlines():
        line = line.strip()
        if '/' in line:
            parts = line.split('/', 1)
            if len(parts) == 2:
                pkg, act = parts
                component = f"{pkg}/{act}"
                launchable[pkg] = component
    return launchable

def get_app_label(apk_path, package):
    """
    Uses aapt (must be available in the shell PATH, e.g., via Android SDK tools)
    to extract the friendly label from the APK.
    """
    cmd = f"aapt dump badging \"{apk_path}\""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        match = re.search(r"application: label='([^']+)'", result.stdout)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"Error running aapt on {apk_path}: {e}")
    return package

def select_option(options, header):
    """
    Uses fzf to let the user select one option from a list.
    """
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write("\n".join(options))
        tmp.flush()
        tmp_name = tmp.name

    env = os.environ.copy()
    env["FZF_DEFAULT_COMMAND"] = f"cat {tmp_name}"
    try:
        # Read/Write directly from Termux TTY
        with open("/dev/tty", "r") as tty_in, open("/dev/tty", "w") as tty_out:
            result = subprocess.run(
                ["fzf", "--header", header],
                env=env,
                stdin=tty_in,
                stdout=subprocess.PIPE,
                stderr=tty_out,
                text=True
            )
    except Exception as e:
        print("Error running fzf:", e)
        os.unlink(tmp_name)
        return None

    os.unlink(tmp_name)
    return result.stdout.strip()

def main():
    package_map = get_installed_apps()
    if not package_map:
        print("No apps found. Please check your permissions or environment.")
        return

    launchable_map = get_launchable_packages()
    if not launchable_map:
        print("No launchable apps found.")
        return

    filtered_map = {pkg: apk for pkg, apk in package_map.items() if pkg in launchable_map}
    if not filtered_map:
        print("No launchable apps found in installed apps.")
        return

    # Use ThreadPoolExecutor to parallelize the extraction of app labels
    apps = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_pkg = {
            executor.submit(get_app_label, apk_path, pkg): pkg
            for pkg, apk_path in filtered_map.items()
        }
        for future in concurrent.futures.as_completed(future_to_pkg):
            pkg = future_to_pkg[future]
            try:
                label = future.result()
            except Exception as exc:
                print(f"Error retrieving label for {pkg}: {exc}")
                label = pkg
            apps.append((label, pkg))
    
    apps.sort(key=lambda x: x[0].lower())
    
    app_labels = [label for label, _ in apps]
    selected_label = select_option(app_labels, "Select a launchable app to manage:")
    if not selected_label:
        print("No selection made.")
        return

    selected_package = next((pkg for label, pkg in apps if label == selected_label), None)
    if not selected_package:
        print("Selected app not found.")
        return

    options = ["Launch", "App Info", "Uninstall", "Extract APK"]
    chosen_option = select_option(options, f"Selected '{selected_label}'. Choose an action:")
    if not chosen_option:
        print("No option selected.")
        return

    if chosen_option == "Launch":
        component = launchable_map.get(selected_package)
        if component:
            print(f"Launching '{selected_label}' ({selected_package})...")
            os.system(f"am start -n {component} > /dev/null 2>&1")
        else:
            print("Launch component not found for the selected app.")
            
    elif chosen_option == "App Info":
        print(f"Opening App Info for '{selected_label}' ({selected_package})...")
        os.system(f"am start -a android.settings.APPLICATION_DETAILS_SETTINGS -d package:{selected_package} > /dev/null 2>&1")
        
    elif chosen_option == "Uninstall":
        print(f"Uninstalling '{selected_label}' ({selected_package}) using the system uninstall method...")
        os.system(f"am start -a android.intent.action.DELETE -d package:{selected_package} > /dev/null 2>&1")
        
    elif chosen_option == "Extract APK":
        apk_path_on_device = package_map.get(selected_package)
        if apk_path_on_device:
            
            # --- START: NEW FILE PATH LOGIC ---
            # Termux mounts internal storage at $HOME/storage/shared
            # The Downloads folder is $HOME/storage/shared/Download
            # Note: This requires the user to have run 'termux-setup-storage'
            
            # Construct the target directory path
            base_storage = os.path.join(os.path.expanduser('~'), 'storage', 'shared')
            downloads_dir = os.path.join(base_storage, 'Download')
            target_dir = os.path.join(downloads_dir, "Extracted APK's")
            destination_file = os.path.join(target_dir, f"{selected_package}.apk")

            print(f"Ensuring destination directory exists: '{target_dir}'...")
            
            # Create the destination directory recursively if it doesn't exist
            # Using mkdir -p via os.system for simplicity in Termux
            if os.system(f"mkdir -p \"{target_dir}\"") != 0:
                 print("Error: Could not create the destination directory. Check Termux storage permissions ('termux-setup-storage').")
                 return
            
            print(f"Copying APK from '{apk_path_on_device}' to '{destination_file}'...")
            
            try:
                # Use native Android 'cp' (copy) command
                copy_cmd = ["cp", apk_path_on_device, destination_file]
                
                # Using subprocess.run for better error handling than os.system
                result = subprocess.run(copy_cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"Successfully extracted APK to {destination_file}")
                else:
                    print(f"Error extracting APK. Copy command failed with return code {result.returncode}.")
                    if result.stderr:
                        print(f"Error details: {result.stderr.strip()}")
            except FileNotFoundError:
                print("Error: 'cp' command not found. This should not happen in a standard Termux shell.")
            except Exception as e:
                print(f"An unexpected error occurred during copy: {e}")
        else:
            print("APK path not found for the selected app.")

    else:
        print("No valid option selected.")

    # After performing the selected action, run menu.py
    print("Launching menu...")
    os.system(f"{sys.executable} menu.py")

if __name__ == "__main__":
    main()