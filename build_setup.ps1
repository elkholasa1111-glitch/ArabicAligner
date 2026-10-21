$ErrorActionPreference = 'Stop'
python tools/build_native_media.py
if ($LASTEXITCODE) { exit $LASTEXITCODE }
python tools/build_native_numpy.py
if ($LASTEXITCODE) { exit $LASTEXITCODE }
python -m pip install -r requirements.txt
python tools/prepare_release_assets.py
if ($LASTEXITCODE) { exit $LASTEXITCODE }
python tools/release.py
exit $LASTEXITCODE
