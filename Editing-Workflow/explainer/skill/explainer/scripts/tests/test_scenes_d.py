"""The object scenes (group D): chat, doc, stat. Real-world objects instead of labelled boxes: a chat window where the
answer follows its question, a document whose passage lights up on its word, a hero figure that counts without
jumping. Each one refuses bad data with a reason, lands its items on their words and composes on every ground."""
import copy, importlib.util, os, re, unittest
from .helpers import SCRIPTS, read, run, scratch, write
from .test_compose import D, VOICE, silent_wav, t_word, words30
from .test_scenes_ui import stub_vendor
import explainer_lib as E
from scenes import REGISTRY

W = lambda i: "word:%d" % i
ICONS = ("book", "clock", "send", "file-text")

GOOD = {
    "chat": {"type": "chat", "name": "HR Assistant", "source": "s1", "messages": [
        {"role": "user", "text": "How many leave days do I get?", "at": W(5)},
        {"role": "assistant", "text": "You get 24 days of paid leave a year.", "at": W(9), "cite": {"text": "Leave policy.pdf", "at": W(12)}}]},
    "doc": {"type": "doc", "name": "leave-policy.pdf", "title": "Annual leave", "source": "s1", "blocks": [
        {"text": "Leave is earned every month."}, {"filler": 2},
        {"text": "Staff get 24 days of paid leave a year.", "at": W(8), "tag": "Section 3.2"}, {"filler": 1}]},
    "stat": {"type": "stat", "value": 363, "prefix": "+$", "unit": "a month", "label": "saved by the average user", "at": W(6),
             "source": "s1"},
}
ANCHORED = {"chat": 3, "doc": 1, "stat": 1}     # message, message, cite; the passage; the figure


def at_minus_lead(i):
    return round(t_word(i) - E.LEAD, 3)


class Case(unittest.TestCase):
    def build(self, scene, bg="mantle"):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        lead = {"type": "title", "id": "lead", "bg": bg, "in": "word:0", "out": "word:4", "text": "Lead in"}
        sc = dict({"id": "sc", "bg": bg, "in": "word:4", "out": D}, **scene)
        sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "scenes": [lead, sc], "sound": {"music": "none", "sfx": False}})
        out = os.path.join(d, "public")
        r = run("explainer-compose.py", "--spec", sp, "--out", out, "--vendor", stub_vendor(d, icons=ICONS))
        return r, (read(os.path.join(out, "index.html")) if r.returncode == 0 else "")

    def ok(self, scene, bg="mantle"):
        r, html = self.build(scene, bg)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return html

    def fails(self, scene, text):
        r, _ = self.build(scene)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn(text, r.stdout + r.stderr)


