# Native build instructions

Build Windows on Windows x64, and macOS on Intel macOS with an x86_64 Python. CPython 3.11.9 and direct dependency versions are pinned; these are reproducible instructions, not a claim of bit-for-bit identical binaries. Release verification records the full resolved environment. Building requires network access, several GB of free disk, and CPU time. Runtime packages contain their models and require no setup downloads.

On Windows install the free Visual Studio C++ Build Tools x64 development environment, MSYS2 with make/diffutils, and Inno Setup 6. Start an x64 developer shell. The native media builder expects `C:\msys64\usr\bin\bash.exe` (override `ARABICALIGNER_BASH` if needed). GitHub Actions documents the same setup in `.github/workflows/release.yml`. On Intel Mac use Xcode Command Line Tools and Python 3.11.9 x86_64. Never cross-build the application and call that native verification.

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS: source .venv/bin/activate
python -m pip install -r requirements-build.txt
python tools/build_native_media.py
python tools/build_native_numpy.py
python -m pip install pybind11==3.0.1
python tools/build_native_ctranslate2.py
python -m pip install -r requirements.txt
python tools/prepare_release_assets.py
python tools/release.py
```

`build_native_media.py` verifies hashes in `third_party/sources.lock.json`, builds shared LGPL FFmpeg without GPL/nonfree/external codec libraries or networking, builds PyAV against that SDK, repairs its dynamic library paths, and installs the local wheel. Do not replace it with the unexamined upstream multimedia wheel for a release. Model revisions are pinned in `prepare_release_assets.py`; Windows stages both current models, macOS small only. Assets are materialized, not dangling Hub symlinks.

`release.py` builds PyInstaller, creates the platform installer, installs/copies it into a fresh Arabic path, uses empty home/model-cache directories, exercises real native Qt and inference under OS network restrictions, tests CLI and reopening, generates checksums, and mirrors corresponding sources. Windows acceptance needs administrator permissions **only for a temporary rule blocking the test executable's outbound networking**, removed in finally; installation itself is per-user. Do not run that acceptance command on a host where a policy disallows the rule. macOS uses sandbox-exec to deny networking for the test process. No global firewall or Gatekeeper settings are changed.

Standard CI runs source regressions only. Heavy packaging is an intentional `workflow_dispatch` at a lightweight tag pointing to the checked-out commit and a pre-existing **draft** release. Only this job has contents write permissions; PR jobs do not receive publish permissions. Uploads remain draft until reports and both packages are reviewed. Use public standard runners within available free plans; do not enable paid/larger runners. Per-file assets must stay below GitHub's 2 GiB limit.

The shared bundle collector is `packaging/bundle.py`. It collects actual package notices and removes unrelated Qt PDF/SVG/QML/Quick/virtual-keyboard plugin roots. Qt and FFmpeg libraries remain dynamically linked and replaceable. Check the actual final native inventory and license files; configuration intent alone is insufficient.

Output: `release/`, `verification/<platform>/`. Exact build/CI links and tested platforms belong in `VERIFICATION.md`. Older packaging helpers are compatibility entry points, not alternative release recipes.

Windows MSVC clean builds disable incremental depfile generation with make command overrides because the upstream awk recipe loses a backslash in this environment. Compilation remains enabled; the exact make options are recorded in native-build.json. Use a fresh build after source changes.

An exact earlier controlled-media cache key can be supplied on intentional runs after reviewing a platform-specific recipe change. Cached wheels must pass validate_media_cache.py (source pins, platform, flags, checksum and linked license). Default keys include the whole builder and source lock; no automatic broad fallback is used.

The same NumPy 1.26.4 source is compiled for release: macOS links system Accelerate and requires 13.3+, Windows uses the bundled numerical fallback. This avoids redistributing opaque GNU numerical runtimes from upstream wheels. CTranslate2 CPU model kernels are unchanged. The builder validates matrix multiplication and SVD; native application acceptance remains required.

CTranslate2 4.8.2 is built from the pinned source commit with CPU submodules. Ruy provides INT8 operations; Mac float operations use system Accelerate. Intel MKL/oneDNN/CUDA are disabled. Compiler OpenMP preserves CPU parallelism: LLVM libomp on Mac (`brew install libomp` for development) and MSVC OpenMP on Windows. This avoids accepting or redistributing Intel Developer Tools components. The source snapshot, submodule revisions, configure options and original component notices accompany the package. Build CTranslate2 before installing runtime requirements so pip retains the controlled wheel. Native acceptance checks INT8 availability and real recognition; performance still depends on hardware.

The packaged Intel Mac preview targets macOS 15, matching the native runner and the target Sequoia system. Individual libraries may be compiled with an older deployment target; the final payload audit checks every Mach-O minimum against the application declaration. Earlier macOS releases are not certified. CMake and compiler OpenMP are build prerequisites; on Mac install CMake/libomp with Homebrew before the recipe.
