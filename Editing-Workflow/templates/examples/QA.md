<!-- EXAMPLE: a made-up project, filled in to show how the template is used. Not a real video. Numbers are illustrative. -->

# ai-tools-hook: QA

| | |
|---|---|
| **Project** | ai-tools-hook |
| **Profile** | youtube |
| **Expected** | 3840x2160, 30 fps, BT.709, -14 LUFS |
| **Latest verdict** | PASS (v2 · hook · attempt 1) |

---

## v2 · hook · attempt 1 · PASS

| | |
|---|---|
| **File** | output-4k.mp4 |
| **md5** | 7c41e0a9… (example) |
| **Composition** | public/index.html |
| **Checked** | 2026-10-06 16:38 |
| **Reports** | VERIFY.md, render-sheet.png, qa/v2-1/strips/ |

### Checks

| # | Check | Tool | Result | Measured | Expected |
|---|---|---|---|---|---|
| 1 | Black frames and flashes | verify-render.py (blackdetect) | PASS | none | none |
| 2 | Size | verify-render.py --res | PASS | 3840x2160 | 3840x2160 |
| 3 | Colour tags | verify-render.py | PASS | bt709 / bt709 / bt709 | bt709 / bt709 / bt709 |
| 4 | Video bitrate | verify-render.py | PASS | 45.8 Mb/s | >= 40 Mb/s |
| 5 | Duration | verify-render.py --index | PASS | 38.200 s | 38.200 s ± 0.033 |
| 6 | A/V sync | verify-render.py | PASS | 0.021 s | under 0.12 s |
| 7 | Clipped words | verify-render.py --words --kept | PASS | 0 of 96 missing | 0 |
| 8 | Every sound present | sound subtraction | PASS | 2 of 2 found | every sfx row found |
| 9 | Motion at transitions | ffmpeg frame strips | PASS | 9 windows, smooth | no jump-then-crawl, dead stop or 1-frame pop |
| 10 | Loudness | ffmpeg ebur128 | NOTE | -24.7 LUFS (camera level) | a part: levelled to -14 at assembly |
| 11 | True peak | ffmpeg ebur128 | NOTE | -6.8 dBTP | a part: checked on the master |
| 12 | Lip sync | flat frame vs source | N/A | - | hook under 60 s |
| 13 | Safe zones (reels) | render-sheet.png | N/A | - | 16:9 file |
| 14 | Frame rate | ffprobe | PASS | 30/1, constant | 30 fps, constant |

### Sounds

| asset | sound | at | window RMS | control RMS | Result |
|---|---|---|---|---|---|
| r04 | pop | 11.92 | 640 | 28 / 31 | PASS |
| r05 | typing | 19.30 | 410 | 27 / 30 | PASS |

### Failures

None.

### Verdict

**PASS**. Deliver.

---

## v1 · hook · attempt 2 · PASS

| | |
|---|---|
| **File** | output-4k.mp4 |
| **md5** | 2d9b7f13… (example) |
| **Composition** | public/index.html |
| **Checked** | 2026-10-05 17:20 |
| **Reports** | VERIFY.md, render-sheet.png, qa/v1-2/strips/ |

### Checks

| # | Check | Tool | Result | Measured | Expected |
|---|---|---|---|---|---|
| 1 | Black frames and flashes | verify-render.py (blackdetect) | PASS | none | none |
| 2 | Size | verify-render.py --res | PASS | 3840x2160 | 3840x2160 |
| 3 | Colour tags | verify-render.py | PASS | bt709 / bt709 / bt709 | bt709 / bt709 / bt709 |
| 4 | Video bitrate | verify-render.py | PASS | 46.2 Mb/s | >= 40 Mb/s |
| 5 | Duration | verify-render.py --index | PASS | 38.200 s | 38.200 s ± 0.033 |
| 6 | A/V sync | verify-render.py | PASS | 0.019 s | under 0.12 s |
| 7 | Clipped words | verify-render.py --words --kept | PASS | 0 of 96 missing | 0 |
| 8 | Every sound present | sound subtraction | PASS | 2 of 2 found | every sfx row found |
| 9 | Motion at transitions | ffmpeg frame strips | PASS | 9 windows, smooth | no jump-then-crawl, dead stop or 1-frame pop |
| 10 | Loudness | ffmpeg ebur128 | NOTE | -24.9 LUFS (camera level) | a part: levelled to -14 at assembly |
| 11 | True peak | ffmpeg ebur128 | NOTE | -7.1 dBTP | a part: checked on the master |
| 12 | Lip sync | flat frame vs source | N/A | - | hook under 60 s |
| 13 | Safe zones (reels) | render-sheet.png | N/A | - | 16:9 file |
| 14 | Frame rate | ffprobe | PASS | 30/1, constant | 30 fps, constant |

