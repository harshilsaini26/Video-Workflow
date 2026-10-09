# Reels playbook

The editing doctrine for short vertical videos: Instagram Reels first, and the same file posts as a YouTube Short and a
TikTok. Every Reels agent reads the sections its brief names, cited as **§R0** to **§R14**. It sits on top of the kit's
rulebook (`.claude/skills/youtube-edit/SKILL.md`, cited as **SKILL › section**) and the creator's `STYLE-GUIDE.md`.
**Free tools only** (§R10).

**Precedence when rules disagree:** (1) platform rules, licences, never covering the face, never working around a
block, never inventing a claim; (2) the creator's notes on this reel; (3) STYLE-GUIDE.md, then SKILL.md; (4) this
playbook; (5) the *default* numbers, which the creator's own Insights override (§R13).

Where each rule comes from: `RESEARCH.md` (S1, S2...). Numbers marked *default* are starting points.

---

## §R0 The profile

| | |
|---|---|
| Canvas | **1080x1920**, 9:16 (S1) |
| Frame rate | **60 fps**, constant (S2). Record at 60; never convert 30 to 60 by doubling frames |
| Record | 4K **vertical** (2160x3840) at 60 fps: zooms up to ~2x stay sharp. 1080x1920 at 60: zoom at most 1.12. A 4K landscape source can be cropped (§R12) |
| Length | **15 to 60 s** by default; up to 3 minutes (Reels and Shorts, S3). One idea per reel |
| Composition | one composition (no sections): `reels-compose.py` builds it at 1080x1920, 60 fps |
| Delivery | H.264 High in MP4, AAC 48 kHz stereo, **about 20 Mb/s** (S2), BT.709 tags, -14 LUFS integrated, true peak under -1 dBTP |
| One file | the same master posts as a Reel, a Short and a TikTok; the safe zone (§R3) is the strictest of the three |

## §R1 What a reel is for

Instagram ranks Reels mostly on **watch time, likes per reach and sends** (S8), and tests each one on a small pool first
(S10). So every reel is built for three things: **watched to the end**, **watched again**, **sent to someone**.

- **One idea**, stated as a one-line promise in the brief (STATUS.md › Brief), with its **payoff** (the moment the
  promise is kept) and its **send-worthy moment** (the line or result someone would forward).
- If the footage has no payoff, the Director says so at Checkpoint A. A reel without a payoff is not fixed in the edit.

## §R2 The hook (0 to 3 s)

The first second decides whether anyone sees the second one (S13); Instagram's Insights now report the **skip rate**,
viewers gone in the first 3 s (S12).

- **Frame one means something**: the result, the face mid-sentence, the object. Never black, a settling camera, a logo
  sting, a greeting or the creator's name. `reels-compose.py` warns when nothing lands in the first 0.5 s.
- **Hook text on screen by 0.3 s**, at most 60 characters (the composer enforces it), readable in about a second,
  stating the promise for a muted viewer.
- **Open on the strongest line.** If the best line is said later, the Cutter moves it to the front (the cut list keeps
  any order) and the reel then plays from the setup, so the opening plays twice in effect: once as the hook, once in
  context, never as a repeated clip of more than about 2 s.
- **The first spoken word survives**: no sound, card entrance or cut lands on it.
- Hook types that work (S13): the result first; a specific claim with a number; a question the viewer has; a mistake
  ("stop doing X"); a before/after.

## §R3 The safe zone

Instagram, TikTok and Shorts lay buttons, captions and the audio line over the video (S5 to S7). One zone for all
three, Meta's published box (the strictest):

| Area | Pixels on 1080x1920 | Rule |
|---|---|---|
| Top band | 0 to 269 | no text, logo or face detail |
| Bottom band | 1248 to 1920 | no text, logo or captions |
| Sides | 65 each side | nothing important |
| Action column band | below y 960, the outer 150 px each side | centred content narrows to 780 px |
| Caption slot | x 150 to 930, y 1050 to 1248 | the burned-in captions live here |

