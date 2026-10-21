# -*- coding: utf-8 -*-
"""ArabicAligner — Local CPU-only Arabic forced alignment -> SRT.

GUI: Drag&Drop audio, paste/load TXT, Align & Create SRT, progress, Open SRT/Folder/Save As.
Local processing. No application uploads.
"""
import os
import sys
import threading
import traceback

APP_NAME = "ArabicAligner"
from app.version import APP_VERSION
from app.models import MODEL_NAMES


def _app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


try:
    from PySide6.QtCore import Qt, Signal, QObject, QThread
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QTextEdit, QCheckBox, QProgressBar, QFileDialog, QMessageBox,
        QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox, QSplitter, QStatusBar,
    )
    HAS_QT = True
except ImportError:
    HAS_QT = False


AUDIO_EXTS = (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".mp4", ".aac", ".wma")


class WorkerSignals(QObject):
    progress = Signal(float, str)
    finished = Signal(object)
    failed = Signal(str)


if HAS_QT:
    class AlignThread(QThread):
        def __init__(self, audio, text, opts):
            super().__init__()
            self.audio = audio
            self.text = text
            self.opts = opts
            self.signals = WorkerSignals()

        def run(self):
            try:
                # ensure app.core importable both in dev and frozen
                base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                root = os.path.dirname(base)
                for p in (root, base):
                    if p not in sys.path:
                        sys.path.insert(0, p)
                try:
                    from app.core.pipeline import run_alignment
                except ImportError:
                    from core.pipeline import run_alignment  # frozen layout fallback

                def cb(p, msg):
                    self.signals.progress.emit(float(p), str(msg))

                res = run_alignment(
                    self.audio, self.text,
                    model_size=self.opts.get("model_size", "small"),
                    show_tags=self.opts.get("show_tags", False),
                    max_chars=self.opts.get("max_chars", 84),
                    max_dur=self.opts.get("max_dur", 6.5),
                    min_dur=self.opts.get("min_dur", 0.9),
                    pause_break=self.opts.get("pause_break", 0.6),
                    cpu_threads=self.opts.get("cpu_threads", 4),
                    progress_cb=cb,
                )
                self.signals.finished.emit(res)
            except Exception as e:
                tb = traceback.format_exc()[-4000:]
                self.signals.failed.emit(f"{e}\n\n{tb}")


