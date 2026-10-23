"""Calibration cases for group F, the 3D box scenes: bars-3d, cube, cards-3d (make-cases.py loads this file). The scene
runs from word 1; its pieces land on word 2 and later."""


def at(i):
    return "word:%d" % i


CASES = {
    "bars-3d": [
        ("short", {"source": "s1", "bars": [{"label": "LBO", "value": 100, "at": at(2)}, {"label": "DCF", "value": 40, "at": at(3)}]}),
        ("mid", {"source": "s1", "floor": "THREE-STATEMENT MODEL", "bars": [
            {"label": "MERGER", "value": 60, "at": at(2)}, {"label": "LBO", "value": 100, "at": at(4)},
            {"label": "DCF", "value": 35, "at": at(6)}]}),
        ("long", {"source": "s1", "floor": "WHAT BANKS BUILD", "bars": [
            {"label": "COMPS", "value": 30, "at": at(2), "text": "30%"}, {"label": "MERGER", "value": 55, "at": at(3), "text": "55%"},
            {"label": "LBO", "value": 100, "at": at(5), "text": "100%"}, {"label": "BUDGET", "value": 20, "at": at(6), "text": "20%"}]}),
    ],
    "cube": [
        ("short", {"at": at(2)}),
        ("mid", {"at": at(2), "turns": [{"dir": "left", "at": at(4)}], "highlight": {"cell": "B2", "at": at(6)}}),
        ("long", {"at": at(2), "labels": ["IS", "BS", "CF", "DCF", "LBO", "M&A", "EPS", "WAC", "IRR"],
                  "turns": [{"dir": "right", "at": at(3)}, {"dir": "up", "at": at(5)}], "twist": [{"dir": "left", "at": at(7)}],
                  "highlight": {"cell": "LBO", "at": at(9)}}),
    ],
    "cards-3d": [
        ("short", {"cards": [{"text": "1", "at": at(2)}]}),
        ("mid", {"cards": [{"text": "1", "at": at(2)}, {"text": "2", "at": at(3)}, {"text": "3", "at": at(4)}]}),
        ("long", {"cards": [{"text": "A", "sub": "the inputs", "at": at(2)}, {"text": "B", "sub": "the model", "at": at(3)},
                            {"text": "C", "sub": "the outputs", "at": at(4)}, {"text": "D", "sub": "the decision", "at": at(5)}]}),
    ],
}
