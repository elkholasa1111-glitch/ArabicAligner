"""Fuzzy forced mapping: ORIGINAL (clean) words -> ASR word timestamps.

Handles: repetitions, numbers, hamza/ya variants, EN-inside-AR, partial failures.
Never raises on small failures: unmatched words are interpolated, never crash.
"""
from __future__ import annotations
from dataclasses import dataclass
import difflib


@dataclass
class TimedWord:
    display: str      # original orthography (with tashkeel, original digits)
    start: float
    end: float
    conf: float       # 0..1 (1 = exact match, lower = interpolated/fuzzy)
    is_tag: bool = False


def _sim(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    # fast path: substring / prefix (common for ة/ه، ال التعريف)
    if a in b or b in a:
        return 0.85
    return difflib.SequenceMatcher(None, a, b).ratio()


def map_reference_to_asr(
    display_tokens: list[str],
    align_keys: list[str],
    is_tag: list[bool],
    asr_words: list,
    asr_keys: list[str],
    audio_dur: float,
) -> list[TimedWord]:
    """DP alignment over normalized keys, then project ASR times onto reference."""
    from app.core.normalizer import normalize_for_align  # noqa (ensure consistent)
    n = len(display_tokens)
    m = len(asr_words)
    out: list[TimedWord] = []

    # Indices of speech tokens only (skip tags: they get zero-duration, attached later)
    ref_idx = [i for i in range(n) if not is_tag[i]]
    if not ref_idx:
        return []
    if m == 0 or audio_dur <= 0:
        # Total ASR failure -> uniform fallback, never crash
        dur = audio_dur if audio_dur > 0 else max(1.0, len(ref_idx) * 0.4)
        step = dur / max(1, len(ref_idx))
        t = 0.0
        for k, i in enumerate(ref_idx):
            out.append(TimedWord(display_tokens[i], t, min(t + step * 0.9, dur), 0.1))
            t += step
        return _reinsert_tags(display_tokens, is_tag, out, ref_idx)

    # Similarity matrix (ref_speech x asr)
    R = len(ref_idx)
    # Cap cost: for very long files (20min ~ 2500 words) DP O(R*M) ~ 6M cells, fine.
    # Use banded DP via difflib anchor seeds to stay fast: we do full DP but with
    # float scores; R,M ~ few thousand -> OK on i5 (<2s).
    import array
    # score[i][j] best score aligning ref[:i] to asr[:j]
    # Use two rows to save RAM.
    GAP = -0.35
    prev = [0.0] * (m + 1)
    # backpointer: store choice compactly only if needed; instead do Hirschberg-lite:
    # For simplicity + robustness we do greedy seeded alignment instead of full traceback
    # when R*M > 12M cells, else full DP with traceback.
    if R * m > 12_000_000:
        return _greedy_seed_align(display_tokens, align_keys, is_tag, ref_idx, asr_words, asr_keys, audio_dur)

    # Full DP with traceback matrix of bytes (0=diag,1=up/skip-ref,2=left/skip-asr)
    bt = bytearray((R + 1) * (m + 1))
    prev = [j * GAP * 0.5 for j in range(m + 1)]
    for i in range(1, R + 1):
        cur = [0.0] * (m + 1)
        cur[0] = i * GAP
        rk = align_keys[ref_idx[i - 1]]
        for j in range(1, m + 1):
            s = _sim(rk, asr_keys[j - 1])  # 0..1
            # reward exact matches strongly, punish weak fuzzy
            diag = prev[j - 1] + (s * 2.0 - 0.6)
            up = prev[j] + GAP          # skip reference word (deletion)
            left = cur[j - 1] + GAP * 0.5  # skip ASR word (insertion)
            best = diag
            choice = 0
            if up > best:
                best = up
                choice = 1
            if left > best:
                best = left
                choice = 2
            cur[j] = best
            bt[i * (m + 1) + j] = choice
        prev = cur

    # Traceback
    pairs: list[tuple[int, int]] = []  # (ref_pos, asr_pos)
    i, j = R, m
    while i > 0 and j > 0:
        c = bt[i * (m + 1) + j]
        if c == 0:
            pairs.append((i - 1, j - 1))
            i -= 1
            j -= 1
        elif c == 1:
            i -= 1
        else:
            j -= 1
    pairs.reverse()

    # Build timed words: for each ref position, collect aligned asr words
    from collections import defaultdict
    aligned: dict[int, list[int]] = defaultdict(list)
    for ri, aj in pairs:
        rk = align_keys[ref_idx[ri]]
        if _sim(rk, asr_keys[aj]) >= 0.45:
            aligned[ri].append(aj)

    timed_by_ref: dict[int, TimedWord] = {}
    for ri in range(R):
        gi = ref_idx[ri]
        if ri in aligned and aligned[ri]:
            js = aligned[ri]
            s = min(asr_words[j].start for j in js)
            e = max(asr_words[j].end for j in js)
            # confidence = mean similarity
            conf = sum(_sim(align_keys[gi], asr_keys[j]) for j in js) / len(js)
            timed_by_ref[ri] = TimedWord(display_tokens[gi], s, e, float(max(0.15, min(1.0, conf))))
        else:
            timed_by_ref[ri] = TimedWord(display_tokens[gi], -1.0, -1.0, 0.0)

    _interpolate_missing(timed_by_ref, R, asr_words, audio_dur)
    ordered = [timed_by_ref[ri] for ri in range(R)]
    return _reinsert_tags(display_tokens, is_tag, ordered, ref_idx)


def _greedy_seed_align(display_tokens, align_keys, is_tag, ref_idx, asr_words, asr_keys, audio_dur):
    """Fallback for huge inputs: seed exact matches then linear interpolate between seeds."""
    R = len(ref_idx)
    # map asr key -> positions
    from collections import defaultdict
    pos = defaultdict(list)
    for j, k in enumerate(asr_keys):
        pos[k].append(j)
    anchors: list[tuple[int, int]] = []
    last_j = -1
    for ri in range(R):
        k = align_keys[ref_idx[ri]]
        cands = [j for j in pos.get(k, []) if j > last_j]
        if cands:
            anchors.append((ri, cands[0]))
            last_j = cands[0]
    timed: dict[int, TimedWord] = {}
    for ri in range(R):
        gi = ref_idx[ri]
        # exact anchor?
        hit = next((a for a in anchors if a[0] == ri), None)
        if hit:
            j = hit[1]
            timed[ri] = TimedWord(display_tokens[gi], asr_words[j].start, asr_words[j].end, 0.95)
        else:
            timed[ri] = TimedWord(display_tokens[gi], -1.0, -1.0, 0.0)
    _interpolate_missing(timed, R, asr_words, audio_dur)
    return _reinsert_tags(display_tokens, is_tag, [timed[ri] for ri in range(R)], ref_idx)


def _interpolate_missing(timed_by_ref: dict[int, TimedWord], R: int, asr_words, audio_dur: float):
    """Fill unmatched runs without modifying ASR-derived anchor timestamps.

    Filling one word at a time made an interpolated word look like a real anchor
    to the next iteration.  The subsequent overlap repair then shifted genuine
    ASR matches.  Work from an immutable anchor list instead and divide only the
    free interval around each missing run.  A run with no available interval is
    represented by zero-duration words; segmentation can still render them as
    part of a valid cue without inventing time or moving a recognized word.
    """
    anchors = [ri for ri in range(R) if timed_by_ref[ri].start >= 0]

    if not anchors:
        # No usable match at all: distribute the reference uniformly as a
        # low-confidence fallback over the known audio duration.
        span = max(0.0, audio_dur)
        step = span / max(1, R)
        for ri in range(R):
            tw = timed_by_ref[ri]
            tw.start = ri * step
            tw.end = min(span, tw.start + step * 0.9)
            tw.conf = 0.1
        return

    def fill_run(first: int, last: int, left: int | None, right: int | None):
        count = last - first + 1
        if left is None:
            gap_start = 0.0
        else:
            gap_start = timed_by_ref[left].end
        if right is None:
            gap_end = max(0.0, audio_dur)
        else:
            gap_end = timed_by_ref[right].start

        # Preserve the recognized anchors even when Whisper timestamps overlap
        # or an edge anchor sits exactly at 0/audio duration.
        gap_start = max(0.0, min(gap_start, max(0.0, audio_dur)))
        gap_end = max(0.0, min(gap_end, max(0.0, audio_dur)))
        span = max(0.0, gap_end - gap_start)
        cell = span / count
        conf = 0.25 if left is not None and right is not None else 0.2
        for offset, ri in enumerate(range(first, last + 1)):
            tw = timed_by_ref[ri]
            if cell > 0:
                # Leave a small amount of separation within each allocated
                # cell, but never extend outside the real surrounding gap.
                pad = min(cell * 0.05, 0.02)
                tw.start = gap_start + offset * cell + pad
                tw.end = gap_start + (offset + 1) * cell - pad
                if tw.end < tw.start:
                    tw.start = tw.end = gap_start + (offset + 0.5) * cell
            else:
                tw.start = tw.end = gap_end
            tw.conf = conf

    previous_anchor: int | None = None
    for anchor in anchors:
        first = 0 if previous_anchor is None else previous_anchor + 1
        if first < anchor:
            fill_run(first, anchor - 1, previous_anchor, anchor)
        previous_anchor = anchor
    if previous_anchor is not None and previous_anchor + 1 < R:
        fill_run(previous_anchor + 1, R - 1, previous_anchor, None)


def _reinsert_tags(display_tokens, is_tag, ordered_speech: list[TimedWord], ref_idx) -> list[TimedWord]:
    """Reinsert tag tokens (zero-duration, is_tag=True) at original positions.

    If show_tags=False the exporter drops them; if True they attach to neighbor time.
    """
    speech_by_global = {g: tw for g, tw in zip(ref_idx, ordered_speech)}
    full: list[TimedWord] = []
    last_time = 0.0
    for i, tok in enumerate(display_tokens):
        if is_tag[i]:
            full.append(TimedWord(tok, last_time, last_time, 1.0, True))
        else:
            tw = speech_by_global[i]
            full.append(tw)
            last_time = tw.end
    # fix tag times to neighbor start (so "show tags" doesn't create 0-dur cue issues)
    for k, tw in enumerate(full):
        if tw.is_tag:
            # attach to next speech word start if exists else prev end
            nxt = next((full[j] for j in range(k + 1, len(full)) if not full[j].is_tag), None)
            if nxt is not None:
                tw.start = tw.end = nxt.start
            else:
                prv = next((full[j] for j in range(k - 1, -1, -1) if not full[j].is_tag), None)
                t = prv.end if prv else last_time
                tw.start = tw.end = t
    return full
