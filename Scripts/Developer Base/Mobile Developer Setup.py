#!/usr/bin/env python3

import os
import sys
import json
import time
import shutil
import tarfile
import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Tuple

# ----------------------------
# Embedded Mobile Dev Setup scripts
# ----------------------------

EMBEDDED_CONFIG = r"""# general settings
PROJECT_NAME="mobile-dev-setup"
AUTHOR="DevToolsX"
VERSION="2.7.0"
DESCRIPTION="Automates the setup of a web development environment in Termux, enabling developers to quickly start building web applications on Android."

# environment variables

# system
OS=$(uname -o)
ARCH=$(uname -m)
PWD=$(pwd)

# light colors
BLACK="\e[1;30m"
BLUE="\e[1;34m"
GREEN="\e[1;32m"
CYAN="\e[1;36m"
RED="\e[1;31m"
PURPLE="\e[1;35m"
YELLOW="\e[1;33m"
WHITE="\e[1;37m"

# dark colors
D_BLACK="\e[0;30m"
D_BLUE="\e[0;34m"
D_GREEN="\e[0;32m"
D_CYAN="\e[0;36m"
D_RED="\e[0;31m"
D_PURPLE="\e[0;35m"
D_YELLOW="\e[0;33m"
D_WHITE="\e[0;37m"

# background colors
BG_BLACK=$(setterm -background black)
BG_BLUE=$(setterm -background blue)
BG_GREEN=$(setterm -background green)
BG_CYAN=$(setterm -background cyan)
BG_RED=$(setterm -background red)
BG_YELLOW=$(setterm -background yellow)
BG_WHITE=$(setterm -background white)

# user variables
"""
EMBEDDED_BOOTSTRAP_SH = r"""#!/bin/bash
source ~/.mobile-dev-setup-tools/config
echo -e "${D_CYAN}Starting Update... ${WHITE}"

# global message only once
echo -e "${D_CYAN}Checking required npm modules... ${WHITE}"

# Check and install npm modules
check_and_install() {
    local module="$1"
    local bin_name="$2"
    
    if ! command -v "$bin_name" >/dev/null 2>&1; then
        echo -e "${YELLOW}Installing ${module}... ${WHITE}"
        npm install -g "$module"
    else
        echo -e "${GREEN}✓ ${bin_name} already installed ${WHITE}"
    fi
}

# Install perl (only if missing)
if ! command -v perl >/dev/null 2>&1; then
    echo -e "${D_CYAN}Installing perl... ${WHITE}"
    yes | pkg install perl
fi

# Install each module
check_and_install "psqlformat" "psqlformat"
check_and_install "@google/gemini-cli@0.1.14" "gemini"
check_and_install "@qwen-code/qwen-code@0.0.9" "qwen"
check_and_install "npm-check-updates" "ncu"
check_and_install "ngrok" "ngrok"

# new extra-keys
new_line="extra-keys = [['ESC','</>','-','HOME',{key: 'UP', display: '▲'},'END','PGUP'], ['TAB','CTRL','ALT',{key: 'LEFT', display: '◀'},{key: 'DOWN', display: '▼'},{key: 'RIGHT', display: '▶'},'PGDN']]"

sed -i "s|^extra-keys =.*|${new_line}|" ~/.termux/termux.properties

# new alias for bat
if ! grep -q 'alias cat="bat --theme=Dracula --style=plain --paging=never"' ~/.zshrc; then
    echo 'alias cat="bat --theme=Dracula --style=plain --paging=never"' >>~/.zshrc
    echo -e "${D_CYAN}Alias for cat created. ${WHITE}"
fi

# zsh-autocomplete – install only if not already present
echo -e "${D_CYAN}Checking zsh-autocomplete plugin... ${WHITE}"

PLUGIN_DIR="$HOME/.zsh-plugins/zsh-autocomplete"
SOURCE_LINE='source ~/.zsh-plugins/zsh-autocomplete/zsh-autocomplete.plugin.zsh'

if [ -d "$PLUGIN_DIR" ] || grep -q "$SOURCE_LINE" ~/.zshrc; then
    echo -e "${GREEN}zsh-autocomplete already installed. ${WHITE}"
else
    echo -e "${YELLOW}Installing zsh-autocomplete plugin... ${WHITE}"
    git clone https://github.com/marlonrichert/zsh-autocomplete.git "$PLUGIN_DIR"
    echo "$SOURCE_LINE" >>~/.zshrc
    echo -e "${GREEN}zsh-autocomplete installed successfully. ${WHITE}"
fi

# final message
echo -e "
${D_CYAN}Update complete!

${BLACK}[ ${CYAN}• ${BLACK}] ${YELLOW} Added intelligent real-time autocompletion with ${CYAN}zsh-autocomplete ${YELLOW}:
      - Type any command and get suggestions as you type
      - Menu selection with arrow keys
      - Shows descriptions and previews where available
      - Highly configurable and very fast

${GREEN}Please restart Termux (or run ${CYAN}exec zsh ${GREEN}) to apply the changes.${WHITE}
"
"""
EMBEDDED_UPDATE_SH = r"""#!/bin/bash

source ~/.mobile-dev-setup-tools/config

# timestamp file
TIMESTAMP_FILE=~/.mobile-dev-setup-tools/.last_update_check
CHECK_INTERVAL=$((24 * 60 * 60))

# check updates
should_check_updates() {
	if [ ! -f "$TIMESTAMP_FILE" ]; then
		return 0 # first time
	fi

	local last_check=$(cat "$TIMESTAMP_FILE")
	local current_time=$(date +%s)
	local time_diff=$((current_time - last_check))

	[ $time_diff -ge $CHECK_INTERVAL ]
}

# update timestamp
update_timestamp() {
	date +%s >"$TIMESTAMP_FILE"
}

# update only if the interval exceeds the specified time frame
if ! should_check_updates; then
  echo ""
  return 0
fi

exec </dev/tty

# mobile-dev-setup-tools update
cd ${core}
git fetch
local_commit=$(git rev-parse main)
remote_commit=$(git rev-parse origin/main)

if [ "${local_commit}" != "${remote_commit}" ]; then
	echo -e -n "${D_CYAN}A new update is available. Would you like to update ${CYAN}Mobile Dev Setup${D_CYAN}? [Y/n] ${WHITE}"
	read -r updateOption

	if [[ "${updateOption}" == "y" || "${updateOption}" == "Y" ]]; then
		git pull origin main
		update_timestamp
		bash bootstrap.sh
	elif [[ "${updateOption}" == "n" || "${updateOption}" == "N" ]]; then
		echo -e "Abort"
		update_timestamp
		cd
	else
		echo -e "Error"
		update_timestamp
		cd
	fi
else
	echo -e ""
	update_timestamp
fi

# nvchad-termux update
cd ~/.mobile-dev-setup-tools/nvchad-termux/
git fetch
local_commit=$(git rev-parse main)
remote_commit=$(git rev-parse origin/main)

if [ "${local_commit}" != "${remote_commit}" ]; then
	echo -e -n "${D_CYAN}A new update is available. Would you like to update ${CYAN}NvChad-Termux${D_CYAN}? [Y/n] ${WHITE}"
	read -r nvchadUpdate

	if [[ "${nvchadUpdate}" == "y" || "${nvchadUpdate}" == "Y" ]]; then
		git pull origin main
		bash bootstrap.sh
	elif [[ "${nvchadUpdate}" == "n" || "${nvchadUpdate}" == "N" ]]; then
		echo -e "Abort"
		cd
	else
		echo -e "Error"
		cd
	fi
else
	cd
fi
"""

