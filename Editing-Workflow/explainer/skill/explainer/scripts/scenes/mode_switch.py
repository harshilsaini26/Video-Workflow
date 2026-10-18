"""mode-switch: a segmented control (a light paper track of chips, like a headphone app's) with a wave under it. On each
option's word its chip fills and a bar slides under it, the wave eases to that option's shape and the note line
under it changes. For "quiet mode shuts the street out, aware mode lets it back in":

  {"type": "mode-switch",
   "options": [{"label": "QUIET", "wave": "calm", "note": "The street goes away", "at": "word:5"},
               {"label": "AWARE", "wave": "noise", "note": "You hear the traffic again", "at": "word:9"},
               {"label": "IMMERSE", "wave": "music", "note": "Just the music, all around you", "at": "word:14"}]}

2 to 4 options, named left to right in the order the voice says them; labels are JetBrains Mono, 10 characters at most;
wave is a waveform kind (noise, calm, music, pulse, flat; scenes/_wave.py). Each label is its own chip: on its word
the chip fills with the accent and its text turns light while the last one empties, and a bar slides along the foot of
the track to it. Every label is on the page once and sits on its own chip (gate E5: no text on a shape not its own).
"""
import explainer_lib as E
from scenes import line_px, need, widest
from scenes import _wave

TYPE = "mode-switch"
MAX_SCALE = 1.4
TRACK_H, TP = 84, 6              # the track, and the chips' inset in it
BAR_ROOM, BAR_Y = 12, 4          # the foot of the track the bar runs along
O_SIZE, O_SPACING, O_PAD = 30, 0.06, 14
LABEL_MAX = 10
PLOT, PLOT_GAP = 240, 40         # the wave under the control
N_SIZE, N_LH, N_GAP = 36, 1.25, 24
SLIDE = 0.6

CSS = """
  .ms { width:100%%; display:flex; flex-direction:column; align-items:center; }
  .ms-track { position:relative; width:100%%; height:%dpx; border-radius:%dpx; opacity:0; }
  .ms-row { position:absolute; left:%dpx; right:%dpx; top:%dpx; bottom:%dpx; display:flex; }
  .ms-bar { position:absolute; left:%dpx; bottom:%dpx; height:4px; border-radius:%dpx; transform:scaleX(0); }
  .ms-o { flex:1 1 0; min-width:0; display:flex; align-items:center; justify-content:center; border-radius:%dpx; font-family: var(--label);
    font-weight:500; font-size:%dpx; line-height:%dpx; letter-spacing:%sem; white-space:nowrap; }
  .ms-plot { position:relative; width:100%%; height:%dpx; margin-top:%dpx; opacity:0; }
  .ms-plot svg { position:absolute; left:0; top:0; }
  .ms-notes { display:grid; width:100%%; margin-top:%dpx; }
  .ms-n { grid-area:1 / 1; font-weight:500; font-size:%dpx; line-height:%dpx; text-align:center; opacity:0; }
""" % (TRACK_H, TRACK_H // 2, TP, TP, TP, BAR_ROOM, TP, BAR_Y, 2, (TRACK_H - TP - BAR_ROOM) // 2, O_SIZE, line_px(O_SIZE, 1.25), O_SPACING,
       PLOT, PLOT_GAP, N_GAP, N_SIZE, line_px(N_SIZE, N_LH))


def validate(scene):
    errs = need(scene, ["options"])
    ops = scene.get("options")
    if not isinstance(ops, list) or not 2 <= len(ops) <= 4:
        return ["a mode-switch takes 2 to 4 options (got %s)" % (len(ops) if isinstance(ops, list) else repr(ops),)]
    for i, o in enumerate(ops):
        if not isinstance(o, dict):
            errs.append("option %d is an object" % i)
            continue
        label = o.get("label")
        if not isinstance(label, str) or not label.strip():
            errs.append("option %d has no label (the mode's name in the control)" % i)
        elif len(label) > LABEL_MAX:
            errs.append("option %d: the label is at most %d characters (got %d: %r)" % (i, LABEL_MAX, len(label), label))
        if o.get("wave") not in _wave.KINDS:
            errs.append("option %d: wave is one of %s (got %r)" % (i, ", ".join(_wave.KINDS), o.get("wave")))
        note = o.get("note")
        if not isinstance(note, str) or not note.strip():
            errs.append("option %d has no note (a short line under the wave)" % i)
        elif len(note) > 60:
            errs.append("option %d: the note is at most 60 characters (got %d)" % (i, len(note)))
        if o.get("at") is None:
            errs.append("option %d has no at (the word its chip fills on)" % i)
    return errs


def _cell(scene):
    return max(E.text_width(o["label"], O_SIZE, "mono500", spacing=O_SPACING) for o in scene["options"]) + 2 * O_PAD


