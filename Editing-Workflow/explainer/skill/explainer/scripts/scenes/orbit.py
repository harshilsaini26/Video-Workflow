"""orbit: Kurzgesagt's flat world. An idea is drawn as a thing, its parts orbit it, and the camera crosses scales into
one of them ("inside every drop of sea water... is a diatom").

  {"type": "orbit", "center": "A drop of sea water", "shape": "circle",
   "nodes": [{"text": "Plankton", "at": "word:5"}, {"text": "Salt", "at": "word:6"}],
   "dive": {"into": 0, "at": "word:8", "center": "A diatom", "shape": "hex",
            "nodes": [{"text": "Silica shell", "at": "word:11"}, {"text": "Chloroplast", "at": "word:12"}]}}

Flat with no outline: every shape is filled three times inside its own clip (a shadow, a highlight edge, the base; the
light comes from the top left), never stroked (huashu-art-motion's TOON.flat, MIT). The centre is the thing (circle,
rounded or hex), up to 4 nodes orbit it, each a flat disc that pops on its word with a ripple ring and a label pill;
signals run along the links while it holds. On a dark ground the centre glows and the stars twinkle (the ambient
layer moves, the subject holds still once it has landed).

`dive` is the scale crossing: the labels go, the camera pushes into the node on a log zoom (each frame grows by the
same factor, so the crossing reads as one steady flight) until the node's colour fills the box, and the next level
pulls out of a centre in that same colour; its nodes then land on their words. The pop never overshoots
(MOTION.md): Kurzgesagt's 108 % pop is replaced by expo.out and the ripple.
"""
import math, random
import explainer_lib as E
from scenes import need, js_obj
import transitions as X

TYPE = "orbit"
DECOR_KEYS = ("into", "shape")
BAKED = True                             # drawn at the width it is given
BEATS = True                             # gate E5 looks at the picture before each node and before the dive
SHAPES = ("circle", "rounded", "hex")
ASPECT = 0.86
R, NR = 0.19, 0.065                      # the centre's and a node's radius, shares of the width
SLOTS = {1: [(0, -0.3)], 2: [(-0.29, -0.29), (0.29, -0.29)], 3: [(-0.29, -0.29), (0.29, -0.29), (0, 0.29)],
         4: [(-0.29, -0.29), (0.29, -0.29), (0.29, 0.29), (-0.29, 0.29)]}   # (x share of the width, y share of the height)
P_SIZE, MAX_NODE, MAX_CENTER = 36, 14, 20
PILL_H, PILL_PAD, PILL_GAP = 66, 22, 16
N_SIZE, N_MIN = 44, 30
DIVE_IN, DIVE_OUT = 0.8, 1.0
PULSE = 1.4
STARS = 18

