# Figure Kernel v0.2 — Phase 3

Phase 3 closes the first real rendering loop without involving the compiler or frontend.

```text
ResolvedMeasurement
  + ReferenceFrame
  + tiny ChartSpec
  + PlotIntent editorial content
        ↓
small offline renderer
        ↓
PlotArtifact metadata + SVG + PNG
```

## Frozen seed

Exactly three figures are materialized:

1. `pi.ns53` — Monthly headline inflation
   - `ci.ns.cpi_monthly`
   - `timeseries_line`
   - `rf.last_5y`
2. `pi.ns54` — Real effective exchange rate
   - `ci.ns.reer_index`
   - `timeseries_line`
   - `rf.last_5y`
   - inline December 2023 marker
   - preserves the source `stale_warning`
3. `pi.ef45` — Goods trade balance
   - `ci.ef.goods_balance_usd`
   - `timeseries_bar`
   - `rf.last_5y`
   - explicit zero baseline

The v0.1 PlotIntent inventory did not contain sufficiently clean single-measure publication intents for these three seed views. Rather than partially materializing multi-measure or legacy-framing intents, Phase 3 adds three narrow v0.2 PlotIntents through two per-vertical addition files. This is selective semantic migration, not a renderer alias or a mass rewrite of the existing inventory.

## Renderers

The implementation uses only the two renderer primitives frozen in `CONTRACT.md`:

- `timeseries_line`
- `timeseries_bar`

The renderer receives already-normalized canonical measurements from `measurement_resolver.py`. It does not fetch providers, resolve Series, calculate economic transforms, resample data, or mutate semantic content.

## Outputs

Running:

```bash
SOURCE_DATE_EPOCH=1786828800 python figures/materialize.py
```

writes exactly:

```text
plot-artifacts/
  manifest.json
  metadata/*.json
  svg/*.svg
  png/*.png
```

The manifest and metadata retain PlotIntent, ChartSpec, ReferenceFrame, CanonicalIndicator, Series ID, snapshot SHA-256, data-as-of date, freshness state, provider identity, source unit and SeriesBinding normalization.

## Human gate

This phase stops before publication. Review the three PNG/SVG files together and ask:

> Do these look like three figures from the same economic publication, and is the visual grammar simple enough that a fourth ordinary time-series figure would feel routine?

Only after visual approval should Phase 4 attach PlotArtifacts to compiled `site-data` and replace frontend placeholders with static `<img>` rendering.
