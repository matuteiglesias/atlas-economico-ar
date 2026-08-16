#!/usr/bin/env python3
"""One-shot bootstrap for the second controlled BCRA population batch.

The script is intentionally temporary. It applies the text/config changes needed
for provider IDs 19, 27, 28, 44, 108 and 160; the network capture and full build
run afterwards in CI. The resulting production files survive, this helper does
not.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def replace_once(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"{rel}: replacement anchor not found")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def append_once(rel: str, marker: str, payload: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if marker in text:
        return
    path.write_text(text.rstrip() + "\n\n" + payload.strip() + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Register the remaining six provider-native Series.
# ---------------------------------------------------------------------------
registry_path = ROOT / "series/bcra_registry.json"
registry = json.loads(registry_path.read_text(encoding="utf-8"))
existing = {str(item["provider_series_id"]) for item in registry["series"]}
new_entries = [
    {
        "id": "series.ar.bcra.peso_deposits_at_bcra",
        "provider_series_id": "19",
        "canonical_indicator_id": "ci.ns.bcra_peso_deposits",
        "label": "Banks' peso deposits with the BCRA",
        "expected_frequency": "daily",
        "freshness_warning_days": 10,
        "snapshot_subdir": "bcra",
    },
    {
        "id": "series.ar.bcra.cpi_monthly",
        "provider_series_id": "27",
        "canonical_indicator_id": "ci.ns.cpi_monthly",
        "label": "BCRA monthly inflation",
        "expected_frequency": "monthly",
        "freshness_warning_days": 75,
        "snapshot_subdir": "bcra",
    },
    {
        "id": "series.ar.bcra.cpi_yoy",
        "provider_series_id": "28",
        "canonical_indicator_id": "ci.ns.cpi_yoy",
        "label": "BCRA year-on-year inflation",
        "expected_frequency": "monthly",
        "freshness_warning_days": 75,
        "snapshot_subdir": "bcra",
    },
    {
        "id": "series.ar.bcra.tamar_private_banks_apr",
        "provider_series_id": "44",
        "canonical_indicator_id": "ci.ns.tamar_nominal",
        "label": "TAMAR private banks APR",
        "expected_frequency": "daily",
        "freshness_warning_days": 10,
        "snapshot_subdir": "bcra",
    },
    {
        "id": "series.ar.bcra.fx_deposits_private_sector",
        "provider_series_id": "108",
        "canonical_indicator_id": "ci.ef.fx_deposits_usd",
        "label": "Private-sector foreign-currency deposits",
        "expected_frequency": "daily",
        "freshness_warning_days": 10,
        "snapshot_subdir": "bcra",
    },
    {
        "id": "series.ar.bcra.policy_rate",
        "provider_series_id": "160",
        "canonical_indicator_id": "ci.ns.policy_rate_nominal",
        "label": "BCRA monetary policy rate",
        "expected_frequency": "daily",
        "freshness_warning_days": 10,
        "snapshot_subdir": "bcra",
    },
]
for entry in new_entries:
    if entry["provider_series_id"] not in existing:
        registry["series"].append(entry)
registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ---------------------------------------------------------------------------
# 2. Runtime SeriesBindings. BCRA monthly CPI is deliberately alternate:
#    the existing Datos Argentina binding remains the sole publication primary.
# ---------------------------------------------------------------------------
append_once(
    "figures/series_bindings.yaml",
    "series.ar.bcra.peso_deposits_at_bcra",
    """
  - series_id: series.ar.bcra.peso_deposits_at_bcra
    canonical_indicator_id: ci.ns.bcra_peso_deposits
    normalization:
      kind: scale
      factor: 1000000

  - series_id: series.ar.bcra.cpi_monthly
    canonical_indicator_id: ci.ns.cpi_monthly
    role: alternate
    normalization:
      kind: identity

  - series_id: series.ar.bcra.cpi_yoy
    canonical_indicator_id: ci.ns.cpi_yoy
    normalization:
      kind: identity

  - series_id: series.ar.bcra.tamar_private_banks_apr
    canonical_indicator_id: ci.ns.tamar_nominal
    normalization:
      kind: identity

  - series_id: series.ar.bcra.fx_deposits_private_sector
    canonical_indicator_id: ci.ef.fx_deposits_usd
    normalization:
      kind: scale
      factor: 0.001

  - series_id: series.ar.bcra.policy_rate
    canonical_indicator_id: ci.ns.policy_rate_nominal
    normalization:
      kind: identity
