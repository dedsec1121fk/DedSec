import os, sys, time, zipfile, shutil, subprocess, re, hashlib, json
from pathlib import Path
from datetime import datetime
TERMUX_ROOT = Path('/data/data/com.termux/files')
HOME_ROOT = Path('/data/data/com.termux/files/home')
DOWNLOADS_ZIP = Path('/storage/emulated/0/Download/name_backup.zip')
DOWNLOADS_DIR = DOWNLOADS_ZIP.parent
CONFIG_FILE = 'backup_config.json'
EXCLUDE_DIR_NAMES = {'cache', '.cache', 'tmp', '.tmp'}
DEFAULT_EXCLUDE_REL_PREFIXES = [Path('home/storage'), Path('usr/var/cache/apt/archives'), Path('usr/var/log'), Path('usr/tmp')]

def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None

def run(cmd, capture=False):
    try:
        if capture:
            p = subprocess.run(cmd, capture_output=True, text=True)
            return (p.returncode, p.stdout or '', p.stderr or '')
        else:
            return (subprocess.run(cmd, check=False).returncode, '', '')
    except Exception as e:
        return (1, '', str(e))

def termux_storage_ready() -> bool:
    return Path('/storage/emulated/0').exists()

def should_exclude(rel_path: Path, exclude_prefixes) -> bool:
    for p in exclude_prefixes:
        try:
            rel_path.relative_to(p)
            return True
        except Exception:
            pass
    if set(rel_path.parts) & EXCLUDE_DIR_NAMES:
        return True
    return False

def human_bytes(n: int) -> str:
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    f = float(n)
    for u in units:
        if f < 1024.0:
            return f'{f:.2f} {u}'
        f /= 1024.0
    return f'{f:.2f} PB'

def load_config():
    default = {'mode': 'full', 'include_caches': False, 'compression_level': 6, 'split_part_mb': 50, 'enable_home_manifest': True}
    if not Path(CONFIG_FILE).exists():
        Path(CONFIG_FILE).write_text(json.dumps(default, indent=2), encoding='utf-8')
        return default
    try:
        cfg = json.loads(Path(CONFIG_FILE).read_text(encoding='utf-8'))
        for k, v in default.items():
            cfg.setdefault(k, v)
        return cfg
    except Exception:
        return default

def preflight():
    if not TERMUX_ROOT.exists():
        print('[!] Termux root not found. Run inside Termux.')
        return False
    if not termux_storage_ready():
        print('[!] Storage not ready. Run: termux-setup-storage')
        return False
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    return True

def estimate_size(source_root: Path, exclude_prefixes) -> int:
    total = 0
    for root, dirs, files in os.walk(source_root, topdown=True, followlinks=False):
        root_p = Path(root)
        rel_root = root_p.relative_to(source_root)
        if rel_root != Path('.') and should_exclude(rel_root, exclude_prefixes):
            dirs[:] = []
            continue
        keep_dirs = []
        for d in dirs:
            rel_d = (root_p / d).relative_to(source_root)
            if should_exclude(rel_d, exclude_prefixes):
                continue
            keep_dirs.append(d)
        dirs[:] = keep_dirs
        for f in files:
            fp = root_p / f
            try:
                if fp.is_symlink():
                    continue
            except Exception:
                continue
            rel_f = fp.relative_to(source_root)
            if should_exclude(rel_f, exclude_prefixes):
                continue
            try:
                total += fp.stat().st_size
            except Exception:
                pass
    return total

