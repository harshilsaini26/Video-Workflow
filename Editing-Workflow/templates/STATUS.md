<!--
STATUS.md: where this video is, and who it is waiting on.

Written by: the Producer ONLY. Agents report to the Producer; they never edit this file.
Read by:    you, the Producer, any new conversation that picks the project up.
Created:    at ingest (Stage 2), copied from Editing-Workflow/templates/STATUS.md.
Updated:    at every hand-off: an agent starts, an agent reports, a gate passes or fails, you answer.

Rules
- Replace every {placeholder}. Leave a cell "-" when it does not apply yet.
- The Stages table always has all 15 rows, in this order. Change State, Owner, Gate, Updated and Note only.
- State is one of: not-started | in-progress | waiting-on-you | blocked | failed | done | skipped
- "failed" means a gate failed and the fix is routed; "blocked" means nobody can continue until something outside the
  workflow changes (a missing file, a tool that will not install). Every blocked or failed row has a row in Blockers.
- A new version (v2, v3...) resets stages 5 to 11 to not-started, unless the note only touches a later stage
  (e.g. a render glitch resets 8 to 10 only). Stages 2 to 4 reset only when the cut changes.
- Never delete rows from Versions, Decisions, Blockers or Log. Close them instead.
- Times are local: YYYY-MM-DD HH:MM. Paths are relative to this folder.
Full field definitions: Editing-Workflow/templates/README.md
-->

# {project}: STATUS

| | |
|---|---|
| **Project** | {project} |
| **Profile** | {youtube \| reels} |
| **Parts** | {one part, or the list: hook, intro-01, section-01 ...} |
| **Version** | {v1} |
| **Current stage** | {stage number and name} |
| **Waiting on** | {you \| agent name \| nobody} |
| **Next step** | {one sentence} |
| **Updated** | {YYYY-MM-DD HH:MM} |

## Stages

| # | Stage | State | Owner | Gate | Updated | Note |
|---|---|---|---|---|---|---|
| 1 | Record | not-started | you | - | - | - |
| 2 | Ingest | not-started | Ingest agent | G1 | - | - |
| 3 | Transcribe | not-started | Transcriber | - | - | - |
| 4 | Cut | not-started | Cutter | G2 G3 G4 | - | - |
| A | Checkpoint A: the cut | not-started | you | A | - | - |
| 5 | Plan | not-started | Director | G5 | - | - |
| 6 | Assets | not-started | Researcher, B-roll scout, Sound designer | G6 | - | - |
| 7 | Compose | not-started | Animator | G7 G8 G9 | - | - |
| B | Checkpoint B: the plan | not-started | you | B | - | - |
| 8 | Render | not-started | Renderer | - | - | - |
| 9 | Verify | not-started | QA agent | G10 G11 | - | - |
| 10 | Assemble and deliver | not-started | Assembler | G12 | - | - |
| 11 | Notes | not-started | you | - | - | - |
| 12 | Learn | not-started | Librarian | G13 | - | - |
| - | Done | not-started | you | - | - | - |

## Versions

| Version | Started | Why | QA | Delivered | File |
|---|---|---|---|---|---|
| v1 | {YYYY-MM-DD HH:MM} | first edit | - | - | - |

## Decisions for you

| id | Asked | Question | Options | Answer | Answered |
|---|---|---|---|---|---|

## Blockers

| id | Since | Stage | What is stuck | Owner | Next step | Closed |
|---|---|---|---|---|---|---|

## Log

Newest at the bottom. One line per event: an agent started or reported, a gate passed or failed, you answered.

| Time | Who | Event |
|---|---|---|
| {YYYY-MM-DD HH:MM} | Producer | project created |
