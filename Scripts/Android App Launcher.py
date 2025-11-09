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

class SimpleAppPermInspector:
    """
    Simplified version of App Perm Inspector for integration
    """
    def __init__(self):
        self.dangerous_permissions = self.load_dangerous_permissions()
        self.tracker_databases = self.load_tracker_databases()
    
    def load_dangerous_permissions(self):
        """Load dangerous Android permissions database"""
        dangerous_perms = {
            "ACCESS_FINE_LOCATION": {"risk": "high", "description": "Access precise location (GPS)", "threat": "Can track your exact location"},
            "ACCESS_COARSE_LOCATION": {"risk": "medium", "description": "Access approximate location", "threat": "Can track your general area"},
            "CAMERA": {"risk": "high", "description": "Access device camera", "threat": "Can take pictures/video without consent"},
            "RECORD_AUDIO": {"risk": "high", "description": "Record audio", "threat": "Can record conversations"},
            "READ_CONTACTS": {"risk": "high", "description": "Read contact list", "threat": "Can access all your contacts"},
            "WRITE_CONTACTS": {"risk": "medium", "description": "Modify contacts", "threat": "Can alter your contact data"},
            "SEND_SMS": {"risk": "critical", "description": "Send SMS messages", "threat": "Can send premium rate SMS"},
            "READ_SMS": {"risk": "critical", "description": "Read SMS messages", "threat": "Can read all your messages"},
            "CALL_PHONE": {"risk": "critical", "description": "Make phone calls", "threat": "Can make calls without consent"},
            "READ_PHONE_STATE": {"risk": "high", "description": "Access phone information", "threat": "Can get phone number, IMEI, etc."},
            "READ_EXTERNAL_STORAGE": {"risk": "medium", "description": "Read external storage", "threat": "Can access your files, photos, documents"},
            "WRITE_EXTERNAL_STORAGE": {"risk": "medium", "description": "Write to external storage", "threat": "Can modify or delete your files"},
            "ACCESS_BACKGROUND_LOCATION": {"risk": "critical", "description": "Access location in background", "threat": "Can track location even when app not in use"},
            "BODY_SENSORS": {"risk": "high", "description": "Access health sensors", "threat": "Can access heart rate, step count, etc."}
        }
        return dangerous_perms
    
    def load_tracker_databases(self):
        """Load known tracker libraries"""
        trackers = {
            "Google Analytics": {"signatures": ["com.google.analytics", "com.google.android.gms.analytics"], "category": "Analytics", "privacy_impact": "high"},
            "Facebook SDK": {"signatures": ["com.facebook", "com.facebook.ads"], "category": "Advertising", "privacy_impact": "high"},
            "Firebase Analytics": {"signatures": ["com.google.firebase.analytics"], "category": "Analytics", "privacy_impact": "medium"},
            "AdMob": {"signatures": ["com.google.android.gms.ads"], "category": "Advertising", "privacy_impact": "high"},
            "Flurry": {"signatures": ["com.flurry.android"], "category": "Analytics", "privacy_impact": "medium"},
            "AppsFlyer": {"signatures": ["com.appsflyer"], "category": "Analytics", "privacy_impact": "high"}
        }
        return trackers
    
    def extract_permissions_basic(self, apk_path):
        """Extract permissions from APK using basic analysis"""
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
            print(f"❌ Permission extraction failed: {e}")
            return []
    
    def detect_trackers(self, apk_path):
        """Detect tracking libraries in APK"""
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
            print(f"❌ Tracker detection error: {e}")
            return []
    
    def analyze_app_permissions(self, apk_path, app_name):
        """Main analysis function"""
        print(f"\n🔍 Analyzing: {app_name}")
        print("="*60)
        
        # Extract permissions
        all_permissions = self.extract_permissions_basic(apk_path)
        
        # Categorize permissions
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
        
        # Detect trackers
        trackers = self.detect_trackers(apk_path)
        
        # Calculate risk score
        risk_score = 0
        for perm in dangerous_perms:
            if perm['risk'] == 'critical': risk_score += 10
            elif perm['risk'] == 'high': risk_score += 7
            elif perm['risk'] == 'medium': risk_score += 4
        
        risk_level = "HIGH" if risk_score >= 20 else "MEDIUM" if risk_score >= 10 else "LOW"
        
        # Display results
        print(f"\n📊 SECURITY ANALYSIS RESULTS")
        print("-" * 40)
        print(f"App: {app_name}")
        print(f"Risk Level: {risk_level} ({risk_score} points)")
        print(f"Total Permissions: {len(all_permissions)}")
        print(f"Dangerous Permissions: {len(dangerous_perms)}")
        print(f"Trackers Found: {len(trackers)}")
        
        if dangerous_perms:
            print(f"\n🔴 DANGEROUS PERMISSIONS:")
            for perm in dangerous_perms:
                risk_color = "🔴" if perm['risk'] == 'critical' else "🟡" if perm['risk'] == 'high' else "🟠"
                print(f"  {risk_color} {perm['name']}")
                print(f"     Description: {perm['description']}")
                print(f"     Threat: {perm['threat']}")
        
        if trackers:
            print(f"\n📊 TRACKING LIBRARIES:")
            for tracker in trackers:
                impact_icon = "🔴" if tracker['privacy_impact'] == 'high' else "🟡"
                print(f"  {impact_icon} {tracker['name']} ({tracker['category']})")
        
        if not dangerous_perms and not trackers:
            print(f"\n✅ No major security issues detected!")
        
        print("\n" + "="*60)
        
        # Save report
        self.save_analysis_report(app_name, apk_path, dangerous_perms, trackers, risk_level, risk_score)
    
    def save_analysis_report(self, app_name, apk_path, dangerous_perms, trackers, risk_level, risk_score):
        """Save analysis report to file"""
        try:
            base_storage = os.path.join(os.path.expanduser('~'), 'storage', 'shared')
            reports_dir = os.path.join(base_storage, 'Download', "App_Security_Reports")
            os.makedirs(reports_dir, exist_ok=True)
            
            safe_name = "".join(c for c in app_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            report_file = os.path.join(reports_dir, f"{safe_name}_security_report.txt")
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("           APP SECURITY ANALYSIS REPORT\n")
                f.write("="*60 + "\n\n")
                
                f.write(f"App Name: {app_name}\n")
                f.write(f"APK Path: {apk_path}\n")
                f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Risk Level: {risk_level}\n")
                f.write(f"Risk Score: {risk_score}\n\n")
                
                if dangerous_perms:
                    f.write("DANGEROUS PERMISSIONS:\n")
                    f.write("-" * 40 + "\n")
                    for perm in dangerous_perms:
                        f.write(f"• {perm['name']}\n")
                        f.write(f"  Risk: {perm['risk'].upper()} | {perm['description']}\n")
                        f.write(f"  Threat: {perm['threat']}\n\n")
                
                if trackers:
                    f.write("TRACKING LIBRARIES:\n")
                    f.write("-" * 40 + "\n")
                    for tracker in trackers:
                        f.write(f"• {tracker['name']}\n")
                        f.write(f"  Category: {tracker['category']}\n")
                        f.write(f"  Privacy Impact: {tracker['privacy_impact'].upper()}\n\n")
                
                f.write("="*60 + "\n")
                f.write("Report generated by Android App Launcher\n")
                f.write("="*60 + "\n")
            
            print(f"📄 Report saved: {report_file}")
            
        except Exception as e:
            print(f"❌ Error saving report: {e}")

def analyze_app_permissions_option(apk_path, package_name, app_label):
    """
    Handle the App Perm Inspector option
    """
    inspector = SimpleAppPermInspector()
    inspector.analyze_app_permissions(apk_path, app_label)

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

    # UPDATED OPTIONS: Added "App Perm Inspector" option
    options = ["Launch", "App Info", "Uninstall", "Extract APK", "App Perm Inspector"]
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
            # Construct the target directory path
            base_storage = os.path.join(os.path.expanduser('~'), 'storage', 'shared')
            downloads_dir = os.path.join(base_storage, 'Download')
            target_dir = os.path.join(downloads_dir, "Extracted APK's")
            destination_file = os.path.join(target_dir, f"{selected_package}.apk")

            print(f"Ensuring destination directory exists: '{target_dir}'...")
            
            # Create the destination directory recursively if it doesn't exist
            if os.system(f"mkdir -p \"{target_dir}\"") != 0:
                 print("Error: Could not create the destination directory. Check Termux storage permissions ('termux-setup-storage').")
                 return
            
            print(f"Copying APK from '{apk_path_on_device}' to '{destination_file}'...")
            
            try:
                # Use native Android 'cp' (copy) command
                copy_cmd = ["cp", apk_path_on_device, destination_file]
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

    elif chosen_option == "App Perm Inspector":
        apk_path_on_device = package_map.get(selected_package)
        if apk_path_on_device:
            analyze_app_permissions_option(apk_path_on_device, selected_package, selected_label)
        else:
            print("APK path not found for the selected app.")

    else:
        print("No valid option selected.")

    # After performing the selected action, run Settings.py
    print("\nLaunching settings...")
    os.system(f"{sys.executable} Settings.py")

if __name__ == "__main__":
    main()