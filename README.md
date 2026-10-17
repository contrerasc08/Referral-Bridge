# Referral Bridge

AI-powered business relationship and referral platform.

> **Status:** Early planning / setup

## Overview

Referral Bridge helps businesses build, track, and grow referral relationships with partners.

_TODO: Add a 2–3 sentence description of the problem it solves and who it's for._

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
├── README.md          # This file: project overview
├── docs/
│   ├── decisions.md   # Log of key decisions and why
│   ├── roadmap.md     # Planned features and priorities
│   └── specs/         # Feature specifications
└── src/               # Application code (once stack is chosen)
```

## Decision log

Key decisions are recorded in [`docs/decisions.md`](docs/decisions.md).

| Date | Decision |
|------|----------|
| 2026-10-17 | Use GitHub as the central hub for code, history, and docs |

## Getting started

_Setup instructions will be added once the tech stack is chosen._
