# Rotating the Postgres password after Railway's security incident (2026-10-25)

**Why.** On 2026-10-21 Railway published a security disclosure and recommended rotating PostgreSQL credentials. The same incident paused builds until about 2026-10-25. I followed Railway's guide, [Security disclosure: recommendation to rotate PostgreSQL database credentials](https://blog.railway.com/p/security-disclosure-recommendation-rotate-postgresql-database-credentials):

- **Rotate with Regenerate.** Use the dashboard's Regenerate button, not `ALTER USER` or editing `POSTGRES_PASSWORD` by hand.
- **Then redeploy.** Redeploy every service that uses the database.
- **Then check.** Look at logs, sessions, roles, extensions and data.

All times are PDT on 2026-10-25, with UTC in brackets where Railway recorded it.

## Timeline

| Time | What | Evidence |
|---|---|---|
| 20:39 | **Pre-checks.** The web service's `DATABASE_URL` is the reference `${{Postgres.DATABASE_URL}}`, not a pasted string, so a redeploy picks up a new password. Postgres has **no public TCP proxy** (`railway tcp-proxy list`: none; removed during the incident). The only outside consumer was `RAILWAY_DATABASE_URL` in my local `.env`, which already pointed at the removed proxy. | Railway API `variables(unrendered: true)`; CLI |
| 20:39:35 | **Baseline audit** (read-only, inside the web container via `railway ssh`). | see "Audit" below |
| 20:41:43 (03:41:43Z) | **Regenerate** clicked in Postgres → Database → Config → Connection. Railway restarted Postgres as deployment `ccc7884d` (`SUCCESS`). `POSTGRES_PASSWORD` and `PGPASSWORD` changed: their hashes match each other (`4d63507a…`) and differ from the old password's (`0c3e459e…`). Only hashes were compared, never the passwords. | Railway deployment list; `sha256` of the variables |
| 20:41:43 (03:41:43Z) | Railway started an automatic web redeploy, `fd7efe56`. It **failed** at build: `No start command detected`. | build log |
| 20:42:09 | **The site was down, as expected.** The running web container still had the old password. `GET /` returned **503** (profile visible, "Projects temporarily unavailable") and `/healthz` returned `503 database unavailable`. | `curl` |
| 20:42:36 (03:42:35Z) | `railway redeploy --service career-platform` started `4047bd49`, which **failed** the same way. | build log |
| 20:43:27 (03:43:27Z) | `railway redeploy --service career-platform --from-source` started `53719eb6` (reason `deploy`, commit `68f7ec3`). | Railway deployment list |
| 20:45:34 | `53719eb6` **`SUCCESS`**. `GET /` returned 200 with all 7 projects, and `/healthz` returned `ok`. | `curl` |
| 20:45:58 | **After audit:** unchanged, see below. | — |

**Downtime:** about 4 minutes (20:41:43–20:45:34). During that time visitors saw the designed 503 page ([db-failure-503.md](db-failure-503.md)), not an error or stale data. The old container's log shows 4 requests answered with 503.

## Why the first two redeploys failed

Railway's plain **redeploy** rebuilds the previous source but doesn't apply `railway.json`, which is where this service's start command (`bash start.sh`) and health check live. Railway now calls `railway.json` deprecated. Without the start command, Railpack couldn't tell how to start the app (`app/main.py`, not a root `main.py`) and stopped.

A deploy **from source**, the same as a push to `main`, applies `railway.json` and worked. Railway's guide suggests `railway redeploy --service …`, but for this service the right command is `railway redeploy --service career-platform --from-source`. A lasting fix is to set the start command in the service's settings, or move to Railway's newer config format, so plain redeploys work too.

## Audit before and after (read-only)

Both audits ran inside the web container (`railway ssh --service career-platform`) through `SET TRANSACTION READ ONLY` over Railway's private network. No public endpoint was opened.

| Check | Before (20:39:35) | After (20:45:58) |
|---|---|---|
| Roles (`pg_roles`) | `postgres` + PostgreSQL's built-in `pg_*` roles only | identical |
| Extensions | `plpgsql` 1.0 only | identical |
| Tables (`public`) | the app's 7 tables | identical |
| Data (sha256 of every row, per table) | — | **identical in all 7 tables** |
| Sessions (`pg_stat_activity`) | 2, both from the web container (`fd12:…` private network) | all started *after* the restart (old sessions dropped). 2 from the web container, plus 1 from `127.0.0.1` (inside the Postgres container, no application name, started 03:42:14Z, 31 s after the restart) |

- **The `127.0.0.1` session:** it can only come from inside the Postgres container, such as Railway's own tooling or the dashboard's Data view. It started after the old password had stopped working, so it isn't an outside session using the old credential. It wasn't terminated.
- **The data:** 1 profile, 4 experience, 2 education, 4 skills, 7 projects, 2 links and 1 settings row, the same as the migration comparison earlier that evening. Earlier changes since the Oct 8 export (projects 5–6 renamed, 7–11 and link 8 added) are explained in the [migration plan's progress log](../superpowers/plans/2026-10-08-railway-postgres-migration.md#progress-log).
- **The new deployment's log:** 0 `password authentication failed` lines and 0 errors.

## Not done, or still open

- **`ADMIN_SECRET`:** **not rotated, by my decision (2026-10-25).** It wasn't part of Railway's database guidance. Its value appeared once in a local working session's output on 2026-10-25, not in the repository or anywhere public. It can be rotated later with `railway variable set ADMIN_SECRET --stdin --skip-deploys`, then a `--from-source` redeploy.
- **The stale local `RAILWAY_DATABASE_URL`:** left in `.env`. It points at the removed proxy and holds the old password, which no longer works, so it's harmless.
- **Database errors aren't logged.** The app catches them to serve the 503 page but doesn't log why. During the outage the old container's log showed 503s and no `password authentication failed` line, so the cause had to be inferred from the timing.
