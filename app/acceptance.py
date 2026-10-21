"""Exercise the real frozen Qt worker with original reference text and audio.

The native widgets receive drag/drop and mouse events. No pipeline, worker,
model, FFmpeg, or save function is mocked. A caller supplies OS network isolation.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import time
import traceback


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--examples", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--expect-network-blocked", action="store_true")
    parser.add_argument("--models", help="optional comma-separated subset for development tests")
    args = parser.parse_args(argv)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.work_dir.mkdir(parents=True, exist_ok=True)
    report = {"ok": False, "platform": sys.platform, "frozen": bool(getattr(sys, "frozen", False)),
              "gui_method": "Qt drag/drop and mouse events on native widgets; real QThread and pipeline",
              "original_reference_used": True, "cases": [], "network_os_enforced": args.expect_network_blocked}
    if args.expect_network_blocked:
        try:
            with socket.create_connection(("1.1.1.1", 443), timeout=3):
                raise RuntimeError("Network isolation control failed: outbound TCP was allowed")
        except OSError as error:
            report["network_probe_error"] = type(error).__name__
    os.environ["HF_HUB_OFFLINE"] = "1"
    from PySide6.QtCore import Qt, QTimer, QMimeData, QUrl, QPoint, QPointF
    from PySide6.QtGui import QDragEnterEvent, QDropEvent
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QMessageBox
    from app.main import MainWindow
    from app.models import MODEL_NAMES
    from app.version import APP_VERSION
    from app.core.whisper_aligner import _bundled_hf_cache, _model_path
    from app.resources import resource_roots
    qt = QApplication.instance() or QApplication([])
    report.update({"version": APP_VERSION, "qt_platform": qt.platformName(), "models": list(MODEL_NAMES)})
    if report['frozen'] and qt.platformName() != ('cocoa' if sys.platform == 'darwin' else 'windows'):
        raise RuntimeError('Release acceptance must use the native GUI platform')
    from PySide6.QtCore import QLibraryInfo
    report['qt_build'] = QLibraryInfo.build()
    import ctranslate2
    report['ctranslate2_version'] = ctranslate2.__version__
    report['cpu_compute_types'] = sorted(ctranslate2.get_supported_compute_types('cpu'))
    if 'int8' not in report['cpu_compute_types']:
        raise RuntimeError('The release runtime does not support the required CPU INT8 mode')
    if report["frozen"]:
        from tools.audit_media import inspect
        report["linked_media"] = inspect()
        from app.core.audio import convert_to_wav16k, find_ffmpeg
        import subprocess
        executable_version = subprocess.check_output([find_ffmpeg(), '-version'], text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        if 'ffmpeg version 8.1.3' not in executable_version or '--disable-gpl' not in executable_version:
            raise RuntimeError('Unexpected frozen FFmpeg executable build')
        report['ffmpeg_executable_version'] = executable_version.splitlines()[:3]
        import wave
        report['media_formats'] = {}
        for extension in ('mp3', 'm4a', 'flac'):
            converted = Path(convert_to_wav16k(str(args.examples / ('msa.' + extension))))
            try:
                with wave.open(str(converted), 'rb') as sound:
                    assert sound.getframerate() == 16000 and sound.getnchannels() == 1
                    assert sound.getnframes() > 16000
                    report['media_formats'][extension] = 'decoded to 16 kHz mono WAV'
            finally:
                converted.unlink(missing_ok=True)
    if args.models:
        selected = args.models.split(",")
        if any(name not in MODEL_NAMES for name in selected):
            raise RuntimeError("Requested acceptance model is not in this platform edition")
    else:
        selected = list(MODEL_NAMES)
    cache = _bundled_hf_cache()
    for name in selected:
        path = _model_path(cache, name) if cache else None
        if not path:
            raise RuntimeError(f"Missing bundled model: {name}")
        if report["frozen"] and not any(Path(path).resolve().is_relative_to(root.resolve()) for root in resource_roots()):
            raise RuntimeError("Frozen test is using a model outside the application")
    window = MainWindow()
    window.show()
    jobs = [("invalid", selected[0])] + [(example, model) for model in selected for example in ("msa", "egyptian")]
    jobs += [('silence', selected[0]), ('mismatch', selected[0])]
    state = {"index": -1, "active": False, "started": time.monotonic(), "message_error": None}
    deadline = time.monotonic() + 15 * 60

    def finish(error=None):
        timer.stop()
        if error:
            report["error"] = str(error).replace(str(args.work_dir), "<TEST>")
        else:
            report["ok"] = True
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        window.close()
        qt.exit(0 if report["ok"] else 1)

    def start_next():
        state["index"] += 1
        if state["index"] >= len(jobs):
            finish()
            return
        name, model = jobs[state["index"]]
        job_dir = args.work_dir / "تجربة المحاذاة مع مسافات" / f"{model}-{name}"
        job_dir.mkdir(parents=True, exist_ok=True)
        audio = job_dir / "ملف صوت sample.wav"
        if name == "invalid":
            audio.write_bytes(b"This is not a media file.")
            text = "هذا اختبار فشل وإعادة محاولة."
        elif name == 'silence':
            import wave
            with wave.open(str(audio), 'wb') as sound:
                sound.setnchannels(1)
                sound.setsampwidth(2)
                sound.setframerate(16000)
                sound.writeframes(b'\0' * (16000 * 2 * 4))
            text = 'هذا نص غير منطوق في تسجيل صامت.'
        elif name == 'mismatch':
            shutil.copy2(args.examples / 'msa.wav', audio)
            text = 'كوكب صحراء شجرة جزيرة مطر بحر.'
        else:
            shutil.copy2(args.examples / f"{name}.wav", audio)
            text = (args.examples / f"{name}.txt").read_text(encoding="utf-8-sig").strip()
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(audio.resolve()))])
        enter = QDragEnterEvent(QPoint(20, 20), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
        drop = QDropEvent(QPointF(20, 20), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
        QApplication.sendEvent(window.drop, enter)
        QApplication.sendEvent(window.drop, drop)
        if not window.audio_path or Path(window.audio_path).resolve() != audio.resolve():
            raise RuntimeError("Audio drop did not select the test file")
        window.text.setPlainText(text)
        window.cmb_model.setCurrentText(model)
        state.update({"audio": audio, "text": text, "active": True, "started": time.monotonic(), "message_error": None})
        QTest.mouseClick(window.btn_run, Qt.LeftButton)

    def poll():
        try:
            if time.monotonic() > deadline:
                raise RuntimeError("GUI acceptance timed out")
            for widget in qt.topLevelWidgets():
                if isinstance(widget, QMessageBox) and widget.isVisible():
                    if widget.icon() == QMessageBox.Critical:
                        state["message_error"] = widget.text()
                    widget.accept()
            if not state["active"]:
                start_next()
                return
            if window.thread is not None and window.thread.isRunning():
                return
            if not window.btn_run.isEnabled():
                return
            name, model = jobs[state["index"]]
            if name == "invalid":
                if not state["message_error"]:
                    raise RuntimeError("Invalid audio did not produce a visible failure")
                report["invalid_input_and_retry"] = True
            else:
                if state["message_error"] or window.prog.value() != 100 or not window.last_result:
                    raise RuntimeError("GUI processing failed: " + str(state["message_error"]))
                result = window.last_result
                if " ".join(cue.text for cue in result.cues).split() != state["text"].split():
                    raise RuntimeError("The original reference words or diacritics changed")
                if (name != 'silence' and result.asr_word_count <= 0) or not result.cues:
                    raise RuntimeError("No speech was recognized in the synthetic fixture")
                if name == 'silence' and (result.asr_word_count != 0 or result.low_conf_rate < .99):
                    raise RuntimeError('Silence did not produce the documented low-confidence fallback')
                if name == 'mismatch' and result.low_conf_rate < .5:
                    raise RuntimeError('Mismatched text was not marked predominantly low-confidence')
                if not all(0 <= c.start < c.end <= result.audio_duration + .001 for c in result.cues):
                    raise RuntimeError("Invalid cue times")
                if not all(a.end <= b.start for a, b in zip(result.cues, result.cues[1:])):
                    raise RuntimeError("Subtitle cues overlap")
                saved = Path(window.srt_path)
                if not saved.is_file() or saved.read_text(encoding="utf-8-sig") != result.srt_text:
                    raise RuntimeError("The GUI did not save the generated SRT")
                exported = args.report.parent / f"{args.report.stem}-{model}-{name}.srt"
                shutil.copy2(saved, exported)
                report["cases"].append({"example": name, "model": model, "preserved_reference": True,
                    "asr_words": result.asr_word_count, "reference_words": result.ref_word_count,
                    "low_confidence_rate": result.low_conf_rate, "cues": len(result.cues),
                    "audio_seconds": result.audio_duration, "processing_seconds": round(time.monotonic() - state["started"], 2),
                    "srt_file": exported.name, "saved_from_gui": True})
                window.grab().save(str(args.report.parent / f"{args.report.stem}-{model}-{name}.png"))
            state["active"] = False
        except Exception:
            finish(traceback.format_exc())

    timer = QTimer()
    timer.timeout.connect(poll)
    timer.start(100)
    return qt.exec()
