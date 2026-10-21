# Research: faceless explainer reels with an AI voice

Background research behind the Explainer profile. Every finding is either a rule in
[`skill/explainer/PLAYBOOK.md`](skill/explainer/PLAYBOOK.md) (cited as **§E1**, **§E2**...) or a deliberate decision
not to adopt it. The short-form basics this profile shares with Reels (the canvas, the safe zone, the first seconds,
loudness) are in the [Reels research](../reels/RESEARCH.md) and not repeated.

Researched 2026-10-14. Advice on faceless and AI-voiced video comes mostly from tool vendors and production studios;
platform rules on AI labels change often. Confidence levels as in the other research files:

| Level | Meaning |
|---|---|
| **Official** | the platform's or the project's own documentation |
| **Documented** | named reporting with specifics, or a feature that exists |
| **Practice** | widely repeated working practice; sources agree on the idea, not on numbers |
| **Vendor** | a single tool vendor, studio or agency; a starting point, never a hard rule |

---

## 1. The reference this profile was built from

| # | Finding | Level | Source |
|---|---|---|---|
| X1 | The Instagram reel the creator supplied (87 s) was decompiled frame by frame: about 10 real cuts; every graphic is code-drawn (HTML and GSAP-like motion, not stock); word captions with a highlight box; three backgrounds (blue gradient, black, light with a dot grid); an AI voice at about -14 LUFS with a 2.1 LU range; a continuous music bed; a talking-avatar mascot from a paid service. | Documented (our own measurement) | the creator's file; `ffprobe`, `ebur128`, scene detection |

**Became:** §E0 (the three layers and backgrounds), §E5 (captions with the highlight box), the scene library. The paid
avatar was dropped (free tools only).

## 2. Hooks and structure

