"""Calibration cases for group G, the 3D containers and round objects: briefcase, beaker, donut, coin, balance (make-cases.py loads
this file). The scene runs from word 1; its pieces land on word 2 and later."""



CASES = {
    "briefcase": [
        ("short", {"at": "word:2", "open": "word:4", "papers": 1}),
        ("mid", {"at": "word:2", "open": "word:4", "papers": 3, "label": "THE DEAL BOOK"}),
        ("long", {"at": "word:2", "open": "word:5", "papers": 5, "label": "EVERY MODEL IN ONE CASE"}),
    ],
    "beaker": [
        ("short", {"source": "s1", "layers": [{"label": "DEBT", "value": 60, "at": "word:2"}]}),
        ("mid", {"source": "s1", "layers": [{"label": "DEBT", "value": 60, "at": "word:2"}, {"label": "EQUITY", "value": 40, "at": "word:4"}]}),
        ("long", {"source": "s1", "layers": [{"label": "SENIOR", "value": 45, "at": "word:2", "text": "4.5x"},
                                              {"label": "MEZZANINE", "value": 15, "at": "word:4", "text": "1.5x"},
                                              {"label": "PREFERRED", "value": 8, "at": "word:5", "text": "0.8x"},
                                              {"label": "EQUITY", "value": 32, "at": "word:7", "text": "3.2x"}]}),
    ],
    "donut": [
        ("short", {"source": "s1", "slices": [{"label": "CASH", "value": 60, "at": "word:2"}, {"label": "STOCK", "value": 40, "at": "word:3"}]}),
        ("mid", {"source": "s1", "center": "$2,600M", "slices": [
            {"label": "STOCK", "value": 780, "text": "$780M", "at": "word:2"}, {"label": "CASH", "value": 1040, "text": "$1,040M", "at": "word:3"},
            {"label": "DEBT", "value": 780, "text": "$780M", "at": "word:4"}]}),
        ("long", {"source": "s1", "center": "100%", "slices": [
            {"label": "US", "value": 42, "text": "42%", "at": "word:2"}, {"label": "EUROPE", "value": 24, "text": "24%", "at": "word:3"},
            {"label": "ASIA", "value": 19, "text": "19%", "at": "word:4"}, {"label": "LATAM", "value": 9, "text": "9%", "at": "word:5"},
            {"label": "OTHER", "value": 6, "text": "6%", "at": "word:6"}]}),
    ],
    "coin": [
        ("short", {"text": "ROI", "at": "word:2"}),
        ("mid", {"text": "EPS", "dir": "up", "sub": "earnings per share", "at": "word:2"}),
        ("long", {"text": "WACC", "dir": "down", "sub": "the cost of capital", "at": "word:3"}),
    ],
    "balance": [
        ("short", {"left": {"label": "COST", "at": "word:2"}, "right": {"label": "VALUE", "at": "word:3"}}),
        ("mid", {"left": {"label": "RISK", "at": "word:2"}, "right": {"label": "RETURN", "at": "word:3"}, "tip": {"to": "right", "at": "word:5"},
                 "note": {"text": "WORTH IT", "at": "word:6"}}),
        ("long", {"left": {"label": "PURCHASE", "at": "word:2"}, "right": {"label": "SYNERGIES", "at": "word:4"},
                  "tip": {"to": "left", "at": "word:6"}, "note": {"text": "THE DEAL OVERPAYS BY FAR", "at": "word:7"}}),
    ],
}
