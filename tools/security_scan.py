"""Pinned, redacted secret scan of fetched history or a native payload."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ASSETS = {
    'win32': ('windows_x64.zip', 'd29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e'),
    'darwin': ('darwin_x64.tar.gz', 'dfe101a4db2255fc85120ac7f3d25e4342c3c20cf749f2c20a18081af1952709'),
    'linux': ('linux_x64.tar.gz', '551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb'),
}


def scan(path, report, history=False):
    directory = ROOT / '.build/gitleaks'
    directory.mkdir(parents=True, exist_ok=True)
    executable = directory / ('gitleaks.exe' if sys.platform == 'win32' else 'gitleaks')
    if not executable.exists():
        suffix, expected = ASSETS[sys.platform]
        name = 'gitleaks_8.30.1_' + suffix
        with urllib.request.urlopen('https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/' + name) as stream:
            data = stream.read()
        if hashlib.sha256(data).hexdigest() != expected:
            raise RuntimeError('Gitleaks download integrity mismatch')
        archive = directory / name
        archive.write_bytes(data)
        if suffix.endswith('.zip'):
            with zipfile.ZipFile(archive) as package:
                executable.write_bytes(package.read('gitleaks.exe'))
        else:
            with tarfile.open(archive) as package:
                executable.write_bytes(package.extractfile('gitleaks').read())
            executable.chmod(0o755)
    report = Path(report)
    report.parent.mkdir(parents=True, exist_ok=True)
    command = [str(executable), 'git' if history else 'dir', str(path), '--redact=100', '--no-banner',
               '--report-format=json', '--report-path=' + str(report), '--log-level=warn']
    if history:
        command.append('--log-opts=--all')
    # Large weight files are binary data; source/history are scanned separately.
    subprocess.run(command, check=True)
    if json.loads(report.read_text()):
        raise RuntimeError('Review redacted secret findings before publication')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--history', action='store_true')
    args = parser.parse_args()
    scan(args.path, args.report, args.history)
