# Operate the VM Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Visitors reach the site at `http://135.225.24.52/`. The app starts on boot, restarts itself after a crash, runs as `azureuser`, and port 8000 stays private.

**Architecture:** A systemd service named `career-platform` runs uvicorn with 2 worker processes on `127.0.0.1:8000`. nginx listens on public port 80 and passes each request to `127.0.0.1:8000`. The Azure firewall (NSG) allows port 80 and has no rule for port 8000.

**Tech Stack:** Ubuntu 24.04, systemd, nginx (from apt), uvicorn 0.54.0 (already in `~/career-platform/.venv`), FastAPI, SQLite.

**Spec:** this request (2026-10-01). The earlier setup is in `docs/superpowers/plans/2026-09-24-azure-vm-migration.md`.

## VM details (found 2026-10-01 with read-only `az` commands)

| Item | Value |
|---|---|
| VM | `vm-career-platform` in resource group `rg-career-platform`, region swedencentral |
| Size / OS | Standard_B2ats_v2 (2 vCPUs, 1 GiB RAM) / Ubuntu 24.04 LTS |
| Public IP | `135.225.24.52` (no DNS name) |
| SSH | `ssh career-vm`, which is `azureuser@135.225.24.52` with key `~/.ssh/isba4775_azure`. Password login is off. |
| NSG `vm-career-platformNSG` | `Allow-SSH-Laptop` (300, port 22, old laptop IP), **`Allow-HTTP-80` (310, port 80, from anyone)**, `AllowSSHFromMyIP` (1000, port 22, current laptop IP). There is no rule for port 8000. |
| App on the VM | Code is in `/home/azureuser/career-platform`, the Python environment is `.venv/`, the database is `data/resume.db`, and secrets are in `.env`. Right now uvicorn is started by hand (`nohup setsid`) on `0.0.0.0:8000`. |

**Note:** an `Allow-HTTP-80` rule already exists, at priority **310** rather than the 320 you planned. Task 3 checks that rule instead of creating it. If you'd rather have it at 320, change its priority in the portal. Don't add a second rule with the same name.

## Global Constraints

- The service is named `career-platform` and runs as `azureuser`. Nothing in the app runs as root.
- uvicorn listens on `127.0.0.1:8000` only. Port 8000 gets no NSG rule.
- Use the existing `~/career-platform` code, `.venv` and `data/resume.db`. Don't change any repo files on the VM or the laptop, and don't add tests.
- No crash or reboot tests. You'll run those yourself.
- Where it runs: **Laptop** means your Mac terminal. **VM** means a command sent with `ssh career-vm '…'` from the laptop. **Portal** means the Azure portal in your browser.

## Review Focus

1. **Secrets not loaded.** If `.env` isn't read, the admin secret falls back to `change-me` and anyone on port 80 could edit the site. Task 1 Step 4 checks that `change-me` gets `401`.
2. **Old process still holds port 8000.** The new service then fails with "address already in use". Task 1 Step 1 stops it and checks that the port is free.
3. **Wrong working directory.** The app would create a new demo database somewhere else and show "Alex Carter". Task 1 Step 4 checks that this demo name doesn't appear.
4. **nginx default page shows instead of the site.** The Ubuntu default site also listens on port 80. Task 2 removes it and checks for the site's own text.
5. **Port 8000 reachable from outside.** Task 3 checks from the laptop that port 8000 is blocked.

## Progress log

_(Add dated results here as each step runs.)_

- **2026-10-01, Task 0 done (read-only, nothing changed).** All checks matched the expected results. Details are under Task 0.
- **2026-10-01, Task 1 done.** The hand-started uvicorn is stopped. The `career-platform` service is enabled and active, running as `azureuser` with 2 workers on `127.0.0.1:8000`. All Step 4 checks matched. Details are under Task 1.
- **2026-10-01, Task 2 done.** nginx 1.24.0 is installed. It serves the site on port 80 of the VM and passes requests to `127.0.0.1:8000`. The Ubuntu default page is turned off, and an auto-restart setting is added. All Step 4 checks matched. Details are under Task 2.
- **2026-10-01, Task 3 done. All tasks are complete.** From the laptop, `http://135.225.24.52/` returns `200` with the real resume page and port 8000 is blocked. The site is served by nginx on port 80 and the `career-platform` service on `127.0.0.1:8000`. Both start at boot, both restart after a crash, and the app runs as `azureuser`. Still to do (by you): the crash and reboot tests (see Known limits). Also worth a look: `Allow-SSH-Laptop` now allows the VM's own IP (see Task 3).

