#!/usr/bin/env python

"""
Ένα προηγμένο, διαδραστικό μετατροπέα αρχείων για Termux χρησιμοποιώντας 'curses'.
Έκδοση 3.1: Οργανώνει όλους τους φακέλους σε έναν κύριο φάκελο "File Converter".

Αυτό το script θα:
1. Ελέγξει και θα εγκαταστήσει τις απαιτούμενες βιβλιοθήκες Python.
2. Ελέγξει για εξωτερικά προγράμματα (ffmpeg, unrar, cairo).
3. Δημιουργήσει έναν φάκελο "File Converter" στο Downloads, που περιέχει 40 υπο-φακέλους.
4. Παρασχέσει ένα περιβάλλον χρήστη βασισμένο στο 'curses' για πλοήγηση.
5. Υποστηρίξει πολλούς μετασχηματισμούς εγγράφων, εικόνων, ήχου/βίντεο και δεδομένων.

ΣΗΜΑΝΤΙΚΕΣ ΟΔΗΓΙΕΣ ΕΓΚΑΤΑΣΤΑΣΗΣ (στο Termux):
pkg install ffmpeg unrar libcairo libgirepository libjpeg-turbo libpng
"""

import sys
import os
import subprocess
import importlib.util
import time
import curses
import traceback
import zipfile
import tarfile
import csv
import json
import gzip
import shutil
from contextlib import redirect_stderr, redirect_stdout

# --- 1. ΡΥΘΜΙΣΗ & ΔΙΑΜΟΡΦΩΣΗ ---

# (14) Βιβλιοθήκες Python για αυτόματη εγκατάσταση
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

# (40) Φάκελοι προς δημιουργία
FOLDER_NAMES = [
    # Εικόνες (10)
    "JPG", "PNG", "WEBP", "BMP", "TIFF", "GIF", "ICO", "TGA", "SVG", "PSD",
    # Έγγραφα (12)
    "PDF", "TXT", "DOCX", "ODT", "HTML", "MD", "CSV", "RTF", "EPUB", "JSON", "XML", "PPTX",
    # Αρχεία (5)
    "ZIP", "TAR", "RAR", "7Z", "GZ",
    # Ήχος (7)
    "MP3", "WAV", "OGG", "FLAC", "M4A", "AAC", "WMA",
    # Βίντεο (6)
    "MP4", "MKV", "AVI", "MOV", "WMV", "FLV"
]

# Βοηθητικές λίστες για λογική
IMAGE_FOLDERS = ["JPG", "PNG", "WEBP", "BMP", "TIFF", "GIF", "ICO", "TGA", "SVG", "PSD"]
IMAGE_EXTS = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif', '.ico', '.tga']
VECTOR_IMAGE_EXTS = ['.svg']
LAYERED_IMAGE_EXTS = ['.psd']
AV_EXTS = ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac', '.wma', '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv']
ARCHIVE_EXTS = ['.zip', '.tar', '.gz', '.bz2', '.rar', '.7z']
TEXT_DOC_EXTS = ['.txt', '.docx', '.odt', '.html', '.md', '.csv', '.rtf', '.epub', '.json', '.xml', '.pptx', '.svg']
DATA_EXTS = ['.csv', '.json', '.xml']

# Διαδρομές
STORAGE_PATH = "/storage/emulated/0"
DOWNLOAD_PATH = os.path.join(STORAGE_PATH, "Download")
# --- ΤΡΟΠΟΠΟΙΗΜΕΝΟ: Όλοι οι φάκελοι είναι τώρα μέσα στον κύριο φάκελο "File Converter" ---
BASE_CONVERTER_PATH = os.path.join(DOWNLOAD_PATH, "File Converter")

# Παγκόσμιες σημαίες για εξωτερικά προγράμματα
HAS_FFMPEG = False
HAS_UNRAR = False
HAS_CAIRO = False

# --- 2. ΣΥΝΑΡΤΗΣΕΙΣ ΡΥΘΜΙΣΗΣ ΠΡΙΝ ΑΠΟ ΤΟ CURSES (Τυπική εκτύπωση) ---

def clear_screen_standard():
    os.system('clear')

