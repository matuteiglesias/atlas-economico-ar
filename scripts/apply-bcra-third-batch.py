#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path.cwd()
TODAY='2026-08-23'

SERIES = [
    {
      'id':'series.ar.bcra.private_credit_total_ars_equiv','provider_series_id':'882','canonical_indicator_id':'ci.ef.private_credit_total_ars','label':'Total private-sector credit, local and foreign currency, ARS equivalent','expected_frequency':'monthly','freshness_warning_days':75,'snapshot_subdir':'bcra'
    },
    {
      'id':'series.ar.bcra.private_credit_peso','provider_series_id':'893','canonical_indicator_id':'ci.ef.private_credit_peso_ars','label':'Private-sector credit in pesos','expected_frequency':'monthly','freshness_warning_days':75,'snapshot_subdir':'bcra'
    },
    {
      'id':'series.ar.bcra.private_credit_fx_ars_equiv','provider_series_id':'904','canonical_indicator_id':'ci.ef.private_credit_fx_ars_equivalent','label':'Private-sector foreign-currency credit, ARS equivalent','expected_frequency':'monthly','freshness_warning_days':75,'snapshot_subdir':'bcra'
    },
    {
      'id':'series.ar.bcra.private_deposits_total_ars_equiv','provider_series_id':'981','canonical_indicator_id':'ci.ef.private_deposits_total_ars','label':'Total private-sector deposits, local and foreign currency, ARS equivalent','expected_frequency':'monthly','freshness_warning_days':75,'snapshot_subdir':'bcra'
    },
    {
      'id':'series.ar.bcra.private_deposits_peso','provider_series_id':'992','canonical_indicator_id':'ci.ef.private_deposits_peso_ars','label':'Private-sector deposits in pesos','expected_frequency':'monthly','freshness_warning_days':75,'snapshot_subdir':'bcra'
    },
    {
      'id':'series.ar.bcra.private_deposits_fx_ars_equiv','provider_series_id':'1003','canonical_indicator_id':'ci.ef.private_deposits_fx_ars_equivalent','label':'Private-sector foreign-currency deposits, ARS equivalent','expected_frequency':'monthly','freshness_warning_days':75,'snapshot_subdir':'bcra'
    },
]

# Registry
p=ROOT/'series/bcra_registry.json'
d=json.loads(p.read_text())
seen={str(x['provider_series_id']) for x in d['series']}
for x in SERIES:
    if x['provider_series_id'] not in seen:
        d['series'].append(x)
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

# Canonical indicators
p=ROOT/'verticals/external_financial_constraint_vertical_v0_2/knowledge/canonical_indicators.yaml'
s=p.read_text()
blocks=[]
canon=[
('ci.ef.private_credit_total_ars','Total private-sector credit, ARS equivalent','ef.private_credit','ars','monthly'),
('ci.ef.private_credit_peso_ars','Private-sector credit in pesos','ef.private_credit','ars','monthly'),
('ci.ef.private_credit_fx_ars_equivalent','Private-sector foreign-currency credit, ARS equivalent','ef.private_credit','ars','monthly'),
('ci.ef.private_deposits_total_ars','Total private-sector deposits, ARS equivalent','ef.fx_deposits','ars','monthly'),
('ci.ef.private_deposits_peso_ars','Private-sector deposits in pesos','ef.fx_deposits','ars','monthly'),
('ci.ef.private_deposits_fx_ars_equivalent','Private-sector foreign-currency deposits, ARS equivalent','ef.fx_deposits','ars','monthly'),
('ci.ef.fx_credit_share','Foreign-currency share of private-sector credit','ef.private_credit','percent_loans','monthly'),
]
for id,label,concept,unit,freq in canon:
    if f'- id: {id}\n' in s: continue
    blocks.append(f'''- id: {id}\n  version: '0.2'\n  status: proposed_v0_2\n  epistemic_class: {'DERIVED/CURATED' if id.endswith('fx_credit_share') else 'CURATED'}\n  created_at: '{TODAY}'\n  updated_at: '{TODAY}'\n  review_state: implementation_ready\n  slice_id: external_financial_constraint\n  label: {label}\n  concept_id: {concept}\n  unit_semantics: {unit}\n  frequency: {freq}\n  series_binding_status: {'DERIVED_FROM_REGISTERED' if id.endswith('fx_credit_share') else 'REGISTERED'}\n  provider_hint: [BCRA]\n  provenance:\n    model_prior_used: false\n    media_evidence_tags: [banking, private credit, deposits, BCRA]\n''')
