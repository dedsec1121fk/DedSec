# DedSec Project — Owner's Development and Maintenance Handbook

**Project creator / owner:** `dedsec1121fk` (as credited in the original project files).  
**Coverage:** Termux on Android; Ubuntu, Kali Linux, Linux Mint and other apt-based Linux systems (best effort).  
**Maintenance edition:** 10 October 2026 · source snapshot `v1.0.2-8-gdbcc9e3` plus subsequent maintenance repairs.  
**Purpose:** Enable a human maintainer to understand the project, recreate the implementation workflow, diagnose failures and prepare safe releases without needing the original developer present.

## 1. What this document is (and is not)

The DedSec Project is attributed to its creator, `dedsec1121fk`. Its actual implementation lives in Python, Bash, HTML, CSS and JavaScript. This handbook describes the structure and a **repeatable from-scratch engineering process** for that source. It is **not a contemporaneous diary** of every historic keystroke, commit or library decision: details of that history cannot be recovered solely from the supplied archive. No AI author is credited as creator of the project. In a release, retain existing contributor and legal-document credits; don't claim that existing contributors did work they didn't do.

**Authorship maintenance statement (owner-provided):** "I created DedSec Project, and the project is mine." Do not replace this statement with an invented milestone timeline or claim proof of the author's development methods from source code alone.

For authentic historical annotations, append dated owner notes under section 16 and keep original git commits where they exist.

## 2. Project goals and design boundaries

The project brings together a bilingual command-line menu, educational utilities, terminal games, a local browser-served desktop interface called DedSec OS, desktop/Termux platform compatibility and contributor documentation. Important principles:

- Start from a single source repository; do not silently switch its `origin` remote to third-party forks.
- Keep English and Greek editions consistent, including help, credits, installation and legal text.
- Separate rootless Termux-specific tools from native desktop Linux: never simulate Android hardware permissions on Ubuntu.
- Use the project Python virtual environment on desktop; avoid pip installing into the OS-managed interpreter (PEP 668).
- Make network and proxy status explicit. Tor or shell HTTP proxy variables are **not** a VPN and do not transparently redirect existing desktop browser traffic.
- Treat passwords, payment credentials, camera/location data and other personal information as private; avoid enabling deceptive collection or publication tools.
- Respect contributor and legal-document credits, upstream licenses and platform restrictions.

## 3. File tree and ownership of functionality

| File/directory | What it does | Primary maintenance consideration |
| --- | --- | --- |
| `Setup.sh` | Cross-platform setup entry for Termux and apt-based Linux | Legal gate first, OS package install, `.venv` creation, logs, import checks |
| `Setup-Termux.sh` | Termux dependency setup | Termux-native `pkg`, binary wheel fallback, core imports, log/status handling |
| `Compat/legal_consent.sh` | Installation terms prompt shared by both installers | `y`, Enter, `n`, `r`, `re`, `rg`; persistent digest-based acceptance |
| `Run.sh` | Entrypoint to main menu | Selects the project `.venv` interpreter on desktop and PATH shims |
| `Compat/bin/` | Safe Termux command shims on desktop | Platform detection; don't override native commands unintentionally |
| `Scripts/Settings.py` | Main menu, settings, embedded DedSec OS server and browser UI | Large module with inline HTML, CSS, JS and generated server; edit cautiously |
| `Scripts/ButSystem.py` | Flask-backed subproject | Flask and supporting Python dependencies must exist in selected interpreter |
| `Scripts/DedSec Market.py` | Menu-driven tool management | Package choice and remove/install boundaries |
| `Scripts/Games/` | Standalone terminal games | Python syntax, dependencies, input loops, terminal sizing |
| `Scripts/Developer Base/` | Developer tools and platform-specific components | Platform support & default output directories |
| `Scripts/Network Tools/` | Network utilities | State/capability displays; do not overpromise masking of traffic |
| `Scripts/Fake Pages/` and `Scripts/Personal Information Capture/` | Sensitive legacy modules | Keep desktop safety barriers; do not make credential/camera capture portable |
| `Scripts/Ελληνική Έκδοση/` / Greek-named edition | Greek menu and script variants | Unicode filename repair and copy consistency |
| `Important Documents/` | Legal originals, translated reading copies, guides | Preserve both legal DOCX originals, keep TXT views in sync |
| `.github/` | CI/repository automation | Avoid surprise expensive jobs and unnecessary release builds |
| `tests/` | Fast static and contract tests | Add tests for every regression |
| `APK's/`, `Extra Content/` | Android artifacts and bundled materials | Large; do not rebuild, re-sign or redistribute without owner authority |

