# New business filings (lead generator)

- **Schedule:** `CRON_TZ=America/New_York 23 6 * * 1,4` (Mon and Thu 6:23 AM)
- **Task created:** 2026-10-22. No runs yet.
- **Writes:** `businesses` (foundBy `filings`), `signals`, `botlog` (`filings-YYYY-MM-DD`, with `gaps`)
- **Follows Targeting.** It searches only focus states (plus `states`), never nationwide. It can be paused in Targeting.

## Instructions (exact text of the scheduled task)

```text
Find newly formed or newly licensed real businesses, and add them to the user's Referral Bridge app, a referral CRM published as a claude.ai artifact at https://claude.ai/artifact/FgVJzZehAG5NhqRiwq2st9 . Its data lives in the artifact's database. Use the ArtifactData tool (or the Artifact tool's read_db / write_db actions if that is what this session offers). Do not republish or edit the page itself. In the app this job is shown as the "New business filings" lead generator.

How the app thinks: every company is a "business". A business becomes a "lead" when one of its needs is bridged to a specialist. New businesses need business banking, SBA or startup financing, a CPA or bookkeeper, an attorney, insurance and payroll.

1. Read the targeting. Get settings/targeting and settings/providers.
   - If targeting.gens.filings is false, only write the run report in step 6 with summary "Paused in Targeting; nothing searched", then stop.
   - This bot searches ONLY within focusStates, plus targeting.states if that list is not empty. It never searches nationwide.
   - The other targeting fields are:
     - industries: prefer these.
     - excludeIndustries: never add these.
     - ownerRun: if true, skip franchise units and subsidiaries of large corporations.
     - keywords: prefer businesses that mention these.
     - excludeWords: never add a business whose name or description contains any of these comma-separated words.
     - perRun: the maximum number of new businesses to add this run.
   - Ignore yearsMin and the employee range for this bot.
   - The revenue range is in settings/providers. New businesses usually have unknown revenue. Add them only if settings/providers.revUnknown is not false.
   - If settings/targeting is missing, use these defaults: focusStates NJ, NY, PA, CT; perRun 10.
2. Read the collections "businesses" and "signals". Skip records with sample: true. Never add a duplicate: same normalized name and same state counts as a duplicate.
3. Look for filings from the last 45 days in those states, using official sources first:
   - State open-data business registrations, for example data.ny.gov new filings, the CT Business Registry on data.ct.gov, data.pa.gov registered businesses, and other states' Secretary of State data.
   - New healthcare provider organizations in the NPI Registry (npiregistry.cms.hhs.gov).
   - New professional, contractor or liquor licenses.
   - Local news and chamber ribbon cuttings that name a new business.
   Keep only filings that look like real operating businesses: a named principal or owner, an industry you can identify, and ideally a website, location or license. Skip shells, holding LLCs with no operations, single-property real-estate LLCs, and anything you can't tie to a real business.
   Never invent people, phone numbers or dates.
4. Add up to perRun businesses.
   - Each business is a document in collection "businesses", id "rw-" + short slug, with these fields:
     - name.
     - industry: use one of the app's industry names, which are Healthcare - dental, Healthcare - medical, Healthcare - therapy and rehab, Healthcare - behavioral health, Healthcare - home health and senior care, Healthcare - pharmacy, Veterinary, Retail, Food service, Hospitality and lodging, Construction, Manufacturing, Wholesale and distribution, Transportation and logistics, Technology and software, Professional services, Finance and insurance, Real estate or holding, Personal services, Auto services, Education and childcare, Arts and recreation, Agriculture, Energy and utilities, Environmental and waste services, Nonprofit, Other.
     - city, county (if known), state (2-letter).
     - entityType: LLC, PLLC, PC, Corporation or Other.
     - formedDate (YYYY-MM-DD).
     - contact ("Name (Title)") if a source names one.
     - source: "State filing" or "NPI registry", foundBy: "filings", lead: true.
     - targetFit: one sentence on how it fits the targeting.
     - notes: 2–3 factual sentences.
     - contacts: [{name, role, phone, email, website, sourceName, sourceUrl, retrievedAt, provenance, note}]. Use provenance "VERIFIED" for registry data.
     - profile: {website, principal, bio, checkedAt}.
     - createdAt and updatedAt (now, ISO).
   - For each business, add 1–2 signals in collection "signals", id "<businessId>--<type>". Fields:
     - businessId.
     - type: new_formation, license_new, npi_new, dba or grand_opening.
     - provider: "web-research", providerName: "New business filings · <source name>".
     - sourceRef (URL), eventDate (the filing date, YYYY-MM-DD), detectedAt (now).
     - evidence: one factual sentence.
     - confidence: 0.7–0.95.
     - provenance: "VERIFIED" for official registry records, otherwise "PROVIDER DATA".
     - mock: false, legacy: false, createdAt, updatedAt.
5. Check coverage gaps. For each added business, check whether "cois" has a Banker or SBA lender and a CPA serving its state (state or serviceArea includes it, or "nationwide"). List any missing combination as a gap string. Do not add specialists yourself.
6. Write a run report to collection "botlog", document id "filings-YYYY-MM-DD" (today), with these fields:
   - bot: "filings", ranAt (now ISO).
   - summary: one plain sentence under 120 characters, for example "Added 9 new businesses in NJ and PA from state filings".
   - added: {businesses: n, signals: n}.
   - links: [{title, url}] for up to 6 sources.
   - gaps: [strings].
   If nothing qualified, the summary is "Searched; no new filings fit your targeting".
7. Write everything in one or two batches. Then reply with a short summary: each business (name, city/state, industry, filing date, source link), plus the gaps.
```
