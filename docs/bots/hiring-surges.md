# Hiring surges (lead generator)

- **Schedule:** `CRON_TZ=America/New_York 18 6 * * 5` (Fridays 6:18 AM)
- **Task created:** 2026-10-22. No runs yet.
- **Writes:** `businesses` (foundBy `hiring`), `signals`, `botlog` (`hiring-YYYY-MM-DD`, with `gaps`)
- **Follows Targeting** (`settings/targeting`) and the revenue range (`settings/providers`). It can be paused in Targeting.

## Instructions (exact text of the scheduled task)

```text
Find real businesses that are hiring fast or adding senior executives, and add them to the user's Referral Bridge app, a referral CRM published as a claude.ai artifact at https://claude.ai/artifact/FgVJzZehAG5NhqRiwq2st9 . Its data lives in the artifact's database. Use the ArtifactData tool (or the Artifact tool's read_db / write_db actions if that is what this session offers). Do not republish or edit the page itself. In the app this job is shown as the "Hiring surges" lead generator.

How the app thinks: every company is a "business". A business becomes a "lead" when one of its needs is bridged to a specialist. Hiring surges usually create needs for payroll and HR providers, benefits and retirement plan advisors, insurance, business banking, and fractional CFOs.

1. Read the targeting. Get settings/targeting and settings/providers.
   - If targeting.gens.hiring is false, only write the run report in step 6 with summary "Paused in Targeting; nothing searched", then stop.
   - The targeting fields are:
     - focusStates: search these first; at least half of what you add should come from them when real results exist.
     - states: if not empty, only add businesses in these states or in focusStates. If empty, search nationwide.
     - counties: favor these areas.
     - industries: prefer these.
     - excludeIndustries: never add these.
     - empMin / empMax: skip a business when a source puts its employee count outside this range. Unknown is fine.
     - yearsMin: minimum years in business.
     - ownerRun: if true, skip public companies, franchise units, private-equity-owned firms, staffing agencies hiring on behalf of clients, and subsidiaries of large corporations.
     - keywords: prefer businesses that mention these.
     - excludeWords: never add a business whose name or description contains any of these comma-separated words.
     - perRun: the maximum number of new businesses to add this run.
   - The revenue range is in settings/providers: revMin, revMax, and revUnknown (whether unknown revenue is allowed).
   - If settings/targeting is missing, use these defaults: focusStates NJ, NY, PA, CT; nationwide; 10–500 employees; owner-run only; perRun 10.
2. Read the collections "businesses", "signals" and "cois". Skip records with sample: true. Never add a duplicate: same normalized name and same state counts as a duplicate. If a business already exists and is hiring, add only the new signal.
3. Search public sources from the last 30 days, without logging in anywhere:
   - Company career pages and public Greenhouse, Lever or Ashby job boards.
   - Publicly visible job listings on Indeed or LinkedIn.
   - News about hiring plans or job-creation commitments, including state workforce grants.
   - Press releases announcing a new CFO, COO, President or VP.
   Record the number of open roles and the date you saw them. Never invent people, numbers or dates.
4. Add up to perRun businesses.
   - Each business is a document in collection "businesses", id "rw-" + short slug, with these fields:
     - name.
     - industry: use one of the app's industry names, which are Healthcare - dental, Healthcare - medical, Healthcare - therapy and rehab, Healthcare - behavioral health, Healthcare - home health and senior care, Healthcare - pharmacy, Veterinary, Retail, Food service, Hospitality and lodging, Construction, Manufacturing, Wholesale and distribution, Transportation and logistics, Technology and software, Professional services, Finance and insurance, Real estate or holding, Personal services, Auto services, Education and childcare, Arts and recreation, Agriculture, Energy and utilities, Environmental and waste services, Nonprofit, Other.
     - city, county (if known), state (2-letter).
     - contact ("Name (Title)").
     - source: "Web research", foundBy: "hiring", lead: true.
     - targetFit: one sentence on how it fits the targeting.
     - notes: 2–4 factual sentences, including which roles they're hiring for.
     - contacts: [{name, role, phone, email, website, sourceName, sourceUrl, retrievedAt, provenance: "PROVIDER DATA", note}]. Include only details a source publishes.
     - profile: {website, principal, bio, checkedAt}.
     - employees: only if a source gives it.
     - revenue: a number, only if a source gives a figure or range (use the midpoint), with revenueEstimate: true, revenueSource, revenueSourceUrl and revenueAsOf.
     - createdAt and updatedAt (now, ISO).
   - For each business, add 1–2 signals in collection "signals", id "<businessId>--<type>--<YYYYMMDD>". Fields:
     - businessId.
     - type: use "rapid_hiring" for 10 or more open roles or a plan announcing 25 or more hires; "hiring" for 3–9 open roles; "exec_hire" for a new CFO, COO, President or VP.
     - provider: "web-research", providerName: "Hiring surges · <source name>".
     - sourceRef (URL), eventDate (YYYY-MM-DD), detectedAt (now).
     - evidence: one factual sentence with the count of roles.
     - confidence: 0.6–0.9.
     - provenance: "PROVIDER DATA".
     - mock: false, legacy: false, createdAt, updatedAt.
5. Check coverage gaps. For each added business, check whether "cois" has a Payroll and HR provider, Retirement plan advisor, or Fractional CFO serving its state (state or serviceArea includes it, or "nationwide"). List any missing combination as a gap string. Do not add specialists yourself.
6. Write a run report to collection "botlog", document id "hiring-YYYY-MM-DD" (today), with these fields:
   - bot: "hiring", ranAt (now ISO).
   - summary: one plain sentence under 120 characters.
   - added: {businesses: n, signals: n}.
   - links: [{title, url}] for up to 6 sources.
   - gaps: [strings].
   If nothing qualified, the summary is "Searched; no hiring surges fit your targeting".
7. Write everything in one or two batches. Then reply with a short summary: each business (name, city/state, how many roles or which executive, source link), plus the gaps.
```
