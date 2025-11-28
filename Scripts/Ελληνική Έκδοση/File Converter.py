#!/usr/bin/env python

"""
Ένας τυπικός μετατροπέας αρχείων (CLI) για το Termux.
Έκδοση 3.1 CLI: Οργανώνει όλους τους φακέλους σε έναν κύριο κατάλογο "File Converter".

Αυτό το σενάριο θα:
1. Ελέγξει και θα εγκαταστήσει τις απαιτούμενες βιβλιοθήκες Python.
2. Ελέγξει για εξωτερικά εκτελέσιμα (ffmpeg, unrar, cairo).
3. Δημιουργήσει έναν φάκελο "File Converter" στα Λήψεις (Downloads),
   ο οποίος περιέχει 40 υπο-φακέλους οργάνωσης.
4. Παρέχει ένα τυπικό περιβάλλον CLI για πλοήγηση με χρήση αριθμητικών επιλογών.
5. Υποστηρίζει πολλές μετατροπές εγγράφων, εικόνων, Ήχου/Βίντεο και δεδομένων.

ΚΡΙΣΙΜΗ ΕΓΚΑΤΑΣΤΑΣΗ (στο Termux):
pkg install ffmpeg unrar libcairo libgirepository libjpeg-turbo libpng
"""

import sys
import os
import subprocess
import importlib.util
import time
import traceback
import zipfile
import tarfile
import csv
import json
import gzip
import shutil
from contextlib import redirect_stderr, redirect_stdout

# --- 1. SETUP & CONFIGURATION ---

# (14) Python libraries to auto-install
REQUIRED_MODULES = {
    "Pillow": "Pillow",         # Εικόνες
    "reportlab": "reportlab",   # Δημιουργία PDF
    "docx": "python-docx",    # Έγγραφα Word
    "odf": "odfpy",           # Έγγραφα OpenOffice
    "bs4": "beautifulsoup4",  # Ανάλυση HTML/XML
    "markdown": "Markdown",     # Ανάλυση Markdown
    "lxml": "lxml",           # Ανάλυση XML/HTML
    "cairosvg": "cairosvg",     # Μετατροπή SVG
    "psd_tools": "psd-tools",   # Ανάγνωση PSD
    "striprtf": "striprtf",     # Ανάγνωση RTF
    "EbookLib": "EbookLib",     # Ανάγνωση EPUB
    "pptx": "python-pptx",    # Ανάγνωση PowerPoint
    "rarfile": "rarfile",       # Εξαγωγή RAR
    "py7zr": "py7zr"          # Εξαγωγή 7-Zip
}

# (40) Folders to create
FOLDER_NAMES = [
    # Images (10)
    "JPG", "PNG", "WEBP", "BMP", "TIFF", "GIF", "ICO", "TGA", "SVG", "PSD",
    # Documents (12)
    "PDF", "TXT", "DOCX", "ODT", "HTML", "MD", "CSV", "RTF", "EPUB", "JSON", "XML", "PPTX",
    # Archives (5)
    "ZIP", "TAR", "RAR", "7Z", "GZ",
    # Audio (7)
    "MP3", "WAV", "OGG", "FLAC", "M4A", "AAC", "WMA",
    # Video (6)
    "MP4", "MKV", "AVI", "MOV", "WMV", "FLV"
]

# Helper lists for logic (ΔΕΝ χρειάζονται μετάφραση)
IMAGE_FOLDERS = ["JPG", "PNG", "WEBP", "BMP", "TIFF", "GIF", "ICO", "TGA", "SVG", "PSD"]
IMAGE_EXTS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif', '.ico', '.tga']
VECTOR_IMAGE_EXTS = ['.svg']
LAYERED_IMAGE_EXTS = ['.psd']
AV_EXTS = ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac', '.wma', '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv']
ARCHIVE_EXTS = ['.zip', '.tar', '.gz', '.bz2', '.rar', '.7z']
TEXT_DOC_EXTS = ['.txt', '.docx', '.odt', '.html', '.md', '.csv', '.rtf', '.epub', '.json', '.xml', '.pptx', '.svg']
DATA_EXTS = ['.csv', '.json', '.xml']

# Paths
STORAGE_PATH = "/storage/emulated/0"
DOWNLOAD_PATH = os.path.join(STORAGE_PATH, "Download")
BASE_CONVERTER_PATH = os.path.join(DOWNLOAD_PATH, "File Converter")

# Global flags for external binaries
HAS_FFMPEG = False
HAS_UNRAR = False
HAS_CAIRO = False

# --- 2. PRE-CURSES SETUP FUNCTIONS (Standard Print) ---

