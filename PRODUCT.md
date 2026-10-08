# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Internship recruiters and hiring managers screening Ethan Jad, an LMU undergraduate. They reach ethanjad.me from LinkedIn, an application, or an email signature, and they skim for 30 to 60 seconds. They want to know who he is, what he studies, when he graduates, what he has done, and how to contact him or get the résumé.

## Product Purpose

A recruiter-facing résumé site for Ethan Jad. It should get him interviews for internships in:

- business analytics / data (SQL, Python, Excel; the ISBA side)
- finance (budgeting, FP&A, corporate finance)
- sports business

The site works when a recruiter takes away the key facts in one scan and then emails him, opens LinkedIn, or downloads the résumé.

## Positioning

He is a dual Finance and ISBA (Information Systems & Business Analytics) student at Loyola Marymount University. He has real budgeting work in a university department, international market-entry consulting, and a sports-media side project he co-founded. The web page should add what the PDF can't: it scans faster, always shows current information, and keeps contact a single click away.

## Operating Context

- FastAPI + Jinja + SQLite app. Deployed on an Azure VM behind HTTPS at ethanjad.me / www.ethanjad.me.
- Content lives in the VM's SQLite DB and is edited through the admin API (`X-Admin-Secret`), not hardcoded in templates.
- `data/profile_snapshot.json` is the last-known-good fallback that is served if SQLite fails.

## Capabilities and Constraints

- Templates render whatever the DB holds: profile, experience, education, skills, projects, links. Design must handle empty and long lists.
- Phone number and street address never appear on the public site. Email and LinkedIn are the only public contact channels.
- The PDF résumé is the canonical source of facts (dates, GPA, titles). The site must match it and offers it as a download. The public download is a separate web-safe export (no phone or address) at `data/resume.pdf` on the server (`RESUME_PDF_PATH`), served at `/resume.pdf`. The button appears only when that file exists.
- ISBA is spelled out as "Information Systems & Business Analytics" for recruiters (user-confirmed 2026-10-07).
- Show the graduation year publicly but no target internship term (user decision, 2026-10-07). The year itself is unconfirmed: the PDF shows LMU Aug 2023–present, so likely 2027.
- Open: whether experience gets structured date/location fields in the DB schema (dates currently sit inside free-text details).

## Brand Commitments

- Name: Ethan Jad. Domain: ethanjad.me.
- Tone (user's choice, 2026-10-06): a "polished LMU student" look. Clean and modern, tightened up, not a finance tear-sheet reinvention.

## Evidence on Hand

From the résumé PDF (`(2.0 NEW Updated) 2026 Resume - Ethan Jad (1).pdf`):

- **Education:** LMU, BBA in Finance & ISBA, Aug 2023–present. GPA 3.62. Dean's List 4×.
- **Experience:**
  - LMU Student Housing: Financial Budgeting Intern (Jun 2026–present) and Front Office Assistant (Aug 2025–May 2026)
  - Lorawine: International Consulting Intern (Aug–Dec 2025), Napa market entry
  - LMU alumni Remote Job Shadowing mentee (May–Aug 2025)
- **Credentials:** Microsoft Office Specialist (Excel 2019 Associate); DataCamp Intermediate Python; Google Prompting Essentials.
- **Projects:** Hoops Recap (co-founder, basketball media platform). Friends of Ballona Wetlands volunteer.
- **Clubs:** ISBA Student Society, Sports Business Association, Finance Society, Accounting Society, Isang Bansa, Nikkei Student Union.
- **Not available:** quantified outcomes or metrics, testimonials, project links or case studies. Do not invent any of these.
- **Stale:** the repo's `data/profile_snapshot.json` still holds "Alex Carter" seed data, not Ethan's.

## Product Principles

1. Recruiter facts first: school, majors, grad year, GPA, and current role all visible without scrolling.
2. The PDF is the source of truth. The site never contradicts it or adds claims it doesn't make.
3. Contact is never more than one click away, through email, LinkedIn, or the résumé download.
4. Templates come from the DB, so every section degrades gracefully when it is empty or long.
5. Analytics, finance, and sports business read as one focused story, not three scattered pitches.