| # | Finding | Level | Source |
|---|---|---|---|
| H1 | With no face on screen, the first line of script and the first frame of motion carry the opening; slow logo intros and channel greetings lose viewers. Outcome, number, contrarian-fact and unfinished-list hooks are the common forms. | Vendor | [ShortsFast](https://shortsfast.com/blog/faceless-shorts-hooks-retention-2026/), [Postiz](https://postiz.com/tools/instagram-reels-hook-generator) |
| H2 | On-screen hook text works best short (about 5 to 8 words) and bold, because many watch without sound. | Vendor | [Skeepers](https://community.skeepers.io/blog/writing-text-hooks/) |
| H3 | Animated graphics and dramatic text in the opening seconds strengthen a hook. | Vendor | [Syllaby](https://syllaby.io/blog/ai-hook-generator-for-reels/) |
| H4 | Widely quoted "70% decide in two seconds" style figures trace back to one unverified report. | Vendor (unverified) | [ShortsFast](https://shortsfast.com/blog/faceless-shorts-hooks-retention-2026/) |

**Became:** §E1 (the hook is line 0, at most 12 spoken words, a specific promise, on screen by 0.3 s; one idea; the
ending is the payoff or the call to action). The 12-word limit is ours: a spoken hook of about 4 s, with the on-screen
title shorter still (H2). The unverified percentages are not used.

## 3. Script length and voice pace

| # | Finding | Level | Source |
|---|---|---|---|
| P1 | Explainer studios plan voiceover at about **140 to 150 words a minute**; a 60 s script is roughly 140 to 160 words; over about 160 words a minute is "too fast". | Practice | [Bread n Beyond](https://breadnbeyond.com/how-many-words-does-a-60-seconds-explainer-video-needs/), [Video Explainers](https://videoexplainers.com/blog/how-to-write-explainer-video-script), [Stimme24](https://www.stimme24.com/en/guide/explainer-video-script/) |
| P2 | If a script runs long, cut words; don't speed up the read. | Practice | [Video Explainers](https://videoexplainers.com/blog/how-to-write-explainer-video-script), [Yum Yum Videos](https://www.yumyumvideos.com/blog/short-vs-long-videos-explainer-video-length-wp/) |

**Became:** §E2.1 uses **2.7 words a second (162 a minute)**, the top of the studios' range, because a reel runs
brisker than a product explainer and the length gate allows ±10% on the voice. **Open:** the real Kokoro rate at speed
1.0 is measured on the first project (the voice's `duration` against the word count); if it reads slower, the Writer's
estimate runs short and the rate in `script-check.py` gets corrected by the Librarian. §E3.2 keeps speed at 1.0 to 1.1
(P2: cut, don't rush).

## 4. Captions

| # | Finding | Level | Source |
|---|---|---|---|
| C1 | Word-by-word captions with the active word highlighted are the dominant short-form style; vendors claim large retention gains over static subtitles, with no published study behind the numbers. | Vendor | [Opus](https://www.opus.pro/blog/best-caption-presets-styles-boost-retention), [BlitzCut](https://blitzcutai.com/blog/animated-captions-vs-static-captions), [OpenClip](https://openclip.app/guides/caption-animation-guide) |
| C2 | The most credible independent figure is about captions in general: in a 2019 Verizon Media / Publicis survey, 80% said they were more likely to finish a video with captions. | Documented | summarised by [ClipSpeed](https://clipspeed.ai/blog/ai-captions-increase-views.html) |
| C3 | The highlight works as a moving focal point the eye follows (a plausible mechanism, not tested). | Vendor | [OpenClip](https://openclip.app/use-cases/karaoke-captions.md) |

**Became:** §E5: captions always on, a few words at a time, the spoken word turning from dim to full colour, and the
highlight box only on emphasis words (as in the reference, X1). No retention number is claimed for it.

## 5. The voice: licence and disclosure

| # | Finding | Level | Source |
|---|---|---|---|
| V1 | **Kokoro-82M is Apache-2.0**, code and weights: "With Apache-licensed weights, Kokoro can be deployed anywhere from production environments to personal projects." (SPEC §13 item 1, checked.) Earlier community copies were labelled MIT; the current release is Apache-2.0. | Official | [hexgrad/kokoro](https://github.com/hexgrad/kokoro) |
| V2 | Kokoro's text-to-phoneme step (misaki) can fall back to **espeak-ng** for words outside its dictionary; espeak-ng is GPL-licensed and installed separately from the system's packages. It runs as a separate tool; nothing of it ships in the reel. | Documented | [misaki on PyPI](https://pypi.org/project/misaki/) |
| V3 | **Meta (Instagram, Facebook):** creators must label content with "realistic-sounding audio" that was digitally generated or altered, including with AI; a reel narrated by a realistic AI voiceover is one of Meta's own examples. The label is shown as "AI info" (earlier "Made with AI"); Meta may apply it itself and may penalise undisclosed content. | Official (via summaries; the help page could not be fetched from here) | [Instagram Help](https://help.instagram.com/761121959519495), [gradually.ai](https://www.gradually.ai/en/instagram-ai-label/), [Minter](https://minter.io/blog/everything-you-need-to-know-about-ai-labels-on-instagram/), [Axios](https://www.axios.com/2024/02/06/meta-ai-labeling-fix-oversight-board) |
| V4 | **YouTube (Shorts):** the "altered or synthetic content" setting is for realistic content a viewer could take as real (a real person saying what they didn't, real events that didn't happen); a generic text-to-speech narrator is generally exempt. | Documented (secondary) | [AIR Media-Tech](https://air.io/en/youtube-glossary/what-is-youtubes-ai-content-disclosure-policy), [gofaceless.ai](https://www.gofaceless.ai/blog/youtube-ai-policy-updates), [PPC Land](https://ppc.land/youtube-introduces-mandatory-disclosure-for-ai-content/) |
| V5 | **TikTok:** creators label AI-generated content that contains realistic images, audio or video, with the AI-generated label or a caption; misleading synthetic media of real people is removed. | Documented (secondary) | [Social Media Today](https://www.socialmediatoday.com/news/tiktok-officially-launches-new-in-stream-labels-for-ai-generated-content/694154/), [Cinerads](https://www.cinerads.com/blog/tiktok-ai-content-policy) |

**Became:** §E0 (Kokoro, free and local), §E3.6 and the Producer's delivery step: the posting checklist tells the
creator to turn on Instagram's AI label for an AI-voiced reel (Meta names exactly this case), and to check YouTube's
and TikTok's current rules when cross-posting. The voice never imitates a real person.

## 6. Libraries in the picture

| # | Finding | Level | Source |
|---|---|---|---|
| L1 | KaTeX (formulas) is MIT; Lucide icons (`lucide-static`) are ISC; three.js is MIT; GSAP is free to use (its standard licence); DM Sans and JetBrains Mono are under the SIL Open Font License, which allows bundling with the licence text. | Official | the packages' licence files (`npm pack`) |

**Became:** §E0. The fonts ship in `skill/explainer/assets/fonts/` with their OFL texts; the libraries are fetched once
with `npm pack` into `assets/vendor/` so renders work offline.

## 6a. What informative short-form explainers do (three articles, 2026-10-16)

Read from the text the creator pasted (the sites are not reachable from the build machine): Doodle Video, *How to
Create TikTok Explainer Videos in 2025*; SpeakerHub, *Pro Tips for Making Explainer Videos That Elevate Your Message*;
CustomerThink, *From Boring to Brilliant: 7 Pro Tips to Create Engaging Explainer Videos*. Practitioner advice, not
studies; adopted where it fits a faceless reel, in intent where the letter does not.

| Tip | Where it lives |
|---|---|
| Short, one idea, clear; "a quick how-to in under 30 seconds", "smarter in less than a minute" (Doodle) | length 30 to 90 s, 30 to 60 s for most (§E1.2, `script-check.py`); one idea or a series |
| A hook that stops the scroll, then simple visual terms (Doodle) | the kinetic hook (§E6.9); a picture for every line (§E2.7) |
| Captions, since many watch with the sound off (Doodle) | word captions, burned in (§E5) |
| End with a call to action: follow, link in bio, comment (Doodle); goals and audience first (CustomerThink #1) | `goal`, `audience` and a CTA that asks for the goal (§E1.0, a warning in `script-check.py`) |
| What to share: how-tos, this vs that, myth busting, case studies and mini stories (Doodle) | `format` and its shape: steps, a compare picture, myth then truth, problem then solution (§E1.3) |
| Trends and sounds only when they fit (Doodle) | the posting checklist: a trending sound added in the app, under the voice, only when it fits |
| Consistency, analytics, a few hashtags (Doodle) | the posting checklist and the analyst comparing reels by format, length and goal |
| Break the fourth wall, a conversational tone (SpeakerHub) | "you" and contractions (§E2.8, a warning) |
| Interactivity: questions that invite comments (SpeakerHub) | one question to the viewer (§E2.8, a warning) |
| Concise, simple language, the key concept early (SpeakerHub) | one idea, short lines, plain words, why it matters as line 2 (§E1, §E2) |
| A strong visual identity: brand colours, consistent fonts and text overlays (SpeakerHub, CustomerThink #2) | the Latte theme and roles; the creator's handle on every frame (`brand.handle`) |
| Real-world examples, case studies, anecdotes (SpeakerHub, CustomerThink #4) | one line with `role: example` (§E2.8, a warning) |
| Data as animated graphs and charts (SpeakerHub, CustomerThink #5) | count-up, bars, line-chart, sheet |
| Creative visual direction: split screen, animation, inserts, transitions not overdone (SpeakerHub, CustomerThink #2) | compare, the build-up scenes, velocity-matched cuts; MOTION.md "flair for flair is noise" |
| Tell a story: problem-solution, hero's journey, personal anecdote (SpeakerHub, CustomerThink #4) | the story format (§E1.3) |
| Humour, well placed and sparing (SpeakerHub, CustomerThink #7) | one light line where it serves the point (§E2.8); not checked |
| A series rather than a one-off (SpeakerHub) | `brand.series` and `brand.part`: "PART n" on every frame; a CTA that promises the next |
| Sound design: no noise, normalised, music and effects at key moments, a chime that marks the key point (CustomerThink #3) | a clean local voice levelled to -16 LUFS, the ducked bed, whooshes and pops, and a chime on the payoff (§E3.8) |
| A voice that matches the tone (CustomerThink #6) | the channel voice picked from samples at Checkpoint A (§E3.1) |
| Collaborate with other creators (SpeakerHub) | not a production step: the creator's call |

## 7. Not adopted

- **A talking avatar or mascot** (the reference has one): every capable avatar service found is paid. A custom scene
  can draw a simple character if a creator wants one.
- **Voice cloning of the creator:** free local options exist, but cloning a real person's voice raises the disclosure
  bar on every platform (V3 to V5); out of scope for version 1.
- **Retention percentages** for hooks and captions (H4, C1): vendor figures with no study behind them.

## Credits: ideas taken from other open-source projects (2026-10-21)

Read and compared against this kit; the rules were kept, their unsourced numbers were not.

| Project (licence) | What we took | Where it lives |
|---|---|---|
| [sergebulaev/instagram-skills](https://github.com/sergebulaev/instagram-skills) (MIT) | the caption writer's rules (a hook in the first 125 characters, one ask with a reason, no dead closer, sized hashtags) and the humanizer's scrub list (leaked AI text, reveal bridges, "it's not X, it's Y", sincerity markers, staccato) with its "do not over-correct" guard | `post-check.py`, `wording.py` / `wording.json` (kit); explainer PLAYBOOK §E2.9; reels PLAYBOOK §R13 |
| [Jakeschincariol/instagram-agent-skill](https://github.com/Jakeschincariol/instagram-agent-skill) (MIT) | the hook dealbreakers (a greeting, "in this video", "stop scrolling", a hashtag or emoji in a spoken hook), stock phrases from its slop list, invisible characters, and its hook formulas as angles to offer the creator; not its hook score (its own README reports it cannot tell a creator's hits from their misses) nor its automatic rewriting (it changes meaning) | `wording.py` / `wording.json`; the Writer's hook angles |
| [Anil-matcha/AI-Youtube-Shorts-Generator](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator) (MIT) | the eight signals for picking reels from a long video, the one-command entry point, and following the speaker's face (per segment here, not per frame); not its paid services, its clipper or its chunked highlight code | `reels-moments.py`, reels PLAYBOOK §R12; `wf.py`; `reels-face-x.py` |
| [storytold/filmcraft](https://github.com/storytold/filmcraft) (MIT OR Apache-2.0) | the editor the hand-off is made for: it imports our FCP 7 XML and `.srt`, and `filmcraft-cli` makes the native project and reads it back for the checks | `nle_xml.py`, `filmcraft.py` (kit); every profile's hand-off |
