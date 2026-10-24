"""donut: a thick 3D ring chart; each slice sweeps in on its word, its label and figure outside the ring, the total in
the middle (how a deal is paid for: $780M stock, $1,040M cash, $780M debt; $2,600M in all).

  {"type": "donut", "center": "$2,600M", "source": "s1", "slices": [{"label": "STOCK", "value": 780, "text": "$780M", "at": "word:6"}, ...]}

2 to 5 slices, each `value` its size (any unit); `text` shows instead of the value; `center` (optional) appears once the
last slice is in. The ring is SVG arcs on a plane tilted in CSS 3D, thickened by copies stacked below it (darker); each
arc's sweep is a stroke-dasharray tween on the timeline (seek-safe). Words sit flat outside the ring for gate E5.
"""
import math
import explainer_lib as E
from scenes import need

TYPE = "donut"
NEEDS_SOURCE = True
HERO_CSS = ".dn-center"
ASPECT = 0.8
TILT = 58                              # the plane's tilt (degrees)
RING, BAND = 0.66, 0.2                  # the ring's outer diameter (share of the width), its band (share of the diameter)
DEPTH, STEP = 7, 4                     # copies stacked under the top ring, px apart
CY = 0.46                              # the ring's centre (share of the height)
L_SIZE, T_SIZE, C_SIZE = 28, 40, 72    # a slice's label (the label face), its figure (DM Sans 700), the total
MAX_LABEL, MAX_TEXT = 10, 9

CSS = """
  .dn { position:relative; width:100%%; opacity:0; }
  .dn-plane { position:absolute; transform-style:preserve-3d; }
  .dn-slice { position:absolute; left:0; top:0; width:100%%; height:100%%; transform-style:preserve-3d; }
  .dn-slice svg { position:absolute; left:0; top:0; overflow:visible; }
  .dn-labels { position:absolute; left:0; top:0; width:100%%; height:100%%; }
  .dn-l { position:absolute; white-space:nowrap; opacity:0; }
  .dn-l small { display:block; font-family: var(--label); font-weight:500; font-size:%dpx; letter-spacing:.08em; line-height:1.15; }
  .dn-l b { display:block; font-weight:700; font-size:%dpx; line-height:1.1; font-variant-numeric: tabular-nums; }
  .dn-center { position:absolute; left:0; width:100%%; text-align:center; font-weight:700; line-height:1; opacity:0;
    font-variant-numeric: tabular-nums; }
""" % (L_SIZE, T_SIZE)


def validate(scene):
    errs = need(scene, ["slices"])
    sl = scene.get("slices") or []
    if not 2 <= len(sl) <= 5:
        errs.append("a donut takes 2 to 5 slices (got %d)" % len(sl))
    for i, s in enumerate(sl):
        if not isinstance(s, dict):
            errs.append("slice %d is {label, value, at}" % i)
            continue
        if not s.get("label") or len(str(s["label"])) > MAX_LABEL:
            errs.append("slice %d label: 1 to %d characters" % (i, MAX_LABEL))
        v = s.get("value")
        if not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0:
            errs.append("slice %d value %r must be a number > 0" % (i, v))
        if s.get("text") is not None and not 0 < len(str(s["text"])) <= MAX_TEXT:
            errs.append("slice %d text: 1 to %d characters" % (i, MAX_TEXT))
        if s.get("at") is None:
            errs.append("slice %d has no at" % i)
    if scene.get("center") is not None and not 0 < len(str(scene["center"])) <= MAX_TEXT:
        errs.append("center: 1 to %d characters" % MAX_TEXT)
    return errs




