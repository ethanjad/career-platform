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

## Project 1 evidence

See [docs/project-1-submission.md](docs/project-1-submission.md) for the full
list. Exercise write-ups:

- [Exercise 03: Azure VM deployment](docs/evidence/ex03.md)
- [Exercise 05: DNS failure investigation (simulation)](docs/evidence/ex05.md)
- [How this site is secured (HTTPS)](docs/how-this-site-is-secured.md)
