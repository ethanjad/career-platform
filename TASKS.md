# Project 1 gaps

Audit of 2026-10-20 against the Project 1 requirements. Each line names the file or check that closes it.

## Resume here (left 2026-10-21 ~01:55 PDT)

Railway was mid-incident: builds paused ("Builds are temporarily paused") and the Postgres public proxy failing TLS. First check that both are back:

- `curl -s https://status.railway.com/ | grep -i paused` prints nothing.
- A `psycopg.connect($RAILWAY_DATABASE_URL)` succeeds.

Then:

1. `git push origin main`, then `railway redeploy --from-source -y` if no deploy starts within a minute. Confirm `SUCCESS` for the tip of `main`, then check live:
   - `/` returns 200 with the real profile
   - `HEAD /` returns 200
2. Fill in the Deployment and After sections of `docs/evidence/reviewed-change-head.md`, then tick section 5.
3. Run the source-vs-target comparison (the export `~/Desktop/github/resume.db.bak-railway-20261008-214832` against live Postgres, read-only). Add it to the migration plan's progress log, then tick the last two section 4 items.
4. Continue with sections 6, 7, 8 and Other. Section 8: keep ex03 **and** add `docs/evidence/railway-deploy-failures.md`.

## 1. Profile and project data

- [x] DB failure returns 503 and shows "Projects temporarily unavailable" with the profile still visible, not the snapshot — `app/main.py`, `app/database.py`, `templates/index.html`, test in `tests/test_public_profile.py`
  - **Done 2026-10-21:** `/` answers 503 with the snapshot profile and "Projects temporarily unavailable" (no snapshot projects). 2 new tests, 33/33 pass on SQLite and PostgreSQL.
- [x] Remove the invented "Alex Carter" content from the tracked snapshot and default/seed data — `data/profile_snapshot.json`, `app/database.py`
  - **Done 2026-10-21:** default, seed and snapshot now hold the live ethanjad.me content. A test guards against the placeholder strings.
- [x] Empty projects table shows a deliberate message instead of hiding the section — `templates/index.html`, test in `tests/test_public_profile.py`
  - **Done 2026-10-21:** section stays and says "No projects are listed right now." Test added.
- [x] Explain the initial database choice (SQLite) and why — README "Decisions" section
  - **Drafted 2026-10-21:** README "Decisions → Starting with SQLite". Reasons inferred from the repo; Ethan to confirm.
- [x] Add a clearly labeled "this website, in progress" project entry — live DB row via `/admin/projects`, checked with `curl https://ethanjad.me/`
  - **Done 2026-10-21 01:30 PDT:** `POST /admin/projects` → `{"ok":true}` 200. `curl https://ethanjad.me/` shows "ethanjad.me (this website, in progress)".
- [x] Record a dated DB-down → 503 → recovery-on-refresh check — new evidence file linked from `docs/project-1-submission.md`
  - **Done 2026-10-21 (local PostgreSQL):** `docs/evidence/db-failure-503.md`, linked from the submission index.
- [x] Rewrite the README "Database fallback" section to match the new behaviour — `README.md`
  - **Done 2026-10-21:** now "Database failure behaviour".

## 2. Azure deployment

- [x] Run and record a controlled VM restart (site responds, reads DB, services come back) — `docs/superpowers/plans/2026-10-01-operate-the-vm.md` progress log
  - **Closed 2026-10-21 without a run:** the VM was deleted on 2026-10-19 before the test. Recorded honestly in `docs/evidence/azure-vm-retired.md` and the VM plan progress log.
- [x] Explain which configuration made the restart work (systemd enable, nginx, `--env-file`) — README Azure section
  - **Done 2026-10-21:** README "Azure VM" section, with the full table in `azure-vm-retired.md`.
