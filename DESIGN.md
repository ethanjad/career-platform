---
name: Ethan Jad
description: A recruiter-facing résumé site styled as one perforated LMU game-day ticket.
colors:
  ground: "#eef1f6"
  paper: "#ffffff"
  ink: "#0f1c33"
  navy: "#00285e"
  crimson: "#ab0c2f"
  crimson-deep: "#8a0925"
  muted: "#535d70"
  line: "#d3dae6"
  perf: "#9aa6bb"
  on-navy: "#ffffff"
  on-navy-muted: "#c3d0ee"
typography:
  display:
    fontFamily: "Schibsted Grotesk, Schibsted Fallback, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(3rem, 7.5vw, 5.75rem)"
    fontWeight: 800
    lineHeight: 0.92
    letterSpacing: "-0.04em"
  headline:
    fontFamily: "Schibsted Grotesk, Schibsted Fallback, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(1.75rem, 3vw, 2.25rem)"
    fontWeight: 800
    lineHeight: 1.1
    letterSpacing: "-0.03em"
  title:
    fontFamily: "Schibsted Grotesk, Schibsted Fallback, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.2rem"
    fontWeight: 700
    lineHeight: 1.35
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Schibsted Grotesk, Schibsted Fallback, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  lede:
    fontFamily: "Schibsted Grotesk, Schibsted Fallback, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.15rem"
    fontWeight: 400
    lineHeight: 1.6
  figure:
    fontFamily: "Schibsted Grotesk, Schibsted Fallback, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.85rem"
    fontWeight: 700
    lineHeight: 1.6
    fontFeature: "tnum"
  legend:
    fontFamily: "Schibsted Grotesk, Schibsted Fallback, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 700
    letterSpacing: "0.32em"
rounded:
  focus: "0.25rem"
  button: "8px"
  ticket: "14px"
spacing:
  xs: "0.75rem"
  sm: "1.25rem"
  md: "1.5rem"
  lg: "2.5rem"
  xl: "4.5rem"
  xxl: "6rem"
components:
  button-primary:
    backgroundColor: "{colors.crimson}"
    textColor: "{colors.on-navy}"
    rounded: "{rounded.button}"
    padding: "0.7rem 1.2rem"
  button-primary-hover:
    backgroundColor: "{colors.crimson-deep}"
    textColor: "{colors.on-navy}"
  button-secondary:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.navy}"
    rounded: "{rounded.button}"
    padding: "0.7rem 1.2rem"
  button-secondary-hover:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.on-navy}"
  ticket-band:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.on-navy-muted}"
    typography: "{typography.legend}"
    rounded: "{rounded.ticket}"
    width: "2.75rem"
  ticket-main:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    padding: "clamp(2rem, 5vw, 3.75rem)"
  ticket-stub:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.on-navy}"
    rounded: "{rounded.ticket}"
    padding: "clamp(1.75rem, 3.5vw, 2.5rem)"
  fixture-number:
    textColor: "{colors.navy}"
    typography: "{typography.figure}"
  nav-link:
    textColor: "{colors.muted}"
    typography: "{typography.body}"
  footer:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.on-navy}"
    padding: "4rem 0"
---

# Design System: Ethan Jad

## Overview

**Creative North Star: "The Season Ticket"**

The recruiter is handed one ticket. The whole system is built from the material of a printed game-day pass: white ticket stock lying on a cool grey-blue counter, LMU navy ink and an edge band, perforations drawn as dashed rules with notches punched clean through the stock, and fine-print legends set small, bold, and widely tracked. Everything below the hero continues the same paper logic: experience reads as a numbered season schedule split by perforations, education and skills read as the ticket's fine print.

Density is calm and editorial. Rank comes from space and position, not from many type sizes: one very large navy name, one heading size per section, and a quiet body. Colour is nearly monochrome navy on cool neutrals; crimson appears exactly once per screen, on the single primary action. The result should read as a polished, focused LMU student, clean and modern, never a finance tear-sheet and never the generic portfolio hero of headline, subcopy, pill buttons and card row.

Motion is a single entrance: the ticket settles up into place and the stub slides in a beat later, as if just torn and handed over. Nothing else moves except colour on hover.

**Key Characteristics:**
- One ticket as the hero: edge band, main panel, perforated tear-off stub.
- Navy ink everywhere; crimson reserved for one action.
- Perforations (dashed rules + punched notches) as the only decorative device.
- One typeface, Schibsted Grotesk, ranked by weight and space.
- Tabular figures on every date and row number, proportional figures in prose.

