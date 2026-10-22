#!/usr/bin/env python3
"""post-check.py: the post caption (POST.md) checked before the creator posts it. It never rewrites.

FAIL: a first line over 125 characters (the app cuts it at "more") or starting with # or @; over 2,200 characters;
      more than 5 hashtags, or a hashtag mid-sentence; bait that gives nothing back ("tag 3 friends", "double tap",
      "comment YES", unless the word is the reel's own comment keyword); a dead closer ("thoughts?", "what do you
      think?"); leaked AI text; a number that is not a sourced number in the script.
WARN: fewer than 3 hashtags, more than one ask, 4 or more emoji, the wording list's stock phrases.

  python3 post-check.py --post videos/<p>/deliver/POST.md [--script script.json] [--brief BRIEF.md] [--keyword CABLE]

Rules adapted from sergebulaev/instagram-skills (ig-caption-writer) and Jakeschincariol/instagram-agent-skill
(ig-caption), both MIT; the numbers are ours (PLAYBOOK §R13, explainer SKILL.md §7).
"""
import argparse, json, os, re, sys

import wording as W

SMALL = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
                                    "fifteen sixteen seventeen eighteen nineteen".split())}
del SMALL["one"]                    # "the one habit" is not a number; "one hundred" still is (below)
TENS = {w: 10 * (i + 2) for i, w in enumerate("twenty thirty forty fifty sixty seventy eighty ninety".split())}
SCALE = {"hundred": 100, "thousand": 1000, "million": 10 ** 6, "billion": 10 ** 9}
BAIT = [re.compile(p, re.I) for p in (r"\btag (\d+|a|two|three|your) (friends?|people|someone)\b", r"\bdouble[- ]tap\b",
                                     r"\blike if you\b", r"\bshare if you\b", r"\bsmash (that|the) like\b")]
COMMENT_WORD = re.compile(r"\b(?i:comment) ['\"“]?([A-Z][A-Z0-9]+)['\"”]?")
DEAD = re.compile(r"(^|\s)(thoughts\?|what do you think\??|agree\?|let me know in the comments\.?)\s*$", re.I)
ASKS = re.compile(r"\b(save|share|send|follow|comment|tag|click|subscribe|link in bio|dm me)\b", re.I)
EMOJI = re.compile(u"[\U0001F300-\U0001FAFF☀-➿]")


def numbers(text):
    """Every number in a text, as values: digits (1,000 / 1.5k / 240) and spelled ones (two hundred and forty)."""
    out = set()
    for m in re.finditer(r"(\d[\d,]*(?:\.\d+)?)\s*([kKmM]\b)?", text):
        v = float(m.group(1).replace(",", ""))
        out.add(v * (1000 if (m.group(2) or "").lower() == "k" else 10 ** 6 if (m.group(2) or "").lower() == "m" else 1))
    cur, total, seen, prev = 0, 0, False, ""
    for w in re.findall(r"[a-z]+", text.lower()) + ["."]:
        if w in SCALE and not seen and prev == "one":
            cur, seen = 1, True
        prev = w
        if w in SMALL:
            cur += SMALL[w]; seen = True
        elif w in TENS:
            cur += TENS[w]; seen = True
        elif w in SCALE and seen:
            if SCALE[w] == 100:
                cur *= 100
            else:
                total += cur * SCALE[w]; cur = 0
        elif w == "and" and seen:
            continue
        elif seen:
            out.add(float(total + cur)); cur, total, seen = 0, 0, False
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--post", required=True)
    ap.add_argument("--script", default="")
    ap.add_argument("--brief", default="")
    ap.add_argument("--keyword", default="")
    a = ap.parse_args()
    try:
        check(a)
    except (OSError, ValueError, AttributeError) as e:
        print("POST ERROR: cannot read %s (%s)" % (getattr(e, "filename", None) or a.script or a.post, e))
        sys.exit(2)


