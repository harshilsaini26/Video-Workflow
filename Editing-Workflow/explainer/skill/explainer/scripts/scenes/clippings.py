"""clippings: Vox's evidence desk. The argument is laid out as real material (a press clipping, a photo print, a
black label strip, an index card), tied together with red string, and marked up as the voice reads it: a highlighter
sweeps the line being quoted, a red pen circles a name, underlines a phrase.

  {"type": "clippings", "source": "le2012",
   "items": [{"kind": "clipping", "head": "A computer learns to see cats",
              "lines": ["1,000 machines, 16,000 cores", "Ten million video frames", "No labels at all"], "at": "word:5"},
             {"kind": "print", "src": "lab.png", "credit": "Photo: Google", "label": "The lab", "halftone": true, "at": "word:9"},
             {"kind": "label", "text": "2012 · Google", "at": "word:12"},
             {"kind": "note", "text": "Nobody told it what a cat is", "at": "word:14"}],
   "marks": [{"kind": "highlight", "item": 0, "line": 1, "at": "word:7"},
             {"kind": "circle", "item": 2, "at": "word:13"},
             {"kind": "underline", "item": 3, "at": "word:16"}],
   "strings": true}

Two frame rates, the grammar's core (huashu-art-motion y2_vox, MIT, measured on Vox's Missing Chapter): the camera
layer is smooth, the things on the desk move on twos, twelve steps a second (onTwos, steps()). Items slide in tilted
and settle; a label types at 13 characters a second; the highlighter is the line's own background, swept left to
right under the words (so the words stay on top and E5 reads them on it); the red circle is one stroke that does not
close, the underline a slightly wavering line; a red string with a pin at each end ties every item to the one before.
Paper is static (no per-frame grain), shadows are weak, and nothing pops or bounces: on a real desk things are just
there. A print is always the creator's photo, with its credit; `halftone` turns it to grey dots.
"""
import math, random
import explainer_lib as E
from scenes import need, line_px

TYPE = "clippings"
DECOR_KEYS = ("item", "line", "halftone", "strings")
KINDS = ("clipping", "print", "label", "note")
MARKS = ("highlight", "circle", "underline")
ITEM_W, GAP, PAD = 0.84, 36, 26
TILT = (-1.2, 1.0, -0.8, 1.3)
H_SIZE, H_LH = 52, 1.12              # the clipping's headline (the serif)
B_SIZE, B_LH = 34, 1.4               # its body lines
L_SIZE, L_PAD = 42, 14               # a label strip
N_SIZE, N_LH = 40, 1.35              # an index card's words
C_SIZE = 32                          # a print's credit (above 28, so the desk may be scaled to fit)
BORDER, IMG_MAX = 14, 230
TWOS = 12                            # steps a second for everything on the desk
TYPE_CPS = 13
SLIDE = 0.58
ON_TWOS = ("window.onTwos = function (n, k) { return function (t) { var q = Math.ceil(t * n - 1e-9) / n; "
           "return 1 - Math.pow(1 - q, k); }; };")

CSS = """
  .cl { position:relative; width:100%%; }
  .cl-item { position:absolute; opacity:0; }
  .cl-paper { padding:%dpx; }
  .cl-head { position:relative; font-size:%dpx; line-height:%dpx; margin-bottom:8px; }
  .cl-rule { position:relative; height:3px; margin-bottom:7px; }
  .cl-line { position:relative; display:inline-block; font-weight:500; font-size:%dpx; line-height:%dpx; white-space:nowrap; padding:0 4px; margin-left:-4px; }
  .cl-label { font-weight:700; font-size:%dpx; line-height:%dpx; padding:%dpx 26px; white-space:nowrap; }
  .cl-note { padding:%dpx %dpx %dpx 56px; font-size:%dpx; line-height:%dpx; }
  .cl-print img { display:block; }
  .cl-dots { position:absolute; mix-blend-mode:multiply; opacity:0.45; background-size:7px 7px; }
  .cl-tape { position:absolute; width:120px; height:32px; }
  .cl-credit { position:absolute; left:0; font-weight:500; font-size:%dpx; line-height:1.3; white-space:nowrap; }
  .cl-marks { position:absolute; left:0; top:0; overflow:visible; pointer-events:none; }
""" % (PAD, H_SIZE, line_px(H_SIZE, H_LH), B_SIZE, line_px(B_SIZE, B_LH), L_SIZE, line_px(L_SIZE, 1.2), L_PAD,
       PAD, PAD, PAD, N_SIZE, line_px(N_SIZE, N_LH), C_SIZE)