def collect_metadata(tmp_dir: Path, enable_home_manifest: bool):
    meta = tmp_dir / 'meta'
    meta.mkdir(parents=True, exist_ok=True)
    if have('pkg'):
        rc, out, err = run(['pkg', 'list-installed'], capture=True)
        (meta / 'pkg_list_installed.txt').write_text(out if out else err, encoding='utf-8')
    else:
        (meta / 'pkg_list_installed.txt').write_text('pkg not found\n', encoding='utf-8')
    try:
        rc, out, err = run([sys.executable, '-m', 'pip', 'freeze'], capture=True)
        (meta / 'pip_freeze.txt').write_text(out if out else err, encoding='utf-8')
    except Exception as e:
        (meta / 'pip_freeze.txt').write_text(str(e), encoding='utf-8')
    if have('termux-info'):
        rc, out, err = run(['termux-info'], capture=True)
        (meta / 'termux_info.txt').write_text(out if out else err, encoding='utf-8')
    else:
        (meta / 'termux_info.txt').write_text('termux-info not available\nInstall: pkg install termux-tools\n', encoding='utf-8')
    (meta / 'backup_created.txt').write_text(datetime.now().isoformat(), encoding='utf-8')
    if enable_home_manifest:
        manifest = meta / 'home_manifest_sha256.txt'
        print('[*] Building HOME manifest (sha256) ...')
        lines = []
        for root, dirs, files in os.walk(HOME_ROOT, topdown=True, followlinks=False):
            root_p = Path(root)
            for f in files:
                fp = root_p / f
                try:
                    if fp.is_symlink():
                        continue
                    data = fp.read_bytes()
                    h = hashlib.sha256(data).hexdigest()
                    rel = fp.relative_to(HOME_ROOT)
                    lines.append(f'{h}  {rel}')
                except Exception:
                    continue
        manifest.write_text('\n'.join(lines) + '\n', encoding='utf-8')

def make_backup(mode: str, include_caches: bool, compression_level: int, enable_home_manifest: bool):
    if not preflight():
        return
    source_root = TERMUX_ROOT if mode == 'full' else HOME_ROOT
    exclude = [] if include_caches else DEFAULT_EXCLUDE_REL_PREFIXES
    print('=== DedSec Πίσωup v5 (Όχι-Root) ===')
    print(f'Mode   : {mode}')
    print(f"Caches : {('included' if include_caches else 'excluded')}")
    print(f'Comp   : {compression_level}')
    print(f'Target : {DOWNLOADS_ZIP}')
    print('[*] Estimating size...')
    est = estimate_size(source_root, exclude)
    print(f'[*] Estimated source size: {human_bytes(est)}')
    try:
        usage = shutil.disk_usage(str(DOWNLOADS_DIR))
        free = usage.free
        print(f'[*] Free space: {human_bytes(free)}')
        if free < max(est * 0.3, 200 * 1024 * 1024):
            print('[!] Προειδοποίηση: Low free space.')
    except Exception:
        pass
    tmp = Path('.dedsec_Πίσωup_tmp')
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    collect_metadata(tmp, enable_home_manifest)
    start = time.time()
    total_files = skipped = 0
    with zipfile.ZipFile(DOWNLOADS_ZIP, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=int(compression_level)) as zf:
        for p in tmp.rglob('*'):
            if p.is_file():
                zf.write(p, arcname=str(p.relative_to(tmp)))
        for root, dirs, files in os.walk(source_root, topdown=True, followlinks=False):
            root_p = Path(root)
            rel_root = root_p.relative_to(source_root)
            if rel_root != Path('.') and should_exclude(rel_root, exclude):
                dirs[:] = []
                continue
            keep_dirs = []
            for d in dirs:
                rel_d = (root_p / d).relative_to(source_root)
                if should_exclude(rel_d, exclude):
                    skipped += 1
                    continue
                keep_dirs.append(d)
            dirs[:] = keep_dirs
            for f in files:
                fp = root_p / f
                try:
                    if fp.is_symlink():
                        skipped += 1
                        continue
                except Exception:
                    skipped += 1
                    continue
                rel_f = fp.relative_to(source_root)
                if should_exclude(rel_f, exclude):
                    skipped += 1
                    continue
                try:
                    zf.write(fp, arcname=str(rel_f))
                    total_files += 1
                    if total_files % 1500 == 0:
                        print(f'[*] Added {total_files} files...')
                except Exception:
                    skipped += 1
    shutil.rmtree(tmp, ignore_errors=True)
    print('[*] Verifying ZIP...')
    try:
        with zipfile.ZipFile(DOWNLOADS_ZIP, 'r') as zf:
            bad = zf.testzip()
        print('[*] ZIP OK.' if not bad else f'[!] ZIP issue at: {bad}')
    except Exception as e:
        print(f'[!] Could Όχιt verify ZIP: {e}')
    dur = time.time() - start
    size = DOWNLOADS_ZIP.stat().st_size
    print('\n--- Backup Done ---')
    print(f'Files   : {total_files}')
    print(f'Skipped : {skipped}')
    print(f'Zip size: {human_bytes(size)}')
    print(f'Time    : {dur:.1f}s')

