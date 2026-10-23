"""briefcase: a case lands on its word, its lid swings open on another and papers rise out of it (the deal book, the
interview prep, "what bankers carry").

  {"type": "briefcase", "at": "word:5", "open": "word:8", "papers": 3, "label": "THE DEAL BOOK"}

`papers` (1 to 5, default 3) is how many sheets rise; `label` a short caption under the case. CSS 3D with perspective:
the case is six faces, the lid a panel hinged on the back edge whose swing is a rotation tweened on the timeline, the
papers rise inside the case (the front face hides them until they clear the rim). Seek-safe.
"""
import math
import explainer_lib as E
from scenes import need

TYPE = "briefcase"
DECOR_KEYS = ("papers", "open")  # how many sheets are drawn, and a word anchor: never a figure on screen
ASPECT = 0.85
VIEW = (-20, -26)                 # tilted down, turned to show the front, top and right
BODY = (0.6, 0.24, 0.32)          # width, depth, height of the case (shares of the scene's width)
OPEN = 112                       # the lid's swing (degrees about its back edge)
C_SIZE, MAX_LABEL = 32, 24

CSS = """
  .bc { position:relative; width:100%%; perspective:2400px; opacity:0; }
  .bc-view, .bc-box, .bc-lid { position:absolute; transform-style:preserve-3d; }
  .bc-f { position:absolute; left:0; top:0; border-radius:10px; }
  .bc-paper { position:absolute; left:0; top:0; border-radius:6px; padding:18px 22px; box-sizing:border-box; }
  .bc-paper i { display:block; height:9px; border-radius:5px; margin-top:12px; }
  .bc-cap { position:absolute; left:0; right:0; text-align:center; font-family: var(--label); font-weight:500; font-size:%dpx;
    letter-spacing:.08em; white-space:nowrap; opacity:0; }
""" % C_SIZE


def validate(scene):
    errs = need(scene, ["at", "open"])
    n = scene.get("papers", 3)
    if not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= 5:
        errs.append("a briefcase holds 1 to 5 papers (got %r)" % (n,))
    if scene.get("label") is not None and not 0 < len(str(scene["label"])) <= MAX_LABEL:
        errs.append("label is a short caption, 1 to %d characters" % MAX_LABEL)
    return errs


def height(scene, width):
    return int(math.ceil(width * ASPECT))


def min_width(scene):
    return 600


def _face(w, h, transform, colour, shade=1.0, extra=""):
    return ('<div class="bc-f" style="width:%.1fpx;height:%.1fpx;margin:%.1fpx 0 0 %.1fpx;background:%s;transform:%s;%s%s"></div>'
            % (w, h, -h / 2.0, -w / 2.0, colour, transform, "filter:brightness(%s);" % shade if shade != 1.0 else "", extra))


