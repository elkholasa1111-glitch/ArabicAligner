"""Read-only resources in source, Windows onedir, and macOS app bundles."""
from pathlib import Path
import sys


def resource_roots() -> list[Path]:
    if not getattr(sys, "frozen", False):
        return [Path(__file__).resolve().parents[1]]
    executable_dir = Path(sys.executable).resolve().parent
    roots = []
    if getattr(sys, "_MEIPASS", None):
        roots.append(Path(sys._MEIPASS).resolve())
    # macOS: executable in Contents/MacOS, data in Contents/Resources.
    if executable_dir.name == "MacOS" and executable_dir.parent.name == "Contents":
        roots.extend([executable_dir.parent / "Resources", executable_dir.parent / "Frameworks"])
    roots.extend([executable_dir / "_internal", executable_dir])
    return list(dict.fromkeys(roots))
