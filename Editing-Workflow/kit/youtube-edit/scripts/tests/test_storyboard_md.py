"""storyboard-md.py: every format compose.py builds gets a row, whatever shape its items take, and nothing crashes."""
import os, re, unittest
from .helpers import SCRIPTS, run, scratch, write, read

# One beat of every format, in the shapes compose.py's catalogue documents (items as lists, dicts, or the dock's triples).
BEATS = [
    {"type": "line", "id": "l1", "text": "You clicked on a thumbnail", "in": 8.5, "out": 11.6},
    {"type": "logo", "id": "yt", "src": "img/youtube.svg", "in": 11.85, "out": 14.9},
    {"type": "list", "id": "ls", "eyebrow": "Sells", "items": [["Candles", 6.24], ["Soap", 7.12, "soap"]], "in": 6.0, "out": 10.4},
    {"type": "bullets", "id": "bu", "items": [["Marketing", 38.48], ["Product catalog", 41.12]], "in": 37.9, "out": 44.9},
    {"type": "chip", "id": "ch", "text": "let's be honest", "in": 24.9, "out": 27.0},
    {"type": "vignette", "id": "vg", "in": 10.35, "out": 12.85},
    {"type": "pointer", "id": "pt", "in": 27.5, "out": 29.98},
    {"type": "site", "id": "st", "src": "img/site.png", "domain": "example.com/pricing", "in": 1, "out": 2, "transition": "punch"},
    {"type": "grid", "id": "th", "images": ["a.jpg", "b.jpg", "c.jpg"], "click_index": 1, "in": 1, "out": 2},
    {"type": "scene", "id": "mo", "kind": "money", "label": "Hundreds of dollars each", "in": 1, "out": 2},
    {"type": "browser3d", "id": "b3", "src": "img/site.png", "domain": "example.com", "label": "The pricing page", "in": 1, "out": 2},
    {"type": "fan3d", "id": "fn", "images": ["a.png", "b.png", "c.png"], "label": "Three tools", "in": 1, "out": 2},
    {"type": "stats", "id": "sa", "title": "The numbers", "items": [{"value": 250, "suffix": "+", "label": "Videos", "at": 1.2}], "in": 1, "out": 2},
    {"type": "growth", "id": "gr", "eyebrow": "Weekly views", "value": 248, "prefix": "+", "suffix": "%", "sub": "since the switch", "in": 1, "out": 2},
    {"type": "bars", "id": "br", "title": "Hours to ship", "rows": [{"label": "Editor", "value": 6.5, "text": "6.5 hrs"}], "in": 1, "out": 2},
    {"type": "pipeline", "id": "pp", "steps": [{"label": "Idea", "icon": "chat"}, {"label": "Paid", "payoff": True}], "in": 1, "out": 2},
    {"type": "hub", "id": "hb", "center": "Trust", "spokes": [["Earned", 1.2], ["Inherited", 1.4]], "in": 1, "out": 2},
    {"type": "equation", "id": "eq", "terms": [["Skills", 1.1], ["+", 1.2], ["Workflows", 1.3], ["=", 1.4], ["40 hrs saved", 1.5, "em"]], "in": 1, "out": 2},
    {"type": "wall", "id": "wl", "slots": ["Thumbnails", "Hooks", "Scripts"], "in": 1, "out": 2},
    {"type": "popout", "id": "po", "title": "What you need", "items": [["A camera", 1.2], ["One script", 1.4]], "in": 1, "out": 2},
    {"type": "flow", "id": "fl", "source": {"label": "One video"}, "outputs": [{"label": "Email"}, {"label": "Shorts"}], "result": {"label": "New subscribers"}, "in": 1, "out": 2},
    {"type": "dashzoom", "id": "dz", "src": "img/studio.png", "card": {"label": "Views", "value": 48210}, "in": 1, "out": 2},
    {"type": "lens", "id": "ln", "title": "Welcome email", "rows": [["Open rate", "48%"]], "in": 1, "out": 2},
    {"type": "search", "id": "sr", "query": "customer discovery questions", "results": [{"title": "The Mom Test"}], "in": 1, "out": 2},
    {"type": "dock", "id": "dk", "title": "My stack", "items": [["img/claude.svg", "Claude", 1.2], ["img/obs.svg", "OBS", 1.4]], "in": 1, "out": 2},
    {"type": "masktitle", "id": "mt", "eyebrow": "PART 2", "text": "Distribution", "sub": "where the first ten come from", "in": 1, "out": 2},
    {"type": "player", "id": "pv", "label": "Watch this next", "title": "How I edit", "in": 1, "out": 2},
    {"type": "image", "id": "im", "src": "img/x.jpg", "label": "The old studio", "in": 1, "out": 2},
    {"type": "layers", "id": "ly", "title": "What is inside an app", "layers": [{"label": "Interface"}, {"label": "Data"}], "in": 1, "out": 2},
    {"type": "world", "id": "wd", "nodes": [{"id": "a", "label": "Policy"}, {"id": "s", "kind": "stat", "value": 51, "suffix": "%", "label": "Rate"}], "in": 1, "out": 2},
    {"type": "deck", "id": "dc", "head": "3 PREDICTIONS", "cards": [{"title": "Agents"}, {"title": "Voice"}], "in": 1, "out": 2},
    {"type": "pills", "id": "pl", "layout": "row", "items": [["Codebase", 1.2], {"text": "Wrong price", "at": 1.4, "tone": "amber"}], "in": 1, "out": 2},
    {"type": "chat", "id": "cf", "messages": [["them", "Did this work?", 1.2], ["me", "Yes.", 1.5, "yes"]], "in": 1, "out": 2},
    {"type": "doc", "id": "dr", "domain": "example.com/news", "title": "A title", "paras": ["p"], "marks": [{"text": "the passage", "at": 1.2}], "in": 1, "out": 2},
    {"type": "clip", "id": "cl", "src": "broll/desk.mp4", "label": "Workforce", "items": [["Fine-tune", 1.2, "-"]], "in": 1, "out": 2},
]

