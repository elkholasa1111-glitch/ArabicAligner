"""Validate local documentation targets and original fixture integrity."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def main():
    files = [ROOT / 'README.md', ROOT / 'README.ar.md', *ROOT.glob('*.md'),
             *ROOT.joinpath('docs').glob('*.md'), ROOT / 'examples/README.md']
    for source in set(files):
        for target in re.findall(r'\]\(([^)]+)\)', source.read_text(encoding='utf-8')):
            if target.startswith(('https://', 'http://', '#')):
                continue
            path = (source.parent / target.split('#')[0]).resolve()
            if not path.is_relative_to(ROOT) or not path.exists():
                raise RuntimeError(f'Broken local link in {source.name}: {target}')
    manifest = json.loads((ROOT / 'examples/provenance.json').read_text(encoding='utf-8'))
    for name, info in manifest['files'].items():
        data = (ROOT / 'examples' / name).read_bytes()
        if len(data) != info['bytes'] or hashlib.sha256(data).hexdigest() != info['sha256']:
            raise RuntimeError('Fixture integrity mismatch: ' + name)
    print('Local documentation links and fixture hashes verified.')


if __name__ == '__main__':
    main()
