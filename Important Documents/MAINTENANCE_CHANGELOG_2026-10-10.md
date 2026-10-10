# DedSec Maintenance Change Summary — 2026-10-10

Original archive: dedsec1121fk-DedSec-v1.0.2-8-gdbcc9e3.zip

## Existing files modified
- `CROSS_PLATFORM.md`
- `README.md`
- `Scripts/ButSystem.py`
- `Scripts/Games/Buzz.py`
- `Scripts/Settings.py`
- `Scripts/Ελληνική Έκδοση/ButSystem.py`
- `Scripts/Ελληνική Έκδοση/Settings.py`
- `Setup-Termux.sh`
- `Setup.sh`

## Files added
- `Compat/legal_consent.sh`
- `Important Documents/DEDSEC_FULL_MAINTENANCE_HANDBOOK_EN.md`
- `Important Documents/DEDSEC_ΟΔΗΓΟΣ_ΣΥΝΤΗΡΗΣΗΣ_GR.md`
- `Important Documents/Legal Disclaimer English Version.txt`
- `Important Documents/Legal Disclaimer Greek Version.txt`
- `Important Documents/MAINTENANCE_CHANGELOG_2026-10-10.md`
- `Important Documents/UBUNTU_QA_REPAIR_TRACKER.md`
- `tests/test_maintenance_regressions.py`

## Validation
- 17/17 pytest checks passed.
- Bash entry points pass `bash -n`.
- Python source compiled.
- Embedded browser JavaScript passes `node --check`.

## Limits
- This build was not installed on the tester’s Ubuntu 26.04.1 machine.
- Full graphical acceptance of all DedSec OS apps is still pending; see `Important Documents/UBUNTU_QA_REPAIR_TRACKER.md`.
- Existing Android APKs were preserved rather than rebuilt or re-signed.
