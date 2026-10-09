# Long-form playbook

The editing doctrine for YouTube long-form videos. Every long-form agent reads the sections its brief names, cited as
**§L0** to **§L14**. It sits on top of the kit's rulebook, `.claude/skills/youtube-edit/SKILL.md` (cited as
**SKILL › section**), and the creator's `STYLE-GUIDE.md`.

**Precedence when rules disagree:**
1. Hard requirements: YouTube's published rules (§L11, §L12), licences, never covering the face, never working around
   a block, never inventing a claim.
2. The creator's notes on **this** video (NOTES.md).
3. `STYLE-GUIDE.md`, then SKILL.md: the look and the house rules.
4. This playbook.
5. Research defaults (the numbers marked *default*), which the creator's own retention data overrides (§L13).

Where each rule comes from is in `RESEARCH.md` (R1, R2...). Numbers marked *default* are starting points.

---

## §L0 What "long-form" means here

- A video of roughly **8 to 25 minutes**: a hook, then two to six **sections**, each with its own intro beat, ending on
  the payoff of the main promise. Videos over 8 minutes are eligible for mid-roll ads (§L12).
- Recorded as one long take, several clips, or one clip per section, often with screen recordings.
- **Composed per section, joined at assembly** (SKILL › Long-form doctrine): each section is its own composition with
  its own storyboard, render and QA, so a note costs one section's render, and no composition exceeds the
  heavy-overlay budget.
