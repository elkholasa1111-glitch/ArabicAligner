"""Behavior boundaries that matter for an Arabic subtitle release."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.mapper import map_reference_to_asr
from app.core.whisper_aligner import ASRWord, _bundled_hf_cache
from app.core.normalizer import tokenize_preserving_original
from app.core.segmenter import segment
from app.core.pipeline import run_alignment
from app.core.srt import cues_to_srt


class BehaviorRegressions(unittest.TestCase):
    def test_repetitions_keep_separate_anchors_and_diacritics(self):
        original = "قَالَ قَالَ نعم نعم"
        display, keys, tags = tokenize_preserving_original(original)
        heard = [ASRWord(word, index, index + .4) for index, word in enumerate(["قال", "قال", "نعم", "نعم"])]
        mapped = map_reference_to_asr(display, keys, tags, heard, ["قال", "قال", "نعم", "نعم"], 4)
        self.assertEqual([w.display for w in mapped], original.split())
        self.assertEqual([w.start for w in mapped], [0, 1, 2, 3])

    def test_pause_splits_and_never_loses_words(self):
        from app.core.mapper import TimedWord
        words = [TimedWord("نعم", .5, .9, 1), TimedWord("نعم", 2.5, 2.9, 1)]
        cues = segment(words, pause_break=.6)
        self.assertEqual(len(cues), 2)
        self.assertEqual(" ".join(c.text for c in cues), "نعم نعم")
        self.assertIn("00:00:00,500 --> 00:00:01,150", cues_to_srt(cues))

    def test_mismatched_reference_is_preserved_but_low_confidence(self):
        original = ["كتاب", "شجرة", "مطر"]
        heard = [ASRWord("نعم", 1, 1.4)]
        mapped = map_reference_to_asr(original, original, [False] * 3, heard, ["نعم"], 3)
        self.assertEqual([word.display for word in mapped], original)
        self.assertTrue(all(word.conf < .35 for word in mapped))
        self.assertTrue(all(0 <= word.start <= word.end <= 3 for word in mapped))

    def test_padding_does_not_erase_a_long_pause_boundary(self):
        from app.core.mapper import TimedWord
        words = [TimedWord('نعم', .5, .9, 1), TimedWord('نعم', 1.6, 2., 1)]
        cues = segment(words, pause_break=.6)
        self.assertEqual(len(cues), 2)
        self.assertLess(cues[0].end, cues[1].start)

    def test_silence_fallback_is_explicitly_low_confidence(self):
        mapped = map_reference_to_asr(["مَرْحَبًا"], ["مرحبا"], [False], [], [], 2)
        self.assertEqual(mapped[0].display, "مَرْحَبًا")
        self.assertLess(mapped[0].conf, .35)

    def test_nonexistent_audio_and_empty_text_are_rejected(self):
        with self.assertRaises(FileNotFoundError):
            run_alignment("not-a-real-recording.wav", "نص")
        with tempfile.NamedTemporaryFile(suffix=".wav") as audio:
            with self.assertRaises(ValueError):
                run_alignment(audio.name, " ")

    def test_frozen_application_ignores_developer_cache_override(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "private-model-cache").mkdir()
            with patch.dict(os.environ, {"ARABICALIGNER_MODELS_DIR": temp}), \
                    patch.object(sys, "frozen", True, create=True), \
                    patch("app.resources.resource_roots", return_value=[]):
                self.assertIsNone(_bundled_hf_cache())

    def test_macos_source_finds_its_prepared_platform_assets(self):
        with tempfile.TemporaryDirectory() as temp:
            cache = Path(temp) / 'offline_assets-macos/models'
            cache.mkdir(parents=True)
            (cache / 'model-marker').mkdir()
            with patch.object(sys, 'platform', 'darwin'), \
                    patch.object(sys, 'frozen', False, create=True), \
                    patch.dict(os.environ, {'ARABICALIGNER_MODELS_DIR': ''}), \
                    patch('app.resources.resource_roots', return_value=[Path(temp)]):
                self.assertEqual(_bundled_hf_cache(), str(cache))


if __name__ == "__main__":
    unittest.main()