def height(scene, width):
    lines = max(E.text_lines(o["note"], N_SIZE, width, "display500") for o in scene["options"])
    return TRACK_H + PLOT_GAP + PLOT + N_GAP + line_px(N_SIZE, N_LH) * lines


def min_width(scene):
    row = int(len(scene["options"]) * _cell(scene)) + 2 * TP + 2
    return max(row, widest([(o["note"], N_SIZE) for o in scene["options"]], pad=2, font="display500"))


def render(scene, ctx, box):
    sid, c, p = ctx.id, ctx.c, ctx.pc            # the control is light paper on any ground; the wave and notes are on the ground
    width = box[2]
    ops = scene["options"]
    n = len(ops)
    times = [ctx.item(o["at"]) for o in ops]
    if any(b[0] <= a[0] for a, b in zip(times, times[1:])):
        ctx.fail("the options move forward in time, left to right, each on a later word (got %s)" % ", ".join(o["at"] for o in ops))
    clear = E.rgba(p["accent"], 0)
    chips = "".join('<span class="ms-o" id="%s-o%d"%s style="background:%s;color:%s">%s</span>' % (sid, i, attrs, clear, p["dim"], ctx.esc(o["label"]))
                    for i, (o, (_, attrs)) in enumerate(zip(ops, times)))
    track = ('<div class="ms-track" id="%s-track" style="background:%s;box-shadow:inset 0 0 0 2px %s, %s"><div class="ms-row">%s</div>'
             '<i class="ms-bar" id="%s-bar" style="width:calc((100%% - %dpx) / %d);background:%s"></i></div>'
             % (sid, p["chrome"], p["card_line"], c["shadow"], chips, sid, 2 * TP, n, p["accent"]))
    notes = "".join('<div class="ms-n" id="%s-n%d" style="color:%s">%s</div>' % (sid, i, c["dim"], ctx.esc(o["note"])) for i, o in enumerate(ops))
    wave = _wave.Wave(ctx, "%s-wave" % sid, width, PLOT, ops[0]["wave"])
    html = ('<div class="ms">%s<div class="ms-plot" id="%s-plot">%s</div><div class="ms-notes">%s</div></div>'
            % (track, sid, _wave.svg("%s-wave" % sid, width, PLOT, c["ink"]), notes))
    m = ctx.tokens["motion"]
    fade = lambda sel, a, b, dur, t, ease: ("tl.fromTo('%s', { opacity: %d }, { opacity: %d, duration: %s, ease: '%s', immediateRender: false }, %.3f);"
                                           % (sel, a, b, dur, ease, t))
    js = wave.setup() + [ctx.enter("#%s-track" % sid, ctx.t_in, {"y": 24}), ctx.enter("#%s-plot" % sid, ctx.t_in + 0.1, {"y": 24})]
    paint = lambda k, a, b, t, ease: ("tl.fromTo('#%s-o%d', { backgroundColor: '%s', color: '%s' }, { backgroundColor: '%s', color: '%s', duration: 0.3, "
                                      "ease: '%s', immediateRender: false }, %.3f);" % (sid, k, a[0], a[1], b[0], b[1], ease, t))
    off, on = (clear, p["dim"]), (p["accent"], p["on_accent"])
    for i, (o, (t, _)) in enumerate(zip(ops, times)):
        js.append(wave.to(o["wave"], t))
        js.append(paint(i, off, on, t, m["enter_ease"]))
        if i == 0:      # the bar arrives under the first option
            js.append("tl.fromTo('#%s-bar', { scaleX: 0 }, { scaleX: 1, duration: 0.3, ease: '%s', immediateRender: false }, %.3f);" % (sid, m["enter_ease"], t))
            js.append(ctx.enter("#%s-n0" % sid, t + 0.15, {"y": 12}, dur=0.3))
            continue
        js.append(paint(i - 1, on, off, t, m["exit_ease"]))
        js.append("tl.fromTo('#%s-bar', { xPercent: %s }, { xPercent: %s, duration: %s, ease: 'power3.inOut', immediateRender: false }, %.3f);"
                  % (sid, _fmt(100.0 * (i - 1)), _fmt(100.0 * i), _wave._n(SLIDE), t))
        js.append(fade("#%s-n%d" % (sid, i - 1), 1, 0, 0.15, t, m["exit_ease"]))
        js.append(ctx.enter("#%s-n%d" % (sid, i), t + 0.15, {"y": 12}, dur=0.3))
    ctx.ambient(wave.scroll(ctx.t_in, ctx.t_out))
    return html, js


def _fmt(v):
    v = round(v, 3)
    return ("%.3f" % v).rstrip("0").rstrip(".") if v else "0"
