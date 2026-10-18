#!/usr/bin/env python3
"""make-cases.py: compose one page per calibration case, then turn Chromium's measurements into the height fixture.

  make-cases.py DIR --vendor VENDOR            # writes DIR/<case>/public/index.html and DIR/cases.json
  node measure-scenes.mjs DIR > measured.jsonl  # each case's .box height at 950 and 780 px
  make-cases.py DIR --merge measured.jsonl      # writes tests/fixtures/heights.json

Three text lengths per scene type (custom excluded: it brings its own box). A developer tool, not part of a video run.
More cases live beside this file in cases_<group>.py (each sets CASES = {type: [(name, data), ...]}); with
--only TYPE,TYPE the run covers just those types, and --fixture NAME writes tests/fixtures/heights-NAME.json, so a new
group of scenes is measured without touching anyone else's rows. Every "src" or "screenshot" anywhere in a case's data
gets a placeholder PNG (images(): a name ending in -<W>x<H> sets its size, for an odd aspect).
"""
import argparse, glob, importlib.util, json, os, re, struct, subprocess, sys, wave, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
FIXTURE = os.path.join(SCRIPTS, "tests", "fixtures", "heights.json")
WORDS = ["word%d" % i for i in range(40)]
D = 40 * 0.4 + 1.0


# a short title first: the case is never the reel's hook (whose items must land by 0.8 s, SOP S8)
LEAD_IN = {"type": "title", "id": "lead", "bg": "mantle", "in": "word:0", "out": "word:1", "text": "Lead"}


def at(i):
    return "word:%d" % i


def lengths(short, mid, long):
    return [("short", short), ("mid", mid), ("long", long)]


CASES = {
    "title": lengths({"text": "Three certificates"},
                     {"text": "Three certificates finance bros gatekeep", "kicker": "IF YOU'RE NEW TO FINANCE"},
                     {"text": "The three certificates finance people quietly gatekeep",
                      "kicker": "A LONG KICKER THAT RUNS OVER MORE THAN ONE LINE", "size": 96}),
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
    "kinetic": lengths({"words": [{"text": "STOP", "at": at(2)}]},
                       {"big": {"text": "3", "at": at(1)}, "words": [{"text": "STEP", "at": at(2)}, {"text": "TRICK", "at": at(3)}], "source": "s"},
                       {"big": {"text": "90%", "at": at(1)}, "words": [{"text": "OF", "at": at(2)}, {"text": "SCRIPTS", "at": at(3)}],
                        "line": {"text": "AI WRITES", "at": at(5)}, "strike": {"word": "WRITES", "at": at(7)},
                        "punch": {"text": "FAIL", "at": at(8)}, "source": "s"}),
}


# the browser with a real page in it: the view is fixed, so only the title under the window changes the height
SHOTS = [("shot-short", {"title": "Coursera", "domain": "coursera.org", "screenshot": "shot.png"}),
         ("shot-long", {"title": "Introduction to Corporate Finance", "subtitle": "The Wharton School",
                        "domain": "coursera.org", "screenshot": "shot.png"})]
CASES["browser"] = CASES["browser"] + SHOTS
# giant captions: the voice's words (word0 to word39 in every case), with and without keywords
CASES["giant-captions"] = lengths({}, {"keywords": ["word5"]}, {"keywords": ["word3", "word7", "word11"]})
# a flow too long for the area travels down a window
CASES["flow"] = CASES["flow"] + [("travel", {"nodes": [{"label": l, "at": at(2 + 2 * i)} for i, l in
                                                     enumerate(["Question", "Search", "Passages", "Prompt", "Answer", "Cite"])]})]


def load_groups(folder=HERE):
    """{type: cases} from every cases_<group>.py in `folder`."""
    out = {}
    for path in sorted(glob.glob(os.path.join(folder, "cases_*.py"))):
        spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for typ, variants in mod.CASES.items():
            if typ in out or typ in CASES:
                raise ValueError("%s: cases for %s are already defined elsewhere" % (path, typ))
            out[typ] = variants
    return out


CASES.update(load_groups())


