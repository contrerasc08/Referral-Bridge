# Referral Bridge

Business needs, bridged to the right specialists.

> **Status:** Working v1, live as a private claude.ai artifact. 11 scheduled bots (all tasks set up) and 7 in-app bots.

## What it is

Referral Bridge is a referral CRM for someone who connects business owners with the specialists who can help them: bankers, SBA and equipment lenders, CPAs, attorneys, insurance agents, wealth advisors, M&A advisors and more.

Every company starts as a **business**. A business becomes a **lead** when one of its needs (financing, succession, insurance and so on) is **bridged** to a specialist who can deliver the solution. The app finds businesses with fresh signals (expansions, hires, ownership changes), predicts what they need, matches the right specialist, and tracks outreach until the referral closes.

It focuses on owner-run US businesses with roughly $1M–$100M in revenue.

## What's built

- **CRM:** businesses, specialists, bridges (Suggested → Approved → Introduced → Meeting → Closed), a prospect pipeline board, outreach history, follow-up tasks, appointments and CSV export. Wide screens get a left sidebar modeled on Jessica's OliveStone CRM.
- **Scoring:** an Opportunity Score (why contact this business now), predicted needs, and a Match Score (how right this specialist is). It learns from closed and rejected bridges. See [docs/specs/scoring.md](docs/specs/scoring.md).
- **Market awareness:** news headlines adjust needs, and industry climate favors growing sectors.
- **Targeting:** focus states, industries, employee range, owner-run only, and excluded words.
- **Brain:** one search across everything, plain-language questions answered from stored data, a bot dashboard, and "what the bots noticed".
- **Bots:** scheduled cloud bots find businesses and specialists, research contacts, write outreach drafts, watch for new signals, vet specialists, track news and coach weekly. In-app bots flag stuck bridges, coverage gaps, missing data and duplicates. See [docs/bots/](docs/bots/README.md).
- **Demo mode** with made-up data, for showing the app safely.

## Repository structure

```
referral-bridge/
├── README.md
├── src/
│   └── index.html           # The whole app (single file, vanilla JS)
└── docs/
    ├── decisions.md         # Why things are the way they are
    ├── roadmap.md           # Done, next, later
    ├── specs/
    │   ├── app-and-workflow.md
    │   ├── data-model.md
    │   └── scoring.md
    └── bots/
        ├── README.md        # Schedules, outputs, report format
        └── *.md             # Exact instructions for each scheduled bot
tests/
├── test_review_fixes.py     # Browser tests (Playwright) for save/delete, flagged specialists, need scoring, learning
├── test_crm_navigation.py   # Browser tests for the sidebar, prospect board, outreach history, follow-ups, appointments
├── test_save_failures.py    # Browser tests: a failed save never shows a success message
└── db/                      # Security tests for the Supabase rules (tests/db/run.sh)
supabase/
├── migrations/              # Tables, roles and row-level security
└── bootstrap_owner.sql      # One-time owner setup, run by hand
```

## How this project is run

This repository is the **single source of truth**. The live app is published from `src/index.html`, and the bots' instructions are recorded in `docs/bots/`.

| Role | Who | Responsibilities |
|------|-----|------------------|
| Owner | @contrerasc08 | Final decisions, priorities |
| Build & implement | Claude | Writes code, publishes the app, runs the bots, keeps docs current |
| Review & plan | ChatGPT | Reviews code and specs, plans features, suggests improvements |

AI assistants don't share conversations. Anything important (decisions, plans, specs) must be written into this repo.

### Change workflow

1. Changes go on a branch with a pull request.
2. The owner reviews and merges.
3. Claude republishes the live app from `src/index.html` and updates any scheduled bot whose instructions changed.

## Running it locally

Open `src/index.html` in a browser. Without the artifact database it saves to `localStorage`. Use ☰ → **Show demo with sample data** to explore. The Ask and CSV-export features only work inside claude.ai.

## Your data

Business, contact and outreach records live in the artifact's private database, **not** in this repo. Nothing personal is committed here.
