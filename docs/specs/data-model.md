# Data model

The app stores everything in its artifact database: a set of document collections, each document with an `id`. The page subscribes to every collection live (`onSnapshot`), so changes from the bots appear without a reload.

Writes are optimistic: the screen updates first, then the database. If a save or delete fails, the app puts the previous record back (or removes a new one that never saved), says so in a message, and `put` or `del` returns `false`. On success they return `true`. Every action checks that result and shows its success message only when the save worked; actions that save several records (deleting a business, bulk removes, quiz matches) say how many failed. When the database isn't available (for example a local file preview), the app falls back to `localStorage` under the key `rb-data`. Demo mode uses `rb-demo`.

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
| `prof` | `companyProfiles` | Company research profiles: any company, every fact linked to its sources |
| `crlist` | `researchLists` | Your private lists of company profiles or people |

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

## companyProfiles

A RelPro-style profile of one company, started on the Company research screen and filled by the Company research bot (or by pasting what you found). It can exist without a business record; "Save to my businesses" creates or updates one and sets `bizId`.

| Field | Notes |
|---|---|
| `name`, `domain`, `city`, `state` | What you searched for |
| `status` | `queued`, `researching`, `done`, `partial`, `failed` |
| `requestedAt`, `researchedAt` | ISO dates |
| `bizId` | The linked business, once saved |
| `sources[]` | `{id, name, url, type (official\|company\|directory\|social\|news\|data\|you), retrievedAt, found, note}`. Ids starting with `u` were added by you. |
| `fields` | Keyed by `legalName, dba, description, industry, ownership, founded, revenue, employees, locations, address, phone, email, website, linkedin, facebook, instagram, x, entityType, status, stateId, formed, registeredAgent, npi, licenses` and the Highlights `naics, sic, certifications, international, sustainability, cannabis, technology, censusTract, tractIncome`. Each is `{v, src[], alt[{v, src[]}]}`: `src` lists the source ids that report `v`; `alt` holds values other sources reported. |
| `people[]` | `{name, title, linkedin, phone, email, src[]}` |
| `filings[]` | `{date, kind, detail, src[]}`. The Finance tab groups kinds into Loans (SBA loan, PPP loan, Loan, Financing), Funding (SEC Form D, Funding, Investment), Liens (UCC lien, Tax lien, Judgment), Government contracts (Government contract, Grant) and Other filings. |
| `news[]` | `{date, title, url, sourceName, summary}` |
| `signals[]` | `{type, date, evidence, src[]}`; become `signals` records when the profile is saved as a business |
| `industryGroup` | One of `INDUSTRIES`, used when saving as a business |
| `summary`, `needs[]`, `talkingPoints[]` | Shown under "Before you call" |

`viewedAt` and `exportedAt` on a profile feed the two system lists, "Previously viewed" (stamped when opened, at most once an hour) and "Exported to file" (stamped when the profile, its people, or a list holding it is exported).

## researchLists

Private lists, like RelPro's Lists: `{name, kind ("company" | "people"), items[]}`. Company items are `{profId, addedAt}`; people items are `{profId, name, title, addedAt}`. System lists aren't stored; they're computed from `viewedAt` and `exportedAt`. On the Profiles screen any list can be shown alone or excluded, so you see only net-new companies (a people list covers the companies its people work at).

Favorite Roles groups live in `settings` doc `favroles`: `{groups: [{name, words}]}`, where `words` is a comma list of title words. Without it the app uses four default groups (Owners and executives, Finance, Operations, HR and benefits).

Saving to a business only fills fields the business doesn't already have, adds new contacts (with their source), adds the profile's source links to `profile.sources`, and adds signals with provider `company-research` (provenance `VERIFIED` when the first source is an official record).

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
