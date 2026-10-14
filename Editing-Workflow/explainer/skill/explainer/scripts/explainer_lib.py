"""explainer_lib.py: shared pieces of the Explainer scripts (word anchors, the look, geometry).

The frame and safe zone are the Reels ones (reels_lib), so one file posts everywhere. A scene owns the scene area; the
captions own the band near the top (SPEC §6.1). Times in a storyboard are word anchors ("word:N", the Nth display word
of transcript.json), so the picture can never drift from the voice.
"""
import importlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def find_reels_lib():
    """Import reels_lib from the Reels skill: $REELS_SCRIPTS, installed side by side, or this repository."""
    cands = [os.environ.get("REELS_SCRIPTS", ""),
             os.path.join(HERE, "..", "..", "reels", "scripts"),                          # .claude/skills/reels/scripts
             os.path.join(HERE, "..", "..", "..", "..", "reels", "skill", "reels", "scripts")]   # Editing-Workflow/reels
    for c in cands:
        if c and os.path.exists(os.path.join(c, "reels_lib.py")):
            sys.path.insert(0, os.path.abspath(c))
            return importlib.import_module("reels_lib")
    sys.exit("reels_lib.py not found: install the Reels skill next to this one (.claude/skills/reels) or set REELS_SCRIPTS")


L = find_reels_lib()

SCENE = {"left": 65, "top": 520, "right": 1015, "bottom": 1248}   # inside L.SAFE; narrower below L.RIGHT_COL_TOP
CAPTION_BAND = (330, 470)
LEAD = 0.2          # an entrance starts this long before its word (beat-check's 0.15 to 0.25 s window)
MAX_OVERLAP = 0.3   # scenes hand over with at most this much overlap
BG_FADE = 0.4       # background cross-fade
TAIL = 0.5          # the composition runs this long past the voice

_ANCHOR = re.compile(r"^word:(\d+)$")


def resolve(ref, words, lead=False):
    """Seconds for an anchor: "word:N" is the start of the Nth display word (minus LEAD when lead); numbers pass."""
    if isinstance(ref, (int, float)) and not isinstance(ref, bool):
        return float(ref)
    m = _ANCHOR.match(str(ref))
    if not m or int(m.group(1)) >= len(words):
        raise ValueError("bad anchor %r" % (ref,))
    t = float(words[int(m.group(1))]["start"])
    return t - LEAD if lead else t


def anchor_text(ref, words):
    """The spoken word an anchor points at (what the kit's beat-check looks for), or "-" for a plain time."""
    if isinstance(ref, (int, float)) and not isinstance(ref, bool):
        return "-"
    resolve(ref, words)
    return str(words[int(_ANCHOR.match(str(ref)).group(1))]["text"])


def load_tokens(path=None):
    """The look: fonts, colours, backgrounds, the highlight box, motion timing (tokens.json next to scripts/)."""
    with open(path or os.path.join(HERE, "..", "tokens.json")) as f:
        return json.load(f)


_GLYPHS = {}


def glyphs():
    """Advance widths in em, measured in Chromium (dev/measure-glyphs.mjs): display700, display500, mono500."""
    if not _GLYPHS:
        with open(os.path.join(HERE, "glyphs.json")) as f:
            _GLYPHS.update(json.load(f))
    return _GLYPHS


def text_width(text, size, font="display700", spacing=0.0):
    """Pixels the text takes on one line at `size` px; `spacing` is the CSS letter-spacing in em."""
    g = glyphs()[font]
    text = str(text)
    return (sum(g.get(c, 0.6) for c in text) + spacing * len(text)) * size


def text_lines(text, size, width, font="display700", spacing=0.0):
    """Lines the browser wraps the text into at `width` px: words break between, never inside (a word wider than the
    width still takes one line; min_width is what catches it)."""
    words = str(text).split()
    if not words:
        return 1
    space = text_width(" ", size, font, spacing)
    lines, cur = 1, None
    for w in words:
        ww = text_width(w, size, font, spacing)
        if cur is None:
            cur = ww
        elif cur + space + ww <= width + 0.5:
            cur += space + ww
        else:
            lines, cur = lines + 1, ww
    return lines
