"""Tests for the Reels scripts. Synthetic fixtures only.

Run from the scripts folder:  python3 -m unittest tests      (-v for names)
The ffmpeg tests skip themselves when ffmpeg / ffprobe are not on PATH; the kit-compatibility tests skip themselves when
the kit's youtube-edit scripts can't be found (installed side by side, or in this repository).
"""
import os


def load_tests(loader, standard_tests, pattern):   # lets `python -m unittest tests` find every tests/test_*.py
    here = os.path.dirname(os.path.abspath(__file__))
    standard_tests.addTests(loader.discover(start_dir=here, pattern=pattern or "test*.py", top_level_dir=os.path.dirname(here)))
    return standard_tests