def check_and_install_dependencies():
    """Ελέγχει και εγκαθιστά τις απαιτούμενες βιβλιοθήκες Python."""
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
                print(f"Επιτυχής εγκατάσταση '{package_name}'.")
            except Exception:
                print(f"ΣΦΑΛΜΑ: Αποτυχία εγκατάστασης '{package_name}'.")
                print(f"Παρακαλώ εγκαταστήστε το χειροκίνητα: pip install {package_name}")
                sys.exit(1)
        else:
            # print(f"Η βιβλιοθήκη '{package_name}' είναι ήδη εγκατεστημένη.")
            pass
    
    if all_installed:
        print("Όλες οι βιβλιοθήκες Python είναι εγκατεστημένες.\n")
    else:
        print("Όλες οι απαιτούμενες βιβλιοθήκες είναι τώρα εγκατεστημένες.\n")
    time.sleep(0.5)

def check_external_bins():
    """Ελέγχει για 'ffmpeg', 'unrar', και 'cairo'."""
    global HAS_FFMPEG, HAS_UNRAR, HAS_CAIRO
    print("--- Έλεγχος Εξωτερικών Προγραμμάτων ---")
    
    # Έλεγχος ffmpeg
    try:
        with open(os.devnull, 'w') as devnull:
            subprocess.run(["ffmpeg", "-version"], check=True, stdout=devnull, stderr=devnull)
        print("Βρέθηκε 'ffmpeg'. Οι μετατροπές ήχου/βίντεο είναι ΕΝΕΡΓΟΠΟΙΗΜΕΝΕΣ.")
        HAS_FFMPEG = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Το 'ffmpeg' δεν βρέθηκε. Οι μετατροπές ήχου/βίντεο είναι ΑΠΕΝΕΡΓΟΠΟΙΗΜΕΝΕΣ.")
        print("  Για ενεργοποίηση, εκτελέστε: pkg install ffmpeg\n")
        HAS_FFMPEG = False

    # Έλεγχος unrar
    try:
        with open(os.devnull, 'w') as devnull:
            subprocess.run(["unrar"], check=True, stdout=devnull, stderr=devnull)
        print("Βρέθηκε 'unrar'. Η εξαγωγή RAR είναι ΕΝΕΡΓΟΠΟΙΗΜΕΝΗ.")
        HAS_UNRAR = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Το 'unrar' δεν βρέθηκε. Η εξαγωγή RAR είναι ΑΠΕΝΕΡΓΟΠΟΙΗΜΕΝΗ.")
        print("  Για ενεργοποίηση, εκτελέστε: pkg install unrar\n")
        HAS_UNRAR = False
        
    # Έλεγχος cairo (για SVG)
    if importlib.util.find_spec("cairosvg") is not None:
        print("Βρέθηκε 'cairosvg'. Οι μετατροπές SVG είναι ΕΝΕΡΓΟΠΟΙΗΜΕΝΕΣ.")
        HAS_CAIRO = True
    else:
        print("ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Η βιβλιοθήκη Python 'cairosvg' δεν βρέθηκε. Η μετατροπή SVG είναι ΑΠΕΝΕΡΓΟΠΟΙΗΜΕΝΗ.")
        print("  Το script προσπάθησε να την εγκαταστήσει, αλλά μπορεί να απέτυχε.")
        print("  Μπορεί επίσης να χρειαστείτε: pkg install libcairo libgirepository\n")
        HAS_CAIRO = False
        
    print("")
    time.sleep(0.5)


def check_storage_access():
    print("--- Έλεγχος Πρόσβασης Αποθήκευσης ---")
    if not os.path.exists(DOWNLOAD_PATH):
        print(f"ΣΦΑΛΜΑ: Δεν είναι δυνατή η πρόσβαση στην εσωτερική αποθήκευση στο '{DOWNLOAD_PATH}'.")
        print("Παρακαλώ εκτελέστε 'termux-setup-storage' στο τερματικό του Termux,")
        print("παραχωρήστε την άδεια και μετά εκτελέστε ξανά αυτό το script.")
        sys.exit(1)
    print("Η πρόσβαση στην αποθήκευση επιβεβαιώθηκε.\n")
    time.sleep(0.5)

