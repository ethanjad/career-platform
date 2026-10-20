---
target: my website
total_score: 23
max_score: 32
na_heuristics: 7,10
p0_count: 0
p1_count: 2
target_identity: "file:/Users/ethanjad/Desktop/github/career-platform/templates/index.html"
target_fingerprint: "sha256:8f2bace09294f36ae527f8165c87c8d89840fdc9d81459e51ba14b7342da4dda"
target_path: /Users/ethanjad/Desktop/github/career-platform/templates/index.html
timestamp: 2026-10-20T03-04-00Z
slug: templates-index-html
---
Method: dual-agent (A: design review, B: detector). Screenshots failed (no browser); review from live HTML + source.

## Design Health Score: 23/32 (Good, 72%); n/a: 7, 10
| # | Heuristic | Score | Key Issue |
|---|---|---|---|
| 1 | Visibility of System Status | 3 | No active nav state |
| 2 | Match System / Real World | 3 | ISBA unexpanded in Education; "Google Suite" |
| 3 | User Control and Freedom | 3 | download attr forces save of PDF |
| 4 | Consistency and Standards | 2 | "Finance and ISBA" vs "ISBA and Finance"; 4x vs (4x); mixed tenses |
| 5 | Error Prevention | 3 | 'Present' substring current-role detection |
| 6 | Recognition Rather Than Recall | 3 | Nav hidden <=700px; no Education link |
| 7 | Flexibility and Efficiency | n/a | single read-once page |
| 8 | Aesthetic and Minimalist Design | 3 | GPA/Dean's List duplicated; filler lede |
| 9 | Error Recovery | 3 | profile_snapshot.json still Alex Carter seed |
| 10 | Help and Documentation | n/a | static résumé |

## Design Specificity
Competent but category-interchangeable (blue accent, pill buttons/tags, timeline dots, white cards, navy footer). Nothing signals LMU/finance/analytics/sports. Detector: templates 0 (CSS unresolved via Jinja url_for); live desktop: tight-leading (threshold, FP), first-viewport-column-overflow (real, likely intentional); mobile body-text-viewport-edge (FP); privacy line-length x5 (real, .prose 68ch ~90 chars). All text contrast passes AA.

## Priority Issues
1. [P1] Lede ("passion for business development") contradicts analytics/finance/sports positioning; best framing only in footer. Fix: rewrite profile.summary (DB). /impeccable clarify
2. [P1] Content inconsistency/duplication hero vs Education (ISBA, 4x, tense, GPA twice). Fix: normalize DB strings. /impeccable clarify
3. [P2] Strongest evidence missing/buried: PDF credentials absent; Hoops Recap same weight as volunteering. Fix: Certifications group; feature Hoops Recap. /impeccable layout
4. [P2] Generic look for "polished LMU student" brief. Fix: LMU-family accent, sidebar h2 to h3 scale, quieter dots/cards. /impeccable colorize, /impeccable typeset
5. [P3] Mobile/edge hardening: nav display:none <=700px, long <title>, empty main column, privacy line length. /impeccable adapt, /impeccable harden

## Persona Red Flags
Recruiter: unclear target track after lede; credentials missing. Casey (mobile): no nav, Contact only by scrolling. Riley: Privacy page says Railway host vs Azure VM in notes; 'Present' detection fragile; empty headline breaks title.

## Minor
Google Suite -> Google Workspace; footer email lacks CTA weight; --line dividers 1.2:1 nearly invisible; "Mentee" title thin.

## Questions
Which one sentence should a recruiter remember? Why are Education/credentials in the narrow sidebar?
