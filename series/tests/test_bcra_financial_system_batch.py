from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / "snapshots" / "bcra"


def read(stem: str) -> dict[str, Decimal]:
    path = SNAP / f"{stem}.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return {row["date"]: Decimal(row["value"]) for row in csv.DictReader(handle) if row["value"]}


class BcraFinancialSystemBatchTests(unittest.TestCase):
    def assert_component_identity(self, total_stem: str, peso_stem: str, fx_stem: str) -> None:
        total, peso, fx = read(total_stem), read(peso_stem), read(fx_stem)
        common = sorted(set(total) & set(peso) & set(fx))
        self.assertGreater(len(common), 200)
        for date in common:
            delta = abs(total[date] - peso[date] - fx[date])
            self.assertLessEqual(delta, Decimal("2"), date)

    def test_private_credit_components_reconcile(self):
        self.assert_component_identity(
            "series_ar_bcra_private_credit_total_ars_equiv",
            "series_ar_bcra_private_credit_peso",
            "series_ar_bcra_private_credit_fx_ars_equiv",
        )

    def test_private_deposit_components_reconcile(self):
        self.assert_component_identity(
            "series_ar_bcra_private_deposits_total_ars_equiv",
            "series_ar_bcra_private_deposits_peso",
            "series_ar_bcra_private_deposits_fx_ars_equiv",
        )


if __name__ == "__main__":
    unittest.main()
