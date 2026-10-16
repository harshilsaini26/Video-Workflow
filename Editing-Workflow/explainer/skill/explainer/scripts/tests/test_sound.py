"""The sound bed: a pad (generated here) or the creator's music, looped to the reel, ducked under the voice, with a whoosh
at every moving transition and a pop as items land, so the reel never drops to silence between lines."""
import array, copy, math, os, re, subprocess, unittest, wave
from .helpers import needs_ffmpeg, read, run, scratch, write
from .test_compose import BOARD, D, VOICE, silent_wav, words30
import sound


def tone_wav(path, seconds, start, end, rate=48000):
    """A voice stand-in: silence with a 440 Hz tone from start to end."""
    data = array.array("h", [int(16000 * math.sin(2 * math.pi * 440 * i / rate)) if start <= i / rate < end else 0
                             for i in range(int(seconds * rate))])
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(data.tobytes())


def rms_db(path, a, b):
    """RMS level in dB (full scale) of a 16-bit WAV between a and b seconds."""
    with wave.open(path) as w:
        rate, ch = w.getframerate(), w.getnchannels()
        w.setpos(int(a * rate))
        data = array.array("h", w.readframes(int((b - a) * rate)))
    if not data:
        return -120.0
    r = math.sqrt(sum(x * x for x in data) / len(data)) / 32768.0
    return 20 * math.log10(r) if r > 0 else -120.0


@needs_ffmpeg
class Sound(unittest.TestCase):
    def build(self, board, voice=None):
        d = scratch(self)
        write(os.path.join(d, "transcript.json"), {"words": words30()})
        (voice or silent_wav)(os.path.join(d, "voice.wav"), VOICE)
        sp = write(os.path.join(d, "storyboard.json"), board)
        r = run("explainer-compose.py", "--spec", sp, "--out", os.path.join(d, "public"))
        return r, os.path.join(d, "public"), d

    def test_default_bed_is_written_and_played(self):
        r, out, _ = self.build(BOARD)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        bed = os.path.join(out, "bed.wav")
        with wave.open(bed) as w:
            self.assertEqual((w.getframerate(), w.getnchannels()), (48000, 2))
            self.assertAlmostEqual(w.getnframes() / 48000.0, D, delta=0.05)
        self.assertIn('<audio id="bed" src="bed.wav" data-start="0" data-duration="%.3f" data-track-index="40" data-volume="1">' % D,
                      read(os.path.join(out, "index.html")))
        quiet = [t / 4.0 for t in range(int(D * 4) - 1) if rms_db(bed, t / 4.0, t / 4.0 + 0.25) < -50]
        self.assertEqual(quiet, [], "silent stretches in the bed")

    def test_music_ducks_under_the_voice(self):
        r, out, _ = self.build(BOARD, voice=lambda p, s: tone_wav(p, s, 2.0, 4.0))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        bed = os.path.join(out, "bed.wav")
        board = copy.deepcopy(BOARD)
        board["sound"] = {"sfx": False}                       # the pad alone, so the comparison is only the ducking
        r, out, _ = self.build(board, voice=lambda p, s: tone_wav(p, s, 2.0, 4.0))
        bed = os.path.join(out, "bed.wav")
        self.assertGreaterEqual(rms_db(bed, 6.0, 7.0) - rms_db(bed, 2.5, 3.5), 6.0)

    def test_sound_effects_land_on_transitions_and_items(self):
        # a whoosh 0.12 s ahead of every moving transition; a pop as each item lands, but never two sounds within 0.35 s
        events = sound.events([("zoom", 3.1), ("wipe", 7.1), ("fade", 0.3)], [1.0, 1.2, 3.15, 5.0])
        self.assertEqual(events, [(1.0, "pop"), (2.98, "whoosh"), (5.0, "pop"), (6.98, "whoosh")])
        r, out, _ = self.build(dict(BOARD, sound={"music": "none", "sfx": False}))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertFalse(os.path.exists(os.path.join(out, "bed.wav")))
        self.assertNotIn('id="bed"', read(os.path.join(out, "index.html")))

    def test_the_creators_music_is_used_and_must_exist(self):
        r, _, d = self.build(dict(BOARD, sound={"music": "music/missing.mp3"}))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("music/missing.mp3", r.stdout)
        d = scratch(self)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=330:duration=3", "-ar", "44100",
                        os.path.join(d, "track.mp3")], check=True)
        out = sound.mix_bed(None, os.path.join(d, "track.mp3"), [], 8.0, os.path.join(d, "bed.wav"))
        self.assertGreater(rms_db(out, 5.0, 6.0), -60)        # looped past the track's 3 s (silence would read -120)
        self.assertLess(rms_db(out, 7.8, 8.0), rms_db(out, 5.0, 6.0) - 6)   # and faded out at the end

    def test_generated_sounds_are_the_same_every_time(self):
        a, b = scratch(self), scratch(self)
        pa, pb = sound.make_sfx(a), sound.make_sfx(b)
        for k in ("whoosh", "pop"):
            with open(pa[k], "rb") as f, open(pb[k], "rb") as g:
                self.assertEqual(f.read(), g.read(), k)
        self.assertEqual(open(sound.make_pad(os.path.join(a, "pad.wav")), "rb").read(),
                         open(sound.make_pad(os.path.join(b, "pad.wav")), "rb").read())


if __name__ == "__main__":
    unittest.main()
