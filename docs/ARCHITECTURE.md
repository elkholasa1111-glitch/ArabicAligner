# Architecture

The existing Python core is shared by the Windows and Intel macOS editions:

1. `app/core/audio.py`: convert a local input to temporary 16 kHz mono PCM WAV.
2. `whisper_aligner.py`: faster-whisper/CTranslate2 CPU INT8 word timestamps,
   Arabic language selection, and bundled Silero VAD via ONNX Runtime.
3. `normalizer.py`: derive comparison keys while retaining original displayed
   tokens, spelling, diacritics, and optional bracketed tags.
4. `mapper.py`: fuzzy sequence matching, timestamp anchors, and interpolation of
   unmatched reference words. Long inputs use a cheaper matching fallback.
5. `segmenter.py` and `srt.py`: group timed words and serialize UTF-8 SRT.

`pipeline.py` orchestrates these stages. `main.py` contains the existing Qt Widgets
GUI and worker thread. `cli.py` calls the same pipeline. `resources.py` handles
source, Windows onedir, and macOS Contents/Resources/Frameworks layouts.
`models.py` preserves platform model choices; `version.py` is the version source.

The application is ASR-assisted reference-text alignment, not a separate CTC
aligner. It does not translate between languages, replace the reference with
recognized text, or establish frame-accurate boundaries. Confidence is derived
from token matching; it is not a calibrated measure of transcription/timing
accuracy. Missing words, silence, repetitions, and long-input fallback can
produce estimated timings and require review.

Packaging is platform-native. Model snapshots are materialized as real files,
not external Hub-cache links. Release media libraries are built from pinned
source. Bundled model loading is explicit and local-files-only; inference has no
account, API key, upload endpoint, or telemetry integration added by this project.
