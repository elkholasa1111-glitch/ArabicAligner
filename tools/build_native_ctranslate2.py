"""Build the existing CTranslate2 version with open CPU math backends."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_native_media import sha256


def run(command, cwd=ROOT, env=None):
    print('+ ' + ' '.join(map(str, command)), flush=True)
    subprocess.run(list(map(str, command)), cwd=cwd, env=env, check=True)


def main():
    item = json.loads((ROOT / 'third_party/ctranslate2.lock.json').read_text())
    directory = ROOT / 'native-ctranslate2'
    directory.mkdir(exist_ok=True)
    wheels = directory / 'wheels'
    wheels.mkdir(exist_ok=True)
    repaired = directory / 'repaired'
    existing = list(repaired.glob('ctranslate2-4.8.2-*.whl'))
    info = directory / 'build-info.json'
    env = os.environ.copy()
    patch = ROOT / 'third_party/patches/ctranslate2-windows-ruy-teardown.patch'
    expected_patch = sha256(patch) if sys.platform == 'win32' else None
    if not existing:
        source = ROOT / '.build/ctranslate2-source'
        if not source.exists():
            run(['git', '-c', 'credential.helper=', 'clone', '--no-checkout', '--filter=blob:none', item['repo'], source])
        run(['git', 'config', 'core.autocrlf', 'false'], cwd=source)
        run(['git', 'checkout', '--detach', item['commit']], cwd=source)
        if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip() != item['commit']:
            raise RuntimeError('CTranslate2 source commit mismatch')
        run(['git', 'submodule', 'update', '--init', '--recursive', '--depth', '1',
             'third_party/spdlog', 'third_party/cpu_features', 'third_party/ruy'], cwd=source)
        if sys.platform == 'win32':
            already_applied = subprocess.run(['git', 'apply', '--reverse', '--check', str(patch)],
                cwd=source, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
            if not already_applied:
                run(['git', 'apply', '--check', patch], cwd=source)
                run(['git', 'apply', patch], cwd=source)
        prefix = directory / 'sdk'
        build = ROOT / '.build/ctranslate2-build'
        options = ['-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_POLICY_VERSION_MINIMUM=3.5',
                   '-DCMAKE_INSTALL_PREFIX=' + str(prefix), '-DBUILD_SHARED_LIBS=ON', '-DBUILD_CLI=OFF',
                   '-DBUILD_TESTS=OFF', '-DWITH_MKL=OFF', '-DWITH_DNNL=OFF', '-DWITH_OPENBLAS=OFF',
                   '-DWITH_CUDA=OFF', '-DWITH_CUDNN=OFF', '-DWITH_RUY=ON', '-DOPENMP_RUNTIME=COMP',
                   '-DRUY_MINIMAL_BUILD=ON', '-DCPUINFO_BUILD_UNIT_TESTS=OFF', '-DCPUINFO_BUILD_BENCHMARKS=OFF']
        if sys.platform == 'darwin':
            omp = subprocess.check_output(['brew', '--prefix', 'libomp'], text=True).strip()
            omp_metadata = json.loads(subprocess.check_output(['brew', 'info', '--json=v2', 'libomp'], text=True))
            options += ['-DWITH_ACCELERATE=ON', '-DCMAKE_OSX_ARCHITECTURES=x86_64',
                        '-DCMAKE_OSX_DEPLOYMENT_TARGET=15.0', '-DCMAKE_PREFIX_PATH=' + omp,
                        # Pinned ruy/platform.h disables all x86 SIMD on Apple
                        # due to an Xcode <=10.2 issue. Modern Apple Clang can
                        # compile its ISA-specific files; runtime CPU dispatch
                        # still selects supported kernels (no -march=native).
                        '-DCMAKE_CXX_FLAGS=-DRUY_FORCE_ENABLE_X86_ENHANCEMENTS',
                        '-DOpenMP_C_FLAGS=-Xpreprocessor;-fopenmp;-I' + omp + '/include',
                        '-DOpenMP_CXX_FLAGS=-Xpreprocessor;-fopenmp;-I' + omp + '/include',
                        '-DOpenMP_C_LIB_NAMES=omp', '-DOpenMP_CXX_LIB_NAMES=omp',
                        '-DOpenMP_omp_LIBRARY=' + omp + '/lib/libomp.dylib']
            env.update({'MACOSX_DEPLOYMENT_TARGET': '15.0', 'ARCHFLAGS': '-arch x86_64',
                        '_PYTHON_HOST_PLATFORM': 'macosx-15.0-x86_64', 'DYLD_LIBRARY_PATH': str(prefix / 'lib')})
        else:
            options += ['-A', 'x64', '-DWITH_ACCELERATE=OFF']
        run(['cmake', '-S', source, '-B', build, *options], env=env)
        run(['cmake', '--build', build, '--config', 'Release', '--parallel', '4'], env=env)
        run(['cmake', '--install', build, '--config', 'Release'], env=env)
        archive = directory / f'CTranslate2-4.8.2-{sys.platform}-source-with-cpu-submodules.tar.gz'
        def source_filter(member):
            return None if '.git' in Path(member.name).parts else member
        with tarfile.open(archive, 'w:gz') as package:
            package.add(source, arcname='CTranslate2-4.8.2', filter=source_filter)
        env.update({'CTRANSLATE2_ROOT': str(prefix), 'CMAKE_BUILD_PARALLEL_LEVEL': '4',
                    'PATH': str(prefix / 'bin') + os.pathsep + env.get('PATH', '')})
        run([sys.executable, 'setup.py', 'bdist_wheel', '--dist-dir', wheels], cwd=source / 'python', env=env)
        wheel = next(wheels.glob('ctranslate2-4.8.2-*.whl'))
        if sys.platform == 'win32':
            extra = [prefix / 'bin']
            redist = os.environ.get('VCToolsRedistDir')
            if redist:
                extra += [p.parent for p in Path(redist).rglob('vcomp140.dll') if 'x64' in p.parts]
            run([sys.executable, '-m', 'delvewheel', 'repair', '--add-path', os.pathsep.join(map(str, extra)),
                 '-w', repaired, wheel], env=env)
        else:
            run([sys.executable, '-m', 'delocate.cmd.delocate_wheel', '-w', repaired, wheel], env=env)
        wheel = next(repaired.glob('ctranslate2-4.8.2-*.whl'))
        notices = directory / 'licenses'
        for path in source.rglob('*'):
            if path.is_file() and '.git' not in path.parts and any(x in path.name.upper() for x in ('LICENSE', 'COPYING', 'NOTICE')):
                target = notices / path.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
        if sys.platform == 'darwin':
            omp_version = omp_metadata['formulae'][0]['versions']['stable']
            license_url = f'https://raw.githubusercontent.com/llvm/llvm-project/llvmorg-{omp_version}/openmp/LICENSE.TXT'
            with urllib.request.urlopen(license_url, timeout=60) as stream:
                omp_license = stream.read()
            (notices / 'LLVM-OpenMP-LICENSE.txt').write_bytes(omp_license)
            (directory / 'openmp-source.json').write_text(json.dumps(omp_metadata, indent=2))
        info.write_text(json.dumps({'source': item, 'platform': sys.platform, 'configure': options,
            'submodules': subprocess.check_output(['git', 'submodule', 'status', '--recursive'], cwd=source, text=True),
            'wheel_sha256': sha256(wheel), 'source_archive_sha256': sha256(archive),
            'windows_ruy_teardown_patch_sha256': expected_patch}, indent=2))
    else:
        wheel = existing[0]
    metadata = json.loads(info.read_text())
    if metadata['source'] != item or metadata['platform'] != sys.platform or sha256(wheel) != metadata['wheel_sha256']:
        raise RuntimeError('Controlled CTranslate2 cache mismatch')
    if metadata.get('windows_ruy_teardown_patch_sha256') != expected_patch:
        raise RuntimeError('Controlled CTranslate2 Windows lifetime patch mismatch; use a fresh native build directory')
    run([sys.executable, '-m', 'pip', 'install', '--no-deps', '--force-reinstall', wheel])


if __name__ == '__main__':
    main()
