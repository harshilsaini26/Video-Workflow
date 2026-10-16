// layout-probe.mjs <job.json>: open an explainer page in Chromium and, for each {id, t} sample, show that scene, seek the
// timeline to t, and look at what is really drawn. Prints one JSON array of {scene, t, kind, text, detail}. Run by
// layout-check.py (gate E5), which finds puppeteer and Chrome on this machine and passes them in the job.
//   kind: "overlap"  two pieces of text overlap
//         "covered"  something painted sits on top of the text
//         "crosses"  the text is drawn over a line or a shape that is not its own card
//         "spill"    the text runs out of the card or chip it sits on
//         "outside"  text or a shape leaves the safe area (x 65 to 1015, y 520 to 1420; x 150 to 930 below y 960)
//         "small"    text drawn smaller than min_px on the 1080 px frame
import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";

const job = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const req = createRequire(path.join(job.puppeteer_dir, "noop.js"));
let puppeteer;
try { puppeteer = req("puppeteer-core"); } catch (e) { puppeteer = req("puppeteer"); }
const browser = await puppeteer.launch({ executablePath: job.chrome, headless: true,
  args: ["--no-sandbox", "--allow-file-access-from-files", "--font-render-hinting=none"] });
const page = await browser.newPage();
await page.setViewport({ width: 1080, height: 1920 });
await page.goto("file://" + path.resolve(job.index), { waitUntil: "load" });
await page.evaluate(async () => { await Promise.all([...document.fonts].map((f) => f.load())); await document.fonts.ready; });
await page.addStyleTag({ content: "* { pointer-events: auto !important; }" });   // elementsFromPoint must see every layer