---

### Task 0: Preflight checks (VM, read-only, about 3 minutes)

**What this does:** checks that everything the plan relies on is actually there before anything changes. Nothing is changed in this task.

- [x] **Step 1: Check the files and the Python environment**

Runs on: **VM**
```bash
ssh career-vm 'cd ~/career-platform && ls -l .env data/resume.db .venv/bin/uvicorn && .venv/bin/uvicorn --version && git status --short'
```
Expected: all three files are listed, the version shows `0.54.0`, and `git status` shows only the known leftovers (`data/profile_snapshot.json` and `data/resume.db.bak-demo-*`).

- [x] **Step 2: Check what's running and what's listening**

Runs on: **VM**
```bash
ssh career-vm 'pgrep -af "[u]vicorn app.main:app"; sudo ss -ltnp; sudo ufw status; systemctl list-unit-files nginx.service career-platform.service'
```
Expected: one uvicorn process from the manual start, listening on `0.0.0.0:8000`; ufw `inactive`; and no nginx or career-platform units yet. If anything looks different, stop and write it in the Progress log.

**Result (2026-10-01): Task 0 complete. Everything matched, and nothing was changed.**

What ran: the two commands above, from the laptop over `ssh career-vm`.

What the checks showed:
- **Step 1:**
  - The files are present: `.env` (153 bytes, mode 600), `data/resume.db` (36864 bytes, mode 600, last changed 2026-09-29 22:22) and `.venv/bin/uvicorn`.
  - The version check printed `Running uvicorn 0.54.0 with CPython 3.12.3 on Linux`.
  - `git status --short` shows only the known leftovers: ` M data/profile_snapshot.json` and `?? data/resume.db.bak-demo-20260929-222233`.
- **Step 2:**
  - **Processes:** the manual start is two processes. One is `uv run --locked uvicorn …` (pid 40660). The other is its child, `.venv/bin/python .venv/bin/uvicorn app.main:app --env-file .env --host 0.0.0.0 --port 8000` (pid 40663). Both match the `[u]vicorn app.main:app` pattern, so Task 1 Step 1's `pkill` stops both.
  - **Listening ports:** `0.0.0.0:8000` (uvicorn, pid 40663) and `0.0.0.0:22` / `[::]:22` (sshd). Ports `127.0.0.53` and `127.0.0.54` port 53 belong to systemd-resolved. Nothing is on port 80 yet.
  - **ufw:** `Status: inactive`, so only the NSG filters traffic and nothing on the VM's own firewall needs changing.
  - **Units:** `0 unit files listed`, so there's no nginx or career-platform unit yet. This command exits with code 1 when it finds no units, which is expected.
  - **sudo:** it ran without asking for a password, which the later tasks need.

---

### Task 1: Run the app as a systemd service (VM, about 6 minutes)

**What this does:** systemd is the Linux program that starts and watches background services. A *unit file* tells it how to run the app:
- `User=azureuser`: the app doesn't run as root.
- `--host 127.0.0.1`: only programs on the VM can reach the app. nginx will be the public front door.
- `--workers 2`: two copies of the app share the work. If one crashes, the other keeps serving while uvicorn starts a replacement.
- `Restart=always`: if the whole uvicorn process dies, systemd starts it again after 3 seconds.
- `WantedBy=multi-user.target` plus `enable`: start the app when the VM boots.
- `--env-file .env`: loads the admin secret. The app doesn't read `.env` by itself.

**Files (on the VM only):**
- Create: `/etc/systemd/system/career-platform.service`

- [x] **Step 1: Stop the hand-started uvicorn**

