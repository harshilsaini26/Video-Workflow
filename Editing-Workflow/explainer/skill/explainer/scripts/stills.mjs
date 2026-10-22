// stills.mjs <job.json>: open the page and save a full-size PNG at each {t, file}, drawn as HyperFrames draws that
// frame: each clip shown only inside its own time (data-start, data-duration), the timeline seeked to t, captions on.
// A job with size: [w, h] and gray: true saves each frame instead as w*h raw 8-bit grey bytes (gate E6 on the page);
// boil: false turns the stroke boil off (data-boil="off") so it cannot hide a frozen stretch. A shot's clip {x, y, w, h}
// saves that part of the frame at 1:1; follow {sel, n, pad, files} saves n frames over the life of the element's clip,
// cropped to its box padded by pad, skipping a frame where it is hidden; sheets [{file, cols, cell: [w, h], cells:
// [{file, label}]}] lay saved frames out side by side with their labels (a missing frame is left out). Run by stills.py, which finds puppeteer and Chrome on this machine and passes them in the job.
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
await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: job.size ? job.size[0] / 1080 : 1 });
await page.goto(pathToFileURL(path.resolve(job.index)).href, { waitUntil: "load" });
if (job.boil === false) await page.evaluate(() => { document.documentElement.dataset.boil = "off"; });
await page.evaluate(async () => { await Promise.all([...document.fonts].map((f) => f.load())); await document.fonts.ready; });
const seek = (t) => page.evaluate((t) => {
    for (const c of document.querySelectorAll("[data-start][data-duration]")) {
      if (c.tagName === "AUDIO" || c.id === "stage") continue;
      const a = parseFloat(c.dataset.start), d = parseFloat(c.dataset.duration);
      c.style.visibility = t >= a - 1e-6 && t < a + d - 1e-6 ? "visible" : "hidden";
    }
    const tl = Object.values(window.__timelines || {})[0];
    if (tl) tl.seek(t, false);
  }, t);
const stage = await page.$("#stage");
for (const s of job.shots) {
  await seek(s.t);
  if (s.clip) { await page.screenshot({ path: s.file, clip: { x: s.clip.x, y: s.clip.y, width: s.clip.w, height: s.clip.h } }); continue; }
  if (!job.gray) { await stage.screenshot({ path: s.file }); continue; }
  const png = await stage.screenshot({ encoding: "base64" });
  const grey = await page.evaluate(async (b64, w, h) => {
    const img = new Image(); img.src = "data:image/png;base64," + b64; await img.decode();
    const c = document.createElement("canvas"); c.width = w; c.height = h;
    const g = c.getContext("2d"); g.drawImage(img, 0, 0, w, h);
    const d = g.getImageData(0, 0, w, h).data; let out = "";
    for (let i = 0; i < d.length; i += 4) out += String.fromCharCode(Math.round(0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2]));
    return btoa(out);
  }, png, job.size[0], job.size[1]);
  fs.writeFileSync(s.file, Buffer.from(grey, "base64"));
}
const f = job.follow;
if (f) {
  const life = await page.evaluate((sel) => {
    const el = document.querySelector(sel), c = el && el.closest("[data-start][data-duration]:not(#stage)");
    if (!el) return null;
    if (!c) return [0, parseFloat(document.getElementById("stage").dataset.duration)];
    return [parseFloat(c.dataset.start), parseFloat(c.dataset.duration)];
  }, f.sel);
  if (!life) { process.stderr.write("no element matches " + f.sel + "\n"); process.exit(1); }
  for (let k = 0; k < f.n; k++) {
    await seek(life[0] + (k + 0.5) * life[1] / f.n);
    const r = await page.evaluate((sel) => {
      const el = document.querySelector(sel);
      if (!el.checkVisibility({ opacityProperty: true, visibilityProperty: true })) return null;
      const b = el.getBoundingClientRect();
      return b.width > 0 && b.height > 0 ? [b.x, b.y, b.width, b.height] : null;
    }, f.sel);
    if (!r) continue;
    const x = Math.max(0, r[0] - f.pad), y = Math.max(0, r[1] - f.pad);
    const w = Math.min(1080, r[0] + r[2] + f.pad) - x, h = Math.min(1920, r[1] + r[3] + f.pad) - y;
    if (w > 0 && h > 0) await page.screenshot({ path: f.files[k], clip: { x, y, width: w, height: h } });
  }
}
const made = {};
for (const sh of job.sheets || []) {
  const cells = sh.cells.filter((c) => fs.existsSync(c.file));
  made[sh.file] = cells.length;
  if (!cells.length) continue;
  const [cw, ch] = sh.cell, cols = Math.min(sh.cols, cells.length), rows = Math.ceil(cells.length / cols);
  const p = await browser.newPage();
  await p.setViewport({ width: cols * cw, height: rows * (ch + 28) });
  await p.setContent("<body style='margin:0;background:#222;font:600 18px monospace;color:#eee;display:grid;grid-template-columns:repeat("
    + cols + "," + cw + "px)'>" + cells.map((c) => "<div style='width:" + cw + "px;height:" + (ch + 28) + "px'><img style='width:" + cw
    + "px;height:" + ch + "px;object-fit:contain;display:block' src='data:image/png;base64," + fs.readFileSync(c.file).toString("base64")
    + "'><div style='height:28px;line-height:28px;padding-left:6px'>" + c.label + "</div></div>").join("") + "</body>");
  await p.screenshot({ path: sh.file, fullPage: true });
  await p.close();
}
await browser.close();
process.stdout.write(JSON.stringify({ shots: job.shots.length, sheets: made }) + "\n");
