// layout-probe.mjs <job.json>: open an explainer page (or each of job.pages) in Chromium and, for each {id, t} sample, show that scene, seek the
// timeline to t, and look at what is really drawn. Prints one JSON array of {scene, t, kind, text, detail}. Run by
// layout-check.py (gate E5), which finds puppeteer and Chrome on this machine and passes them in the job.
//   kind: "overlap"  two pieces of text overlap
//         "covered"  something painted sits on top of the text
//         "crosses"  the text is drawn over a line or a shape that is not its own card
//         "spill"    the text runs out of the card or chip it sits on
//         "outside"  text or a card leaves the safe area (x 65 to 1015, y 345 to 1105; x 150 to 930 below y 960); a
//                    painted shape with no text in it may run on to area.picture_bottom (1650)
//         "handover" at a cut, the outgoing and the incoming scene both show content at 30% or more (job handovers)
//         "small"    text drawn smaller than min_px on the 1080 px frame
//         "contrast" text under 3:1 against what is really behind it (all text is 28 px or more: WCAG's large-text
//                    rule), the stage, the background layers and every filled box under it composited
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
const issues = [];
for (const pg of job.pages || [{ index: job.index, samples: job.samples }]) {
await page.goto(pathToFileURL(path.resolve(pg.index)).href, { waitUntil: "load" });
await page.evaluate(async () => { await Promise.all([...document.fonts].map((f) => f.load())); await document.fonts.ready; });
await page.addStyleTag({ content: "* { pointer-events: auto !important; }" });   // elementsFromPoint must see every layer
for (const s of pg.samples) {
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
    // opaque enough to hide what is under it (a see-through highlighter over a row is not)
    const opaque = (el) => {
      if (!painted(el)) return false;
      const tag = el.tagName.toLowerCase();
      if (SHAPES.has(tag) || tag === "img") return true;
      const cs = getComputedStyle(el);
      const bg = cs.backgroundColor.match(/[\d.]+/g);
      return (bg ? (bg.length > 3 ? parseFloat(bg[3]) : 1) : 0) >= 0.6 || cs.backgroundImage !== "none";
    };
    const name = (el) => (el.id ? "#" + el.id : el.tagName.toLowerCase() + (el.className && el.className.baseVal === undefined ? "." + String(el.className).split(" ")[0] : ""));
    const where = (r) => " (x " + Math.round(r.left) + " to " + Math.round(r.right) + ", y " + Math.round(r.top) + " to " + Math.round(r.bottom) + ")";
    const outside = (r, bottom) => r.left < area.left - 2 || r.right > area.right + 2 || r.top < area.top - 2 || r.bottom > (bottom || area.bottom) + 2 ||
      (r.bottom > area.col_top + 2 && (r.left < area.narrow_left - 2 || r.right > area.narrow_right + 2));
    // what is really visible of a box: clipped by every ancestor that hides its overflow (a screenshot in its window)
    const clip = (el, r) => {
      let { left, top, right, bottom } = r;
      for (let e = el.parentElement; e && e !== document.body; e = e.parentElement) {
        const cs = getComputedStyle(e);
        if (cs.overflow === "visible" && cs.overflowX === "visible" && cs.overflowY === "visible") continue;
        const c = e.getBoundingClientRect();
        left = Math.max(left, c.left); top = Math.max(top, c.top); right = Math.min(right, c.right); bottom = Math.min(bottom, c.bottom);
      }
      return { left, top, right, bottom, width: right - left, height: bottom - top };
    };
    // the text on screen: elements with their own visible text, and the rectangles of its lines
    const texts = [];
    for (const k of root.querySelectorAll(".katex")) {    // a typeset formula is one piece: KaTeX places its glyphs itself
      if (alpha(k) < 0.5) continue;
      const r = k.getBoundingClientRect();
      if (r.width > 1) texts.push({ el: k, rects: [r], text: k.textContent.trim().slice(0, 40), px: 99, formula: true });
    }
    for (const el of root.querySelectorAll("*")) {
      if (el.closest(".katex")) continue;
      const nodes = [...el.childNodes].filter((n) => n.nodeType === 3 && n.textContent.trim());
      if (!nodes.length || alpha(el) < 0.5) continue;
      const rects = [];
      for (const n of nodes) {
        const range = document.createRange();
        range.selectNodeContents(n);
        for (const r of range.getClientRects()) if (r.width > 1 && r.height > 1) rects.push(r);
      }
      // only what is drawn: text still below its mask (kinetic type before its word) is not on screen
      for (let i = rects.length - 1; i >= 0; i--) {
        const v = clip(el, rects[i]);
        if (v.width <= 1 || v.height <= 1) rects.splice(i, 1);
      }
      if (!rects.length) continue;
      const box = el.getBoundingClientRect();
      const scale = el.offsetWidth ? box.width / el.offsetWidth : 1;
      texts.push({ el, rects, text: nodes.map((n) => n.textContent.trim()).join(" ").slice(0, 40),
                   px: parseFloat(getComputedStyle(el).fontSize) * scale });
    }
    // the colour really behind a piece of text: the stage, each background layer, then every filled box above them
    const rgb = (s) => { const m = (s || "").match(/[\d.]+/g); return m ? { r: +m[0], g: +m[1], b: +m[2], a: m.length > 3 ? +m[3] : 1 } : null; };
    const over = (top, under, a) => ({ r: top.r * a + under.r * (1 - a), g: top.g * a + under.g * (1 - a), b: top.b * a + under.b * (1 - a) });
    const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
                         return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
    const ratio = (a, b) => { const [h, l] = [lum(a), lum(b)].sort((x, y) => y - x); return (h + 0.05) / (l + 0.05); };
    const behind = (el) => {
      const stage = document.getElementById("stage") || document.body;
      let c = rgb(getComputedStyle(stage).backgroundColor) || { r: 255, g: 255, b: 255 };
      for (const bg of document.querySelectorAll(".bg")) {
        const v = rgb(getComputedStyle(bg).backgroundColor), a = alpha(bg);
        if (v && a > 0) c = over(v, c, a * v.a);
      }
      const chain = [];
      for (let e = el; e && e !== stage; e = e.parentElement) chain.unshift(e);
      for (const e of chain) {
        const cs = getComputedStyle(e);
        if (cs.backgroundImage !== "none" && e !== el) return null;      // a gradient or a picture: not judged here
        const v = rgb(cs.backgroundColor), a = alpha(e);
        if (v && v.a > 0.02 && a > 0) c = over(v, c, a * v.a);
      }
      return c;
    };
    const related = (a, b) => a === b || a.contains(b) || b.contains(a);
    // where the letters are: a line box is taller than its glyphs (ascent and descent), so two snug lines of a
    // headline touch boxes without touching letters; collisions are judged on the middle 60% of each line
    const core = (r) => ({ left: r.left + 2, right: r.right - 2, top: r.top + r.height * 0.2, bottom: r.bottom - r.height * 0.2,
                           width: r.width - 4, height: r.height * 0.6 });
    const hit = (a, b) => Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) * Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
    for (const t of texts) {
      // half a pixel of grace: the camera's push-in ends at 0.995, so 28 px type settles at 27.9
      if (!t.formula && t.px < minPx - 0.5) out.push({ kind: "small", text: t.text, detail: "text drawn at " + t.px.toFixed(0) + " px (at least " + minPx + "): too small" });
      if (!t.formula && !t.el.closest("svg")) {
        const g = behind(t.el), fg = rgb(getComputedStyle(t.el).color);
        if (g && fg) {
          const seen = over(fg, g, fg.a * alpha(t.el));
          const k = ratio(seen, g);
          if (k < 3) out.push({ kind: "contrast", text: t.text, detail: "contrast " + k.toFixed(2) + ":1 against its ground (3:1 at least)" });
        }
      }
      // judged on the letters, not the font's box (a 220 px number's box reaches far above its digits)
      for (const r of t.rects.map((r) => clip(t.el, t.formula ? r : core(r)))) if (r.width > 1 && outside(r)) { out.push({ kind: "outside", text: t.text, detail: "outside the safe area" + where(r) }); break; }
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
      for (const r of (t.formula ? [] : t.rects.map(core))) {
        // a grid every ~6 px down and ~24 px across the line: a thin rule or a spoke through the words is found
        const ny = Math.max(4, Math.ceil(r.height / 6)), nx = Math.max(3, Math.ceil(r.width / 24));
        for (let ix = 0; ix < nx; ix++) for (let iy = 0; iy < ny; iy++) {
          const x = r.left + r.width * (ix + 0.5) / nx, y = r.top + r.height * (iy + 0.5) / ny;
          const stack = document.elementsFromPoint(x, y);
          const j = stack.findIndex((e) => e === t.el || t.el.contains(e));
          if (j < 0) continue;
          for (const e of stack.slice(0, j)) {
            if (related(e, t.el) || !opaque(e) || alpha(e) < 0.5 || seen.has(e)) continue;
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
      if (a.rects.some((ra) => b.rects.some((rb) => hit(core(ra), core(rb)) > 6)))
        out.push({ kind: "overlap", text: a.text, detail: "overlaps \"" + b.text + "\"" });
    }
    for (const el of root.querySelectorAll("*")) {          // shapes too must stay inside the safe area
      if (!painted(el) || alpha(el) < 0.5) continue;
      const r = clip(el, el.getBoundingClientRect());
      const bare = !el.textContent.trim() && !el.querySelector(".katex");      // no words on it: it may use the lower frame
      if (r.width > 1 && r.height > 1 && outside(r, bare ? area.picture_bottom : area.bottom))
        out.push({ kind: "outside", text: "", detail: name(el) + " is outside the safe area" + where(r) });
    }
    return out;
  }, s, job.area, job.min_px);
  for (const f of found) issues.push(Object.assign({ page: pg.index, scene: s.id, t: s.t }, f));
}
// the cuts: each host shown only inside its own clip (data-start, data-duration), as HyperFrames does
for (const h of pg.handovers || []) {
  const f = await page.evaluate((h) => {
    const tl = Object.values(window.__timelines || {})[0];
    for (const c of document.querySelectorAll(".card-host")) {
      const s = parseFloat(c.dataset.start), d = parseFloat(c.dataset.duration);
      c.style.visibility = h.t >= s - 1e-6 && h.t < s + d - 1e-6 ? "visible" : "hidden";
    }
    for (const c of document.querySelectorAll(".cap-layer, .tx-layer")) c.style.visibility = "hidden";
    if (tl) tl.seek(h.t, false);
    const alpha = (el) => {
      let o = 1;
      for (let e = el; e && e.nodeType === 1; e = e.parentElement) {
        const cs = getComputedStyle(e);
        if (cs.visibility === "hidden" || cs.display === "none") return 0;
        o *= parseFloat(cs.opacity);
      }
      return o;
    };
    // what a scene shows: its strongest piece of text or paint, and where its shown pieces are
    const shown = (id) => {
      const root = document.getElementById(id);
      if (!root) return { a: 0, box: null };
      let a = 0, box = null;
      for (const el of root.querySelectorAll("*")) {
        const own = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
        const cs = getComputedStyle(el);
        const paint = own || cs.backgroundColor !== "rgba(0, 0, 0, 0)" || cs.backgroundImage !== "none" || el.tagName.toLowerCase() === "img";
        if (!paint) continue;
        const v = alpha(el);
        if (v < 0.3) continue;
        const r = el.getBoundingClientRect();
        if (r.width < 2 || r.height < 2) continue;
        a = Math.max(a, v);
        box = box ? { l: Math.min(box.l, r.left), t: Math.min(box.t, r.top), r: Math.max(box.r, r.right), b: Math.max(box.b, r.bottom) }
                  : { l: r.left, t: r.top, r: r.right, b: r.bottom };
      }
      return { a, box };
    };
    const A = shown(h.a), B = shown(h.b);
    if (A.a < 0.3 || B.a < 0.3 || !A.box || !B.box) return null;
    const cross = Math.min(A.box.r, B.box.r) > Math.max(A.box.l, B.box.l) && Math.min(A.box.b, B.box.b) > Math.max(A.box.t, B.box.t);
    return cross ? { kind: "handover", text: "", detail: h.a + " and " + h.b + " are both on screen (" + Math.round(A.a * 100) + "% and " +
                     Math.round(B.a * 100) + "%): the old scene must be gone by the cut" } : null;
  }, h);
  if (f) issues.push(Object.assign({ page: pg.index, scene: h.b, t: h.t }, f));
}
}
await browser.close();
process.stdout.write(JSON.stringify(issues) + "\n");