class Shared(Case):
    def test_every_type_is_found(self):
        for t in GOOD:
            self.assertIn(t, REGISTRY)

    def test_items_land_on_their_words(self):
        for t, sc in GOOD.items():
            html = self.ok(sc)
            body = html.split('id="host-sc"')[1].split('id="captions"')[0]
            self.assertEqual(len(re.findall(r'data-at="[\d.]+" data-anchor="word\d+"', body)), ANCHORED[t], t)

    def test_every_ground(self):
        for t, sc in GOOD.items():
            for bg in ("mantle", "base", "blue", "ink"):
                html = self.ok(sc, bg)
                self.assertNotRegex(html.split('id="host-sc"')[1], r"repeat:|yoyo|Math\.random", (t, bg))

    def test_an_item_outside_the_scene_fails(self):
        for t, sc in GOOD.items():
            bad = copy.deepcopy(sc)
            if t == "chat":
                bad["messages"][0]["at"] = W(2)
            elif t == "doc":
                bad["blocks"][2]["at"] = W(2)
            else:
                bad["at"] = W(2)
            self.fails(bad, "outside the scene")

    def test_longest_cases_fit_the_area(self):
        spec = importlib.util.spec_from_file_location("cases_d", os.path.join(SCRIPTS, "dev", "cases_d.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for t, variants in mod.CASES.items():
            self.assertGreaterEqual(len(variants), 3, t)
            for name, data in variants:
                self.assertEqual(REGISTRY[t].validate(data), [], (t, name))
                self.assertLessEqual(REGISTRY[t].height(data, 780), 600, (t, name))

    def test_text_is_28_px_or_more(self):
        for t in GOOD:
            sizes = [int(x) for x in re.findall(r"font-size:\s*(\d+)px", REGISTRY[t].CSS)]
            self.assertTrue(sizes and min(sizes) >= 28, t)

    def test_no_hex_colours_in_the_modules(self):
        for t in GOOD:
            with open(os.path.join(SCRIPTS, "scenes", "%s.py" % t)) as f:
                self.assertNotRegex(f.read(), r"#[0-9A-Fa-f]{6}\b", t)


class Chat(Case):
    def test_bad_data_says_why(self):
        sc = GOOD["chat"]
        self.fails(dict(sc, messages=sc["messages"][:1]), "1 to 3 exchanges")
        swapped = copy.deepcopy(sc)
        swapped["messages"][0]["role"], swapped["messages"][1]["role"] = "assistant", "user"
        self.fails(swapped, "take turns")
        empty = copy.deepcopy(sc)
        empty["messages"][1]["text"] = ""
        self.fails(empty, "has no text")
        cite = copy.deepcopy(sc)
        cite["messages"][1]["cite"] = {"text": "Leave policy.pdf"}
        self.fails(cite, "cite needs text")

    def test_the_answer_comes_after_its_question(self):
        late = copy.deepcopy(GOOD["chat"])
        late["messages"][0]["at"], late["messages"][1]["at"] = W(9), W(5)
        self.fails(late, "an answer comes after its question")
        early = copy.deepcopy(GOOD["chat"])
        early["messages"][1]["cite"]["at"] = W(7)
        self.fails(early, "lands before the answer")
        html = self.ok(GOOD["chat"])
        q = float(re.search(r'id="sc-b0" data-at="([\d.]+)"', html).group(1))
        a = float(re.search(r'id="sc-b1" data-at="([\d.]+)"', html).group(1))
        c = float(re.search(r'id="sc-c1" data-at="([\d.]+)"', html).group(1))
        self.assertEqual((q, a, c), (at_minus_lead(5), at_minus_lead(9), at_minus_lead(12)))

    def test_it_types_between_the_question_and_the_answer(self):
        html = self.ok(GOOD["chat"])
        dots_in = float(re.search(r"tl\.fromTo\('#sc-d1', \{ opacity: 0[^;]*\}, ([\d.]+)\);", html).group(1))
        dots_out = float(re.search(r"tl\.to\('#sc-d1', \{ opacity: 0[^;]*\}, ([\d.]+)\);", html).group(1))
        self.assertGreater(dots_in, at_minus_lead(5))
        self.assertLess(dots_in, dots_out)
        self.assertLessEqual(dots_out, at_minus_lead(9))
        self.assertRegex(html, r"tl\.to\('#sc-d1 b:nth-child\(1\)', \{ y: -9")             # the dots move in finite steps
        words = re.search(r"tl\.fromTo\('#sc-b1 \.chat-w', \{ opacity: 0 \}, \{[^}]*stagger[^;]*\}, ([\d.]+)\);", html)
        self.assertGreater(float(words.group(1)), at_minus_lead(9))                        # its words stream in after it lands

    def test_a_long_chat_scrolls_and_what_leaves_fades(self):
        sc = copy.deepcopy(GOOD["chat"])
        sc["messages"] += [{"role": "user", "text": "Do they roll over into the next year?", "at": W(15)},
                           {"role": "assistant", "text": "Up to five days, with your manager's approval.", "at": W(19)},
                           {"role": "user", "text": "Who approves it?", "at": W(22)},
                           {"role": "assistant", "text": "Your manager, in the HR portal.", "at": W(25)}]
        mod = REGISTRY["chat"]
        self.assertLessEqual(mod.height(sc, 780), 600)
        html = self.ok(sc)
        self.assertRegex(html, r'class="chat-view" style="height:\d+px"')
        self.assertRegex(html, r"tl\.to\('#sc-stack', \{ y: -[\d.]+")
        self.assertRegex(html, r"tl\.to\('#sc-r0', \{ opacity: 0")

    def test_a_number_in_a_message_needs_a_source_but_the_furniture_does_not(self):
        sc = copy.deepcopy(GOOD["chat"])
        del sc["source"]
        self.fails(sc, "needs a source")
        plain = {"type": "chat", "name": "GPT 4", "placeholder": "Ask 1 thing", "messages": [
            {"role": "user", "text": "Is it free?", "at": W(5)},
            {"role": "assistant", "text": "Yes, for everyone.", "at": W(9), "cite": {"text": "Pricing 2024.pdf", "at": W(12)}}]}
        self.ok(plain)


class Doc(Case):
    def test_bad_data_says_why(self):
        sc = GOOD["doc"]
        none = copy.deepcopy(sc)
        del none["blocks"][2]["at"]
        self.fails(none, "highlights 1 to 3 passages")
        self.fails(dict(sc, blocks=sc["blocks"] + [{"filler": 9}]), "filler is a number of grey lines")
        self.fails(dict(sc, blocks=sc["blocks"] + [{"filler": 1, "at": W(9)}]), "a filler block has no text")
        self.fails(dict(sc, blocks=[{"text": "x", "tag": "p. 4"}, {"text": "y", "at": W(9)}]), "has a tag but no at")

    def test_the_highlight_sweeps_on_its_word_and_the_tag_follows(self):
        html = self.ok(GOOD["doc"])
        self.assertRegex(html, r'<span class="doc-mark" id="sc-m2" data-at="%.3f" data-anchor="word8"' % at_minus_lead(8))
        sweep = re.search(r"tl\.fromTo\('#sc-m2', \{ backgroundSize: '0% 100%' \}, \{ backgroundSize: '100% 100%', duration: ([\d.]+)"
                          r"[^}]*\}, ([\d.]+)\);", html)
        self.assertIsNotNone(sweep)
        self.assertAlmostEqual(float(sweep.group(2)), at_minus_lead(8), places=3)
        tag = float(re.search(r"tl\.fromTo\('#sc-t2', \{ opacity: 0[^;]*\}, ([\d.]+)\);", html).group(1))
        self.assertGreater(tag, float(sweep.group(2)))
        self.assertIn("linear-gradient(%s" % E.rgba(E.theme(E.load_tokens(), "base")["accent"], 0.22), html)

    def test_filler_lines_need_no_source(self):
        self.ok({"type": "doc", "blocks": [{"filler": 3}, {"text": "Ask your manager first.", "at": W(6)}]})

    def test_a_tag_reserves_its_row(self):
        mod = REGISTRY["doc"]
        sc = copy.deepcopy(GOOD["doc"])
        plain = copy.deepcopy(sc)
        del plain["blocks"][2]["tag"]
        self.assertEqual(mod.height(sc, 780) - mod.height(plain, 780), mod.TAG_H + mod.TAG_GAP)


class Stat(Case):
    def test_bad_data_says_why(self):
        sc = GOOD["stat"]
        self.fails(dict(sc, value="lots"), "is not a number")
        self.fails(dict(sc, value=-3), "value is 0 or more")
        self.fails(dict(sc, unit="7 DAYS"), "the digits go in value")

    def test_it_needs_a_source(self):
        sc = dict(GOOD["stat"])
        del sc["source"]
        self.fails(sc, "needs a source")

    def test_it_counts_from_zero_on_its_word(self):
        html = self.ok(GOOD["stat"])
        self.assertRegex(html, r'id="sc-v" data-at="%.3f" data-anchor="word6"' % at_minus_lead(6))
        m = re.search(r"tl\.to\(sc_n, \{ v: 363\.0, duration: ([\d.]+), ease: '[\w.]+', onUpdate: [^;]*; \} \}, ([\d.]+)\);", html)
        self.assertIsNotNone(m)
        self.assertAlmostEqual(float(m.group(2)), at_minus_lead(6) + 0.05, places=3)
        self.assertIn("const sc_n = { v: 0 };", html)
        cells = re.findall(r'<span class="stat-c" style="width:([\d.]+)px(;display:none)?">(\d?)</span>', html)
        self.assertEqual([c[2] for c in cells], ["", "", "0"])                     # three cells, the count starts at 0
        self.assertEqual(len({c[0] for c in cells}), 1)                            # every digit cell the same width

    def test_it_fits_while_counting(self):
        # every cell is as wide as the widest digit and the box is as wide as the final figure: no moment is wider
        mod = REGISTRY["stat"]
        for v, prefix in ((1111, "$"), (99999, "$"), (8, ""), (2.5, "")):
            sc = {"value": v, "prefix": prefix, "decimals": 1 if v == 2.5 else 0}
            s = mod.size(sc)
            self.assertGreaterEqual(mod.fig_width(sc, s), E.L.count_width(v, s, prefix, "", sc["decimals"]), v)
        self.fails(dict(GOOD["stat"], value=111111111, prefix="$"), "wider than the")
        self.ok(dict(GOOD["stat"], value=99999, prefix="$", unit=""))

    def test_the_number_is_200_to_320_px_on_the_frame(self):
        mod = REGISTRY["stat"]
        for sc in ({"value": 8, "unit": "HOURS"}, {"value": 25000, "prefix": "$", "label": "the median cost of one breach"},
                   {"value": 363, "prefix": "+$"}, {"value": 2.5, "decimals": 1, "unit": "WEEKS"}):
            html = self.ok(dict(sc, type="stat", source="s1", at=W(6)))
            scale = float(re.search(r'id="sc-live" style="[^"]*transform:scale\(([\d.]+)\)', html).group(1))
            size = int(re.search(r'class="stat-fig" style="[^"]*font-size:(\d+)px', html).group(1))
            self.assertEqual(size, mod.size(sc))
            self.assertGreaterEqual(size * scale, 200 - 1e-6, sc)
            self.assertLessEqual(size * scale, 320 + 1e-6, sc)


if __name__ == "__main__":
    unittest.main()
