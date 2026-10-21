"""Frozen runtime privacy defaults and GUI logging; no uploads."""
import os
import sys
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
gui_log = sys.platform == 'win32' and not any(flag in sys.argv for flag in
    ('--cli', '--acceptance-test', '--self-test'))
if sys.stdout is None or sys.stderr is None or gui_log:
    from pathlib import Path
    directory = (Path.home() / 'Library/Logs/ArabicAligner' if sys.platform == 'darwin'
                 else Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'ArabicAligner/Logs')
    try:
        directory.mkdir(parents=True, exist_ok=True)
        stream = (directory / 'ArabicAligner.log').open('a', encoding='utf-8', buffering=1)
    except OSError:
        stream = open(os.devnull, 'w')
    sys.stdout = stream if gui_log else (sys.stdout or stream)
    sys.stderr = stream if gui_log else (sys.stderr or stream)
if sys.platform == 'win32':
    # Frozen Python isolates PYTHONIOENCODING. Arabic CLI paths must also work
    # when output is redirected to a pipe rather than a Windows console.
    for output_stream in (sys.stdout, sys.stderr):
        if hasattr(output_stream, 'reconfigure'):
            output_stream.reconfigure(encoding='utf-8', errors='backslashreplace')
