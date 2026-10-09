<!--
ASSET-REQUESTS.md: every asset the plan needs, who gets it, where it came from, and whether we may use it.
One ledger from request to licence.

Written by: the Director adds rows and fills the REQUEST columns (id, kind, beat, at, dur, spec, owner).
            The owner agent fills the FULFILMENT columns of its own rows only (state, file, source, licence, used, note).
            The Producer may set state to needs-you and record your answer in note.
Read by:    the Animator (it starts only when the gate below holds), the Assembler (stock clips and credits go into
            STORYBOARD.md), the QA agent (every sfx row is a sound it must find in the render), you.
Created:    at Plan (Stage 5), copied from Editing-Workflow/templates/ASSET-REQUESTS.md.

Rules
- One row per file the composition will use. The same logo used twice is one row; two different clips are two rows.
- id: r01, r02 ... never reused, never renumbered. A row that is no longer needed becomes state "dropped", not deleted.
- kind and owner come from the tables in Editing-Workflow/templates/README.md.
- spec says exactly what is needed, in one line. The owner must not have to guess.
- state is one of: open | in-progress | filled | skip | needs-you | dropped
  - skip:      the owner could not get it within the rules; note says why; the Director picks another format.
  - needs-you: only you can supply or decide it (a person's photo, a screen recording); the Producer asks you.
- filled needs file, source and licence. A row without a licence is not filled.
- THE GATE (G6): the Animator starts only when no row is open, in-progress or needs-you.
- Paths are relative to this project folder. Times are seconds in the flat cut (transcript.json time).
Full field definitions: Editing-Workflow/templates/README.md
-->

# {project}: ASSET REQUESTS

| | |
|---|---|
| **Project** | {project} |
| **Profile** | {youtube \| reels} |
| **Storyboard** | {storyboard.json, or the part: hook/storyboard.json} |
| **Version** | {v1} |
| **Gate G6** | {open: N rows left \| clear} |
| **Updated** | {YYYY-MM-DD HH:MM} |

## Requests

| id | kind | beat | at | dur | spec | owner | state | file | source | licence | used | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| r01 | {kind} | {beat id} | {s} | {s} | {exactly what} | {agent} | open | - | - | - | - | - |

## Credits

Everything whose licence asks for credit, copied into the video description and STORYBOARD.md by the Assembler.

| id | Credit line |
|---|---|
