"""Calibration cases for group G, the 3D containers and round objects: briefcase, beaker, donut, coin (make-cases.py loads
this file). The scene runs from word 1; its pieces land on word 2 and later."""


def at(i):
    return "word:%d" % i


CASES = {
    "briefcase": [
        ("short", {"at": at(2), "open": at(4), "papers": 1}),
        ("mid", {"at": at(2), "open": at(4), "papers": 3, "label": "THE DEAL BOOK"}),
        ("long", {"at": at(2), "open": at(5), "papers": 5, "label": "EVERY MODEL IN ONE CASE"}),
    ],
    "beaker": [
        ("short", {"source": "s1", "layers": [{"label": "DEBT", "value": 60, "at": at(2)}]}),
        ("mid", {"source": "s1", "layers": [{"label": "DEBT", "value": 60, "at": at(2)}, {"label": "EQUITY", "value": 40, "at": at(4)}]}),
        ("long", {"source": "s1", "layers": [{"label": "SENIOR", "value": 45, "at": at(2), "text": "4.5x"},
                                              {"label": "MEZZANINE", "value": 15, "at": at(4), "text": "1.5x"},
                                              {"label": "PREFERRED", "value": 8, "at": at(5), "text": "0.8x"},
                                              {"label": "EQUITY", "value": 32, "at": at(7), "text": "3.2x"}]}),
    ],
    "donut": [
        ("short", {"source": "s1", "slices": [{"label": "CASH", "value": 60, "at": at(2)}, {"label": "STOCK", "value": 40, "at": at(3)}]}),
        ("mid", {"source": "s1", "center": "$2,600M", "slices": [
            {"label": "STOCK", "value": 780, "text": "$780M", "at": at(2)}, {"label": "CASH", "value": 1040, "text": "$1,040M", "at": at(3)},
            {"label": "DEBT", "value": 780, "text": "$780M", "at": at(4)}]}),
        ("long", {"source": "s1", "center": "100%", "slices": [
            {"label": "US", "value": 42, "text": "42%", "at": at(2)}, {"label": "EUROPE", "value": 24, "text": "24%", "at": at(3)},
            {"label": "ASIA", "value": 19, "text": "19%", "at": at(4)}, {"label": "LATAM", "value": 9, "text": "9%", "at": at(5)},
            {"label": "OTHER", "value": 6, "text": "6%", "at": at(6)}]}),
    ],
    "coin": [
        ("short", {"text": "ROI", "at": at(2)}),
        ("mid", {"text": "EPS", "dir": "up", "sub": "earnings per share", "at": at(2)}),
        ("long", {"text": "WACC", "dir": "down", "sub": "the cost of capital", "at": at(3)}),
    ],
}