# ----------------------------
# Constants / Paths
# ----------------------------

HOME = Path.home()
APP_DIR = HOME / ".mobile-dev-setup"
BACKUPS_DIR = APP_DIR / "backups"
STATE_FILE = APP_DIR / "state.json"

TOOLS_DIR = HOME / ".mobile-dev-setup-tools"
TOOLS_CONFIG_PATH = TOOLS_DIR / "config"
TOOLS_BOOTSTRAP_PATH = TOOLS_DIR / "bootstrap.sh"
TOOLS_UPDATE_PATH = TOOLS_DIR / "update.sh"

TERMUX_DIR = HOME / ".termux"

MARK_BEGIN = "# >>> MOBILE DEV SETUP (managed) >>>"
MARK_END   = "# <<< MOBILE DEV SETUP (managed) <<<"

# Packages from mobile-dev-setup-tools setup.sh
TERMUX_PACKAGES = [
    "git", "gh", "zsh", "neovim", "nodejs", "python", "perl", "php",
    "curl", "wget", "lua-language-server", "lsd", "bat", "tur-repo",
    "proot", "ncurses-utils", "ripgrep", "stylua", "tmate", "cloudflared",
    "translate-shell", "html2text", "jq", "postgresql", "mariadb", "sqlite",
    "bc", "tree", "fzf", "imagemagick", "shfmt",
]

