# BCRA second six-Series population batch

This batch completes the original twelve-Series BCRA tranche with provider IDs
`19`, `27`, `28`, `44`, `108`, and `160`.

The capture layer remains unchanged: catalog, optional methodology and every
paginated values response are preserved byte-for-byte; deterministic snapshots
contain provider-native values and `economic_transform` remains `none`.

Special cases:

- BCRA `27` is an authenticated **alternate** for `ci.ns.cpi_monthly`; Datos
  Argentina remains the publication primary.
- BCRA `160` is intentionally retained as stale historical evidence. Its
  PlotSpecs use a fixed window ending at the provider's July-2025 endpoint.
- Economic transformations newly executable from existing semantics (3-month
  annualized CPI, inflation acceleration, TAMAR ex-post real rate) live only in
  `figures/derived_resolver.py`.

The batch does not add a renderer primitive, runtime API, database, CMS or
frontend chart library.