def png(path, w, h):
    raw = b"".join(b"\x00" + b"\x30\x60\xc0\xff" * w for _ in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) +
                chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


SIZED = re.compile(r"-(\d+)x(\d+)\.\w+$")


def images(data):
    """[(path, width, height)]: a placeholder picture for every "src" and "screenshot" anywhere in a case's data (a
    photo's src inside photos[] too). A name ending in -<W>x<H> before its extension is drawn at that size
    ("banner-3000x1000.png", a 3:1 banner); otherwise a screenshot is 1280x2400 and any other picture 1280x256."""
    out = []

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in ("src", "screenshot") and isinstance(v, str) and v:
                    m = SIZED.search(v)
                    out.append((v,) + ((int(m.group(1)), int(m.group(2))) if m else (1280, 2400) if k == "screenshot" else (1280, 256)))
                else:
                    walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(data)
    return list(dict.fromkeys(out))


def compose(root, vendor, only=None, look=None):
    cases = []
    for typ, variants in CASES.items():
        if only and typ not in only:
            continue
        for name, data in variants:
            case = "%s-%s" % (typ, name)
            d = os.path.join(root, case)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "transcript.json"), "w", encoding="utf-8") as f:
                json.dump({"words": [{"text": w, "start": 0.5 + i * 0.4, "end": 0.8 + i * 0.4} for i, w in enumerate(WORDS)]}, f)
            with wave.open(os.path.join(d, "voice.wav"), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000)
                w.writeframes(b"\x00\x00" * int((D - 0.5) * 8000))
            for rel, w, h in images(data):
                os.makedirs(os.path.dirname(os.path.join(d, rel)), exist_ok=True)
                png(os.path.join(d, rel), w, h)
            scene = dict({"type": typ, "id": "sc", "bg": "mantle", "in": "word:1", "out": D}, **data)
            with open(os.path.join(d, "storyboard.json"), "w", encoding="utf-8") as f:
                json.dump(dict({"id": case, "scenes": [LEAD_IN, scene]}, **({"look": look} if look else {})), f)
            r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "explainer-compose.py"), "--spec", os.path.join(d, "storyboard.json"),
                                "--out", os.path.join(d, "public"), "--vendor", vendor], capture_output=True, text=True, encoding="utf-8", errors="replace")
            if r.returncode:
                sys.exit("%s: %s" % (case, r.stdout + r.stderr))
            cases.append(dict({"case": case, "type": typ, "scene": scene}, **({"look": look} if look else {})))
    with open(os.path.join(root, "cases.json"), "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=1)
    print("composed %d cases in %s" % (len(cases), root))


def merge(root, measured, fixture=FIXTURE):
    cases = {c["case"]: c for c in json.load(open(os.path.join(root, "cases.json"), encoding="utf-8"))}
    rows = []
    for line in open(measured, encoding="utf-8"):
        m = json.loads(line)
        c = cases[m["case"]]
        rows.append(dict({"case": m["case"], "type": c["type"], "scene": c["scene"], "width": m["width"], "height": m["height"]},
                         **({"look": c["look"]} if c.get("look") else {})))
    os.makedirs(os.path.dirname(fixture), exist_ok=True)
    with open(fixture, "w", encoding="utf-8") as f:
        f.write("[\n" + ",\n".join(json.dumps(r) for r in rows) + "\n]\n")
    print("wrote %d rows to %s" % (len(rows), fixture))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("dir")
    ap.add_argument("--vendor", default=os.path.join(SCRIPTS, "..", "assets", "vendor"))
    ap.add_argument("--merge")
    ap.add_argument("--only", help="comma-separated scene types")
    ap.add_argument("--fixture", help="write tests/fixtures/heights-<NAME>.json instead of heights.json")
    ap.add_argument("--look", help="compose the cases in this look (paper); the rows record it")
    a = ap.parse_args()
    fx = os.path.join(SCRIPTS, "tests", "fixtures", "heights-%s.json" % a.fixture) if a.fixture else FIXTURE
    merge(a.dir, a.merge, fx) if a.merge else compose(a.dir, a.vendor, set(a.only.split(",")) if a.only else None, a.look)
