# Atlas contract authority map

This file identifies the live contract boundaries for `atlas-economico-ar`. It exists to prevent agents and downstream consumers from treating frozen implementation bundles or compatibility files as current semantic authority.

## Live runtime authority

Read these layers in dependency order:

1. **Semantic identity and relations** — `argentina_econ_semantic_scope_v0_1/` plus each active vertical under `verticals/` own Concept, QuestionIntent, CanonicalIndicator, Relation and PlotIntent meaning.
2. **Observed technical series** — `series/` owns provider-native Series registration, snapshots, hashes and acquisition provenance. `CanonicalIndicator != Series` remains a hard boundary.
3. **Figure grammar and materialization** — `figures/CONTRACT.md`, `figures/PRESENTATION_VARIANTS.md`, active `figures/specs/`, bindings/resolvers and `plot-artifacts/manifest.json` own the executable figure seam from PlotIntent to PlotArtifact. Canonical `outputs` are self-describing review evidence; derived `embed_outputs` are the page-owned presentation projection and must not replace curation evidence.
4. **Human figure review truth** — `figures/curation_reviews.yaml` is authoritative for explicit terminal curation decisions. `figures/publication_qa.yaml` is a legacy compatibility policy for the six decisions that predated the curation ledger; it must not be independently extended as a second review system.
5. **Plot publication disposition** — `publication/figure_disposition.py` is the single projection from review truth to consumer capabilities (`addressable`, `prominent`, `primaryEvidence`, canonical replacement). Unreviewed plots retain legacy publish behavior during migration.
6. **Question publication boundary** — `publication/question_publication.py` decides whether semantic QuestionIntents earn public routes after materialized plot dispositions are attached. It consumes `primaryEvidence`; it does not reinterpret figure-review states.
7. **Knowledge compiler** — `econ_knowledge_compiler_v0_1/` compiles semantic structures into page-shaped read models. It does not fetch economics, infer publication QA, or render charts.
8. **Canonical compiled publication** — `site-data/` is generated output from the current compiler/publication pipeline, not an independent source of semantic truth.
9. **Frontend** — `web/` is a thin consumer of compiled read models. It must use compiled publication capabilities and the compiler-selected embed presentation rather than recreating curation, question-publication, or figure-presentation rules.
10. **Browser/UX tests** — Playwright and other experience tests assert user-visible invariants produced by the contracts above. They must not define economic or publication semantics themselves.

## Frozen/reference bundles

The following remain useful archaeology or implementation references but are not current runtime authority when they conflict with the layers above:

- `econ_atlas_frontend_contract_v0_1/` — original pre-Next.js frontend freeze;
- `econ_atlas_codex_dev_bundle_v0_1/` — historical implementation packet and fixture counts;
- `econ_knowledge_compiler_v0_1/example-output/` — compiler examples, not current publication output;
- legacy candidate ChartSpecs registered by `figures/legacy_inventory.yaml` — design inventory only.

Do not update live behavior merely to make these frozen bundles uniform with the current system.

## Cross-repository boundary

Atlas economic domain schemas remain producer-owned here. `kb-contracts` may govern shared artifact identity, integrity, provenance and verifiable producer-schema declarations, but it does not own Atlas economic semantics or a universal execution/publication architecture.

Extract a shared schema only when another real producer/consumer demonstrates an interoperability need. Until then, keep this publication kernel small and Atlas-local.
