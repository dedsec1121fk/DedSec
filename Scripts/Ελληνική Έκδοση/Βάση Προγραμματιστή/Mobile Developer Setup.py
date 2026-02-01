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
EMBEDDED_CONFIG = '# general settings\nPROJECT_NAME="mobile-dev-setup"\nAUTHOR="DevToolsX"\nVERSION="2.7.0"\nDESCRIPTION="Automates the setup of a web development environment in Termux, enabling developers to quickly start building web applications on Android."\n\n# environment variables\n\n# system\nOS=$(uname -o)\nARCH=$(uname -m)\nPWD=$(pwd)\n\n# light colors\nBLACK="\\e[1;30m"\nBLUE="\\e[1;34m"\nGREEN="\\e[1;32m"\nCYAN="\\e[1;36m"\nRED="\\e[1;31m"\nPURPLE="\\e[1;35m"\nYELLOW="\\e[1;33m"\nWHITE="\\e[1;37m"\n\n# dark colors\nD_BLACK="\\e[0;30m"\nD_BLUE="\\e[0;34m"\nD_GREEN="\\e[0;32m"\nD_CYAN="\\e[0;36m"\nD_RED="\\e[0;31m"\nD_PURPLE="\\e[0;35m"\nD_YELLOW="\\e[0;33m"\nD_WHITE="\\e[0;37m"\n\n# background colors\nBG_BLACK=$(setterm -background black)\nBG_BLUE=$(setterm -background blue)\nBG_GREEN=$(setterm -background green)\nBG_CYAN=$(setterm -background cyan)\nBG_RED=$(setterm -background red)\nBG_YELLOW=$(setterm -background yellow)\nBG_WHITE=$(setterm -background white)\n\n# user variables\n'
EMBEDDED_BOOTSTRAP_SH = '#!/bin/bash\nsource ~/.mobile-dev-setup-tools/config\necho -e "${D_CYAN}Starting Update... ${WHITE}"\n\n# global message only once\necho -e "${D_CYAN}Checking required npm modules... ${WHITE}"\n\n# Check and install npm modules\ncheck_and_install() {\n    local module="$1"\n    local bin_name="$2"\n    \n    if ! command -v "$bin_name" >/dev/null 2>&1; then\n        echo -e "${YELLOW}Installing ${module}... ${WHITE}"\n        npm install -g "$module"\n    else\n        echo -e "${GREEN}✓ ${bin_name} already installed ${WHITE}"\n    fi\n}\n\n# Install perl (only if missing)\nif ! command -v perl >/dev/null 2>&1; then\n    echo -e "${D_CYAN}Installing perl... ${WHITE}"\n    yes | pkg install perl\nfi\n\n# Install each module\ncheck_and_install "psqlformat" "psqlformat"\ncheck_and_install "@google/gemini-cli@0.1.14" "gemini"\ncheck_and_install "@qwen-code/qwen-code@0.0.9" "qwen"\ncheck_and_install "npm-check-updates" "ncu"\ncheck_and_install "ngrok" "ngrok"\n\n# new extra-keys\nnew_line="extra-keys = [[\'ESC\',\'</>\',\'-\',\'HOME\',{key: \'UP\', display: \'▲\'},\'END\',\'PGUP\'], [\'TAB\',\'CTRL\',\'ALT\',{key: \'LEFT\', display: \'◀\'},{key: \'DOWN\', display: \'▼\'},{key: \'RIGHT\', display: \'▶\'},\'PGDN\']]"\n\nsed -i "s|^extra-keys =.*|${new_line}|" ~/.termux/termux.properties\n\n# new alias for bat\nif ! grep -q \'alias cat="bat --theme=Dracula --style=plain --paging=never"\' ~/.zshrc; then\n    echo \'alias cat="bat --theme=Dracula --style=plain --paging=never"\' >>~/.zshrc\n    echo -e "${D_CYAN}Alias for cat created. ${WHITE}"\nfi\n\n# zsh-autocomplete – install only if not already present\necho -e "${D_CYAN}Checking zsh-autocomplete plugin... ${WHITE}"\n\nPLUGIN_DIR="$HOME/.zsh-plugins/zsh-autocomplete"\nSOURCE_LINE=\'source ~/.zsh-plugins/zsh-autocomplete/zsh-autocomplete.plugin.zsh\'\n\nif [ -d "$PLUGIN_DIR" ] || grep -q "$SOURCE_LINE" ~/.zshrc; then\n    echo -e "${GREEN}zsh-autocomplete already installed. ${WHITE}"\nelse\n    echo -e "${YELLOW}Installing zsh-autocomplete plugin... ${WHITE}"\n    git clone https://github.com/marlonrichert/zsh-autocomplete.git "$PLUGIN_DIR"\n    echo "$SOURCE_LINE" >>~/.zshrc\n    echo -e "${GREEN}zsh-autocomplete installed successfully. ${WHITE}"\nfi\n\n# final message\necho -e "\n${D_CYAN}Update complete!\n\n${BLACK}[ ${CYAN}• ${BLACK}] ${YELLOW} Added intelligent real-time autocompletion with ${CYAN}zsh-autocomplete ${YELLOW}:\n      - Type any command and get suggestions as you type\n      - Menu selection with arrow keys\n      - Shows descriptions and previews where available\n      - Highly configurable and very fast\n\n${GREEN}Please restart Termux (or run ${CYAN}exec zsh ${GREEN}) to apply the changes.${WHITE}\n"\n'
EMBEDDED_UPDATE_SH = '#!/bin/bash\n\nsource ~/.mobile-dev-setup-tools/config\n\n# timestamp file\nTIMESTAMP_FILE=~/.mobile-dev-setup-tools/.last_update_check\nCHECK_INTERVAL=$((24 * 60 * 60))\n\n# check updates\nshould_check_updates() {\n\tif [ ! -f "$TIMESTAMP_FILE" ]; then\n\t\treturn 0 # first time\n\tfi\n\n\tlocal last_check=$(cat "$TIMESTAMP_FILE")\n\tlocal current_time=$(date +%s)\n\tlocal time_diff=$((current_time - last_check))\n\n\t[ $time_diff -ge $CHECK_INTERVAL ]\n}\n\n# update timestamp\nupdate_timestamp() {\n\tdate +%s >"$TIMESTAMP_FILE"\n}\n\n# update only if the interval exceeds the specified time frame\nif ! should_check_updates; then\n  echo ""\n  return 0\nfi\n\nexec </dev/tty\n\n# mobile-dev-setup-tools update\ncd ${core}\ngit fetch\nlocal_commit=$(git rev-parse main)\nremote_commit=$(git rev-parse origin/main)\n\nif [ "${local_commit}" != "${remote_commit}" ]; then\n\techo -e -n "${D_CYAN}A new update is available. Would you like to update ${CYAN}Mobile Dev Setup${D_CYAN}? [Y/n] ${WHITE}"\n\tread -r updateOption\n\n\tif [[ "${updateOption}" == "y" || "${updateOption}" == "Y" ]]; then\n\t\tgit pull origin main\n\t\tupdate_timestamp\n\t\tbash bootstrap.sh\n\telif [[ "${updateOption}" == "n" || "${updateOption}" == "N" ]]; then\n\t\techo -e "Abort"\n\t\tupdate_timestamp\n\t\tcd\n\telse\n\t\techo -e "Error"\n\t\tupdate_timestamp\n\t\tcd\n\tfi\nelse\n\techo -e ""\n\tupdate_timestamp\nfi\n\n# nvchad-termux update\ncd ~/.mobile-dev-setup-tools/nvchad-termux/\ngit fetch\nlocal_commit=$(git rev-parse main)\nremote_commit=$(git rev-parse origin/main)\n\nif [ "${local_commit}" != "${remote_commit}" ]; then\n\techo -e -n "${D_CYAN}A new update is available. Would you like to update ${CYAN}NvChad-Termux${D_CYAN}? [Y/n] ${WHITE}"\n\tread -r nvchadUpdate\n\n\tif [[ "${nvchadUpdate}" == "y" || "${nvchadUpdate}" == "Y" ]]; then\n\t\tgit pull origin main\n\t\tbash bootstrap.sh\n\telif [[ "${nvchadUpdate}" == "n" || "${nvchadUpdate}" == "N" ]]; then\n\t\techo -e "Abort"\n\t\tcd\n\telse\n\t\techo -e "Error"\n\t\tcd\n\tfi\nelse\n\tcd\nfi\n'
HOME = Path.home()
APP_DIR = HOME / '.mobile-dev-setup'
BACKUPS_DIR = APP_DIR / 'backups'
STATE_FILE = APP_DIR / 'state.json'
TOOLS_DIR = HOME / '.mobile-dev-setup-tools'
TOOLS_CONFIG_PATH = TOOLS_DIR / 'config'
TOOLS_BOOTSTRAP_PATH = TOOLS_DIR / 'bootstrap.sh'
TOOLS_UPDATE_PATH = TOOLS_DIR / 'update.sh'
TERMUX_DIR = HOME / '.termux'
MARK_BEGIN = '# >>> MOBILE DEV SETUP (managed) >>>'
MARK_END = '# <<< MOBILE DEV SETUP (managed) <<<'
TERMUX_PACKAGES = ['git', 'gh', 'zsh', 'neovim', 'nodejs', 'python', 'perl', 'php', 'curl', 'wget', 'lua-language-server', 'lsd', 'bat', 'tur-repo', 'proot', 'ncurses-utils', 'ripgrep', 'stylua', 'tmate', 'cloudflared', 'translate-shell', 'html2text', 'jq', 'postgresql', 'mariadb', 'sqlite', 'bc', 'tree', 'fzf', 'imagemagick', 'shfmt']
TERMUX_USER_PACKAGES = ['mongodb']
NPM_GLOBAL_MODULES = ['@devcorex/dev.x', 'typescript', '@nestjs/cli', 'prettier', 'live-server', 'localtunnel', 'vercel', 'markserv', 'psqlformat', '@google/gemini-cli@0.1.14', '@qwen-code/qwen-code@0.0.9', 'npm-check-updates', 'ngrok']
ZSH_PLUGIN_REPOS = [('zsh-defer', 'https://github.com/romkatv/zsh-defer.git', 'source ~/.zsh-plugins/zsh-defer/zsh-defer.plugin.zsh'), ('powerlevel10k', 'https://github.com/romkatv/powerlevel10k.git', 'source ~/.zsh-plugins/powerlevel10k/powerlevel10k.zsh-theme'), ('zsh-autosuggestions', 'https://github.com/zsh-users/zsh-autosuggestions.git', 'source ~/.zsh-plugins/zsh-autosuggestions/zsh-autosuggestions.zsh'), ('zsh-syntax-highlighting', 'https://github.com/zsh-users/zsh-syntax-highlighting.git', 'source ~/.zsh-plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh'), ('zsh-history-substring-search', 'https://github.com/zsh-users/zsh-history-substring-search.git', 'source ~/.zsh-plugins/zsh-history-substring-search/zsh-history-substring-search.zsh'), ('zsh-completions', 'https://github.com/zsh-users/zsh-completions.git', 'fpath+=~/.zsh-plugins/zsh-completions'), ('fzf-tab', 'https://github.com/Aloxaf/fzf-tab.git', 'source ~/.zsh-plugins/fzf-tab/fzf-tab.plugin.zsh'), ('zsh-you-should-use', 'https://github.com/MichaelAquilina/zsh-you-should-use.git', 'source ~/.zsh-plugins/zsh-you-should-use/you-should-use.plugin.zsh'), ('zsh-autopair', 'https://github.com/hlissner/zsh-autopair.git', 'source ~/.zsh-plugins/zsh-autopair/autopair.zsh'), ('zsh-better-npm-completion', 'https://github.com/lukechilds/zsh-better-npm-completion.git', 'source ~/.zsh-plugins/zsh-better-npm-completion/zsh-better-npm-completion.plugin.zsh'), ('zsh-autocomplete', 'https://github.com/marlonrichert/zsh-autocomplete.git', 'source ~/.zsh-plugins/zsh-autocomplete/zsh-autocomplete.plugin.zsh')]
DEFAULT_FONT_URL = 'https://raw.githubusercontent.com/ryanoasis/nerd-fonts/master/patched-fonts/Meslo/L/Regular/MesloLGSNerdFont-Regular.ttf'
NVCHAD_TERMUX_REPO = 'https://github.com/DevToolsXOfficial/nvchad-termux.git'