Runs on: **VM**
```bash
ssh career-vm 'pkill -f "[u]vicorn app.main:app"; sleep 2; pgrep -af "[u]vicorn app.main:app" || echo stopped; sudo ss -ltn "sport = :8000"'
```
Expected: `stopped`, and no line for `:8000`. The brackets in `[u]vicorn` keep `pkill` from matching, and killing, its own SSH session. **The site is down from here until Step 3.**

- [x] **Step 2: Write the unit file**

Runs on: **Laptop** (the text is sent to the VM)
```bash
ssh career-vm 'sudo tee /etc/systemd/system/career-platform.service >/dev/null' <<'EOF'
[Unit]
Description=Career Platform (FastAPI on uvicorn)
After=network-online.target
Wants=network-online.target

[Service]
User=azureuser
Group=azureuser
WorkingDirectory=/home/azureuser/career-platform
ExecStart=/home/azureuser/career-platform/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2 --env-file .env
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```
Check: `ssh career-vm 'sudo systemd-analyze verify career-platform.service && echo ok'` prints `ok`.

- [x] **Step 3: Turn on start-at-boot and start the service now**

Runs on: **VM**
```bash
ssh career-vm 'sudo systemctl daemon-reload && sudo systemctl enable --now career-platform && systemctl is-enabled career-platform && systemctl is-active career-platform'
```
Expected: `enabled` and `active`.

- [x] **Step 4: Check the service**

Runs on: **VM**
```bash
ssh career-vm '
  ps -eo user=,pid=,cmd= | grep -E "[a]pp.main|[m]ultiprocessing"
  sudo ss -ltnp "sport = :8000"
  curl -s -o /dev/null -w "page %{http_code}\n" http://127.0.0.1:8000/
  curl -s http://127.0.0.1:8000/ | grep -c "Alex Carter"
  curl -s -o /dev/null -w "admin %{http_code}\n" -X POST -H "X-Admin-Secret: change-me" -H "Content-Type: application/json" -d "{}" http://127.0.0.1:8000/admin/skills
  journalctl -u career-platform -n 20 --no-pager'
```
Expected:
- Each `app.main` process is owned by `azureuser`. That's 1 parent and 2 workers.
- Port 8000 is listening on `127.0.0.1:8000` only, not `0.0.0.0`.
- `page 200`.
- The `Alex Carter` count is `0`, so the real database is in use.
- `admin 401`, so `.env` was loaded.
- The log shows `Started parent process`, two `Started server process` lines, `Application startup complete` twice, and no tracebacks.

**Result (2026-10-01): Task 1 complete. Every check matched.**

What ran: Steps 1 to 4 exactly as written, from the laptop over `ssh career-vm`.

What the checks showed:
- **Step 1:** `stopped`, and `ss` showed nothing on `:8000`. The site was down from about 22:22 until the service started at 22:23:07 VM time (UTC).
- **Step 2:** `systemd-analyze verify` printed `ok`.
- **Step 3:** systemd created the start-at-boot link `multi-user.target.wants/career-platform.service`, then printed `enabled` and `active`.
- **Step 4:**
  - **Processes:** all are owned by `azureuser`. The parent is uvicorn pid 53990 (parent pid 1, so systemd started it) and the 2 workers are pids 54018 and 54019. There is also one `multiprocessing.resource_tracker` helper, pid 54017. It's a small Python helper process, not a third worker.
  - **Port:** `127.0.0.1:8000` only, held by the parent and both workers. Nothing is on `0.0.0.0:8000` any more.
  - **Page:** `page 200`.
  - **Real database:** the `Alex Carter` count is `0`, so the real database is in use.
  - **Admin secret:** `admin 401`, so `change-me` is rejected.
  - **Log:**
    - `Loading environment from '.env'`
    - `Uvicorn running on http://127.0.0.1:8000`
    - `Started parent process [53990]`
    - two `Started server process` lines
    - two `Application startup complete` lines
    - no tracebacks

**Undo:** `ssh career-vm 'sudo systemctl disable --now career-platform && sudo rm /etc/systemd/system/career-platform.service && sudo systemctl daemon-reload'`. Then restart by hand using the migration plan's PR1 command.

---

