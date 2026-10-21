"""End-to-end pipeline: audio + original Arabic text -> timed words -> cues -> SRT."""
from __future__ import annotations
import os
import tempfile
from dataclasses import dataclass


@dataclass
class AlignResult:
    cues: list
    timed_words: list
    srt_text: str
    audio_duration: float
    asr_word_count: int
    ref_word_count: int
    low_conf_rate: float


def run_alignment(
    audio_path: str,
    original_text: str,
    model_size: str = "small",
    show_tags: bool = False,
    strip_diacritics_for_align: bool = True,
    max_chars: int = 84,
    max_dur: float = 6.5,
    min_dur: float = 0.9,
    pause_break: float = 0.6,
    cpu_threads: int = 4,
    progress_cb=None,
) -> AlignResult:
    from app.core import normalizer as N
    from app.core import audio as A
    from app.core import whisper_aligner as W
    from app.core import mapper as M
    from app.core import segmenter as S
    from app.core import srt as SRT

    def prog(p, msg):
        if progress_cb:
            try:
                progress_cb(p, msg)
            except Exception:
                pass

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio not found: {audio_path}")
    if not original_text or not original_text.strip():
        raise ValueError("النص فارغ. الصق النص أو حمّل ملف TXT.")

    prog(0.02, "Preparing audio (FFmpeg) …")
    wav = A.convert_to_wav16k(audio_path)
    try:
        dur = A.probe_duration(wav)
        if dur <= 0:
            import wave
            with wave.open(wav, "rb") as w:
                dur = w.getnframes() / float(w.getframerate())

        prog(0.08, "Parsing text (keeping original, cleaning copy) …")
        display, keys, is_tag = N.tokenize_preserving_original(original_text, strip_diacritics_for_align)
        n_ref_speech = sum(1 for t in is_tag if not t)
        if n_ref_speech == 0:
            raise ValueError("النص لا يحتوي على كلام بعد إزالة التاجات.")

        prog(0.10, "Transcribing (offline, CPU) …")
        asr_words, lang, _full = W.transcribe_with_words(
            wav, model_size=model_size, cpu_threads=cpu_threads, progress_cb=prog,
        )
        asr_keys = [N.normalize_for_align(N.remove_tashkeel(w.text)) for w in asr_words]

        prog(0.60, f"Mapping {n_ref_speech} reference words onto {len(asr_words)} ASR words …")
        timed = M.map_reference_to_asr(display, keys, is_tag, asr_words, asr_keys, dur)

        prog(0.80, "Smart segmentation …")
        cues = S.segment(
            timed, max_chars=max_chars, max_dur=max_dur, min_dur=min_dur,
            pause_break=pause_break, show_tags=show_tags,
        )
        if not cues:
            raise RuntimeError("تعذّر إنشاء أي مقطع ترجمة (نص/صوت غير متوافقين؟).")

        srt_text = SRT.cues_to_srt(cues)
        low = sum(1 for w in timed if not w.is_tag and w.conf < 0.35) / max(1, n_ref_speech)
        prog(1.0, f"Done: {len(cues)} cues, low-confidence {low:.0%}")
        return AlignResult(cues, timed, srt_text, dur, len(asr_words), n_ref_speech, low)
    finally:
        try:
            if os.path.exists(wav) and wav.endswith(".wav") and tempfile.gettempdir() in wav:
                os.remove(wav)
        except Exception:
            pass
