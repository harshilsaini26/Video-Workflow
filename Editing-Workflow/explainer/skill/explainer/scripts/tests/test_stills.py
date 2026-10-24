"""Checkpoint B's stills: every scene once it has settled, and a stage at each of its beats, each still taken inside its
own scene (stills.plan, no browser needed)."""
import importlib.util, os, unittest
from .helpers import SCRIPTS


def stills():
    spec = importlib.util.spec_from_file_location("stills", os.path.join(SCRIPTS, "stills.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOMENTS = {"duration": 20.0, "scenes": [
    {"id": "hook", "type": "title", "in": 0.0, "out": 3.0},
    {"id": "st", "type": "stage", "in": 3.0, "out": 15.0, "beats": [3.4, 6.0, 9.0, 12.0]},
    {"id": "end", "type": "title", "in": 15.0, "out": 20.0}]}


class Plan(unittest.TestCase):
    def test_every_still_is_inside_its_own_scene_and_a_stage_shows_each_beat(self):
        shots, rows = stills().plan(MOMENTS, "/out")
        span = {s["id"]: (s["in"], s["out"]) for s in MOMENTS["scenes"]}
        for (name, t, sid, _), shot in zip(rows, shots):
            self.assertTrue(span[sid][0] <= t <= span[sid][1], (name, t, sid))
            self.assertEqual(shot["t"], t)
        per = {sid: sum(1 for r in rows if r[2] == sid and not r[0].startswith("hook-")) for sid in span}
        self.assertEqual(per, {"hook": 1, "st": 4, "end": 1})         # the stage before beats 6, 9 and 12, and settled
        names = [r[0] for r in rows]
        self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
