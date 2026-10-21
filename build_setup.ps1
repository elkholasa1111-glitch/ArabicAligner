$ErrorActionPreference = 'Stop'
function Invoke-CheckedPython {
    param([string[]]$PythonArguments)
    & python @PythonArguments
    if ($LASTEXITCODE -ne 0) { throw "Python build step failed ($LASTEXITCODE)." }
}
Invoke-CheckedPython -PythonArguments @('tools/build_native_media.py')
Invoke-CheckedPython -PythonArguments @('tools/build_native_numpy.py')
Invoke-CheckedPython -PythonArguments @('-m','pip','install','pybind11==3.0.1')
Invoke-CheckedPython -PythonArguments @('tools/build_native_ctranslate2.py')
Invoke-CheckedPython -PythonArguments @('-m','pip','install','-r','requirements.txt')
Invoke-CheckedPython -PythonArguments @('tools/prepare_release_assets.py')
Invoke-CheckedPython -PythonArguments @('tools/release.py')
