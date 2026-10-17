"""Shared pieces of the video and grade scenes (grade-slider, eyedropper-grade, film-look, playing-grid, video-card,
reel-feed): the picture (the creator's own PNG or JPG, or a built-in illustration drawn from the Latte palette), a few
player glyphs drawn inline, and the timeline lines for a timecode or a count that runs while a scene holds.

Not a scene (no TYPE, and the leading _ keeps discovery away from it).
"""
import math, re

from scenes import js_obj

PIC_RE = re.compile(r"\.(png|jpe?g)$", re.I)

# Lucide (ISC, lucide.dev) path data, drawn inline so the scenes need no icon files: 24 x 24, stroked in currentColor
GLYPHS = {
    "play": '<polygon points="6 3 20 12 6 21 6 3"/>',
    "pause": '<rect x="14" y="4" width="4" height="16" rx="1"/><rect x="6" y="4" width="4" height="16" rx="1"/>',
    "heart": '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 '
             '8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>',
    "comment": '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
    "send": '<path d="M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 '
            '3.18a2 2 0 0 1 1.112 1.11z"/><path d="m21.854 2.147-10.94 10.939"/>',
    "pipette": '<path d="m2 22 1-1h3l9-9"/><path d="M3 21v-3l9-9"/><path d="m15 6 3.4-3.4a2.1 2.1 0 1 1 3 3L18 9l.4.4a2.1 2.1 0 1 '
               '1-3 3l-3.8-3.8a2.1 2.1 0 1 1 3-3l.4.4Z"/>',
}


def glyph(name, cls="", fill=False, width=2):
    """A player glyph as inline SVG, in currentColor (filled for play and pause, so they read at a glance)."""
    paint = 'fill="currentColor" stroke="currentColor"' if fill else 'fill="none" stroke="currentColor"'
    return ('<svg class="%s" viewBox="0 0 24 24" %s stroke-width="%s" stroke-linecap="round" stroke-linejoin="round">%s</svg>'
            % (cls, paint, width, GLYPHS[name]))


def check_src(value, what="src"):
    """An error for a picture path that is not a PNG or JPG, or None."""
    if value is None:
        return None
    if not isinstance(value, str) or not PIC_RE.search(value):
        return "%s is a PNG or JPG next to storyboard.json (got %r)" % (what, value)
    return None


# the built-in pictures: a landscape in Latte colours, one look per seed (sky top, sky bottom, sun, far, mid, near, ground)
LOOKS = [
    ("lavender", "peach", "yellow", "mauve", "blue", "teal", "green"),       # dusk
    ("sapphire", "base", "yellow", "lavender", "blue", "teal", "green"),     # day
    ("mauve", "peach", "yellow", "pink", "maroon", "mauve", "flamingo"),     # sunset
    ("blue", "lavender", "base", "lavender", "mauve", "blue", "text"),       # night
    ("sky", "base", "peach", "teal", "green", "green", "yellow"),            # meadow
]


def _ridge(seed, base, amp, n, phase):
    """A mountain ridge across 0..400 as a polygon's points: n peaks, their heights and spacing from the seed."""
    pts = ["0,300", "0,%d" % base]
    for k in range(n * 2 + 1):
        x = 400.0 * k / (n * 2)
        up = k % 2 == 1
        jitter = ((seed * 37 + k * 53 + phase * 11) % 29) / 29.0
        y = base - (amp * (0.6 + 0.4 * jitter) if up else amp * 0.15 * jitter)
        pts.append("%.1f,%.1f" % (x, y))
    pts += ["400,%d" % base, "400,300"]
    return " ".join(pts)


