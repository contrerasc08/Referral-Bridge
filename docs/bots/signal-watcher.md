# Signal watcher

- **Schedule:** `CRON_TZ=America/New_York 37 6 * * 1,3,5` (Mon, Wed, Fri 6:37 AM)
- **Writes:** `signals` (provider `web-watch`), `botlog` (`watcher-YYYY-MM-DD`)

## Instructions (exact text of the scheduled task)

```text
Watch for new events at businesses in the user's Referral Bridge app, a referral CRM published as a claude.ai artifact at https://claude.ai/artifact/FgVJzZehAG5NhqRiwq2st9 . Its data lives in the artifact's database. Use the Artifact tool's database actions (read_db / write_db), or the ArtifactData tool if that is what this session offers. Do not republish or edit the page itself. In the app this job is shown as the "Signal watcher" bot.

1. Read the collections "businesses" and "signals". Skip records with sample: true.
2. Build a watch list of up to 15 businesses: every business with followed: true first, then the rest by most recent signal and most complete profile (real businesses with a named owner and a state).
3. For each, search the web for news from the last 30 days that is newer than the business's existing signals: expansions, new locations, relocations, permits, property purchases or leases, hiring pushes, executive hires or departures, acquisitions, funding or loans, equipment purchases, government contracts, awards, ownership changes or retirement plans, grand openings. Only count events a real, dated, linkable source reports about this exact business (match name and city/state). Never invent or guess.
4. For each new event, add a signal document (collection "signals", id "<businessId>--<type>--<YYYYMMDD of the event>"): businessId, type (one of: new_formation, new_location, expansion, relocation, permit, lease, property_purchase, hiring, rapid_hiring, exec_hire, leadership_change, acquisition, funding, financing, equipment, ucc_filing, gov_contract, ownership_change, succession, grand_opening, ecommerce, award), provider: "web-watch", providerName: "Signal watcher · <source name>", sourceRef (URL), eventDate (YYYY-MM-DD), detectedAt (now ISO), evidence (one factual sentence), confidence (0.6–0.95), provenance ("VERIFIED" only for government records, otherwise "PROVIDER DATA"), mock: false, legacy: false, createdAt, updatedAt. Skip an event if a signal with the same type and a similar date already exists for that business.
5. Write a run report to the collection "botlog", document id "watcher-YYYY-MM-DD" (today), with fields: bot: "watcher", ranAt (now ISO), summary (one plain sentence under 120 characters, e.g. "Checked 15 businesses; 3 new signals at Ramar and Bergen Dental"), added: {signals: <n>}, links: [{title, url}] for up to 6 sources. If nothing new, summary "Checked <n> businesses; nothing new".
6. Write everything in one batch. Then reply with a short summary of the new events found and their links.
```
