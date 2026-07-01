import ast
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MIRROR_TEST_URLS = [
    "https://packages.termux.dev/apt/termux-main/dists/stable/Release",
    "https://grimler.se/termux-packages-24/dists/stable/Release",
    "https://termux.mentality.rip/termux-main/dists/stable/Release",
]

SCRIPT_EXTENSIONS = {
    ".py": "python",
    ".pyw": "python",
    ".sh": "shell",
    ".bash": "bash",
    ".zsh": "zsh",
    ".fish": "fish",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".rb": "ruby",
    ".pl": "perl",
    ".pm": "perl",
    ".php": "php",
    ".lua": "lua",
    ".go": "go",
    ".rs": "rust",
    ".c": "c",
    ".h": "c-header",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp-header",
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".r": "r",
    ".R": "r",
    ".ps1": "powershell",
    ".dart": "dart",
    ".scala": "scala",
    ".groovy": "groovy",
    ".ex": "elixir",
    ".exs": "elixir",
    ".erl": "erlang",
    ".tcl": "tcl",
    ".hs": "haskell",
    ".cs": "csharp",
}

SHEBANG_LANGUAGES = {
    "python": "python",
    "python3": "python",
    "bash": "bash",
    "sh": "shell",
    "zsh": "zsh",
    "fish": "fish",
    "node": "javascript",
    "nodejs": "javascript",
    "ruby": "ruby",
    "perl": "perl",
    "php": "php",
    "lua": "lua",
    "luajit": "lua",
    "go": "go",
    "rscript": "r",
    "pwsh": "powershell",
    "powershell": "powershell",
    "dart": "dart",
    "scala": "scala",
    "groovy": "groovy",
    "elixir": "elixir",
    "escript": "erlang",
    "tclsh": "tcl",
    "runhaskell": "haskell",
}


LANGUAGE_TOOLS = {
    "python": [("python", "python")],
    "shell": [("sh", "dash")],
    "bash": [("bash", "bash")],
    "zsh": [("zsh", "zsh")],
    "fish": [("fish", "fish")],
    "javascript": [("node", "nodejs")],
    "typescript": [("node", "nodejs"), ("npx", "nodejs")],
    "ruby": [("ruby", "ruby")],
    "perl": [("perl", "perl")],
    "php": [("php", "php")],
    "lua": [("lua", "lua")],
    "go": [("go", "golang")],
    "rust": [("cargo", "rust"), ("rustc", "rust")],
    "c": [("clang", "clang")],
    "c-header": [("clang", "clang")],
    "cpp": [("clang++", "clang")],
    "cpp-header": [("clang++", "clang")],
    "java": [("javac", "openjdk-21")],
    "kotlin": [("java", "openjdk-21"), ("kotlinc", "kotlin")],
    "r": [("Rscript", "r-base")],
    "powershell": [("pwsh", "powershell")],
    "dart": [("dart", "dart")],
    "scala": [("scala", "scala")],
    "groovy": [("groovy", "groovy")],
    "elixir": [("elixir", "elixir")],
    "erlang": [("erl", "erlang")],
    "tcl": [("tclsh", "tcl")],
    "haskell": [("runhaskell", "ghc")],
    "csharp": [("mcs", "mono")],
}

COMMAND_PACKAGE_MAP = {
    "apt": "apt",
    "apt-get": "apt",
    "awk": "gawk",
    "bash": "bash",
    "bc": "bc",
    "bzip2": "bzip2",
    "cargo": "rust",
    "clang": "clang",
    "clang++": "clang",
    "cmake": "cmake",
    "composer": "composer",
    "convert": "imagemagick",
    "curl": "curl",
    "dig": "dnsutils",
    "dart": "dart",
    "dpkg": "dpkg",
    "elixir": "elixir",
    "erl": "erlang",
    "ffmpeg": "ffmpeg",
    "fish": "fish",
    "fzf": "fzf",
    "g++": "clang",
    "gcc": "clang",
    "git": "git",
    "groovy": "groovy",
    "go": "golang",
    "gpg": "gnupg",
    "gzip": "gzip",
    "java": "openjdk-21",
    "javac": "openjdk-21",
    "jq": "jq",
    "lua": "lua",
    "luajit": "luajit",
    "make": "make",
    "meson": "meson",
    "mcs": "mono",
    "mpv": "mpv",
    "nano": "nano",
    "nc": "netcat-openbsd",
    "ninja": "ninja",
    "node": "nodejs",
    "nodejs": "nodejs",
    "npm": "nodejs",
    "npx": "nodejs",
    "openssl": "openssl",
    "perl": "perl",
    "php": "php",
    "pwsh": "powershell",
    "pip": "python",
    "pip3": "python",
    "pkg-config": "pkg-config",
    "proot": "proot",
    "python": "python",
    "python3": "python",
    "Rscript": "r-base",
    "ruby": "ruby",
    "runhaskell": "ghc",
    "rustc": "rust",
    "scala": "scala",
    "sed": "sed",
    "shellcheck": "shellcheck",
    "ssh": "openssh",
    "sshd": "openssh",
    "tar": "tar",
    "tclsh": "tcl",
    "termux-api-start": "termux-api",
    "termux-battery-status": "termux-api",
    "termux-camera-photo": "termux-api",
    "termux-dialog": "termux-api",
    "termux-location": "termux-api",
    "termux-media-player": "termux-api",
    "termux-notification": "termux-api",
    "termux-storage-get": "termux-api",
    "termux-toast": "termux-api",
    "termux-volume": "termux-api",
    "unzip": "unzip",
    "wget": "wget",
    "xz": "xz-utils",
    "zip": "zip",
    "zsh": "zsh",
}

PYTHON_IMPORT_PACKAGES = {
    "Crypto": ["pycryptodome"],
    "OpenSSL": ["pyOpenSSL"],
    "PIL": ["Pillow"],
    "bs4": ["beautifulsoup4"],
    "cv2": ["opencv-python", "opencv-python-headless"],
    "discord": ["discord.py"],
    "dns": ["dnspython"],
    "dateutil": ["python-dateutil"],
    "dotenv": ["python-dotenv"],
    "fitz": ["PyMuPDF"],
    "googleapiclient": ["google-api-python-client"],
    "jwt": ["PyJWT"],
    "magic": ["python-magic"],
    "mysql": ["mysql-connector-python"],
    "pkg_resources": ["setuptools"],
    "psycopg2": ["psycopg2-binary", "psycopg2"],
    "pyaudio": ["PyAudio"],
    "pygame": ["pygame", "pygame-ce"],
    "serial": ["pyserial"],
    "sklearn": ["scikit-learn"],
    "socks": ["PySocks"],
    "telegram": ["python-telegram-bot"],
    "websocket": ["websocket-client"],
    "yaml": ["PyYAML"],
}

