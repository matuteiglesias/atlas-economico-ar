# Atlas UX battle-test — first Playwright pass

Issue: #17  
Branch: `test/playwright-ux-battle-test`

This is an experience report, not a route census. Static integrity is already covered by the publication and Web verification layers; Playwright exercises the promises visible to a person.

## Missions

### 1. Information scent

`home → populated area → substantive question → primary materialized evidence → direct chart`

Invariant:

- unfinished areas are not presented as navigation destinations;
- analytical cards never expose placeholder / preview-pending language;
- a PUBLIC question visibly leads to real PlotArtifact evidence;
- the direct chart has one page-owned title plus data-through/source context.

### 2. Search truthfulness

`Ctrl/Cmd+K or Search → query → visible selected result → destination`

Invariant:

- search is the discoverability projection, not the semantic inventory;
- promoted materialized evidence is reachable;
- an unmaterialized PlotIntent is absent from chart search results;
- keyboard Enter opens the result that is visibly selected, without assuming an entity-kind hierarchy that the UI does not promise.

### 3. Direct evidence + narrow viewport

`direct chart → publication/freshness context → related question/topic`, plus the high-value question/evidence journey at 390×844.

Invariant:

- `addressable != promoted` for historical evidence;
- mobile navigation exposes only populated areas;
- primary evidence remains readable/reachable without horizontal overflow;
- uncaught page errors and `console.error` events fail the suite.

## First-run finding inventory

The first real browser run completed the existing `pnpm check`, installed Chromium, and ran six focused assertions. Three passed immediately and three failed.

| Finding | Class | Evidence | Resolution |
| --- | --- | --- | --- |
| Direct chart repeated the same answered question in main content, the typed Questions context group, and again under Nearby. | `NAVIGATION_LOOP` | Playwright's role locator found three identical question links on the direct chart route. The Nearby copy added no new path. | Nearby now excludes hrefs already represented by Topics / Questions / Indicators. Main content and typed context navigation remain intentionally available. |
| Keyboard-search test expected a topic even though the visibly selected first result was the substantive reserve-position question. | test assumption, not product defect | Enter correctly opened `How strong is Argentina's reserve position?`. | Test now asserts the selected option's accessible name and verifies Enter opens that exact visible choice. |
| Direct-chart related-navigation assertion was ambiguous because of the same duplicate Nearby path. | `NAVIGATION_LOOP` | Same reproduced duplicate as the first finding. | Covered by the same bounded deduplication repair and regression assertion. |

## What did *not* fail

The first pass found no reproduced:

- `DEAD_END` in the tested primary journey;
- `QUESTION_WITHOUT_EVIDENCE`;
- placeholder/fake-chart leak;
- search promotion of the tested semantic-only PlotIntent;
- incorrect promotion of the tested historical chart;
- `MOBILE_BREAK` or horizontal overflow;
- browser `pageerror` / `console.error` failure.

These statements are intentionally limited to the tested missions, not claims about every public topic/indicator route.

## Cheap surface-state byproduct

`/atlas` already has an explicit producer-visible distinction between active and planned regions. Planned roadmap cards therefore receive a small `data-surface-state="planned"` marker and a lighter neutral surface. No heuristic is inferred from page thinness, and no new status model is introduced.

## Experience-debt delta

- one duplicate related-navigation avenue removed;
- one brittle product-assumption removed from the browser test itself;
- high-value desktop, keyboard, publication-state and mobile journeys become executable regression contracts;
- zero semantic entities, economic claims, sources, measurements, or public routes added to satisfy the tests.
