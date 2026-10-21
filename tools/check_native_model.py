"""Catch native model/worker teardown hangs before expensive Windows packaging."""
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    if '--child' not in sys.argv:
        subprocess.run([sys.executable, __file__, '--child'], cwd=ROOT, check=True, timeout=180)
        return
    from app.core.pipeline import run_alignment
    original = (ROOT / 'examples/msa.txt').read_text(encoding='utf-8').strip()
    results = []
    for attempt in range(2):
        started = time.monotonic()
        result = run_alignment(str(ROOT / 'examples/msa.wav'), original, model_size='small',
            progress_cb=lambda value, message: print(message, flush=True))
        assert result.asr_word_count > 0 and result.cues
        assert ' '.join(c.text for c in result.cues).split() == original.split()
        assert all(0 <= c.start < c.end <= result.audio_duration + .001 for c in result.cues)
        results.append({'attempt': attempt + 1, 'returned_after_model_teardown': True,
                        'seconds': round(time.monotonic() - started, 2), 'asr_words': result.asr_word_count})
        print('Native alignment returned after model teardown: ' + str(attempt + 1), flush=True)
    destination = ROOT / 'verification/windows-x64/native-model-preflight.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({'ok': True, 'real_model': 'small', 'attempts': results}, indent=2))


if __name__ == '__main__':
    main()
