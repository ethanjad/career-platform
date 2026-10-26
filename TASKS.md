# Project 1 gaps

Audit of 2026-10-20 against the Project 1 requirements. Each line names the file or check that closes it.

## Status (2026-10-25)

All items done. Railway's 2026-10-21–22 outage held up the last deploy until 2026-10-25, when it went out as deployment `44a560db`. The final commit SHA is recorded in `docs/project-1-submission.md`.

**Still to decide:** the Railway trial ends about **2026-11-05**. Either move to a paid plan, or export the database and move the site before then.

## 1. Profile and project data

- [x] DB failure returns 503 and shows "Projects temporarily unavailable" with the profile still visible, not the snapshot — `app/main.py`, `app/database.py`, `templates/index.html`, test in `tests/test_public_profile.py`
  - **Done 2026-10-21:** `/` answers 503 with the snapshot profile and "Projects temporarily unavailable" (no snapshot projects). 2 new tests, 33/33 pass on SQLite and PostgreSQL.
- [x] Remove the invented "Alex Carter" content from the tracked snapshot and default/seed data — `data/profile_snapshot.json`, `app/database.py`
  - **Done 2026-10-21:** default, seed and snapshot now hold the live ethanjad.me content. A test guards against the placeholder strings.
- [x] Empty projects table shows a deliberate message instead of hiding the section — `templates/index.html`, test in `tests/test_public_profile.py`
  - **Done 2026-10-21:** section stays and says "No projects are listed right now." Test added.
- [x] Explain the initial database choice (SQLite) and why — README "Decisions" section
  - **Drafted 2026-10-21:** README "Decisions → Starting with SQLite". Reasons inferred from the repo; **confirmed by Ethan 2026-10-22.**
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

- [x] Record the export, copy counts, and the source-vs-target record, content and page comparison — progress log in `docs/superpowers/plans/2026-10-08-railway-postgres-migration.md`
  - **Done 2026-10-25:** row-by-row comparison read via `railway ssh` (read-only, private network; the public proxy is gone). Every exported row is present with the same id; unedited rows are identical. In the plan's progress log.
  - **Partly done 2026-10-21:** export identified (VM copy, 21:48 UTC) and its counts are recorded in the plan's progress log. The source-vs-target comparison is waiting on the Railway Postgres public proxy (Railway incident).
- [x] Show one real change to the original data that seed data couldn't reproduce — same progress log
  - **Done 2026-10-25:** non-seed ids and the headline confirmed live. Also recorded: projects 5–6 edited and 7–11 and link 8 added after cutover.
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

- [x] Record one change: commit SHA → Railway deployment ID → behaviour seen at ethanjad.me — evidence file linked from the submission index
  - **Done 2026-10-25:** `556fb8f` (in `390ef02`) → deployment `44a560db` SUCCESS → `HEAD /` 405 → 200 live. `docs/evidence/reviewed-change-head.md`.
- [x] Rollback for code and database changes — README rollback section
  - **Done 2026-10-21:** README "Rollback → Code / Database" (revert + push, dashboard redeploy, `copy_database` backup/restore).

## 6. Zoho email

- [x] Create the Zoho header analysis — `docs/evidence/zoho-header-check.md`
  - **Done 2026-10-22:** full received-copy headers (Zoho → Gmail), hop table, SPF/DKIM/DMARC with the records each used, ARC, and limits. Gmail address and home IPv6 redacted.
- [x] Add the before-MX message line and what happened to it — `docs/evidence/ex06.md`
  - **Done 2026-10-22:** sent 14:20 from the LMU account, MX created 14:36–14:37, mailbox 14:41:22, delivered 14:41:46. Delayed, not bounced. Timeline and explanation in `ex06.md` §1.
- [x] Record and explain the MX, SPF, DKIM and DMARC records — dated DNS output plus an explanation in `docs/evidence/ex06.md` or the README
  - **Done 2026-10-22:** `ex06.md` §2, "The DNS records behind these results": dated `dig` output, what each record does, how it maps to the header results, and an SPF include chain shown to cover the sending IP.
