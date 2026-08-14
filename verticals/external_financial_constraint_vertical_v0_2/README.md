# External & Financial Constraint vertical v0.2

Second populated vertical for the Argentina Economic Atlas.

It is a deliberate stress test of the architecture because it is coherent on its own while creating natural ports into
Nominal Stabilization: BCRA FX purchases, the real exchange rate, resident hedging, policy credibility, and sovereign spreads.

## Counts
- Concepts: 30
- Relations: 44
- QuestionIntents: 20
- Vertical-specific ReferenceFrames: 7
- CanonicalIndicators: 40
- DerivedIndicators: 5
- PlotIntents: 44
- ChartSpecs: 28

Series registration remains intentionally deferred.

## Improvements over the first vertical
1. Cross-slice ports are explicit and sparse instead of duplicating Nominal concepts.
2. Shared reference-frame IDs are referenced but not duplicated.
3. Question pages receive substantially richer editorial copy through a separate overlay.
4. Editorial language is separated from semantic IDs and methodologies.
5. A Spanish localization skeleton is keyed by stable IDs and intentionally leaves slugs untouched.
6. Co-movement plots explicitly preserve interpretation limits.
7. The bundle is validated for co-compilation with Nominal Stabilization v0.1.
