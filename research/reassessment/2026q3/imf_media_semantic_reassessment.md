# IMF + media semantic reassessment — 2026 Q3

## Executive conclusion

This reassessment does **not** justify a large semantic expansion. The current three-region Atlas already contains most of the right analytical questions. The highest-return next moves are measurement completion, a few explicit cross-region bridges using the existing relation vocabulary, and compact interpretation cues that prevent predictable misreadings.

The main product conclusions are:

1. **Real Economy has the right opening shape but no public-evidence basis yet.** Its best future spine is `q.re01` (breadth/concentration), `q.re03` (growth drivers), and `q.re05` with `q.re06` as the investment/capacity drilldown.
2. **The public reserve question is semantically ahead of its evidence.** `q.ef01` asks for gross reserves, NIR and liquid-buffer distinctions, but its primary materialized evidence is currently the gross-reserve figure `pi.ef46`.
3. **Credit growth needs level and quality context.** Rapid growth from a very shallow base and rising NPLs are not contradictory. The Atlas already has `q.ef14`, `q.ef15`, and `q.ef17`; this needs measurement/cues, not another question.
4. **Three low-cost semantic bridges are worth considering:** `ef.private_credit -> associated_with -> re.financial_conditions`; `ns.real_interest_rate -> associated_with -> re.financial_conditions`; and, more cautiously, `re.imports_volume -> associated_with -> ef.goods_trade_balance`.
5. **Do not create new questions** for reserves-versus-risk, BCRA purchases-versus-external position, real appreciation-versus-external balance, or primary-sector-led recovery. Those analytical ideas are already represented.

Real Economy is present on the base commit and remains inactive, as intended. No semantic object, publication state, activation flag, SeriesBinding, figure, route, or frontend surface is changed by this packet.

## Inputs and reproducibility

External research inputs used:

- IMF: `1934-7685-002.2026.issue-105-en(3).pdf`
  - SHA256: `5824a253c59aeb413070f0d56cfbafa7f750f26c476636024fdc46964ebac85e`
  - bytes: 4,977,422
- Media corpus: `econ_headlines_500(3).csv`
  - SHA256: `01bd5340c4d96cc0cdb71f614f042384c7f9085d62e6aee456568c66dceabec9`
  - bytes: 173,467
- Repository base: `974ae9f5f56ab1595690e5b5e333dee285f435b3`

The original PDF and CSV are not committed.

Source-role boundary used throughout:

- media = attention, vocabulary, timing, recurring confusion;
- IMF = mechanisms, decompositions, trade-offs, interpretation limits, expert framing and candidate measurement ideas;
- official Atlas measurements = measurement truth.

IMF voice is distinguished where material as `IMF_STAFF`, `AUTHORITIES`, `BOARD`, `NATIONAL_DATA`, or `PROGRAM_PROJECTION`.

## Current semantic/publication state

| Region | Concepts | Relations | Questions | Canonical indicators | Derived | PlotIntents | Activation |
|---|---:|---:|---:|---:|---:|---:|---|
| Nominal Stabilization | 25 | 52 | 18 | 42 | 12 | 52 | active |
| External & Financial Constraint | 30 | 44 | 20 | 40 | 5 | 44 | active |
| Real Economy | 18 | 28 | 12 | 23 | 9 | 24 | **inactive** |

Compiler/publication census on the base:

- 6 semantic regions;
- 73 topics;
- 50 QuestionIntents;
- 113 indicators;
- 143 semantic charts;
- 41 materialized PlotArtifacts;
- 15 PUBLIC questions and 35 HOLD questions;
- 22 prominent / primary-evidence PlotArtifacts;
- all 12 Real Economy questions and all 24 Real Economy charts are activation-blocked.

The full per-question reconstruction was performed from each vertical's authoritative `question_intents.yaml`, its linked semantic files, and `site-data/question-publication.json`. This packet deliberately does not mirror complete Concept/Relation/Indicator arrays into a second authority. The structured JSON records compact per-question state and points back to the authoritative semantic files.

There is no committed `growth/frontier.json` on this base; the provider-neutral `growth/frontier.py` kernel is present.

## IMF analytical bridge inventory

The useful IMF signal is how several measurements are joined into an argument, not isolated claims.

### IMF01 — aggregate recovery versus sector composition