def render(scene, ctx, box):
    c, sid = ctx.c, ctx.id
    Wd = box[2]
    H = height(scene, Wd)
    bw, bd, bh = (Wd * k for k in BODY)
    body = c["series"][0][0]
    latch = next((f for f, _ in c["series"] if f != body), c["fill"])
    dark = ctx.tokens["palette"]["text"]
    faces = [
        _face(bw, bh, "translateZ(%.1fpx)" % (bd / 2), body),
        _face(bw, bh, "rotateY(180deg) translateZ(%.1fpx)" % (bd / 2), body, 0.7),
        _face(bd, bh, "rotateY(90deg) translateZ(%.1fpx)" % (bw / 2), body, 0.78),
        _face(bd, bh, "rotateY(-90deg) translateZ(%.1fpx)" % (bw / 2), body, 0.78),
        _face(bw, bd, "rotateX(-90deg) translateZ(%.1fpx)" % (bh / 2), body, 0.6),
        _face(bw * 0.94, bd * 0.9, "rotateX(-90deg) translateZ(%.1fpx)" % (bh / 2 - 6), dark, 1.0, "opacity:.55;"),     # the inside
        # two latches and a band on the front, a little proud of it
        _face(bw * 0.12, bh * 0.14, "translate3d(%.1fpx,%.1fpx,%.1fpx)" % (-bw * 0.28, -bh * 0.32, bd / 2 + 2), latch),
        _face(bw * 0.12, bh * 0.14, "translate3d(%.1fpx,%.1fpx,%.1fpx)" % (bw * 0.28, -bh * 0.32, bd / 2 + 2), latch),
    ]
    # the lid: a pivot on the back top edge; the panel hangs from it and is turned flat over the opening
    lid = ('<div class="bc-lid" id="%s-lid" style="transform:translate3d(0,%.1fpx,%.1fpx)">'
           '<div class="bc-f" style="width:%.1fpx;height:%.1fpx;margin-left:%.1fpx;background:%s;transform-origin:50%% 0;transform:rotateX(90deg);'
           'filter:brightness(1.15)"></div>'
           '<div class="bc-f" style="width:%.1fpx;height:%.1fpx;margin-left:%.1fpx;background:%s;transform-origin:50%% 0;'
           'transform:rotateX(90deg) translateY(%.1fpx) rotateX(-90deg)"></div></div>'
           % (sid, -bh / 2, -bd / 2, bw, bd, -bw / 2, body, bw, bh * 0.16, -bw / 2, body, bd))
    n = scene.get("papers", 3)
    pw, ph = bw * 0.82, bh * 0.92
    papers, js = [], []
    t0, attrs = ctx.item(scene["at"])
    js.append(ctx.enter("#%s-case" % sid, t0, {"scale": 0.85, "y": 40}))
    t1, open_attrs = ctx.item(scene["open"])
    js.append("tl.to('#%s-lid', { rotationX: %d, duration: 0.7, ease: '%s' }, %.3f);" % (sid, OPEN, ctx.tokens["motion"]["enter_ease"], t1))
    for i in range(n):
        z = (i - (n - 1) / 2.0) * bd * 0.7 / max(1, n)
        lines = "".join('<i style="width:%d%%;background:%s"></i>' % (w, c["paper_line"]) for w in (70, 90, 55, 80))
        papers.append('<div class="bc-paper" id="%s-p%d" style="width:%.1fpx;height:%.1fpx;margin:%.1fpx 0 0 %.1fpx;background:%s;'
                      'transform:translate3d(0,%.1fpx,%.1fpx)">%s</div>' % (sid, i, pw, ph, -ph / 2, -pw / 2, c["paper"], bh * 0.1, z, lines))
        js.append("tl.fromTo('#%s-p%d', { y: %.1f }, { y: %.1f, duration: 0.6, ease: '%s', immediateRender: false }, %.3f);"
                  % (sid, i, bh * 0.1, -bh * (0.42 + 0.06 * (i % 2)), ctx.tokens["motion"]["enter_ease"], t1 + 0.3 + 0.12 * i))
    cap = ""
    if scene.get("label"):
        cap = '<div class="bc-cap" id="%s-cap" style="top:%dpx;color:%s">%s</div>' % (sid, H * 0.82, c["dim"], ctx.esc(scene["label"]))
        js.append(ctx.enter("#%s-cap" % sid, t1 + 0.4, {"y": 12}))
    html = ('<div class="bc" id="%s-case"%s style="aspect-ratio:1 / %s"><i%s></i><div class="bc-view" style="left:50%%;top:%dpx;'
            'transform:rotateX(%ddeg) rotateY(%ddeg)"><div class="bc-box">%s%s%s</div></div>%s</div>'
            % (sid, attrs, ASPECT, open_attrs, H * 0.5, VIEW[0], VIEW[1], "".join(faces), "".join(papers), lid, cap))
    ctx.idle("#%s-case" % sid, t1 + 1.4, ctx.t_out - E.EXIT - 0.2, {"y": -10}, every=2.4)
    return html, js
