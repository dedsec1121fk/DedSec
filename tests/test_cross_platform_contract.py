from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def test_setup_help():
    result = subprocess.run(["bash", str(ROOT / "Setup.sh"), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    output = result.stdout + result.stderr
    for name in ("Termux", "Ubuntu", "Kali Linux", "Linux Mint"):
        assert name in output

def test_run_contract():
    text = (ROOT / "Run.sh").read_text(encoding="utf-8")
    for marker in ("DEDSEC_PLATFORM=termux", "DEDSEC_PLATFORM=desktop-linux", "Scripts/Settings.py"):
        assert marker in text