def render(scene, ctx, box):
    c, sid = ctx.c, ctx.id
    Wd = box[2]
    H = height(scene, Wd)
    D = Wd * RING
    w = D * BAND
    r = D / 2.0 - w / 2.0
    C = 2 * math.pi * r
    cx, cy = Wd / 2.0, H * CY
    squash = math.cos(math.radians(TILT))
    sl = scene["slices"]
    total = float(sum(s["value"] for s in sl))
    slices, labels, js = [], [], [ctx.enter("#%s-dn" % sid, ctx.t_in, {"scale": 0.92})]
    start, last = 0.0, ctx.t_in
    for i, s in enumerate(sl):
        t, attrs = ctx.item(s["at"])
        last = max(last, t)
        share = s["value"] / total
        fill = c["series"][i % len(c["series"])][0]
        arc = ('<circle class="dn-arc" cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" stroke-width="%.1f" '
               'style="stroke-dasharray:0 %.1f;stroke-dashoffset:%.1f" transform="rotate(-90 %.1f %.1f)"/>'
               % (D / 2, D / 2, r, fill, w, C, -start * C, D / 2, D / 2))
        copies = "".join('<svg class="dn-depth" width="%.0f" height="%.0f" style="transform:translateZ(%dpx);filter:brightness(.72)">%s</svg>'
                         % (D, D, -k * STEP, arc) for k in range(DEPTH, 0, -1))
        top = '<svg class="dn-top" width="%.0f" height="%.0f">%s</svg>' % (D, D, arc)
        slices.append('<div class="dn-slice" id="%s-s%d" data-share="%.4f"%s>%s%s</div>' % (sid, i, share, attrs, copies, top))
        js.append("tl.fromTo('#%s-s%d .dn-arc', { strokeDasharray: '0 %.1f' }, { strokeDasharray: '%.1f %.1f', duration: 0.7, ease: '%s', "
                  "immediateRender: false }, %.3f);" % (sid, i, C, share * C, C, ctx.tokens["motion"]["enter_ease"], t))
        th = math.radians(-90 + (start + share / 2.0) * 360)
        R = D / 2.0 + 30
        ex, ey = cx + R * math.cos(th), cy + R * squash * math.sin(th) + (DEPTH * STEP * math.sin(math.radians(TILT)) if math.sin(th) > 0 else 0)
        lw = max(E.text_width(str(s["label"]), L_SIZE, "mono500" if "mono500" in E.glyphs() else "display700") * 1.1,
                 E.text_width(str(s.get("text", s["value"])), T_SIZE))
        lh = L_SIZE * 1.15 + T_SIZE * 1.1
        lx = ex if math.cos(th) > 0.25 else (ex - lw if math.cos(th) < -0.25 else ex - lw / 2.0)
        ly = ey - lh if math.sin(th) < -0.25 else (ey if math.sin(th) > 0.25 else ey - lh / 2.0)
        labels.append('<div class="dn-l" id="%s-l%d" style="left:%.1fpx;top:%.1fpx;color:%s"><small style="color:%s">%s</small><b>%s</b></div>'
                      % (sid, i, max(0, min(Wd - lw, lx)), ly, ctx.ink, c["dim"], ctx.esc(s["label"]), ctx.esc(s.get("text", s["value"]))))
        js.append(ctx.enter("#%s-l%d" % (sid, i), t + 0.35, {"y": 10}))
        start += share
    center = ""
    if scene.get("center"):
        hole = (D - 2 * w) * 0.86                      # the total sits inside the hole, never over the ring
        dz = DEPTH * STEP * math.sin(math.radians(TILT))       # the back of the ring's thickness shows inside the hole
        size = int(max(28, min(C_SIZE, hole / max(1e-6, E.text_width(str(scene["center"]), 1, E.hero()["glyphs"])),
                                ((D - 2 * w) * squash - dz) * 0.62)))
        center = ('<div class="dn-center" id="%s-c" style="top:%.1fpx;font-size:%dpx;color:%s">%s</div>'
                  % (sid, cy + dz / 2.0 - size / 2.0, size, ctx.ink, ctx.esc(scene["center"])))
        js.append(ctx.enter("#%s-c" % sid, last + 0.6, {"scale": 0.8}))
    html = ('<div class="dn" id="%s-dn" style="aspect-ratio:1 / %s"><div class="dn-plane" style="left:%.1fpx;top:%.1fpx;width:%.0fpx;height:%.0fpx;'
            'transform:rotateX(%ddeg)">%s</div><div class="dn-labels">%s%s</div></div>'
            % (sid, ASPECT, cx - D / 2, cy - D / 2, D, D, TILT, "".join(slices), "".join(labels), center))
    ctx.idle("#%s-dn" % sid, last + 1.2, ctx.t_out - E.EXIT - 0.2, {"y": -8}, every=2.4)
    return html, js