""",
)

# First explicit alternate-source semantics for the measurement resolver.
replace_once(
    "figures/measurement_resolver.py",
    """    normalization: dict[str, Any]\n    snapshot_path: str\n""",
    """    normalization: dict[str, Any]\n    binding_role: str\n    snapshot_path: str\n""",
)
replace_once(
    "figures/measurement_resolver.py",
    '            "normalization": self.normalization,\n            "snapshot_path": self.snapshot_path,\n',
    '            "normalization": self.normalization,\n            "binding_role": self.binding_role,\n            "snapshot_path": self.snapshot_path,\n',
)
replace_once(
    "figures/measurement_resolver.py",
    """    required = {"series_id", "canonical_indicator_id", "normalization"}\n    if set(binding) != required:\n        raise MeasurementResolutionError(\n            f"{source}: expected exactly {sorted(required)}, got {sorted(binding)}"\n        )\n    normalization = binding["normalization"]\n""",
    """    required = {"series_id", "canonical_indicator_id", "normalization"}\n    allowed = required | {"role"}\n    if not required <= set(binding) or not set(binding) <= allowed:\n        raise MeasurementResolutionError(\n            f"{source}: expected {sorted(required)} plus optional role, got {sorted(binding)}"\n        )\n    role = binding.get("role", "primary")\n    if role not in {"primary", "alternate"}:\n        raise MeasurementResolutionError(f"{source}: role must be primary or alternate")\n    normalization = binding["normalization"]\n""",
)
replace_once(
    "figures/measurement_resolver.py",
    """        normalization=binding["normalization"],\n        snapshot_path=str(snapshot.relative_to(ROOT)),\n""",
    """        normalization=binding["normalization"],\n        binding_role=binding.get("role", "primary"),\n        snapshot_path=str(snapshot.relative_to(ROOT)),\n""",
)
replace_once(
    "figures/measurement_resolver.py",
    """def resolve_all() -> tuple[ResolvedMeasurement, ...]:\n    bindings = load_bindings()\n    registry = load_series_registry()\n    indicators = load_indicator_catalog()\n    return tuple(resolve_binding(binding, registry=registry, indicators=indicators) for binding in bindings)\n\n\ndef resolve_indicator(indicator_id: str) -> ResolvedMeasurement:\n    matches = [item for item in resolve_all() if item.indicator_id == indicator_id]\n    if not matches:\n        raise MeasurementResolutionError(f"no SeriesBinding for {indicator_id}")\n    if len(matches) != 1:\n        raise MeasurementResolutionError(f"ambiguous SeriesBinding for {indicator_id}: {len(matches)}")\n    return matches[0]\n""",
    """def resolve_all_bindings() -> tuple[ResolvedMeasurement, ...]:\n    bindings = load_bindings()\n    registry = load_series_registry()\n    indicators = load_indicator_catalog()\n    return tuple(resolve_binding(binding, registry=registry, indicators=indicators) for binding in bindings)\n\n\ndef resolve_all() -> tuple[ResolvedMeasurement, ...]:\n    \"\"\"Return publication-primary measurements only.\"\"\"\n    return tuple(item for item in resolve_all_bindings() if item.binding_role == "primary")\n\n\ndef resolve_series(series_id: str) -> ResolvedMeasurement:\n    matches = [item for item in resolve_all_bindings() if item.series_id == series_id]\n    if not matches:\n        raise MeasurementResolutionError(f"no SeriesBinding for {series_id}")\n    if len(matches) != 1:\n        raise MeasurementResolutionError(f"ambiguous SeriesBinding for {series_id}: {len(matches)}")\n    return matches[0]\n\n\ndef resolve_indicator(indicator_id: str) -> ResolvedMeasurement:\n    matches = [item for item in resolve_all() if item.indicator_id == indicator_id]\n    if not matches:\n        raise MeasurementResolutionError(f"no primary SeriesBinding for {indicator_id}")\n    if len(matches) != 1:\n        raise MeasurementResolutionError(f"ambiguous primary SeriesBinding for {indicator_id}: {len(matches)}")\n    return matches[0]\n""",
)

