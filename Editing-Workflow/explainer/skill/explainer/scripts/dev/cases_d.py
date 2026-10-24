"""Calibration cases for group D, the object scenes: chat, doc, stat (make-cases.py loads this file). The scene runs
from word 1; its items land on word 2 and later."""



CASES = {
    "chat": [
        ("short", {"messages": [{"role": "user", "text": "Leave days?", "at": "word:2"},
                                {"role": "assistant", "text": "Twenty a year.", "at": "word:5"}]}),
        ("mid", {"name": "HR Assistant", "source": "s",
                 "messages": [{"role": "user", "text": "How many leave days do I get?", "at": "word:2"},
                              {"role": "assistant", "text": "You get 24 days of paid leave a year.", "at": "word:6",
                               "cite": {"text": "Leave policy.pdf", "at": "word:9"}},
                              {"role": "user", "text": "Do they roll over?", "at": "word:12"},
                              {"role": "assistant", "text": "Up to five days, into the next year only.", "at": "word:15"}]}),
        ("long", {"name": "Company Knowledge Assistant", "placeholder": "Ask about any policy", "source": "s",
                  "messages": [{"role": "user", "text": "How many days of paid leave do new employees get in their first year?", "at": "word:2"},
                               {"role": "assistant", "text": "New employees get 24 days of paid leave, earned monthly from the first day they start.",
                                "at": "word:7", "cite": {"text": "Employee handbook, section 3", "at": "word:10"}},
                               {"role": "user", "text": "And can I carry unused days over?", "at": "word:13"},
                               {"role": "assistant", "text": "Yes, up to five days carry into the next year.", "at": "word:17",
                                "cite": {"text": "Leave policy.pdf", "at": "word:20"}},
                               {"role": "user", "text": "Who approves it?", "at": "word:23"},
                               {"role": "assistant", "text": "Your manager approves it in the HR portal.", "at": "word:26"}]}),
        ("wrap", {"name": "Assistant", "placeholder": "Message the assistant",
                  "messages": [{"role": "user", "text": "Can I carry unused leave over to next year?", "at": "word:2"},
                               {"role": "assistant", "text": "Yes, up to five days, if your manager agrees first.", "at": "word:6",
                                "cite": {"text": "Leave policy.pdf", "at": "word:9"}}]}),
        ("long-one", {"name": "Support", "source": "s",
                      "messages": [{"role": "user", "text": "What happens to my unused leave days when I leave the company before the end of the year?",
                                    "at": "word:2"},
                                   {"role": "assistant", "text": "Any leave you have earned but not taken is paid out with your final salary, "
                                    "at your normal daily rate, within thirty days.", "at": "word:8",
                                    "cite": {"text": "Leave policy.pdf", "at": "word:12"}}]}),
    ],
    "doc": [
        ("short", {"blocks": [{"text": "Leave is earned monthly.", "at": "word:2"}]}),
        ("mid", {"name": "leave-policy.pdf", "title": "Annual leave", "source": "s",
                 "blocks": [{"text": "Leave is earned every month."}, {"filler": 1},
                            {"text": "Staff get 24 days of paid leave a year.", "at": "word:4", "tag": "Section 3.2"},
                            {"filler": 1}]}),
        ("long", {"name": "employee-handbook-2024.pdf", "title": "Annual leave for all staff", "source": "s",
                  "blocks": [{"text": "Full-time staff earn 24 days of paid leave each year, accrued monthly from their first day.",
                              "at": "word:4", "tag": "Section 3.2"},
                             {"filler": 1},
                             {"text": "Up to five unused days carry over.", "at": "word:9", "tag": "Section 3.4"}]}),
        ("wrap", {"title": "Annual leave and public holidays for everyone who works here full time",
                  "blocks": [{"text": "This part of the handbook explains how paid leave is earned and booked."},
                             {"text": "Ask your manager first.", "at": "word:3"}, {"filler": 3}]}),
    ],
    "stat": [
        ("short", {"value": 8, "unit": "HOURS", "at": "word:2", "source": "s"}),
        ("mid", {"value": 363, "prefix": "+$", "label": "saved a month", "at": "word:2", "source": "s"}),
        ("long", {"value": 25000, "prefix": "$", "label": "the median cost of one data breach at a small business, in a year",
                  "at": "word:3", "source": "s"}),
        ("decimal", {"value": 2.5, "decimals": 1, "unit": "WEEKS", "label": "to your first model", "source": "s"}),
    ],
}
