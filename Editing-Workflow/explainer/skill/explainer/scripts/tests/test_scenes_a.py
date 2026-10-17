"""Group A, type and social: gravity-drop, title-card, icon-strike, comment-cta, comment-drop. Each refuses bad data with
a reason, lands its items on their words (data-at), composes on all four grounds, and does its one thing: a pile that
falls under gravity, rules that draw out from a kicker, a strike on its word, a keyword that types in, a feed that
stacks newest first."""
import copy, os, re, unittest
from .helpers import read, run, scratch, write
from .test_compose import D, VOICE, silent_wav, t_word, words30
from .test_scenes_ui import stub_vendor
import explainer_lib as E
from scenes import REGISTRY

W = lambda i: "word:%d" % i
TOK = E.load_tokens()
GROUNDS = ("mantle", "base", "blue", "ink")


def at(i):
    return max(0.0, t_word(i) - E.LEAD)


GOOD = {
    "gravity-drop": {"type": "gravity-drop", "items": [{"text": "Excel", "at": W(6)}, {"text": "Accounting", "at": W(8)},
                                                       {"text": "Valuation", "at": W(10)}, {"text": "Python", "at": W(12)}]},
    "title-card": {"type": "title-card", "kicker": "PART 2", "title": "Build the model",
                   "subtitle": {"text": "Three statements, one sheet", "at": W(7)}},
    "icon-strike": {"type": "icon-strike", "icon": "clock", "label": "Paid tools", "at": W(5), "strike": {"at": W(8)},
                    "replacement": {"icon": "book", "label": "Free tools", "at": W(11)}},
    "comment-cta": {"type": "comment-cta", "keyword": {"text": "GUIDE", "at": W(6)}, "gets": {"text": "The free checklist, in your DMs", "at": W(10)}},
    "comment-drop": {"type": "comment-drop", "comments": [
        {"name": "sarah.k", "text": "This saved me hours", "likes": 1204, "time": "2h", "at": W(6)},
        {"name": "dev_mike99", "text": "Why did nobody tell me this", "likes": 87, "at": W(9)},
        {"name": "ana", "text": "Bookmarked", "likes": "2.4k", "at": W(12)}]},
}
ANCHORED = {"gravity-drop": 4, "title-card": 1, "icon-strike": 3, "comment-cta": 2, "comment-drop": 3}


