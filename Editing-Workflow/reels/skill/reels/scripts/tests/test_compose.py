"""reels-compose.py: the vertical stage, the formats, the captions, the guards, and compatibility with the kit's checkers."""
import os, re, unittest
from .helpers import needs_kit, read, run, run_kit, scratch, words, write

SPOKEN = ("Stop@0.10 paying@0.40 for@0.70 editing.@0.95 Here@1.60 are@1.85 three@2.05 free@2.40 tools.@2.70 "
          "First@3.40 OBS@3.80 for@4.20 recording.@4.45 Then@5.20 Parakeet@5.50 for@6.00 words.@6.20 "
          "It@7.00 saved@7.20 me@7.50 $1,000@7.70 a@8.20 month.@8.35 Honestly@9.20 it's@9.60 free.@9.85")

ALL = {"id": "t", "duration": 12.0, "fps": 60,
       "captions": {"transcript": "transcript.json", "em": ["free"], "money": ["$1,000"]},
       "beats": [
           {"type": "hook", "id": "h1", "text": "Stop paying for editing", "em": [0, 1], "in": 0.0, "out": 1.5, "anchor": "-"},
           {"type": "steps", "id": "st", "title": "3 free tools", "items": [["OBS", 3.6], ["Parakeet", 5.3]], "in": 3.3, "out": 6.8, "anchor": "first"},
           {"type": "logo", "id": "lg", "src": "img/obs.svg", "pop": 3.85, "in": 3.55, "out": 5.0, "anchor": "OBS", "pos": "mid"},
           {"type": "stat", "id": "sn", "value": 1000, "prefix": "$", "label": "saved a month", "color": "amber", "count_at": 7.5, "in": 7.45, "out": 9.0, "anchor": "$1,000"},
           {"type": "chip", "id": "ch", "text": "it's actually free", "em": [2, 3], "in": 9.4, "out": 11.0, "anchor": "it's free"},
           {"type": "pills", "id": "pl", "items": [["Free", 2.2], {"text": "No watermark", "at": 2.6, "tone": "amber", "anchor": "tools"}], "in": 1.9, "out": 3.2, "anchor": "three free"},
           {"type": "point", "id": "pt", "text": "Step 2", "sub": "Transcribe", "in": 5.0, "out": 6.6, "anchor": "then", "pos": "low"},
           {"type": "clip", "id": "c1", "src": "broll/desk.mp4", "label": "Real footage", "in": 1.4, "out": 1.9, "anchor": "here are"},
           {"type": "image", "id": "im", "src": "img/page.png", "in": 6.7, "out": 7.4, "anchor": "it saved"}],
       "camera": [["set", 0, 1.0], ["punch", 7.6, 1.18], ["release", 8.6, 0.5]],
       "sounds": [{"src": "sfx/click.mp3", "at": 4.0, "dur": 0.4, "volume": 0.28}]}


