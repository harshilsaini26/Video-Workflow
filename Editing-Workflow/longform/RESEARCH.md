# Research: how professional long-form YouTubers edit

Background research behind the YouTube long-form agents. Every finding here is either a rule in
[`skill/youtube-longform/PLAYBOOK.md`](skill/youtube-longform/PLAYBOOK.md) (cited as **§L1**, **§L2**...) or a deliberate
decision not to adopt it, with the reason.

Researched 2026-10-08. Most material on YouTube editing is creator commentary, agency blogs and tool vendors, not
controlled studies. So every finding carries a confidence level:

| Level | Meaning |
|---|---|
| **Official** | YouTube's own Help Center or blog, or a published standard |
| **Documented** | a named creator or editor describing their own practice, or reporting with data (Tubefilter's cut counts) |
| **Practice** | widely repeated working practice among editors; sources agree on the idea, not on exact numbers |
| **Vendor** | a single blog or tool vendor; a starting point, never a hard rule |

The agents treat **Official** facts as hard requirements, **Documented** and **Practice** findings as defaults, and
**Vendor** numbers only as starting points that the creator's own retention data overrides (§L13).

---

## 1. The opening decides the video

| # | Finding | Level | Source |
|---|---|---|---|
| R1 | YouTube's retention report measures the **intro at 30 seconds**; videos where at least half the audience is still watching at that mark are "above typical intros". | Official | [YouTube Help: Measure key moments for audience retention](https://support.google.com/youtube/answer/9314415?hl=en) |
| R2 | The first minute is where viewers are most likely to leave; **front-load**: tease the best moments inside the first 60 s, then stop telling and start showing. | Documented (leaked MrBeast production guide, authenticity confirmed by two former producers to Passionfruit) | [Tubefilter](https://www.tubefilter.com/2024/09/17/mrbeast-internal-production-guide-leaked-key-points/), [Passionfruit](https://passionfru.it/mrbeast-leaked-document-81151/), [OMR](https://omr.com/de/daily/mrbeast-doc-pdf-leak) |
| R3 | The first minute must **deliver what the thumbnail and title promise**. | Documented (same guide) | as R2 |
| R4 | Strategist Paddy Galloway puts most effort into the intro; intros open storylines with unanswered questions. Exercise: list the questions a viewer has after the title and thumbnail, and answer or open them in the intro. | Documented (secondhand summaries of his podcast appearances) | [Colin and Samir](https://www.colinandsamir.com/resources/the-new-rules-of-youtube-from-paddy-galloway), [Creator Science](https://podcast.creatorscience.com/paddy-galloway/), [scaleviews summary](https://scaleviews.beehiiv.com/p/how-paddy-galloway-forever-broke-the-youtube-algorithm) |
| R5 | A working shape for the opening: prove the title is true in about 10 s, say why it matters in the next 10, give a one-line roadmap; open on a real example, not a greeting or your name. | Practice | [OutlierKit](https://outlierkit.com/resources/youtube-hooks-and-retention/), [GetResponse](https://www.getresponse.com/blog/youtube-hacks) |
| R6 | A sharp drop in the first 30 s is a hook problem; a slow slide through the middle is a retention problem. | Practice | [OutlierKit](https://outlierkit.com/resources/youtube-hooks-and-retention/) |

**Became:** §L1 (the promise), §L2 (the hook), §L13 (reading the retention graph).

## 2. Structure: loops, re-hooks and "but / therefore"

| # | Finding | Level | Source |
|---|---|---|---|
| R7 | **And, But, Therefore** (Trey Parker's "replace *and then* with *but* and *therefore*", formalised by Randy Olson as ABT): setup, complication, consequence. | Documented (as a writing method; no retention study) | [The Good Points](https://thegoodpoints.substack.com/p/and-but-therefore), [PR Daily](https://prdaily.com/?p=316639), [ABT concept](https://concepts.dsebastien.net/concept/abt-storytelling/) |
| R8 | An **open loop** is a question, delayed result or promised explanation that gives a reason to keep watching; open it with a specific expectation, close it with the answer. One or two per video; more erodes trust. | Practice (count is Vendor) | [Creator Essentials: open loop](https://www.creatoressentials.com/glossary/open-loop/), [Subscribr](https://subscribr.ai/youtube-strategy/storytelling-youtube-content-strategy) |
| R9 | One hook at the start is not enough: after each payoff, open the next question (**re-hook**). | Practice | [Subscribr](https://subscribr.ai/youtube-strategy/storytelling-youtube-content-strategy), [OutlierKit](https://outlierkit.com/resources/youtube-hooks-and-retention/) |
| R10 | MrBeast's guide places **re-engagement** beats around minutes 3 and 6 and treats minutes 3 to 6 as the next most important stretch after the first minute. | Documented | [Tubefilter](https://www.tubefilter.com/2024/09/17/mrbeast-internal-production-guide-leaked-key-points/), [Creator Handbook](https://www.creatorhandbook.net/leaked-document-allegedly-reveals-mrbeasts-secrets-to-youtube-success-the-key-takeaways/) |
| R11 | Story first, camera second: "the biggest mistake filmmakers make is turning on a camera before writing their story" (Samir Chaudry); a three-act structure underlies their teaching. | Documented | [Musicbed: Colin and Samir](https://musicbed.com/articles/?p=4386), [course listing](https://www.shopmoment.com/products/youtube-storytelling-how-to-make-videos-people-share-colin-and-samir) |

**Became:** §L3 (structure, loops, re-hooks, transitions). The kit already had "one main loop, one secondary at most"
and "close the promised lesson before any call to action"; the research confirms both.

## 3. Pacing: the move away from over-stimulation

| # | Finding | Level | Source |
|---|---|---|---|
| R12 | In March 2024 MrBeast said his team had **slowed videos down**, focused on story, added breathers between scenes and cut the yelling, and that views rose; he called the "ultra fast paced / overstim" style one that "doesn't even work". | Documented | [Tubefilter](https://tubefilter.com/2024/03/04/mrbeast-editing-style-number-of-cuts-per-video/), [Gigazine](https://gigazine.net/gsc_news/en/20240403-retention-editing-beastification-may-be-end), [Passionfruit](https://passionfru.it/youtube-editing-mrbeast-54202/) |
| R13 | Tubefilter counted **38 cuts per minute** in a March 2023 MrBeast video against **23** in a 2024 one (one minute sampled from each); average 90-day views rose from about 60 M to 150 M, though Tubefilter says the style change cannot be proven to be the cause. | Documented (small sample) | [Tubefilter](https://tubefilter.com/2024/03/04/mrbeast-editing-style-number-of-cuts-per-video/) |
| R14 | A **pattern interrupt** is a change that resets attention (zoom, cutaway, sound, a shift in energy, a joke after a dense stretch). Placement beats quantity: one before a known drop-off point is worth ten scattered ones. Used well, they are invisible. | Practice | [Monitor YT](https://monitoryt.com/blog/editing-for-retention), [Pixflow](https://pixflow.net/blog/youtube-video-retention-editing/), [Etwell](https://etwell.studio/blog/what-is-retention-editing-and-why-does-it-matter-for-youtube) |
| R15 | Cadence advice **conflicts** (every 5 to 8 s, 10 to 20 s, 20 to 40 s, or every 2 to 4 min in long videos). The common reconciliation: **tighter in the opening, looser once the viewer is hooked**; the middle shifts from energy to clarity. | Vendor (numbers), Practice (shape) | [air.io](https://air.io/en/youtube-hacks/advanced-retention-editing-cutting-patterns-that-keep-viewers-past-minute-8), [Gyre](https://gyre.pro/blog/how-to-improve-audience-retention-on-youtube-top-tips), [Increditors](https://increditors.com/video-pacing-youtube-retention-science/) |
| R16 | B-roll should **illustrate what is being said**; every cut should earn its place by bringing something new. Over-editing backfires. | Practice | [Monitor YT](https://monitoryt.com/blog/editing-for-retention), [Edición Video Pro](https://edicionvideopro.com/en/video-workflow-tutorials/audience-retention-how-to-edit-videos-that-keep-viewers-hooked/) |
| R17 | The fast "retention editing" style came out of analytics that said the story did not matter; its spread through imitators may be a bubble. | Documented (former MrBeast editor Trey Yates, via Passionfruit) | [Passionfruit](https://passionfru.it/youtube-editing-mrbeast-54202/) |

**Became:** §L4 (pacing). The kit's own numbers (no stretch without an overlay or camera move over 15 s in the first
90 s, 20 s after, 30 s ever; about 7 overlays and 7 camera moves per 90 s) sit inside the research range and stay as
the defaults, with the "tight early, clarity later, breathers after big moments" shape added.

## 4. How established creators' teams actually spend the edit

| # | Finding | Level | Source |
|---|---|---|---|
| R18 | Ali Abdaal's team: about **30 hours** per video: ~4 h cleaning the A-roll (dead space, mistakes, repeated takes, fillers), **~8 h B-roll** (the largest share), ~6 h titles, motion graphics and animation, ~4 h music and sound design. | Documented (Adobe, from his editors) | [Adobe blog](https://blog.adobe.com/en/publish/2024/09/05/how-ai-helps-ali-abdaal-save-hours-every-week) |
| R19 | His own three-step method: a tight assembly cut first (all mistakes and pauses out), then layer B-roll, then titles, lower thirds, images, screen recordings, animations. | Documented | [Skillshare course](https://www.skillshare.com/en/classes/video-editing-with-final-cut-pro-x-from-beginner-to-youtuber/317873419) |
| R20 | Captions in his long-form are restrained and readable rather than animated; accounts differ on word-by-word vs phrase-by-phrase reveal. | Vendor (conflicting) | [Submagic](https://www.submagic.co/blog/make-captions-like-ali-abdaal), [Choppity](https://www.choppity.com/tools/recreate-video-editing-style/ali-abdaal/) |
| R21 | His team built silence and repetition removal into a tool (FireCut) because the A-roll clean-up is repetitive. | Documented | [FireCut](https://firecut.ai/blog/how-ali-abdaal-edits-10x-faster-a-deep-dive-into-firecut/) |

**Became:** the stage order (cut first, B-roll and graphics after) and the weight given to the B-roll scout and the
Animator. The kit already automates R21 (paper-cut, tighten-cut, dead-air).

## 5. Cutting craft

| # | Finding | Level | Source |
|---|---|---|---|
| R22 | Walter Murch's **Rule of Six**: a cut serves emotion (51 %), story (23 %), rhythm (10 %), eye trace (7 %), the 2D plane (5 %), 3D space (4 %); when a cut can't satisfy all six, give up from the bottom of the list. | Documented (Murch, *In the Blink of an Eye*) | [No Film School](https://nofilmschool.com/2016/11/6-rules-good-cutting-according-oscar-winning-editor-walter-murch), [StudioBinder](https://studiobinder.com/blog/walter-murch-rule-of-six), [UT Austin](https://cloud.wikis.utexas.edu/wiki/spaces/rtf318/pages/80022510/Murch+s+Rule+of+Six) |
| R23 | Eye trace matters more on small screens with graphics: a cut that makes the eye search is costly. | Practice | [No Film School](https://nofilmschool.com/2018/08/editing-eye-trace-mind-rule-six-incorrect) |
| R24 | **J-cut**: the next shot's audio starts before its picture; **L-cut**: the outgoing audio carries over the new picture. In talking-head essays the next sentence often starts over a visual from the previous idea. Pitfalls: overlapping dialogue, carrying audio too long, a jump in background noise that gives the edit away. | Practice | [Adobe](https://www.adobe.com/creativecloud/video/discover/j-cut-and-l-cut), [Creator Essentials: J-cut](https://www.creatoressentials.com/glossary/j-cut/), [BlitzCut](https://blitzcutai.com/blog/hard-cut-vs-j-cut-vs-l-cut) |

**Became:** §L5 (cutting doctrine): Murch's order as the tie-breaker for cut decisions, eye trace for card placement,
and split edits at section entries and cutaways. Room-tone continuity (R24's noise-floor pitfall) was already a kit
rule.

## 6. Sound

| # | Finding | Level | Source |
|---|---|---|---|
| R25 | Voice chain order: high-pass (~80 Hz; higher voices up to ~120 to 200 Hz), light noise reduction, subtractive EQ (mud 200 to 400 Hz), presence (2 to 5 kHz), gentle compression (2:1 to 3:1, 10 to 30 ms attack), de-ess (4 to 8 kHz), loudness last. Light noise reduction only: heavy settings sound robotic. | Practice (Vendor numbers) | [Subscribr audio guide](https://subscribr.ai/youtube-strategy/professional-youtube-audio-guide), [IRPR: mixing for YouTube](https://sounddesign.irpr.agency/guides/how-to-mix-audio-for-youtube/), [Masteringbox](https://masteringbox.com/learn/vocal-processing-chain) |
| R26 | Music sits **15 to 20 dB under** the voice while talking, rising in gaps; ducking is set by threshold, amount, attack and release. Check the mix on a phone speaker and earbuds. | Practice | [IRPR](https://sounddesign.irpr.agency/guides/how-to-mix-audio-for-youtube/), [CapCut ducking](https://www.capcut.com/create/audio-ducking-for-clear-dialogue-in-video) |
| R27 | YouTube publishes **no official LUFS target**; -14 LUFS integrated with true peak under -1 dBTP is the common working target because louder uploads are turned down. | Practice (target), Official (absence) | [DaVinci Resolve Club](https://davinciresolveclub.com/davinci-resolve-audio-levels-lufs.md), [Joseph Nilo](https://josephnilo.com/blog/dialogue-loudness-lufs-true-peak-video/), [YouTube upload settings](https://support.google.com/youtube/answer/1722171?hl=en) |

**Became:** §L9 (sound). The kit's 16 dB (hook) / 19 dB (body) ducking and -14 LUFS / -1 dBTP sit inside these
ranges and stay. The voice chain is new and **opt-in**: an agent cannot listen, so a processed voice is offered to
you as a before/after pair at Checkpoint B, never applied blind.

## 7. Colour

| # | Finding | Level | Source |
|---|---|---|---|
| R28 | **Correct before you grade**: exposure, white balance and skin first; shot matching next; a creative look last, applied consistently. Judge on scopes, not an uncalibrated screen. | Practice | [Ruah Creative](https://ruahcreativehouse.org/blog/how-to-color-grade-video/), [Adobe community](https://community.adobe.com/t5/premiere-pro-discussions/color-grading-basic-correction-and-matching-best-practice/m-p/12442580), [PremiumBeat](https://www.premiumbeat.com/blog/tips-for-coloring-talking-head-interviews-in-davinci-resolve/) |
| R29 | The vectorscope **skin-tone line** shows hue direction only, not the right brightness or saturation; don't force different complexions to one level, and don't neutralise deliberate coloured light. | Practice | [Adobe: correct skin tones](https://helpx.adobe.com/ro/premiere-pro/how-to/correct-skin-tones.html), [DaVinci Resolve Club](https://davinciresolveclub.com/skin-tone-correction-davinci-resolve.md) |
| R30 | Automatic shot matching is a neutral starting point, not a finished grade. | Practice | [DaVinci Resolve Club: shot matching](https://davinciresolveclub.com/davinci-resolve-shot-matching.md) |

**Became:** §L10 (colour): measure and match, never a creative grade without your approval. The kit's BT.709 tagging
rule stays.

## 8. YouTube's own rules for delivery

| # | Finding | Level | Source |
|---|---|---|---|
| R31 | Upload: MP4 with the moov atom at the front, H.264 High Profile, progressive, closed GOP of half the frame rate, CABAC, 4:2:0; upload at the frame rate it was recorded at. **2160p SDR: 35 to 45 Mb/s at 24/25/30 fps, 53 to 68 Mb/s at 48/50/60 fps**; 1080p SDR: 8 / 12 Mb/s. Audio AAC-LC (or Opus), stereo, 48 kHz. | Official | [YouTube Help: recommended upload encoding settings](https://support.google.com/youtube/answer/1722171?hl=en) |
| R32 | **Chapters**: timestamps in the description, the first at 0:00, at least three, each at least 10 s, in order. A broken rule silently disables them. | Practice (consistent across guides; verify on Google's page) | [Storyblocks](https://www.storyblocks.com/resources/tutorials/how-to-add-chapters-to-youtube-video), [Income School](https://incomeschool.com/how-to-add-chapters-to-your-youtube-videos-and-why/), [Tella docs](https://docs.tella.com/help/export-videos/youtube-chapters) |
| R33 | **End screens** go in the last 5 to 20 s, need a video of at least 25 s, and take up to four elements on 16:9. | Official | [YouTube Help: add end screens](https://support.google.com/youtube/answer/6388789) |
| R34 | **Mid-roll ads** are available on monetised videos of 8 minutes or longer; automatic placement uses natural breaks, and since May 2025 YouTube shows fewer ads in interruptive slots (mid-sentence). Manual breaks should sit at natural break points. | Official | [YouTube Help: manage mid-roll ad breaks](https://support.google.com/youtube/answer/6175006?hl=en), [Tubefilter](https://www.tubefilter.com/2020/07/07/youtube-lowering-minimum-video-length-mid-roll-ads/) |
| R35 | **Paid promotion** (sponsorships, product placement, endorsements) must be declared in the video details; YouTube then shows a disclosure at the start. Reports from September 2026 say the policy was renamed "Branded Content". | Official (older wording), reported change | [YouTube Help: paid product placements](https://support.google.com/youtube/answer/154235), [PPC Land](https://ppc.land/youtube-will-label-brand-deals-that-creators-fail-to-disclose/) |
| R36 | **Altered or synthetic content** that a viewer could mistake for a real person, place or event must be disclosed; clearly unrealistic, animated or effects content, and AI used only for productivity (scripts, captions), is exempt. | Official | [YouTube blog](https://blog.youtube/news-and-events/disclosing-ai-generated-content) |
| R37 | **Captions** for long-form: a closed-caption file (SRT, uploaded "with timing") beats burned-in text: viewers choose, and the text is machine-readable. Burned-in captions belong to muted-autoplay feeds (Shorts, Reels). Correct auto-captions before publishing. | Practice | [MarketScale](https://help.marketscale.com/en/articles/15520464-caption-best-practices-why-caption-files-beat-burned-in-captions), [UC Davis](https://communicationsguide.ucdavis.edu/departments/social-media/best-practices/accessibility/video-captions), [OpenClip](https://openclip.app/guides/closed-captions-vs-open-captions) |
| R38 | The retention report's grey band compares a video with your **10 latest videos of similar length**; spikes are rewatches or shares (or a confusing part people rewind), dips are where people left or skipped. | Official | [YouTube Help: key moments](https://support.google.com/youtube/answer/9314415?hl=en), [YouTube Help: retention](https://support.google.com/youtube/answer/1715160) |

**Became:** §L11 (sponsors and disclosures), §L12 (delivery package), §L13 (after publishing).

## 9. Explainer and documentary style

| # | Finding | Level | Source |
|---|---|---|---|
| R39 | The Vox / Johnny Harris look combines animated maps and data graphics, kinetic typography, a highlighter on documents, archival footage, and heavy sound design; briefs that cite it ask for **restraint**: no constant zooms, shake or meme cuts, and room for maps and documents to breathe. | Practice (freelancer listings and a client brief; not the creators' own account) | [Upwork brief](https://www.upwork.com/freelance-jobs/apply/Motion-Graphics-Video-Editor-for-Geopolitics-Finance-Explainer-YouTube-Series-ongoing_~022071344721428727846/), [Contra](https://contra.com/s/WZggPY3k-vox-style-motion-graphics-modern-journalism) |

**Became:** §L6 (visual coverage). The kit already has the matching formats (18 article with highlighter, 18b doc read,
39 world camera, 6 to 8 diagrams); the research adds "let a document or map breathe: one move, then hold".

---

## Where the research and the house style disagree, and who wins

| Topic | Research says | Kit / style guide says | Decision |
|---|---|---|---|
| Sound effects | heavy sound design is part of the explainer look (R39) | silence by default; a sound must have a physical cause | **Kit wins.** The look belongs to the creator (style guide); the agents may suggest more sound at Checkpoint B but never add it unasked. |
| Captions | long-form uses closed captions (R37) | word captions are for Shorts; key-word highlights only in long form | **Agree.** Long-form ships an SRT file; no burned-in captions. |
| End of video | end screens need the last 5 to 20 s (R33) | no outro or end card; the YouTube end screen does the job | **Agree, made precise:** keep the last 20 s free of overlays in the end-screen element areas (§L12). |
| Cut rate | slower, story-led pacing performs (R12, R13) | about 7 overlays + 7 camera moves per 90 s; gap limits | **Kit numbers stay**, plus the shape from R15: tighter in the first 90 s, breathers after big beats. |
| Colour | grade for a look (R28) | no grading step in the kit | **Measure and match only**; a creative look needs your approval and goes in the style guide. |
| Voice processing | a full chain is standard (R25) | the kit only levels loudness | **Opt-in**, as a before/after pair you listen to; never applied blind. |

## What this research could not settle

- **Exact cadence numbers.** Sources range from every 5 s to every 4 min. Your own retention graph decides (§L13).
- **YouTube's loudness behaviour on quiet uploads.** Sources conflict on whether YouTube raises quiet videos; the
  agents deliver at -14 LUFS so it doesn't matter.
- **Chapter rules on Google's own page.** The rules in R32 are consistent across many guides but were not read on
  Google's Help Center; the Assembler checks them anyway because breaking one silently disables chapters.
- **Branded-content wording.** The September 2026 policy rename is reported by secondary sources; the Producer asks
  you to tick whatever YouTube Studio currently shows.
