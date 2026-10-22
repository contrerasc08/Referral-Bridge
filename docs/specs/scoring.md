# Scoring: needs, Opportunity, Match and bridges

The core idea: **a business becomes a lead when one of its needs is bridged to a specialist who can deliver the solution.** Four calculations make that happen, all in `src/index.html` and recomputed on every render (memoized per render).

## 1. Signal strength (`sigEff`)

Each signal type in `SIGNAL_TYPES` has a weight `w`, a half-life `hl` in days, a category, and the needs it implies. A signal's points are:

```
points = w × decay × provenance factor × confidence × learned multiplier
decay  = 0.5 ^ (age / half-life)        (ignored entirely after 4 half-lives)
```

| Provenance | Factor |
|---|---|
| VERIFIED | 1.0 |
| PROVIDER DATA | 0.85 |
| USER-ENTERED | 0.8 |
| AI INFERENCE | 0.5 |

**Learned multiplier.** Once at least 5 bridges with a given signal type have reached a decision (Introduced, Meeting, Closed or Rejected), that type's weight is scaled between ×0.5 and ×1.5, depending on how its close rate compares with the overall close rate.

## 2. Opportunity Score (`opportunity`): how worth contacting is this business right now? (0–100)

The score is the sum of:

- The points of every active signal.
- **Corroboration:** +5 for each independent source beyond the first, up to +15.
- **Change intensity:** +5 for 3 or more signals in the last 30 days.
- **Market conditions:** +2 for each active news item that raises one of its needs, up to +6.
- **Industry climate:** in growth mode, climate score × 3; in "both" mode, |climate| × 2.
- **Lifecycle:** Starting out +12, Growing +8, Planning exit +8.
- **Targeting fit:** −15 to +15. Focus state +6, target industry +6, employee count in range +3 (−4 if outside). An excluded state, industry or word sets the business to "out of target".

The result is clamped to 0–100. The business page shows each line under "Tap for why".

## 3. Predicted needs (`needsFor`)

Each active signal adds probability to the needs listed in its type. The probabilities combine as `1 − Π(1 − p)`. The 20 need ids are in `NEED_DEFS`, each mapped to the professions that can meet it. Active news can then move a need by up to ±15 points (`NEWS_CAP`). The app keeps needs at 20% or higher, up to the top 8.

## 4. Match Score (`score(b, c)`): how right is this specialist for this business? (0–100)

| Dimension | Weight | How |
|---|---|---|
| Need fit | 35% | Confidence of the top predicted need this profession serves. A profession that's only a typical need for the industry gets 40. Otherwise the match score is 0. |
| Location | 20% | Same county 100, serves the county 85, serves the state 70, same home state 55, other 20 |
| Expertise | 15% | Healthcare specialist for a healthcare business 100, specialty words matching the industry 55 + 15 per hit, otherwise 40 |
| Stage fit | 10% | Specialist's `bestStage` equals the business lifecycle 100, any stage 60, mismatch 30 |
| Track record | 15% | 50 + 20 per closed referral − 15 per rejected one |
| Relationship | 5% | Already closed together 100, in the pipeline 70, new 50 |

## 5. Bridges (`bridgesFor`)

For each predicted need, the app finds the best non-sample specialist whose profession serves that need and whose Match Score is at least **50** (`THRESHOLD`). Every need that finds one is a **bridge**. A business with one or more bridges shows as **Lead** / "Bridge ready".

## Industry climate

Each active news item can carry `outlook` points per industry (−2 to +2). An industry's climate is the sum of those points, capped at −4 to +4. Today shows the industries the economy favors, and business cards show ▲ or ▼.

## Revenue range and Targeting

- **Revenue range** (`settings/providers`): businesses outside it are hidden across the app. Unknown revenue is included by default.
- **Targeting** (`settings/targeting`): this does more than filter. It adds the targeting-fit points above, it can hide out-of-target businesses ("Hide businesses outside my targeting"), and the lead generator bots search inside it.
