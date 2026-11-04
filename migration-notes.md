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
| 8 | 2026-11-04 | Restore from the laptop through an SSH tunnel (Task 4) | The owner directed that the restore run from EC2. A laptop-tunnel run had already finished. Its copy, which nothing had used, was dropped, then a fresh dump was restored from EC2 into the empty database | Owner's instruction | None. Both runs matched Railway. The dumps stay on the laptop |
| 9 | 2026-11-04 | No PostgreSQL client on the server | Installed `postgresql-client-18` (18.6) from the PostgreSQL apt repository, client only, no server | The restore tool must be at least as new as Railway's PostgreSQL 18.6 | A third-party apt source on the server, which `unattended-upgrades` doesn't update by default |
| 10 | 2026-11-04 | Task 6 cutover restores from the laptop with `--clean` | Task 6 now restores from EC2. The cutover itself is on hold, with Railway running and DNS unchanged | Owner's instruction, one phase at a time | The Railway trial ends about 2026-11-05 |
| 11 | 2026-11-04 | Step 5 checks run through nginx after the certificate | Ran the app-level checks first, on the server over `127.0.0.1:8000`, with Step 6 and 7 before Steps 3-5 | The Cloudflare token isn't on the server yet | Step 5 must still be run in full through nginx |
| 12 | 2026-11-04 | `sudo pkill -f uvicorn` for the crash test | Used `kill -9` on the service's main process | The `pkill` pattern most likely matched its own SSH command, so that run reported nothing | None. The retest passed |
| 13 | 2026-11-04 | Temporary `deploy-test` branch | Pushed to the public GitHub repo with a deliberately broken `/healthz`, then deleted locally and on GitHub | The deploy script fetches from `origin`, so its rollback test needs a pushed branch | None. It was never on `main` and Railway didn't deploy it |
| 14 | 2026-11-04 | Owner saves the Cloudflare token on the server through a hidden prompt | The first token was pasted into the command by mistake, which exposed it in chat and terminal history, so the owner was asked to delete it and create a new one. Hidden input then led to 5 pastes in one file. The agent kept the one token Cloudflare verified as active and removed the rest, without displaying it | The prompt shows nothing while pasting | The owner must confirm the first token is deleted in Cloudflare |
| 15 | 2026-11-04 | No `aws` DNS record in the plan | Owner asked for `aws.ethanjad.me`: `A` to the Elastic IP, DNS only, added with the Cloudflare CLI. A before-and-after listing shows it's the only change: 10 records became 11 | Owner's request | This name didn't serve the site until deviation 16 |
| 16 | 2026-11-04 | One certificate, for `ethanjad.me`, through Cloudflare DNS validation | Owner asked for HTTPS on `aws.ethanjad.me` the Azure way: a second Let's Encrypt certificate through certbot's nginx plugin (HTTP validation), with HTTP redirecting to HTTPS. nginx now has blocks for this name | Owner's request | Two certificates and two renewal methods. Renewal for this name depends on port 80 staying open |

## Rules from the owner (2026-11-04)

- Work one phase at a time. Keep Railway running and its DNS unchanged.
- Restore from the EC2 instance into an empty database, before anything that creates tables.
- `pg_restore` on the instance must be the same major version as Railway's PostgreSQL or newer.
- Don't run the Azure deploy script or any seed script on AWS.
- Keep secrets outside Git.
- The Railway trial may end on 2026-11-05. No paid plan. The owner accepts this while migrating to AWS (decided 2026-11-04).

## Phase log

- **2026-11-04, restore from EC2: done.** Fresh Railway dump with a matching checksum, `pg_restore` 18.6, into a database with 0 tables and 0 sequences. All 7 tables, 5 sequences and 35 constraints match Railway exactly. Tables are owned by `career_app` and the connection used verified TLS. The dump was removed from the instance afterwards. The app hasn't been started on AWS.
- **2026-11-04, app on EC2: partly done.** Service, secrets, outage, crash, reboot and deploy tests pass. HTTPS and nginx wait for the Cloudflare token. Railway and DNS are unchanged.
- **2026-11-04, app on EC2: done.** HTTPS through nginx passes every visitor check with the name forced to the Elastic IP. Railway and DNS are unchanged. The cutover waits for the owner's go-ahead.
