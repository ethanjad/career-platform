# Azure VM Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the career-platform FastAPI site on the Azure VM `vm-career-platform`, serving the existing SQLite data from the laptop.

**Architecture:** Clone the public GitHub repo onto the VM, install dependencies with uv from a committed `uv.lock`, copy the laptop's `resume.db` into `data/`, and run uvicorn bound to `127.0.0.1:8000` in the background. The site is checked on the VM with `curl`, and from the laptop through an SSH tunnel. No new inbound ports are opened.

**Tech Stack:** Ubuntu 24.04 LTS, apt, git, sqlite3, uv, Python 3.12, FastAPI, Jinja2, uvicorn[standard].

**Spec:** The migration outline in the 2026-09-24 request (Server → Packages → Code → Python → Config → Data → Processes → Verify). Each section below is one of those categories, in that order.

## Global Constraints

- VM: `vm-career-platform`, resource group `rg-career-platform`, region `swedencentral`, size `Standard_B2ats_v2` (2 vCPU, 1 GiB).
- **VM public IP: `<VM_PUBLIC_IP>`.** The laptop's public IP is different and changes between networks. It appears only in the NSG SSH rule (currently `<LAPTOP_IP>`, see the Progress log).
- SSH user `azureuser`, key `~/.ssh/isba4775_azure`, always with `-o IdentitiesOnly=yes`.
- **Placeholders (redacted for the public repo):** `<VM_PUBLIC_IP>` is the VM's public IP (`az vm show -d -g rg-career-platform -n vm-career-platform --query publicIps -o tsv`). `<LAPTOP_IP>` is the laptop's current public IP (`curl -4 -s https://api.ipify.org`). `<OLD_LAPTOP_IP>` is the IP it had on 2026-09-24. The real values live only in `~/.ssh/config` and the NSG.
- NSG allows inbound TCP 22 from the laptop's current IP only (rule `AllowSSHFromMyIP`, currently `<LAPTOP_IP>/32`). This plan opens no other port.
- Repo: `https://github.com/ethanjad/career-platform` (public, branch `main`). VM checkout path: `/home/azureuser/career-platform`.
- Laptop database: `~/Desktop/github/resume.db` (outside the repo; `data/*.db` is git-ignored).
- VM database: `/home/azureuser/career-platform/data/resume.db` (`DATABASE_PATH=data/resume.db`, resolved relative to the repo root by `app/config.py`).
- uvicorn listens on `127.0.0.1:8000` only. **Changed 2026-09-29 at your request: it now listens on `0.0.0.0:8000` (see the Progress log).**
- The app does **not** load `.env` by itself (`app/config.py` reads `os.getenv` only). The env file must be passed to uvicorn with `--env-file .env`.
- Do not use `start.sh` on the VM. It ignores `.env` and binds `0.0.0.0` by default.

## Facts found while writing this plan (read before starting)

1. **There is no `pyproject.toml` or `uv.lock` in the repo.** Dependencies live only in `requirements.txt`, so `uv sync` from a lock file cannot work yet. The Python section starts with a laptop step that creates both files and pushes them.
2. **uv is not installed on the laptop.** Step P1 installs it.
3. **The laptop database contains the same placeholder profile as the seed data** (`Alex Carter`, "Senior Business Analytics Student"). A freshly seeded database would look the same on the page. The *row counts* tell them apart: the laptop file has 4 projects, 16 skills and 2 experience rows, while a fresh seed has 2 projects and 8 skills. The checks below rely on the file hash and those counts.
4. **Pre-existing bug: each page load added duplicate rows. Decision (2026-09-29): fix first.** `initialize_database()` runs on every request and re-inserted the seed rows each time. `skills`, `projects` and `links` have no unique key other than the autoincrement `id`, so every visit added 8 skills, 2 projects and 3 links. The same cause meant admin deletes of the seeded experience/education rows were undone on the next load. Fixed in `a02219b fix: seed only a new database` (branch `fix/seed-only-new-database`): seed only when the `profile` row is missing. The duplicates already in your DB (skills 16, projects 4, links 6) are **not** removed by the fix; cleaning them up is a separate decision. Deployed by step C2.
5. **The app rewrites a tracked file.** Every successful page load rewrites `data/profile_snapshot.json`, which is tracked in git. On the VM, once the site is live, `git status` will show it modified, and a later `git pull --ff-only` that touches that file will refuse to run. Before pulling, run `git -C ~/career-platform stash` or `git -C ~/career-platform checkout data/profile_snapshot.json`. Longer term, the snapshot should be untracked. That's not in this plan.

## Review Focus

- **Seed-instead-of-data:** if uvicorn starts (or any request hits `/`) before `resume.db` is copied, the app silently creates a fresh seeded DB at `data/resume.db`. The page looks almost identical. Guarded by D2 (the file must not exist before the copy) and D4 (sha256 + counts).
- **`.env` ignored:** if uvicorn is started without `--env-file .env`, `ADMIN_SECRET` falls back to the literal `change-me`, so anyone who reaches the port can write to the admin API. Guarded by V4 (admin POST with `change-me` must return 401).
- **Laptop IP change:** on a different network, SSH times out with no error explaining why. Guarded by S1.
- **Process dies on SSH logout:** a plain `&` job can be killed when the session ends. Guarded by using `nohup setsid` in PR1 and checking the process from a *new* SSH session in V1.
- **Snapshot fallback hides DB failures:** if SQLite can't be opened (wrong path, permissions), the page still renders from `data/profile_snapshot.json` and returns 200. Guarded by V2 (the log must show no errors, and `profile_snapshot.json` must become newer than `resume.db`; only a successful live DB read rewrites it).