## Colors

A cool, near-monochrome LMU navy palette on blue-tinted neutrals, with one crimson voice.

### Primary
- **LMU Navy** (navy): the ink of the system. Headings, brand name, row numbers, organisation names, the ticket edge band, the stub, the footer, focus rings, text selection, form accent and caret.

### Secondary
- **LMU Crimson** (crimson): the primary action only (the "Email me" button). Deepens to **Crimson Ink** (crimson-deep) on hover.

### Neutral
- **Counter Grey-Blue** (ground): the page ground the ticket lies on. Also the scrollbar track.
- **Ticket Stock** (paper): the ticket's main panel.
- **Night Ink** (ink): default body text.
- **Slate Fine Print** (muted): ledes, dates, role bodies, nav links, education detail lines.
- **Hairline** (line): solid structural rules (header border, sidebar section dividers, the ticket-foot dashed rule).
- **Perforation Grey** (perf): dashed perforation rules between schedule rows; scrollbar thumb. Decorative only, never text.
- **On-Navy White** (on-navy) and **On-Navy Haze** (on-navy-muted): primary and secondary text on navy surfaces (stub, footer, band). On navy, rules are white at 18 to 55% opacity.

### Named Rules
**The One Crimson Rule.** Crimson is used for the single primary action on a screen and nowhere else: not for links, headings, tags, or hover states of other elements.

**The Navy Ink Rule.** Emphasis is navy, not a new colour. When something needs to stand out, make it navy and heavier before reaching for anything else.

## Typography

**Display Font:** Schibsted Grotesk (self-hosted variable woff2, weights 400 to 900), with a metric-matched Arial fallback ("Schibsted Fallback": size-adjust 104.5%, ascent 93.5%, descent 24.7%) so the swap does not reflow.
**Body Font:** Schibsted Grotesk.

**Character:** A single newsy grotesk doing every job. Tight negative tracking and heavy weights at the top; wide positive tracking only for the ticket's uppercase legends.

### Hierarchy
- **Display** (800, clamp(3rem, 7.5vw, 5.75rem), 0.92): the holder's name on the ticket, navy. Mobile: clamp(2.75rem, 14vw, 4rem). Privacy page title uses clamp(2.5rem, 6vw, 3.75rem).
- **Headline** (800, clamp(1.75rem, 3vw, 2.25rem), 1.1): section heads (Experience, Projects & Involvement) and the footer pitch. Sidebar heads drop to 1.25rem; privacy section heads to 1.5rem.
- **Title** (700, 1.2rem, 1.35): role titles, project titles, school names (1.05rem in the sidebar).
- **Lede** (400, 1.15rem, 1.6, max 60ch): the summary on the ticket, muted.
- **Body** (400, 1rem, 1.6, max 62ch for role bodies): running text. Stub facts are 650 at 1.05rem, 1.35.
- **Figure** (700, 0.85rem, tabular-nums): schedule row numbers ("01") and date ranges; stub dates.
- **Legend** (700, 0.75rem, 0.32em tracking, uppercase): the "ADMIT ONE" edge band. The ticket-foot holder line uses the same voice at 0.72rem, 0.14em.

### Named Rules
**The Tabular Dates Rule.** Every date and row number uses tabular figures; prose never does, because this face widens commas and periods under `tnum`.

**The Few Sizes Rule.** Rank by space, weight and colour, not by adding sizes. A new surface reuses display, headline, title, body and figure; it does not introduce a new step.

## Layout

A single centred shell (min(1120px, 100% - 3rem); 100% - 2rem under 760px). The hero is a three-column ticket grid: a 2.75rem edge band, the flexible main panel, and a stub of minmax(240px, 30%). Below it, a two-column content grid (1.6fr main, 0.8fr sidebar, minimum 250px) with a clamp(3rem, 7vw, 6rem) gutter; the sidebar is sticky at 1.5rem so it rides beside the long schedule. With no experience or projects it collapses to one column.

Schedule rows are a three-column grid: 2ch row number, 8.5rem dates, then the fixture; involvement rows carry no number or dates and indent to the text column. Vertical rhythm: 1.6rem row padding, 4.5rem between main-column sections, 2.5rem between sidebar sections, 6rem before the footer.

At 760px and below the ticket turns upright: band on top running horizontally, main panel, then the stub torn off below along a horizontal perforation. Hero actions become a two-by-two grid so the stub's current role stays in the first phone screen; the "Download" verb and the ticket-foot line are hidden. The content grid stacks; schedule rows drop the date column into the text column.

