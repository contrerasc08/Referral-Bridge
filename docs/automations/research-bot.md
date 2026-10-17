# Research bot

- **Schedule:** `CRON_TZ=America/New_York 42 6 * * 2,4,6` (Tue, Thu, Sat, 6:42 AM)
- **Model:** claude-opus-5-5
- **Snapshot:** 2026-10-17

## Instructions

Find real contact information for businesses in the user's Referral Bridge app, a referral CRM published as a claude.ai artifact at https://claude.ai/artifact/FgVJzZehAG5NhqRiwq2st9 . Its data lives in the artifact's database. Use the Artifact tool's database actions (read_db / write_db), or the ArtifactData tool if that is what this session offers. Do not republish or edit the page itself. In the app this job is shown as the "Research bot".

1. Read the collections "businesses" and "contactRequests". Skip records with sample: true or researchStatus: "skip".
2. Build today's queue of up to 8 businesses, in this order: first any business with a contactRequests document whose status is "Waiting"; then businesses that have no entry in "contacts" with a phone or email; then businesses whose profile.checkedAt is missing or older than 180 days. Within each group, prefer businesses with a revenue between $1M and $100M (or unknown revenue) and the newest createdAt.
3. For each business, search the web for the owner or top executive and the best way to reach them: the company website, its contact page, state licensing boards, the state business registry, chamber of commerce and association directories, LinkedIn company pages (public info only), and local news. Record only details a source actually publishes. Never guess an email pattern, phone number or name. If you can't confirm anything, say so in the profile instead of inventing.
4. Update each business document (merge; don't remove existing fields):
   contacts: append new entries (don't duplicate an existing name + phone/email) as {name, role, phone, email, website, sourceName, sourceUrl, retrievedAt (now ISO), provenance: "PROVIDER DATA" (or "VERIFIED" for a government licensing or registry record), note}.
   profile: {website, principal (owner or top executive name and title), bio (2–3 factual sentences about the business: what it does, size, years in business, locations), checkedAt (now ISO), sources: [{name, url}]}.
   If the source gives a revenue figure or employee count not already stored, add revenue (number, range midpoint) with revenueEstimate: true, revenueSource, revenueSourceUrl, revenueAsOf.
   researchStatus: "done" if you found at least one way to reach a named person, otherwise "partial". updatedAt: now.
   For any contactRequests document you fulfilled, set status: "Done" and doneAt: now.
5. Write a run report to the collection "botlog", document id "research-YYYY-MM-DD" (today's date), with fields: bot: "research", ranAt (now ISO), summary (one plain sentence under 120 characters, e.g. "Found owners and phones for 6 of 8 businesses"), added: {contacts: <number of new contacts>}, links: [{title, url}] for up to 6 of the sources used.
6. Write everything in one or two batches. Then reply with a short summary: each business researched, who you found, how to reach them, and the source links, plus any you couldn't confirm.
