# -*- coding: utf-8 -*-
"""Prepare the model and native FFmpeg assets for a fully offline build.

By default, the two GUI models are staged under ``offline_assets/models``.
The project's offline model cache is used by default and is left intact;
cached snapshots are reused before any network request is made.

Usage:
  py tools\\prepare_offline.py
  py tools\\prepare_offline.py --model small --all-models large-v3-turbo
"""
import argparse
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from app.models import MODEL_NAMES
DEFAULT_MODELS = MODEL_NAMES
REQUIRED_FILES = ("model.bin", "config.json", "tokenizer.json")
VOCABULARY_FILES = ("vocabulary.json", "vocabulary.txt")
MIN_MODEL_BYTES = 50_000_000


def _default_cache_dir() -> str:
    """Return Hugging Face Hub's effective cache path, including env overrides."""
    try:
        from huggingface_hub.constants import HF_HUB_CACHE

        return os.path.abspath(os.fspath(HF_HUB_CACHE))
    except (ImportError, AttributeError):
        # Compatibility fallback for older huggingface_hub installations.
        for name in ("HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE"):
            value = os.environ.get(name)
            if value:
                return os.path.abspath(os.path.expanduser(value))
        hf_home = os.environ.get("HF_HOME")
        if hf_home:
            return os.path.abspath(os.path.join(os.path.expanduser(hf_home), "hub"))
        xdg_home = os.environ.get("XDG_CACHE_HOME")
        base = os.path.expanduser(xdg_home) if xdg_home else os.path.expanduser("~/.cache")
        return os.path.abspath(os.path.join(base, "huggingface", "hub"))


def _repo_id(model: str, model_map: dict[str, str]) -> str:
    repo_id = model_map.get(model)
    if repo_id is None:
        valid = ", ".join(model_map)
        raise ValueError(f"Unknown faster-whisper model {model!r}. Available: {valid}")
    return repo_id


def _model_cache_folder(cache_dir: str, repo_id: str) -> str:
    return os.path.join(cache_dir, "models--" + repo_id.replace("/", "--"))


def _snapshot_candidates(cache_dir: str, repo_id: str) -> list[str]:
    """List cached snapshots with refs/main first, then other revisions."""
    folder = _model_cache_folder(cache_dir, repo_id)
    snapshots_dir = os.path.join(folder, "snapshots")
    if not os.path.isdir(snapshots_dir):
        return []

    candidates: list[str] = []
    ref_path = os.path.join(folder, "refs", "main")
    try:
        with open(ref_path, "r", encoding="utf-8") as ref_file:
            ref = ref_file.read().strip()
        if ref:
            preferred = os.path.join(snapshots_dir, ref)
            if os.path.isdir(preferred):
                candidates.append(preferred)
    except OSError:
        pass

    try:
        others = sorted(
            (os.path.join(snapshots_dir, name) for name in os.listdir(snapshots_dir)),
            key=os.path.getmtime,
            reverse=True,
        )
    except OSError:
        others = []
    for candidate in others:
        if os.path.isdir(candidate) and candidate not in candidates:
            candidates.append(candidate)
    return candidates


def _missing_files(snapshot: str) -> list[str]:
    missing = []
    for name in REQUIRED_FILES:
        path = os.path.join(snapshot, name)
        try:
            size = os.path.getsize(path)
        except OSError:
            size = 0
        if size <= 0 or (name == "model.bin" and size <= MIN_MODEL_BYTES):
            missing.append(name)
    if not any(
        os.path.isfile(os.path.join(snapshot, name))
        and os.path.getsize(os.path.join(snapshot, name)) > 0
        for name in VOCABULARY_FILES
    ):
        missing.append("vocabulary.json or vocabulary.txt")
    return missing


def _cached_snapshot(cache_dir: str, repo_id: str) -> str | None:
    for candidate in _snapshot_candidates(cache_dir, repo_id):
        if not _missing_files(candidate):
            return candidate
    return None


