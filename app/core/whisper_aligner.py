"""Local CPU INT8 word-level recognition used as a fuzzy timing guide.

Original reference tokens are preserved for display. Accuracy and performance
vary by recording and hardware; no external CTC/MMS plugin is implemented.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ASRWord:
    text: str
    start: float
    end: float
    prob: float = 1.0


def _bundled_hf_cache() -> str | None:
    """If installer vendored offline_assets/models, point HF hub there (full offline)."""
    import os, sys
    from app.resources import resource_roots
    cands = [str(root / "offline_assets" / "models") for root in resource_roots()]
    if sys.platform == 'darwin' and not getattr(sys, 'frozen', False):
        cands += [str(root / 'offline_assets-macos' / 'models') for root in resource_roots()]
    # Source-only opt-in for contributors reusing a deliberately selected cache.
    # Frozen releases always load their own files, even if this variable is set.
    if not getattr(sys, "frozen", False) and os.environ.get("ARABICALIGNER_MODELS_DIR"):
        cands.insert(0, os.path.abspath(os.path.expanduser(os.environ["ARABICALIGNER_MODELS_DIR"])))
    for c in cands:
        try:
            if c and os.path.isdir(c) and os.listdir(c):
                return c
        except Exception:
            pass
    return None


def _model_repo(model_size: str) -> str:
    """Map faster-whisper size -> HF repo id (same mapping faster-whisper uses)."""
    from app.models import MODEL_REPOS
    if model_size in MODEL_REPOS:
        return MODEL_REPOS[model_size]
    try:
        from faster_whisper.utils import _MODELS
        if model_size in _MODELS:
            return _MODELS[model_size]
    except Exception:
        pass
    if model_size == "large-v3-turbo":
        return "mobiuslabsgmbh/faster-whisper-large-v3-turbo"
    return f"Systran/faster-whisper-{model_size}"


def _model_cached(cache_dir: str, model_size: str) -> bool:
    """True if the requested model has a usable snapshot in the given HF cache.

    Also validates real byte size: PyInstaller once copied HF symlinks as
    0-byte files, which must NOT count as cached.
    """
    return _model_path(cache_dir, model_size) is not None


def _model_path(cache_dir: str, model_size: str) -> str | None:
    """Resolve complete local files directly; never consult a user cache or network."""
    from pathlib import Path
    folder = Path(cache_dir) / ("models--" + _model_repo(model_size).replace("/", "--"))
    snapshots = folder / "snapshots"
    candidates = []
    ref = folder / "refs" / "main"
    if ref.is_file():
        candidates.append(snapshots / ref.read_text().strip())
    if snapshots.is_dir():
        candidates.extend(sorted(snapshots.iterdir()))
    for path in candidates:
        try:
            required = [path / name for name in ("model.bin", "config.json", "tokenizer.json")]
            vocab = [path / name for name in ("vocabulary.json", "vocabulary.txt")]
            if (all(p.is_file() and p.stat().st_size > 0 for p in required)
                    and required[0].stat().st_size > 50_000_000
                    and any(p.is_file() and p.stat().st_size > 0 for p in vocab)):
                return str(path)
        except OSError:
            continue
    return None


def transcribe_with_words(
    wav_path: str,
    model_size: str = "small",
    device: str = "cpu",
    compute_type: str = "int8",
    cpu_threads: int = 4,
    progress_cb=None,
) -> tuple[list[ASRWord], str, str]:
    """Returns (words, detected_language, full_text). Raises with clear message if missing."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise RuntimeError(
            "faster-whisper is not installed. Run: pip install faster-whisper"
        ) from e

    if progress_cb:
        progress_cb(0.12, "Loading bundled model (offline, CPU) …")

    import os
    cache = _bundled_hf_cache()
    model_path = _model_path(cache, model_size) if cache else None
    if not model_path:
        raise RuntimeError(
            f"ملفات النموذج '{model_size}' غير موجودة أو غير مكتملة. أعد تثبيت النسخة الكاملة من البرنامج."
        )
    try:
        model = WhisperModel(
            model_path, device=device, compute_type=compute_type,
            cpu_threads=cpu_threads, local_files_only=True,
        )
    except Exception as e:
        msg = str(e)
        if "offline" in msg.lower() or "LocalEntryNotFound" in type(e).__name__ or "cannot reach" in msg.lower():
            raise RuntimeError(
                f"تعذر فتح ملفات النموذج '{model_size}'. أعد تثبيت النسخة الكاملة."
            ) from e
        raise

    # vad_filter handles music/long pauses robustly on CPU (silero VAD, tiny)
    segments, info = model.transcribe(
        wav_path,
        language="ar",
        task="transcribe",
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
        word_timestamps=True,
        beam_size=1,  # greedy: fastest on CPU, fine for alignment backbone
        best_of=1,
        temperature=0.0,
        condition_on_previous_text=False,
        initial_prompt="نص عربي فصيح. علامات الترقيم: . ؟ ! ، ؛ :",
    )
    words: list[ASRWord] = []
    full_parts: list[str] = []
    lang = getattr(info, "language", "ar") or "ar"
    for seg in segments:
        full_parts.append(seg.text)
        if getattr(seg, "words", None):
            for w in seg.words:
                t = (w.word or "").strip()
                if not t:
                    continue
                try:
                    s, e = float(w.start), float(w.end)
                except Exception:
                    continue
                words.append(ASRWord(text=t, start=s, end=e, prob=float(getattr(w, "probability", 1.0) or 1.0)))
        if progress_cb and getattr(seg, "end", 0):
            duration = getattr(info, "duration", 0) or 1
            progress_cb(0.15 + 0.40 * min(1.0, seg.end / duration),
                        f"Transcribing: {seg.end:.0f} / {duration:.0f} sec")
    if progress_cb:
        progress_cb(0.55, f"ASR done: {len(words)} words ({lang})")
    return words, lang, " ".join(full_parts).strip()
