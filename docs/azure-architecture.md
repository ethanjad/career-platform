# Azure architecture, step by step

Drafted 2026-10-20 with Claude Code from the repository records. It shows the site as it ran on the Azure VM until the Railway cutover on 2026-10-08.

- **Colors:** blue is home, grey is the internet, orange is Azure, green is outside services.
- **`?`:** marks a detail not recorded in the repo.

Sources: `docs/evidence/ex03.md`, `docs/superpowers/plans/2026-10-01-operate-the-vm.md`, `docs/how-this-site-is-secured.md`, `docs/evidence/ex06.md`.

**Location and ports:**

- **Location:** Azure Sweden Central.
- **Inbound, through the NSG:** TCP 80 and 443 from anyone, and TCP 22 from my IP only.
- **App:** nginx proxied to `127.0.0.1:8000` over the loopback interface.
- **Database:** SQLite, a file opened inside the app, with no network port.
- **Cloudflare DNS:** port 53.

## 1. A visitor opens ethanjad.me

```mermaid
---
title: 1. A visitor opens ethanjad.me
---
sequenceDiagram
  autonumber
  box rgb(227,242,253) Home
    participant B as Laptop
  end
  box rgb(241,241,241) Internet
    participant DNS as Cloudflare DNS
    participant NET as Router + internet ?
  end
  box rgb(255,243,224) Azure VM
    participant F as Firewall
    participant N as Nginx
    participant A as App
    participant DB as SQLite file
  end

  B->>DNS: Where is ethanjad.me?
  DNS-->>B: VM public IP
  B->>NET: Send request, port 443
  NET->>F: Carry it to Azure
  F->>N: Port 443 allowed
  N->>A: Decrypt, pass it on
  A->>DB: Read my profile
  A-->>N: HTML page
  N-->>B: Encrypted page back
```

## 2. Updating the site

```mermaid
---
title: 2. Updating the site
---
sequenceDiagram
  autonumber
  box rgb(227,242,253) Home
    participant L as Laptop
  end
  box rgb(232,245,233) Outside
    participant G as GitHub
  end
  box rgb(255,243,224) Azure VM
    participant V as VM
    participant A as App
  end

  L->>G: git push
  L->>V: SSH in (only my IP allowed)
  V->>G: git pull
  V->>A: Restart the app
  L->>A: Check the site works
```

## 3. Keeping it running

```mermaid
---
title: 3. Keeping it running
---
sequenceDiagram
  autonumber
  box rgb(255,243,224) Azure VM
    participant SD as systemd
    participant A as App
    participant C as certbot
    participant N as Nginx
  end
  box rgb(232,245,233) Outside
    participant LE as Let's Encrypt
  end

  SD->>A: VM boots: start the app
  SD->>A: App crashes: restart it
  C->>C: Certificate expiring soon?
  C->>LE: Prove I own ethanjad.me
  LE-->>C: New certificate
  C->>N: Install it
```

A full reboot test was never run before the VM was deleted on 2026-10-19. See [azure-vm-retired.md](evidence/azure-vm-retired.md).

## 4. Email

```mermaid
---
title: 4. Email
---
sequenceDiagram
  autonumber
  box rgb(232,245,233) Outside
    participant GM as Gmail
  end
  box rgb(241,241,241) Internet
    participant DNS as Cloudflare DNS
  end
  box rgb(232,245,233) Outside
    participant Z as Zoho Mail
  end

  GM->>DNS: Where does ethanjad.me mail go?
  GM->>Z: Deliver the message
  Z->>GM: I reply from Zoho
  GM->>DNS: Check SPF, DKIM, DMARC
  GM->>GM: All pass, so inbox
```

## 5. Analytics

```mermaid
---
title: 5. Analytics
---
sequenceDiagram
  autonumber
  box rgb(227,242,253) Visitor
    participant B as Browser
  end
  box rgb(232,245,233) Outside
    participant GA as Google Analytics
  end

  B->>GA: Page loads: page_view
  B->>GA: Click LinkedIn: click
```

Email and analytics never touch the VM. They were added after the move to Railway, and they work the same on either host.
