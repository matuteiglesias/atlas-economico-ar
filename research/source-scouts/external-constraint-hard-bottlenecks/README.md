# External-constraint hard-bottleneck scout

Date: 2026-08-23

Scope: research only. No Series registration, SeriesBinding edit, DerivedIndicator change, capture, adapter, PlotArtifact, or publication change.

## Question

Can the two high-leverage missing measurements below be implemented faithfully from authoritative sources **without changing current Atlas semantics**?

- `ci.ef.nir_usd` — current frontier witness: 9 blocked PlotIntents.
- `ci.ef.public_fx_debt_service_12m` — current frontier witness: 5 blocked PlotIntents.

The answer for this pass is **no for both**. They should be dropped from the immediate acquisition queue rather than forced through weak mappings.

## 1. `ci.ef.nir_usd` — DROP / SEMANTIC_GAP

### Current Atlas demand

The CanonicalIndicator currently declares only:

- label: `Net international reserves`;
- unit: `usd_billions`;
- frequency: `monthly`.

It does not declare which NIR convention is authoritative.

That omission matters because current PlotIntents use the same indicator for materially different analytical purposes. Examples include:

- `pi.ef03` — **NIR versus program target path**;
- `pi.ef01` — **Gross reserves, NIR, and liquid buffers**;
- `pi.ef06` — **BCRA FX purchases versus NIR accumulation**;
- `pi.ef28` — **Debt service versus reserves**;
- `pi.ef42` — **BCRA FX purchases and reserve accumulation**.

The first use points toward the IMF-program definition. Several others read as an available/liquid-balance-sheet concept.

### Official-source finding

The BCRA itself states that there is **no single definition of RIN/NIR** and distinguishes at least:

1. the definition used to monitor the current IMF EFF program; and
2. the BCRA accounting / balance-sheet definition intended to reflect its usable foreign-currency position.

In the December 2025 IPOM technical note, the IMF-program definition is described as gross reserves less short-original-maturity BCRA foreign-currency liabilities plus Treasury liabilities arising from net IMF-program disbursements, with non-USD items valued at fixed program exchange rates. The BCRA accounting definition instead uses its own balance-sheet liabilities and current market valuation.

The same official table reports a large substantive divergence at 31-Dec-2025:

- BCRA-balance definition: about **+USD 2.9bn**;
- IMF-program definition: about **-USD 14.1bn**.

This is not a representation-normalization issue. Choosing one changes the economic meaning of several existing PlotIntents.

### Source / reproducibility assessment

Official BCRA material publishes the definitions and historical charts, and the BCRA `Principales Variables` surface exposes gross reserves as a series. This scout did **not** identify an equivalent stable provider-native machine-readable NIR Series whose semantics remove the definition choice.

A reconstruction from BCRA balance-sheet components may be possible, but that would introduce a new methodology and component-selection rule. It is therefore outside acquisition and cannot be hidden in a SeriesBinding.

### Decision

`DROP` from the immediate source-acquisition queue.

Classification: `SEMANTIC_GAP`.

Do not register a Series for `ci.ef.nir_usd` until the semantic layer explicitly chooses or separates the relevant NIR conventions. In particular, do not use an IMF-program measure as a generic usable-reserves measure, or vice versa.

## 2. `ci.ef.public_fx_debt_service_12m` — DROP / UNDECLARED_DERIVATION_AND_SCOPE_GAP

### Current Atlas demand

The CanonicalIndicator declares:

- label: `Public-sector FX debt service next 12 months`;
- unit: `usd_billions`;
- frequency: `monthly`.

It is consumed directly by maturity-profile and reserve-adequacy PlotIntents. The declared `di.ef.reserve_fx_service` uses it as an **input**; there is no current DerivedIndicator that constructs the next-12-month service measure from instrument-level debt records.

### Official-source finding

The Secretaría de Finanzas / Oficina Nacional de Crédito Público provides strong authoritative debt sources:

- monthly public-debt workbooks, currently through July 2026;
- quarterly downloadable Excel data and a SIGADE database archive;
- quarterly official maturity-profile reports.

The Q1-2026 report explicitly publishes static maturity profiles based on obligations contracted as of 31-Mar-2026, with capital and interest views and creditor categories. It also shows private-sector debt split between national and foreign currency.

Those are good source materials, but they are **not the current CanonicalIndicator directly**. The published report is principally `Deuda Bruta de la Administración Central`, uses annual maturity buckets in the presentation, and applies explicit coverage/exclusion rules. A rolling monthly "next 12 months public-sector FX debt service" measure would require methodological choices including at least:

- Administration Central versus a broader consolidated public-sector perimeter;
- what `FX` means (foreign-currency-denominated/payable debt, and treatment of dollar-linked peso debt);
- inclusion of capital, interest, or both;
- treatment of intra-public-sector obligations and the report's explicit exclusions;
- treatment of IMF/multilateral obligations;
- exchange-rate/valuation convention;
- rolling-window construction and revision policy.

These are not `identity`/`scale` normalization choices.

### Decision

`DROP` from the immediate source-acquisition queue.

Classification: `UNDECLARED_DERIVATION_AND_SCOPE_GAP`.

The official debt databases are promising raw ingredients, but the Atlas currently lacks the semantic/methodological declaration needed to turn them into `ci.ef.public_fx_debt_service_12m` reproducibly. Do not create an adapter or capture tranche for this indicator yet.

## Frontier consequence

The high frontier leverage of these two indicators is real, but it is **not currently actionable acquisition leverage**.

- NIR: 9 blocked PlotIntents remain blocked because one CanonicalIndicator currently spans incompatible official definitions.
- next-12m public FX debt service: 5 blocked PlotIntents remain blocked because the desired rolling measure is not available as a verified direct official series and the required construction is not declared.

No predicted `DATA_READY` delta is claimed from either candidate.

This is a useful pruning result: neither indicator should consume the next ingestion tranche.

## Recommended next action

Move on to a cleaner bottleneck with a likely exact official measurement, especially the BCRA REM / short-horizon inflation-expectations path. Revisit these two only after a semantic reassessment explicitly resolves the definitions/construction.

## Official sources inspected

- BCRA, *Informe de Política Monetaria — Diciembre de 2025*, technical section "Definiciones complementarias de RIN (BCRA y FMI)": https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/informes/informe-politica-monetaria-2025-T4.pdf
- BCRA, *Principales Variables*: https://www.bcra.gob.ar/principales-variables/
- Ministerio de Economía / Finanzas, *Datos mensuales de la deuda*: https://www.argentina.gob.ar/economia/finanzas/datos-mensuales-de-la-deuda
- Ministerio de Economía / Finanzas, monthly debt data: https://www.argentina.gob.ar/economia/finanzas/datos-mensuales
- Ministerio de Economía / Finanzas, *Datos trimestrales de la deuda*: https://www.argentina.gob.ar/economia/finanzas/datos-trimestrales-de-la-deuda
- Secretaría de Finanzas / ONCP, *Deuda de la Administración Central — I Trimestre 2026*: https://www.argentina.gob.ar/sites/default/files/presentacion_grafica_it_26_c.pdf