append_once(
    "figures/MEASUREMENTS.md",
    "## Primary and alternate Series",
    """
## Primary and alternate Series

A CanonicalIndicator may now have provider redundancy without becoming ambiguous.
`SeriesBinding.role` defaults to `primary`; an explicit `alternate` remains fully
resolvable by Series id but is excluded from `resolve_indicator()` publication
selection. The first real case is monthly CPI: Datos Argentina remains primary
and BCRA variable 27 is retained as an authenticated alternate for QA.

This is source selection, not economic transformation: alternate observations
still use only the normal `identity` / `scale` representation normalization.
""",
)

# ---------------------------------------------------------------------------
# 3. Explicit derived measurements newly closed by this batch.
# ---------------------------------------------------------------------------
replace_once(
    "figures/derived_resolver.py",
    """def resolve_measurement(indicator_id: str) -> FigureMeasurement:\n""",
    """def _month_ordinal(month: str) -> int:\n    year, value = (int(part) for part in month.split("-"))\n    return year * 12 + value\n\n\ndef rolling_three_month_annualized(\n    item: FigureMeasurement, output_id: str, label: str, unit: str\n) -> FigureMeasurement:\n    monthly = month_end_values(item)\n    months = sorted(monthly)\n    observations: list[Observation] = []\n    for index in range(2, len(months)):\n        window = months[index - 2:index + 1]\n        if any(_month_ordinal(b) - _month_ordinal(a) != 1 for a, b in zip(window, window[1:])):\n            continue\n        gross = Decimal("1")\n        for month in window:\n            gross *= Decimal("1") + monthly[month] / Decimal("100")\n        observations.append(\n            Observation(f"{window[-1]}-01", (gross ** 4 - Decimal("1")) * Decimal("100"))\n        )\n    if not observations:\n        raise DerivedResolutionError(f"{output_id}: no contiguous 3-month windows")\n    return FigureMeasurement(\n        output_id, label, unit, "monthly", tuple(observations),\n        item.series_ids, dict(item.snapshot_sha256), item.sources,\n        item.freshness_state, observations[-1].date,\n        f"compound_three_months_annualized:{item.indicator_id}",\n    )\n\n\ndef tamar_real_expost(\n    tamar: FigureMeasurement, cpi: FigureMeasurement, output_id: str, label: str, unit: str\n) -> FigureMeasurement:\n    tamar_month = month_end_values(tamar)\n    cpi_month = month_end_values(cpi)\n    common = sorted(set(tamar_month) & set(cpi_month))\n    observations: list[Observation] = []\n    for month in common:\n        inflation_gross = Decimal("1") + cpi_month[month] / Decimal("100")\n        nominal_gross = Decimal("1") + tamar_month[month] / Decimal("100")\n        if inflation_gross <= 0 or nominal_gross <= 0:\n            continue\n        realized_annual_inflation_gross = inflation_gross ** 12\n        real_rate = (nominal_gross / realized_annual_inflation_gross - Decimal("1")) * Decimal("100")\n        observations.append(Observation(f"{month}-01", real_rate))\n    if not observations:\n        raise DerivedResolutionError(f"{output_id}: no common TAMAR/CPI months")\n    series_ids, hashes, sources, freshness = combine_lineage(tamar, cpi)\n    return FigureMeasurement(\n        output_id, label, unit, "monthly", tuple(observations),\n        series_ids, hashes, sources, freshness, observations[-1].date,\n        "tamar_apr_deflated_by_realized_monthly_cpi_annualized",\n    )\n\n\ndef resolve_measurement(indicator_id: str) -> FigureMeasurement:\n""",
)
replace_once(
    "figures/derived_resolver.py",
    """    if indicator_id == "ci.ns.official_fx_monthly_change":\n""",
    """    if indicator_id == "ci.ns.cpi_3m_ann":\n        return rolling_three_month_annualized(\n            resolve_measurement("ci.ns.cpi_monthly"),\n            indicator_id, label, meta["unit_semantics"],\n        )\n    if indicator_id == "ci.ns.infl_acceleration":\n        return monthly_difference(\n            resolve_measurement("ci.ns.cpi_monthly"),\n            indicator_id, label, meta["unit_semantics"],\n        )\n    if indicator_id == "ci.ns.tamar_real_expost":\n        return tamar_real_expost(\n            resolve_measurement("ci.ns.tamar_nominal"),\n            resolve_measurement("ci.ns.cpi_monthly"),\n            indicator_id, label, meta["unit_semantics"],\n        )\n    if indicator_id == "ci.ns.official_fx_monthly_change":\n""",
)

