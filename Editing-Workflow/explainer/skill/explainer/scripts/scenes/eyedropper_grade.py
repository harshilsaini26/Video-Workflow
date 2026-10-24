"""eyedropper-grade: a picture on a light paper panel with a palette bar under it. On each pick's word an eyedropper
glides to a point on the picture, a round loupe shows the colour it picked, a drop of that colour flies down into the
palette bar (its slot fills with the swatch, its name and its hex code), and the picture's grade tints toward it. For
"pull the orange out of the sunset", "match the shadows to the jacket":

  {"type": "eyedropper-grade", "src": "still.jpg",
   "picks": [{"color": "peach", "x": 0.62, "y": 0.35, "at": "word:6"},
             {"color": "teal", "label": "Shadows", "x": 0.2, "y": 0.8, "at": "word:10"}]}

`color` is a Catppuccin Latte colour name (tokens.json's palette), so every colour on the page stays in the palette;
x and y place the point as fractions of the picture (0 to 1, from its top left). `src` (a PNG or JPG next to
storyboard.json) is optional: without it the panel shows a built-in sunset. Points and hex codes are furniture.
"""
import math
import explainer_lib as E
from scenes import SLOT, js_obj, need
from scenes import _vg

TYPE = "eyedropper-grade"
DECOR_KEYS = {"x", "y"}
PALETTE_NAMES = set(E.load_tokens()["palette"])
PIC_H = 400                              # the picture
PAD_X, PAD_T, PAD_B = 20, 24, 26         # the palette bar's padding
SLOT_H, GAP, RADIUS = 88, 14, 30         # a palette slot, the gap between slots, the panel's corners
SW, SW_L, SW_R, SW_E = 44, 14, 12, 14     # the swatch, its left margin, swatch to text, text to the slot's edge
STACK_H, STACK_SW, STACK_GAP, STACK_PAD = 146, 40, 8, 14   # three picks: each slot stacks swatch, name and hex (narrower)
N_SIZE, H_SIZE = 30, 28                  # the colour's name (DM Sans 700), its hex code (JetBrains Mono 500)
N_LINE, H_LINE = 36, 34
CUR = 64                                 # the eyedropper cursor
HOT = (5, 59)                            # its tip, inside the cursor's box
LOUPE, RING = 104, 6                     # the loupe's diameter and its white ring
DROP = 30
TINT = 0.85                              # how far the picture tints toward the picked colour
REST = (0.84, 0.82)                      # where the cursor waits, as fractions of the picture

CSS = """
  .ed { position:relative; width:100%%; border-radius:%dpx; overflow:hidden; opacity:0; }
  .ed-pic { position:absolute; left:0; top:0; width:100%%; height:%dpx; overflow:hidden; }
  .ed-tint { position:absolute; left:0; top:0; width:100%%; height:100%%; mix-blend-mode:soft-light; opacity:0; }
  .ed-cur { position:absolute; left:0; top:0; width:%dpx; height:%dpx; opacity:0; }
  .ed-cur svg { position:absolute; left:0; top:0; width:100%%; height:100%%; }
  .ed-loupe { position:absolute; left:0; top:0; width:%dpx; height:%dpx; border-radius:50%%; opacity:0; }
  .ed-loupe i { position:absolute; left:50%%; top:50%%; border-radius:2px; }
  .ed-mark { position:absolute; width:24px; height:24px; margin:-12px 0 0 -12px; border-radius:50%%; opacity:0; }
  .ed-drop { position:absolute; left:0; top:0; width:%dpx; height:%dpx; border-radius:50%%; opacity:0; }
  .ed-slot { position:absolute; height:%dpx; border-radius:20px; display:flex; align-items:center; padding-left:%dpx; gap:%dpx; }
  .ed-sw { position:relative; flex:none; width:%dpx; height:%dpx; border-radius:50%%; }
  .ed-sw b { position:absolute; left:0; top:0; width:100%%; height:100%%; border-radius:50%%; transform:scale(0); }
  .ed-slot.st { flex-direction:column; justify-content:center; padding-left:0; gap:%dpx; }
  .ed-slot.st .ed-sw { width:%dpx; height:%dpx; }
  .ed-slot.st .ed-txt { align-items:center; }
  .ed-txt { display:flex; flex-direction:column; white-space:nowrap; }
  .ed-n { font-weight:700; font-size:%dpx; line-height:%dpx; }
  .ed-h { font-family: var(--label); font-weight:500; font-size:%dpx; line-height:%dpx; letter-spacing:.02em; }
""" % (RADIUS, PIC_H, CUR, CUR, LOUPE, LOUPE, DROP, DROP, SLOT_H, SW_L, SW_R, SW, SW, STACK_GAP, STACK_SW, STACK_SW, N_SIZE, N_LINE, H_SIZE, H_LINE) + _vg.CSS


def _name(p):
    return p.get("label") or str(p.get("color", "")).capitalize()


