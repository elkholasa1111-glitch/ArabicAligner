from pathlib import Path
import sys
ROOT = Path(SPECPATH)
sys.path.insert(0, str(ROOT / 'packaging'))
sys.path.insert(0, str(ROOT))
from bundle import inputs, trim_qt
from app.version import APP_VERSION, BUNDLE_VERSION
if sys.platform != 'darwin':
    raise SystemExit('Build macOS on macOS Intel.')
datas, binaries, hidden = inputs(ROOT)
a = Analysis([str(ROOT / 'run.py')], pathex=[str(ROOT)], binaries=binaries, datas=datas,
    hiddenimports=hidden, excludes=['torch', 'torchaudio', 'tensorflow', 'scipy', 'imageio_ffmpeg'],
    runtime_hooks=[str(ROOT / 'tools/runtime.py')], noarchive=False)
trim_qt(a)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='ArabicAligner', debug=False,
    strip=False, upx=False, console=False, target_arch='x86_64', codesign_identity=None)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='ArabicAligner')
app = BUNDLE(coll, name='ArabicAligner.app', bundle_identifier='com.elkholasa.arabicaligner.preview',
    version=BUNDLE_VERSION, info_plist={'CFBundleDisplayName': 'ArabicAligner ' + APP_VERSION,
    'CFBundleShortVersionString': BUNDLE_VERSION, 'LSMinimumSystemVersion': '13.3',
    'NSHighResolutionCapable': True})
