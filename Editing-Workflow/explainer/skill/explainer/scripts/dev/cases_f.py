"""Calibration cases for group F, the 3D box scenes: bars-3d, cube, cards-3d (make-cases.py loads this file). The scene
runs from word 1; its pieces land on word 2 and later."""



CASES = {
    "bars-3d": [
        ("short", {"source": "s1", "bars": [{"label": "LBO", "value": 100, "at": "word:2"}, {"label": "DCF", "value": 40, "at": "word:3"}]}),
        ("mid", {"source": "s1", "floor": "THREE-STATEMENT MODEL", "bars": [
            {"label": "MERGER", "value": 60, "at": "word:2"}, {"label": "LBO", "value": 100, "at": "word:4"},
            {"label": "DCF", "value": 35, "at": "word:6"}]}),
        ("long", {"source": "s1", "floor": "WHAT BANKS BUILD", "bars": [
            {"label": "COMPS", "value": 30, "at": "word:2", "text": "30%"}, {"label": "MERGER", "value": 55, "at": "word:3", "text": "55%"},
            {"label": "LBO", "value": 100, "at": "word:5", "text": "100%"}, {"label": "BUDGET", "value": 20, "at": "word:6", "text": "20%"}]}),
    ],
    "cube": [
        ("short", {"at": "word:2"}),
        ("mid", {"at": "word:2", "turns": [{"dir": "left", "at": "word:4"}], "highlight": {"cell": "B2", "at": "word:6"}}),
        ("long", {"at": "word:2", "labels": ["IS", "BS", "CF", "DCF", "LBO", "M&A", "EPS", "WAC", "IRR"],
                  "turns": [{"dir": "right", "at": "word:3"}, {"dir": "up", "at": "word:5"}], "twist": [{"dir": "left", "at": "word:7"}],
                  "highlight": {"cell": "LBO", "at": "word:9"}}),
    ],
    "cards-3d": [
        ("short", {"cards": [{"text": "1", "at": "word:2"}]}),
        ("mid", {"cards": [{"text": "1", "at": "word:2"}, {"text": "2", "at": "word:3"}, {"text": "3", "at": "word:4"}]}),
        ("long", {"cards": [{"text": "A", "sub": "the inputs", "at": "word:2"}, {"text": "B", "sub": "the model", "at": "word:3"},
                            {"text": "C", "sub": "the outputs", "at": "word:4"}, {"text": "D", "sub": "the decision", "at": "word:5"}]}),
    ],
}
