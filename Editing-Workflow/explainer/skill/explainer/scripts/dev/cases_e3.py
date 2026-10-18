"""Calibration cases for group E3, the editorial scenes: crossed-list, price-sticker, line-art (make-cases.py loads this
file). The scene runs from word 1; its items land on word 2 and later. A top-level "src" gets a placeholder PNG."""


def at(i):
    return "word:%d" % i


CASES = {
    "crossed-list": [
        ("short", {"items": [{"text": "WIRES", "at": at(2), "strike": at(4)}, {"text": "CASE", "at": at(5)}]}),
        ("mid", {"prefix": "NO", "items": [{"text": "CHARGING CASE", "at": at(2), "strike": at(4)},
                                           {"text": "BATTERY", "at": at(5), "strike": at(7)}, {"text": "CABLE", "at": at(8)}]}),
        ("long", {"prefix": "NO MORE", "items": [{"text": "A CASE THAT NEEDS CHARGING", "at": at(2), "strike": at(4)},
                                                 {"text": "BATTERY", "at": at(5)}, {"text": "TANGLED WIRES", "at": at(7), "strike": at(9)},
                                                 {"text": "PAIRING", "at": at(10), "strike": at(12)}]}),
    ],
    "price-sticker": [
        ("short", {"price": "$9", "at": at(2), "source": "s"}),
        ("mid", {"price": "$99", "label": "FOR THE PAIR", "at": at(2), "source": "s"}),
        ("long", {"price": "$1,299", "label": "BEFORE THE CHARGING CASE", "src": "product.png", "at": at(3), "source": "s"}),
    ],
    "line-art": [
        ("short", {"icon": "book", "caption": "read it", "at": at(2)}),
        ("mid", {"icon": "clock", "caption": "it takes an afternoon, seriously", "at": at(2), "strike": at(5)}),
        ("long", {"icon": "file-text", "caption": "the whole manual, every page of it, on one sheet you can fold away",
                  "at": at(2), "strike": at(6)}),
    ],
}
