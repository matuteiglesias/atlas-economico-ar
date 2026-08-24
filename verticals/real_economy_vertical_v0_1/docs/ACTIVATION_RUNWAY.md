# Real Economy — activation runway

Public activation is **not part of v0.1**. The region should become `populated: true` only after a small coherent set of questions earns primary evidence and passes curation/UX gates.

## Candidate flagship opening

### `q.re01` — How broad-based is Argentina's economic recovery across major sectors?

Minimum measurement spine:
- `ci.re.emae_sa_index`
- `ci.re.manufacturing_sa_index`
- `ci.re.construction_sa_index`
- `ci.re.agriculture_sa_index`
- `ci.re.mining_energy_sa_index`

Primary candidate plots: `pi.re01`, `pi.re02`, `pi.re03`.

Why it matters: the IMF's 2026 assessment explicitly highlights an uneven recovery, with labor-intensive construction/manufacturing lagging more dynamic primary sectors.

### `q.re03` — Which components of demand and trade are driving real GDP growth?

Minimum measurement spine:
- `ci.re.real_gdp_level`
- `ci.re.private_consumption_real`
- `ci.re.public_consumption_real`
- `ci.re.gfcf_real`
- `ci.re.exports_real`
- `ci.re.imports_real`

Primary candidate plots: `pi.re04`, `pi.re14`, `pi.re20`, `pi.re21`.

Do not publish a growth-contribution decomposition until accounting semantics are explicitly validated.

### `q.re05` / `q.re06` — Is investment recovering, and is it expanding productive capacity?

Minimum measurement spine:
- `ci.re.gfcf_real`
- `ci.re.gfcf_construction_real`
- `ci.re.gfcf_machinery_real`

Primary candidate plots: `pi.re08`, `pi.re09`, `pi.re10`.

## Secondary opening candidates

- `q.re07`: manufacturing/construction versus aggregate activity;
- `q.re08`: primary-sector leadership;
- `q.re11`: financial conditions and investment, using already-owned External/Nominal indicators as context.

## Activation gate

Do not flip `populated: true` until all of the following hold:

1. at least three analytically distinct flagship questions have real primary PlotArtifacts;
2. those figures pass the Truth → Usefulness → Publication curation loop;
3. question publication derives PUBLIC without overrides used to force readiness;
4. source/freshness semantics are explicit;
5. the area page has concise editorial framing;
6. Playwright proves: home → Real Economy → substantive question → real primary evidence, including mobile;
7. no placeholder/unmaterialized chart is promoted.

A smaller excellent opening is preferred to a directory of weak routes.
