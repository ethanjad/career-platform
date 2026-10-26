# Career Platform

A recruiter-facing FastAPI, Jinja, and PostgreSQL résumé site (SQLite for local development).

**Live site:** https://ethanjad.me. `https://www.ethanjad.me` redirects to it. It's hosted on Railway, with DNS on Cloudflare, email on Zoho Mail and analytics in Google Analytics 4.

## Updating the live site

**Code, templates or styles.** Pushing to `main` is the deploy:

1. **Make the change and run the tests:** `uv run pytest`. Optionally run them against Postgres with `TEST_DATABASE_URL` (see "Deploying on Railway").
2. **Commit and push:** `git push origin main`.
3. **Railway deploys it.** Railway builds the new commit and starts it. It only moves traffic to the new container once `/healthz` answers `ok`, so a build that can't reach the database never goes live.
4. **Check it live:** `curl -s https://ethanjad.me/healthz`, then open the page. Undo with `git revert` (see "Rollback").

**Content** (experience, projects, skills, links). Use the admin API against the live site. No deploy is needed:

```bash
curl -X POST https://ethanjad.me/admin/projects \
  -H "Content-Type: application/json" \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -d '{"title":"…","summary":"…"}'
```

`PUT /admin/<table>/<id>` edits a row and `DELETE` removes one. The same API runs locally (next section).

**Résumé PDF.** Replace `data/resume.pdf` with the web-safe export (no phone number or home address), then commit and push.

## Run in Codespaces

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open port 8000. Without `DATABASE_URL`, a local SQLite database is created and seeded with the same public profile content as the live site when the app starts.

## Admin updates

Set a private `ADMIN_SECRET` in `.env`. Admin API writes require the
`X-Admin-Secret` header:

```bash
curl -X POST http://127.0.0.1:8000/admin/projects \
  -H "Content-Type: application/json" \
  -H "X-Admin-Secret: replace-with-a-long-random-secret" \
  -d '{"title":"Forecasting Model","summary":"Built a demand forecast."}'
```

## Architecture

Diagrams:

- [docs/request-path.md](docs/request-path.md), with PNG copies in `docs/request-path-*.png`:
  - Azure as it was
  - the order of events for one page load
  - Railway today: web and analytics, and email
- [docs/azure-architecture.md](docs/azure-architecture.md): the Azure setup step by step, including updates, restarts, email and analytics.

| Path | From → to | Protocol / port | Where |
|---|---|---|---|
| Name lookup | browser or mail server → Cloudflare DNS | DNS, UDP/TCP 53 | Cloudflare global anycast |
| Web page | browser → Railway edge | HTTPS, TCP 443 (80 only redirects) | Railway, region `sfo` |
| Inside Railway | edge → web container → Postgres | HTTP on `$PORT`, then the Postgres protocol over the private network | Railway |
| `www` | browser → Cloudflare | HTTPS 443 / HTTP 80, 301 to the apex | Cloudflare |
| Analytics | browser → `googletagmanager.com`, `google-analytics.com` | HTTPS, TCP 443 | Google |
| Mail in | sender's server → `mx.zoho.com` | SMTP, TCP 25 | Zoho (US) |
| Mail out | Zoho `165.173.180.0/24` → receiver | SMTP, TCP 25, TLS 1.3 (observed) | Zoho (US) |
| *Azure, until 2026-10-08* | browser → NSG → nginx → uvicorn → SQLite file | HTTPS 443 / HTTP 80, then `127.0.0.1:8000`, then a file read | Azure Sweden Central |

Email and analytics never pass through the web host. They were set up after the move to Railway.

## Database failure behaviour

After every successful database read (including the one after each admin
write), the app saves the public profile to `data/profile_snapshot.json`.

If the database can't be reached when `/` is requested:

- the page returns **HTTP 503**, so monitors and crawlers see that something is wrong
- the profile (name, summary, experience, education, skills, links) still shows, read from the snapshot
- the Projects section says **"Projects temporarily unavailable"** instead of showing old snapshot projects
- the next request after the database comes back gets a normal 200 page; no restart is needed