class C:
    """ANSI colors (safe-ish)."""
    OK = '\x1b[92m'
    INFO = '\x1b[96m'
    WARN = '\x1b[93m'
    ERR = '\x1b[91m'
    DIM = '\x1b[2m'
    END = '\x1b[0m'

def supports_color() -> bool:
    return sys.stdout.isatty() and os.environ.get('TERM', '') not in ('dumb', '')

def c(text: str, color: str) -> str:
    if supports_color():
        return f'{color}{text}{C.END}'
    return text

def header(title: str) -> None:
    print('\n' + c('═' * 56, C.DIM))
    print(c(f'  {title}', C.INFO))
    print(c('═' * 56, C.DIM))

def ensure_dirs() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

def which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)

def is_termux() -> bool:
    return which('pkg') is not None and os.environ.get('PREFIX') is not None

def bash(cmd: str, check: bool=True) -> int:
    """Εκτέλεση a bash -lc command with live output."""
    p = subprocess.Popen(['bash', '-lc', cmd], stdout=sys.stdout, stderr=sys.stderr)
    rc = p.wait()
    if check and rc != 0:
        raise RuntimeError(f'Command απέτυχε ({rc}): {cmd}')
    return rc

def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding='utf-8')
    except FileNotFoundError:
        return ''
    except UnicodeDecodeError:
        return p.read_text(errors='replace')

