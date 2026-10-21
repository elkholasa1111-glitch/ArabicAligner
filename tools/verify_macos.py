"""Validate a self-contained Intel .app without trusting system dependencies."""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.core.whisper_aligner import _model_path
from app.models import MODEL_NAMES, MODEL_FOLDERS


def verify(bundle):
    bundle = Path(bundle).resolve()
    contents = bundle / "Contents"
    resources = contents / "Resources"
    frameworks = contents / "Frameworks"
    executable = contents / "MacOS" / "ArabicAligner"
    required = [contents / "Info.plist", executable,
                resources / "offline_assets" / "MANIFEST.txt",
                frameworks / "offline_assets" / "ffmpeg" / "ffmpeg"]
    for path in required:
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"Missing macOS release dependency: {path}")
    with (contents / "Info.plist").open("rb") as stream:
        info = plistlib.load(stream)
    ffmpeg = required[-1]
    for path in (executable, ffmpeg):
        if not os.access(path, os.X_OK):
            raise RuntimeError(f"Executable permission missing: {path}")
        architectures = subprocess.check_output(["/usr/bin/lipo", "-archs", str(path)], text=True).split()
        if "x86_64" not in architectures:
            raise RuntimeError(f"Not an Intel executable: {path}: {architectures}")
    if not list(frameworks.rglob("libqcocoa.dylib")):
        raise RuntimeError("Native Cocoa Qt platform plugin was not bundled")
    if not (frameworks / "Python.framework").exists() and not list(frameworks.glob("libpython*.dylib")):
        # PyInstaller can also put the Python shared library at the root as 'Python'.
        if not (frameworks / "Python").exists():
            raise RuntimeError("Embedded Python runtime was not bundled")
    cache = resources / "offline_assets" / "models"
    folders = {path.name for path in cache.iterdir() if path.is_dir()}
    if folders != set(MODEL_FOLDERS):
        raise RuntimeError(f"Unexpected release model directories: {folders}")
    report = {"bundle": str(bundle), "version": info["CFBundleShortVersionString"],
              "architecture": "x86_64", "models": {}}
    for name in MODEL_NAMES:
        snapshot = _model_path(str(cache), name)
        if not snapshot:
            raise RuntimeError(f"Missing complete release model: {name}")
        files = {}
        for path in sorted(Path(snapshot).rglob("*")):
            if path.is_symlink():
                # Bundle-internal links made by PyInstaller are legitimate;
                # cache links to files outside the app are not.
                if not path.resolve().is_relative_to(bundle):
                    raise RuntimeError(f"Model points outside the app: {path}")
            if path.is_file():
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
                        digest.update(chunk)
                files[str(path.relative_to(snapshot))] = {"bytes": path.stat().st_size,
                                                          "sha256": digest.hexdigest()}
        report["models"][name] = {"revision": Path(snapshot).name, "files": files}
    subprocess.run(["/usr/bin/codesign", "--verify", "--deep", "--strict", str(bundle)], check=True)
    report["signature"] = "valid ad-hoc signature (not Apple notarized)"
    report["ffmpeg_version"] = subprocess.check_output([str(ffmpeg), "-version"], text=True).splitlines()[0]
    return report


if __name__ == "__main__":
    print(json.dumps(verify(sys.argv[1]), ensure_ascii=False, indent=2))
