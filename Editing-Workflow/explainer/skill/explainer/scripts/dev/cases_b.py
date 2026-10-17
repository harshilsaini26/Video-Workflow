"""Calibration cases for group B (the tool mock-ups): prompt-bar, storyboard-deck, file-drop, nle-timeline,
jiggle-delete. Three lengths each; make-cases.py picks them up (cases_<group>.py). The case page leads in with a title
on word 0 and runs the scene from word 1 to 16 s, so items anchor on word 2 and later."""


def at(i):
    return "word:%d" % i


def lengths(short, mid, long):
    return [("short", short), ("mid", mid), ("long", long)]


CASES = {
    "prompt-bar": lengths(
        {"prompt": {"text": "Make it shorter", "at": at(2)}},
        {"placeholder": "Message the assistant", "prompt": {"text": "Write a hook for my reel about index funds", "at": at(2)},
         "send": {"at": at(9)}},
        {"placeholder": "Ask anything",
         "prompt": {"text": "Turn this transcript into a sixty second reel script with a hook, three beats and a call to action",
                    "at": at(2)},
         "send": {"at": at(12)}, "reply": {"text": "Here is a draft with a hook that lands in the first second", "at": at(14)}}),
    "storyboard-deck": lengths(
        {"frames": [{"note": "Hook", "at": at(2)}, {"note": "Payoff", "sketch": "title", "at": at(5)}]},
        {"frames": [{"note": "Hook", "sketch": "face", "at": at(2)}, {"note": "Screen demo", "sketch": "screen", "at": at(5)},
                    {"note": "The result", "sketch": "chart", "at": at(8)}]},
        {"frames": [{"note": "Cold open", "sketch": "wide", "shot": "1A", "at": at(2)},
                    {"note": "Host", "sketch": "face", "shot": "1B", "at": at(4)},
                    {"note": "Demo", "sketch": "screen", "at": at(6)},
                    {"note": "Outro", "sketch": "title", "at": at(8)}]}),
    "file-drop": lengths(
        {"files": [{"name": "clip.mp4", "at": at(2)}]},
        {"label": "Drop your footage", "files": [{"name": "interview.mp4", "size": "1.2 GB", "at": at(2)},
                                                  {"name": "thumbnail.png", "size": "820 KB", "at": at(4)}],
         "done": {"label": "Uploaded", "at": at(9)}},
        {"label": "Drop files to transcribe",
         "files": [{"name": "episode-final.mov", "size": "3.4 GB", "at": at(2)}, {"name": "voiceover.wav", "size": "48 MB", "at": at(4)},
                   {"name": "script.pdf", "icon": "file-text", "at": at(6)}, {"name": "captions.srt", "size": "12 KB", "at": at(8)}],
         "status": "Transcribing", "done": {"label": "Ready to edit", "at": at(14)}}),
    "nle-timeline": lengths(
        {"tracks": [{"kind": "video", "clips": [{"label": "Hook", "length": 4}, {"label": "Story", "length": 8}]}],
         "cuts": [{"time": 7, "at": at(3)}]},
        {"tracks": [{"kind": "video", "clips": [{"label": "Hook", "length": 3}, {"label": "Interview", "length": 8},
                                                {"label": "Outro", "length": 3}]},
                    {"kind": "audio", "clips": [{"label": "Music", "length": 14}]}],
         "cuts": [{"track": 0, "time": 7, "length": 2.5, "at": at(4)}]},
        {"tracks": [{"kind": "video", "clips": [{"label": "B-roll", "length": 5}, {"label": "Screen", "length": 6}]},
                    {"kind": "video", "clips": [{"label": "Hook", "length": 4}, {"label": "Interview", "length": 9},
                                                {"label": "Outro", "length": 4}]},
                    {"kind": "audio", "clips": [{"label": "Voiceover", "length": 13}, {"label": "Sting", "length": 4}]}],
         "cuts": [{"track": 1, "time": 8, "length": 2, "at": at(4)}, {"track": 1, "time": 11.5, "length": 1, "at": at(9)},
                  {"track": 0, "time": 9, "at": at(13)}]}),
    "jiggle-delete": lengths(
        {"tiles": [{"label": "Notes", "icon": "book"}, {"label": "Timer", "icon": "clock", "at": at(4)}, {"label": "Mail"}]},
        {"jiggle": {"at": at(2)},
         "tiles": [{"label": "Notes", "icon": "book"}, {"label": "Clock", "icon": "clock", "at": at(5)},
                   {"label": "Budget", "icon": "calculator"}, {"label": "Mail", "icon": "send", "at": at(8)}, {"label": "Photos"}],
         "done": {"at": at(12)}},
        {"jiggle": {"at": at(2)},
         "tiles": [{"label": "Notes", "icon": "book"}, {"label": "Clock", "icon": "clock"}, {"label": "Budget", "icon": "calculator", "at": at(5)},
                   {"label": "Messages", "icon": "send"}, {"label": "Files", "icon": "file-text", "at": at(8)}, {"label": "Photos"},
                   {"label": "Weather", "at": at(11)}, {"label": "Podcasts"}],
         "done": {"at": at(16)}}),
}
