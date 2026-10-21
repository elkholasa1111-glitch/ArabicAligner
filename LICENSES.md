# Third-party notices

The original application is licensed under [MIT](LICENSE), copyright Elkholasa. Each third-party component retains its original copyright, license and notices. See [source/replacement instructions](docs/LICENSING.md). License texts from the actual installed distributions are collected in each package's `licenses/` folder (Windows `_internal/licenses`; macOS `Contents/Resources/licenses`). This list is not a replacement for those texts or the native inventory.

| Component | License / source |
| --- | --- |
| Python | PSF; https://www.python.org/downloads/source/ |
| PySide6 Essentials / shiboken6 / Qt 6.11.2 widget runtime | LGPL-3.0 option and upstream third-party notices; https://doc.qt.io/qtforpython-6/licenses.html |
| FFmpeg 8.1.3 controlled shared build | LGPL-3.0-or-later; https://ffmpeg.org/legal.html; exact source/build lock and recipe in this repository |
| PyAV 17.1.0 | BSD-3-Clause; https://github.com/PyAV-Org/PyAV; links the controlled FFmpeg SDK |
| faster-whisper 1.2.1 | MIT; https://github.com/SYSTRAN/faster-whisper |
| CTranslate2 4.8.2 controlled CPU build | MIT plus preserved CPU-submodule notices; https://github.com/OpenNMT/CTranslate2 |
| ONNX Runtime 1.23.2 | MIT and bundled third-party notices; https://github.com/microsoft/onnxruntime |
| Bundled Silero VAD ONNX model from faster-whisper | MIT, Silero Team; https://github.com/snakers4/silero-vad; notice under third_party/licenses |
| NumPy 1.26.4 | BSD-3-Clause and bundled native-library notices; https://numpy.org/doc/1.26/license.html |
| tokenizers 0.23.2 | Apache-2.0; https://github.com/huggingface/tokenizers |
| huggingface_hub 1.31.0 | Apache-2.0; https://github.com/huggingface/huggingface_hub |
| Whisper weights | MIT; https://github.com/openai/whisper |
| Converted small snapshot | MIT upstream/model card; https://huggingface.co/Systran/faster-whisper-small/tree/536b0662742c02347bc0e980a01041f333bce120 |
| Converted turbo snapshot (Windows only) | MIT upstream/model card; https://huggingface.co/mobiuslabsgmbh/faster-whisper-large-v3-turbo/tree/0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf |
| PyInstaller bootloader | GPL with distribution exception; https://pyinstaller.org/en/stable/license.html |

Qt and FFmpeg remain dynamic components. The build excludes unrelated Qt PDF/SVG/QML/Quick/virtual keyboard plugins and opaque imageio FFmpeg executables. Source archives are release assets, not Git history. The supplied models are exactly those the platform GUI offers. No CTC/MMS/XLS-R or TTS runtime is implemented or bundled. Transitive and compiler-runtime notices accompany the actual packages; Windows notices are not assumed to describe macOS.

CTranslate2 source/submodule and compiler OpenMP notices are collected under `licenses/ctranslate2-source` in each native package. Intel developer runtime components from the old wheels are excluded from the controlled builds; no Intel EULA is accepted for the maintainer. Windows standard compiler runtime files retain their vendor redistribution terms.
