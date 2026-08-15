from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import unittest

import yaml

from figures import measurement_resolver as resolver
from figures.derived_resolver import resolve_measurement

ROOT = Path(__file__).resolve().parents[2]


class MeasurementResolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.measurements = {item.indicator_id: item for item in resolver.resolve_all()}

    def test_nine_direct_measurements_resolve(self):
        self.assertEqual(len(self.measurements), 9)
        expected = {
            "ci.ns.cpi_monthly",
            "ci.ns.reer_index",
            "ci.ef.goods_balance_usd",
            "ci.ef.gross_reserves_usd",
            "ci.ns.official_fx",
            "ci.ns.money_market_rate",
            "ci.ns.monetary_base_nominal",
            "ci.ns.bcra_fx_purchases_daily",
            "ci.ns.transactional_m2_nominal",
        }
        self.assertEqual(set(self.measurements), expected)

    def test_seed_normalizations_remain_unchanged(self):
        self.assertEqual(
            self.measurements["ci.ns.cpi_monthly"].latest_value,
            Decimal("2.1137724267861800"),
        )
        self.assertEqual(
            self.measurements["ci.ef.goods_balance_usd"].normalization,
            {"kind": "scale", "factor": 0.001},
        )

    def test_bcra_normalizations_are_representation_only(self):
        self.assertEqual(
            self.measurements["ci.ef.gross_reserves_usd"].normalization,
            {"kind": "scale", "factor": 0.001},
        )
        self.assertEqual(
            self.measurements["ci.ns.monetary_base_nominal"].normalization,
            {"kind": "scale", "factor": 1000000},
        )
        self.assertEqual(
            self.measurements["ci.ns.bcra_fx_purchases_daily"].normalization,
            {"kind": "scale", "factor": 1000000},
        )
        self.assertEqual(self.measurements["ci.ns.official_fx"].normalization, {"kind": "identity"})

    def test_all_bcra_sources_are_fresh(self):
        bcra = [m for m in self.measurements.values() if m.provider == "bcra_monetarias_v4"]
        self.assertEqual(len(bcra), 6)
        self.assertTrue(all(m.freshness_state == "fresh" for m in bcra))

    def test_derived_products_are_resolvable(self):
        expected = {
            "ci.ns.official_fx_monthly_change": "monthly",
            "ci.ef.reserve_change_monthly": "monthly",
            "ci.ef.reserve_accumulation_ytd": "daily",
            "ci.ns.bcra_fx_purchases_cumulative": "daily",
            "ci.ns.monetary_base_real": "monthly",
            "ci.ns.transactional_m2_real": "monthly",
        }
        for indicator_id, frequency in expected.items():
            item = resolve_measurement(indicator_id)
            self.assertEqual(item.frequency, frequency)
            self.assertGreater(len(item.observations), 1)

    def test_real_money_indices_anchor_dec_2023(self):
        for indicator_id in ("ci.ns.monetary_base_real", "ci.ns.transactional_m2_real"):
            item = resolve_measurement(indicator_id)
            anchor = next(obs for obs in item.observations if obs.date == "2023-12-01")
            self.assertEqual(anchor.value.quantize(Decimal("0.000001")), Decimal("100.000000"))

    def test_seed_examples_remain_a_subset_of_runtime_bindings(self):
        runtime = yaml.safe_load((ROOT / "figures/series_bindings.yaml").read_text())["series_bindings"]
        examples = yaml.safe_load((ROOT / "figures/examples.yaml").read_text())["series_bindings"]
        contract_fields = ("series_id", "canonical_indicator_id", "normalization")
        projected_runtime = [
            {field: binding[field] for field in contract_fields}
            for binding in runtime[: len(examples)]
        ]
        projected_examples = [
            {field: binding[field] for field in contract_fields}
            for binding in examples
        ]
        self.assertEqual(projected_runtime, projected_examples)

    def test_unknown_indicator_fails_closed(self):
        with self.assertRaises(resolver.MeasurementResolutionError):
            resolver.resolve_indicator("ci.does.not.exist")


if __name__ == "__main__":
    unittest.main()