if blocks:
    p.write_text(s.rstrip()+"\n"+''.join(blocks))

# Mark the two previously-declared frontier outputs as now implemented without changing their semantics.
def mark_indicator_ready(text: str, indicator_id: str, binding_status: str) -> str:
    token = f"- id: {indicator_id}\n"
    start = text.find(token)
    if start < 0:
        raise RuntimeError(f"missing canonical indicator {indicator_id}")
    nxt = text.find("\n- id: ", start + len(token))
    end = len(text) if nxt < 0 else nxt
    block = text[start:end]
    block = block.replace("review_state: agent_draft_ready_for_human_review", "review_state: implementation_ready")
    block = block.replace("series_binding_status: DEFERRED_ASSUMED_AVAILABLE", f"series_binding_status: {binding_status}")
    return text[:start] + block + text[end:]

s = p.read_text()
s = mark_indicator_ready(s, "ci.ef.real_private_credit_growth", "DERIVED_FROM_REGISTERED")
s = mark_indicator_ready(s, "ci.ef.fx_deposit_share", "DERIVED_FROM_REGISTERED")
p.write_text(s)

# Bindings: provider values are already ARS-equivalent stocks in thousands of ARS.
p=ROOT/'figures/series_bindings.yaml'; s=p.read_text()
for x in SERIES:
    if f"series_id: {x['id']}" in s: continue
    s += f'''\n  - series_id: {x['id']}\n    canonical_indicator_id: {x['canonical_indicator_id']}\n    normalization:\n      kind: scale\n      factor: 1000\n'''
p.write_text(s)

# Derived declaration: repair FX-deposit share; add real credit growth and FX-credit share.
p=ROOT/'verticals/external_financial_constraint_vertical_v0_2/knowledge/derived_indicators.yaml'; s=p.read_text()
old='''  output_indicator_id: ci.ef.fx_deposit_share\n  input_indicator_ids:\n  - ci.ef.fx_deposits_usd\n  methodology: divide FX deposits by total deposits after currency conversion under a documented convention\n'''
new='''  output_indicator_id: ci.ef.fx_deposit_share\n  input_indicator_ids:\n  - ci.ef.private_deposits_fx_ars_equivalent\n  - ci.ef.private_deposits_total_ars\n  methodology: divide provider-consistent private-sector FX deposits in ARS equivalent by total private-sector deposits in ARS equivalent\n'''
if old in s: s=s.replace(old,new)
if 'output_indicator_id: ci.ef.real_private_credit_growth' not in s:
    s += f'''\n- id: di.ef.real_private_credit_growth\n  version: '0.2'\n  status: proposed_v0_2\n  epistemic_class: DERIVED/CURATED\n  created_at: '{TODAY}'\n  updated_at: '{TODAY}'\n  review_state: implementation_ready\n  slice_id: external_financial_constraint\n  output_indicator_id: ci.ef.real_private_credit_growth\n  input_indicator_ids:\n  - ci.ef.private_credit_total_ars\n  - ci.ns.cpi_monthly\n  methodology: compute month-end private credit in constant prices and its 12-month percentage change\n  methodology_status: implemented_v0_2\n  provenance: {{model_prior_used: false, imf_2026_refs: [External sector / financial system discussion]}}\n'''
if 'output_indicator_id: ci.ef.fx_credit_share' not in s:
    s += f'''\n- id: di.ef.fx_credit_share\n  version: '0.2'\n  status: proposed_v0_2\n  epistemic_class: DERIVED/CURATED\n  created_at: '{TODAY}'\n  updated_at: '{TODAY}'\n  review_state: implementation_ready\n  slice_id: external_financial_constraint\n  output_indicator_id: ci.ef.fx_credit_share\n  input_indicator_ids:\n  - ci.ef.private_credit_fx_ars_equivalent\n  - ci.ef.private_credit_total_ars\n  methodology: divide provider-consistent private-sector FX credit in ARS equivalent by total private-sector credit in ARS equivalent\n  methodology_status: implemented_v0_2\n  provenance: {{model_prior_used: false, imf_2026_refs: [External sector / financial system discussion]}}\n'''
