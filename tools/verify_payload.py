"""Fail the release build if a selectable model or native runtime is missing."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.core.whisper_aligner import _model_path
from app.models import MODEL_NAMES, MODEL_FOLDERS


def verify(bundle):
    bundle = Path(bundle)
    internal = bundle / '_internal'
    required = [bundle / 'ArabicAligner.exe', internal / 'python311.dll',
                internal / 'vcruntime140.dll', internal / 'msvcp140.dll',
                internal / 'PySide6' / 'plugins' / 'platforms' / 'qwindows.dll',
                internal / 'offline_assets' / 'ffmpeg' / 'ffmpeg.exe']
    for path in required:
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f'Missing release dependency: {path}')
    cache = internal / 'offline_assets' / 'models'
    folders = {p.name for p in cache.iterdir() if p.is_dir()}
    if folders != set(MODEL_FOLDERS):
        raise RuntimeError(f'Unexpected release model directories: {folders}')
    report = {}
    for name in MODEL_NAMES:
        snapshot = _model_path(str(cache), name)
        if not snapshot:
            raise RuntimeError(f'Missing complete release model: {name}')
        for path in Path(snapshot).iterdir():
            if path.is_symlink():
                raise RuntimeError(f'Release contains a cache symlink: {path}')
        report[name] = {'revision': Path(snapshot).name,
                        'bytes': sum(p.stat().st_size for p in Path(snapshot).iterdir() if p.is_file())}
    return report


if __name__ == '__main__':
    print(json.dumps(verify(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'dist-release' / 'ArabicAligner'), indent=2))
