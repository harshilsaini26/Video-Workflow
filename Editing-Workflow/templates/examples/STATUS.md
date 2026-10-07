<!-- EXAMPLE: a made-up project, filled in to show how the template is used. Not a real video. -->

# ai-tools-hook: STATUS

| | |
|---|---|
| **Project** | ai-tools-hook |
| **Profile** | youtube |
| **Parts** | one part: hook (38.2 s) |
| **Version** | v2 |
| **Current stage** | 10 Assemble and deliver |
| **Waiting on** | Assembler |
| **Next step** | Assembler levels v2 to -14 LUFS and writes STORYBOARD.md; then you watch v2 |
| **Updated** | 2026-10-06 16:42 |

## Stages

| # | Stage | State | Owner | Gate | Updated | Note |
|---|---|---|---|---|---|---|
| 1 | Record | done | you | - | 2026-10-05 09:40 | 1 clip, C0001.MP4, 4K 30 fps, 2:11 |
| 2 | Ingest | done | Ingest agent | G1 | 2026-10-05 10:04 | 1 clip, sound present |
| 3 | Transcribe | done | Transcriber | - | 2026-10-05 10:31 | flat cut re-transcribed after the last apply-cut |
| 4 | Cut | done | Cutter | G2 G3 G4 | 2026-10-05 10:30 | 2:11 → 38.2 s; 0 edge issues; 0 pauses; no drift |
| A | Checkpoint A: the cut | done | you | A | 2026-10-05 11:02 | A01, A02 applied |
| 5 | Plan | done | Director | G5 | 2026-10-06 14:55 | v2: n01, n03, n04 applied; 9 beats |
| 6 | Assets | done | Researcher, B-roll scout, Sound designer | G6 | 2026-10-06 15:10 | v2: r06 music re-ducked (n02) |
| 7 | Compose | done | Animator | G7 G8 G9 | 2026-10-06 15:31 | compose, check, beat-check clean; gap-scan n/a (hook) |
| B | Checkpoint B: the plan | done | you | B | 2026-10-06 15:48 | v2 stills approved |
| 8 | Render | done | Renderer | - | 2026-10-06 16:20 | 4K, 1 worker, 1 min 20 s |
| 9 | Verify | done | QA agent | G10 G11 | 2026-10-06 16:38 | v2 attempt 1 PASS |
| 10 | Assemble and deliver | in-progress | Assembler | G12 | 2026-10-06 16:42 | one-segment assembly levels v2 to -14 LUFS; then QA on the master |
| 11 | Notes | not-started | you | - | - | waiting for v2 |
| 12 | Learn | done | Librarian | G13 | 2026-10-06 14:20 | n02 saved to SKILL.md "Sound"; tests OK |
| - | Done | not-started | you | - | - | - |

## Versions

| Version | Started | Why | QA | Delivered | File |
|---|---|---|---|---|---|
| v1 | 2026-10-05 10:02 | first edit | FAIL (attempt 1), PASS (attempt 2) | 2026-10-05 17:25 | ~/Movies/YouTube Renders/ai-tools-hook/ai-tools-hook-v1-4k.mp4 |
| v2 | 2026-10-06 14:05 | notes n01 to n04 | PASS (attempt 1) | - | - |

## Decisions for you

| id | Asked | Question | Options | Answer | Answered |
|---|---|---|---|---|---|
| D01 | 2026-10-05 12:10 | The list at 0:18 to 0:30 could be a flow diagram instead. Build it? | yes / no, keep the list | no, keep it as a list | 2026-10-05 12:14 |
| D02 | 2026-10-05 12:40 | r07 needs a photo of the guest. Can you send one? | send a photo / skip the photo | skip the photo | 2026-10-05 12:52 |
| D03 | 2026-10-06 14:02 | n04 "make this a little bit better": which part feels weakest? | pacing / the cards / the sound / something else | the last 10 seconds drag | 2026-10-06 14:04 |

## Blockers

| id | Since | Stage | What is stuck | Owner | Next step | Closed |
|---|---|---|---|---|---|---|
| K01 | 2026-10-05 10:05 | 3 | Parakeet model not installed; transcribe would fall back to another engine | Transcriber | `npx hyperframes models install parakeet` | 2026-10-05 10:11 |
| K02 | 2026-10-05 16:58 | 9 | QA FAIL on v1 attempt 1 (Q1 flash, Q2 missing pop) | Renderer, Animator | re-render with 1 worker; add the missing audio id | 2026-10-05 17:20 |

## Log

| Time | Who | Event |
|---|---|---|
| 2026-10-05 10:02 | Producer | project created; profile youtube |
| 2026-10-05 10:04 | Ingest agent | reported: 1 clip, 2:11.4, 3840x2160, 29.97 fps, sound OK |
| 2026-10-05 10:05 | Transcriber | blocked: Parakeet missing (K01) |
| 2026-10-05 10:11 | Transcriber | reported: transcript-raw.json, 338 words |
| 2026-10-05 10:30 | Cutter | reported: 38.2 s flat cut; G2 G3 G4 pass |
| 2026-10-05 10:32 | Producer | Checkpoint A sent (PAPER-CUT.md) |
| 2026-10-05 11:02 | you | Checkpoint A answered: A01, A02 |
| 2026-10-05 11:20 | Cutter | A01, A02 applied; gates pass again |
| 2026-10-05 12:10 | Director | storyboard v1, 9 beats, r01 to r08; asked D01 |
| 2026-10-05 12:14 | you | D01: keep the list |
| 2026-10-05 12:15 | Producer | started Researcher, B-roll scout, Sound designer in parallel |
| 2026-10-05 12:40 | Producer | asked D02 (r07 photo) |
| 2026-10-05 12:52 | you | D02: skip the photo; r07 dropped |
| 2026-10-05 13:30 | Researcher | r08 skip (post blocked); Director swapped beat xp for a chip |
| 2026-10-05 13:45 | Producer | G6 clear |
| 2026-10-05 14:20 | Animator | compose, check, beat-check clean; snaps/sheet.png |
| 2026-10-05 14:22 | Producer | Checkpoint B sent |
| 2026-10-05 15:05 | you | Checkpoint B answered: B01, B02 |
| 2026-10-05 15:40 | Director, Animator | B01, B02 applied; stills re-sent; you approved at 15:52 |
| 2026-10-05 16:40 | Renderer | v1 attempt 1 rendered (4 workers) |
| 2026-10-05 16:58 | QA agent | v1 attempt 1 FAIL: Q1, Q2 (K02) |
| 2026-10-05 17:10 | Renderer | v1 attempt 2 rendered (1 worker); Animator added sfx-pop id |
| 2026-10-05 17:20 | QA agent | v1 attempt 2 PASS |
| 2026-10-05 17:25 | Assembler | v1 delivered, md5 matches |
| 2026-10-06 13:58 | you | notes on v1: n01 to n04 |
| 2026-10-06 14:02 | Producer | asked D03 (n04 unclear) |
| 2026-10-06 14:05 | Producer | v2 started; stages 5 to 11 reset |
| 2026-10-06 14:20 | Librarian | n02 saved to SKILL.md "Sound" (replaced the 16 dB rule); tests OK |
| 2026-10-06 15:48 | you | v2 stills approved |
| 2026-10-06 16:38 | QA agent | v2 attempt 1 PASS |
| 2026-10-06 16:42 | Producer | Assembler started |
