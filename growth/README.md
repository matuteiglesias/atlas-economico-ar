# Atlas measurement frontier

`growth/frontier.py` extracts one provider-neutral calculation from the successful BCRA tranche-3 scout:

```text
registered + bound Series
        ↓
direct CanonicalIndicator availability
        ↓
already-declared DerivedIndicator closure
        ↓
existing PlotIntent demand
        ↓
DATA_READY / MISSING_1 / MISSING_2 / MISSING_3_PLUS
```

The semantic layer remains upstream and producer-owned. This module does **not** decide what the Atlas should want, discover provider catalogs, infer new transformations, rank source candidates, or change publication behavior.

## Inputs

The calculation is fully offline and reads repository truth only:

- `series/*registry.json` plus `figures/series_bindings.yaml` for direct measurements;
- `verticals/*/knowledge/derived_indicators*.yaml` for declared transformations;
- `verticals/*/knowledge/plot_intents*.yaml` for analytical demand;
- `plot-artifacts/manifest.json` and existing figure disposition contracts only for optional materialization/publication annotations.

A direct indicator is available only when its Series is both registered and bound. Derived availability is a fixed-point closure over declared `input_indicator_ids`; no methodology is inferred from prose or from source labels.

## Evidence packet

Run:

```bash
python scripts/build-growth-frontier.py
```

This writes:

- `growth/frontier.json` — authoritative machine-readable frontier;
- `growth/frontier.md` — deterministic human-readable census.

For scratch or CI evidence without changing the working tree, pass `--output-dir /tmp/atlas-growth-frontier`.

Source-specific scouts should consume this frontier and add their own catalog availability, source quality, freshness, semantic-match confidence, and redundancy policy downstream.
