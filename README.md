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

Open port 8000. Without `DATABASE_URL`, a local SQLite database is created and seeded with demo profile content when the app starts.

## Admin updates

Set a private `ADMIN_SECRET` in `.env`. Admin API writes require the
`X-Admin-Secret` header:

```bash
curl -X POST http://127.0.0.1:8000/admin/projects \
  -H "Content-Type: application/json" \
  -H "X-Admin-Secret: replace-with-a-long-random-secret" \
  -d '{"title":"Forecasting Model","summary":"Built a demand forecast."}'
```

## Database fallback

After a successful database read or admin write, the app stores the last
known-good public profile in `data/profile_snapshot.json`. If the database is
unavailable, the public page serves that snapshot instead of a blank or error
page. Keep this snapshot available in the deployed application.

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
