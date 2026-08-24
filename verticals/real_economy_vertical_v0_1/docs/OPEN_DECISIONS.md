# Real Economy v0.1 — Open decisions

These are explicit gates, not omissions to be filled opportunistically.

## 1. GDP growth contributions

The IMF Figure 3 contribution panel is analytically valuable, but a publication-grade decomposition requires verified national-accounts semantics: chain/constant-price basis, seasonal adjustment, imports' sign convention, inventories/statistical discrepancy, and additive compatibility. v0.1 therefore defines component levels and growth questions but **does not invent a contribution DerivedIndicator**.

## 2. Sector aggregation

The public story may benefit from a compact "labor-intensive vs primary/tradable sectors" comparison. v0.1 keeps the underlying sector measures separate. Any composite weighting rule requires an explicit methodology decision.

## 3. Productive-capacity measurement

`re.productive_capacity` is a mechanism/interpretive concept. v0.1 does not create a synthetic capacity index. Investment composition, sectoral output, and export volumes are safer first measurements.

## 4. Financial-conditions transmission

Real private-credit growth and ex-post real TAMAR already exist in neighboring verticals and can be reused as context. Simple co-movement must remain descriptive; causal claims require evidence beyond the Atlas chart layer.

## 5. Official transport

The repository already has a Datos Argentina Series API capture boundary. Source scouting should first test whether current Real Economy measurements can reuse that transport. A new INDEC/MECON adapter is justified only if a high-value official measurement cannot be captured faithfully through the national API.
