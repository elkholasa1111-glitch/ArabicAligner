"""Inspect actual packaged files, architectures and licenses before shipping."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys


def inspect(root):
    root = Path(root)
    files, native, notices = [], [], []
    forbidden = ('Qt6Pdf', 'QtPdf', 'Qt6Svg', 'QtSvg', 'Qt6Qml', 'QtQml', 'Qt6Quick', 'QtQuick',
                 'Qt6VirtualKeyboard', 'QtVirtualKeyboard', 'libx264', 'libx265', 'speech-sample.wav')
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root).as_posix()
        if any(name in relative for name in forbidden) or path.suffix.lower() in ('.key', '.pfx', '.p12'):
            raise RuntimeError('Unexpected payload component: ' + relative)
        if path.suffix.lower() == '.pem':
            import certifi
            data = path.read_bytes()
            if path.name != 'cacert.pem' or data != Path(certifi.where()).read_bytes() or b'PRIVATE KEY' in data:
                raise RuntimeError('Unreviewed PEM payload: ' + relative)
        files.append({'path': relative, 'bytes': path.stat().st_size})
        if any(x in path.name.upper() for x in ('LICENSE', 'COPYING', 'NOTICE')):
            notices.append({'path': relative, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        if sys.platform == 'win32' and path.suffix.lower() in ('.dll', '.exe', '.pyd'):
            with path.open('rb') as stream:
                if stream.read(2) != b'MZ':
                    continue
                stream.seek(0x3c)
                stream.seek(struct.unpack('<I', stream.read(4))[0] + 4)
                machine = struct.unpack('<H', stream.read(2))[0]
                if machine != 0x8664:
                    raise RuntimeError('Non-x64 PE file: ' + relative)
            native.append({'path': relative, 'machine': 'AMD64'})
        elif sys.platform == 'darwin' and (path.suffix in ('.dylib', '.so') or path.name in ('ArabicAligner', 'ffmpeg') or '.framework/' in relative):
            description = subprocess.check_output(['/usr/bin/file', str(path)], text=True).strip().split(': ', 1)[-1]
            if 'Mach-O' in description:
                if 'x86_64' not in description:
                    raise RuntimeError('Native dependency missing Intel slice: ' + relative)
                native.append({'path': relative, 'architecture': description})
    if not notices or not native:
        raise RuntimeError('Missing native or license inventory')
    return {'platform': sys.platform, 'architecture': 'x86_64', 'files': files, 'native_files': native,
            'license_files': notices, 'forbidden_components_absent': True}


if __name__ == '__main__':
    print(json.dumps(inspect(sys.argv[1]), indent=2))
