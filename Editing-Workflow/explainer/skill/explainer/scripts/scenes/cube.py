"""cube: a 3x3x3 cube of cubies with labelled cells on its front (A1 to C3), turning and twisting on the words.

  {"type": "cube", "at": "word:5", "turns": [{"dir": "right", "at": "word:8"}], "twist": [{"dir": "left", "at": "word:11"}],
   "highlight": {"cell": "B2", "at": "word:13"}}

`labels` (9 short strings, read row by row) replaces A1 to C3. Each turn swings the whole cube a quarter (left, right,
up, down); each twist turns its top layer a quarter (left or right), as a Rubik's cube does; `highlight` rings one
labelled cell. CSS 3D: every cubie is six faces, the turns and twists are rotations tweened on the timeline (seek-safe).
For "solve it piece by piece", "every cell connects", "it all has to line up".
"""
import explainer_lib as E
from scenes import need

TYPE = "cube"
DECOR_KEYS = ("labels", "cell")      # cell names (A1, B2): a grid's furniture, not a claim
ASPECT = 0.85
SIDE = 0.6                     # the cube's side, a share of the scene's width
VIEW = (-24, -36)               # the resting view: tilted down, turned to show the front, top and right
GAP = 0.07                      # the dark gap around each sticker, a share of a cubie
L_SIZE = 40                     # a label, DM Sans 700
DIRS = {"left": ("rotationY", 90), "right": ("rotationY", -90), "up": ("rotationX", 90), "down": ("rotationX", -90)}
ROWS = "ABC"
DEFAULT = ["%s%d" % (ROWS[i], j + 1) for j in range(3) for i in range(3)]     # A1 B1 C1 / A2 B2 C2 / A3 B3 C3

CSS = """
  .cb { position:relative; width:100%%; perspective:2600px; opacity:0; }
  .cb-view, .cb-turn, .cb-layer, .cb-q { position:absolute; transform-style:preserve-3d; }
  .cb-face { position:absolute; left:0; top:0; display:flex; align-items:center; justify-content:center; border-radius:12px;
    font-weight:700; font-size:%dpx; backface-visibility:hidden; }
  .cb-hl { position:absolute; inset:-6px; border-radius:16px; opacity:0; }
  .cb-m { position:absolute; width:0; height:0; }
""" % L_SIZE


def _labels(scene):
    return [str(x) for x in scene.get("labels") or DEFAULT]


def validate(scene):
    errs = need(scene, ["at"])
    labels = scene.get("labels")
    if labels is not None and (not isinstance(labels, list) or len(labels) != 9 or any(not str(x).strip() or len(str(x)) > 3 for x in labels)):
        errs.append("labels are 9 labels, short cells (at most 3 characters each), read row by row")
    for k, (key, ok) in enumerate((("turns", "left, right, up or down"), ("twist", "left or right"))):
        for i, m in enumerate(scene.get(key) or []):
            dirs = DIRS if key == "turns" else ("left", "right")
            if not isinstance(m, dict) or m.get("dir") not in dirs:
                errs.append("%s %d: dir is %s (got %r)" % (key, i, ok, m.get("dir") if isinstance(m, dict) else m))
            elif m.get("at") is None:
                errs.append("%s %d has no at" % (key, i))
    hl = scene.get("highlight")
    if hl is not None:
        if not isinstance(hl, dict) or hl.get("at") is None:
            errs.append("highlight is {cell, at}")
        elif str(hl.get("cell")) not in _labels(scene):
            errs.append("highlight cell %r is not one of the labels (%s)" % (hl.get("cell"), " ".join(_labels(scene))))
    return errs