class ComposeReel(unittest.TestCase):
    def build(self, spec, transcript=SPOKEN):
        d = scratch(self)
        if transcript is not None:
            write(os.path.join(d, "transcript.json"), words(transcript))
        sp = write(os.path.join(d, "storyboard.json"), spec)
        r = run("reels-compose.py", "--spec", sp, "--out", os.path.join(d, "public"))
        page = read(os.path.join(d, "public", "index.html")) if r.returncode == 0 else ""
        return r, page, d

    def test_all_formats_build_vertical_at_60(self):
        r, page, _ = self.build(ALL)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('data-fps="60" data-width="1080" data-height="1920"', page)
        for needle in ('id="host-h1"', 'id="host-st"', 'id="st-i1" data-at="5.300" data-anchor="Parakeet"', 'id="host-lg"',
                       'id="host-sn"', 'id="host-ch"', 'id="pl-p1" data-at="2.600" data-anchor="tools"', 'id="host-pt"',
                       'class="cutaway-video clip" id="c1"', 'id="host-c1-over"', 'id="host-im"', 'id="sfx-pop-lg"', 'id="sfx-0"'):
            self.assertIn(needle, page)
        self.assertIn("$1,000", page)                                 # full digits in the final state
        self.assertIn("countUp('#sn-v', 1000.0", page)
        # found in a real render: an SVG logo without width/height collapsed inside a max-size-only <img>
        self.assertIn(".lg img { width:250px; height:240px; object-fit:contain;", page)

    def test_captions_layer_is_not_a_card(self):
        r, page, _ = self.build(ALL)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('class="clip cap-layer" id="captions"', page)
        self.assertNotRegex(page, r'class="card-host[^"]*"[^>]*id="captions"')
        n = len(re.findall(r'class="cap" id="cap\d+"', page))
        self.assertGreaterEqual(n, 8)
        self.assertRegex(page, r'class="cw money" id="cw\d+-\d+">\$1,000<')
        self.assertRegex(page, r'class="cw em" id="cw\d+-\d+">free<')
        self.assertIn("tl.set('#cap0', { visibility: 'visible' }, 0.100);", page)

    def test_captions_off_range(self):
        spec = dict(ALL, captions={"transcript": "transcript.json", "off": [[0.0, 1.5]]})
        r, page, _ = self.build(spec)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotRegex(page, r'class="cw[^"]*" id="cw\d+-\d+">Stop<')      # the hook still says it; the captions don't
        self.assertRegex(page, r'class="cw[^"]*" id="cw0-0">Here<')

    def test_caption_terms_and_replacements(self):
        spec = dict(ALL, captions={"transcript": "transcript.json", "terms": ["OBS"], "replace": {"parakeet": "Parakeet!"}})
        r, page, _ = self.build(spec, transcript=SPOKEN.replace("OBS@3.80", "obs@3.80"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(page, r'id="cw\d+-\d+">OBS<')
        self.assertRegex(page, r'id="cw\d+-\d+">Parakeet!<')

    def test_captions_need_the_transcript(self):
        r, _, _ = self.build(ALL, transcript=None)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("captions need the transcript", r.stderr)
        r, page, _ = self.build(dict(ALL, captions=False), transcript=None)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn('id="captions"', page)

    def test_everything_inside_the_safe_zone(self):
        r, page, _ = self.build(ALL)
        self.assertEqual(r.returncode, 0, r.stderr)
        for left, top, width in re.findall(r'class="box" style="left:(\d+)px;top:(\d+)px;width:(\d+)px"', page):
            left, top, width = int(left), int(top), int(width)
            self.assertGreaterEqual(left, 65); self.assertGreaterEqual(top, 269); self.assertLessEqual(left + width, 1015)

    def test_a_block_past_the_safe_zone_fails(self):
        many = {"type": "steps", "id": "st", "title": "Five", "items": [["One", 1], ["Two", 2], ["Three", 3], ["Four", 4], ["Five", 5]],
                "in": 0.5, "out": 6, "anchor": "-", "pos": "low"}
        r, _, _ = self.build(dict(ALL, beats=[many], captions=False), transcript=None)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("past the safe zone", r.stderr)

    def test_wrapped_text_is_measured_at_the_column_it_gets(self):
        # 3 lines at the wide width, 4 in the narrow column it moves to below y 960: it must not slip past the safe bottom
        long = {"type": "headline", "id": "hd", "text": "x" * 40, "size": 112, "pos": "low", "in": 0.2, "out": 2.0, "anchor": "-"}
        r, _, _ = self.build(dict(ALL, beats=[long], captions=False), transcript=None)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("past the safe zone", r.stderr)
        fits = dict(long, text="Two short lines here", size=84)
        r, page, _ = self.build(dict(ALL, beats=[fits], captions=False), transcript=None)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('class="box" style="left:150px;top:820px;width:780px"', page)

    def test_a_block_in_the_caption_slot_fails_while_captions_show(self):
        chip = {"type": "chip", "id": "ch", "text": "and that is the whole point of this video", "in": 3.3, "out": 6.0, "anchor": "-"}
        r, _, _ = self.build(dict(ALL, beats=[chip]))
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("inside the caption slot", r.stderr)
        r, _, _ = self.build(dict(ALL, beats=[chip], captions={"transcript": "transcript.json", "off": [[3.3, 6.0]]}))
        self.assertEqual(r.returncode, 0, r.stderr)     # captions switched off over the beat: no clash
        r, _, _ = self.build(dict(ALL, beats=[dict(chip, text="it's free")]))
        self.assertEqual(r.returncode, 0, r.stderr)     # a short chip stays above the slot

    def test_block_heights_match_what_the_browser_draws(self):
        # heights measured in Chromium: a pill is 121 px (it was counted as 100), so four pills at mid reach y 1124 and
        # sit in the caption slot (from y 1050) while captions show
        pills = {"type": "pills", "id": "pl", "pos": "mid", "in": 1.9, "out": 3.2, "anchor": "-",
                 "items": [["One", 2.0], ["Two", 2.2], ["Three", 2.4], ["Four", 2.6]]}
        r, _, _ = self.build(dict(ALL, beats=[pills]))
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("inside the caption slot", r.stderr)
        # a number never wraps: $1,000,000 at 150 px is ~828 px, wider than the narrow 780 px column a low block gets
        stat = {"type": "stat", "id": "sn", "value": 1000000, "prefix": "$", "label": "saved", "pos": "low", "in": 0.2, "out": 2.0, "anchor": "-"}
        r, _, _ = self.build(dict(ALL, beats=[stat], captions=False), transcript=None)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("wider than the 780 px column", r.stderr)
        # a pill never wraps either
        long_pill = dict(pills, pos="low", items=[["A really long pill label here", 2.0], ["Two", 2.2]])
        r, _, _ = self.build(dict(ALL, beats=[long_pill], captions=False), transcript=None)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("wider than the 780 px column", r.stderr)
        # and what fits still builds
        r, _, _ = self.build(dict(ALL, beats=[dict(stat, value=1000, pos="mid")], captions=False), transcript=None)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_composition_id_is_escaped_for_each_context(self):
        # the browser decodes the attribute ("Q&amp;A" -> "Q&A") but not script text: the timeline key must be the decoded id
        r, page, _ = self.build(dict(ALL, id='Q&A "reel"', captions=False), transcript=None)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('data-composition-id="Q&amp;A &quot;reel&quot;"', page)
        self.assertIn('window.__timelines["Q&A \\"reel\\""] = tl;', page)

    def test_captions_true_means_the_defaults(self):
        r, page, _ = self.build(dict(ALL, captions=True))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('id="captions"', page)
        r, _, _ = self.build(dict(ALL, captions="yes"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('"captions" is an object of settings', r.stderr)

    def test_guards(self):
        cases = [
            ({"type": "hook", "id": "h", "text": "x" * 61, "in": 0, "out": 1, "anchor": "-"}, "keep it under 60"),
            ({"type": "zoom", "id": "z", "in": 0, "out": 1, "anchor": "-"}, "unknown beat type 'zoom'"),
            ({"type": "chip", "id": "c", "text": "hi", "in": 0, "out": 1}, "every beat needs an anchor"),
            ({"type": "chip", "id": "c", "text": "hi", "in": 2, "out": 1, "anchor": "-"}, "must satisfy"),
            ({"type": "point", "id": "p", "text": "x", "in": 0, "out": 1, "anchor": "-", "pos": "side"}, "unknown pos 'side'"),
            ({"type": "chip", "id": "1h", "text": "hi", "in": 0, "out": 1, "anchor": "-"}, "starts with a letter"),
            ({"type": "chip", "id": 'a"b', "text": "hi", "in": 0, "out": 1, "anchor": "-"}, "starts with a letter"),
        ]
        for beat, msg in cases:
            r, _, _ = self.build(dict(ALL, beats=[beat], captions=False), transcript=None)
            self.assertNotEqual(r.returncode, 0, beat)
            self.assertIn(msg, r.stderr, beat)
        r, _, _ = self.build(dict(ALL, beats=[], captions=False, camera=[["punch", 1.0, 1.8]]), transcript=None)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("is over 1.6", r.stderr)

    def test_late_first_beat_warns(self):
        spec = dict(ALL, captions=False, beats=[{"type": "chip", "id": "c", "text": "hi", "in": 2.0, "out": 3.0, "anchor": "-"}])
        r, _, _ = self.build(spec, transcript=None)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("nothing lands in the first 0.5 s", r.stdout)

    @needs_kit
    def test_kit_beat_check_passes_on_a_reel(self):
        r, _, d = self.build(ALL)
        self.assertEqual(r.returncode, 0, r.stderr)
        bc = run_kit("beat-check.py", "--index", os.path.join(d, "public", "index.html"), "--transcript", os.path.join(d, "transcript.json"))
        self.assertEqual(bc.returncode, 0, bc.stdout + bc.stderr)
        self.assertIn("staleness not checked", bc.stdout)

    @needs_kit
    def test_kit_gap_scan_reads_a_reel(self):
        r, _, d = self.build(ALL)
        self.assertEqual(r.returncode, 0, r.stderr)
        gs = run_kit("gap-scan.py", "--index", os.path.join(d, "public", "index.html"), "--early", "6", "--body", "6", "--max", "8")
        self.assertIn("camera move(s)", gs.stdout)
        self.assertNotIn("Traceback", gs.stderr)

    @needs_kit
    def test_kit_gap_scan_sees_a_static_captioned_reel(self):
        # captions on for 12 s and one 1 s chip: the caption layer must not count as covering the reel (gate G9)
        spec = dict(ALL, beats=[{"type": "chip", "id": "ch", "text": "hi", "in": 0.2, "out": 1.2, "anchor": "-"}], camera=[], sounds=[])
        r, _, d = self.build(spec)
        self.assertEqual(r.returncode, 0, r.stderr)
        gs = run_kit("gap-scan.py", "--index", os.path.join(d, "public", "index.html"), "--early", "4", "--body", "6", "--max", "8")
        self.assertEqual(gs.returncode, 1, gs.stdout)
        self.assertIn("1 overlay(s)", gs.stdout)


if __name__ == "__main__":
    unittest.main()
