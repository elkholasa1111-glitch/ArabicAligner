"""Arabic text normalization for forced alignment (internal use only).

Original text is ALWAYS preserved for SRT output.
This module creates an internal alignment copy.
"""
from __future__ import annotations
import re
import unicodedata

# ElevenLabs-style tags: [whispers] [laughs] [sad] [pause] ... + <break> etc.
TAG_RE = re.compile(r"\[[^\]\n]{1,60}\]|\{[^\}\n]{1,60}\}|<[^>\n]{1,60}>", re.UNICODE)

# Tashkeel / diacritics
TASHKEEL_RE = re.compile(r"[\u0610-\u061A\u064B-\u065F\u06D6-\u06ED\u08E4-\u08FE]", re.UNICODE)
TATWEEL = "\u0640"

AR_INDIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
AR_PUNCT_MAP = str.maketrans({
    "،": ",",
    "؛": ";",
    "؟": "?",
    "«": '"',
    "»": '"',
    "’": "'",
    "‘": "'",
})

END_PUNCT = set([".", "!", "?", "؟", "…", ":", "؛", ";"])
HARD_BREAK_PUNCT = set([".", "!", "?", "؟", "…"])
SOFT_BREAK_PUNCT = set([",", "،", ";", "؛", ":", "—", "-", "–"])


def extract_tags(text: str) -> list[str]:
    return TAG_RE.findall(text)


def remove_tags(text: str) -> str:
    """Remove ElevenLabs-style tags from alignment copy only."""
    return TAG_RE.sub(" ", text)


def remove_tashkeel(text: str) -> str:
    text = TASHKEEL_RE.sub("", text)
    return text.replace(TATWEEL, "")


def normalize_for_align(token: str) -> str:
    """Aggressive-but-safe normalization used ONLY for matching/scoring."""
    t = token.strip()
    if not t:
        return ""
    # Unicode NFKC (folds presentation forms, fullwidth, etc.)
    t = unicodedata.normalize("NFKC", t)
    # lower english
    t = t.lower()
    # arabic-indic digits -> western (for matching only)
    t = t.translate(AR_INDIC_DIGITS)
    # unify punctuation variants
    t = t.translate(AR_PUNCT_MAP)
    # hamza / alef variants -> bare alef
    t = re.sub(r"[أإآٱ]", "ا", t)
    # alef maqsura -> ya, ta marbuta kept distinct? map ة->ه for fuzzy matching
    t = t.replace("ى", "ي")
    t = t.replace("ة", "ه")
    # hamza on waw/ya -> base
    t = t.replace("ؤ", "و").replace("ئ", "ي")
    # strip remaining isolated hamza variants cautiously: keep ء
    # remove non-alphanumeric except arabic block / latin / digits
    t = re.sub(r"[^\w\u0600-\u06FFa-z0-9ء]", "", t, flags=re.UNICODE)
    return t


def tokenize_preserving_original(text: str, strip_diacritics: bool = True) -> tuple[list[str], list[str], list[bool]]:
    """Split original text into display tokens.

    Returns (display_tokens, align_keys, is_tag_flags).
    Tags become standalone tokens flagged True (never treated as speech).
    """
    parts: list[str] = []
    pos = 0
    for m in TAG_RE.finditer(text):
        if m.start() > pos:
            parts.append(text[pos:m.start()])
        parts.append(m.group(0))  # tag as own chunk
        pos = m.end()
    if pos < len(text):
        parts.append(text[pos:])

    display_tokens: list[str] = []
    align_keys: list[str] = []
    is_tag: list[bool] = []
    for chunk in parts:
        if TAG_RE.fullmatch(chunk.strip()):
            display_tokens.append(chunk.strip())
            align_keys.append("")
            is_tag.append(True)
        else:
            for tok in chunk.split():
                tok = tok.strip()
                if not tok:
                    continue
                if TAG_RE.fullmatch(tok):
                    display_tokens.append(tok)
                    align_keys.append("")
                    is_tag.append(True)
                else:
                    # A token may still contain inline tag remnants; strip them
                    clean = TAG_RE.sub("", tok).strip()
                    if not clean:
                        continue
                    no_diac = remove_tashkeel(clean) if strip_diacritics else clean
                    key = normalize_for_align(no_diac)
                    # keep token even if key empty (e.g. pure punctuation/number symbols)
                    display_tokens.append(clean)
                    align_keys.append(key if key else normalize_for_align(clean))
                    is_tag.append(False)
    return display_tokens, align_keys, is_tag


def clean_text_for_asr_compare(text: str, strip_diacritics: bool = True) -> str:
    t = remove_tags(text)
    if strip_diacritics:
        t = remove_tashkeel(t)
    # collapse whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t
