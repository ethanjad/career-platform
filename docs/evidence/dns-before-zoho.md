# DNS records before Zoho Mail setup — ethanjad.me

- **Captured:** 2026-10-13
- **Source:** Cloudflare CLI (`cf` 1.0.0-beta.16), `cf dns records list --zone ethanjad.me`
- **Zone:** ethanjad.me (zone ID `98ee18a8cc9fec8913975c7306c00f37`, status active)
- **Nameservers:** kristin.ns.cloudflare.com, scott.ns.cloudflare.com
- **Record count:** 3

## Records

| Type | Name | Content | TTL | Proxied |
|------|------|---------|-----|---------|
| A | www.ethanjad.me | `<old Azure VM IP, redacted>` | Auto | No |
| CNAME | ethanjad.me | `mdkjjfll.up.railway.app` | Auto | No |
| TXT | _railway-verify.ethanjad.me | `"railway-verify=7431b2814bcb792dcce21c6781c95d1549e2c6e6d1ca0e4b4c4eb53524f5bdbf"` | Auto | No |

The `www` A record still pointed at the old Azure VM (since deleted; IP redacted 2026-10-21). On 2026-10-19 it was replaced by the Cloudflare redirect described in [dns-and-https.md](dns-and-https.md).

There are no MX, SPF, DKIM, or DMARC records yet, so the zone has no mail setup before Zoho is added.

## Raw CLI output

```json
[
  {
    "id": "86b88794bd783860b50f8dd63d7e2b20",
    "name": "www.ethanjad.me",
    "type": "A",
    "content": "<old Azure VM IP, redacted>",
    "proxiable": true,
    "proxied": false,
    "ttl": 1,
    "settings": {},
    "meta": {},
    "comment": null,
    "tags": [],
    "created_on": "2026-10-01T21:41:17.643936Z",
    "modified_on": "2026-10-01T21:41:17.643936Z"
  },
  {
    "id": "128a174e4de9d3e56bc19620715af0ad",
    "name": "ethanjad.me",
    "type": "CNAME",
    "content": "mdkjjfll.up.railway.app",
    "proxiable": true,
    "proxied": false,
    "ttl": 1,
    "settings": {
      "flatten_cname": false
    },
    "meta": {},
    "comment": null,
    "tags": [],
    "created_on": "2026-10-08T22:34:07.596628Z",
    "modified_on": "2026-10-08T22:34:07.596628Z"
  },
  {
    "id": "e0a70f480e4d681248b10bcd0d407a72",
    "name": "_railway-verify.ethanjad.me",
    "type": "TXT",
    "content": "\"railway-verify=7431b2814bcb792dcce21c6781c95d1549e2c6e6d1ca0e4b4c4eb53524f5bdbf\"",
    "proxiable": false,
    "proxied": false,
    "ttl": 1,
    "settings": {},
    "meta": {},
    "comment": null,
    "tags": [],
    "created_on": "2026-10-08T22:34:37.541617Z",
    "modified_on": "2026-10-08T22:34:37.541617Z"
  }
]
```
