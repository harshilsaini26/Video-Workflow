"""The data and list scenes: list-cards, line-chart, bars, duration, qa-stack (SPEC §6.2)."""
import os, re, unittest
from .helpers import read, run, scratch, write
from .test_compose import D, VOICE, silent_wav, t_word, words30
import explainer_lib as E

TOK = E.load_tokens()


class SceneCase(unittest.TestCase):
    def build(self, scene):
        """A short title, then the scene under test from word:4 to the end."""
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        lead = {"type": "title", "id": "lead", "bg": "mantle", "in": "word:0", "out": "word:4", "text": "Lead in"}
        sc = dict({"id": "sc", "bg": "mantle", "in": "word:4", "out": D}, **scene)
        scenes = [lead, sc]
        if sc["out"] not in (D, "end"):     # a short scene under test: a closing scene covers the rest
            scenes.append({"type": "title", "id": "tail", "bg": "mantle", "in": sc["out"], "out": "end", "text": "The end"})
        sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "scenes": scenes})
        out = os.path.join(d, "public")
        r = run("explainer-compose.py", "--spec", sp, "--out", out, "--vendor", os.path.join(d, "vendor"))
        return r, (read(os.path.join(out, "index.html")) if r.returncode == 0 else "")

    def ok(self, scene):
        r, html = self.build(scene)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return html

    def fails(self, scene, text):
        r, _ = self.build(scene)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn(text, r.stdout + r.stderr)


def at_minus_lead(i):
    return round(t_word(i) - E.LEAD, 3)


def entrance_times(html, sel_prefix):
    return [float(t) for t in re.findall(r"tl\.fromTo\('%s[^']*', \{ opacity: 0[^;]*\}, ([\d.]+)\);" % re.escape(sel_prefix), html)]


class ListCards(SceneCase):
    def items(self, n):
        return [{"label": "Card " + "ABCDE"[i], "at": "word:%d" % (6 + 3 * i)} for i in range(n)]

    def test_two_to_four_items(self):
        self.fails({"type": "list-cards", "items": self.items(1)}, "2 to 4")
        self.fails({"type": "list-cards", "items": self.items(5)}, "2 to 4")
        self.ok({"type": "list-cards", "items": self.items(4)})

    def test_card_enters_on_its_word(self):
        html = self.ok({"type": "list-cards", "items": self.items(3)})
        self.assertEqual(entrance_times(html, "#sc-c"), [at_minus_lead(6), at_minus_lead(9), at_minus_lead(12)])
        self.assertEqual(len(re.findall(r'data-at="[\d.]+" data-anchor="word(6|9|12)"', html)), 3)


class EmptyStage(SceneCase):
    def test_list_cards_show_their_slots_from_the_start(self):
        html = self.ok({"type": "list-cards", "items": [{"label": "A", "at": "word:9"}, {"label": "B", "at": "word:12"}]})
        self.assertEqual(len(re.findall(r"tl\.to\('#sc-c\d', \{ opacity: 0\.18", html)), 2)

    def test_a_scene_that_shows_nothing_at_first_warns(self):
        r, _ = self.build({"type": "bars", "source": "s1", "rows": [{"label": "A", "value": 1, "at": "word:12"},
                                                                    {"label": "B", "value": 2, "at": "word:14"}]})
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARN sc: nothing shows for", r.stdout)


class LineChart(SceneCase):
    def chart(self, **kw):
        sc = {"type": "line-chart", "label": "VALUE OF $100", "points": [100, 114, 152, 214, 2650], "x": ["Y0", "Y5", "Y10", "Y15", "Y20"],
              "prefix": "$", "reveal": [{"point": 2, "at": "word:8"}, {"point": 4, "at": "word:12"}], "source": "s2"}
        sc.update(kw)
        return sc

    def test_points_and_x_must_match(self):
        self.fails(self.chart(x=["Y0", "Y5"]), "points")

    def test_reveal_point_in_range(self):
        self.fails(self.chart(reveal=[{"point": 9, "at": "word:8"}]), "point 9")

    def test_counts_to_last_revealed_point_in_full_digits(self):
        html = self.ok(self.chart())
        targets = re.findall(r"countUp\('#sc-v', ([\d.]+), ([\d.]+),", html)
        self.assertEqual(float(targets[-1][1]), 2650)
        self.assertEqual(float(targets[-1][0]), 152)
        self.assertIn("$2,650", html)

    def test_needs_a_source(self):
        sc = self.chart()
        del sc["source"]
        self.fails(sc, "needs a source")


class Bars(SceneCase):
    def bars(self, **kw):
        sc = {"type": "bars", "source": "s1", "rows": [
            {"label": "Coursera", "value": 40, "text": "$40", "at": "word:6"},
            {"label": "CFA", "value": 1000, "text": "$1,000", "hi": True, "at": "word:9"},
            {"label": "CPA", "value": 500, "text": "$500", "at": "word:12"}]}
        sc.update(kw)
        return sc

    def test_values_not_negative(self):
        sc = self.bars()
        sc["rows"][0]["value"] = -1
        self.fails(sc, "value")

    def test_width_proportional_and_hi_cyan(self):
        html = self.ok(self.bars())
        box_w = int(re.search(r'id="sc-live" style="width:(\d+)px', html).group(1))
        fills = re.findall(r'<div class="b-fill" style="width:(\d+)px;background:([^;"]+)', html)
        self.assertEqual(len(fills), 3)
        for (w, col), v in zip(fills, (40, 1000, 500)):
            self.assertAlmostEqual(int(w), box_w * v / 1000, delta=1)
        self.assertEqual(fills[1][1], E.theme(TOK, "mantle")["accent"])
        self.assertNotEqual(fills[0][1], E.theme(TOK, "mantle")["accent"])

    def test_unbreakable_word_too_wide_fails(self):
        sc = self.bars()
        sc["rows"][0]["label"] = "x" * 40
        self.fails(sc, "wider than the")


