// measure-blocks.mjs <cases-dir>: for each reel composed by make-cases.py, the laid-out height of its block once every
// font face has loaded (hidden step rows forced visible). Prints one JSON line per case: {"case", "height"}.
// Needs puppeteer (npm i puppeteer-core here, or PUPPETEER_DIR) and Chromium (/opt/pw-browsers/chromium or CHROME).
// A developer tool, not part of a reel.
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
  const height = await page.evaluate(async () => {
    const host = document.getElementById("host-b");
    host.style.visibility = "visible";
    document.querySelectorAll(".steps .it").forEach((e) => (e.style.display = "flex"));
    await Promise.all([...document.fonts].map((f) => f.load()));
    await document.fonts.ready;
    return host.querySelector(".box").offsetHeight;
  });
  process.stdout.write(JSON.stringify({ case: c.case, height }) + "\n");
}
await browser.close();