TERMUX_USER_PACKAGES = [
    "mongodb",
]

NPM_GLOBAL_MODULES = [
    "@devcorex/dev.x",
    "typescript",
    "@nestjs/cli",
    "prettier",
    "live-server",
    "localtunnel",
    "vercel",
    "markserv",
    "psqlformat",
    "@google/gemini-cli@0.1.14",
    "@qwen-code/qwen-code@0.0.9",
    "npm-check-updates",
    "ngrok",
]

ZSH_PLUGIN_REPOS = [
    ("zsh-defer", "https://github.com/romkatv/zsh-defer.git", "source ~/.zsh-plugins/zsh-defer/zsh-defer.plugin.zsh"),
    ("powerlevel10k", "https://github.com/romkatv/powerlevel10k.git", "source ~/.zsh-plugins/powerlevel10k/powerlevel10k.zsh-theme"),
    ("zsh-autosuggestions", "https://github.com/zsh-users/zsh-autosuggestions.git", "source ~/.zsh-plugins/zsh-autosuggestions/zsh-autosuggestions.zsh"),
    ("zsh-syntax-highlighting", "https://github.com/zsh-users/zsh-syntax-highlighting.git", "source ~/.zsh-plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"),
    ("zsh-history-substring-search", "https://github.com/zsh-users/zsh-history-substring-search.git", "source ~/.zsh-plugins/zsh-history-substring-search/zsh-history-substring-search.zsh"),
    ("zsh-completions", "https://github.com/zsh-users/zsh-completions.git", "fpath+=~/.zsh-plugins/zsh-completions"),
    ("fzf-tab", "https://github.com/Aloxaf/fzf-tab.git", "source ~/.zsh-plugins/fzf-tab/fzf-tab.plugin.zsh"),
    ("zsh-you-should-use", "https://github.com/MichaelAquilina/zsh-you-should-use.git", "source ~/.zsh-plugins/zsh-you-should-use/you-should-use.plugin.zsh"),
    ("zsh-autopair", "https://github.com/hlissner/zsh-autopair.git", "source ~/.zsh-plugins/zsh-autopair/autopair.zsh"),
    ("zsh-better-npm-completion", "https://github.com/lukechilds/zsh-better-npm-completion.git", "source ~/.zsh-plugins/zsh-better-npm-completion/zsh-better-npm-completion.plugin.zsh"),
    ("zsh-autocomplete", "https://github.com/marlonrichert/zsh-autocomplete.git", "source ~/.zsh-plugins/zsh-autocomplete/zsh-autocomplete.plugin.zsh"),
]

# Fonts: mobile-dev-setup-tools ships a Meslo Nerd Font in assets; embedding it would bloat this script.
# Instead, we download a known Nerd Font at install time.
# You can change URL if you prefer a different font.
DEFAULT_FONT_URL = "https://raw.githubusercontent.com/ryanoasis/nerd-fonts/master/patched-fonts/Meslo/L/Regular/MesloLGSNerdFont-Regular.ttf"

NVCHAD_TERMUX_REPO = "https://github.com/DevToolsXOfficial/nvchad-termux.git"

# ----------------------------
# Helpers
# ----------------------------

class C:
    """ANSI colors (safe-ish)."""
    OK = "\033[92m"
    INFO = "\033[96m"
    WARN = "\033[93m"
    ERR = "\033[91m"
    DIM = "\033[2m"
    END = "\033[0m"

def supports_color() -> bool:
    return sys.stdout.isatty() and os.environ.get("TERM", "") not in ("dumb", "")

