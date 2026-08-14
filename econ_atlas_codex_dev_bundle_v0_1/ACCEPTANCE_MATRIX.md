# Final acceptance matrix

## Build

- [ ] App lives under `web/`.
- [ ] `pnpm lint` passes.
- [ ] `pnpm typecheck` passes.
- [ ] `pnpm build` passes.
- [ ] Static export/build artifact succeeds without request-time server dependencies.

## Route coverage

Fixture public entities: **143**.
Total pages with `/` and `/atlas`: **145**.

- [ ] all 6 Areas
- [ ] all 25 Topics
- [ ] all 18 Questions
- [ ] all 42 Indicators
- [ ] all 52 Charts
- [ ] `/`
- [ ] `/atlas`
- [ ] unknown slugs produce a proper not-found outcome

## Data architecture

- [ ] Ordinary entity pages load precompiled entity JSON.
- [ ] React does not traverse `graph.json` to assemble normal page joins.
- [ ] No runtime network API is needed for knowledge data.
- [ ] Missing editorial prose is handled without invented filler.
- [ ] No ontology IDs appear in standard UI.

## Visual

- [ ] `/topics/inflation` strongly resembles the reference at 1536×1024.
- [ ] Three-zone desktop structure works.
- [ ] Editorial serif/sans hierarchy works.
- [ ] Fine borders, quiet shadows, restrained blue accent.
- [ ] Questions are prominent.
- [ ] Exactly three dummy chart styles feel polished.
- [ ] Other chart pages/cards have a coherent placeholder.
- [ ] Dummy charts are labeled illustrative on full Chart pages.

## Navigation

- [ ] left Explore navigation works
- [ ] breadcrumbs work
- [ ] Topic → Question works
- [ ] Question → Chart works
- [ ] Chart → Indicator works
- [ ] Indicator → Topic works
- [ ] related/backlink links resolve
- [ ] unpopulated Areas have polished empty states

## Search

- [ ] Cmd+K / Ctrl+K
- [ ] grouped results
- [ ] keyboard navigation
- [ ] links resolve
- [ ] no backend/search service

## Responsive / accessibility

- [ ] desktop 1536×1024
- [ ] tablet ~768×1024
- [ ] mobile ~390×844
- [ ] no horizontal scrolling
- [ ] mobile Explore drawer
- [ ] visible focus
- [ ] semantic landmarks
- [ ] icon-only controls labeled
- [ ] placeholder SVGs accessible/decorative as appropriate

## Scope

- [ ] no trails
- [ ] no XY atlas layout
- [ ] no graph visualization project
- [ ] no news
- [ ] no provenance UI
- [ ] no DB
- [ ] no CMS
- [ ] no auth
- [ ] no live time-series fetching
- [ ] no chart library
- [ ] no other semantic vertical implementation

**Release status:** ACCEPT only when every applicable item is checked or explicitly waived by the human reviewer.
