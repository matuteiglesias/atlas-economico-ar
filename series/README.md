# Authentic Series Capture v0.1

This directory is the narrow network boundary for the first three real Atlas
Series. It deliberately does **not** render plots and is not imported by the
knowledge compiler or the web build.

## Milestone freeze

Exactly three Datos Argentina Series are registered:

- `145.3_INGNACUAL_DICI_M_38` → `ci.ns.cpi_monthly`
- `116.3_TCRMA_0_M_36` → `ci.ns.reer_index`
- `74.3_ISC_0_M_19` → `ci.ef.goods_balance_usd`

`CanonicalIndicator != Series`: the provider IDs remain technical source
implementations. No economic transformations are applied during capture.

## Local capture

From the repository root:

```bash
make test-series
make capture-seed-series
make validate-series
```

`capture-seed-series` is intentionally networked. It calls only the official
Datos Argentina `/series` endpoint, requesting provider values as CSV with
native IDs and full provider metadata separately.

A successful capture writes:

```text
series/
  raw/datos_argentina/
    <series>.csv
    <series>.metadata.json
  snapshots/
    <series>.csv
    <series>.provenance.json
```

The raw responses are preserved byte-for-byte (apart from deterministic
reassembly if the values endpoint requires pagination). The normalized snapshot
contains only `date`, `value`, the Atlas technical `series_id`, and the native
`provider_series_id`. No percent changes, rebasing, unit conversion, collapsing,
or other economic transformation is performed.

Each provenance sidecar stores request URLs, retrieval time, SHA-256 hashes,
provider metadata, first/latest observations, and a freshness assessment.
Freshness is a warning rather than an integrity failure because publication
lags differ across official series.

## Troubleshooting locally

First test the provider outside Python:

```bash
curl -v --connect-timeout 20 \
  'https://apis.datos.gob.ar/series/api/series?ids=145.3_INGNACUAL_DICI_M_38&format=csv&header=ids&sort=desc&limit=3'
```

Then inspect proxy variables if a tunnel error appears:

```bash
env | grep -iE 'https?_proxy|no_proxy'
```

A response such as `Tunnel connection failed: 403 Forbidden` before an HTTP
response from `apis.datos.gob.ar` usually points to the execution environment or
proxy, not to the Atlas parser. A normal provider response should begin with a
CSV header containing `indice_tiempo` and the requested series ID.

To isolate one registered Series:

```bash
python series/capture.py --only 145.3_INGNACUAL_DICI_M_38
python series/validate.py
```

Note that `validate.py` validates the full three-Series milestone, so after a
single-Series troubleshooting run it expects the other two previously captured
snapshots to exist.

## GitHub Actions

`.github/workflows/capture-seed-series.yml` is manual-only
(`workflow_dispatch`). It performs the same capture and validation on a GitHub
hosted runner and uploads `series/raw/` + `series/snapshots/` as a workflow
artifact. It does not commit or publish the data automatically.

After the workflow is merged to the default branch, use **Actions → Capture
seed economic series → Run workflow**. Download the resulting
`authentic-seed-series` artifact, inspect it, and only then commit approved
snapshots.

## Acceptance gate

Before these snapshots are used by the figure pipeline, a human should verify:

1. provider IDs and source descriptions are the intended economic series;
2. first/latest dates and observation counts are plausible;
3. latest values agree with the official source/release when spot-checked;
4. freshness warnings are understood;
5. `make validate-series` passes from a clean checkout.

No chart support belongs in this milestone.