const issues = [];
for (const s of job.samples) {
  const found = await page.evaluate((s, area, minPx) => {
    const out = [];
    const tl = Object.values(window.__timelines || {})[0];
    for (const h of document.querySelectorAll(".card-host")) h.style.visibility = h.id === "host-" + s.id ? "visible" : "hidden";
    for (const c of document.querySelectorAll(".cap-layer, .tx-layer")) c.style.visibility = "hidden";
    if (tl) tl.seek(s.t, false);
    const root = document.getElementById(s.id);
    if (!root) return [{ kind: "missing", text: "", detail: "no element #" + s.id }];
    const alpha = (el) => {
      let o = 1;
      for (let e = el; e && e.nodeType === 1; e = e.parentElement) {
        const cs = getComputedStyle(e);
        if (cs.visibility === "hidden" || cs.display === "none") return 0;
        o *= parseFloat(cs.opacity);
      }
      return o;
    };
    const SHAPES = new Set(["line", "path", "circle", "rect", "polyline", "polygon", "ellipse"]);
    const painted = (el) => {
      if (el === root || !root.contains(el)) return false;
      if (SHAPES.has(el.tagName.toLowerCase())) {
        const cs = getComputedStyle(el);
        return (cs.stroke !== "none" && parseFloat(cs.strokeWidth) > 0) || (cs.fill !== "none" && cs.fill !== "rgba(0, 0, 0, 0)");
      }
      if (el.tagName.toLowerCase() === "svg") return false;
      const cs = getComputedStyle(el);
      const bg = cs.backgroundColor.match(/[\d.]+/g);
      const bgA = bg ? (bg.length > 3 ? parseFloat(bg[3]) : 1) : 0;
      const border = ["Top", "Right", "Bottom", "Left"].some((k) => parseFloat(cs["border" + k + "Width"]) > 0 && cs["border" + k + "Style"] !== "none");
      return bgA > 0.05 || cs.backgroundImage !== "none" || border || el.tagName.toLowerCase() === "img";
    };
    const name = (el) => (el.id ? "#" + el.id : el.tagName.toLowerCase() + (el.className && el.className.baseVal === undefined ? "." + String(el.className).split(" ")[0] : ""));
    const outside = (r) => r.left < area.left - 2 || r.right > area.right + 2 || r.top < area.top - 2 || r.bottom > area.bottom + 2 ||
      (r.bottom > area.col_top + 2 && (r.left < area.narrow_left - 2 || r.right > area.narrow_right + 2));
    // the text on screen: elements with their own visible text, and the rectangles of its lines
    const texts = [];
    for (const el of root.querySelectorAll("*")) {
      const nodes = [...el.childNodes].filter((n) => n.nodeType === 3 && n.textContent.trim());
      if (!nodes.length || alpha(el) < 0.5) continue;
      const rects = [];
      for (const n of nodes) {
        const range = document.createRange();
        range.selectNodeContents(n);
        for (const r of range.getClientRects()) if (r.width > 1 && r.height > 1) rects.push(r);
      }
      if (!rects.length) continue;
      const box = el.getBoundingClientRect();
      const scale = el.offsetWidth ? box.width / el.offsetWidth : 1;
      texts.push({ el, rects, text: nodes.map((n) => n.textContent.trim()).join(" ").slice(0, 40),
                   px: parseFloat(getComputedStyle(el).fontSize) * scale });
    }
    const related = (a, b) => a === b || a.contains(b) || b.contains(a);
    const hit = (a, b) => Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) * Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
    for (const t of texts) {
      if (t.px < minPx) out.push({ kind: "small", text: t.text, detail: "text drawn at " + t.px.toFixed(0) + " px (at least " + minPx + "): too small" });
      for (const r of t.rects) if (outside(r)) { out.push({ kind: "outside", text: t.text, detail: "outside the safe area" }); break; }
      // its card: the nearest painted element under it (itself included)
      let card = null;
      for (let e = t.el; e && e !== root; e = e.parentElement) if (painted(e)) { card = e; break; }
      if (card) {
        const cr = card.getBoundingClientRect();
        if (t.rects.some((r) => r.left < cr.left - 2 || r.right > cr.right + 2 || r.top < cr.top - 2 || r.bottom > cr.bottom + 2))
          out.push({ kind: "spill", text: t.text, detail: "spills out of " + name(card) });
      }
      // what is drawn above and below it, sampled across each line of text
      const seen = new Set();
      for (const r of t.rects) {
        // a grid every ~6 px down and ~24 px across the line: a thin rule or a spoke through the words is found
        const ny = Math.max(4, Math.ceil(r.height / 6)), nx = Math.max(3, Math.ceil(r.width / 24));
        for (let ix = 0; ix < nx; ix++) for (let iy = 0; iy < ny; iy++) {
          const x = r.left + r.width * (ix + 0.5) / nx, y = r.top + r.height * (iy + 0.5) / ny;
          const stack = document.elementsFromPoint(x, y);
          const j = stack.findIndex((e) => e === t.el || t.el.contains(e));
          if (j < 0) continue;
          for (const e of stack.slice(0, j)) {
            if (related(e, t.el) || !painted(e) || alpha(e) < 0.5 || seen.has(e)) continue;
            seen.add(e);
            out.push({ kind: "covered", text: t.text, detail: "covered by " + name(e) });
          }
          if (painted(t.el)) continue;              // the text sits on its own chip
          for (const e of stack.slice(j + 1)) {
            if (e === root || !root.contains(e)) break;
            if (e.contains(t.el)) { if (painted(e)) break; continue; }
            if (!painted(e) || alpha(e) < 0.5 || seen.has(e)) continue;
            seen.add(e);
            out.push({ kind: "crosses", text: t.text, detail: "crosses " + name(e) });
          }
        }
      }
    }
    for (let i = 0; i < texts.length; i++) for (let k = i + 1; k < texts.length; k++) {
      const a = texts[i], b = texts[k];
      if (related(a.el, b.el)) continue;
      if (a.rects.some((ra) => b.rects.some((rb) => hit(ra, rb) > 6)))
        out.push({ kind: "overlap", text: a.text, detail: "overlaps \"" + b.text + "\"" });
    }
    for (const el of root.querySelectorAll("*")) {          // shapes too must stay inside the safe area
      if (!painted(el) || alpha(el) < 0.5) continue;
      const r = el.getBoundingClientRect();
      if (r.width > 1 && outside(r)) out.push({ kind: "outside", text: "", detail: name(el) + " is outside the safe area" });
    }
    return out;
  }, s, job.area, job.min_px);
  for (const f of found) issues.push(Object.assign({ scene: s.id, t: s.t }, f));
}
await browser.close();
process.stdout.write(JSON.stringify(issues) + "\n");