- [x] Link ex06 and the header check from the README and submission index — `README.md`, `docs/project-1-submission.md`
  - **Done 2026-10-22:** both linked from the README evidence list and the submission index.

## 7. GA4

- [x] Explain how a browser event reaches GA4, why the outbound click is useful, and what the checks prove — `docs/evidence/ex06.md` section 3
  - **Done 2026-10-22:** `ex06.md` §3 adds the 6-step path, a headless-Chrome capture of the real `page_view` and outbound `click` hits (answered locally, nothing sent), why the click is the site's conversion signal, and what the checks do and don't prove.

## 8. Engineering record

- [x] README: live address and how to update the site — `README.md`
  - **Done 2026-10-22:** "Live site" line and an "Updating the live site" section (code → push → healthz-gated deploy; content via the admin API; résumé PDF).
- [x] README: Azure and Railway diagrams with locations, protocols, ports, data flow, email and analytics paths — `README.md` or a linked diagram file
  - **Done 2026-10-22:** README "Architecture" ports table, plus `request-path.md` (Railway split into 3a web/analytics and 3b email) and `azure-architecture.md`. All 8 diagrams render (mermaid-cli), PNGs regenerated, VM IP redacted.
- [x] README: how the migration preserved data and which responsibilities moved — `README.md`
  - **Done 2026-10-21** in section 4 (README "Moving from Azure to Railway").
- [x] README: two decisions with alternatives (Railway migration, managed vs self-hosted email) — `README.md`
  - **Drafted 2026-10-22:** Railway migration and Zoho vs self-hosted email, each with an options table. The "Why" lines were inferred; **confirmed by Ethan 2026-10-22.**
- [x] README: an app/DB failure with symptom, checks, diagnosis, fix and repeat check (ex03's is a sizing story, so consider a Railway migration failure) — `README.md` linking the record
  - **Done 2026-10-22:** README "Failures and fixes": Railway deploy failures (full record) **and** ex03, both included as asked.
  - **Decided 2026-10-21:** keep ex03 and add the Oct 8 Railway deploy failures (with their logs) alongside it. Both are included.
- [x] README: link the DNS/TLS failure, labeled as a simulation — `README.md` linking `docs/evidence/ex05.md`
  - **Done 2026-10-22:** "Failures and fixes" §3, labeled simulation.
- [x] README: reflection — `README.md`
  - **Done 2026-10-22:** Ethan's own words, with typos fixed and split into paragraphs.
- [x] README: service costs or credits, Railway trial end date, cleanup plan, remaining limitations — `README.md`
  - **Partly done 2026-10-22:** Azure $5.00 of credit (Cost Management API), Railway $0.61, free tiers, domain expiry 2027-10-01, cleanup plan and limitations. Domain: $0 via the GitHub Student Pack (confirmed 2026-10-22). Railway trial: $4.34 left, 14 days on 2026-10-22, ending about 2026-11-05 (from Ethan, Railway dashboard).
- [x] Submission index: repo URL, live URL, final commit SHA, and links for all 8 required items — `docs/project-1-submission.md`
  - **Built 2026-10-22:** repo and live URLs, the 8 required items each with their evidence links, and the README part-by-part table. 51 links checked, 0 broken. Final SHA recorded 2026-10-25 after the last deploy.

## Other

- [x] Redact the VM and laptop IPs from the public repo — `docs/superpowers/plans/2026-10-01-operate-the-vm.md`
  - **Done 2026-10-22:** the VM plan now uses `<VM_PUBLIC_IP>` and dated `<LAPTOP_IP_…>` placeholders, with a note. Earlier this session: the diagrams and `dns-before-zoho.md`. **ex03.md keeps the VM IP by Ethan's choice** (submitted answer; the VM is deleted and its IP released). Older commits in git history still contain these IPs; history was not rewritten.
- [x] Commit or ignore the untracked review screenshots — `.impeccable/review/`
  - **Done 2026-10-22:** committed by Ethan's choice (Oct 19 design review; no private data, though the footer copy is now outdated).
