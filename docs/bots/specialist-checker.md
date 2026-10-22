# Specialist checker

- **Schedule:** `CRON_TZ=America/New_York 57 6 * * 4` (Thursdays 6:57 AM)
- **Writes:** `cois` (profile.vettedAt, profile.vetting), `botlog` (`vetting-YYYY-MM-DD`)

## Instructions (exact text of the scheduled task)

```text
Check specialists before the user refers anyone to them, in the user's Referral Bridge app, a referral CRM published as a claude.ai artifact at https://claude.ai/artifact/FgVJzZehAG5NhqRiwq2st9 . Its data lives in the artifact's database. Use the Artifact tool's database actions (read_db / write_db), or the ArtifactData tool if that is what this session offers. Do not republish or edit the page itself. In the app this job is shown as the "Specialist checker" bot.

1. Read the collections "cois" (specialists) and "matches". Skip records with sample: true.
2. Pick up to 8 specialists with no profile.vettedAt (or one older than 365 days). Put first anyone in a match with status Approved, Introduced or Meeting, then the newest.
3. For each, check public records that fit their profession, and record what each one shows:
   - Investment and retirement advisors: FINRA BrokerCheck and SEC Investment Adviser Public Disclosure (registration, disclosures).
   - CPAs: the state board of accountancy license lookup.
   - Attorneys: the state bar's attorney search (admission, status, discipline).
   - Lenders and mortgage-related: NMLS Consumer Access.
   - Insurance agents: the state insurance department license lookup.
   - Everyone: the firm website (does it confirm their title and role?), and BBB or review sites for the firm.
   Only record what a source actually shows, each with its URL. If a lookup can't be done or finds nothing, say so. Never mark someone clear without a source.
4. Update each specialist document (merge; don't remove fields): profile.vettedAt (now ISO), profile.vetting: {status ("clear" if at least one official record confirms them with no disciplinary issues; "flag" if a record shows disciplinary action, an inactive or lapsed license, or conflicting info; "unverified" if nothing official was found), checks: [{what, result, url}], note (1–2 plain sentences the user can read at a glance)}. Add phone, email or website only if an official source publishes them and the field is empty. Set updatedAt: now.
5. Write a run report to the collection "botlog", document id "vetting-YYYY-MM-DD" (today), with fields: bot: "vetting", ranAt (now ISO), summary (one plain sentence under 120 characters, e.g. "Checked 8 specialists: 6 clear, 1 flag, 1 unverified"), added: {checked: <n>}, links: [{title, url}] for up to 6 records, putting any flags first.
6. Write everything in one batch. Then reply with a short summary, calling out any flags clearly.
```
