"""Build pinned, external-codec-free FFmpeg and PyAV on the target platform.

Release packages must use these artifacts, not opaque upstream multimedia wheels.
No system installation or privilege is required. Build downloads are separate
from the fully local final application.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / ".build"
PREFIX = ROOT / "native"


def run(args, cwd=ROOT, env=None):
    print("+ " + " ".join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=cwd, env=env, check=True)


def sha256(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def fetch_source(name, item):
    downloads = BUILD / "sources"
    downloads.mkdir(parents=True, exist_ok=True)
    filename = item["url"].rsplit("/", 1)[1]
    archive = downloads / filename
    if not archive.exists():
        with urllib.request.urlopen(item["url"], timeout=90) as response, archive.open("wb") as target:
            shutil.copyfileobj(response, target, 1024 * 1024)
    if sha256(archive) != item["sha256"]:
        raise RuntimeError(f"Source integrity mismatch: {name}")
    directory = BUILD / f"{name}-source"
    if not directory.exists():
        directory.mkdir()
        with tarfile.open(archive) as package:
            for member in package.getmembers():
                path = (directory / member.name).resolve()
                if not path.is_relative_to(directory.resolve()):
                    raise RuntimeError("Unsafe source archive path")
                if member.issym() or member.islnk():
                    link = (path.parent / member.linkname).resolve()
                    if not link.is_relative_to(directory.resolve()):
                        raise RuntimeError("Unsafe source archive link")
            package.extractall(directory)
    roots = [path for path in directory.iterdir() if path.is_dir()]
    if len(roots) != 1:
        raise RuntimeError(f"Unexpected source layout: {name}")
    return roots[0]


def posix_path(path, bash):
    return subprocess.check_output([bash, "--noprofile", "--norc", "-c",
                                    '/usr/bin/cygpath -u "$1"', "_", str(path)], text=True).strip()


def main():
    if sys.platform not in ("win32", "darwin") or platform.machine().lower() not in ("amd64", "x86_64"):
        raise SystemExit("Release media builds are supported only on native Windows x64 or macOS Intel.")
    items = json.loads((ROOT / "third_party/sources.lock.json").read_text(encoding="utf-8"))
    ffmpeg = fetch_source("ffmpeg", items["ffmpeg"])
    pyav = fetch_source("pyav", items["pyav"])
    environment = os.environ.copy()
    if sys.platform == "win32":
        bash = os.environ.get("ARABICALIGNER_BASH", r"C:\msys64\usr\bin\bash.exe")
        if not Path(bash).is_file() or not shutil.which("cl.exe"):
            raise SystemExit("Use MSYS2 make/bash and an x64 MSVC developer environment; see docs/BUILDING.md.")
        compiler_bin = str(Path(shutil.which("cl.exe")).parent)
        environment["ARABICALIGNER_MSVC_BIN"] = compiler_bin
        environment["MSYS2_ARG_CONV_EXCL"] = "*"
        prefix_arg = posix_path(PREFIX, bash)
    else:
        bash = "/bin/bash"
        prefix_arg = str(PREFIX)
        environment["MACOSX_DEPLOYMENT_TARGET"] = "13.0"
    configure = [
        "--prefix=" + prefix_arg, "--enable-shared", "--disable-static",
        "--disable-autodetect", "--disable-gpl", "--disable-nonfree", "--enable-version3",
        "--disable-ffplay", "--disable-ffprobe", "--disable-doc", "--disable-debug",
        "--disable-network", "--disable-x86asm", "--disable-devices",
        "--disable-encoders", "--enable-encoder=pcm_s16le", "--disable-muxers", "--enable-muxer=wav",
        "--disable-filters", "--enable-filter=aresample,aformat,anull",
        "--disable-protocols", "--enable-protocol=file,pipe",
        "--disable-audiotoolbox", "--disable-videotoolbox", "--disable-mediafoundation",
        "--disable-vulkan", "--disable-vaapi", "--disable-vdpau",
    ]
    if sys.platform == "win32":
        configure += ["--toolchain=msvc", "--arch=x86_64", "--target-os=win64",
                      "--enable-w32threads", "--disable-pthreads"]
        script = 'export PATH="$(cygpath -u "$ARABICALIGNER_MSVC_BIN"):/usr/bin:$PATH"; exec ./configure "$@"'
    else:
        configure += ["--cc=clang", "--arch=x86_64", "--target-os=darwin",
                      "--extra-cflags=-mmacosx-version-min=13.0",
                      "--extra-ldflags=-mmacosx-version-min=13.0"]
        script = 'exec ./configure "$@"'
    run([bash, "--noprofile", "--norc", "-c", script, "_", *configure], cwd=ffmpeg, env=environment)
    if sys.platform == 'win32':
        # Feed makedef the exact make OBJS list via a response file. Windows
        # truncates the all-decoder object argv; codec behavior stays unchanged.
        definition = ffmpeg / 'compat/windows/makedef'
        source = definition.read_text()
        replacements = [
            ('shift\n\nif [ ! -f', 'shift\n\n# Read a make-generated object response file without a long Windows argv.\nif [ "$#" -eq 1 ] && [ "${1#@}" != "$1" ]; then\n    set -- $(cat "${1#@}")\nfi\n\nif [ ! -f'),
            ("trap 'rm -f -- $libname' EXIT", "trap 'rm -f -- $libname ${libname}.rsp' EXIT"),
            ('    lib.exe ${machine_flag} -out:${libname} $@ >/dev/null',
             '    printf \'%s\\n\' "$@" > "${libname}.rsp"\n    lib.exe ${machine_flag} -out:${libname} @${libname}.rsp >/dev/null'),
        ]
        for before, after in replacements:
            if before not in source:
                raise RuntimeError('Unexpected makedef source; review the pinned patch')
            source = source.replace(before, after, 1)
        definition.write_text(source, newline='\n')
        config = ffmpeg / 'ffbuild/config.mak'
        lines = config.read_text().splitlines()
        for index, line in enumerate(lines):
            # The configure probe uses @/dev/null, which MSVC cannot open.
            # Its linker/librarian do support ordinary response files.
            if line.startswith('RESPONSE_FILES='):
                lines[index] = 'RESPONSE_FILES=yes'
            if line.startswith('SLIB_CREATE_DEF_CMD='):
                if '$(OBJS)' not in line:
                    raise RuntimeError('Unexpected Windows export recipe')
                lines[index] = line.replace('$(OBJS)', '$(file >$(SUBDIR)makedef.rsp,$(OBJS)) @$(SUBDIR)makedef.rsp')
        config.write_text('\n'.join(lines) + '\n', newline='\n')
        library_makefile = ffmpeg / 'ffbuild/library.mak'
        source = library_makefile.read_text()
        old = '$(Q)echo $$(filter %.o,$$^) > $$@.objs'
        new = '$$(file >$$@.objs,$$(filter %.o,$$^))'
        if old not in source:
            raise RuntimeError('Unexpected response-file recipe')
        library_makefile.write_text(source.replace(old, new), newline='\n')
    # Fresh Windows builds do not need incremental .d files. MSVC's generated
    # awk depfile recipe loses a backslash with this upstream configure/make
    # combination; disable only depfile generation, not compilation or checks.
    make_options = ' CCDEP= CXXDEP= HOSTCCDEP= ASDEP=' if sys.platform == 'win32' else ''
    make_script = ('export PATH="$(cygpath -u "$ARABICALIGNER_MSVC_BIN"):/usr/bin:$PATH"; '
                   if sys.platform == "win32" else "") + 'make' + make_options + ' -j "$1" && make install'
    run([bash, "--noprofile", "--norc", "-c", make_script, "_", str(min(4, os.cpu_count() or 2))],
        cwd=ffmpeg, env=environment)
    # PyAV's supported --ffmpeg-dir build argument links the same controlled SDK.
    environment["PATH"] = str(PREFIX / "bin") + os.pathsep + environment.get("PATH", "")
    environment["DYLD_LIBRARY_PATH"] = str(PREFIX / "lib")
    wheels = ROOT / "wheelhouse"
    wheels.mkdir(exist_ok=True)
    run([sys.executable, "setup.py", "--ffmpeg-dir=" + str(PREFIX), "bdist_wheel", "--dist-dir", wheels],
        cwd=pyav, env=environment)
    wheel = next(wheels.glob("av-*.whl"))
    repaired = ROOT / "repaired-wheelhouse"
    if sys.platform == "win32":
        run([sys.executable, "-m", "delvewheel", "repair", "--add-path", PREFIX / "bin",
             "-w", repaired, wheel], env=environment)
    else:
        run([sys.executable, "-m", "delocate.cmd.delocate_wheel", "-w", repaired, wheel], env=environment)
    final_wheel = next(repaired.glob("av-*.whl"))
    run([sys.executable, "-m", "pip", "install", "--force-reinstall", "--no-deps", final_wheel])
    info = {"platform": sys.platform, "architecture": platform.machine(), "ffmpeg": items["ffmpeg"],
            "pyav": items["pyav"], "configure": configure, "wheel_sha256": sha256(final_wheel),
            "external_codec_libraries": False, "make_options": make_options.strip(),
            "windows_response_files": sys.platform == 'win32'}
    (PREFIX / "build-info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    print("Controlled native media build complete.", flush=True)


if __name__ == "__main__":
    main()