def c(text: str, color: str) -> str:
    if supports_color():
        return f"{color}{text}{C.END}"
    return text

def header(title: str) -> None:
    print("\n" + c("═" * 56, C.DIM))
    print(c(f"  {title}", C.INFO))
    print(c("═" * 56, C.DIM))

def ensure_dirs() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

def which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)

def is_termux() -> bool:
    return which("pkg") is not None and os.environ.get("PREFIX") is not None

def bash(cmd: str, check: bool = True) -> int:
    """Run a bash -lc command with live output."""
    p = subprocess.Popen(["bash", "-lc", cmd], stdout=sys.stdout, stderr=sys.stderr)
    rc = p.wait()
    if check and rc != 0:
        raise RuntimeError(f"Command failed ({rc}): {cmd}")
    return rc

def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except UnicodeDecodeError:
        return p.read_text(errors="replace")

def write_text(p: Path, content: str, mode: int = 0o644) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    try:
        os.chmod(p, mode)
    except PermissionError:
        pass

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def now_stamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_state(state: dict) -> None:
    ensure_dirs()
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

# ----------------------------
# Backup / Restore
# ----------------------------

BACKUP_TARGETS = [
    TERMUX_DIR / "termux.properties",
    TERMUX_DIR / "colors.properties",
    TERMUX_DIR / "font.ttf",
    HOME / ".zshrc",
    HOME / ".bashrc",
    HOME / ".profile",
]

def make_backup() -> Path:
    """
    Backup Termux settings (NOT packages).
    Produces a tar.gz containing known config files that this tool may change.
    """
    ensure_dirs()
    stamp = now_stamp()
    out = BACKUPS_DIR / f"termux-settings-backup-{stamp}.tar.gz"

    manifest = {
        "created": stamp,
        "targets": [],
        "note": "Backup of Termux settings files only (not installed programs).",
    }

    with tarfile.open(out, "w:gz") as tf:
        for src in BACKUP_TARGETS:
            if src.exists():
                arcname = str(src).replace(str(HOME) + "/", "HOME/")
                tf.add(str(src), arcname=arcname)
                manifest["targets"].append({"path": str(src), "sha256": sha256_file(src)})
        # include a manifest.json inside the tar
        m_bytes = json.dumps(manifest, indent=2).encode("utf-8")
        info = tarfile.TarInfo(name="manifest.json")
        info.size = len(m_bytes)
        info.mtime = time.time()
        tf.addfile(info, fileobj=io_bytes(m_bytes))

    state = load_state()
    state["last_backup"] = str(out)
    state["backups"] = sorted(list(set(state.get("backups", []) + [str(out)])))
    save_state(state)

    print(c(f"✓ Backup saved: {out}", C.OK))
    return out

def io_bytes(b: bytes):
    import io
    return io.BytesIO(b)

def list_backups() -> list[Path]:
    ensure_dirs()
    backups = sorted(BACKUPS_DIR.glob("termux-settings-backup-*.tar.gz"))
    return backups

def restore_backup(backup_path: Path) -> None:
    """
    Restore settings from a backup tar.gz.
    This will overwrite your current files for those settings.
    """
    if not backup_path.exists():
        raise FileNotFoundError(str(backup_path))

    header("Restoring settings")
    print(c("This will overwrite your current Termux settings files.", C.WARN))
    bash("termux-toast 'Restoring Termux settings...' >/dev/null 2>&1 || true", check=False)

    with tarfile.open(backup_path, "r:gz") as tf:
        members = tf.getmembers()
        for m in members:
            if not m.name.startswith("HOME/"):
                continue
            rel = m.name.replace("HOME/", "")
            dest = HOME / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            tf.extract(m, path=str(APP_DIR))  # extract to app dir first
            extracted = APP_DIR / m.name
            # move into place
            shutil.copy2(extracted, dest)

    print(c("✓ Settings restored.", C.OK))
    print(c("Tip: Restart Termux to ensure everything reloads.", C.INFO))

# ----------------------------
# Mobile Dev Setup install / update
# ----------------------------