CSS = """
  .ob { position:relative; width:100%%; }
  .ob-w { position:absolute; left:0; top:0; width:100%%; height:100%%; }
  .ob svg { position:absolute; left:0; top:0; overflow:visible; }
  .ob-flat, .ob-ripple { transform-box:fill-box; transform-origin:center; }
  .ob-pill { position:absolute; height:%dpx; line-height:%dpx; padding:0 %dpx; border-radius:%dpx; font-weight:700;
    font-size:%dpx; white-space:nowrap; opacity:0; }
  .ob-name { position:absolute; text-align:center; font-weight:700; line-height:1.1; border-radius:14px; padding:8px 8px; opacity:0; }
  .ob-glow { position:absolute; border-radius:50%%; opacity:0; }
  .ob-star { position:absolute; width:5px; height:5px; border-radius:50%%; opacity:0.5; }
""" % (PILL_H, PILL_H, PILL_PAD, PILL_H // 2, P_SIZE)


def _nodes_ok(nodes, where):
    errs = []
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= 4:
        return ["%s: 1 to 4 nodes" % where]
    for nd in nodes:
        if not isinstance(nd, dict) or nd.get("at") is None or nd.get("text") is None:
            errs.append("%s: each node is {text, at}" % where)
        elif not 0 < len(str(nd["text"])) <= MAX_NODE:
            errs.append("%s: node text: 1 to %d characters (got %r)" % (where, MAX_NODE, nd["text"]))
    return errs


def validate(scene):
    errs = need(scene, ["center", "nodes"])
    if scene.get("center") is not None and not 0 < len(str(scene["center"])) <= MAX_CENTER:
        errs.append("center: 1 to %d characters" % MAX_CENTER)
    if scene.get("shape") is not None and scene["shape"] not in SHAPES:
        errs.append("shape is circle, rounded or hex")
    if scene.get("nodes") is not None:
        errs += _nodes_ok(scene["nodes"], "nodes")
    dv = scene.get("dive")
    if dv is not None:
        if not isinstance(dv, dict) or dv.get("at") is None or not dv.get("center"):
            return errs + ["dive is {into, at, center, nodes}"]
        n = len(scene["nodes"]) if isinstance(scene.get("nodes"), list) else 0
        if not isinstance(dv.get("into"), int) or isinstance(dv.get("into"), bool) or not 0 <= dv["into"] < max(1, n):
            errs.append("dive.into is 0 to %d (a node of this level)" % max(0, n - 1))
        if not 0 < len(str(dv["center"])) <= MAX_CENTER:
            errs.append("dive.center: 1 to %d characters" % MAX_CENTER)
        if dv.get("shape") is not None and dv["shape"] not in SHAPES:
            errs.append("dive.shape is circle, rounded or hex")
        errs += _nodes_ok(dv.get("nodes"), "dive.nodes")
    return errs


def _pill_w(text):
    return int(math.ceil(E.text_width(str(text), P_SIZE, "display700"))) + 2 * PILL_PAD


def min_width(scene):
    texts = [n["text"] for n in scene["nodes"]] + [n["text"] for n in (scene.get("dive") or {}).get("nodes", [])]
    return max([760] + [int(math.ceil(_pill_w(t) / 0.5)) for t in texts])


def travels(scene):
    """A dive is the camera crossing into a new picture: E4 lets the scene hold past one picture's limit."""
    return bool(scene.get("dive"))


def min_text(scene):
    return min(P_SIZE, N_MIN)


def _shape(kind, cx, cy, r, fill, clip):
    if kind == "rounded":
        return '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f" fill="%s"%s/>' % (cx - r * 0.92, cy - r * 0.92, r * 1.84, r * 1.84, r * 0.36, fill, clip)
    if kind == "hex":
        pts = " L".join("%.1f,%.1f" % (cx + 1.06 * r * math.cos(math.pi / 6 + k * math.pi / 3), cy + 1.06 * r * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6))
        return '<path d="M%s Z" fill="%s"%s/>' % (pts, fill, clip)
    return '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"%s/>' % (cx, cy, r, fill, clip)


def _flat(gid, cls, kind, cx, cy, r, base, tones, extra=""):
    """A flat shape with no outline: the shadow, then the highlight moved up-left, then the base moved back a little,
    each inside the shape's own clip (a band of shadow at the bottom right, a thin light edge at the top left). The
    shadow and the highlight are the base under a see-through layer of the look's own ink and paper (`tones`), so no
    colour outside the palette is ever drawn."""
    kid = gid.replace("-c", "-k").replace("-n", "-kn")
    clip = ' clip-path="url(#%s)"' % kid
    v, w = (0.10 * r, 0.12 * r), (0.04 * r, 0.05 * r)
    shade, light = tones
    layer = lambda dx, dy, over: _shape(kind, cx + dx, cy + dy, r, base, clip) + (_shape(kind, cx + dx, cy + dy, r, over, clip) if over else "")
    return ('<clipPath id="%s">%s</clipPath><g class="%s" id="%s"%s>%s%s%s</g>'
            % (kid, _shape(kind, cx, cy, r, "none", ""), cls, gid, extra,
               layer(0, 0, shade), layer(-v[0], -v[1], light), layer(-v[0] + w[0], -v[1] + w[1], None)))


def _name(text, inner, ctx, nid, cx, cy, color):
    words = str(text).split()
    for size in range(N_SIZE, N_MIN - 1, -2):
        lines, cur = [], ""
        for wd in words:
            t = (cur + " " + wd).strip()
            if E.text_width(t, size, "display700") <= inner or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = wd
        lines.append(cur)
        if len(lines) <= 2 and all(E.text_width(l, size, "display700") <= inner for l in lines):
            h = size * 1.1 * len(lines) + 16            # 8 px of chip above and below the words
            # the name sits on a chip of the centre's own base colour (invisible on its face): E5 reads it on that
            return ('<div class="ob-name" id="%s" style="left:%.1fpx;top:%.1fpx;width:%.1fpx;font-size:%dpx;color:%s;background:%s">%s</div>'
                    % (nid, cx - inner / 2 - 8, cy - h / 2, inner + 16, size, color[1], color[0], "<br>".join(ctx.esc(l) for l in lines)))
    ctx.fail("the centre's name %r does not fit inside it at %d px: shorten it" % (text, N_MIN))


def _level(scene_lvl, k, ctx, Wd, Hd, centre_pair, kind, offset):
    """One level's world: the centre, its orbit, its nodes and pills. Returns (html, node list, js)."""
    c, sid = ctx.c, ctx.id
    cx, cy, r, nr = Wd / 2.0, Hd / 2.0, Wd * R, Wd * NR
    dark = c["dark"]
    svg, html, js, nodes = [], [], [], []
    svg.append('<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" fill="none" stroke="%s" stroke-opacity="0.5" stroke-width="2" '
               'stroke-dasharray="2 14" stroke-linecap="round"/>' % (cx, cy, Wd * 0.41, Hd * 0.41, c["muted"]))
    slots = SLOTS[len(scene_lvl["nodes"])]
    for i, nd in enumerate(scene_lvl["nodes"]):
        fx, fy = slots[i]
        x, y = cx + fx * Wd, cy + fy * Hd
        fill, on = c["series"][(i + offset) % len(c["series"])]
        nodes.append((x, y, fill, on))
        L = math.hypot(x - cx, y - cy)
        svg.append('<line class="ob-line" id="%s-e%d-%d" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="4" '
                   'stroke-linecap="round" stroke-dasharray="%.1f" stroke-dashoffset="%.1f"/>' % (sid, k, i, cx, cy, x, y, c["muted"], L, L))
    tones = (E.rgba(ctx.pc["paper_ink"], 0.28), E.rgba(ctx.pc["paper"], 0.4))
    svg.append(_flat("%s-c%d" % (sid, k), "ob-flat", kind, cx, cy, r, centre_pair[0], tones))
    for i, (x, y, fill, on) in enumerate(nodes):
        svg.append('<circle class="ob-ripple" id="%s-r%d-%d" cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" stroke-width="4" opacity="0"/>'
                   % (sid, k, i, x, y, nr * 1.1, fill))
        svg.append(_flat("%s-n%d-%d" % (sid, k, i), "ob-flat ob-node", "circle", x, y, nr, fill, tones, ' style="opacity:0"'))
        svg.append('<circle class="ob-pulse" id="%s-s%d-%d" cx="%.1f" cy="%.1f" r="7" fill="%s" opacity="0"/>' % (sid, k, i, cx, cy, c["accent2"]))
    pill_bg, pill_ink = (c["ink"], c["bg"]) if dark else (c["card"], c["ink"])
    for i, nd in enumerate(scene_lvl["nodes"]):
        x, y = nodes[i][:2]
        pw = _pill_w(nd["text"])
        if pw > 0.5 * Wd:
            ctx.fail("the label %r is too wide for this box: shorten it" % nd["text"])
        left = min(max(4.0, x - pw / 2.0), Wd - pw - 4.0)
        top = y - nr - PILL_GAP - PILL_H if y < cy else y + nr + PILL_GAP
        t, attrs = ctx.item(nd["at"])
        html.append('<div class="ob-pill" id="%s-p%d-%d" style="left:%.1fpx;top:%.1fpx;background:%s;color:%s"%s>%s</div>'
                    % (sid, k, i, left, top, pill_bg, pill_ink, attrs, ctx.esc(nd["text"])))
    html.append(_name(scene_lvl["center"], 1.4 * r, ctx, "%s-name%d" % (sid, k), cx, cy, centre_pair))
    world = '<svg width="%d" height="%d">%s</svg>%s' % (Wd, Hd, "".join(svg), "".join(html))
    return world, nodes, js


def render(scene, ctx, box):
    c, sid = ctx.c, ctx.id
    Wd = box[2]
    Hd = int(math.ceil(Wd * ASPECT))
    cx, cy, r, nr = Wd / 2.0, Hd / 2.0, Wd * R, Wd * NR
    js = [X.ZOOM_JS]                      # the log zoom eases, shared with the dive transition
    back = []
    if c["dark"]:
        back.append('<div class="ob-glow" id="%s-glow" style="left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx;'
                    'background:radial-gradient(circle, %s 0%%, %s 70%%)"></div>'
                    % (sid, cx - r * 2.4, cy - r * 2.4, r * 4.8, r * 4.8, E.rgba(c["series"][0][0], 0.28), E.rgba(c["series"][0][0], 0)))
        js.append(ctx.enter("#%s-glow" % sid, ctx.t_in, dur=0.8))
        rng = random.Random(7)
        for s in range(STARS):
            back.append('<i class="ob-star" id="%s-st%d" style="left:%dpx;top:%dpx;background:%s"></i>'
                        % (sid, s, rng.randint(8, Wd - 12), rng.randint(8, Hd - 12), c["ink"]))
            ctx.idle("#%s-st%d" % (sid, s), ctx.t_in + rng.random(), ctx.t_out - E.EXIT, {"opacity": 0.15}, every=1.1 + rng.random())
    pair0 = c["series"][0]
    w0, nodes0, _ = _level(scene, 0, ctx, Wd, Hd, pair0, scene.get("shape") or "circle", 1)
    worlds = ['<div class="ob-w" id="%s-w0" style="transform-origin:%s">%s</div>' % (sid, "50% 50%", w0)]
    js.append(ctx.enter("#%s-c0" % sid, ctx.t_in, {"scale": 0.7}))
    js.append(ctx.enter("#%s-name0" % sid, ctx.t_in + 0.2, {"y": 12}))
    dv = scene.get("dive")
    t_dive = ctx.at(dv["at"]) if dv else None
    ends = [t_dive if dv else ctx.t_out - E.EXIT]
    lv = [(scene, nodes0, 0)]
    if dv:
        x, y, fill, on = nodes0[dv["into"]]
        w1, nodes1, _ = _level(dv, 1, ctx, Wd, Hd, (fill, on), dv.get("shape") or "circle", 2)
        worlds[0] = '<div class="ob-w" id="%s-w0" style="transform-origin:%.1fpx %.1fpx">%s</div>' % (sid, x, y, w0)
        worlds.append('<div class="ob-w" id="%s-w1" style="opacity:0;transform-origin:%.1fpx %.1fpx">%s</div>' % (sid, cx, cy, w1))
        lv.append((dv, nodes1, 1))
        ends.append(ctx.t_out - E.EXIT)
    for (lvl, nodes, k), end in zip(lv, ends):
        for i, nd in enumerate(lvl["nodes"]):
            t = ctx.at(nd["at"])
            if k == 1 and t < t_dive + DIVE_IN + DIVE_OUT + 0.1 - 1e-6:
                ctx.fail("the node %r lands at %.2f s, inside the dive (it ends at %.2f s): anchor it after the dive"
                         % (nd["text"], t, t_dive + DIVE_IN + DIVE_OUT))
            if k == 0 and dv and t > t_dive - 0.3:
                ctx.fail("the node %r lands at %.2f s, too close to the dive at %.2f s: anchor it earlier" % (nd["text"], t, t_dive))
            x, y = nodes[i][:2]
            L = math.hypot(x - cx, y - cy)
            js.append("tl.fromTo('#%s-e%d-%d', { strokeDashoffset: %.1f }, { strokeDashoffset: 0, duration: 0.35, ease: 'power2.out', "
                      "immediateRender: false }, %.3f);" % (sid, k, i, L, max(ctx.t_in, t - 0.1)))
            js.append("tl.fromTo('#%s-n%d-%d', { opacity: 0, scale: 0 }, { opacity: 1, scale: 1, duration: 0.5, ease: 'expo.out', "
                      "immediateRender: false }, %.3f);" % (sid, k, i, t))
            js.append("tl.fromTo('#%s-r%d-%d', { opacity: 0.55, scale: 1 }, { opacity: 0, scale: 2.4, duration: 0.9, ease: 'power2.out', "
                      "immediateRender: false }, %.3f);" % (sid, k, i, t))
            js.append(ctx.enter("#%s-p%d-%d" % (sid, k, i), t + 0.15, {"y": 12}))
            p = t + 0.6
            while p + PULSE <= end + 1e-6:          # a signal runs out along the link while the level holds
                ctx.ambient("tl.fromTo('#%s-s%d-%d', %s, %s, %.3f);" % (sid, k, i, js_obj({"attr": {"cx": round(cx, 1), "cy": round(cy, 1)}, "opacity": 1}),
                                                                         js_obj({"attr": {"cx": round(x, 1), "cy": round(y, 1)}, "opacity": 0, "duration": 1.2,
                                                                                 "ease": "none", "immediateRender": False}), p))
                p += PULSE
    if dv:
        x, y = nodes0[dv["into"]][:2]
        hyp = math.hypot(Wd / 2.0, Hd / 2.0)
        Z = round(1.15 * hyp / nr, 1)
        Z2 = round(1.15 * hyp / r, 1)
        js.append("tl.to('#%s-w0 .ob-pill, #%s-w0 .ob-name', { opacity: 0, duration: 0.2, ease: 'power3.in' }, %.3f);" % (sid, sid, t_dive))
        js.append("tl.to('#%s-w0', { scale: %s, x: %.1f, y: %.1f, duration: %s, ease: zoomIn(%s) }, %.3f);"
                  % (sid, Z, cx - x, cy - y, DIVE_IN, Z, t_dive))
        js.append("tl.set('#%s-w0', { opacity: 0 }, %.3f);" % (sid, t_dive + DIVE_IN))
        js.append("tl.fromTo('#%s-w1', { opacity: 1, scale: %s }, { scale: 1, duration: %s, ease: zoomOut(%s), immediateRender: false }, %.3f);"
                  % (sid, Z2, ("%g" % DIVE_OUT), Z2, t_dive + DIVE_IN))
        js.append(ctx.enter("#%s-name1" % sid, t_dive + DIVE_IN + DIVE_OUT * 0.55, {"y": 12}))
        mark = '<i%s></i>' % ctx.item(dv["at"])[1]
    else:
        mark = ""
    html = '<div class="ob" id="%s-ob" style="height:%dpx">%s%s%s</div>' % (sid, Hd, "".join(back), "".join(worlds), mark)
    return html, js
