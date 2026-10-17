#!/usr/bin/env python3
"""align-script.py: time the script's display words from what the recogniser heard (gate E2).

The voice speaks `say`; the screen shows `show`; the recogniser (Parakeet) hears roughly `say`. So: match the heard
words to the `say` words, then carry the times across to the `show` words line by line. "$1,000" spoken as "one
thousand dollars" takes the span from "one" to "dollars"; a recogniser that writes "$1,000" itself matches the whole
span at once.

  align-script.py --script script.json --asr asr.json --out transcript.json [--report VOICE.md]

Gate E2 fails (exit 1) when under 98% of the `say` words were heard, naming the line with the most missing words, or
when a gap inside one line is over 1.2 s. A gap between lines is a pause the script asked for. transcript.json is
written either way, so the failure can be looked at.
"""
import argparse, difflib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from explainer_lib import apply_lexicon, load_lexicon

MIN_RATIO = 0.98
MAX_GAP = 1.2
FUZZY = 0.8   # "whack" for "wack": a near-miss single word still counts as heard

_NON = re.compile(r"[^0-9a-z]+")


def norm(text):
    return _NON.sub("", str(text).lower())


def _split(n_items, n_slots):
    """Cut range(n_slots) into n_items consecutive groups, as evenly as positions allow (n_items <= n_slots)."""
    return [list(range(i * n_slots // n_items, (i + 1) * n_slots // n_items)) for i in range(n_items)]


def map_show(show, say):
    """For each show word, the say-word indices it covers (in order; [] for a show-only word)."""
    sm = difflib.SequenceMatcher(None, [norm(w) for w in show], [norm(w) for w in say], autojunk=False)
    cover, extra = [[] for _ in show], []
    for tag, a0, a1, b0, b1 in sm.get_opcodes():
        if tag == "equal":
            for k in range(a1 - a0):
                cover[a0 + k] = [b0 + k]
        elif tag == "replace":
            n, m = a1 - a0, b1 - b0
            if n <= m:
                for k, grp in enumerate(_split(n, m)):
                    cover[a0 + k] = [b0 + j for j in grp]
            else:   # more show words than say words: they share the say words in order
                for k in range(n):
                    cover[a0 + k] = [b0 + k * m // n]
        elif tag == "insert":   # say-only words join the show word before them (or after, at the start)
            tgt = a0 - 1 if a0 > 0 else (0 if show else None)
            if tgt is not None:
                extra.append((tgt, range(b0, b1)))
    for tgt, idx in extra:     # after every opcode: the word after a leading insert gets its own cover later
        cover[tgt] = sorted(cover[tgt] + list(idx))
    return cover


_ONES = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen "
                                      "fourteen fifteen sixteen seventeen eighteen nineteen".split())}
_TENS = {w: 10 * i for i, w in enumerate("_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()) if w != "_"}
_SCALES = {"hundred": 100, "thousand": 1000, "million": 10 ** 6, "billion": 10 ** 9}
_UNITS = {"%": ("percent",), "$": ("dollar", "dollars"), "€": ("euro", "euros"), "£": ("pound", "pounds"),
          "₹": ("rupee", "rupees")}


def _parts(word):
    return [p for p in re.split(r"[-\s]+", re.sub(r"[^a-z\-]", "", word.lower())) if p]


def is_number_word(word):
    ps = _parts(word)
    return bool(ps) and all(p in _ONES or p in _TENS or p in _SCALES or p in ("and", "point") for p in ps)


def number_values(words):
    """The values a run of number words can mean: "one thousand" 1000, "twenty twenty-four" 2024 (a year) or 44,
    "two point five" 2.5. Empty when the run is not a number."""
    ps = [p for w in words for p in _parts(w)]
    if not ps or not all(is_number_word(w) for w in words) or ps[0] in ("and", "point") or ps[-1] in ("and", "point"):
        return set()
    if "point" in ps:
        i = ps.index("point")
        whole, frac = number_values([" ".join(ps[:i])]), ps[i + 1:]
        if not whole or not frac or any(p not in _ONES or _ONES[p] > 9 for p in frac):
            return set()
        return {w + float("0." + "".join(str(_ONES[p]) for p in frac)) for w in whole}
    total, cur = 0, 0
    for p in ps:
        if p == "and":
            continue
        if p in _ONES:
            cur += _ONES[p]
        elif p in _TENS:
            cur += _TENS[p]
        elif p == "hundred":
            cur = (cur or 1) * 100
        else:
            total, cur = total + (cur or 1) * _SCALES[p], 0
    out = {total + cur}
    if len(words) == 2:                                        # a year read in two halves: "nineteen ninety", "twenty twenty-four"
        halves = [number_values([w]) for w in words]
        if all(len(v) == 1 for v in halves):
            a, b = (next(iter(v)) for v in halves)
            if 10 <= a <= 99 and 0 <= b <= 99:
                out.add(a * 100 + b)
    return out


def heard_number(text):
    """The number a recogniser wrote as digits ("1,000", "$1,000", "10%", "2.5"), or None."""
    t = str(text).strip().rstrip(".,;:!?")
    if not re.search(r"\d", t) or not re.fullmatch(r"[$€£₹]?\d[\d,]*(\.\d+)?%?", t):
        return None
    return float(re.sub(r"[^\d.]", "", t))


def _ratio(a, b):
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def align(lines, asr, lexicon=None):
    """Display words [{"text","start","end","line"}] and stats {"say_words","matched","ratio","max_gap","gap_line"}.

    The spoken words are `say` after the lexicon (what Kokoro actually read); a token that is only punctuation (a dash)
    is not a word on either side."""
    say, groups = [], []   # say: flat [{"norm","line","raw"}]; groups: flat show words {"text","line","say":[flat idx]}
    for ln in lines:
        spoken = apply_lexicon(str(ln.get("say") or ln["show"]), lexicon or {})
        s_words = [w for w in spoken.split() if norm(w)]
        d_words = [w for w in str(ln["show"]).split() if norm(w)]
        base = len(say)
        say += [{"norm": norm(w), "line": ln["id"], "raw": w} for w in s_words]
        for text, cov in zip(d_words, map_show(d_words, s_words)):
            groups.append({"text": text, "line": ln["id"], "say": [base + j for j in cov]})
    owner = {}
    for gi, g in enumerate(groups):
        for j in g["say"]:
            owner.setdefault(j, gi)
    heard = [w for w in asr if norm(w.get("text", ""))]
    hnorm = [norm(w["text"]) for w in heard]

    match = [None] * len(say)   # say index -> (start, end)

    def take(i, h):
        match[i] = (float(heard[h]["start"]), float(heard[h]["end"]))

    sm = difflib.SequenceMatcher(None, [w["norm"] for w in say], hnorm, autojunk=False)
    for tag, a0, a1, b0, b1 in sm.get_opcodes():
        if tag == "equal":
            for k in range(a1 - a0):
                take(a0 + k, b0 + k)
        elif tag == "replace":
            used = set()
            # 1. a heard token that is a whole show word ("$1,000") covers that word's say span
            for h in range(b0, b1):
                for gi in sorted({owner[i] for i in range(a0, a1) if i in owner}):
                    span = groups[gi]["say"]
                    if span and all(a0 <= i < a1 and match[i] is None for i in span) and norm(groups[gi]["text"]) == hnorm[h]:
                        for i in span:
                            take(i, h)
                        used.add(h)
                        break
            # 2. digits heard for number words: "1,000" for "one thousand" (and "dollars" when it heard "$1,000")
            for h in range(b0, b1):
                val = heard_number(heard[h]["text"])
                if h in used or val is None:
                    continue
                best = None
                for i in range(a0, a1):
                    for j in range(a1, i, -1):
                        run = list(range(i, j))
                        if any(match[k] is not None for k in run) or not any(abs(v - val) < 1e-9 for v in number_values([say[k]["raw"] for k in run])):
                            continue
                        if best is None or len(run) > len(best):
                            best = run
                        break
                if best:
                    raw = str(heard[h]["text"])
                    unit = next((u for sym, u in _UNITS.items() if sym in raw), ())
                    nxt = best[-1] + 1
                    if unit and nxt < a1 and match[nxt] is None and say[nxt]["norm"] in unit:
                        best.append(nxt)
                    for k in best:
                        take(k, h)
                    used.add(h)
            # 3. the rest pair in order when they are near-misses
            h = b0
            for i in range(a0, a1):
                if match[i] is not None:
                    continue
                for hh in range(h, b1):
                    if hh not in used and _ratio(say[i]["norm"], hnorm[hh]) >= FUZZY:
                        take(i, hh)
                        used.add(hh)
                        h = hh + 1
                        break

    matched = sum(m is not None for m in match)
    times = _interpolate(match)

    words = []
    for g in groups:
        if g["say"]:
            st, en = times[g["say"][0]][0], times[g["say"][-1]][1]
        else:   # a show-only word sits, zero length, where its neighbours meet
            st = en = None
        words.append({"text": g["text"], "start": st, "end": en, "line": g["line"]})
    for k, w in enumerate(words):
        if w["start"] is None:
            prev = next((x["end"] for x in reversed(words[:k]) if x["start"] is not None), None)
            nxt = next((x["start"] for x in words[k + 1:] if x["start"] is not None), 0.0)
            w["start"] = w["end"] = prev if prev is not None else nxt
    for w in words:
        w["start"], w["end"] = round(w["start"], 3), round(w["end"], 3)

    max_gap, gap_line = 0.0, None
    for i in range(1, len(say)):
        if say[i]["line"] == say[i - 1]["line"]:
            g = times[i][0] - times[i - 1][1]
            if g > max_gap:
                max_gap, gap_line = g, say[i]["line"]
    missing = {}
    for i, m in enumerate(match):
        if m is None:
            missing[say[i]["line"]] = missing.get(say[i]["line"], 0) + 1
    worst = max(missing, key=lambda k: missing[k]) if missing else None
    stats = {"say_words": len(say), "matched": matched, "ratio": matched / len(say) if say else 0.0,
             "max_gap": round(max_gap, 3), "gap_line": gap_line, "worst_line": worst, "missing": missing}
    return words, stats


def _interpolate(match):
    """Times for every say word: heard ones as heard, the others spread evenly between their heard neighbours."""
    out = list(match)
    n = len(out)
    i = 0
    while i < n:
        if out[i] is not None:
            i += 1
            continue
        j = i
        while j < n and out[j] is None:
            j += 1
        lo = out[i - 1][1] if i > 0 else (out[j][0] if j < n else 0.0)
        hi = out[j][0] if j < n else lo
        step = (hi - lo) / (j - i)
        for k in range(i, j):
            out[k] = (lo + (k - i) * step, lo + (k - i + 1) * step)
        i = j
    return out


def report(path, lines, words, stats):
    out = ["# Voice alignment", "",
           "%.1f%% of %d spoken words heard; widest gap inside a line %.2f s%s." % (
               stats["ratio"] * 100, stats["say_words"], stats["max_gap"],
               " (line %s)" % stats["gap_line"] if stats["gap_line"] else ""), "",
           "| line | from | to | missing | shown |", "|---|---|---|---|---|"]
    for ln in lines:
        ws = [w for w in words if w["line"] == ln["id"]]
        if ws:
            out.append("| %s | %.2f | %.2f | %d | %s |" % (ln["id"], ws[0]["start"], ws[-1]["end"],
                                                         stats["missing"].get(ln["id"], 0), ln["show"].replace("|", "\\|")))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--script", required=True)
    ap.add_argument("--asr", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report")
    ap.add_argument("--lexicon", default=os.path.join(HERE, "..", "lexicon.json"),
                    help="the pronunciations tts-kokoro.py applied (default: the skill's lexicon.json)")
    a = ap.parse_args()
    with open(a.script, encoding="utf-8") as f:
        lines = json.load(f)["lines"]
    with open(a.asr, encoding="utf-8") as f:
        d = json.load(f)
    words, st = align(lines, d["words"] if isinstance(d, dict) else d, load_lexicon(a.lexicon))
    spans = [{"id": ln["id"], "start": ws[0]["start"], "end": ws[-1]["end"]}
             for ln in lines for ws in [[w for w in words if w["line"] == ln["id"]]] if ws]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"words": words, "lines": spans}, f, indent=1)
    if a.report:
        report(a.report, lines, words, st)
    errs = []
    if st["ratio"] < MIN_RATIO:
        errs.append("%.1f%% aligned (line %s)" % (st["ratio"] * 100, st["worst_line"]))
    if st["max_gap"] > MAX_GAP:
        errs.append("gap %.2f s in line %s" % (st["max_gap"], st["gap_line"]))
    if errs:
        print("E2 FAIL: " + "; ".join(errs))
        sys.exit(1)
    print("E2 PASS: %.1f%% aligned, widest gap inside a line %.2f s, %d display words" % (st["ratio"] * 100, st["max_gap"], len(words)))


if __name__ == "__main__":
    main()
