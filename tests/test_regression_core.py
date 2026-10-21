# -*- coding: utf-8 -*-
"""Regression tests for timing, segmentation, tag rendering, and SRT output."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.mapper import TimedWord, map_reference_to_asr
from app.core.segmenter import segment
from app.core.srt import fmt_ts
from app.core.whisper_aligner import ASRWord


def test_segmenter_enforces_hard_caps_without_punctuation():
    words = [TimedWord("س", i * 0.5, i * 0.5 + 0.4, 1.0) for i in range(30)]
    cues = segment(
        words,
        max_chars=84,
        max_dur=6.5,
        max_words=14,
        min_dur=0.0,
        pause_break=10.0,
    )

    assert len(cues) > 1
    assert all(len(c.text.split()) <= 14 for c in cues)
    assert all(c.end - c.start <= 6.5 + 1e-9 for c in cues)
    assert sum(len(c.text.split()) for c in cues) == len(words)


def test_segmenter_enforces_character_cap():
    words = [TimedWord("abcd", i * 0.2, i * 0.2 + 0.1, 1.0) for i in range(7)]
    cues = segment(
        words,
        max_chars=9,
        max_dur=20.0,
        max_words=99,
        min_dur=0.0,
        pause_break=10.0,
    )

    assert all(len(c.text) <= 9 for c in cues)
    assert " ".join(c.text for c in cues).split() == ["abcd"] * 7


def test_interpolation_never_moves_recognized_anchors():
    reference = ["lead", "alpha", "missing", "beta", "tail"]
    asr = [ASRWord("alpha", 1.0, 1.4), ASRWord("beta", 2.0, 2.4)]
    mapped = map_reference_to_asr(
        reference,
        reference,
        [False] * len(reference),
        asr,
        [w.text for w in asr],
        3.0,
    )

    assert (mapped[1].start, mapped[1].end) == (1.0, 1.4)
    assert (mapped[3].start, mapped[3].end) == (2.0, 2.4)
    assert all(0.0 <= w.start <= w.end <= 3.0 for w in mapped)

    # No time exists before an anchor at t=0.  The unmatched prefix may be
    # zero-duration, but it must not push the recognized word later.
    prefix = map_reference_to_asr(
        ["unspoken", "hello"],
        ["unspoken", "hello"],
        [False, False],
        [ASRWord("hello", 0.0, 0.4)],
        ["hello"],
        1.0,
    )
    assert (prefix[0].start, prefix[0].end) == (0.0, 0.0)
    assert (prefix[1].start, prefix[1].end) == (0.0, 0.4)


def test_visible_tags_are_attached_to_speech_cues():
    words = [
        TimedWord("هذه", 0.0, 0.3, 1.0),
        TimedWord("جملة", 0.3, 0.6, 1.0),
        TimedWord("عربية", 0.6, 0.9, 1.0),
        TimedWord("طويلة", 0.9, 1.2, 1.0),
        TimedWord("جدا.", 1.2, 1.5, 1.0),
        TimedWord("[laughs]", 1.5, 1.5, 1.0, True),
    ]

    visible = segment(words, show_tags=True, min_dur=0.0)
    hidden = segment(words, show_tags=False, min_dur=0.0)

    assert len(visible) == 1
    assert visible[0].text.endswith("جدا. [laughs]")
    assert visible[0].end == 1.5
    assert all(c.text != "[laughs]" for c in visible)
    assert all("[laughs]" not in c.text for c in hidden)
    assert segment([TimedWord("[laughs]", 0.0, 0.0, 1.0, True)], show_tags=True) == []


def test_zero_duration_unmatched_words_still_make_valid_cues():
    mapped = map_reference_to_asr(
        ["heard", "extra", "tail"],
        ["heard", "extra", "tail"],
        [False, False, False],
        [ASRWord("heard", 0.8, 1.0)],
        ["heard"],
        1.0,
    )
    cues = segment(mapped, max_words=1, min_dur=0.0)

    assert " ".join(c.text for c in cues).split() == ["heard", "extra", "tail"]
    assert all(c.start < c.end for c in cues)
    assert all(a.end <= b.start for a, b in zip(cues, cues[1:]))
    assert cues[-1].end <= 1.0


def test_srt_timestamp_rounding_carries_across_fields():
    assert fmt_ts(59.9996) == "00:01:00,000"
    assert fmt_ts(3599.9996) == "01:00:00,000"
    assert fmt_ts(86399.9996) == "24:00:00,000"
    assert fmt_ts(-0.1) == "00:00:00,000"


def load_tests(loader, tests, pattern):
    import unittest
    return unittest.TestSuite(unittest.FunctionTestCase(value)
                              for name, value in globals().items() if name.startswith("test_"))


if __name__ == "__main__":
    tests = [value for name, value in globals().items() if name.startswith("test_")]
    for test in tests:
        test()
    print(f"ALL {len(tests)} CORE REGRESSION TESTS PASSED")
