"""Calibration cases for group E2, the sound scenes: waveform and mode-switch (make-cases.py loads this file). The
scene runs from word 1; its items land on word 2 and later. The line-chart's step shape has the line's height (only the
path differs), and make-cases keeps one group per type, so its cases stay in make-cases.py and the step is tested in
tests/test_scenes_e2.py."""



CASES = {
    "waveform": [
        ("short", {"states": [{"kind": "noise", "label": "NOISE", "at": "word:2"}]}),
        ("mid", {"color": "accent", "states": [{"kind": "noise", "label": "THE STREET", "at": "word:2"},
                                               {"kind": "calm", "label": "NOISE CANCELLING ON", "at": "word:6"}]}),
        ("long", {"states": [{"kind": "noise", "label": "WHAT A BUSY STREET SOUNDS LIKE", "at": "word:2"},
                             {"kind": "calm", "label": "THE SAME STREET, CANCELLED", "at": "word:6"},
                             {"kind": "music", "label": "AND NOW ONLY THE MUSIC IS LEFT", "at": "word:10"},
                             {"kind": "pulse", "label": "A HEARTBEAT UNDER IT ALL", "at": "word:14"}]}),
        ("flat", {"color": "accent", "states": [{"kind": "flat", "label": "SILENCE", "at": "word:2"},
                                                {"kind": "pulse", "label": "ONE BEAT", "at": "word:5"}]}),
    ],
    "mode-switch": [
        ("short", {"options": [{"label": "ON", "wave": "calm", "note": "Quiet", "at": "word:2"},
                               {"label": "OFF", "wave": "noise", "note": "Loud", "at": "word:5"}]}),
        ("mid", {"options": [{"label": "QUIET", "wave": "calm", "note": "The street goes away", "at": "word:2"},
                             {"label": "AWARE", "wave": "noise", "note": "You hear the traffic again", "at": "word:6"},
                             {"label": "IMMERSE", "wave": "music", "note": "Just the music, all around you", "at": "word:10"}]}),
        ("long", {"options": [{"label": "QUIET", "wave": "calm", "note": "The whole street goes away, even the buses going past", "at": "word:2"},
                              {"label": "AWARE", "wave": "noise", "note": "You hear the traffic and the people around you again", "at": "word:6"},
                              {"label": "IMMERSIVE", "wave": "music", "note": "Only the music is left, and it comes from all around you", "at": "word:10"},
                              {"label": "FOCUS", "wave": "pulse", "note": "Just your own heartbeat while you work", "at": "word:14"}]}),
    ],
}
