// measure-glyphs.mjs <fonts-dir> > ../glyphs.json
// Advance widths (em) of printable ASCII and a few symbols in DM Sans 500/700 and JetBrains Mono 500, measured in
// Chromium. The scene modules wrap text with these, so a box's height is known before the browser sees it.
// <fonts-dir> holds DMSans-500.woff2, DMSans-700.woff2 and JetBrainsMono-500.woff2. A developer tool: not run per video.
import fs from "node:fs";
import path from "node:path";
import { launch } from "./_browser.mjs";

const dir = path.resolve(process.argv[2] || ".");
const chars = [];
for (let c = 32; c < 127; c++) chars.push(String.fromCharCode(c));
chars.push("€", "£", "₹", "–", "—", "’", "“", "”", "…", "×", "÷", "√", "π", "Σ", "≈", "≤", "≥");
const fonts = {
  display700: ["DM Sans", 700, "DMSans-700.woff2"],
  display500: ["DM Sans", 500, "DMSans-500.woff2"],
  mono500: ["JetBrains Mono", 500, "JetBrainsMono-500.woff2"],
};
const faces = Object.values(fonts).map(([fam, w, file]) =>
  `@font-face { font-family: "${fam}"; src: url("${file}") format("woff2"); font-weight: ${w}; }`).join("\n");
const probe = path.join(dir, "_glyphs.html");   // a file page beside the fonts: a blank page may not read file:// fonts
fs.writeFileSync(probe, `<!doctype html><style>${faces} span { font-size: 1000px; white-space: pre; position: absolute; }</style><body></body>`);
const browser = await launch();
const page = await browser.newPage();
await page.goto("file://" + probe);
const out = await page.evaluate(async (fonts, chars) => {
  const res = {};
  for (const [key, [fam, w]] of Object.entries(fonts)) {
    await document.fonts.load(`${w} 1000px "${fam}"`);
    if (!document.fonts.check(`${w} 1000px "${fam}"`)) throw new Error("font did not load: " + fam + " " + w);
    const s = document.createElement("span");
    s.style.fontFamily = `"${fam}"`; s.style.fontWeight = w;
    document.body.appendChild(s);
    res[key] = {};
    for (const c of chars) { s.textContent = c; res[key][c] = Math.round(s.getBoundingClientRect().width) / 1000; }
    s.remove();
  }
  return res;
}, fonts, chars);
await browser.close();
fs.unlinkSync(probe);
process.stdout.write(JSON.stringify(out, null, 1) + "\n");