def write_tools_files(core_path: Path) -> None:
    """
    Write mobile-dev-setup-tools helper scripts into ~/.mobile-dev-setup-tools.
    We set 'core' path inside config so the update script knows where it lives.
    """
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)

    # Ensure config ends with the tools path line (the original setup.sh appends).
    cfg = EMBEDDED_CONFIG.strip() + "\n\n" + f"tools='{core_path}'\n"
    write_text(TOOLS_CONFIG_PATH, cfg)

    write_text(TOOLS_BOOTSTRAP_PATH, EMBEDDED_BOOTSTRAP_SH.strip() + "\n", mode=0o755)
    write_text(TOOLS_UPDATE_PATH, EMBEDDED_UPDATE_SH.strip() + "\n", mode=0o755)

def pkg_update_upgrade() -> None:
    header("Updating Termux packages")
    bash("yes | pkg update")
    bash("yes | pkg upgrade")

def pkg_install(pkgs: Iterable[str]) -> None:
    joined = " ".join(pkgs)
    bash(f"yes | pkg install {joined}")

def npm_install(mods: Iterable[str]) -> None:
    joined = " ".join(mods)
    header("Installing global npm tools")
    bash(f"npm install -g {joined}")

def patch_localtunnel_android_openurl() -> None:
    header("Patching localtunnel Android openurl handler")
    # Same patch as setup.sh, made safe if file doesn't exist.
    cmd = r"""
OPENURL_JS="${PREFIX}/lib/node_modules/localtunnel/node_modules/openurl/openurl.js"
if [ -f "$OPENURL_JS" ]; then
  sed -i '/case '\''win32'\''/,/break;/ a\    case '\''android'\'':\n        command = '\''termux-open-url'\'';\n        break;' "$OPENURL_JS" || true
  sed -i 's/break;/break;/' "$OPENURL_JS" || true
  echo "✓ Patched: $OPENURL_JS"
else
  echo "Skipped (not found): $OPENURL_JS"
fi
"""
    bash(cmd, check=False)

def install_oh_my_zsh() -> None:
    header("Installing Oh My Zsh")
    cmd = r"""
cd "$HOME"
curl -fsSL https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh -o install.sh
# Prevent the installer from switching shells immediately (we want to finish setup first)
sed -i '/exec zsh -l/s/^/#/' install.sh || true
sh install.sh
rm -f install.sh
"""
    bash(cmd)

def clone_zsh_plugins() -> None:
    header("Installing Zsh plugins")
    plugins_dir = HOME / ".zsh-plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)

    for name, repo, zshrc_line in ZSH_PLUGIN_REPOS:
        dest = plugins_dir / name
        if dest.exists():
            print(c(f"✓ {name} already present", C.OK))
            continue
        bash(f"git clone --depth=1 {repo} {dest}")

def upsert_zshrc_section(core_path: Path) -> None:
    header("Configuring ~/.zshrc")
    zshrc = HOME / ".zshrc"
    existing = read_text(zshrc)

    managed_block = "\n".join([
        MARK_BEGIN,
        "# Added by Mobile Developer Setup.py (safe to remove by restore/uninstall).",
        # Plugin source lines (only those that exist)
        *[line for _, _, line in ZSH_PLUGIN_REPOS],
        "",
        "bindkey '^[[A' history-substring-search-up",
        "bindkey '^[[B' history-substring-search-down",
        "",
        "zstyle ':completion:*' menu-select yes",
        "zstyle ':fzf-tab:*' switch-word yes",
        "",
        f"tools='{core_path}'",
        "alias ls=\"lsd\"",
        "alias cat=\"bat --theme=Dracula --style=plain --paging=never\"",
        MARK_END,
        "",
    ])

    if MARK_BEGIN in existing and MARK_END in existing:
        # Replace managed block
        import re
        new = re.sub(
            re.escape(MARK_BEGIN) + r".*?" + re.escape(MARK_END),
            managed_block.strip(),
            existing,
            flags=re.S,
        )
    else:
        new = existing.rstrip() + "\n\n" + managed_block

    write_text(zshrc, new)