def clear_screen_standard():
    os.system('clear')

def check_and_install_dependencies():
    """Checks and installs required Python modules."""
    print("--- Έλεγχος Απαιτούμενων Βιβλιοθηκών Python (14) ---")
    all_installed = True
    for module_name, package_name in REQUIRED_MODULES.items():
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            all_installed = False
            print(f"Εγκατάσταση '{package_name}'...")
            try:
                with open(os.devnull, 'w') as devnull:
                    with redirect_stdout(devnull), redirect_stderr(devnull):
                        subprocess.run([sys.executable, "-m", "pip", "install", package_name], check=True)
                print(f"Εγκαταστάθηκε επιτυχώς το '{package_name}'.")
            except Exception:
                print(f"ΣΦΑΛΜΑ: Απέτυχε η εγκατάσταση του '{package_name}'.")
                print(f"Παρακαλώ εγκαταστήστε το χειροκίνητα: pip install {package_name}")
                sys.exit(1)
        # else:
            # print(f"Η βιβλιοθήκη '{package_name}' είναι ήδη εγκατεστημένη.")
    
    if all_installed:
        print("Όλες οι βιβλιοθήκες Python είναι παρούσες.\n")
    else:
        print("Όλες οι απαιτούμενες βιβλιοθήκες έχουν εγκατασταθεί.\n")
    time.sleep(0.5)

def check_external_bins():
    """Checks for 'ffmpeg', 'unrar', and 'cairo'."""
    global HAS_FFMPEG, HAS_UNRAR, HAS_CAIRO
    print("--- Έλεγχος Εξωτερικών Εκτελέσιμων ---")
    
    # Check ffmpeg
    try:
        with open(os.devnull, 'w') as devnull:
            subprocess.run(["ffmpeg", "-version"], check=True, stdout=devnull, stderr=devnull)
        print("Βρέθηκε το 'ffmpeg'. Οι μετατροπές Ήχου/Βίντεο είναι ΕΝΕΡΓΕΣ.")
        HAS_FFMPEG = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Το 'ffmpeg' δεν βρέθηκε. Οι μετατροπές Ήχου/Βίντεο είναι ΑΝΕΝΕΡΓΕΣ.")
        print("  Για ενεργοποίηση, εκτελέστε: pkg install ffmpeg")
        HAS_FFMPEG = False

    # Check unrar
    try:
        with open(os.devnull, 'w') as devnull:
            subprocess.run(["unrar"], check=True, stdout=devnull, stderr=devnull)
        print("Βρέθηκε το 'unrar'. Η εξαγωγή RAR είναι ΕΝΕΡΓΗ.")
        HAS_UNRAR = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Το 'unrar' δεν βρέθηκε. Η εξαγωγή RAR είναι ΑΝΕΝΕΡΓΗ.")
        print("  Για ενεργοποίηση, εκτελέστε: pkg install unrar")
        HAS_UNRAR = False
        
    # Check cairo (for SVG)
    if importlib.util.find_spec("cairosvg") is not None:
        print("Βρέθηκε το 'cairosvg'. Οι μετατροπές SVG είναι ΕΝΕΡΓΕΣ.")
        HAS_CAIRO = True
    else:
        print("ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Η βιβλιοθήκη Python 'cairosvg' δεν βρέθηκε. Η μετατροπή SVG είναι ΑΝΕΝΕΡΓΗ.")
        print("  Το σενάριο προσπάθησε να την εγκαταστήσει, αλλά μπορεί να απέτυχε.")
        print("  Μπορεί επίσης να χρειαστείτε: pkg install libcairo libgirepository")
        HAS_CAIRO = False
        
    print("\n")
    time.sleep(0.5)


def check_storage_access():
    print("--- Έλεγχος Πρόσβασης Αποθήκευσης ---")
    if not os.path.exists(DOWNLOAD_PATH):
        print(f"ΣΦΑΛΜΑ: Δεν είναι δυνατή η πρόσβαση στον εσωτερικό χώρο αποθήκευσης στη διαδρομή '{DOWNLOAD_PATH}'.")
        print("Παρακαλώ εκτελέστε 'termux-setup-storage' στο τερματικό Termux,")
        print("παραχωρήστε την άδεια, και στη συνέχεια εκτελέστε ξανά αυτό το σενάριο.")
        sys.exit(1)
    print("Η πρόσβαση αποθήκευσης επιβεβαιώθηκε.\n")
    time.sleep(0.5)

