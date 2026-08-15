from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import unittest

import yaml

from figures import measurement_resolver as resolver


ROOT = Path(__file__).resolve().parents[2]


class MeasurementResolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.measurements = {item.indicator_id: item for item in resolver.resolve_all()}

    def test_exactly_three_seed_measurements_resolve(self):
        self.assertEqual(
            set(self.measurements),
            {"ci.ns.cpi_monthly", "ci.ns.reer_index", "ci.ef.goods_balance_usd"},
        )

    def test_ipc_fraction_is_normalized_to_percent(self):
        item = self.measurements["ci.ns.cpi_monthly"]
        self.assertEqual(item.unit_semantics, "percent_mom")
        self.assertEqual(item.frequency, "monthly")
        self.assertEqual(item.data_as_of, "2026-07-01")
        self.assertEqual(item.latest_value, Decimal("2.1137724267861800"))
        self.assertEqual(item.normalization, {"kind": "scale", "factor": 100})
        self.assertEqual(item.freshness_state, "fresh")

    def test_itcrm_identity_preserves_provider_index(self):
        item = self.measurements["ci.ns.reer_index"]
        self.assertEqual(item.unit_semantics, "index")
        self.assertEqual(item.frequency, "monthly")
        self.assertEqual(item.data_as_of, "2024-12-01")
        self.assertEqual(item.latest_value, Decimal("79.7730421256683"))
        self.assertEqual(item.normalization, {"kind": "identity"})
        self.assertEqual(item.freshness_state, "stale_warning")

    def test_trade_balance_millions_are_normalized_to_billions(self):
        item = self.measurements["ci.ef.goods_balance_usd"]
        self.assertEqual(item.unit_semantics, "usd_billions")
        self.assertEqual(item.frequency, "monthly")
        self.assertEqual(item.data_as_of, "2026-06-01")
        self.assertEqual(item.latest_value, Decimal("2.1938482095200006"))
        self.assertEqual(item.normalization, {"kind": "scale", "factor": 0.001})
        self.assertEqual(item.freshness_state, "fresh")

    def test_source_representation_is_preserved_in_snapshots(self):
        ipc = self.measurements["ci.ns.cpi_monthly"]
        trade = self.measurements["ci.ef.goods_balance_usd"]
        self.assertEqual(ipc.source_unit, "Variación intermensual")
        self.assertEqual(trade.source_unit, "Millones de dólares")
        self.assertNotEqual(ipc.latest_value, Decimal("0.0211377242678618"))
        self.assertNotEqual(trade.latest_value, Decimal("2193.8482095200006"))

    def test_runtime_seed_bindings_match_the_frozen_contract_examples(self):
        runtime_doc = yaml.safe_load((ROOT / "figures/series_bindings.yaml").read_text(encoding="utf-8"))
        examples_doc = yaml.safe_load((ROOT / "figures/examples.yaml").read_text(encoding="utf-8"))
        expected = [
            {key: binding[key] for key in ("series_id", "canonical_indicator_id", "normalization")}
            for binding in examples_doc["series_bindings"]
        ]
        self.assertEqual(runtime_doc["series_bindings"], expected)

    def test_unsupported_normalization_fails_closed(self):
        with self.assertRaises(resolver.MeasurementResolutionError):
            resolver.normalize_value("1.0", {"kind": "yoy"})

    def test_unknown_indicator_is_explicit(self):
        with self.assertRaises(resolver.MeasurementResolutionError):
            resolver.resolve_indicator("ci.does.not.exist")


if __name__ == "__main__":
    unittest.main()