## Progress log

- **2026-09-29, Section 1 (Server): complete.**
  - S1: the laptop IP had changed from `<OLD_LAPTOP_IP>` to `<LAPTOP_IP>`. `AllowSSHFromMyIP` now allows `<LAPTOP_IP>/32` (replaced, not added).
  - S2: `VM running`.
  - S3: `~/.ssh/config` didn't exist before, so S3 created it with the `career-vm` block (mode 600). `ssh career-vm` → `azureuser` / `vm-career-platform` / Ubuntu 24.04.4 LTS / 26G free disk / ~440Mi available memory.
- **2026-09-29, Section 2 (Packages): complete.**
  - K1: `git` was already installed (preinstalled on the image) and `sqlite3` was not.
  - K2: installed `sqlite3` 3.45.1-1ubuntu2.8. `git` stayed at 2.43.0-1ubuntu7.3. K2's undo therefore removes **only `sqlite3`**.
- **2026-09-29, Section 3 (Code): complete.**
  - C1: `~/career-platform` didn't exist beforehand. The clone is at `65fbf8c Merge feature/career-platform` on `main`, tracking `origin/main`, which matches the laptop's `origin/main`. `data/` has no `resume.db` (as required before D2).
- **2026-09-29, Section 4 (Python): complete.** You approved the merge and push in P3 before it ran.
  - P1: `uv 0.12.19` installed with Homebrew.
  - P2: branch `chore/uv-lock`. `pyproject.toml` has `requires-python = ">=3.12"` and the 5 dependencies from `requirements.txt`. `uv.lock` resolves 32 packages and includes `python-dotenv`. `uv lock --check` passed and `uv run pytest -q` gave 7 passed on the laptop's Python 3.14.7. No tracked files changed.
  - P3: committed `8d5e08a chore: add uv project and lock file for VM deploy`, fast-forwarded `main`, and pushed. `origin/main` = `8d5e08a`. The local branch `chore/uv-lock` still exists (fully merged).
  - P4: the VM pulled to `8d5e08a`. `pyproject.toml` and `uv.lock` are present.
  - P5: `uv 0.12.21` installed on the VM. The installer also appended `. "$HOME/.local/bin/env"` to `~/.bashrc` (line 119) and `~/.profile` (line 29).
  - P6: `uv sync --locked` used the VM's system Python 3.12.3. The imports check printed `ok`, `pytest -q` gave 7 passed, the working tree is clean, and there's still no `data/resume.db`.
- **2026-09-29, Section 5 (Config): F1 complete. F2 (saving the secret) is yours to do.**
  - F1: `.env` didn't exist beforehand, and it has now been created. Mode `600`, owner `azureuser`, no `replace-with` placeholder, and a 64-character hex `ADMIN_SECRET`. The other values are unchanged from the example. It's git-ignored and `git status` is clean. The secret was never printed to this session.
- **2026-09-29, Section 6 (Data): complete.** F2 is still waiting for your confirmation.
  - D1: the original laptop DB is `7e769ff4…183a`. The `.backup` copy is `ec05e029…14cd`; the hash differs because `.backup` rewrites pages, so D4 compares against the copy. Integrity `ok`, projects 4, skills 16, experience 2.
  - D2: the VM's `data/` had only `.gitkeep` and `profile_snapshot.json`.
  - D3/D4: `data/resume.db` on the VM has sha256 `ec05e029…14cd` (matches), integrity `ok`, counts 4/16/2, mode `600`, 36864 bytes. `git status` is clean.
  - D5: temp copy removed. The laptop original is still `7e769ff4…183a` (unchanged).
  - **Baseline for Verify (V2): projects 4, skills 16, links 6 before any request to `/`.**
- **2026-09-29, fact 4 decision: fix first.** Fix `a02219b` is committed on `fix/seed-only-new-database` (9 tests pass). New step C2 deploys it. C2 is waiting for approval to merge and push, and Section 7 (Processes) is blocked on C2.
- **2026-09-29, C2 complete** (approved). `main` was fast-forwarded to `a02219b` and pushed (`origin/main` = `a02219bace1a…`). The VM pulled `a02219b`, gives `9 passed`, and has a clean working tree.
- **2026-09-29, Section 7 (Processes): complete.**
  - PR1: port 8000 was free beforehand. uvicorn is running: `127.0.0.1:8000` (pid 39936) under `uv run` (pid 39932), session 39932. The log shows `Loading environment from '.env'` and `Application startup complete.`
  - Deviation: the plan's launch command left the local `ssh` hanging. The remote `&` subshell (pid 39931) kept the SSH session's output open. I killed the local `ssh` client and uvicorn kept serving, which proves it survives logout. PR1's command is corrected below for any future restart.