### Task 2: Put nginx on port 80 (VM, about 6 minutes)

**What this does:** nginx is a web server that faces the internet. It accepts visitors on port 80, the default for `http://`, so no port number is needed. It then forwards each request to the app on `127.0.0.1:8000`. nginx needs root only to open port 80. Its worker processes, which handle the traffic, run as the unprivileged `www-data` user. The apt package already starts nginx at boot. A small *drop-in* file adds automatic restarts if it crashes.

**Files (on the VM only):**
- Create: `/etc/nginx/sites-available/career-platform`
- Create: link `/etc/nginx/sites-enabled/career-platform`
- Remove: link `/etc/nginx/sites-enabled/default` (the "Welcome to nginx" page). The original file stays in `sites-available`.
- Create: `/etc/systemd/system/nginx.service.d/restart.conf`

- [x] **Step 1: Install nginx**

Runs on: **VM**
```bash
ssh career-vm 'sudo apt-get update -q && sudo apt-get install -y -q nginx && systemctl is-enabled nginx && systemctl is-active nginx'
```
Expected: `enabled` and `active`.

- [x] **Step 2: Write the site config and switch it on**

Runs on: **Laptop** (the text is sent to the VM)
```bash
ssh career-vm 'sudo tee /etc/nginx/sites-available/career-platform >/dev/null' <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
ssh career-vm 'sudo ln -sf /etc/nginx/sites-available/career-platform /etc/nginx/sites-enabled/career-platform && sudo rm -f /etc/nginx/sites-enabled/default && sudo nginx -t && sudo systemctl reload nginx'
```
Expected: `nginx -t` prints `syntax is ok` and `test is successful`.

- [x] **Step 3: Restart nginx automatically if it crashes**

Runs on: **Laptop** (the text is sent to the VM)
```bash
ssh career-vm 'sudo mkdir -p /etc/systemd/system/nginx.service.d && sudo tee /etc/systemd/system/nginx.service.d/restart.conf >/dev/null' <<'EOF'
[Service]
Restart=on-failure
RestartSec=3
EOF
ssh career-vm 'sudo systemctl daemon-reload && systemctl show nginx -p Restart'
```
Expected: `Restart=on-failure`.

- [x] **Step 4: Check that port 80 serves the site**

Runs on: **VM**
```bash
ssh career-vm '
  curl -s -o /dev/null -w "port80 %{http_code}\n" http://127.0.0.1/
  curl -s http://127.0.0.1/ | grep -c -i "welcome to nginx"
  curl -s http://127.0.0.1/static/styles.css -o /dev/null -w "css %{http_code}\n"
  ps -o user=,cmd= -C nginx'
```
Expected: `port80 200`, a count of `0` for the welcome page, and `css 200`. The nginx `master` process is owned by root and the `worker` processes by `www-data`.

**Result (2026-10-01): Task 2 complete. Every check matched.**

What ran: Steps 1 to 4 from the laptop over `ssh career-vm`. Small differences from the plan text:
- **Step 1:** I added `DEBIAN_FRONTEND=noninteractive` so apt couldn't stop to ask a question. I also sent apt's output to `/tmp/apt-update.log` and `/tmp/apt-nginx.log` on the VM.
- **Step 4:** I added two read-only checks: no `Alex Carter` through port 80, and `ss` for ports 80 and 8000.

What the checks showed:
- **Step 1:** the install exited with `0` and installed `nginx/1.24.0 (Ubuntu)`, which is `enabled` and `active`. apt printed a note, "User sessions running outdated binaries: azureuser @ user manager service". That's just a reminder to restart a background process after the update, it doesn't affect the site, and I left it alone.
- **Step 2:** `nginx -t` printed `syntax is ok` and `test is successful`, and nginx reloaded.
  - `sites-enabled/` now holds only `career-platform`, a link to `sites-available/career-platform`.
  - `sites-available/default` is still there, so the Undo can restore it.