`/healthz` returns 503 `database unavailable` in the same situation, and the
app still starts if the database is down at boot. If the projects table is
empty while the database is up, the section stays on the page and says "No
projects are listed right now."

## Decisions

### Starting with SQLite

The first version stored everything in a SQLite file (`data/resume.db`). Why:

- **One process, one machine.** The site ran as one FastAPI app on one Azure VM, so an in-process database file was enough. There was no separate database server to install, secure, or keep running.
- **Small, rarely written data.** One profile and a few dozen rows, changed only through the admin API. SQLite's single-writer limit didn't matter.
- **Simple backup and move.** Copying the data meant `sqlite3 .backup` and `scp`, which is how it moved from the laptop to the VM.

The alternative was a managed PostgreSQL server from the start. That would
have added cost and setup before the site needed it. SQLite stopped fitting
when the site moved to Railway: container filesystems are rebuilt on each
deploy, so the data needed a database outside the container (see the Railway
section below).

### Moving from the Azure VM to Railway

**Chosen:** Railway (managed containers) with Railway's managed PostgreSQL. Migrated on 2026-10-08.

| Option | For | Against |
|---|---|---|
| **Stay on the Azure VM** | Full control. Already working. Teaches the whole stack (OS, nginx, systemd, firewall, TLS). | I patch the OS, renew certificates, keep SSH safe and watch disk and memory on a 1 GiB VM. Deploying was `ssh` + `git pull` + restart, by hand. SQLite on one disk with hand-made backups. Cost about $5 of student credit by Oct 21 (see "Costs"). |
| **Azure App Service + Azure Database for PostgreSQL** | Managed, and in the same cloud as before. | More services to configure and secure, and a managed Postgres server costs noticeably more than the site needs. |
| **Railway** ✅ | Deploys on every push to `main`, gated by `/healthz`. TLS certificates are automatic. Postgres is one click away on a private network. No OS or web server to maintain. | Less control and visibility. A trial plan with an end date. Logs aren't kept long: the Oct 8 failure logs were gone by Oct 21. A provider outage on 2026-10-21–22 paused all deploys, and there was nothing I could do but wait. |

**Why Railway:** the site is small and changes often, so automatic deploys and certificates matter more than server control. The VM had already taught the server side. Moving to Railway also replaced the SQLite file with a real database service. The trade-off showed up during Railway's Oct 21–22 outage, when the site stayed up but couldn't be updated.

### Managed email (Zoho Mail) vs running my own mail server

**Chosen:** Zoho Mail's free plan for `ethan@ethanjad.me`, set up on 2026-10-13.

| Option | For | Against |
|---|---|---|
| **Self-hosted** (Postfix + Dovecot on the VM) | Full control, no third party reading mail. | Azure blocks outbound port 25 on most subscriptions, so the VM couldn't send mail directly anyway. A new server IP has no sending reputation, so mail tends to land in spam. Spam filtering, TLS certificates, DKIM signing, backups and uptime are all mine. Railway can't receive mail on port 25 at all. |
| **Forwarding only** (Cloudflare Email Routing) | Free, nothing to run. Mail to `@ethanjad.me` goes to Gmail. | Receives only. Replies would come from Gmail, not `ethanjad.me`, so the domain wouldn't pass SPF/DKIM/DMARC as the sender. |
| **Google Workspace** | Familiar Gmail interface. | Paid per user per month. |
| **Zoho Mail (free)** ✅ | Free for a custom domain. Zoho runs the MX servers, spam filtering, sending reputation and DKIM signing. | A third party holds the mail. 5 GB limit and a web or app client only on the free plan (no IMAP). |

**Why Zoho:** a personal address on my own domain needs to *send* mail that lands in inboxes. Sending reputation and DKIM are the hard parts of running mail, and Zoho does both for free. The [header check](docs/evidence/zoho-header-check.md) shows the result: SPF, DKIM and DMARC all pass at Gmail.

## Azure VM (2026-09-29 to 2026-10-08, deleted 2026-10-19)

Before Railway, the site ran on an Ubuntu 24.04 VM in Azure (swedencentral):
nginx on ports 80 and 443 proxied to uvicorn on `127.0.0.1:8000`, with the
SQLite file in `data/`.