# ---------------------------------------------------------------------------
# 4. Selective semantic additions. Legacy intents are reused only when their
#    complete measurement requirements are now honestly satisfied.
# ---------------------------------------------------------------------------
append_once(
    "verticals/nominal_stabilization_vertical_v0_1/knowledge/plot_intents_v0_2.yaml",
    "- id: pi.ns61",
    """
- id: pi.ns61
  version: '0.2'
  status: proposed_v0_2
  epistemic_class: CURATED
  created_at: '2026-08-16'
  updated_at: '2026-08-16'
  review_state: implementation_ready
  slice_id: nominal_stabilization
  title: TAMAR private-bank rate
  question_ids: [q.ns12]
  canonical_indicator_ids: [ci.ns.tamar_nominal]
  reference_frame_ids: []
  purpose: Track the TAMAR nominal annual rate directly without requiring an expectations series.
  plot_status: active_v0_2
  series_binding_status: REGISTERED
  provenance: {model_prior_used: false, media_evidence_tags: [rates, TAMAR, BCRA]}

- id: pi.ns62
  version: '0.2'
  status: proposed_v0_2
  epistemic_class: CURATED
  created_at: '2026-08-16'
  updated_at: '2026-08-16'
  review_state: implementation_ready
  slice_id: nominal_stabilization
  title: TAMAR ex-post real rate
  question_ids: [q.ns12]
  canonical_indicator_ids: [ci.ns.tamar_real_expost]
  reference_frame_ids: []
  purpose: Compare the TAMAR annual return with realized monthly CPI inflation on an explicit annualized real-rate basis.
  plot_status: active_v0_2
  series_binding_status: DERIVED_FROM_REGISTERED
  provenance: {model_prior_used: false, media_evidence_tags: [rates, inflation, TAMAR]}

- id: pi.ns63
  version: '0.2'
  status: proposed_v0_2
  epistemic_class: CURATED
  created_at: '2026-08-16'
  updated_at: '2026-08-16'
  review_state: implementation_ready
  slice_id: nominal_stabilization
  title: BCRA policy rate history
  question_ids: [q.ns12, q.ns13]
  canonical_indicator_ids: [ci.ns.policy_rate_nominal]
  reference_frame_ids: []
  purpose: Preserve the observed BCRA policy-rate history through the final provider observation without implying that the discontinued series is current.
  plot_status: active_v0_2
  series_binding_status: REGISTERED_STALE
  provenance: {model_prior_used: false, media_evidence_tags: [policy rate, BCRA]}

- id: pi.ns64
  version: '0.2'
  status: proposed_v0_2
  epistemic_class: CURATED
  created_at: '2026-08-16'
  updated_at: '2026-08-16'
  review_state: implementation_ready
  slice_id: nominal_stabilization
  title: Bank reserve balances at the BCRA
  question_ids: [q.ns14]
  canonical_indicator_ids: [ci.ns.bcra_peso_deposits]
  reference_frame_ids: []
  purpose: Track banks' peso deposit balances held at the BCRA directly, without inferring a reserve-requirement ratio.
  plot_status: active_v0_2
  series_binding_status: REGISTERED
  provenance: {model_prior_used: false, media_evidence_tags: [bank liquidity, BCRA]}

- id: pi.ns65
  version: '0.2'
  status: proposed_v0_2
  epistemic_class: CURATED
  created_at: '2026-08-16'
  updated_at: '2026-08-16'
  review_state: implementation_ready
  slice_id: nominal_stabilization
  title: Monthly inflation and acceleration
  question_ids: [q.ns01]
  canonical_indicator_ids: [ci.ns.cpi_monthly, ci.ns.infl_acceleration]
  reference_frame_ids: []
  purpose: Show the monthly inflation rate together with its month-to-month change in percentage points.
  plot_status: active_v0_2
  series_binding_status: DERIVED_FROM_REGISTERED
  provenance: {model_prior_used: false, media_evidence_tags: [inflation, acceleration]}
""",
)
append_once(
    "verticals/external_financial_constraint_vertical_v0_2/knowledge/plot_intents_v0_2.yaml",
    "- id: pi.ef50",
    """
- id: pi.ef50
  version: '0.2'
  status: proposed_v0_2
  epistemic_class: CURATED
  created_at: '2026-08-16'
  updated_at: '2026-08-16'
  review_state: implementation_ready
  slice_id: external_financial_constraint
  title: Foreign-currency deposits
  question_ids: [q.ef16]
  canonical_indicator_ids: [ci.ef.fx_deposits_usd]
  reference_frame_ids: []
  purpose: Track the private-sector foreign-currency deposit stock directly in USD billions; the deposit share remains a separate unresolved measurement.
  plot_status: active_v0_2
  series_binding_status: REGISTERED
  provenance: {model_prior_used: false, media_evidence_tags: [FX deposits, banking, BCRA]}
""",
)

