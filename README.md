# Career Platform

A recruiter-facing FastAPI, Jinja, and SQLite resume site.

## Run in Codespaces

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open port 8000. SQLite is initialized with seed profile content on first request.

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
known-good public profile in `data/profile_snapshot.json`. If SQLite is
unavailable, the public page serves that snapshot instead of a blank or error
page. Keep this snapshot available in the deployed application.

## Azure VM path

On an Azure VM, install Python and the requirements, set the environment
variables, and run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For production, run Uvicorn under a process supervisor and allow the chosen
port in the VM network security group.
