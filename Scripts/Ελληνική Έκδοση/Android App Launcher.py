#!/usr/bin/env python3
import os
import subprocess
import re
import concurrent.futures
import tempfile
import sys

# ΣΗΜΕΙΩΣΗ: Αυτό το script προορίζεται πλέον να εκτελεστεί *απευθείας* σε μια συσκευή Android
# μέσα σε ένα περιβάλλον shell όπως το Termux.

def get_installed_apps():
    """
    Ανακτά μια αντιστοίχιση ονομάτων πακέτων με τις διαδρομές των APK τους χρησιμοποιώντας
    μια εγγενή εντολή shell.
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
        # Αντικατάσταση του '.apk=' με '.apk ' για ευκολότερο διαχωρισμό
        line = line.replace(".apk=", ".apk ")
        if " " in line:
            apk_path, package = line.split(" ", 1)
            package_map[package.strip()] = apk_path.strip()
    return package_map

def get_launchable_packages():
    """
    Ανακτά ένα λεξικό που αντιστοιχίζει ονόματα πακέτων στο πλήρες εκκινήσιμο component
    τους χρησιμοποιώντας μια εγγενή εντολή shell.
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
    Χρησιμοποιεί το aapt (πρέπει να είναι διαθέσιμο στο PATH του shell, π.χ., μέσω
    των εργαλείων Android SDK) για να εξαγάγει την φιλική ετικέτα από το APK.
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
    Χρησιμοποιεί το fzf για να επιτρέψει στον χρήστη να επιλέξει μία επιλογή από μια λίστα.
    """
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        tmp.write("\n".join(options))
        tmp.flush()
        tmp_name = tmp.name

    env = os.environ.copy()
    env["FZF_DEFAULT_COMMAND"] = f"cat {tmp_name}"
    try:
        # Ανάγνωση/Γραφή απευθείας από το Termux TTY
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
    package_map = get_installed_apps()
    if not package_map:
        print("Δεν βρέθηκαν εφαρμογές. Ελέγξτε τα δικαιώματά σας ή το περιβάλλον.")
        return

    launchable_map = get_launchable_packages()
    if not launchable_map:
        print("Δεν βρέθηκαν εκκινήσιμες εφαρμογές.")
        return

    filtered_map = {pkg: apk for pkg, apk in package_map.items() if pkg in launchable_map}
    if not filtered_map:
        print("Δεν βρέθηκαν εκκινήσιμες εφαρμογές στις εγκατεστημένες εφαρμογές.")
        return

    # Χρήση ThreadPoolExecutor για παραλληλισμό της εξαγωγής των ετικετών εφαρμογών
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
                print(f"Σφάλμα ανάκτησης ετικέτας για το {pkg}: {exc}")
                label = pkg
            apps.append((label, pkg))
    
    apps.sort(key=lambda x: x[0].lower())
    
    app_labels = [label for label, _ in apps]
    selected_label = select_option(app_labels, "Επιλέξτε μια εκκινήσιμη εφαρμογή για διαχείριση:")
    if not selected_label:
        print("Δεν έγινε καμία επιλογή.")
        return

    selected_package = next((pkg for label, pkg in apps if label == selected_label), None)
    if not selected_package:
        print("Η επιλεγμένη εφαρμογή δεν βρέθηκε.")
        return

    options = ["Εκκίνηση", "Πληροφορίες Εφαρμογής", "Απεγκατάσταση", "Εξαγωγή APK"]
    chosen_option = select_option(options, f"Επιλέχθηκε '{selected_label}'. Επιλέξτε μια ενέργεια:")
    if not chosen_option:
        print("Δεν επιλέχθηκε καμία ενέργεια.")
        return

    if chosen_option == "Εκκίνηση":
        component = launchable_map.get(selected_package)
        if component:
            print(f"Εκκίνηση '{selected_label}' ({selected_package})...")
            os.system(f"am start -n {component} > /dev/null 2>&1")
        else:
            print("Το component εκκίνησης δεν βρέθηκε για την επιλεγμένη εφαρμογή.")
            
    elif chosen_option == "Πληροφορίες Εφαρμογής":
        print(f"Άνοιγμα Πληροφοριών Εφαρμογής για το '{selected_label}' ({selected_package})...")
        os.system(f"am start -a android.settings.APPLICATION_DETAILS_SETTINGS -d package:{selected_package} > /dev/null 2>&1")
        
    elif chosen_option == "Απεγκατάσταση":
        print(f"Απεγκατάσταση '{selected_label}' ({selected_package}) χρησιμοποιώντας τη μέθοδο απεγκατάστασης συστήματος...")
        os.system(f"am start -a android.intent.action.DELETE -d package:{selected_package} > /dev/null 2>&1")
        
    elif chosen_option == "Εξαγωγή APK":
        apk_path_on_device = package_map.get(selected_package)
        if apk_path_on_device:
            
            # --- ΕΝΑΡΞΗ: ΝΕΑ ΛΟΓΙΚΗ ΔΙΑΔΡΟΜΗΣ ΑΡΧΕΙΟΥ ---
            # Το Termux κάνει mount τον εσωτερικό χώρο αποθήκευσης στο $HOME/storage/shared
            # Ο φάκελος Λήψεις είναι $HOME/storage/shared/Download
            # Σημείωση: Αυτό απαιτεί από τον χρήστη να έχει εκτελέσει το 'termux-setup-storage'
            
            # Κατασκευή της διαδρομής του φακέλου προορισμού
            base_storage = os.path.join(os.path.expanduser('~'), 'storage', 'shared')
            downloads_dir = os.path.join(base_storage, 'Download')
            target_dir = os.path.join(downloads_dir, "Extracted APK's")
            destination_file = os.path.join(target_dir, f"{selected_package}.apk")

            print(f"Διασφάλιση ότι υπάρχει ο φάκελος προορισμού: '{target_dir}'...")
            
            # Δημιουργία του φακέλου προορισμού αναδρομικά αν δεν υπάρχει
            # Χρήση mkdir -p μέσω os.system για απλότητα στο Termux
            if os.system(f"mkdir -p \"{target_dir}\"") != 0:
                 print("Σφάλμα: Δεν ήταν δυνατή η δημιουργία του φακέλου προορισμού. Ελέγξτε τα δικαιώματα αποθήκευσης του Termux ('termux-setup-storage').")
                 return
            
            print(f"Αντιγραφή APK από '{apk_path_on_device}' σε '{destination_file}'...")
            
            try:
                # Χρήση της εγγενούς εντολής Android 'cp' (copy)
                copy_cmd = ["cp", apk_path_on_device, destination_file]
                
                # Χρήση subprocess.run για καλύτερο χειρισμό σφαλμάτων από το os.system
                result = subprocess.run(copy_cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"Επιτυχής εξαγωγή APK στο {destination_file}")
                else:
                    print(f"Σφάλμα εξαγωγής APK. Η εντολή αντιγραφής απέτυχε με κωδικό επιστροφής {result.returncode}.")
                    if result.stderr:
                        print(f"Λεπτομέρειες σφάλματος: {result.stderr.strip()}")
            except FileNotFoundError:
                print("Σφάλμα: Η εντολή 'cp' δεν βρέθηκε. Αυτό δεν θα έπρεπε να συμβεί σε ένα τυπικό Termux shell.")
            except Exception as e:
                print(f"Προέκυψε ένα μη αναμενόμενο σφάλμα κατά την αντιγραφή: {e}")
        else:
            print("Η διαδρομή APK δεν βρέθηκε για την επιλεγμένη εφαρμογή.")

    else:
        print("Δεν επιλέχθηκε καμία έγκυρη ενέργεια.")

    # Μετά την εκτέλεση της επιλεγμένης ενέργειας, εκτέλεση του menu.py
    print("Εκκίνηση μενού...")
    os.system(f"{sys.executable} menu.py")

if __name__ == "__main__":
    main()