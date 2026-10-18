"""headline.py: the headline layer, a scene's top-left title in the hero face, as the editorial reels set it ("NO
BATTERY / INSIDE THE EARBUDS"): the scene's picture then takes the rest of the area, centred below it.

  "headline": {"text": "No battery", "accent": ["battery"], "kicker": "THE CATCH", "sub": "INSIDE THE EARBUDS",
               "aside": "seriously?", "at": "word:4", "aside_at": "word:6", "case": "upper"}

- text: the hero face (E.hero(): DM Sans 700 in latte, Archivo 800 wide in paper), as big as 120 px and never under
  64, at most three lines in the 950 px column and 260 px tall together (two lines up to 120 px, three up to 80);
  uppercase unless "case" is "as-is"; accent words take the accent.
- kicker (above, the accent) and sub (below, the ink): JetBrains Mono 28 px, spaced .18em.
- aside: Instrument Serif italic, 56 px, a quiet ink; one in the accent when it ends with "." ("Yes.").
Each line rises through its mask on the headline's word, 0.08 s apart; the kicker wipes in, the sub and the aside fade
up. It lives in the scene's box, outside the camera, so it holds still top-left and leaves with the scene.
"""
import re
import explainer_lib as E

SIZES = list(range(120, 63, -4))   # the headline's size: the largest at which it takes at most three lines
MAX_LINES = 3
MAX_BLOCK = 260                    # the lines together never take more: a long headline sets smaller, the scene keeps room
LINE = 1.04                        # line height, in ems of the headline
KICKER, KICK_H, KICK_GAP = 28, 36, 12
SUB_H, SUB_GAP = 36, 10
ASIDE, ASIDE_H, ASIDE_GAP = 56, 68, 8
GAP = 32                           # between the headline and the scene below it
WIDTH = E.L.SAFE["right"] - E.L.SAFE["left"]   # 950: above y 960 the full width is free
STAGGER = 0.08
LABEL_CHARS = 40

CSS = """
  .hl { position:absolute; display:flex; flex-direction:column; align-items:flex-start; pointer-events:none; z-index:2; }
  .hl-k, .hl-s { font-family: var(--label); font-weight:500; font-size:%dpx; letter-spacing:.18em; white-space:nowrap; }
  .hl-k { height:%dpx; line-height:%dpx; margin-bottom:%dpx; }
  .hl-s { height:%dpx; line-height:%dpx; margin-top:%dpx; opacity:0; }
  .hl-m { overflow:hidden; }
  .hl-l { display:block; white-space:nowrap; }
  .hl-aside { font-size:%dpx; height:%dpx; line-height:%dpx; margin-top:%dpx; white-space:nowrap; opacity:0; }
""" % (KICKER, KICK_H, KICK_H, KICK_GAP, SUB_H, SUB_H, SUB_GAP, ASIDE, ASIDE_H, ASIDE_H, ASIDE_GAP)


def norm(w):
    return re.sub(r"[^a-z0-9]", "", str(w).lower())


def shown(h):
    t = str(h.get("text", "")).strip()
    return t if h.get("case") == "as-is" else t.upper()


def _wrap(words, size, width):
    g = E.hero()
    fits = lambda s: E.text_width(s, size, g["glyphs"], spacing=g["spacing"]) <= width * 0.98
    lines, cur = [], []
    for w in words:
        if cur and not fits(" ".join(cur + [w])):
            lines.append(cur)
            cur = []
        if not fits(w):
            return None
        cur.append(w)
    return lines + [cur] if cur else lines


def layout(h, width=WIDTH):
    """{size, lines: [[word]], line_h, height}: the fewest lines the text takes while it stays big (one line at 88 px
    or more, else two at 80 or more, else three at 64 or more), at the largest size that keeps that count, the lines
    together at most MAX_BLOCK tall."""
    words = shown(h).split()
    for n, least in ((1, 88), (2, 80), (MAX_LINES, SIZES[-1])):
        for size in SIZES:
            if size < least:
                break
            lines = _wrap(words, size, width)
            lh = int(round(size * LINE))
            if lines is not None and len(lines) <= n and len(lines) * lh <= MAX_BLOCK:
                height = len(lines) * lh + (KICK_H + KICK_GAP if h.get("kicker") else 0) + (SUB_H + SUB_GAP if h.get("sub") else 0) \
                    + (ASIDE_H + ASIDE_GAP if h.get("aside") else 0)
                return {"size": size, "lines": lines, "line_h": lh, "height": height}
    raise ValueError("the headline needs more than three lines at %d px: shorten it" % SIZES[-1])