# Honest viewport for provider series 160, known to stop in July 2025.
append_once(
    "figures/reference_frames.yaml",
    "- id: rf.policy_rate_2023_12_to_2025_07",
    """
  - id: rf.policy_rate_2023_12_to_2025_07
    label: Dec 2023–Jul 2025 policy-rate window
    kind: fixed
    window:
      start: '2023-12-01'
      end: '2025-07-10'
""",
)

spec_path = ROOT / "figures/specs/bcra_batch_v0_2.yaml"
if not spec_path.exists():
    spec_path.write_text(
        """schema_version: '0.2'
status: active_bcra_batch_v0_2
chart_specs:
  - {id: cs.bcra2.inflation_momentum, plot_intent_id: pi.ns01, renderer: timeseries_line, frame_id: rf.last_5y}
  - {id: cs.bcra2.inflation_monthly_yoy, plot_intent_id: pi.ns03, renderer: timeseries_line, frame_id: rf.last_5y}
  - {id: cs.bcra2.disinflation_since_dec2023, plot_intent_id: pi.ns04, renderer: timeseries_line, frame_id: rf.since_dec_2023}
  - {id: cs.bcra2.policy_vs_baibar, plot_intent_id: pi.ns31, renderer: timeseries_line, frame_id: rf.policy_rate_2023_12_to_2025_07}
  - {id: cs.bcra2.tamar, plot_intent_id: pi.ns61, renderer: timeseries_line, frame_id: rf.last_12m}
  - {id: cs.bcra2.tamar_real_expost, plot_intent_id: pi.ns62, renderer: timeseries_line, frame_id: rf.last_12m}
  - {id: cs.bcra2.policy_rate, plot_intent_id: pi.ns63, renderer: timeseries_line, frame_id: rf.policy_rate_2023_12_to_2025_07}
  - {id: cs.bcra2.reserve_balances, plot_intent_id: pi.ns64, renderer: timeseries_line, frame_id: rf.last_5y}
  - {id: cs.bcra2.inflation_acceleration, plot_intent_id: pi.ns65, renderer: timeseries_line, frame_id: rf.last_5y}
  - {id: cs.bcra2.fx_deposits, plot_intent_id: pi.ef50, renderer: timeseries_line, frame_id: rf.last_5y}
""",
        encoding="utf-8",
    )

