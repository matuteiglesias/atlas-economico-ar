# Figure Grammar v0.2

Status: architecture freeze candidate

This contract defines the smallest figure layer that connects Atlas semantic demand to reproducible static publication.

The design rule is deliberately conservative:

> Inline first; abstract only after repeated real use.

The figure system is not a dashboard engine and is not a second ontology. It should remain a thin bridge between semantic knowledge, registered measurements, reproducible rendering, and the static frontend.

## Core grammar

```text
Question
  ↓
PlotIntent
  ↓ requires
CanonicalIndicator
  ↑
  ├── SeriesBinding ← SeriesSnapshot
  └── DerivedIndicator ← CanonicalIndicator inputs

PlotIntent
  + resolved CanonicalIndicators
  + ReferenceFrame
  + tiny ChartSpec
  ↓
Materializer
  ↓
PlotArtifact
  ↓
Compiler
  ↓
site-data
  ↓
static frontend
```

The responsibilities are frozen as follows:

- **PlotIntent** — what we want to show and why. It remains the semantic/public identity of a chart.
- **CanonicalIndicator** — what is being measured, including canonical unit semantics and frequency.
- **Series** — a registered provider-native technical observation source.
- **SeriesBinding** — an operational relation describing how one Series implements one CanonicalIndicator.
- **DerivedIndicator** — an explicit economic/statistical calculation from canonical inputs.
- **ReferenceFrame** — the reusable temporal window from which data are viewed.
- **ChartSpec** — the minimal visual recipe for one PlotIntent.
- **Renderer** — a small implementation primitive such as `timeseries_line` or `timeseries_bar`.
- **PlotArtifact** — the exact materialized publication output and the evidence needed to reproduce it.

## 1. PlotIntent remains semantic

PlotIntent owns explanatory demand:

- the question(s) answered;
- the canonical indicator(s) required;
- the editorial purpose of the figure.

PlotIntent MUST NOT own:

- provider URLs or provider-specific Series IDs;
- raw/snapshot paths;
- unit normalization;
- rendering implementation details;
- SVG/PNG paths;
- frontend behavior.

A temporal variant does not automatically imply a new PlotIntent. The same PlotIntent may be materialized under different ReferenceFrames when the economic question is unchanged.

## 2. SeriesBinding is operational, not an ontology node

`CanonicalIndicator != Series` remains a hard boundary.

SeriesBinding connects a registered technical Series to a CanonicalIndicator. In v0.2 it may perform only representation/unit normalization that does not change the economic meaning of the measurement.

Allowed normalization kinds:

```yaml
normalization:
  kind: identity
```

or:

```yaml
normalization:
  kind: scale
  factor: 100
```

Examples of valid normalization:

- fractional monthly inflation `0.021` → canonical percent `2.1` via `scale: 100`;
- USD millions → USD billions via `scale: 0.001`;
- an index already expressed in canonical units via `identity`.

SeriesBinding MUST NOT implement economic transformations such as:

- month-over-month or year-over-year growth;
- rolling windows;
- annualization;
- cumulative sums;
- rebasing to an economic anchor;
- real/nominal adjustment;
- ratios across distinct measurements;
- model estimates.

Those belong in DerivedIndicator.

The v0.2 implementation should begin with only `identity` and `scale`. New normalization primitives require a real measurement case, not anticipation.

## 3. DerivedIndicator owns economic calculation

DerivedIndicator remains the only place for reviewable economic/statistical transformations.

Examples:

- YoY inflation;
- rolling 3-month annualized inflation;
- acceleration;
- cumulative FX purchases;
- FX gaps;
- real interest rates;
- change relative to a curated anchor when the change itself is the economic measurement.

The distinction is:

```text
SeriesBinding normalization = representation/unit
DerivedIndicator            = economic/statistical meaning
```

No renderer or ChartSpec may silently perform a DerivedIndicator transformation.

## 4. ReferenceFrame is temporal only

ReferenceFrame v0.2 means:

> a reusable temporal view context applied after canonical measurements are resolved.

Allowed kinds:

- `relative` — e.g. last 12 months;
- `fixed` — explicit start/end dates, where `end: latest` is allowed;
- `available_history` — all observations available for the resolved figure inputs.

ReferenceFrame does not define:

- rolling calculations;
- YoY/MoM comparisons;
- annualization;
- policy target paths;
- peer-country sets;
- data frequency;
- aggregation rules.

This resolves an ambiguity in the v0.1 inventory, where objects such as `rolling_3m_annualized`, `trailing_12m`, fixed event anchors, policy targets and cross-sectional peers were all represented as ReferenceFrames.

A phrase such as “trailing 12 months” must be disambiguated:

- **view the latest 12 months** → ReferenceFrame;
- **calculate a rolling 12-month quantity** → DerivedIndicator.

Curated historical periods such as governments, crises or policy regimes may be added as fixed ReferenceFrames when a real figure requires them. Their start/end dates are editorial content and must be explicit in data, not hidden in renderer code.

## 5. Annotations stay inline in v0.2

Small historical/event markers are part of ChartSpec:

```yaml
annotations:
  - date: 2023-12-01
    label: December 2023
```

Do not create a separate annotation/event ontology until repeated real figures demonstrate that reuse is valuable.