# Drop-in compatibility packages for modules removed from newer Python versions.
PYTHON_COMPAT_PACKAGES = {
    "aifc": ["standard-aifc"],
    "audioop": ["audioop-lts"],
    "cgi": ["legacy-cgi"],
    "chunk": ["standard-chunk"],
    "cgitb": ["legacy-cgi"],
    "distutils": ["setuptools"],
    "imghdr": ["standard-imghdr"],
    "mailcap": ["standard-mailcap"],
    "pipes": ["standard-pipes"],
    "sndhdr": ["standard-sndhdr"],
    "sunau": ["standard-sunau"],
    "telnetlib": ["standard-telnetlib", "telnetlib-313-and-up"],
    "uu": ["standard-uu"],
    "xdrlib": ["standard-xdrlib"],
}

PYTHON_NATIVE_BUILD_PACKAGES = [
    "clang",
    "make",
    "cmake",
    "pkg-config",
    "rust",
    "openssl",
    "libffi",
]

PYTHON_SYSTEM_DEPENDENCIES = {
    "Pillow": ["libjpeg-turbo", "libpng", "freetype"],
    "PyAudio": ["portaudio"],
    "cffi": ["libffi"],
    "cryptography": ["openssl", "libffi", "rust"],
    "lxml": ["libxml2", "libxslt"],
    "mysqlclient": ["mariadb"],
    "psycopg2": ["postgresql"],
    "psycopg2-binary": ["postgresql"],
    "pyaudio": ["portaudio"],
}

C_HEADER_PACKAGE_MAP = {
    "curl/curl.h": "libcurl",
    "ffi.h": "libffi",
    "jpeglib.h": "libjpeg-turbo",
    "ncurses.h": "ncurses",
    "curses.h": "ncurses",
    "openssl/ssl.h": "openssl",
    "openssl/crypto.h": "openssl",
    "png.h": "libpng",
    "sqlite3.h": "libsqlite",
    "zlib.h": "zlib",
}

PYTHON_MODULE_CACHE = {}

IGNORED_DIRECTORIES = {
    ".git",
    ".gradle",
    ".hg",
    ".m2",
    ".npm",
    ".cache",
    ".svn",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    "target",
    "build",
    "dist",
    "vendor",
}


NODE_BUILTINS = {
    "assert", "assert/strict", "async_hooks", "buffer", "child_process",
    "cluster", "console", "constants", "crypto", "dgram", "diagnostics_channel",
    "dns", "dns/promises", "domain", "events", "fs", "fs/promises", "http",
    "http2", "https", "module", "net", "os", "path", "path/posix",
    "path/win32", "perf_hooks", "process", "punycode", "querystring",
    "readline", "readline/promises", "repl", "stream", "stream/consumers",
    "stream/promises", "stream/web", "string_decoder", "sys", "timers",
    "timers/promises", "tls", "trace_events", "tty", "url", "util",
    "util/types", "v8", "vm", "wasi", "worker_threads", "zlib",
}

SHELL_BUILTINS_AND_KEYWORDS = {
    "alias",
    "bg",
    "break",
    "builtin",
    "case",
    "cd",
    "command",
    "continue",
    "declare",
    "do",
    "done",
    "echo",
    "elif",
    "else",
    "enable",
    "esac",
    "eval",
    "exec",
    "exit",
    "export",
    "false",
    "fc",
    "fg",
    "fi",
    "for",
    "function",
    "getopts",
    "hash",
    "help",
    "history",
    "if",
    "in",
    "jobs",
    "kill",
    "let",
    "local",
    "logout",
    "mapfile",
    "popd",
    "printf",
    "pushd",
    "pwd",
    "read",
    "readonly",
    "return",
    "select",
    "set",
    "shift",
    "shopt",
    "source",
    "suspend",
    "test",
    "then",
    "time",
    "times",
    "trap",
    "true",
    "type",
    "typeset",
    "ulimit",
    "umask",
    "unalias",
    "unset",
    "until",
    "wait",
    "while",
    "{",
    "}",
    "[[",
    "]]",
    "[",
}


def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def run(cmd, check=False, capture=False, cwd=None, env=None, quiet=False):
    cmd = [str(part) for part in cmd]
    if not quiet:
        print(f"\n$ {' '.join(shlex.quote(part) for part in cmd)}")
    try:
        if capture:
            p = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(cwd) if cwd else None,
                env=env,
            )
            return p.returncode, p.stdout or "", p.stderr or ""
        p = subprocess.run(
            cmd,
            check=check,
            cwd=str(cwd) if cwd else None,
            env=env,
        )
        return p.returncode, "", ""
    except Exception as exc:
        return 1, "", str(exc)


def header(title):
    print("\n" + "=" * 64)
    print(title)
    print("=" * 64)


def ensure_pkg():
    if not have("pkg"):
        print("[!] 'pkg' not found. Run inside Termux.")
        return False
    return True


def pkg_install(pkgs):
    if not ensure_pkg():
        return False
    if isinstance(pkgs, str):
        pkgs = [pkgs]
    unique = list(dict.fromkeys(str(pkg) for pkg in pkgs if pkg))
    if not unique:
        return True
    code, _, _ = run(["pkg", "install", "-y", *unique], check=False)
    return code == 0


def ensure_tool(cmd: str, pkg_name: str):
    if have(cmd):
        return True
    print(f"[*] Missing: {cmd} -> installing {pkg_name}")
    pkg_install(pkg_name)
    return have(cmd)


