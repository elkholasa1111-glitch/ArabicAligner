"""Inspect actual linked media-library licensing, not package-name assumptions."""
import ctypes
import json
from pathlib import Path
import sys


def inspect():
    import av
    root = Path(av.__file__).parent
    candidates = list(root.rglob("*avutil*.dylib")) + list(root.rglob("*avutil*.dll"))
    candidates += list((root.parent / "av.libs").glob("*avutil*.dll"))
    if not candidates:
        raise RuntimeError("Cannot locate PyAV's actual FFmpeg utility library")
    library = ctypes.CDLL(str(candidates[0]))
    info = {"pyav_version": av.__version__, "library_file": candidates[0].name}
    for name in ("avutil_license", "avutil_configuration", "av_version_info"):
        function = getattr(library, name)
        function.restype = ctypes.c_char_p
        info[name] = function().decode("utf-8")
    if info["av_version_info"] != "8.1.3":
        raise RuntimeError("Release is not using the pinned controlled FFmpeg build")
    if "LGPL" not in info["avutil_license"] or any(flag in info["avutil_configuration"] for flag in
            ("--enable-gpl", "--enable-nonfree", "--enable-libx264", "--enable-libx265")):
        raise RuntimeError("Unexpected release media license/configuration")
    info["ok"] = True
    return info


if __name__ == "__main__":
    print(json.dumps(inspect(), indent=2))
