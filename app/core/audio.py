"""Audio loading: MP3/WAV/M4A -> 16kHz mono WAV (temp file), via bundled or system FFmpeg."""
from __future__ import annotations
import os
import shutil
import subprocess
import sys
import tempfile
from app.resources import resource_roots


def _candidate_ffmpegs() -> list[str]:
    cands: list[str] = []
    name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    for root in resource_roots():
        cands.extend(str(root / relative / name) for relative in
                     ("offline_assets/ffmpeg", "bin", "."))
    # 2) imageio-ffmpeg bundled binary (pip package, offline-capable if vendored)
    try:
        import imageio_ffmpeg  # type: ignore
        cands.append(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        pass
    # 3) system ffmpeg
    w = shutil.which("ffmpeg")
    if w:
        cands.append(w)
    return [c for c in dict.fromkeys(cands) if c and os.path.isfile(c)
            and (os.name == "nt" or os.access(c, os.X_OK))]


def find_ffmpeg() -> str:
    cands = _candidate_ffmpegs()
    if not cands:
        raise RuntimeError(
            "تعذر العثور على أداة الصوت المدمجة FFmpeg. أعد تثبيت النسخة الكاملة من البرنامج."
        )
    return cands[0]


def convert_to_wav16k(src_path: str, dst_path: str | None = None) -> str:
    """Convert any input audio to 16kHz mono 16-bit WAV. Returns wav path."""
    ffmpeg = find_ffmpeg()
    owns_destination = dst_path is None
    if dst_path is None:
        fd, dst_path = tempfile.mkstemp(suffix="_16k.wav")
        os.close(fd)
    cmd = [
        ffmpeg, "-y", "-v", "error",
        "-i", src_path,
        "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
        dst_path,
    ]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        if proc.returncode != 0 or not os.path.exists(dst_path) or os.path.getsize(dst_path) == 0:
            err = proc.stderr.decode("utf-8", "ignore")[-2000:]
            raise RuntimeError(f"FFmpeg conversion failed: {err}")
    except Exception:
        if owns_destination and os.path.isfile(dst_path):
            os.remove(dst_path)
        raise
    return dst_path


def probe_duration(src_path: str) -> float:
    # Try ffprobe, else wave header fallback
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        try:
            p = subprocess.run(
                [ffprobe, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", src_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15,
            )
            return float(p.stdout.decode().strip())
        except Exception:
            pass
    try:
        import wave, contextlib
        with contextlib.closing(wave.open(src_path, "rb")) as w:
            return w.getnframes() / float(w.getframerate() or 16000)
    except Exception:
        return 0.0
