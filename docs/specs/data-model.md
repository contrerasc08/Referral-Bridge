# Data model

The app stores everything in its artifact database: a set of document collections, each document with an `id`. The page subscribes to every collection live (`onSnapshot`), so changes from the bots appear without a reload.

Writes are optimistic: the screen updates first, then the database. If a save or delete fails, the app puts the previous record back (or removes a new one that never saved), says so in a message, and `put` or `del` returns `false`. On success they return `true`. When the database isn't available (for example a local file preview), the app falls back to `localStorage` under the key `rb-data`. Demo mode uses `rb-demo`.

Records with `sample: true` are test data. They are hidden from bridges and from every bot.

| App key | Collection | What it holds |
|---|---|---|
| `biz` | `businesses` | Companies that may need help |
| `coi` | `cois` | Specialists ("centers of influence"): bankers, CPAs, attorneys and so on |
| `match` | `matches` | Bridges: a business introduced (or about to be) to a specialist |
| `signal` | `signals` | Dated events at a business that suggest a need |
| `news` | `news` | Headlines that adjust needs and industry climate |
| `outreach` | `outreach` | Calls, emails and other touches with a business owner |
| `drafts` | `drafts` | Outreach drafts written by the Intro writer |
| `botlog` | `botlog` | Run reports from the scheduled bots |
| `settings` | `settings` | `providers` (revenue range, quotas, toggles) and `targeting` |
| `creq` | `contactRequests` | "Find a real contact" requests for the Research bot |
| `req` | `leadRequests` | Requests for new businesses |
| `usage` | `providerUsage` | Daily data-source usage counters |
| `task` | `tasks` | Your tasks and the suggestions you added or dismissed |

## businesses

| Field | Notes |
|---|---|
| `name`, `industry`, `city`, `county`, `state` | `industry` is one of the 27 names in `INDUSTRIES`; `state` is a 2-letter code |
| `contact` | "Name (Title)" |
| `phone`, `email` | Optional, entered by hand |
| `contacts[]` | `{name, role, phone, email, website, sourceName, sourceUrl, retrievedAt, provenance, note}` |
| `profile` | `{website, principal, bio, checkedAt, sources[]}` |
| `revenue`, `revenueEstimate`, `revenueSource`, `revenueSourceUrl`, `revenueAsOf` | Revenue is a number. Text like "2.5M" is parsed. |
| `employees` | Number, used by Targeting |
| `source` | For example "Web research", "Manual", "Demo" |
| `foundBy` | Which lead generator found it: `succession`, `permits`, `filings`, `hiring` |
| `targetFit` | One sentence from a lead generator |
| `trigger`, `formedDate` | Older fields, turned into "legacy" signals |
| `prospectStage` | One of Prospect, Qualified, Contacted, Engaged, Discovery call, Proposal sent, Negotiation, Won, Lost |
| `followUpAt` | YYYY-MM-DD |
| `followed` | Shows the business on Today and tells the Signal watcher to check it |
| `researchStatus`, `researchedAt` | Research queue state (`done`, `partial`, `skip`) |
| `possibleDupOf` | Id of a likely duplicate |
| `lead` | Set by bots. In the app, "lead" status is computed from bridges, not from this field. |
| `notes`, `createdAt`, `updatedAt` | |

## cois (specialists)

`name, firm, profession, healthcare, specialties, bestStage, languages, county, state, serviceArea, phone, email, notes, source, profile{website, otherListings, checkedAt, verified, vettedAt, vetting{status, checks[], note}}`

- `profile.vetting.status` is set by the Specialist checker to `clear`, `flag` or `unverified`. A `flag` excludes the specialist from Match scoring, bridges and new bridge approvals, and shows a red "Flagged" tag on their card.

- `profession` is one of the 18 values in `PROFS`.
- `serviceArea` is a comma list of counties, state codes, or `nationwide`.
- `bestStage` is one of Any stage, Starting out, Growing, Established, Planning exit.

## signals

`businessId, type, provider, providerName, sourceRef, eventDate, detectedAt, evidence, confidence (0–1), provenance, mock, legacy`

- `type` is a key of `SIGNAL_TYPES`, about 50 types.
- `provenance` is `VERIFIED`, `PROVIDER DATA`, `USER-ENTERED` or `AI INFERENCE`.

## matches (bridges)

`bizId, coiId, score, status, trigger, opp, sigTypes[], history[{status, at}], reason`

- `status` is one of Approved, Introduced, Meeting, Closed, Rejected, Dismissed.
- `sigTypes` and the final status feed the learned weights, but only for Closed and Rejected matches (see scoring).

## outreach

`bizId, channel (call|email|text|linkedin|visit|other), outcome, contact, note, at, apptAt, apptTime`

`outcome` is one of `none`, `noanswer`, `voicemail`, `spoke`, `interested`, `booked`, `notint`, `bad`.

## drafts

`bizId, coiId, kind (owner_email|call_script|intro_email|followup_email), subject, body, status (new|sent|dismissed), basedOn[], createdAt, sentAt`

## news

`title, publishedAt, sourceName, url, summary, impact, industries[], states[], needs{needId: ±0.02–0.10}, outlook{industry: −2..+2}, expiresAt, addedAt, scope, provenance`

## botlog

See [../bots/README.md](../bots/README.md#run-report-format-botlog).

## settings

- `providers`: `revMin`, `revMax`, `revUnknown`, `quotaDefault`, `autoResearch`, `newsOff`, `climateFocus` (`growth` | `both` | `off`), plus provider toggles.
- `targeting`: `focusStates[]`, `states[]`, `counties`, `industries[]`, `excludeIndustries[]`, `empMin`, `empMax`, `yearsMin`, `ownerRun`, `keywords`, `excludeWords`, `targetOnly`, `perRun`, `gens{succession, permits, filings, hiring}`.

## tasks

`title, why, kind (strategy|intro|connect|checkin|followup|coach|task), bizId, coiId, matchId, dueAt (YYYY-MM-DD), status (open|done|dismissed), source (suggested|you), key, doneAt`

- Suggestions are computed in the app (`suggestedTasks`) from industry climate, news, bridge-ready businesses, coverage gaps, stalled introductions and the Weekly coach. Each has a stable `key`. Adding one to your list or choosing "Not now" stores a task with that key, so the suggestion doesn't come back.
- Business follow-ups still live on the business (`followUpAt`, `followUpNote`) and show in the same list.

## outreach direction

`outreach.dir` is `out` (you reached out) or `in` (they reached out). Older records have no `dir` and count as `out`.
