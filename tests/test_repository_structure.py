from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_required_files_exist():
    required = [
        "README.md", "LICENSE.txt", "SECURITY.md", "CONTRIBUTING.md",
        "TESTING.md", "Setup.sh", "Setup-Termux.sh", "Run.sh",
        "Scripts/Settings.py"
    ]
    missing = [p for p in required if not (ROOT / p).exists()]
    assert not missing, "Missing / Λείπουν: " + ", ".join(missing)