def check(a):
    with open(a.post, encoding="utf-8") as f:
        text = f.read().strip()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    fails, warns = [], []
    if not lines:
        print("POST FAIL: %s is empty" % a.post)
        sys.exit(1)
    first = lines[0]
    if len(first) > 125:
        fails.append("the first line is %d characters: the hook must fit before \"more\" (125)" % len(first))
    if first[:1] in "#@":
        fails.append("the first line starts with %s: open on the hook" % first[0])
    if len(text) > 2200:
        fails.append("the caption is %d characters: the app stops at 2,200" % len(text))
    tags = re.findall(r"(?<![\w&])#[A-Za-z_]\w*", text)        # "#1" is a rank, not a hashtag
    if len(tags) > 5:
        fails.append("%d hashtags: use 3 to 5 that match the reel" % len(tags))
    elif len(tags) < 3:
        warns.append("%d hashtag%s: 3 to 5 help the reel be found (2 to 3 niche, 1 to 2 mid, 0 to 1 broad)" % (len(tags), "" if len(tags) == 1 else "s"))
    for l in lines:
        body = re.sub(r"(\s*#[A-Za-z_]\w*)+\s*$", "", l)
        if re.search(r"(?<![\w&])#[A-Za-z_]\w*", body):
            fails.append("a hashtag mid-sentence (%r): hashtags go at the end" % l[:60])
    for l in lines:
        for rx in BAIT:
            if rx.search(l):
                fails.append("bait that gives nothing back (%r): ask for something with a reason" % l[:60])
        for word in COMMENT_WORD.findall(l):
            if word.lower() != a.keyword.lower():
                fails.append("bait that gives nothing back (comment %s): a comment keyword must get the viewer something%s"
                             % (word, (" (the reel's keyword is %s)" % a.keyword) if a.keyword else ""))
    words_only = [l for l in lines if not re.fullmatch(r"(#[A-Za-z_]\w*\s*)+", l)]
    if words_only and DEAD.search(words_only[-1]):
        fails.append("a dead closer (%r): end on one ask with a reason" % words_only[-1][:60])
    w = W.check_lines([{"id": "post %d" % i, "text": l} for i, l in enumerate(words_only)], hook_index=-1)
    fails += [m for m in w["fail"] if "invisible" in m or any(p["id"] in m for p in W.LISTS["fail"])]
    warns += w["warn"]
    asks = {m.lower() for l in words_only for m in ASKS.findall(l)}
    if len(asks) > 1:
        warns.append("%d asks (%s): one ask, with a reason, works best" % (len(asks), ", ".join(sorted(asks))))
    if len(EMOJI.findall(text)) >= 4:
        warns.append("%d emoji: three at most reads as a person" % len(EMOJI.findall(text)))
    if a.script and os.path.isfile(a.script):
        with open(a.script, encoding="utf-8") as f:
            s = json.load(f)
        known = set()
        for l in s.get("lines", []):
            known |= numbers(l.get("show", "")) | numbers(l.get("say", ""))
        for v in (s.get("sources") or {}).values():
            known |= numbers(json.dumps(v))
        if a.brief and os.path.isfile(a.brief):
            with open(a.brief, encoding="utf-8") as f:
                known |= numbers(f.read())
        body = " ".join(re.sub(r"#[A-Za-z_]\w*|#\d+\b", "", l) for l in words_only)     # hashtags, and "#1" (a rank)
        body = re.sub(r"\b\d{3}\s?\(?[kKbB]\)?(?![\w])", "", body)        # 401(k), 403b, 457(b): plan names
        body = re.sub(r"\bUSB-C\b|\b[A-Z]+\d+\b", "", body)       # names with digits in them (USB4) are names
        for v in sorted(numbers(body) - known):
            fails.append("%s is not a number the script sources: use the sourced figure or drop it" % ("%g" % v))
    for m in fails:
        print("POST FAIL: " + m)
    for m in warns:
        print("POST WARN: " + m)
    print("POST %s: %d lines, %d hashtags" % ("FAIL" if fails else "PASS", len(lines), len(tags)))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