def setup_folders():
    # --- ΤΡΟΠΟΠΟΙΗΜΕΝΟ: Δημιουργεί πρώτα τον κύριο φάκελο "File Converter" ---
    print(f"--- Ρύθμιση Φακέλων Οργάνωσης ---")
    print(f"Τοποθεσία: {BASE_CONVERTER_PATH}")
    try:
        # 1. Δημιουργία του κύριου γονικού φακέλου
        os.makedirs(BASE_CONVERTER_PATH, exist_ok=True)
        # 2. Δημιουργία όλων των 40 υπο-φακέλων μέσα σε αυτόν
        for folder in FOLDER_NAMES:
            os.makedirs(os.path.join(BASE_CONVERTER_PATH, folder), exist_ok=True)
        print(f"Δημιουργήθηκαν/επαληθεύτηκαν επιτυχώς {len(FOLDER_NAMES)} υπο-φάκελοι.\n")
    except Exception as e:
        print(f"ΣΦΑΛΜΑ: Δεν ήταν δυνατή η δημιουργία των φακέλων: {e}")
        sys.exit(1)
    time.sleep(0.5)

# --- 3. ΕΙΣΑΓΩΓΕΣ (Μετά την εγκατάσταση) ---
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
    print(f"ΚΡΙΤΙΚΟ ΣΦΑΛΜΑ: Αποτυχία εισαγωγής βιβλιοθήκης: {e}")
    print("Παρακαλώ βεβαιωθείτε ότι όλες οι εξαρτήσεις είναι εγκατεστημένες (δείτε τα αρχεία καταγραφής έναρξης).")
    sys.exit(1)

# --- 4. ΚΥΡΙΑ ΛΟΓΙΚΗ ΜΕΤΑΤΡΟΠΗΣ ---

def get_text_from_file(input_path, in_ext):
    """Βοηθητική λειτουργία για εξαγωγή απλού κειμένου από διάφορους τύπους εγγράφων."""
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
                    text_lines.append(soup.get_text() + '\n\n') # Προσθήκη κενού μεταξύ κεφαλαίων
        elif in_ext == '.pptx':
            prs = pptx.Presentation(input_path)
            for slide in prs.slides:
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        text_lines.append(shape.text + '\n')
    except Exception as e:
        raise Exception(f"Η εξαγωγή κειμένου απέτυχε: {e}")
    return text_lines

def write_text_to_pdf(text_lines, output_path):
    # (Αμετάβλητο)
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    margin_x, margin_y = 0.75 * inch, 1 * inch
    text_object = c.beginText(margin_x, height - margin_y)
    text_object.setFont("Helvetica", 10)
    line_height, y = 12, height - margin_y
    for line in text_lines:
        for sub_line in line.split('\n'): # Χειρισμός συμβολοσειρών πολλαπλών γραμμών
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

def handle_image_conversion(stdscr, in_path, out_path):
    # (Χειριστής Pillow, αμετάβλητος)
    with Image.open(in_path) as img:
        if out_path.lower().endswith(('.jpg', '.jpeg')):
            if img.mode == 'RGBA':
                img = img.convert('RGB')
        img.save(out_path)

def handle_svg_conversion(stdscr, in_path, out_path):
    """Μετατρέπει SVG σε PNG ή PDF."""
    if not HAS_CAIRO:
        raise Exception("Οι βιβλιοθήκες Cairo/SVG δεν είναι εγκατεστημένες.")
    out_ext = os.path.splitext(out_path)[1].lower()
    if out_ext == '.png':
        cairosvg.svg2png(url=in_path, write_to=out_path)
    elif out_ext == '.pdf':
        cairosvg.svg2pdf(url=in_path, write_to=out_path)
    else:
        raise Exception(f"Η μετατροπή SVG σε {out_ext} δεν υποστηρίζεται.")

def handle_psd_conversion(stdscr, in_path, out_path):
    """Μετατρέπει το σύνθετο PSD σε επίπεδη εικόνα."""
    psd = PSDImage.open(in_path)
    composite_image = psd.composite()
    composite_image.save(out_path)

def handle_av_conversion(stdscr, in_path, out_path):
    # (Αμετάβλητο)
    if not HAS_FFMPEG:
        raise Exception("Το 'ffmpeg' δεν βρέθηκε. Η μετατροπή ήχου/βίντεο είναι απενεργοποιημένη.")
    command = ['ffmpeg', '-i', in_path, '-y', out_path]
    curses.endwin()
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
        print("Πατήστε Enter για επιστροφή στην εφαρμογή...")
        sys.stdin.read(1)
        stdscr.refresh()

