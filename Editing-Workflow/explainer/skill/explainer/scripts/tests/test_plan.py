"""plan-storyboard.py: a draft storyboard from the script's `viz` hints and the aligned words, so the Director edits a
plan that already composes instead of writing every scene and anchor by hand."""
import copy, json, os, re, unittest
from .helpers import load, read, run, scratch, write
from .test_compose import BOARD, VOICE, silent_wav, words30
from .test_scenes_ui import stub_vendor

STEP = 0.35
SCRIPT = {"title": "RAG in a minute", "sources": {"s1": {"title": "x", "url": "https://example.org"}},
          "lines": [
              {"id": "l0", "show": "The 3-step trick that makes AI invent less", "source": "s1"},
              {"id": "l1", "show": "It retrieves, then augments, then generates.", "break": "section",
               "viz": {"type": "flow", "nodes": ["Retrieve", "Augment", "Generate"]}},
              {"id": "l2", "show": "It saved me $1,000 a year.", "source": "s1"},
              {"id": "l3", "show": "Step 2 is the prompt.", "source": "s1"},
              {"id": "l4", "show": "The model reads the passages you found and writes its answer from them instead of guessing",
               "emphasis": ["passages"]},
              {"id": "l5", "show": "Budgeting sits on top of the cost of capital and risk.",
               "viz": {"type": "stack", "items": ["Cost of capital", "Valuation", "Risk"]}}]}


def transcript(script):
    words, t = [], 0.3
    for ln in script["lines"]:
        for w in ln["show"].split():
            words.append({"text": w, "start": round(t, 3), "end": round(t + 0.3, 3), "line": ln["id"]})
            t += STEP
        t += 0.3
    return {"words": words}


