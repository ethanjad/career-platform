# Career Platform

A recruiter-facing FastAPI, Jinja, and PostgreSQL résumé site (SQLite for local development).

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
| Firewall | Me: Azure NSG rules | Railway. Public: the web service, plus a TCP proxy to Postgres (password-protected) used only for laptop-side copies |
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
Before any risky change, take a copy first:

```bash
set -a; . ./.env; set +a
uv run python -m scripts.copy_database "$RAILWAY_DATABASE_URL" "sqlite:///$HOME/Desktop/github/resume-$(date +%Y%m%d-%H%M).db"
```

To restore that copy (this overwrites everything in Postgres):

```bash
uv run python -m scripts.copy_database "sqlite:///$HOME/Desktop/github/resume-<stamp>.db" "$RAILWAY_DATABASE_URL" --replace
```

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

## Project 1 evidence

See [docs/project-1-submission.md](docs/project-1-submission.md) for the full
list. Exercise write-ups:

- [Exercise 03: Azure VM deployment](docs/evidence/ex03.md)
- [Exercise 05: DNS failure investigation (simulation)](docs/evidence/ex05.md)
- [Exercise 06: Zoho email (SPF, DKIM, DMARC) and Google Analytics](docs/evidence/ex06.md)
- [How this site is secured (HTTPS)](docs/how-this-site-is-secured.md)
- [Azure VM: restart setup, final NSG rules, retirement](docs/evidence/azure-vm-retired.md)
- [Database down → 503 → recovery](docs/evidence/db-failure-503.md)
- [DNS records, www redirect and certificates](docs/evidence/dns-and-https.md)