def handle_extraction(stdscr, in_path, out_folder_path, in_ext):
    """Εξάγει διάφορους τύπους αρχείων."""
    base_name = os.path.splitext(os.path.basename(in_path))[0]
    extract_path = os.path.join(out_folder_path, base_name)
    os.makedirs(extract_path, exist_ok=True)
    
    if in_ext == '.zip':
        with zipfile.ZipFile(in_path, 'r') as zf:
            zf.extractall(extract_path)
    elif in_ext in ['.tar', '.gz', '.bz2']:
        if in_ext == '.gz' and not in_path.endswith('.tar.gz'): # Μονό αρχείο gzip
             out_filename = os.path.splitext(os.path.basename(in_path))[0]
             out_path = os.path.join(out_folder_path, out_filename) # Εξαγωγή σε φάκελο, όχι υποφάκελο
             with gzip.open(in_path, 'rb') as f_in:
                 with open(out_path, 'wb') as f_out:
                     shutil.copyfileobj(f_in, f_out)
             return f"Αποσυμπιέστηκε σε: {out_path}" # Διαφορετικό μήνυμα
        else: # .tar, .tar.gz, .tar.bz2
            with tarfile.open(in_path, 'r:*') as tf:
                tf.extractall(extract_path)
    elif in_ext == '.rar':
        if not HAS_UNRAR:
            raise Exception("Το 'unrar' δεν βρέθηκε.")
        with rarfile.RarFile(in_path) as rf:
            rf.extractall(extract_path)
    elif in_ext == '.7z':
        with py7zr.SevenZipFile(in_path, 'r') as zf:
            zf.extractall(extract_path)
            
    return f"Εξήχθη σε: {extract_path}" # Προεπιλεγμένο μήνυμα επιτυχίας

