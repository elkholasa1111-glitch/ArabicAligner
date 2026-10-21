# Native installed-copy acceptance is part of the controlled release recipe.
$ErrorActionPreference = 'Stop'
python tools/release.py
exit $LASTEXITCODE
