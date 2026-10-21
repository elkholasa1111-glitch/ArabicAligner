# Troubleshooting and local privacy

A blocked unsigned installer can be inspected through the operating system's normal file information/security UI. Check the repository, checksum, and provenance before choosing an OS-provided per-app exception. On macOS consult Apple's current instructions for opening a trusted unidentified-developer app. If enterprise policy forbids it, ask that device's administrator or build from source. Do not disable Gatekeeper, SmartScreen, antivirus, or the firewall globally, and do not run an unknown bypass script.

Missing model/FFmpeg errors usually indicate a partial download, incomplete app copy, or quarantined dependency. Re-download the full platform installer, compare SHA-256, and copy the complete .app or install directory. Source setup needs the explicit asset-preparation step. An offline error does not trigger an automatic model download.

For a save error use Save As in a writable folder. Avoid editing a source recording in place while a job is running. There is no cancellation yet; let the worker finish. A failure can be retried. Preserve your original audio/text; only SRT output is written beside them. Temporary converted WAV files are removed after processing; a crash can leave OS temp files.

No application telemetry, user accounts, cloud transcription or cloud transcription API integration is included. Builds and model preparation do access package/source/model hosts. Local logs, error messages and filenames can reveal personal paths or reference contents; inspect and redact them before opening public issues. Windows GUI logs are under `%LOCALAPPDATA%/ArabicAligner/Logs`, and Mac GUI logs under `~/Library/Logs/ArabicAligner`. Deleting a shared log does not revoke a credential that might have been pasted into it.

Report reproducible failures through [SUPPORT.md](../SUPPORT.md). Share a short original example you are authorized to distribute rather than client/team recordings. For vulnerabilities use [SECURITY.md](../SECURITY.md).
