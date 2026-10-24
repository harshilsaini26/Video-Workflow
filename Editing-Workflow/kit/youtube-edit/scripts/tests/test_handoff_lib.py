"""handoff_lib: what every hand-off shares. Overlapping clips go to another lane instead of failing the hand-off; a
failed run leaves the creator's last edit/ exactly as it was; the layer clips are hard-linked, not copied twice."""
import os, unittest
from .helpers import scratch, write


class Lib(unittest.TestCase):
    def test_place_moves_an_overlap_to_a_new_lane(self):
        import nle_xml as X, handoff_lib as H
        d = scratch(self)
        a = write(os.path.join(d, "a.mov"), "x")
        tl = X.Timeline("t", 1080, 1920, 60)
        lanes = [tl.video_track("cards")]
        H.place(tl, lanes, a, 0.0, 2.0, duration=2, name="c1")
        H.place(tl, lanes, a, 1.4, 3.0, duration=2, name="c2")
        H.place(tl, lanes, a, 2.5, 4.0, duration=2, name="c3")
        self.assertEqual([t.name for t in lanes], ["cards", "cards 2"])
        self.assertEqual([[c["name"] for c in t.clips] for t in lanes], [["c1", "c3"], ["c2"]])
        self.assertEqual(tl.validate(), [])

    def test_staged_restores_the_last_edit_on_failure(self):
        import handoff_lib as H
        d = scratch(self)
        edit = os.path.join(d, "edit")
        write(os.path.join(edit, "p.xml"), "the creator's")
        with self.assertRaises(H.HandoffError) as e:
            with H.staged(edit):
                write(os.path.join(edit, "half.xml"), "partial")
                raise ValueError("bad cut-list.json")
        self.assertIn("bad cut-list.json", str(e.exception))
        self.assertEqual(sorted(os.listdir(d)), ["edit"])
        self.assertEqual(os.listdir(edit), ["p.xml"])
        with H.staged(edit) as aside:
            write(os.path.join(edit, "new.xml"), "new")
        self.assertTrue(aside.endswith("edit.v1"))
        self.assertTrue(os.path.isfile(os.path.join(d, "edit.v1", "p.xml")))

    def test_link_or_copy_shares_the_file(self):
        import handoff_lib as H
        d = scratch(self)
        a = write(os.path.join(d, "layers", "l0.mov"), "x" * 100)
        b = H.link_or_copy(a, os.path.join(d, "edit", "gfx", "l0.mov"))
        self.assertEqual(os.stat(a).st_ino, os.stat(b).st_ino)


if __name__ == "__main__":
    unittest.main()
