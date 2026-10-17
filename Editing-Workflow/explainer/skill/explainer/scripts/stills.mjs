// stills.mjs <job.json>: open the page and save a full-size PNG at each {t, file}, drawn as HyperFrames draws that
// frame: each clip shown only inside its own time (data-start, data-duration), the timeline seeked to t, captions on.
// Run by stills.py, which finds puppeteer and Chrome on this machine and passes them in the job.
import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { pathToFileURL } from "node:url";

const job = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const req = createRequire(path.join(job.puppeteer_dir, "noop.js"));
let puppeteer;
try { puppeteer = req("puppeteer-core"); } catch (e) { puppeteer = req("puppeteer"); }
const browser = await puppeteer.launch({ executablePath: job.chrome, headless: true,
  args: ["--no-sandbox", "--allow-file-access-from-files", "--font-render-hinting=none"] });
const page = await browser.newPage();
await page.setViewport({ width: 1080, height: 1920 });
await page.goto(pathToFileURL(path.resolve(job.index)).href, { waitUntil: "load" });
await page.evaluate(async () => { await Promise.all([...document.fonts].map((f) => f.load())); await document.fonts.ready; });
for (const s of job.shots) {
  await page.evaluate((t) => {
    for (const c of document.querySelectorAll("[data-start][data-duration]")) {
      if (c.tagName === "AUDIO" || c.id === "stage") continue;
      const a = parseFloat(c.dataset.start), d = parseFloat(c.dataset.duration);
      c.style.visibility = t >= a - 1e-6 && t < a + d - 1e-6 ? "visible" : "hidden";
    }
    const tl = Object.values(window.__timelines || {})[0];
    if (tl) tl.seek(t, false);
  }, s.t);
  const stage = await page.$("#stage");
  await stage.screenshot({ path: s.file });
}
await browser.close();
process.stdout.write(JSON.stringify({ shots: job.shots.length }) + "\n");
