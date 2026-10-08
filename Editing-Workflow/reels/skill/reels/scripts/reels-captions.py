#!/usr/bin/env python3
"""reels-captions.py: an SRT caption file from a word-level transcript, for platforms that take one (YouTube Shorts,
TikTok, Facebook) next to the burned-in captions. Longer cues than the on-screen ones: up to 7 words, two lines of
about 42 characters, broken at pauses and sentence ends.

Usage:
  python3 reels-captions.py --transcript videos/<p>/transcript.json --out videos/<p>/captions.srt
                            [--max-words 7] [--max-chars 42] [--terms "HyperFrames,Parakeet"] [--duration 34.5]
--terms fixes the spelling of names and products (case-insensitive match of the whole word).
"""
import argparse, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reels_lib as L

ap = argparse.ArgumentParser()
ap.add_argument("--transcript", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--max-words", type=int, default=7)
ap.add_argument("--max-chars", type=int, default=42)
ap.add_argument("--terms", default="")
ap.add_argument("--duration", type=float, help="drop words after this time (the reel's length)")
a = ap.parse_args()

words = L.load_words(a.transcript)
if a.duration:
    words = [w for w in words if w["start"] < a.duration]
terms = [t.strip() for t in a.terms.split(",") if t.strip()]
for w in words:
    for t in terms:
        w["text"] = re.sub(r"(?i)\b%s\b" % re.escape(t), t, w["text"])
chunks = L.chunk_words(words, a.max_words, a.max_chars * 2, gap=0.6, tail=0.8, min_dur=1.0)
if a.duration and chunks:
    chunks[-1]["end"] = min(chunks[-1]["end"], a.duration)
open(a.out, "w").write(L.to_srt(chunks, a.max_chars))
print("wrote %s: %d cues" % (a.out, len(chunks)))