# ---------------------------------------------------------------------------
# 5. Figure kernel / publication scale-up. No new renderer primitive.
# ---------------------------------------------------------------------------
replace_once("figures/materialize.py", "EXPECTED_ARTIFACTS = 25", "EXPECTED_ARTIFACTS = 35")
replace_once(
    "figures/materialize.py",
    '    "percent_mom": ("Monthly change (%)", 1.0, "percent"),\n    "percent": ("Change (%)", 1.0, "percent"),\n    "percentage_points_change": ("Percentage points", 1.0, "percent"),\n',
    '    "percent_mom": ("Monthly change (%)", 1.0, "percent_mom"),\n    "percent_yoy": ("Year-over-year (%)", 1.0, "percent_yoy"),\n    "percent": ("Change (%)", 1.0, "percent"),\n    "percentage_points_change": ("Change in monthly inflation (pp)", 1.0, "percentage_points"),\n',
)
replace_once("figures/kernel_tests/test_materializer.py", "self.assertEqual(len(specs), 25)", "self.assertEqual(len(specs), 35)")
replace_once(
    "figures/kernel_tests/test_materializer.py",
    "def test_materializes_exactly_25_contract_valid_artifacts(self):",
    "def test_materializes_exactly_35_contract_valid_artifacts(self):",
)
replace_once("figures/kernel_tests/test_materializer.py", "self.assertEqual(len(artifacts), 25)", "self.assertEqual(len(artifacts), 35)")
replace_once("figures/kernel_tests/test_materializer.py", 'self.assertEqual(manifest["artifact_count"], 25)', 'self.assertEqual(manifest["artifact_count"], 35)')
replace_once("figures/kernel_tests/test_materializer.py", 'self.assertEqual(len(list((output / "svg").glob("*.svg"))), 25)', 'self.assertEqual(len(list((output / "svg").glob("*.svg"))), 35)')
replace_once("figures/kernel_tests/test_materializer.py", 'self.assertEqual(len(list((output / "png").glob("*.png"))), 25)', 'self.assertEqual(len(list((output / "png").glob("*.png"))), 35)')

replace_once("scripts/build-publication.py", "EXPECTED_CHARTS = 109", "EXPECTED_CHARTS = 115")
replace_once("scripts/build-publication.py", "EXPECTED_ARTIFACTS = 25", "EXPECTED_ARTIFACTS = 35")

# Route verification should scale by construction. Publication CI keeps explicit
# aggregate freeze counts; this verifier owns only route uniqueness/existence.
route_path = ROOT / "web/scripts/verify-routes.mjs"
route_text = route_path.read_text(encoding="utf-8")
route_text = route_text.replace("const expectedRoutes = 293;\n\n", "")
route_text = route_text.replace(
    "if (uniqueRoutes.size !== expectedRoutes) {\n  console.error(`Route contract verification failed: expected ${expectedRoutes} unique routes, found ${uniqueRoutes.size}.`);\n  process.exit(1);\n}\n",
    "if (uniqueRoutes.size !== routes.length) {\n  console.error(`Route contract verification failed: ${routes.length - uniqueRoutes.size} duplicate href(s).`);\n  process.exit(1);\n}\n",
)
route_path.write_text(route_text, encoding="utf-8")

# ---------------------------------------------------------------------------
# 6. BCRA integrity freeze now covers the full original 12-Series tranche.
# ---------------------------------------------------------------------------
replace_once(
    "series/validate_bcra.py",
    '"""Offline integrity validation for the frozen six-Series BCRA expansion batch."""',
    '"""Offline integrity validation for the frozen twelve-Series BCRA tranche."""',
)
replace_once("series/validate_bcra.py", "if len(entries) != 6:", "if len(entries) != 12:")
replace_once(
    "series/validate_bcra.py",
    'raise ValidationError(f"BCRA batch freeze requires exactly 6 Series, found {len(entries)}")',
    'raise ValidationError(f"BCRA tranche freeze requires exactly 12 Series, found {len(entries)}")',
)
replace_once(
    "series/validate_bcra.py",
    'if len({entry["provider_series_id"] for entry in entries}) != 6:',
    'if len({entry["provider_series_id"] for entry in entries}) != 12:',
)
replace_once(
    "series/validate_bcra.py",
    'if len({entry["canonical_indicator_id"] for entry in entries}) != 6:',
    'if len({entry["canonical_indicator_id"] for entry in entries}) != 12:',
)
replace_once(
    "series/validate_bcra.py",
    'raise ValidationError("BCRA batch must bind six distinct CanonicalIndicators")',
    'raise ValidationError("BCRA tranche must map twelve distinct CanonicalIndicators")',
)
replace_once(
    "series/validate_bcra.py",
    'print("PASS: validated 6 authentic BCRA Series captures offline.")',
    'print("PASS: validated 12 authentic BCRA Series captures offline.")',
)