- Locator: Recent Developments ¶5, PDF p.10; Figure 3, PDF p.49.
- Voice: `IMF_STAFF` / national-data-based staff analysis.
- Role: `TENSION`.
- Bridge: aggregate GDP/activity recovery can coexist with weak labor-intensive construction and manufacturing while agriculture, mining and energy lead.
- Atlas: `q.re01`, `q.re02`, `q.re07`, `q.re08`.
- Assessment: **ALREADY_EXPLICIT** semantically; missing measurement/materialization, not a new question.

### IMF02 — inflation slowdown versus composition

- Locator: Recent Developments ¶6, PDF pp.10–11; Figure 4, PDF p.50.
- Voice: `IMF_STAFF`.
- Role: `DECOMPOSITION` / `INTERPRETATION_LIMIT`.
- Bridge: headline inflation can move differently from core/trimmed measures because relative-price corrections, food, regulated prices, inertia and FX pass-through contribute differently.
- Atlas: `q.ns01`–`q.ns05`.
- Assessment: **ALREADY_EXPLICIT**.

### IMF03 — backward-looking indexation during disinflation

- Locator: Recent Developments ¶7 footnote 4, PDF p.11.
- Voice: `IMF_STAFF`.
- Role: `INTERPRETATION_LIMIT`.
- Bridge: falling inflation can temporarily raise real indexed expenditure because nominal adjustments lag.
- Atlas: future Fiscal/Labor boundary, not a three-region expansion target.
- Assessment: **HUMAN_GATE** outside current regional scope.

### IMF04 — FX purchases and real appreciation can coexist

- Locator: Recent Developments ¶9, PDF p.12; Figure 6, PDF p.52.
- Voice: `IMF_STAFF` / `NATIONAL_DATA`.
- Role: `TENSION`.
- Bridge: the peso appreciated in real terms while the BCRA was purchasing FX and rebuilding reserves.
- Atlas: `q.ns10`, `q.ns11`, `q.ef19`, `q.ef20`.
- Assessment: **ALREADY_EXPLICIT**; cue candidate, not new semantics.

### IMF05 — strong exports do not guarantee a stronger current account

- Locator: Recent Developments ¶10, PDF pp.12–13; Figure 6, PDF p.52.
- Voice: `IMF_STAFF` / `NATIONAL_DATA`.
- Role: `DECOMPOSITION`.
- Bridge: energy/agriculture exports strengthened while imports and services outflows could offset the goods improvement.
- Atlas: `q.ef04`, `q.ef05`, `q.re09`, `q.re10`.
- Assessment: **RELATION_GAP** at the Real↔External boundary, not a question gap.

### IMF06 — gross purchases are not NIR accumulation

- Locator: Recent Developments ¶10–11, PDF p.13; Box 7, PDF p.44; Figure 6, PDF p.52.
- Voice: `IMF_STAFF`.
- Role: `INTERPRETATION_LIMIT`.
- Bridge: FX purchases, gross reserves, NIR, liquid buffers, swaps/repos and debt service are distinct stocks/flows.
- Atlas: `q.ef01`, `q.ef02`, `q.ef03`, `q.ef20`.
- Assessment: **MEASUREMENT_GAP** for NIR/liquid-buffer evidence; cue candidate.

### IMF07 — incipient improvement versus external vulnerability

- Locator: Recent Developments ¶11, PDF p.13; Staff Appraisal ¶47, PDF p.35.
- Voice: `IMF_STAFF`.
- Role: `TENSION`.
- Bridge: recent reserve/market improvement can coexist with weak reserve coverage, large FX obligations and incomplete market access.
- Atlas: `q.ef01`, `q.ef08`, `q.ef09`, `q.ef10`, `q.ef13`.
- Assessment: **ALREADY_EXPLICIT**.

### IMF08 — rapid credit growth versus rising credit risk

- Locator: Recent Developments ¶12, PDF pp.13–14; Figure 7, PDF p.53.
- Voice: `IMF_STAFF` / `NATIONAL_DATA`.
- Role: `TENSION`.
- Bridge: real private credit can grow rapidly from a low base while consumer NPLs rise and credit conditions remain tight.
- Atlas: `q.ef14`, `q.ef15`, `q.re11`.
- Assessment: **MEASUREMENT_GAP** for credit-quality evidence; cue candidate.

