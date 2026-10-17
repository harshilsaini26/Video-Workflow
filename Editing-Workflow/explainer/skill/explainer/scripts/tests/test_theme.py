"""The look is Catppuccin Latte (catppuccin/palette, palette.json), designed with Apple's HIG: semantic roles resolved per
background, each pair at its WCAG ratio (accessibility.md: 4.5:1 for text up to 17 pt, 3:1 for large or bold text),
one colour meaning one thing, and nothing on a page outside the palette (a brand's own logo colour aside)."""
import importlib.util, os, re, unittest
from .helpers import SCRIPTS, read, scratch, write
from .test_assets import COURSERA, png
from .test_scenes_ui import SVG, stub_vendor
import explainer_lib as E

TOK = E.load_tokens()
LATTE = {"rosewater": "#dc8a78", "flamingo": "#dd7878", "pink": "#ea76cb", "mauve": "#8839ef", "red": "#d20f39",
         "maroon": "#e64553", "peach": "#fe640b", "yellow": "#df8e1d", "green": "#40a02b", "teal": "#179299",
         "sky": "#04a5e5", "sapphire": "#209fb5", "blue": "#1e66f5", "lavender": "#7287fd", "text": "#4c4f69",
         "subtext1": "#5c5f77", "subtext0": "#6c6f85", "overlay2": "#7c7f93", "overlay1": "#8c8fa1", "overlay0": "#9ca0b0",
         "surface2": "#acb0be", "surface1": "#bcc0cc", "surface0": "#ccd0da", "base": "#eff1f5", "mantle": "#e6e9ef",
         "crust": "#dce0e8"}
RGB = {tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in LATTE.values()}


