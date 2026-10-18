"""thread.py: the thread, one line through the reel (the editorial reels run a cable from scene to scene: it drops in,
becomes the I of a word, loops round a year, turns into a waveform, a ruler, the spine of a diagram).

  "thread": {"color": "ink", "width": 8, "keys": [
      {"at": "word:3", "shape": "drop", "x": 540, "to": 900},
      {"at": "word:9", "shape": "loop", "x": 540, "y": 1000, "rx": 320, "ry": 90},
      {"at": "word:20", "shape": "wave", "y": 1500, "amp": 60},
      {"at": "word:40", "shape": "off"}]}

Shapes (frame pixels, N points each, so any shape morphs into any other):
- drop: a vertical line from above the frame down to `to` at `x` (540, 900);
- loop: a drop to the top of an ellipse (x, y, rx, ry: 540, 1000, 300, 90) and once round it;
- wave: a waveform across the frame at `y` (1500), `amp` (60) high, `period` (360) long; it scrolls while it holds;
- rule: a vertical line at `x` from `from` to `to` (540, 345 to 1105), a ruler for a timeline;
- underline: a horizontal line at `y` (330) from `x0` to `x1` (65 to 1015);
- off: the line lifts straight up out of the frame where it last was.
No key's shape may rest in the captions (the band y 1130 to 1235 inside the column x 150 to 930): a stem goes down the
outer edge, a loop or a wave sits above or below the band (gate E3 names the key). A morph from one side of the band
to the other passes behind the captions for a moment, under their halo.
The first key draws the line on (0.8 s); each later key morphs into its shape on its word (0.6 s, power3.inOut). One
tween runs for the whole reel and its onUpdate draws the shape for the timeline's own time, so any frame a seek lands
on is the same picture. The layer sits above the ground and under the scenes and the captions (z-index 5); gate E5
treats it as the ground (a line may pass behind a scene's words), gate E4 counts each morph as a change.
"""
import json, math
import explainer_lib as E

SHAPES = ("drop", "loop", "wave", "rule", "underline", "off")
N = 96
DRAW, MORPH = 0.8, 0.6
SCROLL = 40.0                      # px a second a wave travels while it holds
SCROLL_MAX = 900.0                 # and no further: the wave's left end (x -1000) never comes into the frame
NUMBERS = ("x", "y", "to", "from", "rx", "ry", "amp", "period", "x0", "x1")
COLORS = ("ink", "accent")
TOP = -40                          # above the frame


def _lerp(a, b, n):
    return [(a[0] + (b[0] - a[0]) * i / (n - 1.0), a[1] + (b[1] - a[1]) * i / (n - 1.0)) for i in range(n)]


def points(shape, p, prev=None):
    """N (x, y) points of a shape in frame pixels; `prev` (the last shape's points) places an `off`."""
    if shape == "drop":
        x = p.get("x", 540)
        return _lerp((x, TOP), (x, p.get("to", 900)), N)
    if shape == "rule":
        x = p.get("x", 540)
        return _lerp((x, p.get("from", E.SCENE["top"])), (x, p.get("to", E.SCENE["bottom"])), N)
    if shape == "underline":
        y = p.get("y", 330)
        return _lerp((p.get("x0", E.SCENE["left"]), y), (p.get("x1", E.SCENE["right"]), y), N)
    if shape == "loop":
        x, y, rx, ry = p.get("x", 540), p.get("y", 1000), p.get("rx", 300), p.get("ry", 90)
        n1 = N // 3
        stem = _lerp((x, TOP), (x, y - ry), n1)
        ring = [(x + rx * math.sin(2 * math.pi * k / (N - n1)), y - ry * math.cos(2 * math.pi * k / (N - n1)))
                for k in range(1, N - n1 + 1)]
        return stem + ring
    if shape == "wave":
        y, amp, per = p.get("y", 1500), p.get("amp", 60), float(p.get("period", 360))
        xs = [-1000 + 2100.0 * i / (N - 1) for i in range(N)]       # a long run to the left: it scrolls right while it holds
        return [(x, y + amp * (0.7 * math.sin(2 * math.pi * x / per) + 0.3 * math.sin(2 * math.pi * x / (per * 0.37) + 1.3)))
                for x in xs]
    if shape == "off":
        return [(x, TOP) for x, _ in (prev or points("drop", {}))]     # every point lifts straight up out of the frame
    raise ValueError("no thread shape %r (the shapes are %s)" % (shape, ", ".join(SHAPES)))


def _number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def crosses_captions(pts):
    """True when a shape passes through the caption band inside the caption column (it would strike the words through)."""
    (y0, y1), (x0, x1) = E.CAPTION_BAND, (E.L.NARROW["left"], E.L.NARROW["right"])
    return any(x0 <= x <= x1 and y0 <= y <= y1 for x, y in pts)


