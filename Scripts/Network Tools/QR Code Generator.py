import os
import re
import subprocess
import sys

# --- Installation Function (Same as before) ---
def install_and_import(package):
    """
    Checks if a package is installed and installs it if missing.
    The 'qrcode[pil]' installs both qrcode and Pillow (PIL) for image generation.
    """
    try:
        __import__(package)
        print(f"✅ Required package '{package}' is already installed.")
    except ImportError:
        print(f"📦 Package '{package}' not found. Installing now...")
        try:
            if package == 'qrcode':
                # Install qrcode with pil dependency for image saving
                subprocess.check_call([sys.executable, "-m", "pip", "install", "qrcode[pil]"])
            else:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            
            __import__(package)
            print(f"✅ Successfully installed '{package}'.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install '{package}'. Error: {e}")
            print("Please ensure 'pip' is installed and working in Termux.")
            sys.exit(1)

install_and_import('qrcode')
import qrcode 

# ----------------------------------------------------------------------
# --- Main Generator Function (Updated Path) ---
# ----------------------------------------------------------------------
def generate_qr_for_link():
    """Generates a QR code image and saves it inside a 'QR Codes' folder 
    within the phone's Downloads directory."""
    
    # 1. Resolve Downloads on Termux or desktop Linux.
    termux_downloads = os.path.expanduser("~/storage/downloads")
    if os.path.isdir(termux_downloads):
        downloads_path = termux_downloads
    else:
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
    folder_name = "QR Codes"
    output_dir = os.path.join(downloads_path, folder_name)
    
    data = input("Enter the link (URL) to encode: ")
    
    # 2. Create the folder if it doesn't exist
    print(f"Checking for output directory: {output_dir}")
    try:
        os.makedirs(output_dir, exist_ok=True)
        print("📁 Directory verified/created.")
    except Exception as e:
        print(f"❌ Error creating output directory: {e}")
        return

    # 3. Sanitize the link for use as a filename
    sanitized_link = re.sub(r'https?://', '', data).rstrip('/')
    sanitized_link = re.sub(r'[^\w.-]', '_', sanitized_link)
    
    file_name = f"{sanitized_link}.png"
    output_path = os.path.join(output_dir, file_name)
    
    # --- QR Code Generation ---
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 4. Save the QR code image
    try:
        img.save(output_path)
        print(f"\n✨ Success! QR Code generated for '{data}'")
        print(f"Saved to: **Downloads/QR Codes/{file_name}**")
        print(f"Full path: {output_path}")
    except Exception as e:
        print(f"\n❌ Error saving file: {e}")

if __name__ == "__main__":
    generate_qr_for_link()