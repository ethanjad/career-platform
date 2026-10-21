# One change through Railway: HEAD requests

This page follows one change from the commit, through the Railway deployment, to what the live site does.

## The problem

While recording the www checks on 2026-10-21 ([dns-and-https.md](dns-and-https.md)), I found that `curl -sI https://ethanjad.me/` returned **405 Method Not Allowed**.

- **Why:** the app's routes accepted only GET, and `curl -I` sends HEAD.
- **Who it affects:** browsers use GET, so visitors weren't affected. Uptime monitors and link checkers often send HEAD, though, and they would report the site as broken.

## The change

- **Commit:** [`556fb8f3a0fead1d2013fd5da6c0a59e7b2a6b3a`](https://github.com/ethanjad/career-platform/commit/556fb8f3a0fead1d2013fd5da6c0a59e7b2a6b3a) "Answer HEAD requests on public routes"
- **Code:** `app/main.py` now registers `/`, `/privacy`, `/resume.pdf` and `/healthz` with `methods=["GET", "HEAD"]`.
- **Test first:** `test_public_routes_answer_head_requests_like_get` in `tests/test_health.py` failed with `assert 405 == 200` before the fix and passed after it. The full suite passed, 34/34.
- **Real-server check before pushing:** a local `uvicorn` returned `HTTP/1.1 200 OK` to `curl -sI` for all four routes, and its log had 0 errors.
- **Review:** the change was reviewed in a Claude Code session and approved by me before it was pushed to `main`. Pushing to `main` is what deploys.

## Before (live, 2026-10-21 01:47:06 PDT)

The active Railway deployment was `c9ca1fd5-2931-420e-847b-533febf4f2e7` (commit `37067f7`, `SUCCESS`).

```
HEAD /         -> 405
HEAD /healthz  -> 405
HEAD /privacy  -> 405
GET  /         -> 200
```

## Deployment

_Pending. Railway paused all builds during an incident on 2026-10-21. To be filled in once the deploy runs: the Railway deployment ID, its status and commit, and the time it went live._

## After (live)

_Pending, same commands as Before._
