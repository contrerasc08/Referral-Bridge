# Prospector

- **Schedule:** `CRON_TZ=America/New_York 52 6 * * 1` (Mondays 6:52 AM)
- **Writes:** `businesses` (foundBy `prospector`), `signals`, `cois`, `botlog` (`prospector-YYYY-MM-DD`, with `gapsFilled`)
- **Follows Targeting.** Its first priority for new specialists is the `gaps` reported by the four lead generators.

## Instructions (exact text of the scheduled task)

```text
Add new real businesses and specialists to the user's Referral Bridge app, a referral CRM published as a claude.ai artifact at https://claude.ai/artifact/FgVJzZehAG5NhqRiwq2st9 . Its data lives in the artifact's database. Use the Artifact tool's database actions (read_db / write_db), or the ArtifactData tool if that is what this session offers. Do not republish or edit the page itself. In the app this job is shown as the "Prospector" bot.

How the app thinks: every company is a "business". A business only becomes a "lead" when one of its needs is bridged to a specialist (advisor) who can deliver the solution. So each week, add both sides: businesses with fresh needs, and specialists who can meet them.

0. Targeting. First read settings/targeting and settings/providers, and follow them for everything below.
   - The targeting fields are:
     - focusStates: search these first; at least half of what you add should come from them when real results exist.
     - states: if not empty, only add businesses and specialists serving these states or focusStates. If empty, search nationwide.
     - counties: favor these areas.
     - industries: prefer these.
     - excludeIndustries: never add these.
     - empMin / empMax: skip a business when a source puts its employee count outside this range.
     - yearsMin: minimum years in business.
     - ownerRun: if true, skip public companies, franchise units, private-equity-owned firms and subsidiaries.
     - keywords: prefer businesses that mention these.
     - excludeWords: never add a business whose name or description contains any of these comma-separated words.
   - The revenue range is settings/providers revMin and revMax, plus revUnknown (whether unknown revenue is allowed).
   - If settings/targeting is missing, use these defaults: focusStates NJ, NY, PA, CT; nationwide; 10–500 employees; owner-run only.
   - Add foundBy: "prospector" and a one-sentence targetFit to every business you add.
1. Read the collections "businesses", "cois" (specialists), "signals", "news" and "botlog". This lets you avoid duplicates (same name and state counts as a duplicate), see which industries are favored right now (news items with positive "outlook" values), and see which needs have no specialist yet. Also read the "gaps" arrays in the most recent botlog reports from the lead generators (bot: succession, permits, filings, hiring). Filling those gaps is your first priority for specialists.
2. Find 8–12 NEW real US businesses that fit the targeting, favoring industries with positive outlook.
   - Good sources: Inc. 5000 and regional fast-growth lists, state economic-development and county IDA announcements, business journals, and permit and expansion news.
   - Prefer owner-run or founder-led companies where the decision-maker is reachable.
   - Every business needs a real, linkable, dated source and a named owner or executive. Never invent people, phone numbers, revenue or dates.
   - Each business is a document in collection "businesses", id "rw-" + short slug, with these fields:
     - name.
     - industry: one of Healthcare - dental, Healthcare - medical, Healthcare - therapy and rehab, Healthcare - behavioral health, Healthcare - home health and senior care, Healthcare - pharmacy, Veterinary, Retail, Food service, Hospitality and lodging, Construction, Manufacturing, Wholesale and distribution, Transportation and logistics, Technology and software, Professional services, Finance and insurance, Real estate or holding, Personal services, Auto services, Education and childcare, Arts and recreation, Agriculture, Energy and utilities, Environmental and waste services, Nonprofit, Other.
     - city, county (if known), state (2-letter).
     - contact ("Name (Title)").
     - source: "Web research", foundBy: "prospector", targetFit, lead: true.
     - notes: 2–4 factual sentences.
     - contacts: [{name, role, phone, email, website, sourceName, sourceUrl, retrievedAt, provenance: "PROVIDER DATA", note}].
     - profile: {website, principal, bio, checkedAt}.
     - employees: if a source gives it.
     - revenue: a number, only if a source gives a figure or range (use the midpoint), with revenueEstimate: true, revenueSource, revenueSourceUrl and revenueAsOf.
     - createdAt and updatedAt (now, ISO).
   - For each business, add 1–3 signals in collection "signals", id "<businessId>--<type>". Fields:
     - businessId.
     - type: one of new_formation, new_location, expansion, relocation, permit, lease, property_purchase, hiring, rapid_hiring, exec_hire, leadership_change, acquisition, funding, financing, equipment, ucc_filing, gov_contract, ownership_change, succession, grand_opening, ecommerce, award.
     - provider: "web-research", providerName: "Claude web research · <source name>".
     - sourceRef (URL), eventDate (YYYY-MM-DD of the event), detectedAt (now).
     - evidence: one factual sentence.
     - confidence: 0.6–0.95.
     - provenance: "VERIFIED" only for government records, otherwise "PROVIDER DATA". Use "AI INFERENCE" for anything you infer.
     - mock: false, legacy: false, createdAt, updatedAt.
3. Find 6–10 NEW real specialists of every type.
   - Priorities, in order: first the lead generators' reported gaps, then other needs that current businesses have and no specialist covers, then focusStates.
   - Types to look for: bankers, SBA lenders, equipment lenders, CPAs, bookkeepers, fractional CFOs, attorneys, commercial real estate brokers, insurance agents, wealth and 401(k) advisors, payroll/HR providers and PEOs, IT and cybersecurity firms, marketing agencies, M&A advisors and business brokers, and consultants.
   - Prefer people who serve businesses in the targeted revenue range. Each specialist needs a named person, firm and a public source.
   - Each specialist is a document in collection "cois", id "rw-adv-" + slug, with these fields:
     - name, firm.
     - profession: one of Banker, SBA lender, Equipment lender, CPA, Bookkeeper, Fractional CFO, Attorney, Real estate, Insurance, Investment advisor, Retirement plan advisor, Merchant services, Payroll and HR, IT and cybersecurity, Marketing agency, M&A advisor or business broker, Business consultant, Other.
     - healthcare: true only if they focus on healthcare.
     - specialties: a comma list that includes industry words.
     - bestStage: Any stage, Starting out, Growing, Established or Planning exit.
     - county, state.
     - serviceArea: a comma list of counties and/or state codes, or "nationwide".
     - phone and email: only if published.
     - notes: their title, office address if published, why they fit, then "Source: <name> (<url>). Not yet vetted by you: meet before referring."
     - lead: true, source: "Web research".
     - profile: {website, otherListings, checkedAt, verified: false}.
     - createdAt, updatedAt.
4. Write a run report to the collection "botlog", document id "prospector-YYYY-MM-DD" (today's date), with these fields:
   - bot: "prospector", ranAt (now, ISO timestamp).
   - summary: one plain sentence under 120 characters.
   - added: {businesses: <n>, specialists: <n>}.
   - links: [{title, url}] for up to 6 of the best sources.
   - gapsFilled: [strings].
5. Write everything in one or two batches. Then reply with a short summary:
   - the businesses added (name, city/state, industry, revenue if known, why now),
   - the specialists added (name, firm, type, area) and which gaps they fill,
   - which businesses are now bridge-ready,
   - the source links.
```