- **Free tools only:** free software and free licences, nothing else. Never Tella, Epidemic Sound, paid stock or
  music, AI-generated footage (the kit's AI B-roll route), paid AI video services such as Motion (motion.so), or a paid
  trial. When something can only be had by paying, the beat changes: a screen recording, a real page, free stock or a
  diagram built with the kit.
- Section folders: `videos/<project>/<NN-slug>/` (e.g. `00-hook/`, `01-the-problem/`). The project folder keeps the
  raw files, the full cut, `STATUS.md`, `NOTES.md` and `assembly.json`.

## §L1 The promise

The title and thumbnail make a promise; the video exists to keep it.

- The Producer records the **brief** before planning (STATUS.md › Brief): working title, thumbnail idea, the one-line
  promise, who it is for, target length, sponsor (yes/no), any must-show moments.
- **The first minute delivers what the thumbnail shows and the title says** (R3). If the thumbnail shows a result, that
  result appears in the first minute, at least as a glimpse.
- List the **questions a viewer has after the title and thumbnail** (R4). The hook answers the first and opens the
  rest; each section closes one.
- The **main promise is paid off before any call to action** (SKILL › The hook gate) and before the end-screen zone.
- Never promise in the edit what the footage doesn't contain. A tease of a later moment must be a real moment from
  later in the video.

## §L2 The hook (0 to 30 s)

YouTube measures the intro at **30 s**; over half the audience still watching there is "above typical" (R1).

**Shape** (*default*, R5):

| Time | Job | Typical devices |
|---|---|---|
| 0 to 3 s | a reason to stay: the most interesting true thing, on a meaningful first frame | the result, a striking line, motion from frame one |
| 3 to ~10 s | prove the title is true | proof on screen: your screen, the number, the thing itself |
| ~10 to 20 s | why it matters to this viewer | the stakes, one line |
| ~20 to 30 s | the roadmap or the open loop | slot wall (9c) or numbered deck (40) planted empty |

**Rules:**
- Open on substance, never a greeting, a channel name or "in this video". Those move after the hook or go.
- **Front-load:** a 1 to 3 s glimpse of the best moment from later in the video may open the hook (R2), cut as a
  flash-forward, its source time noted in the storyboard.
- **It works muted:** the first overlay states the promise on its own.
- **The first spoken word survives:** no sound, card entrance or cut lands on it.
- Tighter pacing than the body: about 6 overlay moments per 37 s and 3 to 5 camera moves per 40 s (SKILL › Pacing,
  Camera). Motion from the first frame.
- Plant **one main loop** (and at most one secondary) with a payoff time: `"loops": [{"question", "planted",
  "payoff"}]` in the hook's storyboard. Checked at Checkpoint B and in the assembled master.

## §L3 Structure: sections, loops and transitions

- **Sections are an argument, not a list.** Write the section order as one line per section joined by **but** or
  **therefore** (R7). A join that can only be written as "and then" is a weak transition: the Director flags it at
  Checkpoint A, so you can reorder, cut, or bridge it with a line you record.
- **Each section** opens with its chapter fixture (progress tag 9b, slot wall 9c or numbered deck 40; SKILL ›
  Sections), states its question in the first sentence, answers it, and ends by opening the next question
  (**re-hook**, R9). A section's last beat is never a dead end.
- **Re-engagement points** (*default*, R10): put a strong beat (a reveal, a demo result, a surprising number, a joke)
  near the **3-minute** and **6-minute** marks of the assembled video, and at every section boundary. If the
  footage has none there, the Director says so; it does not invent one.
- **Open loops:** one main, one secondary at most, each closed on screen (the slot fills, the ghosted stack completes),
  never "we'll come back to this" (SKILL › Long-form doctrine).
- **Breathers** (R12): after a big payoff, hold 1 to 2 s on the result or your reaction before the next section
  starts. Not dead air: a held picture under room tone or the music bed.
- **One persistent world:** a long video is one space the camera moves through, with a spatial grammar decided once
  (left to right = toward the outcome, up = a person, down = the system). SKILL › Long-form doctrine.

## §L4 Pacing

The shape (R15), with the kit's numbers as the floor (SKILL › Long-form doctrine, Pacing):

| Stretch | Nothing-on-screen gap limit | Density | Feel |
|---|---|---|---|
| Hook (0 to ~30 s) | none over ~5 s | ~6 overlay moments per 37 s; 3 to 5 camera moves per 40 s | energy |
| First 90 s | 15 s | about 7 overlays + 7 camera moves per 90 s | energy, then orientation |
| Body | 20 s | about 7 + 7 per 90 s, *lower is fine where the content is dense* | clarity |
| Ever | 30 s | | |

- **"Something changes" means a meaningful change**: a cutaway that illustrates, a card that lands on its word, a
  camera move with a reason. Decoration doesn't count (R14, R16). `gap-scan.py` counts overlays and camera moves; the
  Director judges whether each one earns its place.
- **Pattern interrupts go where attention will dip**, not on a timer (R14): before a long explanation, after a dense
  stretch, at the 3 and 6 minute marks, and wherever the creator's past retention graphs dip (§L13).
- **Against over-stimulation** (R12, R17): no shouting cuts, no stacked effects, no 3D flips, no bounces. One hero
  element at a time. Dense edits keep their density inside a card (a new element about every second), not in the
  number of cards (SKILL › The teardown).
- **Cards hold 3 to 7 s**; past 7 s they need internal motion. Enter 0.4 s `power2.out`, exit 0.35 s `power2.in`.
- **Never divide a section evenly** into equal-length beats; follow the speech.

## §L5 Cutting doctrine

- **Last take wins; the cut is decided by sound** (SKILL › Cut stage): sentence starts from Parakeet, ends from the
  audio; edge-audit to 0; dead air to 0 (no pause over 0.40 s after a sentence, 0.45 s elsewhere).
- **Murch's order as the tie-breaker** (R22): when two cuts compete, choose for **emotion** (does it keep the feeling
  of the moment: a held laugh, a pause after a hard line), then **story** (does it reveal something new), then
  **rhythm**, then **eye trace**. A deliberate pause that carries meaning is kept with `--keep T` or `A-B!`, and noted
  in PAPER-CUT.md so you can see why.
- **Tangents:** a stretch that doesn't serve the section's question is marked as a candidate cut at Checkpoint A
  (reason "tangent"), never cut silently. You decide.
