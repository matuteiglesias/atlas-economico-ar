# BCRA six-Series expansion batch v0.1

Frozen provider IDs: **1, 5, 11, 15, 78, 197**.

The selection is intentionally heuristic rather than a formal GPCA ranking. It
maximizes immediate system-wide coverage across reserves, the official exchange
rate, money-market rates, the monetary base, BCRA FX purchases, and private
transactional M2.

## Binding rule

Provider bytes remain untouched in `series/raw/bcra_monetarias_v4/`. Series
snapshots preserve provider values. Only SeriesBinding may perform unit
normalization; economic transformations live in `figures/derived_resolver.py`.

## Implemented downstream derivations

- official FX monthly change from month-end wholesale FX;
- gross-reserve monthly change;
- gross-reserve YTD accumulation;
- cumulative BCRA FX purchases since 2026-01-01;
- real monetary base, Dec-2023=100;
- real private transactional M2, Dec-2023=100.

The real-money convention is explicit: use each month's final daily stock,
reconstruct a CPI price index from registered monthly inflation, deflate, and
rebase the real balance to December 2023.

## Deliberately still blocked

No projection-gap, M2/GDP, reserve-adequacy, NIR, FX-band, parallel-FX, or
expected-real-rate output is synthesized without the additional required
measurement. Legacy candidate PlotIntents remain inventory unless every required
measurement is resolvable under an explicit methodology.