An annotation marks context. It does not change the underlying measurement.

## 6. ChartSpec becomes intentionally small

A v0.2 ChartSpec answers one question:

> How should this PlotIntent be drawn?

Required fields:

```yaml
id: cs.example
plot_intent_id: pi.example
renderer: timeseries_line
frame_id: rf.last_12m
```

Optional fields in v0.2:

```yaml
annotations: []
overrides: {}
```

The initial supported override is intentionally tiny:

```yaml
overrides:
  zero_baseline: true
```

A ChartSpec MUST NOT repeat information already owned elsewhere, including:

- title or question IDs;
- canonical indicator requirements;
- provider/Series bindings;
- provider URLs;
- economic transforms;
- source provenance;
- refresh policy;
- data-as-of policy.

Those are resolved or recorded by their owning layer.

## 7. Renderer contract

v0.2 starts with exactly two renderer IDs:

- `timeseries_line`;
- `timeseries_bar`.

A renderer receives already-resolved canonical data plus a ReferenceFrame and the small visual options from ChartSpec.

A renderer MAY handle:

- one or more already-compatible canonical series;
- a temporal x-axis;
- canonical/display units supplied by the resolved measurements;
- inline annotations;
- title/subtitle/source/footer supplied by the materialization context;
- SVG and PNG output.

A renderer MUST NOT:

- fetch network data;
- resolve Series bindings;
- decide economic transformations;
- infer aggregation semantics;
- mutate semantic content;
- call the frontend.

`multi_line_time_series`, `line_with_reference_event`, `dual_measure_time_series`, `cumulative_line_or_area`, and similar v0.1 names are not independent renderer primitives in v0.2 unless repeated real figures later prove that they should be.

## 8. PlotArtifact is the publication boundary

A PlotArtifact records the exact figure that was materialized.

Required v0.2 metadata:

```yaml
schema_version: "0.2"
plot_intent_id: pi.example
chart_spec_id: cs.example
frame_id: rf.last_12m
data_as_of: 2026-07-01
generated_at: 2026-08-15T00:00:00Z
indicator_ids:
  - ci.example
series_ids:
  - series.example
snapshot_sha256:
  series.example: <sha256>
outputs:
  svg: plot-artifacts/svg/example.svg
  png: plot-artifacts/png/example.png
alt_text: Example chart description.
```

The artifact may also include resolved source labels and transformation provenance when materialization is implemented.

The critical property is reproducibility: an artifact must identify the exact semantic intent, visual spec, temporal frame, canonical measurements, underlying Series snapshots, data-as-of date, generated files, and enough provenance to reproduce the publication.

PlotArtifact is MATERIALIZED evidence. It is not another source of economic truth.

## 9. Frontend boundary

The frontend remains intentionally dumb.

The future compiled chart read model may contain:

```json
{
  "artifact": {
    "status": "materialized",
    "svg": "/plots/example.svg",
    "png": "/plots/example.png",
    "dataAsOf": "2026-07-01",
    "altText": "..."
  }
}
```

The frontend displays the static artifact. It does not fetch economic APIs, recompute indicators, choose frames, or render charts dynamically.

## 10. v0.1 ChartSpecs are candidate inventory

The existing vertical ChartSpecs are preserved untouched as design inventory. They contain useful hypotheses about figures the Atlas may eventually need, but they are not the v0.2 runtime contract.

They MUST NOT be mass-migrated merely to make schemas uniform.

Migration is selective:

1. a PlotIntent becomes measurement-ready;
2. a real figure is needed;
3. the old candidate spec is inspected;
4. the smallest v0.2 ChartSpec that preserves the intended visual meaning is created;
5. new renderer capability is introduced only when the current two renderers cannot express a real, approved figure.

`legacy_inventory.yaml` records the old files explicitly as `candidate_inventory`.

## 11. Readiness is computed, not modeled

Do not create semantic nodes for `DATA_READY`, `RENDER_READY`, or `PUBLISHED`.

These states are derived from actual objects:

```text
required indicators resolvable → measurement-ready
+ valid ChartSpec              → render-ready
+ PlotArtifact exists          → materialized
+ compiler/frontend inclusion  → published
```

This keeps pipeline state from becoming a second graph that can drift from reality.

## 12. Non-goals for Figure Grammar v0.2

Not part of this contract phase:

- no SVG or PNG generation;
- no matplotlib implementation;
- no compiler changes;
- no frontend changes;
- no runtime economic API;
- no charting library in React;
- no general-purpose transform DSL;
- no automatic frequency conversion;
- no automatic resampling/aggregation;
- no mass migration of existing ChartSpecs;
- no new large template taxonomy;
- no ontology nodes for acquisition, snapshots, bindings, readiness, or annotations.

## 13. Acceptance test for the architecture

The model should remain explainable in one sentence per object:

```text
PlotIntent          = what do we want to show?
CanonicalIndicator  = what is measured?
SeriesBinding       = how do we observe it?
DerivedIndicator    = how do we calculate it?
ReferenceFrame      = when do we look?
ChartSpec           = how do we draw it?
PlotArtifact        = what exactly did we publish?
```

If a future feature cannot be placed naturally into one of those responsibilities, the default response is not to add another abstraction. First test the need with a real figure.
