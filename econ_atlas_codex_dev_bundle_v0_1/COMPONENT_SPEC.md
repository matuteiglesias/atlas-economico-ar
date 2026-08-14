# Component responsibilities

Prefer a small reusable system.

## Shell

### `SiteHeader`
- brand: `ARGENTINA / ECONOMIC ATLAS`
- search trigger with keyboard hint
- optional About link
- no elaborate nav bar

### `ExploreRail`
- uses `navigation.json`
- Area list
- quick links
- active state
- responsive: becomes Sheet/drawer on narrow screens

### `ContextRail`
- accepts already-derived page data
- never queries/traverses graph
- sections selected by page kind

## Editorial primitives

### `EntityHeader`
Props should be generic enough for all public kinds:
- kind/eyebrow
- title
- dek
- intro
- region

### `Breadcrumbs`
Render existing breadcrumbs + current title.
Do not infer semantic ancestry.

### `Section`
Consistent title/action spacing.

### `StatStrip` / `StatRows`
Quiet count presentation.

## Cards

### `QuestionRow` / `QuestionCard`
Title-first, little chrome.

### `TopicLink`
Direct topic relation with optional humanized relation label.

### `ChartCard`
- title
- optional short purpose/dek
- preview surface
- `View chart →`

### `IndicatorRow`
Compact measurement reference.

## Semantic relation labels

Humanize safely:
- `measurement_of` → `Measures`
- `component_of` → `Part of`
- `derived_from` → `Derived from`
- `comparison` → `Compared with`
- `economic_mechanism` → `Connected through`
- `contributes_to` → `Contributes to`
- `constraint_on` → `Constrains`
- `enables` → `Enables`
- `associated_with` → `Associated with`
- `agenda_related` → `Often discussed with`

Do not rewrite a relation into stronger causal language.

## Chart preview system

One `ChartPreview` dispatcher:
- three known slugs → deterministic SVG dummy charts
- everything else → `GenericChartPlaceholder`

No chart library.

## Search

Search palette groups fixture documents by:
1. Questions
2. Topics
3. Charts
4. Indicators
5. Areas

Simple normalized substring/token search is sufficient for v0.1.
Do not add embeddings or a search service.
