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

# Text and cards end by y 1235 (SOP S7, from the RAG reel: QA and the Reels guides judge the bottom 35% as covered by
# the app's caption and buttons, so one limit holds everywhere: here, in the E5 probe and in QA). Painted shapes with
# no text in them (particles, floors, illustration) may run on to PICTURE_BOTTOM: the lower frame is not left empty.
# Below RIGHT_COL_TOP everything keeps the narrow column.
SCENE = {"left": 65, "top": 520, "right": 1015, "bottom": 1235}
PICTURE_BOTTOM = 1650


def inside_scene(left, top, width, height):
    """True when a box sits inside the scene area, and inside the narrow column wherever it reaches below y 960."""
    if left < SCENE["left"] or top < SCENE["top"] or left + width > SCENE["right"] or top + height > SCENE["bottom"]:
        return False
    return top + height <= L.RIGHT_COL_TOP or (left >= L.NARROW["left"] and left + width <= L.NARROW["right"])
CAPTION_BAND = (330, 470)
LEAD = 0.2          # an entrance starts this long before its word (beat-check's 0.15 to 0.25 s window)
MAX_OVERLAP = 0.02  # scenes hand over on one cut: no overlap beyond rounding (SOP S9)
MIN_TEXT = 28       # the smallest text a phone viewer reads on the 1080 px frame (gate E5 checks it drawn)
IDLE_ROOM = 24      # a scene floats and the camera drifts it up to this far: its box keeps this clear of the area's edges
BG_FADE = 0.4       # background cross-fade
TAIL = 0.5          # the composition runs this long past the voice
EXIT = 0.2          # a scene's exit runs over the last EXIT seconds before its cut, so two scenes never share the screen
MAX_VOICE = 90.0    # the ceiling: a reel's voice is at most 90 s (SPEC; the RAG reel shipped at 92.3 s)
HOOK_BY = 0.8       # every item of the hook lands by 0.8 s, so the hook is whole on screen by 1.0 s (SOP S8)

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


def load_lexicon(path=None):
    """Pronunciations kept across projects (lexicon.json next to scripts/): {"WACC": "wack"}."""
    path = path or os.path.join(HERE, "..", "lexicon.json")
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def apply_lexicon(text, lex):
    """Whole-word, case-sensitive replacements: "WACC" -> "wack", but "WACCs" and "wacc" stay. The voice reads the
    result, and the aligner listens for it."""
    for k in sorted(lex, key=len, reverse=True):
        text = re.sub(r"(?<!\w)%s(?!\w)" % re.escape(k), lambda m, v=lex[k]: v, text)
    return text


def rgba(hexcol, alpha):
    """A palette colour at an alpha, as CSS: rgba(r,g,b,a)."""
    return "rgba(%d,%d,%d,%s)" % (int(hexcol[1:3], 16), int(hexcol[3:5], 16), int(hexcol[5:7], 16), ("%.3f" % alpha).rstrip("0").rstrip("."))


def theme(tokens, bg):
    """The colours a scene on background `bg` uses, by role (tokens.json: palette, backgrounds, roles, series):
    bg, card, card_line, ink, dim, muted, line, accent, on_accent, accent2, good, bad, warn, accent_soft, track,
    shadow, series [(fill, text on it)], highlight {fill, text, handle, handle_border}, and the paper roles (paper,
    paper_ink, paper_dim, paper_line, paper_chrome): a UI mock-up (a browser, a chat, an editor) stays light paper on
    any ground, like the reference's white windows on blue. One colour means one thing: accent is "what the voice is
    talking about now"; good, bad and warn are signals, always beside a label.

    A background may override roles, series and highlight (tokens.backgrounds.<bg>): on `blue` and `ink` the text is
    light, cards are a see-through light glass ([colour, alpha]), and the accent is one that shows on that ground."""
    p = tokens["palette"]
    b = tokens["backgrounds"][bg]
    col = lambda v: rgba(p[v[0]], v[1]) if isinstance(v, list) else p[v]
    roles = dict(tokens["roles"], **b.get("roles", {}))
    c = {k: p[v] for k, v in roles.items()}
    c.update(bg=p[b["fill"]], card=col(b["card"]), card_line=col(b["card_line"]))
    dark = bool(b.get("dark"))
    c["dark"] = dark
    c["accent_soft"] = rgba(c["accent"], 0.2 if dark else 0.12)
    c["track"] = rgba(c["ink"], 0.16 if dark else 0.08)
    sh = tokens["shadow"]
    c["shadow"] = sh["card"] % rgba(p[sh["color"]] if not dark else p["text"], b.get("shadow_alpha", sh["alpha"]))
    c["series"] = [(p[f], p[o]) for f, o in b.get("series", tokens["series"])]
    c["highlight"] = {k: p[v] for k, v in b.get("highlight", tokens["highlight"]).items()}
    c.update({k: p[v] for k, v in tokens["paper"].items()})
    return c


def load_tokens(path=None):
    """The look: fonts, the Catppuccin Latte palette and its roles, backgrounds, motion timing (tokens.json next to
    scripts/). Scenes read colours through theme(), never from the palette directly."""
    with open(path or os.path.join(HERE, "..", "tokens.json")) as f:
        return json.load(f)


# Text is measured with the fonts' real glyph widths, kept in reels_lib (glyphs.json there) so both skills share them.
glyphs, text_width, text_lines = L.glyphs, L.text_width, L.text_lines
