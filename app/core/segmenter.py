"""Smart subtitle segmentation — NOT fixed word-count chunking.

Rules (in priority order):
 1) sentence boundaries (. ؟ ? ! …) -> hard break
 2) long pauses (> pause_break, default 0.6s) -> break
 3) soft punctuation (, ، ؛ ; : —) -> preferred break if length allows
 4) max chars per cue (default 84), max duration (default 6.5s), max words safety (14)
 5) min duration (default 0.9s): merge too-short cues forward when possible
 6) never split inside a tag; tags attach to their cue
"""
from __future__ import annotations
from dataclasses import dataclass
import re

HARD = set([".", "!", "?", "؟", "…"])
HARD_TAIL_RE = re.compile(r"[.؟?!\u2026:]$")
SOFT_TAIL_RE = re.compile(r"[,،؛;:—–-]$")


@dataclass
class Cue:
    idx: int
    start: float
    end: float
    text: str


@dataclass
class _SegmentWord:
    display: str
    start: float
    end: float


def _ends_hard(word: str) -> bool:
    w = word.strip()
    return bool(w) and (w[-1] in HARD or w.endswith("..."))


def _ends_soft(word: str) -> bool:
    w = word.strip()
    return bool(w) and (w[-1] in [",", "،", ";", "؛", ":", "—", "–", "-"])


def segment(
    timed_words,
    max_chars: int = 84,
    max_dur: float = 6.5,
    min_dur: float = 0.9,
    pause_break: float = 0.6,
    max_words: int = 14,
    show_tags: bool = False,
) -> list[Cue]:
    # Tags have no independent audio time.  When visible, fold each tag into
    # the following speech token (or the preceding token when trailing) so a
    # sentence break can never create a tag-only cue.
    words: list[_SegmentWord] = []
    pending_tags: list[str] = []
    for w in timed_words:
        display = w.display.strip()
        if not display:
            continue
        if w.is_tag:
            if show_tags:
                pending_tags.append(display)
            continue
        if pending_tags:
            display = " ".join([*pending_tags, display])
            pending_tags = []
        words.append(_SegmentWord(display, w.start, w.end))
    if show_tags and pending_tags and words:
        words[-1].display = " ".join([words[-1].display, *pending_tags])
    if not words:
        return []

    cues: list[Cue] = []
    cur: list = []
    cur_start = words[0].start

    def flush(end_time: float):
        nonlocal cur, cur_start
        if not cur:
            return
        text = " ".join(w.display for w in cur).strip()
        text = re.sub(r"\s+", " ", text)
        s = max(0.0, cur[0].start)
        e = max(end_time, cur[-1].end)
        if e <= s:
            # Interpolated unspoken words may legitimately have no available
            # time.  Place their cue immediately before that point instead of
            # extending beyond the end of the audio.
            point = s
            s = max(0.0, point - 0.3)
            e = point if point > 0 else 0.3
        else:
            # Prefer expanding a very short cue backward.  Extending its end
            # can run past the known final word/audio boundary.
            s = max(0.0, min(s, e - 0.3))
        # clamp cue end to last word end
        e = min(max(e, cur[-1].end), cur[-1].end + 0.15) if e > cur[-1].end + 0.4 else e
        cues.append(Cue(0, round(s, 3), round(e, 3), text))
        cur = []

    for k, w in enumerate(words):
        if cur:
            candidate_text = " ".join([*(x.display for x in cur), w.display])
            candidate_dur = w.end - cur[0].start
            exceeds_cap = (
                len(candidate_text) > max_chars
                or candidate_dur > max_dur
                or len(cur) + 1 > max_words
            )
            if exceeds_cap:
                prev = cur[-1]
                pause = max(0.0, w.start - prev.end)
                end_t = min(prev.end + 0.25, prev.end + pause * 0.5)
                end_t = min(end_t, cur[0].start + max_dur)
                flush(end_t)
        if not cur:
            cur_start = w.start
        cur.append(w)
        is_last = k == len(words) - 1
        nxt = words[k + 1] if not is_last else None

        cur_text = " ".join(x.display for x in cur)
        cur_dur = (cur[-1].end - cur[0].start) if cur else 0
        pause_after = (nxt.start - w.end) if nxt else 0.0

        hard = _ends_hard(w.display)
        soft = _ends_soft(w.display)
        too_long = len(cur_text) >= max_chars or cur_dur >= max_dur or len(cur) >= max_words

        should_break = False
        if is_last:
            should_break = True
        elif hard and (len(cur_text) > 20 or pause_after > 0.15 or cur_dur > 1.2):
            should_break = True
        elif pause_after >= pause_break:
            should_break = True
        elif too_long:
            should_break = True

        if should_break:
            # extend end slightly into pause (max +0.25s) for readability, but not into next word
            end_t = w.end
            if nxt:
                end_t = min(w.end + 0.25, w.end + max(0.0, pause_after * 0.5))
            end_t = min(end_t, cur[0].start + max_dur)
            flush(end_t)

    # post: merge too-short cues (likely split by music/noise) forward
    merged: list[Cue] = []
    i = 0
    while i < len(cues):
        c = cues[i]
        dur = c.end - c.start
        if dur < min_dur and i + 1 < len(cues) and len(c.text) < 30:
            nxt = cues[i + 1]
            combined = (c.text + " " + nxt.text).strip()
            if (
                (nxt.end - c.start) <= max_dur
                and (nxt.start - c.end) < pause_break
                and len(combined) <= max_chars
                and len(combined.split()) <= max_words
            ):
                merged.append(Cue(0, c.start, nxt.end, combined))
                i += 2
                continue
        merged.append(c)
        i += 1

    # Re-time connected groups of overlapping cues as a unit.  Pairwise
    # midpoint edits can make the middle cue negative when several
    # zero-duration unmatched words share the same timestamp.
    i = 0
    while i < len(merged):
        j = i
        group_end = merged[i].end
        while j + 1 < len(merged) and merged[j + 1].start < group_end:
            j += 1
            group_end = max(group_end, merged[j].end)
        if j > i:
            previous_end = merged[i - 1].end if i > 0 else 0.0
            group_start = max(previous_end, min(c.start for c in merged[i:j + 1]))
            span = max(0.001 * (j - i + 1), group_end - group_start)
            step = span / (j - i + 1)
            for offset, cue in enumerate(merged[i:j + 1]):
                cue.start = round(group_start + offset * step, 3)
                cue.end = round(group_start + (offset + 1) * step, 3)
        i = j + 1

    # reindex after merging and overlap normalization
    for n, c in enumerate(merged, 1):
        c.idx = n
    return merged
