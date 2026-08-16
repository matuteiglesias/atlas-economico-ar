from __future__ import annotations

import csv
from decimal import Decimal
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
METHODOLOGY = ROOT / "series/raw/bcra_monetarias_v4/series_ar_bcra_fx_purchases_reserve_factor.methodology.json"
SNAPSHOT = ROOT / "series/snapshots/bcra/series_ar_bcra_fx_purchases_reserve_factor.csv"
PROVENANCE = ROOT / "series/snapshots/bcra/series_ar_bcra_fx_purchases_reserve_factor.provenance.json"


class BCRAFXPurchaseSemanticsTests(unittest.TestCase):
    def test_variable_78_is_signed_sales_and_purchases_evidence(self):
        methodology = json.loads(METHODOLOGY.read_text(encoding="utf-8"))
        detail = methodology["results"][0]["detalle"].lower()
        self.assertIn("sales and purchases", detail)

        provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        self.assertEqual(provenance["provider_series_id"], "78")
        self.assertEqual(provenance["economic_transform"], "none")

        values: list[Decimal] = []
        with SNAPSHOT.open(encoding="utf-8", newline="") as handle:
            for row in csv.reader(handle):
                if not row:
                    continue
                values.append(Decimal(row[1]))

        self.assertTrue(values)
        self.assertLess(min(values), Decimal("0"), "historical BCRA sales must remain negative")
        self.assertGreater(max(values), Decimal("0"), "historical BCRA purchases must remain positive")


if __name__ == "__main__":
    unittest.main()
