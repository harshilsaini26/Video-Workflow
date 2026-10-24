"""network: a neural network, columns of nodes joined by weighted edges; a pixel digit comes in, the forward pass lights
it layer by layer, the answer is ringed, and the error sweeps back from the output to the input ("backpropagation").

  {"type": "network", "layers": [4, 6, 6, 10], "labels": ["0", ..., "9"], "input": {"digit": 3, "at": "word:5"},
   "forward": "word:7", "answer": {"node": 8, "at": "word:10"}, "backward": "word:13"}

2 to 5 layers of 1 to 10 nodes; `labels` (one per output node) sit right of the last column; `input` draws a 5x7 pixel
digit on the left. The weights are seeded from the scene id (the same every render): a positive weight in the accent, a
negative one in the second accent, its strength as its opacity. Each step is a tween on the timeline (seek-safe).
"""
import math, random
from scenes import need

TYPE = "network"
BAKED = True                    # drawn in Python at the width it is given
DECOR_KEYS = ("layers", "labels", "input", "answer", "forward", "backward")   # a diagram's furniture, not a claim
ASPECT = 0.8
STEP = 0.3                      # a layer's turn in a pass (s)
L_SIZE, MAX_LABEL = 30, 3
DIGITS = ("01110100011001110101110011000101110", "00100011000010000100001000010001110", "01110100010000100010001000100011111",
          "11111000100010000010000011000101110", "00010001100101010010111110001000010", "11111100001111000001000011000101110",
          "00110010001000011110100011000101110", "11111000010001000100010000100001000", "01110100011000101110100011000101110",
          "01110100011000101111000010001001100")

CSS = """
  .nw { position:relative; width:100%%; }
  .nw svg { position:absolute; left:0; top:0; overflow:visible; }
  .nw-label { position:absolute; font-family: var(--label); font-weight:500; font-size:%dpx; line-height:1; opacity:0; }
""" % L_SIZE


def validate(scene):
    errs = need(scene, ["layers"])
    L = scene.get("layers") or []
    if not 2 <= len(L) <= 5:
        errs.append("a network takes 2 to 5 layers (got %d)" % len(L))
    if any(not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= 10 for n in L):
        errs.append("each layer has 1 to 10 nodes (got %s)" % L)
        return errs
    if scene.get("labels") is not None and (len(scene["labels"]) != (L[-1] if L else 0)
                                            or any(not 0 < len(str(x)) <= MAX_LABEL for x in scene["labels"])):
        errs.append("labels: one label per output node (%d), each 1 to %d characters" % (L[-1] if L else 0, MAX_LABEL))
    inp = scene.get("input")
    if inp is not None and (not isinstance(inp, dict) or inp.get("digit") not in range(10) or inp.get("at") is None):
        errs.append("input is {digit 0 to 9, at}")
    ans = scene.get("answer")
    if ans is not None and (not isinstance(ans, dict) or not isinstance(ans.get("node"), int) or not L
                            or not 0 <= ans["node"] < L[-1] or ans.get("at") is None):
        errs.append("answer node: {node (an output node, 0 to %d), at}" % ((L[-1] - 1) if L else 0))
    return errs


def height(scene, width):
    return int(math.ceil(width * ASPECT))


def min_width(scene):
    return 600


def min_text(scene):
    """The smallest text it draws (px), or None: only the output labels are words."""
    return L_SIZE if scene.get("labels") else None


