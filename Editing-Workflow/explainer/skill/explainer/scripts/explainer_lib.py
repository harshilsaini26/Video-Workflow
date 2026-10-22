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


def kit_dir():
    """The kit's youtube-edit/scripts folder: $KIT_SCRIPTS, installed side by side, or this repository; None if absent."""
    for c in [os.environ.get("KIT_SCRIPTS", ""),
              os.path.join(HERE, "..", "..", "youtube-edit", "scripts"),                      # .claude/skills/youtube-edit/scripts
              os.path.join(HERE, "..", "..", "..", "..", "kit", "youtube-edit", "scripts")]:   # Editing-Workflow/kit
        if c and os.path.exists(os.path.join(c, "nle_xml.py")):
            return os.path.abspath(c)
    return None


def find_kit(module):
    """Import one of the kit's shared modules (nle_xml, filmcraft, wording) from kit_dir()."""
    d = kit_dir()
    if not d:
        sys.exit("the kit's youtube-edit scripts were not found: install the kit (.claude/skills/youtube-edit) or set KIT_SCRIPTS")
    if d not in sys.path:
        sys.path.insert(0, d)
    return importlib.import_module(module)

# The frame, top to bottom (the editorial pass, 2026-10-18: the centre is always the animation's):
#   the handle band (y 281 to 321), the scene area (y 345 to 1105), the captions, small, at the bottom of the safe area
#   (CAPTION_BAND, y 1130 to 1235). No text of any kind goes below TEXT_BOTTOM (SOP S7, from the RAG reel: QA and the
#   Reels guides judge the bottom 35% as covered by the app's caption and buttons, so one line holds everywhere: here,
#   in the E5 probe and in QA). Painted shapes with no text in them (particles, floors, illustration, the thread) may run
#   on to PICTURE_BOTTOM, behind the captions, which keep a halo of their ground. Below RIGHT_COL_TOP everything keeps the
#   narrow column.
SCENE = {"left": 65, "top": 345, "right": 1015, "bottom": 1105}
TEXT_BOTTOM = 1235
PICTURE_BOTTOM = 1650


def centre_top(h, wide, area_top=None):
    """The top of a box h tall, centred on the scene area's middle (from area_top, under a headline, when given): the
    centre is the animation's. A full-width box rises only as far as it must to end IDLE_ROOM above RIGHT_COL_TOP (the
    app's action column)."""
    top = int(round(((SCENE["top"] if area_top is None else area_top) + SCENE["bottom"]) / 2.0 - h / 2.0))
    if wide:
        top = min(top, L.RIGHT_COL_TOP - IDLE_ROOM - h)
    return top


def inside_scene(left, top, width, height):
    """True when a box sits inside the scene area, and inside the narrow column wherever it reaches below y 960."""
    if left < SCENE["left"] or top < SCENE["top"] or left + width > SCENE["right"] or top + height > SCENE["bottom"]:
        return False
    return top + height <= L.RIGHT_COL_TOP or (left >= L.NARROW["left"] and left + width <= L.NARROW["right"])
CAPTION_BAND = (1130, 1235)
CAPTION_SIZE = 44  # two lines of 44 px fill the band; the scenes keep the centre
LEAD = 0.2          # an entrance starts this long before its word (beat-check's 0.15 to 0.25 s window)
MAX_OVERLAP = 0.02  # scenes hand over on one cut: no overlap beyond rounding (SOP S9)
MIN_TEXT = 28       # the smallest text a phone viewer reads on the 1080 px frame (gate E5 checks it drawn)
IDLE_ROOM = 24      # a scene floats and the camera drifts it up to this far: its box keeps this clear of the area's edges
BG_FADE = 0.4       # background cross-fade
TAIL = 0.5          # the composition runs this long past the voice
EXIT = 0.2          # a scene's exit runs over the last EXIT seconds before its cut, so two scenes never share the screen
CLOSE = 0.4         # the last scene leaves over the last CLOSE seconds, onto the hook's ground (transitions.close)
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
    with open(path, encoding="utf-8") as f:
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


LOOKS = ("latte", "paper")   # latte, the default (Catppuccin Latte); paper, the editorial look (tokens.looks.paper)


def _merge(base, over):
    """`over` laid on `base`: dicts merge key by key, anything else (a list, a value) replaces."""
    out = dict(base)
    for k, v in over.items():
        out[k] = _merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


PALETTES = ("terracotta", "monochrome", "electric-pop", "nordic-frost", "bold-citrus")   # colour only (tokens.palettes)


def _rgb(h):
    return [int(h[i:i + 2], 16) for i in (1, 3, 5)]


