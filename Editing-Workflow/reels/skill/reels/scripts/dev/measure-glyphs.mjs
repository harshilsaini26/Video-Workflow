// measure-glyphs.mjs <fonts-dir> > ../glyphs.json
// Advance widths (em) of printable ASCII and a few symbols in DM Sans 500/700, JetBrains Mono 500, Archivo 800 at
// width 125% (the explainer's paper hero face) and Instrument Serif italic (its aside), measured in Chromium.
// reels_lib.text_lines wraps text with these (for Reels blocks and explainer scenes), so a box's height is known before
// the browser sees it. <fonts-dir> holds the font files (the explainer skill's assets/fonts has them all). A developer
// tool: not run per video.
import fs from "node:fs";
import path from "node:path";
import { launch } from "./_browser.mjs";
import { pathToFileURL } from "node:url";

const dir = path.resolve(process.argv[2] || ".");
const chars = [];
for (let c = 32; c < 127; c++) chars.push(String.fromCharCode(c));
chars.push("€", "£", "₹", "–", "—", "’", "“", "”", "…", "×", "÷", "√", "π", "Σ", "≈", "≤", "≥");
//            family, weight, file, stretch (and the file's range), style
const fonts = {
  display700: ["DM Sans", 700, "DMSans-700.woff2", "100%", "100%", "normal"],
  display500: ["DM Sans", 500, "DMSans-500.woff2", "100%", "100%", "normal"],
  mono500: ["JetBrains Mono", 500, "JetBrainsMono-500.woff2", "100%", "100%", "normal"],
  wide800: ["Archivo", 800, "Archivo-wdth.woff2", "125%", "62% 125%", "normal"],
  serif400i: ["Instrument Serif", 400, "InstrumentSerif-Italic.woff2", "100%", "100%", "italic"],
};
const faces = Object.values(fonts).map(([fam, w, file, , range, style]) =>
  `@font-face { font-family: "${fam}"; src: url("${file}") format("woff2"); font-weight: ${fam === "Archivo" ? "100 900" : w}; ` +
  `font-stretch: ${range}; font-style: ${style}; }`).join("\n");
const probe = path.join(dir, "_glyphs.html");   // a file page beside the fonts: a blank page may not read file:// fonts
fs.writeFileSync(probe, `<!doctype html><style>${faces} span { font-size: 1000px; white-space: pre; position: absolute; }</style><body></body>`);
const browser = await launch();
const page = await browser.newPage();
await page.goto(pathToFileURL(probe).href);
const out = await page.evaluate(async (fonts, chars) => {
  const res = {};
  for (const [key, [fam, w, , stretch, , style]] of Object.entries(fonts)) {
    const spec = `${style} ${w} ${stretch === "100%" ? "" : "expanded "}1000px "${fam}"`;
    await document.fonts.load(spec);
    if (!document.fonts.check(spec)) throw new Error("font did not load: " + fam + " " + w);
    const s = document.createElement("span");
    s.style.fontFamily = `"${fam}"`; s.style.fontWeight = w; s.style.fontStretch = stretch; s.style.fontStyle = style;
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
