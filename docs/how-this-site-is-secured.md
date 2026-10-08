# How This Site Is Secured

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