- [x] Tighten `Allow-SSH-Laptop` (VM's own IP and old IP) and record the final NSG rules — `az network nsg rule list` output in the VM plan
  - **Closed 2026-10-21:** the NSG was deleted 2026-10-19, so the rule can no longer be tightened. The final rules (last recorded 2026-10-08) are in `azure-vm-retired.md`, which notes it was never tightened.
- [x] Confirm the VM is running and keep it running, then fix "The VM is turned off" — `az vm get-instance-view`, `docs/how-this-site-is-secured.md`
  - **Closed 2026-10-21 (you chose not to rebuild):** the VM was auto-shutdown 2026-10-14 and deleted 2026-10-19. "Turned off" now says deleted, linking the record.

## 3. Domain and HTTPS

- [x] Record the current DNS records with what each one is for — dated `cf dns records list` output in a tracked evidence file
  - **Done 2026-10-21:** `docs/evidence/dns-and-https.md`: all 10 records, with a purpose table and a public-DNS cross-check.
- [x] Commit the DNS-before-Zoho snapshot — `docs/evidence/dns-before-zoho.md`
  - **Done 2026-10-21:** committed, with the old VM IP redacted and a note on the later www change.
- [x] Verify `http://www.ethanjad.me` and `https://www.ethanjad.me` both land on the root with a valid certificate — dated `curl -sI` output in evidence
  - **Done 2026-10-21 01:36 PDT:** both → 301 → `https://ethanjad.me/` → 200, `ssl_verify_result=0`. Certificates recorded. Found: HEAD `/` returns 405 (GET-only routes).

## 4. Railway and PostgreSQL migration

- [ ] Record the export, copy counts, and the source-vs-target record, content and page comparison — progress log in `docs/superpowers/plans/2026-10-08-railway-postgres-migration.md`
  - **Partly done 2026-10-21:** export identified (VM copy, 21:48 UTC) and its counts are recorded in the plan's progress log. The source-vs-target comparison is waiting on the Railway Postgres public proxy (Railway incident).
- [ ] Show one real change to the original data that seed data couldn't reproduce — same progress log
  - **Partly done 2026-10-21:** the export's non-seed ids (experience 3–6, projects 5–6, link 7) and the "Class of 2027" headline are recorded. Confirming them in live Postgres is waiting on the same proxy.
- [x] Record the cutover and the post-cutover checks (Task 7 Step 5 results) — same progress log
  - **Done 2026-10-21:** cutover timeline rebuilt from Railway, Cloudflare and certificate timestamps. Step 5 wasn't recorded on the day, so it was re-run today and the output logged. Both are noted honestly in the plan.
- [x] Rollback procedure that handles data written after cutover — README rollback section
  - **Done 2026-10-21:** README "Rollback": export from Postgres at rollback time. The round trip was tested locally, and a row written after the copy came back with its id.
- [x] Azure vs Railway responsibility comparison (OS, runtime, entry point, TLS, code, config, DB software, data, DNS) — README
  - **Done 2026-10-21:** README table covering 11 layers.
- [x] Mark the "No separate spec" gap honestly, or link the spec — README and `docs/project-1-submission.md`
  - **Done 2026-10-21:** stated in the README migration section and the submission index.
- [x] Link the migration plan from the README and the submission index — `README.md`, `docs/project-1-submission.md`
  - **Done 2026-10-21.**

## 5. Reviewed change through Railway

- [ ] Record one change: commit SHA → Railway deployment ID → behaviour seen at ethanjad.me — evidence file linked from the submission index
- [x] Rollback for code and database changes — README rollback section
  - **Done 2026-10-21:** README "Rollback → Code / Database" (revert + push, dashboard redeploy, `copy_database` backup/restore).

## 6. Zoho email

- [ ] Create the Zoho header analysis — `docs/evidence/zoho-header-check.md`
- [ ] Add the before-MX message line and what happened to it — `docs/evidence/ex06.md`
- [ ] Record and explain the MX, SPF, DKIM and DMARC records — dated DNS output plus an explanation in `docs/evidence/ex06.md` or the README
- [ ] Link ex06 and the header check from the README and submission index — `README.md`, `docs/project-1-submission.md`

## 7. GA4

- [ ] Explain how a browser event reaches GA4, why the outbound click is useful, and what the checks prove — `docs/evidence/ex06.md` section 3

## 8. Engineering record

- [ ] README: live address and how to update the site — `README.md`
- [ ] README: Azure and Railway diagrams with locations, protocols, ports, data flow, email and analytics paths — `README.md` or a linked diagram file
- [ ] README: how the migration preserved data and which responsibilities moved — `README.md`
- [ ] README: two decisions with alternatives (Railway migration, managed vs self-hosted email) — `README.md`
- [ ] README: an app/DB failure with symptom, checks, diagnosis, fix and repeat check (ex03's is a sizing story, so consider a Railway migration failure) — `README.md` linking the record
  - **Decided 2026-10-21:** keep ex03 and add the Oct 8 Railway deploy failures (with their logs) alongside it. Both are included.
- [ ] README: link the DNS/TLS failure, labeled as a simulation — `README.md` linking `docs/evidence/ex05.md`
- [ ] README: reflection — `README.md`
- [ ] README: service costs or credits, Railway trial end date, cleanup plan, remaining limitations — `README.md`
- [ ] Submission index: repo URL, live URL, final commit SHA, and links for all 8 required items — `docs/project-1-submission.md`

## Other

- [ ] Redact the VM and laptop IPs from the public repo — `docs/superpowers/plans/2026-10-01-operate-the-vm.md`
- [ ] Commit or ignore the untracked review screenshots — `.impeccable/review/`
