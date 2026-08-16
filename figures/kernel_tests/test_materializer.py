from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "figures"
sys.path.insert(0, str(FIGURES))

import materialize
import validate_contract
from derived_resolver import resolve_measurement


class FigureKernelTests(unittest.TestCase):
    def test_all_active_specs_obey_v02_contract(self):
        frame_ids = validate_contract.validate_reference_frames(
            validate_contract.load_yaml(FIGURES / "reference_frames.yaml")
        )
        renderer_ids = validate_contract.validate_renderers(
            validate_contract.load_yaml(FIGURES / "renderers.yaml")
        )
        specs = materialize.load_specs()
        self.assertEqual(len(specs), 35)
        for index, spec in enumerate(specs):
            validate_contract.validate_chart_spec(
                spec, frame_ids, renderer_ids, f"active.chart_specs[{index}]"
            )

    def test_every_active_intent_is_measurement_ready(self):
        intents = materialize.load_plot_intents()
        for spec in materialize.load_specs():
            required = intents[spec["plot_intent_id"]]["canonical_indicator_ids"]
            self.assertTrue(required)
            for indicator_id in required:
                self.assertEqual(resolve_measurement(indicator_id).indicator_id, indicator_id)

    def test_materializes_exactly_35_contract_valid_artifacts(self):
        frame_ids = validate_contract.validate_reference_frames(
            validate_contract.load_yaml(FIGURES / "reference_frames.yaml")
        )
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            output = Path(tmp) / "plot-artifacts"
            artifacts = materialize.materialize(output)
            self.assertEqual(len(artifacts), 35)
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertEqual(manifest["artifact_count"], 35)
            self.assertEqual(len(list((output / "svg").glob("*.svg"))), 35)
            self.assertEqual(len(list((output / "png").glob("*.png"))), 35)
            for artifact in artifacts:
                validate_contract.validate_plot_artifact(artifact, frame_ids)


if __name__ == "__main__":
    unittest.main()
