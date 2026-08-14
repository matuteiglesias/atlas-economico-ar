# econ-knowledge-compiler v0.1

A small deterministic compiler that converts normalized Argentina Economic Knowledge Layer bundles into frontend-oriented JSON read models.

## Design boundary

The compiler does **not** infer economics, call an LLM, fetch time series, render plots, or design pages.

It does:

1. load one scope bundle and one or more vertical bundles;
2. validate unique IDs and public slugs;
3. resolve normalized references;
4. derive backlinks / `used by` navigation;
5. derive a public graph and two-hop `nearby` entities;
6. apply optional human editorial overrides;
7. compile one page-shaped JSON file per public entity;
8. emit global navigation, search, stats, graph, and editorial-gap reports.

## Public vocabulary

Canonical → public:

- `Concept` → **Topic**
- `QuestionIntent` → **Question**
- `CanonicalIndicator` → **Indicator**
- `PlotIntent` → **Chart**
- `Slice` → **Area**

`Relation`, `ReferenceFrame`, `DerivedIndicator`, and `ChartSpec` remain supporting structures and are embedded/referenced from public read models rather than receiving public routes in v0.1.

## CLI

```bash
python -m pip install -e .

ekc compile \
  --scope argentina_econ_semantic_scope_v0_1.zip \
  --vertical nominal_stabilization_vertical_v0_1.zip \
  --editorial examples/editorial_overrides.yaml \
  --output site-data
```

Repeat `--vertical` as the other five slices are produced. No compiler redesign should be necessary.

## Output

```text
site-data/
├── manifest.json
├── stats.json
├── graph.json
├── navigation.json
├── search-index.json
├── editorial-gaps.json
├── regions/*.json
├── topics/*.json
├── questions/*.json
├── indicators/*.json
└── charts/*.json
```

## Editorial policy

The compiler never fabricates prose merely to fill a UI slot.

Defaults:

- Area `dek` ← slice `mission`
- Topic `dek` ← Concept `description`
- Chart `dek` ← PlotIntent `purpose`
- Question / Indicator `dek` ← empty unless explicitly overridden

Missing copy is reported in `editorial-gaps.json`. Human/editorial writing can therefore improve incrementally without blocking compilation.

## Navigation earned from structure

The compiler derives:

- Topic → Questions / Indicators / Charts
- Question → Topics / Indicators / Charts
- Indicator → Topic / Charts / derived-indicator usage
- Chart → Question / Topics / Indicators / ChartSpec
- Topic incoming/outgoing typed connections
- Area counts and local concept-relation graph
- breadcrumbs
- two-hop `nearby` objects
- global search index

There are intentionally no Trails and no XY/layout positions in v0.1.