def write_text(p: Path, content: str, mode: int=420) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')
    try:
        os.chmod(p, mode)
    except PermissionError:
        pass

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def now_stamp() -> str:
    return time.strftime('%Y%m%d-%H%M%S')

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}

def save_state(state: dict) -> None:
    ensure_dirs()
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding='utf-8')
BACKUP_TARGETS = [TERMUX_DIR / 'termux.properties', TERMUX_DIR / 'colors.properties', TERMUX_DIR / 'font.ttf', HOME / '.zshrc', HOME / '.bashrc', HOME / '.profile']

def make_backup() -> Path:
    """
    Backup Termux settings (NOT packages).
    Produces a tar.gz containing known config files that this tool may change.
    """
    ensure_dirs()
    stamp = now_stamp()
    out = BACKUPS_DIR / f'termux-settings-backup-{stamp}.tar.gz'
    manifest = {'created': stamp, 'targets': [], 'note': 'Backup of Termux settings files only (not installed programs).'}
    with tarfile.open(out, 'w:gz') as tf:
        for src in BACKUP_TARGETS:
            if src.exists():
                arcname = str(src).replace(str(HOME) + '/', 'HOME/')
                tf.add(str(src), arcname=arcname)
                manifest['targets'].append({'path': str(src), 'sha256': sha256_file(src)})
        m_bytes = json.dumps(manifest, indent=2).encode('utf-8')
        info = tarfile.TarInfo(name='manifest.json')
        info.size = len(m_bytes)
        info.mtime = time.time()
        tf.addfile(info, fileobj=io_bytes(m_bytes))
    state = load_state()
    state['last_backup'] = str(out)
    state['backups'] = sorted(list(set(state.get('backups', []) + [str(out)])))
    save_state(state)
    print(c(f'✓ Πίσωup αποθηκεύτηκε: {out}', C.OK))
    return out

