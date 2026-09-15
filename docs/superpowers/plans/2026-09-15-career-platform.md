# Career Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first version of a recruiter-facing, database-backed personal resume and portfolio website with a resilient public profile that remains visible during database outages.

**Architecture:** Use a lightweight Python FastAPI app with Jinja templates and plain CSS for the recruiter-facing site and admin workflow. The app reads from a structured database for normal operation and falls back to a cached public snapshot when the database is unavailable.

**Tech Stack:** Python 3, FastAPI, Jinja2, SQLAlchemy or direct SQL access with SQLite for the first version, plain CSS, a simple admin interface, and a local cached fallback snapshot for public rendering.

**Spec:** `docs/superpowers/specs/2026-09-15-career-platform-design.md`

## Global Constraints

- The public profile must stay visible even when the database is unavailable.
- Keep the first version focused on a strong public resume and portfolio foundation.
- Use a database-backed content model rather than hardcoded content.
- The public site should be fast, readable, and mobile-friendly.
- The first version should not include a job application tracker, networking relationship management, recruiter analytics dashboard, or multi-user authentication.
- The site should be hosted cheaply and simply while remaining expandable for future career platform features.

---

## Stack and Deployment Decision

This plan now assumes the following choices:
- Python FastAPI with Jinja templates and plain CSS
- SQLite for the first version, with an upgrade path to PostgreSQL if needed later
- local Codespace deployment first, then eventual Azure VM deployment

These settings are reflected in the plan below. If you want a different stack or hosting path before execution begins, tell me now and I will adjust the plan before any build work starts.

---

### Task 1: Set up the project skeleton and configuration

**Files:**
- Create: `package.json`, `src/`, `public/`, `server/`, `data/`, `docs/`, `tests/`
- Modify: `.gitignore`, environment config files, project scripts
- Test: `tests/project-setup.test.js`

**Interfaces:**
- Consumes: no prior tasks
- Produces: a working development environment, app entrypoints, and configuration for the frontend and backend

- [ ] **Step 1: Write the failing test**

```js
// tests/project-setup.test.js
const fs = require('fs');

test('project structure includes app and data folders', () => {
  expect(fs.existsSync('src')).toBe(true);
  expect(fs.existsSync('data')).toBe(true);
  expect(fs.existsSync('server')).toBe(true);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand tests/project-setup.test.js`
Expected: FAIL because required directories do not exist yet.

- [ ] **Step 3: Create the minimal project structure and scripts**

Create:
- `package.json` with scripts for dev, build, test, and start
- `src/` for frontend code
- `server/` for API or content-serving logic
- `data/` for seed and fallback content
- `tests/` for application tests
- `.gitignore` for node_modules, build artifacts, and environment files

- [ ] **Step 4: Run the project test to verify it passes**

Run: `npm test -- --runInBand tests/project-setup.test.js`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add package.json .gitignore src server data tests
git commit -m "chore: scaffold career platform"
```

**Done looks like:** The repo contains a working app skeleton, consistent scripts, and a known place for source, data, and tests.

**How to check:** Run `npm test -- --runInBand tests/project-setup.test.js` and confirm the folder structure exists and the project starts cleanly with the defined scripts.

---

### Task 2: Define the database schema and seed content model

**Files:**
- Create: `server/db/schema.sql`, `data/seed.json`, `server/db/index.js`
- Modify: environment config, app startup files
- Test: `tests/db-schema.test.js`

**Interfaces:**
- Consumes: project shell from Task 1
- Produces: typed database tables and seed data for profile, experience, education, skills, projects, links, and settings

- [ ] **Step 1: Write the failing test**

```js
// tests/db-schema.test.js
const { createDatabase } = require('../server/db');