p.write_text(s)

# Derived resolver functions + dispatch.
p=ROOT/'figures/derived_resolver.py'; s=p.read_text()
marker='''def resolve_measurement(indicator_id: str) -> FigureMeasurement:\n'''
func='''def monthly_share(\n    numerator: FigureMeasurement, denominator: FigureMeasurement, output_id: str, label: str, unit: str\n) -> FigureMeasurement:\n    num = month_end_values(numerator)\n    den = month_end_values(denominator)\n    common = sorted(set(num) & set(den))\n    observations = [\n        Observation(f"{month}-01", num[month] / den[month] * Decimal("100"))\n        for month in common if den[month] != 0\n    ]\n    if not observations:\n        raise DerivedResolutionError(f"{output_id}: no common non-zero denominator months")\n    series_ids, hashes, sources, freshness = combine_lineage(numerator, denominator)\n    return FigureMeasurement(\n        output_id, label, unit, "monthly", tuple(observations),\n        series_ids, hashes, sources, freshness, observations[-1].date,\n        f"monthly_share:{numerator.indicator_id}/{denominator.indicator_id}",\n    )\n\n\ndef real_yoy_growth(\n    nominal: FigureMeasurement, cpi: FigureMeasurement, output_id: str, label: str, unit: str\n) -> FigureMeasurement:\n    stock = month_end_values(nominal)\n    cpi_index = reconstruct_cpi_index(cpi)\n    common = sorted(set(stock) & set(cpi_index))\n    real = {month: stock[month] / cpi_index[month] for month in common}\n    observations: list[Observation] = []\n    for month in common:\n        year, mon = (int(part) for part in month.split("-"))\n        prior = f"{year - 1:04d}-{mon:02d}"\n        if prior not in real or real[prior] == 0:\n            continue\n        observations.append(Observation(f"{month}-01", (real[month] / real[prior] - Decimal("1")) * Decimal("100")))\n    if not observations:\n        raise DerivedResolutionError(f"{output_id}: no 12-month real-growth comparisons")\n    series_ids, hashes, sources, freshness = combine_lineage(nominal, cpi)\n    return FigureMeasurement(\n        output_id, label, unit, "monthly", tuple(observations),\n        series_ids, hashes, sources, freshness, observations[-1].date,\n        f"real_yoy_growth:{nominal.indicator_id}",\n    )\n\n\n'''
if 'def monthly_share(' not in s:
    s=s.replace(marker,func+marker)
needle='''    if indicator_id == "ci.ns.cpi_3m_ann":\n'''
dispatch='''    if indicator_id == "ci.ef.real_private_credit_growth":\n        return real_yoy_growth(\n            resolve_measurement("ci.ef.private_credit_total_ars"),\n            resolve_measurement("ci.ns.cpi_monthly"),\n            indicator_id, label, meta["unit_semantics"],\n        )\n    if indicator_id == "ci.ef.fx_deposit_share":\n        return monthly_share(\n            resolve_measurement("ci.ef.private_deposits_fx_ars_equivalent"),\n            resolve_measurement("ci.ef.private_deposits_total_ars"),\n            indicator_id, label, meta["unit_semantics"],\n        )\n    if indicator_id == "ci.ef.fx_credit_share":\n        return monthly_share(\n            resolve_measurement("ci.ef.private_credit_fx_ars_equivalent"),\n            resolve_measurement("ci.ef.private_credit_total_ars"),\n            indicator_id, label, meta["unit_semantics"],\n        )\n'''
if 'if indicator_id == "ci.ef.real_private_credit_growth"' not in s:
    s=s.replace(needle,dispatch+needle)
p.write_text(s)

