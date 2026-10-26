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

Railway paused all builds during an outage and security incident on 2026-10-21–22, so the push waited until builds were back.

- **Pushed:** `git push origin main` on 2026-10-25 at about 20:29 PDT. That put the 18 commits up to `390ef02` on `main`.
- **Railway deployment:** `44a560db-9fd2-47b0-a82b-3a0fee098f31`, triggered by the push.
  - Created 2026-10-26 03:29:50 UTC (20:29:50 PDT) from commit `390ef0271f72d33385fc4580a34eb3aab00d49eb`.
  - Status `SUCCESS` at 20:31:58 PDT, after the `/healthz` check passed.
  - The previous deployment `c9ca1fd5…` changed to `REMOVED`.
- **Contains the fix:** Railway deploys the tip of `main`, so the deployed commit is `390ef02`, not `556fb8f` itself. `git merge-base --is-ancestor 556fb8f 390ef02` succeeds, so `390ef02` includes the fix. The other 15 commits in between change documentation and the 503 behaviour, not routing.
- **Container start:** the new container logged `Application startup complete` at 03:31:41 UTC.

## After (live, 2026-10-25 20:32:09 PDT)

```
HEAD /         -> 200
HEAD /healthz  -> 200
HEAD /privacy  -> 200
GET  /         -> 200
GET  /healthz  -> ok
```

The new deployment's own log shows it served these requests (client IP removed):

```
2026-10-26T03:32:11Z INFO:     … - "HEAD / HTTP/1.1" 200 OK
2026-10-26T03:32:11Z INFO:     … - "HEAD /healthz HTTP/1.1" 200 OK
2026-10-26T03:32:11Z INFO:     … - "HEAD /privacy HTTP/1.1" 200 OK
```

**Result:** at ethanjad.me, `HEAD /` changed from **405** (deployment `c9ca1fd5`, commit `37067f7`) to **200** (deployment `44a560db`, commit `390ef02`, which contains `556fb8f`). `GET` behaviour is unchanged.

## Rollback

If this change had broken the site, either of these would undo it:

- **Revert and push:** `git revert 556fb8f` and push. Railway deploys that like any other change.
- **Redeploy the old build:** while the revert is prepared, redeploy `c9ca1fd5` from the Railway dashboard (Deployments → ⋯ → Redeploy).

No database change was involved. See README "Rollback".
