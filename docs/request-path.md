# Request path: entering ethanjad.me in a browser

Drafted 2026-10-20 with Claude Code from the repository records, as a study aid. Labels ending in `?` are not recorded in this repository (home network details come from Exercise 01) and are unverified.

- The Azure diagram shows the site as it ran until the Railway cutover on 2026-10-08. Email and analytics were added after the cutover, so section 3 shows them.
- On Railway, `start.sh` runs one uvicorn process. `--workers 2` was only on Azure.
- On a database failure the app answers 503. The profile comes from the saved snapshot and Projects shows "temporarily unavailable" ([evidence](evidence/db-failure-503.md)).

## 1. Azure: hardware and services

```mermaid
flowchart LR
  subgraph HOME["Home network (details unverified, from Ex01)"]
    LAPTOP["Laptop<br/>browser + Wi-Fi NIC<br/>private IP via DHCP ?"]
    ROUTER["Home router box ?<br/>AP + switch + router/gateway<br/>NAT + stateful firewall<br/>DHCP server"]
    MODEM["Modem / ONT ?"]
    LAPTOP -->|"Wi-Fi"| ROUTER --> MODEM
  end

  ISP["ISP ?"]
  NET["Internet routers"]
  MODEM --> ISP --> NET

  subgraph DNS["DNS (separate exchange, UDP 53)"]
    RES["Recursive resolver ?<br/>(ISP or router-assigned)"]
    CF["Cloudflare authoritative<br/>kristin / scott.ns.cloudflare.com<br/>ethanjad.me A → VM public IP<br/>DNS only"]
    RES -->|"query / answer"| CF
  end
  LAPTOP -. "1. ethanjad.me? (UDP 53)" .-> RES

  subgraph AZ["Azure, Sweden Central"]
    NSG["NSG firewall<br/>allow TCP 80, 443 from any<br/>allow 22 from my IP only<br/>no rule for 8000"]
    subgraph VM["Ubuntu VM vm-career-platform<br/>public IP (redacted) / private 10.0.0.4"]
      NGINX["Nginx :80 / :443<br/>TLS ends here<br/>Let's Encrypt cert, certbot renews<br/>80 → 301 to https"]
      UV["uvicorn, systemd service<br/>127.0.0.1:8000, 2 workers"]
      APP["FastAPI app<br/>GET / → Jinja index.html"]
      DB[("data/resume.db<br/>SQLite file, opened in-process")]
      NGINX -->|"plain HTTP, loopback"| UV --> APP -->|"file read, no port"| DB
    end
    NSG --> NGINX
  end
  NET -->|"2. TCP 443 + TLS + HTTP"| NSG

  GA["Google Analytics<br/>gtag.js + collect"]
  LAPTOP -. "4. page_view / click (HTTPS)" .-> GA
```

## 2. Order of events (either host)

```mermaid
sequenceDiagram
  participant B as Browser (client)
  participant R as Resolver (server)
  participant C as Cloudflare DNS
  participant W as Web entry: Nginx (Azure) / Railway edge
  participant A as App (uvicorn + FastAPI)
  participant D as Database: SQLite file / PostgreSQL
  participant G as Google Analytics

  B->>R: ethanjad.me? (UDP 53, skipped if cached)
  R->>C: ask authoritative server
  C-->>R: address (Azure: VM IP / Railway: edge IPs, flattened CNAME)
  R-->>B: address
  B->>W: http://ethanjad.me (TCP 80)
  W-->>B: 301 → https://ethanjad.me
  B->>W: TCP 443 + TLS handshake (check hostname, dates, chain)
  Note over B,W: TLS ends at the web entry
  B->>W: GET / (encrypted)
  W->>A: GET / (plain HTTP, Azure: 127.0.0.1:8000 / Railway: $PORT)
  A->>D: read profile, experience, projects…
  D-->>A: rows (or failure → snapshot profile, no projects)
  A-->>W: 200 HTML (503 if the database failed)
  W-->>B: 200 HTML (encrypted)
  B->>W: GET /static/styles.css, font (same connection)
  B->>G: load gtag.js, send page_view
```

## 3. Railway today: web, data, email and analytics

Locations:

- **Railway:** the web service and Postgres. The Oct 8 deployment manifests list region `sfo`.
- **Cloudflare:** DNS and the `www` redirect, on its global anycast network.
- **Zoho Mail:** US data centre (Zoho account country `us`).
- **Google Analytics:** Google's servers.

Ports are the ones recorded or observed. `?` marks values not recorded in this repo.

### 3a. Web pages and analytics

```mermaid
flowchart LR
  B["Visitor's browser"]

  subgraph CFD["Cloudflare (global anycast)"]
    DNS["DNS for ethanjad.me, UDP/TCP 53<br/>apex CNAME → Railway<br/>(DNS only, flattened to A)"]
    WWW["www.ethanjad.me, proxied<br/>TCP 80/443, TLS ends here<br/>301 → https://ethanjad.me"]
  end

  subgraph RW["Railway, region sfo (provider runs OS, proxy, certs)"]
    EDGE["Railway edge<br/>TCP 443, TLS ends here (Let's Encrypt)<br/>TCP 80 → 301 to https"]
    CT["web container<br/>uvicorn on $PORT, 1 process<br/>--proxy-headers, disk wiped each deploy"]
    PG[("PostgreSQL 18<br/>private network, port ?")]
    EDGE -->|"plain HTTP +<br/>X-Forwarded-Proto"| CT -->|"Postgres protocol"| PG
  end

  GA["Google Analytics<br/>googletagmanager.com: gtag.js<br/>google-analytics.com/g/collect"]

  B -. "1. DNS lookup" .-> DNS
  B -. "www requests only" .-> WWW
  B -->|"2. GET /, HTTPS 443"| EDGE
  B -->|"3. page_view, click<br/>HTTPS 443"| GA
```

### 3b. Email (Zoho Mail, US)

```mermaid
flowchart LR
  subgraph IN["Incoming: someone emails ethan@ethanjad.me"]
    direction LR
    S1["Sender's mail server<br/>(Gmail, Microsoft 365)"] -. "MX lookup, port 53" .-> D1["Cloudflare DNS<br/>MX 10/20/50 → mx, mx2, mx3.zoho.com"]
    S1 -->|"SMTP, TCP 25, TLS ?"| Z1["Zoho inbound MX"] --> MB[("Zoho mailbox")]
  end
  subgraph OUT["Outgoing: I reply from Zoho"]
    direction LR
    ME["Me: Zoho web app"] -->|"HTTPS 443"| Z2["Zoho outbound<br/>165.173.180.0/24<br/>signs DKIM s=zmail"]
    Z2 -->|"SMTP, TCP 25, TLS 1.3"| R2["Receiver (Gmail)"]
    R2 -. "SPF / DKIM / DMARC lookups, port 53" .-> D2["Cloudflare DNS<br/>TXT: SPF, zmail._domainkey, _dmarc"]
  end
```

**What never touches Railway:**

- **Email.** It goes between mail servers and Zoho, steered by Cloudflare DNS.
- **Analytics.** The visitor's browser sends it straight to Google.

Railway only serves the web pages and holds the database.
