"""Calibration cases for group E1, the picture scenes of the editorial pass: product-hero and photo-grid (make-cases.py
loads this file). The scene runs from word 1; its items land on word 2 and later.

The pictures are placeholders that make-cases.py (and the theme and layout tests) write next to the case's storyboard:
any "src" anywhere in the data gets one. A name ending in -<W>x<H> (before its extension) gives that size, so a case
can ask for an odd aspect ("banner-3000x1000.png" is a 3:1 banner, "tall-500x1000.png" a 1:2 cut-out); a name without
one gets the default size (see make-cases.py images()). The placeholders are opaque PNGs (no alpha): the JPEG case.
"""


def at(i):
    return "word:%d" % i


def credit(i):
    return "stand-in image" if i % 2 == 0 else "J. Rivera"


CASES = {
    "product-hero": [
        ("short", {"src": "bud-1200x1200.png", "alt": "an earbud", "at": at(2)}),
        ("mid", {"src": "bud-1200x1200.png", "alt": "an earbud on its side", "title": "No wire", "title_at": at(2), "at": at(3),
                 "aspect": 1.0, "notes": [{"x": 0.75, "y": 0.16, "label": "WAIT... A WIRE?", "at": at(5), "mark": "circle",
                                           "side": "left"}]}),
        ("long", {"src": "kit-1600x1200.png", "alt": "the charging case open, both earbuds inside", "title": "Twelve hours",
                  "title_at": at(2), "at": at(3), "aspect": 4 / 3.0, "float": False,
                  "notes": [{"x": 0.3, "y": 0.06, "label": "+ USB-C", "at": at(5), "mark": "dot", "side": "right"},
                            {"x": 0.8, "y": 0.94, "label": "CASE", "at": at(7), "mark": "circle", "side": "left"}]}),
        # the odd aspects: a 3:1 banner, a 1:2 tall cut-out
        ("banner", {"src": "banner-3000x1000.png", "alt": "a wide banner", "title": "Wide", "title_at": at(2), "at": at(2),
                    "aspect": 3.0}),
        ("tall", {"src": "tall-500x1000.png", "alt": "a tall bottle", "title": "Tall", "at": at(2), "aspect": 0.5,
                  "notes": [{"x": 0.5, "y": 0.1, "label": "CAP", "at": at(4), "mark": "dot", "side": "right"}]}),
    ],
    "photo-grid": [
        ("short", {"photos": [{"src": "p1-1200x800.png", "credit": credit(0), "at": at(2)}]}),
        ("mid", {"layout": "grid", "photos": [{"src": "p%d-1200x800.png" % i, "credit": credit(i), "tag": tag, "at": at(2 + i)}
                                              for i, tag in enumerate(["BEFORE", "AFTER", None])]}),
        ("long", {"layout": "collage",
                  "photos": [{"src": "p%d-1200x800.png" % i, "credit": credit(i), "tag": ["WIDE", "CLOSE", "DETAIL", "PLUG"][i], "at": at(2 + 2 * i)}
                             for i in range(4)],
                  "notes": [{"x": 0.2, "y": 0.5, "label": "THE PLUG", "at": at(3), "mark": "circle", "side": "right"}]}),
        ("stack", {"layout": "stack", "photos": [{"src": "s%d-1600x900.png" % i, "credit": credit(i), "at": at(2)} for i in range(3)]}),
        ("pair", {"layout": "grid", "photos": [{"src": "q%d-1200x800.png" % i, "credit": credit(i), "at": at(2 + i)} for i in range(2)]}),
        ("collage-two", {"layout": "collage", "photos": [{"src": "c0-900x1200.png", "credit": credit(0), "tag": "NEW", "at": at(2)},
                                                         {"src": "c1-1200x1200.png", "credit": credit(1), "at": at(4)}]}),
    ],
}