def setup_folders():
    # --- MODIFIED: Creates the main "File Converter" directory first ---
    print(f"--- Ρύθμιση Φακέλων Οργάνωσης ---")
    print(f"Τοποθεσία: {BASE_CONVERTER_PATH}")
    try:
        # 1. Create the main parent directory
        os.makedirs(BASE_CONVERTER_PATH, exist_ok=True)
        # 2. Create all 40 sub-folders inside it
        for folder in FOLDER_NAMES:
            os.makedirs(os.path.join(BASE_CONVERTER_PATH, folder), exist_ok=True)
        print(f"Δημιουργήθηκαν/επιβεβαιώθηκαν επιτυχώς {len(FOLDER_NAMES)} υπο-φάκελοι.\n")
    except Exception as e:
        print(f"ΣΦΑΛΜΑ: Δεν ήταν δυνατή η δημιουργία φακέλων: {e}")
        sys.exit(1)
    time.sleep(0.5)

# --- 3. IMPORTS (Post-Installation) ---
try:
    from PIL import Image
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from docx import Document
    from odf.opendocument import load as odf_load
    from odf.text import P as odf_P
    from bs4 import BeautifulSoup
    import markdown
    import lxml
    import cairosvg
    from psd_tools import PSDImage
    from striprtf.striprtf import rtf_to_text
    from ebooklib import epub, ITEM_DOCUMENT
    import pptx
    import rarfile
    import py7zr
except ImportError as e:
    # This block is for robustness, but dependency checks should catch this first.
    print(f"ΚΡΙΣΙΜΟ ΣΦΑΛΜΑ: Απέτυχε η εισαγωγή βιβλιοθήκης: {e}")
    print("Βεβαιωθείτε ότι όλες οι εξαρτήσεις είναι εγκατεστημένες (δείτε τα αρχικά μηνύματα).")
    sys.exit(1)

