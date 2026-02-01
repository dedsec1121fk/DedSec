import os
import shutil
import subprocess
import sys
from pathlib import Path
MIRROR_TEST_URLS = ['https://packages.termux.dev/apt/termux-main/dists/stable/Release', 'https://grimler.se/termux-packages-24/dists/stable/Release', 'https://termux.mentality.rip/termux-main/dists/stable/Release']

def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None

def run(cmd, check=False, capture=False):
    print(f"\n$ {' '.join(cmd)}")
    try:
        if capture:
            p = subprocess.run(cmd, capture_output=True, text=True)
            return (p.returncode, p.stdout or '', p.stderr or '')
        else:
            p = subprocess.run(cmd, check=check)
            return (p.returncode, '', '')
    except Exception as e:
        return (1, '', str(e))

def header(title):
    print('\n' + '=' * 56)
    print(title)
    print('=' * 56)

def ensure_pkg():
    if not have('pkg'):
        print("[!] 'pkg' not found. Run inside Termux.")
        return False
    return True

def pkg_install(pkgs):
    if not ensure_pkg():
        return
    if isinstance(pkgs, str):
        pkgs = [pkgs]
    run(['pkg', 'install', '-y', *pkgs], check=False)

def ensure_tool(cmd: str, pkg_name: str):
    if not have(cmd):
        print(f'[*] Λείπει: {cmd} -> Εγκατάστασηing {pkg_name}')
        pkg_install(pkg_name)

def ensure_python_pip():
    header('Ensure Python + Pip')
    pkg_install('python')
    run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel'], check=False)

def ensure_pip_pkg(py_pkg: str):
    try:
        __import__(py_pkg)
        print(f'[*] Python dep OK: {py_pkg}')
        return
    except Exception:
        pass
    print(f'[*] Installing python dep: {py_pkg}')
    run([sys.executable, '-m', 'pip', 'install', '--upgrade', py_pkg], check=False)

def info():
    header('System Πληροφορίες')
    print(f'Python : {sys.version.split()[0]}')
    print(f"HOME   : {os.environ.get('HOME')}")
    print(f"PREFIX : {os.environ.get('PREFIX')}")
    print(f"SHELL  : {os.environ.get('SHELL')}")
    print(f"Διαδρομή   : {os.environ.get('PATH')}")
    print('Logs (if using launcher): ~/DedSec/logs')
    ensure_tool('termux-info', 'termux-tools')
    if have('termux-info'):
        run(['termux-info'], check=False)

def doctor():
    header('Doctor Έλεγχοςs')
    ensure_tool('curl', 'curl')
    ensure_tool('ca-certificates', 'ca-certificates')
    ensure_tool('openssl', 'openssl')
    ensure_tool('termux-change-repo', 'termux-tools')
    info()
    print('\nTools:')
    for t in ['pkg', 'apt', 'dpkg', 'curl', 'python', 'pip', 'git', 'openssl', 'wget', 'termux-change-repo']:
        print(f" - {t:18}: {('OK' if have(t) else 'MISSING')}")
    print('\nFree space (Termux root):')
    try:
        usage = shutil.disk_usage('/data/data/com.termux/files')
        gb = 1024 ** 3
        print(f' - Total: {usage.total / gb:.2f} GB')
        print(f' - Free : {usage.free / gb:.2f} GB')
    except Exception as e:
        print(f' - Could Όχιt read disk usage: {e}')
    header('Δίκτυο quick test')
    if have('ping'):
        run(['ping', '-c', '1', '1.1.1.1'], check=False)
        run(['ping', '-c', '1', 'google.com'], check=False)
    if have('curl'):
        run(['curl', '-I', '-L', '--max-time', '10', 'https://example.com'], check=False)

def mirror_test():
    header('Mirror Quick Test')
    ensure_tool('curl', 'curl')
    for url in MIRROR_TEST_URLS:
        run(['curl', '-I', '--max-time', '10', '-L', url], check=False)

def setup_storage():
    header('Αποθήκευση Setup')
    ensure_tool('termux-setup-storage', 'termux-tools')
    if Path('/storage/emulated/0').exists():
        print('[*] Αποθήκευση already accessible.')
        return
    run(['termux-setup-storage'], check=False)

def update_upgrade():
    header('Update/Upgrade')
    run(['pkg', 'update', '-y'], check=False)
    run(['pkg', 'upgrade', '-y'], check=False)

def fix_broken():
    header('Fix Broken Packages')
    run(['apt', '--fix-broken', 'install', '-y'], check=False)
    run(['dpkg', '--configure', '-a'], check=False)

def reset_lists_and_clean():
    header('Reset Lists + Clean Cache')
    run(['apt', 'clean'], check=False)
    lists = Path(os.environ.get('PREFIX', '/data/data/com.termux/files/usr')) / 'var/lib/apt/lists'
    if lists.exists():
        for p in lists.glob('*'):
            if p.is_file():
                try:
                    p.unlink()
                except Exception:
                    pass
        print(f'[*] Removed apt lists in {lists}')
    run(['pkg', 'update', '-y'], check=False)

def fix_releaseinfo_change():
    header('Fix: Release πληροφορίες changed')
    run(['apt-get', 'update', '--allow-releaseinfo-change'], check=False)

def fix_hash_sum_mismatch():
    header('Fix: Hash Sum mismatch')
    reset_lists_and_clean()
    run(['pkg', 'update', '-y'], check=False)

def fix_tls_cert_issues():
    header('Fix: TLS/Certificate issues')
    pkg_install(['ca-certificates', 'openssl'])
    run(['pkg', 'update', '-y'], check=False)