**What made it survive restarts:**

- The `career-platform` systemd service was **enabled**, so it started at every boot. It had `Restart=always` to come back after a crash.
- Its `WorkingDirectory` was the repo, so it opened the real database.
- It used `--env-file .env`, so the secrets loaded without anyone logging in.
- nginx was enabled by its package and had a `Restart=on-failure` drop-in.

A full reboot test was never run before the VM was deleted. See
[azure-vm-retired.md](docs/evidence/azure-vm-retired.md) for what was tested,
the final firewall (NSG) rules, and the shutdown and deletion record.

## Deploying on Railway

The `web` service deploys `main` with `railway.json` (start: `start.sh`,
healthcheck: `/healthz`). It needs two variables:

- `DATABASE_URL` = `${{Postgres.DATABASE_URL}}` (Railway reference variable)
- `ADMIN_SECRET` = a long random string

To copy data between databases (keeps ids, refuses to overwrite unless
`--replace`):

```bash
uv run python -m scripts.copy_database SOURCE_URL TARGET_URL
```

Run the tests against Postgres by pointing `TEST_DATABASE_URL` at a
throwaway database whose name contains `test`.

## Moving from Azure to Railway and PostgreSQL (2026-10-08)

Plan and progress log:
[2026-10-08-railway-postgres-migration.md](docs/superpowers/plans/2026-10-08-railway-postgres-migration.md).
There was no separate design spec for this move. The plan was written from
the request and from what inspecting the app found, and those findings are
listed at the top of the plan.

**How the data was preserved:**

1. **Export.** The VM's SQLite file was exported with `sqlite3 .backup`, an online, consistent copy. That copy is kept off-repo as `resume.db.bak-railway-20261008-214832`.
2. **Copy.** `scripts/copy_database.py` copied every table into Railway Postgres, keeping each row's `id`. It then moved the id sequences past the highest id, so the next admin insert doesn't collide. It refuses to write into a database that already has data unless given `--replace`.
3. **Copy before the first deploy.** The data went in before the first deploy, so the app's startup step found a profile row and didn't seed the demo data.

The copied rows keep ids that seeding could never produce: experience 3–6, projects 5–6, link 7. Seeding always starts at 1. The source-versus-target comparison is in the plan's progress log.

**Who is responsible for what:**