def validate(scene):
    errs = need(scene, ["items"])
    items = scene.get("items")
    if items is not None and (not isinstance(items, list) or not 1 <= len(items) <= 4):
        return errs + ["1 to 4 items"]
    for i, it in enumerate(items or []):
        if not isinstance(it, dict) or it.get("at") is None:
            errs.append("item %d needs its word (at)" % i)
            continue
        k = it.get("kind")
        if k not in KINDS:
            errs.append("item %d: kind is clipping, print, label or note (got %r)" % (i, k))
        elif k == "clipping":
            if not 0 < len(str(it.get("head") or "")) <= 60:
                errs.append("item %d: a clipping's head is 1 to 60 characters" % i)
            ls = it.get("lines")
            if not isinstance(ls, list) or not 1 <= len(ls) <= 4 or any(not 0 < len(str(x)) <= 40 for x in ls):
                errs.append("item %d: a clipping has 1 to 4 lines of 1 to 40 characters" % i)
        elif k == "print":
            if not it.get("src"):
                errs.append("item %d: a print is the creator's photo (src)" % i)
            if not 0 < len(str(it.get("credit") or "")) <= 40:
                errs.append("item %d: a print needs its credit (1 to 40 characters)" % i)
            if it.get("label") is not None and not 0 < len(str(it["label"])) <= 24:
                errs.append("item %d: a print's label is 1 to 24 characters" % i)
        elif k == "label" and not 0 < len(str(it.get("text") or "")) <= 24:
            errs.append("item %d: a label is 1 to 24 characters" % i)
        elif k == "note" and not 0 < len(str(it.get("text") or "")) <= 60:
            errs.append("item %d: a note is 1 to 60 characters" % i)
    for j, m in enumerate(scene.get("marks") or []):
        if not isinstance(m, dict) or m.get("at") is None or not isinstance(m.get("item"), int):
            errs.append("mark %d is {kind, item, at}" % j)
            continue
        if m.get("kind") not in MARKS:
            errs.append("mark %d: kind is highlight, circle or underline" % j)
            continue
        if not isinstance(items, list) or not 0 <= m["item"] < len(items):
            errs.append("mark %d: item is 0 to %d" % (j, len(items or [1]) - 1))
            continue
        it = items[m["item"]]
        lines = it.get("lines") if isinstance(it, dict) else None
        if m["kind"] == "highlight" and (not isinstance(it, dict) or it.get("kind") != "clipping"):
            errs.append("mark %d: a highlight marks a line of a clipping" % j)
        elif m["kind"] in ("highlight", "underline") and isinstance(it, dict) and it.get("kind") == "clipping":
            if not isinstance(m.get("line"), int) or not isinstance(lines, list) or not 0 <= m["line"] < len(lines):
                errs.append("mark %d: line is 0 to %d" % (j, len(lines or [1]) - 1))
        elif m["kind"] == "underline" and isinstance(it, dict) and it.get("kind") == "print":
            errs.append("mark %d: underline a clipping's line, a label or a note, not a print" % j)
    return errs


def _iw(width):
    return int(round(width * ITEM_W))


def _note_lines(text, iw):
    return E.text_lines(text, N_SIZE, iw - PAD - 56, "serif400i")


def _head_lines(text, iw):
    return E.text_lines(text, H_SIZE, iw - 2 * PAD, "serif400i")


def _print_size(it, iw, ctx=None):
    w, h = it.get("_size") or (4, 3)
    pw = iw * 0.7 - 2 * BORDER
    ph = pw * h / float(w)
    if ph > IMG_MAX:
        ph, pw = IMG_MAX, IMG_MAX * w / float(h)
    return pw, ph


def _item_h(it, iw):
    k = it["kind"]
    if k == "clipping":
        return 2 * PAD + _head_lines(it["head"], iw) * line_px(H_SIZE, H_LH) + 8 + 10 + len(it["lines"]) * line_px(B_SIZE, B_LH)
    if k == "label":
        return line_px(L_SIZE, 1.2) + 2 * L_PAD
    if k == "note":
        return 2 * PAD + _note_lines(it["text"], iw) * line_px(N_SIZE, N_LH)
    pw, ph = _print_size(it, iw)
    return int(math.ceil(ph)) + 2 * BORDER + 10 + line_px(C_SIZE, 1.3)


