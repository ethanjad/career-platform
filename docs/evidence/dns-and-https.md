# DNS records and HTTPS for ethanjad.me

DNS for `ethanjad.me` is hosted on Cloudflare (nameservers `kristin.ns.cloudflare.com`, `scott.ns.cloudflare.com`). The records before email was added are in [dns-before-zoho.md](dns-before-zoho.md).

## Domain control (captured 2026-10-25 21:00 PDT)

How control works:

1. **I register the domain.** `ethanjad.me` is registered to me at Namecheap, through the GitHub Student Pack.
2. **The registrar delegates DNS to Cloudflare.** At Namecheap I set the domain's nameservers to the two Cloudflare servers assigned to my account.
3. **Cloudflare answers for the domain.** It accepted the zone (status *active*), and every record below is managed in my Cloudflare account.

Three independent sources agree:

```
$ whois ethanjad.me            (registry and registrar, abridged)
Domain Name: ethanjad.me
Registrar: NameCheap, Inc.
Creation Date: 2026-10-01T01:39:32Z
Registry Expiry Date: 2027-10-01T01:39:32Z
Domain Status: clientTransferProhibited
Name Server: kristin.ns.cloudflare.com
Name Server: scott.ns.cloudflare.com

$ dig +short NS ethanjad.me @1.1.1.1      (what the public internet sees)
kristin.ns.cloudflare.com.
scott.ns.cloudflare.com.

$ cf zones list                           (my Cloudflare account)
ethanjad.me | status active | plan Free Website | name_servers ['kristin.ns.cloudflare.com', 'scott.ns.cloudflare.com'] | activated 2026-10-01T21:58:52
```

**`clientTransferProhibited`** is the registrar lock, which stops the domain being moved to another registrar without my action. The registration runs to **2027-10-01** and must be renewed before then (README "Costs, cleanup and limitations").

## Current records (captured 2026-10-21 01:36 PDT)

Captured with `cf dns records list --zone ethanjad.me` (`cf` 1.0.0-beta.16) and shown one record per line. `TTL` is `1` (Auto) for every record.

```
A     www.ethanjad.me                    proxied=True  modified=2026-10-19  192.0.2.1
CNAME ethanjad.me                        proxied=False modified=2026-10-08  mdkjjfll.up.railway.app
MX    ethanjad.me                    10  proxied=False modified=2026-10-13  mx.zoho.com
MX    ethanjad.me                    20  proxied=False modified=2026-10-13  mx2.zoho.com
MX    ethanjad.me                    50  proxied=False modified=2026-10-13  mx3.zoho.com
TXT   _dmarc.ethanjad.me                 proxied=False modified=2026-10-13  "v=DMARC1; p=none; rua=mailto:ethan@ethanjad.me"
TXT   _railway-verify.ethanjad.me        proxied=False modified=2026-10-08  "railway-verify=7431b2814bcb792dcce21c6781c95d1549e2c6e6d1ca0e4b4c4eb53524f5bdbf"
TXT   ethanjad.me                        proxied=False modified=2026-10-13  "v=spf1 include:zohomail.com ~all"
TXT   ethanjad.me                        proxied=False modified=2026-10-13  "zoho-verification=zb86256365.zmverify.zoho.com"
TXT   zmail._domainkey.ethanjad.me       proxied=False modified=2026-10-13  "v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDjjk5Kw+OXH9iiBPSnfUFFKOiYt2zyu3G+8OgNj2sA4RqcZYgpgAiLo6VWDlwOHMLKTR4u1idHi+GPhfKQNK0sFRV9Fshpm4MY6CcDc1rwkQgeBrQaEDBcwsoW8CKqILCH9WQACUmiQ3D8/67bWsz1HrKg0YtZO45rj3GrNPw/AQIDAQAB"
```

## What each record is for

| Record | Purpose |
|---|---|
| `CNAME ethanjad.me → mdkjjfll.up.railway.app` | **The website.** Sends the root domain to the Railway service. Cloudflare flattens a CNAME at the root, so public resolvers get an A record for Railway's edge. It's DNS only (not proxied), so Railway terminates TLS with its own certificate. |
| `TXT _railway-verify` | Proves to Railway that I control the domain, so Railway would attach it and issue the certificate. |
| `A www → 192.0.2.1`, proxied | **The www redirect.** Proxied means visitors reach Cloudflare, never this address. `192.0.2.1` is a reserved documentation address that is never contacted. A Cloudflare redirect rule sends every `www` request to the same path on `https://ethanjad.me` with a 301. |
| `MX` ×3 (`mx`, `mx2`, `mx3.zoho.com`, priority 10/20/50) | **Incoming mail.** Tells other mail servers to deliver `@ethanjad.me` mail to Zoho. Lower priority is tried first, and the others are backups. |
| `TXT zoho-verification=…` | Proves to Zoho that I own the domain. |
| `TXT v=spf1 include:zohomail.com ~all` | **SPF.** Lists Zoho's servers as allowed to send mail for `ethanjad.me`. `~all` asks receivers to treat mail from anywhere else as suspicious (soft fail). |
| `TXT zmail._domainkey` | **DKIM.** The public key receivers use to check the signature Zoho adds to each outgoing message (selector `zmail`). |
| `TXT _dmarc` `p=none` | **DMARC.** Tells receivers what to do when SPF/DKIM don't line up with the From domain. `p=none` means only monitor, don't reject. Reports go to `ethan@ethanjad.me`. |

Public DNS (`dig @1.1.1.1`, same time) agreed:

- `ethanjad.me A 69.46.46.65` (Railway, through the flattened CNAME)
- `www.ethanjad.me A 104.21.25.167 172.67.134.101` (Cloudflare proxy addresses)
- the same MX, SPF and DMARC values

## www and HTTPS checks (2026-10-21 01:36 PDT)

```
$ curl -sI http://www.ethanjad.me/
HTTP/1.1 301 Moved Permanently
Location: https://ethanjad.me/
Server: cloudflare

$ curl -sI https://www.ethanjad.me/
HTTP/2 301
location: https://ethanjad.me/
server: cloudflare

$ curl -sI https://www.ethanjad.me/privacy?x=1
HTTP/2 301
location: https://ethanjad.me/privacy?x=1
server: cloudflare

$ curl -sI http://ethanjad.me/
HTTP/1.1 301 Moved Permanently
location: https://ethanjad.me/

$ curl -sL http://www.ethanjad.me/  -> hops 1, final https://ethanjad.me/ -> 200, ssl_verify_result=0
$ curl -sL https://www.ethanjad.me/ -> hops 1, final https://ethanjad.me/ -> 200, ssl_verify_result=0
```

Certificates (`openssl s_client -servername <host>`):

| Host | Served by | Issuer | Covers | Expires |
|---|---|---|---|---|
| `www.ethanjad.me` | Cloudflare | Let's Encrypt `YE2` | `*.ethanjad.me`, `ethanjad.me` | 2026-12-30 |
| `ethanjad.me` | Railway | Let's Encrypt `YR2` | `ethanjad.me` | 2027-01-06 |

**Result**

- Both `http://www.ethanjad.me` and `https://www.ethanjad.me` land on `https://ethanjad.me/` in one 301, keeping the path and query.
- The final page returns 200, and certificate verification passed (`ssl_verify_result=0`).
- Plain `http://ethanjad.me` redirects to HTTPS.

**Note:** `curl -sI https://ethanjad.me/` (a HEAD request) returns `405`, because the app's routes accept only GET. Browsers use GET, so visitors are unaffected, which is why the landing checks above use GET.
