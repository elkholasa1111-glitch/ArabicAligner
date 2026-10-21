"""SRT read/write utilities (UTF-8, Arabic-safe)."""
from __future__ import annotations


def fmt_ts(sec: float) -> str:
    total_ms = max(0, int(round(float(sec) * 1000)))
    total_s, ms = divmod(total_ms, 1000)
    h, rem = divmod(total_s, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def cues_to_srt(cues) -> str:
    lines: list[str] = []
    for c in cues:
        lines.append(str(c.idx))
        lines.append(f"{fmt_ts(c.start)} --> {fmt_ts(c.end)}")
        lines.append(c.text)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def write_srt(path: str, cues) -> str:
    data = cues_to_srt(cues)
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write(data)
    return path
