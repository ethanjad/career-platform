# How This Site Is Secured

## Current setup (updated October 18, 2026)

The site no longer runs on my Azure Virtual Machine. ethanjad.me is now hosted on Railway, and www.ethanjad.me is handled by Cloudflare, which redirects it to ethanjad.me. The VM is turned off and does not serve any traffic. The original write-up below describes the old VM setup.

**ethanjad.me (Railway).** My DNS record for ethanjad.me points to Railway. The certificate is issued by Let’s Encrypt (Intermediate CA “YR2”), covers ethanjad.me, and expires on January 6, 2027. Railway requests and renews this certificate automatically, so I no longer run certbot. Encryption begins in the visitor’s browser and ends at Railway’s edge proxy, which holds the private key. The proxy decrypts the request and passes it to my app inside Railway’s network. A visitor who uses http:// is redirected to https:// with a 301.

**www.ethanjad.me (Cloudflare redirect).** Railway’s plan only allows one custom domain per service, so instead of hosting www on Railway, I let Cloudflare answer for it. The www DNS record is proxied through Cloudflare and points to a placeholder address (192.0.2.1) that is never contacted. A Cloudflare redirect rule sends every request for www to the same page on ethanjad.me with a 301 permanent redirect, and the path and query string carry over (for example, https://www.ethanjad.me/privacy goes to https://ethanjad.me/privacy). This works for both http:// and https://. For www, encryption begins in the browser and ends at Cloudflare. Cloudflare holds the private key for its own certificate, which is issued by Let’s Encrypt (“YE2”), covers ethanjad.me and *.ethanjad.me, and is renewed by Cloudflare automatically. Because the redirect happens at Cloudflare, the request never travels any further.

**Open ports.** I no longer manage a server, so there is no SSH port (22) to protect. Visitors can only reach Railway and Cloudflare on the standard web ports, 443 (HTTPS) and 80 (HTTP, which only redirects to HTTPS).

```console
$ echo | openssl s_client -connect ethanjad.me:443 -servername ethanjad.me 2>/dev/null | openssl x509 -noout -subject -issuer -dates
subject=CN=ethanjad.me
issuer=C=US, O=Let's Encrypt, CN=YR2
notBefore=Oct  8 21:38:56 2026 GMT
notAfter=Jan  6 21:38:55 2027 GMT

$ curl -sI https://www.ethanjad.me/privacy | grep -iE '^(HTTP|location|server)'
HTTP/2 301
location: https://ethanjad.me/privacy
server: cloudflare
```

## Original setup (Azure VM, October 7, 2026)

In order to answer the question, “How do I know my data to my site is encrypted”, we must first acknowledge other contributing aspects.

The issuer of my certificate is Let’s Encrypt (Intermediate CA “YE2”). This is a certificate authority that is publicly trusted. The domains that are covered are ethanjad.me and www.ethanjad.me, expiring on January 4, 2027.

Renewal works through the use of a tool called certbot. It runs on my server and checks twice per day, scanning to determine if the expiration date of my certificate is upcoming. Certbot will ask Let’s Encrypt for a new certificate once the expiration date is within 30 days. Certbot will also check to verify if I own ethanjad.me. It does this by accessing my site over the internet. Afterwards, certbot will install the new certificate and reload nginx. My renewal test showed that I passed. The phrase “all simulated renewals succeeded” returned. The timer check confirmed that automatic check is turned on, along with the last and upcoming runs.

The ports that are open to the internet include 443 (HTTPS), 80 (HTTP), and 22 (SSH). Port 443 is open because it serves my site and is encrypted. Port 80 is open because it sends site visitors to the secured HTTPS. It also enables Let’s Encrypt to view my site when renewing. Port 22 is open because it allows me to log into the Azure User account and manage the site. The 3 addresses that can connect to my SSH port are my current laptop address, my server’s public address, and an older address from the LMU network.

Encryption begins in the visitor’s browser. More specifically, when they connect to https://ethanjad.me. Encryption ends at nginx within my Virtual Machine. This is because nginx contains the private key. It then decrypts the visitor request, before passing it onwards to the app over an unencrypted connection that never leaves the machine.

When a customer checks the certificate in Chrome, they can see 2 important lines: “Connection is secure” and “Certificate is valid”. The first line means that “Your information is private when sent to this site”. The second line contains data like the issuer, organization, and validity period.

```console
$ echo | openssl s_client -connect ethanjad.me:443 -servername ethanjad.me 2>/dev/null | openssl x509 -noout -subject -issuer -dates
subject=CN=ethanjad.me
issuer=C=US, O=Let's Encrypt, CN=YE2
notBefore=Oct  6 21:03:43 2026 GMT
notAfter=Jan  4 21:03:42 2027 GMT
```