def ensure_python_pip():
    header("Ensure Python + Pip")
    pkg_install("python")
    python_cmd = shutil.which("python") or sys.executable
    run([python_cmd, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=False)


def ensure_pip_pkg(py_pkg: str):
    try:
        __import__(py_pkg)
        print(f"[*] Python dep OK: {py_pkg}")
        return
    except Exception:
        pass
    print(f"[*] Installing python dep: {py_pkg}")
    python_cmd = shutil.which("python") or sys.executable
    run([python_cmd, "-m", "pip", "install", "--upgrade", py_pkg], check=False)


def info():
    header("System Info")
    print(f"Python : {sys.version.split()[0]}")
    print(f"HOME   : {os.environ.get('HOME')}")
    print(f"PREFIX : {os.environ.get('PREFIX')}")
    print(f"SHELL  : {os.environ.get('SHELL')}")
    print(f"PATH   : {os.environ.get('PATH')}")
    print("Logs (if using launcher): ~/DedSec/logs")

    ensure_tool("termux-info", "termux-tools")
    if have("termux-info"):
        run(["termux-info"], check=False)


def doctor():
    header("Doctor Checks")
    ensure_tool("curl", "curl")
    ensure_tool("openssl", "openssl")
    ensure_tool("termux-change-repo", "termux-tools")

    info()

    print("\nTools:")
    for tool in ["pkg", "apt", "dpkg", "curl", "python", "pip", "git", "openssl", "wget", "termux-change-repo"]:
        print(f" - {tool:18}: {'OK' if have(tool) else 'MISSING'}")

    print("\nFree space (Termux root):")
    try:
        usage = shutil.disk_usage("/data/data/com.termux/files")
        gb = 1024 ** 3
        print(f" - Total: {usage.total / gb:.2f} GB")
        print(f" - Free : {usage.free / gb:.2f} GB")
    except Exception as exc:
        print(f" - Could not read disk usage: {exc}")

    header("Network quick test")
    if have("ping"):
        run(["ping", "-c", "1", "1.1.1.1"], check=False)
        run(["ping", "-c", "1", "google.com"], check=False)
    if have("curl"):
        run(["curl", "-I", "-L", "--max-time", "10", "https://example.com"], check=False)


def mirror_test():
    header("Mirror Quick Test")
    ensure_tool("curl", "curl")
    for url in MIRROR_TEST_URLS:
        run(["curl", "-I", "--max-time", "10", "-L", url], check=False)


def setup_storage():
    header("Storage Setup")
    ensure_tool("termux-setup-storage", "termux-tools")
    shared = Path.home() / "storage" / "shared"
    if shared.exists() and os.access(shared, os.R_OK):
        print("[*] Storage already accessible.")
        return
    run(["termux-setup-storage"], check=False)


def update_upgrade():
    header("Update/Upgrade")
    run(["pkg", "update", "-y"], check=False)
    run(["pkg", "upgrade", "-y"], check=False)


def fix_broken():
    header("Fix Broken Packages")
    run(["apt", "--fix-broken", "install", "-y"], check=False)
    run(["dpkg", "--configure", "-a"], check=False)


def reset_lists_and_clean():
    header("Reset Lists + Clean Cache")
    run(["apt", "clean"], check=False)
    lists = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr")) / "var/lib/apt/lists"
    if lists.exists():
        for item in lists.glob("*"):
            try:
                if item.is_file() or item.is_symlink():
                    item.unlink()
                elif item.is_dir() and item.name != "partial":
                    shutil.rmtree(item)
            except Exception:
                pass
        print(f"[*] Removed apt lists in {lists}")
    run(["pkg", "update", "-y"], check=False)


def fix_releaseinfo_change():
    header("Fix: Release info changed")
    run(["apt-get", "update", "--allow-releaseinfo-change"], check=False)


def fix_hash_sum_mismatch():
    header("Fix: Hash Sum mismatch")
    reset_lists_and_clean()
    run(["pkg", "update", "-y"], check=False)


def fix_tls_cert_issues():
    header("Fix: TLS/Certificate issues")
    pkg_install(["ca-certificates", "openssl"])
    run(["pkg", "update", "-y"], check=False)


def clean_deb_cache():
    header("Clean .deb cache")
    prefix = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr"))
    archives = prefix / "var/cache/apt/archives"
    removed = 0
    if archives.exists():
        for item in archives.glob("*.deb"):
            try:
                item.unlink()
                removed += 1
            except Exception:
                pass
    print(f"[*] Removed {removed} .deb files.")


def clean_pip_cache():
    header("Clean pip cache")
    ensure_python_pip()
    python_cmd = shutil.which("python") or sys.executable
    run([python_cmd, "-m", "pip", "cache", "purge"], check=False)


def install_basics():
    header("Install Basics")
    pkg_install(["git", "curl", "wget", "openssl", "ca-certificates", "nano", "unzip", "tar", "termux-tools"])


def pip_repair():
    header("Pip Repair")
    ensure_python_pip()
    python_cmd = shutil.which("python") or sys.executable
    run([python_cmd, "-m", "pip", "install", "--upgrade", "--force-reinstall", "pip", "setuptools", "wheel"], check=False)
    print("If pip fails to download: try switching network or disabling Private DNS temporarily.")


def python_deps_check():
    header("Python deps check")
    ensure_python_pip()
    ensure_pip_pkg("requests")
    ensure_pip_pkg("colorama")


def repo_helper():
    header("Repo Helper")
    ensure_tool("termux-change-repo", "termux-tools")
    if have("termux-change-repo"):
        run(["termux-change-repo"], check=False)


def fix_home_permissions():
    header("Fix $HOME Permissions (user files only)")
    home = Path(os.environ.get("HOME", str(Path.home())))
    if not home.exists():
        print("[!] HOME not found.")
        return
    count = 0
    for item in home.rglob("*"):
        try:
            if item.is_symlink():
                continue
            if (home / "storage") in item.parents or item == (home / "storage"):
                continue
            if item.is_dir():
                item.chmod(0o700)
            elif item.is_file():
                # Preserve executable files rather than removing their execute bit.
                current_mode = item.stat().st_mode
                item.chmod(0o700 if current_mode & 0o111 else 0o600)
            count += 1
        except Exception:
            continue
    print(f"[*] Done. Updated {count} items.")


def fix_shell_path():
    header("Shell/PATH Fixer (safe)")
    home = Path(os.environ.get("HOME", str(Path.home())))
    shells = [home / ".bashrc", home / ".zshrc", home / ".profile"]
    line = 'export PATH="$PREFIX/bin:$PATH"'
    for shell_file in shells:
        try:
            if not shell_file.exists():
                continue
            text = shell_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            if any(line in row for row in text):
                continue
            text += ["", "# DedSec Repair Wizard: ensure Termux PATH", line]
            shell_file.write_text("\n".join(text) + "\n", encoding="utf-8")
            print(f"[*] Updated: {shell_file.name}")
        except Exception as exc:
            print(f"[!] Could not update {shell_file}: {exc}")
    print("[*] Restart Termux to apply PATH changes.")


class ScriptKeeperReport:
    def __init__(self):
        self.scanned_files = 0
        self.scripts = 0
        self.languages = {}
        self.installed = []
        self.already_ok = []
        self.fixed = []
        self.warnings = []
        self.failures = []
        self.syntax_failures = []

    def language(self, name):
        self.languages[name] = self.languages.get(name, 0) + 1

    def line(self, category, message):
        getattr(self, category).append(message)
        marker = {
            "installed": "[+]",
            "already_ok": "[*]",
            "fixed": "[+]",
            "warnings": "[!]",
            "failures": "[-]",
            "syntax_failures": "[-]",
        }.get(category, "[*]")
        print(f"{marker} {message}")

    def save(self, root):
        log_dir = Path.home() / "DedSec" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        path = log_dir / f"script_keeper_{stamp}.log"
        lines = [
            "DedSec Script Keeper report",
            f"Scan root: {root}",
            f"Scanned files: {self.scanned_files}",
            f"Scripts detected: {self.scripts}",
            f"Languages: {json.dumps(self.languages, sort_keys=True)}",
            "",
        ]
        for title, values in [
            ("INSTALLED", self.installed),
            ("ALREADY OK", self.already_ok),
            ("FIXED", self.fixed),
            ("WARNINGS", self.warnings),
            ("FAILURES", self.failures),
            ("SYNTAX/CHECK FAILURES", self.syntax_failures),
        ]:
            lines.append(f"=== {title} ===")
            lines.extend(values or ["None"])
            lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")
        return path


def read_text_safe(path, max_bytes=2 * 1024 * 1024):
    try:
        if path.stat().st_size > max_bytes:
            return None
        raw = path.read_bytes()
        if b"\x00" in raw[:8192]:
            return None
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return None


def shebang_command(text):
    if not text or not text.startswith("#!"):
        return None
    first = text.splitlines()[0][2:].strip()
    try:
        parts = shlex.split(first)
    except ValueError:
        parts = first.split()
    if not parts:
        return None
    command = Path(parts[0]).name
    if command == "env":
        parts = [part for part in parts[1:] if not part.startswith("-") and "=" not in part]
        if not parts:
            return None
        command = Path(parts[0]).name
    return command.lower()


def detect_language(path, text):
    command = shebang_command(text)
    if command:
        for token, language in SHEBANG_LANGUAGES.items():
            if command == token or command.startswith(token):
                return language
    suffix = path.suffix
    if suffix in SCRIPT_EXTENSIONS:
        return SCRIPT_EXTENSIONS[suffix]
    if command:
        return f"generic:{command}"
    return None


def iter_script_files(root, report):
    if root.is_file():
        report.scanned_files += 1
        text = read_text_safe(root)
        language = detect_language(root, text)
        if language:
            yield root, language, text or ""
        return

    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [name for name in dirs if name not in IGNORED_DIRECTORIES]
        current_path = Path(current)
        for name in files:
            path = current_path / name
            report.scanned_files += 1
            text = read_text_safe(path)
            if text is None:
                continue
            language = detect_language(path, text)
            if language:
                yield path, language, text


def ensure_language_tools(language, auto_install, report):
    if language.startswith("generic:"):
        command = language.split(":", 1)[1]
        if have(command):
            return
        package = COMMAND_PACKAGE_MAP.get(command)
        if not package:
            report.line("warnings", f"Unknown shebang interpreter '{command}' is missing; no safe Termux package mapping exists")
            return
        if auto_install and pkg_install(package) and have(command):
            report.line("installed", f"Installed Termux package '{package}' for shebang interpreter '{command}'")
        elif auto_install:
            report.line("failures", f"Could not install '{package}' for shebang interpreter '{command}'")
        else:
            report.line("warnings", f"Missing shebang interpreter '{command}' (package: {package})")
        return
    for command, package in LANGUAGE_TOOLS.get(language, []):
        if have(command):
            continue
        if not auto_install:
            report.line("warnings", f"Missing interpreter/tool '{command}' (Termux package: {package})")
            continue
        print(f"[*] {language}: installing missing tool {command} from package {package}")
        if pkg_install(package) and have(command):
            report.line("installed", f"Installed Termux package '{package}' for {language}")
        else:
            report.line("failures", f"Could not install '{package}' required by {language}")


def python_module_available(module, refresh=False):
    if not refresh and module in PYTHON_MODULE_CACHE:
        return PYTHON_MODULE_CACHE[module]
    python_cmd = shutil.which("python") or sys.executable
    code, _, _ = run(
        [
            python_cmd,
            "-c",
            "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec(sys.argv[1]) else 1)",
            module,
        ],
        capture=True,
        quiet=True,
    )
    available = code == 0
    PYTHON_MODULE_CACHE[module] = available
    return available


def parse_python_imports(text):
    modules = set()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return modules
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module.split(".")[0])
    return modules


