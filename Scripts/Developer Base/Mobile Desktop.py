#!/usr/bin/env python3
"""
Termux Linux Desktop Manager ULTIMATE v8 (no root)
==================================================

Adds Program Manager (cross-distro, best-effort):
- List & Install programs (per installed distro)
- Remove programs
- Update distro + programs (full upgrade)

Works only with distros supported by Termux `proot-distro`.
Desktop/VNC/X11 features remain.

Security:
- VNC LAN access is OFF by default (localhost only).
"""

import os
import re
import json
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

APP_DIR = Path.home() / ".termux_linux_vnc_manager"
CONFIG_PATH = APP_DIR / "config.json"

DEFAULT_CONFIG = {
    "language": "en",
    "systems": {}  # per distro settings + installed programs (tracked best-effort)
}

GEOMETRY_PRESETS = [
    "800x600",
    "1024x600",
    "1280x720",
    "1366x768",
    "1600x900",
    "1920x1080",
]

DESKTOP_CHOICES = ["xfce", "fluxbox", "lxde", "openbox"]

# ----------------------------
# Program Catalog (best-effort)
# Each item provides install/remove/update commands per distro family.
# Families: debian, arch, alpine, fedora, suse, void, unknown
# ----------------------------

PROGRAMS = [
    {
        "id": "libreoffice",
        "en": "LibreOffice (Full Office Suite)",
        "desc_en": "Writer/Calc/Impress. Heavy but complete.",
        "cmd": {
            "debian": {
                "install": "apt-get update -y && apt-get install -y libreoffice || apt-get install -y libreoffice-writer libreoffice-calc libreoffice-impress",
                "remove": "apt-get remove -y libreoffice libreoffice-writer libreoffice-calc libreoffice-impress || true && apt-get autoremove -y || true",
            },
            "arch": {
                "install": "pacman -Syu --noconfirm || true; pacman -S --noconfirm libreoffice-fresh || pacman -S --noconfirm libreoffice-still",
                "remove": "pacman -Rns --noconfirm libreoffice-fresh libreoffice-still || true",
            },
            "alpine": {
                "install": "apk update && apk add libreoffice || apk add libreoffice-writer libreoffice-calc libreoffice-impress",
                "remove": "apk del libreoffice libreoffice-writer libreoffice-calc libreoffice-impress || true",
            },
            "fedora": {
                "install": "dnf -y upgrade || true; dnf -y install libreoffice",
                "remove": "dnf -y remove libreoffice || true",
            },
            "suse": {
                "install": "zypper --non-interactive refresh || true; zypper --non-interactive install libreoffice",
                "remove": "zypper --non-interactive remove libreoffice || true",
            },
            "void": {
                "install": "xbps-install -Suy || true; xbps-install -y libreoffice",
                "remove": "xbps-remove -Ry libreoffice || true",
            },
        },
    },
    {
        "id": "office_light",
        "en": "Light Office (AbiWord + Gnumeric)",
        "desc_en": "Much lighter than LibreOffice. Good for weak phones.",
        "cmd": {
            "debian": {
                "install": "apt-get update -y && apt-get install -y abiword gnumeric",
                "remove": "apt-get remove -y abiword gnumeric || true && apt-get autoremove -y || true",
            },
            "arch": {
                "install": "pacman -Syu --noconfirm || true; pacman -S --noconfirm abiword gnumeric",
                "remove": "pacman -Rns --noconfirm abiword gnumeric || true",
            },
            "alpine": {
                "install": "apk update && apk add abiword gnumeric",
                "remove": "apk del abiword gnumeric || true",
            },
            "fedora": {
                "install": "dnf -y upgrade || true; dnf -y install abiword gnumeric",
                "remove": "dnf -y remove abiword gnumeric || true",
            },
            "suse": {
                "install": "zypper --non-interactive refresh || true; zypper --non-interactive install abiword gnumeric",
                "remove": "zypper --non-interactive remove abiword gnumeric || true",
            },
            "void": {
                "install": "xbps-install -Suy || true; xbps-install -y abiword gnumeric",
                "remove": "xbps-remove -Ry abiword gnumeric || true",
            },
        },
    },
    {
        "id": "firefox",
        "en": "Firefox Browser",
        "desc_en": "Full browser (may be heavy).",
        "cmd": {
            "debian": {
                "install": "apt-get update -y && (apt-get install -y firefox-esr || apt-get install -y firefox)",
                "remove": "apt-get remove -y firefox-esr firefox || true && apt-get autoremove -y || true",
            },
            "arch": {
                "install": "pacman -Syu --noconfirm || true; pacman -S --noconfirm firefox",
                "remove": "pacman -Rns --noconfirm firefox || true",
            },
            "alpine": {
                "install": "apk update && apk add firefox-esr || apk add firefox",
                "remove": "apk del firefox-esr firefox || true",
            },
            "fedora": {
                "install": "dnf -y upgrade || true; dnf -y install firefox",
                "remove": "dnf -y remove firefox || true",
            },
            "suse": {
                "install": "zypper --non-interactive refresh || true; zypper --non-interactive install MozillaFirefox",
                "remove": "zypper --non-interactive remove MozillaFirefox || true",
            },
            "void": {
                "install": "xbps-install -Suy || true; xbps-install -y firefox",
                "remove": "xbps-remove -Ry firefox || true",
            },
        },
    },
    {
        "id": "chromium",
        "en": "Chromium Browser",
        "desc_en": "Open-source Chrome-based browser.",
        "cmd": {
            "debian": {
                "install": "apt-get update -y && apt-get install -y chromium || apt-get install -y chromium-browser",
                "remove": "apt-get remove -y chromium chromium-browser || true && apt-get autoremove -y || true",
            },
            "arch": {
                "install": "pacman -Syu --noconfirm || true; pacman -S --noconfirm chromium",
                "remove": "pacman -Rns --noconfirm chromium || true",
            },
            "alpine": {
                "install": "apk update && apk add chromium",
                "remove": "apk del chromium || true",
            },
            "fedora": {
                "install": "dnf -y upgrade || true; dnf -y install chromium",
                "remove": "dnf -y remove chromium || true",
            },
            "suse": {
                "install": "zypper --non-interactive refresh || true; zypper --non-interactive install chromium",
                "remove": "zypper --non-interactive remove chromium || true",
            },
            "void": {
                "install": "xbps-install -Suy || true; xbps-install -y chromium",
                "remove": "xbps-remove -Ry chromium || true",
            },
        },
    },
    {
        "id": "vlc",
        "en": "VLC Media Player",
        "desc_en": "Media player for many formats.",
        "cmd": {
            "debian": {"install": "apt-get update -y && apt-get install -y vlc", "remove": "apt-get remove -y vlc || true && apt-get autoremove -y || true"},
            "arch": {"install": "pacman -Syu --noconfirm || true; pacman -S --noconfirm vlc", "remove": "pacman -Rns --noconfirm vlc || true"},
            "alpine": {"install": "apk update && apk add vlc", "remove": "apk del vlc || true"},
            "fedora": {"install": "dnf -y upgrade || true; dnf -y install vlc", "remove": "dnf -y remove vlc || true"},
            "suse": {"install": "zypper --non-interactive refresh || true; zypper --non-interactive install vlc", "remove": "zypper --non-interactive remove vlc || true"},
            "void": {"install": "xbps-install -Suy || true; xbps-install -y vlc", "remove": "xbps-remove -Ry vlc || true"},
        },
    },
    {
        "id": "gimp",
        "en": "GIMP (Image Editor)",
        "desc_en": "Advanced image editor.",
        "cmd": {
            "debian": {"install": "apt-get update -y && apt-get install -y gimp", "remove": "apt-get remove -y gimp || true && apt-get autoremove -y || true"},
            "arch": {"install": "pacman -Syu --noconfirm || true; pacman -S --noconfirm gimp", "remove": "pacman -Rns --noconfirm gimp || true"},
            "alpine": {"install": "apk update && apk add gimp", "remove": "apk del gimp || true"},
            "fedora": {"install": "dnf -y upgrade || true; dnf -y install gimp", "remove": "dnf -y remove gimp || true"},
            "suse": {"install": "zypper --non-interactive refresh || true; zypper --non-interactive install gimp", "remove": "zypper --non-interactive remove gimp || true"},
            "void": {"install": "xbps-install -Suy || true; xbps-install -y gimp", "remove": "xbps-remove -Ry gimp || true"},
        },
    },
    {
        "id": "inkscape",
        "en": "Inkscape (Vector)",
        "desc_en": "Vector graphics editor.",
        "cmd": {
            "debian": {"install": "apt-get update -y && apt-get install -y inkscape", "remove": "apt-get remove -y inkscape || true && apt-get autoremove -y || true"},
            "arch": {"install": "pacman -Syu --noconfirm || true; pacman -S --noconfirm inkscape", "remove": "pacman -Rns --noconfirm inkscape || true"},
            "alpine": {"install": "apk update && apk add inkscape", "remove": "apk del inkscape || true"},
            "fedora": {"install": "dnf -y upgrade || true; dnf -y install inkscape", "remove": "dnf -y remove inkscape || true"},
            "suse": {"install": "zypper --non-interactive refresh || true; zypper --non-interactive install inkscape", "remove": "zypper --non-interactive remove inkscape || true"},
            "void": {"install": "xbps-install -Suy || true; xbps-install -y inkscape", "remove": "xbps-remove -Ry inkscape || true"},
        },
    },
    {
        "id": "dev_tools",
        "en": "Dev Tools (git + python + node)",
        "desc_en": "Useful tools for coding.",
        "cmd": {
            "debian": {"install": "apt-get update -y && apt-get install -y git python3 python3-pip nodejs npm", "remove": "apt-get remove -y git python3 python3-pip nodejs npm || true && apt-get autoremove -y || true"},
            "arch": {"install": "pacman -Syu --noconfirm || true; pacman -S --noconfirm git python python-pip nodejs npm", "remove": "pacman -Rns --noconfirm git python python-pip nodejs npm || true"},
            "alpine": {"install": "apk update && apk add git python3 py3-pip nodejs npm", "remove": "apk del git python3 py3-pip nodejs npm || true"},
            "fedora": {"install": "dnf -y upgrade || true; dnf -y install git python3 python3-pip nodejs npm", "remove": "dnf -y remove git python3 python3-pip nodejs npm || true"},
            "suse": {"install": "zypper --non-interactive refresh || true; zypper --non-interactive install git python3 python3-pip nodejs npm", "remove": "zypper --non-interactive remove git python3 python3-pip nodejs npm || true"},
            "void": {"install": "xbps-install -Suy || true; xbps-install -y git python3 python3-pip nodejs npm", "remove": "xbps-remove -Ry git python3 python3-pip nodejs npm || true"},
        },
    },
    {
        "id": "system_utils",
        "en": "System Utils (htop + fastfetch/neofetch)",
        "desc_en": "Monitoring + system info.",
        "cmd": {
            "debian": {"install": "apt-get update -y && apt-get install -y htop fastfetch || apt-get install -y htop neofetch", "remove": "apt-get remove -y htop fastfetch neofetch || true && apt-get autoremove -y || true"},
            "arch": {"install": "pacman -Syu --noconfirm || true; pacman -S --noconfirm htop fastfetch || pacman -S --noconfirm htop neofetch", "remove": "pacman -Rns --noconfirm htop fastfetch neofetch || true"},
            "alpine": {"install": "apk update && apk add htop fastfetch || apk add htop neofetch", "remove": "apk del htop fastfetch neofetch || true"},
            "fedora": {"install": "dnf -y upgrade || true; dnf -y install htop fastfetch || dnf -y install htop neofetch", "remove": "dnf -y remove htop fastfetch neofetch || true"},
            "suse": {"install": "zypper --non-interactive refresh || true; zypper --non-interactive install htop fastfetch || zypper --non-interactive install htop neofetch", "remove": "zypper --non-interactive remove htop fastfetch neofetch || true"},
            "void": {"install": "xbps-install -Suy || true; xbps-install -y htop fastfetch || xbps-install -y htop neofetch", "remove": "xbps-remove -Ry htop fastfetch neofetch || true"},
        },
    },
]