def _frac(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v <= 1


def validate(scene):
    errs = need(scene, ["picks"])
    picks = scene.get("picks") or []
    if not isinstance(picks, list) or not 1 <= len(picks) <= 3:
        return errs + ["an eyedropper-grade takes 1 to 3 picks (got %s)" % (len(picks) if isinstance(picks, list) else picks,)]
    for i, p in enumerate(picks):
        if not isinstance(p, dict):
            errs.append("pick %d is an object" % i)
            continue
        if p.get("color") not in PALETTE_NAMES:
            errs.append("pick %d: color is a Catppuccin Latte colour name (one of %s; got %r)"
                        % (i, ", ".join(sorted(PALETTE_NAMES)), p.get("color")))
        for k in ("x", "y"):
            if not _frac(p.get(k)):
                errs.append("pick %d: %s is a fraction of the picture, 0 to 1 (got %r)" % (i, k, p.get(k)))
        if p.get("at") is None:
            errs.append("pick %d has no at" % i)
        if p.get("label") is not None and not str(p["label"]).strip():
            errs.append("pick %d: label is empty" % i)
    e = _vg.check_src(scene.get("src"))
    return errs + ([e] if e else [])


def stacked(scene):
    """Three slots side by side would leave the hex codes too small: each one stacks instead."""
    return len(scene["picks"]) == 3


def slot_h(scene):
    return STACK_H if stacked(scene) else SLOT_H


def height(scene, width):
    return PIC_H + PAD_T + slot_h(scene) + PAD_B


def _slot_min(scene):
    hexw = E.text_width("#FFFFFF", H_SIZE, "mono500", spacing=0.02)
    text = int(math.ceil(max(max(E.text_width(_name(p), N_SIZE), hexw) for p in scene["picks"])))
    return text + 2 * STACK_PAD if stacked(scene) else text + SW_L + SW + SW_R + SW_E


def min_width(scene):
    n = len(scene["picks"])
    return 2 * PAD_X + n * _slot_min(scene) + (n - 1) * GAP


def _px(v):
    return round(v, 2)


def render(scene, ctx, box):
    pc, sid, W = ctx.pc, ctx.id, box[2]
    pal, mo = ctx.tokens["palette"], ctx.tokens["motion"]
    picks = scene["picks"]
    n = len(picks)
    slot_w = (W - 2 * PAD_X - (n - 1) * GAP) / float(n)
    halo = E.rgba(pc["ink"], 0.22)
    tints, marks, drops, slots, js = [], [], [], [], []
    cursor = ('<div class="ed-cur" id="%s-cur" style="color:%s">%s%s</div>'
              % (sid, pc["ink"], _vg.glyph("pipette", width=5).replace('stroke="currentColor"', 'stroke="%s"' % pc["card"]),
                 _vg.glyph("pipette", width=2.2)))
    loupe = ('<div class="ed-loupe" id="%s-lp" style="box-shadow:inset 0 0 0 %dpx %s, 0 10px 26px %s">'
             '<i style="width:22px;height:4px;margin:-2px 0 0 -11px;background:%s"></i><i style="width:4px;height:22px;margin:-11px 0 0 -2px;background:%s"></i></div>'
             % (sid, RING, pc["card"], halo, pc["card"], pc["card"]))
    rest = (REST[0] * W - HOT[0], REST[1] * PIC_H - HOT[1])
    js.append("tl.set('#%s-cur', %s, 0);" % (sid, js_obj({"x": _px(rest[0]), "y": _px(rest[1])})))
    js.append(ctx.enter("#%s-cur" % sid, ctx.t_in + 0.2, {"scale": 0.8}))
    at, prev_t, prev_end = rest, None, ctx.t_in + 0.3
    for i, p in enumerate(picks):
        t, attrs = ctx.item(p["at"])
        if prev_t is not None and t < prev_t + 0.4:
            ctx.fail("pick %d lands %.2f s after the one before it; give each pick its own word, at least 0.4 s apart" % (i, t - prev_t))
        col = pal[p["color"]]
        px, py = p["x"] * W, p["y"] * PIC_H
        # the cursor glides in just before the word, so the pick itself lands on it
        start = max(prev_end, t - 0.55)
        dur = max(0.05, t - start)
        to = (px - HOT[0], py - HOT[1])
        js.append(_vg.tween("#%s-cur" % sid, {"x": _px(at[0]), "y": _px(at[1])},
                            {"x": _px(to[0]), "y": _px(to[1]), "duration": round(dur, 3), "ease": "power3.inOut"}, start))
        at = to
        # the point marks the picture; the loupe opens beside it, up and to the right where there is room
        marks.append('<i class="ed-mark" id="%s-m%d"%s style="left:%spx;top:%spx;background:%s;box-shadow:inset 0 0 0 5px %s, 0 2px 8px %s"></i>'
                     % (sid, i, attrs, _px(px), _px(py), col, pc["card"], halo))
        js.append(ctx.enter("#%s-m%d" % (sid, i), t, {"scale": 0.3}, dur=0.3))
        lx = px + 40 if px + 40 + LOUPE <= W - 12 else px - 40 - LOUPE
        ly = py - 40 - LOUPE if py - 40 - LOUPE >= 12 else min(py + 40, PIC_H - LOUPE - 12)
        js.append("tl.set('#%s-lp', %s, %.3f);" % (sid, js_obj({"x": _px(lx), "y": _px(ly), "backgroundColor": col}), t))
        js.append(_vg.tween("#%s-lp" % sid, {"opacity": 0, "scale": 0.6}, {"opacity": 1, "scale": 1, "duration": 0.3, "ease": mo["enter_ease"]}, t))
        js.append(_vg.tween("#%s-lp" % sid, {"opacity": 1}, {"opacity": 0, "duration": 0.3, "ease": mo["exit_ease"]}, t + 0.95))
        # a drop of the colour flies from the loupe into its slot, and the slot fills as it lands
        if stacked(scene):    # the swatch tops the slot's centred stack
            sx = PAD_X + i * (slot_w + GAP) + slot_w / 2.0
            sy = PIC_H + PAD_T + (STACK_H - (STACK_SW + STACK_GAP + N_LINE + H_LINE)) / 2.0 + STACK_SW / 2.0
        else:
            sx = PAD_X + i * (slot_w + GAP) + SW_L + SW / 2.0
            sy = PIC_H + PAD_T + SLOT_H / 2.0
        d0 = (lx + LOUPE / 2.0 - DROP / 2.0, ly + LOUPE / 2.0 - DROP / 2.0)
        d1 = (sx - DROP / 2.0, sy - DROP / 2.0)
        drops.append('<i class="ed-drop" id="%s-d%d" style="background:%s;box-shadow:inset 0 0 0 4px %s"></i>' % (sid, i, col, pc["card"]))
        js.append(_vg.tween("#%s-d%d" % (sid, i), {"x": _px(d0[0]), "y": _px(d0[1]), "opacity": 1},
                            {"x": _px(d1[0]), "y": _px(d1[1]), "duration": 0.45, "ease": "power3.inOut"}, t + 0.2))
        js.append(_vg.tween("#%s-d%d" % (sid, i), {"opacity": 1}, {"opacity": 0, "duration": 0.15, "ease": "none"}, t + 0.65))
        js.append(_vg.tween("#%s-s%d b" % (sid, i), {"scale": 0}, {"scale": 1, "duration": 0.35, "ease": mo["enter_ease"]}, t + 0.6))
        slots.append('<div class="ed-slot%s" id="%s-s%d" style="left:%spx;top:%dpx;width:%spx;height:%dpx;background:%s;box-shadow:inset 0 0 0 2px %s">'
                     '<span class="ed-sw" style="box-shadow:inset 0 0 0 3px %s"><b style="background:%s"></b></span>'
                     '<span class="ed-txt gt"><span class="ed-n" style="color:%s">%s</span><span class="ed-h" style="color:%s">%s</span></span></div>'
                     % (" st" if stacked(scene) else "", sid, i, _px(PAD_X + i * (slot_w + GAP)), PIC_H + PAD_T, _px(slot_w), slot_h(scene), pc["chrome"], pc["line"], pc["line"], col,
                        pc["ink"], ctx.esc(_name(p)), pc["dim"], col.upper()))
        js += ctx.slot("#%s-s%d" % (sid, i))
        js.append(ctx.enter("#%s-s%d" % (sid, i), t + 0.55, {"opacity": SLOT}, dur=0.3))
        js.append(ctx.fill("#%s-s%d" % (sid, i), t + 0.55))
        # the picture leans toward the colour (the last pick's tint gives way)
        tints.append('<i class="ed-tint" id="%s-t%d" style="background:%s"></i>' % (sid, i, col))
        js.append(_vg.tween("#%s-t%d" % (sid, i), {"opacity": 0}, {"opacity": TINT, "duration": 0.8, "ease": "power2.inOut"}, t + 0.6))
        if i:
            js.append(_vg.tween("#%s-t%d" % (sid, i - 1), {"opacity": TINT}, {"opacity": 0, "duration": 0.8, "ease": "power2.inOut"}, t + 0.6))
        prev_t, prev_end = t, t + 0.95
    # the cursor steps aside once the last colour is in, so the graded picture shows whole
    back = (min(at[0] + 60, W - CUR - 8), min(at[1] + 40, PIC_H - CUR - 8))
    if prev_t + 1.6 <= ctx.t_out:
        js.append(_vg.tween("#%s-cur" % sid, {"x": _px(at[0]), "y": _px(at[1])},
                            {"x": _px(back[0]), "y": _px(back[1]), "duration": 0.6, "ease": "power3.inOut"}, prev_t + 1.0))
    pic = ('<div class="ed-pic" style="background:%s">%s%s</div>' % (pc["chrome"], _vg.picture(ctx, scene.get("src"), "p", seed=2), "".join(tints)))
    html = ('<div class="ed" id="%s-panel" style="height:%dpx;%s">%s<div class="ed-bar">%s</div>%s%s%s%s</div>'
            % (sid, height(scene, W), ctx.paper_card(), pic, "".join(slots), "".join(marks), loupe, "".join(drops), cursor))
    js.insert(0, ctx.enter("#%s-panel" % sid, ctx.t_in, {"y": 40, "scale": 0.96}))
    return html, js