- **2026-09-29, Section 8 (Verify): complete.** The migration is live on the VM (localhost only).
  - V1 `200`.
  - V2: `Alex Carter` ×3, `Northwind Retail` ×1, `Revenue Trend Dashboard` ×2 (the 2 existing duplicates). Counts 4/16/6, unchanged, so the fix works. `snapshot rewritten`, `log clean`.
  - V3: I checked through a temporary tunnel: page `200`, `styles.css` `200 text/css` 5017 B, title `Alex Carter | Senior Business Analytics Student`. Tunnel closed afterwards. The visual check in your browser is still yours to do.
  - V4 `401`. Counts still 4/16/6 afterwards, and the log has 0 errors.
  - V5: `000` then `blocked`. Port 8000 isn't reachable from the internet.
  - **Still open:** F2 (confirm the admin secret is saved), the V3 visual check, cleaning up the existing duplicate rows (optional), and the `profile_snapshot.json` git issue (fact 5). The uvicorn process won't survive a reboot or deallocation (see PR1).
- **2026-09-29, change after migration: uvicorn now listens on every address (`0.0.0.0:8000`)**, at your request. No Azure changes were made.
  - Stopped the old process, and port 8000 was confirmed free. Restarted with the corrected PR1 command, using `--host 0.0.0.0`. The `ssh` call returned right away (exit 0), which confirms the `setsid -f` fix.
  - `ss -ltnp`: `0.0.0.0:8000` uvicorn (pid 40663), `0.0.0.0:22` / `[::]:22` sshd, and `127.0.0.53`/`127.0.0.54:53` systemd-resolved. The log shows `Uvicorn running on http://0.0.0.0:8000`. `127.0.0.1` → 200, `10.0.0.4` → 200.
  - **Port 8000 is publicly reachable:** `http://<VM_PUBLIC_IP>:8000/` → `200` from the laptop. The NSG has two rules this session did not create: `Temp-HTTP-8000` (priority 310, TCP 8000 from `*`) and `Allow-SSH-Laptop` (priority 300, TCP 22 from the old laptop IP `<OLD_LAPTOP_IP>/32`). This supersedes V5's result and the "opens no other port" constraint.
  - `.env` still says `HOST=127.0.0.1`. The `--host 0.0.0.0` flag overrides it, because uvicorn's CLI flag wins and the app never reads `HOST`.
  - Found a problem with the PR1 undo: `pkill -f "uvicorn app.main:app"` run through `ssh` also matches the remote shell running it (its command line contains the same text), so it kills its own session (exit 255). It did stop uvicorn. The undo now uses the pattern `[u]vicorn app.main:app`, which doesn't match itself.
- **2026-09-29, laptop DB: demo content replaced with your real resume data** (approved row by row before writing).
  - Backup first: `~/Desktop/github/resume.db.bak-20260929-152025` (integrity `ok`).
  - Written in one transaction: the profile row updated; experience, education, projects and skills cleared and replaced. New counts: experience 4, education 2, projects 2, skills 4. Links left unchanged (6 demo rows).
  - Checks: integrity `ok`, and the page renders from a scratch copy with status 200, the new content, and no demo text. The render added no rows (the seeding fix works).
  - **The VM's `data/resume.db` still has the demo data.** To update the site, repeat D1 and D3–D5 (the laptop file is the source). The expected counts are now 4/2/2/4 rather than D1's 4/16/2, and links stay at 6.
  - Rollback: `cp ~/Desktop/github/resume.db.bak-20260929-152025 ~/Desktop/github/resume.db`.
