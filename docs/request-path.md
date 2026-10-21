# Request path: entering ethanjad.me in a browser

Drafted 2026-10-20 with Claude Code from the repository records, as a study aid. Labels ending in `?` are not recorded in this repository (home network details come from Exercise 01) and are unverified.

- The Azure diagram shows the site as it ran until the Railway cutover on 2026-10-08.
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
    CF["Cloudflare authoritative<br/>kristin / scott.ns.cloudflare.com<br/>ethanjad.me A → 135.225.24.52<br/>DNS only"]
    RES -->|"query / answer"| CF
  end
  LAPTOP -. "1. ethanjad.me? (UDP 53)" .-> RES

  subgraph AZ["Azure, Sweden Central"]
    NSG["NSG firewall<br/>allow TCP 80, 443 from any<br/>allow 22 from my IP only<br/>no rule for 8000"]
    subgraph VM["Ubuntu VM vm-career-platform<br/>public 135.225.24.52 / private 10.0.0.4"]
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

## 3. What changes on Railway

```mermaid
flowchart LR
  B["Browser"]
  subgraph CFD["Cloudflare DNS"]
    APEX["ethanjad.me CNAME → mdkjjfll.up.railway.app<br/>DNS only, flattened to A records"]
    WWW["www.ethanjad.me proxied<br/>redirect rule → 301 to ethanjad.me<br/>TLS ends at Cloudflare"]
  end
  subgraph RW["Railway (provider runs OS, proxy, certs)"]
    EDGE["Railway edge<br/>TLS ends here, Let's Encrypt, auto-renew<br/>http → https redirect"]
    CT["web container<br/>start.sh: uvicorn on $PORT<br/>--proxy-headers, 1 process<br/>disk wiped each deploy"]
    PG[("PostgreSQL service<br/>DATABASE_URL = Postgres.DATABASE_URL<br/>private network")]
    EDGE -->|"plain HTTP + X-Forwarded-Proto"| CT -->|"TCP, Postgres protocol"| PG
  end
  B -. "DNS lookup" .-> APEX
  B -->|"TCP 443 + TLS"| EDGE
  B -. "www requests only" .-> WWW
```
