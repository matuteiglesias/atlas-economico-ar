# Nominal Stabilization Vertical v0.1 — Build Method

This vertical implements the shared sequence:

1. **Evidence packet**
   - Media subset: inflation, FX, rates, and reserves lanes from the 500-headline corpus.
   - Expert source: IMF 2026 Article IV / EFF review, especially monetary/FX policy passages and Figures 1 and 4.
   - Model prior: used only to normalize standard economic language, propose missing analytical objects, and structure candidate transformations. It does not override source provenance.

2. **Concepts**
   - Create the bounded vocabulary required to reason about nominal stabilization.
   - API series names are not concepts.
   - Cross-slice objects are declared as boundary ports rather than allowing scope creep.

3. **Relations**
   - Every edge is typed.
   - `agenda_related` is never treated as causal.
   - `economic_mechanism` is a theory/policy-transmission relation, not proof of causal effect.

4. **QuestionIntents**
   - Questions are generated from evidence + concepts + relations.
   - Questions define explanatory demand and later constrain measurement.

5. **ReferenceFrames**
   - Standardize comparisons such as previous period, Dec-2023, Apr-2025 FX framework, and Jan-2026 purchase program.

6. **CanonicalIndicators**
   - Define stable measurement needs.
   - Technical series registration is **omitted by design** in this version.
   - Every indicator has `series_binding_status: DEFERRED_ASSUMED_AVAILABLE`.

7. **DerivedIndicators**
   - Only explicit transformations needed by approved questions.
   - Formula/methodology is written down now; technical series inputs bind later.

8. **PlotIntents**
   - Every plot answers at least one QuestionIntent.
   - PlotIntent is the durable intellectual visual object.

9. **ChartSpecs**
   - Only a selected subset of PlotIntents receives a spec in v0.1.
   - Specs are executable in structure but bind to CanonicalIndicators rather than technical Series IDs.

10. **Validation**
    - Duplicate IDs.
    - Unknown references.
    - Orphan concepts.
    - Questions without plots.
    - PlotIntents without indicators.
    - Derived outputs/inputs unknown to indicator registry.
    - ChartSpecs pointing to unknown plots/indicators.
    - Explicitly deferred series-binding count.

## Status

`vertical_complete_candidate`: semantically populated and machine-validated, but still awaiting human canonicalization/review.
