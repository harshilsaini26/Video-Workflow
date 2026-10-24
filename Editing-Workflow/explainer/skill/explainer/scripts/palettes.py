#!/usr/bin/env python3
"""palettes.py: the five colour palettes, to offer the creator a choice (colour only: either look takes any of them).

  palettes.py                       each palette: its colours, mood, how to use it, what it is best for
  palettes.py --for "<the topic>"   the same five, the best fit for the topic first

The choice goes in script.json or the storyboard as "palette": "<name>" (or plan-storyboard.py --palette <name>);
no palette keeps the look's own colours. The cards are tokens.json's palettes (PLAYBOOK §E6.10).
"""
import argparse, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
# a few words around each "best for", so a topic said in the creator's own words still finds its palette
NEAR = {"terracotta": "home craft handmade bakery bread coffee cafe yoga calm spa decor garden recipe slow",
        "monochrome": "fashion style editorial model camera studio building design minimal premium brand jewellery watch",
        "electric-pop": "festival concert gig party gaming club launch drop tiktok trend creator teen dance",
        "nordic-frost": "software app dashboard startup ai data bank money invest insurance health clinic doctor security cloud",
        "bold-citrus": "snack recipe cooking meal restaurant burger juice smoothie gym workout sport child family fun"}


def score(card, name, topic):
    words = set(re.findall(r"[a-z]+", topic.lower()))
    best = set(re.findall(r"[a-z]+", " ".join(card["best_for"]).lower()))
    return 3 * len(words & best) + len(words & set(NEAR.get(name, "").split()))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--for", dest="topic", default="")
    a = ap.parse_args()
    with open(os.path.join(HERE, "..", "tokens.json"), encoding="utf-8") as f:
        cards = json.load(f)["palettes"]
    names = list(cards)
    if a.topic:
        names.sort(key=lambda n: -score(cards[n], n, a.topic))      # stable: ties keep the tokens' order
    for n in names:
        c = cards[n]
        print("%s  (%s)  %s\n  %s\n  use: %s\n  best for: %s\n" % (n, c["title"], " ".join(c["colors"]), c["mood"], c["use"],
                                                                    ", ".join(c["best_for"])))


if __name__ == "__main__":
    main()
