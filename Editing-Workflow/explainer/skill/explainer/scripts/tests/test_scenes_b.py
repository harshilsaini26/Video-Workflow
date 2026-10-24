"""Group B, the tool mock-ups: prompt-bar, storyboard-deck, file-drop, nle-timeline, jiggle-delete. Each is light paper on
any ground, refuses bad data with a reason, puts data-at on every word-anchored item, and does its one change on its
word: the prompt types in, the frames are dealt, the files drop, a cut splits a clip and ripples, a tile leaves and the
rest move up."""
import copy, os, re, unittest
from .helpers import read, run, scratch, write
from .test_compose import D, VOICE, silent_wav, words30
from .test_scenes_ui import stub_vendor
from scenes import REGISTRY

W = lambda i: "word:%d" % i
T = lambda i: round(0.5 + 0.4 * i - 0.2, 3)          # an item's time: its word's start minus the lead
ICONS = ("book", "clock", "calculator", "send", "file-text")

GOOD = {
    "prompt-bar": {"type": "prompt-bar", "placeholder": "Ask anything", "prompt": {"text": "Write a hook about index funds", "at": W(6)},
                   "send": {"at": W(12)}, "reply": {"text": "Here are three hooks", "at": W(15)}},
    "storyboard-deck": {"type": "storyboard-deck", "frames": [{"note": "Hook", "sketch": "face", "at": W(6)},
                                                              {"note": "Demo", "sketch": "screen", "at": W(9)},
                                                              {"note": "Result", "sketch": "chart", "at": W(12)}]},
    "file-drop": {"type": "file-drop", "files": [{"name": "interview.mp4", "size": "1.2 GB", "at": W(6)},
                                                 {"name": "notes.pdf", "icon": "file-text", "at": W(8)}],
                  "done": {"label": "Uploaded", "at": W(14)}},
    "nle-timeline": {"type": "nle-timeline",
                     "tracks": [{"kind": "video", "clips": [{"label": "Hook", "length": 3}, {"label": "Interview", "length": 8},
                                                            {"label": "Outro", "length": 5}]},
                                {"kind": "audio", "clips": [{"label": "Music", "length": 16}]}],
                     "cuts": [{"track": 0, "time": 7, "length": 2, "at": W(8)}, {"track": 0, "time": 14, "at": W(14)}]},
    "jiggle-delete": {"type": "jiggle-delete", "jiggle": {"at": W(5)},
                      "tiles": [{"label": "Notes", "icon": "book"}, {"label": "Clock", "icon": "clock", "at": W(8)},
                                {"label": "Budget", "icon": "calculator"}, {"label": "Mail", "at": W(11)}, {"label": "Photos"}],
                      "done": {"at": W(18)}},
}
ITEMS = {"prompt-bar": 3, "storyboard-deck": 3, "file-drop": 3, "nle-timeline": 2, "jiggle-delete": 4}