def validate(spec, words):
    if not isinstance(spec, dict) or not isinstance(spec.get("keys"), list) or not spec["keys"]:
        return ["the thread is {\"keys\": [{\"at\": \"word:N\", \"shape\": ...}], \"color\", \"width\"}"]
    errs = []
    if spec.get("color", "ink") not in COLORS:
        errs.append("color is ink or accent (got %r)" % spec.get("color"))
    width = spec.get("width", 8)
    if not _number(width) or not 4 <= width <= 16:
        errs.append("width is 4 to 16 px (got %r)" % (width,))
    last, prev = -1.0, None
    for i, k in enumerate(spec["keys"]):
        if not isinstance(k, dict):
            errs.append("key %d is {\"at\": \"word:N\", \"shape\": ...} (got %r)" % (i, k))
            continue
        nan = [n for n in NUMBERS if n in k and not _number(k[n])]
        if nan:
            errs.append("key %d: %s must be a number (got %s)" % (i, ", ".join(nan), ", ".join(repr(k[n]) for n in nan)))
        elif k.get("shape") == "wave" and k.get("period", 360) <= 0:
            errs.append("key %d: a wave's period is more than 0 px (got %r)" % (i, k["period"]))
        elif k.get("shape") not in SHAPES:
            errs.append("key %d: no shape %r (the shapes are %s)" % (i, k.get("shape"), ", ".join(SHAPES)))
        else:
            prev = points(k["shape"], k, prev)
            if k["shape"] != "off" and crosses_captions(prev):
                errs.append("key %d (%s) runs through the captions (y %d to %d, x %d to %d): keep a stem to the outer edge "
                            "(x under %d or over %d) and a loop or wave above or below the band"
                            % (i, k["shape"], E.CAPTION_BAND[0], E.CAPTION_BAND[1], E.L.NARROW["left"], E.L.NARROW["right"],
                               E.L.NARROW["left"], E.L.NARROW["right"]))
        try:
            t = E.resolve(k.get("at"), words, lead=True)
        except (ValueError, TypeError) as e:
            errs.append("key %d: %s" % (i, e))
            continue
        if t <= last:
            errs.append("key %d (%s) is not after the key before it: keys go in time order" % (i, k.get("at")))
        last = t
    return errs


def render(spec, words, tok, D, ground_at, grounds=()):
    """(html, js, spans): the layer, its timeline lines, and the moments of change for pace-check. `grounds` are the
    times the ground may change (each scene's start): the line takes that ground's colour then, key or no key."""
    keys, prev, pts, times = spec["keys"], None, [], []
    for k in keys:
        prev = points(k["shape"], k, prev)
        pts.append([[round(x, 1), round(y, 1)] for x, y in prev])
        times.append(round(max(0.0, E.resolve(k["at"], words, lead=True)), 3))
    waves = [1 if k["shape"] == "wave" else 0 for k in keys]
    held = lambda i: min(SCROLL_MAX, max(0.0, times[i + 1] - times[i] - MORPH) * SCROLL)
    offs = [0] + [round(held(i - 1), 1) if waves[i - 1] else 0 for i in range(1, len(keys))]   # where a wave had got to
    pts = [[[round(x + offs[i], 1), y] for x, y in p] if keys[i]["shape"] == "off" else p for i, p in enumerate(pts)]
    role = spec.get("color", "ink")
    color = E.theme(tok, ground_at(times[0]))[role]
    html = ('    <svg class="thread" data-thread="1" width="1080" height="1920" viewBox="0 0 1080 1920"><g id="th-g"><path id="th-p" pathLength="1" '
            'd="M0 0" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round" '
            'style="stroke-dasharray:1;stroke-dashoffset:1"/></g></svg>\n' % (color, spec.get("width", 8)))
    js = ["const TH_K = %s;" % json.dumps(pts, separators=(",", ":")),
          "const TH_T = %s;" % json.dumps(times),
          "const TH_W = %s;" % json.dumps(waves),
          "const TH_O = %s;" % json.dumps(offs),
          "const TH_E = gsap.parseEase('power3.inOut');",
          "const TH_P = { v: 0 };",
          ("function thAt(t) {\n"
           "          const p = document.getElementById('th-p'), g = document.getElementById('th-g');\n"
           "          let i = -1; for (let k = 0; k < TH_T.length; k++) if (TH_T[k] <= t + 1e-6) i = k;\n"
           "          p.style.strokeDashoffset = i < 0 ? 1 : Math.max(0, 1 - (t - TH_T[0]) / %s);\n"
           "          if (i < 0) i = 0;\n"
           "          const m = i > 0 ? TH_E(Math.min(1, (t - TH_T[i]) / %s)) : 1, a = TH_K[Math.max(0, i - 1)], b = TH_K[i];\n"
           "          let d = '';\n"
           "          for (let n = 0; n < b.length; n++) {\n"
           "            const ax = a[n][0] + TH_O[i], x = ax + (b[n][0] - ax) * m, y = a[n][1] + (b[n][1] - a[n][1]) * m;\n"
           "            d += (n ? ' L' : 'M') + x.toFixed(1) + ' ' + y.toFixed(1);\n"
           "          }\n"
           "          p.setAttribute('d', d);\n"
           "          const hold = TH_W[i] ? Math.max(0, t - TH_T[i] - %s) : 0;\n"
           "          g.setAttribute('transform', 'translate(' + Math.min(%s, hold * %s).toFixed(1) + ' 0)');\n"
           "        }") % (DRAW, MORPH, MORPH, SCROLL_MAX, SCROLL),
          "tl.fromTo(TH_P, { v: 0 }, { v: 1, duration: %.3f, ease: 'none', immediateRender: false, onUpdate: function () { thAt(tl.time()); } }, 0);" % D,
          "thAt(0);"]
    cur = color
    for t0 in sorted(set(t for t in list(times[1:]) + [float(g) for g in grounds] if t > times[0])):
        c = E.theme(tok, ground_at(t0))[role]
        if c != cur:
            js.append("tl.set('#th-p', { attr: { stroke: '%s' } }, %.3f);" % (c, t0))
            cur = c
    spans = [[times[0], round(times[0] + DRAW, 3)]] + [[t, round(t + MORPH, 3)] for t in times[1:]]
    return html, js, spans


CSS = """
  .thread { position:absolute; left:0; top:0; width:1080px; height:1920px; z-index:5; pointer-events:none; overflow:visible; }
"""
