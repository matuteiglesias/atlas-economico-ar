# Argentina Economic Atlas — Codex Development Bundle v0.1

**Goal:** implement the first production-quality frontend of the Argentina Economic Atlas using the
already-compiled knowledge read model.

## End gate

A local/static site exists that:

- visually follows `reference/visual-target-inflation-topic.png`;
- renders the complete **Nominal Stabilization** slice;
- exposes all public entity routes from the fixture:
  - 6 Areas
  - 25 Topics
  - 18 Questions
  - 42 Indicators
  - 52 Charts
- generates **145 total site pages** including `/` and `/atlas`;
- provides working backlinks/navigation/search;
- has polished empty states for the five unpopulated Areas;
- uses only three deterministic dummy charts as visual placeholders;
- requires no database, API, CMS, real time-series binding, graph layout, or provenance UI.

## Sources of truth

Read in this order:

1. `AGENTS.md` — execution rules.
2. `CODEX_MASTER_PROMPT.md` — task intent.
3. `contracts/frontend/` — frozen product/page/frontend contracts.
4. `reference/visual-target-inflation-topic.png` — visual acceptance target.
5. `fixtures/site-data/` — exact read model the app must consume.
6. `tasks/` — PR-by-PR execution plan.
7. `ACCEPTANCE_MATRIX.md` — final gate.

## Architecture

```text
compiled site-data JSON
        ↓
thin typed data adapter
        ↓
Next.js App Router / static generation
        ↓
shared editorial components
        ↓
Area / Topic / Question / Indicator / Chart pages
```

The frontend must **not** reconstruct the semantic graph for normal pages. The compiler already did that work.

## Human/Codex operating model

Codex has high autonomy *inside* each approved PR packet. It may implement routine details without asking.
At the end of each PR packet it must stop, run the prescribed checks, summarize changes, and request the
human gate. Target handwritten code change per PR: **≤ ~1,000 net LOC**, excluding lockfiles, generated
scaffolding, and copied fixture data.
