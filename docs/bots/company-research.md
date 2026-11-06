# Company research bot

Fills the RelPro-style company profiles you start on the **Company research** screen. It checks many sources, merges what they say into one profile, and links every fact to the source it came from.

- **Schedule:** `CRON_TZ=America/New_York 17 6 * * *` (every day, 6:17 AM). Also runs on demand: "Run my company research."
- **Writes:** `companyProfiles`, `botlog` (`company-research-YYYY-MM-DD`)
- **Status:** instructions written; the scheduled task is created after this change is merged.

## Instructions (exact text of the scheduled task)

```text
Build sourced company profiles in the user's Referral Bridge app, a referral CRM published as a claude.ai artifact at https://claude.ai/artifact/FgVJzZehAG5NhqRiwq2st9 . Its data lives in the artifact's database. Use the Artifact tool's database actions (read_db / write_db), or the ArtifactData tool if that is what this session offers. Do not republish or edit the page itself. In the app this job is shown as the "Company research bot".

1. Read the collection "companyProfiles". Today's queue is every document with status "queued", oldest requestedAt first, up to 6. If there are none, write the run report (step 6) with summary "No profiles waiting" and stop.
2. Set each queued profile's status to "researching" before you start it.
3. For each profile, use its name, domain, city and state to check these sources. Search the web for each one and open the actual record or page:
   - Official: the state business registry for its state (legal name, entity type, entity ID, formation date, status, officers, registered agent); OpenCorporates; SEC EDGAR (Form D raises); SBA loan data and ProPublica's PPP search; USAspending and SAM.gov (federal contracts, NAICS); the NPI Registry and state licensing boards for healthcare practices; county or city permit records; UCC lien search where the state offers it free.
   - Company: its own website (About, Team, Locations, Contact pages) and press releases.
   - Directories: Google Maps listing, BBB, Dun & Bradstreet and ZoomInfo public pages (revenue and employee estimates), Indeed (open roles).
   - Social: the LinkedIn company page and public LinkedIn profiles of owners and executives (public info only).
   - News: Google News and local business journals from the last 2 years.
   Record only what a source actually publishes. Never guess a value, an email pattern or a phone number. A source you checked that had nothing still goes in "sources" with found: false.
4. Update the profile document (merge; keep any facts and sources already there, including ones with ids starting "u", which the user added):
   sources: [{id ("s1", "s2", … continuing after existing ids), name, url (the exact page, not a search page when a record page exists), type ("official" | "company" | "directory" | "social" | "news" | "data"), retrievedAt (now ISO), found (true/false), note (optional, e.g. "No Form D filings")}].
   fields: an object keyed by legalName, dba, description, industry, naics, ownership, entityType, status, revenue, employees, founded, locations, address, phone, website, email, linkedin, stateId, formed (YYYY-MM-DD), registeredAgent, npi, licenses. Each value is {v, src: [source ids that say this value]}. When sources disagree, put the best-supported value (official records win, then the most sources, then the newest) in v, and each other value in alt: [{v, src}]. Label estimates as estimates ("About $18M (estimate)").
   people: [{name, title, linkedin, phone, email, src}] for owners, officers and executives.
   filings: [{date (YYYY-MM-DD), kind ("State filing" | "UCC lien" | "SBA loan" | "PPP loan" | "SEC Form D" | "Government contract" | "Permit" | "Lawsuit" | "Other"), detail, src}].
   news: [{date, title, url, sourceName, summary}] for up to 6 relevant articles, newest first.
   signals: [{type, date, evidence, src}] using only these types: new_formation, license_new, npi_new, grand_opening, relocation, new_location, expansion, permit, lease, property_purchase, hiring, rapid_hiring, exec_hire, leadership_change, ownership_change, succession, acquisition, merger, funding, financing, equipment, ucc_filing, gov_contract, award, layoffs, restructuring, closure.
   industryGroup: the best match from the app's 27 industries (Healthcare - dental, Healthcare - medical, Healthcare - therapy and rehab, Healthcare - behavioral health, Healthcare - home health and senior care, Healthcare - pharmacy, Veterinary, Retail, Food service, Hospitality and lodging, Construction, Manufacturing, Wholesale and distribution, Transportation and logistics, Technology and software, Professional services, Finance and insurance, Real estate or holding, Personal services, Auto services, Education and childcare, Arts and recreation, Agriculture, Energy and utilities, Environmental and waste services, Nonprofit, Other).
   summary: 2–3 factual sentences: what the company does, how big it is, and what is changing.
   needs: 2–5 short phrases for likely banking and advisory needs, based only on the facts found (e.g. "Equipment financing").
   talkingPoints: 3–5 short sentences to open a conversation, each tied to a fact above. Include one that names any field where sources disagree, so the user can confirm it.
   status: "done" if at least 8 fields were found, "partial" if fewer, "failed" if you could not identify the company. researchedAt and updatedAt: now ISO.
   If the profile has a bizId, do not change that business; the user saves it from the app.
5. If the name matches several companies, pick the one that fits the city, state and domain, and say in the summary which one you chose and why. If none fits, set status "failed" and explain in summary.
6. Write a run report to the collection "botlog", document id "company-research-YYYY-MM-DD", with fields: bot: "company-research", ranAt (now ISO), summary (one plain sentence under 120 characters, e.g. "Built 4 profiles from 37 sources; 1 company not found"), added: {profiles: <number researched>}, links: [{title, url}] for up to 6 of the best sources used.
7. Reply with a short summary: each company, how many fields and sources, any conflicts between sources, and anything you couldn't find.
```