- **Step 3:** `Restart=on-failure`, `RestartUSec=3s`, `DropInPaths=/etc/systemd/system/nginx.service.d/restart.conf`.
- **Step 4:**
  - **Page and styles:** `port80 200`, `css 200`.
  - **Right content:** the `welcome to nginx` count is `0`, and the `Alex Carter` count is `0`.
  - **Processes:** the nginx `master` (pid 54764) is owned by `root`, and the 2 `worker` processes (54955 and 54956) by `www-data`.
  - **Ports:** nginx listens on `0.0.0.0:80` and `[::]:80`. uvicorn is still on `127.0.0.1:8000` only.
  - **Services:** `nginx` and `career-platform` are both `active`.

**Undo:** `ssh career-vm 'sudo rm -f /etc/nginx/sites-enabled/career-platform /etc/systemd/system/nginx.service.d/restart.conf && sudo ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default && sudo systemctl daemon-reload && sudo systemctl reload nginx'`. To remove nginx completely, run `sudo apt-get purge -y nginx nginx-common`.

---

### Task 3: Check the site from the internet (Portal + Laptop, about 3 minutes)

**What this does:** the NSG is Azure's firewall in front of the VM. Port 80 must be allowed. Port 8000 must have no rule, so it stays blocked, and the app only listens on `127.0.0.1` as well. This plan makes no Azure changes.

- [x] **Step 1: Confirm the port 80 rule (Portal or Laptop, read-only)**

`Allow-HTTP-80` already exists (priority 310, TCP 80, source `*`). Check it in the portal under the VM → Networking, or run:
```bash
az network nsg rule list -g rg-career-platform --nsg-name vm-career-platformNSG --query "[].{name:name,prio:priority,port:destinationPortRange,src:sourceAddressPrefix}" -o table
```
Expected: `Allow-HTTP-80` is present, and no rule mentions `8000`.

- [x] **Step 2: Check from outside**

Runs on: **Laptop**
```bash
curl -s -o /dev/null -w "port80 %{http_code}\n" --max-time 10 http://135.225.24.52/
curl -s -o /dev/null -w "port8000 %{http_code}\n" --max-time 10 http://135.225.24.52:8000/ || true
```
Expected: `port80 200` and `port8000 000`, which means blocked. Also open `http://135.225.24.52/` in a browser and confirm the resume page loads with its styles.

- [x] **Step 3: Record the results**

Runs on: **Laptop.** Add a dated entry to this plan's Progress log with each check's output, and tick the boxes. Ticking boxes edits only this plan file.

**Result (2026-10-01): Task 3 complete. Every check matched, and no Azure changes were made.**

What ran: the read-only `az network nsg rule list` command, then the two `curl` checks from the laptop. I added a few read-only extras: a `curl` for `/static/styles.css`, the page `<title>`, a count of demo and default-page text, and a headless Chrome screenshot instead of opening a browser by hand.

What the checks showed:
- **Step 1:** `Allow-HTTP-80` exists: priority 310, Inbound, Allow, TCP, port 80, source `*`. No rule mentions port 8000.
  - **Changed since the morning:** `Allow-SSH-Laptop` (300, port 22) now has source `135.225.24.52/32`, the VM's own public IP. Earlier today it was the old laptop IP. This session didn't change it.
  - `AllowSSHFromMyIP` (1000, port 22, the current laptop IP) is unchanged.
- **Step 2:**
  - `port80 200` and `port8000 000` (blocked).
  - Extra checks: `css 200`, and the page title is `Ethan Jad | Finance and ISBA Student at Loyola Marymount University`. The count of `Alex Carter` and `Welcome to nginx` is `0`.
  - Screenshot of `http://135.225.24.52/` (1280×1600, saved in this session's scratch folder, not the repo): the full resume page renders with its styles. That's the header, the hero section, Experience, Skills and Education.
- **Step 3:** the boxes are ticked and these results are recorded.

---

## Known limits (not fixed here)

- With 2 workers, both can write `data/profile_snapshot.json` at the same moment. That's harmless in practice, because the file is only read when the database fails.
- Plain HTTP only. Adding HTTPS needs a domain name.
- You'll run the crash and reboot tests yourself. Useful commands: `sudo systemctl kill -s KILL career-platform`, `sudo kill -9 <one worker pid>`, `sudo reboot`, then repeat Task 3 Step 2.
