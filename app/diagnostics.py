"""Packaged offline acceptance check, callable without a Python installation."""
import argparse
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import time
import traceback


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', required=True)
    parser.add_argument('--audio')
    parser.add_argument('--native-gui', action='store_true', help='Exercise the native Cocoa/Windows Qt plugin')
    args = parser.parse_args(argv)
    Path(args.report).resolve().parent.mkdir(parents=True, exist_ok=True)
    report = {'ok': False, 'network_blocked_in_process': True, 'models': {},
              'platform': sys.platform, 'frozen': bool(getattr(sys, 'frozen', False))}
    def deny(*args, **kwargs):
        raise RuntimeError('Network is disabled during the offline acceptance check')
    socket.socket.connect = deny
    socket.create_connection = deny
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['QT_QPA_PLATFORM'] = (
        'cocoa' if args.native_gui and sys.platform == 'darwin' else
        'windows' if os.name == 'nt' else 'offscreen')
    report['qt_platform'] = os.environ['QT_QPA_PLATFORM']
    try:
        from PySide6.QtWidgets import QApplication
        from app.main import MainWindow, APP_VERSION
        qt = QApplication.instance() or QApplication([])
        window = MainWindow()
        window.ensurePolished()
        if args.native_gui:
            window.show()
        qt.processEvents()
        screenshot = str(Path(args.report).with_suffix('.png'))
        window.grab().save(screenshot)
        report['gui_screenshot'] = screenshot
        report['version'] = APP_VERSION
        report['gui_models'] = [window.cmb_model.itemText(i) for i in range(window.cmb_model.count())]
        from app.models import MODEL_NAMES, MODEL_FOLDERS
        assert report['gui_models'] == list(MODEL_NAMES)
        window.close()
        from app.core.audio import convert_to_wav16k, find_ffmpeg
        from app.core.whisper_aligner import _bundled_hf_cache, _model_path, transcribe_with_words
        from app.core.pipeline import run_alignment
        report['ffmpeg'] = find_ffmpeg()
        if getattr(sys, 'frozen', False):
            # A system FFmpeg must not make an incomplete installer pass.
            from app.resources import resource_roots
            ffmpeg_path = Path(report['ffmpeg']).resolve()
            assert any(ffmpeg_path.is_relative_to(root.resolve()) for root in resource_roots())
        cache = _bundled_hf_cache()
        if getattr(__import__('sys'), 'frozen', False):
            assert cache and {p.name for p in Path(cache).iterdir() if p.is_dir()} == set(MODEL_FOLDERS)
        for name in report['gui_models']:
            started = time.monotonic()
            path = _model_path(cache, name) if cache else None
            if not path:
                raise RuntimeError(f'Missing complete model: {name}')
            if args.audio:
                wav = convert_to_wav16k(args.audio)
                try:
                    words, _, text = transcribe_with_words(wav, model_size=name)
                finally:
                    Path(wav).unlink(missing_ok=True)
                if not words:
                    raise RuntimeError(f'No speech recognized by {name}')
                result = run_alignment(args.audio, text, model_size=name)
                assert result.cues and '-->' in result.srt_text
                assert all(0 <= c.start < c.end <= result.audio_duration + 0.001 for c in result.cues)
                assert all(a.end <= b.start for a, b in zip(result.cues, result.cues[1:]))
                srt_path = str(Path(args.report).with_name(Path(args.report).stem + '-' + name + '.srt'))
                Path(srt_path).write_text(result.srt_text, encoding='utf-8-sig')
                report['models'][name] = {'ok': True, 'words': len(words), 'cues': len(result.cues),
                                         'seconds': round(time.monotonic() - started, 2), 'path': path,
                                         'srt_file': srt_path}
            else:
                from faster_whisper import WhisperModel
                model = WhisperModel(path, device='cpu', compute_type='int8', cpu_threads=2, local_files_only=True)
                del model
                report['models'][name] = {'ok': True, 'path': path}
        report['ok'] = True
    except Exception:
        report['error'] = traceback.format_exc()
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if report['ok'] else 1
