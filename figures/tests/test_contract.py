from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

FIGURES_DIR = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("figure_contract", FIGURES_DIR / "validate_contract.py")
contract = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(contract)


class FigureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames_doc = contract.load_yaml(FIGURES_DIR / "reference_frames.yaml")
        cls.renderers_doc = contract.load_yaml(FIGURES_DIR / "renderers.yaml")
        cls.examples_doc = contract.load_yaml(FIGURES_DIR / "examples.yaml")
        cls.frame_ids = contract.validate_reference_frames(cls.frames_doc)
        cls.renderer_ids = contract.validate_renderers(cls.renderers_doc)

    def test_repository_contract_validates(self):
        contract.validate_all()

    def test_reference_frame_rejects_economic_transform(self):
        doc = deepcopy(self.frames_doc)
        doc["reference_frames"][0]["transform"] = "rolling_12m"
        with self.assertRaises(contract.ContractError):
            contract.validate_reference_frames(doc)

    def test_series_binding_rejects_economic_formula(self):
        binding = deepcopy(self.examples_doc["series_bindings"][0])
        binding["normalization"] = {"kind": "formula", "expression": "pct_change(x)"}
        with self.assertRaises(contract.ContractError):
            contract.validate_series_binding(binding)

    def test_chart_spec_rejects_series_binding_logic(self):
        spec = deepcopy(self.examples_doc["chart_specs"][0])
        spec["series_id"] = "series.should.not.live.here"
        with self.assertRaises(contract.ContractError):
            contract.validate_chart_spec(spec, self.frame_ids, self.renderer_ids)

    def test_chart_spec_rejects_unregistered_renderer(self):
        spec = deepcopy(self.examples_doc["chart_specs"][0])
        spec["renderer"] = "line_with_reference_event"
        with self.assertRaises(contract.ContractError):
            contract.validate_chart_spec(spec, self.frame_ids, self.renderer_ids)

    def test_plot_artifact_requires_snapshot_hash_for_each_series(self):
        artifact = deepcopy(self.examples_doc["plot_artifact_shape"])
        artifact["series_ids"].append("series.second")
        with self.assertRaises(contract.ContractError):
            contract.validate_plot_artifact(artifact, self.frame_ids)


if __name__ == "__main__":
    unittest.main()