# ----------------------------
# Extended GUI App Catalog (best-effort)
# Adds many more GUI apps as selectable options.
# Notes:
# - Apps are installed INSIDE the selected proot-distro (recommended).
# - Availability varies by distro + repo; if install fails, try Ubuntu/Debian.
# ----------------------------

CATEGORIES = [
    "Desktop & Window Managers",
    "File Managers",
    "Internet",
    "Office & Productivity",
    "Graphics & Design",
    "Media",
    "Messaging",
    "Development",
    "Utilities",
    "Books & PDF",
    "Games",
]

def _mk_cmds(pkgs_deb=None, pkgs_arch=None, pkgs_alpine=None, pkgs_fedora=None, pkgs_suse=None, pkgs_void=None,
             deb_override=None, arch_override=None, alpine_override=None, fedora_override=None, suse_override=None, void_override=None):
    """Build install/remove commands per distro family.
    Provide either package list/string or an override command for a family.
    """
    def _pkgs(x):
        if x is None:
            return None
        if isinstance(x, (list, tuple)):
            return " ".join(x)
        return str(x).strip()

    cmd = {}

    # Debian/Ubuntu
    if deb_override:
        cmd["debian"] = {"install": deb_override, "remove": "true"}
    else:
        pk = _pkgs(pkgs_deb)
        if pk:
            cmd["debian"] = {
                "install": f"export DEBIAN_FRONTEND=noninteractive; apt-get update -y && apt-get install -y {pk}",
                "remove": f"apt-get remove -y {pk} || true && apt-get autoremove -y || true",
            }

    # Arch
    if arch_override:
        cmd["arch"] = {"install": arch_override, "remove": "true"}
    else:
        pk = _pkgs(pkgs_arch)
        if pk:
            cmd["arch"] = {
                "install": f"pacman -Syu --noconfirm || true; pacman -S --noconfirm {pk}",
                "remove": f"pacman -Rns --noconfirm {pk} || true",
            }

    # Alpine
    if alpine_override:
        cmd["alpine"] = {"install": alpine_override, "remove": "true"}
    else:
        pk = _pkgs(pkgs_alpine)
        if pk:
            cmd["alpine"] = {
                "install": f"apk update && apk add {pk}",
                "remove": f"apk del {pk} || true",
            }

    # Fedora
    if fedora_override:
        cmd["fedora"] = {"install": fedora_override, "remove": "true"}
    else:
        pk = _pkgs(pkgs_fedora)
        if pk:
            cmd["fedora"] = {
                "install": f"dnf -y upgrade || true; dnf -y install {pk}",
                "remove": f"dnf -y remove {pk} || true",
            }

    # SUSE
    if suse_override:
        cmd["suse"] = {"install": suse_override, "remove": "true"}
    else:
        pk = _pkgs(pkgs_suse)
        if pk:
            cmd["suse"] = {
                "install": f"zypper --non-interactive refresh || true; zypper --non-interactive install {pk}",
                "remove": f"zypper --non-interactive remove {pk} || true",
            }

    # Void
    if void_override:
        cmd["void"] = {"install": void_override, "remove": "true"}
    else:
        pk = _pkgs(pkgs_void)
        if pk:
            cmd["void"] = {
                "install": f"xbps-install -Suy || true; xbps-install -y {pk}",
                "remove": f"xbps-remove -Ry {pk} || true",
            }

    return cmd

def _add_prog(pid, cat, en, desc_en, *,
              deb=None, arch=None, alpine=None, fedora=None, suse=None, void=None,
              deb_override=None, arch_override=None, alpine_override=None, fedora_override=None, suse_override=None, void_override=None):
    PROGRAMS.append({
        "id": pid,
        "cat": cat,
        "en": en,
        "desc_en": desc_en,
        "cmd": _mk_cmds(
            pkgs_deb=deb, pkgs_arch=arch, pkgs_alpine=alpine, pkgs_fedora=fedora, pkgs_suse=suse, pkgs_void=void,
            deb_override=deb_override, arch_override=arch_override, alpine_override=alpine_override,
            fedora_override=fedora_override, suse_override=suse_override, void_override=void_override,
        )
    })

# --- Desktop / window managers (extra choices)
_add_prog('de_xfce', 'Desktop & Window Managers', 'XFCE Desktop', 'Light and popular desktop.', deb=['xfce4', 'xfce4-goodies'], arch=['xfce4', 'xfce4-goodies'], alpine=['xfce4'], fedora=['@xfce-desktop-environment'], suse=['xfce4'], void=['xfce4'])
_add_prog('de_lxqt', 'Desktop & Window Managers', 'LXQt Desktop', 'Light Qt desktop.', deb=['lxqt', 'sddm'], arch=['lxqt'], alpine=['lxqt'], fedora=['lxqt'], suse=['lxqt'], void=['lxqt'])
_add_prog('de_mate', 'Desktop & Window Managers', 'MATE Desktop', 'Classic GNOME2-style desktop.', deb=['mate-desktop-environment'], arch=['mate', 'mate-extra'], alpine=['mate'], fedora=['@mate-desktop-environment'], suse=['mate'], void=['mate'])
_add_prog('wm_i3', 'Desktop & Window Managers', 'i3 (Tiling WM)', 'Keyboard-driven tiling window manager.', deb=['i3', 'i3status', 'dmenu'], arch=['i3-wm', 'i3status', 'dmenu'], alpine=['i3wm', 'i3status', 'dmenu'], fedora=['i3', 'i3status', 'dmenu'], suse=['i3', 'i3status', 'dmenu'], void=['i3', 'i3status', 'dmenu'])
_add_prog('wm_icewm', 'Desktop & Window Managers', 'IceWM', 'Very light window manager.', deb=['icewm'], arch=['icewm'], alpine=['icewm'], fedora=['icewm'], suse=['icewm'], void=['icewm'])
_add_prog('wm_tint2', 'Desktop & Window Managers', 'Tint2 Panel', 'Lightweight desktop panel/taskbar.', deb=['tint2'], arch=['tint2'], alpine=['tint2'], fedora=['tint2'], suse=['tint2'], void=['tint2'])

# --- File managers
_add_prog('fm_thunar', 'File Managers', 'Thunar (XFCE File Manager)', 'Fast, light file manager.', deb=['thunar'], arch=['thunar'], alpine=['thunar'], fedora=['thunar'], suse=['thunar'], void=['thunar'])
_add_prog('fm_pcmanfm', 'File Managers', 'PCManFM', 'Light file manager (LXDE/LXQt).', deb=['pcmanfm'], arch=['pcmanfm'], alpine=['pcmanfm'], fedora=['pcmanfm'], suse=['pcmanfm'], void=['pcmanfm'])
_add_prog('fm_nautilus', 'File Managers', 'Nautilus (GNOME Files)', 'GNOME file manager (heavier).', deb=['nautilus'], arch=['nautilus'], alpine=['nautilus'], fedora=['nautilus'], suse=['nautilus'], void=['nautilus'])
_add_prog('fm_dolphin', 'File Managers', 'Dolphin (KDE)', 'KDE file manager (feature-rich).', deb=['dolphin'], arch=['dolphin'], alpine=None, fedora=['dolphin'], suse=['dolphin'], void=['dolphin'])

# --- Internet
_add_prog('browser_epiphany', 'Internet', 'GNOME Web (Epiphany)', 'Lighter GNOME browser.', deb=['epiphany-browser'], arch=['epiphany'], alpine=['epiphany'], fedora=['epiphany'], suse=['epiphany'], void=['epiphany'])
_add_prog('browser_qutebrowser', 'Internet', 'qutebrowser', 'Keyboard-driven Qt browser.', deb=['qutebrowser'], arch=['qutebrowser'], alpine=['qutebrowser'], fedora=['qutebrowser'], suse=['qutebrowser'], void=['qutebrowser'])
_add_prog('torrent_qbittorrent', 'Internet', 'qBittorrent', 'Torrent client with GUI.', deb=['qbittorrent'], arch=['qbittorrent'], alpine=['qbittorrent'], fedora=['qbittorrent'], suse=['qbittorrent'], void=['qbittorrent'])
_add_prog('ftp_filezilla', 'Internet', 'FileZilla', 'FTP/SFTP client.', deb=['filezilla'], arch=['filezilla'], alpine=['filezilla'], fedora=['filezilla'], suse=['filezilla'], void=['filezilla'])
_add_prog('remote_remmina', 'Internet', 'Remmina (RDP/VNC)', 'Remote desktop client.', deb=['remmina'], arch=['remmina'], alpine=['remmina'], fedora=['remmina'], suse=['remmina'], void=['remmina'])

# --- Office & productivity
_add_prog('scribus', 'Office & Productivity', 'Scribus (DTP)', 'Desktop publishing (InDesign-style).', deb=['scribus'], arch=['scribus'], alpine=['scribus'], fedora=['scribus'], suse=['scribus'], void=['scribus'])
_add_prog('calibre', 'Office & Productivity', 'Calibre (E-book Manager)', 'Manage e-books, convert formats.', deb=['calibre'], arch=['calibre'], alpine=['calibre'], fedora=['calibre'], suse=['calibre'], void=['calibre'])
_add_prog('xournalpp', 'Office & Productivity', 'Xournal++ (PDF notes)', 'Annotate PDFs, handwritten notes.', deb=['xournalpp'], arch=['xournalpp'], alpine=['xournalpp'], fedora=['xournalpp'], suse=['xournalpp'], void=['xournalpp'])
_add_prog('keepassxc', 'Office & Productivity', 'KeePassXC (Password Manager)', 'Offline password manager.', deb=['keepassxc'], arch=['keepassxc'], alpine=['keepassxc'], fedora=['keepassxc'], suse=['keepassxc'], void=['keepassxc'])
_add_prog('thunderbird', 'Office & Productivity', 'Thunderbird (Email)', 'Email client.', deb=['thunderbird'], arch=['thunderbird'], alpine=['thunderbird'], fedora=['thunderbird'], suse=['MozillaThunderbird'], void=['thunderbird'])

# --- Graphics & design
_add_prog('gimp', 'Graphics & Design', 'GIMP', 'Image editor (Photoshop-style).', deb=['gimp'], arch=['gimp'], alpine=['gimp'], fedora=['gimp'], suse=['gimp'], void=['gimp'])
_add_prog('inkscape', 'Graphics & Design', 'Inkscape', 'Vector editor (Illustrator-style).', deb=['inkscape'], arch=['inkscape'], alpine=['inkscape'], fedora=['inkscape'], suse=['inkscape'], void=['inkscape'])
_add_prog('krita', 'Graphics & Design', 'Krita', 'Digital painting (heavy).', deb=['krita'], arch=['krita'], alpine=None, fedora=['krita'], suse=['krita'], void=['krita'])
_add_prog('blender', 'Graphics & Design', 'Blender', '3D modelling & animation (very heavy).', deb=['blender'], arch=['blender'], alpine=['blender'], fedora=['blender'], suse=['blender'], void=['blender'])

