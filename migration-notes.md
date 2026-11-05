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
| 14 | 2026-11-04 | Owner saves the Cloudflare token on the server through a hidden prompt | The first token was pasted into the command by mistake, which exposed it in chat and terminal history, so the owner was asked to delete it and create a new one. Hidden input then led to 5 pastes in one file. The agent kept the one token Cloudflare verified as active and removed the rest, without displaying it | The prompt shows nothing while pasting | The owner confirmed on 2026-11-04 that the first token is deleted |
| 15 | 2026-11-04 | No `aws` DNS record in the plan | Owner asked for `aws.ethanjad.me`: `A` to the Elastic IP, DNS only, added with the Cloudflare CLI. A before-and-after listing shows it's the only change: 10 records became 11 | Owner's request | This name didn't serve the site until deviation 16 |
| 16 | 2026-11-04 | One certificate, for `ethanjad.me`, through Cloudflare DNS validation | Owner asked for HTTPS on `aws.ethanjad.me` the Azure way: a second Let's Encrypt certificate through certbot's nginx plugin (HTTP validation), with HTTP redirecting to HTTPS. nginx now has blocks for this name | Owner's request | Two certificates and two renewal methods. Renewal for this name depends on port 80 staying open |
| 17 | 2026-11-04 | Owner changes the apex record in the Cloudflare dashboard | Changed with the Cloudflare CLI, keeping the record's ID | Owner asked for help cutting over, and the CLI was already in use for the `aws` record | None. A before-and-after listing shows one changed record |
| 18 | 2026-11-04 | Watch for 24 hours or until the trial ends before merging | Merged right after the cutover | Owner's instruction | Less time to spot a problem while Railway is still a fallback |
| 19 | 2026-11-04 | `tcp_user_timeout` not in the plan | Added `tcp_user_timeout=5000` to `DATABASE_URL` on the server | Testing found a 60-second hang on the first request when the database is cut off | Tested on a copy, not during a failure on the live app |
| 20 | 2026-11-04 | `deploy.sh` as written | Added `~/.local/bin` to its `PATH` | It couldn't find `uv` over a plain SSH command | None |
| 21 | 2026-11-04 | Fresh reviewer for the whole branch | Self-review by the author | Agents aren't spawned without the owner asking | Weaker than a fresh review. The owner can ask for `/code-review` |
| 22 | 2026-11-04 | Redeploy from `main` once | Took two runs. The old `deploy.sh` on the server switched to `main`, then exited with `127` because it couldn't find `uv`. The second run used the fixed script and passed | The fix to the script was part of the same commit | None. The old app kept serving until the restart. A failed `uv sync` still doesn't roll back the checkout, which is a known gap |

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
- **2026-11-04, HTTPS for `aws.ethanjad.me`: done.** Certificate expires 2027-02-02. HTTP redirects with `301`, keeping the path and query. A renewal dry run passes for both certificates. The `ethanjad.me` one first failed with a temporary `rateLimited` "Service busy" reply from Let's Encrypt's test server, and passed on retry. Used `certbot certonly --nginx`, so certbot doesn't edit the nginx config, which stays in `deploy/`. `ethanjad.me` still points at Railway.
- **2026-11-04, owner confirmed:** first Cloudflare token deleted, database passwords saved, midterm interview already passed, so it no longer limits the cutover date.
- **2026-11-04, test of `aws.ethanjad.me`:** 38 visitor and admin checks passed, including a create, update and delete through the admin API on RDS that was undone. Desktop and phone screenshots look correct. The homepage, the PDF and all 13 database comparison lines match Railway. Issue found: with the database cut off abruptly, the first request hangs and nginx returns `504` after 60 seconds, then later requests get a fast `503`. An unknown table in an authenticated admin request returns `500`. A throwaway copy with `tcp_user_timeout=5000` in `DATABASE_URL` cut that first request to about 12 seconds. Not applied yet.
- **2026-11-04, cutover: done at 09:26 UTC.** `ethanjad.me` now points at AWS. Admin edits were frozen during the switch. `tcp_user_timeout` wasn't applied, because the owner hadn't decided.
- **2026-11-04, timeout fix and docs: done.** See deviations 19 to 21.
- **2026-11-04, merged to `main`: done.** Server runs `e9eae02` from `main`. `https://ethanjad.me` returns `200` from nginx, homepage unchanged. `aws-migration` deleted. Merging triggered a Railway build, as expected, which visitors don't reach. To do: external uptime check, spending alert, Zoho test email, remove `railway.json` and `start.sh` after the trial ends (done 2026-11-05).
- **2026-11-04, README: updated.** Added the AWS architecture diagram, the page-load path and what testing found. The Mermaid diagram hasn't been seen rendered.