def python_candidates(module):
    candidates = []
    candidates.extend(PYTHON_COMPAT_PACKAGES.get(module, []))
    candidates.extend(PYTHON_IMPORT_PACKAGES.get(module, []))
    candidates.append(module)
    return list(dict.fromkeys(candidates))


def install_python_module(module, report):
    python_cmd = shutil.which("python") or sys.executable
    candidates = python_candidates(module)
    errors = []
    for package in candidates:
        print(f"[*] Python import '{module}' missing -> trying pip package '{package}'")
        code, out, err = run(
            [python_cmd, "-m", "pip", "install", "--upgrade", package],
            capture=True,
        )
        output = (out + "\n" + err).strip()
        if code == 0 and python_module_available(module, refresh=True):
            report.line("installed", f"Python import '{module}' supplied by '{package}'")
            return True

        errors.append(f"{package}: {output[-500:]}")
        native_markers = (
            "failed building wheel",
            "could not build wheels",
            "error: command 'clang'",
            "cargo",
            "rust compiler",
            "pkg-config",
            "openssl",
            "ffi.h",
        )
        if any(marker in output.lower() for marker in native_markers):
            print("[*] Native build dependency failure detected; installing build tools and retrying.")
            extra_packages = PYTHON_SYSTEM_DEPENDENCIES.get(package, []) + PYTHON_SYSTEM_DEPENDENCIES.get(module, [])
            pkg_install(PYTHON_NATIVE_BUILD_PACKAGES + extra_packages)
            code, out, err = run(
                [python_cmd, "-m", "pip", "install", "--upgrade", "--no-build-isolation", package],
                capture=True,
            )
            output = (out + "\n" + err).strip()
            if code == 0 and python_module_available(module, refresh=True):
                report.line("fixed", f"Python import '{module}' installed as '{package}' after adding build dependencies")
                return True
            errors.append(f"{package} retry: {output[-500:]}")

    report.line(
        "failures",
        f"Python import '{module}' unresolved. Tried: {', '.join(candidates)}. Last error: {errors[-1] if errors else 'unknown'}",
    )
    return False


