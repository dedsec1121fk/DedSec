# DedSec Cross-Platform Compatibility Notes

This build adds a shared launch/setup path for:

- Ubuntu
- Kali Linux
- Linux Mint
- Termux on Android

## Install / update

Run from the project root:

```bash
bash Setup.sh
```

Desktop Linux creates a project-local `.venv` and installs Python packages there instead of modifying the distro-managed Python installation. Termux delegates to the original Termux-native installer (`Setup-Termux.sh`).

To install/update dependencies without opening the menu:

```bash
bash Setup.sh --update-only
```

After setup, launch with:

```bash
./Run.sh
```

## Compatibility changes

- `Setup.sh` now detects Termux versus apt-based desktop Linux.
- Ubuntu/Kali/Mint use `apt-get` plus a local Python `.venv`.
- `Run.sh` always launches the menu with the correct Python interpreter and compatibility PATH.
- `Settings.py` no longer assumes `/data/data/com.termux/...` for the project, home directory, bashrc, or Downloads path.
- Child Python scripts are launched with `sys.executable`, keeping them inside the same environment.
- Desktop compatibility shims provide safe equivalents for common Termux commands such as `pkg`, `termux-open`, `termux-open-url`, clipboard helpers, desktop notifications, basic `termux-info`, battery status, and TTS.
- File Converter, Simple Websites Creator, QR Code Generator, Tree Explorer, and Loading Screen now use desktop-appropriate paths/behavior where applicable.
- English and Greek menu copies receive the same portability fixes.

## Platform-specific tools

Some tools are inherently Android/Termux-specific and do not have a meaningful Ubuntu/Kali/Mint equivalent. In desktop compatibility mode, the menu reports them as not applicable instead of running incorrect system modifications:

- Android App Launcher
- Mobile Desktop (Termux `proot-distro` / Termux:X11 manager)
- Termux Backup Restore
- Termux Repair Wizard
- Mobile Developer Setup

They remain available unchanged on Termux.

## Sensitive tooling

The desktop compatibility launcher does not enable or port tools whose purpose includes phishing, credential/card collection, deceptive camera/location/microphone capture, Trojan behavior, or automated publication of sensitive captured data. Those original source files remain in the archive, but the desktop launcher blocks them rather than making them more portable.

## Validation performed

The full audit is documented in `PORTABILITY_AUDIT.md`. In this build, 209 text/source files (420,647 lines) were statically scanned, all 177 Python files passed syntax compilation, all 14 shell/shim files passed `bash -n`, the main Settings self-tests passed, Terminal Arcade's embedded-module self-test passed, and the desktop launcher/shims received smoke tests.

Actual hardware-dependent features still depend on the host (for example GUI availability, audio devices, Tor service state, network permissions, optional third-party binaries, and Android companion apps).

## Save/output path convention

Tool descriptions now list a save path for every supported target. When a tool uses shared Downloads, the convention is:

- Termux: `~/storage/downloads/...` when the Android storage link is available, otherwise the tool's Android `/storage/emulated/0/Download/...` fallback.
- Ubuntu: XDG Downloads when resolved by Settings, normally `~/Downloads/...`.
- Kali Linux: XDG Downloads when resolved by Settings, normally `~/Downloads/...`.
- Linux Mint: XDG Downloads when resolved by Settings, normally `~/Downloads/...`.

`README.md` has a `Platform Save Paths` block for every documented `Save Location` entry. Settings/Ded-Guy also enriches script descriptions with the four platform paths so the path information is available from the project UI, not only from the README.

Existing safe tools that previously selected an Android path first were adjusted so their runtime output matches the desktop description. This includes Devices Finder, Store Scrapper, CTF God, Dark, ButSystem download exports, and the Greek File Converter status text. Digital Footprint Finder and Store Scrapper now state both Termux and desktop result locations in their own help text.

Android/Termux-only management utilities are marked `Not applicable` on Ubuntu/Kali/Mint. Desktop-disabled sensitive capture/phishing/Trojan modules are marked as not enabled rather than being given a misleading desktop output path.

## Settings/menu compatibility

Settings resolves the active startup file instead of always assuming Termux Bash:

- Termux: `$PREFIX/etc/bash.bashrc`
- Ubuntu/Linux Mint with Bash: `~/.bashrc`
- Kali or another Zsh session: `~/.zshrc`
- Bash sessions on any supported desktop: `~/.bashrc`

Desktop menu auto-start and the `e`/`g` aliases now launch with the same Python interpreter as the configured project environment and inject `Compat/bin` plus the virtual-environment `bin` directory into the child process `PATH`. This keeps `pkg` compatibility, clipboard/open helpers, notifications, and the other compatibility commands available even after opening a completely new shell.

The Change Prompt action emits Bash prompt syntax for Bash and Zsh prompt syntax for Zsh. Save Project uses the resolved Downloads directory and prints the exact output path. Transfer System remains a Termux-to-Termux migration feature; on desktop it returns cleanly with a message directing the user to Save Project rather than reporting a failure.
