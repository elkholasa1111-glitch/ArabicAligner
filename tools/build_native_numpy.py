"""Build NumPy without opaque, statically linked GNU numerical runtimes.

macOS uses system Accelerate (13.3+); Windows uses NumPy's built-in numerical
fallback. CTranslate2 inference retains its own CPU kernels and model choices.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_native_media import fetch_source, sha256


def main():
    directory = ROOT / 'native-numpy'
    directory.mkdir(exist_ok=True)
    item = json.loads((ROOT / 'third_party/sources.lock.json').read_text())['numpy']
    existing = list(directory.glob('numpy-1.26.4-*.whl'))
    info = directory / 'build-info.json'
    if not existing:
        source = fetch_source('numpy', item)
        env = os.environ.copy()
        blas = 'accelerate' if sys.platform == 'darwin' else 'none'
        if sys.platform == 'darwin':
            env.update({'MACOSX_DEPLOYMENT_TARGET': '13.3', 'ARCHFLAGS': '-arch x86_64',
                        '_PYTHON_HOST_PLATFORM': 'macosx-13.3-x86_64'})
        command = [sys.executable, '-m', 'pip', 'wheel', '--no-deps', '--use-pep517', '--wheel-dir', str(directory),
                   '--config-settings=setup-args=-Dblas=' + blas,
                   '--config-settings=setup-args=-Dlapack=' + blas, str(source)]
        subprocess.run(command, check=True, env=env)
        wheel = next(directory.glob('numpy-1.26.4-*.whl'))
        info.write_text(json.dumps({'source': item, 'platform': sys.platform, 'blas': blas,
                                   'command': command, 'wheel_sha256': sha256(wheel)}, indent=2))
    else:
        wheel = existing[0]
    metadata = json.loads(info.read_text())
    if metadata['source'] != item or metadata['platform'] != sys.platform or sha256(wheel) != metadata['wheel_sha256']:
        raise RuntimeError('Controlled NumPy cache mismatch')
    with zipfile.ZipFile(wheel) as package:
        if any(any(name in path.lower() for name in ('gfortran', 'quadmath', 'libgcc', 'openblas'))
               for path in package.namelist() if path.endswith(('.dll', '.dylib', '.so'))):
            raise RuntimeError('Unexpected numerical runtime in controlled NumPy wheel')
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-deps', '--force-reinstall', str(wheel)], check=True)
    subprocess.run([sys.executable, '-c',
        "import numpy as n; assert n.__version__=='1.26.4'; assert (n.array([[1.,2.]]) @ n.array([[3.],[4.]]))[0,0]==11.; n.linalg.svd(n.eye(3)); print(n.__config__.show(mode='dicts'))"], check=True)


if __name__ == '__main__':
    main()
