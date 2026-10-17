"""storyboard-deck: two to four storyboard frames, light paper cards (a shot number, a sketch drawn with simple shapes, a
one-line note). They wait as a face-down deck in the middle; on each frame's word the top card is dealt out to its
place in a fanned row (a gentle arc, a few degrees of turn), turning face up as it lands:

  {"type": "storyboard-deck", "frames": [{"note": "Hook", "sketch": "face", "at": "word:2"},
                                         {"note": "Screen demo", "sketch": "screen", "at": "word:5"},
                                         {"note": "The result", "sketch": "chart", "at": "word:8"}]}

sketch is one of face (a talking head), screen (a phone recording), chart (bars going up), wide (a landscape shot) or
title (a title card); without one the frames take face, screen, chart, wide in turn. `shot` replaces a frame's "SHOT n"
label (UI furniture: no source needed). The cards are sized for the width the scene is given (BAKED). Each note stays on
one line, so the more frames, the shorter the notes: with four, about nine characters each ("Cold open").
"""
import math
import explainer_lib as E
from scenes import js_obj, need

TYPE = "storyboard-deck"
BAKED = True                       # the cards' sizes and the fan are worked out for the width it is given
DECOR_KEYS = {"shot"}
GAP, PAD, RADIUS = 22, 16, 22      # between cards; inside a card
HEAD_SIZE, HEAD_LH, HEAD_GAP = 30, 36, 12      # "SHOT 1": JetBrains Mono 500
SKETCH = 0.75                      # the sketch's height to its width
NOTE_SIZE, NOTE_LH, NOTE_GAP = 30, 40, 14      # the note: DM Sans 700, one line
ANGLES = {2: [-4, 4], 3: [-5, 0, 5], 4: [-6, -2, 2, 6]}
ARC = 20                           # the outer cards sit this much lower than the middle
DECK = [(0, 0, 0), (4, 4, -2.5), (8, 8, 2), (12, 12, -1.5)]   # a card's place in the deck: dx, dy, turn
KINDS = ("face", "screen", "chart", "wide", "title")
MAX_NOTE = 24
WIDE = E.L.SAFE["right"] - E.L.SAFE["left"]     # the widest column (950)

CSS = """
  .sd { position:relative; width:100%%; }
  .sd-card { position:absolute; border-radius:%dpx; padding:%dpx; opacity:0; }
  .sd-head { height:%dpx; font-family: var(--label); font-weight:500; font-size:%dpx; line-height:%dpx; letter-spacing:.06em;
    white-space:nowrap; }
  .sd-sk { margin-top:%dpx; border-radius:12px; overflow:hidden; }
  .sd-sk svg { width:100%%; height:100%%; display:block; }
  .sd-note { margin-top:%dpx; height:%dpx; font-weight:700; font-size:%dpx; line-height:%dpx; white-space:nowrap; }
  .sd-back { position:absolute; inset:%dpx; border-radius:14px; display:flex; align-items:center; justify-content:center; }
  .sd-back svg { width:34%%; height:auto; }
""" % (RADIUS, PAD, HEAD_LH, HEAD_SIZE, HEAD_LH, HEAD_GAP, NOTE_GAP, NOTE_LH, NOTE_SIZE, NOTE_LH, PAD)

CLAPPER = ('<svg viewBox="0 0 24 24" fill="none" stroke="%s" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
           '<path d="M4 11h16v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/><path d="M4 11l-.6-3.2a1.5 1.5 0 0 1 1.2-1.7l13-2.4a1.5 1.5 0 0 1 1.7 1.2L19.9 8z"/>'
           '<path d="M8.6 5.2l2 3.6"/><path d="M13.6 4.3l2 3.6"/></svg>')