class Plan(unittest.TestCase):
    def plan(self, script=SCRIPT):
        d = scratch(self)
        write(os.path.join(d, "script.json"), script)
        tr = transcript(script)
        write(os.path.join(d, "transcript.json"), tr)
        silent_wav(os.path.join(d, "voice.wav"), tr["words"][-1]["end"] + 0.2)
        r = run("plan-storyboard.py", "--script", os.path.join(d, "script.json"), "--transcript", os.path.join(d, "transcript.json"),
                "--out", os.path.join(d, "storyboard.json"), "--report", os.path.join(d, "PLAN.md"), "--vendor", stub_vendor(d))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return d, load(os.path.join(d, "storyboard.json")), tr["words"]

    def test_the_draft_composes_and_keeps_pace(self):
        d, sb, _ = self.plan()
        r = run("explainer-compose.py", "--spec", os.path.join(d, "storyboard.json"), "--out", os.path.join(d, "public"), "--vendor", stub_vendor(d))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run("pace-check.py", "--index", os.path.join(d, "public", "index.html"))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(sb["scenes"][0]["in"], "word:0")
        self.assertEqual(sb["scenes"][-1]["out"], "end")
        for a, b in zip(sb["scenes"], sb["scenes"][1:]):
            self.assertEqual(a["out"], b["in"])
        self.assertIn("| l1 |", read(os.path.join(d, "PLAN.md")))

    def test_a_last_line_with_a_strike_and_a_caption_still_passes_e4(self):
        script = copy.deepcopy(SCRIPT)
        script["lines"][-1] = {"id": "l5", "show": "Pick a mode: slow, medium or fast.",
                               "viz": {"type": "line-art", "icon": "clock", "caption": "Pick a mode", "at": "medium", "strike": "fast."}}
        d, sb, words = self.plan(script)
        said_by = lambda a: words[int(a.split(":")[1])]["text"]
        la = sb["scenes"][-1]
        self.assertEqual(said_by(la["strike"]), "fast.")                 # every piece stays on its word
        self.assertGreater(sb["tail"], 0.5)                               # and the page runs on past the voice
        r = run("explainer-compose.py", "--spec", os.path.join(d, "storyboard.json"), "--out", os.path.join(d, "public"), "--vendor", stub_vendor(d))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run("pace-check.py", "--index", os.path.join(d, "public", "index.html"))
        self.assertNotIn("the last read", r.stdout)

    def test_viz_items_land_on_their_words(self):
        _, sb, words = self.plan()
        flow = next(s for s in sb["scenes"] if s["type"] == "flow")
        said = [words[int(n["at"].split(":")[1])]["text"] for n in flow["nodes"]]
        self.assertEqual(said, ["retrieves,", "augments,", "generates."])
        self.assertEqual([n["label"] for n in flow["nodes"]], ["Retrieve", "Augment", "Generate"])

    def test_a_kinetic_hook_from_plain_words(self):
        script = copy.deepcopy(SCRIPT)
        script["lines"][0]["viz"] = {"type": "kinetic", "big": "3", "words": ["STEP", "TRICK"], "line": "AI INVENTS",
                                     "strike": "INVENTS", "punch": "LESS"}
        d, sb, words = self.plan(script)
        hk = sb["scenes"][0]
        self.assertEqual(hk["type"], "kinetic")
        # SOP S8: the hook is whole on screen by 1.0 s: its pieces land in order on the words said by then
        pos = [int(p["at"].split(":")[1]) for p in [hk["big"]] + hk["words"] + [hk["line"], hk["strike"], hk["punch"]]]
        self.assertEqual(pos, sorted(pos))
        self.assertEqual(pos[0], 0)
        self.assertTrue(all(words[i]["start"] <= 1.0 for i in pos), pos)
        self.assertGreater(len(set(pos)), 1)
        self.assertEqual(hk["strike"]["word"], "INVENTS")
        r = run("explainer-compose.py", "--spec", os.path.join(d, "storyboard.json"), "--out", os.path.join(d, "public"), "--vendor", stub_vendor(d))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_hints_for_the_new_scenes_anchor_their_pieces(self):
        # the writer hints a picture in a line; the planner lands its pieces on the words that say them
        script = copy.deepcopy(SCRIPT)
        script["lines"][4]["viz"] = {"type": "chat", "messages": [{"role": "user", "text": "Which passages?"},
                                                                  {"role": "assistant", "text": "The answer from them"}]}
        script["lines"][5]["viz"] = {"type": "jiggle-delete", "tiles": [{"label": "Budgeting"}, {"label": "Risk", "at": "risk"},
                                                                        {"label": "Capital"}]}
        script["lines"][2]["viz"] = {"type": "gravity-drop", "items": ["saved", "year"]}
        _, sb, words = self.plan(script)
        said = lambda a: words[int(a.split(":")[1])]["text"]
        chat = next(s for s in sb["scenes"] if s["type"] == "chat")
        self.assertEqual([said(m["at"]) for m in chat["messages"]], ["passages", "answer"])
        jd = next(s for s in sb["scenes"] if s["type"] == "jiggle-delete")
        self.assertEqual([("at" in t) for t in jd["tiles"]], [False, True, False])     # only the tile that goes away
        self.assertEqual(said(jd["tiles"][1]["at"]), "risk.")
        script["lines"][2]["viz"] = {"type": "gravity-drop", "items": [{"text": "Cash", "at": "year"}, "saved"]}
        _, sb2, _ = self.plan(script)
        gd2 = next(s for s in sb2["scenes"] if s["type"] == "gravity-drop")
        self.assertEqual(said(gd2["items"][0]["at"]), "year.")         # an "at" written as a word is kept
        gd = next(s for s in sb["scenes"] if s["type"] == "gravity-drop")
        self.assertEqual([said(i["at"]) for i in gd["items"]], ["saved", "year."])
        self.assertTrue(all("text" in i for i in gd["items"]))

    def test_the_grounds_change_with_the_story(self):
        # the hook on the dark ground, the payoff on blue, light grounds between (the reference's rhythm)
        script = dict(copy.deepcopy(SCRIPT), payoff="l4")
        _, sb, _ = self.plan(script)
        self.assertEqual(sb["scenes"][0]["bg"], "ink")
        self.assertEqual([s for s in sb["scenes"] if s["id"].startswith("l4")][0]["bg"], "blue")
        self.assertIn(sb["scenes"][1]["bg"], ("mantle", "base"))

    def test_the_payoff_chimes_and_the_brand_carries_over(self):
        script = dict(copy.deepcopy(SCRIPT), payoff="l4", brand={"handle": "@harshil", "part": 1})
        d, sb, _ = self.plan(script)
        payoff = [s for s in sb["scenes"] if s["id"].startswith("l4")]
        self.assertTrue(payoff[0].get("chime"))
        self.assertEqual(sum(bool(s.get("chime")) for s in sb["scenes"]), 1)
        self.assertEqual(sb["brand"], {"handle": "@harshil", "part": 1})

    def test_an_item_not_spoken_is_spread_evenly(self):
        _, sb, words = self.plan()
        stack = next(s for s in sb["scenes"] if s["type"] == "stack")
        idx = [int(it["at"].split(":")[1]) for it in stack["items"]]
        self.assertEqual((words[idx[0]]["text"], words[idx[2]]["text"]), ("cost", "risk."))
        self.assertEqual(idx[1], (idx[0] + idx[2]) // 2)                 # "Valuation" is never said: halfway between its neighbours
        self.assertTrue(all(words[i]["line"] == "l5" for i in idx))

    def test_rules_without_a_hint(self):
        _, sb, _ = self.plan()
        cu = next(s for s in sb["scenes"] if s["type"] == "count-up")
        self.assertEqual((cu["value"], cu["prefix"], cu["source"]), (1000.0, "$", "s1"))
        num = next(s for s in sb["scenes"] if s["type"] == "number")
        self.assertEqual(num["n"], 2)
        long_line = [s for s in sb["scenes"] if s["id"].startswith("l4")]
        self.assertGreaterEqual(len(long_line), 2)                       # 16 words, 5.6 s: split into beats
        self.assertTrue(any("passages" in s.get("text", "").lower() for s in long_line))
        self.assertEqual(sb["scenes"][0]["bg"], "ink")                     # the hook on the dark ground
        self.assertEqual(next(s for s in sb["scenes"] if s["id"].startswith("l2"))["bg"], "base")   # after the section break
        self.assertIn("passages", sb["captions"]["emphasis"])

    def test_a_line_can_hold_several_pictures(self):
        # a long line gets two scenes: the second starts on its "from" word, and its items land only on its own words
        script = copy.deepcopy(SCRIPT)
        script["lines"][4]["viz"] = [{"type": "title", "text": "Read first"},
                                     {"type": "list-cards", "from": "writes", "items": ["Answer", "Guessing"]}]
        _, sb, words = self.plan(script)
        mine = [s for s in sb["scenes"] if s["id"].startswith("l4")]
        self.assertEqual([s["type"] for s in mine], ["title", "list-cards"])
        start = int(mine[1]["in"].split(":")[1])
        self.assertEqual(words[start]["text"], "writes")
        self.assertEqual(mine[0]["out"], mine[1]["in"])
        idx = [int(it["at"].split(":")[1]) for it in mine[1]["items"]]
        self.assertEqual([words[i]["text"] for i in idx], ["answer", "guessing"])
        self.assertNotIn("from", mine[1])

    def test_a_known_brand_gets_its_logo(self):
        script = copy.deepcopy(SCRIPT)
        script["lines"][3] = {"id": "l3", "show": "Start with the free Coursera course."}
        d = scratch(self)
        v = stub_vendor(d)
        write(os.path.join(v, "simple-icons", "icons", "coursera.svg"), "<svg></svg>")
        write(os.path.join(d, "script.json"), script)
        write(os.path.join(d, "transcript.json"), transcript(script))
        r = run("plan-storyboard.py", "--script", os.path.join(d, "script.json"), "--transcript", os.path.join(d, "transcript.json"),
                "--out", os.path.join(d, "storyboard.json"), "--vendor", v)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        logo = next(s for s in load(os.path.join(d, "storyboard.json"))["scenes"] if s["type"] == "logo-card")
        self.assertEqual(logo["logo"], "coursera")


class TitleRepeat(unittest.TestCase):
    def test_a_title_that_repeats_the_voice_warns(self):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        silent_wav(os.path.join(d, "voice.wav"), VOICE)
        board = copy.deepcopy(BOARD)
        board["scenes"][1] = {"type": "title", "id": "echo", "bg": "mantle", "in": "word:8", "out": "word:18", "text": "word8 word9 word10", "source": "s1"}
        sp = write(os.path.join(d, "storyboard.json"), board)
        r = run("explainer-compose.py", "--spec", sp, "--out", os.path.join(d, "public"))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARN echo: the title repeats what the voice is saying", r.stdout)
        self.assertNotIn("WARN hook", r.stdout)


if __name__ == "__main__":
    unittest.main()