def configure_termux_ui(font_url: str = DEFAULT_FONT_URL) -> None:
    header("Applying Termux UI settings (extra keys, cursor, font)")
    TERMUX_DIR.mkdir(parents=True, exist_ok=True)

    # termux.properties: ensure extra-keys and cursor blink
    termux_props = TERMUX_DIR / "termux.properties"
    props = read_text(termux_props)

    # Minimal, clean settings (inspired by mobile-dev-setup-tools).
    cursor_blink = "terminal-cursor-blink-rate=500"
    extra_keys = "extra-keys = [['ESC','</>','-','HOME',{key: 'UP', display: '▲'},'END','PGUP'], ['TAB','CTRL','ALT',{key: 'LEFT', display: '◀'},{key: 'DOWN', display: '▼'},{key: 'RIGHT', display: '▶'},'PGDN']]"

    lines = [ln for ln in props.splitlines() if ln.strip() != ""]
    def replace_or_add(prefix: str, value: str):
        nonlocal lines
        for i, ln in enumerate(lines):
            if ln.strip().startswith(prefix):
                lines[i] = value
                return
        lines.append(value)

    replace_or_add("terminal-cursor-blink-rate", cursor_blink)
    replace_or_add("extra-keys", extra_keys)

    write_text(termux_props, "\n".join(lines) + "\n")

    # colors.properties
    colors = TERMUX_DIR / "colors.properties"
    col = read_text(colors).splitlines()
    col = [ln for ln in col if not ln.strip().startswith("cursor=")]
    col.append("cursor=#00FF00")
    write_text(colors, "\n".join(col) + "\n")

    # font.ttf download
    cmd = fr"""
cd "$HOME"
mkdir -p "{TERMUX_DIR}"
curl -L --fail "{font_url}" -o "{TERMUX_DIR / 'font.ttf'}"
"""
    bash(cmd)

    # Apply changes
    bash("termux-reload-settings >/dev/null 2>&1 || true", check=False)
    bash("termux-toast 'Termux UI updated (keys/font/colors)' >/dev/null 2>&1 || true", check=False)

def install_nvchad_termux() -> None:
    header("Installing NvChad (Neovim setup)")
    cmd = r"""
rm -rf ~/.config/nvim ~/.local/state/nvim ~/.local/share/nvim
rm -rf ~/.mobile-dev-setup-tools/nvchad-termux
git clone --depth=1 """ + NVCHAD_TERMUX_REPO + r""" ~/.mobile-dev-setup-tools/nvchad-termux
cd ~/.mobile-dev-setup-tools/nvchad-termux
bash nvchad.sh
"""
    bash(cmd)

def install_setup() -> None:
    if not is_termux():
        print(c("This script must be run inside Termux.", C.ERR))
        sys.exit(1)

    ensure_dirs()
    header("Mobile Developer Setup – Install")

    # Auto-backup first (super important)
    print(c("Creating a safety backup of your Termux settings first…", C.INFO))
    backup_path = make_backup()

    # Keep a record that we created this backup automatically
    state = load_state()
    state["install_backup"] = str(backup_path)
    save_state(state)

    core_path = Path.cwd()
    write_tools_files(core_path)

    pkg_update_upgrade()
    header("Installing Termux packages")
    pkg_install(TERMUX_PACKAGES)

    header("Installing Termux user packages (mongodb)")
    pkg_install(TERMUX_USER_PACKAGES)

    npm_install(NPM_GLOBAL_MODULES)
    patch_localtunnel_android_openurl()
    install_oh_my_zsh()
    clone_zsh_plugins()
    upsert_zshrc_section(core_path)
    configure_termux_ui()

    # Optional but included in mobile-dev-setup-tools
    install_nvchad_termux()

    header("Done")
    print(c("✓ Install finished.", C.OK))
    print(c("Restart Termux now to apply everything.", C.INFO))

def run_update() -> None:
    if not is_termux():
        print(c("This script must be run inside Termux.", C.ERR))
        return

    header("Update")
    # Run the original mobile-dev-setup-tools bootstrap for extra tools / fixes
    if TOOLS_BOOTSTRAP_PATH.exists():
        bash(f"bash {TOOLS_BOOTSTRAP_PATH}", check=False)
    else:
        print(c("Tools bootstrap script not found. Run Install first.", C.WARN))

    print(c("✓ Update completed. Restart Termux if anything changed.", C.OK))

