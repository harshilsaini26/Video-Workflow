#!/usr/bin/env python3
"""make-cases.py: compose one page per calibration case, then turn Chromium's measurements into the height fixture.

  make-cases.py DIR --vendor VENDOR            # writes DIR/<case>/public/index.html and DIR/cases.json
  node measure-scenes.mjs DIR > measured.jsonl  # each case's .box height at 950 and 780 px
  make-cases.py DIR --merge measured.jsonl      # writes tests/fixtures/heights.json

Three text lengths per scene type (custom excluded: it brings its own box). A developer tool, not part of a video run.
"""
import argparse, json, os, struct, subprocess, sys, wave, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
FIXTURE = os.path.join(SCRIPTS, "tests", "fixtures", "heights.json")
WORDS = ["word%d" % i for i in range(40)]
D = 40 * 0.4 + 1.0


def at(i):
    return "word:%d" % i


def lengths(short, mid, long):
    return [("short", short), ("mid", mid), ("long", long)]


CASES = {
    "title": lengths({"text": "Three certificates"},
                     {"text": "Three certificates finance bros gatekeep", "kicker": "IF YOU'RE NEW TO FINANCE"},
                     {"text": "The three certificates that finance people quietly gatekeep from everyone new",
                      "kicker": "A LONG KICKER THAT RUNS OVER MORE THAN ONE LINE AT THIS SIZE", "size": 96}),
    "number": lengths({"n": 1}, {"n": 2, "name": "Coursera finance"},
                      {"n": 3, "name": "The Corporate Finance Institute's financial modelling certificate"}),
    "count-up": lengths({"value": 1000, "prefix": "$", "source": "s"}, {"value": 2.5, "decimals": 1, "suffix": "%", "sub": "a year", "source": "s"},
                        {"value": 25000, "prefix": "$", "sub": "the median starting salary for an analyst in New York", "source": "s"}),
    "list-cards": lengths({"items": [{"label": "Free", "at": at(2)}, {"label": "Fast", "at": at(4)}]},
                          {"items": [{"label": "Learn Excel first", "at": at(2)}, {"label": "Then the three statements", "at": at(4)},
                                     {"label": "Then valuation", "at": at(6)}]},
                          {"items": [{"label": "Start with the free Coursera course on corporate finance", "at": at(2)},
                                     {"label": "Model three companies you actually know well", "at": at(4)},
                                     {"label": "Write each one up as a one page memo", "at": at(6)}]}),
    "line-chart": lengths({"points": [1, 2], "x": ["A", "B"], "source": "s"},
                          {"points": [100, 114, 152, 214, 265], "x": ["Y0", "Y5", "Y10", "Y15", "Y20"], "prefix": "$", "label": "VALUE OF $100", "source": "s"},
                          {"points": [100, 140, 190, 260, 340, 480], "x": ["2019", "2020", "2021", "2022", "2023", "2024"], "prefix": "$",
                           "label": "WHAT ONE HUNDRED DOLLARS IN AN INDEX FUND BECAME OVER SIX YEARS", "source": "s"}),
    "bars": lengths({"rows": [{"label": "A", "value": 1, "at": at(2)}, {"label": "B", "value": 2, "at": at(4)}], "source": "s"},
                    {"rows": [{"label": "Coursera", "value": 40, "text": "$40", "at": at(2)}, {"label": "CFA", "value": 1000, "text": "$1,000", "hi": True, "at": at(4)},
                              {"label": "CPA", "value": 500, "text": "$500", "at": at(6)}], "source": "s"},
                    {"rows": [{"label": "The Coursera corporate finance specialisation", "value": 40, "text": "$40 a month", "at": at(2)},
                              {"label": "Chartered Financial Analyst level one", "value": 1000, "text": "$1,000", "at": at(4)},
                              {"label": "Certified Public Accountant", "value": 500, "text": "$500", "at": at(6)},
                              {"label": "Financial Modelling and Valuation Analyst", "value": 600, "text": "$600", "at": at(8)}], "source": "s"}),
    "duration": lengths({"value": 6, "unit": "weeks", "source": "s"}, {"value": 120, "unit": "hours", "style": "dial", "source": "s"},
                        {"value": 3, "unit": "days", "style": "clock", "source": "s"}),
    "qa-stack": lengths({"items": [{"text": "Why?", "at": at(2)}]},
                        {"items": [{"text": "Is the NPV positive?", "em": ["NPV"], "at": at(2)}, {"text": "What is the IRR?", "em": ["IRR"], "at": at(4)},
                                   {"text": "What would change your mind?", "at": at(6)}]},
                        {"items": [{"text": "What happens to the valuation if interest rates rise by one percent next year?", "at": at(2)},
                                   {"text": "Which assumption moves the answer the most?", "at": at(4)},
                                   {"text": "How sure are you of the growth rate?", "at": at(6)}]}),
    "browser": lengths({"title": "Coursera", "domain": "coursera.org"},
                       {"title": "Financial Markets", "subtitle": "Yale University, free to audit", "badges": ["Free", "Certificate"],
                        "button": "Enroll for free", "domain": "coursera.org"},
                       {"title": "Corporate Finance for Complete Beginners",
                        "subtitle": "A long subtitle that explains what the course covers and who it is meant for",
                        "badges": ["Free", "Certificate", "Beginner", "Self paced", "English", "6 weeks"], "button": "Start learning", "domain": "example.org",
                        "source": "s"}),
    "sheet": lengths({"rows": [["Year", "Cash"]]},
                     {"rows": [["Year", "Cash"], ["1", "$100"], ["2", "$120"], ["3", "$150"]], "formula": "=B2*1.2", "source": "s"},
                     {"rows": [["Year", "Revenue", "Cost", "Profit"]] + [[str(y), "$%d" % (100 + 10 * y), "$%d" % (60 + 5 * y), "$%d" % (40 + 5 * y)] for y in range(1, 8)],
                      "formula": "=B8-C8", "highlight": {"row": 3, "at": at(4)}, "source": "s"}),
    "formula": lengths({"tex": "x"}, {"tex": "PV = \\frac{FV}{(1+r)^n}"},
                       {"tex": "NPV", "parts": [{"tex": "NPV =", "at": at(2)}, {"tex": "\\sum_{t=1}^{n} \\frac{CF_t}{(1+r)^t}", "at": at(4)}]}),
    "icon-row": lengths({"items": [{"icon": "book", "label": "Read", "at": at(2)}, {"icon": "clock", "label": "Wait", "at": at(4)}]},
                        {"items": [{"icon": "book", "label": "Learn", "at": at(2)}, {"icon": "calculator", "label": "Model", "at": at(4)},
                                   {"icon": "send", "label": "Apply", "at": at(6)}]},
                        {"items": [{"icon": "book", "label": "Read the annual report", "at": at(2)}, {"icon": "calculator", "label": "Build the model", "at": at(4)},
                                   {"icon": "file-text", "label": "Write the memo", "at": at(6)}, {"icon": "send", "label": "Send it to ten people", "at": at(8)}]}),
    # the build-up scenes have fixed heights: the cases vary the counts, not the text
    "flow": lengths({"nodes": [{"label": "Ask", "at": at(2)}, {"label": "Answer", "at": at(4)}]},
                    {"nodes": [{"label": "Retrieve", "icon": "book", "at": at(2)}, {"label": "Augment", "at": at(4)}, {"label": "Generate", "at": at(6)}]},
                    {"nodes": [{"label": "Search the documents", "icon": "book", "at": at(2)}, {"label": "Rank", "at": at(4)},
                               {"label": "Prompt", "icon": "send", "at": at(6)}, {"label": "Answer", "at": at(8)}]}),
    "stack": lengths({"items": [{"label": "Base", "at": at(2)}, {"label": "Top", "at": at(4)}]},
                     {"items": [{"label": "Time value", "at": at(2)}, {"label": "Risk", "at": at(4)}, {"label": "Budgeting", "at": at(6)}]},
                     {"items": [{"label": "Time value of money", "at": at(2)}, {"label": "Risk and return", "at": at(4)}, {"label": "Cost of capital", "at": at(6)},
                                {"label": "Budgeting", "at": at(8)}, {"label": "Valuation", "at": at(10)}]}),
    "compare": lengths({"left": {"title": "A", "items": [{"text": "x", "at": at(2)}]}, "right": {"title": "B", "items": [{"text": "y", "at": at(4)}]}},
                       {"left": {"title": "Memory", "items": [{"text": "Guesses", "at": at(2)}, {"text": "Dated", "at": at(4)}]},
                        "right": {"title": "RAG", "items": [{"text": "Looks up", "at": at(6)}]}, "winner": {"side": "right", "at": at(8)}},
                       {"left": {"title": "Old way", "items": [{"text": "Manual", "at": at(2)}, {"text": "Slow", "at": at(3)}, {"text": "Costly", "at": at(4)},
                                                               {"text": "Risky", "at": at(5)}]},
                        "right": {"title": "New way", "items": [{"text": "Automatic", "at": at(6)}, {"text": "Fast", "at": at(7)}]}}),
    "timeline": lengths({"steps": [{"label": "Start", "at": at(2)}, {"label": "Finish", "at": at(4)}]},
                        {"steps": [{"label": "Learn", "sub": "Excel basics", "at": at(2)}, {"label": "Build", "at": at(4)}, {"label": "Ship", "sub": "Your model", "at": at(6)}]},
                        {"steps": [{"label": "Read", "sub": "the annual report", "at": at(2)}, {"label": "Model", "at": at(4)}, {"label": "Value", "at": at(6)},
                                   {"label": "Write", "sub": "a one page memo", "at": at(8)}, {"label": "Send", "at": at(10)}]}),
    "cards": lengths({"cards": [{"title": "One", "at": at(2)}]},
                     {"cards": [{"title": "Corporate Finance", "sub": "Coursera", "at": at(2)}, {"title": "Valuation", "at": at(4)}]},
                     {"cards": [{"title": "Corporate Finance", "at": at(2)}, {"title": "Valuation", "at": at(4)}, {"title": "Engineering", "at": at(6)},
                                {"title": "Modelling", "sub": "the hardest one", "at": at(8)}], "focus": {"card": 2, "at": at(10)}}),
    "logo-card": lengths({"logo": "coursera"}, {"logo": "github", "badge": "1", "sub": "Where the code lives"},
                         {"src": "logo.png", "name": "The Wharton School", "badge": "12", "sub": "University of Pennsylvania"}),
    "hub": lengths({"center": "RAG", "items": [{"label": "In", "at": at(2)}, {"label": "Out", "at": at(4)}]},
                   {"center": "Model", "items": [{"label": "Search", "at": at(2)}, {"label": "Rank", "at": at(4)}, {"label": "Answer", "at": at(6)}]},
                   {"center": "You", "items": [{"label": "Budgeting", "at": at(2)}, {"label": "Risk", "at": at(3)}, {"label": "Valuation", "at": at(4)},
                                               {"label": "Markets", "at": at(5)}, {"label": "Data", "at": at(6)}, {"label": "Models", "at": at(7)}]}),
}


