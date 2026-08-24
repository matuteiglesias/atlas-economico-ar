# Source and capture assessment

## Authority

`BCRA REM` is the preferred source family.

The survey is administered and published by the Banco Central de la República Argentina. BCRA explicitly distinguishes REM participant forecasts from BCRA forecasts, which is desirable provenance for an Atlas market-expectations measurement.

The July 2026 release demonstrates current operation: survey 29–31 July 2026, publication 6 August 2026, 45 participants.

## Measurement grain

For headline CPI, REM collects a monthly forecast for the current survey month and six subsequent calendar months. The value in each monthly field is the forecast percentage change for that specific month's headline CPI.

BCRA publishes multiple aggregate statistics for each variable-period cell. The standard `Total` path shown in the current report is the median; the Top-10 path is an average for a selected forecaster group.

Therefore a reproducible source identity must include at least:

- survey vintage month;
- variable: IPC Nivel General;
- forecast target calendar month / relative horizon;
- aggregate statistic (`Total` median if that is the selected Atlas convention).

A title such as "REM inflation expectation" is not a sufficient provider identity.

## Reproducibility

The official BCRA release supports the core acquisition requirements in principle:

- authoritative institution: BCRA;
- regular monthly publication;
- current XLSX workbook;
- stable historical-results XLSX locator;
- provider methodology PDF;
- raw workbook bytes can be preserved locally and hashed;
- retrieval can be timestamped;
- a normalized monthly snapshot can be generated without economic transformation **if** the selected source measurement is a provider-native variable-period-statistic cell.

The main difference from existing Atlas BCRA monetary capture is transport. REM is published as workbooks rather than the monetary-statistics v4 Series API contract.

## Existing transport reuse

### Datos Argentina capture

The current Atlas `series/capture.py` is specifically a Datos Argentina Time Series API client. It requires a stable native provider Series ID and fetches values plus provider metadata from:

`https://apis.datos.gob.ar/series/api/series/`

Datos Argentina does catalog an SSPM REM dataset, with BCRA as primary source. However, its catalog currently reports its last update as 28 September 2023. This scout did not establish a current 2026 national Time Series API ID for the desired REM horizon.

Conclusion: **do not claim `REUSE_EXISTING_DATOS_ARGENTINA_TRANSPORT` yet.** The existence of an old catalog resource does not prove a current API-backed Series implementation.

### BCRA monetary capture

The existing BCRA tranche machinery targets a different API/catalog contract. A REM workbook should not be disguised as a monetary API Series.

### If the semantic gate resolves to a provider-native `t+3` cell

The next implementation scout should first make one bounded attempt to identify a current national Time Series API ID for that exact REM measure.

- If found and current: reuse the existing Datos Argentina transport, with primary source institution retained as BCRA.
- If not found: the scientifically clean implementation is a small **new file-oriented REM capture path** that preserves the official current/historical workbook bytes and explicit field identity. It should not generalize into a broad spreadsheet framework.

No adapter should be implemented until the semantic gate is resolved.

## Why BCRA variable 7933 is not the answer

BCRA's standard `Principales Variables` surface includes a machine-readable time series for `Inflación esperada - REM próximos 12 meses - MEDIANA` (provider variable 7933 in the API ecosystem).

That series is a 12-month expectation, whereas `ci.ns.infl_exp_3m` is a three-month-horizon concept. Mapping it would be a semantic substitution, not a normalization. It is therefore rejected even though its API transport is convenient.

## Source/semantic gate

### Literal point-horizon interpretation

A monthly headline-CPI `t+3` Total median is provider-native REM information. Selecting the same relative horizon across vintages is a source projection, not an economic aggregation.

This is the strongest direct candidate for the current CanonicalIndicator label.

### Three-month-average interpretation

BCRA has documented a short ex-ante real-rate construction using the average of the monthly headline inflation expectations for the following three months. This makes the source family highly relevant to `di.ns.real_rate_exante`.

But an average of three horizon cells is a calculation. Under Atlas contracts it cannot be performed implicitly by acquisition or representation-only SeriesBinding. If this is the intended `ci.ns.infl_exp_3m`, the semantic/derived layer needs to say so first.

## Recommendation

**DO NOT INGEST YET — SEMANTIC AMBIGUITY IS MATERIAL.**

This is a favorable failure mode: source authority, freshness, horizon coverage and reproducibility are all adequate. One narrow semantic decision separates the Atlas from a high-leverage measurement addition.
