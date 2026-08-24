# Real Economy official-series scout

Base: `974ae9f5f56ab1595690e5b5e333dee285f435b3`  
Branch: `research/real-economy-official-series-scout`  
Scope: research/scouting only; no Series registration, capture, binding, PlotArtifact materialization, publication, activation, or adapter implementation.

## Decision

**B. FIRST GENERALIZE EXISTING DATOS ARGENTINA CAPTURE, THEN TRANCHE**

The preferred first data investment is a six-Series tranche, all delivered through the existing Argentina national Series de Tiempo API:

| CanonicalIndicator | Provider Series ID | Primary source | Role |
|---|---|---|---|
| `ci.re.emae_sa_index` | `143.3_NO_PR_2004_A_31` | INDEC | aggregate monthly activity |
| `ci.re.manufacturing_sa_index` | `453.1_SERIE_DESEADA_0_0_24_58` | INDEC | manufacturing breadth |
| `ci.re.construction_sa_index` | `33.2_ISAC_SIN_EDAD_0_M_23_56` | INDEC | construction breadth |
| `ci.re.real_gdp_level` | `3.2_OGP_D_2004_T_17` | INDEC | quarterly aggregate level + declared q/q/y/y closure |
| `ci.re.private_consumption_real` | `3.2_DGCP_D_2004_T_27` | INDEC | household-demand path + declared q/q closure |
| `ci.re.gfcf_real` | `3.2_DGI_D_2004_T_19` | INDEC | investment path + declared q/q closure |

These are not six loosely related finds. In the reconstructed current frontier, each has meaningful marginal closure inside the package.

## Preconditions and authority

The scout starts from current `main` after PR #38 commissioned `verticals/real_economy_vertical_v0_1`. The provider-neutral frontier kernel is present in `growth/frontier.py` and its offline builder in `scripts/build-growth-frontier.py`.

The semantic authority used here is the merged Real Economy vertical, especially its current CanonicalIndicators, DerivedIndicators, PlotIntents and QuestionIntents. No new measurement demand was invented.

The repository execution environment available to this scout could inspect and mutate GitHub but could not obtain an executable checkout because outbound GitHub DNS/network access from the command runner was unavailable. Therefore the frontier counts below were reproduced from the current kernel's declared closure and missing-count rules over the current-main declarations rather than by pretending that `build-growth-frontier.py` ran. Before an ingestion PR, rerun:

```bash
python scripts/build-growth-frontier.py \
  --output-dir /tmp/atlas-real-economy-frontier
```

and compare the resulting Real Economy rows with `tranche_simulation.json`.

## Current Real Economy frontier

Current declared Real Economy has 24 PlotIntents.

| State | Count |
|---|---:|
| DATA_READY | 0 |
| MISSING_1 | 8 |
| MISSING_2 | 10 |
| MISSING_3_PLUS | 6 |

The eight current MISSING_1 PlotIntents are:

`pi.re01`, `pi.re04`, `pi.re05`, `pi.re06`, `pi.re08`, `pi.re17`, `pi.re18`, `pi.re19`.

Structurally, the highest-return direct measurements are not all from one story. GDP, GFCF and private consumption close several single-missing and cross-port plots. EMAE provides the aggregate monthly anchor. Manufacturing and construction have low standalone closure but high combination value because they complete distinct relative-performance plots and declared y/y closure.

## Official-source search

The candidate search was constrained to existing declared CanonicalIndicators and authoritative Argentine sources:

- Argentina national API Series de Tiempo / Datos Argentina;
- Ministerio de Economía / Economía en números / aggregate economic database surfaces;
- underlying INDEC releases and national-accounts workbooks where API catalog metadata was insufficient.

The important architectural distinction is:

- **transport/API provider:** Argentina national Series de Tiempo API;
- **primary source institution:** predominantly INDEC for the preferred tranche.

The quarterly GDP/demand candidates come from the official seasonally adjusted `Oferta y Demanda Globales. Base 2004` family. The current INDEC seasonally adjusted workbook inspected by the scout covers 2004-Q1 through 2026-Q1 and confirms the component identities GDP, imports, private consumption, public consumption, FBCF and exports. The current monthly INDEC surfaces also confirm active 2026 publication of EMAE and manufacturing production; construction is active but its eventual API-mirror latest observation should be checked during capture.

A catalog-page maintenance timestamp is not treated as a Series observation date. Every eventual capture must verify provider metadata and the actual latest observation through the API.

## Why this tranche

