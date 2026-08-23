# Figure curation agent contract

Purpose: progressively improve the Atlas figure set by inspecting real rendered PlotArtifacts and reducing curation debt without changing economic meaning.

Read first:

- `figures/PUBLICATION_QA.md`
- `figures/publication_qa.yaml`
- `figures/CONTRACT.md`
- `figures/PRESENTATION_VARIANTS.md`
- `figures/FIGURE_KERNEL.md`
- current `plot-artifacts/manifest.json`

## Core principle

A PlotArtifact can be technically valid and reproducible yet still be weak, redundant, stale, misleading, or unprofessional as a published analytical figure.

Curation operates *after* measurement validity. Never repair visual quality by changing source facts or substantive semantics.

## Unit of work

The unit is one materialized PlotArtifact plus its PlotIntent, ChartSpec, measurements, provenance, and current publication-QA state.

Inspect the actual canonical review PNG or SVG from `artifact.outputs`. These are intentionally self-describing and include title/subtitle/source chrome so an AI agent or human reviewer can understand the image in isolation. Do **not** curate from `artifact.embed_outputs`; those are deterministic page-owned presentation projections and are not the rendered evidence hashes stored in the curation ledger.

Do not judge a figure from YAML alone.

## Bounded queue

Inspect at most **6 figures per run**. Choose in this order:

1. newly created or materially changed PlotArtifacts;
2. quarantined figures for which a bounded fix is plausible;
3. figures with semantic/technical hazard flags;
4. current-state figures with stale inputs;
5. likely redundant or dominated figures;
6. oldest genuinely unreviewed figures.

Do not re-review stable approved figures unless their structural fingerprint changed or an automatic hazard was triggered.

## Three gates

Apply in order.

### 1. Truth

Could a competent reader infer something the evidence does not support?

Check at minimum:

- stock vs flow;
- level vs change/growth;
- nominal vs real;
- frequency mismatch;
- incompatible units/scales;
- stale series presented as current evidence;
- denominator/sample/construction mismatch;
- derived transformation appropriateness;
- discontinuities or source breaks that could be mistaken for events.

Truth failure => `QUARANTINE` or `HUMAN_GATE`. Do not beautify a scientifically misleading comparison.

### 2. Usefulness

Does this figure answer a distinct economic question better than nearby existing figures?

Check:

- near-duplicate PlotIntents;
- weaker nominal representation when a defensible real/indexed figure exists;
- two figures carrying the same information with one clearly superior;
- a valid figure whose value is archival/reference rather than featured analysis.

Usefulness failure => `REFERENCE` or `SUPERSEDED` with a named preferred PlotIntent when possible.

### 3. Publication

Can a reader recover the intended analytical message quickly and defensibly?

Check:

- reference frame/window;
- geometry (line, step, bar, etc.);
- axis scale and compression;
- unit readability;
- legend order and distinguishability;
- title/question alignment;
- density and overplotting;
- unexplained spikes/breaks;
- whether the chart would be acceptable in a professional economics report without a verbal apology.

Publication failure with sound semantics => `FIX_PENDING` and a bounded rendering fix.

## Working states

Use these concepts when recording review evidence. The current implementation may not yet encode every state; do not force schema changes into unrelated curation work.

Terminal publication decisions:

- `APPROVED` — professional analytical figure.
- `HISTORICAL` — valid historical evidence, not current-state evidence.
- `REFERENCE` — valid but intentionally not part of the featured analytical surface.
- `SUPERSEDED` — valid but dominated by a named better figure.
- `QUARANTINE` — potentially misleading or unresolved; preserve lineage/artifact but exclude from promoted surfaces.

Non-terminal:

- `UNREVIEWED`
- `FIX_PENDING`
- `HUMAN_GATE`

Never treat quarantine as deletion and never delete measurements merely to reduce the public figure count.

## Allowed autonomous fixes

An agent may, when clearly justified:

- choose a better existing ReferenceFrame;
- switch among already-supported renderer/geometry capabilities;
- improve labels, legend ordering, units, or chart titles without changing economic meaning;
- mark stale-but-valid material historical;
- quarantine a clearly misleading rendering;
- supersede an obviously dominated figure and name the preferred existing figure;
- add a regression test for a demonstrated rendering/semantic bug.

Make at most **2 production figure fixes per run**. Rerender and inspect each result before accepting it.

## Human gates / prohibited autonomous changes

Do not autonomously:

- change a source binding to improve a chart;
- redefine a CanonicalIndicator;
- invent or alter a derived methodology;
- change denominators/sample definitions;
- reinterpret a provider variable;
- introduce substantive event annotations without verified evidence;
- add a new renderer primitive merely to rescue one weak chart;
- perform broad style-system redesign.

When one of these is required, leave a precise `HUMAN_GATE` with the smallest decision needed.

## Hazard preflight

Before visual review, identify risk flags such as:

- `STOCK_FLOW_MISMATCH`
- `FREQUENCY_MISMATCH`
- `STALE_CURRENT_CLAIM`
- `LONG_NOMINAL_LEVEL`
- `DUAL_AXIS_RISK`
- `SCALE_COMPRESSION`
- `UNEXPLAINED_BREAK`
- `DENSE_ENCODING`
- `REDUNDANT_FIGURE`
- `MISSING_COMMON_PERIOD`

These are review priorities, not automatic publication decisions.

## Review evidence

A useful review record should identify:

- PlotIntent ID;
- exact canonical review PNG/SVG inspected from `artifact.outputs`;
- current structural inputs (ChartSpec, renderer, ReferenceFrame, indicator IDs);
- hazard flags;
- Truth / Usefulness / Publication decision;
- terminal state or exact bounded fix;
- preferred PlotIntent when superseded;
- human decision required, if any;
- post-fix inspection result.

Future tooling should distinguish a **structural review fingerprint** from the exact rendered PNG hash. A routine data refresh should not invalidate a stable visual review unless structure changes or an automatic hazard appears.

## Definition of done for one curation run

A run is done only when:

1. <=6 actual canonical review figures were inspected;
2. every reviewed figure has a terminal state, a bounded fix, or an explicit human gate;
3. <=2 autonomous production fixes were made;
4. changed figures were rerendered and visually inspected;
5. relevant figure/publication/site validation passes;
6. the report states the curation-debt delta, e.g. `reviewed 6 -> approved 3, superseded 1, repaired 1, quarantined 1; debt -4`.

The objective is convergence: fewer ambiguous publication objects and a smaller, stronger featured figure set over repeated runs.