def validate(h):
    if not isinstance(h, dict) or not str(h.get("text", "")).strip():
        return ["headline is {\"text\": ..., \"at\": \"word:N\"} (kicker, sub, aside, accent optional)"]
    errs = []
    words = {norm(w) for w in str(h["text"]).split()}
    for a in h.get("accent") or []:
        if norm(a) not in words:
            errs.append("headline accent %r is not a word of the headline" % a)
    for k in ("kicker", "sub", "aside"):
        if h.get(k) is not None and (not isinstance(h[k], str) or len(h[k]) > LABEL_CHARS):
            errs.append("headline %s is a short line (%d characters at most)" % (k, LABEL_CHARS))
    if h.get("aside") and E.text_width(h["aside"], ASIDE, E.aside()["glyphs"]) > WIDTH:
        errs.append("headline aside is wider than the column: shorten it")
    if h.get("kicker") and E.text_width(h["kicker"], KICKER, "mono500", spacing=0.18) > WIDTH:
        errs.append("headline kicker is wider than the column: shorten it")
    try:
        layout(h)
    except ValueError as e:
        errs.append(str(e))
    return errs


def render(h, ctx, x, y):
    """(html, js) for the headline with its top-left at (x, y) inside the scene's box; its frame box is (65, 345)."""
    sid, c = ctx.id, ctx.c
    lay = layout(h)
    hero, aside = E.hero(), E.aside()
    accents = {norm(a) for a in h.get("accent") or []}
    t0, attrs = ctx.item(h["at"]) if h.get("at") else (ctx.t_in, "")
    parts, js = [], []
    if h.get("kicker"):
        parts.append('<div class="hl-k" id="%s-hk" style="color:%s">%s</div>' % (sid, c["accent"], ctx.esc(h["kicker"])))
        js.append("tl.fromTo('#%s-hk', { clipPath: 'inset(0 100%% 0 0)' }, { clipPath: 'inset(0 0%% 0 0)', duration: 0.4, ease: 'none', "
                  "immediateRender: false }, %.3f);" % (sid, max(ctx.t_in, t0 - 0.1)))
    for i, ln in enumerate(lay["lines"]):
        spans = " ".join('<span class="hl-w" style="color:%s">%s</span>' % (c["accent"], ctx.esc(w)) if norm(w) in accents else ctx.esc(w)
                         for w in ln)
        parts.append('<div class="hl-m" style="height:%dpx"><div class="hl-l" id="%s-hl%d"%s style="font-size:%dpx;line-height:%dpx;color:%s;%s">%s</div></div>'
                     % (lay["line_h"], sid, i, attrs if i == 0 else "", lay["size"], lay["line_h"], ctx.ink, hero["css"], spans))
        js.append("tl.set('#%s-hl%d', { yPercent: 110 }, 0);" % (sid, i))
        js.append("tl.fromTo('#%s-hl%d', { yPercent: 110 }, { yPercent: 0, duration: 0.55, ease: 'expo.out', immediateRender: false }, %.3f);"
                  % (sid, i, t0 + STAGGER * i))
    after = t0 + STAGGER * (len(lay["lines"]) - 1) + 0.25
    if h.get("sub"):
        parts.append('<div class="hl-s" id="%s-hs" style="color:%s">%s</div>' % (sid, ctx.ink, ctx.esc(h["sub"])))
        js.append("tl.fromTo('#%s-hs', { opacity: 0 }, { opacity: 1, duration: 0.35, ease: 'power3.out', immediateRender: false }, %.3f);" % (sid, after))
    if h.get("aside"):
        ta, a_attrs = ctx.item(h["aside_at"]) if h.get("aside_at") else (after + 0.2, "")
        loud = h["aside"].strip().endswith(".") and h["aside"].strip()[:1].isupper()
        parts.append('<div class="hl-aside" id="%s-ha"%s style="color:%s;%s">%s</div>'
                     % (sid, a_attrs, c["accent"] if loud else c["dim"], aside["css"], ctx.esc(h["aside"])))
        js.append("tl.fromTo('#%s-ha', { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power3.out', immediateRender: false }, %.3f);"
                  % (sid, ta))
    html = '<div class="hl" id="%s-hl" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx">%s</div>' % (sid, x, y, WIDTH, lay["height"], "".join(parts))
    return html, js
