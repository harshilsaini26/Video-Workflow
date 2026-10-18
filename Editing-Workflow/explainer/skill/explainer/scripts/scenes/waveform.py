"""waveform: a sound you can see. One line of 200 points scrolls left for the scene's whole life (so the picture is never
still), and on each state's word its shape and size ease to that state's kind (0.6 s, power3.inOut) while the mono label
under it changes. For "on the street it's all noise... switch it on and it goes calm... then it's just the music":

  {"type": "waveform", "color": "accent",
   "states": [{"kind": "noise", "label": "THE STREET", "at": "word:5"},
              {"kind": "calm", "label": "NOISE CANCELLING ON", "at": "word:9"},
              {"kind": "music", "label": "JUST THE MUSIC", "at": "word:14"}]}

kind is noise, calm, music, pulse or flat (scenes/_wave.py draws them, from a seeded noise table: every render the
same); color is ink (the default) or accent. Before the first state's word the line already runs, quietly, in that
state's shape.
"""
import explainer_lib as E
from scenes import line_px, need, widest
from scenes import _wave

TYPE = "waveform"
MAX_SCALE = 1.4                  # the label stays a label (39 px drawn at most), the wave fills the column
PLOT = 300                       # the wave's height, px
L_SIZE, L_LH, L_GAP = 28, 1.3, 32
L_SPACING = 0.12
LABEL_MAX = 32                   # characters
COLORS = ("ink", "accent")

CSS = """
  .wf { width:100%%; display:flex; flex-direction:column; align-items:center; }
  .wf-plot { position:relative; width:100%%; height:%dpx; opacity:0; }
  .wf-plot svg { position:absolute; left:0; top:0; }
  .wf-labels { display:grid; width:100%%; margin-top:%dpx; }
  .wf-l { grid-area:1 / 1; font-family: var(--label); font-weight:500; font-size:%dpx; line-height:%dpx; letter-spacing:%sem;
    text-align:center; opacity:0; }
""" % (PLOT, L_GAP, L_SIZE, line_px(L_SIZE, L_LH), L_SPACING)


def validate(scene):
    errs = need(scene, ["states"])
    st = scene.get("states")
    if not isinstance(st, list) or not 1 <= len(st) <= 4:
        return ["a waveform takes 1 to 4 states (got %s)" % (len(st) if isinstance(st, list) else repr(st),)]
    for i, s in enumerate(st):
        if not isinstance(s, dict):
            errs.append("state %d is an object" % i)
            continue
        if s.get("kind") not in _wave.KINDS:
            errs.append("state %d: kind is one of %s (got %r)" % (i, ", ".join(_wave.KINDS), s.get("kind")))
        label = s.get("label")
        if not isinstance(label, str) or not label.strip():
            errs.append("state %d has no label (a short mono line under the wave)" % i)
        elif len(label) > LABEL_MAX:
            errs.append("state %d: the label is at most %d characters (got %d: %r)" % (i, LABEL_MAX, len(label), label))
        if s.get("at") is None:
            errs.append("state %d has no at (the word its shape arrives on)" % i)
    if scene.get("color") is not None and scene["color"] not in COLORS:
        errs.append("color is ink or accent (got %r)" % (scene["color"],))
    return errs


def _label_lines(scene, width):
    return max(E.text_lines(s["label"], L_SIZE, width, "mono500", spacing=L_SPACING) for s in scene["states"])


def height(scene, width):
    return PLOT + L_GAP + line_px(L_SIZE, L_LH) * _label_lines(scene, width)


def min_width(scene):
    return max(240, widest([(s["label"], L_SIZE) for s in scene["states"]], pad=2, font="mono500", spacing=L_SPACING))


def render(scene, ctx, box):
    sid, c = ctx.id, ctx.c
    width = box[2]
    st = scene["states"]
    times = []
    for s in st:
        times.append(ctx.item(s["at"]))
    if any(b[0] <= a[0] for a, b in zip(times, times[1:])):
        ctx.fail("the states move forward in time, each on a later word (got %s)" % ", ".join(s["at"] for s in st))
    wave = _wave.Wave(ctx, "%s-wave" % sid, width, PLOT, st[0]["kind"])
    stroke = c[scene.get("color") or "ink"]
    labels = "".join('<div class="wf-l" id="%s-l%d"%s style="color:%s">%s</div>' % (sid, i, attrs, ctx.ink, ctx.esc(s["label"]))
                     for i, (s, (_, attrs)) in enumerate(zip(st, times)))
    html = ('<div class="wf"><div class="wf-plot" id="%s-plot">%s</div><div class="wf-labels">%s</div></div>'
            % (sid, _wave.svg("%s-wave" % sid, width, PLOT, stroke), labels))
    js = wave.setup() + [ctx.enter("#%s-plot" % sid, ctx.t_in, {"y": 24})]
    ease = ctx.tokens["motion"]["exit_ease"]
    for i, (s, (t, _)) in enumerate(zip(st, times)):
        js.append(wave.to(s["kind"], t))
        if i:     # the old label leaves first, then the new one rises: the two never share the line
            js.append("tl.fromTo('#%s-l%d', { opacity: 1 }, { opacity: 0, duration: 0.15, ease: '%s', immediateRender: false }, %.3f);"
                      % (sid, i - 1, ease, t))
            js.append(ctx.enter("#%s-l%d" % (sid, i), t + 0.15, {"y": 12}, dur=0.3))
        else:
            js.append(ctx.enter("#%s-l0" % sid, t, {"y": 12}))
    ctx.ambient(wave.scroll(ctx.t_in, ctx.t_out))
    return html, js
