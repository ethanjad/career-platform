---
target: my website (ethanjad.me homepage)
total_score: 17
max_score: 32
na_heuristics: 7,10
p0_count: 0
p1_count: 3
target_identity: "file:/Users/ethanjad/Desktop/github/career-platform/templates/index.html"
target_fingerprint: "sha256:2dd48704248bf8fb7574fc70de588c87e4c89be9a6c074b0cdc7981e70b2294d"
target_path: /Users/ethanjad/Desktop/github/career-platform/templates/index.html
timestamp: 2026-10-08T04-24-59Z
slug: templates-index-html
closed: true
---
Method: dual-agent (A: design review · B: detector + headless Chrome). First run with PRODUCT.md as context; template unchanged since 2026-10-06 (same sha256).

## Design Health Score (Persuade: personal résumé page)
| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility of System Status | 2 | "Open to opportunities" says no term/role/start; no grad year anywhere |
| 2 | Match System / Real World | 2 | ISBA used 3× in hero, never spelled out; freelancer copy ("role or project in mind") |
| 3 | User Control and Freedom | 3 | Simple anchor page; mobile nav display:none, no replacement |
| 4 | Consistency and Standards | 3 | Coherent; dates live in free text; timeline rule bleeds into Projects |
| 5 | Error Prevention | 2 | "010" numbering; empty links → empty footer; Alex Carter fallback snapshot |
| 6 | Recognition Rather Than Recall | 2 | GPA/Dean's List/BBA buried in sidebar below fold |
| 7 | Flexibility and Efficiency | n/a | Single-scan page (the "shortcut" is the PDF, which is missing) |
| 8 | Aesthetic and Minimalist Design | 2 | 120px name, 9rem padding, 6 decorative kickers; 20% first-viewport coverage |
| 9 | Error Recovery | 1 | 404 = raw JSON {"detail":"Not Found"}; no favicon |
| 10 | Help and Documentation | n/a | No task flow |
| Total | | 17/32 (53%) | Acceptable |

## Design Specificity Verdict
Category-interchangeable SaaS-blue portfolio template; nothing ties it to LMU, analytics, finance or sports business. Detector agrees: hero-eyebrow-chip, kicker-above-heading ×5, overused-font (Inter declared, never loaded → system font renders), first-viewport-column-overflow (viewport-dependent). CLI flat-type-hierarchy on raw template = false positive.

## Priority Issues
- [P1] No résumé PDF anywhere (/resume.pdf 404; main.py serves only / and /static). Fix: serve PDF, make it the primary hero CTA, LinkedIn second, email as text link. /impeccable clarify + /impeccable harden
- [P1] Recruiter facts not visible in one scan: no grad year, GPA buried, current role below fold; hero is eyebrow+headline+lede all restating "Finance & ISBA". Fix: fact line (BBA Finance & ISBA · LMU · Class of 20XX · 3.62 · Dean's List 4×) + "Now:" line; shrink h1/padding so Experience starts above fold. /impeccable layout + /impeccable distill
- [P1] Experience not scannable: dates in prose, multi-sentence muted paragraphs. Fix: date/location column with tabular nums (DB fields or parse), 1–2 short lines each. /impeccable typeset + schema decision
- [P2] Generic identity, sports thread missing: kickers, 01/02 cards, status dot, freelancer footer; clubs, Hoops Recap, MOS Excel, DataCamp Python unused. /impeccable bolder (within "polished LMU") + /impeccable clarify
- [P2] Resilience/a11y: Alex Carter fallback, raw JSON 404, no favicon/OG, "010", empty links column, no mobile nav, no :focus-visible, .card-number 1.85:1. /impeccable harden + /impeccable audit + /impeccable adapt

## Persona Red Flags
- Jordan (recruiter new to LMU): ISBA unexplained; can't tell eligibility year; no PDF to forward.
- Riley: "010"; zero links → no LinkedIn; raw JSON 404; DB failure shows "Alex Carter".
- Casey (mobile): no nav; first job ~1.5 screens down; no sticky résumé/contact.
- Morgan (analytics/sports hiring manager): "Microsoft Office" not Excel/SQL/Python; credentials missing; one sentence of sports.

## Minor Observations
h1 tracking -.08em (glyphs touch); muted text 4.72:1 (barely AA); availability email doesn't look clickable; high school weighted equal to LMU; no OG/canonical/robots; smooth scroll ignores reduced-motion; "case studies will be added soon" empty-state copy.

## Questions to Consider
- Why isn't the top of the page just the PDF's header block plus three buttons?
- Would "Involvement & Credentials" say more than two thin "Selected work" cards?
- What honest artifact (Hoops Recap stat, Excel model) would make this unmistakably Ethan's?
