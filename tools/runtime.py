"""Frozen runtime privacy defaults and GUI logging; no uploads."""
import os
import sys
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
if sys.stdout is None or sys.stderr is None:
    from pathlib import Path
    directory = (Path.home() / 'Library/Logs/ArabicAligner' if sys.platform == 'darwin'
                 else Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'ArabicAligner/Logs')
    try:
        directory.mkdir(parents=True, exist_ok=True)
        stream = (directory / 'ArabicAligner.log').open('a', encoding='utf-8', buffering=1)
    except OSError:
        stream = open(os.devnull, 'w')
    sys.stdout = sys.stdout or stream
    sys.stderr = sys.stderr or stream
