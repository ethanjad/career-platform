# Project 1 gaps

Audit of 2026-10-20 against the Project 1 requirements. Each line names the file or check that closes it.

## 1. Profile and project data

- [ ] DB failure returns 503 and shows "Projects temporarily unavailable" with the profile still visible, not the snapshot — `app/main.py`, `app/database.py`, `templates/index.html`, test in `tests/test_public_profile.py`
- [ ] Remove the invented "Alex Carter" content from the tracked snapshot and default/seed data — `data/profile_snapshot.json`, `app/database.py`
- [ ] Empty projects table shows a deliberate message instead of hiding the section — `templates/index.html`, test in `tests/test_public_profile.py`
- [ ] Explain the initial database choice (SQLite) and why — README "Decisions" section
- [ ] Add a clearly labeled "this website, in progress" project entry — live DB row via `/admin/projects`, checked with `curl https://ethanjad.me/`
- [ ] Record a dated DB-down → 503 → recovery-on-refresh check — new evidence file linked from `docs/project-1-submission.md`
- [ ] Rewrite the README "Database fallback" section to match the new behaviour — `README.md`

## 2. Azure deployment

- [ ] Run and record a controlled VM restart (site responds, reads DB, services come back) — `docs/superpowers/plans/2026-10-01-operate-the-vm.md` progress log
- [ ] Explain which configuration made the restart work (systemd enable, nginx, `--env-file`) — README Azure section
- [ ] Tighten `Allow-SSH-Laptop` (VM's own IP and old IP) and record the final NSG rules — `az network nsg rule list` output in the VM plan
- [ ] Confirm the VM is running and keep it running, then fix "The VM is turned off" — `az vm get-instance-view`, `docs/how-this-site-is-secured.md`

## 3. Domain and HTTPS

- [ ] Record the current DNS records with what each one is for — dated `cf dns records list` output in a tracked evidence file
- [ ] Commit the DNS-before-Zoho snapshot — `docs/evidence/dns-before-zoho.md`
- [ ] Verify `http://www.ethanjad.me` and `https://www.ethanjad.me` both land on the root with a valid certificate — dated `curl -sI` output in evidence

## 4. Railway and PostgreSQL migration

- [ ] Record the export, copy counts, and the source-vs-target record, content and page comparison — progress log in `docs/superpowers/plans/2026-10-08-railway-postgres-migration.md`
- [ ] Show one real change to the original data that seed data couldn't reproduce — same progress log
- [ ] Record the cutover and the post-cutover checks (Task 7 Step 5 results) — same progress log
- [ ] Rollback procedure that handles data written after cutover — README rollback section
- [ ] Azure vs Railway responsibility comparison (OS, runtime, entry point, TLS, code, config, DB software, data, DNS) — README
- [ ] Mark the "No separate spec" gap honestly, or link the spec — README and `docs/project-1-submission.md`
- [ ] Link the migration plan from the README and the submission index — `README.md`, `docs/project-1-submission.md`

## 5. Reviewed change through Railway

- [ ] Record one change: commit SHA → Railway deployment ID → behaviour seen at ethanjad.me — evidence file linked from the submission index
- [ ] Rollback for code and database changes — README rollback section

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
- [ ] README: link the DNS/TLS failure, labeled as a simulation — `README.md` linking `docs/evidence/ex05.md`
- [ ] README: reflection — `README.md`
- [ ] README: service costs or credits, Railway trial end date, cleanup plan, remaining limitations — `README.md`
- [ ] Submission index: repo URL, live URL, final commit SHA, and links for all 8 required items — `docs/project-1-submission.md`

## Other

- [ ] Redact the VM and laptop IPs from the public repo — `docs/superpowers/plans/2026-10-01-operate-the-vm.md`
- [ ] Commit or ignore the untracked review screenshots — `.impeccable/review/`