class Duration(SceneCase):
    def test_unit_and_style(self):
        self.fails({"type": "duration", "value": 6, "unit": "months", "style": "clock", "source": "s1"}, "unit")
        self.fails({"type": "duration", "value": 6, "unit": "weeks", "style": "gauge", "source": "s1"}, "style")
        for style in ("clock", "dial"):
            html = self.ok({"type": "duration", "value": 6, "unit": "weeks", "style": style, "source": "s1"})
            self.assertIn("weeks", html)
            self.assertIn("countUp('#sc-v', 0, 6", html)



class CountsFitWhileCounting(SceneCase):
    """DM Sans digits are proportional (0 is about twice as wide as 1), so a count is measured at its widest moment, not
    at its final number: on the way to $1,111,111 it shows $1,000,000."""

    def test_count_up(self):
        self.fails({"type": "count-up", "value": 1111111, "prefix": "$", "source": "s1"}, "wider than the")   # final ~620 px, ~966 counting
        self.ok({"type": "count-up", "value": 99999, "prefix": "$", "source": "s1"})

    def test_line_chart_readout(self):
        self.fails({"type": "line-chart", "points": [100, 11111111111], "x": ["Y0", "Y20"], "prefix": "$", "source": "s1"},
                   "wider than the")
        self.ok({"type": "line-chart", "points": [100, 2650], "x": ["Y0", "Y20"], "prefix": "$", "source": "s1"})

    def test_duration_in_full_digits(self):
        self.fails({"type": "duration", "value": 111111111, "unit": "hours", "source": "s1"}, "wider than the")
        self.ok({"type": "duration", "value": 1000, "unit": "hours", "source": "s1"})

class QAStack(SceneCase):
    def items(self, n):
        return [{"text": "Is the NPV positive?" if i == 0 else "Question " + "ABCDEF"[i] + " about IRR and NPV", "em": ["NPV"], "at": "word:%d" % (5 + 2 * i)}
                for i in range(n)]

    def test_at_most_five(self):
        self.fails({"type": "qa-stack", "items": self.items(6)}, "at most 5")

    def test_em_terms_highlighted_in_their_item(self):
        html = self.ok({"type": "qa-stack", "items": self.items(3)})
        for i in range(3):
            item = re.search(r'<div class="q-item" id="sc-q%d"[^>]*>(.*?)</div>' % i, html).group(1)
            self.assertEqual(len(re.findall(r'class="q-em"', item)), 1)
            self.assertIn(">NPV", item)


class Shared(SceneCase):
    def test_item_at_outside_scene_fails(self):
        self.fails({"type": "list-cards", "items": [{"label": "a", "at": "word:2"}, {"label": "b", "at": "word:8"}]}, "sc: ")
        self.fails({"type": "list-cards", "items": [{"label": "a", "at": "word:2"}, {"label": "b", "at": "word:8"}]}, "outside the scene")


class DurationDecimals(SceneCase):
    def test_fractional_value_keeps_its_decimal(self):
        html = self.ok({"type": "duration", "value": 1.5, "unit": "hours", "source": "s1"})
        self.assertRegex(html, r"countUp\('#sc-v', 0, 1\.5, [\d.]+, [\d.]+, '', '', 1\);")


class ShortScenes(SceneCase):
    def test_short_duration_finishes_its_count_before_the_exit(self):
        html = self.ok({"type": "duration", "value": 6, "unit": "weeks", "source": "s1", "out": "word:7"})
        t_in, t_out = t_word(4) - E.LEAD, t_word(7) - E.LEAD
        start, dur = map(float, re.search(r"countUp\('#sc-v', 0, 6, ([\d.]+), ([\d.]+),", html).groups())
        self.assertLessEqual(start + dur, t_out + 1e-6)
        sweep = re.search(r"tl\.\w+\('#sc-(hand|arc)'.*duration: ([\d.]+)[^;]*\}, ([\d.]+)\);", html)
        self.assertLessEqual(float(sweep.group(3)) + float(sweep.group(2)), t_out + 1e-6)


class QAHeights(unittest.TestCase):
    def test_highlight_padding_counts_in_the_height(self):
        from scenes import qa_stack as Q
        text = "Is the NPV positive this year"
        width = int(E.text_width(text, Q.SIZE)) + 2 * Q.PAD_X + 2       # fits one line without the highlight box
        plain = {"items": [{"text": text, "at": "word:5"}]}
        em = {"items": [{"text": text, "em": ["NPV"], "at": "word:5"}]}
        self.assertGreater(Q.height(em, width), Q.height(plain, width))