# --- Media
_add_prog('mpv', 'Media', 'mpv (Video Player)', 'Light media player.', deb=['mpv'], arch=['mpv'], alpine=['mpv'], fedora=['mpv'], suse=['mpv'], void=['mpv'])
_add_prog('audacity', 'Media', 'Audacity', 'Audio editor.', deb=['audacity'], arch=['audacity'], alpine=['audacity'], fedora=['audacity'], suse=['audacity'], void=['audacity'])
_add_prog('kdenlive', 'Media', 'Kdenlive', 'Video editor (heavy).', deb=['kdenlive'], arch=['kdenlive'], alpine=None, fedora=['kdenlive'], suse=['kdenlive'], void=['kdenlive'])
_add_prog('obs', 'Media', 'OBS Studio', 'Screen recording/streaming (heavy).', deb=['obs-studio'], arch=['obs-studio'], alpine=['obs-studio'], fedora=['obs-studio'], suse=['obs-studio'], void=['obs-studio'])
_add_prog('pavucontrol', 'Media', 'PulseAudio Volume Control', 'GUI sound mixer.', deb=['pavucontrol'], arch=['pavucontrol'], alpine=['pavucontrol'], fedora=['pavucontrol'], suse=['pavucontrol'], void=['pavucontrol'])

# --- Messaging
_add_prog('pidgin', 'Messaging', 'Pidgin', 'Multi-protocol chat client.', deb=['pidgin'], arch=['pidgin'], alpine=['pidgin'], fedora=['pidgin'], suse=['pidgin'], void=['pidgin'])
_add_prog('hexchat', 'Messaging', 'HexChat (IRC)', 'IRC client.', deb=['hexchat'], arch=['hexchat'], alpine=['hexchat'], fedora=['hexchat'], suse=['hexchat'], void=['hexchat'])
_add_prog('telegram', 'Messaging', 'Telegram Desktop', 'Telegram client (may be heavy).', deb=['telegram-desktop'], arch=['telegram-desktop'], alpine=['telegram-desktop'], fedora=['telegram-desktop'], suse=['telegram-desktop'], void=['telegram-desktop'])

# --- Development
_add_prog('geany', 'Development', 'Geany (Light IDE)', 'Light IDE/editor.', deb=['geany'], arch=['geany'], alpine=['geany'], fedora=['geany'], suse=['geany'], void=['geany'])
_add_prog('code_oss', 'Development', 'VSCodium (VSCode-like)', 'VSCode-like editor (repo-dependent).', deb=['codium'], arch=['code'], alpine=None, fedora=['codium'], suse=None, void=None)
_add_prog('kate', 'Development', 'Kate (KDE Editor)', 'Powerful text editor.', deb=['kate'], arch=['kate'], alpine=None, fedora=['kate'], suse=['kate'], void=['kate'])
_add_prog('gedit', 'Development', 'Gedit', 'GNOME text editor.', deb=['gedit'], arch=['gedit'], alpine=['gedit'], fedora=['gedit'], suse=['gedit'], void=['gedit'])
_add_prog('emacs_gui', 'Development', 'Emacs (GUI)', 'Emacs with GUI.', deb=['emacs'], arch=['emacs'], alpine=['emacs'], fedora=['emacs'], suse=['emacs'], void=['emacs'])
_add_prog('idle', 'Development', 'Python IDLE', 'Python simple IDE.', deb=['idle3'], arch=None, alpine=None, fedora=None, suse=None, void=None)

# --- Utilities
_add_prog('synaptic', 'Utilities', 'Synaptic (Package Manager)', 'GUI package manager (Debian/Ubuntu).', deb=['synaptic'], arch=None, alpine=None, fedora=None, suse=None, void=None)
_add_prog('gparted', 'Utilities', 'GParted', 'Partition editor (may be limited in proot).', deb=['gparted'], arch=['gparted'], alpine=['gparted'], fedora=['gparted'], suse=['gparted'], void=['gparted'])
_add_prog('bleachbit', 'Utilities', 'BleachBit', 'Cleaner (use carefully).', deb=['bleachbit'], arch=['bleachbit'], alpine=None, fedora=['bleachbit'], suse=None, void=None)
_add_prog('xfce_terminal', 'Utilities', 'XFCE Terminal', 'Terminal emulator.', deb=['xfce4-terminal'], arch=['xfce4-terminal'], alpine=['xfce4-terminal'], fedora=['xfce4-terminal'], suse=['xfce4-terminal'], void=['xfce4-terminal'])
_add_prog('terminator', 'Utilities', 'Terminator Terminal', 'Terminal with split panes.', deb=['terminator'], arch=['terminator'], alpine=['terminator'], fedora=['terminator'], suse=['terminator'], void=['terminator'])

# --- Books & PDF
_add_prog('evince', 'Books & PDF', 'Evince (PDF Viewer)', 'GNOME document viewer.', deb=['evince'], arch=['evince'], alpine=['evince'], fedora=['evince'], suse=['evince'], void=['evince'])
_add_prog('okular', 'Books & PDF', 'Okular (PDF Viewer)', 'KDE document viewer.', deb=['okular'], arch=['okular'], alpine=None, fedora=['okular'], suse=['okular'], void=['okular'])

# --- Games (light options; may be heavy on phones)
_add_prog('supertux', 'Games', 'SuperTux', '2D platform game.', deb=['supertux'], arch=['supertux'], alpine=['supertux'], fedora=['supertux'], suse=['supertux'], void=['supertux'])
_add_prog('minetest', 'Games', 'Minetest', 'Open-source voxel sandbox.', deb=['minetest'], arch=['minetest'], alpine=['minetest'], fedora=['minetest'], suse=['minetest'], void=['minetest'])


def prog_name(cfg: Dict, p: Dict) -> str:
    return p.get("en", "")


def prog_desc(cfg: Dict, p: Dict) -> str:
    return p.get("desc_en", "")


# ----------------------------
# Translations (EN / GR)
# ----------------------------
T = {'en': {'title': 'Termux Linux Desktop Manager ULTIMATE v8 (no root)',
        'menu': ['Install A System',
                 'Remove A System',
                 'Change Settings To A System (only for downloaded ones)',
                 'VNC Options (Start/Stop/Info)',
                 'X11 Options (Termux:X11)',
                 'Programs: Display & Install',
                 'Programs: Remove',
                 'Update Distro + Programs',
                 'Install Recommended Extras (for a system)',
                 'Create / Update One-Command Launcher',
                 'Help',
                 'Exit'],
        'choose': 'Choose an option (number): ',
        'press_enter': 'Press Enter to continue...',
        'need_termux': 'This script is intended for Termux. (PREFIX not found)',
        'installing_pkg': 'Installing required Termux packages...',
        'proot_missing': 'proot-distro not found. Installing it now...',
        'fetching_distros': 'Fetching available systems from proot-distro...',
        'no_distros': 'No distros found. Make sure proot-distro works: `proot-distro list`',
        'available': 'Available systems (aliases from proot-distro):',
        'installed': 'Installed systems:',
        'none_installed': '(none installed)',
        'pick_system': 'Pick a system (number): ',
        'invalid': 'Invalid choice.',
        'install_start': 'Installing system:',
        'install_done': 'Install finished.',
        'remove_confirm': 'Type YES to remove this system: ',
        'remove_done': 'Removed.',
        'settings_title': 'System settings:',
        'settings_menu': ['Quick-pick VNC resolution preset',
                          'Set custom VNC resolution (geometry)',
                          'Change VNC color depth',
                          'Change desktop target (xfce / fluxbox / lxde / openbox)',
                          'Change VNC display number',
                          'Toggle LAN access (default: localhost only)',
                          'Toggle Auto-kill stale VNC on Start (default: ON)',
                          'Toggle termux-wake-lock on session start (default: ON)',
                          'Set / change VNC password',
                          'Re-apply setup inside the system (install desktop+VNC again)',
                          'Back'],
        'vnc_title': 'VNC Options:',
        'vnc_menu': ['Start VNC for a system',
                     'Stop VNC for a system',
                     'Restart VNC for a system',
                     'Show VNC status (list sessions)',
                     'Kill ALL VNC sessions in a system',
                     'Show connection info',
                     'Back'],
        'x11_title': 'Termux:X11 Options:',
        'x11_menu': ['Install Termux X11 packages (x11-repo + termux-x11)',
                     'Start desktop via Termux:X11 for a system',
                     'Stop Termux:X11 server (Termux side)',
                     'Show X11 connection info',
                     'Back'],
        'launcher_title': 'One-command launcher:',
        'launcher_menu': ['Create/Update launcher for a system (vnc-<system>)', 'List existing launchers', 'Back'],
        'enter_geometry': 'Enter geometry like 1280x720: ',
        'enter_depth': 'Enter depth (16 or 24 recommended): ',
        'enter_desktop': 'Enter desktop (xfce/fluxbox/lxde/openbox): ',
        'enter_display': 'Enter VNC display number (example 1): ',
        'lan_now': 'LAN access is now:',
        'lan_on': 'ENABLED (VNC accessible on LAN). Make sure you set a strong password!',
        'lan_off': 'DISABLED (localhost only, safest).',
        'autokill_now': 'Auto-kill stale VNC on start is now:',
        'autokill_on': 'ON (recommended).',
        'autokill_off': 'OFF.',
        'wakelock_now': 'termux-wake-lock on start is now:',
        'wakelock_on': 'ON (recommended).',
        'wakelock_off': 'OFF.',
        'saving': 'Saving...',
        'help_title': 'Help / VNC + Termux:X11 + Programs',
        'lang_now': 'Language set to:',
        'ask_vnc_pass': 'Set a VNC password now? (y/n): ',
        'ask_extras': 'Install recommended extras now? (y/n): ',
        'extras_installing': 'Installing recommended extras...',
        'extras_done': 'Recommended extras installed.',
        'vnc_pass_prompt': 'Enter VNC password (min 6 chars, not saved): ',
        'vnc_pass_short': 'Password too short. Skipping.',
        'setup_auto': 'Auto-setup based on phone specs:',
        'specs': 'Detected specs:',
        'ram': 'RAM',
        'cores': 'CPU cores',
        'storage': 'Free storage',
        'chosen': 'Chosen defaults:',
        'desktop': 'Desktop',
        'geometry': 'Geometry',
        'depth': 'Depth',
        'display': 'Display',
        'lan': 'LAN access',
        'autokill': 'Auto-kill stale VNC',
        'wakelock': 'termux-wake-lock',
        'running_setup': 'Running setup inside the system (this can take a while)...',
        'setup_done': 'Setup complete.',
        'setup_partial': 'Setup finished with warnings (some distros vary).',
        'termux_vnc_note': 'Tip: Connect using an Android VNC app (e.g., bVNC / RealVNC).',
        'connect_cmds': 'Connect info:',
        'hostname': 'Hostname',
        'ip_hint': 'If LAN is enabled, use your phone IP on Wi-Fi for remote devices.',
        'launcher_created': 'Launcher created/updated:',
        'launcher_fail': 'Could not create launcher (check permissions).',
        'launchers_found': 'Launchers found:',
        'none': '(none)',
        'recommend_note': 'This menu shows all systems supported by your Termux proot-distro build.',
        'preset_title': 'Choose a preset:',
        'x11_need_app': 'You must install and open the Termux:X11 Android app before using X11 mode.',
        'x11_installing': 'Installing Termux X11 packages in Termux...',
        'x11_done': 'X11 packages installed.',
        'x11_missing': 'termux-x11 not found. Install X11 packages first.',
        'x11_starting': 'Starting termux-x11 server on :0 (Termux side)...',
        'x11_started': 'termux-x11 started. Now starting desktop inside the system...',
        'x11_stopped': 'Stopped termux-x11 server (if it was running).',
        'x11_info': 'X11 info:',
        'programs_title': 'Programs (works best on major distros):',
        'programs_pick': 'Pick a program (number): ',
        'programs_none': 'No programs in catalog.',
        'programs_installing': 'Installing program:',
        'programs_removing': 'Removing program:',
        'programs_done': 'Done.',
        'programs_not_supported': "This program isn't mapped for your distro family yet.",
        'programs_installed_list': 'Installed programs (tracked):',
        'update_title': 'Updating system packages inside:',
        'update_done': 'Update finished.',
        'warn_large': 'Warning: Some programs are very large (LibreOffice, browsers).',
        'programs_browser_title': 'Program Browser:',
        'programs_browser_menu': ['Show ALL programs',
                                  'Pick a category',
                                  'Search by name',
                                  'Install custom package (type any package name)',
                                  'Back'],
        'programs_pick_category': 'Pick a category:',
        'programs_search_prompt': 'Search (name/category/description): ',
        'programs_custom_prompt': 'Package name (example: libreoffice): ',
        'programs_multi_hint': 'Tip: You can install multiple apps: 1,2,5   (or type 0 for custom package)',
        'programs_pick_multi': 'Pick program number(s): '}}


