from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

SERIES_DIR = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("capture_bcra", SERIES_DIR / "capture_bcra.py")
capture = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(capture)


class BcraCaptureUnitTests(unittest.TestCase):
    def test_parse_value_page(self):
        payload = (
            '{"status":200,"metadata":{"resultset":{"count":2,"offset":0,"limit":3000}},'
            '"results":[{"idVariable":5,"detalle":['
            '{"fecha":"2026-08-14","valor":1488.6984},'
            '{"fecha":"2026-08-13","valor":1480.0}]}]}'
        ).encode()
        rows, count = capture.parse_value_page(payload, "5")
        self.assertEqual(count, 2)
        self.assertEqual(rows[0], ("2026-08-14", "1488.6984"))

    def test_normalized_snapshot_has_no_economic_transform(self):
        payload = capture.normalized_csv(
            [("2026-08-11", "57.0")],
            internal_series_id="series.ar.bcra.test",
            provider_series_id="78",
        ).decode()
        self.assertIn("2026-08-11,57.0,series.ar.bcra.test,78", payload)
        self.assertNotIn("57000000", payload)

    def test_catalog_filter_url_is_encoded(self):
        url = capture.build_url("https://api.example/v4.0", "monetarias", idVariable="197", limit=1)
        self.assertEqual(url, "https://api.example/v4.0/monetarias?idVariable=197&limit=1")


if __name__ == "__main__":
    unittest.main()
