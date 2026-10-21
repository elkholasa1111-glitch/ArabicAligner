# -*- coding: utf-8 -*-
"""Smoke tests that run WITHOUT model/audio (fast, offline)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core import normalizer as N
from app.core import segmenter as S
from app.core import srt as SRT
from app.core.mapper import TimedWord


def test_tags_hidden_by_default():
    text = "مرحبًا بكم [laughs] في البرنامج [whispers] اليوم."
    disp, keys, is_tag = N.tokenize_preserving_original(text)
    assert any(is_tag), "tags must be detected"
    # alignment copy has no tags
    clean = N.clean_text_for_asr_compare(text)
    assert "[laughs]" not in clean and "[whispers]" not in clean
    assert N.normalize_for_align(N.remove_tashkeel("مرحبًا")) == "مرحبا"
    # original preserved
    assert any("مرحبًا" in d for d in disp), disp


def test_tashkeel_and_hamza_norm():
    assert N.remove_tashkeel("مَرْحَبًا") == "مرحبا"
    assert N.normalize_for_align("أحمد") == N.normalize_for_align("احمد")
    assert N.normalize_for_align("نهاية") == N.normalize_for_align("نهايه")
    assert N.normalize_for_align("علي") == N.normalize_for_align("على")


def test_segmenter_not_fixed_count():
    # punctuation + pause driven, not fixed N words
    tw = [
        TimedWord("السلام", 0.0, 0.4, 1.0),
        TimedWord("عليكم.", 0.45, 0.9, 1.0),
        TimedWord("كيف", 2.0, 2.3, 1.0),
        TimedWord("حالكم؟", 2.35, 2.8, 1.0),
    ]
    cues = S.segment(tw, max_chars=84, max_dur=6.5, pause_break=0.6)
    assert len(cues) == 2, cues
    srt = SRT.cues_to_srt(cues)
    assert "-->" in srt


def test_mapper_never_crashes_on_empty_asr():
    from app.core.mapper import map_reference_to_asr
    disp = ["مرحبا", "بكم"]
    keys = [N.normalize_for_align("مرحبا"), N.normalize_for_align("بكم")]
    out = map_reference_to_asr(disp, keys, [False, False], [], [], 10.0)
    assert len(out) == 2 and all(w.start >= 0 for w in out)


if __name__ == "__main__":
    test_tags_hidden_by_default()
    test_tashkeel_and_hamza_norm()
    test_segmenter_not_fixed_count()
    test_mapper_never_crashes_on_empty_asr()
    print("ALL SMOKE TESTS PASSED")
