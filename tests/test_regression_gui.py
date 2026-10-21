import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QCloseEvent
from app.main import MainWindow
from app.models import MODEL_NAMES


class GuiRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow()
        self.result = SimpleNamespace(srt_text='1\n00:00:00,000 --> 00:00:01,000\nمرحبا\n',
                                      cues=[1], audio_duration=1, low_conf_rate=0)

    def tearDown(self):
        self.window.thread = None
        self.window.close()

    def test_only_requested_models_are_selectable(self):
        combo = self.window.cmb_model
        self.assertEqual([combo.itemText(i) for i in range(combo.count())], list(MODEL_NAMES))
        if sys.platform == 'darwin':
            self.assertEqual(list(MODEL_NAMES), ['small'])

    def test_completion_saves_beside_original_job_audio(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.window.active_audio_path = str(Path(tmp, 'original.wav'))
            self.window.audio_path = str(Path(tmp, 'new-selection.wav'))
            with patch('app.main.QMessageBox.information'):
                self.window.on_done(self.result)
            self.assertEqual(Path(tmp, 'original.srt').read_text(encoding='utf-8-sig'), self.result.srt_text)
            self.assertFalse(Path(tmp, 'new-selection.srt').exists())

    def test_write_failure_keeps_result_available_for_save_as(self):
        self.window.active_audio_path = 'audio.wav'
        with patch('builtins.open', side_effect=PermissionError('read only')), \
                patch('app.main.QMessageBox.warning'):
            self.window.on_done(self.result)
        self.assertIs(self.window.last_result, self.result)
        self.assertTrue(self.window.btn_save.isEnabled())
        self.assertEqual(self.window.srt_path, '')

    def test_close_during_processing_is_deferred(self):
        self.window.thread = SimpleNamespace(isRunning=lambda: True)
        event = QCloseEvent()
        with patch('app.main.QMessageBox.information'):
            self.window.closeEvent(event)
        self.assertFalse(event.isAccepted())


if __name__ == '__main__':
    unittest.main()
