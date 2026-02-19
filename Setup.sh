#!/data/data/com.termux/files/usr/bin/bash
set -e

# DedSec / Termux full dependency installer
# Installs Termux packages + Python modules required by everything in ./Scripts

echo "[1/6] Termux storage + updates"
termux-setup-storage || true
pkg update -y && pkg upgrade -y

echo "[2/6] Installing core Termux packages"
# Notes:
# - python-cryptography is installed via pkg (recommended on Termux)
# - CairoSVG often needs cairo/pango/gdk-pixbuf runtime libs
# - rarfile may need an unrar backend (unrar/bsdtar). We install unrar if available.
CORE_PACKAGES="\
  aapt clang cloudflared curl ffmpeg fzf git jq nano ncurses nodejs openssh openssl openssl-tool \
  proot python rust termux-api unzip wget zip tor \
  libffi libxml2 libxslt \
  cairo pango gdk-pixbuf \
  unrar\
"

# Python-related Termux packages (use pkg when possible to avoid build issues)
PY_PKG_PACKAGES="\
  python-cryptography \
  python-lxml \
  python-pillow \
  python-numpy \
  python-pandas \
  python-psutil\
"

# Continue even if some packages don't exist on the user's repo/mirror
pkg install -y $CORE_PACKAGES $PY_PKG_PACKAGES || true

echo "[3/6] Upgrading pip tooling"
python -m pip install --upgrade pip setuptools wheel --break-system-packages

echo "[4/6] Installing Python modules used across all Scripts"
# Pinned as names (no versions) so it stays compatible with Termux.
# (We prefer real distribution names; e.g. beautifulsoup4 not 'bs4'.)
PYTHON_PACKAGES="\
  blessed \
  beautifulsoup4 \
  cairosvg \
  colorama \
  dnspython \
  ebooklib \
  exifread \
  flask \
  flask-socketio \
  geopy \
  lxml \
  markdown \
  mutagen \
  numpy \
  odfpy \
  openpyxl \
  pandas \
  phonenumbers \
  playwright \
  psd-tools \
  psutil \
  py7zr \
  pycountry \
  pycryptodome \
  python-docx \
  python-dotenv \
  python-pptx \
  pytz \
  qrcode \
  rarfile \
  reportlab \
  requests \
  rich \
  striprtf \
  tldextract \
  urllib3 \
  validators \
  websocket-client \
  werkzeug \
  zxcvbn \
  pillow\
"

# Install all Python packages (continue on failures so the rest still installs)
python -m pip install --upgrade $PYTHON_PACKAGES --break-system-packages || true

echo "[5/6] Ensuring cryptography is present (Termux package)"
# Avoid pip-building cryptography on Termux. Prefer the Termux package.
pkg install -y python-cryptography || true

echo "[6/6] Optional: Playwright browser install (may not be supported on all Termux builds)"
python -m playwright install chromium || true

# --- Run Settings.py (kept from your original Setup.sh logic) ---
SCRIPT_PATH="./Scripts/Settings.py"
echo "\nAttempting to run: $SCRIPT_PATH"

if [ -f "$SCRIPT_PATH" ]; then
  python "$SCRIPT_PATH" || true
else
  echo "WARNING: $SCRIPT_PATH not found (run this setup from the project root that contains ./Scripts)."
fi

echo "\nDone. If any specific module still errors at runtime, paste the traceback and I’ll patch Setup.sh accordingly."
