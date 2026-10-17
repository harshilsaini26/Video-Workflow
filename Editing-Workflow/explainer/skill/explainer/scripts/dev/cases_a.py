"""Calibration cases for group A (type and social): gravity-drop, title-card, icon-strike, comment-cta, comment-drop.
Three lengths each (make-cases.py composes them; measure-scenes.mjs measures them; --fixture a writes heights-a.json).
The case page runs a lead-in title on word 0 and the scene from word 1, so every item anchors on word 2 or later. The
icons are the ones the theme test's stub vendor carries (book, clock, calculator, send, file-text)."""


def at(i):
    return "word:%d" % i


CASES = {
    "gravity-drop": [
        ("short", {"items": [{"text": "Excel", "at": at(2)}, {"text": "SQL", "at": at(4)}]}),
        ("mid", {"style": "words", "items": [{"text": "Time", "at": at(2)}, {"text": "Risk", "at": at(3)},
                                             {"text": "Return", "at": at(4)}, {"text": "Capital", "at": at(5)}]}),
        ("long", {"items": [{"text": "Excel", "at": at(2)}, {"text": "Accounting basics", "at": at(3)}, {"text": "Valuation", "at": at(4)},
                            {"text": "Python", "at": at(5)}, {"text": "Three statements", "at": at(6)}, {"text": "SQL", "at": at(7)},
                            {"text": "Storytelling", "at": at(8)}, {"text": "Modelling", "at": at(9)}]}),
    ],
    "title-card": [
        ("short", {"kicker": "PART 2", "title": "The model"}),
        ("mid", {"kicker": "STEP 3", "title": "Build the three statements", "subtitle": "Income, balance sheet, cash flow"}),
        ("long", {"kicker": "CHAPTER FOUR", "title": "Valuing the companies you already know",
                  "subtitle": {"text": "What this part of the reel covers, and why it matters before you start", "at": at(4)}}),
    ],
    "icon-strike": [
        ("short", {"icon": "clock", "strike": {"at": at(3)}}),
        ("mid", {"icon": "calculator", "label": "Paid tools", "at": at(2), "strike": {"at": at(4)}}),
        ("long", {"icon": "file-text", "label": "Paid courses", "at": at(2), "strike": {"at": at(4)},
                  "replacement": {"icon": "book", "label": "Free library", "at": at(6)}}),
    ],
    "comment-cta": [
        ("short", {"keyword": {"text": "GO", "at": at(2)}, "gets": {"text": "The link", "at": at(4)}}),
        ("mid", {"keyword": {"text": "GUIDE", "at": at(2)}, "gets": {"text": "The free checklist, in your DMs", "at": at(5)}}),
        ("long", {"kicker": "COMMENT THE WORD", "keyword": {"text": "SPREADSHEET", "at": at(3)},
                  "gets": {"text": "The whole model template, sent straight to your DMs", "at": at(7)}}),
    ],
    "comment-drop": [
        ("short", {"comments": [{"name": "sarah.k", "text": "Saved me hours", "likes": 1204, "at": at(2)},
                                {"name": "mike", "text": "Wish I knew this", "likes": 87, "at": at(4)}]}),
        ("mid", {"comments": [{"name": "sarah.k", "text": "This saved me hours on my first model", "likes": 1204, "time": "2h", "at": at(2)},
                              {"name": "dev_mike", "text": "Why did nobody tell me this", "likes": 87, "time": "1h", "at": at(4)},
                              {"name": "@ana.builds", "text": "Bookmarked", "likes": 12, "time": "4m", "at": at(6)}]}),
        ("long", {"comments": [{"name": "sarah.k", "text": "This saved me hours on my first model, and my manager noticed straight away",
                                "likes": 1204, "time": "2h", "at": at(2)},
                               {"name": "the_finance_student", "text": "Why did nobody at university ever tell me this", "likes": 873,
                                "time": "1h", "at": at(4)},
                               {"name": "ana.builds", "text": "Bookmarked for the weekend", "likes": "2.4k", "time": "4m", "at": at(6)}]}),
    ],
}
