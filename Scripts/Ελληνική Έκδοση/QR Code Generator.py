[file name]: QR Code Generator Greek.py
[file content begin]
import os
import re
import subprocess
import sys

# --- Συνάρτηση Εγκατάστασης (Ίδια με πριν) ---
def install_and_import(package):
    """
    Ελέγχει εάν ένα πακέτο είναι εγκατεστημένο και το εγκαθιστά αν λείπει.
    Το 'qrcode[pil]' εγκαθιστά τόσο το qrcode όσο και το Pillow (PIL) για δημιουργία εικόνων.
    """
    try:
        __import__(package)
        print(f"✅ Το απαιτούμενο πακέτο '{package}' είναι ήδη εγκατεστημένο.")
    except ImportError:
        print(f"📦 Το πακέτο '{package}' δεν βρέθηκε. Γίνεται εγκατάσταση τώρα...")
        try:
            if package == 'qrcode':
                # Εγκατάσταση qrcode με εξάρτηση pil για αποθήκευση εικόνων
                subprocess.check_call([sys.executable, "-m", "pip", "install", "qrcode[pil]"])
            else:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            
            __import__(package)
            print(f"✅ Το πακέτο '{package}' εγκαταστάθηκε με επιτυχία.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Αποτυχία εγκατάστασης του πακέτου '{package}'. Σφάλμα: {e}")
            print("Παρακαλούμε βεβαιωθείτε ότι το 'pip' είναι εγκατεστημένο και λειτουργεί στο Termux.")
            sys.exit(1)

install_and_import('qrcode')
import qrcode 

# ----------------------------------------------------------------------
# --- Κύρια Συνάρτηση Δημιουργίας (Ενημερωμένη Διαδρομή) ---
# ----------------------------------------------------------------------
def generate_qr_for_link():
    """Δημιουργεί μια εικόνα QR code και την αποθηκεύει σε ένα φάκελο 'QR Codes' 
    μέσα στον φάκελο Λήψεις (Downloads) του τηλεφώνου."""
    
    # 1. Ορισμός της σωστής διαδρομής προς τον φάκελο Λήψεις (Downloads)
    # Το ~/storage/downloads/ είναι η διαδρομή Termux για τον φάκελο Λήψεις του τηλεφώνου
    downloads_path = os.path.expanduser("~/storage/downloads/")
    folder_name = "QR Codes"
    # Ο τελικός φάκελος εξόδου θα είναι κάτι όπως: /storage/emulated/0/Download/QR Codes/
    output_dir = os.path.join(downloads_path, folder_name)
    
    data = input("Εισάγετε το σύνδεσμο (URL) για κωδικοποίηση: ")
    
    # 2. Δημιουργία του φακέλου αν δεν υπάρχει
    print(f"Ελέγχεται ο φάκελος εξόδου: {output_dir}")
    try:
        os.makedirs(output_dir, exist_ok=True)
        print("📁 Ο φάκελος επαληθεύτηκε/δημιουργήθηκε.")
    except Exception as e:
        print(f"❌ Σφάλμα δημιουργίας φακέλου. Έχετε εκτελέσει το 'termux-setup-storage'; Σφάλμα: {e}")
        return

    # 3. Καθαρισμός του συνδέσμου για χρήση ως όνομα αρχείου
    sanitized_link = re.sub(r'https?://', '', data).rstrip('/')
    sanitized_link = re.sub(r'[^\w.-]', '_', sanitized_link)
    
    file_name = f"{sanitized_link}.png"
    output_path = os.path.join(output_dir, file_name)
    
    # --- Δημιουργία QR Code ---
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 4. Αποθήκευση της εικόνας QR code
    try:
        img.save(output_path)
        print(f"\n✨ Επιτυχία! Δημιουργήθηκε QR Code για το '{data}'")
        print(f"Αποθηκεύτηκε σε: **Downloads/QR Codes/{file_name}**")
        print(f"Πλήρης διαδρομή: {output_path}")
    except Exception as e:
        print(f"\n❌ Σφάλμα αποθήκευσης αρχείου: {e}")

if __name__ == "__main__":
    generate_qr_for_link()
[file content end]