#!/usr/bin/env python3
# ——— sanitize self for non-breaking spaces ———

import os
import sys

def sanitize_source(path):
    with open(path, 'rb') as f:
        data = f.read()
    cleaned = data.replace(b'\xc2\xa0', b' ')
    if cleaned != data:
        with open(path, 'wb') as f:
            f.write(cleaned)

if __name__ == '__main__' and __file__.endswith('.py'):
    sanitize_source(__file__)
    os.execv(sys.executable, [sys.executable] + sys.argv)

# ——— end sanitizer ———

import time
import sys

def loading_bar(task_name, duration=5):
    sys.stdout.write(f"{task_name} [")
    sys.stdout.flush()
    for i in range(30):
        time.sleep(duration / 30)
        sys.stdout.write("=")
        sys.stdout.flush()
    sys.stdout.write("] Done!\n")

def show_loading_screen():
    os.system("clear")
    print("Initializing DedSec Module...")
    time.sleep(1)
    loading_bar("Loading core")
    loading_bar("Establishing secure shell")
    loading_bar("Decrypting scripts")
    loading_bar("Finalizing")
    print("\nDedSec Module Loaded Successfully.")

try:
    show_loading_screen()
except KeyboardInterrupt:
    print("\nOperation cancelled by user.")