def io_bytes(b: bytes):
    import io
    return io.BytesIO(b)

def list_backups() -> list[Path]:
    ensure_dirs()
    backups = sorted(BACKUPS_DIR.glob('termux-settings-backup-*.tar.gz'))
    return backups

def restore_backup(backup_path: Path) -> None:
    """
    Restore settings from a backup tar.gz.
    This will overwrite your current files for those settings.
    """
    if not backup_path.exists():
        raise FileNotFoundError(str(backup_path))
    header('Restoring Ρυθμίσεις')
    print(c('This will overwrite your current Termux settings files.', C.WARN))
    bash("termux-toast 'Restoring Termux settings...' >/dev/null 2>&1 || true", check=False)
    with tarfile.open(backup_path, 'r:gz') as tf:
        members = tf.getmembers()
        for m in members:
            if not m.name.startswith('HOME/'):
                continue
            rel = m.name.replace('HOME/', '')
            dest = HOME / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            tf.extract(m, path=str(APP_DIR))
            extracted = APP_DIR / m.name
            shutil.copy2(extracted, dest)
    print(c('✓ Ρυθμίσεις Επαναφοράd.', C.OK))
    print(c('Tip: Restart Termux to ensure everything reloads.', C.INFO))

def write_tools_files(core_path: Path) -> None:
    """
    Write mobile-dev-setup-tools helper scripts into ~/.mobile-dev-setup-tools.
    We set 'core' path inside config so the update script knows where it lives.
    """
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    cfg = EMBEDDED_CONFIG.strip() + '\n\n' + f"tools='{core_path}'\n"
    write_text(TOOLS_CONFIG_PATH, cfg)
    write_text(TOOLS_BOOTSTRAP_PATH, EMBEDDED_BOOTSTRAP_SH.strip() + '\n', mode=493)
    write_text(TOOLS_UPDATE_PATH, EMBEDDED_UPDATE_SH.strip() + '\n', mode=493)

