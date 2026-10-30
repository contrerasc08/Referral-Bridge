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
