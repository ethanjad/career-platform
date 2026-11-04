# Move to AWS EC2 and RDS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status (2026-11-03):** planning only. Nothing in this plan has been run and no AWS resources exist.

**Goal:** `https://ethanjad.me` is served from one EC2 instance and a Single-AZ RDS PostgreSQL database, with the same content as Railway, by about 2026-11-04.

**Architecture:** nginx on EC2 ends HTTPS and passes requests to one uvicorn process on `127.0.0.1:8000`, run by systemd. The app reaches a private RDS instance over verified TLS, using `DATABASE_URL`. Data moves as a `pg_dump` from Railway, restored from the laptop through an SSH tunnel. DNS stays in Cloudflare, and only the apex record changes.

**Tech Stack:** AWS CLI (profile `isba-4775`, `us-east-1`), EC2 `t3.micro`, Ubuntu 24.04 x86_64, RDS PostgreSQL 18.6 on `db.t4g.micro`, nginx, systemd, certbot with the Cloudflare DNS plugin, uv, FastAPI.

**Spec:** the 2026-11-03 decisions below. There is no separate design document.

## Decisions

| Decision | Choice | Decided by |
|---|---|---|
| Hosting | EC2 and Single-AZ RDS PostgreSQL | Owner |
| Railway | No paid month. Cut over before the trial ends about 2026-11-05 | Owner |
| RDS permission | The account is the owner's. Prove it by creating the real instance (Task 2) | Owner |
| HTTPS certificate | certbot with Cloudflare DNS validation, issued before DNS moves | Owner |
| Work happens on | Branch `aws-migration`, not `main`, so Railway doesn't redeploy | Owner |
| Instance size | `t3.micro` (1 GiB, same as the Azure VM) | Assumed, not yet confirmed |
| Server access | SSH with a new key, port 22 from the laptop's IP only | Assumed, not yet confirmed |
| Deploys | Manual script with a health check and automatic rollback | Assumed, not yet confirmed |
| Backups | 7 days of RDS backups, deletion protection on, final snapshot on delete | Owner, 2026-11-03 |
| AWS account plan | Upgrade from Free to Paid before creating RDS, so 7-day backups are allowed | Owner, 2026-11-03 |

## Facts checked on 2026-11-03

Read-only calls and `--dry-run` launches only.

- **Launch limits:** policy `ISBA4775EC2Migration` denies launching anything except `t3.micro` and `t3.small`. A `t3.micro` launch with a 20 GB encrypted gp3 disk and IMDSv2 required passes a dry run in `us-east-1`.
- **Other EC2 dry runs that pass:** security group, key import, Elastic IP allocate and associate.
- **RDS:** 18.6 is available and can be ordered on `db.t4g.micro` with gp3 storage. `rds.force_ssl` defaults to `1`. **`CreateDBInstance` is untested**, because RDS has no dry run.
- **`isba-student` can't use:** IAM reads, Budgets, Cost Explorer, Secrets Manager, SNS, CloudWatch Logs.
- **Network:** a default VPC with a default subnet in each of 6 availability zones. `t3.micro` isn't offered in `us-east-1e`.
- **DNS:** apex `A` answer has a 60-second TTL. No CAA records. MX and SPF point at Zoho.
- **App:** 34 tests pass on this branch. The app doesn't read `.env` or `HOST`, so `start.sh` isn't used on EC2.

Estimated cost from AWS's public us-east-1 price files, checked 2026-11-03, at 730 hours a month: **$26.82/mo** (EC2 $7.59, EC2 disk $1.60, public IPv4 $3.65, RDS $11.68, RDS storage $2.30), assuming backups and data transfer stay inside their free allowances. Credits aren't included. Check it against the first bill.

## Global Constraints

- **Do not create AWS resources, change DNS, or push until the owner says to run this plan.** Tasks 2 and 6 each need their own explicit go-ahead.
- Never commit to or push `main` before Task 7. Pushing `main` deploys to Railway.
- This repo is public. Keep the AWS account ID, public IPs, RDS endpoint and secrets out of it. Use placeholders such as `<EIP>`, `<RDS_ENDPOINT>` and `<LAPTOP_IP>`, including in the Progress log.
- Never publish the owner's phone number or home address.
- Every AWS CLI call uses `--profile isba-4775 --region us-east-1`. Commands below leave this out, so set `export AWS_PROFILE=isba-4775 AWS_REGION=us-east-1` first.
- **Owner's rules, 2026-11-04:** one phase at a time; Railway stays running and DNS stays unchanged until the owner says otherwise; restore from EC2 into an empty database; `pg_restore` at least as new as Railway's PostgreSQL; no Azure deploy script or seed script on AWS; no secrets in Git.
- Never put secrets in EC2 user data or in shell commands that print them.
- Make no admin edits (`/admin/*`) from Task 6 Step 1 until Task 7 Step 1 is complete.
- Tick steps and add dated results to the Progress log as they run.
- **Where it runs:** **Laptop** is the Mac terminal. **Server** is `ssh career-aws`. **Console** is a browser step only the owner can do.

