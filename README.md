# ArabicAligner

**Turn an Arabic script and its recording into editable SRT subtitles.**

[العربية](README.ar.md) · [Download](#download) · [Quick start](#quick-start) · [User guide](docs/USAGE.md) · [Help](SUPPORT.md)

[![Source checks](https://github.com/elkholasa1111-glitch/ArabicAligner/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/elkholasa1111-glitch/ArabicAligner/actions/workflows/ci.yml)

ArabicAligner synchronizes an existing Arabic script with its audio. Local speech recognition provides a timing guide; the subtitle text comes from your script, preserving its words and diacritics. Use the desktop interface or the command line on Windows x64 and Intel macOS.

- **Keep your wording:** export the supplied text and diacritics rather than replacing them with the recognizer's transcript.
- **Work locally:** full release packages include models and media tools. Processing needs no account, API key, or internet connection.
- **Control subtitle length:** adjust cue length and duration, then save UTF-8 SRT for your editing workflow.

## Download

Current release: **[1.2.0-beta.1 — public preview](https://github.com/elkholasa1111-glitch/ArabicAligner/releases/tag/v1.2.0-beta.1)**. Choose an installer below; GitHub's source ZIP is for development.

| Platform | Download | Included models |
| --- | --- | --- |
| Windows x64 | [Windows installer · approximately 1.93 GB](https://github.com/elkholasa1111-glitch/ArabicAligner/releases/download/v1.2.0-beta.1/ArabicAligner_1.2.0-beta.1_Windows_x64_Setup.exe) | small (fast); large-v3-turbo |
| macOS 15+ · Intel x86_64 | [Mac disk image · approximately 577 MB](https://github.com/elkholasa1111-glitch/ArabicAligner/releases/download/v1.2.0-beta.1/ArabicAligner_1.2.0-beta.1_macOS_Intel.dmg) | small (fast) |

Windows packages are unsigned. The Mac application is ad-hoc signed and is not Apple notarized. See [installation](docs/USAGE.md), [security-prompt help](docs/TROUBLESHOOTING.md), and the checksums and third-party sources on the [release](https://github.com/elkholasa1111-glitch/ArabicAligner/releases/tag/v1.2.0-beta.1).

The Windows build targets Windows 10/11 x64; installed-copy acceptance ran on Windows Server 2022 x64. The Mac package targets macOS 15+ and was tested on Intel macOS 15.7.9. Apple Silicon, Windows ARM, and Linux are unverified. Older hardware, including MacBook Air 2015, needs a device check. See [tested environments and results](docs/VERIFICATION.md).

## Quick start

1. Install the package for your platform. On Windows, run the per-user installer. On Mac, open the DMG and copy **ArabicAligner Preview.app** to Applications.
2. [Download and extract the original examples](https://github.com/elkholasa1111-glitch/ArabicAligner/releases/download/v1.2.0-beta.1/ArabicAligner_Examples_1.2.0-beta.1.zip). Choose `examples/msa.wav` in the application, then load `examples/msa.txt` with **Load TXT**.
3. Choose **small** and click **Align Create SRT**. The result is saved beside the audio. Use **Open SRT**, **Open Folder**, or **Save As** to inspect or copy it.
4. Open the SRT in your subtitle or video editor and listen through it to check timing before publishing.

For your own recording, supply the text actually spoken. The [user guide](docs/USAGE.md) covers formats, model choices, CLI commands, and recovery from errors.

## Application preview

Actual installed applications after processing the openly licensed example with real model inference and SRT output:

| Windows x64 | Intel macOS |
| --- | --- |
| [![Windows application after aligning the Arabic example](docs/screenshots/windows-small-msa.png)](docs/screenshots/windows-small-msa.png) | [![Intel Mac application after aligning the Arabic example](docs/screenshots/macos-small-msa.png)](docs/screenshots/macos-small-msa.png) |

Inspect an actual [Windows SRT](docs/demo/windows-small-msa.srt) or [Mac SRT](docs/demo/macos-small-msa.srt), and the [original example text and audio](examples/README.md).

## How alignment works

`Audio + your Arabic script → local word timestamps → reference-text matching → SRT`

Recognition supplies approximate timestamps. Matching and interpolation place the original reference words into cues. Punctuation, pauses, and length and duration limits guide cue splitting. Whitespace is normalized; words and diacritics remain in the output. ArabicAligner does not translate between languages. See [Architecture](docs/ARCHITECTURE.md).

### Accuracy and current limits

- **Review timing.** Music, overlapping speech, repetitions, cuts, and dialect differences can reduce alignment quality. No independently measured accuracy percentage is claimed.
- **Use a matching script.** Unspoken or mismatching words are retained with estimated timing. Silence can produce low-confidence estimates. A valid SRT can still need substantial correction.
- **Treat low confidence as a review signal.** It measures internal text matching, not independently calibrated timing accuracy.
- **Allow jobs to finish.** Cancellation is not implemented. Closing is deferred during processing; retry and Save As are available after supported failure paths.

The original MSA and Egyptian-worded examples use a synthetic Arabic voice. They exercise the workflow and text preservation; they are not an authentic Egyptian speech benchmark. [Verification](docs/VERIFICATION.md) distinguishes source tests, installed GUI/CLI checks, offline checks, and remaining manual checks.

## Run from source

Use Python 3.11.9 on Windows x64 or Intel macOS. Follow [Development](docs/DEVELOPMENT.md) for a virtual environment and dependencies, then [Building](docs/BUILDING.md) for models and media assets. Those setup steps download dependencies.

After preparing the environment and assets:

```sh
python run.py
python run.py --cli -a examples/msa.wav -t examples/msa.txt -o example.srt --model small
```

Packaged applications also accept `--cli`; see [platform commands](docs/USAGE.md). Source checks run on Windows and Intel macOS. Native package builds and installed-copy acceptance are separate release operations.

## Privacy and licenses

Full installed packages process audio locally with bundled models. The application has no telemetry, account system, or application uploads. Development setup uses internet downloads. Local errors and logs may contain paths or reference text; review them before sharing. See [troubleshooting and privacy](docs/TROUBLESHOOTING.md).

Original application code is **[MIT licensed](LICENSE), copyright Elkholasa**. Dependencies and model weights retain separate licenses; MIT alone does not cover the whole installer. Read [third-party notices](LICENSES.md) and [source and library-replacement instructions](docs/LICENSING.md). Original examples use [CC0](examples/LICENSE-CC0.txt).

## Help and contribute

[Report a bug](https://github.com/elkholasa1111-glitch/ArabicAligner/issues/new?template=bug_report.yml) · [Request a feature](https://github.com/elkholasa1111-glitch/ArabicAligner/issues/new?template=feature_request.yml) · [Ask a usage question](https://github.com/elkholasa1111-glitch/ArabicAligner/issues/new?template=question.yml)

Maintained by **[Mahmoud Hussein Attay Elsayed](https://github.com/elkholasa1111-glitch)** for **Elkholasa**. See [Maintainership](MAINTAINERS.md) and [Source provenance](docs/PROVENANCE.md). Contributions can improve documentation, Arabic examples, regressions, diagnostics, or packaging; start with [Contributing](CONTRIBUTING.md).

[Support](SUPPORT.md) · [Security](SECURITY.md) · [Changelog](CHANGELOG.md) · [Roadmap](docs/ROADMAP.md)
