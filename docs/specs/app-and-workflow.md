# App structure and daily workflow

## How it's built

- **One self-contained HTML file** (`src/index.html`) with vanilla JavaScript and CSS. There's no build step and no framework.
- **Published as a claude.ai artifact**, which gives it three runtime capabilities:
  - `db`: the shared document database described in [data-model.md](data-model.md).
  - `sample`: lets the Brain's "Ask" feature query Claude with read-only tools over stored data. The tools are `find_businesses`, `get_business`, `find_signals`, `find_advisors`, `get_news`, `get_climate` and `coverage_gaps`.
  - `downloads`: CSV export.
- **Rendering:** each view is a function that returns an HTML string (`viewToday`, `viewBiz`, `viewBizIntel`, `viewBrain` and so on). `render()` redraws the current view. A single delegated click handler reads `data-*` attributes on buttons.
- **Light and dark mode** come from CSS variables, and the layout is designed for phones first.

## Navigation

On phones, the bottom tabs are **Today**, **People**, **Bridges** and **Brain**. Each tab has sub-sections shown as pills (`GROUPS`):

| Tab | Sub-sections |
|---|---|
| Today | Today, Pipeline, Next steps, Discovery calls, Touch log, Research queue |
| People | Businesses, Specialists, Scout, Match a specialist, Look up info |
| Bridges | Bridges (pipeline) |
| Brain | Search & ask, Targeting, Signals, News, Industry climate |

On screens 1024 px and wider, a left sidebar (`SIDENAV`) replaces the bottom tabs and pills, in four groups: **Your day** (Today, Next steps, Discovery calls), **Prospecting** (Pipeline, Businesses, Scout, Touch log, Research queue), **Referrals** (Bridges, Specialists, Match a specialist) and **Insight** (Ask the Brain, Signals, News, Industry climate, Targeting). Labels and layout are Referral Bridge's own; Jessica's OliveStone CRM was a reference for the kind of pages, not a template.

The ☰ menu in the header holds Targeting, Data sources, How to use, and Demo mode (show, reset, exit).

## Demo mode

Demo mode swaps in made-up sample businesses, specialists, bridges, drafts and bot reports, stored in `localStorage` under `rb-demo`. The real database isn't connected at all, so it's safe for showing the app to people. Turn it on from the menu, or by setting `localStorage["rb-mode"]="demo"`.

## Screens

- **Today (home page):** the date (weekday, full date, week, quarter) and four numbers: on today's agenda, overdue, discovery calls, bridge-ready. Then the **Agenda** (today's calls, follow-ups and tasks, then what's coming up), **Talking points** for this week's sales conversations (industry tailwinds and headwinds, news that raises a need with named businesses, quiet introductions, the coach's plan), and an **Industry briefing** (climate, headlines with the needs they raise, and updates since your last visit).
- **Next steps:** your list (business follow-ups and tasks, grouped overdue, today, coming up) and **Suggested for you** (introductions, sales strategy, check-ins on quiet introductions, specialists to find, coach items) with Add to my list, Not now, or Make the introduction. Tapping a task opens the client: contact details, recent history, quick log (Called them, They called me, Emailed them, They emailed me) and one-tap "done, follow up in…". Recording a touch from a task can finish it and set the next follow-up.
- **Scout:** a sentence to complete ("Show me … in … that are …"), then results from your list, across the web and public records, with a panel to have Claude do the search.
- **Businesses:** search, filter chips, and the revenue range.
  - Filters: All, Bridge ready, Follow-up due, Needs a specialist, Not contacted, Fits targeting, one per lead generator, and Drafts ready.
  - Each card shows the score, "Why now", the top need, up to 3 tags and one industry headline.
- **Business page:**
  - The Opportunity score (tap for the breakdown) and status (Lead / Business / Sample).
  - A **Next step** with Call, Log outreach, Bridge to <specialist> and Find a contact buttons.
  - Collapsible sections: Ready-to-send drafts, Bridges and specialists, Contacts, Outreach (stage and follow-up), What they likely need, Industry brief, Signals, Introductions, Details.
- **Page headers** on the CRM pages show the section, the title with a count, and the main commands at top right (for example **Log call or email** and **Export**).
- **Prospect pipeline:** a board with one column per prospect stage and its count. Each card shows the city, contact info on file (owner, phone, email, website, as n/4), and a red **No next step** tag when an open prospect has no follow-up date and no discovery call booked. Drag a card to another column, or use its **⌄** menu: Log call or email, Set or change follow-up, Mark follow-up done, Open business page, Move to stage. **List view** shows the same as a table.
- **Outreach history:** logged, % with an outcome, interested or spoke; outcome chips with counts that filter the table; search over businesses, people and notes; **Log call or email** (pick a business) and **Export** (the filtered log as CSV). Conversion stats and the business export sit under "Conversion and export".
- **Follow-up tasks:** overdue, today and upcoming follow-ups with Log call, Change and Done, then worked prospects with no next step.
- **Appointments:** upcoming discovery calls and the last 30 days.
- **Bridges:** the pipeline (Suggested → Approved → Introduced → Meeting → Closed / Rejected), plus outreach stats and CSV export.
- **Brain:** one search box that covers businesses, specialists, signals and news, with plain-word synonyms. Typing a question offers **Ask the Brain**. Below that are the bot dashboard and "What the bots noticed" (signal → need → specialist chains).

## Daily routine

1. Open **Today** and handle overdue follow-ups.
2. Work "Contact these first": send the drafts the Intro writer prepared, or call.
3. Log every touch with **Log outreach**. Booking a discovery call moves the stage automatically.
4. When a business is bridge-ready, tap **Bridge to <specialist>**. That approves the bridge, and the Intro writer drafts the intro to the specialist.
5. Move bridges along in **Bridges**. Closed and Rejected outcomes teach the scoring.
6. On Friday, read the Weekly coach's plan.

## Making changes

1. Edit `src/index.html` on a branch and open a pull request.
2. Before publishing, check the script's syntax: extract the main `<script>` block and run `node --check` on it.
   - Browser tests (Playwright with a mock database that can be forced to fail): `python3 tests/test_review_fixes.py` for the PR #1 fixes and `python3 tests/test_crm_navigation.py` for navigation and the CRM pages.
3. Test at a 390 px width in light and dark mode. Seed `localStorage["rb-data"]`, or use demo mode.
4. After merging, republish the artifact from `src/index.html` so the live app and the repo stay identical.