## Review Focus

1. **`DATABASE_URL` missing or unread.** The app silently uses SQLite with seed data, and `/healthz` still says `ok`. A visitor should never see seed content. Checked in Task 1 (startup guard) and Task 5 Step 5.
2. **`ADMIN_SECRET` missing.** It falls back to `change-me`, so anyone could edit the site. This happened on Railway until 2026-10-19. Checked in Task 1 (startup guard) and Task 5 Step 5.
3. **App connects to an empty database.** It seeds default rows. Real data must already be restored, so the restore in Task 4 comes before the first app start in Task 5.
4. **Missing forwarded headers.** Asset links come out as `http://` and the page loses its styling on HTTPS. Checked in Task 5 Step 5.
5. **Cutover touches other DNS records.** Email breaks if MX or SPF change, and `www` breaks if its proxied record changes. Checked in Task 6 Steps 2 and 6.

---

### Task 0: Before anything exists (owner)

**Files:** none

- [ ] **Step 1 (Console): Set a spending alert.** Sign in with an account that has billing access, then create a monthly AWS Budget of $30 with an email alert at 80%. `isba-student` can't do this.
- [ ] **Step 2: Confirm the interview date.** The cutover must not fall on the interview day. If the interview is on or before 2026-11-05, decide with the owner whether to cut over before or after it. Record the choice in the Progress log.
- [ ] **Step 3: Confirm the three "assumed" rows in Decisions,** and change them here if needed.
- [ ] **Step 4 (Console): Create a Cloudflare API token.** Permission: Zone → DNS → Edit, limited to zone `ethanjad.me`. Keep it in a password manager for Task 5.
- [ ] **Step 5 (Console): Write down the current apex record** from the Cloudflare dashboard: type, value, proxy status and TTL. DNS answers with an IP, but the stored record may be a CNAME. Task 6's rollback needs the stored record, so keep it privately.

---

### Task 1: Deploy files in the repo

**Files:**
- Create: `deploy/career-platform.service`
- Create: `deploy/nginx-career-platform.conf`
- Create: `deploy/deploy.sh`
- Create: `deploy/dump-railway.sh`
- Create: `deploy/compare-database.sql`
- Create: `tests/test_deploy_config.py`
- Modify: `tests/test_config.py`
- Modify: `templates/privacy.html:21`, `templates/privacy.html:51`

**Interfaces:**
- Produces: service `career-platform` running as user `career` from `/opt/career-platform`. Env file `/etc/career-platform/env`. Snapshot at `/var/lib/career-platform/profile_snapshot.json`.
- Produces: `deploy/deploy.sh <git-ref>`, `deploy/dump-railway.sh <output-file>`, and `deploy/compare-database.sql`, whose output is `table|count|md5`, then sequences, then the constraint count.

- [x] **Step 1: Write the failing tests**

In `tests/test_config.py`:

```python
def test_rds_tls_settings_survive_url_normalization():
    url = "postgresql://u:p@host:5432/db?sslmode=verify-full&sslrootcert=/etc/ca.pem"
    assert normalize_database_url(url) == (
        "postgresql+psycopg://u:p@host:5432/db?sslmode=verify-full&sslrootcert=/etc/ca.pem"
    )
```

In `tests/test_deploy_config.py`, with `DEPLOY = Path(__file__).resolve().parents[1] / "deploy"` and FastAPI's `TestClient`:

```python
def test_service_binds_loopback_with_one_worker_and_reads_the_env_file():
    unit = (DEPLOY / "career-platform.service").read_text()
    assert "--host 127.0.0.1 --port 8000" in unit
    assert "EnvironmentFile=/etc/career-platform/env" in unit
    assert "--workers" not in unit and "start.sh" not in unit

def test_service_refuses_to_start_without_required_secrets():
    unit = (DEPLOY / "career-platform.service").read_text()
    assert 'test -n "$$DATABASE_URL"' in unit and 'test -n "$$ADMIN_SECRET"' in unit

def test_nginx_forwards_scheme_and_redirects_http():
    conf = (DEPLOY / "nginx-career-platform.conf").read_text()
    assert "X-Forwarded-Proto $scheme" in conf
    assert "proxy_pass http://127.0.0.1:8000" in conf
    assert "return 301 https://ethanjad.me$request_uri" in conf

def test_nginx_rejects_unknown_hosts():
    conf = (DEPLOY / "nginx-career-platform.conf").read_text()
    assert "return 444" in conf and "ssl_reject_handshake on" in conf

def test_privacy_page_names_aws_not_railway():
    page = TestClient(app).get("/privacy").text
    assert "Amazon Web Services" in page and "Railway" not in page
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_deploy_config.py tests/test_config.py -q`
Expected: the `test_deploy_config.py` tests FAIL because `deploy/` and the privacy text don't exist. The new `test_config.py` test should already PASS, which pins existing behaviour.

- [x] **Step 3: Write `deploy/career-platform.service`**

`User=career`, `WorkingDirectory=/opt/career-platform`, `EnvironmentFile=/etc/career-platform/env`, `StateDirectory=career-platform`, `Restart=always`, `NoNewPrivileges=true`, `PrivateTmp=true`, `ProtectSystem=strict`, `After=network-online.target`, `WantedBy=multi-user.target`.

```ini
ExecStartPre=/bin/sh -c 'test -n "$$DATABASE_URL" && test -n "$$ADMIN_SECRET"'
ExecStart=/opt/career-platform/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips 127.0.0.1
```

Use one worker. `write_profile_snapshot` isn't atomic, and a partly written file makes `read_profile_snapshot` fall back to defaults.

- [x] **Step 4: Write `deploy/nginx-career-platform.conf`**

Four server blocks:
- Port 80 `default_server`: `return 444`.
- Port 80 `ethanjad.me`: `return 301 https://ethanjad.me$request_uri`.
- Port 443 `default_server`: `ssl_reject_handshake on`.
- Port 443 `ethanjad.me`: certificate from `/etc/letsencrypt/live/ethanjad.me/`, `ssl_protocols TLSv1.2 TLSv1.3`, `proxy_pass http://127.0.0.1:8000`, and `Host`, `X-Forwarded-For` and `X-Forwarded-Proto $scheme` headers.

`www` stays on Cloudflare and isn't configured here.

- [x] **Step 5: Write `deploy/deploy.sh <git-ref>`**

Runs on the server from `/opt/career-platform`. Use `set -euo pipefail`. Record the current commit, `git fetch --prune origin`, `git checkout --detach origin/<ref>`, `uv sync --locked`, `sudo systemctl restart career-platform`, then poll `http://127.0.0.1:8000/healthz` for up to 30 seconds. If it never returns `200`, check out the recorded commit, sync, restart and exit 1.

- [x] **Step 6: Write `deploy/dump-railway.sh <output-file>`**

The method proven on 2026-10-29. It needs no public proxy. It streams base64 so SSH can't corrupt the file, fails if either checksum differs, and sets the file to mode `600`.

```bash
railway ssh --service Postgres -- 'f=/tmp/bk.dump; pg_dump -U "$PGUSER" -d "$PGDATABASE" -Fc --no-owner --no-privileges -f $f && echo "SHA $(sha256sum $f | cut -d" " -f1)" && echo BEGIN && base64 -w0 $f && echo && echo END && rm -f $f' 2>/dev/null > "$raw"
# Remote sha = the SHA line. File = the lines between BEGIN and END, with \r and \n removed, then base64 -d.
```

- [x] **Step 7: Write `deploy/compare-database.sql`**

Based on the 2026-10-29 query, with `COLLATE "C"` so row order can't differ between servers:

```sql
\pset tuples_only on
\pset format unaligned
select t,
  (xpath('/row/c/text()', query_to_xml(format('select count(*) c from public.%I', t), false, true, '')))[1]::text,
  (xpath('/row/h/text()', query_to_xml(format('select md5(coalesce(string_agg(x::text, ''|'' order by x::text collate "C"), '''')) h from public.%I x', t), false, true, '')))[1]::text
from unnest(array['education','experience','links','profile','projects','settings','skills']) t order by t;
select 'seq', sequencename, last_value from pg_sequences where schemaname='public' order by 2;
select 'constraints', count(*) from pg_constraint c join pg_namespace n on n.oid=c.connamespace where n.nspname='public';
```

- [x] **Step 8: Update the privacy page**

In `templates/privacy.html`, change the date on line 21 to the actual cutover date, and replace line 51 with:

```html
<li><strong>Amazon Web Services (AWS)</strong> hosts the site and its database. The site's server keeps technical logs of requests, such as the IP address, the page requested and the time, for about 14 days. I only look at these to fix problems with the site.</li>
```

