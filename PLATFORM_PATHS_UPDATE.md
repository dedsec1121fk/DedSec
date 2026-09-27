# Platform Save Paths and Settings Validation

Targets: Termux (Android), Ubuntu, Kali Linux, Linux Mint.

## What changed

Every documented tool save location in `README.md` now has a `Platform Save Paths` section with explicit entries for all four targets. The Settings/Ded-Guy metadata layer also adds those paths to script descriptions dynamically.

For ordinary desktop output, Ubuntu, Kali Linux and Linux Mint use the user's Downloads directory (XDG Downloads when Settings can resolve it, otherwise `~/Downloads`). Termux continues to use Android shared storage (`~/storage/downloads` or the tool's Android Download fallback).

Android/Termux-only system-management tools are described as not applicable on desktop. Modules intentionally blocked by the desktop compatibility launcher are not falsely advertised with an operational desktop save path.

## Settings/menu fixes

Settings now chooses `~/.zshrc` for Zsh and `~/.bashrc` for Bash on desktop while retaining Termux's `$PREFIX/etc/bash.bashrc`. Auto-start and language aliases retain the same project Python interpreter, `.venv` path and `Compat/bin` path as a normal desktop launch. The prompt editor emits shell-appropriate prompt syntax for Bash and Zsh.

Save Project resolves and prints the current platform Downloads path. Transfer System remains Termux-only and returns a clean informational result on desktop rather than failing. About/System Usage displays platform-aware information.

## Runtime path corrections

The runtime output paths were aligned with the descriptions for safe cross-platform tools that still had Android-first assumptions, including Devices Finder, Store Scrapper, CTF God, Dark and ButSystem. The Greek File Converter now displays its actual resolved output folder. Digital Footprint Finder and Store Scrapper help text explicitly shows both Termux and desktop result paths.

## Validation results

- 177/177 Python files compile.
- 14/14 Bash/shebang shell files pass `bash -n`.
- 88/88 README Save Location entries have Platform Save Paths.
- English and Greek Settings copies are identical.
- Fresh Bash settings/autostart test passes.
- Fresh Zsh settings/autostart test passes.
- Desktop Transfer System handling passes.
- Ded-Guy database, inline UI and UI/language self-tests pass.

Hardware-, GUI-, network- and external-service-dependent behavior still depends on the machine and installed services. Run `bash Setup.sh` and launch through `./Run.sh` for the supported environment setup.
- The embedded tool-catalog nesting edge case for File Converter is handled at runtime, so its four-platform path description appears correctly in Settings/Ded-Guy as well as README.
