# Project 1 Submission

- **Live site:** https://ethanjad.me (`https://www.ethanjad.me` redirects there)
- **Repository:** https://github.com/ethanjad/career-platform
- **Final commit:** [`de5fc00eb413f0618be3ebd21c9e0a2a6d019c9d`](https://github.com/ethanjad/career-platform/commit/de5fc00eb413f0618be3ebd21c9e0a2a6d019c9d). Deployed to Railway as `c1e32d22-fa0a-4aae-a7fb-024f7c9ebd04` (`SUCCESS`, 2026-10-25 20:37 PDT). The only commit after it adds this line.
- **Engineering record:** [README.md](../README.md)

## The 8 required items

### 1. Profile and project data, with database failure behaviour

- [README: Database failure behaviour](../README.md#database-failure-behaviour). A database outage returns 503, keeps the profile visible and shows "Projects temporarily unavailable". An empty projects table shows a message.
- [README: Decisions → Starting with SQLite](../README.md#starting-with-sqlite)
- Evidence: [db-failure-503.md](evidence/db-failure-503.md), a dated database-down → 503 → recovery check.
- "This website, in progress" is a live project entry, added through `/admin/projects` on 2026-10-21.

### 2. Azure deployment

- [README: Azure VM](../README.md#azure-vm-2026-09-29-to-2026-10-08-deleted-2026-10-19): what made it survive restarts.
- [ex03.md](evidence/ex03.md): VM details, screenshot and troubleshooting.
- [azure-vm-retired.md](evidence/azure-vm-retired.md): the restart configuration, the final NSG rules, and the shutdown and deletion record. The reboot test was never run.
- [VM operations plan and progress log](superpowers/plans/2026-10-01-operate-the-vm.md)

### 3. Domain and HTTPS

- [dns-and-https.md](evidence/dns-and-https.md): all current DNS records and what each is for, the `www` → root redirect checks, and certificates.
- [dns-before-zoho.md](evidence/dns-before-zoho.md): the records before email was added.
- [how-this-site-is-secured.md](how-this-site-is-secured.md)

### 4. Railway and PostgreSQL migration

- [README: Moving from Azure to Railway and PostgreSQL](../README.md#moving-from-azure-to-railway-and-postgresql-2026-10-08): how the data was preserved, and the responsibility table.
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
