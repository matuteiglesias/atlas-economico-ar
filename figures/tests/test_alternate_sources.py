from __future__ import annotations

from decimal import Decimal
import unittest

from figures import measurement_resolver as resolver


def by_month(measurement):
    return {observation.date[:7]: observation.value for observation in measurement.observations}


class AlternateSourceTests(unittest.TestCase):
    def test_recent_bcra_monthly_cpi_tracks_primary_within_rounding_tolerance(self):
        primary = resolver.resolve_indicator("ci.ns.cpi_monthly")
        alternate = resolver.resolve_series("series.ar.bcra.cpi_monthly")

        self.assertEqual(primary.provider, "datos_argentina")
        self.assertEqual(primary.binding_role, "primary")
        self.assertEqual(alternate.provider, "bcra_monetarias_v4")
        self.assertEqual(alternate.binding_role, "alternate")
        self.assertEqual(alternate.provider_series_id, "27")

        primary_months = by_month(primary)
        alternate_months = by_month(alternate)
        common = sorted(set(primary_months) & set(alternate_months))[-24:]
        self.assertGreaterEqual(len(common), 12)

        for month in common:
            difference = abs(primary_months[month] - alternate_months[month])
            self.assertLessEqual(
                difference,
                Decimal("0.06"),
                f"{month}: primary={primary_months[month]} alternate={alternate_months[month]}",
            )


if __name__ == "__main__":
    unittest.main()
