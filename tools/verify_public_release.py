"""Stream public downloads without authentication and verify their full hashes."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import struct
import time
import urllib.request

REPO = 'elkholasa1111-glitch/ArabicAligner'


def request(url):
    # No GitHub token, cookie jar, credential helper or signed-in browser.
    return urllib.request.urlopen(urllib.request.Request(url, headers={
        'User-Agent': 'ArabicAligner-anonymous-release-verification'}), timeout=90)


def get_json(path):
    with request('https://api.github.com/repos/' + REPO + '/' + path) as stream:
        return json.load(stream)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tag', required=True)
    parser.add_argument('--expected-commit', required=True)
    parser.add_argument('--output', default='verification/public-download-verification.json')
    args = parser.parse_args()
    if not re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+(?:-[a-zA-Z0-9.-]+)?', args.tag):
        raise ValueError('Expected a version tag')
    if not re.fullmatch(r'[a-f0-9]{40}', args.expected_commit):
        raise ValueError('Expected a full reviewed source commit')
    release = get_json('releases/tags/' + args.tag)
    assert not release['draft']
    assert get_json('git/ref/tags/' + args.tag)['object']['sha'] == args.expected_commit
    assets = {x['name']: x for x in release['assets']}
    expected = {}
    for name in ('SHA256SUMS-win32.txt', 'SHA256SUMS-darwin.txt'):
        with request(assets[name]['browser_download_url']) as stream:
            for line in stream.read().decode().splitlines():
                digest, filename = line.split('  ', 1)
                if filename in expected and expected[filename] != digest:
                    raise RuntimeError('Platform manifest disagreement: ' + filename)
                expected[filename] = digest
    names = sorted(name for name in assets if name.endswith(('_Setup.exe', '_Intel.dmg')))
    assert len(names) == 2

    def verify(name):
        asset, digest, count = assets[name], hashlib.sha256(), 0
        header = b''
        with request(asset['browser_download_url']) as stream:
            status = stream.status
            while chunk := stream.read(1024 * 1024):
                if not header:
                    header = chunk[:4096]
                digest.update(chunk)
                count += len(chunk)
        actual = digest.hexdigest()
        assert status == 200 and count == asset['size'] and actual == expected[name]
        if asset.get('digest'):
            assert asset['digest'] == 'sha256:' + actual
        result = {'name': name, 'url': asset['browser_download_url'], 'http_status': status,
                  'bytes': count, 'sha256': actual, 'authenticated': False}
        if name.endswith('.exe'):
            assert header[:2] == b'MZ'
            pe = struct.unpack_from('<I', header, 0x3c)[0]
            assert header[pe:pe + 4] == b'PE\0\0'
            optional = pe + 24
            magic = struct.unpack_from('<H', header, optional)[0]
            directories = optional + (96 if magic == 0x10b else 112)
            certificate_offset, certificate_size = struct.unpack_from('<II', header, directories + 4 * 8)
            result['authenticode_attached_certificate'] = bool(certificate_offset or certificate_size)
            assert not result['authenticode_attached_certificate'], 'Review unexpected signing state'
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        binaries = list(pool.map(verify, names))
    documents = []
    for name in ('README.md', 'README.ar.md'):
        url = 'https://raw.githubusercontent.com/' + REPO + '/main/' + name
        with request(url) as stream:
            assert stream.status == 200 and len(stream.read()) > 100
            documents.append({'url': url, 'status': stream.status})
    result = {'date_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'repo': REPO, 'tag': args.tag, 'source_commit': args.expected_commit,
        'release_url': release['html_url'], 'published_at': release['published_at'],
        'authenticated': False, 'method': 'Full HTTP response streamed into SHA-256, not only HEAD or metadata',
        'binaries': binaries, 'documents': documents,
        'download_accounting': 'These verification downloads are our own, not independent adoption.'}
    source_record = Path(__file__).resolve().parents[1] / 'docs/release-source-equivalence.json'
    if source_record.is_file():
        record = json.loads(source_record.read_text(encoding='utf-8'))
        if record['release_tag'] == args.tag:
            assert record['public_release_tag_commit'] == args.expected_commit
            assert record['runtime_build_fixture_and_third_party_blobs_unchanged']
            for binary in binaries:
                assert record['package_sha256'][binary['name']] == binary['sha256']
            result['native_build_record_commit'] = record['native_build_record_commit']
            result['source_inventory_sha256'] = record['file_inventory_sha256']
            result['source_record_url'] = ('https://github.com/' + REPO +
                '/blob/main/docs/SOURCE-RECORD.md')
            result['packages_rebuilt_during_metadata_normalization'] = False
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
