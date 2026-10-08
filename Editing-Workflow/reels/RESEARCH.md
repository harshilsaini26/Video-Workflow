# Research: how short vertical videos are edited

Background research behind the Reels agents (Instagram Reels first; the same file also suits YouTube Shorts and
TikTok). Every finding is either a rule in [`skill/reels/PLAYBOOK.md`](skill/reels/PLAYBOOK.md) (cited as **§R1**,
**§R2**...) or a deliberate decision not to adopt it.

Researched 2026-10-08. Short-form advice is dominated by tool vendors and agencies; platform documentation is thin and
changes often. Confidence levels as in the long-form research:

| Level | Meaning |
|---|---|
| **Official** | the platform's own documentation, or its head stated it publicly |
| **Documented** | named reporting with specifics, or a platform feature that exists (an Insights metric) |
| **Practice** | widely repeated working practice; sources agree on the idea, not on numbers |
| **Vendor** | a single tool vendor or agency; a starting point, never a hard rule |

---

## 1. Format and specs

| # | Finding | Level | Source |
|---|---|---|---|
| S1 | The canvas is **1080x1920, 9:16**. Upload H.264 in MP4 with AAC audio; HEVC gains nothing (platforms transcode). | Practice | [Argil spec sheet](https://argil.ai/blog/instagram-reel-size-e350f), [ContentStudio](https://contentstudio.io/blog/instagram-reel-size), [Orlo upload limits](https://support.orlo.tech/instagram-media-upload-limits) |
| S2 | **60 fps is accepted** (23 to 60 fps); most guides default to 30, and 60 roughly doubles file size. Bitrate advice conflicts (5 to 12 Mb/s recommended; a ceiling of about 25 Mb/s quoted). | Vendor | [Orlo](https://support.orlo.tech/instagram-media-upload-limits), [Argil](https://argil.ai/blog/instagram-reel-size-e350f) |
| S3 | **Length:** Instagram Reels up to 3 minutes for most accounts (sources conflict on higher limits); YouTube Shorts up to **3 minutes** for 9:16 or square uploads since 15 October 2024; TikTok uploads much longer. Guides still favour 15 to 45 s for completion. | Documented (Shorts), Vendor (the rest) | [Gigazine on Shorts](https://gigazine.net/gsc_news/en/20241004-youtube-short-video-length-3-minutes), [Kapwing](https://kapwing.com/resources/youtube-shorts-is-making-a-huge-change-to-its-maximum-video-length-and-it-will-affect-creators), [Framia](https://framia.converge.ai/blog/how-long-can-instagram-reels-be/) |
| S4 | Nothing above 1080p survives to Shorts viewers; 1080x1920 is the delivery size everywhere. | Vendor | [Async](https://async.com/blog/how-long-can-youtube-shorts-be/) |

**Became:** §R0 (the profile: 1080x1920, 60 fps, H.264/AAC, about 20 Mb/s, up to 3 minutes, 15 to 60 s by default).

## 2. Safe zones

| # | Finding | Level | Source |
|---|---|---|---|
| S5 | Meta's published guidance (written for ads) keeps text, logos and key content out of the **top 14 %, the bottom 35 % and 6 % each side**: on 1080x1920 about **269 px, 672 px and 65 px**, leaving about 950x979 px. Reported as one unified spec for Stories and Reels since March 2026 (unconfirmed). | Documented (Meta's figures via several summaries) | [Campaign Swift](https://campaignswift.com/blog/instagram-safe-zone-sizes), [Kreatli](https://kreatli.com/guides/instagram-reels-safe-zone), [Zeely](https://zeely.ai/blog/master-instagram-safe-zones/), [1ClickReport](https://www.1clickreport.com/blog/meta-ads-creative-safe-zones-2026-guide) |
| S6 | Organic-Reels numbers vary widely (top 108 to 250 px, bottom 320 to 430 px, right 35 to 130 px). All agree: the **right-hand action column** (like, comment, share, save) and the **bottom caption/audio strip** cover content; keep faces and text away from both. | Vendor | [House of Marketers](https://houseofmarketers.com/guide-to-safe-zones-tiktok-facebook-instagram-stories-reels/), [Grow Creator](https://growcreator.pro/blog/instagram-reel-safe-zone), [Minta](https://www.minta.ai/blog-post/instagram-safe-zone) |
| S7 | TikTok's UI: about 120 px top, 150 px right, 250 px bottom (one guide). Shorts' overlay is described as lighter. | Vendor | [Emplifi](https://emplifi.io/resources/blog/tiktok-ad-specs), [Hopper HQ](https://www.hopperhq.com/blog/youtube-shorts-dimensions/?amp=1) |

**Became:** §R3. One zone for every platform: **Meta's box** (the strictest of the three), so one file posts
everywhere. The composer places every overlay inside it by construction, and a guide overlay is drawn on every snapshot.

## 3. What the platform rewards

| # | Finding | Level | Source |
|---|---|---|---|
| S8 | Adam Mosseri (head of Instagram) named **watch time, likes per reach and sends (DM shares)** as the most important ranking signals for Reels (January 2025). Sends weigh heavily because they reach non-followers. | Documented (via secondary reports) | [Hootsuite](https://blog.hootsuite.com/instagram-algorithm/), [OnlineMarketing.de](https://onlinemarketing.de/social-media-marketing/instagram-reels-metriken-adam-mosseri-insights), [Dataslayer](https://dataslayer.ai/blog/instagram-algorithm-2025-complete-guide-for-marketers) |
| S9 | Mosseri's tips include a **strong hook**, captions, audio, **non-watermarked original content**, and Reels of 3 minutes or less. | Documented | [Hootsuite](https://blog.hootsuite.com/instagram-algorithm/) |
| S10 | New Reels are shown to a small test pool first; distribution grows if watch time and sends are strong. Skips, "Not interested" and quick exits count against a Reel. | Practice | [Dataslayer](https://dataslayer.ai/blog/instagram-algorithm-2025-complete-guide-for-marketers), [SocialPilot](https://www.socialpilot.co/instagram-marketing/how-instagram-algorithm-works) |
| S11 | Instagram downranks **reposted and watermarked** content (TikTok watermarks since 2024) and, reportedly from 2026, accounts that mostly repost; "if you made it, it's original", including editing outside Instagram. Transformation means new narration, graphics or commentary; credits don't count. | Documented | [Planoly](https://planoly.com/blog/instagram-updates-its-original-content-policy), [Social Media Today](https://www.socialmediatoday.com/news/instagrams-updating-its-ranking-algorithm-to-put-more-focus-on-original-co/622424), [eMarketer](https://www.emarketer.com/content/instagram-s-algorithm-clamps-down-on-repurposed--unoriginal-photos-posts) |
| S12 | Instagram's Insights show a **retention chart** and a **skip rate** (viewers who left in the first 3 seconds; it replaced "view rate"). A healthy curve drops in the first 1 to 2 s, then flattens. Compare average watch time against the Reel's length and your own history; there is no reliable external benchmark. | Documented (the metrics), Vendor (benchmarks) | [Social Samosa](https://www.socialsamosa.com/news-2/instagram-retention-chart-skip-rate-new-performance-metrics-reels-9730992), [Metricool](https://metricool.com/instagram-reel-analytics/), [Inro](https://www.inro.social/blog/instagram-reels-insights), [Windsor](https://windsor.ai/instagram-reels-retention-chatgpt/) |

**Became:** §R1 (what a reel is for), §R2 (the hook), §R9 (originality), §R13 (reading Insights). The reel is built
to be **watched to the end, rewatched and sent**: a promise in the first second, a payoff, and something worth
sending.

## 4. Editing practice

| # | Finding | Level | Source |
|---|---|---|---|
| S13 | **The first 1 to 3 seconds decide it.** Plan what the viewer sees in the first second and reads or hears by the third; open mid-action or on the result, never on a slow intro. | Practice | [Descript](https://descript.com/blog/article/edit-short-form-video), [CapCut hooks](https://www.capcut.com/create/short-form-video-hooks), [Dataslayer](https://dataslayer.ai/blog/instagram-algorithm-2025-complete-guide-for-marketers) |
| S14 | **Cut every pause and hesitation**; shots of about 1 to 3 s are common, but fast cutting can feel frantic for explainers. | Practice (numbers Vendor) | [Splice](https://spliceapp.com/blog/mastering-short-form-video-editing-guide/), [Opus](https://www.opus.pro/blog/video-editing-tips) |
| S15 | A **loop ending** that leads back into the first frame adds rewatches; it needs a clear setup and a payoff, or the viewer has to re-orient. A video that just stops feels unfinished. | Practice | [CapCut looping hooks](https://www.capcut.com/create/looping-narrative-hooks-watch-time), [DOR](https://clip.dor.gg/en/blog/gaming-shorts-viral-pattern) |
| S16 | Music too loud buries the voice. | Practice | [Splice](https://spliceapp.com/blog/mastering-short-form-video-editing-guide/) |
| S17 | Repurposing long-form: **curation is most of the work**; pick moments with their own hook (a question, a surprising fact, a demo); each clip must **stand on its own** (cut "as I mentioned earlier", add the missing setup on screen); write a hook for the short, not the long video. YouTube advises Shorts that preview the long video yet stand alone. | Documented (YouTube's tips via Social Media Today), Practice | [Social Media Today](https://www.socialmediatoday.com/news/youtube-tips-convert-long-form-videos-to-shorts/745711/), [Subscribr](https://subscribr.ai/youtube-strategy/repurpose-long-videos-into-shorts), [Opus](https://www.opus.pro/blog/youtube-shorts-at-scale) |

**Became:** §R2 (hook), §R4 (pacing), §R6 (ending and loop), §R12 (the long-form-to-reel route).

## 5. Captions

| # | Finding | Level | Source |
|---|---|---|---|
| S18 | A large share of Reels is watched with the sound off (vendors estimate 50 to 80 %, unsourced); the argument that a muted viewer needs on-screen words is widely accepted. | Vendor (numbers), Practice (idea) | [BlitzCut](https://blitzcutai.com/blog/instagram-reels-captions-auto-subtitles), [Opus](https://www.opus.pro/blog/instagram-reels-caption-subtitle-best-practices) |
| S19 | **Burned-in captions** reach every viewer on every platform and allow word-by-word highlighting; native captions only show for viewers who turned them on. Use both where possible. | Practice | [Krumzi](https://www.krumzi.com/blog/add-captions-to-instagram-reels), [Subanana](https://subanana.com/en/blog/how-to-add-subtitles-instagram-reels) |
| S20 | Readability beats quantity: large text (one guide: 60 to 75 px on 1080x1920, kept well above the bottom), few words at a time; review auto-captions before posting. | Vendor | [Clipspeed](https://www.clipspeed.ai/blog/instagram-reels-captions.html), [Klap](https://klap.app/blog/how-to-add-caption-to-instagram-reels) |
| S21 | The written post caption: up to 2,200 characters, but only about the first 125 are read before "more". | Vendor | [Clipspeed](https://www.clipspeed.ai/blog/instagram-reels-captions.html) |

**Became:** §R5. Word-exact burned-in captions (the kit's Shorts rule, now built), on the kept words only, 1 to 3
words at a time, the spoken word highlighted, inside the safe zone; plus an SRT file for platforms that take one.

## 6. Free music and sound

| # | Finding | Level | Source |
|---|---|---|---|
| S22 | **Pixabay Content License:** free use and modification, commercial included, **no attribution required**; no selling content as-is, no misleading use, trademarks and depicted people may carry their own rights. Some Pixabay tracks are registered with Content ID, so a correct licence can still draw a claim: keep the licence file. | Official (Pixabay's summary), Practice (Content ID) | [Pixabay licence](https://pixabay.com/en/service/license/), [Pixabay FAQ](https://pixabay.com/service/faq/), [Thematic vs Pixabay](https://hellothematic.com/thematic-vs-pixabay/), [Newcastle University](https://www.newcastle.edu.au/__data/assets/pdf_file/0006/875994/Suggested-music-file-sites.pdf) |
| S23 | **Creative Commons** ranges from CC0 (no conditions) to non-commercial and no-derivatives licences: check every sound; "copyright-free" labels are usually wrong. Keep proof of every licence. | Practice | [Foxi Music](https://www.foximusic.com/blog/it/instagram-reels-music-copyright-legal-guide/), [Sprintlaw](https://sprintlaw.co.uk/articles/how-to-add-music-to-instagram-reels-without-copyright-issues-the-definitive-guide-for-uk-businesses-creators/) |
| S24 | Instagram's in-app music library covers personal use; **business accounts** get the narrower Meta Sound Collection. Heavily reused free tracks make Reels sound alike. | Practice | [Sprintlaw](https://sprintlaw.co.uk/articles/how-to-add-music-to-instagram-reels-without-copyright-issues-the-definitive-guide-for-uk-businesses-creators/), [Lilach Bullock](https://www.lilachbullock.com/where-to-get-free-background-music-youtube-instagram/) |

**Became:** §R7 (sound and music) and §R10 (free tools only): silence by default; free effects only (the HyperFrames
library, Pixabay, Freesound **CC0 only**); music either from Pixabay with the licence saved, or none in the file and
added in the app at posting.

---

## Where the research and the house style disagree, and who wins

| Topic | Research says | Kit / style guide says | Decision |
|---|---|---|---|
| Captions | burned-in, word by word, for sound-off viewers (S18, S19) | word-by-word captions are for Shorts | **Agree**: reels always carry burned-in word captions. |
| Sound effects | short-form often stacks effects | silence by default; a sound needs a cause | **Kit wins.** The look is the creator's. |
| Pacing | 1 to 3 s shots (S14) | no flash cuts, no overstim | **Both:** dead air cut harder than long form (0.25 s), but no flash cuts or stacked effects. |
| Safe zone | numbers conflict (S5 to S7) | style guide: cards never on the face | **Meta's box** for everything, plus the face rule. |
| Music | trending audio helps discovery (common claim) | music low, ducked | Music in the file only when licensed and free; otherwise none in the file and the creator may add in-app audio at posting. |
| Frame rate | 30 fps is the common default (S2) | the profile asks for 60 fps | **60 fps** (accepted everywhere), recorded at 60 so motion is real, not doubled frames. |

## What this research could not settle

- **Exact safe-zone pixels** for organic Reels: the strictest published box is used, and a real phone preview is the
  final check (the QA agent asks the creator for one when anything sits near an edge).
- **Bitrate**: recommendations range 5 to 25 Mb/s; 20 Mb/s at 1080p60 sits under the quoted ceiling and leaves the
  platform's transcode good material.
- **Ideal length**: platform limits are clear; what works for this creator comes from their own Insights (§R13).
