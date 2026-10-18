"""The wave shared by waveform and mode-switch: one SVG path of POINTS points that scrolls left for a scene's whole life
and changes its shape on words, deterministic and seek-safe.

A plain object (the proxy) holds the phase `p` (in samples), the amplitude `a` and one weight per kind (w0..w4). GSAP
tweens the proxy on the timeline; every tween's onUpdate redraws the path's d from the proxy, so whatever time the
timeline is seeked to, the picture is the one for that time. The noise is a table Python writes into the page from a
seed (the scene id's CRC), never the browser's dice or clock: every render draws the same wave.

  KINDS     noise (jagged static), calm (a slow swell), music (a busy wave that beats), pulse (a heartbeat spike),
            flat (a faint ripple: still moving, so the picture is never still)

Not a scene (no TYPE, and the leading _ keeps discovery away from it).
"""
import zlib

from scenes import js_obj

KINDS = ("noise", "calm", "music", "pulse", "flat")
POINTS = 200          # points on the path
TABLE = 256           # seeded noise values, in -1..1
SPEED = 40            # samples the wave scrolls a second (a pulse every 1.25 s)
MORPH = 0.6           # seconds a change of shape takes
WAIT = 0.3            # the amplitude before the first word: the first shape, quiet, already moving
STROKE = 6

# each kind as a JS expression of u (the sample under point i, phase included), nz(x) (the noise table, interpolated)
# and k (u's place in a 50-sample period, 0..1); all stay inside -1..1
SHAPES = {
    "noise": "nz(u)",
    "calm": "0.62 * Math.sin(u * 0.1257) + 0.16 * Math.sin(u * 0.273)",
    "music": "(0.35 + 0.65 * Math.abs(Math.sin(u * 0.0698))) * (0.6 * Math.sin(u * 0.698) + 0.4 * Math.sin(u * 1.185))",
    "pulse": "Math.exp(-((k - 0.5) * (k - 0.5)) / 0.0009) - 0.4 * Math.exp(-((k - 0.56) * (k - 0.56)) / 0.0009) + 0.04 * nz(u * 0.5)",
    "flat": "0.05 * nz(u * 0.25)",
}


def seed_of(key):
    return zlib.crc32(str(key).encode("utf-8")) & 0x7FFFFFFF


def table(seed, n=TABLE):
    """n values in -1..1 from a linear congruential generator: the same seed, the same values, on every machine."""
    s, out = (seed or 1) & 0x7FFFFFFF, []
    for _ in range(n):
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        out.append(round(s / float(0x7FFFFFFF) * 2 - 1, 3))
    return out


def weights(kind):
    return {"w%d" % i: (1 if k == kind else 0) for i, k in enumerate(KINDS)}


def svg(path_id, width, height, stroke, cls=""):
    """The plot: a flat line at the middle until the first draw (which runs as soon as the page's script does)."""
    mid = height / 2.0
    return ('<svg class="%s" width="%d" height="%d" viewBox="0 0 %d %d"><path id="%s" d="M0 %s L%d %s" fill="none" stroke="%s" '
            'stroke-width="%d" stroke-linecap="round" stroke-linejoin="round"/></svg>'
            % (cls, width, height, width, height, path_id, _n(mid), width, _n(mid), stroke, STROKE))


def _n(v):
    return ("%.1f" % v).rstrip("0").rstrip(".")


class Wave:
    """One scene's wave: Wave(ctx, path_id, width, height, first_kind). setup() is its proxy and draw function,
    scroll() the scene-long linear phase (ambient), to(kind, t) a change of shape on a word."""

    def __init__(self, ctx, path_id, width, height, kind):
        self.ctx, self.path_id, self.width, self.height = ctx, path_id, int(width), int(height)
        self.v = "%s_wv" % ctx.id
        self.state = dict({"a": WAIT}, **weights(kind))

    def setup(self):
        v, m = self.v, STROKE / 2.0 + 2
        mix = " + ".join("o.w%d * (%s)" % (i, SHAPES[k]) for i, k in enumerate(KINDS))
        return [
            "const %s_T = [%s];" % (v, ", ".join(("%.3f" % x).rstrip("0").rstrip(".") if x else "0" for x in table(seed_of(self.ctx.id)))),
            "const %s = %s;" % (v, js_obj(dict({"p": 0}, **self.state))),
            "const %s_draw = function () { const T = %s_T, L = T.length, o = %s, out = []; "
            "const nz = function (x) { const i = Math.floor(x), f = x - i, a = T[((i %% L) + L) %% L], b = T[(((i + 1) %% L) + L) %% L]; "
            "return a + (b - a) * f; }; "
            "for (let i = 0; i < %d; i++) { const u = i + o.p, k = (((u %% 50) + 50) %% 50) / 50; const v = %s; "
            "const env = 0.15 + 0.85 * Math.sin(Math.PI * i / %d); "
            "const y = Math.max(%s, Math.min(%s, %s - v * env * o.a * %s)); "
            "out.push((i ? 'L' : 'M') + (i * %s).toFixed(1) + ' ' + y.toFixed(1)); } "
            "document.getElementById('%s').setAttribute('d', out.join(' ')); };"
            % (v, v, v, POINTS, mix, POINTS - 1, _n(m), _n(self.height - m), _n(self.height / 2.0), _n(self.height / 2.0 - m),
               repr(round(self.width / float(POINTS - 1), 4)), self.path_id),
            "%s_draw();" % v,
        ]

    def scroll(self, t0, t1):
        """The phase over [t0, t1], linear: the wave never stops travelling while its scene is on."""
        dur = round(t1 - t0, 3)
        return ("tl.fromTo(%s, { p: 0 }, { p: %s, duration: %.3f, ease: 'none', immediateRender: false, onUpdate: %s_draw }, %.3f);"
                % (self.v, _n(SPEED * dur), dur, self.v, t0))

    def to(self, kind, t, amp=1):
        """Its shape (and amplitude) eased to `kind` from wherever the last change left it, on t."""
        new = dict({"a": amp}, **weights(kind))
        mine = "w%d" % KINDS.index(kind)     # the arriving kind is always named, so each change reads as its shape
        frm = {k: self.state[k] for k in new if self.state[k] != new[k] or k == mine}
        to = {k: new[k] for k in frm}
        self.state = new
        return ("tl.fromTo(%s, %s, %s, %.3f);" % (self.v, js_obj(frm), js_obj(to)[:-2] + ", duration: %s, ease: 'power3.inOut', "
                "immediateRender: false, onUpdate: %s_draw }" % (_n(MORPH), self.v), t))
