# -*- coding: utf-8 -*-
"""CLI fallback (works without GUI): python -m app.cli -a audio.mp3 -t text.txt -o out.srt"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    ap = argparse.ArgumentParser(description="ArabicAligner offline CLI")
    ap.add_argument("-a", "--audio", required=True)
    ap.add_argument("-t", "--text", required=True, help="TXT file (utf-8) or literal text with --raw")
    ap.add_argument("--raw", action="store_true", help="treat --text as literal string")
    ap.add_argument("-o", "--out", default="")
    ap.add_argument("--model", default="small")
    ap.add_argument("--show-tags", action="store_true")
    ap.add_argument("--max-chars", type=int, default=84)
    ap.add_argument("--max-dur", type=float, default=6.5)
    args = ap.parse_args()

    if args.raw:
        text = args.text
    else:
        with open(args.text, encoding="utf-8-sig") as f:
            text = f.read()

    from app.core.pipeline import run_alignment

    def cb(p, m):
        print(f"[{int(p*100):3d}%] {m}", flush=True)

    res = run_alignment(
        args.audio, text, model_size=args.model, show_tags=args.show_tags,
        max_chars=args.max_chars, max_dur=args.max_dur, progress_cb=cb,
    )
    out = args.out or (os.path.splitext(args.audio)[0] + ".srt")
    with open(out, "w", encoding="utf-8-sig") as f:
        f.write(res.srt_text)
    print(f"Wrote {out} ({len(res.cues)} cues)")


if __name__ == "__main__":
    main()
