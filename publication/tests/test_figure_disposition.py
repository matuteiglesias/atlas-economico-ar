from __future__ import annotations

import unittest

from publication.figure_disposition import PlotPublicationError, derive_plot_publication, disposition_map


class PlotPublicationDispositionTests(unittest.TestCase):
    def test_curation_terminal_states_override_legacy_defaults(self) -> None:
        ledger = derive_plot_publication(
            ["pi.approved", "pi.reference", "pi.historical", "pi.superseded", "pi.quarantine", "pi.unreviewed"],
            {
                "pi.approved": {"state": "APPROVED", "note": "primary"},
                "pi.reference": {"state": "REFERENCE", "note": "reference"},
                "pi.historical": {"state": "HISTORICAL", "note": "history"},
                "pi.superseded": {
                    "state": "SUPERSEDED",
                    "preferred_plot_intent_id": "pi.approved",
                    "note": "prefer approved",
                },
                "pi.quarantine": {"state": "QUARANTINE", "note": "unsafe prominence"},
            },
            {},
        )
        records = disposition_map(ledger)

        self.assertTrue(records["pi.approved"]["prominent"])
        self.assertTrue(records["pi.approved"]["primaryEvidence"])
        for pid in ("pi.reference", "pi.historical", "pi.superseded", "pi.quarantine"):
            self.assertTrue(records[pid]["addressable"])
            self.assertFalse(records[pid]["prominent"])
            self.assertFalse(records[pid]["primaryEvidence"])
        self.assertEqual(records["pi.superseded"]["canonicalPlotIntentId"], "pi.approved")
        self.assertEqual(records["pi.unreviewed"]["state"], "UNREVIEWED")
        self.assertTrue(records["pi.unreviewed"]["prominent"])
        self.assertTrue(records["pi.unreviewed"]["primaryEvidence"])
        self.assertFalse(records["pi.unreviewed"]["reviewed"])

    def test_legacy_exception_remains_a_compatibility_fallback(self) -> None:
        ledger = derive_plot_publication(
            ["pi.history", "pi.quarantine", "pi.default"],
            {},
            {
                "pi.history": {"status": "historical", "note": "old history"},
                "pi.quarantine": {"status": "quarantine", "note": "old quarantine"},
            },
        )
        records = disposition_map(ledger)
        self.assertEqual(records["pi.history"]["state"], "HISTORICAL")
        self.assertEqual(records["pi.quarantine"]["state"], "QUARANTINE")
        self.assertEqual(records["pi.default"]["state"], "UNREVIEWED")

    def test_superseded_requires_materialized_canonical_plot(self) -> None:
        with self.assertRaises(PlotPublicationError):
            derive_plot_publication(
                ["pi.old"],
                {"pi.old": {"state": "SUPERSEDED", "preferred_plot_intent_id": "pi.missing"}},
                {},
            )


if __name__ == "__main__":
    unittest.main()