class GroupA(unittest.TestCase):
    def build(self, scene, bg="mantle"):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        lead = {"type": "title", "id": "lead", "bg": "mantle", "in": "word:0", "out": "word:4", "text": "Lead in"}
        sc = dict({"id": "sc", "bg": bg, "in": "word:4", "out": D}, **scene)
        sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "scenes": [lead, sc], "sound": {"music": "none", "sfx": False}})
        out = os.path.join(d, "public")
        r = run("explainer-compose.py", "--spec", sp, "--out", out, "--vendor", stub_vendor(d))
        return r, (read(os.path.join(out, "index.html")) if r.returncode == 0 else "")

    def ok(self, scene, bg="mantle"):
        r, html = self.build(scene, bg)
        self.assertEqual(r.returncode, 0, "%s: %s" % (scene["type"], r.stdout + r.stderr))
        return html

    def test_every_type_is_registered(self):
        for t in GOOD:
            self.assertIn(t, REGISTRY)

    def test_items_land_on_their_words(self):
        for t, sc in GOOD.items():
            body = self.ok(sc).split('id="host-sc"')[1].split('id="captions"')[0]
            self.assertEqual(len(re.findall(r'data-at="[\d.]+" data-anchor="[^"]+"', body)), ANCHORED[t], t)

    def test_each_composes_on_all_four_grounds(self):
        for t, sc in GOOD.items():
            for bg in GROUNDS:
                html = self.ok(sc, bg)
                self.assertNotRegex(html, r"['\"](back|elastic|bounce)\.\w+", (t, bg))
                self.assertNotRegex(html, r"repeat: -1|yoyo|Math\.random", (t, bg))

    def test_bad_data_fails_with_a_reason(self):
        g, tc, ic, cc, cd = (copy.deepcopy(GOOD[k]) for k in ("gravity-drop", "title-card", "icon-strike", "comment-cta", "comment-drop"))
        cases = [
            (dict(g, items=g["items"][:1]), "2 to 8 items"),
            (dict(g, style="confetti"), "style"),
            (dict(g, items=[{"text": "Excel"}] + g["items"][1:]), "item 0 has no at"),
            (dict(g, items=list(reversed(g["items"]))), "in order"),
            ({k: v for k, v in tc.items() if k != "kicker"}, "missing 'kicker'"),
            (dict(tc, kicker="A KICKER FAR TOO LONG FOR A CARD"), "kicker"),
            (dict(tc, subtitle={"text": "No word"}), "subtitle"),
            (dict(ic, strike={}), "strike"),
            (dict(ic, icon="Not An Icon"), "Lucide"),
            (dict(ic, replacement={"icon": "book"}), "replacement needs"),
            (dict(cc, keyword={"text": "TWO WORDS", "at": W(6)}), "one word"),
            (dict(cc, keyword="GUIDE"), "keyword is {text, at}"),
            (dict(cc, gets={"text": "The checklist", "at": W(5)}), "before the keyword"),
            (dict(cd, comments=cd["comments"][:1]), "2 to 4 comments"),
            (dict(cd, comments=[dict(cd["comments"][0], name="")] + cd["comments"][1:]), "has no name"),
            (dict(cd, comments=list(reversed(cd["comments"]))), "in order"),
        ]
        for sc, word in cases:
            r, _ = self.build(sc)
            self.assertNotEqual(r.returncode, 0, (sc["type"], word))
            self.assertIn(word, r.stdout, (sc["type"], word, r.stdout))

    def test_an_item_outside_the_scene_fails(self):
        g = copy.deepcopy(GOOD["gravity-drop"])
        g["items"][0]["at"] = W(2)
        r, _ = self.build(g)
        self.assertIn("outside the scene", r.stdout)

    # ---- gravity-drop ---------------------------------------------------------------------------------------------
    def test_pieces_fall_under_gravity_and_rebound_twice(self):
        html = self.ok(GOOD["gravity-drop"])
        for i, w in enumerate((6, 8, 10, 12)):
            sel = "#sc-p%d" % i
            fall = re.search(r"tl\.fromTo\('%s', \{ y: -([\d.]+), rotation: [-\d.]+ \}, \{ y: 0, rotation: [-\d.]+, duration: ([\d.]+), "
                             r"ease: 'power2\.in', immediateRender: false \}, ([\d.]+)\);" % sel, html)
            self.assertTrue(fall, sel)
            self.assertAlmostEqual(float(fall.group(3)), at(w), places=3)          # it starts falling on its word
            ups = [float(h) for h in re.findall(r"tl\.to\('%s', \{ y: -([\d.]+),[^}]*ease: 'power2\.out'[^}]*\}" % sel, html)]
            downs = re.findall(r"tl\.to\('%s', \{ y: 0, duration: [\d.]+, ease: 'power2\.in' \}" % sel, html)
            self.assertEqual(len(ups), 2, sel)
            self.assertEqual(len(downs), 2, sel)
            self.assertGreater(ups[0], ups[1])                                     # each rebound smaller
            self.assertLess(ups[0], float(fall.group(1)) / 5.0)
        # a piece dropped from higher falls for longer (a square-root law, not one duration for all)
        mod = REGISTRY["gravity-drop"]
        self.assertLess(mod.fall(0, 200)[0][1], mod.fall(0, 600)[0][1])
        self.assertAlmostEqual(mod.fall(0, 600)[0][1] / mod.fall(0, 150)[0][1], 2.0, places=3)

    def test_the_pile_builds_from_the_bottom_and_never_through_itself(self):
        mod = REGISTRY["gravity-drop"]
        sets = [["Excel", "SQL"], ["Excel", "Accounting basics", "Valuation", "Python", "Three statements", "SQL", "Storytelling", "Modelling"],
                ["A", "Bb", "Ccc", "Dddd", "Eeeee", "Ffffff", "Ggggggg"], ["Time", "Risk", "Return", "Capital"]]
        for style in ("chips", "words"):
            for labels in sets:
                sc = {"style": style, "items": [{"text": l, "at": W(6)} for l in labels]}
                for width in (mod.min_width(sc), 600, 780, 950):
                    width = max(width, mod.min_width(sc))
                    places, h = mod.layout(sc, width)
                    st = mod.STYLES[style]
                    tops = [p[1] for p in places]
                    self.assertEqual(tops[0], h - st["h"], (style, labels))               # the first lands on the floor
                    self.assertEqual(tops, sorted(tops, reverse=True), (style, labels))   # later pieces land on or above
                    for i, (x, y, w) in enumerate(places):
                        self.assertGreaterEqual(x, 0)
                        self.assertLessEqual(x + w, width + 1)
                        for x2, y2, w2 in places[:i]:
                            if y2 == y:
                                self.assertTrue(x >= x2 + w2 + st["gx"] - 1 or x2 >= x + w + st["gx"] - 1, (labels, i))

    def test_the_newest_piece_wears_the_accent(self):
        html = self.ok(GOOD["gravity-drop"])
        c = E.theme(TOK, "mantle")
        accents = re.findall(r"tl\.to\('#sc-p(\d)', \{ borderColor: '%s'" % c["accent"], html)
        rests = re.findall(r"tl\.to\('#sc-p(\d)', \{ borderColor: '%s'" % c["line"], html)
        self.assertEqual(accents, ["0", "1", "2", "3"])
        self.assertEqual(rests, ["0", "1", "2"])

    # ---- title-card -----------------------------------------------------------------------------------------------
    def test_the_rules_draw_out_from_the_kicker(self):
        html = self.ok(GOOD["title-card"])
        css = REGISTRY["title-card"].CSS
        self.assertIn(".tc-rule.l { transform-origin:100% 50%; }", css)                 # the left one grows leftwards
        self.assertIn(".tc-rule.r { transform-origin:0 50%; }", css)
        self.assertRegex(html, r'<i class="tc-rule l"[^>]*></i><span class="tc-k"[^>]*>PART 2</span><i class="tc-rule r"')
        self.assertRegex(html, r"tl\.fromTo\('#sc-rl, #sc-rr', \{ scaleX: 0 \}, \{ scaleX: 1,")
        self.assertRegex(html, r"tl\.fromTo\('#sc \.tc-t \.w', \{ yPercent: 100, clipPath: 'inset\(-30% -12% 100% -12%\)' \}")
        self.assertRegex(html, r'id="sc-s" data-at="%.3f"' % at(7))

    def test_a_chapter_number_needs_no_source_but_a_title_number_does(self):
        self.ok(dict(GOOD["title-card"], kicker="STEP 3"))
        r, _ = self.build(dict(GOOD["title-card"], title="3 rules for models"))
        self.assertIn("needs a source", r.stdout)
        self.ok(dict(GOOD["title-card"], title="3 rules for models", source="s1"))

    # ---- icon-strike ----------------------------------------------------------------------------------------------
    def test_the_strike_lands_on_its_word_and_the_icon_dims(self):
        html = self.ok(GOOD["icon-strike"])
        c = E.theme(TOK, "mantle")
        self.assertRegex(html, r'<svg class="is-x" id="sc-x" data-at="%.3f"' % at(8))
        self.assertRegex(html, r'<line id="sc-xs"[^>]*stroke="%s"' % c["bad"])
        self.assertRegex(html, r"tl\.fromTo\('#sc-xh, #sc-xs', \{ strokeDashoffset: \d+ \}, \{ strokeDashoffset: 0, [^}]*\}, %.3f\);" % at(8))
        dim = re.search(r"tl\.to\('#sc-o-d', \{ opacity: ([\d.]+),[^}]*\}, ([\d.]+)\);", html)
        self.assertLess(float(dim.group(1)), 0.5)
        self.assertGreater(float(dim.group(2)), at(8))
        self.assertRegex(html, r"tl\.to\('#sc-o-l', \{ color: '%s'" % c["muted"])

    def test_the_replacement_lands_after_and_the_struck_icon_steps_aside(self):
        html = self.ok(GOOD["icon-strike"])
        self.assertRegex(html, r'class="is-col" id="sc-n" data-at="%.3f"' % at(11))
        self.assertRegex(html, r"tl\.to\('#sc-o', \{ x: -[\d.]+, scale: 0\.6,[^}]*\}, %.3f\);" % at(11))
        late = dict(GOOD["icon-strike"], replacement=dict(GOOD["icon-strike"]["replacement"], at=W(6)))
        r, _ = self.build(late)
        self.assertIn("comes before the strike", r.stdout)
        alone = {k: v for k, v in GOOD["icon-strike"].items() if k != "replacement"}
        self.assertNotIn('id="sc-n"', self.ok(alone))
        mod = REGISTRY["icon-strike"]
        self.assertLessEqual(mod.min_width(GOOD["icon-strike"]), 780)

    # ---- comment-cta ----------------------------------------------------------------------------------------------
    def test_the_keyword_types_in_character_by_character(self):
        html = self.ok(GOOD["comment-cta"])
        p = E.theme(TOK, "base")
        self.assertRegex(html, r'<div class="cc-chip" id="sc-chip" data-at="%.3f"' % at(6))
        self.assertIn('<span class="cc-typed" id="sc-typed" style="color:%s"><span id="sc-c0">G</span><span id="sc-c1">U</span>' % p["paper_ink"], html)
        sets = [(int(i), float(t)) for i, t in re.findall(r"tl\.set\('#sc-c(\d)', \{ display: 'inline' \}, ([\d.]+)\);", html)]
        self.assertEqual([i for i, _ in sets], [0, 1, 2, 3, 4])
        self.assertAlmostEqual(sets[0][1], at(6), places=3)                      # the first letter on the word
        steps = [b - a for (_, a), (_, b) in zip(sets, sets[1:])]
        self.assertTrue(all(abs(s - REGISTRY["comment-cta"].TYPE_STEP) < 1e-3 for s in steps), steps)
        self.assertRegex(html, r"tl\.set\('#sc-ph', \{ opacity: 0 \}, %.3f\);" % at(6))   # the placeholder gives way
        post = re.search(r"tl\.to\('#sc-post', \{ color: '%s',[^}]*\}, ([\d.]+)\);" % p["accent"], html)
        self.assertGreater(float(post.group(1)), sets[-1][1])                     # Post wakes once it is typed
        self.assertRegex(html, r'class="cc-g" id="sc-g" data-at="%.3f"' % at(10))

    def test_the_comment_box_is_paper_on_every_ground(self):
        p = E.theme(TOK, "base")
        for bg in GROUNDS:
            html = self.ok(GOOD["comment-cta"], bg)
            self.assertRegex(html, r'class="cc-box" id="sc-box" style="background:%s;' % p["paper"])

    def test_a_long_keyword_shrinks_on_its_chip(self):
        mod = REGISTRY["comment-cta"]
        self.assertEqual(mod.chip_size("GO", 780), mod.C_SIZE)
        long = mod.chip_size("SPREADSHEETS", 650)
        self.assertLess(long, mod.C_SIZE)
        self.assertGreaterEqual(long, mod.C_MIN)
        self.assertLessEqual(E.text_width("SPREADSHEETS", long, spacing=mod.C_TRACK) + 2 * mod.C_PAD, 650)

    # ---- comment-drop ---------------------------------------------------------------------------------------------
    def test_comments_stack_newest_first(self):
        html = self.ok(GOOD["comment-drop"])
        mod = REGISTRY["comment-drop"]
        self.assertIn("flex-direction:column-reverse", mod.CSS)             # the last comment in the list sits on top
        ids = re.findall(r'class="cd-c" id="sc-c(\d)" data-at="([\d.]+)"', html)
        self.assertEqual([i for i, _ in ids], ["0", "1", "2"])
        for (_, t), w in zip(ids, (6, 9, 12)):
            self.assertAlmostEqual(float(t), at(w), places=3)
        for i, w in enumerate((6, 9, 12)):
            drop = re.search(r"tl\.fromTo\('#sc-c%d', \{ opacity: 0, y: (-?[\d.]+) \}, \{ opacity: 1, y: (-?[\d.]+),[^}]*\}, ([\d.]+)\);" % i, html)
            self.assertAlmostEqual(float(drop.group(3)), at(w), places=3)
            self.assertLess(float(drop.group(1)), float(drop.group(2)))       # it drops into place from above
            pushes = re.findall(r"tl\.to\('#sc-c%d', \{ y: (-?[\d.]+), duration" % i, html)
            self.assertEqual(len(pushes), 2 - i)                               # every later comment pushes it down
            ys = [float(drop.group(2))] + [float(y) for y in pushes]
            self.assertEqual(ys, sorted(ys))
            self.assertEqual(ys[-1], 0.0)                                      # and it ends in its own place
        self.assertEqual(float(re.search(r"tl\.fromTo\('#sc-c2', \{ opacity: 0, y: (-?[\d.]+) \}, \{ opacity: 1, y: (-?[\d.]+)", html).group(2)), 0)

    def test_names_counts_and_times_are_furniture(self):
        html = self.ok(GOOD["comment-drop"])                                   # 1204 likes, dev_mike99: no source needed
        self.assertIn(">1.2k<", html)
        self.assertIn(">@dev_mike99<", html)
        self.assertRegex(html, r'class="cd-av"[^>]*>D<')
        cd = copy.deepcopy(GOOD["comment-drop"])
        cd["comments"][0]["text"] = "Saved me 10 hours"
        r, _ = self.build(cd)
        self.assertIn("needs a source", r.stdout)

    def test_heights_fit_the_scene_area(self):
        for t, sc in GOOD.items():
            mod = REGISTRY[t]
            w = max(780, mod.min_width(sc))
            self.assertLessEqual(mod.height(sc, w), 600, t)


if __name__ == "__main__":
    unittest.main()