def pkg_update_upgrade() -> None:
    header('Updating Termux packages')
    bash('yes | pkg update')
    bash('yes | pkg upgrade')

def pkg_install(pkgs: Iterable[str]) -> None:
    joined = ' '.join(pkgs)
    bash(f'yes | pkg install {joined}')

def npm_install(mods: Iterable[str]) -> None:
    joined = ' '.join(mods)
    header('Εγκατάστασηing global npm tools')
    bash(f'npm Εγκατάσταση -g {joined}')

def patch_localtunnel_android_openurl() -> None:
    header('Patching localtunnel Android openurl handler')
    cmd = '\nOPENURL_JS="${PREFIX}/lib/node_modules/localtunnel/node_modules/openurl/openurl.js"\nif [ -f "$OPENURL_JS" ]; then\n  sed -i \'/case \'\\\'\'win32\'\\\'\'/,/break;/ a\\    case \'\\\'\'android\'\\\'\':\\n        command = \'\\\'\'termux-open-url\'\\\'\';\\n        break;\' "$OPENURL_JS" || true\n  sed -i \'s/break;/break;/\' "$OPENURL_JS" || true\n  echo "✓ Patched: $OPENURL_JS"\nelse\n  echo "Skipped (not found): $OPENURL_JS"\nfi\n'
    bash(cmd, check=False)

def install_oh_my_zsh() -> None:
    header('Εγκατάστασηing Oh My Zsh')
    cmd = '\ncd "$HOME"\ncurl -fsSL https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh -o install.sh\n# Prevent the installer from switching shells immediately (we want to finish setup first)\nsed -i \'/exec zsh -l/s/^/#/\' install.sh || true\nsh install.sh\nrm -f install.sh\n'
    bash(cmd)

def clone_zsh_plugins() -> None:
    header('Εγκατάστασηing Zsh plugins')
    plugins_dir = HOME / '.zsh-plugins'
    plugins_dir.mkdir(parents=True, exist_ok=True)
    for name, repo, zshrc_line in ZSH_PLUGIN_REPOS:
        dest = plugins_dir / name
        if dest.exists():
            print(c(f'✓ {name} already present', C.OK))
            continue
        bash(f'git clone --depth=1 {repo} {dest}')

def upsert_zshrc_section(core_path: Path) -> None:
    header('Configuring ~/.zshrc')
    zshrc = HOME / '.zshrc'
    existing = read_text(zshrc)
    managed_block = '\n'.join([MARK_BEGIN, '# Added by Mobile Developer Setup.py (safe to remove by restore/uninstall).', *[line for _, _, line in ZSH_PLUGIN_REPOS], '', "bindkey '^[[A' history-substring-search-up", "bindkey '^[[B' history-substring-search-down", '', "zstyle ':completion:*' μενού-select Ναι", "zstyle ':fzf-tab:*' switch-word Ναι", '', f"tools='{core_path}'", 'alias ls="lsd"', 'alias cat="bat --theme=Dracula --style=plain --paging=never"', MARK_END, ''])
    if MARK_BEGIN in existing and MARK_END in existing:
        import re
        new = re.sub(re.escape(MARK_BEGIN) + '.*?' + re.escape(MARK_END), managed_block.strip(), existing, flags=re.S)
    else:
        new = existing.rstrip() + '\n\n' + managed_block
    write_text(zshrc, new)

