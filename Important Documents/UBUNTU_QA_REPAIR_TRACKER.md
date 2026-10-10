# Ubuntu 26.04.1 tester — repair tracker (10 October 2026)

The issue list comes from `Observations - Ubuntu Linux.pdf` supplied by the project owner. "Addressed in code" is not equivalent to "confirmed fixed on Ubuntu". A real GUI regression pass is still necessary.

| Reviewer finding | Patch or finding | Status |
| --- | --- | --- |
| Setup feedback/log missing | Captured setup stdout+stderr in timestamped per-user log; dependency checks print details | Addressed in code; installer needs Ubuntu run |
| Scroll wheel jumps / arrow menu won't wrap | Enabled up/down wrap at list menu ends, plus style/language selection; mouse wheel still needs terminal test | **Partially addressed** |
| Malformed `\0. Exit` duplicate | Fixed duplicate Settings number-style Exit by using 0 only | Addressed in code; needs interactive test |
| First install auto-start not effective | Added one-time `--configure-menu-autostart` after install on Linux/Termux, respecting saved opt-out | Addressed in code; needs new shell test |
| Update source 2 rewrites git origin | Alternate source is checked out to a separate folder; avoids main `origin` overwrite | Addressed in code; needs remote regression |
| Self-update says "Termux" on Ubuntu | Dynamic interpreter/script path and platform-neutral command wording | Addressed in code |
| Save Project hangs | Desktop now builds a local ZIP instead of remote clones and APK fetching, with progress and staged output | Addressed in code; test real filesystem |
| Tor status contradictory / Termux wording | Improved wording about proxy scope and opening a new shell; service-state test needs real Tor | **Partially addressed** |
| HTTP proxy doesn't change website geolocation | Not a global VPN: existing browser/VPN traffic isn't changed by env vars; document limitation | **Limitation documented** |
| DedSec OS browser can't embed websites | Shows iframe restrictions + `Open External` fallback | **Browser/platform limitation** |
| Word toolbar loses selection or color | Last valid editor selection preserved before format commands | Addressed in code; GUI verification required |
| Word resize handles obscure close button | Reduced top-corner resize handle region | Addressed in CSS; GUI verification required |
| Terminal minimal support / duplicate text | Fixed undefined JS session variable in control-key handler; full PTY/echo issue not solved | **Partially addressed** |
| Task manager categories hidden; sort by RAM | Processes sorted by RSS memory descending; wrapped Control Center tabs prevent hidden tab access | Addressed in code; GUI test required |
| Scratchpad save disappears | Read-back verification, per-profile file path, local browser cache fallback | Addressed in code; GUI verification required |
| Software Center asks Android storage on Ubuntu | Platform-aware desktop storage readiness, Linux package manager, hide Android permission actions | Addressed in code; Linux privilege testing required |
| Solitaire unable to play | Improved pane pointer/scroll accessibility; existing logic retained | **Partially addressed; GUI test required** |
| Tic-Tac-Toe unable to place symbols | Improved pane pointer/scroll accessibility; existing game click bindings retained | **Partially addressed; GUI test required** |
| Memory unable to flip cards | Improved pane pointer/scroll accessibility; existing card click logic retained | **Partially addressed; GUI test required** |
| Pinball ball outside bumpers | Adjusted shot location and velocity to enter playfield | Addressed in physics; GUI test required |
| 2048 moves not working | Added keyboard arrows/WASD along with existing onscreen buttons | Addressed in input; GUI test required |
| Connect Four unable to drop discs | Improved pane pointer/scroll accessibility; existing logic retained | **Partially addressed; GUI test required** |
| Help cards/sections don't respond | Handler contracts reviewed and clickability/stacking adjusted; no browser UI smoke available | **Partially addressed; GUI test required** |
| Photo Editor blank/no painting | `New canvas` creates an actual image; brush can operate on it | Addressed in code; GUI test required |
| Termux wording/Android bridge in desktop OS | Some copy corrected; remaining platform copy and feature parity needs full sweep | **Partially addressed** |
| `ButSystem.py` Flask missing (PEP 668) | Flask/Flask-SocketIO/etc are core dependencies in Linux `.venv`; direct Ubuntu system-Python launch re-execs project `.venv`; Termux core updated | Addressed in setup; install test required |
| `Buzz.py` NameError cfg | Fixed quiz config variable scope/indentation | Addressed in code; gameplay test required |
| Fake phishing and capture pages disabled / Enter behavior | Retain deliberate desktop security restrictions; blocked scripts now return to the menu after Enter | **Restrictions preserved; menu return fixed in code** |

**Bilingual runtime:** Both English and Greek editions of `Settings.py` and `ButSystem.py` are synchronized; the Greek `Buzz.py` retains its separate localized questions/game menu.

**Verification performed here:** Shell syntax, Python compilation, JS grammar and repository tests. This is **not** an Ubuntu 26.04.1 end-to-end acceptance run. Re-run the tester's cases with mouse and keyboard before declaring all issues solved.
