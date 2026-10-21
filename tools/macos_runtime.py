"""PyInstaller runtime setup for an offline Finder-launched macOS app."""
import os
import sys

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# GUI bundles have no terminal. Native dependencies still write diagnostics.
# Keep them in the standard user log directory, never inside the app bundle.
if sys.stdout is None or sys.stderr is None:
    from pathlib import Path
    log_dir = Path.home() / "Library" / "Logs" / "ArabicAligner"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_stream = (log_dir / "ArabicAligner.log").open("a", encoding="utf-8", buffering=1)
    except OSError:
        log_stream = open(os.devnull, "w")
    if sys.stdout is None:
        sys.stdout = log_stream
    if sys.stderr is None:
        sys.stderr = log_stream
