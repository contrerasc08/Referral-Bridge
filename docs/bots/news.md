# News bot

- **Schedule:** `CRON_TZ=America/New_York 47 6 */2 * *` (6:47 AM on odd dates)
- **Writes:** `news`, `botlog` (`news-YYYY-MM-DD`)

## Instructions (exact text of the scheduled task)

```text
Update the economic and industry news in the user's Referral Bridge app, a referral CRM published as a claude.ai artifact at https://claude.ai/artifact/FgVJzZehAG5NhqRiwq2st9 . The app stores news in its artifact database, collection "news". Write to it with the Artifact tool's database actions (read_db / write_db), or the ArtifactData tool if that is what this session offers. Do not republish or edit the page itself. In the app this job is shown as the "News bot".

Steps:
1. Read the "news" collection (list it) and the "businesses" collection, so you know which items exist and which industries and states the user's real businesses are in. Skip records with sample: true.
2. Search the web for news from the last 3–4 days that matters to business owners and their advisors (bankers, CPAs, attorneys, insurance, wealth): Federal Reserve and interest rates, jobs report, inflation (CPI/PPI), ISM factory and services surveys, SBA lending rules, tariffs and costs, plus industry news for the industries the businesses are in (for example manufacturing, dental and medical practices, physical therapy, construction, logistics). Cover the whole US, with extra attention to states where the user has businesses. Only use real, dated, linkable sources. Never invent a headline, number or date.
3. Add 2 to 6 new items. Skip anything already stored (same story or same URL). Each item is a document with an id like "news-YYYY-MM-DD-short-slug" and these fields:
   title (plain-English headline), publishedAt (YYYY-MM-DD), sourceName, url, summary (2–3 factual sentences with the key numbers), impact (1–2 sentences: why it matters to owners and which advisors it creates demand for), industries (array of industry names it applies to, or ["all"]), states (array of 2-letter codes, or [] for nationwide), needs (object of need id to a small number 0.02–0.10: how much it raises that need; negative to lower), outlook (object of industry name to an integer from -2 to +2: how the news changes that industry's economic climate; omit if none), expiresAt (YYYY-MM-DD, usually 6–10 weeks out; 3–6 months for rule changes), addedAt (now, ISO timestamp), scope ("economy" or "industry"), provenance: "PROVIDER DATA".
   Valid industry names: Healthcare - dental, Healthcare - medical, Healthcare - therapy and rehab, Healthcare - behavioral health, Healthcare - home health and senior care, Healthcare - pharmacy, Veterinary, Retail, Food service, Hospitality and lodging, Construction, Manufacturing, Wholesale and distribution, Transportation and logistics, Technology and software, Professional services, Finance and insurance, Real estate or holding, Personal services, Auto services, Education and childcare, Arts and recreation, Agriculture, Energy and utilities, Environmental and waste services, Nonprofit, Other. You may also use "Healthcare (all)" in outlook.
   Valid need ids: banking, sba, equipment, cre, merchant, payroll, accounting, tax, insurance, legal, wealth, retirement, hr, marketing, tech, cyber, succession, ma, cfo, strategy.
4. Keep the industry climate honest. Only give outlook points when the source clearly shows an industry growing or shrinking, and don't double-count a story that is already stored. If a newer report replaces an older one (for example a new jobs report), set the older item's expiresAt to today so only the latest counts.
5. Write a run report to the collection "botlog", document id "news-YYYY-MM-DD" (today's date), with fields: bot: "news", ranAt (now, ISO timestamp), summary (one plain sentence under 120 characters, e.g. "Added 3 headlines; manufacturing climate up, retail down"), added: {news: <number added>}, links: [{title, url}] for up to 6 headlines added. Write a report even when nothing new was added (summary "No new relevant news").
6. Write everything in one batch. Then reply with a short summary: the headlines added (each with its source link), any industries whose climate changed, and anything expired.
```
