from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

FIGURES = Path(__file__).resolve().parents[1]
if str(FIGURES) not in sys.path:
    sys.path.insert(0, str(FIGURES))

import curation


class CurationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = {
            "id": "cs.test",
            "plot_intent_id": "pi.test",
            "renderer": "timeseries_line",
            "frame_id": "rf.last_5y",
        }
        self.artifact = {
            "plot_intent_id": "pi.test",
            "chart_spec_id": "cs.test",
            "renderer": "timeseries_line",
            "frame_id": "rf.last_5y",
            "indicator_ids": ["ci.test.level"],
            "series_ids": ["series.test"],
            "unit_semantics": ["ars"],
            "freshness_state": "fresh",
            "data_as_of": "2026-08-01",
            "generated_at": "2026-08-02T00:00:00Z",
            "snapshot_sha256": {"series.test": "a" * 64},
            "sources": [
                {
                    "series_id": "series.test",
                    "provider": "provider",
                    "provider_series_id": "1",
                    "normalization": {"kind": "scale", "factor": 1000000},
                    "snapshot_sha256": "a" * 64,
                }
            ],
        }

    def test_refresh_does_not_invalidate_structural_review(self) -> None:
        before = curation.structural_fingerprint(self.spec, self.artifact)
        refreshed = copy.deepcopy(self.artifact)
        refreshed["data_as_of"] = "2026-08-20"
        refreshed["generated_at"] = "2026-08-21T00:00:00Z"
        refreshed["snapshot_sha256"]["series.test"] = "b" * 64
        refreshed["sources"][0]["snapshot_sha256"] = "b" * 64
        after = curation.structural_fingerprint(self.spec, refreshed)
        self.assertEqual(before, after)

    def test_structural_change_invalidates_review(self) -> None:
        before = curation.structural_fingerprint(self.spec, self.artifact)
        changed = dict(self.spec)
        changed["frame_id"] = "rf.last_12m"
        after = curation.structural_fingerprint(changed, self.artifact)
        self.assertNotEqual(before, after)

    def test_hazard_preflight_is_conservative_and_deterministic(self) -> None:
        hazards = curation.automatic_hazards(
            self.artifact,
            {"ci.test.level": "monthly"},
            redundant=True,
        )
        self.assertEqual(hazards, {"LONG_NOMINAL_LEVEL", "REDUNDANT_FIGURE"})

        mixed = copy.deepcopy(self.artifact)
        mixed["indicator_ids"] = ["ci.test.daily", "ci.test.monthly"]
        mixed["freshness_state"] = "stale_warning"
        hazards = curation.automatic_hazards(
            mixed,
            {"ci.test.daily": "daily", "ci.test.monthly": "monthly"},
        )
        self.assertIn("FREQUENCY_MISMATCH", hazards)
        self.assertIn("STALE_CURRENT_CLAIM", hazards)

    def test_migrated_real_review_batch_is_current(self) -> None:
        report = curation.validate_repository(strict_fingerprints=True)
        self.assertEqual(report["stale_fingerprints"], [])
        self.assertGreaterEqual(report["terminal_count"], 6)

        ledger = curation.load_ledger()
        expected = {
            "pi.ns31": "HISTORICAL",
            "pi.ns63": "HISTORICAL",
            "pi.ns64": "QUARANTINE",
            "pi.ns58": "SUPERSEDED",
            "pi.ns59": "QUARANTINE",
            "pi.ef49": "QUARANTINE",
        }
        self.assertEqual({plot_id: ledger[plot_id]["state"] for plot_id in expected}, expected)
        self.assertEqual(ledger["pi.ns58"]["preferred_plot_intent_id"], "pi.ns41")

    def test_queue_is_bounded(self) -> None:
        queue = curation.build_queue(limit=6)
        self.assertLessEqual(len(queue), 6)
        self.assertTrue(all(item["state"] != "APPROVED" for item in queue))


if __name__ == "__main__":
    unittest.main()