def render(scene, ctx, box):
    c, sid = ctx.c, ctx.id
    Wd = box[2]
    H = height(scene, Wd)
    L = scene["layers"]
    rng = random.Random(sum(map(ord, sid)) * 7 + sum(L))
    pad = 30
    x0 = Wd * 0.26 if scene.get("input") else pad + 20
    x1 = Wd - (70 if scene.get("labels") else pad + 20)
    xs = [x0 + (x1 - x0) * l / (len(L) - 1) for l in range(len(L))]
    gap = (H - 2 * pad) / float(max(L))
    r = min(20, gap * 0.34)
    ys = [[H / 2.0 + (k - (n - 1) / 2.0) * gap for k in range(n)] for n in L]
    pos, neg = c["accent"], c["accent2"]
    edges, backs, nodes, fills = [], [], [], []
    for l in range(1, len(L)):
        e, b = [], []
        for i in range(L[l - 1]):
            for k in range(L[l]):
                w = rng.uniform(-1, 1)
                e.append('<line class="nw-edge" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-opacity="%.2f" stroke-width="2"/>'
                         % (xs[l - 1], ys[l - 1][i], xs[l], ys[l][k], pos if w > 0 else neg, 0.25 + 0.6 * abs(w)))
                b.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (xs[l - 1], ys[l - 1][i], xs[l], ys[l][k]))
        edges.append('<g id="%s-e%d" opacity="0.45">%s</g>' % (sid, l, "".join(e)))
        backs.append('<g id="%s-b%d" opacity="0" stroke="%s" stroke-width="3">%s</g>' % (sid, l, c["bad"], "".join(b)))
    ans = scene.get("answer")
    for l, n in enumerate(L):
        f = []
        for k in range(n):
            nodes.append('<circle class="nw-node" cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="%s" stroke-width="3"/>'
                         % (xs[l], ys[l][k], r, c["bg"], c["accent"] if l < len(L) - 1 else c["ink"]))
            act = 1.0 if (ans and l == len(L) - 1 and k == ans["node"]) else rng.uniform(0.12, 0.8 if l == len(L) - 1 else 1.0)
            f.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" fill-opacity="%.2f"/>' % (xs[l], ys[l][k], r - 3, c["ink"], act))
        fills.append('<g id="%s-a%d" opacity="0">%s</g>' % (sid, l, "".join(f)))
    extra, js = [], [ctx.enter("#%s-nw" % sid, ctx.t_in, {"scale": 0.94})]
    marks = []
    if scene.get("labels"):
        for k, lab in enumerate(scene["labels"]):
            hot = ans and k == ans["node"]
            extra.append('<div class="nw-label" id="%s-l%d" style="left:%.1fpx;top:%.1fpx;color:%s;font-weight:%d">%s</div>'
                         % (sid, k, x1 + r + 14, ys[-1][k] - L_SIZE / 2.0, c["ink"] if hot else c["dim"], 700 if hot else 500, ctx.esc(lab)))
        js.append(ctx.enter("#%s-nw .nw-label" % sid, ctx.t_in + 0.3, {"x": -10}, stagger=0.3))
    svg_px = ""
    if scene.get("input"):
        t, attrs = ctx.item(scene["input"]["at"])
        marks.append("<i%s></i>" % attrs)
        bits = DIGITS[scene["input"]["digit"]]
        cell = min((x0 - 2 * pad) / 5.0, (H * 0.5) / 7.0)
        gx, gy = pad, H / 2.0 - 3.5 * cell
        svg_px = ('<g id="%s-in" opacity="0"><rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none" stroke="%s" stroke-width="3"/>%s</g>'
                  % (sid, gx - 6, gy - 6, 5 * cell + 12, 7 * cell + 12, c["line"],
                     "".join('<rect class="nw-px" data-on="%s" x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" fill-opacity="%s"/>'
                             % (b, gx + (j % 5) * cell + 1, gy + (j // 5) * cell + 1, cell - 2, cell - 2, c["ink"], "1" if b == "1" else "0.08")
                             for j, b in enumerate(bits))))
        js.append(ctx.enter("#%s-in" % sid, t, {"x": -20}))
    if scene.get("forward") is not None:
        t, attrs = ctx.item(scene["forward"])
        marks.append("<i%s></i>" % attrs)
        for l in range(len(L)):
            js.append(ctx.enter("#%s-a%d" % (sid, l), t + l * STEP, dur=0.3))
            if l:
                js.append("tl.fromTo('#%s-e%d', { opacity: 0.45 }, { opacity: 1, duration: %.2f, ease: 'power2.out', immediateRender: false }, %.3f);"
                          % (sid, l, STEP, t + (l - 1) * STEP + 0.1))
                js.append("tl.to('#%s-e%d', { opacity: 0.6, duration: 0.5, ease: 'power2.inOut' }, %.3f);" % (sid, l, t + l * STEP + 0.1))
    ring = ""
    if ans:
        t, attrs = ctx.item(ans["at"])
        marks.append("<i%s></i>" % attrs)
        ring = ('<circle id="%s-ans" cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" stroke-width="5" opacity="0"/>'
                % (sid, xs[-1], ys[-1][ans["node"]], r + 9, c["accent2"]))
        js.append("tl.fromTo('#%s-ans', { opacity: 0, scale: 1.6, transformOrigin: '50%% 50%%' }, { opacity: 1, scale: 1, duration: 0.45, "
                  "ease: '%s', immediateRender: false }, %.3f);" % (sid, ctx.tokens["motion"]["enter_ease"], t))
    if scene.get("backward") is not None:
        t, attrs = ctx.item(scene["backward"])
        marks.append("<i%s></i>" % attrs)
        for l in range(len(L) - 1, 0, -1):
            at = t + (len(L) - 1 - l) * STEP
            js.append("tl.fromTo('#%s-b%d', { opacity: 0 }, { opacity: 0.9, duration: %.2f, ease: 'power2.out', immediateRender: false }, %.3f);"
                      % (sid, l, STEP, at))
            js.append("tl.to('#%s-b%d', { opacity: 0.15, duration: 0.6, ease: 'power2.inOut' }, %.3f);" % (sid, l, at + STEP))
    html = ('<div class="nw" id="%s-nw" style="height:%dpx;aspect-ratio:1 / %s"><svg width="%.0f" height="%d">%s%s%s%s%s%s</svg>%s%s</div>'
            % (sid, H, ASPECT, Wd, H, "".join(edges), "".join(backs), "".join(nodes), "".join(fills), ring, svg_px,
               "".join(extra), "".join(marks)))
    return html, js