def sketch(kind, c):
    """A storyboard sketch in a 160 x 120 view: outlines in ink, paper fills, one touch of the accent."""
    ink, paper, acc, dim = c["ink"], c["card"], c["accent"], c["dim"]
    s = 'stroke="%s" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"' % ink
    body = {
        "face": ('<path d="M30 122c4-30 24-42 50-42s46 12 50 42" fill="%s" %s/><circle cx="80" cy="50" r="22" fill="%s" %s/>'
                 '<circle cx="20" cy="18" r="6" fill="%s"/><path d="M134 14h14v12 M148 94v12h-14" fill="none" %s/>'
                 % (paper, s, paper, s, acc, s)),
        "screen": ('<rect x="54" y="10" width="52" height="100" rx="9" fill="%s" %s/><path d="M65 30h30 M65 42h20 M65 54h25" fill="none" %s/>'
                   '<rect x="65" y="68" width="30" height="24" rx="4" fill="%s"/><path d="M118 74l16 6-7 3-3 7z" fill="%s" %s/>'
                   % (paper, s, s, acc, paper, s)),
        "chart": ('<path d="M22 102h118 M22 102V16" fill="none" %s/><rect x="38" y="76" width="20" height="26" rx="3" fill="%s" %s/>'
                  '<rect x="68" y="58" width="20" height="44" rx="3" fill="%s" %s/><rect x="98" y="34" width="20" height="68" rx="3" fill="%s"/>'
                  '<path d="M34 60l30-20 20 8 40-30 M112 18h12v12" fill="none" stroke="%s" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>'
                  % (s, paper, s, paper, s, acc, dim)),
        "wide": ('<path d="M6 86h148" fill="none" %s/><path d="M14 86l34-46 22 28 16-20 34 38z" fill="%s" %s/>'
                 '<circle cx="126" cy="34" r="12" fill="%s"/>' % (s, paper, s, acc)),
        "title": ('<rect x="28" y="34" width="104" height="16" rx="8" fill="%s"/><rect x="42" y="60" width="76" height="11" rx="5.5" fill="%s"/>'
                  '<rect x="58" y="82" width="44" height="11" rx="5.5" fill="%s"/>' % (ink, dim, acc)),
    }[kind]
    return '<svg viewBox="0 0 160 120" preserveAspectRatio="xMidYMid meet">%s</svg>' % body


def _kinds(scene):
    order = ("face", "screen", "chart", "wide")
    return [f.get("sketch") or order[i % len(order)] for i, f in enumerate(scene["frames"])]


def _shot(f, i):
    return str(f.get("shot") or "SHOT %d" % (i + 1))


def card_h(w):
    return 2 * PAD + HEAD_LH + HEAD_GAP + sketch_h(w) + NOTE_GAP + NOTE_LH


def sketch_h(w):
    return int(round((w - 2 * PAD) * SKETCH))