# ----------------------------
# Utilities
# ----------------------------
def load_config() -> Dict:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if "systems" not in cfg:
            cfg["systems"] = {}
        cfg["language"] = "en"
        return cfg
    except Exception:
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)

def save_config(cfg: Dict) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

def tr(cfg: Dict, key: str) -> str:
    lang = cfg.get("language", "en")
    return T.get(lang, T["en"]).get(key, key)

def pause(cfg: Dict) -> None:
    input(tr(cfg, "press_enter"))

def run(cmd: List[str], check: bool=True, capture: bool=False) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.setdefault("TERM", "dumb")
    if capture:
        return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=check, env=env)
    return subprocess.run(cmd, check=check, env=env)

def sh_quote(s: str) -> str:
    return "'" + s.replace("'", "'\"'\"'") + "'"

def get_prefix() -> Optional[str]:
    return os.environ.get("PREFIX")

def proot_exists() -> bool:
    return shutil.which("proot-distro") is not None

def ensure_termux_deps(cfg: Dict) -> bool:
    prefix = get_prefix()
    if not prefix:
        print(tr(cfg, "need_termux"))
        return False
    print(tr(cfg, "installing_pkg"))
    run(["pkg", "update", "-y"], check=False)
    run(["pkg", "install", "-y", "python", "proot-distro", "termux-tools", "coreutils", "procps"], check=False)
    return True

def ensure_termux_x11_packages(cfg: Dict) -> bool:
    if shutil.which("termux-x11") is not None:
        return True
    print(tr(cfg, "x11_installing"))
    run(["pkg", "install", "-y", "x11-repo"], check=False)
    run(["pkg", "install", "-y", "termux-x11"], check=False)
    ok = shutil.which("termux-x11") is not None
    if ok:
        print(tr(cfg, "x11_done"))
    return ok