### IMF09 — resident dollarization is not always an external outflow

- Locator: Recent Developments ¶12 and footnote 11, PDF p.14.
- Voice: `IMF_STAFF`.
- Role: `INTERPRETATION_LIMIT`.
- Bridge: household FX purchases may remain inside the domestic banking system, supporting FX deposits and lending, rather than mechanically leaving the system.
- Atlas: `q.ef07`, `q.ef16`.
- Assessment: **CUE_CANDIDATE**.

### IMF10 — investment announcements versus realized productive capacity

- Locator: Recent Developments ¶13, PDF p.14; Structural Policies ¶34, PDF pp.28–29.
- Voice: `IMF_STAFF` / `AUTHORITIES` where views differ.
- Role: `INTERPRETATION_LIMIT`.
- Bridge: approved/announced strategic investments are not the same as realized fixed investment or productive capacity.
- Atlas: `q.re05`, `q.re06`, `q.re10`.
- Assessment: **MEASUREMENT_GAP** for investment composition.

### IMF11 — baseline growth/export assumptions are projections

- Locator: Outlook and Risks / program baseline, PDF pp.15–18 and later tables.
- Voice: `PROGRAM_PROJECTION`.
- Role: `INTERPRETATION_LIMIT`.
- Bridge: projected growth, FDI and export expansion should frame questions but must not become measurement truth.
- Atlas: all regions.
- Assessment: **NO_ACTION** beyond provenance discipline.

### IMF12 — energy shock: inflation cost versus external benefit

- Locator: Box 3, PDF p.40.
- Voice: `IMF_STAFF` scenario analysis.
- Role: `TRADE_OFF`.
- Bridge: higher global energy prices can raise inflation and subsidies while improving terms of trade and hydrocarbon exports.
- Atlas: Nominal↔External now; Fiscal later.
- Assessment: **HUMAN_GATE** for event-sensitive cue design, not a permanent semantic object.

### IMF13 — reserve accumulation, remonetization and disinflation are jointly constrained

- Locator: Monetary/FX ¶26–28, PDF pp.23–25.
- Voice: `IMF_STAFF` / program understanding.
- Role: `TRADE_OFF`.
- Bridge: reserve purchases can be absorbed more easily as money demand recovers; weak money demand changes sterilization and inflation risk.
- Atlas: `q.ns11`, `q.ns15`, `q.ns16`, `q.ef20`.
- Assessment: **ALREADY_EXPLICIT**.

### IMF14 — reserves and sovereign spreads share common drivers

- Locator: Authorities' Views ¶29, PDF p.26.
- Voice: `AUTHORITIES`.
- Role: `INTERPRETATION_LIMIT`.
- Bridge: authorities explicitly caution against reading a one-way causal effect from reserve levels to sovereign risk.
- Atlas: `q.ef09`.
- Assessment: **CUE_CANDIDATE**; preserve source voice.

### IMF15 — lower policy/market rates do not imply easy credit

- Locator: Monetary/FX ¶27, PDF p.24; Financial Sector ¶30, PDF p.26; Figure 7, PDF p.53.
- Voice: `IMF_STAFF`.
- Role: `INTERPRETATION_LIMIT`.
- Bridge: rates can fall while consumer borrowing remains expensive and bank credit allocation stays constrained by risk/NPLs.
- Atlas: `q.ns12`, `q.ef15`, `q.re11`.
- Assessment: **CUE_CANDIDATE** and cross-region relation opportunity.

### IMF16 — market access is a financing-quality question, not just spread level

- Locator: Financing Policy ¶24–25, PDF pp.22–23; Exceptional Access, PDF pp.33–34.
- Voice: `IMF_STAFF` / `AUTHORITIES`.
- Role: `STRUCTURAL_COMPARISON` / `INTERPRETATION_LIMIT`.
- Bridge: repos, guarantees and domestic-law FX issuance can bridge financing needs without yet proving durable international market access.
- Atlas: `q.ef08`, `q.ef10`–`q.ef12`.
- Assessment: **ALREADY_EXPLICIT**.

### IMF17 — fast credit growth versus a shallow financial system