def python_module_is_local(module, path, scan_root):
    root = scan_root if scan_root.is_dir() else scan_root.parent
    candidates = []
    current = path.parent
    while True:
        candidates.extend([current / f"{module}.py", current / module / "__init__.py"])
        if current == root or current.parent == current:
            break
        try:
            current.relative_to(root)
        except ValueError:
            break
        current = current.parent
    candidates.extend([
        root / f"{module}.py",
        root / module / "__init__.py",
        root / "src" / f"{module}.py",
        root / "src" / module / "__init__.py",
    ])
    return any(candidate.exists() for candidate in candidates)


def check_python_script(path, text, scan_root, auto_install, report):
    python_cmd = shutil.which("python") or sys.executable
    code, _, err = run(
        [
            python_cmd,
            "-c",
            "import sys,tokenize; f=tokenize.open(sys.argv[1]); compile(f.read(), sys.argv[1], 'exec')",
            path,
        ],
        capture=True,
    )
    if code != 0:
        report.line("syntax_failures", f"{path}: Python compile check failed: {err.strip()}")

    stdlib = getattr(sys, "stdlib_module_names", set())
    local_names = {item.stem for item in path.parent.glob("*.py")}
    local_names.update(item.name for item in path.parent.iterdir() if item.is_dir() and (item / "__init__.py").exists())
    for module in sorted(parse_python_imports(text)):
        if module in stdlib or module in local_names or python_module_is_local(module, path, scan_root) or python_module_available(module):
            continue
        if auto_install:
            install_python_module(module, report)
        else:
            report.line("warnings", f"{path}: missing Python import '{module}'")


def find_project_file(start, names, stop):
    current = start if start.is_dir() else start.parent
    stop = stop.resolve()
    while True:
        for name in names:
            candidate = current / name
            if candidate.exists():
                return candidate
        if current.resolve() == stop or current.parent == current:
            return None
        try:
            current.resolve().relative_to(stop)
        except ValueError:
            return None
        current = current.parent


def parse_shell_commands(text):
    commands = set()
    wrappers = {"command", "env", "exec", "nohup", "sudo", "time"}
    control = {"if", "while", "until", "then", "do", "else", "elif"}

    for original in text.splitlines():
        line = re.sub(r"(?<!\\)#.*$", "", original).strip()
        if not line:
            continue
        # Split pipelines, command chains, substitutions, and control-flow boundaries.
        segments = re.split(r"(?:&&|\|\||[;|`(){}]|\bthen\b|\bdo\b|\belse\b)", line)
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue
            try:
                tokens = shlex.split(segment, comments=False, posix=True)
            except ValueError:
                tokens = segment.split()
            if not tokens:
                continue

            while tokens and tokens[0] in control:
                tokens.pop(0)
            while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
                tokens.pop(0)
            while tokens and tokens[0] in wrappers:
                wrapper = tokens.pop(0)
                if wrapper == "env":
                    while tokens and (tokens[0].startswith("-") or "=" in tokens[0]):
                        tokens.pop(0)
                elif wrapper == "command" and tokens and tokens[0] in {"-v", "-V", "-p"}:
                    # `command -v foo` is a feature check, not an invocation of foo.
                    tokens = []
                    break
                elif wrapper in {"sudo", "time"}:
                    while tokens and tokens[0].startswith("-"):
                        tokens.pop(0)
            if not tokens:
                continue
            command = tokens[0]
            if command in SHELL_BUILTINS_AND_KEYWORDS:
                continue
            if command.startswith(("-", "$", "/", ".", "~")) or "=" in command:
                continue
            if "/" in command:
                command = Path(command).name
            if re.match(r"^[A-Za-z0-9_.+:-]+$", command):
                commands.add(command)
    return commands


def check_shell_script(path, language, text, auto_install, report):
    shell_cmd = {
        "bash": "bash",
        "zsh": "zsh",
        "fish": "fish",
        "shell": "sh",
    }.get(language, "sh")
    if have(shell_cmd):
        args = [shell_cmd, "-n", path]
        if shell_cmd == "fish":
            args = [shell_cmd, "-n", path]
        code, _, err = run(args, capture=True)
        if code != 0:
            report.line("syntax_failures", f"{path}: {shell_cmd} syntax check failed: {err.strip()}")

    for command in sorted(parse_shell_commands(text)):
        if have(command):
            continue
        package = COMMAND_PACKAGE_MAP.get(command)
        if not package:
            report.line("warnings", f"{path}: command '{command}' is missing and has no safe Termux package mapping")
            continue
        if auto_install and pkg_install(package) and have(command):
            report.line("installed", f"Installed Termux package '{package}' for command '{command}' used by {path}")
        elif auto_install:
            report.line("failures", f"Could not install '{package}' for command '{command}' used by {path}")
        else:
            report.line("warnings", f"{path}: missing command '{command}' (package: {package})")


def parse_javascript_modules(text):
    modules = set()
    patterns = [
        r"\brequire\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
        r"\bfrom\s+['\"]([^'\"]+)['\"]",
        r"\bimport\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
        r"\bimport\s+['\"]([^'\"]+)['\"]",
    ]
    for pattern in patterns:
        modules.update(re.findall(pattern, text))
    result = set()
    for module in modules:
        if module.startswith((".", "/", "node:")) or module in NODE_BUILTINS:
            continue
        if module.startswith("@"):
            parts = module.split("/")
            result.add("/".join(parts[:2]))
        else:
            result.add(module.split("/")[0])
    return result


