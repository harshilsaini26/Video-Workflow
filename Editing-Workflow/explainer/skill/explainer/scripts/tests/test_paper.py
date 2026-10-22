"""paper.py: the paper look's seeded texture (after ClaudeAnimationBase's makePaper, MIT): the same bytes every time,
at most 6% darker than the ground, and only on the base ground of the paper look."""
import copy, os, re, struct, unittest, zlib
from .helpers import SCRIPTS, read, run, scratch, write
from .test_compose import BOARD, VOICE, silent_wav, words30
import explainer_lib as E
import paper


def rgba(path):
    """(w, h, bytes) of an 8-bit RGBA PNG with no interlace (filter types 0 to 4)."""
    with open(path, "rb") as f:
        data = f.read()
    pos, idat = 8, b""
    while pos < len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8])
        if kind == b"IHDR":
            w, h = struct.unpack(">II", data[pos + 8:pos + 16])
        elif kind == b"IDAT":
            idat += data[pos + 8:pos + 8 + n]
        pos += 12 + n
    raw, out, stride = zlib.decompress(idat), bytearray(), w * 4
    prev = bytearray(stride)
    for y in range(h):
        ft, line = raw[y * (stride + 1)], bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a, b = line[i - 4] if i >= 4 else 0, prev[i]
            c = prev[i - 4] if i >= 4 else 0
            p = a + b - c
            pr = a if abs(p - a) <= abs(p - b) and abs(p - a) <= abs(p - c) else (b if abs(p - b) <= abs(p - c) else c)
            line[i] = (line[i] + (0, a, b, (a + b) // 2, pr)[ft]) & 255
        out += line
        prev = line
    return w, h, bytes(out)


def lum(r, g, b):
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


class Paper(unittest.TestCase):
    def test_same_bytes_every_time(self):
        d = scratch(self)
        a, b = paper.texture(os.path.join(d, "a.png")), paper.texture(os.path.join(d, "b.png"))
        with open(a, "rb") as fa, open(b, "rb") as fb:
            self.assertEqual(fa.read(), fb.read())
        with open(a, "rb") as fa, open(paper.SHIPPED, "rb") as fs:
            self.assertEqual(fa.read(), fs.read(), "assets/paper.png is stale: run paper.py")

    def test_darkening_is_at_most_six_percent(self):
        w, h, px = rgba(paper.SHIPPED)
        self.assertEqual((w, h), (540, 960))
        base = E.load_tokens(look="paper")["palette"]["base"]
        br, bg_, bb = (int(base[i:i + 2], 16) for i in (1, 3, 5))
        worst = 1.0
        for i in range(0, len(px), 4):
            al = px[i + 3] / 255.0
            if al:
                c = [px[i + k] * al + v * (1 - al) for k, v in enumerate((br, bg_, bb))]
                worst = min(worst, lum(*c) / lum(br, bg_, bb))
        self.assertGreaterEqual(worst, 0.94)
        self.assertLess(worst, 0.99)                                 # and it is there to see


class OnTheGround(unittest.TestCase):
    def page(self, look, grounds):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        b = copy.deepcopy(BOARD)
        b["look"] = look
        for sc, g in zip(b["scenes"], grounds):
            sc["bg"] = g
        r = run("explainer-compose.py", "--spec", write(os.path.join(d, "storyboard.json"), b), "--out", os.path.join(d, "public"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return read(os.path.join(d, "public", "index.html")), os.path.join(d, "public")

    def test_texture_only_on_base(self):
        html, out = self.page("paper", ["blue", "base", "ink"])
        bgs = re.findall(r'<div class="bg" id="bg\d+" style="([^"]*)"', html)
        self.assertEqual(len(bgs), 3)
        self.assertEqual(["paper.png" in s for s in bgs], [False, True, False])
        self.assertTrue(os.path.exists(os.path.join(out, "assets", "paper.png")))

    def test_latte_has_none(self):
        html, out = self.page("latte", ["mantle", "base", "ink"])
        self.assertNotIn("paper.png", html)
        self.assertFalse(os.path.exists(os.path.join(out, "assets", "paper.png")))
