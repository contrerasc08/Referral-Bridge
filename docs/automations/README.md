# Automations (the "bots")

Three of the app's bots are **Claude scheduled tasks**, not code in this repo. Each run starts a fresh Claude session that searches the web and writes records into the app's database. The app only displays what they write (see `botlog` in [`../data-model.md`](../data-model.md)).

The other four bots in the app (Matchmaker, Scorer, Follow-up watcher, Duplicate checker) run live inside `src/index.html`.

| Bot | Schedule (New York time) | Writes to | Instructions |
|-----|--------------------------|-----------|--------------|
| News bot | Every other day, 6:47 AM | `news`, `botlog` | [news-bot.md](news-bot.md) |
| Prospector | Mondays, 6:52 AM | `businesses`, `signals`, `cois`, `botlog` | [prospector.md](prospector.md) |
| Research bot | Tue, Thu, Sat, 6:42 AM | `businesses`, `contactRequests`, `botlog` | [research-bot.md](research-bot.md) |

Snapshot taken 2026-10-17 from the scheduled tasks on the owner's Claude account. If you change a bot there, update its file here so the repo stays the source of truth.

All three point at the live app: `https://claude.ai/artifact/FgVJzZehAG5NhqRiwq2st9`.