# the browser with a real page in it: the view is fixed, so only the title under the window changes the height
SHOTS = [("shot-short", {"title": "Coursera", "domain": "coursera.org", "screenshot": "shot.png"}),
         ("shot-long", {"title": "Introduction to Corporate Finance", "subtitle": "The Wharton School",
                        "domain": "coursera.org", "screenshot": "shot.png"})]
CASES["browser"] = CASES["browser"] + SHOTS


def png(path, w, h):
    raw = b"".join(b"\x00" + b"\x30\x60\xc0" * w for _ in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) +
                chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def compose(root, vendor):
    cases = []
    for typ, variants in CASES.items():
        for name, data in variants:
            case = "%s-%s" % (typ, name)
            d = os.path.join(root, case)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "transcript.json"), "w") as f:
                json.dump({"words": [{"text": w, "start": 0.5 + i * 0.4, "end": 0.8 + i * 0.4} for i, w in enumerate(WORDS)]}, f)
            with wave.open(os.path.join(d, "voice.wav"), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000)
                w.writeframes(b"\x00\x00" * int((D - 0.5) * 8000))
            for key in ("screenshot", "src"):
                if data.get(key):
                    png(os.path.join(d, data[key]), 1280, 2400 if key == "screenshot" else 256)
            scene = dict({"type": typ, "id": "sc", "bg": "mantle", "in": "word:0", "out": D}, **data)
            with open(os.path.join(d, "storyboard.json"), "w") as f:
                json.dump({"id": case, "scenes": [scene]}, f)
            r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "explainer-compose.py"), "--spec", os.path.join(d, "storyboard.json"),
                                "--out", os.path.join(d, "public"), "--vendor", vendor], capture_output=True, text=True)
            if r.returncode:
                sys.exit("%s: %s" % (case, r.stdout + r.stderr))
            cases.append({"case": case, "type": typ, "scene": scene})
    with open(os.path.join(root, "cases.json"), "w") as f:
        json.dump(cases, f, indent=1)
    print("composed %d cases in %s" % (len(cases), root))


def merge(root, measured):
    cases = {c["case"]: c for c in json.load(open(os.path.join(root, "cases.json")))}
    rows = []
    for line in open(measured):
        m = json.loads(line)
        c = cases[m["case"]]
        rows.append({"case": m["case"], "type": c["type"], "scene": c["scene"], "width": m["width"], "height": m["height"]})
    os.makedirs(os.path.dirname(FIXTURE), exist_ok=True)
    with open(FIXTURE, "w") as f:
        f.write("[\n" + ",\n".join(json.dumps(r) for r in rows) + "\n]\n")
    print("wrote %d rows to %s" % (len(rows), FIXTURE))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("dir")
    ap.add_argument("--vendor", default=os.path.join(SCRIPTS, "..", "assets", "vendor"))
    ap.add_argument("--merge")
    a = ap.parse_args()
    merge(a.dir, a.merge) if a.merge else compose(a.dir, a.vendor)
