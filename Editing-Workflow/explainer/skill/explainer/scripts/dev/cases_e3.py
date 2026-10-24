"""Calibration cases for group E3, the editorial scenes: crossed-list, price-sticker, line-art (make-cases.py loads this
file). The scene runs from word 1; its items land on word 2 and later. A top-level "src" gets a placeholder PNG."""



CASES = {
    "crossed-list": [
        ("short", {"items": [{"text": "WIRES", "at": "word:2", "strike": "word:4"}, {"text": "CASE", "at": "word:5"}]}),
        ("mid", {"prefix": "NO", "items": [{"text": "CHARGING CASE", "at": "word:2", "strike": "word:4"},
                                           {"text": "BATTERY", "at": "word:5", "strike": "word:7"}, {"text": "CABLE", "at": "word:8"}]}),
        ("long", {"prefix": "NO MORE", "items": [{"text": "A CASE THAT NEEDS CHARGING", "at": "word:2", "strike": "word:4"},
                                                 {"text": "BATTERY", "at": "word:5"}, {"text": "TANGLED WIRES", "at": "word:7", "strike": "word:9"},
                                                 {"text": "PAIRING", "at": "word:10", "strike": "word:12"}]}),
    ],
    "price-sticker": [
        ("short", {"price": "$9", "at": "word:2", "source": "s"}),
        ("mid", {"price": "$99", "label": "FOR THE PAIR", "at": "word:2", "source": "s"}),
        ("long", {"price": "$1,299", "label": "BEFORE THE CHARGING CASE", "src": "product.png", "at": "word:3", "source": "s"}),
    ],
    "line-art": [
        ("short", {"icon": "book", "caption": "read it", "at": "word:2"}),
        ("mid", {"icon": "clock", "caption": "it takes an afternoon, seriously", "at": "word:2", "strike": "word:5"}),
        ("long", {"icon": "file-text", "caption": "the whole manual, every page of it, on one sheet you can fold away",
                  "at": "word:2", "strike": "word:6"}),
    ],
}