- **Repetition across sections:** the same point made twice in different sections is flagged at Checkpoint A with both
  times.
- **Split edits (J and L cuts, R24)**, inside a section (a single-camera talking video has one voice track, so a split
  edit means the picture changes at a different moment from the sentence):
  - **The house default is picture first:** a card or cutaway lands 0.15 to 0.25 s before its word (STYLE-GUIDE.md
    "a beat before I say it").
  - **L out of a cutaway:** a cutaway may hold 0.2 to 0.5 s past the end of its sentence before returning to you, so
    the image settles before your face comes back.
  - **J into a cutaway (the exception):** for an emotional or reflective line, the sentence starts on your face and the
    cutaway arrives as the key word lands. Named as a deliberate choice in the storyboard (`"split": "J"` in the
    beat's note), never by accident.
  - **Section boundaries are hard joins:** `assemble.py` joins sections end to end, so audio cannot run across a
    boundary. Soften a boundary inside the next section instead: it opens on its chapter fixture and the first word
    starts 0.2 to 0.4 s in, over the fixture.
  - Keep the room tone continuous across every cut; a jump in background noise gives the edit away.
- **Jump cuts stay naked by default** (SKILL › Camera); dress one only when the energy changes; at most one per 10 s
  in long form; cutaways go on jump cuts first (`cut-map.json`).
- **Eye trace** (R23): a card enters where the eye already is (near your face or the previous card), never across the
  frame from it; a cutaway that follows a card keeps the subject near the card's position.

## §L6 Visual coverage

- **Your face is not the default background** (SKILL › Long-form doctrine): aim for **40 % or more** of a talking
  section full-frame (cutaways, diagrams, world scenes, screen recordings).
- **B-roll illustrates; it never decorates** (R16): every cutaway shows what the sentence says. If a viewer couldn't
  say in three words what a shot shows and why it is there, it goes.
- **Proof over illustration:** your own screen recordings and real pages first, then archive, then stock. Stock never
  stands in for proof.
- **A person or job you name gets 2.5 to 3.5 s of footage of that person**, right after you describe them.
- **An app you name gets a designed window; a website you name gets the real page** (SKILL › Long-form doctrine).
- **Explainers are found, not requested** (SKILL › Finding explainers): enumeration, "the way this works is", chained
  causation, stage words. Propose each diagram before building it.
- **Documents and maps breathe** (R39): a page or diagram gets one move (push to the passage, highlight, hold), not
  constant motion. Hold long enough to read: about 2 s per short line of on-screen text plus 1 s.
- **Variety:** never the same device twice in a row; no list panels in a long-form body (each list becomes pills, a
  world loop, one device per number, a pipeline). The format chooser in SKILL › When two formats compete decides
  ties.

## §L7 Camera

All of SKILL › Camera applies. Long-form specifics:
- **Creeps carry thoughts, punches mark points:** a 110 to 112 % creep over a 5 to 10 s explanation; a 118 to 125 %
  punch only on the word that matters (the number, the turn, the punchline).
- **One gesture, not two moves** (SKILL › Long-form doctrine): two moves in a row on one subject merge into one.
- **At most one dressed jump cut per 10 s**; `set 1.0` on the exact jump frame at every cut; never carry a zoom
  across a cut.
- **Switch framing between jump cuts on long camera-only stretches** (1.0 / 1.09) so each reads as a punch, not a
  bump.

## §L8 Text on screen

- **About 20 on-screen words per section**, no sentences; everything reads in under 2 s (SKILL › Long-form doctrine).
- The **lower line** is the default for a single line of copy; **key-word highlight (12)** for two or three words in
  long form; **no word-by-word burned-in captions** in long form (they belong to Shorts and Reels; R37).
- **Numbers in full digits** (`$207,000,000`), counted up; money in amber; one gradient per frame; highlighted words
  never dark blue (STYLE-GUIDE.md).
- **Chapter fixtures** name sections in 2 to 4 words in your phrasing.

## §L9 Sound

- **Silence is the default; a sound needs a physical cause on screen** (SKILL › Sound). The allowed list and volumes
  are in SKILL › Sound and the workflow README § 6.7. One or two per hook; long form about one per 30 s at most.
- **Music** (R26, SKILL › Sound):
  - a track with some tension under the hook (~18 s), then a calm bed under the body;
  - ducked about **16 dB (hook) and 19 dB (body)** under your voice, rising in gaps and breathers;
  - **a change of bed may mark a new section or a change of mood** (one per section at most), crossfaded over 1 to
    2 s on the section boundary, never mid-sentence;
  - no music under a dense explanation if it competes; drop it 3 to 6 dB further there;
  - **how it is built:** `assemble.py` joins and levels the voice-only master first. Its own `music` key is a single
    loop at one flat level, so long form doesn't use it. The Sound designer then builds one full-length bed timed to
    the section start times in `ASSEMBLY.md`, and the Assembler ducks it under the voice with the sidechain command
    in SKILL › Sound, keeping the voice-only master as the no-music twin;
  - the final master is **-14 LUFS integrated, true peak under -1 dBTP** (R27); if adding the bed moved it by more
    than 1 LU, the Assembler re-levels the audio (video stream copied).
- **Voice polish (opt-in)** (R25): offered when the voice is muddy, noisy or harsh. The Sound designer renders a
  10 to 15 s **before/after pair** for you to listen to at Checkpoint B; only with your yes is the chain applied to
  the flat cut's audio (picture untouched, timing unchanged). Starting chain (*default*):
  `highpass=f=80` (100 to 120 for a higher voice) → `afftdn=nr=8` (light) → `equalizer=f=300:t=q:w=1.2:g=-2` →
  `equalizer=f=3500:t=q:w=1.0:g=2` → `acompressor=threshold=-20dB:ratio=2.5:attack=20:release=200` → `deesser`.
  The original audio is kept; the chain is recorded in ASSET-REQUESTS.md as a row of kind `voice`.
- **Room tone everywhere there is no speech**, never digital silence (SKILL › Edges).
- **Check on small speakers:** the QA agent's loudness check is the measurement; your listen on a phone is the
  judgement. Agents never claim to have listened.

## §L10 Colour

- **Measure, match, never grade without approval** (R28 to R30). At ingest the Ingest agent measures each clip
  (average luma, black and white points, colour cast from `signalstats`) and flags clips that differ from the
  reference clip (the first talking-head clip).
- A **correction** (exposure, white balance, matching a second camera) is proposed at Checkpoint A with a before/after
  still; applied only with your yes, before the cut is encoded.
- A **creative look** is a style-guide decision, not a per-video one.
- The skin-tone line shows hue direction only (R29); never neutralise deliberate coloured light.
- Every file is tagged **BT.709** (SKILL › Traps: the render drops two tags).

## §L11 Sponsors and disclosures

- **A sponsor segment is its own section** (`NN-sponsor/`), with its own chapter ("Sponsor: <brand>" or the
  creator's wording), composed with the same house style, and **never part of the hook**. Typical placement:
  after the hook and the first section's opening, at a natural break (a convention, not a rule; the creator decides).
- **Disclosure:** the Producer reminds you to declare the paid promotion / branded content in YouTube Studio for any
  video with a sponsor, a product placement or an endorsement (R35); the wording in Studio may have changed.
- **No AI shots** (§L0): the team never generates footage. If the creator supplies realistic synthetic footage of a
  person, place or event themselves, it needs YouTube's altered or synthetic content label (R36).
- **Claims:** every on-screen number, quote or headline comes from a real source recorded in ASSET-REQUESTS.md; client
  messages are real (with permission) or labelled as an example.

## §L12 The delivery package

What the Assembler hands over, next to the master:

| File | Rules |
|---|---|
| `<project>-full-4k.mp4` | 3840x2160, the recorded frame rate (30), H.264 High, AAC 48 kHz stereo, moov at the front, BT.709 tags, **35 to 45 Mb/s** at 30 fps (53 to 68 at 60) (R31); -14 LUFS, true peak under -1 dBTP |
| `<project>-full-4k-nomusic.mp4` | the same without the music bed (when there is music) |
| `chapters.txt` | first line `0:00`, **at least 3 chapters, each at least 10 s, in order**, `M:SS` under an hour, `H:MM:SS` over (R32). The Assembler validates these; a broken rule silently disables chapters |
| `captions.srt` | closed captions from the delivered words (§L12 below), for upload "with timing" (R37) |
| `ad-breaks.txt` | for videos of 8 minutes or more: suggested manual mid-roll times at natural breaks (R34) |
| `STORYBOARD.md` | time / beat / on screen, every stock clip with page, licence and seconds, credits |
| `DESCRIPTION.md` | chapters, credits, links you said "in the description", disclosure reminders |
| `ASSEMBLY.md`, md5 | from `assemble.py` |

- **End-screen zone** (R33): the **last 20 s** carry no overlay in the end-screen element areas (the right half and
  the lower centre on 16:9); keep talking, B-roll or the closing line there. No outro card (SKILL › Rejected).
- **Captions:** built from the transcript of the **delivered master** (the final words, after every cut), one cue per
  phrase, at most 2 lines of about 42 characters, 1 to 6 s each, never spanning a section boundary; names and terms
  spelled as in the script or the creator's notes.
- **Ad breaks:** candidates at section boundaries and at breathers, at least 2 minutes apart, never mid-sentence,
  never inside the hook or the sponsor segment; the creator places them in YouTube Studio.

## §L13 After publishing: learning from retention

The research can't settle cadence numbers; the creator's audience can.

- After a video has been live about a week, you can hand the Producer a **screenshot or CSV export** of YouTube
  Studio's retention graph. The Analyst maps it onto the delivered `STORYBOARD.md` (master times) and `chapters.txt`.
- How to read it (R1, R6, R38):
  - **intro** (the 30 s point): under ~50 % → the hook didn't keep the promise; compare the first 30 s with §L2;
  - **dips**: the beat on screen 0 to 10 s before the dip is the suspect (a slow explanation, a tangent, a repeated
    point, a missing re-hook);
  - **spikes**: rewatches: either the best moment (keep doing that) or a confusing one (clarify);
  - **slow slide** through the middle: pacing or structure (§L3, §L4), not the hook;
  - the grey band is the channel's own last 10 videos of similar length: compare with that, not with other channels.
- Each finding becomes **one proposed rule** for the Librarian, saved only when you agree. Over time the *default*
  numbers in this playbook get replaced by numbers from your own channel.

## §L14 Long-form failure patterns (check before Checkpoint B)

| Pattern | Looks like | Fix |
|---|---|---|
| Promise drift | the first minute is about something the thumbnail doesn't show | move the proof forward (§L1) |
| Greeting open | "Hey guys, welcome back" in the first 3 s | cut or move after the hook (§L2) |
| "And then" chain | sections joined only by sequence | reorder, bridge, or cut (§L3) |
| Dead middle | a body stretch with no re-hook for minutes | find a beat to move or plant a question (§L3) |
| Wallpaper B-roll | cutaways that don't illustrate the sentence | replace with proof or remove (§L6) |
| Overstim | effects stacked, cards back to back, no breathers | remove, hold, breathe (§L4) |
| Face default | long stretches of only your face | full-frame scenes for abstract ideas (§L6) |
| Unclosed loop | a planted question never answered on screen | close it, or don't plant it (§L3) |
| CTA before payoff | "subscribe" or a pitch before the promise is kept | move it after the payoff (§L1) |
| Cluttered ending | cards in the last 20 s | clear the end-screen zone (§L12) |
| Silent chapters | chapters that break a rule | fix `chapters.txt` (§L12) |