EXPECT = {   # a word each format's row must show
    "line": "You clicked on a thumbnail", "logo": "youtube.svg", "list": "Sells: Candles, Soap", "bullets": "Marketing, Product catalog",
    "site": "site.png", "grid": "3 of the channel's own thumbnails, click on tile 2", "scene": "Hundreds of dollars each",
    "browser3d": "The pricing page", "fan3d": "3 screenshots", "stats": "The numbers: 250+ Videos", "growth": "+248% since the switch",
    "bars": "Editor 6.5 hrs", "pipeline": "Idea → Paid", "hub": "Trust: Earned, Inherited", "equation": "Skills + Workflows = 40 hrs saved",
    "wall": "Thumbnails, Hooks, Scripts", "popout": "What you need: A camera, One script", "flow": "One video → Email, Shorts → New subscribers",
    "dashzoom": "Views 48210", "lens": "Open rate 48%", "search": '"customer discovery questions": The Mom Test', "dock": "My stack: Claude, OBS",
    "masktitle": "PART 2: Distribution · where the first ten come from", "player": "Watch this next: How I edit", "image": "The old studio",
    "layers": "Interface, Data", "world": "Policy, 51% Rate", "deck": "3 PREDICTIONS: Agents, Voice", "pills": "Codebase, Wrong price",
    "chat": "them: Did this work? / me: Yes.", "doc": 'A title: "the passage"', "clip": "Workforce: Fine-tune",
}


class StoryboardMd(unittest.TestCase):
    def build(self, spec, *extra):
        d = scratch(self)
        write(os.path.join(d, "p", "storyboard.json"), spec)
        out = os.path.join(d, "STORYBOARD.md")
        r = run("storyboard-md.py", "--title", "T v1", "--project", os.path.join(d, "p") + ":01-part:Part one", "--out", out, *extra)
        return r, (read(out) if r.returncode == 0 else "")

    def test_every_format_gets_a_row_with_its_words(self):
        r, md = self.build({"id": "C1", "duration": 45.0, "beats": BEATS, "camera": [["set", 0, 1.0], ["punch", 18.3, 1.18]]})
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = [l for l in md.splitlines() if re.match(r"\| \d", l)]
        self.assertEqual(len(rows), len(BEATS))
        for b, row in zip(BEATS, rows):
            if b["type"] in EXPECT:
                self.assertIn(EXPECT[b["type"]], row, b["type"])
        self.assertIn("| camera | 1 moves | punch 18.3 |", md)
        self.assertIn("full-screen site cutaway (example.com/pricing) · punch cut", md)
        self.assertNotIn("img/claude.svg", md)   # the dock shows labels, not icon paths

    def test_every_compose_format_is_described(self):
        types = set(re.findall(r'(?:if|elif) t == "(\w+)"', read(os.path.join(SCRIPTS, "compose.py"))))
        self.assertGreater(len(types), 30)
        self.assertEqual(types - {b["type"] for b in BEATS}, set(), "add a beat for each new compose.py format")
        r, md = self.build({"id": "C1", "duration": 45.0, "beats": BEATS})
        for t in types:   # no row falls back to the bare type name
            self.assertNotRegex(md, r"\| %s \|" % t, t)

    def test_header_tag_notes_and_concerns(self):
        r, md = self.build({"id": "C1", "duration": 12.0, "tag": {"n": 1, "of": 5, "label": "Thumbnails", "in": 0.2, "out": 5.3},
                            "beats": BEATS[:1]}, "--note", "the hook moved first", "--concern", "check the logo")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("# T v1", md)
        self.assertIn("## 01-part: Part one (C1, 12.0 s)", md)
        self.assertIn("| 0.2 - 5.3 | progress tag | 1 of 5 · Thumbnails |", md)
        self.assertIn("- the hook moved first", md)
        self.assertIn("- check the logo", md)
        self.assertIn("| camera | 0 moves |  |", md)

    def test_unknown_format_and_table_breakers_never_crash(self):
        r, md = self.build({"id": "C1", "duration": 5.0, "beats": [
            {"type": "future", "id": "f", "in": 0.5, "out": 1.0, "items": [{"label": "New"}, 3, None]},
            {"type": "line", "id": "l", "text": "A | B\nC", "in": 1.0, "out": 2.0},
            {"type": "pills", "id": "p", "in": 2.0, "out": 3.0, "items": []}]})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("| 0.5 - 1.0 | future | New, 3 |", md)
        self.assertIn("A \\| B C", md)   # a pipe or newline can't break the table
