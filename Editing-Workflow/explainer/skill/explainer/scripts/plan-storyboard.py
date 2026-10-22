#!/usr/bin/env python3
"""plan-storyboard.py: a draft storyboard.json from the script and the aligned words (PLAYBOOK §E4), for the Director to
edit instead of writing every scene and anchor by hand.

  plan-storyboard.py --script script.json --transcript transcript.json --out storyboard.json [--report PLAN.md] [--vendor DIR]

Each script line becomes one or more scenes, anchored to its own words:
- a line with a `viz` hint becomes that scene: {"type": "flow", "nodes": ["Retrieve", "Augment", "Generate"]}. Items may
  be plain strings; each lands on the first word of the line that matches its first word (in order), and an item the
  line never says is spread evenly between its neighbours. Any other "at" written as a word ("better") is found the
  same way. A long line can hold a list of hints: each after the first starts on its "from" word and anchors its items
  on its own part of the line.
- without a hint: a money or percent figure ("$1,000", "40%") → count-up; "step 2", "number 3", "first", "second" at
  the start → number; a brand whose mark is in the local simple-icons set → logo-card; line 0 → a title of the hook;
  anything else → title beats of at most 2.5 s, each showing the line's emphasis word or its last key words (a draft:
  replace them with pictures).
- a line's source goes on its scenes. The grounds keep a rhythm, like the reference's: the hook on the dark `ink`, the
  payoff on `blue`, the light surfaces between (a `section` break moves them along mantle → base → mantle), and inside a
  section every third scene on `blue`, so the frame never sits on one colour for long.
Every scene's out is the next scene's in; the last runs to "end". The report lists each scene and the rule that made it.
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from scenes import logo_card

BEAT = 2.5
HOOK_BY, LEAD = 0.8, 0.2          # explainer_lib's: the hook's items land by 0.8 s, an entrance 0.2 s before its word
TAIL, LAST_READ = 0.5, 1.5        # the page runs TAIL past the voice; the last read lands LAST_READ before the end (E4)
DERIVED = 0.8                     # and a scene may land a piece up to this long after its anchor (line-art's caption)
BGS = ["mantle", "base"]          # the two light Latte surfaces (tokens.json), alternating at each section break
HOOK_BG, PAYOFF_BG, BEAT_BG = "ink", "blue", "blue"
ONE_GROUND = "base"                     # the paper look: every scene on the paper
STOP = set("a an and are as at be but by for from has have i in is it its me my of on or our so than that the their them then "
           "there these they this to was we were what when which who will with you your".split())
ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5}
LIST_KEYS = {"nodes": "label", "items": "label", "steps": "label", "cards": "title", "rows": "label", "parts": "tex",
             "frames": "note", "files": "name", "comments": "text", "messages": "text", "sliders": "label",
             "picks": "label", "reels": "caption", "tiles": "label"}
# per scene type: a list whose text sits in another field, or (None) a list where only some entries land on a word
# (a doc's passages, the tiles a jiggle deletes): those take an "at" written as a word, nothing else
TYPE_LISTS = {"qa-stack": {"items": "text"}, "gravity-drop": {"items": "text"}, "jiggle-delete": {"tiles": None},
              "doc": {"blocks": None}, "nle-timeline": {"cuts": None}}
MONEY = re.compile(r"([$€£₹])\s?(\d[\d,]*(?:\.\d+)?)|(\d[\d,]*(?:\.\d+)?)\s?%")


def norm(w):
    return re.sub(r"[^a-z0-9]", "", str(w).lower())


def key_word(text):
    ws = [norm(w) for w in str(text).split() if norm(w)]
    return next((w for w in ws if w not in STOP), ws[0] if ws else "")


def matches(said, key):
    if "-" in str(said):     # "3-step" says both "3" and "step"
        return any(matches(part, key) for part in str(said).split("-") if part) or matches(str(said).replace("-", ""), key)
    a = norm(said)
    if not a or not key:
        return False
    if a == key:
        return True
    short = min(len(a), len(key))
    return short >= 4 and (a.startswith(key) or key.startswith(a))


def anchor_list(entries, field, idx, words, same=False):
    """Give every entry an "at" on the line's words (idx): matched in order, the rest spread between their neighbours.
    With same, two entries may land on one word (a kinetic hook's "3" and "STEP" are both said by "3-step")."""
    pos, cursor = [], 0
    for e in entries:
        if isinstance(e.get("at"), str) and e["at"].startswith("word:"):
            pos.append(int(e["at"][5:]))
            continue
        key = key_word(e["at"] if isinstance(e.get("at"), str) else e.get(field, ""))   # an "at" written as a word wins
        hit = next((j for j in range(cursor, len(idx)) if matches(words[idx[j]]["text"], key)), None)
        pos.append(idx[hit] if hit is not None else None)
        if hit is not None:
            cursor = hit if same else hit + 1
    k = 0
    while k < len(pos):
        if pos[k] is not None:
            k += 1
            continue
        m = k
        while m < len(pos) and pos[m] is None:
            m += 1
        a = pos[k - 1] if k else idx[0] - 1
        b = pos[m] if m < len(pos) else idx[-1] + 1
        for j in range(k, m):
            pos[j] = min(idx[-1], max(idx[0], int(round(a + (b - a) * (j - k + 1) / float(m - k + 1)))))
        k = m
    for e, p in zip(entries, pos):
        e["at"] = "word:%d" % p


def find_word(text, idx, words):
    key = key_word(text)
    return next((i for i in idx if matches(words[i]["text"], key)), idx[-1])


def kinetic(sc, idx, words):
    from scenes import kinetic as K
    """A kinetic hook from plain words: {"big": "3", "words": ["STEP", "TRICK"], "line": "AI INVENTS", "strike": "INVENTS",
    "punch": "LESS"} -> each piece an object with its own "at", landed in order on the words that say it."""
    for k in ("big", "line", "punch"):
        if isinstance(sc.get(k), str):
            sc[k] = {"text": sc[k]}
    if isinstance(sc.get("strike"), str):
        sc["strike"] = {"word": sc["strike"]}
    if isinstance(sc.get("words"), list):
        sc["words"] = [{"text": w} if isinstance(w, str) else w for w in sc["words"]]
    K.normalize(sc)                      # "5 STEPS" written as words: the 5 is the hero
    seq = ([sc["big"]] if sc.get("big") else []) + list(sc.get("words") or []) + ([sc["line"]] if sc.get("line") else [])
    if sc.get("strike"):
        sc["strike"].setdefault("text", sc["strike"]["word"])
        seq.append(sc["strike"])
    if sc.get("punch"):
        seq.append(sc["punch"])
    anchor_list(seq, "text", idx, words, same=True)
    if sc.get("strike"):
        sc["strike"].pop("text", None)
    return sc


def hook_anchors(sc, words, limit):
    """SOP S8: the hook is whole on screen by 1.0 s, so every piece of the first scene lands on a word said by `limit`
    (word start, seconds). A kinetic hook's pieces are spread in order over those words; any other late anchor moves
    to the last of them."""
    early = [i for i, w in enumerate(words) if w["start"] <= limit] or [0]
    if sc.get("type") == "kinetic":
        seq = [sc[k] for k in ("big",) if sc.get(k)] + list(sc.get("words") or []) + [sc[k] for k in ("line", "strike", "punch") if sc.get(k)]
        for j, piece in enumerate(seq):
            piece["at"] = "word:%d" % early[int(round(j * (len(early) - 1) / float(max(1, len(seq) - 1))))]
        return sc
    return clamp_at(sc, early[-1])


def anchors(o):
    """Every word index an anchor ("in", "at", "strike", "<name>_at": word:N) anywhere in o points at."""
    if isinstance(o, dict):
        for k, v in o.items():
            if (k in ("in", "at", "strike") or k.endswith("_at")) and isinstance(v, str) and v.startswith("word:"):
                yield int(v[5:])
            else:
                yield from anchors(v)
    elif isinstance(o, list):
        for v in o:
            yield from anchors(v)


def clamp_at(o, last):
    """Every "at" (word:N) anywhere in o later than word `last` moves to it."""
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "at" and isinstance(v, str) and v.startswith("word:") and int(v[5:]) > last:
                o[k] = "word:%d" % last
            else:
                clamp_at(v, last)
    elif isinstance(o, list):
        for v in o:
            clamp_at(v, last)
    return o


def from_viz(viz, idx, words):
    sc = json.loads(json.dumps(viz))
    if sc.get("type") == "kinetic":
        return kinetic(sc, idx, words)
    lists = dict(LIST_KEYS, **TYPE_LISTS.get(sc.get("type"), {}))
    for key, field in lists.items():
        if isinstance(sc.get(key), list) and field:
            sc[key] = [dict({field: e}) if isinstance(e, str) else e for e in sc[key]]
            anchor_list(sc[key], field, idx, words)
    for side in ("left", "right"):
        if isinstance(sc.get(side), dict) and isinstance(sc[side].get("items"), list):
            sc[side]["items"] = [{"text": e} if isinstance(e, str) else e for e in sc[side]["items"]]
            anchor_list(sc[side]["items"], "text", idx, words)
    if isinstance(sc.get("reveal"), list):
        anchor_list(sc["reveal"], "at", idx, words)
    def words_to_anchors(o):           # any "at", "<name>_at" or "strike" written as a word, anywhere in the hint, lands on it
        if isinstance(o, dict):
            for k in [k for k in o if k in ("at", "strike") or k.endswith("_at")]:
                if isinstance(o[k], str) and not o[k].startswith("word:"):
                    o[k] = "word:%d" % find_word(o[k], idx, words)
            for v in o.values():
                words_to_anchors(v)
        elif isinstance(o, list):
            for v in o:
                words_to_anchors(v)
    words_to_anchors(sc)
    return sc


def thread_anchors(thread, words):
    """The script's thread with each key's "at" (a word of the voice) on that word: the keys in order, each found after
    the one before, across the whole transcript."""
    th = json.loads(json.dumps(thread))
    cursor = 0
    for k in th.get("keys", []):
        at = k.get("at")
        if isinstance(at, str) and at.startswith("word:"):
            cursor = int(at.split(":")[1]) + 1
            continue
        key = key_word(str(at))
        hit = next((i for i in range(cursor, len(words)) if matches(words[i]["text"], key)), None)
        if hit is None:
            sys.exit("thread key %r: no word %r after word %d of the voice" % (k.get("shape"), at, cursor))
        k["at"] = "word:%d" % hit
        cursor = hit + 1
    return th


def logos(vendor):
    d = os.path.join(vendor, "simple-icons", "icons")
    return {f[:-4] for f in os.listdir(d) if f.endswith(".svg")} if os.path.isdir(d) else set()


def keywords(chunk, emphasis):
    em = [w["text"] for w in chunk if norm(w["text"]) in emphasis]
    if em:
        return " ".join(re.sub(r"[,.;:!?]+$", "", w) for w in em)
    keys = [re.sub(r"[,.;:!?]+$", "", w["text"]) for w in chunk if norm(w["text"]) not in STOP]
    return " ".join(keys[-3:]) or re.sub(r"[,.;:!?]+$", "", chunk[-1]["text"])


def plan_line(li, ln, idx, words, brands):
    """[(first word index, scene without id/in/out/bg, rule)] for one line."""
    show = str(ln.get("show", ""))
    if isinstance(ln.get("viz"), list) and ln["viz"]:
        # several pictures for one line: each after the first starts on its "from" word (else the line is split evenly),
        # and its items land on its own stretch of words only
        hints, starts, cursor = ln["viz"], [0], 1
        for k, h in enumerate(hints[1:], 1):
            even = max(cursor, min(len(idx) - 1, round(len(idx) * k / float(len(hints)))))
            key = key_word(h.get("from", ""))
            hit = next((j for j in range(cursor, len(idx)) if key and matches(words[idx[j]]["text"], key)), None)
            starts.append(hit if hit is not None else even)
            cursor = starts[-1] + 1
        out = []
        for k, h in enumerate(hints):
            part = idx[starts[k]:starts[k + 1] if k + 1 < len(starts) else len(idx)] or [idx[starts[k]]]
            out.append((part[0], from_viz({x: y for x, y in h.items() if x != "from"}, part, words), "viz"))
        return out
    if ln.get("viz"):
        return [(idx[0], from_viz(ln["viz"], idx, words), "viz")]
    m = MONEY.search(show)
    if m:
        num = m.group(2) or m.group(3)
        value = float(num.replace(",", ""))
        dec = len(num.split(".")[1]) if "." in num else 0
        sc = {"type": "count-up", "value": value, "prefix": m.group(1) or "", "suffix": "%" if m.group(3) else "", "decimals": dec}
        return [(idx[0], sc, "a money or percent figure")]
    first = [norm(w) for w in show.split()[:2]]
    n = None
    if first and first[0] in ("step", "number", "no", "part") and len(first) > 1 and first[1].isdigit():
        n = int(first[1])
    elif first and first[0] in ORDINALS:
        n = ORDINALS[first[0]]
    if n is not None and n < 100:
        sc = {"type": "number", "n": n}
        if ln.get("emphasis"):
            sc["name"] = ln["emphasis"][0]
        return [(idx[0], sc, "a numbered step")]
    for w in show.split():
        clean = re.sub(r"[^\w.+&-]", "", w)
        s = logo_card.slug(clean)
        if clean[:1].isupper() and len(s) >= 4 and s in brands:
            return [(idx[0], {"type": "logo-card", "logo": s}, "a brand in the local logo set")]
    if li == 0:
        return [(idx[0], {"type": "title", "text": show, "size": 96}, "the hook")]
    emphasis = {norm(e) for e in ln.get("emphasis", [])}
    beats, start = [], 0
    for j in range(1, len(idx) + 1):
        if j == len(idx) or words[idx[j]]["start"] - words[idx[start]]["start"] >= BEAT:
            chunk = [words[i] for i in idx[start:j]]
            beats.append((idx[start], {"type": "title", "text": keywords(chunk, emphasis)}, "plain words: a draft title"))
            start = j
    return beats


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--script", required=True)
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--look", help="latte or paper (default: the script's look, else latte)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--report")
    ap.add_argument("--vendor", default=os.path.join(HERE, "..", "assets", "vendor"))
    a = ap.parse_args()
    with open(a.script, encoding="utf-8") as f:
        S = json.load(f)
    with open(a.transcript, encoding="utf-8") as f:
        T = json.load(f)
    words = T["words"] if isinstance(T, dict) else T
    if not all("line" in w for w in words):
        sys.exit("transcript.json has no line ids: align it with align-script.py")
    brands = logos(a.vendor)
    look = a.look or S.get("look") or "latte"
    scenes, rows, bg, used, in_section = [], [], 0, set(), 0
    for li, ln in enumerate(S.get("lines", [])):
        idx = [i for i, w in enumerate(words) if w["line"] == ln["id"]]
        if not idx:
            continue
        base = re.sub(r"[^A-Za-z0-9_]", "_", str(ln["id"]))
        base = base if re.match(r"^[A-Za-z]", base) else "l" + base
        for k, (start, sc, rule) in enumerate(plan_line(li, ln, idx, words, brands)):
            sid = base if k == 0 else "%s_%d" % (base, k + 1)
            while sid in used:
                sid += "_"
            used.add(sid)
            ground = BGS[bg % len(BGS)]
            if not scenes:
                ground = HOOK_BG
            elif k == 0 and ln["id"] == S.get("payoff"):
                ground = PAYOFF_BG
            else:
                in_section += 1
                if in_section % 3 == 0:
                    ground = BEAT_BG
            if look == "paper":
                ground = ONE_GROUND           # the editorial look keeps one ground: colour comes from the pictures
            full = dict({"type": sc["type"], "id": sid, "bg": ground, "in": "word:%d" % start}, **{x: y for x, y in sc.items() if x != "type"})
            if ln.get("source"):
                full["source"] = ln["source"]
            if k == 0 and ln["id"] == S.get("payoff"):
                full["chime"] = True         # the payoff lands with a chime: a sound the viewer remembers it by
            scenes.append(full)
            rows.append((ln["id"], sid, sc["type"], rule, " ".join(words[i]["text"] for i in idx)[:60]))
        if ln.get("break") == "section":
            bg += 1
            in_section = 0
    if not scenes:
        sys.exit("no scenes: no transcript words carry the script's line ids")
    scenes[0]["in"] = "word:0"
    hook_anchors(scenes[0], words, HOOK_BY + LEAD)
    # the last read needs LAST_READ s on screen (E4): when the last line lands late, the page runs on past the voice
    last = max([words[i]["start"] for i in anchors(scenes[-1])] or [0.0]) - LEAD + DERIVED
    tail = round(last + LAST_READ - words[-1]["end"], 2)
    for x, y in zip(scenes, scenes[1:]):
        x["out"] = y["in"]
    scenes[-1]["out"] = "end"
    emphasis = []
    for ln in S.get("lines", []):
        emphasis += [e for e in ln.get("emphasis", []) if e not in emphasis]
    board = {"id": re.sub(r"[^a-z0-9]+", "-", str(S.get("title", "reel")).lower()).strip("-") or "reel", "fps": 60,
             "voice": "voice.wav", "transcript": "transcript.json", "captions": {"emphasis": emphasis}, "scenes": scenes}
    if look != "latte":
        board["look"] = look
    if tail > TAIL:
        board["tail"] = tail                 # seconds the page runs past the voice (default TAIL)
    if S.get("thread"):
        board["thread"] = thread_anchors(S["thread"], words)    # one line through the reel, keyed on the voice's words
    if S.get("brand"):
        board["brand"] = S["brand"]          # the handle and the series part, on every frame
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(board, f, indent=1)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write("# Draft plan\n\nFrom plan-storyboard.py. Replace every \"draft title\" with a picture (a `viz` hint in the "
                    "script, or a scene in storyboard.json).\n\n| line | scene | type | why | words |\n|---|---|---|---|---|\n")
            f.write("".join("| %s | %s | %s | %s | %s |\n" % r for r in rows))
    drafts = sum(1 for r in rows if r[3].startswith("plain"))
    print("wrote %s: %d scenes from %d lines (%d from viz hints, %d draft titles to replace)"
          % (a.out, len(scenes), len(S.get("lines", [])), sum(1 for r in rows if r[3] == "viz"), drafts))


if __name__ == "__main__":
    main()