Simulating the preferred six direct measurements plus only already-declared DerivedIndicator closure changes the Real Economy frontier to:

| State | After tranche |
|---|---:|
| DATA_READY | 14 |
| MISSING_1 | 2 |
| MISSING_2 | 6 |
| MISSING_3_PLUS | 2 |

Newly DATA_READY:

`pi.re01`, `pi.re04`, `pi.re05`, `pi.re06`, `pi.re07`, `pi.re08`, `pi.re09`, `pi.re11`, `pi.re12`, `pi.re17`, `pi.re18`, `pi.re19`, `pi.re22`, `pi.re23`.

Declared derivative outputs closed by the tranche:

- `ci.re.emae_yoy`
- `ci.re.manufacturing_yoy`
- `ci.re.construction_yoy`
- `ci.re.real_gdp_qoq`
- `ci.re.real_gdp_yoy`
- `ci.re.private_consumption_qoq`
- `ci.re.gfcf_qoq`

At least one DATA_READY evidence path then touches eight current QuestionIntents: `q.re01`, `q.re02`, `q.re03`, `q.re04`, `q.re05`, `q.re07`, `q.re11`, `q.re12`.

This does **not** mean eight questions are publication-ready; it means the measurement frontier no longer blocks at least one substantive plot for them.

A coherent six-Series national-accounts-only alternative (GDP, private/public consumption, GFCF, exports, imports) reaches 13 DATA_READY plots and is a strong later package, but it is narrower. The preferred mixed tranche reaches 14 while serving aggregate activity, sectoral relative performance, consumption, investment, historical comparison and already-owned financial-condition boundary ports.

## Candidate decisions

Full metadata is in `candidate_series.json`.

### PURSUE

The six preferred Series above are classified `EXACT`.

### WATCH

- `ci.re.public_consumption_real`, `ci.re.exports_real`, `ci.re.imports_real`: exact national-accounts sources exist, but their first-tranche marginal value is more combination-dependent.
- `ci.re.gfcf_construction_real`, `ci.re.gfcf_machinery_real`: official constant-price component Series exist, but the inspected catalog resource did not make seasonal/comparability semantics explicit enough for a clean binding. Human methodology check first.

### DROP for this scout

- `ci.re.agriculture_sa_index`: an official sector series is not enough if seasonal adjustment is not established. Do not map a raw sector series to an `_sa_index`.
- `ci.re.mining_energy_sa_index`: official mining and energy measures exist, but the current CanonicalIndicator is combined. Do not invent an aggregation.
- `ci.re.commerce_sa_index`: currently no Real Economy PlotIntent demands it, so it is not a frontier priority.

Interesting official high-frequency measures with no current CanonicalIndicator are recorded only as `ATTRACTIVE_BUT_NOT_DECLARED`.

## Activation contribution

The preferred tranche moves the data frontier from 0 to 14 DATA_READY Real Economy PlotIntents.

For a conservative **three-question evidence opening**, the smallest additional **data** gap after this tranche is **none**: current `q.re04`, `q.re05` and `q.re07`/`q.re12` can have substantive measurement paths. That does not activate the region. Plot materialization, scientific curation, question publication, editorial framing and browser/UX gates remain mandatory.

The next high-value data gap is the two-Series investment-composition pair for `q.re06`:

- `ci.re.gfcf_construction_real`
- `ci.re.gfcf_machinery_real`

but it remains behind a semantic HUMAN_GATE on seasonal/comparability treatment.

Full state transitions are in `tranche_simulation.json`.

## Adapter conclusion

No new Ministerio de Economía adapter is justified.

All six preferred provider IDs belong to the same national Series API contract already used by `series/capture.py`. The existing acquisition design already preserves the right invariants: provider-native ID, raw bytes, provider metadata, normalized date/value snapshot, provenance, SHA-256, freshness and `economic_transform=none`.

However, current capture validation is still intentionally frozen around the original three-Series seed milestone. `series/validate.py` requires exactly three registered Series and freezes the complete raw/snapshot file set. That is a real implementation gate.

Therefore the next implementation step should be a **small Datos Argentina generalization**: make the existing transport/validation path registry-driven beyond the seed freeze while preserving its byte/provenance guarantees. Only then ingest the preferred six-Series tranche.

See `adapter_assessment.md` for the bounded architecture finding.

## Final action

**B. FIRST GENERALIZE EXISTING DATOS ARGENTINA CAPTURE, THEN TRANCHE.**
