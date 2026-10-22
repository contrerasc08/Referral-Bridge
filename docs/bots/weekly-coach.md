# Weekly coach

- **Schedule:** `CRON_TZ=America/New_York 7 16 * * 5` (Fridays 4:07 PM)
- **Writes:** `botlog` only (`coach-YYYY-MM-DD`, with `plan` and `stats`). The plan shows on the Today screen for 8 days.

## Instructions (exact text of the scheduled task)

```text
Write the weekly production review and next week's plan for the user's Referral Bridge app, a referral CRM published as a claude.ai artifact at https://claude.ai/artifact/FgVJzZehAG5NhqRiwq2st9 . Its data lives in the artifact's database. Use the Artifact tool's database actions (read_db / write_db), or the ArtifactData tool if that is what this session offers. Do not republish or edit the page itself. In the app this job is shown as the "Weekly coach" bot, and its plan appears on the app's Today screen.

How the app thinks: a business becomes a lead when one of its needs is bridged to a specialist who can deliver the solution. Production means: owners contacted, discovery calls booked, bridges approved, introductions made, meetings held, and closed referrals.

1. Read the collections "businesses", "cois", "matches", "outreach", "signals", "drafts" and "botlog". Skip anything with sample: true.
2. Measure the last 7 days: outreach logged (by channel and outcome), discovery calls booked, businesses moved to a new prospect stage, matches created and status changes (Approved, Introduced, Meeting, Closed, Rejected, from each match's history), drafts sent vs still waiting, new businesses and specialists added by the bots. Compare with the week before when there's data.
3. Spot what matters most: follow-ups overdue, bridges stuck in the same stage 7+ days, high-scoring businesses never contacted, approved bridges with no intro yet, needs with no specialist in a state (and how many businesses that blocks), any specialist the Specialist checker flagged.
4. Write a run report to the collection "botlog", document id "coach-YYYY-MM-DD" (today), with fields: bot: "coach", ranAt (now ISO), summary (one plain sentence under 120 characters with the week's key numbers and the single most important focus, e.g. "6 calls, 2 discovery calls, 1 intro made. Focus: push Bergen Dental intro"), plan (array of 3–6 short, concrete actions for next week, each naming the business or specialist and the action, most valuable first, e.g. "Call Dr. Lee at PT Center: follow-up is 4 days overdue"), stats: {outreach, booked, bridgesApproved, introsMade, meetings, closed}. Use only what the data shows; don't invent activity. If there was no activity, say so kindly and make the plan about getting started.
5. Then reply with the summary and the plan.
```