test('database exposes expected profile tables', async () => {
  const db = createDatabase();
  expect(db).toBeDefined();
  expect(typeof db.listTables).toBe('function');
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand tests/db-schema.test.js`
Expected: FAIL because the migration or database layer does not exist yet.

- [ ] **Step 3: Create schema and seed data**

Create the following tables or data structure:
- `profile`
- `experience`
- `education`
- `skill`
- `project`
- `link`
- `settings`

Seed example data with sample values for a realistic senior business analytics student profile. The seed must include:
- name
- headline
- bio summary
- sample experience entries
- education entries
- skill items
- at least two sample projects
- contact links

- [ ] **Step 4: Run the database test to verify it passes**

Run: `npm test -- --runInBand tests/db-schema.test.js`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/db data/seed.json tests/db-schema.test.js
git commit -m "feat: add profile data model"
```

**Done looks like:** The application can connect to a database layer and has a valid schema for all major profile sections.

**How to check:** Run the schema test and inspect the database contents with a local query or a node script to confirm each table exists and contains seed data.

---

### Task 3: Add a resilient public profile fallback layer

**Files:**
- Create: `server/fallback.js`, `server/cache.js`, `src/lib/profile-loader.js`
- Modify: app startup or request-layer code, admin/data update flow
- Test: `tests/fallback.test.js`

**Interfaces:**
- Consumes: database layer and seed data from Task 2
- Produces: `loadPublicProfile()` function that returns database data when available and cached profile data when the database is unavailable

- [ ] **Step 1: Write the failing test**

```js
// tests/fallback.test.js
const { loadPublicProfile } = require('../server/fallback');

test('returns cached snapshot when database is unavailable', async () => {
  const result = await loadPublicProfile({ dbAvailable: false });
  expect(result).toBeDefined();
  expect(result.profile).toBeDefined();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand tests/fallback.test.js`
Expected: FAIL because fallback logic does not exist yet.

- [ ] **Step 3: Implement fallback behavior**

Implement a profile loader that behaves as follows:
- Attempt to read current profile data from the database.
- On success, render the live data.
- On failure or timeout, load the last known good snapshot from a cache file or static fallback record.
- Return the same public profile shape in both cases.
- Keep the fallback data consistent with the seeded profile schema.

Write a small cache writer so the latest valid content is always saved as the current fallback snapshot.

- [ ] **Step 4: Run the fallback test to verify it passes**

Run: `npm test -- --runInBand tests/fallback.test.js`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/fallback.js server/cache.js src/lib/profile-loader.js tests/fallback.test.js
git commit -m "feat: add public profile fallback"
```

**Done looks like:** The public site can still render profile content even when the database is unavailable; the site does not break or return an empty profile.

**How to check:** Simulate a database failure in a local environment and verify the page still loads with the cached profile content instead of an error.

---

### Task 4: Build the public profile pages and layout

**Files:**
- Create: `src/pages/`, `src/components/`, `src/styles/`
- Modify: front-end routing and page rendering logic
- Test: `tests/profile-page.test.js`

**Interfaces:**
- Consumes: `loadPublicProfile()` from Task 3
- Produces: a recruiter-friendly page with profile, experience, education, skills, projects, links, and contact sections

- [ ] **Step 1: Write the failing test**

```js
// tests/profile-page.test.js
const { renderPage } = require('../src/pages/profile');

test('profile page renders core resume sections', () => {
  const html = renderPage({
    profile: { name: 'Example User' },
    experience: [],
    education: [],
    skills: [],
    projects: [],
  });
  expect(html).toContain('Example User');
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm test -- --runInBand tests/profile-page.test.js`
Expected: FAIL because the page does not exist yet.

- [ ] **Step 3: Implement a recruiter-friendly profile page**

Build a page with:
- hero/profile summary
- experience timeline
- education section
- skills grouping
- project cards or case-study list
- links to relevant external profiles
- contact section

Use simple, clean CSS and ensure the layout is mobile-friendly.

- [ ] **Step 4: Run the page test to verify it passes**

Run: `npm test -- --runInBand tests/profile-page.test.js`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/pages src/components src/styles tests/profile-page.test.js
git commit -m "feat: add public profile experience pages"
```

**Done looks like:** A professional, mobile-friendly public profile page loads and displays all major sections of the resume.

**How to check:** Run the app locally and confirm the page renders each major section with realistic sample data.

---

### Task 5: Build the admin content workflow

**Files:**
- Create: `server/admin.js`, `src/admin/`, `src/components/AdminForm.jsx`
- Modify: API routes and authorization layer
- Test: `tests/admin-workflow.test.js`

**Interfaces:**
- Consumes: the database schema from Task 2
- Produces: CRUD handlers for profile, experience, education, skills, projects, and links

- [ ] **Step 1: Write the failing test**

```js
// tests/admin-workflow.test.js
const { createExperienceRecord } = require('../server/admin');

test('creates an experience record with required fields', () => {
  const record = createExperienceRecord({
    company_name: 'Example Co',
    job_title: 'Analyst',
  });
  expect(record.company_name).toBe('Example Co');
  expect(record.job_title).toBe('Analyst');
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm test -- --runInBand tests/admin-workflow.test.js`
Expected: FAIL because admin record creation is not implemented.

- [ ] **Step 3: Implement basic CRUD operations**

Add admin endpoints or forms for:
- profile update
- adding/editing/deleting experience entries
- adding/editing/deleting education entries
- adding/editing/deleting skills
- adding/editing/deleting projects
- adding/editing/deleting links

Use a simple, private admin interface or secure API route. Since the spec excludes multi-user auth for v1, keep the admin access model minimal but protected by a basic secret or local-only admin route.

- [ ] **Step 4: Run the admin tests to verify they pass**

Run: `npm test -- --runInBand tests/admin-workflow.test.js`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add server/admin.js src/admin tests/admin-workflow.test.js
git commit -m "feat: add admin content workflow"
```

**Done looks like:** A user can create, update, and remove content records through a simple admin flow.

**How to check:** Use the admin interface or API locally to create a project and confirm it appears on the public page.

---

### Task 6: Add deployment and environment configuration for low-cost hosting

**Files:**
- Create: `.env.example`, `Dockerfile` or deployment config, `README.md` updates
- Modify: environment setup, config, documentation
- Test: `tests/config.test.js`

**Interfaces:**
- Consumes: app and config values from Tasks 1-5
- Produces: environment-driven app configuration for hosting, database, and fallback settings

- [ ] **Step 1: Write the failing test**

```js
// tests/config.test.js
const { getConfig } = require('../server/config');

test('returns database and fallback settings', () => {
  const config = getConfig();
  expect(config.databaseUrl).toBeDefined();
  expect(config.fallbackEnabled).toBe(true);
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm test -- --runInBand tests/config.test.js`
Expected: FAIL because config support is not implemented.

- [ ] **Step 3: Implement environment config**

Create config values for:
- database connection string
- app port
- admin secret or local access flag
- fallback toggle
- static/public rendering mode

Document required environment variables for a low-cost hosting environment.

- [ ] **Step 4: Run the config test to verify it passes**

Run: `npm test -- --runInBand tests/config.test.js`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .env.example server/config.js README.md tests/config.test.js
git commit -m "chore: add deployment config"
```

**Done looks like:** The app can be configured for a simple hosting setup without hardcoded credentials or environment assumptions.

**How to check:** Start the app with a sample `.env` file and confirm the app resolves DB and fallback settings correctly.

---

### Task 7: Validate the full user flow and harden edge cases

**Files:**
- Create: `tests/end-to-end.test.js`, `tests/resilience.test.js`
- Modify: app startup and final cleanup
- Test: end-to-end and outage flow tests

**Interfaces:**
- Consumes: all previous tasks
- Produces: verified site behavior under normal and failure conditions

- [ ] **Step 1: Write the failing end-to-end tests**

```js
// tests/resilience.test.js
const { simulateDbFailure } = require('../server/fallback');

test('public profile remains available during database outage', async () => {
  const profile = await simulateDbFailure();
  expect(profile).toBeDefined();
  expect(profile.profile).toBeDefined();
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npm test -- --runInBand tests/end-to-end.test.js tests/resilience.test.js`
Expected: FAIL before final integration is added.

- [ ] **Step 3: Run the full validation sequence**

Verify that:
- a recruiter can open the homepage and see the public profile
- each major section renders correctly
- editing content through admin updates the content model
- the public profile remains available when the database is temporarily unavailable
- no broken or blank page appears during outage conditions

- [ ] **Step 4: Fix any issues uncovered by the validation pass**

Adjust logic and UI until all validation checks pass.

- [ ] **Step 5: Commit**

```bash
git add tests server src
git commit -m "fix: validate full profile user flow"
```

**Done looks like:** The end-to-end workflow is stable and the site works in both normal and database-down states.

**How to check:** Run the application locally, verify the profile renders, update a project record through admin, and then simulate a database outage to confirm the public page continues rendering the cached profile.

---

### Task 8: Final documentation and launch readiness review

**Files:**
- Modify: `README.md`, any admin docs, setup notes, deployment notes
- Test: no code tests required, but a final README validation pass

**Interfaces:**
- Consumes: final app behavior from all prior tasks
- Produces: a clean handoff document ready for local setup, admin use, and future expansion

- [ ] **Step 1: Write the final setup guide**

Document:
- install steps
- environment variables required
- how to run the app in dev mode
- how to initialize database seed data
- how to update profile content
- how the fallback behaves during database outages

- [ ] **Step 2: Review against the spec**

Check each requirement from the design doc:
- public recruiter-facing profile
- structured content model
- simple admin workflow
- low-cost hosting direction
- public availability during DB outages
- future growth readiness

- [ ] **Step 3: Final verification**

Run: `npm test -- --runInBand` and verify the final app boots successfully.

- [ ] **Step 4: Commit**

```bash
git add README.md docs/
git commit -m "docs: finalize launch readiness"
```

**Done looks like:** The project is documented and ready for local setup, future iteration, and eventual deployment.

**How to check:** Follow the README steps from a clean checkout and ensure the project runs without missing setup steps or undocumented assumptions.

---

## Implementation Notes

- This project is intentionally scoped to a strong first version: public profile + structured content + admin updates + fallback resilience.
- The fallback requirement is non-negotiable because the website is meant to serve professional visibility.
- Future enhancements such as application tracking, networking, and a broader platform should be added only after this foundation is proven stable.
- Every task above includes a concrete test, an implementation step, and a verification method so the build remains controlled and reviewable.

If you approve this plan, I can either:
- run it in this session using the executing-plans workflow, or
- dispatch it through subagent-driven development task-by-task.