if HAS_QT:
    class DropLabel(QLabel):
        fileDropped = Signal(str)

        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self.setAcceptDrops(True)

        def dragEnterEvent(self, e):
            if e.mimeData().hasUrls():
                e.acceptProposedAction()
            else:
                e.ignore()

        def dropEvent(self, e):
            for u in e.mimeData().urls():
                p = u.toLocalFile()
                if p:
                    self.fileDropped.emit(p)
                    break


    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} — Offline Arabic Forced Alignment")
            self.resize(980, 700)
            self.audio_path = ""
            self.srt_path = ""
            self.last_result = None
            self.thread = None
            self._build()

        def _build(self):
            central = QWidget()
            self.setCentralWidget(central)
            root = QVBoxLayout(central)

            title = QLabel("🎙️ ArabicAligner — محاذاة عربية محلية (CPU فقط) → SRT")
            title.setAlignment(Qt.AlignCenter)
            title.setStyleSheet("font-size:16px;font-weight:bold;padding:6px;")
            root.addWidget(title)

            # Audio row
            audio_box = QGroupBox("1) ملف الصوت (MP3 / WAV / M4A) — اسحب وأفلت هنا")
            al = QVBoxLayout(audio_box)
            self.drop = DropLabel("⬇️ اسحب ملف الصوت هنا أو اضغط Browse")
            self.drop.setAlignment(Qt.AlignCenter)
            self.drop.setMinimumHeight(64)
            self.drop.setStyleSheet(
                "border:2px dashed #888;border-radius:10px;padding:14px;color:#444;background:#fafafa;")
            self.drop.fileDropped.connect(self.set_audio)
            al.addWidget(self.drop)
            row = QHBoxLayout()
            self.audio_lbl = QLabel("لا يوجد ملف بعد")
            self.audio_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            btn_browse = QPushButton("Browse…")
            btn_browse.clicked.connect(self.browse_audio)
            row.addWidget(self.audio_lbl, 1)
            row.addWidget(btn_browse)
            al.addLayout(row)
            root.addWidget(audio_box)

            # Text row
            text_box = QGroupBox("2) النص العربي الأصلي (يبقى كما هو في SRT)")
            tl = QVBoxLayout(text_box)
            self.text = QTextEdit()
            self.text.setPlaceholderText(
                "الصق النص هنا… يمكن أن يحتوي على تشكيل وتاجات ElevenLabs مثل [whispers] [laughs] [sad]\n"
                "التاجات تُحذف من نسخة المحاذاة فقط ولا تُعتبر كلامًا منطوقًا.")
            self.text.setLayoutDirection(Qt.RightToLeft)
            self.text.setMinimumHeight(150)
            tl.addWidget(self.text)
            trow = QHBoxLayout()
            btn_load = QPushButton("Load TXT…")
            btn_load.clicked.connect(self.load_txt)
            btn_clear = QPushButton("Clear")
            btn_clear.clicked.connect(self.text.clear)
            self.chars_lbl = QLabel("0 chars")
            self.text.textChanged.connect(
                lambda: self.chars_lbl.setText(f"{len(self.text.toPlainText())} chars"))
            trow.addWidget(btn_load)
            trow.addWidget(btn_clear)
            trow.addStretch(1)
            trow.addWidget(self.chars_lbl)
            tl.addLayout(trow)
            root.addWidget(text_box, 1)

            # Options
            opt_box = QGroupBox("Options")
            ol = QHBoxLayout(opt_box)
            self.chk_tags = QCheckBox("إظهار التاجات في SRT")
            self.chk_tags.setChecked(False)  # default hidden
            self.chk_tags.setToolTip("الافتراضي: إخفاء التاجات مثل [laughs] من ملف SRT")
            ol.addWidget(self.chk_tags)
            ol.addWidget(QLabel("Model:"))
            self.cmb_model = QComboBox()
            self.cmb_model.addItems(MODEL_NAMES)
            self.cmb_model.setToolTip(
                "النموذج السريع small مدمج ويعمل بدون إنترنت." if len(MODEL_NAMES) == 1 else
                "النموذجان مدمجان ويعملان بدون إنترنت. small أسرع وlarge-v3-turbo أدق عادةً.")
            ol.addWidget(self.cmb_model)
            ol.addWidget(QLabel("Max chars:"))
            self.spn_chars = QSpinBox()
            self.spn_chars.setRange(40, 120)
            self.spn_chars.setValue(84)
            ol.addWidget(self.spn_chars)
            ol.addWidget(QLabel("Max sec:"))
            self.spn_dur = QDoubleSpinBox()
            self.spn_dur.setRange(3.0, 10.0)
            self.spn_dur.setSingleStep(0.5)
            self.spn_dur.setValue(6.5)
            ol.addWidget(self.spn_dur)
            ol.addStretch(1)
            root.addWidget(opt_box)

            # Run
            run_row = QHBoxLayout()
            self.btn_run = QPushButton("🚀 Align & Create SRT")
            self.btn_run.setMinimumHeight(44)
            self.btn_run.setStyleSheet(
                "font-size:15px;font-weight:bold;background:#1a7f37;color:white;border-radius:8px;padding:8px;")
            self.btn_run.clicked.connect(self.start_align)
            run_row.addWidget(self.btn_run, 1)
            root.addLayout(run_row)

            self.prog = QProgressBar()
            self.prog.setRange(0, 100)
            self.prog.setValue(0)
            root.addWidget(self.prog)
            self.status_lbl = QLabel("جاهز. كل شيء يعمل محليًا بدون إنترنت.")
            root.addWidget(self.status_lbl)

            # Output row
            out_row = QHBoxLayout()
            self.btn_open_srt = QPushButton("Open SRT")
            self.btn_open_srt.setEnabled(False)
            self.btn_open_srt.clicked.connect(self.open_srt)
            self.btn_folder = QPushButton("Open Folder")
            self.btn_folder.setEnabled(False)
            self.btn_folder.clicked.connect(self.open_folder)
            self.btn_save = QPushButton("Save As…")
            self.btn_save.setEnabled(False)
            self.btn_save.clicked.connect(self.save_as)
            out_row.addWidget(self.btn_open_srt)
            out_row.addWidget(self.btn_folder)
            out_row.addWidget(self.btn_save)
            out_row.addStretch(1)
            root.addLayout(out_row)
            self.setStatusBar(QStatusBar())

        # ---- slots ----
        def set_audio(self, p):
            if os.path.isdir(p):
                return
            if not p.lower().endswith(AUDIO_EXTS):
                QMessageBox.warning(self, "Audio", f"صيغة غير مدعومة:\n{p}\n\nالمدعوم: MP3/WAV/M4A/OGG/FLAC/MP4")
                return
            self.audio_path = p
            self.audio_lbl.setText(p)
            self.drop.setText(f"✅ {os.path.basename(p)}")

        def browse_audio(self):
            p, _ = QFileDialog.getOpenFileName(
                self, "Choose audio", "",
                "Audio (*.mp3 *.wav *.m4a *.ogg *.flac *.mp4 *.aac *.wma)")
            if p:
                self.set_audio(p)

        def load_txt(self):
            p, _ = QFileDialog.getOpenFileName(self, "Load TXT", "", "Text (*.txt *.md)")
            if p:
                try:
                    with open(p, encoding="utf-8-sig") as f:
                        self.text.setPlainText(f.read())
                except Exception:
                    with open(p, encoding="cp1256", errors="ignore") as f:
                        self.text.setPlainText(f.read())

        def start_align(self):
            if self.thread is not None and self.thread.isRunning():
                return
            txt = self.text.toPlainText()
            if not self.audio_path or not os.path.exists(self.audio_path):
                QMessageBox.warning(self, "Missing", "اختر ملف الصوت أولًا.")
                return
            if not txt.strip():
                QMessageBox.warning(self, "Missing", "الصق النص أو حمّل ملف TXT.")
                return
            self.btn_run.setEnabled(False)
            self.prog.setValue(1)
            self.status_lbl.setText("Starting…")
            opts = dict(
                model_size=self.cmb_model.currentText(),
                show_tags=self.chk_tags.isChecked(),
                max_chars=int(self.spn_chars.value()),
                max_dur=float(self.spn_dur.value()),
                min_dur=0.9, pause_break=0.6,
                cpu_threads=max(1, min(4, (os.cpu_count() or 4) - 1)),
            )
            self.thread = AlignThread(self.audio_path, txt, opts)
            self.active_audio_path = self.audio_path
            self.btn_open_srt.setEnabled(False)
            self.btn_folder.setEnabled(False)
            self.btn_save.setEnabled(False)
            self.thread.signals.progress.connect(self.on_prog)
            self.thread.signals.finished.connect(self.on_done)
            self.thread.signals.failed.connect(self.on_fail)
            self.thread.start()

        def on_prog(self, p, msg):
            self.prog.setValue(int(max(0, min(1, p)) * 100))
            self.status_lbl.setText(msg)
            self.statusBar().showMessage(msg)

        def on_done(self, res):
            self.btn_run.setEnabled(True)
            self.prog.setValue(100)
            self.last_result = res
            base, _ = os.path.splitext(self.active_audio_path)
            default_out = base + ".srt"
            try:
                with open(default_out, "w", encoding="utf-8-sig") as f:
                    f.write(res.srt_text)
                self.srt_path = default_out
            except Exception as e:
                self.srt_path = ""
                self.btn_save.setEnabled(True)
                self.status_lbl.setText("تمت المحاذاة. استخدم Save As لحفظ النتيجة في مكان آخر.")
                QMessageBox.warning(self, "Save As", f"تعذر الحفظ بجانب الصوت. النتيجة محفوظة مؤقتًا؛ استخدم Save As.\n{e}")
                return
            self.status_lbl.setText(
                f"✅ Done: {len(res.cues)} cues | {res.audio_duration:.1f}s | "
                f"low-conf {res.low_conf_rate:.0%} — {default_out}")
            self.btn_open_srt.setEnabled(True)
            self.btn_folder.setEnabled(True)
            self.btn_save.setEnabled(True)
            QMessageBox.information(
                self, "Done",
                f"تم إنشاء SRT بنجاح ✅\n\nCues: {len(res.cues)}\n"
                f"Duration: {res.audio_duration:.1f}s\nFile:\n{default_out}")

        def on_fail(self, msg):
            self.btn_run.setEnabled(True)
            self.status_lbl.setText("❌ Failed — see details")
            QMessageBox.critical(self, "Alignment failed", msg[:3000])

        def open_srt(self):
            if self.srt_path and os.path.exists(self.srt_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(self.srt_path)))

        def open_folder(self):
            if self.srt_path:
                QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(os.path.abspath(self.srt_path))))

        def save_as(self):
            if not self.last_result:
                return
            p, _ = QFileDialog.getSaveFileName(self, "Save SRT", self.srt_path or "output.srt",
                                               "Subtitles (*.srt)")
            if p:
                try:
                    with open(p, "w", encoding="utf-8-sig") as f:
                        f.write(self.last_result.srt_text)
                except OSError as e:
                    QMessageBox.warning(self, "Save failed", str(e))
                    return
                self.srt_path = p
                self.btn_open_srt.setEnabled(True)
                self.btn_folder.setEnabled(True)
                self.status_lbl.setText(f"Saved: {p}")

        def closeEvent(self, event):
            if self.thread is not None and self.thread.isRunning():
                QMessageBox.information(self, "Processing", "انتظر حتى تنتهي المحاذاة قبل إغلاق البرنامج.")
                event.ignore()
                return
            event.accept()


def main():
    if not HAS_QT:
        print("PySide6 is not installed. Run: pip install PySide6")
        print("Or use CLI: python -m app.cli --help")
        sys.exit(2)
    # frozen: fix sys.path for app.core
    base = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(base)
    for p in (root, base):
        if p not in sys.path:
            sys.path.insert(0, p)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
