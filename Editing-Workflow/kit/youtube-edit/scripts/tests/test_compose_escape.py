"""compose.py: storyboard text is shown as text. A "<" or "&" in a label, list item or title ("R&D", "<b>") must never
become HTML: escaped where it lands in the page, so the card keeps its words and its markup."""
import copy, os, unittest
from .helpers import read, run, scratch, write
from .test_compose_drafts import WORLD
from .test_storyboard_md import BEATS

RAW = "R<b>X</b>&Y"
TEXT_KEYS = {"text", "label", "title", "eyebrow", "sub", "center", "head", "badge", "query", "kicker", "date", "name"}


def poison(beat):
    """Every on-screen text field of a beat set to RAW (paths, ids, times and icon names left alone)."""
    b = copy.deepcopy(beat)

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in TEXT_KEYS and isinstance(v, str):
                    node[k] = RAW
                else:
                    walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(b)
    for key in ("items", "spokes", "terms", "messages"):
        for it in b.get(key, []):
            if isinstance(it, list):
                k = 1 if b["type"] == "dock" or key == "messages" else 0
                if isinstance(it[k], str):
                    it[k] = RAW
    if "slots" in b:
        b["slots"] = [RAW for _ in b["slots"]]
    if "cards" in b:
        for c in b["cards"]:
            c["title"] = RAW
    return b


SKIP = {"doc", "dashzoom", "world", "player", "vignette", "pointer"}   # doc escapes already; dashzoom needs a real image
CASES = [b for b in BEATS if b["type"] not in SKIP] + [WORLD,
         {"type": "player", "id": "pv", "label": "Watch this next", "thumb": "img/thumbs/x.jpg", "title": "A title", "length": 754, "in": 1, "out": 2}]


class Escape(unittest.TestCase):
    def test_text_never_becomes_markup(self):
        leaks = []
        for beat in CASES:
            d = scratch(self)
            b = poison(beat)
            b["in"], b["out"] = 1.0, 4.0
            sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "duration": 10.0, "tag": {"n": 1, "of": 3, "label": RAW, "in": 0.2, "out": 0.9},
                                                            "beats": [b]})
            r = run("compose.py", "--spec", sp, "--out", os.path.join(d, "public"))
            if r.returncode:
                leaks.append("%s: compose failed: %s" % (b["type"], r.stderr.strip()[-200:]))
                continue
            body = read(os.path.join(d, "public", "index.html")).split("<script")[0]
            if "<b>X</b>" in body:
                leaks.append(b["type"])
        self.assertEqual(leaks, [])
