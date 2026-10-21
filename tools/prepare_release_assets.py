"""Stage pinned model snapshots and the controlled native media runtime."""
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.models import MODEL_NAMES, MODEL_REPOS
from tools.prepare_offline import _stage_snapshot, _snapshot_file_sizes, _write_manifest

MODEL_REVISIONS = {
    "small": "536b0662742c02347bc0e980a01041f333bce120",
    "large-v3-turbo": "0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf",
}


def main():
    from huggingface_hub import snapshot_download
    assets = ROOT / ("offline_assets-macos" if sys.platform == "darwin" else "offline_assets")
    native = ROOT / "native"
    if not (native / "build-info.json").is_file():
        raise SystemExit("Build the controlled media runtime with tools/build_native_media.py first.")
    ffmpeg_dir = assets / "ffmpeg"
    ffmpeg_dir.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        paths = list((native / "bin").glob("*.dll")) + [native / "bin/ffmpeg.exe"]
    else:
        paths = [native / "bin/ffmpeg"] + list((native / "lib").glob("*.dylib"))
    for path in paths:
        if not path.is_file():
            raise RuntimeError(f"Missing native dependency: {path.name}")
        shutil.copy2(path.resolve(), ffmpeg_dir / path.name)
    models = []
    for name in MODEL_NAMES:
        source = snapshot_download(repo_id=MODEL_REPOS[name], revision=MODEL_REVISIONS[name],
                                   cache_dir=ROOT / ".build/model-cache", allow_patterns=["model.bin", "config.json",
                                   "tokenizer.json", "vocabulary.*", "preprocessor_config.json"])
        staged, revision = _stage_snapshot(source, str(assets / "models"), MODEL_REPOS[name])
        sizes = _snapshot_file_sizes(staged)
        models.append({"name": name, "repo_id": MODEL_REPOS[name], "revision": revision,
                       "snapshot_size_bytes": sum(sizes.values()), "file_sizes": sizes})
    executable = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    _write_manifest(str(assets / "MANIFEST.txt"), models, (ffmpeg_dir / executable).stat().st_size, executable)
    print("Prepared models: " + ", ".join(MODEL_NAMES), flush=True)


if __name__ == "__main__":
    main()
