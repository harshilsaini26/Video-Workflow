#!/usr/bin/env python3
"""make-cases.py: compose one page per calibration case, then turn Chromium's measurements into the height fixture.

  make-cases.py DIR --vendor VENDOR            # writes DIR/<case>/public/index.html and DIR/cases.json
  node measure-scenes.mjs DIR > measured.jsonl  # each case's .box height at 950 and 780 px
  make-cases.py DIR --merge measured.jsonl      # writes tests/fixtures/heights.json

Three text lengths per scene type (custom excluded: it brings its own box). A developer tool, not part of a video run.
"""
import argparse, json, os, subprocess, sys, wave

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
                        {"value": 125000, "prefix": "$", "sub": "the median starting salary for an analyst in New York", "source": "s"}),
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
}


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
            scene = dict({"type": typ, "id": "sc", "bg": "black", "in": "word:0", "out": D}, **data)
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