# --- 4. CORE CONVERSION LOGIC (ΔΕΝ χρειάζονται μετάφραση) ---
# (Διατηρείται ο κώδικας της λογικής μετατροπής ίδιος)
# ... (all conversion handler functions remain in English) ...
def get_text_from_file(input_path, in_ext):
    """Helper to extract raw text from various document types."""
    text_lines = []
    try:
        if in_ext == '.txt':
            with open(input_path, 'r', encoding='utf-8') as f:
                text_lines = f.readlines()
        elif in_ext == '.docx':
            doc = Document(input_path)
            text_lines = [para.text + '\n' for para in doc.paragraphs]
        elif in_ext == '.odt':
            doc = odf_load(input_path)
            for para in doc.getElementsByType(odf_P):
                text_lines.append(str(para) + '\n')
        elif in_ext in ['.html', '.xml', '.svg']:
            with open(input_path, 'r', encoding='utf-8') as f:
                parser = 'lxml' if in_ext != '.html' else 'html.parser'
                soup = BeautifulSoup(f, parser)
                text_lines = [line + '\n' for line in soup.get_text().splitlines()]
        elif in_ext == '.md':
            with open(input_path, 'r', encoding='utf-8') as f:
                html = markdown.markdown(f.read())
                soup = BeautifulSoup(html, 'html.parser')
                text_lines = [line + '\n' for line in soup.get_text().splitlines()]
        elif in_ext == '.csv':
            with open(input_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                text_lines = [','.join(row) + '\n' for row in reader]
        elif in_ext == '.json':
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                text_lines = [json.dumps(data, indent=2)]
        elif in_ext == '.rtf':
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            text_lines = [rtf_to_text(content)]
        elif in_ext == '.epub':
            book = epub.read_epub(input_path)
            for item in book.get_items():
                if item.get_type() == ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text_lines.append(soup.get_text() + '\n\n') # Add space between chapters
        elif in_ext == '.pptx':
            prs = pptx.Presentation(input_path)
            for slide in prs.slides:
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        text_lines.append(shape.text + '\n')
    except Exception as e:
        raise Exception(f"Αποτυχία εξαγωγής κειμένου: {e}")
    return text_lines

def write_text_to_pdf(text_lines, output_path):
    # (Unchanged)
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    margin_x, margin_y = 0.75 * inch, 1 * inch
    text_object = c.beginText(margin_x, height - margin_y)
    text_object.setFont("Helvetica", 10)
    line_height, y = 12, height - margin_y
    for line in text_lines:
        for sub_line in line.split('\n'): # Handle multi-line strings
            if y < margin_y:
                c.drawText(text_object)
                c.showPage()
                text_object = c.beginText(margin_x, height - margin_y)
                text_object.setFont("Helvetica", 10)
                y = height - margin_y
            text_object.textLine(sub_line.strip('\r'))
            y -= line_height
    c.drawText(text_object)
    c.save()

def handle_image_conversion(in_path, out_path):
    # (Pillow handler, unchanged)
    with Image.open(in_path) as img:
        if out_path.lower().endswith(('.jpg', '.jpeg')):
            if img.mode == 'RGBA':
                img = img.convert('RGB')
        img.save(out_path)

def handle_svg_conversion(in_path, out_path):
    """Converts SVG to PNG or PDF."""
    if not HAS_CAIRO:
        raise Exception("Οι βιβλιοθήκες Cairo/SVG δεν είναι εγκατεστημένες.")
    out_ext = os.path.splitext(out_path)[1].lower()
    if out_ext == '.png':
        cairosvg.svg2png(url=in_path, write_to=out_path)
    elif out_ext == '.pdf':
        cairosvg.svg2pdf(url=in_path, write_to=out_path)
    else:
        raise Exception(f"Η μετατροπή SVG σε {out_ext} δεν υποστηρίζεται.")

def handle_psd_conversion(in_path, out_path):
    """Converts PSD composite to a flat image."""
    psd = PSDImage.open(in_path)
    composite_image = psd.composite()
    composite_image.save(out_path)

def handle_av_conversion(in_path, out_path):
    # (Unchanged - Note: curses.endwin() is removed)
    if not HAS_FFMPEG:
        raise Exception("Το 'ffmpeg' δεν βρέθηκε. Η μετατροπή Ήχου/Βίντεο είναι απενεργοποιημένη.")
    command = ['ffmpeg', '-i', in_path, '-y', out_path]
    print("--- Εκτέλεση ffmpeg ---")
    print(f"Εντολή: {' '.join(command)}")
    print("Αυτό μπορεί να πάρει λίγο χρόνο...")
    try:
        with open(os.devnull, 'w') as devnull:
            subprocess.run(command, check=True, stdout=devnull, stderr=subprocess.STDOUT)
        print("Η μετατροπή ffmpeg ολοκληρώθηκε επιτυχώς.")
    except Exception as e:
        print(f"ΣΦΑΛΜΑ ffmpeg: {e}")
        raise Exception(f"Η μετατροπή ffmpeg απέτυχε. {e}")
    finally:
        input("Πατήστε Enter για να συνεχίσετε...")

def handle_extraction(in_path, out_folder_path, in_ext):
    """Extracts various archive types."""
    base_name = os.path.splitext(os.path.basename(in_path))[0]
    extract_path = os.path.join(out_folder_path, base_name)
    os.makedirs(extract_path, exist_ok=True)
    
    if in_ext == '.zip':
        with zipfile.ZipFile(in_path, 'r') as zf:
            zf.extractall(extract_path)
    elif in_ext in ['.tar', '.bz2']:
        with tarfile.open(in_path, 'r:*') as tf:
            tf.extractall(extract_path)
    elif in_ext == '.gz':
        if not in_path.endswith('.tar.gz'): # Single file gzip
             out_filename = os.path.splitext(os.path.basename(in_path))[0]
             out_path = os.path.join(out_folder_path, out_filename) # Extract to folder, not subfolder
             with gzip.open(in_path, 'rb') as f_in:
                 with open(out_path, 'wb') as f_out:
                     shutil.copyfileobj(f_in, f_out)
             return f"Αποσυμπιέστηκε σε: {out_path}" # Return different message
        else: # .tar.gz
            with tarfile.open(in_path, 'r:gz') as tf:
                tf.extractall(extract_path)
    elif in_ext == '.rar':
        if not HAS_UNRAR:
            raise Exception("Δεν βρέθηκε το εκτελέσιμο 'unrar'.")
        with rarfile.RarFile(in_path) as rf:
            rf.extractall(extract_path)
    elif in_ext == '.7z':
        with py7zr.SevenZipFile(in_path, 'r') as zf:
            zf.extractall(extract_path)
            
    return f"Εξαγωγή σε: {extract_path}" # Default success message

def handle_data_conversion(in_path, out_path, in_ext, out_ext):
    """Handles CSV <-> JSON conversions."""
    if in_ext == '.csv' and out_ext == '.json':
        data = []
        with open(in_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    elif in_ext == '.json' and out_ext == '.csv':
        with open(in_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list) or not data:
            raise Exception("Το JSON πρέπει να είναι μια μη-κενή λίστα αντικειμένων.")
        if not all(isinstance(x, dict) for x in data):
            raise Exception("Το JSON πρέπει να είναι μια λίστα αντικειμένων (λεξικών).")
            
        headers = data[0].keys()
        with open(out_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
    else:
        raise Exception(f"Η μετατροπή δεδομένων {in_ext} σε {out_ext} δεν υποστηρίζεται.")

def handle_md_to_html(in_path, out_path):
    # (Unchanged)
    with open(in_path, 'r', encoding='utf-8') as f:
        html = markdown.markdown(f.read())
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

def handle_single_image_to_pdf(in_path, out_path):
    # (Unchanged)
    try:
        with Image.open(in_path) as img:
            img_rgb = img.convert('RGB')
            img_rgb.save(out_path, "PDF", resolution=100.0)
    except Exception as e:
        raise Exception(f"Σφάλμα Pillow (Εικόνα->PDF): {e}")

def handle_multi_image_to_pdf(image_paths, out_path):
    # (Unchanged)
    try:
        images_rgb = []
        for path in image_paths:
            img = Image.open(path)
            images_rgb.append(img.convert('RGB'))
        if not images_rgb:
            raise Exception("Δεν βρέθηκαν εικόνες για μετατροπή.")
        images_rgb[0].save(
            out_path, "PDF", resolution=100.0,
            save_all=True, append_images=images_rgb[1:]
        )
    except Exception as e:
        raise Exception(f"Σφάλμα Pillow (Πολλαπλές Εικόνες->PDF): {e}")

# --- 5. MAIN CONVERSION ROUTER ---

def convert_file(in_path, out_folder_name):
    """
    Main router function for dispatching conversion tasks.
    Returns (success_bool, message_string)
    """
    in_ext = os.path.splitext(in_path)[1].lower()
    out_ext = f".{out_folder_name.lower()}"
    
    base_name = os.path.splitext(os.path.basename(in_path))[0]
    out_folder_path = os.path.join(BASE_CONVERTER_PATH, out_folder_name)
    out_path = os.path.join(out_folder_path, f"{base_name}{out_ext}")

    try:
        # --- Route 1: Extraction ---
        if in_ext in ARCHIVE_EXTS and out_folder_name.upper() in [f.replace('.', '').upper() for f in ARCHIVE_EXTS]:
            # For extraction, output folder is usually the same as input type (e.g., ZIP -> ZIP folder)
            # GZ is handled specially in handle_extraction (for single files)
            message = handle_extraction(in_path, out_folder_path, in_ext)
            return (True, message)

        # --- Route 2: SVG Conversion (to PNG, PDF) ---
        if in_ext in VECTOR_IMAGE_EXTS and out_ext in ['.png', '.pdf']:
            handle_svg_conversion(in_path, out_path)
            return (True, f"Αποθηκεύτηκε σε: {out_path}")

        # --- Route 3: PSD Conversion (to flat image) ---
        if in_ext in LAYERED_IMAGE_EXTS and out_ext in IMAGE_EXTS:
            handle_psd_conversion(in_path, out_path)
            return (True, f"Αποθηκεύτηκε σε: {out_path}")

        # --- Route 4: Image-to-Image (Pillow) ---
        if in_ext in IMAGE_EXTS and out_ext in IMAGE_EXTS:
            handle_image_conversion(in_path, out_path)
            return (True, f"Αποθηκεύτηκε σε: {out_path}")
            
        # --- Route 5: Single Image-to-PDF ---
        if in_ext in IMAGE_EXTS and out_ext == '.pdf':
            handle_single_image_to_pdf(in_path, out_path)
            return (True, f"Αποθηκεύτηκε σε: {out_path}")

        # --- Route 6: A/V-to-A/V (ffmpeg) ---
        if in_ext in AV_EXTS and out_ext in AV_EXTS:
            handle_av_conversion(in_path, out_path)
            return (True, f"Αποθηκεύτηκε σε: {out_path}")
            
        # --- Route 7: Data Conversion (CSV <-> JSON) ---
        if in_ext in ['.csv', '.json'] and out_ext in ['.csv', '.json']:
            handle_data_conversion(in_path, out_path, in_ext, out_ext)
            return (True, f"Αποθηκεύτηκε σε: {out_path}")

        # --- Route 8: MD-to-HTML ---
        if in_ext == '.md' and out_ext == '.html':
            handle_md_to_html(in_path, out_path)
            return (True, f"Αποθηκεύτηκε σε: {out_path}")

        # --- Route 9: Anything-to-TXT ---
        if out_ext == '.txt' and in_ext in TEXT_DOC_EXTS:
            text_lines = get_text_from_file(in_path, in_ext)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.writelines(text_lines)
            return (True, f"Αποθηκεύτηκε σε: {out_path}")
            
        # --- Route 10: Anything-to-PDF ---
        if out_ext == '.pdf' and in_ext in TEXT_DOC_EXTS:
            text_lines = get_text_from_file(in_path, in_ext)
            write_text_to_pdf(text_lines, out_path)
            return (True, f"Αποθηκεύτηκε σε: {out_path}")

        # --- No Route Found ---
        return (False, f"Μη υποστηριζόμενη μετατροπή: {in_ext} σε {out_ext}")

    except Exception as e:
        return (False, f"ΣΦΑΛΜΑ: {str(e)}")


# --- 6. CLI UI HELPER FUNCTIONS ---

def run_numerical_menu(title, options, back_option=True):
    """Presents a list of options and waits for a numerical selection."""
    while True:
        print("\n" + "=" * 40)
        print(f"--- {title} ---")
        print("=" * 40)
        
        indexed_options = []
        for i, option in enumerate(options):
            indexed_options.append((i + 1, option))
            print(f"[{i + 1}] {option}")
            
        if back_option:
            print(f"[0] Πίσω")
            max_choice = len(options)
        else:
            max_choice = len(options)
        
        choice = input(f"\nΕισάγετε επιλογή (0-{max_choice}): ").strip()
        
        if choice == '0' and back_option:
            return None # Go Back
        
        try:
            int_choice = int(choice)
            if 1 <= int_choice <= len(options):
                return options[int_choice - 1]
            else:
                print(f"Μη έγκυρη επιλογή. Παρακαλώ εισάγετε έναν αριθμό μεταξύ 0 και {max_choice}.")
        except ValueError:
            print("Μη έγκυρη εισαγωγή. Παρακαλώ εισάγετε έναν αριθμό.")
        input("Πατήστε Enter για να συνεχίσετε...")
        clear_screen_standard()

def run_file_selector(folder_path, title, input_folder_name):
    """Lists files in a directory and allows numerical selection."""
    while True:
        clear_screen_standard()
        try:
            files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            files.sort()
        except Exception as e:
            print(f"\n[ΣΦΑΛΜΑ] Σφάλμα ανάγνωσης {folder_path}: {e}")
            input("Πατήστε Enter για να συνεχίσετε...")
            return None
        
        print("\n" + "=" * 40)
        print(f"--- {title} ---")
        print(f"Φάκελος: /Download/File Converter/{input_folder_name}")
        print("=" * 40)
        
        if not files:
            print(f"\n[ΠΛΗΡΟΦΟΡΙΑ] Δεν βρέθηκαν αρχεία στον {os.path.basename(folder_path)}.")
            input("Πατήστε Enter για να συνεχίσετε...")
            return None
            
        options = []
        
        if input_folder_name in IMAGE_FOLDERS:
            # Multi-image PDF option at index 1
            options.append(f"** Μετατροπή ΟΛΩΝ των {len(files)} Εικόνων στον '{input_folder_name}' σε ένα PDF **")
        
        options.extend(files)
        
        for i, option in enumerate(options):
            print(f"[{i + 1}] {option}")
        
        print(f"[0] Πίσω")
        
        max_choice = len(options)
        choice = input(f"\nΕισάγετε επιλογή (0-{max_choice}): ").strip()
        
        if choice == '0':
            return None
        
        try:
            int_choice = int(choice)
            if 1 <= int_choice <= len(options):
                return options[int_choice - 1]
            else:
                print(f"Μη έγκυρη επιλογή. Παρακαλώ εισάγετε έναν αριθμό μεταξύ 0 και {max_choice}.")
        except ValueError:
            print("Μη έγκυρη εισαγωγή. Παρακαλώ εισάγετε έναν αριθμό.")
        input("Πατήστε Enter για να συνεχίσετε...")

def run_confirmation(prompt):
    """Gets a Yes/No confirmation."""
    while True:
        print("\n" + "=" * 40)
        print(f"*** Επιβεβαίωση ***")
        print("=" * 40)
        print(prompt)
        print("[1] Ναι")
        print("[2] Όχι")
        choice = input("Εισάγετε επιλογή (1 ή 2): ").strip()
        if choice == '1':
            return "Yes"
        elif choice == '2':
            return "No"
        else:
            print("Μη έγκυρη επιλογή. Παρακαλώ εισάγετε 1 για Ναι ή 2 για Όχι.")
            input("Πατήστε Enter για να συνεχίσετε...")

def run_help():
    clear_screen_standard()
    print("\n" + "=" * 40)
    print("--- Βοήθεια / Οδηγίες Χρήσης ---")
    print("=" * 40)
    help_text = [
        "Αυτός ο μετατροπέας χρησιμοποιεί μια απλή διαδικασία 3 βημάτων:",
        "",
        "1. ΜΕΤΑΦΕΡΕΤΕ ΤΑ ΑΡΧΕΙΑ ΣΑΣ:",
        "   Χρησιμοποιήστε τον Διαχειριστή Αρχείων του τηλεφώνου σας. Πηγαίνετε στο:",
        f"   /Download/File Converter/",
        "   Μετακινήστε τα αρχεία στον σωστό φάκελο (π.χ., μετακινήστε το 'report.docx' στον φάκελο 'DOCX').",
        "",
        "2. ΕΚΤΕΛΕΣΤΕ ΑΥΤΟ ΤΟΝ ΜΕΤΑΤΡΟΠΕΑ:",
        "   Επιλέξτε 'Μετατροπή Αρχείου' από το κύριο μενού.",
        "",
        "3. ΑΚΟΛΟΥΘΗΣΤΕ ΤΑ ΒΗΜΑΤΑ:",
        "   Βήμα 1: Επιλέξτε τον φάκελο ΕΙΣΟΔΟΥ (π.χ., 'DOCX').",
        "   Βήμα 2: Επιλέξτε το αρχείο που θέλετε να μετατρέψετε (με αριθμό).",
        "   Βήμα 3: Επιλέξτε τη μορφή ΕΞΟΔΟΥ (π.χ., 'PDF').",
        "",
        "** ΕΙΔΙΚΕΣ ΜΕΤΑΤΡΟΠΕΣ **",
        " - Αρχεία Συμπίεσης (ZIP, RAR, 7Z, TAR, GZ): Επιλέξτε το αρχείο εισόδου, και στη συνέχεια επιλέξτε τον *ίδιο* φάκελο ως έξοδο.",
        "   Αυτό θα εξαγάγει το αρχείο σε έναν υπο-φάκελο μέσα στον φάκελο του τύπου: /ZIP/file_name/",
        " - PDF Πολλαπλών Εικόνων: Κατά την επιλογή αρχείου από φάκελο εικόνων (JPG, PNG, κ.λπ.), επιλέξτε την ειδική επιλογή:",
        "   '** Μετατροπή ΟΛΩΝ... **' για να συνδυάσετε όλες τις εικόνες αυτού του φακέλου σε ένα PDF.",
        " - Δεδομένα: Μπορείτε να μετατρέψετε CSV <-> JSON.",
        " - Ήχος/Βίντεο: Οι μετατροπές Ήχου/Βίντεο απαιτούν το 'ffmpeg' (δείτε την αρχική εκκίνηση)."
    ]
    for line in help_text:
        print(line)
    
    input("\nΠατήστε Enter για επιστροφή στο κύριο μενού...")

def run_text_input(prompt):
    """Gets a string input from the user."""
    clear_screen_standard()
    print("\n" + "=" * 40)
    print("--- Απαιτείται Εισαγωγή ---")
    print("=" * 40)
    
    text = input(f"{prompt}: ").strip()
    return text

def run_multi_image_to_pdf_wizard(input_folder_path, input_folder_name):
    """Handles the multi-image to PDF logic."""
    clear_screen_standard()
    print("\n" + "=" * 40)
    print("--- Οδηγός PDF Πολλαπλών Εικόνων ---")
    print("=" * 40)
    
    try:
        image_paths = [
            os.path.join(input_folder_path, f) 
            for f in os.listdir(input_folder_path) 
            if os.path.splitext(f)[1].lower() in IMAGE_EXTS
        ]
        image_paths.sort()
    except Exception as e:
        print(f"\n[ΣΦΑΛΜΑ] Σφάλμα ανάγνωσης εικόνων: {e}")
        input("Πατήστε Enter για να συνεχίσετε...")
        return
    
    if not image_paths:
        print("\n[ΣΦΑΛΜΑ] Δεν βρέθηκαν εικόνες σε αυτόν τον φάκελο.")
        input("Πατήστε Enter για να συνεχίσετε...")
        return
        
    confirm = run_confirmation(f"Συνδυασμός και των {len(image_paths)} εικόνων στον φάκελο '{input_folder_name}' σε ένα PDF;")
    if confirm != "Yes": return
    
    default_name = f"{input_folder_name}_Album"
    filename = run_text_input(f"Εισάγετε όνομα για το PDF (προεπιλογή: {default_name})")
    
    if not filename: filename = default_name
    
    out_folder_path = os.path.join(BASE_CONVERTER_PATH, "PDF")
    out_path = os.path.join(out_folder_path, f"{filename}.pdf")
    
    print("\n[ΠΛΗΡΟΦΟΡΙΑ] Επεξεργασία... συνδυασμός εικόνων σε PDF. Αυτό μπορεί να πάρει λίγο χρόνο...")
    
    try:
        handle_multi_image_to_pdf(image_paths, out_path)
        print(f"\n[ΕΠΙΤΥΧΙΑ] Αποθηκεύτηκε σε: {out_path}")
    except Exception as e:
        print(f"\n[ΣΦΑΛΜΑ] {e}")
        
    input("Πατήστε Enter για να συνεχίσετε...")

# --- 7. MAIN CLI APPLICATION ---

def main_cli():
    """The main CLI loop."""
    while True:
        clear_screen_standard()
        main_choice = run_numerical_menu(
            "Κύριο Μενού", 
            ["Μετατροπή Αρχείου", "Βοήθεια / Οδηγίες Χρήσης", "Έξοδος"], 
            back_option=False # Exit is explicitly handled
        )
        
        if main_choice == "Έξοδος": break
        if main_choice == "Βοήθεια / Οδηγίες Χρήσης": run_help(); continue
            
        # 1. Choose INPUT Folder
        input_folder = run_numerical_menu("Βήμα 1: Επιλέξτε Φάκελο ΕΙΣΟΔΟΥ", FOLDER_NAMES)
        if input_folder is None: continue
        input_folder_path = os.path.join(BASE_CONVERTER_PATH, input_folder)
        
        # 2. Choose File
        input_file = run_file_selector(input_folder_path, f"Βήμα 2: Επιλέξτε Αρχείο από τον '{input_folder}'", input_folder)
        if input_file is None: continue
        
        # Check for Multi-Image PDF special option
        if input_file.startswith("** Μετατροπή ΟΛΩΝ"):
            run_multi_image_to_pdf_wizard(input_folder_path, input_folder)
            continue
            
        full_input_path = os.path.join(input_folder_path, input_file)
        in_ext = os.path.splitext(input_file)[1].lower()
        
        # --- Determine Output Folder and Prompt ---
        is_archive = in_ext in ARCHIVE_EXTS
        
        if is_archive:
            # Special Case: Archive Extraction (Output folder is the same)
            output_folder = input_folder
            prompt = f"Εξαγωγή του αρχείου '{input_file}' στον φάκελο '/File Converter/{output_folder}/';"
        else:
            # Normal Conversion Path: Choose OUTPUT Folder
            output_folder = run_numerical_menu("Βήμα 3: Επιλέξτε Μορφή/Φάκελο ΕΞΟΔΟΥ", FOLDER_NAMES)
            if output_folder is None: continue
            if output_folder == input_folder:
                print("\n[ΣΦΑΛΜΑ] Ο φάκελος Εισόδου και Εξόδου δεν μπορεί να είναι ο ίδιος για μετατροπή (επιλέξτε τον ίδιο φάκελο μόνο για αρχεία συμπίεσης).")
                input("Πατήστε Enter για να συνεχίσετε...")
                continue
            prompt = f"Μετατροπή του '{input_file}' σε μορφή {output_folder};"
             
        # 3. Confirmation
        confirm = run_confirmation(prompt)
        if confirm != "Yes": continue

        # 4. Conversion
        print("\n[ΠΛΗΡΟΦΟΡΙΑ] Επεξεργασία, παρακαλώ περιμένετε...")
        success, message = convert_file(full_input_path, output_folder)
        
        if success:
            print(f"\n[ΕΠΙΤΥΧΙΑ] {message}")
        else:
            print(f"\n[ΣΦΑΛΜΑ] {message}")
            
        input("Πατήστε Enter για να συνεχίσετε...")

# --- 8. SCRIPT ENTRYPOINT ---

if __name__ == "__main__":
    try:
        clear_screen_standard()
        print("--- Εκκίνηση Termux Μετατροπέας v3.1 CLI (40 Μορφές) ---")
        check_and_install_dependencies()
        check_external_bins()
        check_storage_access()
        setup_folders()
        
        print("--- Η Ρύθμιση Ολοκληρώθηκε ---")
        print(f"Οι φάκελοι οργάνωσης είναι έτοιμοι στη διαδρομή: {BASE_CONVERTER_PATH}")
        print("\nΕκκίνηση εφαρμογής...")
        time.sleep(1)
        
        main_cli()
        print("\nΟ Μετατροπέας Αρχείων τερμάτισε επιτυχώς.")

    except KeyboardInterrupt:
        print("\nΈξοδος...")
    except Exception as e:
        print("\nΠροέκυψε ένα κρίσιμο σφάλμα:")
        traceback.print_exc()
        input("Πατήστε Enter για έξοδο...")
    finally:
        os.system('clear')