## Elevation & Depth

Flat paper on a flat counter, with one exception: the ticket itself is lifted by a soft two-layer drop shadow so it reads as a physical object lying on the ground. It is a `filter: drop-shadow`, not a box-shadow, because it must follow the punched notches. Everything else is flat and separated by rules and tone.

### Shadow Vocabulary
- **Ticket lift** (`filter: drop-shadow(0 1px 1px rgb(15 28 51 / 8%)) drop-shadow(0 14px 22px rgb(15 28 51 / 16%))`): the hero ticket only.

### Named Rules
**The One Object Rule.** Only the ticket casts a shadow. Sections, lists, and sidebar items are flat; they are print on the page, not objects on it.

## Shapes

Mostly square paper with a few deliberate rounds. The ticket's outer ends carry a 14px radius (band on the left, stub on the right; top and bottom when stacked on mobile). Buttons use a gently rounded 8px corner, never a pill. Focus outlines round to 0.25rem (8px on buttons).

The signature geometry is the perforation: a 2px dashed white rule on the stub seam, inset 1.25rem from each end, with a 13px circular notch masked out of both halves at the top and bottom of the seam. Schedule rows use 1px dashed perforation-grey rules; the ticket-foot uses a 1px dashed hairline. Solid 1px hairlines are reserved for structural separation (header, sidebar sections, education items).

## Components

### Buttons
Confident, inked, compact.
- **Shape:** gently rounded (8px), 2px border, 700 weight, 0.7rem 1.2rem padding.
- **Primary:** crimson fill and border, white text. One per screen.
- **Secondary:** transparent on the ticket stock, 2px navy border, navy text. Used for résumé PDF and LinkedIn / GitHub.
- **Hover / Focus:** primary deepens to crimson-deep; secondary fills navy with white text; 0.15s ease-out colour transitions. Focus is a 2px navy outline offset 3px.
- **Note:** a smaller 600-weight "PDF" tag (0.75em) can trail the label.

### Navigation
A slim header (68px; 58px on mobile) over a hairline: navy 800-weight name on the left, muted 600-weight 0.9rem links on the right that turn navy and underline on hover. The links are kept on mobile.

### Ticket (signature)
The hero. Edge band (navy, vertical "ADMIT ONE" legend, rotated so it reads bottom-to-top), main panel (ticket stock with display name, lede, actions, and a dashed holder line pinned to the bottom), and stub (navy, a list of headline facts split by faint white rules, then a dashed rule and the current role with tabular dates). Entrance: the ticket rises 14px over 0.7s, the stub slides in 0.15s later over 0.9s, both on cubic-bezier(.16, 1, .3, 1); disabled under reduced motion.

### Schedule (signature)
Experience as a season schedule: each fixture is a numbered row (navy, two-digit, tabular), a muted tabular date range, then title, navy organisation line and muted body. Rows are separated by dashed perforation rules top and bottom.

### Fine print (sidebar)
Education and skills: smaller heads (1.25rem), sections divided by solid hairlines, muted 0.95rem detail lines with bold ink degrees, and skills as a wrapped run of 600-weight words (no chips, no pills).

### Footer
A full-width navy band: headline pitch in white, the email as a large underlined link (white underline at 40%, solid on hover), and a row of on-navy-haze links with a small inline SVG external-link mark.

## Do's and Don'ts

### Do:
- **Do** keep crimson on exactly one primary action per screen.
- **Do** draw separations as perforations: dashed rules, with punched 13px notches where a ticket edge tears.
- **Do** set every date and row number in tabular figures, and keep prose proportional.
- **Do** use Schibsted Grotesk for every role, with the metric-matched fallback.
- **Do** keep text on navy in on-navy or on-navy-muted, and rules on navy as translucent white.
- **Do** lift only the ticket, using drop-shadow so the notches stay punched.

### Don't:
- **Don't** use a box-shadow on the ticket; it fills in the notches.
- **Don't** use pill-shaped buttons or tag chips; buttons are 8px, skills are plain words.
- **Don't** fall back to the generic portfolio hero (headline, subcopy, pill buttons, card row).
- **Don't** introduce a second typeface or new type sizes for emphasis; use weight, navy, and space.
- **Don't** use perforation grey for text; it is a rule colour only.
- **Don't** add uppercase tracked labels above headings; the tracked legend voice belongs to the ticket's own band and fine print.