The `Scripts/Settings.py` monolith is unusually large. Avoid broad text substitutions or reformatting the whole file: embedded Python strings, HTML, CSS and JavaScript are interleaved.

## 4. How to rebuild the project architecture from the beginning

These are **engineering reconstruction steps**, not a claim that the author followed this exact historic order:

1. **Choose the interfaces.** Define a text menu callable from a shell, English/Greek command labels and an optional local browser desktop. Decide which features may run on Linux and which require Termux.
2. **Create the root folder.** Add `Setup.sh`, `Setup-Termux.sh`, `Run.sh`, `Scripts/`, `Compat/`, `Important Documents/`, `.github/`, `tests/` and a `README.md` describing requirements.
3. **Implement `Settings.py` as the routing layer.** Store a menu-style preference, language preference, autostart flag and toolkit directory indexing. Discover files by path, launch safe Python children using `sys.executable` and return cleanly after child process termination.
4. **Implement Termux installation.** Use `pkg` for platform packages; install Python dependencies while considering Android wheels and native `python-*` packages. Verify imports after install. Run on Termux itself before declaring success.
5. **Implement Linux installation.** Detect an apt-based distribution; create `.venv`; install Flask/Flask-SocketIO etc. inside that venv; expose compatibility helpers in `Compat/bin`. Never change system Python's site packages.
6. **Add legal confirmation ahead of setup side effects.** Present readable copies of the legal DOCX documents before installing packages or writing startup hooks. Reject `n` or closed stdin. Persist acceptance against the document digest; re-prompt after terms change.
7. **Develop the local OS in `Settings.py`.** The server accepts local HTTP API requests; the embedded HTML/CSS/JS implements windows, document editors, terminal, browser, files, games, preferences and troubleshooting. Keep each browser control tied to a real handler and endpoint.
8. **Add self-contained games.** Maintain separate game state, reset/new-game path, pointer/keyboard inputs, score rendering and pause behavior. Include deterministic logic tests and real browser input tests.
9. **Add safe backups/updates.** Backups should archive local project files into Downloads with progress and atomic finalization. Repository updates must use the intended canonical origin without overwriting it from a fork.
10. **Document and verify.** Add bilingual instructions, contributor credits, syntax checking, first-setup refusal tests, API tests and GUI smoke tests. Build/release only after all required checks pass.

## 5. Fresh install, setup consent and retry

From the project root:

```bash
bash Setup.sh
# After first successful install, for normal launches:
./Run.sh
# Update dependencies without opening the menu:
bash Setup.sh --update-only
# Avoid a long OS upgrade when debugging:
bash Setup.sh --skip-system-update --required-only --no-run
```

The very first setup asks the user to accept legal documents from `Important Documents/`:

| Response | Behavior |
| --- | --- |
| `y` or **Enter** | Accept; setup continues |
| `n` | Decline; returns a nonzero code; **no package/profile modifications before the prompt** |
| `r` | Show reading instructions |
| `re` | Print English legal document, then return to prompt |
| `rg` | Print Greek legal document, then return to prompt |
| EOF / Ctrl+D | Reject unattended installation; no implicit acceptance |

Signed legal DOCX source documents were **not rewritten** by the maintenance patch; UTF-8 TXT reading copies are added so an installer can display them in a terminal without installing a DOCX reader. Keep TXT and DOCX in sync whenever the originals change. The marker `~/.local/state/dedsec/legal-acceptance-v1.txt` stores a hash of the original DOCX texts, **not** a scanned user signature, and is per-user. It requires re-acceptance when those originals change. This is a UX approval record, not a substitute for legal advice or a legally enforceable signature workflow.

The gate covers both `Setup.sh` and direct `Setup-Termux.sh`. `--help` is available without accepting because it installs nothing. Existing installations can retry declined setup at any time.

## 6. Python environment and dependencies

Linux desktop:

