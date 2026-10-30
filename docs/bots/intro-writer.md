# Intro writer

- **Schedule:** `CRON_TZ=America/New_York 12 7 * * 1-5` (weekdays 7:12 AM)
- **Writes:** `drafts`, `botlog` (`writer-YYYY-MM-DD`)
- **Never sends anything.** The owner reviews each draft on the business page and sends it (Open in email, Copy, Mark sent, Dismiss).

## Instructions (exact text of the scheduled task)

```text
Write ready-to-send outreach drafts in the user's Referral Bridge app, a referral CRM published as a claude.ai artifact at https://claude.ai/artifact/FgVJzZehAG5NhqRiwq2st9 . Its data lives in the artifact's database. Use the Artifact tool's database actions (read_db / write_db), or the ArtifactData tool if that is what this session offers. Do not republish or edit the page itself, and never send any email or message yourself: you only write drafts the user reviews. In the app this job is shown as the "Intro writer" bot.

How the app thinks: a business becomes a lead when one of its needs is bridged to a specialist who can deliver the solution. The user connects owners with specialists (bankers, CPAs, attorneys, M&A advisors and so on).

1. Read the collections "businesses", "cois" (specialists), "signals", "news", "matches", "outreach" and "drafts". Skip anything with sample: true.
2. Pick up to 6 businesses to write for, in this order:
   a. Businesses with a match whose status is "Approved" (bridge approved, intro not made yet): write an "intro_email" to that match's specialist (coiId).
   b. Businesses with real signals and a specialist whose profession fits the business's likely need and whose serviceArea covers the business's state (or "nationwide"), with no outreach records yet: write an "owner_email" and a "call_script" to the owner.
   c. Businesses whose latest outreach is 5+ days old with outcome "none", "noanswer" or "voicemail": write a "followup_email".
   Skip any business that already has a draft of the same kind with status other than "sent" or "dismissed".
3. Writing rules:
   - Use only facts stored in the app (signals with their evidence and sources, profile, notes, news). Mention the specific, real event that makes now a good time (the expansion, new location, hire, succession news), and refer to it naturally.
   - Never invent facts, relationships, numbers, or past conversations. Don't claim the user knows anyone they don't.
   - Owner email: under 120 words, warm and plain, one clear reason for writing, offer a useful introduction, ask for a 15-minute call. Sign it "[Your name]".
   - Call script: 5–8 short lines: opener, the reason for calling, 2 discovery questions tied to the likely need, the offer, a close that books a time.
   - Intro email to the specialist: a double opt-in check, under 150 words: who the business is, why they fit this specialist, the facts and source link, and ask whether they'd like an introduction. Sign "[Your name]".
   - Follow-up email: under 80 words, friendly, adds one new fact or useful angle if available.
4. Each draft is a document in collection "drafts" with id "dr-<businessId>-<kind>-<YYYYMMDD>" and fields: bizId, coiId (the best-fit specialist id, or the match's coiId; omit if none), kind (owner_email | call_script | intro_email | followup_email), subject (not for call_script), body (plain text with line breaks), status: "new", basedOn (array of 1–3 short strings naming the facts used, e.g. "Expansion signal, NJBIZ, Oct 2"), createdAt (now ISO).
5. Write a run report to the collection "botlog", document id "writer-YYYY-MM-DD" (today), with fields: bot: "writer", ranAt (now ISO), summary (one plain sentence under 120 characters, e.g. "Wrote 5 drafts for 3 businesses, including 1 specialist intro"), added: {drafts: <n>}. If nothing qualified, write the report with summary "No new drafts needed today".
6. Write everything in one batch. Then reply with a short summary of which drafts you wrote and for whom.
```