Task 3 Step 5 confirms the 14 days. If the server's setting differs, correct this text.

- [x] **Step 9: Run all the tests**

Run: `uv run pytest -q`
Expected: all pass, with the 34 existing tests and the new ones. Also run `bash -n deploy/deploy.sh deploy/dump-railway.sh` and expect no output.

- [x] **Step 10: Commit to the branch**

```bash
git add deploy tests/test_deploy_config.py tests/test_config.py templates/privacy.html
git commit -m "feat: add EC2 service, nginx config and migration scripts"
```

Railway keeps serving its own privacy text, because this change isn't on `main`.

---

### Task 2: Security groups and RDS (billing starts here)

**Needs the owner's go-ahead.** The RDS instance costs money from the moment it exists.

**Files:** none

**Interfaces:**
- Produces: security groups `career-web-sg` and `career-db-sg`, RDS instance `career-platform-db`, database `career_platform`, master user `career_admin`, and `<RDS_ENDPOINT>`.
- Produces: `~/.config/career-platform/aws.env` on the laptop (mode `600`) holding `MASTER_PW` and `APP_PW`, each from `openssl rand -hex 32`. Hex needs no URL-encoding. Also save both in a password manager.

- [x] **Step 1 (Laptop): Generate the passwords** into `aws.env`, without printing them.

- [x] **Step 2 (Laptop): Create the security groups** in the default VPC.
  - `career-web-sg`: TCP 80 and 443 from `0.0.0.0/0`, TCP 22 from `<LAPTOP_IP>/32` (`curl -s https://checkip.amazonaws.com`).
  - `career-db-sg`: TCP 5432 with `career-web-sg` as the source, and no other inbound rule.

  Expected: `describe-security-groups` shows exactly these rules, and nothing allows 5432 from a CIDR.

- [x] **Step 3 (Laptop): Create the DB subnet group** `career-platform-db-subnets` from the default subnets in `us-east-1a` and `us-east-1b`. Find them with `describe-subnets --filters Name=default-for-az,Values=true`.

- [x] **Step 4 (Laptop): Create the instance.** This is the permission test.

```bash
aws rds create-db-instance \
  --db-instance-identifier career-platform-db --db-name career_platform \
  --engine postgres --engine-version 18.6 --db-instance-class db.t4g.micro \
  --storage-type gp3 --allocated-storage 20 --storage-encrypted \
  --no-multi-az --availability-zone us-east-1a --no-publicly-accessible \
  --db-subnet-group-name career-platform-db-subnets --vpc-security-group-ids <DB_SG_ID> \
  --master-username career_admin --master-user-password "$MASTER_PW" \
  --backup-retention-period 7 --preferred-backup-window 08:00-08:30 \
  --preferred-maintenance-window sun:09:00-sun:09:30 \
  --auto-minor-version-upgrade --deletion-protection --copy-tags-to-snapshot \
  --monitoring-interval 0 --no-enable-performance-insights
```

First attempt (2026-11-03) failed with `FreeTierRestrictionError`: the Free account plan doesn't allow 7-day backup retention. The owner chose to upgrade to the Paid plan first, then retry with this exact command.

If this returns `AccessDenied`, stop and add the permission as the account owner. If `db.t4g.micro` is denied, try `db.t3.micro`, which is also orderable on 18.6. Note the price change and record it in the Progress log.

- [ ] **Step 5 (Laptop): Wait and check.**

Run: `aws rds wait db-instance-available --db-instance-identifier career-platform-db`, then `describe-db-instances`.
Expected: `PubliclyAccessible=false`, `MultiAZ=false`, `StorageEncrypted=true`, `DeletionProtection=true`, `BackupRetentionPeriod=7`, `EngineVersion=18.6`.

---

### Task 3: EC2 instance and server setup

**Files:** none

**Interfaces:**
- Consumes: `career-web-sg` from Task 2. Files from Task 1, once the branch is on GitHub.
- Produces: instance `career-platform-web`, `<EIP>`, SSH alias `career-aws`, code in `/opt/career-platform`.

- [x] **Step 1 (Laptop): Create and import a new key.** Run `ssh-keygen -t ed25519 -f ~/.ssh/isba4775_aws`, then `aws ec2 import-key-pair --key-name career-aws`. Don't reuse the Azure key.

- [x] **Step 2 (Laptop): Launch one instance.** Get the AMI from SSM parameter `/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id`. Use type `t3.micro`, the `us-east-1a` default subnet, `career-web-sg`, a 20 GB encrypted gp3 root disk, `--metadata-options HttpTokens=required,HttpEndpoint=enabled,HttpPutResponseHopLimit=1`, `--credit-specification CpuCredits=standard`, `--disable-api-termination`, and no user data. Run with `--dry-run` first.

