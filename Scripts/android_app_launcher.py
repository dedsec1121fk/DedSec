#!/usr/bin/env python3
import os
import subprocess
import re

def get_installed_apps():
    """
    Retrieves a mapping of package names to their APK paths using:
      cmd package list packages --user 0 -e -f
    The output is piped through sed to produce lines like:
      /data/app/org.fossify.camera-1/base.apk org.fossify.camera
    """
    package_map = {}
    cmd = "cmd package list packages --user 0 -e -f | sed 's/package://; s/\\.apk=/\\.apk /'"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        output = result.stdout.strip()
    except Exception as e:
        print("Error running package list command:", e)
        return package_map

    for line in output.splitlines():
        line = line.strip()
        if " " in line:
            apk_path, package = line.split(" ", 1)
            package_map[package.strip()] = apk_path.strip()
    return package_map

def get_launchable_packages():
    """
    Retrieves a set of package names that have a launchable activity.
    Uses:
      cmd package query-activities --user 0 --brief -a android.intent.action.MAIN -c android.intent.category.LAUNCHER
    Each valid line should be of the form: com.example.app/.MainActivity
    """
    launchable = set()
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
            package = line.split('/')[0]
            launchable.add(package)
    return launchable

def get_app_label(apk_path, package):
    """
    Uses aapt to extract the friendly label from the APK.
    If unsuccessful, returns the package name.
    """
    cmd = f"aapt dump badging \"{apk_path}\""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        # Look for a line like: application: label='Fossify Camera'
        match = re.search(r"application: label='([^']+)'", result.stdout)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"Error running aapt on {apk_path}: {e}")
    return package

def select_option(options, header):
    """
    Uses fzf to let the user select one option from a newline-separated list.
    Returns the selected option (or None if nothing was chosen).
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
    # Get the mapping of all installed apps (package -> apk_path)
    package_map = get_installed_apps()
    if not package_map:
        print("No apps found. Please check your permissions or environment.")
        return

    # Get the set of launchable packages
    launchable_set = get_launchable_packages()
    if not launchable_set:
        print("No launchable apps found.")
        return

    # Filter to only include launchable apps
    filtered_map = {pkg: apk for pkg, apk in package_map.items() if pkg in launchable_set}
    
    if not filtered_map:
        print("No launchable apps found in installed apps.")
        return

    # Build a list of tuples: (friendly_label, package)
    apps = []
    for package, apk_path in filtered_map.items():
        label = get_app_label(apk_path, package)
        apps.append((label, package))
    
    # Sort the apps alphabetically by label (case-insensitive)
    apps.sort(key=lambda x: x[0].lower())
    
    # Prepare a list for fzf displaying only the friendly labels
    app_labels = [label for label, _ in apps]
    selected_label = select_option(app_labels, "Select a launchable app to manage:")
    
    if not selected_label:
        print("No selection made.")
        return

    # Find the package corresponding to the selected label
    selected_package = next((pkg for label, pkg in apps if label == selected_label), None)
    if not selected_package:
        print("Selected app not found.")
        return

    # Present options for the chosen app
    options = ["Launch", "App Info", "Uninstall"]
    chosen_option = select_option(options, f"Selected '{selected_label}'. Choose an action:")
    
    if not chosen_option:
        print("No option selected.")
        return

    if chosen_option == "Launch":
        print(f"Launching '{selected_label}' ({selected_package})...")
        os.system(f"monkey -p {selected_package} -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1")
    elif chosen_option == "App Info":
        print(f"Opening App Info for '{selected_label}' ({selected_package})...")
        os.system(f"am start -a android.settings.APPLICATION_DETAILS_SETTINGS -d package:{selected_package} > /dev/null 2>&1")
    elif chosen_option == "Uninstall":
        print(f"Uninstalling '{selected_label}' ({selected_package})...")
        os.system(f"pm uninstall {selected_package} > /dev/null 2>&1")
    else:
        print("No valid option selected.")

if __name__ == "__main__":
    main()