def _download_snapshot(model: str, cache_dir: str, repo_id: str, download_model) -> str:
    """Use a complete cached revision when possible, then download if needed."""
    cached = _cached_snapshot(cache_dir, repo_id)
    if cached:
        revision = os.path.basename(cached)
        try:
            # Go through faster-whisper's supported resolver, with the cache
            # explicitly supplied, while pinning the exact cached revision.
            resolved = download_model(
                model,
                cache_dir=cache_dir,
                revision=revision,
                local_files_only=True,
            )
        except Exception:
            # A complete HF snapshot can still be used if an older Hub cache
            # layout cannot resolve its revision through snapshot_download.
            resolved = cached
        if not _missing_files(resolved):
            return resolved
        if not _missing_files(cached):
            return cached

    try:
        snapshot = download_model(model, cache_dir=cache_dir, local_files_only=True)
    except Exception:
        snapshot = None
    if snapshot and not _missing_files(snapshot):
        return snapshot

    # The requested model is absent or incomplete in the existing cache.
    # download_model reuses any of its cached files and fetches only what is
    # missing. It writes to the selected HF cache; that cache is never moved.
    snapshot = download_model(model, cache_dir=cache_dir, local_files_only=False)
    missing = _missing_files(snapshot)
    if missing:
        raise RuntimeError(
            f"Downloaded model {model!r} is incomplete at {snapshot}: "
            f"missing or empty {', '.join(missing)}"
        )
    return snapshot


def _stage_snapshot(snapshot: str, models_dir: str, repo_id: str) -> tuple[str, str]:
    """Copy a resolved snapshot into the bundled HF-cache layout."""
    revision = os.path.basename(os.path.normpath(snapshot))
    repo_folder = _model_cache_folder(models_dir, repo_id)
    target = os.path.join(repo_folder, "snapshots", revision)
    os.makedirs(os.path.dirname(target), exist_ok=True)

    same_path = os.path.normcase(os.path.realpath(snapshot)) == os.path.normcase(
        os.path.realpath(target)
    )
    if not same_path:
        # Follow HF cache symlinks so the installer contains real model data,
        # even when the source cache stores files as links to its blobs folder.
        shutil.copytree(snapshot, target, dirs_exist_ok=True, symlinks=False)

    missing = _missing_files(target)
    if missing:
        raise RuntimeError(
            f"Staged model snapshot {target} is incomplete: "
            f"missing or empty {', '.join(missing)}"
        )

    refs_dir = os.path.join(repo_folder, "refs")
    os.makedirs(refs_dir, exist_ok=True)
    with open(os.path.join(refs_dir, "main"), "w", encoding="utf-8") as ref_file:
        ref_file.write(revision)
    return target, revision


def _snapshot_file_sizes(snapshot: str) -> dict[str, int]:
    sizes: dict[str, int] = {}
    for root, _, files in os.walk(snapshot):
        for name in files:
            path = os.path.join(root, name)
            relative = os.path.relpath(path, snapshot).replace(os.sep, "/")
            try:
                sizes[relative] = os.path.getsize(path)
            except OSError:
                continue
    return dict(sorted(sizes.items()))


