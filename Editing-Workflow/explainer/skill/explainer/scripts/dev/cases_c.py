"""Calibration cases for group C (video and grade): grade-slider, eyedropper-grade, film-look, playing-grid, video-card,
reel-feed. Three lengths each; some with a picture next to storyboard.json ("src": make-cases.py writes it), some with
the built-in one. Read by make-cases.py (load_groups) and by the theme and layout gates."""



CASES = {
    "grade-slider": [
        ("short", {"sliders": [{"kind": "contrast", "from": 0, "to": 40, "at": "word:2"}]}),
        ("mid", {"src": "pic.png", "sliders": [{"kind": "exposure", "from": 0, "to": 30, "at": "word:2"},
                                               {"kind": "saturation", "from": 0, "to": -60, "at": "word:5"}]}),
        ("long", {"sliders": [{"kind": "contrast", "label": "Contrast", "from": -20, "to": 45, "at": "word:2"},
                              {"kind": "saturation", "label": "Vibrance", "from": 0, "to": 35, "at": "word:5"},
                              {"kind": "temperature", "label": "Temperature", "from": -40, "to": 70, "at": "word:8"}]}),
    ],
    "eyedropper-grade": [
        ("short", {"picks": [{"color": "peach", "x": 0.3, "y": 0.3, "at": "word:2"}]}),
        ("mid", {"src": "pic.png", "picks": [{"color": "yellow", "label": "Sun", "x": 0.25, "y": 0.25, "at": "word:2"},
                                             {"color": "teal", "x": 0.7, "y": 0.8, "at": "word:6"}]}),
        ("long", {"picks": [{"color": "peach", "label": "Highlights", "x": 0.3, "y": 0.3, "at": "word:2"},
                            {"color": "mauve", "label": "Midtones", "x": 0.55, "y": 0.6, "at": "word:6"},
                            {"color": "sapphire", "label": "Shadows", "x": 0.9, "y": 0.9, "at": "word:10"}]}),
    ],
    "film-look": [
        ("short", {"at": "word:2"}),
        ("mid", {"src": "pic.png", "at": "word:3", "title": "The film look"}),
        ("long", {"at": "word:4", "before": "Phone", "after": "Cinema",
                  "title": "Letterbox, grain, a warm grade and a soft vignette on every single shot"}),
    ],
    "playing-grid": [
        ("short", {"tiles": [{"at": "word:2"}, {"at": "word:3"}, {"at": "word:4"}, {"at": "word:5"}]}),
        ("mid", {"src": "pic.png", "tiles": [{"label": "Vlog", "at": "word:2"}, {"label": "Tutorial", "at": "word:3"}, {"at": "word:4"},
                                             {"at": "word:5"}, {"label": "Review", "at": "word:6"}, {"at": "word:7"}],
                 "pick": {"tile": 4, "at": "word:10"}}),
        ("long", {"tiles": [{"label": "Routine", "at": "word:2"}, {"label": "Unboxing", "at": "word:3"}, {"at": "word:4"},
                            {"at": "word:5"}, {"label": "Studio tour", "at": "word:6"}, {"at": "word:7"}, {"at": "word:8"}, {"at": "word:9"},
                            {"label": "Backstage", "at": "word:10"}], "pick": {"tile": 8, "at": "word:13"}}),
    ],
    "video-card": [
        ("short", {"title": "Grading", "channel": "Notes", "duration": "3:24", "play": {"at": "word:2"}}),
        ("mid", {"src": "pic.png", "title": "Colour grading in ten minutes", "channel": "Studio Notes", "meta": "1.2M views",
                 "duration": "10:24", "start": "1:05", "play": {"at": "word:3"}}),
        ("long", {"title": "The complete beginner's guide to colour grading your phone footage like a film",
                  "channel": "The Colour Lab Collective", "meta": "84K views · 3 days ago", "duration": "1:02:40",
                  "play": {"at": "word:4"}}),
    ],
    "reel-feed": [
        ("short", {"reels": [{"user": "@a", "caption": "Grade", "likes": 12, "comments": 3, "shares": 1},
                             {"user": "@b", "caption": "Next", "likes": 40, "comments": 5, "shares": 2, "at": "word:4"}]}),
        ("mid", {"src": "pic.png", "reels": [{"user": "@studio.notes", "caption": "Three grades every film uses", "likes": 12400,
                                              "comments": 318, "shares": 1200},
                                             {"user": "@colourlab", "caption": "Teal and orange, explained", "likes": 98000,
                                              "comments": 2100, "shares": 5400, "at": "word:6"}]}),
        ("long", {"reels": [{"user": "@studio.notes", "caption": "Three grades every film uses daily", "likes": 9999,
                             "comments": 318, "shares": 1200, "at": "word:2"},
                            {"user": "@colourlab", "caption": "Teal and orange, for phone shooters", "likes": 1250000,
                             "comments": 21000, "shares": 54000, "at": "word:6"},
                            {"user": "@grainandglow", "caption": "Why film grain makes it look expensive", "likes": 431000,
                             "comments": 9800, "shares": 12000, "at": "word:10"}]}),
    ],
}