- [x] **Step 3 (Laptop): Allocate and attach an Elastic IP,** then add the `career-aws` alias to `~/.ssh/config` (user `ubuntu`, key `~/.ssh/isba4775_aws`).

Run: `ssh career-aws 'lsb_release -ds; uname -m; free -m | sed -n 2p'`
Expected: Ubuntu 24.04, `x86_64`, about 1 GiB of memory.

- [x] **Step 4 (Server): Install the base packages.** `apt-get update && apt-get upgrade -y`, then `nginx certbot python3-certbot-dns-cloudflare unattended-upgrades`. Install uv. Create system user `career` with no login shell. Make `/opt/career-platform` owned by `ubuntu`, and `/etc/career-platform` owned by `root:career` with mode `750`.

Expected: `systemctl is-enabled unattended-upgrades` prints `enabled`.

- [x] **Step 5 (Server): Confirm log retention.**

Run: `grep -E 'daily|rotate' /etc/logrotate.d/nginx`
Expected: `daily` and `rotate 14`, matching the privacy text from Task 1 Step 8. If it differs, set it to match.

- [x] **Step 6 (Laptop): Push the branch. Needs the owner's OK.**

Run: `git push -u origin aws-migration`, then `railway deployment list | head -3`.
Expected: the latest Railway deployment hasn't changed. Railway must only build `main`. On 2026-10-08 it deployed `main` before a migration branch was merged, so check rather than assume.

- [x] **Step 7 (Server): Clone and install.**

```bash
git clone --branch aws-migration https://github.com/ethanjad/career-platform.git /opt/career-platform
cd /opt/career-platform && uv sync --locked && uv run pytest -q
```

Expected: all tests pass on the server, and `git status --short` is empty. Tests must not change tracked files.

---

### Task 4: Database role and restore rehearsal

**Files:** none

**Interfaces:**
- Consumes: `<RDS_ENDPOINT>` and `aws.env` from Task 2. `career-aws` from Task 3. `deploy/dump-railway.sh` and `deploy/compare-database.sql` from Task 1.
- Produces: role `career_app`, which owns `career_platform`, and a restore process proven on real data. Laptop restore connection, called `$CONN` below:

```
host=<RDS_ENDPOINT> hostaddr=127.0.0.1 port=15432 dbname=career_platform user=career_app sslmode=verify-full sslrootcert=$HOME/.config/career-platform/rds-global-bundle.pem
```

`hostaddr` sends traffic down the tunnel while TLS still verifies the real RDS name.

- [x] **Step 1 (Laptop): Download the RDS certificate bundle** from `https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem` to `~/.config/career-platform/rds-global-bundle.pem`.

- [x] **Step 2 (Laptop): Open the tunnel.** *(Superseded 2026-11-04: restores now run from EC2. See `migration-notes.md`.)* Run `ssh -N -L 15432:<RDS_ENDPOINT>:5432 career-aws`. This uses the laptop's 18.6 tools, because the Ubuntu 24.04 client may be too old to read this dump.

- [x] **Step 3 (Laptop): Create the app role.** Connect as `career_admin` and run:

```sql
\getenv app_pw APP_PW
CREATE ROLE career_app LOGIN PASSWORD :'app_pw';
GRANT career_app TO career_admin;
ALTER DATABASE career_platform OWNER TO career_app;
```

Expected: connecting with `$CONN` works, and `select ssl from pg_stat_ssl where pid = pg_backend_pid()` returns `t`. The app can create its tables but isn't an admin.

- [x] **Step 4 (Laptop): Take a fresh dump.** Run `deploy/dump-railway.sh ~/Backups/career-platform/railway-rehearsal-<UTC>.dump`.
Expected: the checksums match.

- [x] **Step 5 (EC2, changed 2026-11-04): Restore into the empty database,** using `pg_restore` 18 from `postgresql-client-18`, without `--clean`. The command below is the original laptop form.

```bash
pg_restore -d "$CONN" --clean --if-exists --no-owner --no-privileges --exit-on-error --single-transaction <dump>
```

Set `PGPASSWORD` from `APP_PW` for this command. Expected: exit 0 with no errors.

- [x] **Step 6: Compare RDS to Railway.** Run `deploy/compare-database.sql` on both, using `railway ssh --service Postgres` for one and `$CONN` for the other, then `diff` the output.
Expected: no differences. Row counts on 2026-10-29 were education 2, experience 4, links 2, profile 1, projects 7, settings 1, skills 4. Later admin edits could change them, and that's fine as long as both sides match.

