// Writes web/config.js from environment variables at deploy time, so no key is stored in the repo.
// Cloudflare Pages: build command "node scripts/write-config.mjs", output directory "web".
// Needs SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY. Refuses a secret or service-role key.
import { writeFileSync } from "node:fs";
const url = (process.env.SUPABASE_URL || "").trim().replace(/\/+$/, "");
const key = (process.env.SUPABASE_PUBLISHABLE_KEY || "").trim();
const stop = (m) => { console.error("write-config: " + m); process.exit(1); };
if (!url || !key) stop("set SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY");
if (!/^https:\/\/[a-z0-9-]+\.supabase\.co$/.test(url)) stop("SUPABASE_URL should look like https://<project>.supabase.co");
if (/^sb_secret_/.test(key)) stop("that is a secret key; use the publishable key (sb_publishable_...)");
const parts = key.split(".");
if (parts.length === 3) {
  let role = "";
  try { role = JSON.parse(Buffer.from(parts[1], "base64url").toString()).role; } catch {}
  if (role === "service_role") stop("that is the service_role key; use the publishable key");
}
writeFileSync(new URL("../web/config.js", import.meta.url),
  "window.RB_CONFIG=" + JSON.stringify({ supabaseUrl: url, supabaseKey: key }) + ";\n");
console.log("write-config: wrote web/config.js for " + url);
