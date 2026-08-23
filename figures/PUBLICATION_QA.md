# Human publication QA

This layer is deliberately editorial and small. It does **not** add ontology nodes, mutate PlotIntent identity, or decide whether a measurement exists. It answers a later question:

> A PlotArtifact can be technically valid and reproducible; should it be promoted as analytical evidence?

## Current authority

`figures/curation_reviews.yaml` is the authoritative review ledger for explicit figure decisions. Terminal curation states are `APPROVED`, `REFERENCE`, `HISTORICAL`, `SUPERSEDED`, and `QUARANTINE`.

`figures/publication_qa.yaml` is now a **legacy compatibility policy** containing the six publication decisions that predated the curation ledger. Do not extend it as a parallel review system. The existing curation validator requires those legacy exceptions to remain represented in the ledger.

`publication/figure_disposition.py` projects review truth once into consumer capabilities:

- `addressable` — a direct materialized chart remains reachable;
- `prominent` — suitable for ordinary featured/list prominence;
- `primaryEvidence` — eligible to promote a QuestionIntent to a public question route;
- `canonicalPlotIntentId` — replacement when a figure is superseded.

During migration, an unreviewed PlotArtifact retains the historical default-publish behavior. Once a terminal curation decision exists, that decision is authoritative. The frontend and question-publication contract consume the compiled disposition; they do not reinterpret curation states themselves.

Quarantine, reference, historical, and superseded are therefore **not deletion** and are not data-quality failures. They are publication dispositions over preserved semantic and materialized evidence.

## Curation ledger and review packs

The ledger records terminal/workflow curation state, hazard evidence, preferred PlotIntent when superseded, and a structural fingerprint that changes when renderer/frame/indicator/source structure changes but remains stable across ordinary data refreshes.

Run `make validate-figure-curation` to validate the ledger and pinned structural identities. Run `make figure-qa-pack` to emit the next deterministic review queue (at most six figures) into `/tmp/atlas-figure-qa-pack`. The pack copies the actual PNG/SVG files, records their current SHA-256 hashes and semantic context, and is deliberately refused if the output path is inside the repository.

The six pre-existing publication exceptions are migrated into the ledger without changing their historical review meaning. Legacy decisions predate rendered SHA-256 review evidence; new terminal decisions made through the curation loop must record both PNG and SVG hashes separately from the structural fingerprint.

## Human test

For each figure, ask in order:

1. What can the eye actually recover from the plot?
2. What economic question can the figure answer in one sentence?
3. Is the measurement/transformation appropriate (nominal vs real, stock vs change, daily vs monthly, cumulative vs flow, level vs growth)?
4. Does the graphical encoding help answer that question?
5. Would this figure be acceptable in an economic report without a verbal apology?

The QA layer should remain separate from typography, color and spacing work.

## Legacy pass-1 decisions

Historical:

- `pi.ns31` policy rate vs BAIBAR — the policy-rate input ends on 2025-07-10.
- `pi.ns63` BCRA policy-rate history — valid history, not current policy evidence.

Quarantined/superseded at migration:

- `pi.ns64` nominal bank reserve balances — long-run nominal ARS levels are weak analytical evidence in a high-inflation period.
- `pi.ns58` nominal monetary base vs transactional M2 — the common-base real-index figure (`pi.ns41`) is analytically stronger.
- `pi.ns59` daily FX purchases vs monetary-base stock — flow/stock mismatch.
- `pi.ef49` daily FX purchases vs gross-reserve stock — flow/stock mismatch.

Bounded fixes from that pass included the shorter inflation-momentum frame, step geometry for policy-rate history, and a sign-preservation regression test for BCRA variable 78.

## Deliberately unresolved after pass 1

These still require economic/editorial judgment rather than automatic fixes:

- BAIBAR: choose between a current-liquidity frame and a stress-history frame.
- Foreign-currency deposits: investigate the late-2024 break before annotating it as an economic event.
- Gross reserves: identify and verify the economic events behind major discontinuities before annotating them.
- Inflation vs FX depreciation: decide between common-axis changes, aligned panels, cumulative movements, or a pass-through diagnostic.
- Purchases vs official FX: reconsider line geometry and possibly weekly aggregation.
- Monetization dashboard: retain as a curated synthesis figure rather than treating complex dashboards as a default primitive.

The rule remains: fix or quarantine weak publication objects; do not delete useful measurements merely because one rendering is weak.
