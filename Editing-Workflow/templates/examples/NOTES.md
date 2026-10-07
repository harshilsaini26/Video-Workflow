<!-- EXAMPLE: a made-up project, filled in to show how the template is used. Not a real video. -->

# ai-tools-hook: NOTES

| | |
|---|---|
| **Project** | ai-tools-hook |
| **Profile** | youtube |
| **Open notes** | 0 |
| **Updated** | 2026-10-06 15:31 |

## Checkpoint A: the cut

| id | Given | Your words | at | kind | Owner | Action | state | Fixed in | save | repeat |
|---|---|---|---|---|---|---|---|---|---|---|
| A01 | 2026-10-05 11:02 | "Keep the earlier take of the studio line." | 0:41 raw | cut | Cutter | hand-cut.py keeps take 1 of the studio line, drops take 2 | done | v1 | no | - |
| A02 | 2026-10-05 11:02 | "The joke about coffee goes." | 1:12 raw | cut | Cutter | removed 1:10.4 to 1:16.9 (raw); edge-audit 0 | done | v1 | no | - |

## Checkpoint B: the plan

| id | Given | Your words | at | kind | Owner | Action | state | Fixed in | save | repeat |
|---|---|---|---|---|---|---|---|---|---|---|
| B01 | 2026-10-05 15:05 | "The card at 0:14 covers my face." | 14.0 | on-screen | Director | list card moved from tl to tr (right of x 1220, 640 px wide) | done | v1 | no | - |
| B02 | 2026-10-05 15:05 | "Make the YouTube logo bigger." | 11.9 | on-screen | Director | logo 220 → 264 px tall (the SKILL.md size) | done | v1 | no | - |

## Notes on v1

| id | Given | Your words | at | kind | Owner | Action | state | Fixed in | save | repeat |
|---|---|---|---|---|---|---|---|---|---|---|
| n01 | 2026-10-06 13:58 | "At second 22 the list has too many words." | 22.0 | on-screen | Director | items cut to 1 to 3 words each ("Invite teammates" style) | done | v2 | no | - |
| n02 | 2026-10-06 13:58 | "The music is way too loud under the hook. Save this to the skill." | 0:00 to 0:18 | sound | Sound designer | music ducked 20 dB under the voice instead of 16 | done | v2 | yes | - |
| n03 | 2026-10-06 13:58 | "Around second 30 the zoom feels jumpy." | 30.0 | on-screen | Director | two camera moves merged into one gesture (one punch, `power2.inOut`) | done | v2 | ask → you said no | - |
| n04 | 2026-10-06 13:58 | "Could you please make this a little bit better?" | whole video | general | Producer → Director | asked D03; you said the last 10 s drag: a creep 1.00 → 1.10 from 28.0 to 36.0 and the chip moved 0.4 s earlier | done | v2 | no | - |

## Notes on v2

| id | Given | Your words | at | kind | Owner | Action | state | Fixed in | save | repeat |
|---|---|---|---|---|---|---|---|---|---|---|

## Saved to the skill

| Saved | Notes | Where | Rule as written | Check or test added |
|---|---|---|---|---|
| 2026-10-06 14:20 | n02 | SKILL.md › Sound › Music | "Duck the music about 20 dB under your voice in the hook (16 dB was still too loud) and 19 dB in the body." Replaces the old 16 dB hook rule. | none: a level choice, checked by ear. If it comes back (a repeat), add a loudness-gap check to verify-render.py and a test. |
