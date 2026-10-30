# Putting the portal online (private, free address)

The portal in `web/` is static files. It runs on Cloudflare Pages on a free `*.pages.dev` address, so no domain needs to be bought. Nothing is deployed without the owner's go-ahead.

## One-time setup (owner)

1. Create a free Cloudflare account and go to **Workers & Pages → Create → Pages → Connect to Git**. Pick the `Referral-Bridge` repository.
2. Build settings:
   - Production branch: `main`
   - Build command: `node scripts/write-config.mjs`
   - Build output directory: `web`
3. Environment variables (Production and Preview):
   - `SUPABASE_URL` = `https://<project>.supabase.co`
   - `SUPABASE_PUBLISHABLE_KEY` = the **publishable** key (`sb_publishable_...`). Never the secret key. The build stops if it's given one.
4. Deploy. Cloudflare gives an address like `https://referral-bridge.pages.dev`.
5. In Supabase, **Authentication → URL Configuration**: set **Site URL** to that address and add it under **Redirect URLs**. Invite and reset emails link there.
6. Optional extra lock: **Zero Trust → Access** can put an email check in front of the whole address for free (up to 50 people).

## Updating

Merging to `main` redeploys automatically. Pull requests get their own preview address.

## Trying it locally

Copy `web/config.example.js` to `web/config.js`, fill in the URL and publishable key, then serve the folder (for example `python3 -m http.server -d web 8080`) and open http://localhost:8080. Add that address to Supabase's Redirect URLs if you want reset links to come back to it. `web/config.js` is ignored by git.
