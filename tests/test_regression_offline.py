import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.whisper_aligner import _model_path, transcribe_with_words
from app.core.audio import convert_to_wav16k
from app.core.normalizer import tokenize_preserving_original


class OfflineModels(unittest.TestCase):
    def test_conversion_launch_failure_cleans_its_tempfile(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch('app.core.audio.find_ffmpeg', return_value='ffmpeg.exe'), \
                    patch('app.core.audio.tempfile.tempdir', tmp), \
                    patch('app.core.audio.subprocess.run', side_effect=OSError('cannot launch')):
                with self.assertRaises(OSError):
                    convert_to_wav16k('unused.wav')
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_diacritics_option_changes_keys_only(self):
        stripped = tokenize_preserving_original('مَرْحَبًا', True)
        kept = tokenize_preserving_original('مَرْحَبًا', False)
        self.assertEqual(stripped[0], kept[0])
        self.assertNotEqual(stripped[1], kept[1])

    def test_incomplete_snapshot_is_not_a_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            snap = Path(tmp, 'models--Systran--faster-whisper-small', 'snapshots', 'revision')
            snap.mkdir(parents=True)
            with (snap / 'model.bin').open('wb') as f:
                f.truncate(50_000_001)
            self.assertIsNone(_model_path(tmp, 'small'))
            for name in ('config.json', 'tokenizer.json', 'vocabulary.txt'):
                (snap / name).write_text('{}')
            self.assertEqual(_model_path(tmp, 'small'), str(snap))
            (snap / 'tokenizer.json').write_text('')
            self.assertIsNone(_model_path(tmp, 'small'))

    def test_missing_model_never_starts_download(self):
        with patch('app.core.whisper_aligner._bundled_hf_cache', return_value=None), \
                patch('faster_whisper.WhisperModel') as model:
            with self.assertRaises(RuntimeError):
                transcribe_with_words('unused.wav')
            model.assert_not_called()


if __name__ == '__main__':
    unittest.main()
