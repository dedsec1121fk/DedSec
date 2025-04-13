#!/usr/bin/env python3
import curses
import base64
import os
import getpass
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2

# Minimum password length
MIN_PASSWORD_LENGTH = 8

def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derives a 64-byte (512-bit) key using PBKDF2-HMAC-SHA512.
    AES-256 requires only 32 bytes, so we take the first half.
    """
    key = PBKDF2(password, salt, dkLen=64, count=200000, hmac_hash_module=None)
    return key[:32]  # Use the first 32 bytes for AES-256

def encrypt(plaintext: str, password: str) -> str:
    """
    Encrypts plaintext using AES-256-GCM.
    Format: salt (16 bytes) + nonce (16 bytes) + tag (16 bytes) + ciphertext (variable length)
    Encodes the final output using URL-safe Base64.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return "Error: Password must be at least 8 characters."

    salt = get_random_bytes(16)  # 16-byte salt
    key = derive_key(password, salt)
    cipher = AES.new(key, AES.MODE_GCM)  # AES-GCM mode
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())
    encrypted_data = salt + cipher.nonce + tag + ciphertext
    return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')

def decrypt(encrypted_text: str, password: str) -> str:
    """
    Decrypts a Base64-encoded string produced by the encrypt() function.
    Returns the plaintext or an error message if decryption fails.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return "Error: Password must be at least 8 characters."

    try:
        encrypted_data = base64.urlsafe_b64decode(encrypted_text)
        salt = encrypted_data[:16]
        nonce = encrypted_data[16:32]
        tag = encrypted_data[32:48]
        ciphertext = encrypted_data[48:]
        key = derive_key(password, salt)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext.decode('utf-8')
    except Exception:
        return "Decryption failed: Incorrect password or corrupted data."

def menu(stdscr):
    """
    Displays a menu using curses. The user navigates using arrow keys and selects an option with Enter.
    Returns the selected menu option.
    """
    curses.curs_set(0)  # Hide the cursor
    stdscr.clear()
    stdscr.refresh()
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

    options = ["Encrypt A Message", "Decrypt A Message", "Exit"]
    current_row = 0

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        for idx, row in enumerate(options):
            x = w // 2 - len(row) // 2
            y = h // 2 - len(options) // 2 + idx
            if idx == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, x, row)
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(y, x, row)
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(options) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, ord("\n")]:
            return options[current_row]

def get_valid_password():
    """ Prompts for a password, ensuring it meets the minimum length requirement. """
    while True:
        password = getpass.getpass("Enter password (at least 8 characters): ")
        if len(password) >= MIN_PASSWORD_LENGTH:
            return password
        print("Error: Password must be at least 8 characters. Try again.")

def main():
    while True:
        selected_option = curses.wrapper(menu)
        print(f"\nSelected Option: {selected_option}\n")
        if selected_option == "Exit":
            print("Exiting...")
            break
        elif selected_option == "Encrypt A Message":
            plaintext = input("Enter the message to encrypt: ")
            password = get_valid_password()
            encrypted = encrypt(plaintext, password)
            print("\nEncrypted message:")
            print(encrypted)
        elif selected_option == "Decrypt A Message":
            encrypted_text = input("Enter the message to decrypt: ")
            password = get_valid_password()
            decrypted = decrypt(encrypted_text, password)
            print("\nDecrypted message:")
            print(decrypted)

        input("\nPress Enter to return to the menu...")

if __name__ == "__main__":
    main()
