from pathlib import Path
import os
import sys
ROOT = Path(SPECPATH)
sys.path.insert(0, str(ROOT / 'packaging'))
sys.path.insert(0, str(ROOT))
from bundle import inputs, trim_qt
if sys.platform != 'win32':
    raise SystemExit('Build Windows on Windows x64.')
windows = os.environ.get('WINDIR', r'C:\Windows')
os.environ['PATH'] = os.pathsep.join([str(ROOT / 'native/bin'), windows + r'\System32', windows,
                                    sys.base_prefix, str(Path(sys.prefix) / 'Scripts')])
datas, binaries, hidden = inputs(ROOT)
a = Analysis([str(ROOT / 'run.py')], pathex=[str(ROOT)], binaries=binaries, datas=datas,
    hiddenimports=hidden, excludes=['torch', 'torchaudio', 'tensorflow', 'scipy', 'imageio_ffmpeg'],
    runtime_hooks=[str(ROOT / 'tools/runtime.py')], noarchive=False)
trim_qt(a)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='ArabicAligner',
    debug=False, strip=False, upx=False, console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='ArabicAligner')
