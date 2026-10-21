# ArabicAligner

[العربية](README.ar.md) · [Start here](#start-here) · [Download](https://github.com/elkholasa1111-glitch/ArabicAligner/releases) · [Help](SUPPORT.md)

Synchronize an existing Arabic script with its recording and export editable SRT subtitles. ArabicAligner uses local CPU speech recognition as a timing guide, matches it against your supplied text, and keeps the original words and diacritics in the subtitles. It is a desktop application with a CLI, maintained by Mahmoud Hussein Attay Elsayed. Original application copyright: Elkholasa. See [provenance](docs/PROVENANCE.md).

## Start here

The first unified public release is **1.2.0-beta.1**, a preview combining the existing Windows and Intel Mac editions. Download only assets listed on the release page; source archives are not installers. While a candidate is being built, an absent platform asset is not an available download. [Release verification](docs/VERIFICATION.md) distinguishes completed tests from outstanding work.

| Platform | Asset name | Models | Status and requirements |
| --- | --- | --- | --- |
| Windows x64 | `ArabicAligner_1.2.0-beta.1_Windows_x64_Setup.exe` | small; large-v3-turbo | Unsigned. Windows 10/11 x64 build target; see actual tested OS in verification. Preview installs separately from 1.1.1. |
| macOS Intel x86_64 | `ArabicAligner_1.2.0-beta.1_macOS_Intel.dmg` | small only | Ad-hoc signing, no Developer ID or notarization. macOS 15+ package target; native verification uses macOS 15 Intel. |

Apple Silicon, Windows ARM, Linux, and every OS version within the build targets are not validated. Intel does not imply universal. CPU inference can be slow on older laptops; the target MacBook Air 2015 itself still requires a user hardware check. No CUDA or GPU setup is required.

1. Download the matching installer from [Releases](https://github.com/elkholasa1111-glitch/ArabicAligner/releases). Compare its SHA-256 with the platform's `SHA256SUMS` file. Keep the installer and corresponding license/source assets available.
2. Windows: run the installer for your user. macOS: open the DMG and copy ArabicAligner Preview.app into Applications, keeping an older copy separately if needed. For security prompts, follow [troubleshooting](docs/TROUBLESHOOTING.md); do not disable device protections.
3. Browse to or drop a local audio file. Paste the exact script or load a UTF-8 TXT. Choose small (fast) or, on Windows, large-v3-turbo.
4. Click **Align & Create SRT**. The application saves UTF-8 SRT beside the audio. Use **Open SRT**, **Open Folder**, or **Save As**. Open the SRT with a subtitle editor or your video editor and review its timing.

MP3, WAV, M4A, OGG, FLAC, MP4, AAC, and WMA are offered by the file picker. Actual support depends on the included FFmpeg decoders; encrypted/DRM media is not supported. WAV examples are covered by native acceptance checks. Other input formats need format-specific validation; see verification.

## What the tool does and where review matters

This is reference-text alignment, not a translation service. Recognition supplies approximate word timestamps; fuzzy matching and interpolation place the original reference words. Whitespace is normalized. Optional bracket tags can be displayed; they have no independent audio timing. Punctuation, pauses, character limits, and duration limits guide cue splitting.

Unspoken or mismatched reference words are retained with estimated timing. Silence may yield uniformly estimated, low-confidence timings. A mismatching script can therefore produce a syntactically valid but inaccurate SRT. The low-confidence percentage is an internal matching heuristic, **not an independent accuracy score**. Diacritics are preserved in display text rather than recognized acoustically. Overlapping speech, music, accents, repetitions, and recording cuts need human review. There is no guarantee of 100% accuracy or coverage of all Arabic dialects. No external CTC/MMS alignment engine is implemented.

There is currently no cancellation button. Closing is deferred while a job runs. After a failure, retry is available; if automatic saving fails, use Save As. Do not rely on forced termination to preserve an unfinished job.

## Try an original example

[examples/](examples/README.md) contains short original MSA and Egyptian-worded scripts, synthetic WAVs, provenance, and example SRTs. The synthetic Arabic voice is not an authentic Egyptian pronunciation benchmark. It tests the actual pipeline and text preservation; timing quality still needs listening review.

```sh
python run.py --cli -a examples/msa.wav -t examples/msa.txt -o example.srt --model small
```

Install the source environment and model/media assets first: [development](docs/DEVELOPMENT.md), [native builds](docs/BUILDING.md), [architecture](docs/ARCHITECTURE.md). Frozen applications also accept `--cli`. Run the Windows CLI from a terminal to see progress; a desktop GUI launch hides its own console and records diagnostic output in the application log. The output SRT is the result to check.

## Privacy, licensing, and contributing

The installed full packages contain their models and media runtime. They perform audio processing locally without accounts, API keys, telemetry, or application uploads. Build/development setup downloads dependencies and model weights. Local output and diagnostic errors can contain filenames and reference text: review logs before sharing them. See [privacy and troubleshooting](docs/TROUBLESHOOTING.md).

The original application source is [MIT](LICENSE). This does **not** make the entire installer MIT. Qt/PySide, FFmpeg, Python, model weights, and native dependencies retain their own terms. Read [third-party notices](LICENSES.md), [replacement/source instructions](docs/LICENSING.md), and the license files inside each package.

[Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Support](SUPPORT.md) · [Changelog](CHANGELOG.md) · [Roadmap](docs/ROADMAP.md). GitHub issues are the public support channel; no response SLA is promised. 