def configure_termux_ui(font_url: str=DEFAULT_FONT_URL) -> None:
    header('Applying Termux UI settings (extra keys, cursor, font)')
    TERMUX_DIR.mkdir(parents=True, exist_ok=True)
    termux_props = TERMUX_DIR / 'termux.properties'
    props = read_text(termux_props)
    cursor_blink = 'terminal-cursor-blink-rate=500'
    extra_keys = "extra-keys = [['ESC','</>','-','HOME',{key: 'UP', display: '▲'},'END','PGUP'], ['TAB','CTRL','ALT',{key: 'LEFT', display: '◀'},{key: 'DOWN', display: '▼'},{key: 'RIGHT', display: '▶'},'PGDN']]"
    lines = [ln for ln in props.splitlines() if ln.strip() != '']

    def replace_or_add(prefix: str, value: str):
        nonlocal lines
        for i, ln in enumerate(lines):
            if ln.strip().startswith(prefix):
                lines[i] = value
                return
        lines.append(value)
    replace_or_add('terminal-cursor-blink-rate', cursor_blink)
    replace_or_add('extra-keys', extra_keys)
    write_text(termux_props, '\n'.join(lines) + '\n')
    colors = TERMUX_DIR / 'colors.properties'
    col = read_text(colors).splitlines()
    col = [ln for ln in col if not ln.strip().startswith('cursor=')]
    col.append('cursor=#00FF00')
    write_text(colors, '\n'.join(col) + '\n')
    cmd = f'''\ncd "$HOME"\nmkdir -p "{TERMUX_DIR}"\ncurl -L --fail "{font_url}" -o "{TERMUX_DIR / 'font.ttf'}"\n'''
    bash(cmd)
    bash('termux-reload-settings >/dev/null 2>&1 || true', check=False)
    bash("termux-toast 'Termux UI updated (keys/font/colors)' >/dev/null 2>&1 || true", check=False)

def install_nvchad_termux() -> None:
    header('Εγκατάστασηing NvChad (Neovim setup)')
    cmd = '\nrm -rf ~/.config/nvim ~/.local/state/nvim ~/.local/share/nvim\nrm -rf ~/.mobile-dev-setup-tools/nvchad-termux\ngit clone --depth=1 ' + NVCHAD_TERMUX_REPO + ' ~/.mobile-dev-setup-tools/nvchad-termux\ncd ~/.mobile-dev-setup-tools/nvchad-termux\nbash nvchad.sh\n'
    bash(cmd)

def install_setup() -> None:
    if not is_termux():
        print(c('This script must be run inside Termux.', C.ERR))
        sys.exit(1)
    ensure_dirs()
    header('Mobile Developer Setup – Εγκατάσταση')
    print(c('Creating a safety backup of your Termux settings first…', C.INFO))
    backup_path = make_backup()
    state = load_state()
    state['install_backup'] = str(backup_path)
    save_state(state)
    core_path = Path.cwd()
    write_tools_files(core_path)
    pkg_update_upgrade()
    header('Installing Termux packages')
    pkg_install(TERMUX_PACKAGES)
    header('Installing Termux user packages (mongodb)')
    pkg_install(TERMUX_USER_PACKAGES)
    npm_install(NPM_GLOBAL_MODULES)
    patch_localtunnel_android_openurl()
    install_oh_my_zsh()
    clone_zsh_plugins()
    upsert_zshrc_section(core_path)
    configure_termux_ui()
    install_nvchad_termux()
    header('Έτοιμο')
    print(c('✓ Εγκατάσταση finished.', C.OK))
    print(c('Restart Termux now to apply everything.', C.INFO))

def run_update() -> None:
    if not is_termux():
        print(c('This script must be run inside Termux.', C.ERR))
        return
    header('Update')
    if TOOLS_BOOTSTRAP_PATH.exists():
        bash(f'bash {TOOLS_BOOTSTRAP_PATH}', check=False)
    else:
        print(c('Tools bootstrap script Όχιt βρέθηκε. Εκτέλεση Εγκατάσταση first.', C.WARN))
    print(c('✓ Update completed. Restart Termux if anything changed.', C.OK))