def lum(h):
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def flat(css, under):
    """A card colour as seen: rgba(...) over the background, as #rrggbb."""
    m = re.match(r"rgba\((\d+),(\d+),(\d+),([\d.]+)\)", css.replace(" ", ""))
    if not m:
        return css
    a = float(m.group(4))
    u = [int(under[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join("%02x" % int(round(int(m.group(k + 1)) * a + u[k] * (1 - a))) for k in range(3))


def make_cases():
    spec = importlib.util.spec_from_file_location("make_cases", os.path.join(SCRIPTS, "dev", "make-cases.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Theme(unittest.TestCase):
    def test_the_palette_is_latte(self):
        self.assertEqual({k: v.lower() for k, v in TOK["palette"].items()}, LATTE)

    def test_backgrounds_are_latte_surfaces_plus_blue_and_ink(self):
        # the reference changes between light, strong blue and dark grounds from scene to scene; all four are Latte
        self.assertEqual(set(TOK["backgrounds"]), {"mantle", "base", "blue", "ink"})
        for name, fill in (("mantle", "mantle"), ("base", "base"), ("blue", "blue"), ("ink", "text")):
            self.assertEqual(E.theme(TOK, name)["bg"].lower(), LATTE[fill])

    def test_ui_mockups_keep_light_paper_on_any_background(self):
        for name in TOK["backgrounds"]:
            c = E.theme(TOK, name)
            self.assertEqual((c["paper"].lower(), c["paper_ink"].lower()), (LATTE["base"], LATTE["text"]), name)
            self.assertGreaterEqual(ratio(c["paper_dim"], c["paper"]), 3.0)

    def test_every_role_meets_its_contrast(self):
        for name in TOK["backgrounds"]:
            c = E.theme(TOK, name)
            body = 4.5 if name in ("mantle", "base") else 3.0     # every text is 28 px or more: WCAG's large-text 3:1
            for surface in (c["bg"], flat(c["card"], c["bg"])):
                self.assertGreaterEqual(ratio(c["ink"], surface), body, name)         # body text
                for role in ("dim", "muted", "accent"):                              # only ever 30 px or larger, or bold
                    self.assertGreaterEqual(ratio(c[role], surface), 3.0, (name, role))
            self.assertNotEqual(c["accent"].lower(), c["bg"].lower(), name)     # the accent shows on its own ground
            self.assertGreaterEqual(ratio(c["on_accent"], c["accent"]), 3.0, name)
            for fill, on in c["series"]:
                self.assertGreaterEqual(ratio(on, fill), 3.0, (name, fill))
            hl = c["highlight"]
            self.assertGreaterEqual(ratio(hl["text"], hl["fill"]), 3.0, name)

    def test_text_reads_over_the_glows_at_their_brightest(self):
        # the glows sit behind the scenes, the captions and the handle band; the probe sees only the flat ground, so the
        # tokens hold every text role at 3:1 over each glow's centre on its ground (the worst place text can sit)
        for name in TOK["backgrounds"]:
            c = E.theme(TOK, name)
            for g in TOK["ambient"]["glows"][name]:
                under = flat(E.rgba(TOK["palette"][g["color"]], g["alpha"]), c["bg"])
                for role in ("ink", "dim", "muted", "accent"):
                    self.assertGreaterEqual(ratio(c[role], under), 3.0, (name, g["color"], g["alpha"], role))
                hl = c["highlight"]
                self.assertGreaterEqual(ratio(hl["fill"], under), 1.5, (name, g["color"], "the caption chip shows"))

    def test_one_colour_means_one_thing(self):
        c = E.theme(TOK, "mantle")
        self.assertEqual(c["accent"].lower(), LATTE["blue"])
        signals = {c["good"].lower(), c["bad"].lower(), c["warn"].lower()}
        self.assertEqual(len(signals), 3)
        self.assertNotIn(c["accent"].lower(), signals)

    def test_every_colour_on_every_scene_is_latte(self):
        mc = make_cases()
        root = scratch(self)
        vendor = stub_vendor(root, icons=("book", "clock", "calculator", "send", "file-text"))
        write(os.path.join(vendor, "simple-icons", "icons", "coursera.svg"), COURSERA)
        write(os.path.join(vendor, "simple-icons", "icons", "github.svg"), COURSERA.replace("Coursera", "GitHub"))
        write(os.path.join(vendor, "simple-icons", "_data", "simple-icons.json"),
              {"icons": [{"title": "Coursera", "hex": "0056D2"}, {"title": "GitHub", "hex": "181717"}]})
        bgs = ["mantle", "blue", "base", "ink"]
        for k, (typ, variants) in enumerate(sorted(mc.CASES.items())):
            for j, (name, data) in enumerate(variants):
                d = os.path.join(root, "%s-%s" % (typ, name))
                for key in ("screenshot", "src"):
                    if data.get(key):
                        png(os.path.join(d, data[key]), 1280, 2400 if key == "screenshot" else 256)
                html = self.compose(d, dict({"type": typ, "id": "sc", "bg": bgs[(k + j) % 4], "in": "word:1", "out": 16.0}, **data), vendor)
                page = re.sub(r'<div class="lc-mark">.*?</div>', "", html, flags=re.S)   # a brand's own mark, in its own colour
                for h in re.findall(r"#[0-9A-Fa-f]{6}\b", page):
                    self.assertIn(h.lower(), LATTE.values(), "%s-%s: %s" % (typ, name, h))
                for rgb in re.findall(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", page):
                    self.assertIn(tuple(map(int, rgb)), RGB, "%s-%s: rgb%s" % (typ, name, rgb))

    def compose(self, d, scene, vendor):
        from .helpers import run
        from .test_compose import silent_wav
        write(os.path.join(d, "transcript.json"), {"words": [{"text": "word%d" % i, "start": 0.5 + i * 0.4, "end": 0.8 + i * 0.4}
                                                              for i in range(40)]})
        silent_wav(os.path.join(d, "voice.wav"), 15.5)
        sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "scenes": [make_cases().LEAD_IN, scene], "sound": {"music": "none", "sfx": False}})
        r = run("explainer-compose.py", "--spec", sp, "--out", os.path.join(d, "public"), "--vendor", vendor)
        self.assertEqual(r.returncode, 0, "%s: %s" % (scene["type"], r.stdout + r.stderr))
        return read(os.path.join(d, "public", "index.html"))


if __name__ == "__main__":
    unittest.main()