| Layer | Azure VM | Railway |
|---|---|---|
| Operating system | Me: Ubuntu 24.04, patched with `apt` | Railway (container image built by Railpack) |
| Python runtime | Me: a uv-managed venv on the VM | Railway, pinned by `.python-version` (3.12) |
| Entry point / process | Me: systemd unit, `uvicorn --workers 2` | Railway runs `start.sh` (one uvicorn) and restarts it `ON_FAILURE` |
| Reverse proxy and TLS | Me: nginx + Certbot (Let's Encrypt) | Railway's edge, with automatic Let's Encrypt |
| Firewall | Me: Azure NSG rules | Railway. Only the web service is public. Postgres has no public endpoint (its TCP proxy was removed during Railway's 2026-10-21–22 incident), and one is opened only temporarily for a copy (see "Rollback → Database"). |
| Code delivery | Me: `ssh` + `git pull` + `systemctl restart` | Railway: build and deploy on each push to `main`, gated by `/healthz` |
| Configuration and secrets | Me: `.env` on the VM disk | Railway service variables (`DATABASE_URL`, `ADMIN_SECRET`) |
| Database software | Me: SQLite library inside the app | Railway: managed PostgreSQL 18 service |
| Data | Me: one file on the VM disk, backups by hand | Railway volume behind Postgres. **Backups are still mine** (`copy_database` to a file) |
| DNS | Me: Cloudflare A record to the VM IP | Still me: Cloudflare CNAME to Railway, plus the `www` redirect rule |
| App code, content, admin secret | Me | Still me |

## Rollback

### Code

Every deploy is a commit on `main`, so rolling back code is a revert:

```bash
git revert <bad-sha>        # new commit that undoes it
git push origin main        # Railway builds and deploys it like any change
```

If `main` can't be fixed quickly, redeploy an earlier good build from the
Railway dashboard (Deployments → ⋯ → Redeploy). Then revert on `main`, so
the next push doesn't bring the bad code back.

### Database

Content changes go through the admin API, so undoing one is another admin
call, made with the old values (`PUT /admin/<table>/<id>`) or a `DELETE`.
Before any risky change, take a copy first.

Postgres has no public endpoint, so the copy runs through a **temporary** TCP proxy that is deleted afterwards:

```bash
railway tcp-proxy create --port 5432 --service Postgres   # note the proxy id, host and port it prints
# DB_URL = postgresql://postgres:<PGPASSWORD>@<proxy host>:<proxy port>/railway
#   (PGPASSWORD from: railway variables --service Postgres --kv)
uv run python -m scripts.copy_database "$DB_URL" "sqlite:///$HOME/Desktop/github/resume-$(date +%Y%m%d-%H%M).db"
railway tcp-proxy delete <proxy-id> --yes                  # close it again
```

To restore that copy (this overwrites everything in Postgres), open the proxy the same way, then:

```bash
uv run python -m scripts.copy_database "sqlite:///$HOME/Desktop/github/resume-<stamp>.db" "$DB_URL" --replace
```

For a read-only look without opening anything, run Python inside the web container with `railway ssh --service career-platform`, which reaches Postgres over the private network. This is how the migration was checked on 2026-10-25. The proxy steps above haven't been run since the proxy was removed.

### Back off Railway, keeping data written after cutover

Rolling back to the pre-cutover SQLite export would lose every edit made
on Railway, such as the "this website, in progress" project. So **export
from Postgres at rollback time**, not from the old file:

1. **Freeze.** Make no admin writes from here on.
2. **Export the live data.** Run the `copy_database` Postgres → SQLite command above. This was tested on 2026-10-21 on a local cluster: a row written after the copy came back with its id.
3. **Restore on the new host.** Put that file on the new host as `data/resume.db`, with the same app commit.
4. **Switch DNS.** In Cloudflare, point `ethanjad.me` at the new host (an A record, DNS only), then check `curl https://ethanjad.me/healthz`.

The old Azure VM was deleted on 2026-10-19. A rollback to Azure now means
rebuilding it from the [VM plan](docs/superpowers/plans/2026-10-01-operate-the-vm.md)
before step 3.

## Failures and fixes

### 1. Railway deploys failed during the migration (app/database, 2026-10-08)

Full record: [railway-deploy-failures.md](docs/evidence/railway-deploy-failures.md).

- **Symptom:** the first three Railway deployments (21:27, 21:30 and 22:08 UTC) were marked `FAILED`. The site stayed on the Azure VM.
- **Checks:** `railway deployment list` showed what each deploy built: commits `a7b5899` and `3f89893`, triggered by setting up the service and by a push. `git show <sha>:<file>` showed what `main` held at those commits.
- **Diagnosis:** Railway was connected to `main` before the migration branch was merged. Those commits had no `railway.json`, no Postgres driver, no `DATABASE_URL` support and no Python pin, so they were the old SQLite-only app. The build logs had expired by the time this was written up, so the exact error isn't known.
- **Fix:** merging `railway-postgres` into `main` (`7ca25e5`). Its deploy succeeded.
- **Repeat check:** every deploy since has succeeded. On 2026-10-21, `/healthz` returned `ok` and the real profile was served (migration plan progress log).

### 2. Choosing the VM's size and region (Azure, 2026-09)

Write-up in my own words: [ex03.md §3](docs/evidence/ex03.md#3-troubleshooting).

- **What happened:** the VM was created in Sweden Central before I had picked a size, region and price.
- **Why it stayed:** by the time I wanted US Central, the VM was already running and working. I kept it and accepted slower response times and a slightly higher price.

### 3. DNS/TLS failure after a migration (simulation)

**Simulation:** [ex05.md](docs/evidence/ex05.md) uses the course's supplied outputs, not my live domain.

- **Symptom:** `curl` failed with `(60) certificate subject name does not match`.
- **Diagnosis:** a stale DNS `A` record still pointed at the old VM, which served the old certificate.
- **Fix:** replace the `A` record with a `CNAME` to Railway.

## Reflection

One thing that surprised me was the ease of Railway in comparison to Azure. On Azure I had to keep editing the inbound network rules to accommodate my new IP address. On Railway there is no server to SSH into, so there are no rules like that to maintain.

One thing I would do differently is deploy the Azure VM in a different region, preferably one closer to where I am located. I originally deployed it in Sweden because Claude proceeded without my approval. This may have caused background delays and lagging.

I learned an abundance about the parts that make up the web application, such as Uvicorn, FastAPI, Jinja, and SQLite. By taking all of the knowledge that I have learned, I now have the confidence to understand the behind-the-scenes activity that occurs when visiting a website, or when establishing a website myself.

## Costs, cleanup and limitations

### What it costs

| Service | Plan | Cost so far |
|---|---|---|
| Azure (VM, disk, public IP), Sep – Oct 19 | Azure for Students credit | **$5.00** of credit: storage $2.07, virtual network / IP $2.93, VM compute $0.00 (free allowance). From the Cost Management API, 2026-10-22. |
| Railway (web + Postgres) | Trial | $0.61 for Oct 5–21 (`railway usage`). **$4.34 of trial credit left, 14 days remaining on 2026-10-22, so the trial ends about 2026-11-05** (Railway dashboard). |
| Cloudflare DNS + `www` redirect | Free | $0 |
| Zoho Mail | Free (5 GB, one domain) | $0 |
| Google Analytics 4 | Free | $0 |
| Domain `ethanjad.me` | Namecheap via the GitHub Student Pack, registered 2026-10-01, **expires 2027-10-01** | $0 for the first year. Renewal is at Namecheap's normal price. |

### Cleanup plan

- **Azure, done 2026-10-19:** the VM, disk, IP, NSG and the whole `rg-career-platform` group were deleted. Only `NetworkWatcherRG`, created automatically by Azure and free, remains.
- **Railway, before about 2026-11-05 (trial end):** either move to a paid plan, or export the database with `copy_database` (see "Rollback") and move the site off Railway before the trial lapses. If the trial lapses, the site goes down.
- **Domain, before 2027-10-01:** renew it, or let it go. If it lapses, the site, email and certificates all stop.
- **Secrets:** rotate `ADMIN_SECRET` and the Postgres password once Railway publishes guidance on its 2026-10-21 security incident.

### Remaining limitations

- **One app process and one database, with no replicas.** A Railway outage takes the site down, and during the 2026-10-21–22 incident deploys were paused for more than a day.
- **Backups are manual.** Nothing exports Postgres on a schedule.
- **DMARC only reports.** It's `p=none`, so forged mail from `ethanjad.me` is reported, not blocked.
- **No consent banner.** Analytics are blocked by many content blockers, so GA4 under-counts.
- **Old deploy logs aren't kept.** The Oct 8 build logs were already gone when I looked on Oct 21, so failures have to be recorded on the day.
- **The admin API is the only way to edit content.** It's protected by a single shared secret, with no admin UI and no audit log.

## Project 1 evidence

See [docs/project-1-submission.md](docs/project-1-submission.md) for the full
list. Exercise write-ups:

- [Exercise 03: Azure VM deployment](docs/evidence/ex03.md)
- [Exercise 05: DNS failure investigation (simulation)](docs/evidence/ex05.md)
- [Exercise 06: Zoho email (SPF, DKIM, DMARC) and Google Analytics](docs/evidence/ex06.md)
- [Zoho header check: hop-by-hop SPF, DKIM, DMARC analysis](docs/evidence/zoho-header-check.md)
- [How this site is secured (HTTPS)](docs/how-this-site-is-secured.md)
- [Azure VM: restart setup, final NSG rules, retirement](docs/evidence/azure-vm-retired.md)
- [Database down → 503 → recovery](docs/evidence/db-failure-503.md)
- [DNS records, www redirect and certificates](docs/evidence/dns-and-https.md)
- [Railway deploy failures during the migration](docs/evidence/railway-deploy-failures.md)
- [Architecture diagrams](docs/request-path.md) · [Azure step by step](docs/azure-architecture.md)