def uninstall_files_only() -> None:
    """
    Remove files/directories created by this setup (but do NOT uninstall packages).
    Restoring a backup is the safest way to undo all customizations.
    """
    header('Removing setup files (does Όχιt αφαίρεση packages)')
    paths = [TOOLS_DIR, HOME / '.zsh-plugins', APP_DIR / 'HOME']
    for p in paths:
        if p.exists():
            try:
                shutil.rmtree(p)
                print(c(f'✓ Αφαιρέθηκε {p}', C.OK))
            except Exception as e:
                print(c(f'! Could Όχιt αφαίρεση {p}: {e}', C.WARN))
    zshrc = HOME / '.zshrc'
    if zshrc.exists():
        import re
        txt = read_text(zshrc)
        if MARK_BEGIN in txt and MARK_END in txt:
            new = re.sub(re.escape(MARK_BEGIN) + '.*?' + re.escape(MARK_END) + '\\n?', '', txt, flags=re.S).rstrip() + '\n'
            write_text(zshrc, new)
            print(c('✓ Removed managed section from ~/.zshrc', C.OK))
    print(c('Files αφαιρέθηκε. To fully undo Ρυθμίσεις, Επαναφορά a Πίσωup.', C.INFO))

def choose_backup_interactive() -> Optional[Path]:
    backups = list_backups()
    if not backups:
        print(c('No backups found in ~/.mobile-dev-setup-tools/backups', C.WARN))
        return None
    print(c('\nAvailable Πίσωups:', C.INFO))
    for i, b in enumerate(backups, 1):
        print(f'  {i}) {b.name}')
    while True:
        choice = input(c('Pick a Πίσωup number (or 0 to ακύρωση): ', C.INFO)).strip()
        if choice == '0':
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(backups):
            return backups[int(choice) - 1]
        print(c('Μη έγκυρη επιλογή.', C.WARN))

def restore_and_remove() -> None:
    if not is_termux():
        print(c('This script must be run inside Termux.', C.ERR))
        return
    header('Επαναφορά Ρυθμίσεις + αφαίρεση setup files')
    b = choose_backup_interactive()
    if not b:
        return
    restore_backup(b)
    uninstall_files_only()
    header('Έτοιμο')
    print(c('✓ Επαναφοράd Ρυθμίσεις and αφαιρέθηκε setup files.', C.OK))
    print(c('Restart Termux now.', C.INFO))

def backup_only() -> None:
    if not is_termux():
        print(c('This script must be run inside Termux.', C.ERR))
        return
    header('Backup Termux settings')
    make_backup()

def show_info() -> None:
    header('Info')
    state = load_state()
    print('App dir:', APP_DIR)
    print('Πίσωups:', BACKUPS_DIR)
    if state.get('install_backup'):
        print('Εγκατάσταση Πίσωup:', state['install_backup'])
    if state.get('last_backup'):
        print('Last Πίσωup:', state['last_backup'])
    print('\nThis tool changes only settings + config files and creates ~/.mobile-dev-setup-tools and ~/.zsh-plugins.')

def menu() -> None:
    ensure_dirs()
    while True:
        header('Mobile Developer Setup')
        print('1) Install / Setup (Mobile dev environment)')
        print('2) Update (extras / fixes)')
        print('3) Backup Termux settings')
        print('4) Επαναφορά Ρυθμίσεις + Αφαίρεση setup files (undo)')
        print('5) Αφαίρεση setup files only (keep current Ρυθμίσεις)')
        print('6) Πληροφορίες')
        print('0) Έξοδος')
        choice = input(c('\nChoose a number: ', C.INFO)).strip()
        try:
            if choice == '1':
                install_setup()
            elif choice == '2':
                run_update()
            elif choice == '3':
                backup_only()
            elif choice == '4':
                restore_and_remove()
            elif choice == '5':
                uninstall_files_only()
            elif choice == '6':
                show_info()
            elif choice == '0':
                print(c('Bye!', C.OK))
                return
            else:
                print(c('Μη έγκυρη επιλογή. Use numbers from the μενού.', C.WARN))
        except KeyboardInterrupt:
            print('\n' + c('Ακυρώθηκε.', C.WARN))
        except Exception as e:
            print(c(f'\nΣφάλμα: {e}', C.ERR))
            print(c('If something απέτυχε mid-Εγκατάσταση, you can Επαναφορά your Πίσωup from επιλογή 4.', C.INFO))
        input(c('\nΠάτα Enter to return to the μενού…', C.DIM))

def main() -> None:
    menu()
if __name__ == '__main__':
    main()