---

### Task 5: Run the app on EC2 with HTTPS, before DNS moves

**Files:** none

**Interfaces:**
- Consumes: everything above.
- Produces: a complete site at `<EIP>` that's reachable only by forcing the name to resolve there. `/etc/career-platform/env` has mode `640`, owner `root:career`.

- [x] **Step 1 (Server): Write the env file,** without echoing secrets. Copy `ADMIN_SECRET` from the laptop's `.env`, because this migration doesn't rotate it. Also put the RDS bundle at `/etc/career-platform/rds-global-bundle.pem`.

```
DATABASE_URL=postgresql://career_app:<APP_PW>@<RDS_ENDPOINT>:5432/career_platform?sslmode=verify-full&sslrootcert=/etc/career-platform/rds-global-bundle.pem
ADMIN_SECRET=<ADMIN_SECRET>
SNAPSHOT_PATH=/var/lib/career-platform/profile_snapshot.json
ENABLE_FALLBACK=true
```

- [x] **Step 2 (Server): Start the service.** Install the unit from `deploy/`, then `systemctl enable --now career-platform`.

Run: `curl -s 127.0.0.1:8000/healthz; sudo ss -ltnp | grep 8000`
Expected: `ok`, listening on `127.0.0.1:8000` only.

- [x] **Step 3 (Server): Issue the certificate.** Write the Task 0 token to `/etc/letsencrypt/cloudflare.ini` with mode `600`.

```bash
sudo certbot certonly --dns-cloudflare --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini \
  -d ethanjad.me --agree-tos --register-unsafely-without-email \
  --deploy-hook "systemctl reload nginx"
```

Expected: certificate saved under `/etc/letsencrypt/live/ethanjad.me/`. Then `sudo certbot renew --dry-run` succeeds.

- [x] **Step 4 (Server): Enable nginx.** Install the config from `deploy/`, remove the default site, then run `sudo nginx -t && sudo systemctl reload nginx`.

- [x] **Step 5 (Laptop): Check the site as a visitor would,** with `R="--resolve ethanjad.me:443:<EIP> --resolve ethanjad.me:80:<EIP>"`.

| Check | Expected |
|---|---|
| `curl -s $R https://ethanjad.me/healthz` | `ok` |
| `curl -sI $R http://ethanjad.me/` | `301` to `https://ethanjad.me/` |
| `curl -s $R https://ethanjad.me/` diffed against the same page from Railway, with hosts stripped | identical. This also proves it's serving real data, not seed rows |
| Asset links in that page | all `https://` |
| `curl -s -o /dev/null -w '%{http_code}' -X POST $R https://ethanjad.me/admin/links -H 'X-Admin-Secret: change-me'` | `401` |
| `curl -I $R https://ethanjad.me/resume.pdf` | `200`, `application/pdf` |
| `nc -z -w 5 <EIP> 8000` and `nc -z -w 5 <RDS_ENDPOINT> 5432` | both fail |
| `ls -l /var/lib/career-platform/profile_snapshot.json` | exists, owned by `career`, holds the real name |
| `git -C /opt/career-platform status --short` | empty |

- [x] **Step 6 (Server): Test a database failure and a restart.**
  - Run `sudo iptables -I OUTPUT -p tcp --dport 5432 -j REJECT`. `/healthz` and `/` return `503`, the profile still shows from the snapshot, and Projects shows "temporarily unavailable".
  - Remove the rule with `sudo iptables -D OUTPUT -p tcp --dport 5432 -j REJECT`. `/healthz` returns `ok`.
  - Run `sudo reboot`. After it returns, `curl -s $R https://ethanjad.me/healthz` from the laptop returns `ok`, with no manual steps.
  - Run `sudo pkill -f uvicorn`. systemd brings it back within seconds.

- [x] **Step 7 (Server): Test the deploy script.** Run `deploy/deploy.sh aws-migration`.
Expected: exit 0 and a healthy site. Test its rollback by pushing a temporary branch `deploy-test` where `/healthz` returns 500, then running `deploy/deploy.sh deploy-test`. Expected: exit 1, with the earlier commit running again. Delete `deploy-test` afterwards, locally and on GitHub.

---

### Task 6: Cutover

**Needs the owner's go-ahead on the day.** Do this by 2026-11-04, outside the interview day, so a full day remains to fall back to Railway. Expected visitor impact: none, because both hosts serve the same content while DNS changes.

**Files:** none