def check_javascript_script(path, language, text, root, auto_install, report, processed_manifests):
    if language == "javascript" and have("node"):
        code, _, err = run(["node", "--check", path], capture=True)
        if code != 0:
            report.line("syntax_failures", f"{path}: Node syntax check failed: {err.strip()[-800:]}")

    manifest = find_project_file(path, ["package.json"], root)
    project_dir = manifest.parent if manifest else path.parent
    if manifest and manifest not in processed_manifests:
        processed_manifests.add(manifest)
        if auto_install:
            code, _, err = run(["npm", "install", "--no-audit", "--no-fund"], capture=True, cwd=project_dir)
            if code == 0:
                report.line("installed", f"Installed npm dependencies from {manifest}")
            else:
                report.line("failures", f"npm install failed in {project_dir}: {err.strip()[-600:]}")

    node_modules = project_dir / "node_modules"
    for module in sorted(parse_javascript_modules(text)):
        module_path = node_modules / module
        if module_path.exists():
            continue
        if auto_install:
            save_args = ["--save"] if manifest else ["--no-save", "--no-package-lock"]
            code, _, err = run(["npm", "install", module, *save_args, "--no-audit", "--no-fund"], capture=True, cwd=project_dir)
            if code == 0:
                report.line("installed", f"Installed npm module '{module}' for {path}")
            else:
                report.line("failures", f"npm module '{module}' failed for {path}: {err.strip()[-600:]}")
        else:
            report.line("warnings", f"{path}: npm module may be missing: {module}")

    if language == "typescript" and auto_install:
        local_tsc = project_dir / "node_modules" / ".bin" / "tsc"
        if not local_tsc.exists():
            type_args = ["--save-dev"] if manifest else ["--no-save", "--no-package-lock"]
            code, _, err = run(["npm", "install", "typescript", *type_args, "--no-audit", "--no-fund"], capture=True, cwd=project_dir)
            if code == 0:
                report.line("installed", f"Installed local TypeScript compiler in {project_dir}")
            else:
                report.line("failures", f"Could not install TypeScript in {project_dir}: {err.strip()[-600:]}")
        if local_tsc.exists():
            code, _, err = run([local_tsc, "--noEmit", "--skipLibCheck", path], capture=True, cwd=project_dir)
            if code != 0:
                report.line("syntax_failures", f"{path}: TypeScript check failed: {err.strip()[-800:]}")


def parse_ruby_requires(text):
    return set(re.findall(r"\brequire\s*[\( ]\s*['\"]([^'\"]+)['\"]", text))


def check_ruby_script(path, text, auto_install, report):
    if have("ruby"):
        code, _, err = run(["ruby", "-c", path], capture=True)
        if code != 0:
            report.line("syntax_failures", f"{path}: Ruby syntax check failed: {err.strip()}")
    for library in sorted(parse_ruby_requires(text)):
        code, _, _ = run(["ruby", "-e", f"require {library!r}"], capture=True, quiet=True)
        if code == 0:
            continue
        gem_name = library.split("/")[0]
        if auto_install:
            code, _, err = run(["gem", "install", gem_name, "--no-document"], capture=True)
            if code == 0:
                report.line("installed", f"Installed Ruby gem '{gem_name}' for {path}")
            else:
                report.line("failures", f"Ruby gem '{gem_name}' failed for {path}: {err.strip()[-600:]}")
        else:
            report.line("warnings", f"{path}: missing Ruby library '{library}'")


def parse_perl_modules(text):
    modules = set()
    for module in re.findall(r"^\s*(?:use|require)\s+([A-Za-z_][A-Za-z0-9_:]*)", text, re.MULTILINE):
        if module not in {"strict", "warnings", "feature", "lib", "vars", "utf8", "integer", "bytes"}:
            modules.add(module)
    return modules


def check_perl_script(path, text, auto_install, report):
    if have("perl"):
        code, _, err = run(["perl", "-c", path], capture=True)
        if code != 0:
            report.line("syntax_failures", f"{path}: Perl compile check failed: {err.strip()}")
    for module in sorted(parse_perl_modules(text)):
        code, _, _ = run(["perl", f"-M{module}", "-e", "1"], capture=True, quiet=True)
        if code == 0:
            continue
        if auto_install:
            env = os.environ.copy()
            env["PERL_MM_USE_DEFAULT"] = "1"
            code, _, err = run(["cpan", "-T", module], capture=True, env=env)
            if code == 0:
                report.line("installed", f"Installed Perl module '{module}' for {path}")
            else:
                report.line("failures", f"Perl module '{module}' failed for {path}: {err.strip()[-600:]}")
        else:
            report.line("warnings", f"{path}: missing Perl module '{module}'")


def parse_lua_modules(text):
    return set(re.findall(r"\brequire\s*\(?\s*['\"]([^'\"]+)['\"]\s*\)?", text))


def check_lua_script(path, text, auto_install, report):
    if have("lua"):
        code, _, err = run(["lua", "-e", f"assert(loadfile({str(path)!r}))"], capture=True)
        if code != 0:
            report.line("syntax_failures", f"{path}: Lua syntax check failed: {err.strip()}")
    for module in sorted(parse_lua_modules(text)):
        code, _, _ = run(["lua", "-e", f"require({module!r})"], capture=True, quiet=True)
        if code == 0:
            continue
        if auto_install:
            ensure_tool("luarocks", "luarocks")
            if have("luarocks"):
                code, _, err = run(["luarocks", "install", module], capture=True)
                if code == 0:
                    report.line("installed", f"Installed Lua rock '{module}' for {path}")
                else:
                    report.line("failures", f"Lua rock '{module}' failed for {path}: {err.strip()[-600:]}")
        else:
            report.line("warnings", f"{path}: missing Lua module '{module}'")


def parse_c_headers(text):
    return set(re.findall(r"^\s*#\s*include\s*[<\"]([^>\"]+)[>\"]", text, re.MULTILINE))


def check_c_script(path, language, text, auto_install, report):
    compiler = "clang++" if language in {"cpp", "cpp-header"} else "clang"
    for header_name in parse_c_headers(text):
        package = C_HEADER_PACKAGE_MAP.get(header_name)
        if package and auto_install:
            # Installing an already-installed Termux package is harmless and lets pkg verify it.
            pkg_install(package)
    if path.suffix.lower() in {".h", ".hpp"}:
        return
    code, _, err = run([compiler, "-fsyntax-only", path], capture=True)
    if code != 0:
        report.line("syntax_failures", f"{path}: {compiler} check failed: {err.strip()[-1000:]}")


