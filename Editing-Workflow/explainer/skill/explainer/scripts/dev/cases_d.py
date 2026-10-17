"""Calibration cases for group D, the object scenes: chat, doc, stat (make-cases.py loads this file). The scene runs
from word 1; its items land on word 2 and later."""


def at(i):
    return "word:%d" % i


CASES = {
    "chat": [
        ("short", {"messages": [{"role": "user", "text": "Leave days?", "at": at(2)},
                                {"role": "assistant", "text": "Twenty a year.", "at": at(5)}]}),
        ("mid", {"name": "HR Assistant", "source": "s",
                 "messages": [{"role": "user", "text": "How many leave days do I get?", "at": at(2)},
                              {"role": "assistant", "text": "You get 24 days of paid leave a year.", "at": at(6),
                               "cite": {"text": "Leave policy.pdf", "at": at(9)}},
                              {"role": "user", "text": "Do they roll over?", "at": at(12)},
                              {"role": "assistant", "text": "Up to five days, into the next year only.", "at": at(15)}]}),
        ("long", {"name": "Company Knowledge Assistant", "placeholder": "Ask about any policy", "source": "s",
                  "messages": [{"role": "user", "text": "How many days of paid leave do new employees get in their first year?", "at": at(2)},
                               {"role": "assistant", "text": "New employees get 24 days of paid leave, earned monthly from the first day they start.",
                                "at": at(7), "cite": {"text": "Employee handbook, section 3", "at": at(10)}},
                               {"role": "user", "text": "And can I carry unused days over?", "at": at(13)},
                               {"role": "assistant", "text": "Yes, up to five days carry into the next year.", "at": at(17),
                                "cite": {"text": "Leave policy.pdf", "at": at(20)}},
                               {"role": "user", "text": "Who approves it?", "at": at(23)},
                               {"role": "assistant", "text": "Your manager approves it in the HR portal.", "at": at(26)}]}),
        ("wrap", {"name": "Assistant", "placeholder": "Message the assistant",
                  "messages": [{"role": "user", "text": "Can I carry unused leave over to next year?", "at": at(2)},
                               {"role": "assistant", "text": "Yes, up to five days, if your manager agrees first.", "at": at(6),
                                "cite": {"text": "Leave policy.pdf", "at": at(9)}}]}),
        ("long-one", {"name": "Support", "source": "s",
                      "messages": [{"role": "user", "text": "What happens to my unused leave days when I leave the company before the end of the year?",
                                    "at": at(2)},
                                   {"role": "assistant", "text": "Any leave you have earned but not taken is paid out with your final salary, "
                                    "at your normal daily rate, within thirty days.", "at": at(8),
                                    "cite": {"text": "Leave policy.pdf", "at": at(12)}}]}),
    ],
    "doc": [
        ("short", {"blocks": [{"text": "Leave is earned monthly.", "at": at(2)}]}),
        ("mid", {"name": "leave-policy.pdf", "title": "Annual leave", "source": "s",
                 "blocks": [{"text": "Leave is earned every month."}, {"filler": 1},
                            {"text": "Staff get 24 days of paid leave a year.", "at": at(4), "tag": "Section 3.2"},
                            {"filler": 1}]}),
        ("long", {"name": "employee-handbook-2024.pdf", "title": "Annual leave for all staff", "source": "s",
                  "blocks": [{"text": "Full-time staff earn 24 days of paid leave each year, accrued monthly from their first day.",
                              "at": at(4), "tag": "Section 3.2"},
                             {"filler": 1},
                             {"text": "Up to five unused days carry over.", "at": at(9), "tag": "Section 3.4"}]}),
        ("wrap", {"title": "Annual leave and public holidays for everyone who works here full time",
                  "blocks": [{"text": "This part of the handbook explains how paid leave is earned and booked."},
                             {"text": "Ask your manager first.", "at": at(3)}, {"filler": 3}]}),
    ],
    "stat": [
        ("short", {"value": 8, "unit": "HOURS", "at": at(2), "source": "s"}),
        ("mid", {"value": 363, "prefix": "+$", "label": "saved a month", "at": at(2), "source": "s"}),
        ("long", {"value": 25000, "prefix": "$", "label": "the median cost of one data breach at a small business, in a year",
                  "at": at(3), "source": "s"}),
        ("decimal", {"value": 2.5, "decimals": 1, "unit": "WEEKS", "label": "to your first model", "source": "s"}),
    ],
}
