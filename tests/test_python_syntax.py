from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", ".venv", "__pycache__"}

def test_all_python_files_compile():
    files = [p for p in ROOT.rglob("*.py") if not any(x in EXCLUDED for x in p.parts)]
    assert files, "No Python files found / Δεν βρέθηκαν Python αρχεία."
    errors = []
    for path in files:
        try:
            compile(path.read_bytes(), str(path), "exec")
        except SyntaxError as exc:
            errors.append(f"{path.relative_to(ROOT)}:{exc.lineno}: {exc.msg}")
    assert not errors, "\n".join(errors)
