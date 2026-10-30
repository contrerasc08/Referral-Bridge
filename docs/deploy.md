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
