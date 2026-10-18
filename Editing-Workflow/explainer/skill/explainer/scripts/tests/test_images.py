"""Images and annotations (the editorial pass): a creator's image is sized from its own header (PNG, JPEG, WebP, GIF;
no PIL), copied next to the page, and can carry notes that draw on over it: a circle, a leader line, a pill label."""
import os, re, struct, unittest, zlib
from .helpers import scratch, write
from .test_compose import t_word, words30
import explainer_lib as E

TOK = E.load_tokens()


def png_bytes(w, h):
    raw = b"".join(b"\x00" + b"\x80\x80\x80\xff" * w for _ in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def jpeg_bytes(w, h):
    # SOI, an APP0 segment, then SOF0 with the size (enough for a header reader)
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    sof0 = b"\xff\xc0" + struct.pack(">HBHHB", 11, 8, h, w, 1) + b"\x01\x11\x00"
    return b"\xff\xd8" + app0 + sof0 + b"\xff\xd9"


def exif_jpeg_bytes(w, h, orientation, order=b"MM"):
    # a phone photo: stored w x h, with an EXIF orientation tag (6 and 8: turned a quarter, so shown h x w)
    pk = (lambda f, *v: struct.pack(">" + f, *v)) if order == b"MM" else (lambda f, *v: struct.pack("<" + f, *v))
    tiff = order + pk("H", 42) + pk("I", 8) + pk("H", 1) + pk("HHI", 0x0112, 3, 1) + pk("H", orientation) + b"\x00\x00" + pk("I", 0)
    app1 = b"\xff\xe1" + struct.pack(">H", 2 + 6 + len(tiff)) + b"Exif\x00\x00" + tiff
    sof0 = b"\xff\xc0" + struct.pack(">HBHHB", 11, 8, h, w, 1) + b"\x01\x11\x00"
    return b"\xff\xd8" + app1 + sof0 + b"\xff\xd9"


def rgb_png_bytes(w, h):
    raw = b"".join(b"\x00" + b"\x80\x80\x80" * w for _ in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def webp_bytes(w, h):
    vp8x = b"VP8X" + struct.pack("<I", 10) + b"\x00\x00\x00\x00" + (w - 1).to_bytes(3, "little") + (h - 1).to_bytes(3, "little")
    return b"RIFF" + struct.pack("<I", 4 + len(vp8x)) + b"WEBP" + vp8x


def gif_bytes(w, h):
    return b"GIF89a" + struct.pack("<HH", w, h) + b"\x00\x00\x00;"


def ctx_for(d, sid="ph", bg="mantle", tok=TOK):
    from scenes import Ctx
    return Ctx({"id": sid, "type": "product-hero"}, 0.0, 10.0, words30(), tok, d, os.path.join(d, "public"), bg, [], d)


class Sizes(unittest.TestCase):
    def test_sizes_of_png_jpeg_webp_gif(self):
        import imagesize
        d = scratch(self)
        for name, data, size in (("a.png", png_bytes(37, 21), (37, 21)), ("b.jpg", jpeg_bytes(640, 480), (640, 480)),
                                 ("c.webp", webp_bytes(300, 200), (300, 200)), ("d.gif", gif_bytes(12, 34), (12, 34))):
            p = os.path.join(d, name)
            with open(p, "wb") as f:
                f.write(data)
            self.assertEqual(imagesize.size(p), size, name)

    def test_not_an_image_is_named(self):
        import imagesize
        d = scratch(self)
        p = write(os.path.join(d, "x.png"), "not an image")
        with self.assertRaisesRegex(ValueError, "not a PNG, JPEG, WebP or GIF"):
            imagesize.size(p)

    def test_a_phone_photo_turned_by_exif_is_sized_as_shown(self):
        # a portrait phone photo is stored 4032x3024 with orientation 6; the browser draws it 3024x4032
        import imagesize
        d = scratch(self)
        for k, (o, order) in enumerate(((6, b"MM"), (8, b"II"), (1, b"MM"), (3, b"II"))):
            p = os.path.join(d, "p%d.jpg" % k)
            with open(p, "wb") as f:
                f.write(exif_jpeg_bytes(4032, 3024, o, order))
            self.assertEqual(imagesize.size(p), (3024, 4032) if o in (5, 6, 7, 8) else (4032, 3024), (o, order))

    def test_alpha_says_whether_an_image_can_be_a_cut_out(self):
        import imagesize
        d = scratch(self)
        for name, data, want in (("a.png", png_bytes(8, 8), True), ("b.png", rgb_png_bytes(8, 8), False),
                                 ("c.jpg", jpeg_bytes(8, 8), False), ("d.webp", webp_bytes(8, 8), False)):
            p = os.path.join(d, name)
            with open(p, "wb") as f:
                f.write(data)
            self.assertEqual(imagesize.alpha(p), want, name)

    def test_two_files_with_the_same_name_stay_apart(self):
        # IMG_0001.jpg from two folders: each keeps its own copy next to the page
        d = scratch(self)
        for sub, (w, h) in (("a", (40, 30)), ("b", (30, 40))):
            os.makedirs(os.path.join(d, sub), exist_ok=True)
            with open(os.path.join(d, sub, "photo.png"), "wb") as f:
                f.write(png_bytes(w, h))
        ctx = ctx_for(d)
        (pa, wa, ha), (pb, wb, hb) = ctx.image("a/photo.png"), ctx.image("b/photo.png")
        self.assertNotEqual(pa, pb)
        self.assertEqual(((wa, ha), (wb, hb)), ((40, 30), (30, 40)))
        import imagesize
        self.assertEqual(imagesize.size(os.path.join(d, "public", pb)), (30, 40))

    def test_backslash_paths_resolve_for_every_asset(self):
        d = scratch(self)
        os.makedirs(os.path.join(d, "assets"), exist_ok=True)
        with open(os.path.join(d, "assets", "logo.png"), "wb") as f:
            f.write(png_bytes(10, 10))
        rel, src = ctx_for(d).asset("assets\\logo.png")
        self.assertTrue(os.path.isfile(src) and os.path.isfile(os.path.join(d, "public", rel)))

    def test_backslash_src_resolves(self):
        # a storyboard written on Windows: assets\earbuds.png, relative to storyboard.json
        d = scratch(self)
        os.makedirs(os.path.join(d, "assets"), exist_ok=True)
        with open(os.path.join(d, "assets", "earbuds.png"), "wb") as f:
            f.write(png_bytes(40, 30))
        rel, w, h = ctx_for(d).image("assets\\earbuds.png")
        self.assertEqual((w, h), (40, 30))
        self.assertTrue(rel.startswith("assets/") and rel.endswith("earbuds.png"))
        self.assertTrue(os.path.isfile(os.path.join(d, "public", rel)))


class Notes(unittest.TestCase):
    NOTE = {"x": 0.7, "y": 0.8, "label": "WAIT... A WIRE?", "at": "word:4", "mark": "circle", "side": "left"}

    def test_a_note_draws_its_circle_then_its_label_on_its_word(self):
        from scenes import _annotate as A
        d = scratch(self)
        html, js = A.render([self.NOTE], ctx_for(d), 800, 900, "ph")
        t = t_word(4) - E.LEAD
        page = "\n".join(js)
        self.assertRegex(html, r'<circle[^>]*stroke="%s"' % E.theme(TOK, "mantle")["accent"])
        self.assertRegex(page, r"tl\.fromTo\('#ph-n0c', \{ strokeDashoffset: [\d.]+ \}, \{ strokeDashoffset: 0, duration: 0\.45, ease: 'power2\.inOut', immediateRender: false \}, %.3f\);" % t)
        self.assertRegex(page, r"tl\.fromTo\('#ph-n0l', \{ scaleX: 0 \}, \{ scaleX: 1, duration: 0\.2[^}]*\}, %.3f\);" % (t + 0.3))
        self.assertRegex(page, r"tl\.fromTo\('#ph-n0t', \{ opacity: 0, x: 12 \}, \{ opacity: 1, x: 0, duration: 0\.3[^}]*\}, %.3f\);" % (t + 0.45))
        self.assertRegex(html, r'id="ph-n0t" data-at="%.3f" data-anchor="word4"' % t)
        self.assertIn("WAIT... A WIRE?", html)

    def test_a_label_that_cannot_fit_fails_naming_it(self):
        from scenes import _annotate as A, SceneError
        d = scratch(self)
        with self.assertRaisesRegex(SceneError, "WAIT... A WIRE"):
            A.render([dict(self.NOTE, x=0.1, side="left")], ctx_for(d), 800, 900, "ph")

    def test_notes_are_checked(self):
        from scenes import _annotate as A
        self.assertEqual(A.validate([self.NOTE]), [])
        self.assertTrue(A.validate([dict(self.NOTE, x=1.4)]))
        self.assertTrue(A.validate([dict(self.NOTE, mark="star")]))
        self.assertTrue(A.validate([dict(self.NOTE, label="x" * 60)]))
        self.assertTrue(A.validate("not a list"))


if __name__ == "__main__":
    unittest.main()
