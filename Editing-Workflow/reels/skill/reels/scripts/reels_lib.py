"""reels_lib.py: shared pieces of the Reels scripts (safe zone, caption chunking, SRT).

The frame is 1080x1920. The safe zone is Meta's published box for Reels and Stories (top 14 %, bottom 35 %, 6 % each
side), the strictest of Instagram, TikTok and YouTube Shorts, so one file posts everywhere. Below RIGHT_COL_TOP the right
edge also holds the platforms' action column (like, comment, share), so anything centred down there is narrower.
"""
import json, re

W, H = 1080, 1920
SAFE_TOP, SAFE_BOTTOM, SAFE_SIDE = 269, 672, 65           # px clear of platform UI (PLAYBOOK §R3)
SAFE = {"left": SAFE_SIDE, "top": SAFE_TOP, "right": W - SAFE_SIDE, "bottom": H - SAFE_BOTTOM}   # 65,269 .. 1015,1248
RIGHT_COL_TOP, RIGHT_COL_W = 960, 150                     # the action column: keep centred content 150 px from both edges below y 960
NARROW = {"left": RIGHT_COL_W, "right": W - RIGHT_COL_W}  # 150 .. 930

# where the text-bearing formats sit (the top of their box), all inside SAFE
SLOTS = {"top": 290, "mid": 640, "low": 820}
CAPTION_TOP = 1050                                         # captions: two lines fit above SAFE bottom (1248)
CAPTION_MAX_BOTTOM = SAFE["bottom"]


def inside_safe(left, top, width, height):
    """True when the box sits inside the safe zone (and inside the narrow band if it reaches below RIGHT_COL_TOP)."""
    right, bottom = left + width, top + height
    if left < SAFE["left"] or top < SAFE["top"] or right > SAFE["right"] or bottom > SAFE["bottom"]:
        return False
    if bottom > RIGHT_COL_TOP and (left < NARROW["left"] or right > NARROW["right"]):
        return False
    return True


def load_words(path):
    d = json.load(open(path))
    words = d["words"] if isinstance(d, dict) and "words" in d else d
    return [{"text": str(w["text"]).strip(), "start": float(w["start"]), "end": float(w["end"])} for w in words if str(w["text"]).strip()]


_TRAIL = re.compile(r"[,.;:]+$")

def clean_word(text):
    """Caption form of a word: trailing commas, full stops, semicolons and colons go; ? ! $ % and apostrophes stay."""
    return _TRAIL.sub("", text.strip())


def ends_sentence(text):
    return bool(re.search(r"[.?!]['\"]?$", text.strip()))


def chunk_words(words, max_words=3, max_chars=18, gap=0.35, tail=0.6, min_dur=0.25):
    """Group transcript words into caption chunks.

    A new chunk starts when the current one has max_words, when adding the word would pass max_chars (spaces
    included), after a pause longer than `gap` between words, or after a word that ends a sentence (or a comma, once
    the chunk has two words). Each chunk shows from its first word's start until the next chunk starts, or `tail`
    seconds after its last word ends, whichever is first; never shorter than min_dur.
    Returns [{"start", "end", "words": [{"text", "start", "end"}]}].
    """
    chunks, cur = [], []
    for i, w in enumerate(words):
        t = clean_word(w["text"])
        if not t:
            continue
        ww = dict(w, text=t)
        if cur:
            prev = cur[-1]
            text_len = len(" ".join(x["text"] for x in cur)) + 1 + len(t)
            raw_prev = words[i - 1]["text"] if i > 0 else ""
            brk = (len(cur) >= max_words or text_len > max_chars or w["start"] - prev["end"] > gap
                   or ends_sentence(raw_prev) or (raw_prev.rstrip().endswith(",") and len(cur) >= 2))
            if brk:
                chunks.append(cur); cur = []
        cur.append(ww)
    if cur:
        chunks.append(cur)
    out = []
    for i, c in enumerate(chunks):
        start = c[0]["start"]
        nxt = chunks[i + 1][0]["start"] if i + 1 < len(chunks) else None
        end = max(c[-1]["end"] + tail if nxt is None else min(c[-1]["end"] + tail, nxt), start + min_dur)
        if nxt is not None and nxt > start:
            end = min(end, nxt)          # never overlap the next chunk, even to reach min_dur
        out.append({"start": round(start, 3), "end": round(end, 3), "words": c})
    return out


def srt_time(t):
    t = max(0.0, t)
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def wrap_two_lines(text, width=42):
    """At most two lines, broken at the space nearest the middle when the text is longer than one line."""
    if len(text) <= width or " " not in text:
        return text
    mid = len(text) // 2
    spaces = [i for i, ch in enumerate(text) if ch == " "]
    cut = min(spaces, key=lambda i: abs(i - mid))
    return text[:cut] + "\n" + text[cut + 1:]


def to_srt(chunks, width=42):
    lines = []
    for n, c in enumerate(chunks, 1):
        text = " ".join(w["text"] for w in c["words"])
        lines += [str(n), "%s --> %s" % (srt_time(c["start"]), srt_time(c["end"])), wrap_two_lines(text, width), ""]
    return "\n".join(lines)


def norm(s):
    return re.sub(r"[^a-z0-9$%' ]+", "", s.lower()).strip()


def full_digits(value, prefix="", suffix="", decimals=0):
    """Numbers are written out in full (PLAYBOOK §R5, STYLE-GUIDE): 1000 -> 1,000, never 1K."""
    return "%s%s%s" % (prefix, ("{:,.%df}" % int(decimals)).format(value), suffix)
