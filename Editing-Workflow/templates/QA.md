<!--
QA.md: can this file go out? The QA agent's verdict on every render, patch and master.

Written by: the QA agent ONLY. It never fixes anything; it measures, decides and names who owns each fix.
Read by:    the Producer (routes every FAIL), the owner of each fix, the Assembler (needs PASS on every part), you.
Created:    at the first render (Stage 9), copied from Editing-Workflow/templates/QA.md.

Rules
- One section per file checked, NEWEST AT THE TOP. Never edit an old section; a re-check is a new section.
- A section is titled: ## {version} · {part} · attempt {n} · {PASS | FAIL}
- Every check row has a result: PASS | FAIL | NOTE | N/A
  - NOTE is allowed only for the known exceptions listed in Editing-Workflow/templates/README.md
    (e.g. the bitrate floor on a mostly still screen when every other check passes).
  - N/A only where the check does not apply (lip sync on a hook under 60 s, safe zones on a 16:9 file).
- Verdict is PASS only when no row is FAIL. One FAIL makes the whole file FAIL.
- Every FAIL gets a row in Failures with the time, what was seen, and the owner from README section 8.
- Every sfx row in ASSET-REQUESTS.md gets a row in Sounds.
- The md5 is of the file exactly as checked; delivery must match it.
- Never claim to have heard audio from numbers alone: say "measured", or "listened" only when it was.
Full field definitions: Editing-Workflow/templates/README.md
-->

# {project}: QA

| | |
|---|---|
| **Project** | {project} |
| **Profile** | {youtube \| reels} |
| **Expected** | {3840x2160 \| 1080x1920}, {30 \| 60} fps, BT.709, -14 LUFS |
| **Latest verdict** | {PASS \| FAIL} ({version} · {part} · attempt {n}) |

---

## {v1} · {part} · attempt {1} · {PASS | FAIL}

| | |
|---|---|
| **File** | {output-4k.mp4} |
| **md5** | {md5} |
| **Composition** | {public/index.html} |
| **Checked** | {YYYY-MM-DD HH:MM} |
| **Reports** | {VERIFY.md, render-sheet.png, qa/strips/} |

### Checks

| # | Check | Tool | Result | Measured | Expected |
|---|---|---|---|---|---|
| 1 | Black frames and flashes | verify-render.py (blackdetect) | - | - | none |
| 2 | Size | verify-render.py --res | - | - | {WxH} |
| 3 | Colour tags | verify-render.py | - | - | bt709 / bt709 / bt709 |
| 4 | Video bitrate | verify-render.py | - | - | >= floor for the size |
| 5 | Duration | verify-render.py --index | - | - | data-duration ± 1 frame |
| 6 | A/V sync | verify-render.py | - | - | under 0.12 s |
| 7 | Clipped words | verify-render.py --words --kept | - | - | 0 kept words missing |
| 8 | Every sound present | sound subtraction (see Sounds) | - | - | every sfx row found |
| 9 | Motion at transitions | ffmpeg frame strips | - | - | no jump-then-crawl, dead stop or 1-frame pop |
| 10 | Loudness | ffmpeg ebur128 | - | - | master: -14 LUFS ± 1 (a part: NOTE, levelled at assembly) |
| 11 | True peak | ffmpeg ebur128 | - | - | master: under -1 dBTP (a part: NOTE) |
| 12 | Lip sync | flat frame vs source | - | - | within 1 frame |
| 13 | Safe zones (reels) | render-sheet.png | - | - | nothing in the bottom 20 % or right edge |
| 14 | Frame rate | ffprobe | - | - | {30 \| 60} fps, constant |

### Sounds

| asset | sound | at | window RMS | control RMS | Result |
|---|---|---|---|---|---|

### Failures

| id | at | Check | What was seen | Owner of the fix | Suggested fix |
|---|---|---|---|---|---|

### Verdict

**{PASS | FAIL}**. {One sentence: deliver, or what has to be fixed first.}
