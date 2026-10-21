"""Shared resource collection; platform bootloaders remain native."""
import importlib.metadata
from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_all


def inputs(root):
    from app.models import MODEL_FOLDERS
    assets = root / ('offline_assets-macos' if sys.platform == 'darwin' else 'offline_assets')
    datas, binaries, hidden = [], [], []
    for package in ('faster_whisper', 'ctranslate2', 'onnxruntime'):
        d, b, h = collect_all(package)
        datas += d
        binaries += b
        hidden += h
    for distribution in importlib.metadata.distributions():
        for relative in distribution.files or []:
            if any(part in relative.name.upper() for part in ('LICENSE', 'COPYING', 'NOTICE')):
                source = Path(distribution.locate_file(relative))
                if source.is_file():
                    datas.append((str(source), str(Path('licenses', distribution.metadata['Name'], Path(relative).parent))))
    for source in (Path(sys.base_prefix) / 'LICENSE.txt', Path(sys.base_prefix) / 'LICENSE'):
        if source.is_file():
            datas.append((str(source), 'licenses/python'))
    for filename in ('LICENSE', 'LICENSES.md', 'README.md', 'README.ar.md'):
        datas.append((str(root / filename), '.'))
    datas += [(str(root / 'third_party'), 'third_party'), (str(assets / 'MANIFEST.txt'), 'offline_assets')]
    datas += [(str(root / 'native-ctranslate2/licenses'), 'licenses/ctranslate2-source'),
              (str(root / 'native-ctranslate2/build-info.json'), 'third_party/ctranslate2-build')]
    for folder in MODEL_FOLDERS:
        model = assets / 'models' / folder
        if not model.is_dir():
            raise RuntimeError('Missing prepared model: ' + folder)
        for source in model.rglob('*'):
            relative = source.relative_to(model)
            if source.is_file() and relative.parts[0] in ('snapshots', 'refs'):
                datas.append((str(source.resolve()), str(Path('offline_assets/models', folder, relative.parent))))
    for source in (assets / 'ffmpeg').iterdir():
        if source.is_file():
            binaries.append((str(source), 'offline_assets/ffmpeg'))
    return datas, binaries, hidden


def trim_qt(analysis):
    forbidden = ('Qt6Pdf', 'QtPdf', 'Qt6Svg', 'QtSvg', 'Qt6Qml', 'QtQml',
                 'Qt6Quick', 'QtQuick', 'Qt6VirtualKeyboard', 'QtVirtualKeyboard')
    def allowed(entry):
        name = entry[0].replace('\\', '/')
        if any(part in name for part in forbidden):
            return False
        return not any('/plugins/' + part + '/' in '/' + name for part in
                       ('imageformats', 'iconengines', 'platforminputcontexts'))
    analysis.binaries = [entry for entry in analysis.binaries if allowed(entry)]
    analysis.datas = [entry for entry in analysis.datas if allowed(entry)]
