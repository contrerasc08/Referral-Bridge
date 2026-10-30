# Roadmap

## Done (v1)
- [x] Repository and docs structure
- [x] CRM: businesses, specialists, bridges pipeline, outreach logging, prospect stages, follow-ups, CSV export
- [x] Signals engine (about 50 signal types) with decay, provenance and corroboration
- [x] Opportunity Score, predicted needs, Match Score, bridges (Match ≥ 50)
- [x] Learning from closed and rejected bridges
- [x] News and industry climate shaping scores
- [x] Revenue range and Targeting
- [x] Research queue for finding real contacts
- [x] Brain tab: unified search, Q&A over stored data, bot dashboard
- [x] Scheduled bots: News, Prospector, Research, Intro writer, Signal watcher, Specialist checker, Weekly coach, Retiring owners, Permits and expansions
- [x] Scheduled tasks for the New business filings and Hiring surges lead generators (created 2026-10-22)
- [x] Review fixes from PR #1: failed saves and deletes restore data; flagged specialists excluded from scoring and new bridges; each bridge scored against its own need; learning only from Closed and Rejected referrals
- [x] In-app bots: Matchmaker, Scorer, Follow-up watcher, Pipeline nudger, Gap finder, Data cleaner, Duplicate checker
- [x] Ready-to-send drafts on business pages
- [x] Demo mode with made-up data
- [x] Code and specs in GitHub
- [x] CRM-style navigation from Jessica's OliveStone screenshots: sidebar on wide screens, prospect pipeline board with drag and ⌄ task menus, outreach history with outcome filters and export, follow-up tasks, appointments

## Next
- [ ] Turn on automatic approval for the **Research bot** task (its Oct 20 run was abandoned waiting for approval)
- [ ] Show the Specialist checker's full results (clear / unverified, with the checks and links) on the specialist detail sheet. "Flagged" already shows on cards and blocks bridges.
- [ ] Show lead generator coverage gaps in the Brain and feed them to the Prospector
- [ ] Read-only sharing for a partner (view without editing)
- [ ] Export or sync to Jessica's OliveStone CRM (needs an import format or API from the vendor)

## Later
- [ ] Split `src/index.html` into modules with a small build step
- [ ] Automated tests for scoring (fixtures and expected scores)
- [ ] Email and calendar connections so sent drafts and booked meetings log themselves
- [ ] Multi-user support (a team sharing one pipeline)