def safe_extract(zf: zipfile.ZipFile, member: zipfile.ZipInfo, target_dir: Path) -> bool:
    mp = Path(member.filename)
    if mp.is_absolute() or '..' in mp.parts:
        return False
    out_path = (target_dir / mp).resolve()
    if not str(out_path).startswith(str(target_dir.resolve())):
        return False
    try:
        zf.extract(member, path=str(target_dir))
        return True
    except Exception:
        return False

def restore_zip(mode: str):
    if not preflight():
        return
    if not DOWNLOADS_ZIP.exists():
        print('[!] Πίσωup Όχιt βρέθηκε.')
        return
    if mode == 'dry':
        confirm = 'LIST'
        print('Mode: DRY list.')
    else:
        confirm = 'RESTORE'
        print('!!! Προειδοποίηση !!! Επαναφορά may overwrite files.')
    if input(f'Type {confirm} to Συνέχεια: ').strip() != confirm:
        print('[*] Ακυρώθηκε.')
        return
    extracted = skipped = errors = 0
    with zipfile.ZipFile(DOWNLOADS_ZIP, 'r') as zf:
        members = zf.infolist()
        if mode == 'dry':
            for i, m in enumerate(members[:250], start=1):
                print(f'{i:03d} {m.filename} ({human_bytes(m.file_size)})')
            if len(members) > 250:
                print(f'... and {len(members) - 250} more.')
            return
        for m in members:
            p = Path(m.filename)
            if mode == 'home' and (len(p.parts) == 0 or p.parts[0] != 'home'):
                skipped += 1
                continue
            ok = safe_extract(zf, m, TERMUX_ROOT)
            if ok:
                extracted += 1
            else:
                errors += 1
    print('\n--- Restore Done ---')
    print(f'Extracted: {extracted}')
    print(f'Skipped  : {skipped}')
    print(f'Σφάλμαs   : {errors}')
    print('Tip: Restart Termux after restore.')

def parse_pkg_names(pkg_list_text: str):
    names = []
    for line in pkg_list_text.splitlines():
        line = line.strip()
        if not line or line.lower().startswith('listing'):
            continue
        token = line.split()[0]
        if '/' in token:
            token = token.split('/')[0]
        if re.match('^[a-z0-9][a-z0-9+.-]*$', token):
            names.append(token)
    return sorted(set(names))

def restore_assistant():
    if not preflight():
        return
    if not DOWNLOADS_ZIP.exists():
        print('[!] Πίσωup Όχιt βρέθηκε.')
        return
    if not have('pkg'):
        print('[!] pkg not found.')
        return
    with zipfile.ZipFile(DOWNLOADS_ZIP, 'r') as zf:

        def read_member(name):
            try:
                with zf.open(name, 'r') as f:
                    return f.read().decode('utf-8', errors='ignore')
            except Exception:
                return ''
        pkg_text = read_member('meta/pkg_list_installed.txt')
        pip_text = read_member('meta/pip_freeze.txt')
    pkgs = parse_pkg_names(pkg_text)
    pip_lines = [ln.strip() for ln in pip_text.splitlines() if ln.strip() and (not ln.startswith('#'))]
    print(f'Packages: {len(pkgs)} | Pip lines: {len(pip_lines)}')
    if pkgs and input('Reinstall Termux packages? (y/N): ').strip().lower() == 'y':
        run(['pkg', 'update', '-y'])
        for i in range(0, len(pkgs), 45):
            part = pkgs[i:i + 45]
            run(['pkg', 'install', '-y', *part])
    if pip_lines and input('Reinstall pip packages? (y/N): ').strip().lower() == 'y':
        run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel'])
        req = Path('.dedsec_requirements.txt')
        req.write_text('\n'.join(pip_lines) + '\n', encoding='utf-8')
        run([sys.executable, '-m', 'pip', 'install', '-r', str(req)])
        try:
            req.unlink()
        except Exception:
            pass

