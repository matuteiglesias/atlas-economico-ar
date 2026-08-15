# Canonical Measurement Resolver v0.2

Phase 2 implements the measurement boundary frozen in `CONTRACT.md`.

The resolver is intentionally small and offline:

```text
registered Series
  + authenticated snapshot/provenance
  + SeriesBinding
  + CanonicalIndicator metadata
        ↓
resolved canonical measurement in memory
```

Authoritative inputs:

- `series/registry.json` — registered provider-native Series;
- `series/snapshots/*.csv` + provenance sidecars — authenticated observations;
- `figures/series_bindings.yaml` — operational Series → CanonicalIndicator normalization;
- vertical `canonical_indicators.yaml` files — canonical unit semantics and frequency.

The resolver performs only the two normalization primitives allowed by Figure Grammar v0.2:

- `identity`;
- `scale`.

It does not calculate YoY/MoM rates, rolling windows, annualization, cumulative values, rebasing, ratios, models, resampling, or aggregation. Those remain `DerivedIndicator` responsibilities.

It also does not write normalized datasets. Canonical values are produced in memory so the future materializer can consume them without creating another persisted copy of the observations.

## Current seed bindings

```text
IPC monthly        0.021... provider fraction  × 100   → percent_mom
ITCRM              provider index               identity → index
Goods trade balance USD millions                × 0.001 → usd_billions
```

## Inspect locally

From the repository root, with PyYAML installed:

```bash
python figures/measurement_resolver.py
python figures/measurement_resolver.py --tail 3
python figures/measurement_resolver.py --indicator ci.ns.cpi_monthly --json
```

The command is read-only and network-free. It verifies snapshot hashes and provenance before resolving values.

## Phase boundary

This phase produces **zero charts and zero PlotArtifacts**. Phase 3 may import this resolver and add the two frozen renderer primitives without changing the measurement semantics.
