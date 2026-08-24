# REM inflation-expectations frontier scout

## Question

Can official BCRA REM data implement the existing `ci.ns.infl_exp_3m` exactly, without changing Atlas semantics, and if so what is the declared-closure frontier delta?

## Result

**HUMAN_GATE — do not ingest yet.**

The BCRA REM is authoritative, current, monthly, machine-readable through official XLSX workbooks, and it contains exactly the raw forecast information needed to represent short-horizon headline CPI expectations. The remaining blocker is semantic, not source quality.

The current Atlas CanonicalIndicator is:

- `ci.ns.infl_exp_3m`
- label: `Expected inflation three months ahead`
- unit semantics: `percent`
- frequency: `monthly`

That definition does not specify whether the measurement means:

1. the REM median forecast for the single calendar month three months after the survey month (`t+3`), or
2. an aggregate of the next three monthly REM forecasts.

REM itself publishes monthly headline-CPI forecasts for the survey month and six subsequent months. For the aggregate "Total" results, BCRA reports the median. This makes a `t+3` monthly point forecast directly observable from the official REM release.

However, the Atlas also declares `di.ns.real_rate_exante`, which consumes `ci.ns.tamar_nominal` and `ci.ns.infl_exp_3m` and says the nominal rate must be adjusted for a **compatible expected-inflation horizon**. BCRA's own documented short ex-ante real-rate convention has used the **average of the monthly headline-inflation expectations for the following three months**, rather than the point forecast for month `t+3`.

Those are different measurements. Choosing between them in a source scout would silently settle Atlas semantics and potentially alter the meaning of the declared real-rate derivation.

## Official-source findings

### Current BCRA REM

Primary surface:

`https://www.bcra.gob.ar/relevamiento-expectativas-mercado-rem/`

The July 2026 release was published 6 August 2026 from a survey conducted 29–31 July with 45 participants. BCRA describes REM forecasts as participant forecasts, not BCRA projections.

For headline CPI, the current REM asks for monthly forecasts for the current survey month plus six subsequent months. The July 2026 Total median path is visible in the official release; e.g. the October 2026 monthly headline-CPI forecast is 1.7%.

Official current workbook:

`https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/informes/tablas-relevamiento-expectativas-mercado-jul-2026.xlsx`

Official historical workbook:

`https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/informes/historico-relevamiento-expectativas-mercado.xlsx`

Official methodological considerations:

`https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/informes/consideraciones-relevamiento-expectativas-mercado.pdf`

The methodology states that monthly form fields contain the forecast monthly inflation rate for each requested calendar month. BCRA publishes aggregate statistics including mean, median, dispersion and percentiles.

### BCRA Principales Variables API

The standard BCRA "Principales Variables" surface publishes:

`Inflación esperada - REM próximos 12 meses - MEDIANA`

This is a 12-month-ahead annual inflation expectation, not the desired three-month horizon, so it is not a valid mapping for `ci.ns.infl_exp_3m`.

### Datos Argentina mirror

Datos Argentina has an official SSPM dataset named `Relevamiento de Expectativas de Mercado (REM)` whose primary source is BCRA:

`https://datos.gob.ar/dataset/sspm-relevamiento-expectativas-mercado-rem`

Its catalog metadata currently says the dataset was last updated on 28 September 2023. It therefore cannot be assumed to provide the current 2026 REM measurement. No current national Series API identifier was established in this scout for a `t+3` REM forecast.

## Semantic alternatives

### A. Point forecast at `t+3`

Interpret `Expected inflation three months ahead` literally as the REM Total median monthly headline-CPI forecast for calendar month `survey_month + 3`.

- Source semantics: direct.
- Acquisition transform: none beyond selecting the provider-native field/horizon/statistic.
- Match to literal label: strong.
- Problem: the declared ex-ante TAMAR derivation does not demonstrate that a one-month inflation forecast observed three months ahead is horizon-compatible with the nominal TAMAR rate.

Decision: **WATCH / HUMAN_GATE**.

### B. Average of the following three monthly expectations

Use the arithmetic average of the REM monthly headline-CPI expectations for `t+1`, `t+2`, `t+3`, matching BCRA's documented historical short ex-ante real-rate convention.

- Source family: authoritative REM.
- Match to ex-ante real-rate use: economically much stronger.
- Direct Series mapping: **no**. The average is a transformation across three provider fields.
- Current Atlas methodology: no DerivedIndicator declares this calculation, and the CanonicalIndicator definition does not say it is a three-month average.

Decision: **REJECT AS DIRECT MAPPING / HUMAN_GATE FOR SEMANTIC CLARIFICATION**.

## Conditional frontier value

If the semantic owner confirms a direct implementation of `ci.ns.infl_exp_3m`, the generic frontier's declared closure would also unlock `ci.ns.tamar_real_exante`, because `ci.ns.tamar_nominal` is already directly available.

The conditional simulation is recorded in `frontier_simulation.json`. It moves four PlotIntents to `DATA_READY` and affects nine distinct PlotIntents across `q.ns07`, `q.ns12`, and `q.ns18` without double-counting.

The headline census would move conditionally from:

- `DATA_READY`: 52 → 56
- `MISSING_1`: 28 → 27
- `MISSING_2`: 26 → 27
- `MISSING_3_PLUS`: 13 → 9

The four newly `DATA_READY` plots are all in the real-rate/policy-stance family (`q.ns12`): `pi.ns27`, `pi.ns28`, `pi.ns29`, and `pi.ns49`.

The inflation-path (`q.ns07`) and credibility (`q.ns18`) families improve materially but remain blocked by other measurements such as `ci.ns.infl_exp_1m`, `ci.ns.infl_exp_eop`, and `ci.ns.fx_gap_ccl`.

## Smallest next decision

Before any Series registration or adapter work, settle one question:

> Does `ci.ns.infl_exp_3m` mean the REM monthly headline-CPI point forecast for month `t+3`, or a declared aggregation of the following three monthly headline-CPI expectations?

If the answer is `t+3`, the source scout can proceed to pin the exact workbook field/history and choose the smallest reproducible capture path.

If the answer is `average next three months`, the semantic/derived layer must first declare that methodology; it must not be hidden in SeriesBinding or acquisition.

## Boundaries held

This scout did not register a Series, edit SeriesBindings, change a CanonicalIndicator, add a DerivedIndicator, ingest an XLSX, materialize a PlotArtifact, change publication state, or modify the frontend.
