# Zoho header check: does mail from ethanjad.me authenticate?

**What this checks.** A message sent from my Zoho mailbox (`ethan@ethanjad.me`) to an outside Gmail account. I read the full headers of the received copy and checked which server handled it, whether it travelled encrypted, and whether SPF, DKIM and DMARC passed for `ethanjad.me`.

- **Message:** "Re: test hi", sent from Zoho on 2026-10-18 at 23:00:16 PDT.
- **Source:** Gmail → the received message → ⋮ → *Show original*. Pasted into the session on 2026-10-22.
- **Edits:** the Gmail address is replaced with `[gmail-user]`. Long signature values (`b=`) are cut with `…`. The body is left out. Header lines are unwrapped, and nothing else is changed.

## Headers (received copy, bottom = oldest)

Mail headers are read **bottom-up**: each server adds its lines on top.

```
Delivered-To: [gmail-user]@gmail.com
Received: by 2002:a05:6a10:ef5e:b0:75b:680a:ca37 with SMTP id tu30csp6481636pxb; Sun, 18 Oct 2026 23:00:18 -0700 (PDT)
X-Received: by 2002:a05:6a00:2992:b0:882:bba:8791 with SMTP id d2e1a72fcca58-8a04cd2673fmr4993598b3a.34.1792389618636; Sun, 18 Oct 2026 23:00:18 -0700 (PDT)
ARC-Seal: i=2; a=rsa-sha256; t=1792389618; cv=pass; d=google.com; s=arc-20260327; b=Mfq/aTo5…
ARC-Message-Signature: i=2; a=rsa-sha256; c=relaxed/relaxed; d=google.com; s=arc-20260327; h=user-agent:importance:mime-version:subject:references:in-reply-to:message-id:to:from:date:dkim-signature; bh=rlmJ4Gk6MQIoiy/9pJ4BdXkaE2KiYVPXpw7b0UydFvM=; …
ARC-Authentication-Results: i=2; mx.google.com; dkim=pass header.i=@ethanjad.me header.s=zmail header.b=UorepyL2; arc=pass (i=1 spf=pass spfdomain=ethanjad.me dkim=pass dkdomain=ethanjad.me dmarc=pass fromdomain=ethanjad.me>); spf=pass (google.com: domain of ethan@ethanjad.me designates 165.173.180.52 as permitted sender) smtp.mailfrom=ethan@ethanjad.me; dmarc=pass (p=NONE sp=NONE dis=NONE) header.from=ethanjad.me
Return-Path: <ethan@ethanjad.me>
Received: from sender6-of-o52.zoho.com (sender6-of-o52.zoho.com. [165.173.180.52]) by mx.google.com with ESMTPS id d2e1a72fcca58-8a000cbf739si13489042b3a.41.2026.10.18.23.00.18 for <[gmail-user]@gmail.com> (version=TLS1_3 cipher=TLS_AES_256_GCM_SHA384 bits=256/256); Sun, 18 Oct 2026 23:00:18 -0700 (PDT)
Received-SPF: pass (google.com: domain of ethan@ethanjad.me designates 165.173.180.52 as permitted sender) client-ip=165.173.180.52;
Authentication-Results: mx.google.com; dkim=pass header.i=@ethanjad.me header.s=zmail header.b=UorepyL2; arc=pass (i=1 spf=pass spfdomain=ethanjad.me dkim=pass dkdomain=ethanjad.me dmarc=pass fromdomain=ethanjad.me>); spf=pass (google.com: domain of ethan@ethanjad.me designates 165.173.180.52 as permitted sender) smtp.mailfrom=ethan@ethanjad.me; dmarc=pass (p=NONE sp=NONE dis=NONE) header.from=ethanjad.me
ARC-Seal: i=1; a=rsa-sha256; t=1792389617; cv=none; d=zohomail.com; s=zohoarc; b=h+TX7GKq…
ARC-Message-Signature: i=1; a=rsa-sha256; c=relaxed/relaxed; d=zohomail.com; s=zohoarc; t=1792389617; h=Content-Type:Date:Date:From:From:In-Reply-To:MIME-Version:Message-ID:Subject:Subject:To:To:Message-Id:Reply-To:Cc; bh=rlmJ4Gk6MQIoiy/9pJ4BdXkaE2KiYVPXpw7b0UydFvM=; b=iMJOoF9x…
ARC-Authentication-Results: i=1; mx.zohomail.com; dkim=pass header.i=ethanjad.me; spf=pass smtp.mailfrom=ethan@ethanjad.me; dmarc=pass header.from=<ethan@ethanjad.me>
DKIM-Signature: v=1; a=rsa-sha256; q=dns/txt; c=relaxed/relaxed; t=1792389617; s=zmail; d=ethanjad.me; i=ethan@ethanjad.me; h=Date:Date:From:From:To:To:Message-Id:Message-Id:In-Reply-To:Subject:Subject:MIME-Version:Content-Type:Reply-To:Cc; bh=rlmJ4Gk6MQIoiy/9pJ4BdXkaE2KiYVPXpw7b0UydFvM=; b=UorepyL2aWt7…
Received: from mail.zoho.com by mx.zohomail.com with SMTP id 1792389616095866.0260965752549; Sun, 18 Oct 2026 23:00:16 -0700 (PDT)
Date: Sun, 18 Oct 2026 23:00:16 -0700
From: Ethan Jad <ethan@ethanjad.me>
To: "Ethan J" <[gmail-user]@gmail.com>
Message-Id: <1a152bf11cf.3c649a1a691070.9212558604884528367@ethanjad.me>
In-Reply-To: <66FB54F0-273D-4699-9194-9AAA93D3F8F2@gmail.com>
Subject: Re: test hi
User-Agent: Zoho Mail
```

