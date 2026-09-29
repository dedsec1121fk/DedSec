from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def shell_files():
    files = set(ROOT.glob("*.sh"))
    compat = ROOT / "Compat" / "bin"

    if compat.is_dir():
        for path in compat.iterdir():
            if not path.is_file():
                continue
            try:
                first_line = path.open(
                    "r", encoding="utf-8", errors="ignore"
                ).readline()
            except OSError:
                continue

            if first_line.startswith("#!") and (
                "bash" in first_line or "/sh" in first_line
            ):
                files.add(path)

    return sorted(files)


@pytest.mark.skipif(
    shutil.which("bash") is None,
    reason="bash unavailable / Το bash δεν είναι διαθέσιμο",
)
def test_shell_syntax():
    files = shell_files()
    assert files, "No shell files found / Δεν βρέθηκαν shell αρχεία."

    failures = []
    for path in files:
        result = subprocess.run(
            ["bash", "-n", str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            failures.append(
                f"{path.relative_to(ROOT)}: {(result.stderr or result.stdout).strip()}"
            )

    assert not failures, (
        "Shell syntax errors / Σφάλματα shell syntax:\n" + "\n".join(failures)
    )