- Locator: Box 8, PDF p.45; Figure 2, PDF p.48.
- Voice: `IMF_STAFF`.
- Role: `STRUCTURAL_COMPARISON`.
- Bridge: a high credit growth rate is compatible with private credit remaining very low as a share of GDP.
- Atlas: `q.ef14`, `q.ef17`.
- Assessment: **CUE_CANDIDATE**.

### IMF18 — productivity diagnosis versus current recovery

- Locator: Structural Policies ¶33–34, PDF pp.27–28; Figure 2, PDF p.48.
- Voice: `IMF_STAFF`.
- Role: `STRUCTURAL_COMPARISON`.
- Bridge: short-run output recovery does not establish productivity convergence or durable capacity deepening.
- Atlas: `q.re05`, `q.re06`, `q.re12`.
- Assessment: **CUE_CANDIDATE**; no new productivity question now.

### IMF19 — resource boom can precede broad employment gains

- Locator: Structural Policies ¶34, PDF p.28.
- Voice: `IMF_STAFF`.
- Role: `TENSION`.
- Bridge: primary-sector expansion may require spillovers to services/manufacturing and other regions before benefits become broad-based.
- Atlas: `q.re01`, `q.re07`, `q.re08`; future Labor port.
- Assessment: **SEMANTIC_FOLLOWUP** for Labor, not a new Real question.

### IMF20 — official statistics have interpretation limits

- Locator: Data Quality and Adequacy ¶43, PDF p.32; Monetary/FX ¶28, PDF p.25.
- Voice: `IMF_STAFF`.
- Role: `INTERPRETATION_LIMIT`.
- Bridge: outdated CPI weights and national-accounts base/granularity can matter for interpretation even when official data remain the measurement authority.
- Atlas: `q.ns01`–`q.ns04`, Real national-accounts questions.
- Assessment: **HUMAN_GATE** before any persistent warning/cue policy.

### IMF21 — poverty improvement is a decomposition, not only inflation

- Locator: Box 1, PDF p.38; Figure 3, PDF p.49.
- Voice: `IMF_STAFF` / `NATIONAL_DATA`.
- Role: `DECOMPOSITION`.
- Bridge: labor income, relative basic-basket inflation, pensions and transfers contribute separately to poverty changes.
- Atlas: future Household Welfare/Labor boundary; Nominal only supplies one piece.
- Assessment: **HUMAN_GATE** / future-region follow-up.

### IMF22 — BCRA balance-sheet improvement versus negative net FX position

- Locator: Box 7, PDF p.44.
- Voice: `IMF_STAFF`.
- Role: `TENSION`.
- Bridge: liability-side/peso balance-sheet repair can coexist with a deeply negative net FX position.
- Atlas: `q.ef01`, `q.ef03`, `q.ef11`.
- Assessment: **CUE_CANDIDATE** / measurement support.

### IMF23 — financial deepening needs both level and resilience

- Locator: Box 8, PDF p.45; Figure 7, PDF p.53.
- Voice: `IMF_STAFF`.
- Role: `STRUCTURAL_COMPARISON`.
- Bridge: credit deepening should be read beside capital/liquidity buffers, NPLs and funding structure.
- Atlas: `q.ef14`–`q.ef17`.
- Assessment: **ALREADY_EXPLICIT**, incomplete empirically.

### IMF24 — Figure 3 supplies the Real Economy opening architecture

- Locator: Figure 3, PDF p.49.
- Voice: `IMF_STAFF` / `NATIONAL_DATA`.
- Role: `DECOMPOSITION`.
- Bridge: sector activity, GDP contributions, employment composition, real wages and poverty are shown as one connected recovery story.
- Atlas: `q.re01`, `q.re03`, future Labor/Welfare ports.
- Assessment: validates a **thin Real opening**, not broad activation.

## Media agenda sensing

### Corpus structure

The corpus contains 500 rows and 500 unique `article_key` values from 210 sources. `published_at` is missing for 62 rows. Effective dates (using `published_at`, then collection first-seen when absent) span June 2025 to August 2026, but the collection is bursty: only 10 months contain observations and only 99 calendar days are represented.

`observation_count` ranges from 1 to 7 (median 2; mean 2.024). The largest source accounts for 7.8% of raw rows and the largest collection digest for 7.6%.

Deterministic near-duplicate handling:

- `article_key` is the primary identity;
- normalize title text;
- compare only within the existing economic lane and, where dates are available, within four days;
- merge when title Jaccard >= 0.72, token-set similarity >= 95, or sequence similarity >= 91;
- preserve source diversity and persistence statistics per cluster.