def height(scene, width):
    iw = _iw(width)
    return sum(_item_h(it, iw) for it in scene["items"]) + GAP * (len(scene["items"]) - 1) + 20


def min_width(scene):
    need_w = 600
    for it in scene["items"]:
        texts = [(t, B_SIZE, "display500", 2 * PAD + 8) for t in it.get("lines") or []]
        if it["kind"] == "label":
            texts.append((it["text"], L_SIZE, "display700", 52))
        for t, size, font, pad in texts:
            need_w = max(need_w, int(math.ceil((E.text_width(str(t), size, font) + pad) / ITEM_W)))
    return need_w


def min_text(scene):
    return C_SIZE if any(it["kind"] == "print" for it in scene["items"]) else B_SIZE


def _torn(w, h, seed):
    """A clip-path polygon that tears the card's top and bottom edges (up to 7 px in), seeded: the paper itself is torn,
    so the words sit straight on it with nothing between."""
    rng = random.Random(seed)
    top = ["%.1fpx %.1fpx" % (x, rng.uniform(0, 7)) for x in range(0, int(w) + 1, 14)]
    bottom = ["%.1fpx %.1fpx" % (x, h - rng.uniform(0, 7)) for x in range(int(w), -1, -14)]
    return "clip-path:polygon(%s)" % ", ".join(top + bottom)


def _hand(points, seed, amp=2.4):
    rng = random.Random(seed)
    return "M" + " L".join("%.1f,%.1f" % (x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)) for x, y in points)


def _length(points):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:]))


def _draw(sel, length, dur, t):
    n = max(2, int(round(dur * TWOS)))
    return ("tl.fromTo('%s', { strokeDashoffset: %.1f }, { strokeDashoffset: 0, duration: %s, ease: 'steps(%d)', immediateRender: false }, %.3f);"
            % (sel, length, dur, n, t))


