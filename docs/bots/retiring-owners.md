# Retiring owners (lead generator)

- **Schedule:** `CRON_TZ=America/New_York 33 6 * * 2` (Tuesdays 6:33 AM)
- **Writes:** `businesses` (foundBy `succession`), `signals`, `botlog` (`succession-YYYY-MM-DD`, with `gaps`)
- **Follows Targeting** (`settings/targeting`) and the revenue range (`settings/providers`). It can be paused in Targeting.

## Instructions (exact text of the scheduled task)

```text
Find new real businesses whose owners are nearing retirement or an exit, and add them to the user's Referral Bridge app, a referral CRM published as a claude.ai artifact at https://claude.ai/artifact/FgVJzZehAG5NhqRiwq2st9 . Its data lives in the artifact's database. Use the ArtifactData tool (or the Artifact tool's read_db / write_db actions if that is what this session offers). Do not republish or edit the page itself. In the app this job is shown as the "Retiring owners" lead generator.

How the app thinks: every company is a "business". A business becomes a "lead" when one of its needs is bridged to a specialist (banker, CPA, attorney, M&A advisor and so on). Succession needs usually go to M&A advisors and business brokers, wealth advisors, estate and business attorneys, and CPAs.

1. Read the targeting. Get settings/targeting and settings/providers.
   - If targeting.gens.succession is false, only write the run report in step 6 with summary "Paused in Targeting; nothing searched", then stop.
   - The targeting fields are:
     - focusStates: search these first; at least half of what you add should come from them when real results exist.
     - states: if not empty, only add businesses in these states or in focusStates. If empty, search nationwide.
     - counties: favor these areas.
     - industries: prefer these.
     - excludeIndustries: never add these.
     - empMin / empMax: skip a business when a source puts its employee count outside this range. Unknown is fine.
     - yearsMin: minimum years in business. For this bot, prefer businesses with 20+ years in any case.
     - ownerRun: if true, skip public companies, franchise units, private-equity-owned firms and subsidiaries of large corporations.
     - keywords: prefer businesses that mention these.
     - excludeWords: never add a business whose name or description contains any of these comma-separated words.
     - perRun: the maximum number of new businesses to add this run.
   - The revenue range is in settings/providers: revMin, revMax, and revUnknown (whether unknown revenue is allowed).
   - If settings/targeting is missing, use these defaults: focusStates NJ, NY, PA, CT; nationwide; 10–500 employees; owner-run only; perRun 10.
2. Read the collections "businesses", "signals" and "cois". Skip records with sample: true. Never add a duplicate: same normalized name and same state counts as a duplicate.
3. Search the web for real, dated, linkable evidence of an upcoming ownership transition at an identifiable business. Look for:
   - Local business journal and newspaper stories about an owner retiring, stepping back, planning succession, handing off to the next generation, or looking for a buyer.
   - ESOP or employee-ownership announcements.
   - Long-tenured founders still running the company, for example a 40th anniversary story with the founder as CEO.
   - Named (not anonymous) business-for-sale listings on BizBuySell, BizQuest or DealStream.
   - State and industry association news.
   Only state an owner's age if a source states it. Never guess age from photos. Never use obituaries or health information. Anonymous for-sale listings without a business name are not usable. A succession signal you infer only from tenure (for example, founded in 1984 and the founder is still CEO) gets provenance "AI INFERENCE" and confidence of 0.65 or less. Never invent people, phone numbers, revenue or dates.
4. Add up to perRun businesses.
   - Each business is a document in collection "businesses", id "rw-" + short slug, with these fields:
     - name.
     - industry: use one of the app's industry names, which are Healthcare - dental, Healthcare - medical, Healthcare - therapy and rehab, Healthcare - behavioral health, Healthcare - home health and senior care, Healthcare - pharmacy, Veterinary, Retail, Food service, Hospitality and lodging, Construction, Manufacturing, Wholesale and distribution, Transportation and logistics, Technology and software, Professional services, Finance and insurance, Real estate or holding, Personal services, Auto services, Education and childcare, Arts and recreation, Agriculture, Energy and utilities, Environmental and waste services, Nonprofit, Other.
     - city, county (if known), state (2-letter).
     - contact ("Name (Title)").
     - source: "Web research", foundBy: "succession", lead: true.
     - targetFit: one sentence on how it fits the targeting.
     - notes: 2–4 factual sentences.
     - contacts: [{name, role, phone, email, website, sourceName, sourceUrl, retrievedAt, provenance: "PROVIDER DATA", note}]. Include only details a source publishes.
     - profile: {website, principal, bio, checkedAt}.
     - employees: only if a source gives it.
     - revenue: a number, only if a source gives a figure or range (use the midpoint), with revenueEstimate: true, revenueSource, revenueSourceUrl and revenueAsOf.
     - createdAt and updatedAt (now, ISO).
   - For each business, add 1–2 signals in collection "signals", id "<businessId>--<type>". Fields:
     - businessId.
     - type: succession, founder_change or ownership_change.
     - provider: "web-research", providerName: "Retiring owners · <source name>".
     - sourceRef (URL), eventDate (YYYY-MM-DD), detectedAt (now).
     - evidence: one factual sentence.
     - confidence: 0.6–0.95.
     - provenance: "VERIFIED" only for government records, otherwise "PROVIDER DATA" or "AI INFERENCE" as above.
     - mock: false, legacy: false, createdAt, updatedAt.
5. Check coverage gaps. For each added business, check whether any record in "cois" has a profession of M&A advisor or business broker, Investment advisor, or Attorney, and serves its state (state or serviceArea includes it, or "nationwide"). List any missing combination as a gap string, for example "No M&A advisor serving OH (Acme Tool)". Do not add specialists yourself; the Prospector does that.
6. Write a run report to collection "botlog", document id "succession-YYYY-MM-DD" (today), with these fields:
   - bot: "succession", ranAt (now ISO).
   - summary: one plain sentence under 120 characters, for example "Added 7 businesses with retiring owners, 4 in focus states".
   - added: {businesses: n, signals: n}.
   - links: [{title, url}] for up to 6 sources.
   - gaps: [strings].
   If nothing qualified, the summary is "Searched; no new retiring-owner businesses fit your targeting".
7. Write everything in one or two batches. Then reply with a short summary: each business added (name, city/state, industry, why now, source link), plus the gaps.
```
