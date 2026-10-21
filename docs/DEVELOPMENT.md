# Development and a complete example

Use Python 3.11 on Windows x64 or Intel macOS. For a quick source-only check, create/activate a virtual environment, run `python -m pip install -r requirements.txt`, then `python -m unittest discover -s tests -v`. Those tests do not download model weights. Headless CI sets `QT_QPA_PLATFORM=offscreen`; native packaging tests must use the real platform plugin.

For actual audio, follow [BUILDING.md](BUILDING.md) through native media/model preparation. This downloads controlled FFmpeg and the platform's pinned models. Then:

```sh
python run.py
python run.py --cli -a examples/msa.wav -t examples/msa.txt -o example.srt --model small
python run.py --cli -a examples/egyptian.wav -t examples/egyptian.txt -o egyptian.srt --model small
python run.py --acceptance-test --examples examples --report verification/source-gui.json --work-dir .build/source-gui
```

Open the generated SRT in a subtitle editor. Check that the reference's words and diacritics survived, then listen for timing errors. The sample SRT files illustrate output, not manually certified word boundaries. The optional `ARABICALIGNER_MODELS_DIR` selects an explicit development Hub-layout cache; frozen packages ignore it and use their bundled models. No personal files outside the checkout are required.

To regenerate the openly dedicated synthetic examples, obtain eSpeak NG 1.52.0 from its official project, then run `python tools/generate_examples.py --help` and the documented arguments. The generator needs the native sem/ar voice and does not use MBROLA. Regeneration can change bytes if voice/build versions differ; provenance records exact hashes.

Add behavior regressions to `tests/test_regression_*.py`. Prefer concrete failures involving reference preservation, timestamp validity, error recovery or bundle resources. Do not mock out inference and describe the test as model acceptance. Run the suite, explain the change and evidence in a PR, and follow [CONTRIBUTING.md](../CONTRIBUTING.md).