def render(scene, ctx, box):
    c, pc, sid = ctx.c, ctx.pc, ctx.id
    Wd = box[2]
    iw = _iw(Wd)
    red, ink, paper = pc["bad"], pc["paper_ink"], pc["paper"]
    items = scene["items"]
    for it in items:
        if it["kind"] == "print":
            page, w, h = ctx.image(it["src"])
            it["_page"], it["_size"] = page, (w, h)
    js = [ON_TWOS]
    lift = lambda a: "3px 6px 10px %s" % E.rgba(ink, a)      # a weak shadow in the paper's own ink: things lie flat on the desk
    html, marks_svg, rects, times = [], [], [], []
    y = 10
    for i, it in enumerate(items):
        k = it["kind"]
        h = _item_h(it, iw)
        t, attrs = ctx.item(it["at"])
        times.append(t)
        tilt = TILT[i % len(TILT)]
        if k == "label":
            w = int(math.ceil(E.text_width(it["text"], L_SIZE, "display700"))) + 52
        elif k == "print":
            pw, ph = _print_size(it, iw)
            w = int(math.ceil(pw)) + 2 * BORDER
        else:
            w = iw
        left = (Wd - w) / 2.0 + (0.03 * Wd if i % 2 else -0.03 * Wd)
        rects.append((left, y, w, h, tilt))
        style = "left:%.1fpx;top:%dpx;width:%dpx;transform:rotate(%.1fdeg)" % (left, y, w, tilt)
        if k == "clipping":
            lines = []
            for j, ln in enumerate(it["lines"]):
                hid = next((mi for mi, m in enumerate(scene.get("marks") or []) if m["kind"] == "highlight" and m["item"] == i and m["line"] == j), None)
                hl = (' id="%s-h%d" style="background:linear-gradient(%s, %s) no-repeat;background-size:0%% 100%%"' % (sid, hid, pc["marker"], pc["marker"])
                      if hid is not None else "")
                lines.append('<div><span class="cl-line"%s>%s</span></div>' % (hl, ctx.esc(ln)))
            html.append('<div class="cl-item cl-clipping" id="%s-i%d" style="%s;height:%dpx;filter:drop-shadow(%s)"%s><div class="cl-paper" data-torn="1" style="height:%dpx;'
                        'background:%s;color:%s;%s"><div class="cl-head" style="%s">%s</div><div class="cl-rule" style="background:%s"></div>%s</div></div>'
                        % (sid, i, style, h, lift(0.22), attrs, h, paper, ink, _torn(w, h, 31 + i), E.aside()["css"], ctx.esc(it["head"]), ink, "".join(lines)))
        elif k == "label":
            html.append('<div class="cl-item cl-label" id="%s-i%d" style="%s;background:%s;color:%s;box-shadow:%s"%s><span id="%s-t%d" style="display:inline-block">%s</span></div>'
                        % (sid, i, style, ink, paper, lift(0.25), attrs, sid, i, ctx.esc(it["text"])))
            n = len(it["text"])
            js.append("tl.fromTo('#%s-t%d', { clipPath: 'inset(0 100%% 0 0)' }, { clipPath: 'inset(0 0%% 0 0)', duration: %s, ease: 'steps(%d)', "
                      "immediateRender: false }, %.3f);" % (sid, i, round(n / float(TYPE_CPS), 2), n, t + 0.2))
        elif k == "note":
            lp = line_px(N_SIZE, N_LH)              # ruled lines one text line apart, a red margin, like an index card
            rules = ("background-color:%s;background-image:repeating-linear-gradient(to bottom, transparent 0, transparent %dpx, %s %dpx, %s %dpx);"
                     "background-position:0 %dpx" % (pc["card"], lp - 2, pc["accent_soft"], lp - 2, pc["accent_soft"], lp, PAD - 4))
            html.append('<div class="cl-item cl-note" id="%s-i%d" style="%s;height:%dpx;%s;color:%s;box-shadow:%s;%s"%s>'
                        '<i style="position:absolute;left:40px;top:0;width:3px;height:100%%;background:%s"></i>%s</div>'
                        % (sid, i, style, h, rules, ink, lift(0.2), E.aside()["css"], attrs, E.rgba(red, 0.6), ctx.esc(it["text"])))
        else:
            pw, ph = _print_size(it, iw)
            dots = ('<div class="cl-dots" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;background-image:radial-gradient(circle, %s 1.6px, transparent 2px)"></div>'
                    % (BORDER, BORDER, pw, ph, ink)) if it.get("halftone") else ""
            filt = ";filter:grayscale(1) contrast(1.25)" if it.get("halftone") else ""
            tape = E.rgba(pc["paper_chrome"], 0.7)
            label = ""
            if it.get("label"):
                label = ('<div class="cl-label" style="position:absolute;left:-14px;top:%dpx;background:%s;color:%s;transform:rotate(-1.5deg)">%s</div>'
                         % (int(ph + 2 * BORDER - line_px(L_SIZE, 1.2) - 2 * L_PAD - 10), ink, paper, ctx.esc(it["label"])))
            html.append('<div class="cl-item cl-print" id="%s-i%d" style="%s;height:%dpx"%s>'
                        '<div style="position:relative;background:%s;padding:%dpx;box-shadow:%s">'
                        '<img src="%s" alt="" style="width:%dpx;height:%dpx%s">%s</div>'
                        '<i class="cl-tape" style="left:-30px;top:-8px;background:%s;transform:rotate(-35deg)"></i>'
                        '<i class="cl-tape" style="right:-30px;top:-8px;background:%s;transform:rotate(35deg)"></i>%s'
                        '<div class="cl-credit" style="top:%dpx;color:%s">%s</div></div>'
                        % (sid, i, style, h, attrs, paper, BORDER, lift(0.25), it["_page"], pw, ph, filt, dots, tape, tape, label,
                           int(ph + 2 * BORDER + 10), c["dim"], ctx.esc(it["credit"])))
        js.append("tl.fromTo('#%s-i%d', { opacity: 0, x: 140, rotation: %s }, { opacity: 1, x: 0, rotation: %s, duration: %s, ease: onTwos(%d, 4), "
                  "immediateRender: false }, %.3f);" % (sid, i, round(tilt + 10, 1), tilt, SLIDE, int(round(SLIDE * TWOS)), t))
        y += h + GAP
    H = height(scene, Wd)
    if scene.get("strings", True):
        for i in range(1, len(items)):
            (l0, y0, w0, h0, _), (l1, y1, w1, h1, _) = rects[i - 1], rects[i]
            a, b = (l0 + w0 * 0.7, y0 + h0 - 4), (l1 + w1 * 0.3, y1 + 4)     # pinned at the paper's edge, clear of its words
            ctl = ((a[0] + b[0]) / 2 + 70, (a[1] + b[1]) / 2 + 20)
            pts = [((1 - u) ** 2 * a[0] + 2 * (1 - u) * u * ctl[0] + u * u * b[0], (1 - u) ** 2 * a[1] + 2 * (1 - u) * u * ctl[1] + u * u * b[1])
                   for u in (k / 20.0 for k in range(21))]
            L = _length(pts)
            marks_svg.append('<path class="cl-string" id="%s-s%d" d="%s" fill="none" stroke="%s" stroke-width="4" stroke-linecap="round" '
                             'stroke-dasharray="%.1f" stroke-dashoffset="%.1f"/>' % (sid, i, _hand(pts, 50 + i, 0.6), red, L, L))
            for p_, kk in ((a, 0), (b, 1)):
                marks_svg.append('<circle class="cl-pin" id="%s-pin%d-%d" cx="%.1f" cy="%.1f" r="8" fill="%s" opacity="0"/>' % (sid, i, kk, p_[0], p_[1], red))
            t0 = max(ctx.t_in, times[i] - 0.45)
            js.append("tl.set('#%s-pin%d-0', { opacity: 1 }, %.3f);" % (sid, i, t0))
            js.append(_draw("#%s-s%d" % (sid, i), L, 0.42, t0))
            js.append("tl.set('#%s-pin%d-1', { opacity: 1 }, %.3f);" % (sid, i, t0 + 0.42))
    for mi, m in enumerate(scene.get("marks") or []):
        t, attrs = ctx.item(m["at"])
        it, (left, top, w, h, tilt) = items[m["item"]], rects[m["item"]]
        if t < times[m["item"]] + 0.3:
            ctx.fail("mark %d lands at %.2f s, before its item lands (%.2f s): anchor it on a later word" % (mi, t, times[m["item"]]))
        html.append("<i%s></i>" % attrs)
        if m["kind"] == "highlight":
            js.append("tl.fromTo('#%s-h%d', { backgroundSize: '0%% 100%%' }, { backgroundSize: '100%% 100%%', duration: 0.75, ease: 'steps(9)', "
                      "immediateRender: false }, %.3f);" % (sid, mi, t))
            continue
        if it["kind"] == "clipping" and m["kind"] == "underline":    # the line's box inside the card (a circle rings the whole item)
            ly = top + PAD + _head_lines(it["head"], iw) * line_px(H_SIZE, H_LH) + 18 + m.get("line", 0) * line_px(B_SIZE, B_LH)
            lw = E.text_width(it["lines"][m.get("line", 0)], B_SIZE, "display500")
            tx, ty, tw, th = left + PAD, ly, lw, line_px(B_SIZE, B_LH)
        else:
            tx, ty, tw, th = left, top, w, h
        if m["kind"] == "underline":
            if it["kind"] == "note":
                tx, tw = left + 56, min(w - 56 - PAD, E.text_width(it["text"], N_SIZE, "serif400i"))
                ty, th = top + PAD, _note_lines(it["text"], iw) * line_px(N_SIZE, N_LH)
            pts = [(tx + tw * u / 12.0, ty + th + 4 + 3 * math.sin(u * 1.3)) for u in range(13)]
        else:
            cx, cy, rx, ry = tx + tw / 2.0, ty + th / 2.0, tw / 2.0 + 30, th / 2.0 + 24
            pts = [(cx + rx * math.cos(-2.6 + 2 * math.pi * 1.08 * u / 44.0), cy + ry * math.sin(-2.6 + 2 * math.pi * 1.08 * u / 44.0)) for u in range(45)]
        L = _length(pts)
        dur = 0.5 if m["kind"] == "underline" else 0.65
        marks_svg.append('<path class="cl-mark" id="%s-m%d" d="%s" fill="none" stroke="%s" stroke-width="6" stroke-linecap="round" '
                         'stroke-linejoin="round" stroke-dasharray="%.1f" stroke-dashoffset="%.1f"/>' % (sid, mi, _hand(pts, 70 + mi), red, L + 20, L + 20))
        js.append(_draw("#%s-m%d" % (sid, mi), L + 20, dur, t))
    out = ('<div class="cl" id="%s-cl" style="height:%dpx">%s<svg class="cl-marks" width="%d" height="%d">%s</svg></div>'
           % (sid, H, "".join(html), Wd, H, "".join(marks_svg)))
    return out, js