- `reels-compose.py` places every format inside this box **by construction** and fails the build when a block would
  cross it (`reels_lib.SAFE`). Wrapping text is measured at the column it actually gets (the narrow 780 px one below
  y 960), and a block that reaches into the caption slot while captions show fails too: move it up, shorten it, or
  switch captions off over that beat (§R5). Every format's height matches what Chromium draws (measured), and a pill
  or a count-up number, which never wrap, fails when it is wider than its column.
- `reels-safezone.py` draws the zone on every snapshot (red: covered, orange: the action-column band, cyan: the caption
  slot). The Animator and QA look at the guided sheet, not the bare stills.
- **The face** sits in the upper middle (roughly y 350 to 950): set `video_position` (the crop) and `origin` (the
  zoom anchor) so the eyes stay there, and put text where the face isn't (`pos`: top, mid or low).
- Anything within 20 px of a band edge: the QA agent asks the creator for one real phone preview before posting.

## §R4 Pacing

- **Dead air**: no pause over **0.30 s** (0.25 s after a sentence) (*default*, S14):
  `dead-air.py W --plan --max 0.30 --max-sentence 0.25 --target 0.15`.
- **Something meaningful changes every 2 to 4 s** (*default*): a cut, a camera move, a card, a cutaway. Captions
  changing don't count. Checked with the kit's gap-scan:
  `gap-scan.py --index public/index.html --early 4 --body 6 --max 8`.
- **Cards hold 1.5 to 4 s.** Enter 0.4 s, exit 0.3 s; no bounces, no 3D flips, no flash cuts, no stacked effects
  (SKILL › Rejected).
