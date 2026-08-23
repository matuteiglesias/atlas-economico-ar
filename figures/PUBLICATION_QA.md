# Human publication QA

This layer is deliberately editorial and small. It does **not** add ontology nodes, mutate PlotIntent identity, or decide whether a measurement exists. It answers a later question:

> A PlotArtifact can be technically valid and reproducible; should it be promoted as an analytical figure?

`figures/publication_qa.yaml` is an exception policy over materialized PlotIntents. The default is `publish`; only reviewed exceptions are recorded.

## Statuses

- `publish` — normal publication behavior.
- `historical` — valid evidence, but explicitly historical rather than current-state evidence.
- `quarantine` — keep the PlotIntent, measurement lineage, PlotArtifact and direct chart URL, but exclude the figure from featured chart grids until the editorial problem is resolved.

Quarantine is therefore **not deletion** and is not a data-quality failure. It is a publication decision.

## Curation ledger and review packs

`figures/curation_reviews.yaml` is the review ledger; it does not replace the publication policy. It records terminal/workflow curation state, hazard evidence, preferred PlotIntent when superseded, and a structural fingerprint that changes when renderer/frame/indicator/source structure changes but remains stable across ordinary data refreshes.

Run `make validate-figure-curation` to validate the ledger and pinned structural identities. Run `make figure-qa-pack` to emit the next deterministic review queue (at most six figures) into `/tmp/atlas-figure-qa-pack`. The pack copies the actual PNG/SVG files, records their current SHA-256 hashes and semantic context, and is deliberately refused if the output path is inside the repository.

The six pre-existing publication exceptions are migrated into the ledger without changing their public behavior. Legacy decisions predate rendered SHA-256 review evidence; new terminal decisions made through the curation loop must record both PNG and SVG hashes separately from the structural fingerprint.

## First-pass human test

For each figure, ask in order:

1. What can the eye actually recover from the plot?
2. What economic question can the figure answer in one sentence?
3. Is the measurement/transformation appropriate (nominal vs real, stock vs change, daily vs monthly, cumulative vs flow, level vs growth)?
4. Does the graphical encoding help answer that question?
5. Would this figure be acceptable in an economic report without a verbal apology?

The QA layer should remain separate from typography, color and spacing work.

## Decisions in pass 1

Historical:

- `pi.ns31` policy rate vs BAIBAR — the policy-rate input ends on 2025-07-10.
- `pi.ns63` BCRA policy-rate history — valid history, not current policy evidence.

Quarantined:

- `pi.ns64` nominal bank reserve balances — long-run nominal ARS levels are weak analytical evidence in a high-inflation period.
- `pi.ns58` nominal monetary base vs transactional M2 — the common-base real-index figure (`pi.ns41`) is analytically stronger.
- `pi.ns59` daily FX purchases vs monetary-base stock — flow/stock mismatch.
- `pi.ef49` daily FX purchases vs gross-reserve stock — flow/stock mismatch.

Bounded fixes:

- `pi.ns01` inflation momentum moves from five years to `rf.last_18m`. The first visual-QA candidate used `rf.since_dec_2023`, but the 2024 annualized spike still compressed the 2025–26 variation; the final 18-month frame matches the current-momentum question better.
- `pi.ns63` uses step geometry because the policy-rate series is a policy setting process, not a continuously interpolated signal.
- BCRA variable 78 receives a regression test proving that source signs are preserved: its official methodology covers both sales and purchases and the historical snapshot contains both negative and positive observations.

## Deliberately unresolved after pass 1

These require another economic/editorial decision rather than an automatic fix:

- BAIBAR: choose between a current-liquidity frame and a stress-history frame.
- Foreign-currency deposits: investigate the late-2024 break before annotating it as an economic event.
- Gross reserves: identify and verify the economic events behind major discontinuities before annotating them.
- Inflation vs FX depreciation: decide between common-axis changes, aligned panels, cumulative movements, or a pass-through diagnostic.
- Purchases vs official FX: reconsider line geometry and possibly weekly aggregation.
- Monetization dashboard: retain as a curated synthesis figure rather than treating complex dashboards as a default primitive.

The rule remains: fix or quarantine weak publication objects; do not delete useful measurements merely because one rendering is weak.