def clean_deb_cache():
    header('Clean .deb cache')
    prefix = Path(os.environ.get('PREFIX', '/data/data/com.termux/files/usr'))
    archives = prefix / 'var/cache/apt/archives'
    removed = 0
    if archives.exists():
        for p in archives.glob('*.deb'):
            try:
                p.unlink()
                removed += 1
            except Exception:
                pass
    print(f'[*] Αφαιρέθηκε {removed} .deb files.')

def clean_pip_cache():
    header('Clean pip cache')
    ensure_python_pip()
    run([sys.executable, '-m', 'pip', 'cache', 'purge'], check=False)

def install_basics():
    header('Εγκατάσταση Basics')
    pkg_install(['git', 'curl', 'wget', 'openssl', 'ca-certificates', 'nano', 'unzip', 'tar', 'termux-tools'])

def pip_repair():
    header('Pip Repair')
    ensure_python_pip()
    run([sys.executable, '-m', 'pip', 'install', '--upgrade', '--force-reinstall', 'pip', 'setuptools', 'wheel'], check=False)
    print('If pip fails to download: try switching network or disabling Private DNS temporarily.')

def python_deps_check():
    header('Python deps check')
    ensure_python_pip()
    ensure_pip_pkg('requests')
    ensure_pip_pkg('colorama')

def repo_helper():
    header('Repo Βοήθειαer')
    ensure_tool('termux-change-repo', 'termux-tools')
    if have('termux-change-repo'):
        run(['termux-change-repo'], check=False)

def fix_home_permissions():
    header('Fix $HOME Άδειες (user files only)')
    home = Path(os.environ.get('HOME', str(Path.home())))
    if not home.exists():
        print('[!] HOME Όχιt βρέθηκε.')
        return
    count = 0
    for p in home.rglob('*'):
        try:
            if p.is_symlink():
                continue
            if home / 'storage' in p.parents or p == home / 'storage':
                continue
            if p.is_dir():
                p.chmod(448)
            elif p.is_file():
                p.chmod(384)
            count += 1
        except Exception:
            continue
    print(f'[*] Έτοιμο. Ενημέρωσηd {count} items.')

def fix_shell_path():
    header('Shell/PATH Fixer (safe)')
    home = Path(os.environ.get('HOME', str(Path.home())))
    shells = [home / '.bashrc', home / '.zshrc', home / '.profile']
    line = 'export PATH="$PREFIX/bin:$PATH"'
    for shf in shells:
        try:
            if not shf.exists():
                continue
            txt = shf.read_text(encoding='utf-8', errors='ignore').splitlines()
            if any((line in x for x in txt)):
                continue
            txt += ['', '# DedSec Repair Wizard: ensure Termux PATH', line]
            shf.write_text('\n'.join(txt) + '\n', encoding='utf-8')
            print(f'[*] Ενημέρωσηd: {shf.name}')
        except Exception as e:
            print(f'[!] Could Όχιt Ενημέρωση {shf}: {e}')
    print('[*] Restart Termux to apply PATH changes.')

def full_repair_sequence():
    header('Full Επιδιόρθωση Sequence (Όχι Root)')
    setup_storage()
    update_upgrade()
    fix_broken()
    reset_lists_and_clean()
    install_basics()
    ensure_python_pip()
    python_deps_check()
    print('[*] Full Επιδιόρθωση Έτοιμο.')

def menu():
    if not ensure_pkg():
        return
    while True:
        print('\n=== DedSec Termux Repair Wizard v5 (No-Root) ===')
        print('1) Doctor (diagΌχιse)')
        print('2) Mirror quick test')
        print('3) Setup αποθήκευση άδεια')
        print('4) Ενημέρωση + Αναβάθμιση')
        print('5) Fix broken packages')
        print('6) Reset apt lists + clean cache')
        print('7) Fix: Release πληροφορίες changed')
        print('8) Fix: Hash Sum mismatch')
        print('9) Fix: TLS/Certificate issues')
        print('10) Clean .deb cache')
        print('11) Clean pip cache')
        print('12) Εγκατάσταση basics')
        print('13) Ensure Python + pip')
        print('14) Pip repair')
        print('15) Python deps check (requests/colorama)')
        print('16) Repo helper (termux-change-repo)')
        print('17) Fix $HOME άδειες')
        print('18) Shell/PATH fixer')
        print('19) Εκτέλεση FULL Επιδιόρθωση sequence')
        print('0) Έξοδος')
        c = input('> ').strip()
        if c == '1':
            doctor()
        elif c == '2':
            mirror_test()
        elif c == '3':
            setup_storage()
        elif c == '4':
            update_upgrade()
        elif c == '5':
            fix_broken()
        elif c == '6':
            reset_lists_and_clean()
        elif c == '7':
            fix_releaseinfo_change()
        elif c == '8':
            fix_hash_sum_mismatch()
        elif c == '9':
            fix_tls_cert_issues()
        elif c == '10':
            clean_deb_cache()
        elif c == '11':
            clean_pip_cache()
        elif c == '12':
            install_basics()
        elif c == '13':
            ensure_python_pip()
        elif c == '14':
            pip_repair()
        elif c == '15':
            python_deps_check()
        elif c == '16':
            repo_helper()
        elif c == '17':
            fix_home_permissions()
        elif c == '18':
            fix_shell_path()
        elif c == '19':
            full_repair_sequence()
        elif c == '0':
            break
        else:
            print('[!] Μη έγκυρη επιλογή.')
if __name__ == '__main__':
    try:
        menu()
    except KeyboardInterrupt:
        print('\n[!] Ακυρώθηκε.')