### Sounds

| asset | sound | at | window RMS | control RMS | Result |
|---|---|---|---|---|---|
| r04 | pop | 11.92 | 655 | 29 / 31 | PASS |
| r05 | typing | 19.30 | 405 | 28 / 30 | PASS |

### Failures

None. Q1 and Q2 from attempt 1 are fixed.

### Verdict

**PASS**. Deliver.

---

## v1 · hook · attempt 1 · FAIL

| | |
|---|---|
| **File** | output-4k.mp4 |
| **md5** | a0c3e58e… (example) |
| **Composition** | public/index.html |
| **Checked** | 2026-10-05 16:58 |
| **Reports** | VERIFY.md, render-sheet.png, qa/v1-1/strips/ |

### Checks

| # | Check | Tool | Result | Measured | Expected |
|---|---|---|---|---|---|
| 1 | Black frames and flashes | verify-render.py (blackdetect) | FAIL | 14.000 to 14.067 s (2 frames) | none |
| 2 | Size | verify-render.py --res | PASS | 3840x2160 | 3840x2160 |
| 3 | Colour tags | verify-render.py | PASS | bt709 / bt709 / bt709 | bt709 / bt709 / bt709 |
| 4 | Video bitrate | verify-render.py | PASS | 45.9 Mb/s | >= 40 Mb/s |
| 5 | Duration | verify-render.py --index | PASS | 38.200 s | 38.200 s ± 0.033 |
| 6 | A/V sync | verify-render.py | PASS | 0.020 s | under 0.12 s |
| 7 | Clipped words | verify-render.py --words --kept | PASS | 0 of 96 missing | 0 |
| 8 | Every sound present | sound subtraction | FAIL | 1 of 2 found | every sfx row found |
| 9 | Motion at transitions | ffmpeg frame strips | PASS | 9 windows, smooth | no jump-then-crawl, dead stop or 1-frame pop |
| 10 | Loudness | ffmpeg ebur128 | NOTE | -24.9 LUFS (camera level) | a part: levelled to -14 at assembly |
| 11 | True peak | ffmpeg ebur128 | NOTE | -7.1 dBTP | a part: checked on the master |
| 12 | Lip sync | flat frame vs source | N/A | - | hook under 60 s |
| 13 | Safe zones (reels) | render-sheet.png | N/A | - | 16:9 file |
| 14 | Frame rate | ffprobe | PASS | 30/1, constant | 30 fps, constant |

### Sounds

| asset | sound | at | window RMS | control RMS | Result |
|---|---|---|---|---|---|
| r04 | pop | 11.92 | 31 | 29 / 30 | FAIL |
| r05 | typing | 19.30 | 408 | 28 / 30 | PASS |

### Failures

| id | at | Check | What was seen | Owner of the fix | Suggested fix |
|---|---|---|---|---|---|
| Q1 | 14.000 | 1 Black frames | a 2-frame black flash under the glass card entrance; rendered with 4 parallel workers | Renderer | re-render with `--workers 1` |
| Q2 | 11.92 | 8 Sound present | the pop window measures like the quiet controls; `<audio>` for the pop has no `id` | Animator | give the pop's `<audio>` an `id` and its own track index, rebuild |

### Verdict

**FAIL**. Do not deliver: fix Q1 and Q2, render again, check again.