- **Jump cuts read as intentional:** alternate the framing at each jump cut (`["set", t, 1.0]` / `["set", t, 1.08]`)
  so a cut lands as a punch, not a skip (S14 shot lengths; SKILL › Camera's framing switch).
- **One hero element at a time** (plus the captions). Never the same device twice in a row (the composer warns).
- Fast is not frantic: an explainer keeps a beat to read each card (S14).

## §R5 Captions and text

- **Burned-in captions always** (S18, S19), built by `reels-compose.py` from the transcript of the **final cut**:
  1 to 3 words at a time (`max_words`), at most 18 characters (`max_chars`), 84 px *default* (64 to 100), the word
  being said turns **cyan**, money in **amber** (`money`), key words in cyan (`em`). Trailing commas and full stops go;
  ? ! $ % stay. **Names spelled right on screen:** `terms` (the brief's names and products) and `replace` (a word
  Parakeet misheard) fix the displayed words; the timing stays Parakeet's.
- **Captions off** (`off` ranges) only where on-screen text already says the same words (often the hook) or a
  cutaway carries its own text. Never off for more than about 3 s.
- **On-screen copy:** the hook 60 characters at most; a headline 2 to 3 lines; steps 22 characters each, 5 at most;
  about 12 words on screen at once, captions included.
- **Numbers in full digits** (`$1,000`, never `$1K`), counted up with `stat`; money amber; highlighted words never
  dark blue (STYLE-GUIDE.md).
- **SRT too:** `reels-captions.py` writes `captions.srt` for Shorts, TikTok and Facebook, with the brief's terms
  spelled right.

## §R6 The ending and the loop

- **End on the payoff**, or on the line right after it. No outro, end card, "thanks for watching" or fade to black
  (a fade kills the loop) (S15, SKILL › Rejected).
- **The loop:** where it is natural, the last line leads back into the first ("...and that's why" → "Stop paying
  for editing"); the last frame's framing matches the first (same scale, same position). Noted in the storyboard's
  `loop` and checked at Checkpoint B.
- **A call to action** is optional, spoken or a `chip`, in the last 2 s at most, never before the payoff (comment a
  word, follow for part 2, the full video on the channel).

## §R7 Sound and music

- **Silence is the default; a sound needs a physical cause on screen** (SKILL › Sound): pop on a logo (0.34), click on
  a cursor click (0.28), typing for exactly the typing time (0.22), a notification only on a phone notification, a
  cha-ching at 0.07 on a money count. Never a whoosh under text. One or two per reel.
- **Music** (S22 to S24), one of:
  1. **none in the file**, and the creator adds audio in the app when posting (trending audio, or the Meta Sound
     Collection on a business account), kept low under the voice; or
  2. **in the file**, from a free licensed source only: Pixabay (save the licence page; some tracks are registered with
     Content ID), Freesound **CC0 only**, or the HyperFrames library; about **18 dB under the voice** (*default*), the
     master levelled to -14 LUFS.
- **Voice polish** is opt-in, offered as a before/after pair (as in long-form PLAYBOOK §L9); agents never claim to
  have listened.
- **Room tone** in every pause, never digital silence (SKILL › Edges).

## §R8 The formats

What `reels-compose.py` builds (JSON shapes in its docstring). Every one has an `anchor`; text formats take `pos`
(top, mid, low).

| Format | Use for | Notes |
|---|---|---|
| `hook` | the first 0.3 to 3 s | ≤ 60 characters, 96 px *default*, words rise in, key words cyan; `box: true` on bright footage |
| `headline` | a statement mid-reel | 84 px, 2 to 3 lines |
| `point` | one big word or step ("Step 2") with a sub line | 132 px; colour cyan, amber or white |
| `steps` | a numbered list said out loud | glass card, items arrive on their words, 5 at most, 22 characters each |
| `pills` | 1 to 5 short labels | a centred column; tone cyan for the one that matters, amber for a risk |
| `logo` | naming a tool | glass plate, logo only (you say the name), one pop |
| `chip` | the punchline, a CTA | magenta emphasis on dark glass, usually `pos: low` |
| `stat` | one number that matters | counts up in full digits; money amber |
| `clip` | B-roll, a screen recording, archive | full-frame vertical cutaway (conform it first), optional label |
| `image` | a screenshot or page | on the dark wash with a slow push |

- **Choosing:** a list said out loud → `steps` (or `pills` for one-to-three-word labels); a tool → `logo`; a number →
  `stat`; a joke or the turn → `chip`; anything you show rather than say → `clip` or `image`.
- **Landscape sources** become vertical with `reels-conform.py`: `--fit blur` (the source whole over a blurred copy,
  best for screen recordings), `--fit cover --focus 0..1` (crop), `--fit contain` (rarely).
- Anything the composer doesn't build goes in `raw_html` / `raw_js`, inside the safe zone, following SKILL ›
  Animating glass and Traps.

## §R9 Originality

- **Only original, unwatermarked work** (S9, S11): never a clip with another app's watermark, never a repost. Third-party
  material is used only when licensed and transformed (your commentary, graphics, narration); a credit line is not a
  transformation.
- **Proof is real:** your own screen recordings and real pages; stock never stands in for a result.
- Generated (AI) footage is outside the free profile; if the creator supplies some, a realistic AI shot needs the
  platform's AI label (YouTube's altered-content disclosure; the long-form RESEARCH R36).

## §R10 Free tools only

| Job | Free tool or source |
|---|---|
| Edit, transcribe, render | the kit: Parakeet (English, European languages) or Whisper large-v3 (Hindi and others), auto-editor, FFmpeg, HyperFrames (+ GSAP, a free library) |
| Screen recording | OBS Studio, or the OS recorder (macOS Screenshot toolbar, Windows Game Bar / Snipping Tool) |
| Stock footage | Pexels (free API key), Coverr, Mixkit free licence |
| Logos, pages | the brand's press kit; `npx hyperframes capture`; headless Chrome |
| Sound effects | the HyperFrames library (Pixabay Content License), Pixabay, Freesound **CC0 only** |
| Music | none in the file (add in-app), Pixabay Music, Freesound CC0 |
| Fonts | DM Sans (SIL Open Font License, in the kit) |

**Excluded:** Tella, Epidemic Sound, paid stock, AI image or video generation (including AI motion-design services
such as Motion, motion.so), anything with a free trial that turns paid. Claude itself is the one paid tool (the
creator's plan).

## §R11 Camera

- `origin` **"50% 28%"** *default* (the zoom anchors near the eyes so the head never crops); `video_position` sets the
  crop of a non-vertical source.
- **Punch** 1.12 to 1.20 on the word that matters; **creep** 1.00 → 1.06 across a thought; `release` before a cutaway.
- **At most 1.6** (the composer enforces it); a 1080p source at most 1.12.
- **Alternate framing at jump cuts** (§R4); never carry a zoom into a cutaway.

## §R12 The long-form → reel route

Turning a long video into reels (S17). Most of the work is choosing.

1. **Pick moments that stand alone:** a single point with its own hook (a question, a surprising number, a demo, a
   strong opinion), 15 to 60 s, that needs nothing said earlier. The Director lists candidates with times from the
   long-form transcript, why each works, and its hook line.
2. **Cut from the best source:** the raw 4K source (not the delivered master: no long-form overlays, no burned-in
   graphics). A 4K landscape source is cropped to vertical with `video_position` (the face's x position, e.g.
   `"38% 50%"`); check the crop on stills.
3. **Make it stand alone:** cut "as I said earlier", "in this video", "next"; add the missing setup as on-screen text
   or a recorded line; write a **new hook** for the reel (the creator can record a 3 s line).
4. **Point back** only after the payoff: a `chip` "Full video on my channel" in the last 2 s, if the creator wants it.
5. Each reel is its own project folder (`videos/<long-project>-reel-<n>/`) and goes through every gate.

## §R13 Delivery, posting and Insights

**The package** (the Packager): `reel.mp4` (§R0 spec), `cover.jpg` (a 1080x1920 frame the creator picks, its key
content inside the centre **1080x1440** so the profile grid crop keeps it), `captions.srt`, `POST.md` (the post caption
draft: the first ~125 characters carry the hook (S21), 3 to 5 relevant hashtags, any credits; the posting checklist),
`STORYBOARD.md`.

**Posting checklist:** post as a Reel (not a feed video); the cover set; music added in-app if chosen (low under the
voice); no watermark; the same file to Shorts and TikTok if wanted (upload `captions.srt` where accepted).

**After about a week** (§R1, S12): the creator sends a screenshot of Instagram's Insights for the reel (skip rate,
retention chart, average watch time, sends and shares), or YouTube Studio's Shorts retention. The Analyst maps it onto
`STORYBOARD.md`:
- **skip rate** high → the first 3 s (§R2);
- a **drop** on the retention chart → the beat 0 to 2 s before it;
- a curve that **flattens** after 1 to 2 s → healthy;
- **average watch time** read against the reel's length and the creator's own history, never an outside benchmark.
Findings become at most three proposed rules; the creator decides; the Librarian saves.

## §R14 Reel failure patterns (check before Checkpoint B)

| Pattern | Looks like | Fix |
|---|---|---|
| Slow open | a greeting, a logo, a settling camera in the first second | open on the strongest line (§R2) |
| Silent hook | the first 2 s mean nothing with the sound off | hook text by 0.3 s (§R2) |
| Under the UI | text or a face detail in a red band on the guided sheet | move it (§R3) |
| Caption clash | captions over other text, or captions off for long | `off` only where text repeats the words (§R5) |
| Dead air | pauses over 0.30 s | the dead-air loop (§R4) |
| Static stretch | 6 s with nothing new | a camera move, a card, a cutaway (§R4) |
| Overstim | stacked effects, card after card, no beat to read | remove, hold (§R4) |
| Context missing | "as I said earlier" in a cut from long-form | cut it, add setup (§R12) |
| Dead end | a fade out, an outro, "thanks for watching" | end on the payoff, loop (§R6) |
| Unlicensed or watermarked | a track or clip without a free licence, another app's watermark | replace (§R9, §R10) |