def parse_distros_from_list_output(text: str) -> List[str]:
    # Extract ONLY aliases inside < ... > from proot-distro list output.
    text = re.sub(r"\x1b\[[0-9;?]*[ -/]*[@-~]", "", text)             # CSI
    text = re.sub(r"\x1b\][^\x07]*(\x07|\x1b\\)", "", text)           # OSC
    text = re.sub(r"\x1b\([A-Za-z0-9]", "", text)                     # ESC( B
    text = re.sub(r"\x1b\)[A-Za-z0-9]", "", text)                     # ESC) B

    distros: List[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        low = line.lower()
        if "proot-distro install" in low:
            continue
        for m in re.finditer(r"<\s*([a-z0-9._-]+)\s*>", line, flags=re.IGNORECASE):
            alias = m.group(1).strip().lower()
            if alias in ("alias", "aliases", "termux"):  # hide "termux" entry (not useful as a proot desktop)
                continue
            distros.append(alias)

    seen = set()
    out: List[str] = []
    for d in distros:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out

def get_available_distros(cfg: Dict) -> List[str]:
    print(tr(cfg, "fetching_distros"))
    if not proot_exists():
        print(tr(cfg, "proot_missing"))
        run(["pkg", "install", "-y", "proot-distro"], check=False)
    try:
        out = run(["proot-distro", "list"], capture=True, check=False).stdout
    except Exception:
        return []
    return parse_distros_from_list_output(out)

def get_installed_distros() -> List[str]:
    prefix = get_prefix()
    if not prefix:
        return []
    installed_root = Path(prefix) / "var" / "lib" / "proot-distro" / "installed-rootfs"
    if not installed_root.exists():
        return []
    return sorted([p.name for p in installed_root.iterdir() if p.is_dir()])

def read_mem_gb() -> Optional[float]:
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    kb = int(re.findall(r"\d+", line)[0])
                    return kb / 1024 / 1024
    except Exception:
        pass
    return None

def read_cpu_cores() -> int:
    try:
        return os.cpu_count() or 1
    except Exception:
        return 1

def read_free_storage_gb() -> Optional[float]:
    try:
        usage = shutil.disk_usage(str(Path.home()))
        return usage.free / (1024**3)
    except Exception:
        return None

def choose_defaults_by_specs() -> Dict:
    mem_gb = read_mem_gb() or 3.0
    cores = read_cpu_cores()
    free_gb = read_free_storage_gb() or 5.0

    if mem_gb < 2.5 or free_gb < 5.0:
        desktop = "fluxbox"
    elif mem_gb < 4.0:
        desktop = "lxde"
    else:
        desktop = "xfce"

    if mem_gb < 2.5:
        geometry, depth = "1024x600", 16
    elif mem_gb < 4.0:
        geometry, depth = "1280x720", 16
    else:
        geometry, depth = "1600x900", 24

    return {
        "mem_gb": mem_gb,
        "cores": cores,
        "free_gb": free_gb,
        "desktop": desktop,
        "geometry": geometry,
        "depth": depth,
        "display": 1,
        "allow_lan": False,
        "auto_kill_stale": True,
        "wake_lock": True,
        "x11_display": ":0",
        "installed_programs": []
    }

def detect_family(distro_name: str) -> str:
    d = distro_name.lower()
    # apk-based
    if any(x in d for x in ["alpine", "adelie", "chimera"]):
        return "alpine"
    # apt-based
    if any(x in d for x in ["ubuntu", "debian", "kali", "parrot", "mint", "devuan", "deepin", "pardus", "trisquel"]):
        return "debian"
    # pacman-based
    if any(x in d for x in ["arch", "manjaro", "endeavouros", "artix"]):
        return "arch"
    # rpm-based
    if any(x in d for x in ["fedora", "centos", "rocky", "alma", "rhel", "oracle", "almalinux", "rockylinux"]):
        return "fedora"
    # zypper
    if any(x in d for x in ["opensuse", "suse"]):
        return "suse"
    # xbps
    if "void" in d:
        return "void"
    return "unknown"

def proot_login_cmd(distro: str, inner_cmd: str) -> List[str]:
    return ["proot-distro", "login", distro, "--shared-tmp", "--", "/bin/sh", "-lc", inner_cmd]

def ensure_system_entry(cfg: Dict, distro: str) -> None:
    defaults = choose_defaults_by_specs()
    cfg["systems"].setdefault(distro, {
        "desktop": defaults["desktop"],
        "geometry": defaults["geometry"],
        "depth": defaults["depth"],
        "display": defaults["display"],
        "allow_lan": defaults["allow_lan"],
        "auto_kill_stale": defaults["auto_kill_stale"],
        "wake_lock": defaults["wake_lock"],
        "x11_display": defaults["x11_display"],
        "installed_programs": defaults["installed_programs"],
    })
    save_config(cfg)

def desktop_start_cmd(desktop: str) -> str:
    if desktop == "xfce":
        return "dbus-launch --exit-with-session startxfce4"
    if desktop == "lxde":
        return "dbus-launch --exit-with-session startlxde"
    if desktop == "openbox":
        return "dbus-launch --exit-with-session openbox-session"
    return "dbus-launch --exit-with-session fluxbox"

def apply_xstartup(distro: str, desktop: str) -> None:
    start_cmd = desktop_start_cmd(desktop)
    body = f"""#!/bin/sh
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
{start_cmd}
"""
    cmd = r"""
mkdir -p ~/.vnc
cat > ~/.vnc/xstartup <<'EOF'
%s
EOF
chmod +x ~/.vnc/xstartup
""" % body
    run(proot_login_cmd(distro, cmd), check=False)

def detect_vnc_command(distro: str) -> str:
    cmd = r"""
if command -v vncserver >/dev/null 2>&1; then echo vncserver; exit 0; fi
if command -v tigervncserver >/dev/null 2>&1; then echo tigervncserver; exit 0; fi
echo ""
"""
    try:
        return run(proot_login_cmd(distro, cmd), capture=True, check=False).stdout.strip()
    except Exception:
        return ""

def install_desktop_and_vnc(cfg: Dict, distro: str, desktop: str) -> bool:
    family = detect_family(distro)

    common_debian = "dbus-x11 xauth xterm sudo locales tzdata ca-certificates curl wget nano procps psmisc fonts-dejavu"
    common_arch = "dbus xorg-xauth xterm sudo ca-certificates curl wget nano procps-ng psmisc ttf-dejavu"
    common_alpine = "dbus xauth xterm sudo ca-certificates curl wget nano procps psmisc font-dejavu"
    common_fedora = "dbus-x11 xorg-x11-xauth xterm sudo ca-certificates curl wget nano procps-ng psmisc dejavu-sans-fonts"
    common_suse = "dbus-1 xauth xterm sudo ca-certificates curl wget nano procps psmisc"
    common_void = "dbus xauth xterm sudo ca-certificates curl wget nano procps psmisc"

    def pkgs_for_desktop(d: str, fam: str) -> str:
        if fam in ("debian", "arch", "alpine", "void"):
            if d == "xfce": return "xfce4 xfce4-goodies" if fam != "alpine" else "xfce4 xfce4-terminal"
            if d == "lxde": return "lxde"
            if d == "openbox": return "openbox obconf tint2" if fam != "alpine" else "openbox tint2"
            return "fluxbox"
        if fam == "fedora":
            if d == "xfce": return "xfce4-session xfce4-panel xfce4-terminal xfwm4 thunar"
            if d == "lxde": return "lxde-common openbox lxterminal pcmanfm"
            if d == "openbox": return "openbox tint2"
            return "fluxbox"
        if fam == "suse":
            if d == "xfce": return "xfce4-session xfce4-terminal"
            if d == "lxde": return "lxde-common openbox"
            if d == "openbox": return "openbox tint2"
            return "fluxbox"
        return ""

    vnc_debian = "tigervnc-standalone-server tigervnc-common"
    vnc_arch = "tigervnc"
    vnc_alpine = "tigervnc"
    vnc_fedora = "tigervnc-server"
    vnc_suse = "tigervnc"
    vnc_void = "tigervnc"

    if desktop not in DESKTOP_CHOICES:
        desktop = "xfce"

    if family == "debian":
        pkgs = f"{pkgs_for_desktop(desktop, family)} {vnc_debian} {common_debian}"
        cmd = f"""
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y || true
apt-get install -y {pkgs} || true
sed -i 's/^# *en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen 2>/dev/null || true
locale-gen 2>/dev/null || true
"""
    elif family == "arch":
        pkgs = f"{pkgs_for_desktop(desktop, family)} {vnc_arch} {common_arch}"
        cmd = f"pacman -Syu --noconfirm || true; pacman -S --noconfirm {pkgs} || true"
    elif family == "alpine":
        pkgs = f"{pkgs_for_desktop(desktop, family)} {vnc_alpine} {common_alpine}"
        cmd = f"apk update; apk upgrade || true; apk add {pkgs} || true"
    elif family == "fedora":
        pkgs = f"{pkgs_for_desktop(desktop, family)} {vnc_fedora} {common_fedora}"
        cmd = f"dnf -y upgrade || true; dnf -y install {pkgs} || true"
    elif family == "suse":
        pkgs = f"{pkgs_for_desktop(desktop, family)} {vnc_suse} {common_suse}"
        cmd = f"zypper --non-interactive refresh || true; zypper --non-interactive update || true; zypper --non-interactive install {pkgs} || true"
    elif family == "void":
        pkgs = f"{pkgs_for_desktop(desktop, family)} {vnc_void} {common_void}"
        cmd = f"xbps-install -Suy || true; xbps-install -y {pkgs} || true"
    else:
        return False

    run(proot_login_cmd(distro, cmd), check=False)
    apply_xstartup(distro, desktop)
    return True

def set_vnc_password(cfg: Dict, distro: str, password: str) -> None:
    if len(password) < 6:
        print(tr(cfg, "vnc_pass_short"))
        return
    cmd = f"""
if command -v vncpasswd >/dev/null 2>&1; then
  (printf %s\\\\n {sh_quote(password)}; printf %s\\\\n {sh_quote(password)}; printf \\\\n) | vncpasswd || true
fi
"""
    run(proot_login_cmd(distro, cmd), check=False)

def termux_wake_lock(enable: bool) -> None:
    if shutil.which("termux-wake-lock") is None:
        return
    run(["termux-wake-lock" if enable else "termux-wake-unlock"], check=False)

def vnc_list_raw(distro: str) -> str:
    cmd = r"""
VCMD=""
if command -v vncserver >/dev/null 2>&1; then VCMD="vncserver"; fi
if command -v tigervncserver >/dev/null 2>&1; then VCMD="tigervncserver"; fi
if [ -n "$VCMD" ]; then $VCMD -list || true; fi
"""
    try:
        return run(proot_login_cmd(distro, cmd), capture=True, check=False).stdout
    except Exception:
        return ""

def vnc_display_running(distro: str, display: int) -> bool:
    return (f":{display}" in vnc_list_raw(distro))

def vnc_start(cfg: Dict, distro: str) -> None:
    sys_cfg = cfg["systems"][distro]
    display = int(sys_cfg["display"])
    geometry = sys_cfg["geometry"]
    depth = int(sys_cfg["depth"])
    allow_lan = bool(sys_cfg.get("allow_lan", False))
    auto_kill = bool(sys_cfg.get("auto_kill_stale", True))
    wake_lock = bool(sys_cfg.get("wake_lock", True))

    termux_wake_lock(wake_lock)

    localhost_flag = "" if allow_lan else "-localhost"
    vcmd = detect_vnc_command(distro) or "vncserver"

    if auto_kill and vnc_display_running(distro, display):
        vnc_stop(cfg, distro)

    cmd = f"""
VCMD="{vcmd}"
if ! command -v "$VCMD" >/dev/null 2>&1; then
  echo "No VNC server command found (vncserver/tigervncserver)."
  exit 2
fi
$VCMD :{display} -geometry {geometry} -depth {depth} {localhost_flag} || exit $?
$VCMD -list || true
"""
    run(proot_login_cmd(distro, cmd), check=False)

def vnc_stop(cfg: Dict, distro: str) -> None:
    sys_cfg = cfg["systems"][distro]
    display = int(sys_cfg["display"])
    vcmd = detect_vnc_command(distro) or "vncserver"
    cmd = f"""
VCMD="{vcmd}"
if command -v "$VCMD" >/dev/null 2>&1; then
  $VCMD -kill :{display} || true
  $VCMD -list || true
fi
"""
    run(proot_login_cmd(distro, cmd), check=False)

def vnc_kill_all(distro: str) -> None:
    cmd = r"""
VCMD=""
if command -v vncserver >/dev/null 2>&1; then VCMD="vncserver"; fi
if command -v tigervncserver >/dev/null 2>&1; then VCMD="tigervncserver"; fi
if [ -z "$VCMD" ]; then exit 0; fi
$VCMD -list 2>/dev/null | awk '/^:[0-9]+/ {print $1}' | while read -r d; do
  $VCMD -kill "$d" || true
done
$VCMD -list || true
"""
    run(proot_login_cmd(distro, cmd), check=False)

def vnc_status(cfg: Dict, distro: str) -> None:
    cmd = r"""
VCMD=""
if command -v vncserver >/dev/null 2>&1; then VCMD="vncserver"; fi
if command -v tigervncserver >/dev/null 2>&1; then VCMD="tigervncserver"; fi
if [ -n "$VCMD" ]; then $VCMD -list || true; else echo "No VNC server found."; fi
"""
    run(proot_login_cmd(distro, cmd), check=False)

def get_phone_ip() -> Optional[str]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None

def connection_info(cfg: Dict, distro: str) -> None:
    sys_cfg = cfg["systems"][distro]
    display = int(sys_cfg["display"])
    allow_lan = bool(sys_cfg.get("allow_lan", False))
    port = 5900 + display
    host = socket.gethostname()
    phone_ip = get_phone_ip()

    print(f"\n{tr(cfg,'hostname')}: {host}")
    print(f"System: {distro}")
    print(f"Display: :{display}  ->  Port: {port}")
    print(f"{tr(cfg,'lan')}: {'ON' if allow_lan else 'OFF'}")
    print("\n" + tr(cfg, "connect_cmds"))
    print(f"  - Local (same phone): 127.0.0.1:{port}")
    if allow_lan:
        print(f"  - Wi-Fi: {(phone_ip or '<your-phone-ip>')}:{port}")
        print("  " + tr(cfg, "ip_hint"))

# ----------------------------
# Termux:X11 helpers
# ----------------------------
def x11_stop_server(cfg: Dict) -> None:
    run(["pkill", "-f", "termux-x11"], check=False)
    print(tr(cfg, "x11_stopped"))

def x11_start_server(cfg: Dict) -> bool:
    if shutil.which("termux-x11") is None:
        print(tr(cfg, "x11_missing"))
        return False
    print(tr(cfg, "x11_starting"))
    try:
        subprocess.Popen(["termux-x11", ":0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def x11_start_desktop_in_distro(cfg: Dict, distro: str) -> None:
    sys_cfg = cfg["systems"][distro]
    desktop = sys_cfg["desktop"]
    x11_display = sys_cfg.get("x11_display", ":0")
    wake_lock = bool(sys_cfg.get("wake_lock", True))
    termux_wake_lock(wake_lock)

    start_cmd = desktop_start_cmd(desktop)
    cmd = f"""
export DISPLAY={sh_quote(x11_display)}
export XDG_RUNTIME_DIR="${{XDG_RUNTIME_DIR:-/tmp/runtime-$USER}}"
mkdir -p "$XDG_RUNTIME_DIR" || true
chmod 700 "$XDG_RUNTIME_DIR" || true
{start_cmd} || true
"""
    run(proot_login_cmd(distro, cmd), check=False)

def x11_info(cfg: Dict) -> None:
    print("\n" + tr(cfg, "x11_info"))
    print("  - DISPLAY: :0")
    print("  - 1) Open Termux:X11 app")
    print("  - 2) In Termux: termux-x11 :0")
    print("  - 3) Here: X11 Options -> Start desktop")



def install_recommended_extras(cfg: Dict, distro: str) -> None:
    """
    Best-effort "quality of life" extras so the desktop feels usable.
    Installs depend on distro family and chosen desktop.
    """
    ensure_system_entry(cfg, distro)
    sys_cfg = cfg["systems"][distro]
    desktop = sys_cfg.get("desktop", "xfce")
    family = detect_family(distro)

    # Pick a sensible file manager/terminal based on desktop preference
    if desktop == "xfce":
        fm = ("thunar", "thunar-volman", "gvfs", "gvfs-backends")
        term = ("xfce4-terminal",)
    elif desktop == "lxde":
        fm = ("pcmanfm", "gvfs", "gvfs-backends")
        term = ("lxterminal",)
    else:
        # fluxbox/openbox: keep it light but usable
        fm = ("pcmanfm", "gvfs", "gvfs-backends")
        term = ("xterm",)

    # Common extras (best-effort)
    common_tools = ("xdg-utils", "file", "unzip", "zip", "p7zip", "p7zip-full", "tar", "wget", "curl", "nano")
    # Fonts/icons (help a lot on VNC)
    fonts_icons_deb = ("fonts-noto", "fonts-dejavu", "papirus-icon-theme")
    fonts_icons_arch = ("noto-fonts", "ttf-dejavu", "papirus-icon-theme")
    fonts_icons_fedora = ("google-noto-sans-fonts", "dejavu-sans-fonts")
    fonts_icons_suse = ("noto-sans-fonts", "dejavu-fonts")
    fonts_icons_alpine = ("font-noto", "font-dejavu")
    fonts_icons_void = ("noto-fonts-ttf", "dejavu-fonts-ttf")

    # Optional extras that improve UX; installed with || true so missing pkgs won't break.
    extras = []
    extras += list(fm) + list(term)

    # Add a lightweight GUI editor and clipboard tools when available
    extras += ["mousepad", "leafpad", "xclip", "xsel", "dbus-x11", "dbus"]

    # Audio (best-effort): pulseaudio can help some apps
    extras += ["pulseaudio", "pavucontrol"]

    # Now build per-family command
    if family == "debian":
        pkgs = " ".join(extras + list(common_tools) + list(fonts_icons_deb))
        cmd = f"""
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y {pkgs} || true
"""
    elif family == "arch":
        pkgs = " ".join(extras + list(common_tools) + list(fonts_icons_arch))
        cmd = f"""
pacman -Syu --noconfirm || true
pacman -S --noconfirm {pkgs} || true
"""
    elif family == "alpine":
        pkgs = " ".join(extras + list(common_tools) + list(fonts_icons_alpine))
        cmd = f"""
apk update
apk add {pkgs} || true
"""
    elif family == "fedora":
        pkgs = " ".join(extras + list(common_tools) + list(fonts_icons_fedora))
        cmd = f"""
dnf -y upgrade || true
dnf -y install {pkgs} || true
"""
    elif family == "suse":
        pkgs = " ".join(extras + list(common_tools) + list(fonts_icons_suse))
        cmd = f"""
zypper --non-interactive refresh || true
zypper --non-interactive install {pkgs} || true
"""
    elif family == "void":
        pkgs = " ".join(extras + list(common_tools) + list(fonts_icons_void))
        cmd = f"""
xbps-install -Suy || true
xbps-install -y {pkgs} || true
"""
    else:
        print(tr(cfg, "programs_not_supported"))
        return

    print(tr(cfg, "extras_installing"))
    run(proot_login_cmd(distro, cmd), check=False)
    print(tr(cfg, "extras_done"))

# ----------------------------
# Program Manager
# ----------------------------
def get_program_by_id(pid: str) -> Optional[Dict]:
    for p in PROGRAMS:
        if p["id"] == pid:
            return p
    return None

def get_program_command(p: Dict, family: str, action: str) -> Optional[str]:
    fam_map = p.get("cmd", {}).get(family, {})
    return fam_map.get(action)

def mark_program_installed(cfg: Dict, distro: str, pid: str, installed: bool) -> None:
    ensure_system_entry(cfg, distro)
    lst = cfg["systems"][distro].setdefault("installed_programs", [])
    if installed and pid not in lst:
        lst.append(pid)
    if (not installed) and pid in lst:
        lst.remove(pid)
    save_config(cfg)

def list_installed_programs(cfg: Dict, distro: str) -> List[str]:
    ensure_system_entry(cfg, distro)
    return cfg["systems"][distro].get("installed_programs", []) or []

def _validate_pkg_name(pkg: str) -> Optional[str]:
    pkg = (pkg or "").strip()
    if not pkg:
        return None
    # prevent shell injection: allow only common package name chars
    if not re.fullmatch(r"[A-Za-z0-9.+_-]+", pkg):
        return None
    return pkg

def install_custom_package(cfg: Dict, distro: str, pkg: str) -> Optional[str]:
    """Install an arbitrary package name inside a distro (best-effort). Returns tracking id or None."""
    pkg = _validate_pkg_name(pkg)
    if not pkg:
        print(tr(cfg, "invalid"))
        return None

    family = detect_family(distro)
    if family == "debian":
        cmd = f"apt-get update -y && apt-get install -y {pkg}"
    elif family == "arch":
        cmd = f"pacman -Syu --noconfirm || true; pacman -S --noconfirm {pkg}"
    elif family == "alpine":
        cmd = f"apk update && apk add {pkg}"
    elif family == "fedora":
        cmd = f"dnf -y upgrade || true; dnf -y install {pkg}"
    elif family == "suse":
        cmd = f"zypper --non-interactive refresh || true; zypper --non-interactive install {pkg}"
    elif family == "void":
        cmd = f"xbps-install -Suy || true; xbps-install -y {pkg}"
    else:
        print(tr(cfg, "programs_not_supported"))
        return None

    print(f"{tr(cfg,'programs_installing')} {pkg}")
    run(proot_login_cmd(distro, cmd), check=False)

    pid = f"pkg:{pkg}"
    mark_program_installed(cfg, distro, pid, True)
    print(tr(cfg, "programs_done"))
    return pid

def remove_custom_package(cfg: Dict, distro: str, pkg: str) -> None:
    pkg = _validate_pkg_name(pkg)
    if not pkg:
        print(tr(cfg, "invalid"))
        return

    family = detect_family(distro)
    if family == "debian":
        cmd = f"apt-get remove -y {pkg} || true && apt-get autoremove -y || true"
    elif family == "arch":
        cmd = f"pacman -Rns --noconfirm {pkg} || true"
    elif family == "alpine":
        cmd = f"apk del {pkg} || true"
    elif family == "fedora":
        cmd = f"dnf -y remove {pkg} || true"
    elif family == "suse":
        cmd = f"zypper --non-interactive remove {pkg} || true"
    elif family == "void":
        cmd = f"xbps-remove -Ry {pkg} || true"
    else:
        print(tr(cfg, "programs_not_supported"))
        return

    print(f"{tr(cfg,'programs_removing')} {pkg}")
    run(proot_login_cmd(distro, cmd), check=False)
    print(tr(cfg, "programs_done"))


def install_program(cfg: Dict, distro: str, pid: str) -> None:
    p = get_program_by_id(pid)
    if not p:
        return
    family = detect_family(distro)
    cmd = get_program_command(p, family, "install")
    if not cmd:
        print(tr(cfg, "programs_not_supported"))
        return
    print(f"{tr(cfg,'programs_installing')} {prog_name(cfg,p)}")
    print(tr(cfg, "warn_large"))
    run(proot_login_cmd(distro, cmd), check=False)
    mark_program_installed(cfg, distro, pid, True)
    print(tr(cfg, "programs_done"))

def remove_program(cfg: Dict, distro: str, pid: str) -> None:
    # custom tracked packages: pid like 'pkg:<name>'
    if pid.startswith("pkg:"):
        pkg = pid.split(":", 1)[1]
        remove_custom_package(cfg, distro, pkg)
        mark_program_installed(cfg, distro, pid, False)
        return

    p = get_program_by_id(pid)
    if not p:
        return
    family = detect_family(distro)
    cmd = get_program_command(p, family, "remove")
    if not cmd:
        print(tr(cfg, "programs_not_supported"))
        return
    print(f"{tr(cfg,'programs_removing')} {prog_name(cfg,p)}")
    run(proot_login_cmd(distro, cmd), check=False)
    mark_program_installed(cfg, distro, pid, False)
    print(tr(cfg, "programs_done"))

def update_distro_and_programs(cfg: Dict, distro: str) -> None:
    family = detect_family(distro)
    print(f"{tr(cfg,'update_title')} {distro}")
    if family == "debian":
        cmd = "apt-get update -y && apt-get upgrade -y && apt-get autoremove -y || true"
    elif family == "arch":
        cmd = "pacman -Syu --noconfirm || true"
    elif family == "alpine":
        cmd = "apk update && apk upgrade || true"
    elif family == "fedora":
        cmd = "dnf -y upgrade || true"
    elif family == "suse":
        cmd = "zypper --non-interactive refresh || true; zypper --non-interactive update || true"
    elif family == "void":
        cmd = "xbps-install -Suy || true"
    else:
        cmd = ""
    if not cmd:
        print(tr(cfg, "programs_not_supported"))
        return
    run(proot_login_cmd(distro, cmd), check=False)
    print(tr(cfg, "update_done"))

# ----------------------------
# Launcher creation
# ----------------------------
def sanitize_launcher_name(distro: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "-", distro)

def launcher_desktop_cmd(desktop: str) -> str:
    if desktop == "xfce":
        return "dbus-launch --exit-with-session startxfce4"
    if desktop == "lxde":
        return "dbus-launch --exit-with-session startlxde"
    if desktop == "openbox":
        return "dbus-launch --exit-with-session openbox-session"
    return "dbus-launch --exit-with-session fluxbox"

def create_launcher(cfg: Dict, distro: str) -> Optional[Path]:
    prefix = get_prefix()
    if not prefix:
        return None
    ensure_system_entry(cfg, distro)
    sys_cfg = cfg["systems"][distro]

    launcher_name = f"vnc-{sanitize_launcher_name(distro)}"
    launcher_path = Path(prefix) / "bin" / launcher_name

    display = int(sys_cfg["display"])
    geometry = sys_cfg["geometry"]
    depth = int(sys_cfg["depth"])
    allow_lan = bool(sys_cfg.get("allow_lan", False))
    auto_kill = bool(sys_cfg.get("auto_kill_stale", True))
    wake_lock = bool(sys_cfg.get("wake_lock", True))
    localhost_flag = "" if allow_lan else "-localhost"
    port = 5900 + display
    desktop = sys_cfg.get("desktop", "xfce")
    x11_disp = sys_cfg.get("x11_display", ":0")

    shebang = "#!/data/data/com.termux/files/usr/bin/bash"
    wakelock_snippet = "termux-wake-lock >/dev/null 2>&1 || true" if wake_lock else "termux-wake-unlock >/dev/null 2>&1 || true"
    autokill_snippet = "VCMD=''; command -v vncserver >/dev/null 2>&1 && VCMD='vncserver'; command -v tigervncserver >/dev/null 2>&1 && VCMD='tigervncserver'; [ -n \"$VCMD\" ] && $VCMD -kill :$DISPLAY 2>/dev/null || true" if auto_kill else ":"
    x11_desktop_cmd = launcher_desktop_cmd(desktop)

    content = f"""{shebang}
set -e

SYSTEM={sh_quote(distro)}
DISPLAY={display}
GEOMETRY={sh_quote(geometry)}
DEPTH={depth}
LOCALHOST_FLAG={sh_quote(localhost_flag)}
PORT={port}
X11_DISPLAY={sh_quote(x11_disp)}
DESKTOP_CMD={sh_quote(x11_desktop_cmd)}

cmd="$1"
if [ -z "$cmd" ]; then cmd="start"; fi

case "$cmd" in
  start)
    {wakelock_snippet}
    proot-distro login "$SYSTEM" --shared-tmp -- /bin/sh -lc '{autokill_snippet}; VCMD=""; command -v vncserver >/dev/null 2>&1 && VCMD="vncserver"; command -v tigervncserver >/dev/null 2>&1 && VCMD="tigervncserver"; [ -z "$VCMD" ] && echo "No VNC server found." && exit 2; $VCMD :{display} -geometry {geometry} -depth {depth} {localhost_flag} || exit $?; $VCMD -list || true'
    echo
    echo "Connect: 127.0.0.1:$PORT"
    ;;
  stop)
    proot-distro login "$SYSTEM" --shared-tmp -- /bin/sh -lc 'VCMD=""; command -v vncserver >/dev/null 2>&1 && VCMD="vncserver"; command -v tigervncserver >/dev/null 2>&1 && VCMD="tigervncserver"; [ -n "$VCMD" ] && $VCMD -kill :{display} || true; [ -n "$VCMD" ] && $VCMD -list || true'
    ;;
  restart)
    {wakelock_snippet}
    proot-distro login "$SYSTEM" --shared-tmp -- /bin/sh -lc 'VCMD=""; command -v vncserver >/dev/null 2>&1 && VCMD="vncserver"; command -v tigervncserver >/dev/null 2>&1 && VCMD="tigervncserver"; [ -z "$VCMD" ] && echo "No VNC server found." && exit 2; $VCMD -kill :{display} || true; $VCMD :{display} -geometry {geometry} -depth {depth} {localhost_flag} || exit $?; $VCMD -list || true'
    echo
    echo "Connect: 127.0.0.1:$PORT"
    ;;
  status)
    proot-distro login "$SYSTEM" --shared-tmp -- /bin/sh -lc 'VCMD=""; command -v vncserver >/dev/null 2>&1 && VCMD="vncserver"; command -v tigervncserver >/dev/null 2>&1 && VCMD="tigervncserver"; [ -n "$VCMD" ] && $VCMD -list || true'
    ;;
  info)
    echo "System: $SYSTEM"
    echo "Display: :{display}"
    echo "Port: $PORT"
    ;;
  login)
    proot-distro login "$SYSTEM" --shared-tmp
    ;;
  x11-start)
    {wakelock_snippet}
    termux-x11 :0 >/dev/null 2>&1 &
    proot-distro login "$SYSTEM" --shared-tmp -- /bin/sh -lc "export DISPLAY=$X11_DISPLAY; export XDG_RUNTIME_DIR=${{XDG_RUNTIME_DIR:-/tmp/runtime-$USER}}; mkdir -p \\\"$XDG_RUNTIME_DIR\\\" || true; chmod 700 \\\"$XDG_RUNTIME_DIR\\\" || true; $DESKTOP_CMD || true"
    ;;
  x11-stop)
    pkill -f termux-x11 || true
    ;;
  *)
    echo "Usage: {launcher_name} [start|stop|restart|status|info|login|x11-start|x11-stop]"
    exit 1
    ;;
esac
"""
    try:
        launcher_path.write_text(content, encoding="utf-8")
        launcher_path.chmod(0o755)
        return launcher_path
    except Exception:
        return None

def list_launchers() -> List[str]:
    prefix = get_prefix()
    if not prefix:
        return []
    bin_dir = Path(prefix) / "bin"
    if not bin_dir.exists():
        return []
    return sorted([p.name for p in bin_dir.iterdir() if p.is_file() and p.name.startswith("vnc-")])

# ----------------------------
# Menu helpers
# ----------------------------
def pick_from_list(prompt: str, items: List[str]) -> Optional[str]:
    if not items:
        return None
    for i, d in enumerate(items, 1):
        print(f"  {i}) {d}")
    try:
        idx = int(input("\n" + prompt).strip())
        if 1 <= idx <= len(items):
            return items[idx - 1]
        return None
    except Exception:
        return None

# ----------------------------
# Actions
# ----------------------------
def action_install(cfg: Dict) -> None:
    available = get_available_distros(cfg)
    if not available:
        print(tr(cfg, "no_distros"))
        pause(cfg)
        return

    print("\n" + tr(cfg, "available"))
    print(tr(cfg, "recommend_note"))
    distro = pick_from_list(tr(cfg, "pick_system"), available)
    if not distro:
        print(tr(cfg, "invalid"))
        pause(cfg)
        return

    ensure_system_entry(cfg, distro)
    defaults = choose_defaults_by_specs()
    sys_cfg = cfg["systems"][distro]

    print("\n" + tr(cfg, "setup_auto"))
    print(tr(cfg, "specs"))
    print(f"  - {tr(cfg,'ram')}: {defaults['mem_gb']:.2f} GB")
    print(f"  - {tr(cfg,'cores')}: {defaults['cores']}")
    print(f"  - {tr(cfg,'storage')}: {defaults['free_gb']:.2f} GB")
    print(tr(cfg, "chosen"))
    print(f"  - {tr(cfg,'desktop')}: {sys_cfg['desktop']}")
    print(f"  - {tr(cfg,'geometry')}: {sys_cfg['geometry']}")
    print(f"  - {tr(cfg,'depth')}: {sys_cfg['depth']}")
    print(f"  - {tr(cfg,'display')}: :{sys_cfg['display']}")

    print(f"\n{tr(cfg, 'install_start')} {distro}")
    run(["proot-distro", "install", distro], check=False)
    print(tr(cfg, "install_done"))

    print("\n" + tr(cfg, "running_setup"))
    ok = install_desktop_and_vnc(cfg, distro, sys_cfg["desktop"])
    if ok:
        yn = input("\n" + tr(cfg, "ask_vnc_pass")).strip().lower()
        if yn == "y":
            pw = input(tr(cfg, "vnc_pass_prompt")).strip()
            set_vnc_password(cfg, distro, pw)

        yn2 = input(tr(cfg, "ask_extras")).strip().lower()
        if yn2 == "y":
            install_recommended_extras(cfg, distro)
        print(tr(cfg, "setup_done"))
    else:
        print(tr(cfg, "setup_partial"))

    lp = create_launcher(cfg, distro)
    if lp:
        print(f"{tr(cfg,'launcher_created')} {lp}")
    else:
        print(tr(cfg, "launcher_fail"))

    pause(cfg)

def action_remove_system(cfg: Dict) -> None:
    installed = get_installed_distros()
    print("\n" + tr(cfg, "installed"))
    if not installed:
        print("  " + tr(cfg, "none_installed"))
        pause(cfg)
        return
    distro = pick_from_list(tr(cfg, "pick_system"), installed)
    if not distro:
        print(tr(cfg, "invalid"))
        pause(cfg)
        return
    confirm = input(tr(cfg, "remove_confirm")).strip()
    if confirm != "YES":
        print(tr(cfg, "invalid"))
        pause(cfg)
        return
    run(["proot-distro", "remove", distro], check=False)
    cfg["systems"].pop(distro, None)
    save_config(cfg)
    print(tr(cfg, "remove_done"))
    pause(cfg)

def action_settings(cfg: Dict) -> None:
    installed = get_installed_distros()
    print("\n" + tr(cfg, "installed"))
    if not installed:
        print("  " + tr(cfg, "none_installed"))
        pause(cfg)
        return
    distro = pick_from_list(tr(cfg, "pick_system"), installed)
    if not distro:
        print(tr(cfg, "invalid"))
        pause(cfg)
        return
    ensure_system_entry(cfg, distro)

    while True:
        sys_cfg = cfg["systems"][distro]
        print("\n" + tr(cfg, "settings_title"))
        print(
            f"  {distro}: desktop={sys_cfg['desktop']} geometry={sys_cfg['geometry']} depth={sys_cfg['depth']} "
            f"display=:{sys_cfg['display']} LAN={'ON' if sys_cfg.get('allow_lan') else 'OFF'} "
            f"AutoKill={'ON' if sys_cfg.get('auto_kill_stale') else 'OFF'} WakeLock={'ON' if sys_cfg.get('wake_lock') else 'OFF'}"
        )
        items = T[cfg.get("language","en")]["settings_menu"]
        for i, item in enumerate(items, 1):
            print(f"  {i}) {item}")

        choice = input("\n" + tr(cfg, "choose")).strip()
        if choice == "1":
            print("\n" + tr(cfg, "preset_title"))
            preset = pick_from_list(tr(cfg, "pick_system"), GEOMETRY_PRESETS)
            if preset:
                sys_cfg["geometry"] = preset
                save_config(cfg)
            else:
                print(tr(cfg, "invalid"))
        elif choice == "2":
            g = input(tr(cfg, "enter_geometry")).strip()
            if re.match(r"^\d{3,5}x\d{3,5}$", g):
                sys_cfg["geometry"] = g
                save_config(cfg)
            else:
                print(tr(cfg, "invalid"))
        elif choice == "3":
            d = input(tr(cfg, "enter_depth")).strip()
            if d.isdigit() and int(d) in (8, 16, 24, 32):
                sys_cfg["depth"] = int(d)
                save_config(cfg)
            else:
                print(tr(cfg, "invalid"))
        elif choice == "4":
            desk = input(tr(cfg, "enter_desktop")).strip().lower()
            if desk in DESKTOP_CHOICES:
                sys_cfg["desktop"] = desk
                save_config(cfg)
                apply_xstartup(distro, desk)
            else:
                print(tr(cfg, "invalid"))
        elif choice == "5":
            disp = input(tr(cfg, "enter_display")).strip()
            if disp.isdigit() and 0 < int(disp) < 100:
                sys_cfg["display"] = int(disp)
                save_config(cfg)
            else:
                print(tr(cfg, "invalid"))
        elif choice == "6":
            sys_cfg["allow_lan"] = not bool(sys_cfg.get("allow_lan", False))
            save_config(cfg)
            print(tr(cfg, "lan_now"))
            print(tr(cfg, "lan_on") if sys_cfg["allow_lan"] else tr(cfg, "lan_off"))
        elif choice == "7":
            sys_cfg["auto_kill_stale"] = not bool(sys_cfg.get("auto_kill_stale", True))
            save_config(cfg)
            print(tr(cfg, "autokill_now"))
            print(tr(cfg, "autokill_on") if sys_cfg["auto_kill_stale"] else tr(cfg, "autokill_off"))
        elif choice == "8":
            sys_cfg["wake_lock"] = not bool(sys_cfg.get("wake_lock", True))
            save_config(cfg)
            print(tr(cfg, "wakelock_now"))
            print(tr(cfg, "wakelock_on") if sys_cfg["wake_lock"] else tr(cfg, "wakelock_off"))
        elif choice == "9":
            pw = input(tr(cfg, "vnc_pass_prompt")).strip()
            set_vnc_password(cfg, distro, pw)
        elif choice == "10":
            print("\n" + tr(cfg, "running_setup"))
            ok = install_desktop_and_vnc(cfg, distro, sys_cfg["desktop"])
            print(tr(cfg, "setup_done") if ok else tr(cfg, "setup_partial"))
        elif choice == "11":
            lp = create_launcher(cfg, distro)
            if lp:
                print(f"{tr(cfg,'launcher_created')} {lp}")
            break
        else:
            print(tr(cfg, "invalid"))

def action_vnc(cfg: Dict) -> None:
    installed = get_installed_distros()
    if not installed:
        print("\n" + tr(cfg, "installed"))
        print("  " + tr(cfg, "none_installed"))
        pause(cfg)
        return

    while True:
        print("\n" + tr(cfg, "vnc_title"))
        items = T[cfg.get("language","en")]["vnc_menu"]
        for i, item in enumerate(items, 1):
            print(f"  {i}) {item}")
        choice = input("\n" + tr(cfg, "choose")).strip()

        if choice in ("1","2","3","4","5","6"):
            print("\n" + tr(cfg, "installed"))
            distro = pick_from_list(tr(cfg, "pick_system"), installed)
            if not distro:
                print(tr(cfg, "invalid"))
                continue
            ensure_system_entry(cfg, distro)

            if choice == "1":
                vnc_start(cfg, distro)
                connection_info(cfg, distro)
                pause(cfg)
            elif choice == "2":
                vnc_stop(cfg, distro)
                pause(cfg)
            elif choice == "3":
                vnc_stop(cfg, distro)
                vnc_start(cfg, distro)
                connection_info(cfg, distro)
                pause(cfg)
            elif choice == "4":
                vnc_status(cfg, distro)
                pause(cfg)
            elif choice == "5":
                vnc_kill_all(distro)
                pause(cfg)
            elif choice == "6":
                connection_info(cfg, distro)
                pause(cfg)
        elif choice == "7":
            break
        else:
            print(tr(cfg, "invalid"))

def action_x11(cfg: Dict) -> None:
    installed = get_installed_distros()
    if not installed:
        print("\n" + tr(cfg, "installed"))
        print("  " + tr(cfg, "none_installed"))
        pause(cfg)
        return
    while True:
        print("\n" + tr(cfg, "x11_title"))
        items = T[cfg.get("language","en")]["x11_menu"]
        for i, item in enumerate(items, 1):
            print(f"  {i}) {item}")
        choice = input("\n" + tr(cfg, "choose")).strip()

        if choice == "1":
            ensure_termux_x11_packages(cfg)
            pause(cfg)
        elif choice == "2":
            print("\n" + tr(cfg, "installed"))
            distro = pick_from_list(tr(cfg, "pick_system"), installed)
            if not distro:
                print(tr(cfg, "invalid"))
                continue
            ensure_system_entry(cfg, distro)
            if not ensure_termux_x11_packages(cfg):
                print(tr(cfg, "x11_missing"))
                pause(cfg)
                continue
            print(tr(cfg, "x11_need_app"))
            if x11_start_server(cfg):
                print(tr(cfg, "x11_started"))
                x11_start_desktop_in_distro(cfg, distro)
            pause(cfg)
        elif choice == "3":
            x11_stop_server(cfg)
            pause(cfg)
        elif choice == "4":
            x11_info(cfg)
            pause(cfg)
        elif choice == "5":
            break
        else:
            print(tr(cfg, "invalid"))

def pick_or_install_system_for_programs(cfg: Dict) -> Optional[str]:
    """Pick an installed distro for program actions.
    If none are installed yet, let the user install one from the available list.
    """
    installed = get_installed_distros()

    print("\n" + tr(cfg, "installed"))
    if installed:
        distro = pick_from_list(tr(cfg, "pick_system"), installed)
        if not distro:
            return None
        return distro

    # No installed systems yet -> offer to install one so program manager is usable
    print("  " + tr(cfg, "none_installed"))

    available = get_available_distros(cfg)
    if not available:
        print(tr(cfg, "no_distros"))
        return None

    print("\n" + tr(cfg, "available"))
    print(tr(cfg, "recommend_note"))
    distro = pick_from_list(tr(cfg, "pick_system"), available)
    if not distro:
        return None

    ensure_system_entry(cfg, distro)
    print(f"\n{tr(cfg, 'install_start')} {distro}")
    run(["proot-distro", "install", distro], check=False)
    print(tr(cfg, "install_done"))

    # Keep it lightweight: do not auto-install desktop/VNC here.
    print("\nTip: If you want GUI apps (LibreOffice, browsers) to open in VNC/X11, run full setup:")
    print("  - Menu 1) Install A System  (or)")
    print("  - Menu 3) Change Settings -> Re-apply setup inside the system")
    return distro


def action_programs_install(cfg: Dict) -> None:
    distro = pick_or_install_system_for_programs(cfg)
    if not distro:
        print(tr(cfg, "invalid"))
        pause(cfg)
        return

    ensure_system_entry(cfg, distro)
    installed_pids = set(list_installed_programs(cfg, distro))

    # --- Browser / filter menu so we can have a very large catalog without spamming the terminal
    print("\n" + tr(cfg, "programs_browser_title"))
    items = T[cfg.get("language","en")].get("programs_browser_menu", [
        "Show ALL programs",
        "Pick a category",
        "Search by name",
        "Install custom package (type any package name)",
        "Back"
    ])
    for i, item in enumerate(items, 1):
        print(f"  {i}) {item}")

    choice = input("\n" + tr(cfg, "choose")).strip()

    if choice == "5":
        return

    if choice == "4":
        pkg_prompt = tr(cfg, "programs_custom_prompt")
        pkg = input(pkg_prompt).strip()
        install_custom_package(cfg, distro, pkg)
        pause(cfg)
        return

    view = list(PROGRAMS)

    if choice == "2":
        # category
        cats = sorted({p.get("cat","Other") for p in PROGRAMS})
        print("\n" + tr(cfg, "programs_pick_category"))
        for i, c in enumerate(cats, 1):
            print(f"  {i}) {c}")
        raw = input("\n" + tr(cfg, "choose")).strip()
        try:
            idx = int(raw)
            if not (1 <= idx <= len(cats)):
                raise ValueError
            cat = cats[idx - 1]
            view = [p for p in PROGRAMS if p.get("cat","Other") == cat]
        except Exception:
            print(tr(cfg, "invalid"))
            pause(cfg)
            return

    elif choice == "3":
        q = input(tr(cfg, "programs_search_prompt")).strip().lower()
        if q:
            def _match(p):
                name = (p.get("en","") + " " + p.get("gr","")).lower()
                desc = (p.get("desc_en","") + " " + p.get("desc_gr","")).lower()
                cat = str(p.get("cat","")).lower()
                return q in name or q in desc or q in cat
            view = [p for p in PROGRAMS if _match(p)]

    elif choice != "1":
        print(tr(cfg, "invalid"))
        pause(cfg)
        return

    print("\n" + tr(cfg, "programs_title"))
    if not view:
        print(tr(cfg, "programs_none"))
        pause(cfg)
        return

    # Print a compact list: name + category + install mark
    for i, p in enumerate(view, 1):
        mark = "[installed]" if p["id"] in installed_pids else ""
        cat = p.get("cat", "Other")
        print(f"  {i}) {prog_name(cfg, p)}  ({cat}) {mark}")
        print(f"     - {prog_desc(cfg, p)}")

    print("\n" + tr(cfg, "programs_multi_hint"))

    raw = input("\n" + tr(cfg, "programs_pick_multi")).strip()

    # Allow "0" shortcut for custom package too
    if raw == "0":
        pkg = input(tr(cfg, "programs_custom_prompt")).strip()
        install_custom_package(cfg, distro, pkg)
        pause(cfg)
        return

    # Allow multiple selections: 1,2,5
    picks = []
    for part in re.split(r"[,\s]+", raw):
        part = part.strip()
        if not part:
            continue
        if not part.isdigit():
            print(tr(cfg, "invalid"))
            pause(cfg)
            return
        picks.append(int(part))

    if not picks:
        print(tr(cfg, "invalid"))
        pause(cfg)
        return

    for idx in picks:
        if not (1 <= idx <= len(view)):
            print(tr(cfg, "invalid"))
            continue
        pid = view[idx - 1]["id"]
        install_program(cfg, distro, pid)

    pause(cfg)


def action_programs_remove(cfg: Dict) -> None:
    installed = get_installed_distros()
    if not installed:
        print("\n" + tr(cfg, "installed"))
        print("  " + tr(cfg, "none_installed"))
        pause(cfg)
        return

    print("\n" + tr(cfg, "installed"))
    distro = pick_from_list(tr(cfg, "pick_system"), installed)
    if not distro:
        print(tr(cfg, "invalid"))
        pause(cfg)
        return
    ensure_system_entry(cfg, distro)
    installed_pids = list_installed_programs(cfg, distro)

    print("\n" + tr(cfg, "programs_installed_list"))
    if not installed_pids:
        print("  " + tr(cfg, "none"))
        pause(cfg)
        return

    # show installed with names
    display = []
    for pid in installed_pids:
        p = get_program_by_id(pid)
        display.append((pid, prog_name(cfg, p) if p else pid))
    for i, (_, name) in enumerate(display, 1):
        print(f"  {i}) {name}")

    try:
        idx = int(input("\n" + tr(cfg, "programs_pick")).strip())
        if not (1 <= idx <= len(display)):
            raise ValueError
        pid = display[idx - 1][0]
    except Exception:
        print(tr(cfg, "invalid"))
        pause(cfg)
        return

    remove_program(cfg, distro, pid)
    pause(cfg)

def action_update(cfg: Dict) -> None:
    installed = get_installed_distros()
    print("\n" + tr(cfg, "installed"))
    if not installed:
        print("  " + tr(cfg, "none_installed"))
        pause(cfg)
        return
    distro = pick_from_list(tr(cfg, "pick_system"), installed)
    if not distro:
        print(tr(cfg, "invalid"))
        pause(cfg)
        return
    ensure_system_entry(cfg, distro)
    update_distro_and_programs(cfg, distro)
    pause(cfg)


def action_extras_menu(cfg: Dict) -> None:
    installed = get_installed_distros()
    print("\n" + tr(cfg, "installed"))
    if not installed:
        print("  " + tr(cfg, "none_installed"))
        pause(cfg)
        return
    distro = pick_from_list(tr(cfg, "pick_system"), installed)
    if not distro:
        print(tr(cfg, "invalid"))
        pause(cfg)
        return
    ensure_system_entry(cfg, distro)
    install_recommended_extras(cfg, distro)
    pause(cfg)

def action_launcher(cfg: Dict) -> None:
    installed = get_installed_distros()
    if not installed:
        print("\n" + tr(cfg, "installed"))
        print("  " + tr(cfg, "none_installed"))
        pause(cfg)
        return
    while True:
        print("\n" + tr(cfg, "launcher_title"))
        items = T[cfg.get("language","en")]["launcher_menu"]
        for i, item in enumerate(items, 1):
            print(f"  {i}) {item}")
        choice = input("\n" + tr(cfg, "choose")).strip()

        if choice == "1":
            print("\n" + tr(cfg, "installed"))
            distro = pick_from_list(tr(cfg, "pick_system"), installed)
            if not distro:
                print(tr(cfg, "invalid"))
                continue
            ensure_system_entry(cfg, distro)
            lp = create_launcher(cfg, distro)
            if lp:
                print(f"{tr(cfg,'launcher_created')} {lp}")
                print(f"Try: {lp.name} start")
                print(f"Try: {lp.name} stop")
                print(f"Try: {lp.name} x11-start")
            else:
                print(tr(cfg, "launcher_fail"))
            pause(cfg)
        elif choice == "2":
            ls = list_launchers()
            print("\n" + tr(cfg, "launchers_found"))
            if not ls:
                print("  " + tr(cfg, "none"))
            else:
                for x in ls:
                    print("  - " + x)
            pause(cfg)
        elif choice == "3":
            break
        else:
            print(tr(cfg, "invalid"))

def action_help(cfg: Dict) -> None:
    print("\n" + tr(cfg, "help_title"))
    print("-" * 70)
    print("\nVNC:")
    print("  - Start: vnc-<system> start   (or menu -> VNC Options)")
    print("  - Stop : vnc-<system> stop")
    print("  - Ports: :1 -> 5901, :2 -> 5902 ...")
    print("  - Default is localhost-only (safe). Enable LAN only if you set a strong password.")
    print("\nTermux:X11:")
    print("  - Install + open Termux:X11 Android app")
    print("  - In this menu: X11 Options -> Install packages -> Start desktop")
    print("\nPrograms:")
    print("  - Use Programs menu to install/remove common apps.")
    print("  - Some packages may not exist on very small distros; try a major distro like ubuntu/debian/fedora.")
    pause(cfg)

# ----------------------------
# Main
# ----------------------------
def main() -> None:
    cfg = load_config()
    if not ensure_termux_deps(cfg):
        return

    while True:
        print("\n" + "=" * 76)
        print(tr(cfg, "title"))
        print("=" * 76)

        menu_items = T[cfg.get("language","en")]["menu"]
        for i, item in enumerate(menu_items, 1):
            print(f"{i}) {item}")

        choice = input("\n" + tr(cfg, "choose")).strip()

        if choice == "1":
            action_install(cfg)
        elif choice == "2":
            action_remove_system(cfg)
        elif choice == "3":
            action_settings(cfg)
        elif choice == "4":
            action_vnc(cfg)
        elif choice == "5":
            action_x11(cfg)
        elif choice == "6":
            action_programs_install(cfg)
        elif choice == "7":
            action_programs_remove(cfg)
        elif choice == "8":
            action_update(cfg)
        elif choice == "9":
            action_extras_menu(cfg)
        elif choice == "10":
            action_launcher(cfg)
        elif choice == "11":
            action_help(cfg)
        elif choice == "12":
            break
        else:
            print(tr(cfg, "invalid"))
            pause(cfg)

if __name__ == "__main__":
    main()