def handle_data_conversion(stdscr, in_path, out_path, in_ext, out_ext):
    """Χειρίζεται μετατροπές CSV <-> JSON."""
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
            raise Exception("Το JSON πρέπει να είναι μια μη κενή λίστα αντικειμένων.")
        if not all(isinstance(x, dict) for x in data):
            raise Exception("Το JSON πρέπει να είναι μια λίστα αντικειμένων (λεξικά).")
            
        headers = data[0].keys()
        with open(out_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
    else:
        raise Exception(f"Η μετατροπή δεδομένων {in_ext} σε {out_ext} δεν υποστηρίζεται.")

def handle_md_to_html(stdscr, in_path, out_path):
    # (Αμετάβλητο)
    with open(in_path, 'r', encoding='utf-8') as f:
        html = markdown.markdown(f.read())
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

def handle_single_image_to_pdf(stdscr, in_path, out_path):
    # (Αμετάβλητο)
    try:
        with Image.open(in_path) as img:
            img_rgb = img.convert('RGB')
            img_rgb.save(out_path, "PDF", resolution=100.0)
    except Exception as e:
        raise Exception(f"Σφάλμα Pillow (Εικόνα->PDF): {e}")

def handle_multi_image_to_pdf(stdscr, image_paths, out_path):
    # (Αμετάβλητο)
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

# --- 5. ΚΥΡΙΟΣ ΔΙΑΝΟΜΕΑΣ ΜΕΤΑΤΡΟΠΗΣ ---

def convert_file(stdscr, in_path, out_folder_name):
    """
    Κύρια λειτουργία δρομολόγησης για την αποστολή εργασιών μετατροπής.
    Επιστρέφει (επιτυχία_boolean, μήνυμα_συμβολοσειρά)
    """
    in_ext = os.path.splitext(in_path)[1].lower()
    out_ext = f".{out_folder_name.lower()}"
    
    base_name = os.path.splitext(os.path.basename(in_path))[0]
    out_folder_path = os.path.join(BASE_CONVERTER_PATH, out_folder_name)
    out_path = os.path.join(out_folder_path, f"{base_name}{out_ext}")

    try:
        # --- Διαδρομή 1: Εξαγωγή ---
        if in_ext in ARCHIVE_EXTS:
            # Σημείωση: Τα αρχεία GZ θα αποσυμπιεστούν *μέσα* στον φάκελο με όνομα GZ
            # Όλα τα άλλα (ZIP, TAR, RAR, 7Z) εξάγονται σε *υπο-φάκελο*
            out_folder = out_folder_path if in_ext == '.gz' else os.path.join(BASE_CONVERTER_PATH, out_folder_name)
            message = handle_extraction(stdscr, in_path, out_folder, in_ext)
            return (True, message)

        # --- Διαδρομή 2: Μετατροπή SVG (σε PNG, PDF) ---
        if in_ext in VECTOR_IMAGE_EXTS and out_ext in ['.png', '.pdf']:
            handle_svg_conversion(stdscr, in_path, out_path)
            return (True, f"Αποθηκεύτηκε σε: {out_path}")

        # --- Διαδρομή 3: Μετατροπή PSD (σε επίπεδη εικόνα) ---
        if in_ext in LAYERED_IMAGE_EXTS and out_ext in IMAGE_EXTS:
            handle_psd_conversion(stdscr, in_path, out_path)
            return (True, f"Αποθηκεύτηκε σε: {out_path}")

        # --- Διαδρομή 4: Εικόνα-σε-Εικόνα (Pillow) ---
        if in_ext in IMAGE_EXTS and out_ext in IMAGE_EXTS:
            handle_image_conversion(stdscr, in_path, out_path)
            return (True, f"Αποθηκεύτηκε σε: {out_path}")
            
        # --- Διαδρομή 5: Μονή Εικόνα-σε-PDF ---
        if in_ext in IMAGE_EXTS and out_ext == '.pdf':
            handle_single_image_to_pdf(stdscr, in_path, out_path)
            return (True, f"Αποθηκεύτηκε σε: {out_path}")

        # --- Διαδρομή 6: Ήχος/Βίντεο-σε-Ήχος/Βίντεο (ffmpeg) ---
        if in_ext in AV_EXTS and out_ext in AV_EXTS:
            handle_av_conversion(stdscr, in_path, out_path)
            return (True, f"Αποθηκεύτηκε σε: {out_path}")
            
        # --- Διαδρομή 7: Μετατροπή Δεδομένων (CSV <-> JSON) ---
        if in_ext in ['.csv', '.json'] and out_ext in ['.csv', '.json']:
            handle_data_conversion(stdscr, in_path, out_path, in_ext, out_ext)
            return (True, f"Αποθηκεύτηκε σε: {out_path}")

        # --- Διαδρομή 8: MD-σε-HTML ---
        if in_ext == '.md' and out_ext == '.html':
            handle_md_to_html(stdscr, in_path, out_path)
            return (True, f"Αποθηκεύτηκε σε: {out_path}")

        # --- Διαδρομή 9: Οτιδήποτε-σε-TXT ---
        if out_ext == '.txt' and in_ext in TEXT_DOC_EXTS:
            text_lines = get_text_from_file(in_path, in_ext)
            with open(out_path, 'w', encoding='utf-8') as f:
                f.writelines(text_lines)
            return (True, f"Αποθηκεύτηκε σε: {out_path}")
            
        # --- Διαδρομή 10: Οτιδήποτε-σε-PDF ---
        if out_ext == '.pdf' and in_ext in TEXT_DOC_EXTS:
            text_lines = get_text_from_file(in_path, in_ext)
            write_text_to_pdf(text_lines, out_path)
            return (True, f"Αποθηκεύτηκε σε: {out_path}")

        # --- Δεν Βρέθηκε Διαδρομή ---
        return (False, f"Μη υποστηριζόμενη μετατροπή: {in_ext} σε {out_ext}")

    except Exception as e:
        return (False, f"ΣΦΑΛΜΑ: {str(e)}")


# --- 6. ΒΟΗΘΗΤΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ ΠΕΡΙΒΑΛΛΟΝΤΟΣ ΧΡΗΣΤΗ CURSES ---
# (Αμετάβλητες από v2, αλλά προστέθηκε σημείωση στο run_help)

def draw_header(stdscr, title):
    h, w = stdscr.getmaxyx()
    stdscr.attron(curses.color_pair(2))
    stdscr.addstr(0, 0, " " * w, curses.color_pair(2))
    header_text = f" Termux Curses Converter (q για έξοδο/πίσω) "
    stdscr.addstr(0, (w - len(header_text)) // 2, header_text, curses.A_REVERSE)
    stdscr.attroff(curses.color_pair(2))
    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(2, (w - len(title)) // 2, title)
    stdscr.attroff(curses.color_pair(1))

def draw_status(stdscr, message, is_error=False):
    h, w = stdscr.getmaxyx()
    nav_hint = " (Βελάκια, Enter για Επιλογή, q για Πίσω) "
    hint_len = len(nav_hint)
    color = curses.color_pair(3) if is_error else curses.color_pair(2)
    stdscr.attron(color)
    stdscr.addstr(h - 1, 0, " " * (w - 1))
    stdscr.addstr(h - 1, 1, message[:w - hint_len - 2])
    stdscr.attron(curses.A_REVERSE)
    stdscr.addstr(h - 1, w - hint_len - 1, nav_hint)
    stdscr.attroff(curses.A_REVERSE)
    stdscr.attroff(color)

def run_menu(stdscr, title, options, sub_title=""):
    current_idx = 0
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        draw_header(stdscr, title)
        if sub_title:
            stdscr.addstr(4, (w - len(sub_title)) // 2, sub_title)
        draw_status(stdscr, "Επιλέξτε μια επιλογή.")
        
        for i, option in enumerate(options):
            display_option = option
            if len(option) > w - 8:
                display_option = option[:w - 11] + "..."
            x = (w - len(display_option)) // 2 - 2
            y = h // 2 - len(options) // 2 + i
            if i == current_idx:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, x, f"> {display_option} <")
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(y, x, f"  {display_option}  ")
        
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP:
            current_idx = (current_idx - 1) % len(options)
        elif key == curses.KEY_DOWN:
            current_idx = (current_idx + 1) % len(options)
        elif key in [curses.KEY_ENTER, 10, 13]:
            return options[current_idx]
        elif key == ord('q'):
            return None

def run_file_selector(stdscr, folder_path, title, input_folder_name):
    try:
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        files.sort()
    except Exception as e:
        draw_status(stdscr, f"Σφάλμα ανάγνωσης {folder_path}: {e}", is_error=True)
        stdscr.getch()
        return None
    
    if not files:
        draw_status(stdscr, f"Δεν βρέθηκαν αρχεία στον φάκελο {os.path.basename(folder_path)}", is_error=True)
        stdscr.getch()
        return None
        
    options = ["[ .. Επιστροφή .. ]"]
    
    if input_folder_name in IMAGE_FOLDERS:
        options.append(f"[ ** Μετατροπή ΟΛΩΝ των {len(files)} Εικόνων στον φάκελο '{input_folder_name}' σε ένα PDF ** ]")
    
    options.extend(files)
    # --- ΤΡΟΠΟΠΟΙΗΜΕΝΟ: Ενημερωμένη διαδρομή στον υπότιτλο ---
    selection = run_menu(stdscr, title, options, f"Φάκελος: /Download/File Converter/{input_folder_name}")
    if selection == "[ .. Επιστροφή .. ]":
        return None
    return selection

def run_confirmation(stdscr, prompt):
    options = ["Ναι", "Όχι"]
    selection = run_menu(stdscr, prompt, options, "Παρακαλώ επιβεβαιώστε")
    return selection

def run_help(stdscr):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    draw_header(stdscr, "Πώς να Χρησιμοποιήσετε")
    help_text = [
        "Αυτός ο μετατροπέας χρησιμοποιεί μια απλή διαδικασία 3 βημάτων:",
        "",
        "1. ΜΕΤΑΚΙΝΗΣΤΕ ΤΑ ΑΡΧΕΙΑ ΣΑΣ:",
        "   Χρησιμοποιήστε τη Διαχείριση Αρχείων του τηλεφώνου σας. Μεταβείτε στο:",
        # --- ΤΡΟΠΟΠΟΙΗΜΕΝΟ: Ενημερωμένη διαδρομή στο κείμενο βοήθειας ---
        f"   /Download/File Converter/",
        "   Μετακινήστε αρχεία στον σωστό φάκελο (π.χ., μετακινήστε",
        "   το 'report.docx' στον φάκελο 'DOCX').",
        "",
        "2. ΕΚΤΕΛΕΣΤΕ ΑΥΤΟΝ ΤΟΝ ΜΕΤΑΤΡΟΠΕΑ:",
        "   Επιλέξτε 'Μετατροπή Αρχείου' από το κύριο μενού.",
        "",
        "3. ΑΚΟΛΟΥΘΗΣΤΕ ΤΙΣ ΟΔΗΓΙΕΣ:",
        "   Βήμα 1: Επιλέξτε τον φάκελο ΕΙΣΟΔΟΥ (π.χ., 'DOCX').",
        "   Βήμα 2: Επιλέξτε το αρχείο που θέλετε να μετατρέψετε.",
        "   Βήμα 3: Επιλέξτε τη ΜΟΡΦΗ ΕΞΟΔΟΥ (π.χ., 'PDF').",
        "",
        "** ΕΙΔΙΚΕΣ ΜΕΤΑΤΡΟΠΕΣ **",
        " - Αρχεία (ZIP, RAR, 7Z, TAR): Επιλέξτε 'ZIP' -> 'file.zip' -> 'ZIP'",
        "   Αυτό θα εξαγάγει το 'file.zip' σε έναν νέο φάκελο: /ZIP/file/",
        " - PDF Πολλαπλών Εικόνων: Επιλέξτε 'JPG' -> '[ ** Μετατροπή ΟΛΩΝ... ** ]'",
        "   Αυτό συνδυάζει όλες τις εικόνες στον φάκελο 'JPG' σε ένα PDF.",
        " - Δεδομένα: Μπορείτε να μετατρέψετε CSV <-> JSON.",
        " - Ήχος/Βίντεο: Οι μετατροπές ήχου/βίντεο απαιτούν 'ffmpeg' (δείτε την έναρξη)."
    ]
    for i, line in enumerate(help_text):
        if 5 + i >= h - 2: break # Σταματά αν είναι πολύ μεγάλο για την οθόνη
        stdscr.addstr(5 + i, (w - len(line)) // 2, line)
    draw_status(stdscr, "Πατήστε 'q' ή Enter για επιστροφή.")
    stdscr.refresh()
    while True:
        key = stdscr.getch()
        if key in [ord('q'), curses.KEY_ENTER, 10, 13]:
            return

def run_text_input(stdscr, prompt):
    # (Αμετάβλητο)
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    draw_header(stdscr, "Απαιτείται Εισαγωγή")
    stdscr.addstr(h // 2 - 1, (w - len(prompt)) // 2, prompt)
    box_y, box_x = h // 2 + 1, w // 2 - 20
    stdscr.attron(curses.color_pair(2))
    stdscr.addstr(box_y, box_x, " " * 40)
    stdscr.attroff(curses.color_pair(2))
    draw_status(stdscr, "Πληκτρολογήστε το όνομα αρχείου (χωρίς επέκταση). Πατήστε Enter όταν τελειώσετε.")
    curses.curs_set(1)
    stdscr.keypad(True)
    text = ""
    while True:
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(box_y, box_x, " " * 40)
        stdscr.addstr(box_y, box_x + 1, text[:38])
        stdscr.attroff(curses.color_pair(2))
        stdscr.move(box_y, box_x + 1 + len(text))
        stdscr.refresh()
        key = stdscr.getch()
        if key in [curses.KEY_ENTER, 10, 13]:
            break
        elif key == ord('q'):
            text = None; break
        elif key in [curses.KEY_BACKSPACE, 127, 8]:
            text = text[:-1]
        elif 32 <= key <= 126:
            if len(text) < 38: text += chr(key)
    curses.curs_set(0); stdscr.keypad(False); return text

def run_multi_image_to_pdf_wizard(stdscr, input_folder_path, input_folder_name):
    # (Αμετάβλητο)
    try:
        image_paths = [
            os.path.join(input_folder_path, f) 
            for f in os.listdir(input_folder_path) 
            if os.path.splitext(f)[1].lower() in IMAGE_EXTS
        ]
        image_paths.sort()
    except Exception as e:
        draw_status(stdscr, f"Σφάλμα ανάγνωσης εικόνων: {e}", is_error=True); stdscr.getch(); return
    if not image_paths:
        draw_status(stdscr, "Δεν βρέθηκαν εικόνες σε αυτόν τον φάκελο.", is_error=True); stdscr.getch(); return
    confirm = run_confirmation(stdscr, f"Συνδυασμός όλων των {len(image_paths)} εικόνων στον φάκελο '{input_folder_name}' σε ένα PDF;")
    if confirm != "Ναι": return
    default_name = f"{input_folder_name}_Album"
    filename = run_text_input(stdscr, f"Εισάγετε ένα όνομα για το PDF (προεπιλογή: {default_name})")
    if filename is None: return
    if not filename: filename = default_name
    out_folder_path = os.path.join(BASE_CONVERTER_PATH, "PDF")
    out_path = os.path.join(out_folder_path, f"{filename}.pdf")
    draw_status(stdscr, "Εργασία... συνδυασμός εικόνων σε PDF..."); stdscr.refresh()
    try:
        handle_multi_image_to_pdf(stdscr, image_paths, out_path)
        draw_status(stdscr, f"Επιτυχία! Αποθηκεύτηκε σε: /PDF/{filename}.pdf")
    except Exception as e:
        draw_status(stdscr, f"ΣΦΑΛΜΑ: {e}", is_error=True)
    stdscr.getch()

# --- 7. ΚΥΡΙΑ ΕΦΑΡΜΟΓΗ CURSES ---

def main(stdscr):
    # (Αμετάβλητο)
    curses.curs_set(0); stdscr.nodelay(0); stdscr.timeout(-1)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK) # Επισήμανση
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE) # Κεφαλίδα/Υποσέλιδο
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_RED)   # Σφάλμα

    while True:
        main_choice = run_menu(stdscr, "Κύριο Μενού", ["Μετατροπή Αρχείου", "Βοήθεια / Πώς να Χρησιμοποιήσετε", "Έξοδος"])
        if main_choice == "Έξοδος" or main_choice is None: break
        if main_choice == "Βοήθεια / Πώς να Χρησιμοποιήσετε": run_help(stdscr); continue
            
        input_folder = run_menu(stdscr, "Βήμα 1: Επιλογή Φακέλου ΕΙΣΟΔΟΥ", FOLDER_NAMES)
        if input_folder is None: continue
        input_folder_path = os.path.join(BASE_CONVERTER_PATH, input_folder)
        input_file = run_file_selector(stdscr, input_folder_path, f"Βήμα 2: Επιλογή Αρχείου από '{input_folder}'", input_folder)
        if input_file is None: continue
        
        if input_file.startswith("[ ** Μετατροπή ΟΛΩΝ"):
            run_multi_image_to_pdf_wizard(stdscr, input_folder_path, input_folder)
            continue
            
        full_input_path = os.path.join(input_folder_path, input_file)
        
        # --- Ειδική Περίπτωση: Εξαγωγή Αρχείου ---
        in_ext = os.path.splitext(input_file)[1].lower()
        if in_ext in ARCHIVE_EXTS:
            # Για αρχεία, ο "φάκελος εξόδου" είναι απλά ο φάκελος του ίδιου τύπου
            # π.χ., εξαγωγή ενός αρχείου ZIP στον φάκελο "ZIP".
            output_folder = input_folder
            prompt = f"Εξαγωγή '{input_file}' στον '/{output_folder}/';"
            if in_ext not in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']:
                output_folder = input_folder # Ασφάλεια
                
        else:
            # --- Κανονική Διαδρομή Μετατροπής ---
            output_folder = run_menu(stdscr, "Βήμα 3: Επιλογή Μορφής/Φακέλου ΕΞΟΔΟΥ", FOLDER_NAMES)
            if output_folder is None: continue
            if output_folder == input_folder:
                draw_status(stdscr, "Σφάλμα: Ο φάκελος εισόδου και εξόδου δεν μπορεί να είναι ο ίδιος.", is_error=True)
                stdscr.getch(); continue
            prompt = f"Μετατροπή '{input_file}' σε μορφή {output_folder};"
             
        confirm = run_confirmation(stdscr, prompt)
        if confirm != "Ναι": continue

        draw_status(stdscr, "Εργασία, παρακαλώ περιμένετε..."); stdscr.refresh()
        success, message = convert_file(stdscr, full_input_path, output_folder)
        draw_status(stdscr, message, is_error=not success)
        stdscr.getch()

# --- 8. ΣΗΜΕΙΟ ΕΝΑΡΞΗΣ ΣΚΡΙΠΤ ---

if __name__ == "__main__":
    try:
        clear_screen_standard()
        print("--- Αρχικοποίηση Termux Converter v3.1 (40 Μορφές) ---")
        check_and_install_dependencies()
        check_external_bins()
        check_storage_access()
        setup_folders()
        
        print("--- Ρύθμιση Ολοκληρώθηκε ---")
        # --- ΤΡΟΠΟΠΟΙΗΜΕΝΟ: Ενημερωμένο μήνυμα τελικής διαδρομής ---
        print(f"Οι φάκελοι οργάνωσης είναι έτοιμοι στο: /storage/emulated/0/Download/File Converter/")
        print("\nΕκκίνηση εφαρμογής...")
        time.sleep(1)
        
        curses.wrapper(main)
        print("Ο Μετατροπέας Αρχείων τερμάτισε επιτυχώς.")

    except KeyboardInterrupt:
        print("\nΈξοδος...")
    except Exception as e:
        print("\nΠροέκυψε ένα κρίσιμο σφάλμα:")
        traceback.print_exc()
    finally:
        os.system('clear')