- [x] **Step 1: Freeze admin edits** and record the time.

- [x] **Step 2 (Laptop): Save the current DNS answers.**

Run: `for t in A MX TXT; do dig +short $t ethanjad.me; done; dig +short www.ethanjad.me` and save the output.

- [x] **Step 3 (Laptop): Take the final dump, restore and compare,** as in Task 4 Steps 4–6, running the restore from EC2 into an emptied database, to `~/Backups/career-platform/railway-final-<UTC>.dump`. Run `sudo systemctl stop career-platform` before the restore and start it afterwards, so nothing reads half-restored tables. Repeat the Task 5 Step 5 page comparison.
Expected: `diff` is empty. **Stop here if it isn't.**

- [x] **Step 4 (Console): Change the apex record only.** In Cloudflare, set `ethanjad.me` to `A <EIP>`, DNS only, with the lowest TTL. Don't touch `www`, MX, TXT or anything else.

- [x] **Step 5 (Laptop): Verify from outside.**

Run: `dig +short ethanjad.me @1.1.1.1`, then `curl -sI https://ethanjad.me/ | grep -i '^server'`, then `curl -s https://ethanjad.me/healthz`.
Expected: `<EIP>`, `server: nginx` with no `x-railway-*` headers, and `ok`. Open the site in a browser, including `/privacy` and the résumé PDF.

- [ ] **Step 6 (Laptop): Confirm nothing else moved.** Repeat the Step 2 lookups and `curl -sI https://www.ethanjad.me/`.
Expected: only the `A` answer changed, and `www` still returns `301` to `https://ethanjad.me/`. Send a test email through Zoho and confirm it arrives.

**Rollback, while Railway is still up:** restore the Task 0 Step 5 record in Cloudflare, then check `curl -s https://ethanjad.me/healthz` and the `x-railway-*` header. With admin edits frozen, Railway's data is still current, so nothing is lost. **After the trial lapses, this rollback no longer exists** and recovery means fixing AWS.

---

### Task 7: After cutover

**Files:**
- Create: `docs/aws-architecture.md`
- Modify: `README.md` (sections listed in Step 4), `docs/how-this-site-is-secured.md`, `docs/request-path.md`, `TASKS.md`, `PRODUCT.md:29`
- Delete, after the trial ends: `railway.json`, `start.sh`

`docs/project-1-submission.md` stays as written, because it records what was submitted at commit `5252820`.

- [ ] **Step 1: Watch for 24 hours, or until the trial ends, whichever comes first.** Then lift the admin freeze and keep the final dump.

- [ ] **Step 2 (Console): Add an external uptime check** on `https://ethanjad.me/healthz`, with any free monitor. SNS alerts are denied for `isba-student`, and nothing else reports the site being down.

- [x] **Step 3: Take a first manual RDS snapshot** with `aws rds create-db-snapshot`. Expected: `available`. To test a real recovery, restore it to a temporary instance only if you accept the extra cost, then delete that instance.

- [x] **Step 4: Update the docs.**
  - `docs/aws-architecture.md`: request path, ports, security groups, who manages what, compared with Railway.
  - README: "Updating the live site", "Architecture", "Rollback", "Costs, cleanup and limitations", plus a "Moving from Railway to AWS" decision with the alternatives compared and why they were rejected.
  - `docs/how-this-site-is-secured.md`: nginx TLS, certbot renewal, SSH and security groups are the owner's again.
  - `docs/request-path.md`: a new AWS path. Mark the Railway one as historical.

  Before committing, search `docs` and `README.md` for the real account ID, Elastic IP and RDS endpoint.
  Expected: none of them appear.

- [ ] **Step 5: Merge to `main`. Needs the owner's OK.** This triggers a Railway build that nobody reaches anymore. Then, on the server, run `deploy/deploy.sh main` and check `/healthz`.

- [ ] **Step 6: After the trial ends,** remove `railway.json` and `start.sh`, and update `tests/` if any of them refer to those files. Confirm the Railway project is gone or stopped on its dashboard, with no paid plan attached.

- [x] **Step 7: Note the remaining limits in the README.**
  - One server and one database, in one availability zone. A failure in `us-east-1a` takes the site down.
  - Lockouts when the laptop's IP changes. Fix: update the port 22 rule in the console.
  - Kernel updates need a manual reboot.
  - The manual dumps exist only on the laptop.
  - The domain, the AWS credits and the bill all have end dates to watch.

### Stopping or abandoning this migration

If this is abandoned, or when the site is retired, AWS keeps billing until these are all gone. In order:

1. `aws ec2 modify-instance-attribute --no-disable-api-termination`, then terminate the instance.
2. Release the Elastic IP.
3. `aws rds modify-db-instance --no-deletion-protection --apply-immediately`, then `delete-db-instance` with a final snapshot.
4. Delete manual snapshots once they aren't needed, since they bill for storage.
5. Delete the DB subnet group and both security groups.
6. Revoke the Cloudflare token.

Stopping isn't enough. A stopped instance still bills for its disk and IP, and a stopped RDS instance restarts by itself after 7 days.

## Progress log

_(Add dated results here as each step runs.)_

- **2026-11-04, Task 7 Steps 3, 4 and 7 done.** `tcp_user_timeout=5000` added to the server's `DATABASE_URL`. Manual snapshot requested. Docs updated. `deploy.sh` now finds `uv` on its own. The whole-branch review was a self-review, not a fresh reviewer. Step 1's wait was skipped because the owner asked to merge now. Steps 2 and 6 remain.
- **2026-11-04, Task 6 cutover done at 09:26 UTC.** Final dump restored from EC2 into an emptied database and matched Railway. Apex changed from a `CNAME` to Railway to `A <EIP>`, DNS only, with the Cloudflare CLI; no other record changed. The site serves from nginx on AWS. The Zoho test email is still to do.
- **2026-11-04, Task 5 done.** Let's Encrypt certificate issued through Cloudflare DNS validation, expires 2027-02-02; renewal dry run passes and the timer is on. Through nginx with HTTPS, forced to `<EIP>`: homepage identical to Railway, `http://` redirects with `301`, no `http://` asset links, `change-me` gets `401`, the PDF and privacy page are correct, and bare-IP requests get no answer. No `_acme-challenge` record left behind. DNS still points at Railway.
- **2026-11-04, Task 5 Steps 1, 2, 6 and 7 done; Steps 3-5 wait for the Cloudflare token.** The app runs as `career` on `127.0.0.1:8000`. Tested on the server, not yet through nginx: the homepage is identical to Railway's, and `change-me` gets `401`. A blocked database gives `503` with the snapshot profile, then recovers. It came back after a reboot and after `kill -9`. The deploy script rolled back a broken deploy. Railway and DNS are unchanged.
- **2026-11-04, Task 4 done, from EC2.** Restored a fresh Railway dump with `pg_restore` 18.6 into a database with 0 tables. 7 tables, 5 sequences and 35 constraints match Railway. Railway still serves the site, and DNS is unchanged. Details and deviations are in `migration-notes.md`.
- **2026-11-04, Tasks 1 and 3 done.** Task 1 commit `a937bc9`, 40 tests pass locally. Branch pushed, and Railway's latest deployment is unchanged. Server: packages installed, `unattended-upgrades` enabled, nginx logs rotate daily and keep 14 (matches the privacy text), code cloned to `/opt/career-platform`, 40 tests pass on the server with a clean working tree. Deviations are in `migration-notes.md`.
- **2026-11-04, Task 3 Steps 1–3 done.** Key `career-aws` created (no passphrase, so the owner can add one with `ssh-keygen -p`). `t3.micro` in `us-east-1a` running, x86_64, IMDSv2 required, hop limit 1, standard credits, termination protection on, 20 GB encrypted gp3. Elastic IP `<EIP>` attached and SSH alias added. `ssh career-aws` works: Ubuntu 24.04.5, x86_64, 909 MiB of memory. A metadata request without a token returns `401`, so IMDSv2 is enforced.
- **2026-11-04, Task 2 Step 4 done.** After the owner upgraded to the Paid plan, the create call succeeded at 08:05 UTC, on the second background retry. `describe-db-instances` showed `db.t4g.micro`, 18.6, Single-AZ, not public, encrypted, deletion protection on, 7-day backups, 20 GB gp3, `us-east-1a`. Step 5 (waiting for `available`) is still running.
- **2026-11-03, Task 2 Steps 1–3 done, Step 4 blocked.** Passwords are in `~/.config/career-platform/aws.env` (mode `600`). `career-web-sg` allows 80 and 443 from anywhere and 22 from `<LAPTOP_IP>/32`. `career-db-sg` allows 5432 only from `career-web-sg`. Subnet group `career-platform-db-subnets` is `Complete`. `create-db-instance` failed with `FreeTierRestrictionError` on backup retention, and `describe-db-instances` confirms no instance exists. Waiting for the owner to upgrade to the Paid plan.
- **2026-11-03, plan written.** Branch `aws-migration` created from `main` at `646d1b9`. Baseline: 34 tests pass. No AWS resources created, no DNS changed, nothing pushed.