def _mix(a, b, t):
    """a moved toward b by t (0 to 1), as #RRGGBB."""
    return "#" + "".join("%02X" % int(round(x + (y - x) * t)) for x, y in zip(_rgb(a), _rgb(b)))


def _lum(h):
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (v / 255.0 for v in _rgb(h))
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def _ratio(a, b):
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _readable(c, grounds, need):
    """c, or c taken darker (on light grounds) or lighter (on dark) in its own hue until it reads at `need` on each."""
    to = "#000000" if min(_lum(g) for g in grounds) > 0.18 else "#FFFFFF"
    for k in range(34):
        out = _mix(c, to, k * 0.03)
        if all(_ratio(out, g) >= need for g in grounds):
            return out
    return to


def palette_tokens(spec, look_ambient):
    """A palette's colour tokens (palette names, roles, grounds, series, highlight, paper, ambient) from its few
    choices in tokens.palettes: shapes keep its exact colours; text that would not read is taken deeper in its own hue."""
    g, ink = spec["ground"], spec["ink"]
    m = spec.get("mantle") or _mix(g, ink, 0.05)
    crust = _mix(m, ink, 0.06)
    lights = [g, m, crust]                    # text reads on both light grounds and over their darkest glow
    p = {"base": g, "mantle": m, "crust": crust, "text": ink,
         "subtext1": _readable(_mix(ink, g, 0.15), lights, 4.5), "subtext0": _readable(_mix(ink, g, 0.30), lights, 3.0),
         "overlay2": _readable(_mix(ink, g, 0.45), lights, 3.0), "overlay1": _mix(ink, g, 0.55), "overlay0": _mix(ink, g, 0.65),
         "surface2": _mix(ink, g, 0.75), "surface1": _mix(ink, g, 0.83), "surface0": _mix(ink, g, 0.90),
         "flamingo": spec["accent"], "peach": _readable(spec["accent"], lights, 3.0),
         "pink": spec["accent2"], "lavender": _readable(spec["accent2"], lights, 3.0),
         "blue": spec["strong"], "mauve": spec["dark"],
         "teal": spec["good"], "green": _readable(spec["good"], lights, 3.0),
         "maroon": spec["bad"], "red": _readable(spec["bad"], lights, 3.0),
         "sapphire": spec["warn"], "yellow": _readable(spec["warn"], lights, 3.0)}
    p["rosewater"] = _mix(spec["accent"], g, 0.55)
    p["sky"] = _mix(spec["accent2"], g, 0.55)
    for k, c in enumerate(spec.get("cycle", []), 1):
        p["c%d" % k] = c
    named = {}
    for n in ("flamingo", "pink", "blue", "mauve", "teal", "maroon", "sapphire", "text", "base", "mantle") + tuple("c%d" % k for k in range(1, 6)):
        if n in p:
            named.setdefault(p[n].upper(), n)
    best = lambda fill: max(("text", "base"), key=lambda n: _ratio(p[n], p[fill]))      # the text that reads on a fill
    series = [[named[c.upper()], best(named[c.upper()])] for c in spec["series"] if _ratio(p[best(named[c.upper()])], c) >= 3.0]
    five = lambda ss: [ss[i % len(ss)] for i in range(5)]        # scenes read up to five series entries: repeat, never add
    series = five(series)
    hl = "flamingo" if _ratio(p[best("flamingo")], p["flamingo"]) >= 3.0 else "peach"

    def coloured(fill):                       # a strong ground (or a citrus step): one text colour does everything on it
        t = best(fill)
        return {"fill": fill, "dark": t == "base", "card": fill, "card_line": [t, 0.34],
                "roles": {"ink": t, "dim": t, "muted": t, "line": t, "accent": t, "on_accent": fill, "accent2": t, "chrome": "crust"},
                "series": five([[t, fill]] + [s for s in series if s[0] != fill]), "highlight": {"fill": t, "text": fill, "handle": fill, "handle_border": t},
                "shadow_alpha": 0.28}
    dark = "mauve"
    under = [p[dark], _mix(p[dark], p["base"], 0.06)]        # the dark ground, and its brightest glow
    acc_d = next(n for n in ("flamingo", "rosewater", "base") if all(_ratio(p[n], u) >= 3.0 for u in under))
    grounds = {"mantle": {"fill": "mantle", "card": "base", "card_line": "surface0"},
               "base": {"fill": "base", "card": "base", "card_line": "surface0"},
               "blue": coloured("blue"),
               "ink": {"fill": dark, "dark": True, "card": dark, "card_line": ["base", 0.26],
                       "roles": {"ink": "base", "dim": "crust", "muted": "surface0", "line": "surface2", "accent": acc_d,
                                 "on_accent": best(acc_d), "accent2": "crust", "chrome": "crust"},
                       "series": five([[acc_d, best(acc_d)], ["base", dark]] + [s for s in series if _ratio(p[s[0]], p[dark]) >= 1.5 and s[0] not in (acc_d, dark)]),
                       "highlight": {"fill": acc_d, "text": best(acc_d), "handle": best(acc_d), "handle_border": acc_d}, "shadow_alpha": 0.3}}
    cycle = ["c%d" % k for k in range(1, len(spec.get("cycle", [])) + 1)]
    for c in cycle:
        grounds[c] = coloured(c)
    glows, parts = {}, {}
    for gname, b in grounds.items():
        src = look_ambient["glows"].get(gname) or look_ambient["glows"]["blue"]
        if gname in ("mantle", "base"):
            cols = [("crust", 0.5), ("surface0", 0.35), ("crust", 0.4)]
            parts[gname] = [["overlay0", 0.3], ["surface2", 0.45], ["flamingo", 0.22]]
        else:
            t = b["roles"]["ink"]
            cols = [(t, 0.06), ("base" if t == "text" else "text", 0.05), (t, 0.04)]
            parts[gname] = [[t, 0.22], [t, 0.14]]
        glows[gname] = [dict(gl, color=c, alpha=a) for gl, (c, a) in zip(src, cols)]
    return {"palette": p, "backgrounds": grounds, "series": series, "cycle": cycle,
            "roles": {"ink": "text", "dim": "subtext0", "muted": "overlay2", "line": "surface1", "accent": "peach",
                      "on_accent": best("peach"), "accent2": "lavender", "good": "green", "bad": "red", "warn": "yellow", "chrome": "crust"},
            "highlight": {"fill": hl, "text": best(hl), "handle": best(hl), "handle_border": hl},
            "paper": {"paper": "base", "paper_ink": "text", "paper_dim": "subtext0", "paper_line": "surface0", "paper_chrome": "crust"},
            "shadow": {"color": "text"}, "ambient": {"glows": glows, "particles": {"colors": parts}}}


