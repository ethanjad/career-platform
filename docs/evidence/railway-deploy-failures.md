# Railway deploy failures during the migration (2026-10-08)

On migration day, Railway marked three deployments `FAILED` before the first one succeeded. This record was put together on 2026-10-21 from `railway deployment list --json` and the git history.

**The build and deploy logs can't be recovered.** `railway logs <id> --build` and `--deployment` return nothing for these deployments, though the same commands return logs for recent ones. The logs have aged out of Railway's retention, so the exact error message is lost. The diagnosis below rests on what *is* recorded.

## Symptom

| Created (UTC) | Deployment | Commit | Trigger | Status |
|---|---|---|---|---|
| 21:27:38 | `32117335-95e5-4fa9-9fd5-108672e20e70` | `a7b5899` "Add docs on how the site is secured" | service config change (`patchId` set) | `FAILED` |
| 21:30:12 | `2e91aa73-263d-4cf3-bec2-3184e5d24ccc` | `a7b5899` | service config change (`patchId` set) | `FAILED` |
| 22:08:47 | `bdef622f-8fbd-4faf-a568-f7d3975421c8` | `3f89893` "docs: add Railway + Postgres migration plan" | push to `main` | `FAILED` |
| 22:29:49 | `755291ea-221b-45a8-ad52-034e5f463e93` | `7ca25e5` "Merge branch 'railway-postgres'" | push to `main` | succeeded, later replaced (`REMOVED`) |

## Checks

What `main` contained at each deployed commit (`git show <sha>:<file>`):

| | `a7b5899`, `3f89893` (failed) | `7ca25e5` (worked) |
|---|---|---|
| `railway.json` (start command, `/healthz` check) | **missing** | present |
| `DATABASE_URL` support in `app/config.py` | **none** (SQLite only) | yes |
| `sqlalchemy`, `psycopg` in `requirements.txt` | **missing** | present |
| `.python-version` | **missing** | `3.12` |
| `start.sh` trusts proxy headers | no | yes |

## Diagnosis

Railway was connected to `main` before the Postgres-ready code was on `main`.

- **Order of steps:** the migration work was on the `railway-postgres` branch. The Railway service was pointed at the repo and given its variables (plan Task 6, Steps 2–3) while `main` still held the old SQLite-only app.
- **The trigger:** those config changes started the two `a7b5899` deploys, and pushing the plan to `main` started the third.
- **What failed exactly:** each of those builds lacked the pieces the plan added (Railway config, Python pin, Postgres driver, `DATABASE_URL` handling). Without the logs, it can't be confirmed which of them failed first.

## Fix

Merging `railway-postgres` into `main` (`7ca25e5`, 15:29 PDT) put the Railway config, the Postgres support and the Python pin on `main`, and the next deploy went live.

## Repeat check

- **2026-10-21:** every deploy since `7ca25e5` has succeeded or been replaced by a newer one. The live checks in the [migration plan's progress log](../superpowers/plans/2026-10-08-railway-postgres-migration.md#progress-log) pass (`/healthz` → `ok`, real profile served, valid certificate).

## Lesson

Connect a hosting service to a branch only once that branch can actually run there, or point the service at the feature branch until it merges. And save deploy logs on the day: Railway doesn't keep them.
