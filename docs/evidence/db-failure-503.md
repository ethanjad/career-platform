# Database down → 503 → recovery on refresh

What the site does when PostgreSQL can't be reached, and that it recovers without a restart. The behaviour is described in the README ("Database failure behaviour").

## Local check, 2026-10-21

- **Setup:** a throwaway PostgreSQL 18 cluster on `127.0.0.1:55432`, and the app run with `uvicorn app.main:app --port 8765` and `DATABASE_URL` pointing at that cluster.
- **Steps:** I requested `/` and `/healthz` with the database up, then stopped it with `pg_ctl stop -m fast` and requested again. Then I started it again and requested again, without restarting the app.
- **Page check:** a `grep` of each page for `<h1>Ethan Jad</h1>` (profile visible), `Hoops Recap` (a live project) and `Projects temporarily unavailable`.

```
== database up  2026-10-21 01:17:53 PDT
GET / -> 200
ok (healthz 200)
   1 <h1>Ethan Jad</h1>
   1 Hoops Recap
== database stopped  2026-10-21 01:17:54 PDT
GET / -> 503
database unavailable (healthz 503)
   1 <h1>Ethan Jad</h1>
   1 Projects temporarily unavailable
== database restarted, app not restarted  2026-10-21 01:17:56 PDT
GET / -> 200
ok (healthz 200)
   1 <h1>Ethan Jad</h1>
   1 Hoops Recap
```

**What this shows**

- With the database down, the page returns 503, the profile stays visible, and no snapshot projects are shown.
- The first request after the database came back got the normal page. No restart was needed, because the connection pool's pre-ping drops dead connections.
- The app log had 0 `ERROR` lines.

The same behaviour is covered by these tests:

- `test_database_failure_returns_503_with_profile_visible_and_projects_unavailable`
- `test_page_recovers_on_next_request_after_database_returns`

Both are in `tests/test_public_profile.py`, and the suite passes on SQLite and on PostgreSQL (`TEST_DATABASE_URL`).
