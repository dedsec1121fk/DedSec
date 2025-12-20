#!/usr/bin/env python3
import os
import subprocess
import re
import concurrent.futures
import tempfile
import sys
import zipfile
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

# ΣΗΜΕΙΩΣΗ: Αυτό το σενάριο προορίζεται πλέον να εκτελείται *απευθείας* σε μια συσκευή Android
# μέσα σε ένα περιβάλλον shell όπως το Termux.

def get_installed_apps():
    """
    Ανακτά μια αντιστοίχιση ονομάτων πακέτων με τις διαδρομές APK τους χρησιμοποιώντας μια εγγενή εντολή shell.
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
    Ανακτά ένα λεξικό που αντιστοιχίζει ονόματα πακέτων με το πλήρες εκκινήσιμο στοιχείο τους (component)
    χρησιμοποιώντας μια εγγενή εντολή shell.
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
    Χρησιμοποιεί το aapt (πρέπει να είναι διαθέσιμο στο PATH του shell, π.χ., μέσω των εργαλείων Android SDK)
    για να εξαγάγει την φιλική ετικέτα από το APK.
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
        # Άμεση ανάγνωση/εγγραφή από το TTY του Termux
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

class SimpleAppPermInspector:
    """
    Απλοποιημένη έκδοση του App Perm Inspector για ενσωμάτωση
    """
    def __init__(self):
        self.dangerous_permissions = self.load_dangerous_permissions()
        self.tracker_databases = self.load_tracker_databases()
    
    def load_dangerous_permissions(self):
        """Φόρτωση βάσης δεδομένων επικίνδυνων αδειών Android"""
        dangerous_perms = {
            "ACCESS_FINE_LOCATION": {"risk": "high", "description": "Πρόσβαση σε ακριβή τοποθεσία (GPS)", "threat": "Μπορεί να παρακολουθεί την ακριβή τοποθεσία σας"},
            "ACCESS_COARSE_LOCATION": {"risk": "medium", "description": "Πρόσβαση σε κατά προσέγγιση τοποθεσία", "threat": "Μπορεί να παρακολουθεί τη γενική περιοχή σας"},
            "CAMERA": {"risk": "high", "description": "Πρόσβαση στην κάμερα της συσκευής", "threat": "Μπορεί να τραβήξει φωτογραφίες/βίντεο χωρίς συγκατάθεση"},
            "RECORD_AUDIO": {"risk": "high", "description": "Εγγραφή ήχου", "threat": "Μπορεί να ηχογραφήσει συνομιλίες"},
            "READ_CONTACTS": {"risk": "high", "description": "Ανάγνωση λίστας επαφών", "threat": "Μπορεί να αποκτήσει πρόσβαση σε όλες τις επαφές σας"},
            "WRITE_CONTACTS": {"risk": "medium", "description": "Τροποποίηση επαφών", "threat": "Μπορεί να αλλάξει τα δεδομένα των επαφών σας"},
            "SEND_SMS": {"risk": "critical", "description": "Αποστολή μηνυμάτων SMS", "threat": "Μπορεί να στείλει SMS υψηλής χρέωσης"},
            "READ_SMS": {"risk": "critical", "description": "Ανάγνωση μηνυμάτων SMS", "threat": "Μπορεί να διαβάσει όλα τα μηνύματά σας"},
            "CALL_PHONE": {"risk": "critical", "description": "Πραγματοποίηση τηλεφωνικών κλήσεων", "threat": "Μπορεί να πραγματοποιήσει κλήσεις χωρίς συγκατάθεση"},
            "READ_PHONE_STATE": {"risk": "high", "description": "Πρόσβαση σε πληροφορίες τηλεφώνου", "threat": "Μπορεί να λάβει τον αριθμό τηλεφώνου, ΙΜΕΙ, κ.λπ."},
            "READ_EXTERNAL_STORAGE": {"risk": "medium", "description": "Ανάγνωση εξωτερικού χώρου αποθήκευσης", "threat": "Μπορεί να αποκτήσει πρόσβαση στα αρχεία, τις φωτογραφίες, τα έγγραφά σας"},
            "WRITE_EXTERNAL_STORAGE": {"risk": "medium", "description": "Εγγραφή σε εξωτερικό χώρο αποθήκευσης", "threat": "Μπορεί να τροποποιήσει ή να διαγράψει τα αρχεία σας"},
            "ACCESS_BACKGROUND_LOCATION": {"risk": "critical", "description": "Πρόσβαση στην τοποθεσία στο παρασκήνιο", "threat": "Μπορεί να παρακολουθεί την τοποθεσία ακόμα και όταν η εφαρμογή δεν χρησιμοποιείται"},
            "BODY_SENSORS": {"risk": "high", "description": "Πρόσβαση σε αισθητήρες υγείας", "threat": "Μπορεί να έχει πρόσβαση σε καρδιακό ρυθμό, αριθμό βημάτων, κ.λπ."}
        }
        return dangerous_perms
    
    def load_tracker_databases(self):
        """Φόρτωση γνωστών βιβλιοθηκών παρακολούθησης (trackers)"""
        trackers = {
            "Google Analytics": {"signatures": ["com.google.analytics", "com.google.android.gms.analytics"], "category": "Αναλυτικά", "privacy_impact": "high"},
            "Facebook SDK": {"signatures": ["com.facebook", "com.facebook.ads"], "category": "Διαφήμιση", "privacy_impact": "high"},
            "Firebase Analytics": {"signatures": ["com.google.firebase.analytics"], "category": "Αναλυτικά", "privacy_impact": "medium"},
            "AdMob": {"signatures": ["com.google.android.gms.ads"], "category": "Διαφήμιση", "privacy_impact": "high"},
            "Flurry": {"signatures": ["com.flurry.android"], "category": "Αναλυτικά", "privacy_impact": "medium"},
            "AppsFlyer": {"signatures": ["com.appsflyer"], "category": "Αναλυτικά", "privacy_impact": "high"}
        }
        return trackers
    
    def extract_permissions_basic(self, apk_path):
        """Εξαγωγή αδειών από το APK χρησιμοποιώντας βασική ανάλυση"""
        try:
            with zipfile.ZipFile(apk_path, 'r') as apk_zip:
                permission_pattern = r'android\.permission\.[A-Z_]+'
                permissions_found = set()
                
                for file_name in apk_zip.namelist():
                    if file_name.endswith('.xml') or file_name.endswith('.dex') or file_name.endswith('.arsc'):
                        try:
                            with apk_zip.open(file_name) as file:
                                content = file.read().decode('utf-8', errors='ignore')
                                found_perms = re.findall(permission_pattern, content)
                                permissions_found.update(found_perms)
                        except:
                            continue
                
                return list(permissions_found)
                
        except Exception as e:
            print(f"❌ Η εξαγωγή αδειών απέτυχε: {e}")
            return []
    
    def detect_trackers(self, apk_path):
        """Εντοπισμός βιβλιοθηκών παρακολούθησης (trackers) στο APK"""
        trackers_found = []
        try:
            with zipfile.ZipFile(apk_path, 'r') as apk_zip:
                all_files = apk_zip.namelist()
                
                for tracker_name, tracker_info in self.tracker_databases.items():
                    for signature in tracker_info['signatures']:
                        if any(signature in file_path for file_path in all_files):
                            trackers_found.append({
                                'name': tracker_name,
                                'category': tracker_info['category'],
                                'privacy_impact': tracker_info['privacy_impact']
                            })
            
            return trackers_found
            
        except Exception as e:
            print(f"❌ Σφάλμα εντοπισμού tracker: {e}")
            return []
    
    def analyze_app_permissions(self, apk_path, app_name):
        """Κύρια συνάρτηση ανάλυσης"""
        print(f"\n🔍 Ανάλυση σε εξέλιξη: {app_name}")
        print("="*60)
        
        # Εξαγωγή αδειών
        all_permissions = self.extract_permissions_basic(apk_path)
        
        # Κατηγοριοποίηση αδειών
        dangerous_perms = []
        normal_perms = []
        
        for perm in all_permissions:
            perm_name = perm.split('.')[-1] if '.' in perm else perm
            if perm_name in self.dangerous_permissions:
                dangerous_perms.append({
                    'name': perm,
                    'risk': self.dangerous_permissions[perm_name]['risk'],
                    'description': self.dangerous_permissions[perm_name]['description'],
                    'threat': self.dangerous_permissions[perm_name]['threat']
                })
            else:
                normal_perms.append(perm)
        
        # Εντοπισμός trackers
        trackers = self.detect_trackers(apk_path)
        
        # Υπολογισμός βαθμολογίας κινδύνου
        risk_score = 0
        for perm in dangerous_perms:
            if perm['risk'] == 'critical': risk_score += 10
            elif perm['risk'] == 'high': risk_score += 7
            elif perm['risk'] == 'medium': risk_score += 4
        
        risk_level = "ΥΨΗΛΟ" if risk_score >= 20 else "ΜΕΤΡΙΟ" if risk_score >= 10 else "ΧΑΜΗΛΟ"
        
        # Εμφάνιση αποτελεσμάτων
        print(f"\n📊 ΑΠΟΤΕΛΕΣΜΑΤΑ ΑΝΑΛΥΣΗΣ ΑΣΦΑΛΕΙΑΣ")
        print("-" * 40)
        print(f"Εφαρμογή: {app_name}")
        print(f"Επίπεδο Κινδύνου: {risk_level} ({risk_score} πόντοι)")
        print(f"Σύνολο Αδειών: {len(all_permissions)}")
        print(f"Επικίνδυνες Άδειες: {len(dangerous_perms)}")
        print(f"Trackers που βρέθηκαν: {len(trackers)}")
        
        if dangerous_perms:
            print(f"\n🔴 ΕΠΙΚΙΝΔΥΝΕΣ ΑΔΕΙΕΣ:")
            for perm in dangerous_perms:
                risk_color = "🔴" if perm['risk'] == 'critical' else "🟡" if perm['risk'] == 'high' else "🟠"
                print(f"  {risk_color} {perm['name']}")
                print(f"     Περιγραφή: {perm['description']}")
                print(f"     Απειλή: {perm['threat']}")
        
        if trackers:
            print(f"\n📊 ΒΙΒΛΙΟΘΗΚΕΣ ΠΑΡΑΚΟΛΟΥΘΗΣΗΣ:")
            for tracker in trackers:
                impact_icon = "🔴" if tracker['privacy_impact'] == 'high' else "🟡"
                print(f"  {impact_icon} {tracker['name']} ({tracker['category']})")
        
        if not dangerous_perms and not trackers:
            print(f"\n✅ Δεν εντοπίστηκαν σημαντικά προβλήματα ασφαλείας!")
        
        print("\n" + "="*60)
        
        # Αποθήκευση αναφοράς
        self.save_analysis_report(app_name, apk_path, dangerous_perms, trackers, risk_level, risk_score)
    
    def save_analysis_report(self, app_name, apk_path, dangerous_perms, trackers, risk_level, risk_score):
        """Αποθήκευση αναφοράς ανάλυσης σε αρχείο"""
        try:
            base_storage = os.path.join(os.path.expanduser('~'), 'storage', 'shared')
            reports_dir = os.path.join(base_storage, 'Download', "Αναφορές_Ασφαλείας_Εφαρμογών")
            os.makedirs(reports_dir, exist_ok=True)
            
            safe_name = "".join(c for c in app_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            report_file = os.path.join(reports_dir, f"{safe_name}_αναφορά_ασφαλείας.txt")
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("           ΑΝΑΦΟΡΑ ΑΝΑΛΥΣΗΣ ΑΣΦΑΛΕΙΑΣ ΕΦΑΡΜΟΓΗΣ\n")
                f.write("="*60 + "\n\n")
                
                f.write(f"Όνομα Εφαρμογής: {app_name}\n")
                f.write(f"Διαδρομή APK: {apk_path}\n")
                f.write(f"Ημερομηνία Ανάλυσης: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Επίπεδο Κινδύνου: {risk_level}\n")
                f.write(f"Βαθμολογία Κινδύνου: {risk_score}\n\n")
                
                if dangerous_perms:
                    f.write("ΕΠΙΚΙΝΔΥΝΕΣ ΑΔΕΙΕΣ:\n")
                    f.write("-" * 40 + "\n")
                    for perm in dangerous_perms:
                        risk_gr = perm['risk'].upper()
                        if risk_gr == "CRITICAL": risk_gr = "ΚΡΙΣΙΜΟΣ"
                        elif risk_gr == "HIGH": risk_gr = "ΥΨΗΛΟΣ"
                        elif risk_gr == "MEDIUM": risk_gr = "ΜΕΤΡΙΟΣ"
                        
                        f.write(f"• {perm['name']}\n")
                        f.write(f"  Κίνδυνος: {risk_gr} | {perm['description']}\n")
                        f.write(f"  Απειλή: {perm['threat']}\n\n")
                
                if trackers:
                    f.write("ΒΙΒΛΙΟΘΗΚΕΣ ΠΑΡΑΚΟΛΟΥΘΗΣΗΣ:\n")
                    f.write("-" * 40 + "\n")
                    for tracker in trackers:
                        impact_gr = "ΥΨΗΛΟΣ" if tracker['privacy_impact'] == 'high' else "ΜΕΤΡΙΟΣ"
                        f.write(f"• {tracker['name']}\n")
                        f.write(f"  Κατηγορία: {tracker['category']}\n")
                        f.write(f"  Αντίκτυπος Απορρήτου: {impact_gr}\n\n")
                
                f.write("="*60 + "\n")
                f.write("Η αναφορά δημιουργήθηκε από το Android App Launcher\n")
                f.write("="*60 + "\n")
            
            print(f"📄 Η αναφορά αποθηκεύτηκε: {report_file}")
            
        except Exception as e:
            print(f"❌ Σφάλμα κατά την αποθήκευση της αναφοράς: {e}")

def analyze_app_permissions_option(apk_path, package_name, app_label):
    """
    Διαχείριση της επιλογής App Perm Inspector
    """
    inspector = SimpleAppPermInspector()
    inspector.analyze_app_permissions(apk_path, app_label)

def main():
    package_map = get_installed_apps()
    if not package_map:
        print("Δεν βρέθηκαν εφαρμογές. Ελέγξτε τις άδειές σας ή το περιβάλλον.")
        return

    launchable_map = get_launchable_packages()
    if not launchable_map:
        print("Δεν βρέθηκαν εκκινήσιμες εφαρμογές.")
        return

    filtered_map = {pkg: apk for pkg, apk in package_map.items() if pkg in launchable_map}
    if not filtered_map:
        print("Δεν βρέθηκαν εκκινήσιμες εφαρμογές στις εγκατεστημένες εφαρμογές.")
        return

    # Χρήση ThreadPoolExecutor για παράλληλη εξαγωγή των ετικετών εφαρμογών
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
                print(f"Σφάλμα κατά την ανάκτηση της ετικέτας για {pkg}: {exc}")
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

    # ΕΝΗΜΕΡΩΜΕΝΕΣ ΕΠΙΛΟΓΕΣ: Προστέθηκε η επιλογή "Επιθεωρητής Αδειών"
    options = ["Εκκίνηση", "Πληροφορίες Εφαρμογής", "Απεγκατάσταση", "Εξαγωγή APK", "Επιθεωρητής Αδειών"]
    chosen_option = select_option(options, f"Επιλέχθηκε: '{selected_label}'. Διαλέξτε μια ενέργεια:")
    if not chosen_option:
        print("Δεν επιλέχθηκε καμία ενέργεια.")
        return

    if chosen_option == "Εκκίνηση":
        component = launchable_map.get(selected_package)
        if component:
            print(f"Εκκίνηση '{selected_label}' ({selected_package})...")
            os.system(f"am start -n {component} > /dev/null 2>&1")
        else:
            print("Το στοιχείο εκκίνησης (component) δεν βρέθηκε για την επιλεγμένη εφαρμογή.")
            
    elif chosen_option == "Πληροφορίες Εφαρμογής":
        print(f"Άνοιγμα Πληροφοριών Εφαρμογής για '{selected_label}' ({selected_package})...")
        os.system(f"am start -a android.settings.APPLICATION_DETAILS_SETTINGS -d package:{selected_package} > /dev/null 2>&1")
        
    elif chosen_option == "Απεγκατάσταση":
        print(f"Απεγκατάσταση '{selected_label}' ({selected_package}) μέσω της μεθόδου συστήματος...")
        os.system(f"am start -a android.intent.action.DELETE -d package:{selected_package} > /dev/null 2>&1")
        
    elif chosen_option == "Εξαγωγή APK":
        apk_path_on_device = package_map.get(selected_package)
        if apk_path_on_device:
            # Κατασκευή της διαδρομής του καταλόγου προορισμού
            base_storage = os.path.join(os.path.expanduser('~'), 'storage', 'shared')
            downloads_dir = os.path.join(base_storage, 'Download')
            target_dir = os.path.join(downloads_dir, "Εξαγμένα_APK")
            destination_file = os.path.join(target_dir, f"{selected_package}.apk")

            print(f"Εξασφάλιση ύπαρξης καταλόγου προορισμού: '{target_dir}'...")
            
            # Δημιουργία του καταλόγου προορισμού αναδρομικά αν δεν υπάρχει
            if os.system(f"mkdir -p \"{target_dir}\"") != 0:
                 print("Σφάλμα: Δεν ήταν δυνατή η δημιουργία του καταλόγου προορισμού. Ελέγξτε τις άδειες αποθήκευσης του Termux ('termux-setup-storage').")
                 return
            
            print(f"Αντιγραφή APK από '{apk_path_on_device}' σε '{destination_file}'...")
            
            try:
                # Χρήση της εγγενούς εντολής 'cp' (copy) του Android
                copy_cmd = ["cp", apk_path_on_device, destination_file]
                result = subprocess.run(copy_cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"Επιτυχής εξαγωγή APK στο {destination_file}")
                else:
                    print(f"Σφάλμα κατά την εξαγωγή του APK. Η εντολή αντιγραφής απέτυχε με κωδικό εξόδου {result.returncode}.")
                    if result.stderr:
                        print(f"Λεπτομέρειες σφάλματος: {result.stderr.strip()}")
            except FileNotFoundError:
                print("Σφάλμα: Η εντολή 'cp' δεν βρέθηκε. Αυτό δεν θα έπρεπε να συμβαίνει σε ένα τυπικό shell του Termux.")
            except Exception as e:
                print(f"Προέκυψε ένα μη αναμενόμενο σφάλμα κατά την αντιγραφή: {e}")
        else:
            print("Η διαδρομή APK δεν βρέθηκε για την επιλεγμένη εφαρμογή.")

    elif chosen_option == "Επιθεωρητής Αδειών":
        apk_path_on_device = package_map.get(selected_package)
        if apk_path_on_device:
            analyze_app_permissions_option(apk_path_on_device, selected_package, selected_label)
        else:
            print("Η διαδρομή APK δεν βρέθηκε για την επιλεγμένη εφαρμογή.")

    else:
        print("Δεν επιλέχθηκε έγκυρη ενέργεια.")

    # Μετά την εκτέλεση της επιλεγμένης ενέργειας, εκτέλεση του Settings.py
    print("\nΕκκίνηση ρυθμίσεων...")
    os.system(f"{sys.executable} Settings.py")

if __name__ == "__main__":
    main()