This reduces 500 raw rows to 478 analytical records. Nine obvious foreign-macro false-positive groups were excluded from the bounded Argentina economic attention inventory.

The cluster CSV contains only aggregate cluster records. Headline counts are **attention evidence only** and are not used as a ranking of economic importance.

### Recurring attention clusters

| Cluster | Dedup articles | Distinct sources | Interpretation |
|---|---:|---:|---|
| Dollar / FX market and gap | 77 | 45 | Very salient but analytically well covered already by Nominal FX questions. |
| Inflation momentum / CPI | 58 | 49 | Persistent demand for current inflation and acceleration/deceleration. |
| Wages / paritarias | 56 | 49 | Strong Labor-boundary demand; do not leak into Nominal semantics. |
| Reserves / BCRA purchases | 41 | 22 | High interpretation pressure around purchases versus usable buffers. |
| Inflation versus wages | 37 | 29 | Cross-region public question pressure, but Labor is not yet in the loaded three-region graph. |
| Employment / labor market | 32 | 32 | Important future cross-port for Real recovery breadth. |
| Poverty / basic basket | 28 | 27 | Strong Welfare boundary; IMF Box 1 clarifies why headline CPI alone is insufficient. |
| Rates / savings | 28 | 19 | Useful bridge to real financial conditions, not a new rate question. |
| Activity / consumption | 23 | 20 | Supports Real Economy opening priority. |
| Sovereign risk / markets | 23 | 16 | Supports `q.ef08`/`q.ef09`; no new semantic object. |
| Trade / external | 20 | 17 | Supports Real↔External imports/export-capacity bridge. |
| Fiscal anchor | 19 | 17 | Future Fiscal region, not this packet's expansion target. |
| Debt / refinancing | 18 | 13 | Existing External questions already cover maturity wall and financing mix. |
| Credit / finance | 9 | 8 | Lower volume but high analytical leverage because of low-base/quality interpretation. |

## Semantic reassessment findings

### High-value measurement gaps

**1. Finish `q.ef01` empirically.**

`q.ef01` is PUBLIC and semantically asks for the distinction among gross reserves, NIR, liquid buffers and adequacy. Its current primary artifact `pi.ef46` is explicitly a gross-reserve stock view. Send the already-declared NIR/liquid-buffer demand to the measurement scout rather than adding semantics.

**2. Materialize the Real Economy sector-breadth bundle.**

For `q.re01`, highest leverage is the existing declared bundle:

- `ci.re.emae_sa_index`
- `ci.re.manufacturing_sa_index`
- `ci.re.construction_sa_index`
- `ci.re.agriculture_sa_index`
- `ci.re.mining_energy_sa_index`

This unlocks the opening question and several subordinate sector comparisons.

**3. Measure investment composition.**

For `q.re06`, prioritize `ci.re.gfcf_construction_real` and `ci.re.gfcf_machinery_real`. This is the cheapest way to distinguish cyclical construction from capacity-deepening machinery/equipment.

**4. Add credit-quality evidence before telling a normalization story.**

`q.ef15` already exists. Bind/measure the already-declared NPL/capital evidence rather than adding a new risk question.

### Low-cost relation gaps

All proposed edges use the existing `associated_with` vocabulary and deliberately avoid causal wording.

1. `ef.private_credit --associated_with--> re.financial_conditions`
   - The plot layer already crosses this boundary in `pi.re17`; the concept graph should make the same descriptive bridge explicit.
2. `ns.real_interest_rate --associated_with--> re.financial_conditions`
   - `pi.re18` already places investment beside real rates without causal claims.
3. `re.imports_volume --associated_with--> ef.goods_trade_balance`
   - Useful but should carry a unit/valuation interpretation limit: real import volume is not identical to nominal goods-balance value.

### Already explicit; do not duplicate

- BCRA FX purchases versus reserve/external outcomes: `q.ns11`, `q.ef03`, `q.ef20`.
- Reserves versus sovereign risk: `q.ef09`.
- Real appreciation versus external balance: `q.ef19`.
- Fast private-credit growth versus financial depth: `q.ef14`, `q.ef17`.
- Broad versus concentrated recovery: `q.re01`, `q.re02`, `q.re07`, `q.re08`.
- Imports versus domestic-demand recovery: `q.re09`.