def uninstall_files_only() -> None:
    """
    Remove files/directories created by this setup (but do NOT uninstall packages).
    Restoring a backup is the safest way to undo all customizations.
    """
    header("Removing setup files (does not remove packages)")
    paths = [
        TOOLS_DIR,
        HOME / ".zsh-plugins",
        APP_DIR / "HOME",  # temporary restore extraction
    ]
    for p in paths:
        if p.exists():
            try:
                shutil.rmtree(p)
                print(c(f"✓ Removed {p}", C.OK))
            except Exception as e:
                print(c(f"! Could not remove {p}: {e}", C.WARN))

    # Remove our managed block from .zshrc (if present) – without touching user content.
    zshrc = HOME / ".zshrc"
    if zshrc.exists():
        import re
        txt = read_text(zshrc)
        if MARK_BEGIN in txt and MARK_END in txt:
            new = re.sub(
                re.escape(MARK_BEGIN) + r".*?" + re.escape(MARK_END) + r"\n?",
                "",
                txt,
                flags=re.S,
            ).rstrip() + "\n"
            write_text(zshrc, new)
            print(c("✓ Removed managed section from ~/.zshrc", C.OK))

    print(c("Files removed. To fully undo settings, restore a backup.", C.INFO))

def choose_backup_interactive() -> Optional[Path]:
    backups = list_backups()
    if not backups:
        print(c("No backups found in ~/.mobile-dev-setup-tools/backups", C.WARN))
        return None

    print(c("\nAvailable backups:", C.INFO))
    for i, b in enumerate(backups, 1):
        print(f"  {i}) {b.name}")

    while True:
        choice = input(c("Pick a backup number (or 0 to cancel): ", C.INFO)).strip()
        if choice == "0":
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(backups):
            return backups[int(choice) - 1]
        print(c("Invalid choice.", C.WARN))

def restore_and_remove() -> None:
    if not is_termux():
        print(c("This script must be run inside Termux.", C.ERR))
        return

    header("Restore settings + remove setup files")
    b = choose_backup_interactive()
    if not b:
        return

    restore_backup(b)
    uninstall_files_only()

    header("Done")
    print(c("✓ Restored settings and removed setup files.", C.OK))
    print(c("Restart Termux now.", C.INFO))

def backup_only() -> None:
    if not is_termux():
        print(c("This script must be run inside Termux.", C.ERR))
        return
    header("Backup Termux settings")
    make_backup()

def show_info() -> None:
    header("Info")
    state = load_state()
    print("App dir:", APP_DIR)
    print("Backups:", BACKUPS_DIR)
    if state.get("install_backup"):
        print("Install backup:", state["install_backup"])
    if state.get("last_backup"):
        print("Last backup:", state["last_backup"])
    print("\nThis tool changes only settings + config files and creates ~/.mobile-dev-setup-tools and ~/.zsh-plugins.")

# ----------------------------
# Menu UI
# ----------------------------

def menu() -> None:
    ensure_dirs()
    while True:
        header("Mobile Developer Setup")
        print("1) Install / Setup (Mobile dev environment)")
        print("2) Update (extras / fixes)")
        print("3) Backup Termux settings")
        print("4) Restore settings + Remove setup files (undo)")
        print("5) Remove setup files only (keep current settings)")
        print("6) Info")
        print("0) Exit")
        choice = input(c("\nChoose a number: ", C.INFO)).strip()

        try:
            if choice == "1":
                install_setup()
            elif choice == "2":
                run_update()
            elif choice == "3":
                backup_only()
            elif choice == "4":
                restore_and_remove()
            elif choice == "5":
                uninstall_files_only()
            elif choice == "6":
                show_info()
            elif choice == "0":
                print(c("Bye!", C.OK))
                return
            else:
                print(c("Invalid choice. Use numbers from the menu.", C.WARN))
        except KeyboardInterrupt:
            print("\n" + c("Cancelled.", C.WARN))
        except Exception as e:
            print(c(f"\nError: {e}", C.ERR))
            print(c("If something failed mid-install, you can restore your backup from option 4.", C.INFO))
        input(c("\nPress Enter to return to the menu…", C.DIM))

def main() -> None:
    # Allow running non-interactively later, but default to menu.
    menu()

if __name__ == "__main__":
    main()