def _write_manifest(manifest_path: str, models: list[dict], ffmpeg_size: int,
                    ffmpeg_name: str = "ffmpeg.exe") -> None:
    with open(manifest_path, "w", encoding="utf-8") as manifest:
        manifest.write("format=ArabicAligner offline assets v1\n")
        manifest.write("models=" + ",".join(item["name"] for item in models) + "\n")
        for item in models:
            prefix = "model." + item["name"]
            manifest.write(f"{prefix}.repo_id={item['repo_id']}\n")
            manifest.write(f"{prefix}.revision={item['revision']}\n")
            manifest.write(f"{prefix}.snapshot_size_bytes={item['snapshot_size_bytes']}\n")
            for filename, size in item["file_sizes"].items():
                manifest.write(f"{prefix}.file.{filename}.bytes={size}\n")
        manifest.write("ffmpeg=bundled\n")
        manifest.write(f"ffmpeg.file=ffmpeg/{ffmpeg_name}\nffmpeg.size_bytes={ffmpeg_size}\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--model",
        default=None,
        help="single model to prepare (when used, replaces the default model list)",
    )
    ap.add_argument(
        "--all-models",
        default=None,
        help="comma-separated model list; by default small,large-v3-turbo",
    )
    ap.add_argument(
        "--models-dir",
        default=os.path.join(ROOT, "offline_assets", "models"),
    )
    ap.add_argument(
        "--cache-dir",
        default=None,
        help="Hugging Face Hub cache to reuse (defaults to the offline models directory)",
    )
    ap.add_argument(
        "--ffmpeg-dest",
        default=os.path.join(ROOT, "offline_assets", "ffmpeg"),
    )
    ap.add_argument("--manifest", default=os.path.join(ROOT, "offline_assets", "MANIFEST.txt"))
    args = ap.parse_args()

    if args.model is not None:
        models = [args.model]
        if args.all_models:
            models.extend(part.strip() for part in args.all_models.split(",") if part.strip())
    elif args.all_models is not None:
        models = [part.strip() for part in args.all_models.split(",") if part.strip()]
    else:
        models = list(DEFAULT_MODELS)
    models = list(dict.fromkeys(models))
    if not models:
        ap.error("at least one model must be selected")

    try:
        from faster_whisper.utils import _MODELS, download_model
    except ImportError as exc:
        raise RuntimeError("faster-whisper is required to prepare offline models") from exc
    for model in models:
        _repo_id(model, _MODELS)

    cache_dir = os.path.abspath(os.path.expanduser(args.cache_dir or args.models_dir))
    models_dir = os.path.abspath(args.models_dir)
    ffmpeg_dest = os.path.abspath(args.ffmpeg_dest)
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(ffmpeg_dest, exist_ok=True)

    print("[1/2] Vendoring FFmpeg binary (imageio-ffmpeg)", flush=True)
    try:
        import imageio_ffmpeg
    except ImportError as exc:
        raise RuntimeError("imageio-ffmpeg is required to bundle offline FFmpeg") from exc
    ffmpeg_source = imageio_ffmpeg.get_ffmpeg_exe()
    if not os.path.isfile(ffmpeg_source) or os.path.getsize(ffmpeg_source) <= 0:
        raise RuntimeError(f"imageio-ffmpeg did not provide a usable FFmpeg binary: {ffmpeg_source}")
    ffmpeg_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    ffmpeg_path = os.path.join(ffmpeg_dest, ffmpeg_name)
    shutil.copy2(ffmpeg_source, ffmpeg_path)
    if os.name != "nt":
        os.chmod(ffmpeg_path, 0o755)
    ffmpeg_size = os.path.getsize(ffmpeg_path)
    if ffmpeg_size <= 0:
        raise RuntimeError(f"FFmpeg copy is missing or empty: {ffmpeg_path}")
    print(f"  ffmpeg -> {ffmpeg_path} ({ffmpeg_size} bytes)", flush=True)

    print(f"[2/2] Preparing faster-whisper models: {models}", flush=True)
    prepared = []
    for model in models:
        repo_id = _repo_id(model, _MODELS)
        print(f"  resolving {model} in HF cache {cache_dir} ...", flush=True)
        source_snapshot = _download_snapshot(model, cache_dir, repo_id, download_model)
        staged_snapshot, revision = _stage_snapshot(source_snapshot, models_dir, repo_id)
        file_sizes = _snapshot_file_sizes(staged_snapshot)
        if not file_sizes:
            raise RuntimeError(f"Model snapshot contains no files: {staged_snapshot}")
        snapshot_size = sum(file_sizes.values())
        prepared.append(
            {
                "name": model,
                "repo_id": repo_id,
                "revision": revision,
                "snapshot_size_bytes": snapshot_size,
                "file_sizes": file_sizes,
            }
        )
        print(
            f"  OK {model} revision {revision} "
            f"({snapshot_size:,} bytes)",
            flush=True,
        )

    manifest_path = os.path.abspath(args.manifest)
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    _write_manifest(manifest_path, prepared, ffmpeg_size, ffmpeg_name)
    print(f"OK: offline_assets ready; manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
