// Shared by the dev harnesses: launch Chromium through puppeteer (from this folder's node_modules, the current
// folder's, or $PUPPETEER_DIR) with /opt/pw-browsers/chromium or $CHROME.
import { createRequire } from "node:module";
import path from "node:path";

export async function launch() {
  const roots = [process.env.PUPPETEER_DIR, process.cwd(), path.dirname(new URL(import.meta.url).pathname)].filter(Boolean);
  let puppeteer = null;
  for (const r of roots) {
    try { puppeteer = createRequire(path.join(r, "noop.js"))("puppeteer-core"); break; } catch (e) {}
    try { puppeteer = createRequire(path.join(r, "noop.js"))("puppeteer"); break; } catch (e) {}
  }
  if (!puppeteer) throw new Error("puppeteer not found: npm i puppeteer-core in this folder, or set PUPPETEER_DIR to a folder that has it");
  return puppeteer.launch({ executablePath: process.env.CHROME || "/opt/pw-browsers/chromium", headless: true,
                            args: ["--no-sandbox", "--allow-file-access-from-files", "--font-render-hinting=none"] });
}
