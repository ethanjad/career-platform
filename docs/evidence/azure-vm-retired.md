# Azure VM: how it ran, and how it was retired

The site ran on the Azure VM `vm-career-platform` (Ubuntu 24.04, swedencentral) until the Railway cutover on 2026-10-08. This page records what happened to the VM afterwards and what was and wasn't tested while it existed.

## What the activity log shows (read 2026-10-21)

From `az monitor activity-log list --offset 30d` with read-only queries. Subscription IDs are left out.

| Time (UTC) | Event | By |
|---|---|---|
| 2026-10-14 07:00:57 | `virtualMachines/deallocate` succeeded | an Azure service identity, not a user sign-in |
| 2026-10-19 06:55–06:57 | auto-shutdown schedule, disk, network interface, VM, public IP, virtual network and NSG deleted | my account |
| 2026-10-19 06:57:52 | resource group `rg-career-platform` deleted | my account |

- **Stopped by the auto-shutdown schedule.** The VM had an auto-shutdown schedule (the `DevTestLab/schedules` resource deleted on 2026-10-19). The deallocation at exactly 07:00 UTC (midnight Pacific) matches that schedule.
- **Nothing is left in Azure.** On 2026-10-21, `az group list` shows only `NetworkWatcherRG`, and `az vm list` is empty. There is no VM to restart and no NSG to change.

## Restart behaviour: configured, never tested by reboot

**No controlled reboot was ever run and recorded.** The VM plan (`docs/superpowers/plans/2026-10-01-operate-the-vm.md`) left the crash and reboot tests to me, and the VM was deleted before they were done.

What *was* recorded:

- On 2026-10-01, both services showed `enabled` and `active`.
- On 2026-10-08, a manual `sudo systemctl restart career-platform` brought the app back `active`, with no journal errors.

The restart behaviour came from this configuration, all recorded in the VM plan:

| Piece | Setting | What it does after a reboot or crash |
|---|---|---|
| App service `/etc/systemd/system/career-platform.service` | `systemctl enable` + `WantedBy=multi-user.target` | Starts the app at every boot, with no SSH needed |
| | `After=` / `Wants=network-online.target` | Waits for networking before starting |
| | `Restart=always`, `RestartSec=3` | Restarts the app 3 s after any exit |
| | `WorkingDirectory=/home/azureuser/career-platform` | Opens the real `data/resume.db`, not a new demo database |
| | `--env-file .env` | Loads `ADMIN_SECRET` and the other settings without a login shell |
| | `--host 127.0.0.1 --port 8000 --workers 2` | Keeps the app private behind nginx; one worker can keep serving while the other restarts |
| nginx | Enabled by the apt package; drop-in `Restart=on-failure` | Starts at boot, restarts after a crash, proxies to `127.0.0.1:8000` |

## Final NSG rules

The NSG `vm-career-platformNSG` was deleted on 2026-10-19. The last recorded rules (VM plan, 2026-10-08) are below. IP addresses are described rather than listed.

| Rule | Priority | Port | Source |
|---|---|---|---|
| `Allow-SSH-Laptop` | 300 | 22 | the VM's own public IP and an old laptop IP. Neither was needed, and **it was never tightened** |
| `Allow-HTTP-80` | 310 | 80 | any |
| `Allow-HTTPS-443` | 320 | 443 | any |
| `AllowSSHFromMyIP` | 1000 | 22 | the laptop's IP at the time |

There was no rule for port 8000. `Allow-SSH-Laptop` should have been deleted, since `AllowSSHFromMyIP` already covered SSH from the laptop.
