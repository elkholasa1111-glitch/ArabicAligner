"""Create redistributable, synthetic speech from original project text.

Run with an official eSpeak NG executable. The engine is not redistributed in
the app. Speech is synthetic; it is not a human-dialect accuracy benchmark.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import wave

ROOT = Path(__file__).resolve().parents[1]
TEXTS = {
    "msa": "مَرْحَبًا بِكُمْ. هذا مثالٌ قصيرٌ لاختبارِ الترجمة. نُحافِظُ على الكلماتِ والتشكيلِ، ونراجعُ التوقيتَ بعدَ الحفظ.",
    "egyptian": "أهلًا بيكم. ده مثال صغير بالمصري. بنختار ملف الصوت، وبنحط نفس الكلام، وبعدين بنراجع الترجمة ونحفظها.",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--espeak", required=True, type=Path)
    args = parser.parse_args()
    examples = ROOT / "examples"
    manifest = {"origin": "Original project-authored text, synthesized with eSpeak NG 1.52.0 (native sem/ar voice)",
                "license": "CC0-1.0", "human_recordings": False,
                "limitations": "Synthetic samples. Egyptian refers to script wording, not a validated Egyptian voice/accent.",
                "files": {}}
    for name, text in TEXTS.items():
        reference = examples / f"{name}.txt"
        reference.write_text(text + "\n", encoding="utf-8")
        # Some Windows eSpeak builds use narrow-character file APIs. Keep the
        # generator's temporary input/output paths separate from the Arabic
        # filesystem-path tests of ArabicAligner itself.
        with tempfile.TemporaryDirectory(prefix="arabicaligner-synthesis-") as temp:
            source_text = Path(temp, "input.txt")
            source_text.write_text(text, encoding="utf-8")
            raw = Path(temp, "output.wav")
            subprocess.run([str(args.espeak.resolve()), "--path=" + str(args.espeak.resolve().parent),
                            "-b", "1", "-v", "sem/ar", "-s", "135", "-f", str(source_text),
                            "-w", str(raw)], cwd=args.espeak.resolve().parent, check=True)
            with wave.open(str(raw), "rb") as source:
                params = source.getparams()
                frames = source.readframes(source.getnframes())
        # Include explicit leading/trailing silence for the full-flow tests.
        target = examples / f"{name}.wav"
        silence = b"\0" * (params.framerate * params.nchannels * params.sampwidth // 2)
        with wave.open(str(target), "wb") as result:
            result.setparams(params)
            result.writeframes(silence + frames + silence)
        for path in (reference, target):
            manifest["files"][path.name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                           "bytes": path.stat().st_size}
    (examples / "provenance.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