def render(scene, ctx, box):
    c, sid = ctx.c, ctx.id
    Wd = box[2]
    H = height(scene, Wd)
    S = int(round(Wd * SIDE))
    q = S / 3.0
    g = max(4, int(q * GAP))
    labels = _labels(scene)
    dark = ctx.tokens["palette"]["text"]      # the gaps and the hidden insides: always the palette's darkest, on any ground
    series = [f for f, _ in c["series"]]
    on = dict(c["series"])
    faces = {"front": series[0], "right": series[1 % len(series)], "top": series[2 % len(series)],
             "left": series[3 % len(series)], "back": series[4 % len(series)], "bottom": series[0]}
    place = {"front": "translateZ(%.1fpx)", "back": "rotateY(180deg) translateZ(%.1fpx)", "right": "rotateY(90deg) translateZ(%.1fpx)",
             "left": "rotateY(-90deg) translateZ(%.1fpx)", "top": "rotateX(90deg) translateZ(%.1fpx)", "bottom": "rotateX(-90deg) translateZ(%.1fpx)"}
    hl = scene.get("highlight") or {}
    layers = {"top": [], "rest": []}
    for j in range(3):                      # rows, top to bottom
        for k in range(3):                  # depth, back to front
            for i in range(3):              # columns, left to right
                out = {"front": k == 2, "back": k == 0, "right": i == 2, "left": i == 0, "top": j == 0, "bottom": j == 2}
                fs = []
                for name, outer in out.items():
                    col = faces[name] if outer else dark
                    text = ""
                    if name == "front" and outer:
                        cell = labels[j * 3 + i]
                        ring = ('<div class="cb-hl" id="%s-hl" style="box-shadow:0 0 0 6px %s"></div>' % (sid, c["fill"])
                                if hl and str(hl.get("cell")) == cell else "")
                        text = '<span class="cb-l" data-depth="behind" style="color:%s">%s</span>%s' % (on.get(col, dark), ctx.esc(cell), ring)
                    fs.append('<div class="cb-face" style="width:%.1fpx;height:%.1fpx;background:%s;box-shadow:inset 0 0 0 %dpx %s;'
                              'transform:%s">%s</div>' % (q, q, col, g, dark, place[name] % (q / 2.0), text))
                layers["top" if j == 0 else "rest"].append(
                    '<div class="cb-q" style="transform:translate3d(%.1fpx,%.1fpx,%.1fpx)">%s</div>'
                    % ((i - 1) * q - q / 2.0, (j - 1) * q - q / 2.0, (k - 1) * q, "".join(fs)))
    t0, attrs = ctx.item(scene["at"])
    js = [ctx.enter("#%s-cube" % sid, t0, {"scale": 0.7})]
    marks = []
    angle = {"rotationX": 0, "rotationY": 0}
    for m in scene.get("turns") or []:
        t, a = ctx.item(m["at"])
        prop, d = DIRS[m["dir"]]
        angle[prop] += d
        marks.append('<i class="cb-m"%s></i>' % a)
        js.append("tl.to('#%s-turn', { %s: %d, duration: 0.7, ease: 'power3.inOut' }, %.3f);" % (sid, prop, angle[prop], t))
    twist = 0
    for m in scene.get("twist") or []:
        t, a = ctx.item(m["at"])
        twist += 90 if m["dir"] == "left" else -90
        marks.append('<i class="cb-m"%s></i>' % a)
        js.append("tl.to('#%s-top', { rotationY: %d, duration: 0.6, ease: 'power3.inOut' }, %.3f);" % (sid, twist, t))
    if hl:
        t, a = ctx.item(hl["at"])
        marks.append('<i class="cb-m"%s></i>' % a)
        js.append(ctx.enter("#%s-hl" % sid, t, {"scale": 1.3}))
    html = ('<div class="cb" id="%s-cube"%s style="aspect-ratio:1 / %s"><div class="cb-view" style="left:50%%;top:50%%;transform:rotateX(%ddeg) rotateY(%ddeg)">'
            '<div class="cb-turn" id="%s-turn"><div class="cb-layer" id="%s-top">%s</div><div class="cb-layer" id="%s-rest">%s</div></div></div>%s</div>'
            % (sid, attrs, ASPECT, VIEW[0], VIEW[1], sid, sid, "".join(layers["top"]), sid, "".join(layers["rest"]), "".join(marks)))
    ctx.idle("#%s-cube" % sid, t0 + 0.8, ctx.t_out - E.EXIT - 0.2, {"y": -10}, every=2.4)
    return html, js
