"""Calibration cases for group I, the three film grammars (huashu-art-motion, MIT): 3Blue1Brown's morph, Kurzgesagt's
orbit and Vox's clippings (make-cases.py loads this file). The scene runs from word 1; its pieces land on word 2 and
later, 0.4 s apart."""

DIGIT = [0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0]

CASES = {
    "morph": [
        ("short", {"n": 4, "steps": [{"form": "row", "at": "word:2"}, {"form": "merge", "at": "word:6"}]}),
        ("mid", {"n": 16, "values": [0.2 + 0.8 * v for v in DIGIT],
                 "steps": [{"form": "grid", "at": "word:2", "label": "Pixels"}, {"form": "column", "at": "word:6", "label": "Input neurons", "color": "accent2"},
                           {"form": "merge", "at": "word:10", "label": "One weighted sum"}]}),
        ("long", {"n": 36, "steps": [{"form": "grid", "at": "word:2", "label": "Thirty-six pixels"},
                                     {"form": "bars", "at": "word:6", "label": "How bright each one is", "heights": [((k * 7) % 10) / 10.0 + 0.05 for k in range(36)]},
                                     {"form": "ring", "at": "word:10", "label": "A ring of neurons"}, {"form": "merge", "at": "word:14", "label": "One output"}],
                  "indicate": {"piece": 3, "at": "word:18"}}),
    ],
    "orbit": [
        ("short", {"center": "A cell", "nodes": [{"text": "Nucleus", "at": "word:2"}]}),
        ("mid", {"center": "A drop of sea water", "nodes": [{"text": "Plankton", "at": "word:2"}, {"text": "Salt", "at": "word:3"},
                                                            {"text": "Bacteria", "at": "word:4"}]}),
        ("long", {"center": "The immune system", "shape": "rounded",
                  "nodes": [{"text": "Macrophages", "at": "word:2"}, {"text": "Neutrophils", "at": "word:3"},
                            {"text": "T cells", "at": "word:4"}, {"text": "Antibodies", "at": "word:5"}],
                  "dive": {"into": 2, "at": "word:7", "center": "One T cell", "shape": "hex",
                           "nodes": [{"text": "Receptors", "at": "word:13"}, {"text": "Signals", "at": "word:14"},
                                     {"text": "Memory", "at": "word:15"}, {"text": "Killer mode", "at": "word:16"}]}}),
    ],
    "clippings": [
        ("short", {"items": [{"kind": "label", "text": "The lab", "at": "word:2"}]}),
        ("mid", {"source": "s", "items": [{"kind": "clipping", "head": "A computer learns to see cats",
                                           "lines": ["1,000 machines, 16,000 cores", "Ten million video frames", "No labels at all"], "at": "word:2"},
                                          {"kind": "print", "src": "desk-800x560.png", "credit": "Photo: the creator", "label": "The lab",
                                           "halftone": True, "at": "word:6"},
                                          {"kind": "label", "text": "2012 · Google", "at": "word:10"}],
                 "marks": [{"kind": "highlight", "item": 0, "line": 1, "at": "word:4"}, {"kind": "circle", "item": 2, "at": "word:12"}]}),
        ("long", {"items": [{"kind": "clipping", "head": "The night the market forgot how to price risk, again",
                             "lines": ["Banks held the loans for weeks", "Nobody priced the default", "The rating stayed where it was",
                                       "Then the whole desk went quiet"], "at": "word:2"},
                            {"kind": "note", "text": "Who checked the numbers on the loans before they were sold?", "at": "word:8"}],
                  "marks": [{"kind": "highlight", "item": 0, "line": 2, "at": "word:4"}, {"kind": "underline", "item": 0, "line": 3, "at": "word:6"},
                            {"kind": "circle", "item": 1, "at": "word:11"}]}),
    ],
}
