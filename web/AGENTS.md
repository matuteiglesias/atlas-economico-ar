# Web / UX agent contract

Purpose: harden the Atlas as a usable analytical experience, not merely a statically valid set of routes.

Read first:

- `web/README.md`
- `web/package.json`
- `scripts/build-publication.py`
- generated `site-data/manifest.json` and `site-data/stats.json`
- the relevant semantic source files for any page being changed

## Core principle

Static integrity is necessary but insufficient. `verify:data`, `verify:plots`, typecheck, build, and route verification prove that the compiled site is internally consistent; they do not prove that a human can understand, navigate, or successfully use it.

UX work must therefore exercise the built site through realistic browser journeys.

## Public-surface principle

The semantic inventory may be larger than the public navigational surface.

Do **not** assume every QuestionIntent, PlotIntent, indicator, or concept deserves its own prominent route merely because it exists in the knowledge model.

Questions in particular must earn public prominence. Preserve useful semantic inventory while allowing weak/redundant/template questions to be withheld, merged, redirected, or treated as reference material by an explicit publication contract.

Do not delete semantic material just to make route counts smaller.

## Battle-test method

Each UX agent run should simulate at most **3 user missions** end-to-end in a real browser. Prefer Playwright once the harness exists.

Representative missions:

1. **Question-first** — arrive with an economic question, find an answer-bearing figure, understand the measurement and continue to related evidence.
2. **Chart-first** — open a chart directly, understand what it shows, freshness/source context, and navigate to the question/topic it supports.
3. **Atlas exploration** — start from the Atlas/home surface, choose a topic/area, distinguish substantive pages from stubs, and reach useful evidence without dead-end loops.
4. **Freshness/source inspection** — determine whether a chart is current, historical, stale-warning, or quarantined and inspect its evidence/source context.
5. **Mobile/narrow viewport** — complete one high-value journey without clipped controls, unreadable charts, broken navigation, or excessive backtracking.

A run should record the exact mission, route sequence, failure, and smallest repair.

## Experience failure classes

Classify findings rather than reporting vague polish issues:

- `DEAD_END` — route offers no useful next action/evidence.
- `STUB_PAGE` — public route exists but contains little beyond a title/metadata shell.
- `REDUNDANT_ROUTE` — multiple public pages offer materially the same user value.
- `QUESTION_WITHOUT_EVIDENCE` — question page has no answer-bearing materialized evidence.
- `EVIDENCE_WITHOUT_CONTEXT` — chart exists but question/interpretation/source context is too weak.
- `NAVIGATION_LOOP` — related links circulate without advancing understanding.
- `PROMINENCE_MISMATCH` — reference/historical/quarantined material is surfaced like a primary analytical result.
- `FRESHNESS_AMBIGUITY` — user cannot tell whether evidence is current.
- `MOBILE_BREAK` — important interaction/content fails on narrow viewport.
- `ACCESSIBILITY_BREAK` — keyboard, labels, semantics, focus, contrast, or alternative text prevents use.
- `VISUAL_REGRESSION` — layout/rendered chart changes materially without intended UX benefit.

## Question publication contract to implement

QuestionIntent identity and public route eligibility must become separate concerns.

The eventual compiler contract should support a question being retained in the semantic graph while not being promoted as a first-class public route.

A question should normally be **PUBLIC** only if all are true:

1. it is semantically distinct enough to justify its own user entry point;
2. it has at least one useful evidence path (materialized PlotArtifact and/or strong indicator evidence) that can actually help answer it;
3. its page provides meaningful context rather than a metadata-only shell;
4. it is not clearly dominated by another question that should be canonical;
5. its public status is compatible with the publication status of its evidence.

Likely non-public states:

- `REFERENCE` — valid semantic question, useful for graph/search/internal linkage but not a primary route;
- `SUPERSEDED` — dominated by a named canonical question;
- `HOLD` — potentially valuable, but evidence/page contract is not mature enough for publication.

Do not invent the final field/schema casually; implement it once in the compiler/publication boundary with validation and tests.

## Playwright contract

When adding Playwright, optimize for **experience invariants**, not screenshot-count vanity.

Minimum initial suite:

- home/Atlas loads without console/page errors;
- one representative area -> question -> chart journey works;
- one direct chart route exposes title, chart image, freshness/source context, and related navigation;
- quarantined/historical publication states are represented correctly in navigation/prominence;
- generated internal links used by the tested journeys resolve;
- one mobile viewport completes the primary journey;
- one accessibility/keyboard smoke path is executable;
- browser test fails on uncaught console errors and page errors.

Use stable semantic selectors/roles and user-visible text. Avoid coupling tests to incidental DOM structure.

Screenshots may be captured for diagnosis or a small number of stable visual assertions, but broad screenshot snapshots are not a substitute for behavioral tests.

## Allowed autonomous UX fixes

Agents may make small, evidence-backed changes such as:

- remove/promote links according to an existing publication contract;
- improve navigation labels and hierarchy;
- make publication/freshness status legible;
- fix broken or misleading related-link ordering;
- improve responsive layout/accessibility;
- consolidate a clearly redundant presentation component;
- add Playwright coverage for a reproduced experience defect.

## Human gates / prohibited autonomous changes

Do not autonomously:

- delete semantic questions because their current pages are weak;
- merge economically distinct questions solely because wording is similar;
- change economic claims or source interpretation to make a page easier to explain;
- perform a full visual redesign without a bounded demonstrated UX problem;
- introduce a new information architecture when a local publication/filtering contract would solve the issue.

Escalate when pruning requires deciding whether two economically meaningful questions are substantively equivalent.

## Definition of done for one UX run

A run is done when:

1. <=3 real user missions were executed in-browser;
2. each material finding has a classified failure mode and reproducible path;
3. at most 1-3 bounded fixes were applied;
4. a Playwright regression test exists for every fixed reproducible browser defect once the harness supports it;
5. `pnpm check` plus the relevant browser suite pass;
6. the report states the experience-debt delta, not only files changed.

The objective is a smaller and more trustworthy public surface: fewer stubs/dead ends, stronger evidence-bearing routes, and stable user journeys as the semantic inventory grows.