def geom(scene, width):
    """The fan at this width: card width and height, each card's left, top and turn, and the box height."""
    n = len(scene["frames"])
    ang = ANGLES[n]
    m = 8
    for _ in range(4):                 # the margin a turned card needs depends on its size: settle it
        w = int((width - 2 * m - (n - 1) * GAP) // n)
        h = card_h(w)
        a = math.radians(max(abs(x) for x in ang))
        m = int(math.ceil(w / 2.0 * math.cos(a) + h / 2.0 * math.sin(a) - w / 2.0)) + 4
    w = int((width - 2 * m - (n - 1) * GAP) // n)
    h = card_h(w)
    left0 = (width - (n * w + (n - 1) * GAP)) / 2.0
    cards, tops, bots = [], [], []
    for i in range(n):
        u = (2.0 * i / (n - 1) - 1) if n > 1 else 0.0
        y = ARC * u * u
        a = math.radians(abs(ang[i]))
        ey = w / 2.0 * math.sin(a) + h / 2.0 * math.cos(a)
        tops.append(y + h / 2.0 - ey)
        bots.append(y + h / 2.0 + ey)
        cards.append([left0 + i * (w + GAP), y, ang[i]])
    lift = 2 - min(tops)
    for cd in cards:
        cd[1] += lift
    return {"w": w, "h": h, "cards": cards, "height": int(math.ceil(max(bots) + lift)) + 2}


def validate(scene):
    errs = need(scene, ["frames"])
    fr = scene.get("frames") or []
    if not 2 <= len(fr) <= 4:
        errs.append("a storyboard deck deals 2 to 4 frames (got %d)" % len(fr))
    for i, f in enumerate(fr):
        if not isinstance(f, dict):
            errs.append("frame %d is not an object" % i)
            continue
        if not str(f.get("note") or "").strip():
            errs.append("frame %d has no note" % i)
        elif len(f["note"]) > MAX_NOTE:
            errs.append("frame %d's note is %d characters; one short line, at most %d" % (i, len(f["note"]), MAX_NOTE))
        if f.get("at") is None:
            errs.append("frame %d has no at" % i)
        if f.get("sketch") is not None and f["sketch"] not in KINDS:
            errs.append("frame %d: sketch %r is not one of %s" % (i, f["sketch"], ", ".join(KINDS)))
        if f.get("shot") is not None and len(str(f["shot"])) > 8:
            errs.append("frame %d: shot is a short label (at most 8 characters)" % i)
    if not errs and min_width(scene) > WIDE:
        worst = max(scene["frames"], key=lambda f: E.text_width(f["note"], NOTE_SIZE))
        errs.append("%d notes on one line each do not fit side by side: shorten the longest (%r), or deal fewer frames"
                    % (len(fr), worst["note"]))
    return errs


def height(scene, width):
    return geom(scene, width)["height"]


def _need(scene):
    """The inner width a card needs: its note on one line, its shot label."""
    return max(max(E.text_width(f["note"], NOTE_SIZE), E.text_width(_shot(f, i), HEAD_SIZE, "mono500", 0.06))
               for i, f in enumerate(scene["frames"])) + 6


def min_width(scene):
    inner = _need(scene)
    for w in range(240, 2400, 4):
        if geom(scene, w)["w"] - 2 * PAD >= inner:
            return w
    return 2400


def render(scene, ctx, box):
    c, mo = ctx.pc, ctx.tokens["motion"]
    sid = ctx.id
    g = geom(scene, box[2])
    w, h, n = g["w"], g["h"], len(scene["frames"])
    deck_left = (box[2] - w) / 2.0
    deck_top = min(cd[1] for cd in g["cards"])
    kinds = _kinds(scene)
    parts, js = [], []
    for i, f in enumerate(scene["frames"]):
        t, attrs = ctx.item(f["at"])
        left, top, turn = g["cards"][i]
        dx, dy, jit = DECK[i]
        x0, y0 = round(deck_left + dx - left, 1), round(deck_top + dy - top, 1)
        parts.append('<div class="sd-card" id="%s-f%d"%s style="left:%.1fpx;top:%.1fpx;width:%dpx;height:%dpx;z-index:%d;%s">'
                     '<div class="sd-head gt" style="color:%s">%s</div>'
                     '<div class="sd-sk gt" style="height:%dpx;background:%s">%s</div>'
                     '<div class="sd-note gt" style="color:%s">%s</div>'
                     '<div class="sd-back" style="background:%s">%s</div></div>'
                     % (sid, i, attrs, left, top, w, h, n - i, ctx.paper_card(), c["dim"], ctx.esc(_shot(f, i)),
                        sketch_h(w), c["chrome"], sketch(kinds[i], c), c["ink"], ctx.esc(f["note"]),
                        c["accent_soft"], CLAPPER % c["accent"]))
        sel = "#%s-f%d" % (sid, i)
        # the deck: every card face down in the middle from the scene's in, the deepest first
        js.append("tl.set('%s .gt', { opacity: 0 }, 0);" % sel)
        js.append("tl.fromTo('%s', %s, %s, %.3f);" % (sel, js_obj({"opacity": 0, "x": x0, "y": y0 - 50, "rotation": jit}),
                                                       js_obj({"opacity": 1, "y": y0, "duration": mo["enter"], "ease": mo["enter_ease"],
                                                               "immediateRender": False}), ctx.t_in + 0.06 * (n - 1 - i)))
        # dealt on its word: out to its place in the fan, face up as it lands
        js.append("tl.fromTo('%s', %s, %s, %.3f);" % (sel, js_obj({"x": x0, "y": y0, "rotation": jit}),
                                                       js_obj({"x": 0, "y": 0, "rotation": turn, "duration": 0.7, "ease": "expo.out",
                                                               "immediateRender": False}), t))
        js.append("tl.to('%s .sd-back', %s, %.3f);" % (sel, js_obj({"opacity": 0, "duration": 0.2, "ease": mo["exit_ease"]}), t + 0.12))
        js.append(ctx.fill(sel, t + 0.1))
    ctx.idle("#%s .sd" % sid, ctx.t_in + 0.6, ctx.t_out, {"y": -8})       # the fan floats while it holds
    return '<div class="sd" style="height:%dpx">%s</div>' % (g["height"], "".join(parts)), js