class B(unittest.TestCase):
    def build(self, scene, bg="mantle"):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        lead = {"type": "title", "id": "lead", "bg": "mantle", "in": "word:0", "out": "word:4", "text": "Lead in"}
        sc = dict({"id": "sc", "bg": bg, "in": "word:4", "out": D}, **scene)
        sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "scenes": [lead, sc]})
        out = os.path.join(d, "public")
        r = run("explainer-compose.py", "--spec", sp, "--out", out, "--vendor", stub_vendor(d, icons=ICONS))
        return r, (read(os.path.join(out, "index.html")) if r.returncode == 0 else "")

    def ok(self, scene, bg="mantle"):
        r, html = self.build(scene, bg)
        self.assertEqual(r.returncode, 0, "%s: %s" % (scene["type"], r.stdout + r.stderr))
        return html

    def fails(self, scene, text):
        r, _ = self.build(scene)
        self.assertNotEqual(r.returncode, 0, "%s should fail (%s): %s" % (scene["type"], text, r.stdout))
        self.assertIn(text, r.stdout + r.stderr, scene["type"])

    @staticmethod
    def body(html):
        return html.split('id="host-sc"')[1].split('id="captions"')[0]

    @staticmethod
    def js(html):
        """The scene's own timeline lines."""
        return html.split("// sc (")[1].split("\n// ")[0] if "// sc (" in html else ""

    # ---- every type -------------------------------------------------------------------------------------------------
    def test_every_type_is_registered_with_the_contract(self):
        for t in GOOD:
            mod = REGISTRY[t]
            for name in ("CSS", "validate", "height", "min_width", "render"):
                self.assertTrue(hasattr(mod, name), (t, name))
            self.assertNotRegex(mod.CSS, r"#[0-9a-fA-F]{3,6}\b", t)                     # colours come from ctx
            sizes = [int(x) for x in re.findall(r"font-size:\s*(\d+)px", mod.CSS)]
            self.assertTrue(sizes and min(sizes) >= 30, (t, sizes))     # 28 px drawn even at the composer's smallest scale

    def test_items_land_on_their_words(self):
        for t, sc in GOOD.items():
            body = self.body(self.ok(sc))
            self.assertEqual(len(re.findall(r'data-at="[\d.]+" data-anchor="word\d+"', body)), ITEMS[t], t)

    def test_each_composes_on_all_four_grounds_in_paper(self):
        for t, sc in GOOD.items():
            for bg in ("mantle", "base", "blue", "ink"):
                html = self.ok(sc, bg)
                self.assertIn("#eff1f5", self.body(html), (t, bg))           # light paper (Latte base) on every ground

    def test_motion_is_finite_and_calm(self):
        for t, sc in GOOD.items():
            js = self.js(self.ok(sc))
            self.assertTrue(js, t)
            for bad in ("repeat", "yoyo", "Math.random", "bounce", "elastic", "back.", "Date.now"):
                self.assertNotIn(bad, js, (t, bad))

    def test_an_item_outside_the_scene_fails(self):
        for t, sc in GOOD.items():
            bad = copy.deepcopy(sc)
            key = {"prompt-bar": lambda s: s["prompt"], "storyboard-deck": lambda s: s["frames"][0], "file-drop": lambda s: s["files"][0],
                   "nle-timeline": lambda s: s["cuts"][0], "jiggle-delete": lambda s: s["tiles"][1]}[t]
            key(bad)["at"] = W(2)
            self.fails(bad, "outside the scene")

    # ---- prompt-bar -------------------------------------------------------------------------------------------------
    def test_prompt_bar_refuses_bad_data(self):
        g = GOOD["prompt-bar"]
        self.fails(dict(g, prompt={"text": "", "at": W(6)}), "prompt needs text")
        self.fails(dict(g, prompt={"text": "x " * 70, "at": W(6)}), "at most 120")
        self.fails(dict(g, send={}), "send needs at")
        self.fails(dict(g, reply={"text": "Hi"}), "reply needs text and at")
        self.fails(dict(g, send={"at": W(7)}), "give it more words")

    def test_the_prompt_types_in_letter_by_letter_on_its_word(self):
        html = self.ok(GOOD["prompt-bar"])
        text = GOOD["prompt-bar"]["prompt"]["text"]
        letters = re.findall(r'<span class="pb-ch" id="sc-c(\d+)">(.)</span>', html)
        self.assertEqual("".join(ch for _, ch in letters), text.replace(" ", ""))
        times = [float(x) for x in re.findall(r"tl\.set\('#sc-c\d+', \{ opacity: 1, '--on': 1 \}, ([\d.]+)\);", html)]
        self.assertEqual(len(times), len(letters))
        self.assertAlmostEqual(times[0], T(6), places=2)                      # the first letter on the word
        self.assertEqual(times, sorted(times))
        self.assertLess(times[-1], T(12))                                     # all typed before the send
        self.assertIn("tl.fromTo('#sc-send', { scale: 1 }", html)
        self.assertRegex(html, r"tl\.fromTo\('#sc-send', \{ scale: 1 \}, \{[^}]*\}, %.3f\);" % T(12))
        self.assertIn('class="pb-reply"', html)

    # ---- storyboard-deck --------------------------------------------------------------------------------------------
    def test_storyboard_deck_refuses_bad_data(self):
        g = GOOD["storyboard-deck"]
        self.fails(dict(g, frames=g["frames"][:1]), "2 to 4 frames")
        self.fails(dict(g, frames=g["frames"] * 2), "2 to 4 frames")
        self.fails(dict(g, frames=[dict(g["frames"][0], sketch="robot")] + g["frames"][1:]), "is not one of")
        self.fails(dict(g, frames=[{"note": "x", "at": W(6)}, {"at": W(8)}]), "frame 1 has no note")
        long = [{"note": "Talking head shot", "at": W(6 + k)} for k in range(4)]
        self.fails(dict(g, frames=long), "do not fit side by side")

    def test_each_frame_is_dealt_from_the_deck_on_its_word(self):
        html = self.ok(GOOD["storyboard-deck"])
        for i, w in enumerate((6, 9, 12)):
            m = re.search(r"tl\.fromTo\('#sc-f%d', \{ x: [-\d.]+, y: [-\d.]+, rotation: [-\d.]+ \}, \{ x: 0, y: 0, rotation: (-?[\d.]+),[^}]*\}, ([\d.]+)\);"
                          % i, html)
            self.assertTrue(m, i)
            self.assertAlmostEqual(float(m.group(2)), T(w), places=2)
            self.assertEqual(float(m.group(1)), (-5, 0, 5)[i])                # fanned
            self.assertIn("tl.set('#sc-f%d .gt', { opacity: 0 }, 0);" % i, html)   # face down until then

    # ---- file-drop --------------------------------------------------------------------------------------------------
    def test_file_drop_refuses_bad_data(self):
        g = GOOD["file-drop"]
        self.fails(dict(g, files=[]), "missing 'files'")
        self.fails(dict(g, files=g["files"] * 3), "1 to 4 files")
        self.fails(dict(g, files=[{"name": "a.mp4"}]), "file 0 has no at")
        self.fails(dict(g, done={"at": W(9)}), "no time after the last file")
        self.fails(dict(g, files=list(reversed(g["files"]))), "in the order they are listed")

    def test_files_drop_on_their_words_and_the_check_lands_on_done(self):
        html = self.ok(GOOD["file-drop"])
        for i, w in enumerate((6, 8)):
            self.assertRegex(html, r"tl\.fromTo\('#sc-r%d', \{ opacity: 0, y: -150, scale: 0\.94 \}, \{[^}]*\}, %.3f\);" % (i, T(w)))
        self.assertRegex(html, r"tl\.fromTo\('#sc-check', \{ opacity: 0, scale: 0\.4 \}, \{[^}]*\}, %.3f\);" % T(14))
        self.assertRegex(html, r"tl\.fromTo\('#sc-fill', \{ scaleX: 0 \}, \{ scaleX: 1,[^}]*\}, [\d.]+\);")
        self.assertIn(">MP4<", html)                                          # the extension on its tile
        # a file name and its size are furniture: no source needed for "mp4" or "1.2 GB"
        self.assertNotIn("source", GOOD["file-drop"])

    # ---- nle-timeline -----------------------------------------------------------------------------------------------
    def test_nle_timeline_refuses_bad_data(self):
        g = GOOD["nle-timeline"]
        self.fails(dict(g, tracks=g["tracks"] * 2), "1 to 3 tracks")
        self.fails(dict(g, tracks=[{"kind": "film", "clips": [{"label": "A", "length": 3}]}]), "kind is video or audio")
        self.fails(dict(g, tracks=[{"clips": [{"label": "A"}]}], cuts=[]), "needs a length")
        self.fails(dict(g, cuts=[{"track": 0, "time": 30, "at": W(8)}]), "is not inside a clip")
        self.fails(dict(g, cuts=[{"track": 0, "time": 7, "length": 6, "at": W(8)}]), "runs past the end of its clip")
        self.fails(dict(g, cuts=[{"track": 0, "time": 7, "length": 2, "at": W(8)}, {"track": 0, "time": 8, "at": W(12)}]), "overlap")
        self.fails(dict(g, cuts=[{"track": 5, "time": 7, "at": W(8)}]), "is not one of the 2 tracks")
        self.fails(dict(g, cuts=[{"track": 0, "time": 3.05, "length": 1, "at": W(8)}]), "too short on the timeline")

    def test_a_cut_splits_the_clip_lifts_the_piece_out_and_ripples(self):
        html = self.ok(GOOD["nle-timeline"])
        # Interview (3 to 11 s) is cut at 7 to 9 and Outro (11 to 16 s) split at 14: track 0 has Hook, Interview in three pieces,
        # Outro in two
        pieces = re.findall(r'class="nl-piece" id="sc-p0-(\d+)"', html)
        self.assertEqual(len(pieces), 6)
        # the middle piece of Interview lifts away just after the word
        self.assertRegex(html, r"tl\.to\('#sc-p0-2', \{ y: -18, opacity: 0,[^}]*\}, %.3f\);" % (T(8) + 0.3))
        # the pieces after it, and Outro's label with its piece, ripple left on that cut
        for el in ("#sc-p0-3", "#sc-p0-4", "#sc-l0-4"):
            m = re.search(r"tl\.fromTo\('%s', \{ x: -?0(?:\.0)? \}, \{ x: (-[\d.]+),[^}]*\}, %.3f\);" % (el, T(8) + 0.55), html)
            self.assertTrue(m, el)
            self.assertLess(float(m.group(1)), -10)
        # the playhead jumps to the cut on its word, and the razor mark carries the word
        self.assertRegex(html, r"tl\.fromTo\('#sc-ph', \{ x: [\d.]+ \}, \{ x: [\d.]+, duration: 0\.3, ease: 'expo\.out'[^}]*\}, %.3f\);" % T(8))
        self.assertRegex(html, r'class="nl-razor" id="sc-k0-0" data-at="%.3f" data-anchor="word8"' % T(8))
        # nothing on the music track moves
        self.assertNotRegex(html, r"tl\.fromTo\('#sc-p1-")
        self.assertIn(">V1<", html)
        self.assertIn(">A1<", html)

    # ---- jiggle-delete ----------------------------------------------------------------------------------------------
    def test_jiggle_delete_refuses_bad_data(self):
        g = GOOD["jiggle-delete"]
        self.fails(dict(g, tiles=g["tiles"][:2]), "3 to 8 tiles")
        self.fails(dict(g, tiles=[{k: v for k, v in t.items() if k != "at"} for t in g["tiles"]]), "no tile is deleted")
        self.fails(dict(g, tiles=[dict(t, at=W(8 + 3 * k)) for k, t in enumerate(g["tiles"][:3])]), "keep at least one")
        self.fails(dict(g, jiggle={"at": W(8)}), "before the tiles start to jiggle")
        self.fails(dict(g, done={"at": W(11)}), "before the last tile has gone")

    def test_deleted_tiles_leave_on_their_words_and_the_rest_move_up(self):
        html = self.ok(GOOD["jiggle-delete"])
        for i, w in ((1, 8), (3, 11)):
            self.assertRegex(html, r"tl\.to\('#sc-t%d', \{ scale: 0, opacity: 0,[^}]*\}, %.3f\);" % (i, T(w) + 0.12))
            self.assertRegex(html, r"tl\.to\('#sc-b%d', \{ backgroundColor: '#d20f39'" % i)
        # after Clock (1) goes, Budget (2) moves into its place: one column left
        m = re.search(r"tl\.fromTo\('#sc-t2', \{ x: 0, y: 0 \}, \{ x: (-[\d.]+), y: 0,[^}]*\}, ([\d.]+)\);", html)
        self.assertTrue(m)
        self.assertGreater(float(m.group(2)), T(8))
        # after Mail (3) goes too, Photos (4) moves up from the second row to the first row's last place
        self.assertRegex(html, r"tl\.fromTo\('#sc-t4', \{ x: [-\d.]+, y: [-\d.]+ \}, \{ x: [\d.]+, y: -[\d.]+,")
        # the jiggle: many small finite swings, out of step, that stop on Done
        swings = re.findall(r"tl\.to\('#sc \.jd-tile\.(ev|od)', \{ rotation: (-?[\d.]+), duration: 0\.13", html)
        self.assertGreater(len(swings), 20)
        self.assertTrue(all(abs(float(a)) <= 3 for _, a in swings))
        self.assertRegex(html, r"tl\.to\('#sc \.jd-tile', \{ rotation: 0,[^}]*\}, %.3f\);" % T(18))


if __name__ == "__main__":
    unittest.main()
