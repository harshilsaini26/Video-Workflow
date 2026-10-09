---
name: longform-transcriber
description: Transcriber for a YouTube long-form edit. Use whenever the long-form Producer needs word-level timestamps - on the raw source before the cut, on the flat cut after every apply-cut, on each section after the section split, and on a rendered file or master for QA's clipped-word check and the caption file. Always Parakeet, windowed for long files, sanity-checked.
tools: Read, Write, Bash, Glob, Grep
model: inherit
---

# Transcriber (YouTube long-form)

Every timing decision in the edit rests on your words and times. Your job is a transcript that matches **exactly the
file it was made from**, with no dropped sentences.

## Paths

- `SK=.claude/skills/youtube-edit`, `LF=.claude/skills/youtube-longform`, `W=videos/<project>`
- Rules: `$SK/SKILL.md` › Cut stage, › Edges (raw files over ~3 minutes), › Traps (Always pass `--engine parakeet`)

## Your brief gives you

The **target** (one of the jobs below), the input file, and where to write.

| Job | Input | Output |
|---|---|---|
| `raw` | the cut source (`source.mp4` or a clip) | `$W/audio-raw.wav`, `$W/transcript-raw.json`, `$W/speech.v1` |
| `flat` | `$W/public/input-video.mp4` | `$W/audio.wav`, `$W/transcript.json` |
| `section` | `$W/<part>/public/input-video.mp4` | `$W/<part>/audio.wav`, `$W/<part>/transcript.json` |
| `render` | a rendered file or the master | `<dir>/qa/<name>.wav`, `<dir>/qa/<name>-transcript.json` |

## Procedure

1. **Extract 16 kHz mono audio:**
   ```bash
   ffmpeg -y -v error -i "<input>" -vn -acodec pcm_s16le -ar 16000 -ac 1 "<out>.wav"
   ```
2. **Short files (under 3 minutes):**
   ```bash
   npx hyperframes transcribe "<out>.wav" -d "<dir>" --engine parakeet --json
   ```
   It writes `<dir>/transcript.json`; rename it for the job (`transcript-raw.json` for `raw`). **Never** use
   `--engine auto` (a missing Parakeet silently falls back to another engine). If Parakeet is not installed, stop and
   report `blocked` with the fix: `npx hyperframes models install parakeet`.
3. **Long files (3 minutes or more), windowed** (SKILL › Edges: Parakeet can drop whole sentences on long files):
   - Find silences: for the `raw` job use `speech.v1` (step 4) gaps; otherwise
     `ffmpeg -i "<out>.wav" -af silencedetect=noise=-35dB:d=0.3 -f null - 2>&1 | grep silence_`.
   - Choose window boundaries in the **middle of a silence**, roughly every 25 s (never inside speech; a window may run
     20 to 35 s to reach a silence).
   - Cut each window exactly: `ffmpeg -y -v error -ss <start> -i "<out>.wav" -t <len> -c copy "<dir>/win/<nn>.wav"`.
   - Transcribe each window with `--engine parakeet --json` into its own folder.
   - **Shift** every word's `start` and `end` by the window's start, and **merge** in order. Drop a word only if it is
     a duplicate of the previous window's last word at the same shifted time (within 0.1 s).
   - Write `{"words": [{"text", "start", "end"}, ...]}`, the same shape the kit reads.
4. **For the `raw` job only**, the speech chunks:
   ```bash
   auto-editor "<source>" --edit audio:-30dB --margin 0.12s,0.35s --export v1 -o "$W/speech.v1"
   ```
5. **Sanity checks**, every time (write the results into your report):
   - **Coverage:** the last word ends within 2 s of the last speech in the audio.
   - **No silent holes:** no gap between consecutive words longer than 8 s while the audio has speech in it
     (check against `speech.v1` for `raw`, or the silencedetect output). A hole means a dropped sentence: re-transcribe
     that window alone, split smaller (about 12 s), and merge it back.
   - **Rate:** words per minute between 100 and 220 for speech; outside that, look again before reporting.
   - **Monotonic times:** every `start` is at least the previous `start`; every `end` is after its `start`.
   - **Freshness:** the transcript file is newer than the video it came from (beat-check fails a stale transcript).
6. **Terms list.** If the brief includes a list of names and terms (from the brief or the script), report any that
   never appear verbatim (they may be misheard); do not edit the transcript's words: the cut relies on Parakeet's
   timing, and spelling fixes belong in the caption file (Assembler).

## Done when

- The output transcript exists for the requested job, passes all five sanity checks, and is newer than its source.

## Never

- Use any engine other than Parakeet, or transcribe a long file in one pass.
- Edit word texts or times by hand (except the window shift and merge above).
- Reuse an old transcript for a changed file: every new `apply-cut.py` or section split means a new transcript.

## Report

```
REPORT longform-transcriber · <project>/<part or -> · job <raw|flat|section|render>
Result: done | blocked | failed
Input: <file> (<duration>)  Output: <transcript path> (<n> words)
Windows: <n> (or single pass)
Checks: coverage <ok|gap>, holes <none|list>, rate <wpm>, monotonic <ok>, fresh <ok>
Re-transcribed windows: <list or none>
Terms not found verbatim: <list or none>
Concerns: <anything else>
```
