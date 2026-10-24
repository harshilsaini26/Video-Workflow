"""Calibration cases for group H, the math scenes: plot, network, surface (make-cases.py loads this file). The scene runs
from word 1; its pieces land on word 2 and later."""



CASES = {
    "plot": [
        ("short", {"panels": [{"from": 0.9, "min": 0.1}], "descend": "word:3"}),
        ("mid", {"x": "w", "y": "L", "tangent": "word:2", "descend": "word:4",
                 "panels": [{"from": 0.9, "min": 0.1}, {"from": -0.7, "min": 0.3}, {"from": 0.5, "min": -0.4}, {"from": -0.9, "min": 0.0}]}),
        ("long", {"x": "w", "y": "L", "tangent": "word:2", "descend": "word:5",
                  "panels": [{"from": 0.9, "min": 0.1}, {"from": -0.7, "min": 0.3}, {"from": 0.5, "min": -0.4},
                             {"from": -0.9, "min": 0.0}, {"from": 0.2, "min": -0.6}, {"from": -0.3, "min": 0.7}]}),
    ],
    "network": [
        ("short", {"layers": [3, 4, 2], "forward": "word:2"}),
        ("mid", {"layers": [4, 6, 6, 10], "labels": [str(d) for d in range(10)], "input": {"digit": 3, "at": "word:2"},
                 "forward": "word:3", "answer": {"node": 8, "at": "word:5"}}),
        ("long", {"layers": [5, 8, 8, 8, 10], "labels": [str(d) for d in range(10)], "input": {"digit": 7, "at": "word:2"},
                  "forward": "word:3", "answer": {"node": 7, "at": "word:5"}, "backward": "word:7"}),
    ],
    "surface": [
        ("short", {"descend": {"at": "word:2", "steps": 3}}),
        ("mid", {"label": "LOSS", "descend": {"at": "word:2", "steps": 6}}),
        ("long", {"label": "THE LOSS SURFACE", "start": [0.65, -0.6], "lr": 0.3, "descend": {"at": "word:3", "steps": 10}}),
    ],
    "stage": [
        ("short", {"objects": [{"id": "net", "scene": {"type": "network", "layers": [3, 4, 2], "forward": "word:2"}, "box": [175, 0, 600]}]}),
        ("mid", {"objects": [
            {"id": "eq", "scene": {"type": "formula", "tex": "e = \\hat{y} - y"}, "box": [175, 0, 600], "out": "word:4"},
            {"id": "net", "scene": {"type": "network", "layers": [4, 6, 6, 10], "forward": "word:2"}, "box": [175, 200, 600]}],
                 "moves": [{"obj": "net", "at": "word:4", "box": [0, 0, 300]}]}),
        ("long", {"objects": [
            {"id": "eq", "scene": {"type": "formula", "tex": "w \\leftarrow w - \\eta \\nabla L"}, "box": [175, 0, 600]},
            {"id": "net", "scene": {"type": "network", "layers": [4, 6, 6, 10], "forward": "word:2"}, "box": [100, 190, 680], "out": "word:5"},
            {"id": "pl", "scene": {"type": "plot", "descend": "word:6", "panels": [{"from": 0.9, "min": 0.1}, {"from": -0.7, "min": 0.3}]},
             "box": [225, 230, 640], "in": "word:5"}]}),
    ],
    "outputs": [
        ("short", {"labels": ["YES", "NO"], "guess": [0.3, 0.7], "at": "word:2"}),
        ("mid", {"labels": [str(d) for d in range(10)], "guess": [0.1, 0.05, 0.2, 0.15, 0.1, 0.1, 0.15, 0.1, 0.6, 0.25], "at": "word:2",
                 "target": {"row": 3, "at": "word:3"}, "error": "word:4"}),
        ("long", {"labels": [str(d) for d in range(10)], "guess": [0.1, 0.05, 0.2, 0.15, 0.1, 0.1, 0.15, 0.1, 0.6, 0.25], "at": "word:2",
                  "target": {"row": 3, "at": "word:3"}, "error": "word:4", "loss": "word:5"}),
    ],
}
