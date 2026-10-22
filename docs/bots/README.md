# Bots

Referral Bridge has two kinds of bots.

- **Scheduled bots** run in the cloud as Claude scheduled tasks, even when the app is closed. Each one reads and writes the app's database (never the page code) and leaves a run report in the `botlog` collection, which the Brain tab shows.
- **In-app bots** are plain JavaScript in `src/index.html`. They recompute every time the app renders, so they're always current.

All times are New York time. Every scheduled bot runs in auto mode (no approval prompts) and uses the owner's Claude usage.

## Scheduled bots

| Bot | Schedule | What it does | Writes | Report id | Instructions |
|---|---|---|---|---|---|
| News bot | Every other day (odd dates), 6:47 AM | Economic and industry headlines that shift needs and industry climate | `news` | `news-YYYY-MM-DD` | [news.md](news.md) |
| Prospector | Mondays 6:52 AM | New $1M–$100M owner-run businesses, plus specialists who can serve them | `businesses`, `signals`, `cois` | `prospector-…` | [prospector.md](prospector.md) |
| Research bot | Tue, Thu, Sat 6:42 AM | Owner, phone, email and website for businesses in the research queue | `businesses` (contacts, profile), `contactRequests` | `research-…` | [research.md](research.md) |
| Intro writer | Weekdays 7:12 AM | Draft owner emails, call scripts, specialist intros and follow-ups. Never sends anything. | `drafts` | `writer-…` | [intro-writer.md](intro-writer.md) |
| Signal watcher | Mon, Wed, Fri 6:37 AM | New events at followed and top businesses | `signals` | `watcher-…` | [signal-watcher.md](signal-watcher.md) |
| Specialist checker | Thursdays 6:57 AM | License and disciplinary checks before referring | `cois` (profile.vetting) | `vetting-…` | [specialist-checker.md](specialist-checker.md) |
| Weekly coach | Fridays 4:07 PM | Week in review and next week's plan (shown on Today) | `botlog` only | `coach-…` | [weekly-coach.md](weekly-coach.md) |
| Retiring owners | Tuesdays 6:33 AM | Lead generator: owners nearing retirement or exit. Follows Targeting. | `businesses`, `signals` | `succession-…` | [retiring-owners.md](retiring-owners.md) |
| Permits and expansions | Wednesdays 6:28 AM | Lead generator: permits, IDA/EDC announcements, expansions. Follows Targeting. | `businesses`, `signals` | `permits-…` | [permits-expansions.md](permits-expansions.md) |
| New business filings | Mon and Thu 6:23 AM | Lead generator shown in the app. **No scheduled task yet.** | — | `filings-…` | — |
| Hiring surges | Fridays 6:18 AM | Lead generator shown in the app. **No scheduled task yet.** | — | `hiring-…` | — |

## In-app bots

| Bot | What it shows |
|---|---|
| Matchmaker | How many businesses are bridge-ready and how many still need a specialist |
| Scorer | How many businesses were scored, and the top one |
| Follow-up watcher | Follow-ups due now and later this week |
| Pipeline nudger | Bridges stuck in the same stage for 7+ days |
| Gap finder | The most common missing specialist type, by state |
| Data cleaner | Businesses missing a phone or email, state, industry or named owner |
| Duplicate checker | Possible duplicate businesses |

## Run report format (`botlog`)

```json
{
  "bot": "writer",
  "ranAt": "2026-10-21T11:17:00Z",
  "summary": "One plain sentence under 120 characters",
  "added": { "drafts": 3 },
  "links": [{ "title": "Source name", "url": "https://…" }],
  "plan": ["Weekly coach only: 3–6 concrete actions"],
  "gaps": ["Lead generators only: missing specialist coverage"]
}
```

## Changing a bot

1. Edit its instructions file here in a pull request.
2. After it's merged, ask Claude to update the scheduled task to match. The task, not this file, is what actually runs.
3. If the bot writes new fields, update `docs/specs/data-model.md` and the app.