# ---------------------------------------------------------------------------
# 7. Tests: primary publication selection, alternate CPI, stale policy rate,
#    and newly available derived measurements.
# ---------------------------------------------------------------------------
test_path = ROOT / "figures/tests/test_measurement_resolver.py"
test_text = test_path.read_text(encoding="utf-8")
test_text = test_text.replace("def test_nine_direct_measurements_resolve(self):", "def test_fourteen_primary_direct_measurements_resolve(self):")
test_text = test_text.replace("self.assertEqual(len(self.measurements), 9)", "self.assertEqual(len(self.measurements), 14)", 1)
test_text = test_text.replace(
    '            "ci.ns.transactional_m2_nominal",\n        }',
    '            "ci.ns.transactional_m2_nominal",\n            "ci.ns.cpi_yoy",\n            "ci.ns.tamar_nominal",\n            "ci.ns.policy_rate_nominal",\n            "ci.ns.bcra_peso_deposits",\n            "ci.ef.fx_deposits_usd",\n        }',
    1,
)
test_text = test_text.replace(
    """    def test_all_bcra_sources_are_fresh(self):\n        bcra = [m for m in self.measurements.values() if m.provider == \"bcra_monetarias_v4\"]\n        self.assertEqual(len(bcra), 6)\n        self.assertTrue(all(m.freshness_state == \"fresh\" for m in bcra))\n""",
    """    def test_bcra_primary_freshness_is_explicit(self):\n        bcra = [m for m in self.measurements.values() if m.provider == \"bcra_monetarias_v4\"]\n        self.assertEqual(len(bcra), 11)\n        policy = self.measurements[\"ci.ns.policy_rate_nominal\"]\n        self.assertEqual(policy.freshness_state, \"stale_warning\")\n        self.assertTrue(\n            all(m.freshness_state == \"fresh\" for m in bcra if m.indicator_id != \"ci.ns.policy_rate_nominal\")\n        )\n\n    def test_bcra_monthly_cpi_is_authenticated_alternate(self):\n        primary = resolver.resolve_indicator(\"ci.ns.cpi_monthly\")\n        alternate = resolver.resolve_series(\"series.ar.bcra.cpi_monthly\")\n        self.assertEqual(primary.provider, \"datos_argentina\")\n        self.assertEqual(primary.binding_role, \"primary\")\n        self.assertEqual(alternate.indicator_id, \"ci.ns.cpi_monthly\")\n        self.assertEqual(alternate.provider, \"bcra_monetarias_v4\")\n        self.assertEqual(alternate.binding_role, \"alternate\")\n""",
)
test_text = test_text.replace(
    '            "ci.ns.transactional_m2_real": "monthly",\n',
    '            "ci.ns.transactional_m2_real": "monthly",\n            "ci.ns.cpi_3m_ann": "monthly",\n            "ci.ns.infl_acceleration": "monthly",\n            "ci.ns.tamar_real_expost": "monthly",\n',
)
test_path.write_text(test_text, encoding="utf-8")

batch_doc = ROOT / "series/BCRA_BATCH_V0_2.md"
batch_doc.write_text(
    """# BCRA second six-Series population batch\n\nThis batch completes the original twelve-Series BCRA tranche with provider IDs\n`19`, `27`, `28`, `44`, `108`, and `160`.\n\nThe capture layer remains unchanged: catalog, optional methodology and every\npaginated values response are preserved byte-for-byte; deterministic snapshots\ncontain provider-native values and `economic_transform` remains `none`.\n\nSpecial cases:\n\n- BCRA `27` is an authenticated **alternate** for `ci.ns.cpi_monthly`; Datos\n  Argentina remains the publication primary.\n- BCRA `160` is intentionally retained as stale historical evidence. Its\n  PlotSpecs use a fixed window ending at the provider's July-2025 endpoint.\n- Economic transformations newly executable from existing semantics (3-month\n  annualized CPI, inflation acceleration, TAMAR ex-post real rate) live only in\n  `figures/derived_resolver.py`.\n\nThe batch does not add a renderer primitive, runtime API, database, CMS or\nfrontend chart library.\n""",
    encoding="utf-8",
)

print("PASS: staged second six-Series BCRA expansion")