def parse_r_packages(text):
    packages = set()
    pattern = re.compile(r"\b(?:library|require|requireNamespace)\s*\(\s*(?:package\s*=\s*)?['\"]?([A-Za-z][A-Za-z0-9._]+)")
    packages.update(pattern.findall(text))
    return packages


def check_r_script(path, text, auto_install, report):
    if not have("Rscript"):
        return
    code, _, err = run(["Rscript", "-e", f"parse(file={str(path)!r})"], capture=True)
    if code != 0:
        report.line("syntax_failures", f"{path}: R parse check failed: {err.strip()[-800:]}")
    for package in sorted(parse_r_packages(text)):
        probe = f"quit(status=if (requireNamespace({package!r}, quietly=TRUE)) 0 else 1)"
        code, _, _ = run(["Rscript", "-e", probe], capture=True, quiet=True)
        if code == 0:
            continue
        if auto_install:
            install = f"install.packages({package!r}, repos='https://cloud.r-project.org')"
            code, _, err = run(["Rscript", "-e", install], capture=True)
            if code == 0:
                report.line("installed", f"Installed R package '{package}' for {path}")
            else:
                report.line("failures", f"R package '{package}' failed for {path}: {err.strip()[-600:]}")
        else:
            report.line("warnings", f"{path}: missing R package '{package}'")


def check_project_manifests(root, auto_install, report, processed_manifests, recursive=True):
    manifest_names = {
        "requirements.txt",
        "pyproject.toml",
        "setup.py",
        "Pipfile",
        "package.json",
        "Gemfile",
        "composer.json",
        "go.mod",
        "Cargo.toml",
        "pom.xml",
    }
    walker = os.walk(root, followlinks=False) if recursive else [(str(root), [], [item.name for item in root.iterdir() if item.is_file()])]
    for current, dirs, files in walker:
        dirs[:] = [name for name in dirs if name not in IGNORED_DIRECTORIES]
        current_path = Path(current)
        for name in files:
            requirements_file = bool(re.fullmatch(r"requirements(?:[-_.][^/]*)?\.txt", name, re.IGNORECASE))
            if name not in manifest_names and not requirements_file:
                continue
            if name == "setup.py" and (current_path / "pyproject.toml").exists():
                continue
            manifest = current_path / name
            if manifest in processed_manifests:
                continue
            processed_manifests.add(manifest)
            if not auto_install:
                report.line("warnings", f"Dependency manifest found but automatic installation disabled: {manifest}")
                continue

            if requirements_file:
                ensure_language_tools("python", True, report)
                python_cmd = shutil.which("python") or sys.executable
                code, _, err = run([python_cmd, "-m", "pip", "install", "-r", manifest], capture=True, cwd=current_path)
            elif name in {"pyproject.toml", "setup.py"}:
                ensure_language_tools("python", True, report)
                python_cmd = shutil.which("python") or sys.executable
                code, _, err = run([python_cmd, "-m", "pip", "install", "--upgrade", "."], capture=True, cwd=current_path)
            elif name == "Pipfile":
                ensure_language_tools("python", True, report)
                if not have("pipenv"):
                    python_cmd = shutil.which("python") or sys.executable
                    run([python_cmd, "-m", "pip", "install", "pipenv"], capture=True)
                code, _, err = run(["pipenv", "install"], capture=True, cwd=current_path) if have("pipenv") else (1, "", "pipenv unavailable")
            elif name == "package.json":
                ensure_language_tools("javascript", True, report)
                code, _, err = run(["npm", "install", "--no-audit", "--no-fund"], capture=True, cwd=current_path)
            elif name == "Gemfile":
                ensure_language_tools("ruby", True, report)
                if not have("bundle"):
                    run(["gem", "install", "bundler", "--no-document"], capture=True)
                code, _, err = run(["bundle", "install"], capture=True, cwd=current_path) if have("bundle") else (1, "", "bundler unavailable")
            elif name == "composer.json":
                ensure_language_tools("php", True, report)
                ensure_tool("composer", "composer")
                code, _, err = run(["composer", "install", "--no-interaction"], capture=True, cwd=current_path) if have("composer") else (1, "", "composer unavailable")
            elif name == "go.mod":
                ensure_language_tools("go", True, report)
                code, _, err = run(["go", "mod", "download"], capture=True, cwd=current_path)
            elif name == "Cargo.toml":
                ensure_language_tools("rust", True, report)
                code, _, err = run(["cargo", "fetch", "--manifest-path", manifest], capture=True, cwd=current_path)
            elif name == "pom.xml":
                ensure_language_tools("java", True, report)
                ensure_tool("mvn", "maven")
                code, _, err = run(["mvn", "-q", "dependency:go-offline"], capture=True, cwd=current_path) if have("mvn") else (1, "", "maven unavailable")
            else:
                continue

            if code == 0:
                report.line("installed", f"Processed dependency manifest: {manifest}")
            else:
                report.line("failures", f"Dependency installation failed for {manifest}: {err.strip()[-800:]}")