def load_tokens(path=None, look=None, palette=None):
    """The look: fonts, the palette and its roles, backgrounds, motion timing (tokens.json next to scripts/). `look`
    lays tokens.looks.<look> over the base (Catppuccin Latte); paper renames no palette colour, so a scene that names one
    resolves in either look. Scenes read colours through theme(), never from the palette directly. tok["look"] names it."""
    with open(path or os.path.join(HERE, "..", "tokens.json"), encoding="utf-8") as f:
        tok = json.load(f)
    look = look or "latte"
    if look not in LOOKS:
        raise ValueError("no look %r: the looks are %s" % (look, ", ".join(LOOKS)))
    looks = tok.pop("looks", {})
    if look != "latte":
        tok = _merge(tok, looks[look])
    tok["look"] = look
    if palette:                               # colour only: laid over the look's colours, never its fonts or effects
        if palette not in PALETTES:
            raise ValueError("no palette %r: the palettes are %s" % (palette, ", ".join(PALETTES)))
        over = palette_tokens(tok["palettes"][palette], tok["ambient"])
        tok["backgrounds"] = {}                 # the palette's grounds replace the look's (names may differ: citrus steps)
        tok["ambient"]["glows"], tok["ambient"]["particles"]["colors"] = {}, {}
        tok = _merge(tok, over)
    tok["palette_name"] = palette
    return tok


_FACE = {}


def use_look(tok):
    """The look the page is composed in: hero() and aside() answer for it (the composer calls this once, before it
    places any scene, since a scene's height depends on the face its big text is set in)."""
    _FACE.clear()
    _FACE.update(hero=tok["fonts"]["hero"], aside=tok["fonts"]["aside"])


def _face(f):
    css = "font-family:'%s';font-stretch:%s;font-weight:%d;letter-spacing:%sem" % (f["family"], f["stretch"], f["weight"], f["spacing"])
    if f.get("style"):
        css += ";font-style:%s" % f["style"]
    return dict(f, css=css)


def hero():
    """The face of the big words (headlines, kinetic, giant captions, title cards, stat figures, price stickers): DM Sans
    700 in latte, Archivo 800 at width 125% in paper. {family, stretch, weight, glyphs (the glyphs() table), spacing,
    css}. Body text inside UI mock-ups stays DM Sans in every look."""
    if not _FACE:
        use_look(load_tokens())
    return _face(_FACE["hero"])


def aside():
    """The face of a short aside ("seriously?"): Instrument Serif italic, in every look."""
    if not _FACE:
        use_look(load_tokens())
    return _face(_FACE["aside"])


# Text is measured with the fonts' real glyph widths, kept in reels_lib (glyphs.json there) so both skills share them.
glyphs, text_width, text_lines = L.glyphs, L.text_width, L.text_lines