def illustration(ctx, key, seed=0):
    """The built-in picture: an SVG landscape in Latte colours that fills its box (slice), the same on every render."""
    p = ctx.tokens["palette"]
    sky0, sky1, sun, far, mid, near, ground = (p[c] for c in LOOKS[seed % len(LOOKS)])
    gid = "%s-%s-sky" % (ctx.id, key)
    sx = 90 + (seed * 71) % 220
    sy = 92 + (seed * 23) % 40
    hill = "M0 236 C 80 %d, 150 %d, 230 238 S 360 %d, 400 228 L 400 300 L 0 300 Z" % (206 - seed % 3 * 8, 214, 216 + seed % 4 * 6)
    return ('<svg class="vg-ill" viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice">'
            '<defs><linearGradient id="%s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s"/>'
            '<stop offset="1" stop-color="%s"/></linearGradient></defs>'
            '<rect width="400" height="300" fill="url(#%s)"/>'
            '<circle cx="%d" cy="%d" r="64" fill="%s" fill-opacity="0.25"/><circle cx="%d" cy="%d" r="34" fill="%s"/>'
            '<polygon points="%s" fill="%s" fill-opacity="0.75"/>'
            '<polygon points="%s" fill="%s"/>'
            '<path d="%s" fill="%s"/>'
            '<rect y="262" width="400" height="38" fill="%s"/>'
            '</svg>' % (gid, sky0, sky1, gid, sx, sy, sun, sx, sy, sun,
                        _ridge(seed, 200, 92, 3, 1), far, _ridge(seed + 1, 228, 70, 4, 2), mid, hill, near, ground))


def picture(ctx, src, key, seed=0, pos="50% 50%"):
    """What fills a picture box: the creator's own image (staged next to the page, cropped to the box) or the built-in
    illustration."""
    if src:
        rel, _ = ctx.asset(src)
        return '<img class="vg-img" src="%s" alt="" style="object-position:%s" />' % (ctx.esc(rel), pos)
    return illustration(ctx, key, seed)


CSS = """
  .vg-img, .vg-ill { position:absolute; left:0; top:0; width:100%; height:100%; display:block; }
  .vg-img { object-fit:cover; }
"""


def ticker(el_id, t, dur, v0, v1, fmt_js, ease="none"):
    """A timeline line that runs a number from v0 to v1 over [t, t + dur], writing fmt_js(v) into #el_id as it goes
    (a timecode, a like count): deterministic, on the timeline, seekable."""
    return ("tl.fromTo({ v: %s }, { v: %s }, { v: %s, duration: %.3f, ease: '%s', immediateRender: false, onUpdate: function () "
            "{ var v = this.targets()[0].v; document.getElementById('%s').textContent = %s; } }, %.3f);"
            % (_num(v0), _num(v0), _num(v1), dur, ease, el_id, fmt_js, t))


def _num(v):
    return ("%.3f" % v).rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


CLOCK_JS = ("(v >= 3600 ? Math.floor(v / 3600) + ':' + ('0' + Math.floor(v % 3600 / 60)).slice(-2) : Math.floor(v / 60)) + ':' + "
            "('0' + Math.floor(v % 60)).slice(-2)")
COUNT_JS = ("(v >= 1e6 ? (v / 1e6).toFixed(1) + 'M' : v >= 1e4 ? (v / 1e3).toFixed(1) + 'K' : "
            "Math.round(v).toLocaleString('en-US'))")


def clock(sec):
    """m:ss (h:mm:ss from an hour), as CLOCK_JS writes it."""
    sec = int(math.floor(sec))
    if sec >= 3600:
        return "%d:%02d:%02d" % (sec // 3600, sec % 3600 // 60, sec % 60)
    return "%d:%02d" % (sec // 60, sec % 60)


def count(v):
    """12.4K, 1.2M, 318 or 1,204: as COUNT_JS writes it."""
    if v >= 1e6:
        return "%.1fM" % (v / 1e6)
    if v >= 1e4:
        return "%.1fK" % (v / 1e3)
    return "{:,}".format(int(round(v)))


def parse_clock(s):
    """Seconds from "m:ss" (or "h:mm:ss"), or None."""
    m = re.match(r"^(\d+):([0-5]\d)(?::([0-5]\d))?$", str(s or ""))
    if not m:
        return None
    a, b, c = m.groups()
    return int(a) * 3600 + int(b) * 60 + int(c) if c is not None else int(a) * 60 + int(b)


def tween(sel, frm, to, t):
    """An explicit fromTo that waits for its time (immediateRender: false)."""
    to = dict(to, immediateRender=False)
    return "tl.fromTo('%s', %s, %s, %.3f);" % (sel, js_obj(frm), js_obj(to), t)
