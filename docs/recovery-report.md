# Recovery Report

**Date:** 2026-10-17 · **Branch:** `development` · **Prepared by:** Claude, for review by @contrerasc08 and ChatGPT

No new features were started. This report describes the project exactly as recovered.

---

## 1. Where the project was found

Nothing existed in GitHub before today. The project lived in the owner's Claude account:

| Item | Source | Last updated | In this repo |
|------|--------|--------------|--------------|
| **Referral Bridge app (latest working version)** | Claude artifact `FgVJzZehAG5NhqRiwq2st9` | 2026-10-17 | `src/index.html` |
| Intelligence Preview (interactive phone mockup) | Claude design canvas `GU2A64JC8y8gbrtkmbhbKu` | 2026-09-30 | `design/intelligence-preview/` |
| Bridgework (earlier prototype) | Claude artifact `4Ar7WdBiqAKTGbHRNGQGJw` | 2026-09-22 | `archive/bridgework-prototype.html` |
| News bot, Prospector, Research bot | Claude scheduled tasks | 2026-10-17 | `docs/automations/` |

**Latest working version:** the `FgVJzZeh…` artifact, updated today. It is the only one that is a full app; the other two are an earlier prototype and a design mockup.

**Verification:** I read all 2,108 lines of the app, checked its JavaScript for syntax errors (none), and opened it in a headless browser. Every screen loads with no errors, and adding a test business and specialist produced a correct Opportunity Score, predicted needs and Match Score.

## 2. What the project actually is

The whole app is **one self-contained HTML file** (~240 KB, ~160 functions). There is:

- **No backend server**
- **No SQL database, schema files or migrations** (records are JSON documents; see `docs/data-model.md`)
- **No package dependencies**, so no `package.json` and no `node_modules`
- **No API keys, passwords or `.env` files.** The code only names *placeholder* environment variables (e.g. `RB_GOOGLE_PLACES_API_KEY`) for a future server; no values exist anywhere.

External dependencies are just Google Fonts (Figtree) and, when opened inside Claude, the Claude artifact runtime (`window.claude.use`) for the shared database, AI questions (`sample`) and file downloads.

### Not copied into GitHub, on purpose

- **The live data** (businesses, specialists, contacts, outreach) stays in the artifact database. It includes real people's names, phones and emails, and you asked me to prepare code, not data. If you want a backup, use the app's More › Outreach › Export, or ask me and we'll decide where it should go.
- **Design canvas runtime files** (~4 MB of the canvas editor's own code). Only your mockup and its layout file were copied.

## 3. What is implemented

**Core model**
- Businesses, specialists (advisors), and "bridges" (a business need matched to a specialist). A business becomes a *lead* once a need is bridged at Match Score 50+.
- Intelligence engine: 49 signal types → **Opportunity Score** (0–100, with time decay, source-trust weighting, corroboration and lifecycle bonuses) → 20 **predicted needs** with confidence and urgency → **Match Score** per advisor (need fit, location, expertise, stage, track record, relationship).
- Every score is explainable: "tap for why" shows each point.
- Data labels on everything: Verified, Sourced, AI estimate, You entered, Test data.

**Screens:** Today, Brain (search + AI questions), Businesses, business detail page, Bridges pipeline, Specialists, Signals feed, Outreach CRM, Research queue, Find businesses, Find a specialist (plus a 6-question match quiz), Look up public info, Industry climate, News, Data sources, Guide.

**Working features**
- Add/edit/delete businesses and specialists; contacts with a source on every detail
- CSV import (NY DOS, CT, PA, NJ, NPI registry formats) with NAICS-to-industry mapping and duplicate detection
- CSV export of businesses
- Pipeline stages (Approved → Introduced → Meeting → Closed/Rejected) with history
- Outreach logging, follow-ups, discovery calls, booking and close rates
- Learning loop: signal weights adjust from real outcomes once 10+ intros are recorded
- News and industry climate nudge scores, with caps
- Revenue range filter across the app
- "Ask the Brain": AI answers from stored records only, with clickable citations (works only inside Claude)
- Sync across devices inside Claude; falls back to this-device storage elsewhere
- Light and dark mode, mobile-first layout

**Automations (outside the code):** three scheduled Claude tasks add news, new businesses/specialists, and researched contacts. The News bot last ran successfully this morning; the Research bot was running at the time of this snapshot; the Prospector next runs Monday.

## 4. What still needs development

**Not built yet (the app says so itself)**
1. **Live data connectors.** About 100 sources are catalogued, but none connect live. The 16 "test connectors" generate *fake, labeled* signals. Real signals today come only from manual entry, CSV import, and the scheduled bots.
2. **A server.** Needed for live connectors and API keys.
3. **Real referral-fee or compliance handling.** The old Bridgework prototype had a fee ledger and a warning that CPAs, attorneys and some advisors face fee restrictions; the current app dropped both.

**Structural limits**
4. **Tied to Claude.** Sync, AI questions and the bots depend on the Claude artifact. Outside Claude it's a single-device app with no AI.
5. **Data ceiling.** Each collection loads at most 1,000 records (3,000 signals). Fine now, a hard wall as the Prospector adds ~10–20 records a week.
6. **No accounts, roles or team access.** One user only.
7. **One 2,100-line file.** Hard for two assistants to review and change safely.
8. **No automated tests.**
9. **Two copies of the code.** The live app is still edited in Claude; this repo is a snapshot. Until one is chosen as the source of truth, they will drift.

**Smaller issues noticed**
10. Sample/demo records and test signals can mix into scores until removed (the app warns about this).
11. Industries and markets are partly hard-coded to NY, NJ, CT and PA (lead finder, county lists), while the bots search nationwide.

## 5. Recommended next milestone

**Milestone 1: Make GitHub the source of truth** (no new features)

1. Decide the workflow: changes go into the repo first, then get published to the Claude artifact (or the reverse, but only one direction).
2. Split `src/index.html` into separate files (styles, scoring engine, views, storage) with no behavior change.
3. Add tests for the scoring engine (Opportunity, Needs, Match), since that is the core of the product.
4. Take a data backup in a format you choose.

This makes everything after it safer, including the bigger decision that follows: whether to build a server and a real database (needed for live connectors, more than 1,000 records, and team access) or to keep running inside Claude.

## 6. Questions for the review

- Should GitHub or the Claude artifact be the source of truth going forward?
- Do you want the live data backed up, and where?
- Is staying inside Claude acceptable for now, or is a stand-alone app the goal?
- Should the referral-fee ledger from Bridgework come back?