### Deemphasize rather than delete

At a future Real Economy activation audit, do not make `q.re02`, `q.re07`, `q.re08` and `q.re12` peer opening promises. They are useful subordinate decompositions/reference views, but a thin public hierarchy is stronger if `q.re01` owns the breadth story.

No current semantic object is recommended for deletion in this PR.

## Analytical cue candidate packet

These are proposals only. No `AnalyticalCue` schema is introduced.

| ID | Role | Target | Proposed text | Temporal character |
|---|---|---|---|---|
| CUE01 | interpretation_limit | `q.ef01` | **Gross reserves are not the same as net or immediately usable external buffers.** | STRUCTURAL |
| CUE02 | interpretation_limit | `q.ef03`, `q.ef20` | **BCRA FX purchases are one reserve flow; debt service, financing and other balance-sheet changes also move NIR.** | CURRENT |
| CUE03 | interpretation_limit | `q.ef14`, `q.ef17` | **Fast credit growth can coexist with a shallow financial system when lending starts from an unusually low base.** | STRUCTURAL |
| CUE04 | tension | `q.ns12`, `q.ef15`, `q.re11` | **Lower market rates do not by themselves mean easy credit when asset quality and bank risk constraints are tightening.** | CURRENT |
| CUE05 | tension | `q.re01` | **Aggregate recovery can strengthen while labor-intensive sectors remain weak, so sector breadth matters alongside the headline index.** | CURRENT |
| CUE06 | interpretation_limit | `q.re05`, `q.re06` | **Higher fixed investment is more informative when its construction and machinery components are separated.** | STRUCTURAL |
| CUE07 | bridge | `q.re09`, `q.ef04` | **Rising imports can signal recovering domestic demand while simultaneously weakening external-balance arithmetic.** | STRUCTURAL |
| CUE08 | interpretation_limit | `q.ef09` | **Reserves and sovereign spreads share common drivers; co-movement should not be read as one-way causality.** | STRUCTURAL |
| CUE09 | tension | `q.ns10`, `q.ef19` | **Real appreciation can coexist with FX purchases and reserve accumulation; the external interpretation depends on the wider balance of payments.** | CURRENT |
| CUE10 | interpretation_limit | `q.ef07`, `q.ef16` | **Resident dollar buying need not equal capital flight when FX deposits remain inside the domestic banking system.** | CURRENT |

## Prioritized semantic resettlement

| Priority | Action | Atlas IDs | Why | Marginal complexity | Product gain |
|---|---|---|---|---|---|
| HIGH | SEND_TO_MEASUREMENT_SCOUT | `q.re01`, sector activity CIs | Unlocks the strongest future Real opening and several subordinate questions. | Medium | Very high |
| HIGH | SEND_TO_MEASUREMENT_SCOUT | `q.ef01`, `ci.ef.nir_usd`, liquid-buffer/adequacy CIs | Brings an already-public reserve question into alignment with its own semantics. | Medium | Very high |
| HIGH | SEND_TO_MEASUREMENT_SCOUT | `q.re06`, `ci.re.gfcf_construction_real`, `ci.re.gfcf_machinery_real` | Converts investment level into capacity-composition intelligence. | Low–medium | High |
| HIGH | ADD_EXISTING_RELATION | `ef.private_credit`, `re.financial_conditions` | Makes an already-used plot boundary explicit. | Very low | High |
| HIGH | ADD_EXISTING_RELATION | `ns.real_interest_rate`, `re.financial_conditions` | Connects public Nominal evidence to future Real transmission context. | Very low | High |
| HIGH | CUE_CANDIDATE | `q.ef14`, `q.ef17` | Prevents the low-base credit-growth misreading. | Very low | High |
| MEDIUM | ADD_EXISTING_RELATION | `re.imports_volume`, `ef.goods_trade_balance` | Makes demand/external arithmetic visible without inventing causality. | Very low | Medium–high |
| MEDIUM | SEND_TO_MEASUREMENT_SCOUT | `q.ef15`, NPL/capital CIs | Balances the credit-deepening story with risk evidence. | Low–medium | Medium–high |
| MEDIUM | DEEMPHASIZE | `q.re02`, `q.re07`, `q.re08`, `q.re12` | Preserves a thin opening hierarchy. | None now | High via less public noise |
| MEDIUM | CUE_CANDIDATE | `q.ef01`, `q.ef03`, `q.ef09` | Prevents stock/flow and causal reserve misreads. | Very low | Medium–high |
| LOW | HUMAN_GATE | CPI/national-account data-quality cues | Persistent statistical caveats change epistemic presentation and need human judgment. | Low technical / high methodological | Uncertain |

