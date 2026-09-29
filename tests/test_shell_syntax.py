from pathlib import Path
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]

@pytest.mark.skipif(shutil.which("bash") is None, reason="bash unavailable")
def test_shell_syntax():
    files = list(ROOT.glob("*.sh"))
    assert files
    failures = []
    for path in files:
        result = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
        if result.returncode != 0:
            failures.append(f"{path.name}: {result.stderr.strip()}")
    assert not failures, "\n".join(failures)
