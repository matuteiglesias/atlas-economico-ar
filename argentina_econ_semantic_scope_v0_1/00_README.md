# Argentina Economic Knowledge Layer — Semantic Scope Freeze v0.1

Status: **SCOPE FROZEN FOR VERTICAL CONSTRUCTION**

Purpose: provide the shared semantic reference that all later slice-by-slice vertical builds must obey.

This bundle does **not** contain the final instances of Concepts, Relations, QuestionIntents,
CanonicalIndicators, Series, DerivedIndicators, PlotIntents, or ChartSpecs. It defines the
bounded regions, cross-region interfaces, allowed ontology classes, epistemic rules, source roles,
and construction sequence that will be used to create those instances.

## Semantic regions

1. `nominal_stabilization`
2. `external_financial_constraint`
3. `real_economy`
4. `labor_incomes`
5. `household_welfare`
6. `fiscal_regime`

Global overlay:

7. `structural_transformation` — cross-cutting, not a seventh independent vertical.

## Core architectural rule

Earlier classes constrain later classes.

`evidence → concepts → relations → questions → indicators → series → derived indicators → plot intents → chart specs`

AI must not generate all classes independently.

## Source roles

- **Media sensing**: public agenda, recurring questions, vocabulary, attention bridges.
- **Expert/official reports (starting with IMF 2026 Article IV)**: mechanisms, decompositions,
  trade-offs, structural relations, methodological frames, candidate measurements.
- **Official statistical/administrative sources**: measurement truth and technical series.
- **Human curation**: canonicalization, epistemic typing, approval, merge/reject decisions.

## Freeze rule

Changes to slice boundaries, global class definitions, relation-type vocabulary, or source/epistemic
policy require an explicit version bump. Later verticals may add instances, but must not silently
change this scope contract.
