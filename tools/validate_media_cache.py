"""Validate an explicitly selected controlled SDK cache before installing it.

A maintainer may select an earlier trusted cache after reviewing a platform-only
build-tool change. Default builds retain the complete builder/source cache key.
"""
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_native_media import sha256


def main():
    info = json.loads((ROOT / 'native/build-info.json').read_text())
    sources = json.loads((ROOT / 'third_party/sources.lock.json').read_text())
    if info['platform'] != sys.platform or info['architecture'].lower() != platform.machine().lower():
        raise RuntimeError('Cached SDK platform mismatch')
    if any(info[name] != sources[name] for name in ('ffmpeg', 'pyav')):
        raise RuntimeError('Cached SDK corresponding-source mismatch')
    configure = info['configure']
    required = ('--enable-shared', '--disable-static', '--disable-autodetect', '--disable-gpl',
                '--disable-nonfree', '--enable-version3', '--disable-network', '--arch=x86_64')
    if not all(flag in configure for flag in required) or info['external_codec_libraries']:
        raise RuntimeError('Cached SDK configuration mismatch')
    if any(flag in configure for flag in ('--enable-gpl', '--enable-nonfree')):
        raise RuntimeError('Unexpected cached media license')
    wheels = list((ROOT / 'repaired-wheelhouse').glob('av-17.1.0-*.whl'))
    if len(wheels) != 1 or sha256(wheels[0]) != info['wheel_sha256']:
        raise RuntimeError('Cached wheel integrity mismatch')
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-deps', str(wheels[0])], check=True)
    from tools.audit_media import inspect
    inspect()
    print('Verified cached SDK source pins, platform, configuration, wheel hash and actual linked media license.')


if __name__ == '__main__':
    main()