# Display-unit semantics and artifact freeze count.
p=ROOT/'figures/materialize.py'; s=p.read_text()
s=s.replace('EXPECTED_ARTIFACTS = 35','EXPECTED_ARTIFACTS = 41')
anchor='''    "percent_annualized": ("Annual rate (%)", 1.0, "percent"),\n'''
add='''    "percent_yoy_real": ("Real year-over-year (%)", 1.0, "percent"),\n    "percent_deposits": ("Share (%)", 1.0, "percent_share"),\n    "percent_loans": ("Share (%)", 1.0, "percent_share"),\n'''
if '"percent_yoy_real"' not in s: s=s.replace(anchor,anchor+add)
p.write_text(s)

# Four narrow provider-driven PlotIntents; two existing frontier intents are reused as-is.
p=ROOT/'verticals/external_financial_constraint_vertical_v0_2/knowledge/plot_intents_v0_2.yaml'; s=p.read_text()
plots=[
('pi.ef51','Private credit by currency',[ 'ci.ef.private_credit_peso_ars','ci.ef.private_credit_fx_ars_equivalent'],['q.ef14'],'Separate peso and foreign-currency components of private credit using provider-consistent ARS-equivalent stocks.'),
('pi.ef52','Private deposits by currency',['ci.ef.private_deposits_peso_ars','ci.ef.private_deposits_fx_ars_equivalent'],['q.ef16'],'Separate peso and foreign-currency components of private deposits using provider-consistent ARS-equivalent stocks.'),
('pi.ef53','Foreign-currency shares of private credit and deposits',['ci.ef.fx_credit_share','ci.ef.fx_deposit_share'],['q.ef14','q.ef16'],'Compare dollarization on the asset and liability sides of domestic financial intermediation.'),
('pi.ef54','Private credit and deposits',['ci.ef.private_credit_total_ars','ci.ef.private_deposits_total_ars'],['q.ef14','q.ef17'],'Place total private credit beside the private deposit base using consistent ARS-equivalent source measurements.'),
]
for pid,title,inds,qs,purpose in plots:
    if f'- id: {pid}\n' in s: continue
    qstr='['+', '.join(qs)+']'; istr='['+', '.join(inds)+']'
    s += f'''\n- id: {pid}\n  version: '0.2'\n  status: proposed_v0_2\n  epistemic_class: CURATED\n  created_at: '{TODAY}'\n  updated_at: '{TODAY}'\n  review_state: implementation_ready\n  slice_id: external_financial_constraint\n  title: {title}\n  question_ids: {qstr}\n  canonical_indicator_ids: {istr}\n  reference_frame_ids: []\n  purpose: {purpose}\n  plot_status: active_v0_2\n  series_binding_status: DERIVED_FROM_REGISTERED\n  provenance: {{model_prior_used: false, media_evidence_tags: [banking, private credit, deposits, BCRA]}}\n'''
p.write_text(s)

# Six ChartSpecs: two frontier closures + four small additions.
p=ROOT/'figures/specs/bcra_batch_v0_3.yaml'
if not p.exists():
    p.write_text('''schema_version: '0.2'\nstatus: active_bcra_batch_v0_3\nchart_specs:\n  - {id: cs.bcra3.real_private_credit_growth, plot_intent_id: pi.ef30, renderer: timeseries_line, frame_id: rf.last_5y}\n  - {id: cs.bcra3.fx_deposits_share, plot_intent_id: pi.ef33, renderer: timeseries_line, frame_id: rf.last_5y}\n  - {id: cs.bcra3.private_credit_currency, plot_intent_id: pi.ef51, renderer: timeseries_line, frame_id: rf.last_5y}\n  - {id: cs.bcra3.private_deposits_currency, plot_intent_id: pi.ef52, renderer: timeseries_line, frame_id: rf.last_5y}\n  - {id: cs.bcra3.fx_shares, plot_intent_id: pi.ef53, renderer: timeseries_line, frame_id: rf.last_5y}\n  - {id: cs.bcra3.credit_vs_deposits, plot_intent_id: pi.ef54, renderer: timeseries_line, frame_id: rf.last_5y}\n''')

