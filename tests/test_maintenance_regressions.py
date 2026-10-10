"""No-install regressions for the first-run legal gate and Ubuntu QA repairs."""
from pathlib import Path
import os
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
LEGAL=ROOT/'Compat'/'legal_consent.sh'


def _env(home):
    env=os.environ.copy()
    env['HOME']=str(home)
    env.pop('TERMUX_VERSION', None)
    env['PREFIX']='/usr/local'
    return env


def _legal(home, answer):
    shell=f'ROOT_DIR={str(ROOT)!r}; source "{LEGAL}"; dedsec_require_legal_acceptance'
    return subprocess.run(['bash','-c',shell], input=answer, text=True, capture_output=True,env=_env(home),timeout=20)


def test_declining_terms_stops_without_state(tmp_path):
    h=tmp_path/'isolated-home';h.mkdir()
    result=_legal(h,'n\n')
    assert result.returncode != 0
    assert 'Declined' in result.stdout
    assert not (h/'.local').exists()
    assert not (h/'.dedsec').exists()


def test_missing_input_fails_closed(tmp_path):
    result=_legal(tmp_path,'')
    assert result.returncode != 0
    assert not (tmp_path/'.local').exists()


def test_accept_and_repeat_without_prompt(tmp_path):
    accepted=_legal(tmp_path,'y\n')
    assert accepted.returncode==0,accepted.stdout+accepted.stderr
    marker=tmp_path/'.local/state/dedsec/legal-acceptance-v1.txt'
    assert marker.is_file() and marker.read_text().strip()
    repeated=_legal(tmp_path,'')
    assert repeated.returncode==0
    assert 'Previously accepted' in repeated.stdout
    assert 'Legal choice' not in repeated.stdout


def test_enter_means_accept(tmp_path):
    response=_legal(tmp_path,'\n')
    assert response.returncode==0


def test_read_english_and_greek_then_decline(tmp_path):
    response=_legal(tmp_path,'r\nre\nrg\nn\n')
    assert response.returncode!=0
    assert 'English Version.txt' in response.stdout
    assert 'Greek Version.txt' in response.stdout
    assert 'Declined' in response.stdout
    assert not (tmp_path/'.local').exists()


def test_setup_stops_before_any_side_effect_on_n(tmp_path):
    h=tmp_path/'fresh';h.mkdir()
    command=['bash',str(ROOT/'Setup.sh'),'--skip-system-update','--required-only','--no-run']
    result=subprocess.run(command,input='n\n',env=_env(h),text=True,capture_output=True,timeout=20)
    assert result.returncode!=0
    assert 'Declined' in result.stdout
    assert not (h/'.dedsec').exists()
    assert not (h/'.local').exists()


def test_direct_termux_setup_stops_before_install_on_n(tmp_path):
    h=tmp_path/'fresh';h.mkdir()
    command=['bash',str(ROOT/'Setup-Termux.sh'),'--skip-system-update','--no-run']
    result=subprocess.run(command,input='n\n',env=_env(h),text=True,capture_output=True,timeout=20)
    assert result.returncode!=0
    assert 'Declined' in result.stdout
    assert not (h/'.dedsec').exists()


def test_legal_files_present():
    doc=ROOT/'Important Documents'
    for lang in ('English','Greek'):
        assert (doc/f'Legal Disclaimer {lang} Version.docx').stat().st_size>1000
        assert (doc/f'Legal Disclaimer {lang} Version.txt').stat().st_size>1000


def test_maintenance_files_and_source_guards():
    doc=ROOT/'Important Documents'
    assert (doc/'DEDSEC_FULL_MAINTENANCE_HANDBOOK_EN.md').stat().st_size>10000
    assert (doc/'DEDSEC_ΟΔΗΓΟΣ_ΣΥΝΤΗΡΗΣΗΣ_GR.md').stat().st_size>2000
    assert (doc/'UBUNTU_QA_REPAIR_TRACKER.md').stat().st_size>2000
    setup=(ROOT/'Setup.sh').read_text()
    assert setup.index('dedsec_require_legal_acceptance')<setup.index('APT=(apt-get)')
    assert '--configure-menu-autostart' in setup
    source=(ROOT/'Scripts/Settings.py').read_text()
    assert 'def _save_desktop_project_local' in source
    assert 'def update_dedsec_source_2' in source
    assert 'def save_project' in source
    assert '--configure-menu-autostart' in source
    assert 'proWordSavedRange' in source
    assert "GAMES.active==='g2048'" in source
    termux=(ROOT/'Setup-Termux.sh').read_text()
    assert termux.index('dedsec_require_legal_acceptance')<termux.index('if [ "$SKIP_REPOSITORY_REFRESH"')


def test_buzz_syntax_and_cfg_scope():
    import ast
    s=(ROOT/'Scripts/Games/Buzz.py').read_text()
    tree=ast.parse(s)
    quiz=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=='mode_buzz_choice']
    assert quiz
    assert 'cfg' in [n.id for n in ast.walk(quiz[0]) if isinstance(n,ast.Name)]
    assert not any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='rounds' for t in n.targets) for n in tree.body)


def test_bilingual_edition_shared_runtime_is_synchronized():
    """The Greek edition ships the same auto-translating Settings and ButSystem runtime."""
    for name in ('Settings.py', 'ButSystem.py'):
        assert (ROOT/'Scripts'/name).read_bytes() == (ROOT/'Scripts'/'Ελληνική Έκδοση'/name).read_bytes()


def test_unsupported_scripts_return_to_menu():
    code=(ROOT/'Scripts/Settings.py').read_text()
    for menu in ('run_list_menu', 'run_number_menu', 'run_grid_menu'):
        segment=code.split(f'def {menu}():',1)[1].split('\ndef ',1)[0]
        assert 'if retcode == 126:' in segment
        assert 'continue' in segment.split('if retcode == 126:',1)[1].split('\n',2)[1]
