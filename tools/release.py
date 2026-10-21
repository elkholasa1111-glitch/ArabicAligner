"""Native packaging and installed-copy acceptance. Run intentionally, not on PRs."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.version import APP_VERSION
from tools.build_native_media import sha256


def run(args, env=None):
    print('+ ' + ' '.join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=ROOT, env=env, check=True, timeout=3600)


def accept(executable, reports, work):
    env = os.environ.copy()
    home = work / 'empty-home'
    home.mkdir(parents=True)
    env.update({'HOME': str(home), 'HF_HOME': str(home / 'hf'), 'HF_HUB_CACHE': str(home / 'hf/hub'),
                'HF_HUB_OFFLINE': '1', 'HF_HUB_DISABLE_TELEMETRY': '1'})
    if sys.platform == 'win32':
        env.update({'USERPROFILE': str(home), 'LOCALAPPDATA': str(home / 'AppData/Local'),
                    'APPDATA': str(home / 'AppData/Roaming')})
    # Establish that the test endpoint is reachable before restricting the app.
    with socket.create_connection(('1.1.1.1', 443), timeout=10):
        pass
    if sys.platform == 'darwin':
        env['PATH'] = '/usr/bin:/bin:/usr/sbin:/sbin'
        env['QT_QPA_PLATFORM'] = 'cocoa'
        prefix = ['/usr/bin/sandbox-exec', '-p', '(version 1)(allow default)(deny network*)']
    else:
        # This rule applies only to this test's installed executable.
        rule = 'ArabicAligner-Release-' + str(os.getpid())
        run(['powershell', '-NoProfile', '-File', ROOT / 'tools/test_firewall.ps1',
             '-Name', rule, '-Program', executable])
        prefix = []
    try:
        run([*prefix, executable, '--acceptance-test', '--examples', ROOT / 'examples', '--report', reports / 'gui.json',
             '--work-dir', work / 'processing', '--expect-network-blocked'], env)
        result = json.loads((reports / 'gui.json').read_text(encoding='utf-8'))
        if not result['ok'] or not result['network_os_enforced']:
            raise RuntimeError('Installed GUI acceptance failed')
        for example in ('msa', 'egyptian'):
            output = reports / f'cli-{example}.srt'
            run([*prefix, executable, '--cli', '-a', ROOT / 'examples' / f'{example}.wav', '-t',
                 ROOT / 'examples' / f'{example}.txt', '-o', output, '--model', 'small'], env)
            if not output.is_file() or '-->' not in output.read_text(encoding='utf-8-sig'):
                raise RuntimeError('Frozen CLI did not produce SRT')
        # A second process proves reopening with native Qt and model resolution.
        run([*prefix, executable, '--self-test', '--native-gui', '--report', reports / 'restart.json'], env)
        if not json.loads((reports / 'restart.json').read_text())['ok']:
            raise RuntimeError('Restart acceptance failed')
        if any((home / 'hf').rglob('model.bin')):
            raise RuntimeError('Acceptance unexpectedly populated a home model cache')
        # Open the actual output in the platform text editor, then close only our process.
        command = (['/System/Applications/TextEdit.app/Contents/MacOS/TextEdit'] if sys.platform == 'darwin'
                   else ['notepad.exe'])
        editor = subprocess.Popen([*command, str(reports / 'cli-msa.srt')])
        time.sleep(3)
        editor_opened = editor.poll() is None
        if editor_opened:
            editor.terminate()
            editor.wait(timeout=20)
        result['editor_process_observed'] = editor_opened
        result['empty_cache_after_test'] = True
        result['os_isolation'] = 'sandbox-exec deny network*' if sys.platform == 'darwin' else 'Windows outbound application firewall rule'
        (reports / 'installed-summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    finally:
        for log in home.rglob('ArabicAligner.log'):
            shutil.copy2(log, reports / 'runtime.log')
        if sys.platform == 'win32':
            run(['powershell', '-NoProfile', '-File', ROOT / 'tools/test_firewall.ps1', '-Name', rule, '-Remove'])


def main():
    if platform.machine().lower() not in ('amd64', 'x86_64') or sys.platform not in ('win32', 'darwin'):
        raise SystemExit('Use native Windows x64 or macOS Intel.')
    output = ROOT / 'release'
    output.mkdir(exist_ok=True)
    reports = ROOT / 'verification' / ('macos-intel' if sys.platform == 'darwin' else 'windows-x64')
    reports.mkdir(parents=True, exist_ok=True)
    environment = {'date_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                   'platform': platform.platform(), 'machine': platform.machine(), 'python': sys.version,
                   'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()}
    (reports / 'environment.json').write_text(json.dumps(environment, indent=2))
    (reports / 'dependencies.txt').write_text(subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True))
    run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
    run([sys.executable, 'tools/check_source.py'])
    run([sys.executable, 'tools/audit_media.py'])
    spec = 'ArabicAligner-macos.spec' if sys.platform == 'darwin' else 'ArabicAligner.spec'
    run([sys.executable, '-m', 'PyInstaller', spec, '--noconfirm', '--clean'])
    from tools.payload_inventory import inspect
    payload = ROOT / ('dist/ArabicAligner Preview.app' if sys.platform == 'darwin' else 'dist/ArabicAligner')
    (reports / 'payload.json').write_text(json.dumps(inspect(payload), indent=2))
    from tools.security_scan import scan
    scan(payload, reports / 'gitleaks-payload.json')
    stem = 'ArabicAligner_' + APP_VERSION
    if sys.platform == 'darwin':
        bundle = ROOT / 'dist/ArabicAligner Preview.app'
        dmg = output / f'{stem}_macOS_Intel.dmg'
        with tempfile.TemporaryDirectory(prefix='arabicaligner-dmg-') as temp:
            stage = Path(temp) / 'image'
            stage.mkdir()
            run(['/usr/bin/ditto', bundle, stage / bundle.name])
            (stage / 'Applications').symlink_to('/Applications', target_is_directory=True)
            shutil.copy2(ROOT / 'README.ar.md', stage / 'INSTALL.md')
            run(['/usr/bin/hdiutil', 'create', '-volname', 'ArabicAligner Preview', '-srcfolder', stage,
                 '-ov', '-format', 'UDZO', dmg])
            mount = Path(temp) / 'mount'
            mount.mkdir()
            run(['/usr/bin/hdiutil', 'attach', '-readonly', '-nobrowse', '-mountpoint', mount, dmg])
            try:
                installed = Path(temp) / 'Arabic install تجربة' / bundle.name
                installed.parent.mkdir()
                run(['/usr/bin/ditto', mount / bundle.name, installed])
                accept(installed / 'Contents/MacOS/ArabicAligner', reports, Path(temp) / 'acceptance')
                run(['/usr/bin/codesign', '--verify', '--deep', '--strict', installed])
                (reports / 'signature.txt').write_text(subprocess.check_output(
                    ['/usr/bin/codesign', '-dv', '--verbose=2', str(installed)], stderr=subprocess.STDOUT, text=True))
            finally:
                run(['/usr/bin/hdiutil', 'detach', mount])
    else:
        iscc = shutil.which('ISCC.exe') or r'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
        run([iscc, 'installer.iss'])
        setup = output / f'{stem}_Windows_x64_Setup.exe'
        with tempfile.TemporaryDirectory(prefix='arabicaligner-installed-') as temp:
            installed = Path(temp) / 'Arabic install تجربة'
            run([setup, '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/VERIFICATION=1', '/DIR=' + str(installed)])
            try:
                accept(installed / 'ArabicAligner.exe', reports, Path(temp) / 'acceptance')
            finally:
                if (installed / 'unins000.exe').exists():
                    run([installed / 'unins000.exe', '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART'])
        (reports / 'signature.txt').write_text('Unsigned: no Authenticode certificate used.\n')
    shutil.copy2(ROOT / 'native/build-info.json', reports / 'native-build.json')
    shutil.copy2(ROOT / 'native-numpy/build-info.json', reports / 'numpy-build.json')
    shutil.copy2(ROOT / 'native-ctranslate2/build-info.json', reports / 'ctranslate2-build.json')
    for archive in (ROOT / 'native-ctranslate2').glob('*source*.tar.gz'):
        shutil.copy2(archive, output / archive.name)
    shutil.make_archive(str(output / ('verification-' + sys.platform)), 'zip', reports)
    # Mirror exact corresponding sources. Heavy files are release assets, never Git objects.
    items = json.loads((ROOT / 'third_party/sources.lock.json').read_text())
    for name, item in items.items():
        if item.get('platforms') and sys.platform not in item['platforms']:
            continue
        destination = output / item['url'].rsplit('/', 1)[1]
        cached = ROOT / '.build/sources' / destination.name
        if cached.exists():
            shutil.copy2(cached, destination)
        elif not destination.exists():
            with urllib.request.urlopen(item['url'], timeout=120) as source, destination.open('wb') as target:
                shutil.copyfileobj(source, target)
        if sha256(destination) != item['sha256']:
            raise RuntimeError('Corresponding source hash mismatch: ' + name)
    checksums = []
    for path in sorted(output.iterdir()):
        if path.is_file() and not path.name.startswith('SHA256SUMS'):
            if path.stat().st_size >= 2 * 1024**3:
                raise RuntimeError('Release asset exceeds GitHub 2 GiB limit: ' + path.name)
            checksums.append(sha256(path) + '  ' + path.name)
    (output / ('SHA256SUMS-' + sys.platform + '.txt')).write_text('\n'.join(checksums) + '\n')


if __name__ == '__main__':
    main()
