# Migration notes: Railway to AWS EC2 and RDS

Running record of the move, and every deviation from [the plan](docs/superpowers/plans/2026-11-03-aws-ec2-rds-migration.md). Step-by-step results are in the plan's Progress log. This repo is public, so account IDs, public IPs, the RDS endpoint and secrets stay out of this file.

## Deviations from the plan

| # | Date | Plan said | What happened | Why | Cost or risk |
|---|---|---|---|---|---|
| 1 | 2026-11-03 | Free plan not considered; create RDS with 7-day backups | The Free account plan refused 7-day retention (`FreeTierRestrictionError`). The owner upgraded to the Paid plan, and the create call succeeded on a later retry | The owner chose to keep 7-day backups over shortening them | The no-charge guarantee is gone. Real charges begin once credits run out |
| 2 | 2026-11-03 | Budget alert at 80% of $30 | Recommended $30 actual and forecasted instead. Not yet confirmed as set | $26.82/mo reaches 80% around day 27 of every month | None, if the owner sets it |
| 3 | 2026-11-04 | Task order 1, 2, 3 | Tasks 2 and 3 Steps 1-3 ran before Task 1 | The owner asked for the database and instance first | None. Nothing in them depended on Task 1 |
| 4 | 2026-11-04 | `ssh-keygen` with no passphrase decision | New SSH key has no passphrase | The agent can't type one, and the plan didn't specify | A stolen laptop session could use the key. The owner can add one with `ssh-keygen -p` |
| 5 | 2026-11-04 | Instance launch settings | Also set `DeleteOnTermination=true` on the disk and added `Name` tags | Avoids a leftover billed disk at teardown; easier to identify | None |
| 6 | 2026-11-04 | Privacy test as written | Test also calls `initialize_database()` | The page needs a database to render in tests, as the existing privacy test does | None |
| 7 | 2026-11-04 | Privacy date is "the actual cutover date" | Set to November 4, 2026, the target date | Correct it if the cutover slips | Small: a wrong date on the page |
