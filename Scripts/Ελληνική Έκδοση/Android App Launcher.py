#!/usr/bin/env python3
import os
import subprocess
import re
import concurrent.futures
import tempfile
import sys

def get_installed_apps():
    """
    Retrieves a mapping of package names to their APK paths using:
      cmd package list packages --user 0 -e -f
    The output is expected to produce lines like:
      package:/data/app/org.fossify.camera-1/base.apk=org.fossify.camera
    """
    package_map = {}
    cmd = "cmd package list packages --user 0 -e -f"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        output = result.stdout.strip()
    except Exception as e:
        print("Σφάλμα κατά την εκτέλεση της εντολής λίστας πακέτων:", e)
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
    Retrieves a dictionary mapping package names to their full launchable component.
    Uses:
      cmd package query-activities --user 0 --brief -a android.intent.action.MAIN -c android.intent.category.LAUNCHER
    Each valid line should be of the form: com.example.app/.MainActivity
    """
    launchable = {}
    cmd = "cmd package query-activities --user 0 --brief -a android.intent.action.MAIN -c android.intent.category.LAUNCHER"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        output = result.stdout.strip()
    except Exception as e:
        print("Σφάλμα κατά την εκτέλεση της εντολής query-activities:", e)
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
    Uses aapt to extract the friendly label from the APK.
    If unsuccessful, returns the package name.
    """
    cmd = f"aapt dump badging \"{apk_path}\""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        match = re.search(r"application: label='([^']+)'", result.stdout)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"Σφάλμα κατά την εκτέλεση του aapt στο {apk_path}: {e}")
    return package

def select_option(options, header):
    """
    Uses fzf to let the user select one option from a list.
    This version writes the options to a temporary file and sets FZF_DEFAULT_COMMAND,
    so that fzf reads from the file while its stdin remains attached to /dev/tty for interactivity.
    Returns the selected option (or None if nothing was chosen).
    """
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write("\n".join(options))
        tmp.flush()
        tmp_name = tmp.name

    env = os.environ.copy()
    env["FZF_DEFAULT_COMMAND"] = f"cat {tmp_name}"
    try:
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
        print("Σφάλμα κατά την εκτέλεση του fzf:", e)
        os.unlink(tmp_name)
        return None

    os.unlink(tmp_name)
    return result.stdout.strip()

def main():
    # Get all installed apps (package -> apk_path)
    package_map = get_installed_apps()
    if not package_map:
        print("Δεν βρέθηκαν εφαρμογές. Ελέγξτε τις άδειες ή το περιβάλλον σας.")
        return

    # Get the mapping of launchable packages to their launchable component
    launchable_map = get_launchable_packages()
    if not launchable_map:
        print("Δεν βρέθηκαν εκκινήσιμες εφαρμογές.")
        return

    # Filter to only include launchable apps that are installed
    filtered_map = {pkg: apk for pkg, apk in package_map.items() if pkg in launchable_map}
    if not filtered_map:
        print("Δεν βρέθηκαν εκκινήσιμες εφαρμογές στις εγκατεστημένες εφαρμογές.")
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
                print(f"Σφάλμα κατά την ανάκτηση ετικέτας για {pkg}: {exc}")
                label = pkg
            apps.append((label, pkg))
    
    # Sort the apps alphabetically by label (case-insensitive)
    apps.sort(key=lambda x: x[0].lower())
    
    # Prepare a list for fzf displaying only the friendly labels
    app_labels = [label for label, _ in apps]
    selected_label = select_option(app_labels, "Επιλέξτε μια εκκινήσιμη εφαρμογή για διαχείριση:")
    if not selected_label:
        print("Δεν έγινε καμία επιλογή.")
        return

    # Find the package corresponding to the selected label
    selected_package = next((pkg for label, pkg in apps if label == selected_label), None)
    if not selected_package:
        print("Η επιλεγμένη εφαρμογή δεν βρέθηκε.")
        return

    # Present options for the chosen app
    options = ["Εκκίνηση", "Πληροφορίες Εφαρμογής", "Απεγκατάσταση"]
    chosen_option = select_option(options, f"Επιλέχθηκε '{selected_label}'. Επιλέξτε μια ενέργεια:")
    if not chosen_option:
        print("Δεν επιλέχθηκε καμία ενέργεια.")
        return

    if chosen_option == "Εκκίνηση":
        component = launchable_map.get(selected_package)
        if component:
            print(f"Εκκίνηση της '{selected_label}' ({selected_package})...")
            os.system(f"am start -n {component} > /dev/null 2>&1")
        else:
            print("Το στοιχείο εκκίνησης δεν βρέθηκε για την επιλεγμένη εφαρμογή.")
    elif chosen_option == "Πληροφορίες Εφαρμογής":
        print(f"Άνοιγμα Πληροφοριών Εφαρμογής για την '{selected_label}' ({selected_package})...")
        os.system(f"am start -a android.settings.APPLICATION_DETAILS_SETTINGS -d package:{selected_package} > /dev/null 2>&1")
    elif chosen_option == "Απεγκατάσταση":
        print(f"Απεγκατάσταση της '{selected_label}' ({selected_package}) χρησιμοποιώντας τη μέθοδο απεγκατάστασης του συστήματος...")
        os.system(f"am start -a android.intent.action.DELETE -d package:{selected_package} > /dev/null 2>&1")
    else:
        print("Δεν επιλέχθηκε έγκυρη ενέργεια.")

    # After performing the selected action, run menu.py
    print("Εκκίνηση του menu...")
    os.system(f"{sys.executable} menu.py")

if __name__ == "__main__":
    main()