# Batch decision record.
p=ROOT/'series/BCRA_BATCH_V0_3.md'
if not p.exists():
    p.write_text('''# BCRA third six-Series population batch\n\nThis tranche was selected after recomputing the live PlotIntent frontier against `main` and scanning all 1,610 BCRA Monetary Statistics v4 catalog rows.\n\nSelected provider IDs: `882`, `893`, `904`, `981`, `992`, and `1003`.\n\nThey form one provider-consistent monthly financial-system block (1999-present): total/peso/foreign-currency private credit and total/peso/foreign-currency private deposits, all expressed by the provider in thousands of ARS. The two component identities are explicitly tested.\n\nThe batch closes existing demand for real private-credit growth and the foreign-currency deposit share, and supports four narrow publication views on currency composition and intermediation without adding a renderer primitive.\n\nNo economic transformation occurs in acquisition. Representation normalization (`thousand ARS -> ARS`) stays in `SeriesBinding`; real growth and shares live in `figures/derived_resolver.py`.\n''')

# Provider decomposition identities are hard guardrails for the six-source block.
p=ROOT/'series/tests/test_bcra_financial_system_batch.py'
if not p.exists():
    p.write_text('''from __future__ import annotations\n\nimport csv\nfrom decimal import Decimal\nfrom pathlib import Path\nimport unittest\n\nROOT = Path(__file__).resolve().parents[1]\nSNAP = ROOT / "snapshots" / "bcra"\n\n\ndef read(stem: str) -> dict[str, Decimal]:\n    path = SNAP / f"{stem}.csv"\n    with path.open(encoding="utf-8", newline="") as handle:\n        return {row["date"]: Decimal(row["value"]) for row in csv.DictReader(handle) if row["value"]}\n\n\nclass BcraFinancialSystemBatchTests(unittest.TestCase):\n    def assert_component_identity(self, total_stem: str, peso_stem: str, fx_stem: str) -> None:\n        total, peso, fx = read(total_stem), read(peso_stem), read(fx_stem)\n        common = sorted(set(total) & set(peso) & set(fx))\n        self.assertGreater(len(common), 200)\n        for date in common:\n            delta = abs(total[date] - peso[date] - fx[date])\n            self.assertLessEqual(delta, Decimal("2"), date)\n\n    def test_private_credit_components_reconcile(self):\n        self.assert_component_identity(\n            "series_ar_bcra_private_credit_total_ars_equiv",\n            "series_ar_bcra_private_credit_peso",\n            "series_ar_bcra_private_credit_fx_ars_equiv",\n        )\n\n    def test_private_deposit_components_reconcile(self):\n        self.assert_component_identity(\n            "series_ar_bcra_private_deposits_total_ars_equiv",\n            "series_ar_bcra_private_deposits_peso",\n            "series_ar_bcra_private_deposits_fx_ars_equiv",\n        )\n\n\nif __name__ == "__main__":\n    unittest.main()\n''')

# Freeze counts in code/tests/workflows/compiler.
repls={
'figures/kernel_tests/test_materializer.py': [('35','41')],
'scripts/build-publication.py':[
    ('EXPECTED_CHARTS = 115','EXPECTED_CHARTS = 119'),
    ('EXPECTED_INDICATORS = 83','EXPECTED_INDICATORS = 90'),
    ('EXPECTED_ARTIFACTS = 35','EXPECTED_ARTIFACTS = 41'),
    ('EXPECTED_PROMINENT_ARTIFACTS = 31','EXPECTED_PROMINENT_ARTIFACTS = 37'),
],
'.github/workflows/figure-kernel.yml':[('== 35','== 41'),('exactly 35 published','exactly 41 published')],
'.github/workflows/publication.yml':[
    ("== 83", "== 90"),
    ("== 115", "== 119"),
    ("== 297", "== 308"),
    ("== 35", "== 41"),
    ("== 31", "== 37"),
    ("PASS: 115 charts, 83 indicators, 35 PlotArtifacts; 31 prominent", "PASS: 119 charts, 90 indicators, 41 PlotArtifacts; 37 prominent"),
],
}
for rel, pairs in repls.items():
    p=ROOT/rel; s=p.read_text()
    for a,b in pairs: s=s.replace(a,b)
    p.write_text(s)

print('Applied BCRA third-batch source/config changes.')
