# Project 1 Submission

- **Live site:** https://ethanjad.me (`https://www.ethanjad.me` redirects there)
- **Repository:** https://github.com/ethanjad/career-platform
- **Final commit (submitted):** [`5252820944f182c74acdee1166ba404e3037b804`](https://github.com/ethanjad/career-platform/commit/5252820944f182c74acdee1166ba404e3037b804). Deployed to Railway as `e8cb7374-8958-4359-81da-940c6625a9d1` (`SUCCESS`, 2026-10-25 21:02 PDT). The only commit after it writes this line and the status in `TASKS.md`. It can't contain its own SHA.
- **Engineering record:** [README.md](../README.md)
- **History:** [commit history](https://github.com/ethanjad/career-platform/commits/main), and the dated plans with progress logs in [`docs/superpowers/plans/`](superpowers/plans/) (Azure VM, VM operations, Railway migration). [`TASKS.md`](../TASKS.md) is the gap checklist used to finish the project.

## Checked before submitting (2026-10-25 21:02 PDT, logged out of GitHub)

- **Repository:** the repository and the commit page open publicly (HTTP 200).
- **Evidence files:** all 19 linked files and folders exist on GitHub at the submitted commit, and the commit history page opens.
- **Live site:** `https://ethanjad.me/`, `http://ethanjad.me/`, `https://www.ethanjad.me/` and `http://www.ethanjad.me/` all end at `https://ethanjad.me/` with HTTP 200 and a valid certificate.
- **Same version:** the live deployment's app code is identical to the submitted commit. The app code hasn't changed since commit `556fb8f`.

## What I could not verify

| Item | Why | Where it's recorded |
|---|---|---|
| A reboot test of the Azure VM | Never run before the VM was deleted on 2026-10-19 | [azure-vm-retired.md](evidence/azure-vm-retired.md) |
| The exact error behind the Oct 8 Railway deploy failures | Railway's build logs had expired by Oct 21. Cause inferred from the repository state. | [railway-deploy-failures.md](evidence/railway-deploy-failures.md) |
| The `copy_database` output and the post-cutover checks on Oct 8 itself | Not saved on the day. The data was compared row by row on Oct 25, and the checks were re-run on Oct 21. | [migration plan, progress log](superpowers/plans/2026-10-08-railway-postgres-migration.md#progress-log) |
| TLS and SPF/DKIM/DMARC results for mail *into* Zoho (Gmail → Zoho) | Only the sender's copy was available. The Zoho → Gmail direction is fully verified. | [zoho-header-check.md](evidence/zoho-header-check.md) |
| Microsoft's individual retry attempts for the message sent before MX existed | Microsoft's queue isn't visible. Send and arrival times are recorded. | [ex06.md §1](evidence/ex06.md) |
| That GA4 received the hits from the Oct 22 browser capture | Sending was blocked on purpose. GA4 receipt is shown by the Oct 18 Realtime screenshots instead. That GA4 doesn't store IPs is Google's claim. | [ex06.md §3](evidence/ex06.md#3-live-site-and-google-analytics) |
| Railway region for the current deploy, and the Postgres private port | Region `sfo` comes from the Oct 8 deployment manifests. The port isn't exposed in any record. | [request-path.md](request-path.md) |
| The README's database backup/restore steps through a temporary TCP proxy | Not run since Railway removed the public proxy. A read-only `railway ssh` check was run instead. | [README: Rollback](../README.md#rollback) |
| The origin of one `127.0.0.1` database session after the password rotation | It comes from inside the Postgres container, most likely Railway's own tooling | [postgres-credential-rotation.md](evidence/postgres-credential-rotation.md) |

## The 8 required items

### 1. Profile and project data, with database failure behaviour

- [README: Database failure behaviour](../README.md#database-failure-behaviour). A database outage returns 503, keeps the profile visible and shows "Projects temporarily unavailable". An empty projects table shows a message.
- [README: Decisions → Starting with SQLite](../README.md#starting-with-sqlite)
- Evidence: [db-failure-503.md](evidence/db-failure-503.md), a dated database-down → 503 → recovery check.
- "This website, in progress" is a live project entry, added through `/admin/projects` on 2026-10-21.

### 2. Azure deployment

- [README: Azure VM](../README.md#azure-vm-2026-09-29-to-2026-10-08-deleted-2026-10-19): what made it survive restarts, plus **SSH and network rules** (key-only SSH, NSG ports, why 8000 stayed closed).
- [ex03.md](evidence/ex03.md): VM details, screenshot and troubleshooting.
- [azure-vm-retired.md](evidence/azure-vm-retired.md): the restart configuration, the final NSG rules, and the shutdown and deletion record. The reboot test was never run.
- [VM operations plan and progress log](superpowers/plans/2026-10-01-operate-the-vm.md)

### 3. Domain and HTTPS

- [dns-and-https.md](evidence/dns-and-https.md): **domain control** (whois, registrar lock, nameserver delegation to Cloudflare), all current DNS records and what each is for, the `www` → root redirect checks, and certificates.
- [dns-before-zoho.md](evidence/dns-before-zoho.md): the records before email was added.
- [how-this-site-is-secured.md](how-this-site-is-secured.md)

### 4. Railway and PostgreSQL migration

- [README: Moving from Azure to Railway and PostgreSQL](../README.md#moving-from-azure-to-railway-and-postgresql-2026-10-08): the **dependency inventory**, database compatibility, how the data was preserved, and the responsibility table.
- [postgres-credential-rotation.md](evidence/postgres-credential-rotation.md): the Postgres password rotated after Railway's 2026-10-21 security incident (timeline, downtime, before/after audit).
- [README: Rollback](../README.md#rollback): code, database, and leaving Railway while keeping data written after cutover.
- [Migration plan and progress log](superpowers/plans/2026-10-08-railway-postgres-migration.md): the export, the cutover timeline and the post-cutover checks. There was no separate spec; the plan was written from the request and the findings at its top.

### 5. A reviewed change through Railway

- [reviewed-change-head.md](evidence/reviewed-change-head.md): HEAD requests returned 405 and now return 200. It traces commit → Railway deployment → behaviour at ethanjad.me.

### 6. Zoho email

- [ex06.md §1–2](evidence/ex06.md): the send/receive tests, what happened to a message sent before the MX records existed, and the MX, SPF, DKIM and DMARC records explained.
- [zoho-header-check.md](evidence/zoho-header-check.md): a hop-by-hop header analysis. SPF, DKIM and DMARC all pass.

### 7. Google Analytics 4

- [ex06.md §3](evidence/ex06.md#3-live-site-and-google-analytics): Realtime screenshots, how a browser event reaches GA4 (with a captured `page_view` and outbound `click`), why the outbound click matters, and what the checks prove.

### 8. Engineering record (README)

| Part | Where |
|---|---|
| Live address and how to update the site | [Updating the live site](../README.md#updating-the-live-site) |
| Diagrams: locations, protocols, ports, data flow, email and analytics | [Architecture](../README.md#architecture) · [request-path.md](request-path.md) · [azure-architecture.md](azure-architecture.md) |
| How the migration preserved data, and which responsibilities moved | [Moving from Azure to Railway](../README.md#moving-from-azure-to-railway-and-postgresql-2026-10-08) |
| Decisions with alternatives | [Decisions](../README.md#decisions): SQLite, the move to Railway, and Zoho vs self-hosted email |
| An app/database failure | [Failures and fixes §1](../README.md#failures-and-fixes) · [railway-deploy-failures.md](evidence/railway-deploy-failures.md). Also ex03's VM story (§2). |
| DNS/TLS failure (**simulation**) | [Failures and fixes §3](../README.md#failures-and-fixes) · [ex05.md](evidence/ex05.md) |
| Reflection | [Reflection](../README.md#reflection) |
| Costs, trial end date, cleanup plan, limitations | [Costs, cleanup and limitations](../README.md#costs-cleanup-and-limitations) |