- **2026-11-04, follow-up.** The admin unknown-table `500` is fixed (`8f26c3f`): the live server returns `404` with a valid secret and `401` without one. The owner reports checking the padlock, a laptop and phone click-through, the LinkedIn link, Google Analytics and Zoho email by hand. Billing page: $0.00 after credits, $139.84 of $140 left. Small load test: 300 requests, 5 at a time, 0 failed, median 352 ms, slowest 550 ms. DNS re-checked: 11 records, none changed since the cutover, `www` still redirects. External uptime check added as a GitHub Actions job. The "Not verified" list below is what was true at the time of the test.

- **2026-11-04, live outage retest.** The owner ran it, with the database blocked by a firewall rule for 25 seconds at 21:30 UTC. Requests went through nginx from the server itself. First request `503` in 10.2 seconds, not `504` after 60. Later requests `503` in about 5 seconds, so not the fast `503` seen earlier: each one waits for the 5-second `connect_timeout`. `/resume.pdf` returned `200` but also took about 5 seconds, cause not looked into. `/healthz` returned `200` within 1 second of unblocking, and no firewall rule was left behind. Response bodies weren't checked in this run.

## Section 10 test record: `aws.ethanjad.me` (2026-11-04)

### What I tested, and the evidence

| Test | Evidence | Result |
|---|---|---|
| `A` record `aws` points at the Elastic IP, DNS only | Cloudflare CLI: `A aws.ethanjad.me <EIP> proxied=False` | Pass |
| No other record changed | The other 10 records, including their IDs, match the listing taken before `aws` was added | Pass |
| DNS from the laptop | `nslookup aws.ethanjad.me` returns `<EIP>`, the address AWS reports | Pass |
| Let's Encrypt certificate | Issuer Let's Encrypt `YE1`, covers `aws.ethanjad.me`, expires 2027-02-02, `curl` verify result `0` | Pass |
| HTTP redirects to HTTPS | `301` to `https://aws.ethanjad.me/`, keeping path and query | Pass |
| Renewal | `certbot renew --dry-run` succeeds for both certificates, the first `ethanjad.me` try hit a temporary Let's Encrypt "Service busy" | Pass on retry |
| Pages and assets | `/`, `/privacy`, `/healthz`, `/resume.pdf` and CSS return `200`; a missing page returns `404`; all 5 same-site links load | Pass |
| Same content as Railway | Homepage identical after removing host names; `resume.pdf` byte-identical; database: all 7 tables, 5 sequences and constraint count match | Pass |
| Rendering | Headless Chrome screenshots at 1280 and 500 px wide look correct | Pass |
| Admin security | No secret, a wrong secret and `change-me` all return `401` | Pass |
| Admin writes | Create, update and delete through the API on RDS appeared on the page, then were undone; Railway never got the row | Pass |
| Crash, reboot, deploy rollback | Service came back after `kill -9` and a reboot; a broken deploy rolled back with exit `1` | Pass |
| External links | 6 of 7 return `200` | Pass, see below |
| Database cut off suddenly | Later requests return `503` with the profile and notice, the PDF still downloads, and it recovers by itself. **The first request hangs and gets `504` after 60 seconds** | Known issue, not fixed |

38 scripted visitor and admin checks passed. The crash, reboot, rollback, outage and renewal tests were run separately.

### Not verified

- **Padlock in a real browser:** the certificate was checked with `curl` and `openssl`. The owner needs to open the site and look.
- **Cloudflare dashboard:** the record was checked through the CLI. The owner needs to look for the grey cloud and the unchanged Railway and mail records.
- **A person using the site:** clicks and layout on a real laptop and phone, beyond screenshots.
- **LinkedIn link:** LinkedIn answered `999`, which it commonly sends to automated requests, so the link itself is unconfirmed.
- **`mailto:` link:** not clicked. Zoho mail wasn't tested, and it doesn't depend on this server.
- **Google Analytics data:** the tag is on the page and its script loads, but I didn't check that visits arrive.
- **A real RDS restart or failover:** the outage was simulated with a firewall rule on the server.
- **Load:** no traffic testing.
- **First bill:** cost is an estimate from AWS's price files. `isba-student` can't read billing.
- **Spending alert:** not confirmed as set.
- **`tcp_user_timeout=5000`:** a throwaway copy reduced the first-request hang to about 12 seconds. Applied to the real app afterwards, but not retested with a failure there, to avoid disturbing live visitors.

