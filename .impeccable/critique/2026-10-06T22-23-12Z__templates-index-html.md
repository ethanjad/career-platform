---
target: critique (career-platform homepage)
total_score: 20
max_score: 32
na_heuristics: 7,10
p0_count: 0
p1_count: 2
target_identity: "file:/Users/ethanjad/Desktop/github/career-platform/templates/index.html"
target_fingerprint: "sha256:2dd48704248bf8fb7574fc70de588c87e4c89be9a6c074b0cdc7981e70b2294d"
target_path: /Users/ethanjad/Desktop/github/career-platform/templates/index.html
timestamp: 2026-10-06T22-23-12Z
slug: templates-index-html
---
Method: dual-agent (A: design review · B: detector + headless browser)

## Design Health Score (Persuade: personal résumé page)
| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility of System Status | 2 | No current-section indicator in nav; no custom error page |
| 2 | Match System / Real World | 2 | Dates buried mid-sentence in details; "ISBA" never spelled out |
| 3 | User Control and Freedom | 2 | Nav display:none ≤700px, no replacement, no back-to-top |
| 4 | Consistency and Standards | 3 | Consistent system; nav omits Skills/Education |
| 5 | Error Prevention | 2 | mailto-only contact (3×), no copy-email fallback |
| 6 | Recognition Rather Than Recall | 2 | No résumé PDF; skills uncategorized; dates unscannable |
| 7 | Flexibility and Efficiency | n/a | One-page résumé |
| 8 | Aesthetic and Minimalist Design | 3 | Clean; decorative eyebrow on every heading; email repeated |
| 9 | Error Recovery | 2 | Default nginx 404; "will be added soon" empty states |
| 10 | Help and Documentation | n/a | Not applicable |
| Total | | 20/32 (63%) | Acceptable |

## Design Specificity Verdict
Category-interchangeable 2023 portfolio template (giant tight-tracked name, eyebrow kickers, pill buttons, "Open to opportunities" card, numbered cards, navy "Have a role or project in mind?" footer). Nothing signals finance; strong real content (LMU, 3.62, Dean's List 4×, budgeting/consulting roles) is not foregrounded.
Detector: hero-eyebrow-chip ("Finance & ISBA" above h1), kicker-above-heading ×5 (browser only), overused-font (Inter — and Inter is never loaded), first-viewport-column-overflow (147% vs 93% at 1440×900). flat-type-hierarchy on raw template = false positive (Jinja url_for stylesheet unresolved). Overlay ran headlessly on a local copy only; injection on live HTTPS blocked by Chrome.

## Priority Issues
- [P1] Experience buries recruiter facts: dates inline in prose, no outcomes/metrics, no résumé PDF. Fix: start/end/location fields, fixed date column w/ tabular nums, 2–3 outcome bullets, hero PDF download. /impeccable clarify → /impeccable layout
- [P1] Interchangeable aesthetic, nothing finance: 6 eyebrow/kicker detections; generic headline copy. Fix: one finance-native direction (tear sheet/ledger), lead with "LMU '27 · 3.62 · Dean's List 4×", drop kickers, rewrite headline. /impeccable bolder → /impeccable clarify
- [P2] Declared font (Inter) never loaded; rendering varies per OS. /impeccable typeset
- [P2] Mobile: nav hidden ≤700px (styles.css:73), small tap targets, no sticky contact. /impeccable adapt
- [P2] A11y: zero :focus-visible rules; .card-number #f0b44d on white 1.85:1; status dot announced; .links div aria-label w/o role; target=_blank unannounced. /impeccable audit

## Persona Red Flags
- Jordan (recruiter): ISBA unexplained; dates in prose; no PDF; projects unlinked with no outcomes.
- Riley: "010" from 10th project; four "will be added soon" when empty; profile_visible ignored; no OG/Twitter tags, favicon 404.
- Casey: no nav; 18vw h1 pushes content below fold; no sticky contact; no overflow-wrap.

## Minor Observations
Header translucent but not sticky; skills.category unused; footer h2 orphan "mind?"; smooth scroll ignores reduced-motion; repo profile_snapshot.json still holds "Alex Carter" seed (DB-failure fallback would show it); https://IP serves site with cert mismatch; VM plan still cites http://<VM_PUBLIC_IP>/.

## Questions to Consider
- What single fact should a recruiter remember, and is it above the fold?
- Why SaaS-pitch vocabulary instead of finance's visual language?
- What does the web page give a recruiter that the PDF doesn't?
