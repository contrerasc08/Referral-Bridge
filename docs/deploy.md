# Putting the portal online (private, free address)

The portal in `web/` is static files. Cloudflare serves it as a Worker with static assets, on a free `*.workers.dev` address, so no domain needs to be bought. `wrangler.jsonc` describes it. Nothing is deployed without the owner's go-ahead.

## One-time setup (owner)

1. In the Cloudflare dashboard, go to **Workers & Pages → Create → Import a repository**, connect GitHub, and pick `Referral-Bridge`.
2. Settings:
   - Project name: `referral-bridge` (must match `name` in `wrangler.jsonc`)
   - Build command: `node scripts/write-config.mjs`
   - Deploy command: `npx wrangler deploy`
   - Build variables (under **Advanced settings → Build variables**, not runtime variables):
     - `SUPABASE_URL` = `https://<project>.supabase.co`
     - `SUPABASE_PUBLISHABLE_KEY` = the **publishable** key (`sb_publishable_...`). Never the secret key. The build stops if it's given one.
3. Deploy. The address is `https://referral-bridge.<your-subdomain>.workers.dev`.
4. In Supabase, **Authentication → URL Configuration**: set **Site URL** to that address and add it under **Redirect URLs**. Invite and reset emails link there.
5. Optional extra lock: the Worker's **Settings → Domains & Routes** lets you turn on Cloudflare Access, which puts an email check in front of the whole address (free up to 50 people).

## Updating

Merging to `main` redeploys automatically. Other branches get their own preview address.

## Trying it locally

Copy `web/config.example.js` to `web/config.js`, fill in the URL and publishable key, then run `npx wrangler dev` (or `python3 -m http.server -d web 8080`). `web/config.js` is ignored by git.

## Sign-in page design and bridge photos

The sign-in page uses the Ivory & Slate design shared with the EcoBridge site. Its George Washington Bridge photo (looking along the empty lanes toward the towers) changes with the time of day in New York:

| Part of day | When | File |
| --- | --- | --- |
| Morning | Sunrise until noon | `web/assets/bridges/gw-entry-morning.webp` |
| Afternoon | Noon until sunset | `web/assets/bridges/gw-entry-afternoon.webp` |
| Night | Sunset until sunrise | `web/assets/bridges/gw-entry-night.webp` |

Keep the same camera angle and crop in all three, with no cars or people. Save them as WebP about 1600px wide.

The page picks the photo with `web/js/bridge-clock.mjs`, which uses SunCalc 2.1.2 (copied unchanged into `web/js/vendor/suncalc.js`) to work out sunrise and sunset at the bridge each New York day, including daylight saving changes. `web/js/bridge-images.mjs` loads the right photo on arrival, when the tab comes back into view, and every 30 seconds while the page is open. If a photo fails to load, the last good one stays. Until the photos are added, a drawn bridge tinted for the time of day shows instead. The same files are used by the EcoBridge site; keep the copies in step.

"Back to home" and "Request access" point to the EcoBridge site. To change that address, set the optional `ECOBRIDGE_URL` build variable in Cloudflare.
