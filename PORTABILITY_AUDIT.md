# Cross-Platform Portability Audit

Targets: Termux (Android), Ubuntu, Kali Linux, Linux Mint.

## Audit scope

A complete static portability scan was run across the project text/source tree, not only the main launcher. The generated audit report itself is excluded from the scan count.

- 209 text/source files scanned
- 420,647 source/text lines scanned
- 177 Python files syntax-compiled
- 14 shell/compatibility files validated with `bash -n`
- English and Greek copies were checked

The line scan searched for Termux absolute paths, Android shared-storage paths, `termux-*` commands, `pkg`, `proot-distro`/Termux:X11 calls, Android shell commands, apt/sudo assumptions, desktop opener commands, and hard-coded home/prefix assumptions.

## Runtime validation completed

- `Scripts/Settings.py --build-id`: PASS
- `Scripts/Settings.py --ded-guy-core-self-test`: PASS
- `Scripts/Settings.py --pipboy-self-test`: PASS
- `Scripts/Settings.py --pipboy-database-self-test`: PASS
- `Scripts/Games/Terminal Arcade.py --selftest`: PASS
- Desktop hardware-information smoke test: PASS
- Desktop compatibility opener/clipboard/notification shim tests: PASS
- `Setup.sh --help`: PASS
- `Setup-Termux.sh --help` through bash: PASS
- Desktop `Run.sh` launcher simulation using a local venv interpreter: PASS

## Portability fixes applied during this audit

1. Missing optional Android commands no longer crash desktop Linux. The shared silent-command helper now catches OS-level command lookup/execution errors and reports the command as unavailable.
2. Hardware/storage information uses `/` on desktop instead of Android `/data`; Android carrier/version fields are marked not applicable on desktop, while Linux DMI information is used when available.
3. `Mobile Developer Setup.py` is now treated like the other Termux-only management utilities on desktop because its package lists, shell configuration and UI changes are explicitly designed for Termux.
4. The desktop `termux-open` shim now handles the `--chooser` form used by the project instead of trying to open the option itself.
5. The desktop `termux-clipboard-set` shim now supports both stdin input and the argument form used by `Settings.py`.
6. A desktop `termux-notification` shim was added so existing reminder/game notification calls can use `notify-send` when available and fail safely on headless systems.
7. Desktop optional dependencies were expanded for existing features: Wayland/X11 clipboard support, desktop notifications, `at`, DNS/ping/traceroute utilities, mDNS/SNMP/NetBIOS helpers, Zsh/Neovim/media helpers, SQLite CLI, jq/ripgrep/rsync.
8. The `pkg` compatibility shim now maps additional Termux package names to Debian-family equivalents and explicitly reports Termux-only repositories/proot tooling as unsupported instead of sending invalid package names to apt.
9. Battery reporting no longer displays `None%` on desktop systems without a battery.

## Platform behavior

### Termux

`Setup.sh` detects Termux and delegates to `Setup-Termux.sh`. Android/Termux-specific functionality remains on the native Termux path. Features depending on Termux:API, Termux:X11, Android storage permissions or companion apps still require those Android components.

### Ubuntu / Kali Linux / Linux Mint

`Setup.sh` uses apt and creates a project-local `.venv`. `Run.sh` adds the compatibility shims to `PATH` and launches all child Python tools with that same environment. Desktop equivalents are used for common operations such as opening URLs/files, clipboard access, notifications, TTS and battery information where the host supports them.

The following utilities are inherently Android/Termux management tools and are reported as not applicable on desktop rather than modifying the wrong system:

- Android App Launcher
- Termux Backup Restore
- Termux Repair Wizard
- Mobile Desktop
- Mobile Developer Setup

The desktop launcher also keeps the existing safety restriction for credential/card capture, deceptive personal-information capture, phishing pages, Trojan behavior and automated sensitive-data publication. Their source files are not made operational by the desktop compatibility layer.

## What cannot be guaranteed by static auditing

A source audit cannot guarantee every hardware-, network- or third-party-service-dependent path on every installation. GUI availability, audio devices, desktop notification services, Tor state, firewall/network permissions, external APIs, package repository contents, and Android companion-app permissions vary by machine. Optional dependencies are therefore installed best-effort and affected features already contain availability/fallback handling where applicable.

For supported desktop use, run the project through `bash Setup.sh` and then `./Run.sh` so child tools inherit the compatibility PATH and project virtual environment.

## Platform-path and Settings follow-up pass — 2026-09-18

A second portability pass focused on user-visible save paths and Settings/menu behavior.

- All 88 documented `Save Location` entries now have a matching four-platform `Platform Save Paths` block.
- Settings/Ded-Guy appends Termux, Ubuntu, Kali Linux and Linux Mint save paths to catalog-derived script descriptions.
- Desktop Downloads resolution uses XDG when available and falls back to `~/Downloads`.
- Kali/Zsh and Bash startup files are selected from the active shell; an explicit Bash session no longer gets redirected to an existing `.zshrc`.
- Desktop auto-start/aliases preserve the project Python interpreter and compatibility `PATH`.
- Change Prompt now generates valid Bash or Zsh prompt syntax according to the selected startup file.
- Desktop Transfer System exits successfully with a not-applicable explanation and the portable backup path.
- Runtime save-path mismatches were corrected in Devices Finder, Store Scrapper, CTF God, Dark and ButSystem; the Greek File Converter status display now prints its actual resolved path.
- Digital Footprint Finder and Store Scrapper internal help text now identifies both Termux and Ubuntu/Kali/Mint result locations.
- `pypdf` remains included in the desktop Python dependency set for Digital Footprint Finder.

Follow-up validation:

- Python syntax compilation: 177/177 PASS.
- Shell/shebang-aware Bash syntax validation: 14/14 PASS.
- English and Greek `Settings.py`: byte-identical PASS.
- README save-path coverage: 88/88 PASS.
- Fresh Bash Settings startup/config test: PASS.
- Fresh Zsh Settings startup/config test: PASS.
- `--termux-transfer` desktop behavior: PASS.
- Ded-Guy database refresh self-test: PASS.
- Ded-Guy inline UI self-test: PASS.
- Ded-Guy UI/language self-test: PASS.
- The embedded README catalog's File Converter/outer-details nesting edge case is handled so File Converter receives the same runtime platform-path description as the other tools.
