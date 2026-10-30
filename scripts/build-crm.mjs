// Builds the portal's copy of the CRM from src/index.html, so both run the same code.
// Writes web/crm/app.css and web/crm/app.js (generated, not committed). The portal's
// security policy forbids inline scripts and styles, so they move into their own files.
// Run by scripts/write-config.mjs at deploy time; run it by hand before local tests.
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";

const src = readFileSync(new URL("../src/index.html", import.meta.url), "utf8");
const stop = (m) => { console.error("build-crm: " + m); process.exit(1); };

const css = (src.match(/<link href="https:\/\/fonts\.googleapis\.com[^>]*>\s*<style>([\s\S]*?)<\/style>/) || [])[1];
if (!css) stop("couldn't find the app's stylesheet in src/index.html");
const markup = (src.match(/(<header class="top">[\s\S]*?)<script>/) || [])[1];
if (!markup) stop("couldn't find the app's markup in src/index.html");
const scripts = [...src.matchAll(/<script>([\s\S]*?)<\/script>/g)];
const js = scripts.length ? scripts[scripts.length - 1][1] : "";
if (!/function connect\(\)/.test(js)) stop("couldn't find the app's script in src/index.html");

// Figtree is served from this site instead of Google Fonts.
const font = `@font-face{font-family:Figtree;font-style:normal;font-weight:300 900;font-display:swap;src:url(../fonts/figtree-latin-wght.woff2) format("woff2")}\n`;

mkdirSync(new URL("../web/crm/", import.meta.url), { recursive: true });
writeFileSync(new URL("../web/crm/app.css", import.meta.url), "/* Generated from src/index.html by scripts/build-crm.mjs. Edit the source, not this file. */\n" + font + css.trim() + "\n");
writeFileSync(new URL("../web/crm/app.js", import.meta.url),
  "/* Generated from src/index.html by scripts/build-crm.mjs. Edit the source, not this file. */\n" +
  "document.body.innerHTML=" + JSON.stringify(markup.trim()) + ";\n" + js.trim() + "\n");
console.log("build-crm: wrote web/crm/app.css and web/crm/app.js");
