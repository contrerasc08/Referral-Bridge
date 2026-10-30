# Decision Log

Record every significant decision here so all collaborators (human and AI) work from the same information.

Format: date, decision, why, and who decided.

---

## 2026-10-17: GitHub is the central hub

- **Decision:** Use this GitHub repository as the single source of truth for code, history, and documentation.
- **Why:** Claude and ChatGPT don't share conversations. A shared repo keeps both working from the same plans and code.
- **Roles:** Claude builds and implements; ChatGPT reviews and plans; the owner makes final calls.
- **Decided by:** @contrerasc08

## 2026-10 (before the repo): A single-file app published as a claude.ai artifact

- **Decision:** Build the app as one self-contained HTML file with vanilla JavaScript, hosted as a claude.ai artifact.
- **Why:** There's no server to run. The artifact provides a private database, Claude-powered Q&A and file downloads. Changes can be published in seconds.
- **Trade-off:** One big file. If the app outgrows this, the next step is splitting it into modules with a build step, or moving to a hosted stack.
- **Decided by:** @contrerasc08 with Claude

## 2026-10: "Business" vs "lead"

- **Decision:** Every company is a *business*. It becomes a *lead* only when one of its needs is bridged to a specialist who can meet it (Match Score ≥ 50).
- **Why:** The value is in the bridge (need + solution), not in a list of names.
- **Decided by:** @contrerasc08

## 2026-10: Target owner-run businesses with $1M–$100M revenue, nationwide

- **Decision:** Default revenue range of $1M–$100M. Skip public companies, large corporations and franchise units. Specialists can come from anywhere in the US.
- **Why:** Early results full of big corporations weren't useful. Owner-run companies have a reachable decision-maker.
- **Decided by:** @contrerasc08

## 2026-10: Two separate scores

- **Decision:** The Opportunity Score (should I contact this business now?) and the Match Score (is this specialist right for them?) stay separate.
- **Why:** They answer different questions. Mixing them hides why a recommendation was made.
- **Decided by:** Claude, approved by @contrerasc08

## 2026-10: Every fact carries provenance

- **Decision:** Signals and contacts are labeled Verified, Sourced (provider data), You entered, or AI estimate. AI inferences count at half weight.
- **Why:** Bots must never invent people, numbers or dates. Labels make it clear what to trust.
- **Decided by:** Claude, approved by @contrerasc08

## 2026-10: Bots write data, never the page, and never send messages

- **Decision:** Scheduled bots read and write only the database and log every run to `botlog`. The Intro writer only drafts; the owner sends.
- **Why:** It keeps the app stable, makes every bot action visible in the Brain tab, and keeps a human in control of outreach.
- **Decided by:** @contrerasc08 with Claude

## 2026-10: Real records stay out of demos and out of git

- **Decision:** Demos use made-up data in a separate storage key. This repo contains code and docs only.
- **Why:** The database holds real people's contact details and a private pipeline.
- **Decided by:** @contrerasc08

## 2026-10-24: CRM navigation follows Jessica's OliveStone CRM

- **Decision:** On wide screens, use a left sidebar with one named item per job (dashboard, businesses, prospect pipeline, outreach history, follow-up tasks, appointments) and put each page's main commands at top right, with a ⌄ menu on every business row or card. Phones keep the bottom tabs and pills.
- **Why:** Jessica's CRM is the workflow people already use for outreach. Matching its layout and commands makes moving between the two tools easy. The screenshots stay out of this repo because they show client and lead names.
- **Decided by:** @contrerasc08 (asked for it), built by Claude

## 2026-10-30: Supabase for login, MFA and company-level security

- **Decision:** Move from the claude.ai artifact database to Supabase Auth (email and password, authenticator-app MFA) and Postgres with row-level security. Host the page on a free static host. Every record belongs to a company, and the database checks each user's role on every read and write.
- **Why:** The app is becoming a multi-company product. Postgres suits linked CRM data, reporting and a later Salesforce sync, and row-level security keeps companies apart even if the page has a bug.
- **Owner account:** created by the owner on the preview, then promoted with a one-time SQL script run by hand. No password or service key is ever in the repo.
- **Decided by:** @contrerasc08, plan by Claude