## The path, hop by hop

| # | Time (PDT) | Hop | What it shows |
|---|---|---|---|
| 1 | 23:00:16 | `mail.zoho.com` → `mx.zohomail.com` | Zoho's web app hands the message to Zoho's outbound mail system. This is inside Zoho. |
| 2 | 23:00:17 | Zoho signs | Zoho adds the **DKIM-Signature** for `d=ethanjad.me` and seals its own checks in **ARC** set `i=1`. |
| 3 | 23:00:18 | `sender6-of-o52.zoho.com [165.173.180.52]` → `mx.google.com` | The hand-off between companies. `ESMTPS` with **TLS 1.3** (`TLS_AES_256_GCM_SHA384`), so the message was encrypted in transit. |
| 4 | 23:00:18 | inside Google | Gmail records its results (**Authentication-Results**), adds ARC set `i=2`, and delivers to the inbox. |

Total time from Zoho to the Gmail inbox: about **2 seconds**.

## The three checks

| Check | Result | Why it passed | DNS record it used |
|---|---|---|---|
| **SPF**: is this server allowed to send for the envelope domain? | `spf=pass`, `smtp.mailfrom=ethan@ethanjad.me`, `client-ip=165.173.180.52` | Gmail looked up `ethanjad.me`'s SPF: `include:zohomail.com` → `include:spf.zohomail.com` → `ip4:165.173.180.0/24`, which contains the connecting IP. I followed the same chain on 2026-10-22. | `TXT ethanjad.me "v=spf1 include:zohomail.com ~all"` |
| **DKIM**: was the message signed by the domain and left unaltered? | `dkim=pass header.i=@ethanjad.me header.s=zmail header.b=UorepyL2` | Gmail fetched the public key at `zmail._domainkey.ethanjad.me`. The signature (`b=`) verified over the listed headers (`h=` includes From, To, Subject, Date, Message-Id), and the body hash (`bh=`) matched the body. | `TXT zmail._domainkey.ethanjad.me "v=DKIM1; k=rsa; p=…"` |
| **DMARC**: does a passing check match the visible From domain? | `dmarc=pass (p=NONE sp=NONE dis=NONE) header.from=ethanjad.me` | The From domain is `ethanjad.me`. Both SPF (`mailfrom` domain `ethanjad.me`) and DKIM (`d=ethanjad.me`) passed **and** use that same domain, so they are *aligned*. DMARC needs only one, and it got both. `dis=NONE` means Gmail took no action. | `TXT _dmarc.ethanjad.me "v=DMARC1; p=none; rua=…"` |

**What this proves.** Gmail confirmed, for this message, that `ethanjad.me`'s DNS authorises Zoho to send for it (SPF), that the message was signed with the domain's key and not altered (DKIM), and that both match the From address (DMARC). The records in [ex06 §2](ex06.md#the-dns-records-behind-these-results) are doing their job.

**What it doesn't prove.**
- **One message to one receiver.** Other providers (Outlook, Yahoo) run their own checks.
- **No blocking yet.** Because the DMARC policy is `p=none`, a forged message claiming to be from `ethanjad.me` would be *reported* but not blocked. Moving to `p=quarantine`, then `p=reject`, is the next step.

## Smaller details

- **ARC (`i=1` by Zoho, `i=2` by Google).** A chain of sealed results, so a later forwarder can see that the message passed when it was first checked. Gmail found Zoho's seal valid (`arc=pass`, `cv=pass`).
- **`Return-Path: <ethan@ethanjad.me>`.** The envelope sender, where bounces would go. It's on `ethanjad.me`, which is why SPF is checked against this domain and not a Zoho one.
- **Signed headers.** DKIM's `h=` lists `From`, `To` and `Subject` twice. This "over-signing" stops anyone from adding a second From or Subject header without breaking the signature.

## The other direction (Gmail → Zoho), partial

The only copy available of the earlier "Re: test hi" (Gmail → Zoho, 22:32 PDT) is the **sender's copy** in Gmail. It shows just the submission hop:

```
Received: from smtpclient.apple ([home IPv6, redacted]) by smtp.gmail.com with ESMTPSA id 00721157ae682-8b0e58af029sm37368317b3.19.2026.10.18.22.32.29 for <ethan@ethanjad.me> (version=TLS1_2 cipher=ECDHE-ECDSA-AES128-GCM-SHA256 bits=128/128); Sun, 18 Oct 2026 22:32:30 -0700 (PDT)
```

Apple Mail logged in to Gmail's submission server (`ESMTPSA`, where the `A` means authenticated) over TLS 1.2. Gmail adds its DKIM signature after this point, and Zoho records its checks on arrival, so this copy can't show either. Zoho's *Show original* on the received copy would cover that direction.
