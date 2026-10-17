# Referral Bridge

AI-powered business relationship and referral platform.

> **Status:** Working app recovered from Claude (2026-10-17). See [`docs/recovery-report.md`](docs/recovery-report.md).

## Overview

Referral Bridge finds businesses that are likely to need help right now (from signals like new formations, expansions, hiring and financing), predicts what they need, and bridges each need to the right specialist: bankers, CPAs, attorneys, insurance agents and other advisors. A business becomes a *lead* once one of its needs is bridged.

## Goals

- [ ] Define core user types (e.g., referrers, receiving businesses, admins)
- [ ] Define the referral workflow (submit → track → follow up → reward)
- [ ] Choose tech stack
- [ ] Build MVP

## How this project is run

This repository is the **single source of truth** for Referral Bridge: code, decisions, and documentation all live here.

| Role | Who | Responsibilities |
|------|-----|------------------|
| Owner | @contrerasc08 | Final decisions, priorities |
| Build & implement | Claude | Writes code, project structure, technical docs |
| Review & plan | ChatGPT | Reviews code, plans features, suggests improvements |

AI assistants do **not** share conversations with each other. Anything important (decisions, plans, specs) must be written into this repo so every assistant works from the same information.

## Repository structure

```
referral-bridge/
├── README.md
├── src/
│   └── index.html            # The whole app (single file: HTML, CSS, JavaScript)
├── docs/
│   ├── recovery-report.md    # What exists, what's missing, next milestone
│   ├── data-model.md         # Collections and fields (the database schema)
│   ├── automations/          # Instructions for the scheduled research bots
│   ├── decisions.md          # Log of key decisions and why
│   ├── roadmap.md            # Planned work
│   └── specs/                # Feature specifications
├── design/                   # Design mockups
└── archive/                  # Earlier prototypes
```

## Decision log

Key decisions are recorded in [`docs/decisions.md`](docs/decisions.md).

| Date | Decision |
|------|----------|
| 2026-10-17 | Use GitHub as the central hub for code, history, and docs |

## Getting started

Open `src/index.html` in any browser. No install or build step.

- Opened as a plain file, it saves data on that device only and the AI "Ask" feature is off.
- The live version runs inside Claude as an artifact, where data syncs across devices and AI questions work.
