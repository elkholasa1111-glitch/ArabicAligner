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
    result = subprocess.run(command)
    if result.returncode not in (0, 1):
        raise RuntimeError('Gitleaks did not finish successfully')
    findings = json.loads(report.read_text())
    reviewed, unresolved = [], []
    for finding in findings:
        source = Path(finding['File'])
        # Reviewed against Microsoft v1.23.2 upstream: this line assigns the
        # public enum onnx.TensorProto.INT64 to map_key_type, not a credential.
        known_enum = (not history and finding['RuleID'] == 'generic-api-key'
            and finding['StartLine'] == 2198 and finding['EndLine'] == 2198
            and source.as_posix().endswith('/onnxruntime/tools/symbolic_shape_infer.py')
            and hashlib.sha256(source.read_text(encoding='utf-8').encode()).hexdigest()
                == '869c5b3247775d201751f72e989b66ae5deec58fb5dd65094f5533400d52051e')
        if known_enum:
            reviewed.append({'rule': finding['RuleID'], 'file': 'onnxruntime/tools/symbolic_shape_infer.py',
                'line': 2198, 'classification': 'false positive: public ONNX tensor enum',
                'upstream': 'https://github.com/microsoft/onnxruntime/blob/v1.23.2/onnxruntime/python/tools/symbolic_shape_infer.py'})
        else:
            unresolved.append(finding)
    report.with_name(report.stem + '-review.json').write_text(json.dumps({
        'raw_findings': len(findings), 'reviewed_false_positives': reviewed,
        'unresolved_findings': len(unresolved)}, indent=2))
    if unresolved:
        raise RuntimeError('Review redacted secret findings before publication')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--history', action='store_true')
    args = parser.parse_args()
    scan(args.path, args.report, args.history)
