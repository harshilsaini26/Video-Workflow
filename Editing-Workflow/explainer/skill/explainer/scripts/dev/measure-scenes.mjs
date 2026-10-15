// measure-scenes.mjs <cases-dir>: for each composed case (from make-cases.py), the laid-out height of its scene box at
// the wide (950 px) and narrow (780 px) column, once fonts are ready. Prints one JSON line per case and width:
// {"case", "scene", "width", "height"}. A developer tool: not run per video.
import fs from "node:fs";
import path from "node:path";
import { launch } from "./_browser.mjs";

const dir = path.resolve(process.argv[2] || ".");
const cases = JSON.parse(fs.readFileSync(path.join(dir, "cases.json"), "utf8"));
const browser = await launch();
const page = await browser.newPage();
await page.setViewport({ width: 1080, height: 1920 });
for (const c of cases) {
  await page.goto("file://" + path.join(dir, c.case, "public", "index.html"), { waitUntil: "load" });
  const rows = await page.evaluate(async (id) => {
    const box = document.getElementById(id);
    box.closest(".card-host").style.visibility = "visible";
    await Promise.all([...document.fonts].map((f) => f.load()));   // every face, not only those already in view
    await document.fonts.ready;
    const out = [];
    for (const w of [950, 780]) {
      box.style.width = w + "px";
      box.style.height = "auto";
      out.push({ width: w, height: box.offsetHeight });
    }
    return out;
  }, c.scene.id);
  for (const r of rows) process.stdout.write(JSON.stringify({ case: c.case, scene: c.scene.id, width: r.width, height: r.height }) + "\n");
}
await browser.close();