No candidate clears the bar for a new QuestionIntent in this pass.

## Real Economy activation-oriented review

Status: semantic vertical present; `populated = false`; 12 QuestionIntents; 24 PlotIntents; 0 materialized Real Economy PlotArtifacts.

### Recommended future opening spine

1. **`q.re01` — How broad-based is Argentina's economic recovery across major sectors?**
   - strongest opening synthesis;
   - directly matches the aggregate-versus-composition IMF bridge;
   - should own the sector-breadth story.
2. **`q.re03` — Which components of demand and trade are driving real GDP growth?**
   - explains the aggregate result rather than merely charting it;
   - natural bridge to External through imports/exports.
3. **`q.re05` — Is fixed investment recovering, and how durable is the improvement?**
   - strongest bridge from cyclical recovery to durable capacity;
   - `q.re06` should be the high-value composition drilldown once data are bound.

### Supporting rather than leading initially

- `q.re02`, `q.re07`, `q.re08`: sector decompositions supporting `q.re01`.
- `q.re04`: consumption component supporting the growth-driver story.
- `q.re06`: investment composition drilldown once machinery/construction data exist.
- `q.re12`: historical/reference framing, not a leading public promise.

### Cross-ports

- **Labor:** `q.re01` / `q.re07` / `q.re08` should eventually connect to employment intensity/growth. IMF evidence makes this important, but Labor semantics should own the labor side. Do not invent it here.
- **External:** `q.re09` / `q.re10` already form good ports to `q.ef04` / `q.ef05`; one cautious imports↔goods-balance relation is enough.
- **Nominal:** `q.re11` already uses real-rate context. The missing `ns.real_interest_rate -> associated_with -> re.financial_conditions` edge would make the port explicit.

### Activation criterion suggested for a later audit

Do not activate Real Economy merely because its semantic inventory exists. First materialize and curate at least one primary figure for each of `q.re01`, `q.re03`, and `q.re05`, then re-run publication/UX review on that thin spine.

## Things we considered and recommend NOT building now

1. **No new primary-sectors-versus-labor-intensive-recovery question.** `q.re01`/`q.re02`/`q.re07`/`q.re08` already cover the Real side; the missing increment is Labor cross-port evidence.
2. **No new reserves-versus-sovereign-risk question.** `q.ef09` already asks it directly.
3. **No new BCRA-purchases-versus-external-position question.** `q.ef20` already exists; the gap is measurement and interpretation.
4. **No new real-appreciation-versus-external-balance question.** `q.ef19` already exists.
5. **No Household Welfare semantics from the IMF poverty box in this PR.** The bridge belongs to Welfare/Labor boundaries; Nominal provides only one component.
6. **No Fiscal Regime semantics from IMF fiscal boxes in this PR.** Fiscal is outside this three-region reassessment and remains independently inactive.
7. **No new causal global relation type** for competitiveness, crowding-out, or reserve-to-spread causality. Existing descriptive vocabulary is sufficient; stronger claims require a human ontology/methodology gate.
8. **No IMF projection Series as measurement truth.** Program/staff projections remain framing inputs.
9. **No additional daily-dollar quote trackers/questions.** FX attention is high, but the analytical dimensions are already represented.
10. **No large NLP/media-classification framework.** The deterministic 500-row analysis is adequate for agenda sensing.
11. **Do not activate `q.re02`, `q.re07`, `q.re08`, or `q.re12` as peer public routes on day one.** They are useful support but would weaken the opening hierarchy before Real evidence is materialized.

## Boundary check

This packet changes research files only. It does not edit Concepts, Relations, QuestionIntents, CanonicalIndicators, DerivedIndicators, PlotIntents, ChartSpecs, Series, SeriesBindings, figures, publication state, region activation, routes, or frontend UI. It proposes decisions for later PRs without changing E2's current declared measurement demand.
