"""Regressions for Finder bundles, offline resources, and opening output."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.resources import resource_roots
from app.core.audio import _candidate_ffmpegs
from app.core.whisper_aligner import _bundled_hf_cache
from app.main import MainWindow
from PySide6.QtWidgets import QApplication


class BundleResources(unittest.TestCase):
    def test_finder_layout_uses_contents_resources(self):
        with tempfile.TemporaryDirectory() as temp:
            contents = Path(temp).resolve() / "برنامج بمسافات.app" / "Contents"
            executable = contents / "MacOS" / "ArabicAligner"
            resources = contents / "Resources"
            frameworks = contents / "Frameworks"
            cache = resources / "offline_assets" / "models"
            cache.mkdir(parents=True)
            (cache / "models--Systran--faster-whisper-small").mkdir()
            with patch.object(sys, "frozen", True, create=True), \
                    patch.object(sys, "_MEIPASS", str(frameworks), create=True), \
                    patch.object(sys, "executable", str(executable)):
                self.assertEqual(resource_roots()[0], frameworks)
                self.assertIn(resources, resource_roots())
                self.assertEqual(_bundled_hf_cache(), str(cache))

    def test_macos_ffmpeg_is_found_without_system_ffmpeg(self):
        with tempfile.TemporaryDirectory() as temp:
            binary = Path(temp, "offline_assets", "ffmpeg", "ffmpeg")
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b"native FFmpeg placeholder")
            binary.chmod(0o755)
            with patch("app.core.audio.resource_roots", return_value=[Path(temp)]), \
                    patch("app.core.audio.sys.platform", "darwin"), \
                    patch("app.core.audio.shutil.which", return_value=None), \
                    patch("imageio_ffmpeg.get_ffmpeg_exe", side_effect=RuntimeError("not used")):
                self.assertEqual(_candidate_ffmpegs(), [str(binary)])

    def test_no_duplicate_resource_roots(self):
        with patch.object(sys, "frozen", True, create=True), \
                patch.object(sys, "_MEIPASS", str(Path(sys.executable).parent), create=True):
            roots = resource_roots()
            self.assertEqual(len(roots), len(set(roots)))


class OpenOutput(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def test_open_subtitle_and_folder_use_local_file_urls(self):
        with tempfile.TemporaryDirectory(prefix="ArabicAligner ") as temp:
            subtitle = Path(temp, "ترجمة عربية.srt")
            subtitle.write_text("test", encoding="utf-8")
            window = MainWindow()
            try:
                window.srt_path = str(subtitle)
                with patch("app.main.QDesktopServices.openUrl", return_value=True) as open_url:
                    window.open_srt()
                    self.assertEqual(open_url.call_args.args[0].toLocalFile(), str(subtitle).replace("\\", "/"))
                    window.open_folder()
                    self.assertEqual(open_url.call_args.args[0].toLocalFile(), str(subtitle.parent).replace("\\", "/"))
            finally:
                window.close()


if __name__ == "__main__":
    unittest.main()