```bash
bash Setup.sh --skip-system-update --required-only --no-run
./.venv/bin/python -c 'import flask, flask_socketio, requests; print("Core imports OK")'
./.venv/bin/python Scripts/Settings.py --build-id
./.venv/bin/python Scripts/Games/Buzz.py
```

`python3 Scripts/ButSystem.py` may **still** fail if the host interpreter differs from `.venv`: use `./Run.sh` or explicitly `./.venv/bin/python Scripts/ButSystem.py`. Do not work around PEP 668 by using `sudo pip install --break-system-packages`. All launcher processes should inherit the selected interpreter or call `sys.executable`. `Flask`, `Flask-SocketIO`, Werkzeug, Jinja2, cryptography and QR-code support are now core setup requirements on desktop; corresponding dependencies were included in Termux core where appropriate.

Termux: the main interpreter is normally `python` from `pkg`, and Python modules are installed with Termux-native packages or pip when safe. Hardware features still require the Android companion apps and appropriate user permissions.

## 7. Menu, shell startup, language and modes

Preference data lives in `Language.json` (path resolved by `Settings.py`; don't assume it is always in the project root). A user-selected style and `menu_autostart` flag must persist independently of fresh setup. `--configure-menu-autostart` refreshes the shell startup block once after packages install; this can create a startup block but **must not turn autostart back on if the user disabled it**.

- **Termux:** `$PREFIX/etc/bash.bashrc`.
- **Bash desktop:** `~/.bashrc`.
- **Zsh desktop:** `~/.zshrc`.
- Supported styles: list, grid, number, Ded-Guy (`pipboy` alias), DedSec OS.
- Prefer terminal-agnostic launch commands in documentation. Don't say "restart Termux" on Ubuntu.
- Preserve the shell content outside `# DedSec` managed blocks; do not overwrite custom aliases or user startup logic.

Mouse wheel and arrow menu navigation must be checked with a real interactive terminal; terminal control libraries and hosts report wheel deltas differently. When choosing an exit item, ensure only one correctly numbered or zero-labelled entry exists.

## 8. Updates and Git source integrity

Canonical project source is `https://github.com/dedsec1121fk/DedSec`. Alternate source under `sal-scar/DedSec` is a third-party source. Never silently replace the canonical repo's `origin` or automatically merge unrelated code from the alternate fork. The maintenance build keeps the alternative in `~/DedSec-Alternate-Source` as a separate local checkout.

```bash
git remote -v
git status --short
git branch --show-current
git fetch origin
# Inspect changed files first; use only the correct repo:
git log -5 --oneline
```

The staged `Settings-Updated.py` updater should print the command with the actual current interpreter/path instead of hard-coding Termux. Protect against updates to a dirty working directory, path traversal and unexpected remote changes. Back up user data and run tests before installing a staged update. Do not use `git reset --hard` as an updater shortcut.

## 9. Backup and recovery

On desktop, `Settings → Save DedSec Project` now makes a local, offline project ZIP, avoiding network downloads or cloning large Android artifacts. A partial output file is promoted atomically only on success. It excludes generated `.git`, venv, Python caches and other transient files. Its destination is the XDG Downloads directory (or `~/Downloads` fallback). Check the printed path; keep an earlier backup until the new one completes.

On Termux, the legacy extended backup/export path is still present and may copy more folders or apps: its duration and I/O may be much higher. Verify that no private secrets, SSH keys, browser profiles or session tokens are unintentionally archived. Do not provide an export download to a public server without the user's permission.

Recovery for desktop: keep the backup, extract it into a NEW folder, run `bash Setup.sh` and then `./Run.sh`; do not blindly overwrite an active checkout. Shell profile cleanup uses only DedSec-managed blocks.

## 10. DedSec OS — architecture and API contract

`Scripts/Settings.py` embeds an HTML document (`INDEX_HTML`) and a generated Python HTTP server source. The browser is a UI client, not a privileged OS kernel. JavaScript communicates with localhost endpoints such as `/api/system/scratchpad`, `/api/system/processes`, `/api/system/storage`, `/api/downloads` and package metadata endpoints. Understand those two sides before modifying a feature.

**Adding a UI feature safely:** find its HTML `id`, the `addEventListener` or event delegation handler, the client `apiGet`/`apiPost` call, the server route handler, the underlying function, and any state persistence. Add a regression check for each link. Avoid duplicate IDs and parallel handlers bound more than once. For dynamic UI, attach handlers after inserting elements or use delegated events.

The embedded browser uses iframes/reader views. Third-party sites can refuse iframe embedding using `X-Frame-Options` or CSP `frame-ancestors`; no local code can legally force those sites to embed. Show an explanatory fallback and open the page in the external browser. **Do not** remove browser security protections or claim every site can render internally.

Termux-specific Android bridge commands are not available on desktop. Hide or disable their controls with a clear "not supported on this platform" explanation instead of showing Android storage permissions on Ubuntu.

## 11. DedSec OS apps and known regression risks

**Games:** Solitaire and Memory have dynamic click handlers; Tic-Tac-Toe, Connect Four and 2048 live in the workspace game extension; Pinball uses a `requestAnimationFrame` simulation. The OS game state is created lazily when Games is opened. Validate game tabs, pointer events, card stacking, window z-index, keyboard focus and pane sizing on an actual supported browser. For 2048, both touch arrows and keyboard arrows/WASD should move tiles; Pinball uses left/right launch controls.

**Scratchpad:** the authoritative note is stored under the active OS profile's `notes/Scratchpad.txt`. The maintenance build checks a saved note by reading it back through the API and caches it locally as a connection fallback. A toast alone is not proof that a save succeeded. Respect the 2 MB limit and check writes/permissions.

**Word:** rich text uses browser editing commands; preserve the current selection when toolbar/picker elements take focus. Test bold/italic/underline/strike, text color, typing after formatting and reopening saved text. Browser support for `execCommand` varies. The maintenance build retains the last in-editor text range for toolbar operations.

**Photo Studio:** use `New canvas` before painting on an empty workspace, then activate brush mode. Verify draw and save on both images and blank canvases. For `canvas.toDataURL`, note memory usage and cross-origin taint restrictions.

**Software Center:** desktop package metadata belongs to apt; Android storage-link detection must only run on Termux. The maintenance build distinguishes `platform: desktop` and avoids demanding Android permissions for local Linux package lists. A privileged apt install may still require sudo, host policy and a working apt repository.

**Help & Troubleshooting:** topic buttons, category sidebar, wizard, diagnostics and `Help` action buttons are all meant to be wired. Check that buttons remain clickable within desktop window CSS and when content is re-rendered. A click should navigate to the matching article, not silently do nothing.

**Task manager:** process lists are best presented with highest RAM users first and a scrollable pane; process action safety requires matching process start ticks to avoid affecting a reused PID.

**Terminal:** the web terminal is not guaranteed to be a full PTY, and command echo from a shell must not be mistaken for a duplicate execution. Use a real terminal for full-screen ncurses apps and commands requiring job control. Fix Javascript ReferenceErrors in special-key handlers and do not execute terminal input twice.

## 12. Network and privacy semantics

- **Tor enabled** should mean a running Tor service, not merely a saved checkbox. Verify SOCKS listener reachability and background process health. If the state is uncertain, print "unknown" instead of claiming active anonymity.
- An **HTTP proxy** installed in environment variables influences applications that honor those variables after they start. It does not re-route all host traffic, geolocation, browser tabs, or the user's existing VPN.
- Document the actual proxy endpoint, testing method, scope and limitations. A country label is a proxy preset, not proof of a changed external IP.
- Avoid automatic scraping or secret publication. Never display private API tokens in logs or screenshots.

## 13. Testing: fast, safe, repeatable

Before committing:

```bash
bash -n Setup.sh Setup-Termux.sh Run.sh Compat/legal_consent.sh
python -m compileall -q Scripts tests
python -m pytest -q tests
# JS is inside Settings.py; extract the INDEX_HTML scripts and run `node --check`.
# See tests/test_maintenance_regressions.py for legal and source contract checks.
```

Then manually test on each supported platform: fresh legal consent; declined setup without side effects; Terms reading `re` and `rg`; re-accept after DOCX changes; first shell autostart; disabled autostart remains disabled; `ButSystem.py` under the right interpreter; `Buzz.py` gameplay; Git remote unchanged after both update options; backup progresses and archive opens; Tor/proxy status honesty; Word formatting, Scratchpad reload, Photo canvas; all six reviewer-flagged games; Help buttons; apt package controls; browser external fallback; no Termux-only prompts on desktop; Greek language.

Do **not** run apt, package upgrades, network downloads, external site probing, or changes to a real home directory as part of fast CI unit tests. Use isolated temporary HOME directories and mocks. GUI acceptance still needs a real graphical machine: static parsing isn't functional proof.

## 14. Security, legal compliance and ownership

Keep the original legal disclaimer DOCX files and contributor credits. Source code should not assume a license transfer beyond the actual license/agreement text. Review `LICENSE.txt` and any applicable third-party assets before modifying distribution terms.

The project contains legacy folders with names referring to fake pages, information capture and Trojan behavior. These are high-risk: maintain the safer desktop compatibility behavior that blocks deceptive credential/card, camera/location/microphone capture and unauthorized publication. The runner returns code 126 when a utility is intentionally unavailable; list/number/grid menu handlers must stay open and offer navigation rather than exiting the menu. For legitimate defensive training, use consent-based simulated data, locally hosted fixtures and synthetic credentials. Do not "fix" unavailable dangerous features by making them operational.

Do not embed secret credentials in docs, the ZIP backup or issue attachments. Default to local loopback for the OS server. Harden any remote access with authentication, CSRF/origin checks and authorization before publishing it publicly.

## 15. Release and rollback checklist

1. Branch from a clean canonical main checkout. Confirm `git remote -v`.
2. Make a ZIP/data backup before code changes; preserve release binaries and signatures unchanged unless owner expressly approves rebuilding them.
3. Make changes in small isolated files, especially for the `Settings.py` monolith.
4. Run Bash/Python/JS syntax tests, legal consent unit tests and file checks.
5. Validate Ubuntu, Kali, Mint and Termux behavior independently; no claim of "all fixed" until confirmed by the relevant platform tester.
6. Re-run the Ubuntu observation issue list and attach evidence or label an issue still awaiting live testing.
7. Update English/Greek help and documentation together, preserving credits.
8. Review repository status for generated caches, accidental secrets, large diffs and unexpected remote URL changes.
9. Release one branch only; consolidate CI runs so actions minutes are not wasted. Avoid auto-pushing from a setup script.
10. On regression, restore a prior verified commit/ZIP without deleting users' data or overwriting shell customization.

## 16. Owner's original-history record (fill with verified information)

To preserve how the original author developed the project over time, add only dated facts the author confirms. Possible entries: when the initial shell menu was coded; when Greek support was built; which first Python tools were written; when DedSec OS was introduced; how Termux dependency decisions changed; how Ubuntu compatibility evolved. Record commit IDs, dates, screenshots or correspondence if available. The current ZIP alone does not establish those dates or prove historical tool usage, so this handbook intentionally does not invent them.

## 17. Quick fault lookup

| Symptom | Likely cause | Start here |
| --- | --- | --- |
| Installer refuses | Terms declined or unreadable legal originals | `Compat/legal_consent.sh`, `Important Documents/` |
| `ModuleNotFoundError: flask` | System Python instead of `.venv`, missing core dependency | `./Run.sh`, `Setup.sh`, `Scripts/ButSystem.py` |
| `cfg` undefined in Buzz | Wrong scope/indentation in quiz loop | `Scripts/Games/Buzz.py`, quiz choice branch |
| Project save looks frozen | Legacy remote clone/APK operation | Use desktop local ZIP; inspect setup log and disk |
| Unknown source remote | Updater rewrote `origin` or downloaded fork | `git remote -v`, updater path in `Settings.py` |
| Browser website blank | External site prohibits iframe | Use `Open External` / Reader view |
| Scratchpad lost | Write error, profile switch or stale browser state | API read-back, profile `notes/Scratchpad.txt` |
| Software Center asks Android permission | Termux-only storage logic applied on desktop | Platform status branch in generated server |
| Games ignore clicking | Window overlap, inaccessible tab, UI init or CSS | Check JS console and actual browser pointer events |
| UI formatting wrong | Contenteditable loses selection on toolbar focus | Selection preservation in Word ribbon |
| Shell menu doesn't auto-start | First-install hook absent, shell profile mismatch | `--configure-menu-autostart`, stored preference |
| Tor not changing browser IP | Tor SOCKS service isn't a VPN / browser ignores proxy env | Check SOCKS listener and new process scope |

**Maintainer rule:** Never represent an untested feature as fixed; record partial changes and request a real platform regression test before a public stable release.