def script_keeper():
    header("Script Keeper")
    print("Scans scripts without running them, checks syntax/tooling, and installs missing dependencies.")
    print("Supported detection includes Python, shell, JavaScript/TypeScript, Ruby, Perl, PHP, Lua,")
    print("Go, Rust, C/C++, Java, Kotlin, R, PowerShell, Dart, Scala, Groovy, Elixir,")
    print("Erlang, Tcl, Haskell, C#, extensionless shebang scripts, and project manifests.")

    default_root = Path.cwd()
    raw = input(f"Folder or script to check [{default_root}]: ").strip()
    root = Path(os.path.expandvars(os.path.expanduser(raw))) if raw else default_root
    try:
        root = root.resolve()
    except Exception:
        pass
    if not root.exists():
        print(f"[!] Path not found: {root}")
        return

    auto_answer = input("Automatically install missing packages/modules? [Y/n]: ").strip().lower()
    auto_install = auto_answer not in {"n", "no"}

    report = ScriptKeeperReport()
    processed_manifests = set()
    found_script = False
    print("[*] Scanning files and checking recognized scripts...")

    for path, language, text in iter_script_files(root, report):
        found_script = True
        report.scripts += 1
        report.language(language)
        print(f"\n--- {language.upper()}: {path} ---")
        ensure_language_tools(language, auto_install, report)

        if language == "python":
            check_python_script(path, text, root, auto_install, report)
        elif language in {"shell", "bash", "zsh", "fish"}:
            check_shell_script(path, language, text, auto_install, report)
        elif language in {"javascript", "typescript"}:
            check_javascript_script(path, language, text, root if root.is_dir() else root.parent, auto_install, report, processed_manifests)
        elif language == "ruby":
            check_ruby_script(path, text, auto_install, report)
        elif language == "perl":
            check_perl_script(path, text, auto_install, report)
        elif language == "lua":
            check_lua_script(path, text, auto_install, report)
        elif language in {"c", "c-header", "cpp", "cpp-header"}:
            check_c_script(path, language, text, auto_install, report)
        elif language == "php" and have("php"):
            code, _, err = run(["php", "-l", path], capture=True)
            if code != 0:
                report.line("syntax_failures", f"{path}: PHP lint failed: {err.strip()}")
        elif language == "go":
            manifest = find_project_file(path, ["go.mod"], root if root.is_dir() else root.parent)
            if manifest and auto_install and manifest not in processed_manifests:
                processed_manifests.add(manifest)
                code, _, err = run(["go", "mod", "download"], capture=True, cwd=manifest.parent)
                if code == 0:
                    report.line("installed", f"Downloaded Go modules for {manifest.parent}")
                else:
                    report.line("failures", f"Go module download failed for {manifest.parent}: {err.strip()[-600:]}")
        elif language == "rust":
            manifest = find_project_file(path, ["Cargo.toml"], root if root.is_dir() else root.parent)
            if manifest and auto_install and manifest not in processed_manifests:
                processed_manifests.add(manifest)
                code, _, err = run(["cargo", "fetch", "--manifest-path", manifest], capture=True, cwd=manifest.parent)
                if code == 0:
                    report.line("installed", f"Downloaded Rust crates for {manifest.parent}")
                else:
                    report.line("failures", f"Cargo fetch failed for {manifest.parent}: {err.strip()[-600:]}")
        elif language == "java" and have("javac"):
            with tempfile.TemporaryDirectory(prefix="script-keeper-java-") as output_dir:
                code, _, err = run(["javac", "-Xlint", "-d", output_dir, path], capture=True)
            if code != 0:
                report.line("syntax_failures", f"{path}: Java check failed: {err.strip()[-800:]}")
        elif language == "r":
            check_r_script(path, text, auto_install, report)
        elif language.startswith("generic:"):
            report.line("already_ok", f"Recognized extensionless script using shebang interpreter '{language.split(':', 1)[1]}': {path}")

    if not found_script:
        print("[!] No recognized scripts were found. Unknown text files are not executed or guessed.")

    manifest_root = root if root.is_dir() else root.parent
    check_project_manifests(manifest_root, auto_install, report, processed_manifests, recursive=root.is_dir())

    python_manifest_seen = any(
        item.name in {"pyproject.toml", "setup.py", "Pipfile"}
        or item.name.lower().startswith("requirements")
        for item in processed_manifests
    )
    if have("python") and ("python" in report.languages or python_manifest_seen):
        code, out, err = run(["python", "-m", "pip", "check"], capture=True)
        if code == 0:
            report.line("already_ok", "Python package dependency check passed")
        else:
            report.line("failures", f"pip check reported conflicts: {(out + err).strip()[-1000:]}")

    log_path = report.save(root)
    header("Script Keeper Summary")
    print(f"Scanned files : {report.scanned_files}")
    print(f"Scripts found : {report.scripts}")
    print(f"Languages     : {', '.join(f'{k}={v}' for k, v in sorted(report.languages.items())) or 'none'}")
    print(f"Installed     : {len(report.installed)}")
    print(f"Fixed         : {len(report.fixed)}")
    print(f"Warnings      : {len(report.warnings)}")
    print(f"Failures      : {len(report.failures)}")
    print(f"Syntax issues : {len(report.syntax_failures)}")
    print(f"Report saved  : {log_path}")
    print("[*] Scanned scripts are not directly launched. Package managers may run dependency build/install hooks.")


def full_repair_sequence():
    header("Full Repair Sequence (No Root)")
    setup_storage()
    update_upgrade()
    fix_broken()
    reset_lists_and_clean()
    install_basics()
    ensure_python_pip()
    python_deps_check()
    print("[*] Full repair done.")


def menu():
    if not ensure_pkg():
        return
    while True:
        print("\n=== DedSec Termux Repair Wizard (No-Root) ===")
        print("1) Doctor (diagnose)")
        print("2) Mirror quick test")
        print("3) Setup storage permission")
        print("4) Update + Upgrade")
        print("5) Fix broken packages")
        print("6) Reset apt lists + clean cache")
        print("7) Fix: Release info changed")
        print("8) Fix: Hash Sum mismatch")
        print("9) Fix: TLS/Certificate issues")
        print("10) Clean .deb cache")
        print("11) Clean pip cache")
        print("12) Install basics")
        print("13) Ensure Python + pip")
        print("14) Pip repair")
        print("15) Python deps check (requests/colorama)")
        print("16) Repo helper (termux-change-repo)")
        print("17) Fix $HOME permissions")
        print("18) Shell/PATH fixer")
        print("19) Run FULL repair sequence")
        print("20) Script Keeper")
        print("0) Exit")
        choice = input("> ").strip()
        if choice == "1":
            doctor()
        elif choice == "2":
            mirror_test()
        elif choice == "3":
            setup_storage()
        elif choice == "4":
            update_upgrade()
        elif choice == "5":
            fix_broken()
        elif choice == "6":
            reset_lists_and_clean()
        elif choice == "7":
            fix_releaseinfo_change()
        elif choice == "8":
            fix_hash_sum_mismatch()
        elif choice == "9":
            fix_tls_cert_issues()
        elif choice == "10":
            clean_deb_cache()
        elif choice == "11":
            clean_pip_cache()
        elif choice == "12":
            install_basics()
        elif choice == "13":
            ensure_python_pip()
        elif choice == "14":
            pip_repair()
        elif choice == "15":
            python_deps_check()
        elif choice == "16":
            repo_helper()
        elif choice == "17":
            fix_home_permissions()
        elif choice == "18":
            fix_shell_path()
        elif choice == "19":
            full_repair_sequence()
        elif choice == "20":
            script_keeper()
        elif choice == "0":
            break
        else:
            print("[!] Invalid choice.")


if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\n[!] Cancelled.")
