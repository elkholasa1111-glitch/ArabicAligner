# Installation and usage

[English introduction](../README.md) · [الدليل العربي](../README.ar.md) · [Troubleshooting](TROUBLESHOOTING.md)

## Choose a package

Get the current **1.2.0-beta.1** preview from [Releases](https://github.com/elkholasa1111-glitch/ArabicAligner/releases/tag/v1.2.0-beta.1). The full installers include models and media tools. Processing is local; development and build preparation downloads are separate.

| Platform | Package | Models |
| --- | --- | --- |
| Windows x64 | `ArabicAligner_1.2.0-beta.1_Windows_x64_Setup.exe` | small; large-v3-turbo |
| macOS 15+ Intel x86_64 | `ArabicAligner_1.2.0-beta.1_macOS_Intel.dmg` | small |

The Windows build targets Windows 10/11 x64; installed-copy testing used Windows Server 2022 x64. Mac testing used Intel macOS 15.7.9. Apple Silicon, Windows ARM, and Linux have not been validated. See [Verification](VERIFICATION.md) for the tested environments, signing, offline checks, and remaining device/manual checks.

### Check a download

Download the matching `SHA256SUMS-win32.txt` or `SHA256SUMS-darwin.txt` from the same release. Compare the package's SHA-256 against the entry in that file.

Windows PowerShell, from your download directory:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath '.\ArabicAligner_1.2.0-beta.1_Windows_x64_Setup.exe'
```

macOS Terminal, from your download directory:

```sh
shasum -a 256 ArabicAligner_1.2.0-beta.1_macOS_Intel.dmg
```

Checksums detect download corruption; they do not replace publisher signing.

### Install

**Windows:** run the per-user installer and open **ArabicAligner Preview** from the Start menu. The preview installs separately from the historical 1.1.1 edition. The installer is unsigned.

**Mac:** open the DMG and copy **ArabicAligner Preview.app** to Applications. The Intel app uses an ad-hoc signature and is not Apple notarized. The separate Preview name allows an older copy to remain alongside it.

For download/security prompts, follow [Troubleshooting](TROUBLESHOOTING.md). Keep system protections enabled. No GPU or CUDA installation is needed.

## First alignment

1. Download and extract [the original example ZIP](https://github.com/elkholasa1111-glitch/ArabicAligner/releases/download/v1.2.0-beta.1/ArabicAligner_Examples_1.2.0-beta.1.zip).
2. Select or drop `examples/msa.wav` in the application.
3. Use **Load TXT** to load `examples/msa.txt`, or paste its text.
4. Choose **small**. Keep the initial cue-length and duration settings.
5. Click **Align Create SRT** and wait for completion. The SRT is saved beside the audio; if saving fails, use **Save As** to select a writable location.
6. Use **Open SRT** or **Open Folder**. Open the UTF-8 SRT in your subtitle/video editor and listen through it to review timing.

The supplied text begins:

> مَرْحَبًا بِكُمْ. هذا مثالٌ قصيرٌ لاختبارِ الترجمة.

The [actual Windows output](demo/windows-small-msa.srt) begins:

```srt
1
00:00:00,110 --> 00:00:01,860
مَرْحَبًا بِكُمْ.
```

Model/platform results can differ. This output illustrates the installed workflow; its timestamps are not independently annotated ground truth. Try `egyptian.wav` with `egyptian.txt` as a second original example. The voice is synthetic Arabic, not an authentic Egyptian benchmark.

## Your recordings

Supply the script actually spoken. Unspoken reference words remain in the SRT with estimated timing, so remove unrelated introductions, headings, or edits from the reference when they are not spoken. Keep any diacritics you want in the exported text.

The picker offers WAV, MP3, M4A, OGG, FLAC, MP4, AAC, and WMA. Decoder availability determines actual format support; protected/DRM media is unsupported. WAV and decoding of MP3, M4A, and FLAC have native acceptance evidence. Other formats need specific validation.

**small** is the fast model and the only Mac model. Windows also includes **large-v3-turbo**, which needs more resources and is not guaranteed to perform better on every recording. Both use local CPU inference.

**Max chars** and **Max sec** guide cue splitting. **low-conf** is an internal text-matching signal: listen to the output when it is high, and review timing even when it is low. Music, silence, repetitions, overlapping speech, cuts, and mismatching reference text can produce estimated timings. See [Architecture](ARCHITECTURE.md).

Jobs cannot currently be cancelled. Closing is deferred while processing runs. After a supported error, correct the input and retry. Preserve a saved SRT before starting another job if you need to keep that version.

## Command line

Use quoted absolute paths for your audio, UTF-8 script, and output, especially when names contain spaces or Arabic. `--help` lists available arguments. `--model small` selects the small model on both platforms.

### Installed Windows application

With the default per-user installation, from PowerShell:

```powershell
& "$env:LOCALAPPDATA\Programs\ArabicAligner Preview\ArabicAligner.exe" --cli --help
& "$env:LOCALAPPDATA\Programs\ArabicAligner Preview\ArabicAligner.exe" --cli -a 'C:\Audio\recording.wav' -t 'C:\Audio\script.txt' -o 'C:\Audio\subtitles.srt' --model small
```

If you selected a different installation folder, use its executable path. Terminal launches retain CLI diagnostics; GUI launches hide their own console and write a local diagnostic log.

### Installed Mac application

With the app in Applications, from Terminal:

```sh
"/Applications/ArabicAligner Preview.app/Contents/MacOS/ArabicAligner" --cli --help
"/Applications/ArabicAligner Preview.app/Contents/MacOS/ArabicAligner" --cli -a "/path/to/recording.wav" -t "/path/to/script.txt" -o "/path/to/subtitles.srt" --model small
```

Replace the illustrative input/output paths with your own files. The tested packaged CLI supports Arabic and spaced paths on both systems.

### Source checkout

After the environment and assets in [Development](DEVELOPMENT.md) and [Building](BUILDING.md) are prepared, from the repository root:

```sh
python run.py --cli --help
python run.py --cli -a examples/msa.wav -t examples/msa.txt -o example.srt --model small
```

## Get help

Use [Troubleshooting](TROUBLESHOOTING.md), then [Support](../SUPPORT.md). For a report, include the release, OS version, architecture, model, and a small permitted example. Keep private recordings, transcripts, account information, and full logs out of public issues.
