# Real Economy Vertical v0.1

Status: **semantically commissioned; public activation intentionally OFF**.

This bundle turns the frozen `real_economy` slice into the Atlas's third semantic vertical without registering new Series, materializing new figures, or making public promises. It follows the repository-wide sequence:

`evidence → concepts → typed relations → questions → reference frames → canonical indicators → declared derivations → plot intents → selected semantic ChartSpecs`

## Analytical spine

1. breadth of the recovery across sectors;
2. sources of GDP growth and domestic demand;
3. investment and productive capacity;
4. private consumption and import intensity;
5. manufacturing/construction versus primary-sector divergence;
6. financial conditions as a boundary-port input to real activity;
7. productive capacity as a boundary port to exports/external constraint.

The vertical is deliberately compact. It does not duplicate labor-market, poverty, reserve, fiscal-institution, or inflation semantics owned by neighboring regions.

## Publication state

`argentina_econ_semantic_scope_v0_1/slices/real_economy.yaml` remains `populated: false`.

The ordinary publication build loads this bundle, but the region activation firewall must keep every Real Economy Topic, Question, Indicator, and Chart child non-addressable and non-discoverable until a later activation review. Semantic graph presence is not public readiness.

## Measurement state

Technical Series binding is deferred. `growth/frontier.py` can now calculate the exact official-data frontier for this vertical. The next source-scouting job should search official INDEC / national Series de Tiempo / MECON sources against these declared CanonicalIndicators rather than growing semantics from whatever an API happens to expose.

See `docs/ACTIVATION_RUNWAY.md` for the smallest plausible public opening and `docs/OPEN_DECISIONS.md` for methodological gates intentionally left unresolved.