def split_file(path: Path, part_mb: int=50):
    if not path.exists():
        print('[!] Αρχείο Όχιt βρέθηκε.')
        return
    part_size = part_mb * 1024 * 1024
    with open(path, 'rb') as r:
        i = 1
        while True:
            chunk = r.read(part_size)
            if not chunk:
                break
            out = path.with_suffix(path.suffix + f'.part{i:02d}')
            with open(out, 'wb') as w:
                w.write(chunk)
            print(f'[*] Wrote {out.name} ({human_bytes(len(chunk))})')
            i += 1
    print('[*] Split ολοκληρώθηκε.')

def join_parts(base_zip: Path):
    parts = sorted(base_zip.parent.glob(base_zip.name + '.part*'))
    if not parts:
        print('[!] Όχι parts βρέθηκε.')
        return
    with open(base_zip, 'wb') as w:
        for p in parts:
            with open(p, 'rb') as r:
                shutil.copyfileobj(r, w)
            print(f'[*] Added {p.name}')
    print(f'[*] Reassembled: {base_zip}')

def verify_home_manifest():
    if not DOWNLOADS_ZIP.exists():
        print('[!] Πίσωup Όχιt βρέθηκε.')
        return
    with zipfile.ZipFile(DOWNLOADS_ZIP, 'r') as zf:
        try:
            with zf.open('meta/home_manifest_sha256.txt', 'r') as f:
                manifest = f.read().decode('utf-8', errors='ignore').splitlines()
        except Exception:
            print('[!] Όχι home manifest in Πίσωup. Enable it in config and re-Πίσωup.')
            return
    print('[*] Verifying HOME files against manifest...')
    ok = bad = missing = 0
    for line in manifest:
        line = line.strip()
        if not line:
            continue
        try:
            h, rel = line.split('  ', 1)
        except Exception:
            continue
        fp = HOME_ROOT / rel
        if not fp.exists():
            missing += 1
            continue
        try:
            data = fp.read_bytes()
            hh = hashlib.sha256(data).hexdigest()
            if hh == h:
                ok += 1
            else:
                bad += 1
        except Exception:
            bad += 1
    print(f'OK: {ok} | Changed: {bad} | Λείπει: {missing}')

def menu():
    cfg = load_config()
    while True:
        print('\n=== DedSec Backup/Restore v5 (No-Root) ===')
        print(f"Config: {CONFIG_FILE}  (mode={cfg['mode']}, caches={cfg['include_caches']}, comp={cfg['compression_level']})")
        print('1) Πίσωup using config')
        print('2) Επαναφορά FULL')
        print('3) Επαναφορά HOME-only')
        print('4) Dry LIST')
        print('5) Restore Assistant (reinstall pkgs/pip)')
        print('6) Split name_backup.zip')
        print('7) Join parts into name_backup.zip')
        print('8) Verify HOME manifest (if present)')
        print('9) Έξοδος')
        c = input('> ').strip()
        if c == '1':
            make_backup(cfg['mode'], bool(cfg['include_caches']), int(cfg['compression_level']), bool(cfg['enable_home_manifest']))
        elif c == '2':
            restore_zip('full')
        elif c == '3':
            restore_zip('home')
        elif c == '4':
            restore_zip('dry')
        elif c == '5':
            restore_assistant()
        elif c == '6':
            split_file(DOWNLOADS_ZIP, int(cfg.get('split_part_mb', 50)))
        elif c == '7':
            join_parts(DOWNLOADS_ZIP)
        elif c == '8':
            verify_home_manifest()
        elif c == '9':
            break
        else:
            print('[!] Μη έγκυρη επιλογή.')
if __name__ == '__main__':
    try:
        menu()
    except KeyboardInterrupt:
        print('\n[!] Ακυρώθηκε.')