- **2026-09-29, live site updated to reflect the resume.**
  - Template: the hero eyebrow changed from "Business analytics & strategy" to "Finance & ISBA", written test-first (`test_homepage_eyebrow_matches_finance_and_isba_focus`: RED, then GREEN, 10 passed). Commit `0801b8e`, merged fast-forward to `main` and pushed. The VM pulled it. No uvicorn restart was needed, because Jinja reloads changed templates.
  - Laptop DB: the 6 demo links were replaced with 1 link (LinkedIn, from the resume). Backup first: `~/Desktop/github/resume.db.bak-20260929-152221`. Final counts: experience 4, education 2, projects 2, skills 4, links 1.
  - VM DB, deployed with D1/D3–D5 plus two safeguards. First, the VM's old demo DB was backed up to `data/resume.db.bak-demo-20260929-222233` (mode 600). Second, the new file was uploaded as `resume.db.incoming`, hash-checked, then `mv`'d over `resume.db`, so the live app never reads a half-copied file. sha256 `88f87f89…8629` matches, integrity `ok`, counts 4/2/2/4/1.
  - Public page `http://<VM_PUBLIC_IP>:8000/` → 200. All the new content is present. Demo strings are absent: `Alex Carter`, `Northwind`, `Rensselaer`, `example.com`, and the old eyebrow. The log has 0 errors.
  - Leftovers on the VM: `data/resume.db.bak-demo-…` shows in `git status` as untracked (`data/*.db` doesn't match it), and `data/profile_snapshot.json` shows as modified (fact 5). Neither blocks pulls of commits that don't touch them.
- **2026-09-29, Track record layout fix.** The live site showed the experience text squeezed into a ~1rem column, one word per line. Cause: `.timeline-item` was a `1rem 1fr` grid, but `.timeline-marker` is `position: absolute` and takes no grid cell, so the text landed in the 1rem track. Fix: removed `display: grid; gap; grid-template-columns` from `.timeline-item`. The marker and vertical line are unchanged. Checked with headless-Chrome screenshots before and after (1280px, and 500px, the narrowest headless renders) plus 10 tests passing. There's no automated test for this CSS. Commit `3d23e09`, pushed. The VM pulled it and serves the new CSS, and a live screenshot confirmed the fix. No restart was needed.
- **2026-09-29, housekeeping.** The duplicate resume PDF in `docs/superpowers/specs/` was deleted (byte-identical to the kept copy). `.gitignore` now ignores `*.pdf` and `.DS_Store` (commit `e6181d2`), so the resume PDF at the repo root stays untracked. Rule: never publish the phone number or home address.
- **Status when paused (2026-09-29): the site is live at `http://<VM_PUBLIC_IP>:8000/`, showing the resume content. `main` = `e6181d2` plus this entry.**
  - Open items, in suggested order:
    1. F2: save `ADMIN_SECRET` to a password manager (run the command in your own terminal).
    2. NSG review: `Temp-HTTP-8000` (8000 from `*`) and `Allow-SSH-Laptop` (22 from `<OLD_LAPTOP_IP>`) were added outside this session. Narrow or remove them as needed.
    3. uvicorn doesn't survive a reboot or deallocation. Restart it with PR1's command (`--host 0.0.0.0` to match the current state), or add a systemd unit.
    4. `.env` says `HOST=127.0.0.1`, while the running process uses `--host 0.0.0.0` (the flag wins). Align them if you want `.env` to be accurate.
    5. Fact 5: `data/profile_snapshot.json` is tracked and rewritten by the app. Consider untracking it.
    6. Cleanup: merged local branches (`chore/uv-lock`, `fix/seed-only-new-database`, `content/resume-eyebrow`, `style/track-record-width`), the laptop DB backups `~/Desktop/github/resume.db.bak-*`, and the VM backup `data/resume.db.bak-demo-*`.
  - Before resuming: re-check the laptop IP against `AllowSSHFromMyIP` (S1), and check the VM is running (S2).

---

## Section 1: Server

Everything here is read-only except the SSH alias and, if the laptop IP changed, the NSG rule update.

- [x] **S1: Confirm the laptop's public IP still matches the NSG rule**
  - **Where:** laptop
  - **Run:** `curl -4 -s https://api.ipify.org; echo`
  - **Why:** the NSG only allows SSH from the IP in `AllowSSHFromMyIP`.
  - **Check:** output matches the rule's source (`az network nsg rule show -g rg-career-platform --nsg-name vm-career-platformNSG -n AllowSSHFromMyIP --query sourceAddressPrefix -o tsv`). If it's different, run:
    `az network nsg rule update -g rg-career-platform --nsg-name vm-career-platformNSG -n AllowSSHFromMyIP --source-address-prefixes <NEW_IP>/32`
  - **Undo:** nothing to undo. If you ran the update, re-run it with the previous IP.
  - **Result (2026-09-29):** the IP had changed to `<LAPTOP_IP>`, and the rule was updated to `<LAPTOP_IP>/32`.

- [x] **S2: Confirm the VM is running**
  - **Where:** laptop (Azure CLI)
  - **Run:** `az vm get-instance-view -g rg-career-platform -n vm-career-platform --query "instanceView.statuses[1].displayStatus" -o tsv`
  - **Why:** a deallocated VM refuses SSH.
  - **Check:** output is `VM running`. If it's `VM deallocated`, run `az vm start -g rg-career-platform -n vm-career-platform`. The public IP is Standard/static, so it stays `<VM_PUBLIC_IP>`.
  - **Undo:** `az vm deallocate -g rg-career-platform -n vm-career-platform` (only if you started it here and want it off again).
  - **Result (2026-09-29):** `VM running`. No start was needed.

- [x] **S3: Add an SSH alias so every later command uses the right user and key**
  - **Where:** laptop
  - **Run:**
    ```bash
    cat >> ~/.ssh/config <<'EOF'

    # career-platform Azure VM
    Host career-vm
        HostName <VM_PUBLIC_IP>
        User azureuser
        IdentityFile ~/.ssh/isba4775_azure
        IdentitiesOnly yes
    EOF
    chmod 600 ~/.ssh/config
    ```
  - **Why:** every later `ssh`/`scp` then uses `azureuser` and `~/.ssh/isba4775_azure` automatically, with no chance of mixing up the two IPs.
  - **Check:** `ssh career-vm 'whoami; hostname; . /etc/os-release; echo "$PRETTY_NAME"; df -h / | tail -1; free -h | sed -n 2p'`
    Expected: `azureuser`, `vm-career-platform`, `Ubuntu 24.04.x LTS`, disk and memory lines.
  - **Undo:** delete the `# career-platform Azure VM` block from `~/.ssh/config`. The file didn't exist before S3, so `rm ~/.ssh/config` is also a full undo, as long as nothing else has been added to it since.
  - **Result (2026-09-29):** created `~/.ssh/config`. Login through `career-vm` passed every check.

## Section 2: Packages

- [x] **K1: Record which packages are already installed**
  - **Where:** VM
  - **Run:** `ssh career-vm 'dpkg-query -W -f="\${Package} \${Status}\n" git sqlite3 2>&1'`
  - **Why:** Ubuntu cloud images usually ship `git`. The undo step must remove only what this plan installed.
  - **Check:** write down which of `git` and `sqlite3` show `install ok installed`.
  - **Undo:** nothing to undo.
  - **Result (2026-09-29):** `git install ok installed`. `sqlite3` was not installed (`no packages found matching sqlite3`).

- [x] **K2: Install git and sqlite3**
  - **Where:** VM
  - **Run:** `ssh career-vm 'sudo apt-get update && sudo apt-get install -y git sqlite3'`
  - **Why:** git clones the code, and sqlite3 lets us inspect the database on the VM.
  - **Check:** `ssh career-vm 'git --version && sqlite3 --version'` prints both versions.
  - **Undo:** `ssh career-vm 'sudo apt-get remove -y sqlite3'`. Per K1, `git` was preinstalled, so don't remove it.
  - **Result (2026-09-29):** `git version 2.43.0`, `sqlite3 3.45.1`. Both report `install ok installed`.

## Section 3: Code

- [x] **C1: Clone the repo**
  - **Where:** VM
  - **Run:** `ssh career-vm 'git clone https://github.com/ethanjad/career-platform.git ~/career-platform'`
  - **Why:** gets the application code onto the VM. The repo is public, so no credentials are needed.
  - **Check:** `ssh career-vm 'git -C ~/career-platform log -1 --oneline'` matches the laptop's `git -C ~/Desktop/github/career-platform log origin/main -1 --oneline` (currently `65fbf8c Merge feature/career-platform`).
  - **Undo:** `ssh career-vm 'rm -rf ~/career-platform'`. Stop uvicorn first (PR1 undo) if it's running, and copy `data/resume.db` off the VM first if the site has been live.
  - **Result (2026-09-29):** cloned at `65fbf8c`, matching the laptop's `origin/main`. The working tree is clean, and `data/` contains only the tracked files (`profile_snapshot.json`, plus `.gitkeep`, which `ls` hides).

- [x] **C2: Deploy the seeding fix (fact 4)**
  - **Where:** laptop (merge + push), then VM (pull)
  - **Run:**
    ```bash
    # laptop
    git -C ~/Desktop/github/career-platform switch main
    git -C ~/Desktop/github/career-platform merge --ff-only fix/seed-only-new-database
    git -C ~/Desktop/github/career-platform push origin main
    # VM
    ssh career-vm 'git -C ~/career-platform pull --ff-only && git -C ~/career-platform log -1 --oneline'
    ```
  - **Why:** your decision was to fix the seeding before the site goes live, so the fix must be on the VM before PR1.
  - **Check:**
    - `git ls-remote origin main` equals the laptop's `git rev-parse HEAD` (`a02219b…`), and the VM prints `a02219b fix: seed only a new database`.
    - `ssh career-vm 'cd ~/career-platform && ~/.local/bin/uv run pytest -q'` gives 9 passed.
  - **Undo:** `git revert a02219b && git push origin main`, then pull on the VM.
  - **Result (2026-09-29):** approved, merged fast-forward and pushed. `git ls-remote origin main` = local `HEAD` = `a02219bace1a…`. The VM prints `a02219b fix: seed only a new database` and `9 passed, 1 warning`.
  - **History:** the fix was written test-first. RED: the 2 new tests failed on duplicate rows (skills 16≠8, projects 4≠2, links 6≠3) and on the restored seed row (`[1, 2] != [2]`). GREEN: 9 passed. Checked against a scratch copy of your real DB: counts stayed `[2, 2, 16, 4, 6]` after 2 loads. Committed `a02219b` on `fix/seed-only-new-database`.

## Section 4: Python

- [x] **P1: Install uv on the laptop**
  - **Where:** laptop
  - **Run:** `brew install uv`
  - **Why:** the lock file has to be generated before the VM can `uv sync` from it.
  - **Check:** `uv --version` prints a version.
  - **Undo:** `brew uninstall uv`
  - **Result (2026-09-29):** `uv 0.12.19 (Homebrew 2026-09-24 aarch64-apple-darwin)`.

- [x] **P2: Create `pyproject.toml` and `uv.lock` from `requirements.txt`**
  - **Where:** laptop, in `~/Desktop/github/career-platform`
  - **Run:**
    ```bash
    cd ~/Desktop/github/career-platform
    git switch -c chore/uv-lock
    uv init --bare --name career-platform --python 3.12
    uv add -r requirements.txt
    ```
  - **Why:** `uv sync` needs a project file and a lock file. `--python 3.12` sets `requires-python = ">=3.12"`, which matches Ubuntu 24.04's system Python. `requirements.txt` stays in place for the README's pip path.
  - **Check:**
    - `git status --short` shows only `pyproject.toml` and `uv.lock` as new (`.venv/` is ignored).
    - `uv lock --check` exits 0.
    - `uv run pytest -q` passes. The tests use `tmp_path`, so they don't touch any real database.
  - **Undo:** `git switch main && git branch -D chore/uv-lock && rm -rf .venv`
  - **Result (2026-09-29):** only `pyproject.toml` and `uv.lock` are new (plus this untracked plan file). `uv lock --check` exited 0 (32 packages), and `python-dotenv` is in the lock. `uv run pytest -q` gave `7 passed, 1 warning`. The warning is a Starlette deprecation notice about `httpx` in `TestClient`, which only affects the tests.

- [x] **P3: Commit, merge to main, push**
  - **Where:** laptop
  - **Run:**
    ```bash
    git add pyproject.toml uv.lock
    git commit -m "chore: add uv project and lock file for VM deploy"
    git switch main
    git merge --ff-only chore/uv-lock
    git push origin main
    ```
  - **Why:** the VM installs from what's on GitHub.
  - **Check:** `git ls-remote origin main` shows the same SHA as `git rev-parse HEAD`.
  - **Undo:** `git revert <commit-sha> && git push origin main`
  - **Result (2026-09-29):** `8d5e08a` was merged fast-forward into `main` and pushed. `git ls-remote origin main` = `8d5e08ac11f9…` = local `HEAD`.

- [x] **P4: Pull the lock file onto the VM**
  - **Where:** VM
  - **Run:** `ssh career-vm 'git -C ~/career-platform pull --ff-only'`
  - **Why:** C1 cloned the repo before the lock file existed.
  - **Check:** `ssh career-vm 'ls ~/career-platform/pyproject.toml ~/career-platform/uv.lock'` lists both files.
  - **Undo:** `ssh career-vm 'git -C ~/career-platform reset --hard 65fbf8c'`
  - **Result (2026-09-29):** VM at `8d5e08a`, and both files are listed.

- [x] **P5: Install uv on the VM**
  - **Where:** VM
  - **Run:** `ssh career-vm 'curl -LsSf https://astral.sh/uv/install.sh | sh'`
  - **Why:** uv isn't in Ubuntu's apt repos. The installer puts `uv` in `~/.local/bin`.
  - **Check:** `ssh career-vm '~/.local/bin/uv --version'`
  - **Undo:** `ssh career-vm 'rm -f ~/.local/bin/uv ~/.local/bin/uvx ~/.local/bin/env ~/.local/bin/env.fish && rm -rf ~/.local/share/uv ~/.cache/uv && sed -i "/\.local\/bin\/env/d" ~/.bashrc ~/.profile'`. The installer adds `. "$HOME/.local/bin/env"` to `~/.bashrc` and `~/.profile`, and the `sed` removes those lines.
  - **Result (2026-09-29):** `uv 0.12.21 (x86_64-unknown-linux-gnu)`. Shell edits: `~/.bashrc:119` and `~/.profile:29`.

- [x] **P6: `uv sync` from the lock file**
  - **Where:** VM
  - **Run:** `ssh career-vm 'cd ~/career-platform && ~/.local/bin/uv sync --locked'`
  - **Why:** `--locked` installs exactly the versions in `uv.lock`, and fails instead of quietly re-resolving if the lock is out of date.
  - **Check:**
    - `ssh career-vm 'cd ~/career-platform && ~/.local/bin/uv run python -c "import fastapi, uvicorn, jinja2, dotenv; print(\"ok\")"'` prints `ok`. `dotenv` must import, because `--env-file` in PR1 depends on it.
    - `ssh career-vm 'cd ~/career-platform && ~/.local/bin/uv run pytest -q'` passes.
  - **Undo:** `ssh career-vm 'rm -rf ~/career-platform/.venv'`
  - **Result (2026-09-29):** synced with no lock changes, using Python 3.12.3 (system). Imports printed `ok`, and pytest gave `7 passed, 1 warning` (the same Starlette/httpx deprecation as on the laptop). `git status` is clean, and `data/` contains only the tracked files.

## Section 5: Config

- [x] **F1: Create `.env` from the example, with a real admin secret**
  - **Where:** VM
  - **Run:**
    ```bash
    ssh career-vm 'cd ~/career-platform \
      && cp -n .env.example .env \
      && chmod 600 .env \
      && sed -i "s/^ADMIN_SECRET=.*/ADMIN_SECRET=$(openssl rand -hex 32)/" .env'
    ```
  - **Why:** the example secret is public on GitHub. `cp -n` never overwrites an existing `.env`. `HOST=127.0.0.1`, `PORT=8000`, `DATABASE_PATH=data/resume.db` and `ENABLE_FALLBACK=true` stay as in the example.
  - **Check:**
    - `ssh career-vm 'cd ~/career-platform && stat -c %a .env && grep -c replace-with .env; grep -E "^(DATABASE_PATH|HOST|PORT)=" .env'`
      Expected: `600`, then `0`, then `DATABASE_PATH=data/resume.db`, `HOST=127.0.0.1`, `PORT=8000`.
    - `ssh career-vm 'cd ~/career-platform && git check-ignore .env'` prints `.env`, so it can never be committed.
  - **Undo:** `ssh career-vm 'rm ~/career-platform/.env'`
  - **Result (2026-09-29):** `600 azureuser`, placeholder count `0`, `DATABASE_PATH=data/resume.db`, `ENABLE_FALLBACK=true`, `HOST=127.0.0.1`, `PORT=8000`, secret length 64, `git check-ignore .env` → `.env`. Ubuntu's `cp` warns that `-n` is non-portable (`--update=none` is the new spelling). It's only a warning, and the no-overwrite behavior held.

- [ ] **F2: Save the admin secret somewhere you control**
  - **Where:** laptop, reading from the VM
  - **Run:** in **your own terminal**, not through Claude, so the secret stays out of the chat log: `ssh career-vm 'grep ^ADMIN_SECRET= ~/career-platform/.env'`. Then store the value in your password manager.
  - **Why:** you need it to call `/admin/*`. It exists only on the VM.
  - **Check:** the value is in your password manager.
  - **Status (2026-09-29):** waiting for you to confirm it's saved.
  - **Undo:** nothing to undo.

## Section 6: Data

**Uvicorn must not start, and nothing may request `/`, until D4 passes.**

- [x] **D1: Make a consistent copy and record its fingerprint**
  - **Where:** laptop
  - **Run:**
    ```bash
    sqlite3 ~/Desktop/github/resume.db ".backup /tmp/resume-upload.db"
    sqlite3 -readonly /tmp/resume-upload.db "PRAGMA integrity_check; SELECT 'projects',count(*) FROM projects; SELECT 'skills',count(*) FROM skills; SELECT 'experience',count(*) FROM experience;"
    shasum -a 256 /tmp/resume-upload.db
    ```
  - **Why:** `.backup` produces a clean single file even if the DB is open somewhere. The counts and hash are what D4 compares against.
  - **Check:** `ok`, then counts (expected today: projects 4, skills 16, experience 2). Write down the counts and the sha256.
  - **Undo:** `rm /tmp/resume-upload.db`. The original `~/Desktop/github/resume.db` is never modified.
  - **Result (2026-09-29):** `ok`, projects 4, skills 16, experience 2. Copy sha256 `ec05e02974a14f2f5b12aa24819b63a569f4923275420a5fe286d5d38e4914cd`. The original's sha256 is `7e769ff415e03d49bf4f89c06d18fa834db4053b5e0a2e5804b166391b88183a`; it differs because `.backup` rebuilds the file, so compare against the copy's hash.

- [x] **D2: Confirm the VM has no database yet**
  - **Where:** VM
  - **Run:** `ssh career-vm 'ls -la ~/career-platform/data/'`
  - **Why:** if `resume.db` already exists, something created a seed DB. It would be overwritten, but it also means the order was broken somewhere.
  - **Result (2026-09-29):** only `.gitkeep` and `profile_snapshot.json` were listed.
  - **Check:** only `.gitkeep` and `profile_snapshot.json` are listed. If `resume.db` exists, run `mv ~/career-platform/data/resume.db ~/career-platform/data/resume.db.seed-$(date +%s)` on the VM before continuing.
  - **Undo:** nothing to undo.

- [x] **D3: Copy the database to the VM**
  - **Where:** laptop
  - **Run:** `scp /tmp/resume-upload.db career-vm:career-platform/data/resume.db`
  - **Why:** puts your data where `DATABASE_PATH=data/resume.db` points.
  - **Check:** covered by D4.
  - **Undo:** `ssh career-vm 'rm ~/career-platform/data/resume.db'`

- [x] **D4: Verify the copy on the VM**
  - **Where:** VM
  - **Run:**
    ```bash
    ssh career-vm 'cd ~/career-platform/data \
      && chmod 600 resume.db \
      && sha256sum resume.db \
      && sqlite3 -readonly resume.db "PRAGMA integrity_check; SELECT count(*) FROM projects; SELECT count(*) FROM skills; SELECT count(*) FROM experience;"'
    ```
  - **Why:** proves the VM file is byte-for-byte the laptop file.
  - **Check:** the sha256 equals the one from D1, then `ok`, then three counts in the order projects, skills, experience, matching D1.
  - **Result (2026-09-29):** sha256 `ec05e029…14cd` (match), `ok`, 4 / 16 / 2, `600 azureuser 36864 bytes`.
  - **Undo:** same as D3.

- [x] **D5: Delete the temporary copy on the laptop**
  - **Where:** laptop
  - **Run:** `rm /tmp/resume-upload.db`
  - **Check:** `ls /tmp/resume-upload.db` reports no such file.
  - **Undo:** nothing to undo. Re-run D1 if needed.
  - **Result (2026-09-29):** removed. The laptop original's sha256 is still `7e769ff4…183a`.

## Section 7: Processes

- [x] **PR1: Start uvicorn in the background, surviving logout**
  - **Where:** VM
  - **Run:**
    ```bash
    ssh career-vm 'cd ~/career-platform && nohup setsid -f ~/.local/bin/uv run --locked \
      uvicorn app.main:app --env-file .env --host 127.0.0.1 --port 8000 \
      > ~/uvicorn.log 2>&1 < /dev/null'
    ```
  - **Why:**
    - `--env-file .env` is the only way the app sees `ADMIN_SECRET` and the other settings.
    - `--host 127.0.0.1` keeps it private, since the NSG only allows port 22 anyway.
    - `nohup setsid -f` detaches it from the SSH session. `-f` makes `setsid` fork and return right away, and the child's output already goes to the log, so the `ssh` command exits. The original version used `&` instead of `-f`; its background subshell kept the SSH session's output open and the local `ssh` never returned (see Result).
  - **Check:**
    - `ssh career-vm 'ss -ltnp | grep 8000'` shows `127.0.0.1:8000`.
    - `ssh career-vm 'tail -5 ~/uvicorn.log'` shows `Uvicorn running on http://127.0.0.1:8000` and no traceback.
  - **Undo:** `ssh career-vm 'pkill -f "[u]vicorn app.main:app"'`, then confirm `ssh career-vm 'pgrep -af "[u]vicorn app.main"'` prints nothing. The `[u]` keeps the pattern from matching the remote shell running the command; without it, the shell kills its own session. See the Progress log, 2026-09-29.
  - **Result (2026-09-29):** ran the original `&` version. `ss` → `127.0.0.1:8000 users:(("uvicorn",pid=39936))`. The log has `Loading environment from '.env'` … `Uvicorn running on http://127.0.0.1:8000` and no errors. The local `ssh` hung, so I killed it; uvicorn kept running (checked from a new SSH session). An idle leftover `bash -c …` (pid 39931) is the parent of `uv` (39932). The undo's `pkill -f "uvicorn app.main:app"` matches all three processes.
  - **Note:** this does not survive a VM reboot or deallocation. A systemd unit would be a separate follow-up; it's not in your outline.

## Section 8: Verify

- [x] **V1: The site answers on the VM (from a fresh SSH session)**
  - **Where:** VM
  - **Run:** `ssh career-vm 'curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/'`
  - **Why:** a new SSH connection proves the process outlived the session that started it.
  - **Check:** `200`
  - **Undo:** nothing to undo. After C2, requests no longer add rows (fact 4).
  - **Result (2026-09-29):** `200`.

- [x] **V2: The page shows your data, read live from `resume.db`**
  - **Where:** VM
  - **Run:**
    ```bash
    ssh career-vm 'cd ~/career-platform \
      && curl -s http://127.0.0.1:8000/ | grep -oE "Alex Carter|Revenue Trend Dashboard|Northwind Retail" | sort | uniq -c \
      && sqlite3 -readonly data/resume.db "SELECT count(*) FROM projects; SELECT count(*) FROM skills; SELECT count(*) FROM links;" \
      && (find data/profile_snapshot.json -newer data/resume.db | grep -q . && echo "snapshot rewritten" || echo "snapshot NOT rewritten") \
      && (grep -iE "error|traceback" ~/uvicorn.log || echo "log clean")'
    ```
  - **Why:**
    - The page content confirms rendering.
    - The snapshot being newer than `resume.db` proves the live DB was read. D3 copied `resume.db` in after the clone, so the snapshot starts out older. `load_public_profile()` rewrites the snapshot only after a successful DB read, and the fallback path never rewrites a valid snapshot. A timestamp is used rather than `git status` because the rewritten content could match the committed file byte for byte.
    - The counts prove the fix is live: they must still equal D1's (projects 4, skills 16, links 6) after the requests from V1 and V2.
  - **Check:** all three strings appear, counts are `4`, `16`, `6`, it prints `snapshot rewritten`, and the output ends with `log clean`.
  - **Result (2026-09-29):** `3 Alex Carter`, `1 Northwind Retail`, `2 Revenue Trend Dashboard`. Counts `4`, `16`, `6`. `snapshot rewritten`, `log clean`. Every item passed.
  - **Undo:** nothing to undo.

- [x] **V3: See it in your browser through an SSH tunnel**
  - **Where:** laptop
  - **Run:** `ssh -N -L 8000:127.0.0.1:8000 career-vm`, then open `http://localhost:8000` in your browser.
  - **Why:** visual check that CSS and templates load, without opening a public port.
  - **Check:** the styled resume page shows your profile, experience, projects, skills and links.
  - **Result (2026-09-29):** automated part only. Through `ssh -f -N -L 8000:127.0.0.1:8000 career-vm`, `/` → `200` with title `Alex Carter | Senior Business Analytics Student`, and `/static/styles.css` → `200 text/css`, 5017 B. The tunnel was closed afterwards. **The visual check in your browser is still for you to do.**
  - **Undo:** press Ctrl-C in the tunnel terminal.

- [x] **V4: The admin API rejects the default secret**
  - **Where:** VM
  - **Run:**
    ```bash
    ssh career-vm 'curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/admin/projects \
      -H "Content-Type: application/json" -H "X-Admin-Secret: change-me" -d "{}"'
    ```
  - **Why:** proves `.env` was loaded. Without it, `change-me` would be accepted.
  - **Check:** `401`. The request is rejected before anything is written.
  - **Result (2026-09-29):** `401`. The counts were rechecked afterwards and are still 4/16/6.
  - **Undo:** nothing to undo.

- [x] **V5: Nothing is exposed publicly**
  - **Where:** laptop
  - **Run:** `curl -s -m 5 -o /dev/null -w "%{http_code}\n" http://<VM_PUBLIC_IP>:8000/ || echo blocked`
  - **Why:** confirms the site is reachable only via the VM or the tunnel, as intended.
  - **Check:** `blocked` (or `000`).
  - **Result (2026-09-29):** `000`, then `blocked`.
  - **Undo:** nothing to undo.

---

## Full rollback (reverse order)

1. PR1 undo: stop uvicorn (`pkill -f "[u]vicorn app.main:app"`).
2. If the site was live, copy the data back first: `scp career-vm:career-platform/data/resume.db ~/Desktop/github/resume-from-vm.db`
3. C1 undo: `rm -rf ~/career-platform` on the VM. This also removes `.env`, the DB and `.venv`.
4. P5 undo: remove uv from the VM, including its lines in `~/.bashrc` and `~/.profile` (see P5).
5. K2 undo: `sudo apt-get remove -y sqlite3` (git was preinstalled; keep it).
6. P3 undo: revert the lock commit on `main`, if you don't want to keep it.
7. P1 undo: `brew uninstall uv` on the laptop, if unwanted.
8. S3 undo: remove the `career-vm` block from `~/.ssh/config`.
